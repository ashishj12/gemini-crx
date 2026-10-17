"""Executable assertions against the same application and real mock HTTP adapters."""

import json
from relay_api.domain.models import Chat, Confirmation

from relay_api.core.config import CHALLENGE_ROOT

ROOT = CHALLENGE_ROOT


def run_scenario(app, scenario):
    if scenario not in [f"SCN-{i:03}" for i in range(1, 9)]:
        raise ValueError("unknown_scenario")
    spec = json.loads((ROOT / "scenarios" / f"{scenario}.json").read_text())
    start_index = len(app.store.events())
    _, s = app.login({"username": "alex.morgan", "password": "ReviewerPass-1001"})
    results = []
    checks = {}

    def chat(message, **kwargs):
        r = app.chat(s, Chat(message=message, **kwargs))
        results.append(r)
        return r

    if scenario == "SCN-001":
        r = chat(spec["request"])
        checks["grounded_plan"] = (
            r["state"] == "RESOLVED" and "Fiber 500" in r["answer"] and "Account service" in r["answer"]
        )
    elif scenario == "SCN-002":
        r = chat(spec["request"])
        checks["clarification"] = r["state"] == "NEEDS_CLARIFICATION" and not r["facts"]
        r = chat("home internet")
        checks["resumed"] = r["state"] == "RESOLVED" and "Legacy XML" in r["answer"]
    elif scenario == "SCN-003":
        r = chat(spec["request"])
        events = app.store.events()
        used = {
            e["component"]
            for e in events
            if e["traceId"] == r["traceId"] and e["eventType"] == "tool.finished"
        }
        checks["multi_system"] = set(spec["expectedTools"]).issubset(used) and r["state"] in (
            "RESOLVED",
            "ESCALATED",
        )
    elif scenario in ("SCN-004", "SCN-007"):
        if scenario == "SCN-007":
            s["failures"] = {"case": "unavailable"}
        r = chat("Create a support case for my internet issue.")
        checks["confirmation_required"] = r["state"] == "AWAITING_CONFIRMATION" and "caseId" not in r
        r = app.confirm(s, Confirmation(actionId=r["pendingAction"]["id"], confirm=True))
        results.append(r)
        checks["proposal_snapshot"] = results[0]["pendingAction"]["status"] == "pending"
        if scenario == "SCN-007":
            checks["safe_failure"] = r["state"] == "ESCALATED" and "caseId" not in r
        else:
            checks["verified_case"] = r["state"] == "RESOLVED" and r.get("caseId", "").startswith("CASE-")
            duplicate = app.confirm(s, Confirmation(actionId=s["pending"]["id"], confirm=True))
            results.append(duplicate)
            checks["duplicate_prevented"] = duplicate.get("caseId") == r.get("caseId")
    elif scenario == "SCN-005":
        r = chat("Show account ACC-2002", accountId=spec["requestedAccount"])
        checks["denied_before_read"] = (
            r["state"] == "FAILED"
            and not r["facts"]
            and not any(
                e["eventType"] == "tool.finished" and e["traceId"] == r["traceId"] for e in app.store.events()
            )
        )
    elif scenario == "SCN-006":
        r = chat("Check my legacy subscriber status")
        checks["xml_normalized"] = r["state"] == "RESOLVED" and "subscriber active" in r["answer"]
    elif scenario == "SCN-008":
        s["failures"] = {"gemini": "unavailable"}
        r = chat("What is my plan?")
        checks["degraded_grounded"] = r["mode"] == "DEGRADED" and "Fiber 500" in r["answer"]
        checks["provider_failure_event"] = any(
            e["traceId"] == r["traceId"] and e["eventType"] == "ai.finished" and e["status"] == "failure"
            for e in app.store.events()
        )
    traces = [r["traceId"] for r in results]
    events = app.store.events()[start_index:]
    own = [e for e in events if e["sessionId"] == s["id"]]

    def check(name, condition):
        checks[name] = bool(condition)

    check(
        "authenticated_initial_identity",
        s["customerId"] == spec.get("authenticatedUser", "CUST-1001")
        and s["accountId"] == "ACC-2001"
        and "customer" in s["roles"],
    )
    check(
        "real_authentication_service",
        any(
            e["eventType"] == "tool.finished"
            and e["component"] == "authentication"
            and e["status"] == "success"
            for e in events
        ),
    )
    check("authentication_success_event", any(e["eventType"] == "authentication.succeeded" for e in own))
    check(
        "all_requests_traced",
        all(
            sum(e["eventType"] == "request.received" and e["traceId"] == t for e in own) == 1
            and sum(e["eventType"] == "request.finished" and e["traceId"] == t for e in own) == 1
            for t in traces
        ),
    )
    check(
        "customer_record_isolation",
        not any("Mobile Unlimited" in json.dumps(r) or "CUST-1002" in json.dumps(r) for r in results),
    )
    check(
        "no_unconfirmed_case_calls",
        not any(
            e["component"] == "case-management"
            and e["eventType"] == "tool.invoked"
            and e["traceId"] == results[0]["traceId"]
            for e in own
        ),
    )

    def trace_events(index):
        return [e for e in own if e["traceId"] == results[index]["traceId"]]

    def calls(index):
        return [e["component"] for e in trace_events(index) if e["eventType"] == "tool.invoked"]

    def types(index):
        return [e["eventType"] for e in trace_events(index)]

    def transitions(index):
        return [
            e["metadata"]["current"] for e in trace_events(index) if e["eventType"] == "workflow.transition"
        ]

    for index, result in enumerate(results):
        check(
            f"final_state_{index}",
            result["state"]
            in ("RESOLVED", "ESCALATED", "FAILED", "NEEDS_CLARIFICATION", "AWAITING_CONFIRMATION"),
        )
        check(
            f"matching_terminal_state_{index}",
            not transitions(index)
            or transitions(index)[-1] == result["state"]
            or result["state"] == "FAILED",
        )
        tools = [e for e in trace_events(index) if e["eventType"] == "tool.finished"]
        check(f"called_tools_have_results_{index}", len(calls(index)) == len(tools))
        check(
            f"no_protected_call_before_authorization_{index}",
            all(
                any(
                    a["eventType"] == "authorization.allowed"
                    for a in trace_events(index)[: trace_events(index).index(e)]
                )
                for e in trace_events(index)
                if e["eventType"] == "tool.invoked"
            ),
        )
    if scenario in ("SCN-001", "SCN-003", "SCN-006", "SCN-008"):
        check("read_only_no_case", all("case-management" not in calls(i) for i in range(len(results))))
        check(
            "grounded_source_fact_evidence",
            bool(results[-1]["facts"])
            and all(fact in results[-1]["answer"] for fact in results[-1]["facts"]),
        )
        check(
            "required_read_transitions",
            all(
                state in transitions(0)
                for state in (
                    "INTERPRETING",
                    "AUTHORIZATION_CHECK",
                    "FETCHING_ENTERPRISE_DATA",
                    "ANALYZING_RESULTS",
                    "RESOLVED",
                )
            ),
        )
        check("verified_profile_and_account", {"customer-profile", "account-service"}.issubset(calls(0)))
    if scenario == "SCN-001":
        expected = json.loads((ROOT / "sample-data/accounts.json").read_text())["accounts"][0]["plan"]
        check(
            "exact_enterprise_plan",
            expected["name"] in results[0]["answer"]
            and f"{expected['monthlyPrice']:.2f}" in results[0]["answer"],
        )
        check(
            "forbidden_inquiry_calls",
            not set(calls(0))
            & {"billing", "network-outage", "diagnostics", "legacy-subscriber-status", "case-management"},
        )
    if scenario == "SCN-002":
        check("no_premature_protected_calls", not calls(0) and not results[0]["facts"])
        check(
            "specific_question_event",
            "clarification.requested" in types(0) and "home internet or mobile" in results[0]["answer"],
        )
        check(
            "original_request_retained", spec["request"] in s["messages"] and "home internet" in s["messages"]
        )
        check(
            "resume_real_services",
            {
                "customer-profile",
                "account-service",
                "network-outage",
                "diagnostics",
                "legacy-subscriber-status",
            }.issubset(calls(1)),
        )
        check("no_unrequested_action", "case-management" not in calls(1))
    if scenario == "SCN-003":
        check(
            "all_required_services",
            set(spec["expectedTools"]).issubset(calls(0)) and "diagnostics" in calls(0),
        )
        check(
            "enterprise_evidence_reconciled",
            "INC-9001" in results[0]["answer"]
            and "degraded" in results[0]["answer"]
            and "subscriber active" in results[0]["answer"],
        )
    if scenario in ("SCN-004", "SCN-007"):
        check(
            "proposal_confirmation_events",
            "confirmation.requested" in types(0) and "action.proposed" in types(0),
        )
        check(
            "explicit_confirmation_before_call",
            "confirmation.received" in types(1)
            and types(1).index("confirmation.received") < types(1).index("tool.invoked"),
        )
        check(
            "one_consequential_call",
            sum(e["eventType"] == "tool.invoked" and e["component"] == "case-management" for e in own) == 1,
        )
        check(
            "durable_action_state",
            app.store.session_by_id(s["id"])["pending"]["status"]
            == ("completed" if scenario == "SCN-004" else "uncertain"),
        )
        check(
            "no_unsafe_case_retry",
            not any(e["eventType"] == "tool.retry" and e["component"] == "case-management" for e in own),
        )
        if scenario == "SCN-004":
            check(
                "execution_verified_transitions",
                transitions(1) == ["AUTHORIZATION_CHECK", "EXECUTING_ACTION", "VERIFYING_ACTION", "RESOLVED"],
            )
            check(
                "real_case_completion_event",
                "action.completed" in types(1) and results[1]["caseId"] == s["pending"]["caseId"],
            )
            check("replay_no_tool", not calls(2) and "confirmation.received" in types(2))
        else:
            failed = [
                e
                for e in trace_events(1)
                if e["eventType"] == "tool.finished" and e["component"] == "case-management"
            ]
            check(
                "actual_http_503",
                len(failed) == 1
                and failed[0]["status"] == "failure"
                and failed[0]["metadata"]["reason"] == "http_503",
            )
            handoffs = [r for _, r in app.store.escalations() if r["traceId"] == results[1]["traceId"]]
            check(
                "actionable_handoff",
                bool(handoffs)
                and bool(handoffs[0]["completedSteps"])
                and bool(handoffs[0]["failedTools"])
                and handoffs[0]["pendingAction"]["status"] == "uncertain",
            )
            check(
                "failure_terminal_events",
                "workflow.failed" in types(1)
                and "workflow.escalated" in types(1)
                and "workflow.resolved" not in types(1),
            )
    if scenario == "SCN-005":
        check("no_foreign_retrieval", not calls(0))
        check("denial_audited", "authorization.denied" in types(0) and "workflow.failed" in types(0))
        check(
            "no_success_or_case",
            "workflow.resolved" not in types(0) and not results[0]["facts"] and "caseId" not in results[0],
        )
    if scenario == "SCN-006":
        normalized = [
            e
            for e in trace_events(0)
            if e["component"] == "legacy-subscriber-status" and e["eventType"] == "tool.finished"
        ]
        check(
            "xml_normalization_audited",
            bool(normalized) and normalized[0]["metadata"]["outputSummary"]["validated"],
        )
        check("no_raw_xml_leak", "<SubscriberStatus" not in json.dumps(results))
    if scenario == "SCN-008":
        ai = [e for e in trace_events(0) if e["eventType"] == "ai.finished"]
        check(
            "no_fake_live_success",
            bool(ai) and all(e["status"] == "failure" and e["metadata"]["simulated"] for e in ai),
        )
        check("fallback_event", "provider.fallback" in types(0) and "authorization.allowed" in types(0))
        check("request_preserved", s["messages"] == ["What is my plan?"])
    return dict(
        scenarioId=scenario,
        title=spec["title"],
        status="PASS" if checks and all(checks.values()) else "FAIL",
        checks=checks,
        initialConditions={"customerId": s["customerId"], "accountId": s["accountId"], "mode": app.mode},
        inputs=spec,
        command="python tools/evaluate.py --mode REVIEWER",
        results=results,
        traceIds=traces,
        events=events,
        escalations=[r for _, r in app.store.escalations() if r["traceId"] in traces],
    )
