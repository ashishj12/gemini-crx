"use client";
import { useState } from "react";
import {
  ArrowRight,
  Check,
  Eye,
  EyeOff,
  LockKeyhole,
  ShieldCheck,
} from "lucide-react";
import { api } from "@/lib/api";
import { Brand } from "./ui";

export function Login({ onSuccess }: { onSuccess: () => Promise<void> }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [visible, setVisible] = useState(false);
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api("login", { username, password });
      setPassword("");
      await onSuccess();
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page">
      <section className="login-story">
        <Brand />
        <div className="connection-art" aria-hidden>
          <div className="orbit o1" />
          <div className="orbit o2" />
          <div className="orbit o3" />
          <span className="connection-node n1" />
          <span className="connection-node n2" />
          <span className="connection-node n3" />
          <div className="connection-center">
            <span>r.</span>
          </div>
        </div>
        <div className="story-copy">
          <span className="eyebrow light">A BETTER CONNECTION STARTS HERE</span>
          <h1>
            Support that
            <br />
            gets you
            <br />
            <em>somewhere.</em>
          </h1>
          <p>
            Less back and forth.
            <br />
            More getting on with your day.
          </p>
        </div>
        <div className="story-footer">
          <span>
            <ShieldCheck size={15} /> Secure by design
          </span>
          <span>Connected to a resolution. ↗</span>
        </div>
      </section>
      <section className="login-form-side">
        <div className="login-top">
          <span>YOUR SUPPORT, SIMPLIFIED</span>
          <span className="small-label">01 / SIGN IN</span>
        </div>
        <div className="login-content">
          <div className="login-lock">
            <LockKeyhole size={21} strokeWidth={1.6} />
          </div>
          <span className="eyebrow">WELCOME TO RELAY</span>
          <h2>
            A little less friction.
            <br />A lot more resolved.
          </h2>
          <p>
            Sign in to get clear answers about your account,
            <br className="desktop-br" /> your bill, and your connection.
          </p>
          <form onSubmit={submit}>
            <label htmlFor="username">Username</label>
            <input
              id="username"
              autoComplete="username"
              placeholder="Your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              maxLength={100}
            />
            <label htmlFor="password">Password</label>
            <div className="password-input">
              <input
                id="password"
                type={visible ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                maxLength={200}
              />
              <button
                type="button"
                className="icon-button"
                aria-label={visible ? "Hide password" : "Show password"}
                onClick={() => setVisible(!visible)}
              >
                {visible ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
            {error && (
              <div className="notice error" role="alert">
                {error}
              </div>
            )}
            <button className="button primary login-submit" disabled={busy}>
              {busy ? "Connecting…" : "Continue to your workspace"}
              <ArrowRight size={17} />
            </button>
          </form>
          <div className="secure-note">
            <ShieldCheck size={14} /> Your account. Your information. Always
            protected.
          </div>
          <details className="sample-accounts">
            <summary>
              Exploring the challenge? Use a sample account <span>+</span>
            </summary>
            <p>
              Supplied synthetic users only. These credentials never access real
              customer records.
            </p>
            {[
              {
                name: "Alex Morgan",
                user: "alex.morgan",
                pass: "ReviewerPass-1001",
                role: "Home internet",
              },
              {
                name: "Jordan Lee",
                user: "jordan.lee",
                pass: "ReviewerPass-1002",
                role: "Mobile",
              },
              {
                name: "Taylor Smith",
                user: "support.agent",
                pass: "ReviewerPass-3001",
                role: "Reviewer / operations",
              },
            ].map((a) => (
              <button
                key={a.user}
                type="button"
                onClick={() => {
                  setUsername(a.user);
                  setPassword(a.pass);
                  setError("");
                }}
              >
                <span>
                  {a.name}
                  <small>{a.role}</small>
                </span>
                <ArrowRight size={16} />
              </button>
            ))}
          </details>
        </div>
        <div className="login-bottom">
          <span>Built for clearer conversations.</span>
          <span>RELAY CX © 2026</span>
        </div>
      </section>
    </main>
  );
}
