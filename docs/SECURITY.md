# Security

The trust boundary is the backend, never the model or browser. Synthetic authentication is performed against the supplied login API and its response is validated. A random token is sent only in an HttpOnly, SameSite=Strict cookie; SHA-256 of the token indexes server-side state. The original upstream accessToken is never persisted or sent to Gemini. Sessions expire at the upstream lifetime capped at one hour. Logout expires the row and removes the cookie. Reauthentication generates a fresh token.

Protected tools enforce unexpired customer-role sessions and exact account binding before record retrieval, then verify returned identities. Legacy and diagnostic service IDs must belong to the session account. Customer-supplied account references are checked before AI interpretation; model schemas cannot propose arbitrary IDs or URLs. No direct endpoint offers arbitrary enterprise retrieval. Trace visibility is restricted to the owning session or support-agent role. Operations data and scenario execution require the support-agent role; that role alone cannot perform customer actions.

Login attempts are capped at 30 per source IP per minute in the application process. Browser writes require JSON; mismatched Origin is rejected. SameSite cookies, no permissive CORS, origin validation, no-store, nosniff, frame blocking and React-escaped output limit browser attacks. In production configure PUBLIC_ORIGIN and COOKIE_SECURE=true behind TLS. No cookie signing secret is needed for opaque sessions. Expose only the Next.js gateway behind a TLS ingress; keep API and fixtures private.

## Confirmation and idempotency

An action proposal stores a random ACT identifier, authenticated account, redacted summary, timestamp and pending status. Only `/api/confirm` with a matching action ID and a strict boolean can execute it; chat text such as “yes” never submits a case. Authorization is checked again at execution. Proposals expire after ten minutes; cancellation prevents later submission. The executing marker is committed before the external POST, and completed case ID/status is committed afterward. A repeated or concurrent confirmation returns the recorded case ID without another POST. The case service receives the same action identifier as its idempotency key.

Transport errors or malformed responses after submission are ambiguous. Mark the action uncertain and escalate; do not automatically retry. Restart while executing is also blocked. The supplied service stores keys in RAM, so durability across mock restarts is limited. There is no case lookup endpoint; an agent must reconcile an uncertain action out of band before proposing another action. Do not clear the database to “fix” an uncertain state.

## Threat model and evidence

| Threat | Control | Regression evidence |
|---|---|---|
| Unauthenticated access | Cookie/session gate | test_http_auth_and_roles |
| Cross-customer record read | Pre-fetch account binding and returned identity | test_tool_guard_before_network; test_trace_isolation; SCN-005 |
| Model ownership claim | Strict schema, no model tools | test_invalid_gemini_output; test_prompt_injection_cannot_change_identity |
| Embedded enterprise instructions | Treat all input as data, deterministic rendering | provider system instruction; fact selection tests |
| Replayed/concurrent action | Durable action states, lock, idempotency key | test_duplicate_concurrent_and_restart |
| Confirmation bypass | Dedicated strict action-confirmation API | test_confirm_binding_decline_and_no_chat_bypass |
| Malicious XML / DTD / entity | UTF-8-only bounded parser; reject declarations and duplicate/missing fields | test_legacy_bad_xml |
| Failure falsely reported successful | Validated results and explicit escalation | test_real_service_failure; SCN-007 |
| Secret leakage | Discard credentials; redaction; no request-body logging | test_event_schema_metrics_redaction |

## Remaining production controls

The synthetic APIs do not enforce tokens themselves. Local binding and Compose internal networking are essential. Replace them with authenticated private enterprise APIs and service IAM/mTLS before deployment. The configured enterprise origin is trusted operator configuration; no model or client may change it. Sensitive history and handoffs are stored in a local SQLite file and restricted by filesystem access, not application encryption. Add encryption-at-rest policy, retention, purge, backup access controls, and audit export. Pattern redaction is intentionally bounded and cannot recognize every possible secret a customer pastes; use enterprise DLP/minimization for real customers. Browser-rendered history is accessible to anyone who steals a live session cookie; TLS and device/session controls remain necessary.

SQLite plus the process lock supports one process only. Add transactional shared action claims and durable backend idempotency before horizontal scaling. Request/IP limits are process-local and no WAF, full abuse controls, SSO/OIDC, upstream credential rotation or penetration testing is supplied. Human support uses a coarse global support-agent role in synthetic evaluation; production needs scoped queues, consent and least-privilege agent access. The integration suite uses controlled doubles; current live evidence records genuine inference separately. Comprehensive adversarial live-model evaluation remains future work.
