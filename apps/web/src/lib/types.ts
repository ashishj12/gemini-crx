export type Mode = "LIVE_AI" | "REVIEWER" | "DEGRADED";
export type HistoryMessage = {
  role: "user" | "assistant";
  text: string;
  traceId?: string;
};
export type Action = {
  id: string;
  summary: string;
  status: string;
  accountId: string;
  caseId?: string;
};
export type Session = {
  customerId: string;
  accountId: string | null;
  roles: string[];
  mode: Mode;
  state: string;
  history: HistoryMessage[];
  pendingAction: Action | null;
};
export type ChatResult = {
  answer: string;
  traceId: string;
  state: string;
  mode: Mode;
  facts: string[];
  pendingAction?: Action;
  caseId?: string;
  escalationId?: string;
};
export type Overview = {
  name: string;
  account: {
    accountId: string;
    status: string;
    plan: { name: string; monthlyPrice: number };
    services: { type: string; status: string }[];
  };
  traceId: string;
  source: string;
};
export type TelemetryEvent = {
  eventId: string;
  traceId: string;
  sessionId: string;
  timestamp: string;
  eventType: string;
  component: string;
  status: string;
  durationMs: number;
  metadata: Record<string, unknown>;
};
export type Scenario = {
  scenarioId: string;
  title: string;
  request?: string;
  expected?: string[];
  expectedTools?: string[];
  expectedOutcome?: string;
};
export type ScenarioResult = {
  scenarioId: string;
  title: string;
  status: "PASS" | "FAIL";
  checks: Record<string, boolean>;
  traceIds: string[];
  results: ChatResult[];
};
export type Metrics = {
  sessions: number;
  requests: number;
  resolutionRate: number;
  escalationRate: number;
  failureRate: number;
  averageWorkflowMs: number;
  toolSuccessRate: number;
  failuresByIntegration: Record<string, number>;
  authenticationFailures: number;
  authorizationDenials: number;
  geminiFailures: number;
  geminiLatencyMs: number;
  retries: number;
  humanHandoffRate: number;
  toolUsage: Record<string, number>;
  telemetryRejected: number;
};
export type Escalation = {
  escalationId: string;
  traceId: string;
  requestSummary: string;
  reason: string;
  completedSteps: string[];
  recommendedNextStep: string;
  pendingAction?: Action;
};
