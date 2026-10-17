"use client";
import { useEffect, useRef, useState } from "react";
import {
  Check,
  Clock3,
  Copy,
  ExternalLink,
  ShieldCheck,
  X,
  XCircle,
} from "lucide-react";
import { api, titleCase } from "@/lib/api";
import type { TelemetryEvent } from "@/lib/types";
import { Busy } from "./ui";
export function TraceDrawer({
  traceId,
  onClose,
}: {
  traceId: string | null;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    if (!traceId) return;
    setEvents([]);
    setError("");
    dialog.current?.showModal();
    api<TelemetryEvent[]>(`traces/${traceId}`)
      .then(setEvents)
      .catch((e) => setError(e.message));
  }, [traceId]);
  if (!traceId) return null;
  const tools = events.filter((e) => e.eventType === "tool.finished");
  return (
    <dialog
      ref={dialog}
      className="trace-dialog"
      onCancel={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="trace-sheet">
        <header>
          <div>
            <span className="eyebrow">EXECUTION EVIDENCE</span>
            <h2>From request to result.</h2>
          </div>
          <button
            className="icon-button"
            aria-label="Close execution trace"
            onClick={onClose}
          >
            <X size={21} />
          </button>
        </header>
        <p className="muted">
          The checks, sources, and decisions behind this response.
        </p>
        <div className="trace-reference">
          <span>{traceId}</span>
          <button
            className="icon-button"
            aria-label="Copy trace ID"
            onClick={() => navigator.clipboard.writeText(traceId)}
          >
            <Copy size={15} />
          </button>
        </div>
        {error && (
          <div className="notice error" role="alert">
            {error}
          </div>
        )}
        {!events.length && !error ? (
          <Busy label="Retrieving execution evidence" />
        ) : (
          <>
            <div className="trace-summary">
              <div>
                <strong>{tools.length}</strong>
                <span>Enterprise checks</span>
              </div>
              <div>
                <strong>
                  {
                    events.filter(
                      (e) => e.eventType === "authorization.allowed",
                    ).length
                  }
                </strong>
                <span>Access checks</span>
              </div>
              <div>
                <strong>
                  {Math.round(
                    events.find((e) => e.eventType === "request.finished")
                      ?.durationMs ?? 0,
                  )}
                  <small>ms</small>
                </strong>
                <span>Request duration</span>
              </div>
            </div>
            <div className="trace-timeline">
              {events.map((event) => (
                <div
                  className={`trace-event ${event.status}`}
                  key={event.eventId}
                >
                  <span className="timeline-marker">
                    {event.status === "failure" || event.status === "denied" ? (
                      <XCircle size={13} />
                    ) : (
                      <Check size={12} />
                    )}
                  </span>
                  <div>
                    <div className="trace-event-heading">
                      <strong>
                        {titleCase(event.eventType.replaceAll(".", " "))}
                      </strong>
                      <span>
                        {event.durationMs > 0
                          ? `${Math.round(event.durationMs)} ms`
                          : ""}
                      </span>
                    </div>
                    <p>
                      {titleCase(event.component)}
                      <span className={`tiny-status ${event.status}`}>
                        {event.status}
                      </span>
                    </p>
                    {Object.keys(event.metadata).length > 0 && (
                      <details>
                        <summary>View check details</summary>
                        <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                      </details>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
        <footer className="trace-footer">
          <ShieldCheck size={14} /> Credentials and protected model instructions
          are excluded.
        </footer>
      </div>
    </dialog>
  );
}
