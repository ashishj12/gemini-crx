const paths = new Set([
  "health",
  "login",
  "logout",
  "session",
  "chat",
  "confirm",
  "scenarios",
  "account/overview",
  "reviewer/run",
  "ops/metrics",
  "ops/events",
  "ops/escalations",
  "ops/health",
]);
export function allowedPath(path: string): boolean {
  return paths.has(path) || /^traces\/TRACE-[a-f0-9]{32}$/.test(path);
}
export function upstreamPath(path: string): string {
  if (!allowedPath(path)) throw new Error("Disallowed API route");
  return path === "health" ? "/health" : `/api/${path}`;
}

export function sameOrigin(
  origin: string | null,
  host: string | null,
  protocol: string,
): boolean {
  if (!origin) return true;
  try {
    const url = new URL(origin);
    return (
      url.host === host && url.protocol === protocol && url.origin === origin
    );
  } catch {
    return false;
  }
}
