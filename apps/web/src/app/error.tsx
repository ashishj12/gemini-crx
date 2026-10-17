"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <main className="fatal">
      <span className="eyebrow">LET’S RECONNECT</span>
      <h1>
        Something interrupted
        <br />
        your workspace.
      </h1>
      <p>
        Your account actions remain protected. Reload the workspace to continue.
      </p>
      <button className="button primary" onClick={reset}>
        Try again
      </button>
    </main>
  );
}
