"use client";
import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Check,
  CircleCheck,
  Clock3,
  RefreshCw,
  Search,
  ShieldCheck,
  Users,
} from "lucide-react";
import { api, percent, titleCase } from "@/lib/api";
import type { Escalation, Metrics, Session, TelemetryEvent } from "@/lib/types";
import { Busy, Empty } from "./ui";
export function OperationsWorkspace({
  session,
  onTrace,
}: {
  session: Session;
  onTrace: (id: string) => void;
}) {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [handoffs, setHandoffs] = useState<Escalation[]>([]);
  const [health, setHealth] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const [updated, setUpdated] = useState("");
  const allowed = session.roles.includes("support-agent");
  async function refresh() {
    setBusy(true);
    setError("");
    try {
      const [m, e, h, services] = await Promise.all([
        api<Metrics>("ops/metrics"),
        api<TelemetryEvent[]>("ops/events"),
        api<Escalation[]>("ops/escalations"),
        api<{ enterprise: { status: string } }>("ops/health"),
      ]);
      setMetrics(m);
      setEvents(e);
      setHandoffs(h);
      setHealth(services.enterprise.status);
      setUpdated(
        new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (allowed) refresh();
  }, [allowed]);
  const workflows = useMemo(() => {
    const traces = new Map<string, TelemetryEvent[]>();
    for (const event of events) {
      if (!traces.has(event.traceId)) traces.set(event.traceId, []);
      traces.get(event.traceId)!.push(event);
    }
    return [...traces.entries()]
      .filter(([, group]) =>
        group.some((e) => e.eventType === "request.received"),
      )
      .reverse()
      .filter(([id, group]) =>
        `${id} ${group.map((e) => e.component).join(" ")}`
          .toLowerCase()
          .includes(query.toLowerCase()),
      )
      .slice(0, 40);
  }, [events, query]);
  if (!allowed)
    return (
      <>
        <div className="page-intro">
          <div>
            <span className="eyebrow">OPERATIONS</span>
            <h1>The bigger picture.</h1>
            <p>Understand how requests move from conversation to resolution.</p>
          </div>
        </div>
        <div className="notice">
          This workspace requires the supplied support representative account.
          Customer conversations and account information remain protected.
        </div>
      </>
    );
  return (
    <div>
      <div className="page-intro">
        <div>
          <span className="eyebrow">THE WORK BEHIND THE CONVERSATION</span>
          <h1>The bigger picture.</h1>
          <p>
            Actual requests. Measured outcomes. Nothing between you and the
            evidence.
          </p>
        </div>
        <button className="button secondary" onClick={refresh} disabled={busy}>
          <RefreshCw size={14} className={busy ? "spin" : ""} />
          Refresh data
        </button>
      </div>
      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}
      {!metrics ? (
        <Busy label="Retrieving operational events" />
      ) : (
        <>
          <div className="ops-statusbar">
            <span>
              <span
                className={`status-dot ${health === "ok" ? "" : "warning"}`}
              />
              Enterprise services{" "}
              {health === "ok" ? "available" : "unavailable"}
            </span>
            <span>
              All persisted activity <span className="small-separator">/</span>{" "}
              Updated {updated} local time
            </span>
          </div>
          <div className="metric-grid">
            {[
              {
                name: "Customer sessions",
                value: metrics.sessions,
                icon: Users,
                foot: "Authenticated sessions created",
              },
              {
                name: "Support requests",
                value: metrics.requests,
                icon: Activity,
                foot: "Conversation & confirmation requests",
              },
              {
                name: "Resolution rate",
                value: percent(metrics.resolutionRate),
                icon: CircleCheck,
                foot: "Resolved events / requests",
              },
              {
                name: "Average duration",
                value: `${Math.round(metrics.averageWorkflowMs)} ms`,
                icon: Clock3,
                foot: "From request to recorded outcome",
              },
            ].map((metric, index) => (
              <div
                className={`metric-card ${index === 2 ? "accent" : ""}`}
                key={metric.name}
              >
                <div>
                  <span>{metric.name}</span>
                  <metric.icon size={17} strokeWidth={1.5} />
                </div>
                <strong>{metric.value}</strong>
                <p>{metric.foot}</p>
              </div>
            ))}
          </div>
          <div className="ops-chart-grid">
            <section className="panel tool-panel">
              <div className="section-heading">
                <div>
                  <span className="eyebrow">ENTERPRISE ACTIVITY</span>
                  <h3>Every tool has a part to play.</h3>
                </div>
                <span className="small-label">ACTUAL CALLS</span>
              </div>
              {Object.keys(metrics.toolUsage).length === 0 ? (
                <Empty title="Waiting for activity">
                  Run a customer workflow to see enterprise tool usage.
                </Empty>
              ) : (
                <div className="tool-bars">
                  {Object.entries(metrics.toolUsage)
                    .sort((a, b) => b[1] - a[1])
                    .map(([name, count]) => (
                      <div className="tool-bar-row" key={name}>
                        <span>{titleCase(name)}</span>
                        <div>
                          <span
                            style={{
                              width: `${Math.max(2, (count / Math.max(...Object.values(metrics.toolUsage))) * 100)}%`,
                            }}
                          />
                        </div>
                        <strong>{count}</strong>
                      </div>
                    ))}
                </div>
              )}
            </section>
            <section className="panel reliability-panel">
              <span className="eyebrow">RELIABILITY, IN VIEW</span>
              <h3>
                Good outcomes start
                <br />
                with trustworthy systems.
              </h3>
              <div className="reliability-number">
                {percent(metrics.toolSuccessRate)}
                <span>tool-call success rate</span>
              </div>
              <div className="reliability-track">
                <span style={{ width: `${metrics.toolSuccessRate * 100}%` }} />
              </div>
              <div className="reliability-details">
                <span>
                  Human handoff{" "}
                  <strong>{percent(metrics.humanHandoffRate)}</strong>
                </span>
                <span>
                  Authorization denials{" "}
                  <strong>{metrics.authorizationDenials}</strong>
                </span>
                <span>
                  Gemini failures <strong>{metrics.geminiFailures}</strong>
                </span>
                <span>
                  Safe retries <strong>{metrics.retries}</strong>
                </span>
                <span>
                  Invalid events rejected{" "}
                  <strong>{metrics.telemetryRejected}</strong>
                </span>
              </div>
            </section>
          </div>
          <section className="panel workflows-panel">
            <div className="section-heading">
              <div>
                <span className="eyebrow">FOLLOW THE WORK</span>
                <h3>Workflow explorer</h3>
              </div>
              <label className="search-input">
                <Search size={15} />
                <span className="sr-only">Search trace or component</span>
                <input
                  placeholder="Find a trace or component…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
              </label>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>REQUEST / TRACE</th>
                    <th>COMPONENTS</th>
                    <th>OUTCOME</th>
                    <th>DURATION</th>
                    <th>TIME</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {workflows.map(([id, group]) => {
                    const final = group
                      .filter((e) => e.eventType === "workflow.transition")
                      .at(-1);
                    const denied = group.some(
                      (e) => e.eventType === "authorization.denied",
                    );
                    const finished = group.find(
                      (e) => e.eventType === "request.finished",
                    );
                    const state = denied
                      ? "Access denied"
                      : String(
                          final?.metadata.current ??
                            (finished ? "Complete" : "In progress"),
                        );
                    const tools = [
                      ...new Set(
                        group
                          .filter((e) => e.eventType === "tool.invoked")
                          .map((e) => e.component),
                      ),
                    ];
                    return (
                      <tr key={id}>
                        <td>
                          <button
                            className="trace-id-link"
                            onClick={() => onTrace(id)}
                          >
                            {id.slice(0, 19)}…
                          </button>
                        </td>
                        <td>
                          {tools.length
                            ? tools.slice(0, 2).map(titleCase).join(", ") +
                              (tools.length > 2 ? ` +${tools.length - 2}` : "")
                            : "Security / orchestration"}
                        </td>
                        <td>
                          <span
                            className={`outcome ${denied || state === "ESCALATED" ? "attention" : ""}`}
                          >
                            {titleCase(state)}
                          </span>
                        </td>
                        <td>
                          {finished
                            ? `${Math.round(finished.durationMs)} ms`
                            : "—"}
                        </td>
                        <td>
                          {new Date(group[0].timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </td>
                        <td>
                          <button
                            className="icon-button"
                            aria-label={`Inspect ${id}`}
                            onClick={() => onTrace(id)}
                          >
                            <ArrowUpRight size={15} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {!workflows.length && (
                <Empty title="No matching workflows">
                  Try another search or start a customer conversation.
                </Empty>
              )}
            </div>
          </section>
          <section className="handoffs-section">
            <div className="section-heading">
              <div>
                <span className="eyebrow">A CLEAR NEXT STEP</span>
                <h2>Human handoffs</h2>
              </div>
              <span className="outline-tag">{handoffs.length} recorded</span>
            </div>
            {!handoffs.length ? (
              <Empty title="Nothing waiting for a handoff.">
                Requests that need human judgment will arrive here with their
                context intact.
              </Empty>
            ) : (
              <div className="handoff-grid">
                {handoffs
                  .slice()
                  .reverse()
                  .slice(0, 12)
                  .map((handoff) => (
                    <article
                      className="handoff-card"
                      key={handoff.escalationId}
                    >
                      <div className="section-heading">
                        <span className="handoff-badge">Human review</span>
                        <button
                          className="icon-button"
                          aria-label={`Inspect handoff ${handoff.escalationId}`}
                          onClick={() => onTrace(handoff.traceId)}
                        >
                          <ArrowUpRight size={16} />
                        </button>
                      </div>
                      <h3>{handoff.requestSummary}</h3>
                      <p className="handoff-reason">
                        {titleCase(handoff.reason.replaceAll(":", " · "))}
                      </p>
                      <div className="completed-steps">
                        {handoff.completedSteps.map((step) => (
                          <span key={step}>
                            <Check size={11} />
                            {titleCase(step)}
                          </span>
                        ))}
                      </div>
                      <p className="handoff-next">
                        {handoff.recommendedNextStep}
                      </p>
                      <footer>
                        <span>{handoff.escalationId.slice(0, 19)}…</span>
                        {handoff.pendingAction && (
                          <span>Action: {handoff.pendingAction.status}</span>
                        )}
                      </footer>
                    </article>
                  ))}
              </div>
            )}
          </section>
          <details className="metrics-details">
            <summary>
              View all measurements and integration failures <span>+</span>
            </summary>
            <pre>{JSON.stringify(metrics, null, 2)}</pre>
          </details>
        </>
      )}
    </div>
  );
}
