"""Allowlisted enterprise operations. Ownership is checked before any protected read."""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pydantic import ValidationError
from relay_api.domain.models import Auth, Profile, Account, Billing, Outage, Diagnostic, Case


class IntegrationError(Exception):
    def __init__(self, service, reason, temporary=False):
        self.service, self.reason, self.temporary = service, reason, temporary
        super().__init__(service + ":" + reason)


class Denied(Exception):
    pass


class Gateway:
    def __init__(self, store, base, timeout=2, retries=1):
        self.store, self.base, self.timeout, self.retries = store, base.rstrip("/"), timeout, retries
        self.http = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def authorize(self, s, account, trace):
        if (
            s["expires"] <= time.time()
            or "customer" not in s["roles"]
            or not account
            or account != s.get("accountId")
        ):
            self.store.emit("authorization.denied", trace, s["id"], status="denied")
            raise Denied("Account access denied.")
        self.store.emit("authorization.allowed", trace, s["id"])

    def reading(self, s, t):
        self.authorize(s, s.get("accountId"), t)
        if s.get("state") != "FETCHING_ENTERPRISE_DATA":
            self.store.emit("authorization.denied", t, s["id"], status="denied", reason="workflow_tool_scope")
            raise Denied("Tool not allowed in this workflow state.")

    def request(self, name, path, trace, s, payload=None, schema=None, xml=False, safe=False, normalize=None):
        start = time.monotonic()
        attempts = 1 + (self.retries if payload is None or safe else 0)
        self.store.emit(
            "tool.invoked",
            trace,
            s["id"],
            component=name,
            method="POST" if payload is not None else "GET",
            inputSummary="credentials submitted to synthetic identity service"
            if name == "authentication"
            else "validated session-scoped parameters",
            safeRetry=bool(payload is None or safe),
        )
        for attempt in range(attempts):
            try:
                headers = {
                    "Content-Type": "application/xml" if xml else "application/json",
                    "X-Correlation-ID": trace,
                }
                if s.get("failures") and os.getenv("APP_MODE", "REVIEWER") == "REVIEWER":
                    headers["X-Reviewer-Failures"] = json.dumps(s["failures"])
                body = (
                    payload.encode() if xml else json.dumps(payload).encode() if payload is not None else None
                )
                req = urllib.request.Request(self.base + path, data=body, headers=headers)
                with self.http.open(req, timeout=self.timeout) as response:
                    raw = response.read(262145)
                if len(raw) > 262144:
                    raise ValueError("oversized")
                result = raw if xml else json.loads(raw)
                if schema:
                    result = schema.model_validate(result)
                if normalize:
                    result = normalize(result)
                self.store.emit(
                    "tool.finished",
                    trace,
                    s["id"],
                    component=name,
                    duration=(time.monotonic() - start) * 1000,
                    outputSummary={
                        "validated": True,
                        "recordType": name,
                        "identityChecked": name not in ("authentication", "health"),
                    },
                )
                return result
            except urllib.error.HTTPError as e:
                error = IntegrationError(name, "http_" + str(e.code), e.code in (429, 500, 502, 503, 504))
            except (TimeoutError, urllib.error.URLError, ConnectionError, OSError):
                error = IntegrationError(name, "transport_or_timeout", True)
            except (ValueError, ValidationError):
                error = IntegrationError(name, "invalid_response")
            except IntegrationError as e:
                error = e
            if not error.temporary or attempt == attempts - 1:
                self.store.emit(
                    "tool.finished",
                    trace,
                    s["id"],
                    status="failure",
                    component=name,
                    duration=(time.monotonic() - start) * 1000,
                    reason=error.reason,
                )
                raise error
            self.store.emit("tool.retry", trace, s["id"], component=name, attempt=attempt + 1)
            time.sleep(0.05 * (attempt + 1))

    def login(self, data, trace, anonymous):
        return self.request("authentication", "/api/auth/login", trace, anonymous, payload=data, schema=Auth)

    def profile(self, s, t):
        self.reading(s, t)

        def verify(p):
            if p.customerId != s["customerId"] or p.accountId != s["accountId"]:
                raise IntegrationError("customer-profile", "identity_mismatch")
            return p

        return self.request(
            "customer-profile", "/api/customers/" + s["customerId"], t, s, schema=Profile, normalize=verify
        )

    def account(self, s, t, account):
        self.authorize(s, account, t)
        self.reading(s, t)

        def verify(a):
            if a.accountId != account or a.customerId != s["customerId"]:
                raise IntegrationError("account-service", "identity_mismatch")
            return a

        return self.request(
            "account-service", "/api/accounts/" + account, t, s, schema=Account, normalize=verify
        )

    def billing(self, s, t, account):
        self.authorize(s, account, t)
        self.reading(s, t)

        def verify(b):
            if b.accountId != account or abs(sum(i.amount for i in b.items) - b.total) > 0.01:
                raise IntegrationError("billing", "inconsistent_record")
            return b

        return self.request(
            "billing", "/api/accounts/" + account + "/billing", t, s, schema=Billing, normalize=verify
        )

    def network(self, s, t, profile):
        self.reading(s, t)
        if profile.customerId != s["customerId"] or profile.accountId != s["accountId"]:
            raise Denied("Profile access denied.")

        def verify(o):
            if o.postalCode != profile.postalCode:
                raise IntegrationError("network-outage", "identity_mismatch")
            return o

        return self.request(
            "network-outage",
            "/api/network/outages?" + urllib.parse.urlencode({"postalCode": profile.postalCode}),
            t,
            s,
            schema=Outage,
            normalize=verify,
        )

    def diagnostics(self, s, t, service):
        self.reading(s, t)
        if service not in {x.serviceId for x in self.account(s, t, s["accountId"]).services}:
            raise Denied("Service access denied.")

        def verify(d):
            if d.serviceId != service:
                raise IntegrationError("diagnostics", "identity_mismatch")
            return d

        return self.request(
            "diagnostics",
            "/api/diagnostics",
            t,
            s,
            payload={"serviceId": service},
            schema=Diagnostic,
            safe=True,
            normalize=verify,
        )

    def legacy(self, s, t, service):
        self.reading(s, t)
        if service not in {x.serviceId for x in self.account(s, t, s["accountId"]).services}:
            raise Denied("Service access denied.")
        root = ET.Element("SubscriberStatusRequest")
        ET.SubElement(root, "AccountNumber").text = s["accountId"]
        ET.SubElement(root, "ServiceNumber").text = service
        return self.request(
            "legacy-subscriber-status",
            "/api/legacy/subscriber-status",
            t,
            s,
            payload=ET.tostring(root, encoding="unicode"),
            xml=True,
            safe=True,
            normalize=lambda raw: parse_legacy(raw, s["accountId"], service),
        )

    def create_case(self, s, t, action):
        self.authorize(s, s["accountId"], t)
        saved = self.store.session_by_id(s["id"])
        pending = (saved or {}).get("pending") or {}
        if (
            not saved
            or saved["state"] != "EXECUTING_ACTION"
            or s["state"] != "EXECUTING_ACTION"
            or pending.get("id") != action.get("id")
            or pending.get("status") != "executing"
            or not pending.get("confirmedAt")
            or pending.get("accountId") != s["accountId"]
        ):
            self.store.emit(
                "authorization.denied",
                t,
                s["id"],
                status="denied",
                reason="confirmation_or_workflow_required",
            )
            raise Denied("Confirmed durable action required.")

        def verify(c):
            if (
                c.accountId != s["accountId"]
                or c.customerId != s["customerId"]
                or c.idempotencyKey != action["id"]
            ):
                raise IntegrationError("case-management", "identity_mismatch")
            return c

        return self.request(
            "case-management",
            "/api/support-cases",
            t,
            s,
            payload={
                "customerId": s["customerId"],
                "accountId": s["accountId"],
                "summary": pending["summary"],
                "idempotencyKey": pending["id"],
            },
            schema=Case,
            normalize=verify,
        )


def parse_legacy(raw, account, service):
    def fail(reason):
        raise IntegrationError("legacy-subscriber-status", reason)

    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        fail("unsafe_xml")
    if b"\x00" in raw:
        fail("unsafe_xml")
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        fail("unsafe_xml")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        fail("malformed_xml")
    if root.tag != "SubscriberStatusResponse":
        fail("invalid_root")
    fields = {
        k: (root.findtext(k) or "").strip()
        for k in ("ACCT_NO", "SVC_NO", "SVC_STAT", "NET_STAT", "ERR_CD", "RESP_TS")
    }
    if any(len(root.findall(k)) != 1 for k in fields):
        fail("missing_or_duplicate_field")
    if fields["ERR_CD"] != "0":
        fail(
            {
                "101": "account_missing",
                "102": "service_missing",
                "205": "auth_rejected",
                "301": "missing_field",
                "429": "rate_limited",
                "503": "unavailable",
                "900": "unknown_error",
            }.get(fields["ERR_CD"], "unknown_error")
        )
    if not all(fields.values()):
        fail("missing_field")
    if fields["ACCT_NO"] != account or fields["SVC_NO"] != service:
        fail("identity_mismatch")
    status = {"A": "active", "S": "suspended", "I": "inactive"}.get(fields["SVC_STAT"].upper())
    network = fields["NET_STAT"].lower()
    if not status or network not in ("normal", "degraded", "outage"):
        fail("unknown_status")
    return {"subscriberStatus": status, "networkStatus": network, "observedAt": fields["RESP_TS"]}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None
