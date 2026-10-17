"""Negative behavior and durability checks required by the final challenge directive."""

import copy
import json
import time
import pytest
from relay_api.infrastructure.enterprise import Denied
from relay_api.domain.models import Chat, Confirmation
from relay_api.infrastructure.storage import uid
from relay_api.application.workflows import ResolutionService


def test_event_ingestion_rejects_invalid_payload_safely(stack):
    store = stack[0].store
    before = len(store.events())
    assert not store.ingest({"password": "do-not-store", "eventType": "x"})
    assert not store.ingest(
        {
            "eventId": "x",
            "traceId": "x",
            "sessionId": "x",
            "timestamp": "x",
            "eventType": "x",
            "component": "x",
            "status": "invented",
        }
    )
    assert not store.ingest(None)
    assert len(store.events()) == before and store.metrics()["telemetryRejected"] == 3
    assert "do-not-store" not in str(list(store.db.execute("SELECT * FROM telemetry_rejections")))


def test_structured_log_redacts_sensitive_values(stack):
    store = stack[0].store
    store.emit(
        "test.event",
        uid("TRACE"),
        "test",
        password="secret-value",
        nested={"accessToken": "upstream-token"},
        summary="password=raw-password",
    )
    raw = store.log_path.read_text()
    assert "secret-value" not in raw and "upstream-token" not in raw and "raw-password" not in raw
    assert json.loads(raw.splitlines()[-1])["metadata"]["password"] == "[REDACTED]"


def test_tool_scope_prevents_direct_action_bypass(stack, customer):
    app, mock, _ = stack
    action = {"id": uid("ACT"), "summary": "case", "accountId": customer["accountId"], "status": "pending"}
    with pytest.raises(Denied):
        app.gateway.create_case(customer, uid("TRACE"), action)
    customer["state"] = "EXECUTING_ACTION"
    action["status"] = "executing"
    action["confirmedAt"] = time.time()
    with pytest.raises(Denied):
        app.gateway.create_case(customer, uid("TRACE"), action)
    assert not mock.CASES


def test_tool_scope_prevents_reads_outside_workflow(stack, customer):
    app, _, _ = stack
    with pytest.raises(Denied):
        app.gateway.account(customer, uid("TRACE"), customer["accountId"])
    assert not any(
        e["eventType"] == "tool.invoked" and e["component"] == "account-service" for e in app.store.events()
    )


def test_actual_database_reopen_preserves_action_and_history(stack, customer):
    app, mock, _ = stack
    r = app.chat(customer, Chat(message="Create a support case for my internet issue."))
    path = app.store.db.execute("PRAGMA database_list").fetchone()[2]
    reopened = ResolutionService(path, app.gateway.base)
    try:
        s = reopened.store.session_by_id(customer["id"])
        assert s["pending"]["id"] == r["pendingAction"]["id"] and s["history"]
        c = Confirmation(actionId=s["pending"]["id"], confirm=True)
        created = reopened.confirm(s, c)
        stale = copy.deepcopy(customer)
        assert app.confirm(stale, c)["caseId"] == created["caseId"]
        assert len(mock.CASES) == 1
        assert app.store.session_by_id(customer["id"])["pending"]["status"] == "completed"
    finally:
        reopened.store.db.close()


def test_interrupted_execution_requires_reconciliation_after_restart(stack, customer):
    app, mock, _ = stack
    app.chat(customer, Chat(message="Create a support case"))
    customer["state"] = "EXECUTING_ACTION"
    customer["pending"].update(status="executing", confirmedAt=time.time())
    app.store.save(customer)
    reopened = ResolutionService(app.store.db.execute("PRAGMA database_list").fetchone()[2], app.gateway.base)
    try:
        s = reopened.store.session_by_id(customer["id"])
        r = reopened.confirm(s, Confirmation(actionId=s["pending"]["id"], confirm=True))
        assert r["state"] == "FAILED" and not mock.CASES
    finally:
        reopened.store.db.close()


def test_repeated_action_request_does_not_open_new_case(stack, customer):
    app, mock, _ = stack
    message = "Create a support case for my internet issue."
    app.chat(customer, Chat(message=message))
    first = app.confirm(customer, Confirmation(actionId=customer["pending"]["id"], confirm=True))
    repeat = app.chat(customer, Chat(message=message))
    assert repeat["caseId"] == first["caseId"] and "pendingAction" not in repeat and len(mock.CASES) == 1


def test_response_consistency_failure_is_failed_tool_not_success(stack, customer):
    app, mock, _ = stack
    mock.ACCOUNTS[0]["customerId"] = "CUST-1002"
    r = app.chat(customer, Chat(message="my plan"))
    tools = [
        e
        for e in app.store.events()
        if e["traceId"] == r["traceId"]
        and e["eventType"] == "tool.finished"
        and e["component"] == "account-service"
    ]
    assert (
        len(tools) == 1
        and tools[0]["status"] == "failure"
        and tools[0]["metadata"]["reason"] == "identity_mismatch"
    )
    assert app.store.metrics()["failuresByIntegration"]["account-service"] == 1


def test_internal_processing_failure_preserves_correlated_handoff(stack, customer, monkeypatch):
    app, _, _ = stack

    def fail(*args):
        raise RuntimeError("secret=must-not-leak")

    monkeypatch.setattr(app.gateway, "profile", fail)
    r = app.chat(customer, Chat(message="my plan"))
    assert r["state"] == "ESCALATED" and "must-not-leak" not in json.dumps(r)
    events = [e for e in app.store.events() if e["traceId"] == r["traceId"]]
    assert {"processing.failed", "workflow.failed", "workflow.escalated", "request.finished"}.issubset(
        {e["eventType"] for e in events}
    )
    assert app.store.escalations()[-1][1]["reason"] == "internal_processing_failure"


def test_confirmation_event_precedes_side_effect(stack, customer):
    app, _, _ = stack
    app.chat(customer, Chat(message="Create a support case"))
    r = app.confirm(customer, Confirmation(actionId=customer["pending"]["id"], confirm=True))
    events = [e for e in app.store.events() if e["traceId"] == r["traceId"]]
    names = [e["eventType"] for e in events]
    assert (
        names.index("confirmation.received") < names.index("tool.invoked") < names.index("action.completed")
    )


def test_dotenv_is_data_only_and_process_environment_wins(tmp_path, monkeypatch):
    from relay_api.core.config import load_environment

    file = tmp_path / ".env"
    file.write_text(
        'GEMINI_MODEL="test-model"\nGEMINI_API_KEY=synthetic-test-key\nAPP_MODE=LIVE_AI\nPATH=do-not-override\n'
    )
    monkeypatch.setenv("APP_MODE", "REVIEWER")
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("PATH", "unchanged")
    load_environment(file)
    assert (
        __import__("os").environ["APP_MODE"] == "REVIEWER"
        and __import__("os").environ["GEMINI_MODEL"] == "test-model"
    )
    assert __import__("os").environ["PATH"] == "unchanged"


def test_enterprise_rate_limit_bounded_retries(stack, customer, monkeypatch):
    app, mock, _ = stack
    seen = []
    original = mock.H.js

    def rate_limit(handler, status, obj):
        if handler.path.endswith("/billing"):
            seen.append(handler.path)
            return original(handler, 429, {"error": "rate_limited"})
        return original(handler, status, obj)

    monkeypatch.setattr(mock.H, "js", rate_limit)
    r = app.chat(customer, Chat(message="Show my bill"))
    assert r["state"] == "ESCALATED" and len(seen) == 2
    events = [e for e in app.store.events() if e["traceId"] == r["traceId"]]
    assert sum(e["eventType"] == "tool.retry" for e in events) == 1
    assert app.store.escalations()[-1][1]["reason"] == "billing:http_429"


def test_malformed_json_and_nonfinite_billing_are_rejected(stack, customer, monkeypatch):
    app, mock, _ = stack
    original = mock.H.js

    def malformed(handler, status, obj):
        if handler.path.endswith("/billing"):
            raw = b"{invalid"
            handler.send_response(200)
            handler.send_header("Content-Length", str(len(raw)))
            handler.end_headers()
            handler.wfile.write(raw)
            return
        return original(handler, status, obj)

    monkeypatch.setattr(mock.H, "js", malformed)
    assert app.chat(customer, Chat(message="Show my bill"))["state"] == "ESCALATED"
    from relay_api.domain.models import Billing

    with pytest.raises(ValueError):
        Billing.model_validate(
            {
                "accountId": "ACC-2001",
                "period": "2026-09",
                "total": 5,
                "items": [{"description": "x", "amount": float("nan")}],
            }
        )
