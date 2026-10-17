"""Verify the running Compose stack through the public Next.js gateway."""

import json
from pathlib import Path
import subprocess
import httpx

ROOT = Path(__file__).resolve().parents[1]


def verify():
    results = []
    with httpx.Client(base_url="http://127.0.0.1:3000", trust_env=False, timeout=120) as client:
        client.get("/").raise_for_status()
        client.get("/api/health").raise_for_status()
        assert client.post("/api/chat", json={"message": "my plan"}).status_code == 401
        assert client.post("/api/login", json={}, headers={"Origin": "https://evil.test"}).status_code == 403
        client.post(
            "/api/login",
            json={"username": "support.agent", "password": "ReviewerPass-3001"},
            headers={"Origin": "http://127.0.0.1:3000"},
        ).raise_for_status()
        for number in range(1, 9):
            response = client.post("/api/reviewer/run", json={"scenarioId": f"SCN-{number:03}"})
            response.raise_for_status()
            result = response.json()
            results.append(result)
            print(result["scenarioId"], result["status"], flush=True)
        assert all(r["status"] == "PASS" for r in results)
        assert client.get("/api/ops/metrics").json()["requests"] > 0
    images = {}
    users = {}
    for service in ("api", "web", "enterprise"):
        images[service] = subprocess.check_output(
            ["docker", "image", "inspect", "relay-release-" + service, "--format", "{{.Id}}"], text=True
        ).strip()
        users[service] = subprocess.check_output(
            ["docker", "compose", "-p", "relay-release", "exec", "-T", service, "id", "-u"], text=True
        ).strip()
        assert users[service] != "0"
    evidence = {
        "status": "PASS",
        "command": "python tools/verify_containers.py",
        "publicGateway": "http://127.0.0.1:3000",
        "unauthenticatedDenied": True,
        "foreignOriginDenied": True,
        "images": images,
        "runtimeUIDs": users,
        "results": results,
    }
    (ROOT / "evidence/current/docker-verification.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    verify()
