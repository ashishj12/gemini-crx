"use client";
import { useEffect, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowRight,
  ArrowUp,
  ArrowUpRight,
  Check,
  CheckCheck,
  CircleHelp,
  FileText,
  Headphones,
  MessageSquare,
  Plus,
  ShieldCheck,
  Sparkles,
  Wifi,
  X,
} from "lucide-react";
import { api, titleCase } from "@/lib/api";
import type {
  Action,
  ChatResult,
  HistoryMessage,
  Mode,
  Overview,
  Session,
} from "@/lib/types";
import { SourceLabel } from "./ui";

const suggestions = [
  {
    icon: FileText,
    title: "Understand my bill",
    detail: "A clear view of what you’re paying for",
    message: "Show my billing details",
  },
  {
    icon: Wifi,
    title: "Fix my connection",
    detail: "Let’s find out what’s going on",
    message: "My service is not working.",
  },
  {
    icon: MessageSquare,
    title: "Check my plan",
    detail: "Get to know your current service",
    message: "What plan am I currently using?",
  },
];
export function SupportWorkspace({
  session,
  onMode,
  onTrace,
}: {
  session: Session;
  onMode: (mode: Mode) => void;
  onTrace: (id: string) => void;
}) {
  const [overview, setOverview] = useState<Overview | null>(null);
  const [overviewError, setOverviewError] = useState("");
  const [messages, setMessages] = useState<HistoryMessage[]>(
    session.history ?? [],
  );
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState<Action | null>(
    session.pendingAction?.status === "pending" ? session.pendingAction : null,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [state, setState] = useState(session.state);
  const log = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);
  const customer = session.roles.includes("customer");
  useEffect(() => {
    if (customer)
      api<Overview>("account/overview")
        .then(setOverview)
        .catch((e) => setOverviewError(e.message));
  }, [customer]);
  useEffect(() => {
    if (log.current) log.current.scrollTop = log.current.scrollHeight;
  }, [messages, busy, pending]);
  function consume(result: ChatResult) {
    setMessages((items) => [
      ...items,
      { role: "assistant", text: result.answer, traceId: result.traceId },
    ]);
    onMode(result.mode);
    setState(result.state);
    if (result.pendingAction) setPending(result.pendingAction);
    else if (result.caseId || result.escalationId) setPending(null);
  }
  async function send(text: string) {
    if (!text.trim() || busy) return;
    setMessage("");
    setError("");
    setBusy(true);
    setMessages((items) => [...items, { role: "user", text: text.trim() }]);
    try {
      consume(await api<ChatResult>("chat", { message: text.trim() }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function confirm(accepted: boolean) {
    if (!pending || busy) return;
    setBusy(true);
    setError("");
    try {
      const response = await api<ChatResult>("confirm", {
        actionId: pending.id,
        confirm: accepted,
      });
      setPending(null);
      consume(response);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const firstName = overview?.name.split(" ")[0];
  return (
    <div className="support-workspace">
      <div className="page-intro">
        <div>
          <span className="eyebrow">YOUR SUPPORT WORKSPACE</span>
          <h1>
            {firstName
              ? `Hi ${firstName}. Let’s sort it out.`
              : "Let’s get you connected."}
          </h1>
          <p>Clear answers. Real progress. A little more peace of mind.</p>
        </div>
        <span className="intro-annotation">
          <span className="status-dot" /> Here when you need us
        </span>
      </div>
      {!customer && (
        <div className="notice">
          You’re signed in as a support representative. Use the Review lab and
          Operations workspaces, or sign in as a customer to start a support
          conversation.
        </div>
      )}
      <div className="support-top-grid">
        <div className="welcome-card">
          <span className="eyebrow">CONNECTED TO A RESOLUTION</span>
          <h2>
            Good support starts
            <br />
            with a <span>clear conversation.</span>
          </h2>
          <p>
            From a question about your bill to a connection that
            <br className="desktop-br" /> needs attention — let’s take the next
            step together.
          </p>
          <button className="text-link" onClick={() => input.current?.focus()}>
            Tell us what you need <ArrowDown size={15} />
          </button>
          <div className="welcome-symbol" aria-hidden>
            <div />
            <div />
            <div />
            <ArrowUpRight size={52} strokeWidth={1.15} />
          </div>
        </div>
        <section className="account-card">
          <div className="section-heading">
            <span className="eyebrow">YOUR CONNECTED LIFE</span>
            <Wifi size={19} strokeWidth={1.5} />
          </div>
          {overview ? (
            <>
              <div className="account-plan">
                <h3>{overview.account.plan.name}</h3>
                <span className="account-state">
                  <span className="status-dot" />
                  Account {overview.account.status}
                </span>
              </div>
              <div className="plan-price">
                {overview.account.plan.monthlyPrice.toFixed(2)}
                <span> / month</span>
              </div>
              <div className="account-bottom">
                <div>
                  <small>ACCOUNT</small>
                  <span>{overview.account.accountId}</span>
                </div>
                <button
                  className="icon-button bordered"
                  aria-label="Inspect account verification"
                  onClick={() => onTrace(overview.traceId)}
                >
                  <ArrowUpRight size={18} />
                </button>
              </div>
              <SourceLabel>Verified account information</SourceLabel>
            </>
          ) : (
            <div className="account-loading">
              <p>
                {overviewError ||
                  (customer
                    ? "Retrieving your verified account…"
                    : "Customer details appear after customer sign-in.")}
              </p>
              {overviewError && (
                <button
                  className="text-link"
                  onClick={() => {
                    setOverviewError("");
                    api<Overview>("account/overview")
                      .then(setOverview)
                      .catch((e) => setOverviewError(e.message));
                  }}
                >
                  Try again <ArrowRight size={14} />
                </button>
              )}
            </div>
          )}
        </section>
      </div>
      <div className="conversation-grid">
        <section className="conversation-panel">
          <div className="conversation-heading">
            <div>
              <span className="assistant-symbol">
                <Sparkles size={19} />
              </span>
              <div>
                <h3>Your resolution assistant</h3>
                <p>
                  <span className="status-dot" /> Ready to help you move forward
                </p>
              </div>
            </div>
            <span className="session-label">
              PRIVATE CONVERSATION <ShieldCheck size={13} />
            </span>
          </div>
          <div
            className={`conversation-log ${messages.length ? "has-messages" : ""}`}
            ref={log}
            role="log"
            aria-live="polite"
            aria-label="Support conversation"
          >
            {messages.length === 0 ? (
              <div className="conversation-empty">
                <span className="empty-spark">
                  <Sparkles size={30} strokeWidth={1.2} />
                </span>
                <h2>What can we clear up today?</h2>
                <p>A simple question is a good place to start.</p>
                <div className="suggestion-grid">
                  {suggestions.map((item) => (
                    <button
                      key={item.title}
                      disabled={!customer}
                      onClick={() => send(item.message)}
                    >
                      <item.icon size={19} strokeWidth={1.5} />
                      <strong>{item.title}</strong>
                      <span>{item.detail}</span>
                      <ArrowUpRight size={15} />
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((item, index) => (
                <article className={`chat-message ${item.role}`} key={index}>
                  {item.role === "assistant" && (
                    <span className="message-avatar">r.</span>
                  )}
                  <div>
                    <span className="message-label">
                      {item.role === "user" ? "YOU" : "RELAY"}
                    </span>
                    <p>{item.text}</p>
                    {item.traceId && (
                      <button
                        className="verification-link"
                        onClick={() => onTrace(item.traceId!)}
                      >
                        <CheckCheck size={13} /> How this was verified{" "}
                        <ArrowUpRight size={12} />
                      </button>
                    )}
                  </div>
                </article>
              ))
            )}
            {busy && (
              <div className="thinking" role="status">
                <span />
                <span />
                <span />
                <p>Working on your request…</p>
              </div>
            )}
            {pending && (
              <div className="confirmation-card">
                <div className="confirmation-icon">
                  <ShieldCheck size={20} />
                </div>
                <span className="eyebrow">YOUR GO-AHEAD, FIRST</span>
                <h3>Ready to create this support case?</h3>
                <p>{pending.summary}</p>
                <span className="confirmation-account">
                  For account {pending.accountId} · One support case
                </span>
                <div>
                  <button
                    className="button primary"
                    disabled={busy}
                    onClick={() => confirm(true)}
                  >
                    Confirm & create case <ArrowRight size={15} />
                  </button>
                  <button
                    className="button secondary"
                    disabled={busy}
                    onClick={() => confirm(false)}
                  >
                    Not now
                  </button>
                </div>
              </div>
            )}
          </div>
          {error && (
            <div className="notice error composer-error" role="alert">
              {error}
            </div>
          )}
          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              send(message);
            }}
          >
            <label className="sr-only" htmlFor="support-message">
              Your support request
            </label>
            <textarea
              ref={input}
              id="support-message"
              placeholder="What’s on your mind?"
              rows={2}
              value={message}
              maxLength={2000}
              disabled={!customer}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(message);
                }
              }}
            />
            <button
              className="send-button"
              aria-label="Send support request"
              disabled={busy || !message.trim() || !customer}
            >
              <ArrowUp size={19} />
            </button>
          </form>
          <div className="composer-footnote">
            <span>
              <LockIcon />
              Your information stays protected.
            </span>
            <span>
              ↵ Send <span className="key-separator">·</span> Shift + ↵ New line
            </span>
          </div>
        </section>
        <aside className="support-context">
          <section className="context-block">
            <div className="section-heading">
              <span className="eyebrow">A LITTLE REASSURANCE</span>
              <ShieldCheck size={18} strokeWidth={1.4} />
            </div>
            <h3>
              Every answer has
              <br />
              something behind it.
            </h3>
            <p>
              Your account is verified before we access it. Answers come from
              your actual service records. Changes wait for your confirmation.
            </p>
            <div className="trust-item">
              <span>
                <Check size={12} />
              </span>{" "}
              Verified account access
            </div>
            <div className="trust-item">
              <span>
                <Check size={12} />
              </span>{" "}
              Answers grounded in your records
            </div>
            <div className="trust-item">
              <span>
                <Check size={12} />
              </span>{" "}
              You’re in control of every action
            </div>
          </section>
          <section className="context-block recent-block">
            <span className="eyebrow">THIS CONVERSATION</span>
            <div className="workflow-state">
              <span className={`workflow-dot ${state.toLowerCase()}`} />
              <div>
                <strong>
                  {state === "NEW" ? "A fresh start" : titleCase(state)}
                </strong>
                <p>
                  {state === "AWAITING_CONFIRMATION"
                    ? "Waiting for your go-ahead"
                    : state === "NEEDS_CLARIFICATION"
                      ? "A little context will help"
                      : state === "ESCALATED"
                        ? "Context saved for human review"
                        : "Your session stays with you"}
                </p>
              </div>
            </div>
            {messages
              .filter((item) => item.traceId)
              .slice(-3)
              .reverse()
              .map((item, index) => (
                <button
                  className="recent-request"
                  key={index}
                  onClick={() => onTrace(item.traceId!)}
                >
                  <span>
                    {item.text.slice(0, 67)}
                    {item.text.length > 67 ? "…" : ""}
                  </span>
                  <ArrowUpRight size={14} />
                </button>
              ))}
          </section>
          <section className="human-card">
            <Headphones size={22} strokeWidth={1.5} />
            <h3>
              Sometimes, a person
              <br />
              is the right next step.
            </h3>
            <p>
              We’ll keep the context, so you don’t have to start from scratch.
            </p>
            <button
              className="text-link"
              disabled={!customer || busy}
              onClick={() =>
                send(
                  "Please escalate this conversation to a human support representative.",
                )
              }
            >
              Request human support <ArrowRight size={15} />
            </button>
          </section>
        </aside>
      </div>
    </div>
  );
}
function LockIcon() {
  return <ShieldCheck size={12} />;
}
