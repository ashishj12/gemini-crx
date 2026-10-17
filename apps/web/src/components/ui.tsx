"use client";
import {
  ArrowUpRight,
  Check,
  LoaderCircle,
  Radio,
  ShieldCheck,
} from "lucide-react";
import type { Mode } from "@/lib/types";
export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="brand">
      <span className="brand-mark" aria-hidden>
        r<span />
      </span>
      {!compact && (
        <span>
          relay<span className="brand-period">.</span>
        </span>
      )}
    </div>
  );
}
export function ModeBadge({ mode }: { mode: Mode }) {
  return (
    <span className={`mode-badge ${mode.toLowerCase()}`}>
      <span className="status-dot" />
      {mode === "LIVE_AI"
        ? "Live AI"
        : mode === "DEGRADED"
          ? "Degraded mode"
          : "Reviewer mode"}
    </span>
  );
}
export function Busy({ label = "Loading your workspace" }: { label?: string }) {
  return (
    <div className="busy" role="status">
      <LoaderCircle className="spin" size={18} />
      {label}
    </div>
  );
}
export function SourceLabel({ children }: { children: React.ReactNode }) {
  return (
    <span className="source-label">
      <ShieldCheck size={13} />
      {children}
    </span>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="empty-state">
      <Radio size={30} strokeWidth={1.2} />
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
