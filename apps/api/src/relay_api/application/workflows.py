"""Single controlled orchestrator with persistent, two-phase actions."""

import os
from copy import deepcopy
import re
import secrets
import time
from relay_api.infrastructure.enterprise import Gateway, Denied, IntegrationError
from relay_api.ai.providers import Gemini, Reviewer, redact, provider_reason
from relay_api.infrastructure.storage import Store, digest, uid

TRANSITIONS = {
    "NEW": {"INTERPRETING", "AUTHORIZATION_CHECK"},
    "INTERPRETING": {"NEEDS_CLARIFICATION", "AUTHORIZATION_CHECK", "ESCALATED"},
    "AUTHORIZATION_CHECK": {
        "FETCHING_ENTERPRISE_DATA",
        "EXECUTING_ACTION",
        "RESOLVED",
        "FAILED",
        "ESCALATED",
    },
    "FETCHING_ENTERPRISE_DATA": {"ANALYZING_RESULTS", "AWAITING_CONFIRMATION", "ESCALATED"},
    "ANALYZING_RESULTS": {"RESOLVED", "ESCALATED"},
    "EXECUTING_ACTION": {"VERIFYING_ACTION", "ESCALATED"},
    "VERIFYING_ACTION": {"RESOLVED", "ESCALATED"},
}


class ResolutionService:
    def overview(self, session):
        """An independent authorized read; never changes an in-flight chat/action."""
        with self.store.lock:
            context = deepcopy(session)
            context["state"] = "NEW"
            trace = uid("TRACE")
            start = time.monotonic()
            self.store.emit("request.received", trace, context["id"])
            try:
                self.state(context, trace, "AUTHORIZATION_CHECK")
                self.gateway.authorize(context, context.get("accountId"), trace)
                self.state(context, trace, "FETCHING_ENTERPRISE_DATA")
                profile = self.gateway.profile(context, trace)
                account = self.gateway.account(context, trace, context["accountId"])
                self.state(context, trace, "ANALYZING_RESULTS")
                self.state(context, trace, "RESOLVED")
                self.store.emit("workflow.resolved", trace, context["id"])
                self.store.emit(
                    "request.finished", trace, context["id"], duration=(time.monotonic() - start) * 1000
                )
                return {
                    "name": profile.name,
                    "account": account.model_dump(),
                    "traceId": trace,
                    "source": "Enterprise account service",
                }
            except (Denied, IntegrationError):
                self.store.emit("workflow.failed", trace, context["id"], status="failure")
                self.store.emit(
                    "request.finished",
                    trace,
                    context["id"],
                    status="failure",
                    duration=(time.monotonic() - start) * 1000,
                )
                raise

    def __init__(self, database=None, base=None):
        self.mode = os.getenv("APP_MODE", "REVIEWER").upper()
        if self.mode not in ("REVIEWER", "LIVE_AI", "DEGRADED"):
            raise ValueError("Invalid APP_MODE")
        self.store = Store(database or os.getenv("DATABASE_PATH", "data/cx.sqlite"))
        self.gateway = Gateway(
            self.store,
            base or os.getenv("ENTERPRISE_API_BASE_URL", os.getenv("MOCK_API_BASE", "http://127.0.0.1:8090")),
            float(os.getenv("REQUEST_TIMEOUT", "2")),
            min(2, max(0, int(os.getenv("MAX_RETRIES", "1")))),
        )
        self.ai = Gemini() if self.mode == "LIVE_AI" else Reviewer()

    def login(self, data):
        t = uid("TRACE")
        anon = {"id": "anonymous"}
        self.store.emit("authentication.attempted", t, "anonymous", status="pending")
        try:
            auth = self.gateway.login(data, t, anon)
            if auth.expiresIn <= 0:
                raise IntegrationError("authentication", "expired_identity")
        except IntegrationError:
            self.store.emit("authentication.failed", t, "anonymous", status="failure")
            raise
        token = secrets.token_urlsafe(32)
        s = dict(
            id=digest(token),
            expires=time.time() + min(auth.expiresIn, 3600),
            customerId=auth.customerId,
            accountId=auth.accountId,
            roles=auth.roles,
            messages=[],
            history=[],
            completedSteps=[],
            state="NEW",
            pending=None,
            failures={},
            mode=self.mode,
        )
        self.store.save(s)
        self.store.emit("session.created", t, s["id"])
        self.store.emit("authentication.succeeded", t, s["id"])
        return token, s

    def state(self, s, t, new):
        if new not in TRANSITIONS.get(s["state"], set()):
            raise RuntimeError("invalid_transition:" + s["state"] + "->" + new)
        old = s["state"]
        s["state"] = new
        self.store.emit("workflow.transition", t, s["id"], previous=old, current=new)

    def ai_call(self, s, t, operation, data):
        provider = (
            "gemini"
            if self.mode == "LIVE_AI"
            else "reviewer"
            if self.mode == "REVIEWER"
            else "deterministic-fallback"
        )
        self.store.emit("agent.invoked", t, s["id"], component=provider, operation=operation)
        if self.mode == "DEGRADED":
            self.store.emit(
                "provider.fallback", t, s["id"], reason="configured_degraded_mode", operation=operation
            )
            s["mode"] = "DEGRADED"
            return getattr(Reviewer(), operation)(data)
        if self.mode == "REVIEWER" and s.get("failures", {}).get("gemini") != "unavailable":
            return getattr(Reviewer(), operation)(data)
        start = time.monotonic()
        try:
            if s.get("failures", {}).get("gemini") == "unavailable":
                raise TimeoutError("simulation")
            result = getattr(self.ai, operation)(data)
            self.store.emit(
                "ai.finished",
                t,
                s["id"],
                component="gemini",
                duration=(time.monotonic() - start) * 1000,
                operation=operation,
                model=os.getenv("GEMINI_MODEL", "unconfigured"),
                simulated=False,
            )
            s["mode"] = "DEGRADED" if s.get("_ai_failed") else "LIVE_AI"
            return result
        except Exception as error:
            self.store.emit(
                "ai.finished",
                t,
                s["id"],
                status="failure",
                component="gemini",
                duration=(time.monotonic() - start) * 1000,
                operation=operation,
                model=os.getenv("GEMINI_MODEL", "unconfigured"),
                reason=provider_reason(error),
                simulated=s.get("failures", {}).get("gemini") == "unavailable",
            )
            self.store.emit(
                "provider.fallback", t, s["id"], operation=operation, reason=provider_reason(error)
            )
            s["_ai_failed"] = True
            s["mode"] = "DEGRADED"
            return getattr(Reviewer(), operation)(data)

    def escalation(self, s, t, reason):
        steps = list(
            dict.fromkeys(
                s.get("completedSteps", [])
                + [
                    e["component"]
                    for e in self.store.events()
                    if e["traceId"] == t and e["eventType"] == "tool.finished" and e["status"] == "success"
                ]
            )
        )
        events = [e for e in self.store.events() if e["traceId"] == t]
        record = dict(
            escalationId=uid("ESC"),
            traceId=t,
            customerId=s["customerId"],
            requestSummary="; ".join(s["messages"][-2:]),
            completedSteps=steps,
            reason=reason,
            recommendedNextStep="Human support should inspect verified facts and integration status; reconcile uncertain actions before retrying.",
            pendingAction=s.get("pending"),
            facts=s.get("facts", []),
            verifiedContext={
                "accountId": s.get("accountId"),
                "identitySource": "synthetic-authentication-service",
            },
            failedTools=[
                {"component": e["component"], "reason": e["metadata"].get("reason", "integration_failure")}
                for e in events
                if e["eventType"] == "tool.finished" and e["status"] == "failure"
            ],
        )
        self.store.escalate(s["id"], record)
        self.state(s, t, "ESCALATED")
        self.store.emit("workflow.escalated", t, s["id"])
        return {
            "answer": "This request needs human review. No new successful action is claimed. Handoff "
            + record["escalationId"],
            "escalationId": record["escalationId"],
        }

    def finish(self, s, t, start, result, failed=False):
        s["completedSteps"] = list(
            dict.fromkeys(
                s.get("completedSteps", [])
                + [
                    e["component"]
                    for e in self.store.events()
                    if e["traceId"] == t and e["eventType"] == "tool.finished" and e["status"] == "success"
                ]
            )
        )
        s.setdefault("history", []).append({"role": "assistant", "text": result["answer"], "traceId": t})
        s["history"] = s["history"][-40:]
        self.store.save(s)
        if failed:
            self.store.emit("workflow.failed", t, s["id"], status="failure", finalState=s["state"])
        self.store.emit(
            "request.finished",
            t,
            s["id"],
            status="failure" if failed else "success",
            duration=(time.monotonic() - start) * 1000,
        )
        return deepcopy(dict(traceId=t, state=s["state"], mode=s["mode"], facts=s.get("facts", []), **result))

    def internal_failure(self, s, t, start):
        self.store.emit(
            "processing.failed", t, s["id"], status="failure", reason="internal_processing_failure"
        )
        if s.get("pending", {}) and s["pending"]["status"] == "executing":
            s["pending"]["status"] = "uncertain"
        return self.finish(s, t, start, self.escalation(s, t, "internal_processing_failure"), True)

    def chat(self, s, data):
        with self.store.lock:
            t = uid("TRACE")
            start = time.monotonic()
            self.store.emit("request.received", t, s["id"])
            previous = s["state"]
            s["state"] = "NEW"
            s["facts"] = []
            s["_ai_failed"] = False
            if previous != "NEEDS_CLARIFICATION":
                s["completedSteps"] = []
            message = redact(data.message)
            s.setdefault("history", []).append({"role": "user", "text": message})
            s["messages"] = (s["messages"][-3:] if previous == "NEEDS_CLARIFICATION" else []) + [message]
            self.state(s, t, "INTERPRETING")
            try:
                refs = re.findall(r"\bACC-\d+\b", data.message.upper())
                for account in refs + ([data.accountId] if data.accountId else []):
                    self.gateway.authorize(s, account, t)
                decision = self.ai_call(s, t, "interpret", s["messages"])
                intent = decision.intent
                self.store.emit(
                    "intent.classified",
                    t,
                    s["id"],
                    intent=intent,
                    service=decision.service,
                    confidence=decision.confidence,
                    mode=s["mode"],
                )
                if intent == "unknown" or (intent == "network" and decision.service == "unknown"):
                    self.state(s, t, "NEEDS_CLARIFICATION")
                    self.store.emit(
                        "clarification.requested",
                        t,
                        s["id"],
                        status="pending",
                        missingInformation="service_type"
                        if intent == "network"
                        else "supported_request_intent",
                    )
                    return self.finish(
                        s,
                        t,
                        start,
                        {
                            "answer": "Which service is affected: home internet or mobile?"
                            if intent == "network"
                            else "Do you need plan information, billing, network diagnostics, subscriber status, or a support case?"
                        },
                    )
                if intent == "handoff":
                    return self.finish(s, t, start, self.escalation(s, t, "customer_requested_handoff"))
                self.state(s, t, "AUTHORIZATION_CHECK")
                account = data.accountId or s.get("accountId")
                self.gateway.authorize(s, account, t)
                self.state(s, t, "FETCHING_ENTERPRISE_DATA")
                p = self.gateway.profile(s, t)
                a = self.gateway.account(s, t, account)
                facts = s["facts"]
                if intent == "case":
                    existing = s.get("pending") or {}
                    if (
                        existing.get("status") == "completed"
                        and existing.get("summary") == message
                        and time.time() - existing["created"] < 600
                    ):
                        self.state(s, t, "ANALYZING_RESULTS")
                        self.state(s, t, "RESOLVED")
                        self.store.emit("action.replayed", t, s["id"], caseId=existing["caseId"])
                        return self.finish(
                            s,
                            t,
                            start,
                            {
                                "answer": "This request was already completed. Case " + existing["caseId"],
                                "caseId": existing["caseId"],
                            },
                        )
                    if s.get("pending") and s["pending"]["status"] in ("pending", "executing", "uncertain"):
                        action = s["pending"]
                    else:
                        action = dict(
                            id=uid("ACT"),
                            summary=message,
                            accountId=account,
                            status="pending",
                            created=time.time(),
                        )
                        s["pending"] = action
                    if action["status"] in ("executing", "uncertain"):
                        return self.finish(
                            s, t, start, self.escalation(s, t, "prior_action_requires_reconciliation")
                        )
                    self.state(s, t, "AWAITING_CONFIRMATION")
                    self.store.emit("action.proposed", t, s["id"], status="pending", actionId=action["id"])
                    self.store.emit(
                        "confirmation.requested", t, s["id"], status="pending", actionId=action["id"]
                    )
                    return self.finish(
                        s,
                        t,
                        start,
                        {
                            "answer": "Confirm creation of one support case for your account: "
                            + action["summary"],
                            "pendingAction": action,
                        },
                    )
                if intent == "account":
                    facts.append(
                        "Account service: your plan is "
                        + a.plan.name
                        + "; monthly plan price "
                        + format(a.plan.monthlyPrice, ".2f")
                        + "; account status "
                        + a.status
                        + "."
                    )
                elif intent == "billing":
                    b = self.gateway.billing(s, t, account)
                    facts.append(f"Billing service: {b.period} total {b.total:.2f}.")
                    facts.extend(f"Billing item: {i.description}: {i.amount:.2f}." for i in b.items)
                else:
                    service = next((x for x in a.services if decision.service in ("unknown", x.type)), None)
                    if not service:
                        raise IntegrationError("account-service", "service_not_owned")
                    if intent == "network":
                        o = self.gateway.network(s, t, p)
                        d = self.gateway.diagnostics(s, t, service.serviceId)
                        facts.append(
                            "Network service reports "
                            + o.status
                            + "; incident "
                            + str(o.incidentId or "none")
                            + "."
                        )
                        if o.estimatedRestoration:
                            facts.append(
                                "Source restoration estimate (may be stale): " + o.estimatedRestoration + "."
                            )
                        facts.append("Diagnostics: " + d.result + ".")
                    legacy = self.gateway.legacy(s, t, service.serviceId)
                    facts.append(
                        "Legacy XML: subscriber "
                        + legacy["subscriberStatus"]
                        + "; network "
                        + legacy["networkStatus"]
                        + "; observed "
                        + legacy["observedAt"]
                        + "."
                    )
                    if intent == "network" and (
                        o.status == "unknown"
                        or (o.status == "normal") != (legacy["networkStatus"] == "normal")
                    ):
                        return self.finish(
                            s, t, start, self.escalation(s, t, "conflicting_or_unknown_network_status")
                        )
                self.state(s, t, "ANALYZING_RESULTS")
                order = self.ai_call(s, t, "select", facts)
                answer = " ".join(facts[i] for i in order)
                self.state(s, t, "RESOLVED")
                self.store.emit("workflow.resolved", t, s["id"])
                return self.finish(s, t, start, {"answer": answer})
            except Denied:
                s["state"] = "FAILED"
                return self.finish(s, t, start, {"answer": "Account access denied."}, True)
            except IntegrationError as error:
                return self.finish(
                    s, t, start, self.escalation(s, t, error.service + ":" + error.reason), True
                )
            except Exception:
                return self.internal_failure(s, t, start)

    def confirm(self, s, data):
        with self.store.lock:
            t = uid("TRACE")
            start = time.monotonic()
            self.store.emit("request.received", t, s["id"])
            s["state"] = "NEW"
            s["facts"] = []
            self.state(s, t, "AUTHORIZATION_CHECK")
            try:
                self.gateway.authorize(s, s.get("accountId"), t)
            except Denied:
                s["state"] = "FAILED"
                return self.finish(s, t, start, {"answer": "Account access denied."}, True)
            action = s.get("pending")
            durable = self.store.session_by_id(s["id"])
            durable_action = (durable or {}).get("pending") or {}
            if durable_action.get("id") == data.actionId and durable_action.get("status") != "pending":
                s["pending"] = deepcopy(durable_action)
                action = s["pending"]
            if not action or action["id"] != data.actionId:
                self.store.emit(
                    "confirmation.rejected", t, s["id"], status="denied", reason="action_mismatch"
                )
                s["state"] = "FAILED"
                return self.finish(
                    s, t, start, {"answer": "Confirmation does not match a pending action."}, True
                )
            self.store.emit(
                "confirmation.received",
                t,
                s["id"],
                actionId=action["id"],
                confirmed=data.confirm,
                replay=action["status"] == "completed",
            )
            if action["status"] == "completed":
                self.state(s, t, "RESOLVED")
                return self.finish(
                    s,
                    t,
                    start,
                    {
                        "answer": "This action was already completed. Case " + action["caseId"],
                        "caseId": action["caseId"],
                    },
                )
            if action["status"] != "pending" or time.time() - action["created"] > 600:
                s["state"] = "FAILED"
                return self.finish(
                    s,
                    t,
                    start,
                    {
                        "answer": "This action cannot be retried. Request human reconciliation or a new proposal."
                    },
                    True,
                )
            if not data.confirm:
                action["status"] = "cancelled"
                self.state(s, t, "RESOLVED")
                self.store.emit("action.cancelled", t, s["id"])
                return self.finish(s, t, start, {"answer": "Case creation cancelled. No case was submitted."})
            self.state(s, t, "EXECUTING_ACTION")
            action["status"] = "executing"
            action["confirmedAt"] = time.time()
            self.store.save(s)
            try:
                c = self.gateway.create_case(s, t, action)
                self.state(s, t, "VERIFYING_ACTION")
                action.update(status="completed", caseId=c.caseId)
                self.state(s, t, "RESOLVED")
                self.store.emit("workflow.resolved", t, s["id"])
                self.store.emit("action.completed", t, s["id"], caseId=c.caseId)
                return self.finish(
                    s, t, start, {"answer": "Support case " + c.caseId + " is open.", "caseId": c.caseId}
                )
            except IntegrationError as error:
                action["status"] = "uncertain"
                return self.finish(
                    s, t, start, self.escalation(s, t, error.service + ":" + error.reason), True
                )
            except Exception:
                return self.internal_failure(s, t, start)
