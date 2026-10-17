import { NextRequest, NextResponse } from "next/server";
import { allowedPath, upstreamPath, sameOrigin } from "@/lib/proxy-policy";

export const dynamic = "force-dynamic";
async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const path = (await context.params).path.join("/");
  if (!allowedPath(path))
    return NextResponse.json({ error: "not_found" }, { status: 404 });
  if (
    request.method === "POST" &&
    !sameOrigin(
      request.headers.get("origin"),
      request.headers.get("host"),
      new URL(request.url).protocol,
    )
  ) {
    return NextResponse.json({ error: "origin_denied" }, { status: 403 });
  }
  let body: Uint8Array | undefined;
  if (request.method === "POST") {
    const reader = request.body?.getReader();
    const chunks: Uint8Array[] = [];
    let size = 0;
    if (reader)
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        size += value.byteLength;
        if (size > 8192) {
          await reader.cancel();
          return NextResponse.json(
            { error: "invalid_body_size" },
            { status: 413 },
          );
        }
        chunks.push(value);
      }
    body = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) {
      body.set(chunk, offset);
      offset += chunk.length;
    }
  }
  try {
    const base = process.env.RELAY_API_URL ?? "http://127.0.0.1:8080";
    const response = await fetch(new URL(upstreamPath(path), base), {
      method: request.method,
      body: body as BodyInit | undefined,
      redirect: "error",
      cache: "no-store",
      signal: AbortSignal.timeout(120000),
      headers: {
        "Content-Type":
          request.headers.get("content-type") ?? "application/json",
        Cookie: request.headers.get("cookie") ?? "",
        ...(request.headers.get("origin")
          ? { Origin: request.headers.get("origin")! }
          : {}),
      },
    });
    const headers = new Headers({
      "Content-Type": "application/json",
      "Cache-Control": "no-store",
    });
    const cookie = response.headers.get("set-cookie");
    if (cookie) headers.set("set-cookie", cookie);
    return new NextResponse(await response.arrayBuffer(), {
      status: response.status,
      headers,
    });
  } catch {
    return NextResponse.json(
      { error: "upstream_unavailable" },
      { status: 503 },
    );
  }
}
export { proxy as GET, proxy as POST };
