import xml.etree.ElementTree as ET
import pytest
from relay_api.infrastructure.enterprise import IntegrationError, parse_legacy
from relay_api.domain.models import Chat


def xml(**overrides):
    d = dict(
        ACCT_NO="ACC-2001",
        SVC_NO="SVC-5001",
        SVC_STAT="A",
        NET_STAT="DEGRADED",
        ERR_CD="0",
        RESP_TS="2026-10-13T08:30:00Z",
    )
    d.update(overrides)
    r = ET.Element("SubscriberStatusResponse")
    for k, v in d.items():
        ET.SubElement(r, k).text = v
    return ET.tostring(r)


@pytest.mark.parametrize(
    "raw,reason",
    [
        (b"<broken>", "malformed_xml"),
        (b'<!DOCTYPE x [<!ENTITY test SYSTEM "file:///secrets">]><x/>', "unsafe_xml"),
        (xml(SVC_STAT=""), "missing_field"),
        (xml(ACCT_NO="ACC-2002"), "identity_mismatch"),
        (xml(NET_STAT="ALIEN"), "unknown_status"),
    ],
)
def test_legacy_bad_xml(raw, reason):
    with pytest.raises(IntegrationError, match=reason):
        parse_legacy(raw, "ACC-2001", "SVC-5001")


@pytest.mark.parametrize(
    "code,reason",
    [
        ("101", "account_missing"),
        ("102", "service_missing"),
        ("205", "auth_rejected"),
        ("301", "missing_field"),
        ("429", "rate_limited"),
        ("503", "unavailable"),
        ("900", "unknown_error"),
    ],
)
def test_legacy_error_mapping(code, reason):
    with pytest.raises(IntegrationError, match=reason):
        parse_legacy(xml(ERR_CD=code), "ACC-2001", "SVC-5001")


def test_valid_legacy():
    assert parse_legacy(xml(), "ACC-2001", "SVC-5001")["subscriberStatus"] == "active"


def test_legacy_encoding_and_duplicate_fields():
    for raw in [
        xml().decode().encode("utf-16"),
        xml().replace(b"</SubscriberStatusResponse>", b"<ERR_CD>0</ERR_CD></SubscriberStatusResponse>"),
    ]:
        with pytest.raises(IntegrationError):
            parse_legacy(raw, "ACC-2001", "SVC-5001")


@pytest.mark.parametrize(
    "integration,mode,message",
    [
        ("billing", "malformed", "Show my bill"),
        ("billing", "unavailable", "Show my bill"),
        ("legacy", "malformed", "legacy status"),
        ("legacy", "unavailable", "legacy status"),
        ("legacy", "timeout", "legacy status"),
    ],
)
def test_real_service_failure(stack, customer, integration, mode, message):
    app, _, _ = stack
    app.gateway.timeout = 0.05
    customer["failures"] = {integration: mode}
    r = app.chat(customer, Chat(message=message))
    assert r["state"] == "ESCALATED" and "caseId" not in r
    assert app.store.escalations()[-1][1]["reason"].startswith(
        "legacy-subscriber-status" if integration == "legacy" else "billing"
    )
    if mode in ("unavailable", "timeout"):
        assert any(
            e["eventType"] == "tool.retry" and e["traceId"] == r["traceId"] for e in app.store.events()
        )


def test_connection_failure(stack, customer):
    app, _, _ = stack
    app.gateway.base = "http://127.0.0.1:1"
    app.gateway.timeout = 0.05
    r = app.chat(customer, Chat(message="my plan"))
    assert r["state"] == "ESCALATED"


def test_billing_grounding(stack, customer):
    r = stack[0].chat(customer, Chat(message="Show my bill"))
    assert r["state"] == "RESOLVED" and "84.99" in r["answer"] and "Equipment: 5.00" in r["answer"]


def test_handoff_context(stack, customer):
    r = stack[0].chat(customer, Chat(message="Please escalate to a human"))
    assert r["state"] == "ESCALATED"
    record = stack[0].store.escalations()[-1][1]
    assert "human" in record["requestSummary"] and record["recommendedNextStep"]
