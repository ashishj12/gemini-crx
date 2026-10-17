"use client";
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  Bell,
  ChevronRight,
  CircleHelp,
  FlaskConical,
  Headphones,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import type { Mode, Session } from "@/lib/types";
import { Brand, Busy, ModeBadge } from "./ui";
import { Login } from "./login";
import { SupportWorkspace } from "./support-workspace";
import { ReviewWorkspace } from "./review-workspace";
import { OperationsWorkspace } from "./operations-workspace";
import { TraceDrawer } from "./trace-drawer";
type View = "support" | "review" | "operations";
const navigation = [
  {
    id: "support" as View,
    label: "Customer support",
    icon: MessageSquare,
    short: "Support",
  },
  {
    id: "review" as View,
    label: "Review lab",
    icon: FlaskConical,
    short: "Review lab",
  },
  {
    id: "operations" as View,
    label: "Operations",
    icon: Activity,
    short: "Operations",
  },
];
export function Workspace() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<View>("support");
  const [trace, setTrace] = useState<string | null>(null);
  const [serviceOnline, setServiceOnline] = useState(false);
  const [error, setError] = useState("");
  async function restore() {
    try {
      const current = await api<Session>("session");
      setSession(current);
      if (current.roles.includes("support-agent")) setView("operations");
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 401))
        setError((e as Error).message);
      setSession(null);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    restore();
    api("health")
      .then(() => setServiceOnline(true))
      .catch(() => setServiceOnline(false));
  }, []);
  async function logout() {
    try {
      await api("logout", {});
      setSession(null);
      setTrace(null);
      setView("support");
    } catch (e) {
      setError((e as Error).message);
    }
  }
  const onMode = (mode: Mode) =>
    setSession((current) => (current ? { ...current, mode } : null));
  if (loading)
    return (
      <div className="app-loading">
        <Brand />
        <Busy />
      </div>
    );
  if (!session) return <Login onSuccess={restore} />;
  const currentNav = navigation.find((item) => item.id === view)!;
  return (
    <div className="app-shell">
      <a className="skip-link" href="#workspace-main">
        Skip to workspace
      </a>
      <aside className="sidebar">
        <Brand />
        <div className="workspace-name">
          <span className="workspace-icon">
            <LayoutDashboard size={15} />
          </span>
          <div>
            Resolution workspace<small>Telecom & connected services</small>
          </div>
          <span className="workspace-chevron">⌄</span>
        </div>
        <span className="nav-heading">YOUR WORKSPACE</span>
        <nav aria-label="Main workspace">
          {navigation.map((item) => (
            <button
              key={item.id}
              className={view === item.id ? "active" : ""}
              onClick={() => setView(item.id)}
              aria-current={view === item.id ? "page" : undefined}
            >
              <item.icon size={18} strokeWidth={1.6} />
              <span>{item.label}</span>
              {view === item.id && <span className="nav-active-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className="note-icon">
              <ShieldCheck size={17} />
            </span>
            <strong>
              Real people.
              <br />
              Real resolutions.
            </strong>
            <p>Every step backed by verified information.</p>
            <span>
              THAT’S THE RELAY WAY <ArrowUpRight size={13} />
            </span>
          </div>
          <div className="signed-in">
            <span className="avatar">
              {session.roles.includes("support-agent")
                ? "TS"
                : session.customerId.endsWith("1")
                  ? "AM"
                  : "JL"}
            </span>
            <div>
              <strong>{session.customerId}</strong>
              <small>
                {session.roles.includes("support-agent")
                  ? "Support representative"
                  : "Customer account"}
              </small>
            </div>
            <button
              className="icon-button"
              aria-label="Sign out"
              onClick={logout}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumbs">
            <span>Workspace</span>
            <ChevronRight size={13} />
            <strong>{currentNav.label}</strong>
          </div>
          <div className="topbar-right">
            <span className="service-status">
              <span
                className={`status-dot ${serviceOnline ? "" : "warning"}`}
              />
              {serviceOnline
                ? "Resolution service online"
                : "Connecting to service"}
            </span>
            <span className="topbar-divider" />
            <ModeBadge mode={session.mode} />
            <button
              className="icon-button mobile-logout"
              aria-label="Sign out"
              onClick={logout}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main className="workspace-main" id="workspace-main">
          {error && (
            <div className="notice error" role="alert">
              {error}
              <button className="text-link" onClick={() => setError("")}>
                Dismiss
              </button>
            </div>
          )}
          {session.mode === "DEGRADED" && (
            <div className="notice degraded-notice">
              <CircleHelp size={17} />
              <span>
                Live AI is currently unavailable. Supported account workflows
                remain available, with the same security checks.
              </span>
            </div>
          )}
          {view === "support" ? (
            <SupportWorkspace
              key={session.customerId}
              session={session}
              onMode={onMode}
              onTrace={setTrace}
            />
          ) : view === "review" ? (
            <ReviewWorkspace session={session} onTrace={setTrace} />
          ) : (
            <OperationsWorkspace session={session} onTrace={setTrace} />
          )}
          <footer className="workspace-footer">
            <span>
              <span className="footer-mark">r.</span>Connected to a resolution.
            </span>
            <span>VERIFIED INFORMATION. CLEARER OUTCOMES.</span>
          </footer>
        </main>
      </div>
      <TraceDrawer traceId={trace} onClose={() => setTrace(null)} />
    </div>
  );
}
