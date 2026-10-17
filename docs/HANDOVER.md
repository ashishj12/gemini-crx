# Handover

Relay resolves synthetic telecom requests by combining authenticated customer records, billing, outages, read-only diagnostics and legacy subscriber evidence. Support-case creation is the supported consequential operation. The supplied archive's scenarios and fixture records are retained to make review reproducible.

## Decisions and extension points

The Python business workflow is now a modular src package served by FastAPI/Uvicorn; Next.js/TypeScript and Bun provide the UI. Pydantic handles boundaries; stdlib HTTP handles the fixed enterprise API; SQLite makes local state/action/trace persistence reproducible. One orchestrator is sufficient; no autonomous multi-agent system was added. Gemini adds structured language interpretation and verified fact ordering, while security and actions remain deterministic. Restricting synthesis to fact IDs trades freer phrasing for strong customer-specific grounding.

To add an enterprise tool, add response models in `domain/models.py`, a fixed-path method in `infrastructure/enterprise.py`, deterministic identity/permission checks and a bounded retry policy. Classify read-only POSTs explicitly; never allow arbitrary method/URL/body through chat. Add actual mock-service integration tests and malformed/identity mismatch tests. Update contract documentation and evidence matrix.

To add a workflow, extend the strict Interpretation intent enum and provider prompt/reviewer routing, then add a fixed orchestration branch. Define transitions, required facts and failure/handoff behavior. Actions need proposal state, exact confirmation binding, reauthorization, durable execution claims, response identity verification and duplicate/uncertain-outcome tests. Review TRANSITIONS when changing state paths.

Update Gemini system instructions and structured response models together in `ai/providers.py`. Inputs are data, never instructions. Keep identifiers, credentials and tool URLs out of the model output contract. Test invalid/extra fields, empty replies, wrong fact permutations, provider errors and partial-stage fallback. Add live evals only when credentials are deliberately supplied; do not transform doubled success into evidence of live inference.

## Debugging and operations

Sign in as support.agent, inspect Operations, choose a trace and compare request.received, workflow transitions, authorization, tool.finished/retry, ai.finished and request.finished. Tool metadata reports a sanitized error class. Query `/api/ops/escalations` for completed steps, reason, facts and pending-action state. Customer traces remain session scoped. Metrics use the same persisted events and documented denominators; they are not hardcoded dashboard values.

Failure environments: MOCK_AUTH_MODE=expired|unavailable; MOCK_BILLING_MODE=malformed|unavailable|timeout; MOCK_LEGACY_MODE=malformed|unavailable|timeout; MOCK_CASE_MODE=unavailable. Restart only the mock to apply environment changes. The reviewer runner uses per-session headers, enabled explicitly by MOCK_ALLOW_FAILURES=true, so parallel reviewer runs do not mutate global failure modes. Gemini injection is an explicit provider-failure simulation recorded as such. UI clears only results, not state/evidence.

Run all regression tests from repository root. They start isolated real HTTP services on ephemeral ports, use temporary databases and write current scenario/JUnit artifacts. The HTTP smoke runner additionally verifies the public reviewer/ops API. Tests requiring localhost may need host permission in a restricted agent sandbox; this is an environment restriction, not a reason to replace HTTP calls with fake business results.

## Remaining roadmap

1. Monitor live provider availability and review the genuine execution evidence before qualification.
2. Run Docker/Compose in a working daemon, perform a clean install and image vulnerability review.
3. Migrate SQLite to a durable transactional shared store and implement multi-instance action claims.
4. Replace synthetic authentication/downstream services with private IAM-protected enterprise APIs and OIDC/SSO.
5. Add queue-scoped agent access, external handoff delivery, enterprise DLP, retention and encrypted backups.
6. Export structured events/spans to Cloud Logging/Monitoring/Trace, add token accounting and alerts.
7. Harden ingress, deadlines, request concurrency, graceful draining, load/chaos testing and incident runbooks.

Known source limitations: historical outage estimates; only one successful legacy subscriber fixture; in-memory mock case keys; no case lookup API. These cannot be interpreted as real-world outage predictions or durable backend guarantees. The demo video is excluded by the latest user request.
