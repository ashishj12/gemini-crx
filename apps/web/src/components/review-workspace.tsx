"use client";
import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  CirclePlay,
  FlaskConical,
  RotateCcw,
  ShieldCheck,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import type { Scenario, ScenarioResult, Session } from "@/lib/types";
import { Busy, Empty } from "./ui";
export function ReviewWorkspace({
  session,
  onTrace,
}: {
  session: Session;
  onTrace: (id: string) => void;
}) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [selected, setSelected] = useState("SCN-001");
  const [results, setResults] = useState<ScenarioResult[]>([]);
  const [running, setRunning] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    api<Scenario[]>("scenarios")
      .then(setScenarios)
      .catch((e) => setError(e.message));
  }, []);
  const allowed =
    session.roles.includes("support-agent") && session.mode === "REVIEWER";
  async function run(all: boolean) {
    setError("");
    const targets = all
      ? scenarios
      : scenarios.filter((s) => s.scenarioId === selected);
    for (const target of targets) {
      setRunning(target.scenarioId);
      try {
        const result = await api<ScenarioResult>("reviewer/run", {
          scenarioId: target.scenarioId,
        });
        setResults((items) => [
          result,
          ...items.filter((i) => i.scenarioId !== result.scenarioId),
        ]);
      } catch (e) {
        setError((e as Error).message);
        break;
      }
    }
    setRunning("");
  }
  const passed = results.filter((r) => r.status === "PASS").length;
  return (
    <div>
      <div className="page-intro">
        <div>
          <span className="eyebrow">REPEATABLE. REVIEWABLE. REAL.</span>
          <h1>Proof, not promises.</h1>
          <p>
            Eight customer scenarios. The actual workflows, systems, and
            decisions behind them.
          </p>
        </div>
        <span className="outline-tag">
          <FlaskConical size={14} /> REVIEW LAB
        </span>
      </div>
      {!allowed && (
        <div className="notice">
          Scenario execution requires Reviewer mode and the supplied support
          representative account. Sign out to switch accounts.
        </div>
      )}
      <div className="lab-overview">
        <div>
          <span className="eyebrow">MANDATORY ACCEPTANCE SUITE</span>
          <h2>Every path to a resolution.</h2>
          <p>
            Only the model interpretation is deterministic. Authentication,
            enterprise calls, legacy XML, confirmations, and telemetry execute
            through the real backend.
          </p>
        </div>
        <div className="lab-score">
          <strong>
            {passed}
            <span>/08</span>
          </strong>
          <p>verified in this run</p>
        </div>
      </div>
      {error && (
        <div className="notice error" role="alert">
          {error}
        </div>
      )}
      {!scenarios.length ? (
        <Busy label="Loading supplied scenarios" />
      ) : (
        <>
          <div className="lab-toolbar">
            <div>
              <span className="status-dot" />{" "}
              {running ? `Executing ${running}` : "Ready for evaluation"}
            </div>
            <div>
              <button
                className="button secondary"
                onClick={() => setResults([])}
                disabled={!!running}
              >
                <RotateCcw size={14} />
                Reset display
              </button>
              <button
                className="button primary"
                onClick={() => run(true)}
                disabled={!allowed || !!running}
              >
                {running ? "Running workflows…" : "Run all eight scenarios"}
                <ArrowRight size={15} />
              </button>
            </div>
          </div>
          <div className="scenario-grid">
            {scenarios.map((scenario, index) => {
              const result = results.find(
                (r) => r.scenarioId === scenario.scenarioId,
              );
              return (
                <button
                  className={`scenario-card ${selected === scenario.scenarioId ? "selected" : ""}`}
                  key={scenario.scenarioId}
                  onClick={() => setSelected(scenario.scenarioId)}
                  aria-pressed={selected === scenario.scenarioId}
                >
                  <div>
                    <span className="scenario-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span
                      className={`test-status ${result?.status.toLowerCase() ?? "idle"}`}
                    >
                      {result ? (
                        result.status === "PASS" ? (
                          <>
                            <Check size={12} />
                            Verified
                          </>
                        ) : (
                          <>
                            <X size={12} />
                            Failed
                          </>
                        )
                      ) : (
                        "Not run"
                      )}
                    </span>
                  </div>
                  <h3>{scenario.title}</h3>
                  <p>
                    {scenario.expected?.slice(0, 3).join(" · ") ??
                      scenario.expectedOutcome ??
                      scenario.expectedTools?.join(" · ")}
                  </p>
                  <div className="scenario-bottom">
                    <span>{scenario.scenarioId}</span>
                    <ArrowUpRight size={17} />
                  </div>
                </button>
              );
            })}
          </div>
          <div className="selected-run">
            <span>
              <ShieldCheck size={14} />
              {selected} selected · uses supplied synthetic identity and
              fixtures
            </span>
            <button
              className="button secondary"
              onClick={() => run(false)}
              disabled={!allowed || !!running}
            >
              Run selected
              <CirclePlay size={15} />
            </button>
          </div>
        </>
      )}
      <section className="results-section">
        <div className="section-heading">
          <h2>Execution results</h2>
          <span className="small-label">FROM ACTUAL BACKEND CHECKS</span>
        </div>
        {!results.length ? (
          <Empty title="The evidence starts when you run.">
            Select a scenario or run the complete suite. Each result includes
            the checks and real execution traces.
          </Empty>
        ) : (
          results.map((result) => (
            <details className="result-row" key={result.scenarioId}>
              <summary>
                <span className={`result-icon ${result.status.toLowerCase()}`}>
                  {result.status === "PASS" ? (
                    <Check size={17} />
                  ) : (
                    <X size={17} />
                  )}
                </span>
                <span>
                  <strong>{result.title}</strong>
                  <small>
                    {result.scenarioId} ·{" "}
                    {Object.values(result.checks).filter(Boolean).length} /{" "}
                    {Object.keys(result.checks).length} checks passed
                  </small>
                </span>
                <span className="test-status">{result.status}</span>
                <span className="expand-plus">+</span>
              </summary>
              <div className="result-details">
                <div className="checks-list">
                  {Object.entries(result.checks).map(([name, pass]) => (
                    <div
                      key={name}
                      className={pass ? "check-pass" : "check-fail"}
                    >
                      {pass ? <Check size={12} /> : <X size={12} />}
                      <span>{name.replaceAll("_", " ")}</span>
                    </div>
                  ))}
                </div>
                {result.results.map((response, index) => (
                  <div className="scenario-response" key={index}>
                    <span className="eyebrow">
                      {response.state.replaceAll("_", " ")}
                    </span>
                    <p>{response.answer}</p>
                    <button
                      className="verification-link"
                      onClick={() => onTrace(response.traceId)}
                    >
                      Inspect execution trace
                      <ArrowUpRight size={13} />
                    </button>
                  </div>
                ))}
              </div>
            </details>
          ))
        )}
      </section>
      <div className="lab-footnote">
        <FlaskConical size={15} />
        <p>
          SCN-007 causes a real mock-service 503. SCN-008 explicitly simulates
          provider unavailability. Reset clears this display, while backend
          evidence stays in the audit history.
        </p>
      </div>
    </div>
  );
}
