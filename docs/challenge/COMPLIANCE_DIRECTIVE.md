# FINAL TOPCODER COMPLIANCE AND QUALIFICATION DIRECTIVE

The following instructions override any weaker or conflicting instructions elsewhere in this master prompt.

## 1. Source-of-truth enforcement

The actual challenge specification, supplied scenario files, scoring documents, API contracts, and starter repository are authoritative.

Do not assume the master prompt perfectly captures every scenario detail.

Extract every mandatory requirement and every scenario assertion directly from those resources before implementation.

If the master prompt conflicts with the supplied resources, follow the supplied resources.

## 2. Complete requirement traceability

Create a requirement-to-evidence matrix before implementation and maintain it throughout development.

For every requirement, record:

- Original requirement wording or reference.
- Implementation location.
- Supporting automated test.
- Applicable mandatory scenario.
- Execution evidence.
- Current status.
- Remaining limitation.

No requirement may be marked complete merely because a source file or documentation section exists.

## 3. Qualification gates

Read the actual qualification and scoring files.

Enforce all mandatory qualification gates, including any minimum overall score, category-specific minimums, mandatory scenario completion, reproducibility conditions, and disqualifying security or implementation failures.

A passing test count alone does not prove qualification.

Do not invent an estimated qualification score. Any scoring assessment must be grounded in the supplied rubric and verifiable evidence.

## 4. Scenario-driven acceptance testing

Read all eight supplied scenario fixtures.

For every scenario, implement explicit executable assertions for:

- Initial conditions.
- Customer identity and ownership.
- User inputs.
- Expected workflow transitions.
- Required enterprise API calls.
- Forbidden API calls.
- Required confirmation.
- Expected response data.
- Failure behavior.
- Trace and telemetry events.
- Final resolution or escalation status.

Include negative tests proving forbidden behavior did not occur.

Run all scenarios against the actual application workflow and supplied mock services.

## 5. End-to-end evidence

Provide reproducible evidence for every mandatory scenario.

Evidence should include where relevant:

- Scenario identifier.
- Test command.
- Test result.
- Trace ID.
- Workflow events.
- Invoked tools.
- Verified enterprise responses.
- Authorization decisions.
- Confirmation events.
- Backend action references.
- Failure and escalation records.

The evidence must originate from actual execution, not manually fabricated JSON or screenshots.

## 6. Reviewer-mode integrity

Reviewer mode may simulate Gemini interpretation, but it must not replace the actual business logic with predetermined final responses.

Use the same:

- Authentication and authorization implementation.
- Workflow orchestration.
- Tool gateways.
- Enterprise adapters.
- Legacy XML handling.
- Action confirmation.
- Idempotency logic.
- Failure handling.
- Event pipeline.
- Trace generation.

Clearly label Live AI, Reviewer, and Degraded modes.

Prove that reviewer mode runs without requiring paid model access.

## 7. Persisted workflow and action safety

Persist essential workflow state, including pending confirmations, action status, and escalation context.

Ensure that client refreshes, duplicate submissions, retries, and interrupted workflows do not cause unauthorized or duplicate consequential actions.

Where the mock backend cannot guarantee idempotency, implement the strongest feasible application-level safeguard and document its limitations.

## 8. Actual Gemini verification

Document every Gemini invocation:

- Model identifier.
- Purpose.
- Input context.
- Prompt instructions.
- Expected structured output.
- Validation.
- Safety restrictions.
- Error handling.
- Relevant telemetry.

Test the live integration with real credentials when available.

If credentials are unavailable, distinguish implemented-but-unverified live functionality from successfully tested reviewer functionality.

Never claim live Gemini execution occurred without genuine evidence.

## 9. Production-readiness honesty

Deliver a deployment-ready proof of capability appropriate to the challenge.

Do not misrepresent synthetic authentication, mock telecom services, local persistence, or deployment documentation as a fully certified production telecommunications platform.

Clearly distinguish:

- Implemented and tested locally.
- Verified through mock enterprise services.
- Verified with live Gemini.
- Deployment configuration prepared.
- Actually deployed to Google Cloud.
- Recommended future production enhancements.

## 10. Final compliance audit

After completing the implementation:

1. Reread the original challenge specification.
2. Reread every mandatory scenario.
3. Reread the scoring and qualification documents.
4. Compare each requirement to executable evidence.
5. Execute the full automated test suite.
6. Run all eight scenarios.
7. Verify security regression tests.
8. Verify telemetry and trace completeness.
9. Verify documented startup from a clean environment.
10. Check the final deliverables against the challenge's exact submission requirements.

Create `docs/FINAL_COMPLIANCE_AUDIT.md` containing a complete checklist with PASS, FAIL, BLOCKED, or NOT TESTED for every requirement.

Do not declare the challenge fully completed if any mandatory qualification gate remains unverified or failed.

Fix all feasible failures before finalizing the submission.

**The final objective is not merely to generate a large amount of code. It is to deliver a working, secure, reproducible solution whose behavior and evidence satisfy the original Topcoder challenge requirements.**