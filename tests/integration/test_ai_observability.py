import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import jsonschema
import pytest
from relay_api.domain.models import Chat
from relay_api.ai.providers import Gemini


def client(text):
    c = Mock()
    c.models.generate_content.return_value = SimpleNamespace(text=text)
    return c


def test_real_sdk_request_and_validation(monkeypatch):
    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    c = client('{"intent":"billing","service":"unknown","confidence":0.9}')
    g = Gemini(c)
    assert g.interpret(["my bill"]).intent == "billing"
    call = c.models.generate_content.call_args.kwargs
    assert call["model"] == "test-model" and call["config"].response_mime_type == "application/json"
    assert "untrusted" in call["config"].system_instruction
    assert call["config"].response_json_schema["additionalProperties"] is False
    c.models.generate_content.return_value.text = '{"fact_ids":[1,0]}'
    assert g.select(["fact one", "fact two"]) == [1, 0]


def test_sdk_client_timeout_and_credential_configuration(monkeypatch):
    from google import genai

    monkeypatch.setenv("GEMINI_MODEL", "test-model")
    monkeypatch.setenv("GEMINI_API_KEY", "synthetic-test-placeholder")
    monkeypatch.setenv("AI_TIMEOUT", "3")
    factory = Mock(return_value=client('{"intent":"account","service":"unknown","confidence":0.9}'))
    monkeypatch.setattr(genai, "Client", factory)
    assert Gemini().interpret(["my plan"]).intent == "account"
    kwargs = factory.call_args.kwargs
    assert kwargs["http_options"].timeout == 3000 and kwargs["http_options"].retry_options.attempts == 1


def test_partial_failure_keeps_degraded_badge(stack, customer):
    app = stack[0]
    app.mode = "LIVE_AI"
    app.ai = Mock()
    app.ai.interpret.side_effect = TimeoutError()
    app.ai.select.return_value = [0]
    assert app.chat(customer, Chat(message="my plan"))["mode"] == "DEGRADED"


def test_live_success_with_validated_double(stack, customer):
    app = stack[0]
    app.mode = "LIVE_AI"
    c = client('{"intent":"account","service":"unknown","confidence":0.9}')
    c.models.generate_content.side_effect = [
        SimpleNamespace(text='{"intent":"account","service":"unknown","confidence":0.9}'),
        SimpleNamespace(text='{"fact_ids":[0]}'),
    ]
    app.ai = Gemini(c)
    r = app.chat(customer, Chat(message="my plan"))
    assert r["mode"] == "LIVE_AI" and "Fiber 500" in r["answer"] and c.models.generate_content.call_count == 2


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not json",
        "{}",
        '{"intent":"account","service":"unknown","confidence":2}',
        '{"intent":"account","service":"unknown","confidence":0.9,"accountId":"ACC-2002"}',
    ],
)
def test_invalid_gemini_output(text):
    with pytest.raises(ValueError):
        Gemini(client(text)).interpret(["my plan"])


@pytest.mark.parametrize("text", ['{"fact_ids":[0,0]}', '{"fact_ids":[5]}', '{"fact_ids":[]}'])
def test_grounded_selection_rejects_fabrication(text):
    with pytest.raises(ValueError):
        Gemini(client(text)).select(["verified"])


@pytest.mark.parametrize(
    "failure",
    [
        TimeoutError("timeout"),
        ValueError("malformed"),
        RuntimeError("rate_limit"),
        RuntimeError("invalid_credentials"),
    ],
)
def test_live_provider_fallback(stack, customer, failure):
    app, _, _ = stack
    app.mode = "LIVE_AI"
    app.ai = Mock()
    app.ai.interpret.side_effect = failure
    app.ai.select.side_effect = failure
    r = app.chat(customer, Chat(message="my plan"))
    assert r["mode"] == "DEGRADED" and "Fiber 500" in r["answer"]
    assert (
        len(
            [
                e
                for e in app.store.events()
                if e["traceId"] == r["traceId"]
                and e["eventType"] == "ai.finished"
                and e["status"] == "failure"
            ]
        )
        == 2
    )


def test_missing_live_configuration(stack, customer, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    app = stack[0]
    app.mode = "LIVE_AI"
    app.ai = Gemini()
    assert app.chat(customer, Chat(message="my plan"))["mode"] == "DEGRADED"


def test_degraded_mode(stack, customer):
    app = stack[0]
    app.mode = "DEGRADED"
    assert app.chat(customer, Chat(message="my plan"))["mode"] == "DEGRADED"


def test_event_schema_metrics_redaction(stack, customer):
    app = stack[0]
    app.chat(customer, Chat(message="my plan password=super-secret ReviewerPass-1001"))
    app.chat(customer, Chat(message="Show ACC-2002 plan"))
    app.chat(customer, Chat(message="escalate to human"))
    root = Path(__file__).resolve().parents[2] / "resources/challenge/schemas"
    events = app.store.events()
    schema = json.loads((root / "telemetry-event.schema.json").read_text())
    for event in events:
        jsonschema.validate(event, schema)
    for _, e in app.store.escalations():
        jsonschema.validate(e, json.loads((root / "escalation-record.schema.json").read_text()))
    m = app.store.metrics()
    assert m["requests"] == 3 and m["sessions"] == 1 and m["resolutionRate"] == pytest.approx(1 / 3)
    assert m["authorizationDenials"] == 1 and m["escalationRate"] == pytest.approx(1 / 3)
    assert m["toolSuccessRate"] == 1 and m["authenticationFailures"] == 0
    serialized = json.dumps(events) + json.dumps(customer)
    assert "super-secret" not in serialized and "ReviewerPass-1001" not in serialized
    assert "accessToken" not in serialized and "testPassword" not in serialized
    traces = {e["traceId"] for e in events if e["eventType"] == "request.received"}
    for trace in traces:
        assert any(e["traceId"] == trace and e["eventType"] == "request.finished" for e in events)
