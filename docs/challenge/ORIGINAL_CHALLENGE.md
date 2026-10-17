Topcoder is seeking production-grade solutions for an Enterprise AI Customer Experience Resolution System built on Google Cloud Platform (GCP) and Gemini Customer Experience (Gemini CX) architecture.

In this challenge, you will act as a Lead Forward Deployed Engineer (FDE). You will design, build, and deploy an end-to-end, multi-agent AI customer support resolution engine for a major Telecommunications / Communications Service Provider (CSP). The system must securely integrate with legacy backend services (Billing, Network Diagnostics, Account Auth), feature robust multi-agent orchestration, implement enterprise-grade security protocols, and provide complete observability and telemetry.

Objective: Build a proof-of-concept (PoC) enterprise agentic solution capable of autonomously handling complex customer scenarios—such as authenticating a subscriber, running broadband hardware diagnostics, resolving billing disputes, or performing automated escalation—using Gemini CX / Google Cloud AI frameworks.

Challenge Goal
Complete and productionize the supplied AI customer-experience solution so that it can:

Understand customer requests using Gemini
Ask relevant clarification questions
Manage conversation and workflow context
Coordinate agents, workflows, and enterprise tools
Authenticate customers before accessing protected information
Enforce authorization outside the AI model
Integrate with modern and legacy enterprise systems
Produce responses grounded in verified enterprise data
Perform supported actions only after validation and confirmation
Handle AI and enterprise-service failures safely
Escalate unresolved requests with useful context
Generate structured logs, traces, events, and operational metrics
Support repeatable automated evaluation
Provide a credible Google Cloud deployment approach
Enable another engineering team to understand and extend the solution
The productionized solution is the practical evidence used to validate and rank competitors. Building the solution is not the final business outcome of the challenge.

Challenge Type
AI Exponential League Practical Qualification and Productionization Challenge

This challenge combines:

Existing codebase analysis
Gemini integration
Conversational AI
Agentic architecture
Workflow and tool orchestration
Secure API implementation
Authentication and authorization
Enterprise integration
Legacy-system adaptation
Data pipelines
Telemetry and observability
Reliability engineering
Automated testing
Google Cloud deployment planning
Technical handover
Participants may use:

A single controlled AI agent
Multiple specialized agents
Deterministic workflow orchestration
A hybrid AI and rules-based architecture
Google-supported agent frameworks
A custom implementation
Framework choice alone will not determine the score.

Participants must improve the supplied starter solution rather than replace it with an unrelated implementation.

Business Scenario
A telecommunications provider uses separate enterprise systems for:

Customer identity
Customer profiles
Accounts and subscriptions
Billing information
Product and service eligibility
Network and service status
Technical diagnostics
Support-case management
The provider has started developing an AI-powered customer-experience solution, but the current implementation is not ready for production.

The supplied solution contains gaps such as:

Incomplete Gemini integration
Weak or incomplete agent orchestration
Stubbed enterprise integrations
Missing authorization controls
Incomplete legacy-system handling
Unsafe enterprise-action execution
Limited failure handling
Missing telemetry and traces
Incomplete automated tests
Limited deployment documentation
Participants must transform the starter solution into a secure, reliable, observable, and deployment-ready proof of capability.

The system is a technical assessment environment. It must use only supplied or synthetic customer data and must not connect to real customer records.

Supplied Starter Package
The challenge repository will include:

Partially implemented source code
Basic customer interaction interface or conversation runner
Initial Gemini integration or provider adapter
Stubbed agent or workflow orchestration
Mock authentication service
Customer-profile service
Account and subscription service
Billing or service-information service
Network-status or diagnostics service
Case-management service
Legacy telecom service
Sample customer and account data
Test users and roles
Mandatory customer scenarios
Failure-simulation controls
API documentation and schemas
Initial architecture documentation
Known technical gaps
Sample environment configuration
The same starter package, scenarios, test data, and failure controls will be provided to all competitors.

Participants may refactor individual components where necessary, but the required workflows and supplied enterprise integrations must remain reviewable.

Target Users
1. Customer

The customer uses the solution to:

Ask account or service questions
Report service issues
Request technical assistance
Review available service options
Perform supported account or service actions
Receive a verified resolution or escalation reference
2. Customer Support Representative

The support representative receives escalated requests containing:

Request summary
Verified customer context
Completed workflow steps
Enterprise systems already accessed
Retrieved evidence
Failed tools or integrations
Pending actions
Recommended next step
Request or trace identifier
3. Operations and Engineering User

The operations or engineering user reviews:

Workflow executions
Agent and tool activity
Integration performance
Authentication and authorization events
Failed requests
Escalations
Operational metrics
Application health
Core User Journey
A customer submits a natural-language request.
Gemini interprets the request and extracts relevant information.
The system asks for clarification if required information is missing.
The customer authenticates when protected information or actions are involved.
Deterministic authorization logic validates access.
The orchestrator selects the appropriate agent, workflow, or enterprise tool.
Enterprise data is retrieved and normalized.
The system validates the returned information.
A grounded response or proposed action is presented.
The customer confirms any consequential action.
The enterprise action is executed and verified.
The system returns a confirmed outcome or creates an escalation.
The complete execution is recorded through structured events and traces.
Operational metrics are updated from actual workflow activity.
Functional Requirements
1. Gemini and Conversational AI

The solution must use Gemini meaningfully within the required customer workflows.

Gemini may be used for:

Intent classification
Entity extraction
Request interpretation
Clarification-question generation
Workflow planning
Agent routing
Tool selection
Enterprise-information synthesis
Grounded response generation
Escalation summarization
Participants must document:

Gemini model or service used
Where the model is invoked
Purpose of each model invocation
Context supplied to the model
Prompt or agent instructions
Structured output definitions
Output validation
Safety controls
Failure behavior
Decisions enforced outside the model
Authentication, authorization, record ownership, confirmation, and protected business actions must be enforced through deterministic application logic.

A submission implemented entirely through fixed responses or hardcoded scenario branches will not qualify.

2. Agent Architecture and Orchestration

Participants must complete or improve the supplied agentic or workflow architecture.

The solution may use:

A primary orchestrator with specialized agents
A controlled tool-using agent
Multiple cooperating agents
A deterministic workflow with AI-assisted steps
A hybrid architecture
The implementation must demonstrate:

Clear agent or component responsibilities
Controlled tool access
Conversation and workflow state management
Routing and delegation logic
Validation before tool execution
Loop prevention
Completion and termination conditions
Timeout and error handling
Human review and escalation points
If multiple agents are used, participants must explain:

Why each agent is required
What information it can access
Which tools it may execute
How context is transferred
How conflicting results are handled
How unnecessary agent calls are avoided
How the workflow determines completion
Using more agents will not automatically receive a higher score. The architecture must be appropriate, controlled, reliable, and maintainable.

3. Customer Authentication and Authorization

The solution must authenticate customers before accessing protected information or executing protected actions.

The implementation must:

Use the supplied authentication service or an approved equivalent
Maintain authentication state appropriately
Handle invalid and expired authentication
Prevent one customer from accessing another customer’s records
Enforce record ownership or role permissions
Restrict tools according to the authenticated user and workflow state
Validate model-generated tool parameters
Record authentication and authorization events
Protect credentials and tokens from the AI model
Avoid exposing sensitive authentication information in logs or traces
The AI model must never be the sole authority for granting access.

A simulated authentication flow is acceptable because the challenge uses synthetic data, but the flow and enforcement must be technically meaningful.

4. Enterprise and Legacy-System Integration

The solution must integrate with the supplied enterprise services and the legacy telecom service.

The integration layer must handle:

Request validation
Response validation
Data normalization
Enterprise authentication
Error-code mapping
Timeouts
Safe and limited retries
Missing or partial data
Malformed responses
Rate limits
Duplicate requests
Failed enterprise operations
Enterprise systems must be accessed through controlled tools, services, or adapters. Gemini must not receive unrestricted access to raw enterprise endpoints.

Legacy Telecom Adapter

The supplied legacy service may include:

XML requests or responses
Inconsistent field names
Legacy status codes
Unusual error codes
Missing optional fields
Slow responses
Intermittent failures
Older authentication behavior
Participants must complete or implement an adapter that:

Communicates with the legacy interface.
Validates the returned response.
Converts the response into a consistent internal model.
Maps legacy errors into application-level errors.
Prevents raw legacy-system behavior from leaking into the AI and customer layers.
Produces useful diagnostic events without exposing protected data.
The legacy service must not be bypassed or replaced with hardcoded results.

5. Grounded and Trustworthy Responses

Customer-facing responses must be grounded in customer input and verified enterprise information.

The solution must distinguish between:

Customer-provided information
Retrieved enterprise information
AI-generated interpretation
Assumptions
Recommendations
Confirmed actions
Unverified information
The solution must not:

Invent customer or account records
Generate unsupported charges, plans, outages, cases, or reference numbers
Present assumptions as verified facts
Claim that a tool was called when it was not
Report a failed action as successful
Replace unavailable data with fabricated values
Hide materially conflicting enterprise information
If required information is unavailable or unclear, the system must ask for clarification, provide a qualified response, use an approved fallback, or escalate the request.

6. Clarification and Context Management

The solution must identify incomplete or ambiguous customer requests.

It must:

Determine what information is missing
Ask a relevant and specific clarification question
Preserve previously supplied information
Resume the existing workflow after clarification
Avoid asking for information already provided
Avoid unsupported assumptions
Avoid calling protected or consequential tools prematurely
Generic requests for “more information” will receive limited credit when the missing information can be identified precisely.

7. Controlled Enterprise Action

The solution must support at least one consequential enterprise action.

Examples include:

Creating a support case
Scheduling technical assistance
Submitting a service-change request
Updating an account preference
Requesting a supported plan change
Before completing the action, the solution must:

Authenticate the customer.
Verify authorization.
Validate the requested action and parameters.
Present an understandable action summary.
Obtain explicit customer confirmation.
Execute the controlled enterprise tool.
Validate the backend response.
Report success only after confirmed execution.
Return a valid reference identifier where applicable.
Record the action and result.
Prevent accidental duplicate execution.
A proposed or recommended action must not be shown as completed.

8. Failure Handling and Human Escalation

The solution must safely handle:

Gemini provider failure
Enterprise API failure
Network timeout
Rate limit
Invalid or expired authentication
Unauthorized requests
Missing or conflicting enterprise data
Malformed responses
Failed enterprise actions
Duplicate action requests
Internal processing failures
The implementation must:

Detect and classify the failure
Preserve relevant workflow state
Avoid fabricating an outcome
Retry only when safe and appropriate
Limit retry attempts
Prevent duplicate consequential actions
Provide a clear customer-facing explanation
Use a documented fallback where available
Escalate when safe completion is not possible
Record the failure in logs, traces, and metrics
An escalation record must include:

Customer request summary
Available verified context
Completed workflow steps
Enterprise systems accessed
Relevant evidence
Failed tools or integrations
Error summary
Pending action
Recommended next step
Request or trace identifier
The receiving representative should be able to continue the request without requiring the customer to repeat the entire interaction.

9. Data Pipeline, Telemetry, and Observability

The solution must produce structured events for important workflow activity.

Events should include, where applicable:

Session started
Request received
Intent classified
Clarification requested
Authentication attempted
Authentication succeeded or failed
Authorization allowed or denied
Agent invoked
Tool invoked
Tool completed or failed
Retry performed
Confirmation requested
Confirmation received
Enterprise action completed
Escalation created
Workflow resolved
Workflow failed
Each event must contain a correlation or trace identifier.

Telemetry Pipeline

The telemetry pipeline must:

Accept structured application events
Validate event formats
Associate events with a request or session
Support request-level investigation
Support operational metrics
Handle invalid events safely
Avoid unnecessary sensitive-data storage
Workflow Trace
Reviewers must be able to inspect:

Trace identifier
Workflow steps
Agents or components invoked
Enterprise tools called
Sanitized input and output summaries
Execution duration
Success or failure status
Retry and fallback events
Authorization decisions
Confirmation events
Final outcome
Escalation reason
Passwords, tokens, secrets, unnecessary personal data, and protected model instructions must not appear in the trace.

Operational View

The solution must show metrics generated from actual application events, such as:

Total sessions
Resolution rate
Escalation rate
Failure rate
Average workflow duration
Tool-call success rate
Failures by integration
Authentication failures
Authorization denials
Agent and tool usage
Retry frequency
Gemini latency and failures
Human handoff rate

Static or manually entered monitoring data will not satisfy this requirement.

Mandatory Evaluation Scenarios
Every submission will be reviewed using the same scenarios, test users, data, and failure conditions.

1. Grounded Customer Inquiry

A customer requests protected account, subscription, billing, or service information.
The solution must authenticate the customer, retrieve the correct authorized record, normalize the enterprise response, and return a grounded answer.
2. Ambiguous Request

A customer provides insufficient information.
The solution must identify the missing information, ask a specific clarification question, preserve context, and continue after clarification.
3. Multi-System Issue Resolution

A customer reports an issue requiring multiple enterprise systems.
The solution must coordinate the necessary agents or tools, preserve context, reconcile the returned information, and resolve or safely escalate the request.
4. Protected Enterprise Action

An authenticated customer requests a supported action.
The solution must validate, authorize, summarize, confirm, execute, verify, and record the action while preventing duplicate execution.
5. Unauthorized Access Attempt

An authenticated customer attempts to access another customer’s record.
The solution must deny access through deterministic authorization logic, avoid retrieving or exposing the protected record, and record the denial.
6. Legacy-System Request

A customer request requires information from the supplied legacy telecom service.
The solution must call the service, process its legacy format, normalize the response, map errors, and use the result within the customer workflow.
7. Enterprise-Service Failure

A required enterprise service fails, times out, or returns incomplete information.
The solution must avoid false success, apply safe retry behavior, preserve workflow state, and escalate where necessary.
8. Gemini Provider Failure

Gemini becomes unavailable.
The solution must detect the failure, preserve the active request, continue deterministic security controls, enter a documented fallback or degraded mode, and record the failure.
Google Technology Expectations
The primary AI workflow must demonstrate practical use of Gemini or another Google AI capability identified in the challenge package.

Participants must document:

Google services used
Gemini integration
Agent or orchestration approach
Identity and authentication design
Enterprise-integration approach
Logging and telemetry approach
Google Cloud deployment architecture
Security considerations
Changes required for production deployment
If direct access to a specific Gemini Customer Experience product is not provided, participants must explain how the implemented solution maps to the intended Google customer-experience environment.

Simply mentioning Google products without working implementation or a credible technical mapping will receive limited credit.

Live AI and Reviewer Mode
Live AI Mode

The submission must include a functional Gemini integration with:

Model integration code
Configuration instructions
Prompt or agent instructions
Structured output validation
Failure handling
Execution evidence
Recorded demonstration
Active credentials must not be included.

Reviewer Mode

The submission must provide a deterministic, cached, recorded, or mock reviewer mode for all mandatory scenarios.

Reviewer mode must continue to exercise the real:

User workflow
Authentication and authorization
Application services
Integration adapters
Validation logic
Controlled-action logic
Failure handling
Telemetry pipeline
Trace generation
Reviewer mode must not be a disconnected set of static screens or predefined final responses.

The solution must clearly show whether it is using:

Live AI mode
Reviewer mode
Degraded fallback mode
Reviewer mode does not replace the mandatory live AI implementation.

Solution Depth Requirement
The following are not sufficient:

A static chatbot demonstration
A set of hardcoded responses
A single model call without enterprise integration
Architecture documents without working implementation
A UI that does not exercise the supplied APIs
Static telemetry or manually entered metrics
A mock-only implementation without live Gemini integration
A replacement application that bypasses the starter solution
A recorded demonstration that reviewers cannot reproduce
A valid submission must demonstrate:

Meaningful Gemini usage
Controlled agent or workflow orchestration
Authentication and deterministic authorization
Modern and legacy enterprise integration
Grounded responses
Protected enterprise-action handling
Failure recovery and escalation
Structured events and request-level traces
Event-derived operational metrics
Repeatable tests
Deployment preparation
Customer-team handover
Technology Expectations
The implementation stack may be extended or adjusted where justified.

The final solution must be:

Runnable locally
Reviewable without private participant assistance
Maintainable and documented
Secure in handling synthetic customer data
Transparent about AI-generated and enterprise-sourced information
Configurable through environment variables
Free from hardcoded active credentials
Capable of running mandatory scenarios without paid reviewer access
Prepared for Google Cloud deployment
A browser interface is recommended because the engagement concerns customer-experience solutions, but visual design is not the primary focus. A functional conversation runner with appropriate engineering and operational views may also be acceptable.

Deliverables
1. Productionized Starter Solution

The completed solution must include:

Gemini integration
Agent or workflow orchestration
Authentication and authorization
Enterprise API integrations
Legacy telecom adapter
Grounded response handling
Controlled enterprise action
Failure and escalation handling
Telemetry pipeline
Workflow trace
Operational monitoring
Live AI and reviewer modes
2. Source Code

The source code must be clean, modular, documented, and easy to run.

3. Automated Tests or Evaluation Runner

Tests must cover:

Successful inquiry
Clarification
Authentication success and failure
Authorization enforcement
Cross-customer access denial
Controlled-action confirmation
Successful and failed enterprise actions
Duplicate-action protection
Legacy-response normalization
Enterprise timeout or malformed response
Gemini provider failure
Escalation creation
Telemetry-event generation
4. README

The README must explain:

Local setup
Environment configuration
Live AI mode
Reviewer mode
Mandatory scenario execution
Test execution
Gemini integration
Agent orchestration
Enterprise integrations
Security controls
Telemetry and traces
Known limitations
5. Architecture Diagram

The diagram should show:

Customer interaction layer
Gemini integration
Agents or orchestrator
Authentication and authorization
Enterprise tool layer
Legacy adapter
Data stores
Telemetry pipeline
Trace and monitoring views
Deployment boundaries
6. Deployment Documentation

The deployment documentation must cover:

Local or containerized execution
Health checks
Environment configuration
Timeout and retry settings
Persistence approach
Google Cloud deployment mapping
Scaling and performance considerations
Security considerations
Cost considerations
Recovery or rollback approach
7. Customer-Team Handover Package

The handover package must explain:

Business problem
Architecture
Agent and component responsibilities
Key design decisions
Security approach
How to add a new tool or integration
How to modify the orchestration
How to inspect traces
How to diagnose failures
Known limitations
Recommended production roadmap
8. Demo Video

Recommended duration: 3 to 5 minutes.

The demonstration should show:

A grounded customer inquiry
Clarification handling
A protected enterprise action
Authorization enforcement
Legacy-system processing
A simulated service failure and escalation
Workflow traces and operational metrics
Live AI or evidence of live Gemini integration
Reviewer mode
Key design decisions
9. Requirement-to-Evidence Matrix

The repository must map each challenge requirement to its implementation and review evidence.

Requirement:
Implemented Capability:
Code or Component Location:
Supporting Test:
Reviewer Scenario:
Execution Evidence:
Coverage Status:
Known Limitation:
10. Summary of Changes

Participants must identify:

Starter components retained
Components completed
Components refactored
Security issues fixed
Integrations implemented
Reliability improvements
Observability improvements
Remaining limitations
Evaluation Criteria
1. Gemini and Conversational AI: 15%

Meaningful Gemini integration
Request understanding
Context management
Clarification behavior
Grounded responses
Structured output validation
Gemini failure handling
2. Agent Architecture and Orchestration: 15%

Appropriate architecture
Clear agent and component responsibilities
Routing and delegation
Tool permissions
State management
Loop prevention
Termination behavior
Human escalation
3. Enterprise and Legacy Integration: 15%

API implementation
Contract validation
Data normalization
Legacy adapter
Error mapping
Timeout and retry handling
Integration boundaries
Maintainability
4. Secure APIs, Authentication, and Authorization: 15%

Authentication
Authorization
Customer isolation
Tool-level controls
Parameter validation
Confirmation handling
Duplicate-action protection
Secret handling
Auditability
5. Mandatory Customer Scenarios: 10%

End-to-end completion
Business correctness
State preservation
Verified outcomes
Appropriate escalation
6. Data Pipelines, Telemetry, and Observability: 10%

Structured events
Correlation identifiers
Request-level traces
Event-derived metrics
Diagnostic usefulness
Sensitive-data protection
7. Reliability and Troubleshooting: 10%

Enterprise dependency failures
Gemini provider failures
Timeout and retry behavior
State preservation
Duplicate protection
Fallback behavior
Escalation quality
8. Testing and Software Quality: 5%

Functional tests
Security tests
Integration tests
Failure tests
Code organization
Validation
Maintainability
9. Deployment and Customer-Team Enablement: 5%

Reproducible setup
Google Cloud deployment mapping
Technical documentation
Customer handover
Production recommendations
Total: 100%

Success Definition
A successful submission allows an evaluator to:

Run the productionized starter solution.
Execute all mandatory scenarios.
Verify meaningful Gemini usage.
Inspect controlled agent or workflow orchestration.
Confirm authentication and customer isolation.
Verify protected enterprise-action controls.
Exercise the legacy telecom integration.
Confirm responses are grounded in enterprise data.
Simulate Gemini and enterprise-service failures.
Review escalation records.
Inspect request-level traces.
Review event-derived operational metrics.
Run the automated tests.
Review the Google Cloud deployment approach.
Understand how the solution can be maintained and extended.
Challenge Resources
Will be provided in the challenge forums by the Copilot.