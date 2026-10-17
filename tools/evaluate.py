"""Isolated real-HTTP evaluator. Starts both supplied services on ephemeral loopback ports."""

import argparse
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import httpx
from processes import stop_children

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api/src"))
from relay_api.core.config import load_environment  # noqa: E402


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def evaluate(mode="REVIEWER", output=None):
    load_environment()
    if mode == "LIVE_AI" and not all(os.getenv(k) for k in ("GEMINI_API_KEY", "GEMINI_MODEL")):
        result = {
            "status": "BLOCKED",
            "mode": mode,
            "reason": "Gemini key/model not configured; no inference attempted",
            "results": [],
        }
        if output:
            Path(output).write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
    children = []
    records = []
    with tempfile.TemporaryDirectory(prefix="relay-evaluation-") as temp:
        enterprise_port, app_port = free_port(), free_port()
        env = dict(
            os.environ,
            APP_MODE=mode,
            MOCK_HOST="127.0.0.1",
            APP_HOST="127.0.0.1",
            MOCK_PORT=str(enterprise_port),
            APP_PORT=str(app_port),
            PORT=str(app_port),
            ENTERPRISE_API_BASE_URL=f"http://127.0.0.1:{enterprise_port}",
            PUBLIC_ORIGIN=f"http://127.0.0.1:{app_port}",
            DATABASE_PATH=str(Path(temp) / "cx.sqlite"),
            STRUCTURED_LOG_PATH=str(Path(temp) / "events.jsonl"),
            MOCK_ALLOW_FAILURES="true" if mode == "REVIEWER" else "false",
            MOCK_AUTH_MODE="normal",
            MOCK_BILLING_MODE="success",
            MOCK_LEGACY_MODE="success",
            MOCK_CASE_MODE="success",
        )
        try:
            env["PYTHONPATH"] = os.pathsep.join(
                [str(ROOT / "apps/api/src"), str(ROOT / "services/mock-telecom/src")]
            )
            for module in ("relay_mock", "relay_api"):
                children.append(
                    subprocess.Popen(
                        [sys.executable, "-m", module],
                        env=env,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                )
            with httpx.Client(base_url=env["PUBLIC_ORIGIN"], trust_env=False, timeout=90) as client:
                deadline = time.monotonic() + 20
                while True:
                    try:
                        if client.get("/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic() > deadline:
                        raise RuntimeError("application_startup_timeout")
                    time.sleep(0.1)
                assert client.post("/api/chat", json={"message": "my plan"}).status_code == 401
                if mode == "REVIEWER":
                    client.post(
                        "/api/login", json={"username": "support.agent", "password": "ReviewerPass-3001"}
                    ).raise_for_status()
                    for n in range(1, 9):
                        response = client.post("/api/reviewer/run", json={"scenarioId": f"SCN-{n:03}"})
                        response.raise_for_status()
                        record = response.json()
                        records.append(record)
                        print(
                            record["scenarioId"],
                            record["status"],
                            len(record["checks"]),
                            "checks",
                            flush=True,
                        )
                else:
                    client.post(
                        "/api/login", json={"username": "alex.morgan", "password": "ReviewerPass-1001"}
                    ).raise_for_status()
                    for message in (
                        "What internet plan am I currently using?",
                        "My service is not working.",
                        "home internet",
                        "Create a support case for my internet issue.",
                    ):
                        response = client.post("/api/chat", json={"message": message})
                        response.raise_for_status()
                        record = response.json()
                        record["input"] = message
                        record["events"] = client.get("/api/traces/" + record["traceId"]).json()
                        records.append(record)
                    if records[-1].get("pendingAction"):
                        response = client.post(
                            "/api/confirm",
                            json={"actionId": records[-1]["pendingAction"]["id"], "confirm": True},
                        )
                        response.raise_for_status()
                        record = response.json()
                        record["events"] = client.get("/api/traces/" + record["traceId"]).json()
                        records.append(record)
                client.post("/api/logout", json={}).raise_for_status()
                client.post(
                    "/api/login", json={"username": "support.agent", "password": "ReviewerPass-3001"}
                ).raise_for_status()
                events = client.get("/api/ops/events").json()
                metrics = client.get("/api/ops/metrics").json()
                if mode == "REVIEWER":
                    passed = all(r["status"] == "PASS" for r in records)
                else:
                    ai = [e for e in events if e["eventType"] == "ai.finished"]
                    passed = (
                        len(records) == 5
                        and all(r["mode"] == "LIVE_AI" for r in records)
                        and all(e["status"] == "success" and not e["metadata"]["simulated"] for e in ai)
                        and len(ai) >= 5
                        and "Fiber 500" in records[0]["answer"]
                        and records[1]["state"] == "NEEDS_CLARIFICATION"
                        and records[2]["state"] == "RESOLVED"
                        and records[3]["state"] == "AWAITING_CONFIRMATION"
                        and bool(records[4].get("caseId"))
                    )
                result = {
                    "status": "PASS" if passed else "FAIL",
                    "mode": mode,
                    "results": records,
                    "metrics": metrics,
                    "model": os.getenv("GEMINI_MODEL", "unconfigured") if mode == "LIVE_AI" else None,
                    "events": events,
                    "command": f"{sys.executable} tools/evaluate.py --mode {mode}",
                }
        finally:
            stop_children(children)
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["REVIEWER", "LIVE_AI"], default="REVIEWER")
    parser.add_argument("--output", default="evidence/current/http-scenarios.json")
    args = parser.parse_args()
    result = evaluate(args.mode, args.output)
    print(args.mode, result["status"])
    sys.exit(0 if result["status"] == "PASS" else 2)
