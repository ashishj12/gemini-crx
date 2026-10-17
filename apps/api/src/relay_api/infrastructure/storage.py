"""SQLite persistence; bearer secrets are hashed and never included in telemetry."""

import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from jsonschema import Draft202012Validator
from relay_api.ai.providers import redact
from relay_api.core.config import CHALLENGE_ROOT


def uid(prefix):
    return prefix + "-" + uuid.uuid4().hex


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, expires REAL, data TEXT);
        CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY, body TEXT);
        CREATE TABLE IF NOT EXISTS escalations (id TEXT PRIMARY KEY, session TEXT, body TEXT);
        CREATE TABLE IF NOT EXISTS telemetry_rejections (timestamp TEXT, reason TEXT);
        """)
        schema = CHALLENGE_ROOT / "schemas/telemetry-event.schema.json"
        self.validator = Draft202012Validator(json.loads(schema.read_text()))
        self.log_path = Path(os.getenv("STRUCTURED_LOG_PATH", str(Path(path).parent / "events.jsonl")))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, s):
        with self.lock, self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?,?,?)", (s["id"], s["expires"], json.dumps(s))
            )

    def session(self, token):
        return self.session_by_id(digest(token))

    def session_by_id(self, session_id):
        with self.lock:
            row = self.db.execute("SELECT data FROM sessions WHERE id=?", (session_id,)).fetchone()
        if not row:
            return None
        s = json.loads(row[0])
        return s if s["expires"] > time.time() else None

    def emit(self, kind, trace, session, status="success", component="orchestrator", duration=0, **metadata):
        event = dict(
            eventId=uid("EVT"),
            traceId=trace,
            sessionId=session,
            timestamp=datetime.now(timezone.utc).isoformat(),
            eventType=kind,
            component=component,
            status=status,
            durationMs=max(0, duration),
            metadata=metadata,
        )
        if not self.ingest(event):
            raise ValueError("invalid_internal_telemetry_event")
        return event

    def ingest(self, event):
        """Reject invalid events without storing their potentially sensitive payloads."""

        def sanitize(value, key=""):
            if any(word in key.lower() for word in ("password", "token", "secret", "api_key", "apikey")):
                return "[REDACTED]"
            if isinstance(value, dict):
                return {k: sanitize(v, k) for k, v in value.items()}
            if isinstance(value, list):
                return [sanitize(v) for v in value]
            return redact(value) if isinstance(value, str) else value

        try:
            event = sanitize(event)
            self.validator.validate(event)
            encoded = json.dumps(event, allow_nan=False)
        except Exception:
            # Only a category is retained, never raw invalid input or exception text.
            with self.lock, self.db:
                self.db.execute(
                    "INSERT INTO telemetry_rejections VALUES (?,?)",
                    (datetime.now(timezone.utc).isoformat(), "invalid_event_schema"),
                )
            return False
        with self.lock, self.db:
            self.db.execute("INSERT INTO events(body) VALUES (?)", (encoded,))
            try:
                with self.log_path.open("a", encoding="utf-8") as log:
                    log.write(encoded + "\n")
            except OSError:
                pass  # SQLite remains the authoritative event sink if file logging fails.
        return True

    def events(self):
        with self.lock:
            return [json.loads(r[0]) for r in self.db.execute("SELECT body FROM events ORDER BY seq")]

    def escalate(self, session, record):
        with self.lock, self.db:
            self.db.execute(
                "INSERT INTO escalations VALUES (?,?,?)",
                (record["escalationId"], session, json.dumps(record)),
            )

    def escalations(self):
        with self.lock:
            return [(r[0], json.loads(r[1])) for r in self.db.execute("SELECT session,body FROM escalations")]

    def metrics(self):
        events = self.events()

        def count(kind):
            return sum(e["eventType"] == kind for e in events)

        requests = count("request.received")
        tools = [e for e in events if e["eventType"] == "tool.finished"]
        ai = [e for e in events if e["eventType"] == "ai.finished"]
        finished = [e for e in events if e["eventType"] == "request.finished"]

        def ratio(n, d):
            return n / d if d else 0

        with self.lock:
            rejected = self.db.execute("SELECT COUNT(*) FROM telemetry_rejections").fetchone()[0]
        return dict(
            window="all persisted events since database initialization",
            telemetryRejected=rejected,
            sessions=count("session.created"),
            requests=requests,
            resolutionRate=ratio(count("workflow.resolved"), requests),
            escalationRate=ratio(count("workflow.escalated"), requests),
            failureRate=ratio(sum(e["status"] == "failure" for e in finished), requests),
            averageWorkflowMs=ratio(sum(e["durationMs"] for e in finished), len(finished)),
            toolSuccessRate=ratio(sum(e["status"] == "success" for e in tools), len(tools)),
            failuresByIntegration={
                name: sum(e["status"] == "failure" and e["component"] == name for e in tools)
                for name in {e["component"] for e in tools}
            },
            authenticationFailures=count("authentication.failed"),
            authorizationDenials=count("authorization.denied"),
            geminiFailures=sum(e["status"] == "failure" for e in ai),
            geminiLatencyMs=ratio(sum(e["durationMs"] for e in ai), len(ai)),
            retries=count("tool.retry"),
            retryRate=ratio(count("tool.retry"), len(tools)),
            humanHandoffRate=ratio(count("workflow.escalated"), requests),
            toolUsage={
                name: sum(e["component"] == name for e in tools) for name in {e["component"] for e in tools}
            },
            agentUsage={
                name: sum(e["component"] == name for e in events if e["eventType"] == "agent.invoked")
                for name in {e["component"] for e in events if e["eventType"] == "agent.invoked"}
            },
        )
