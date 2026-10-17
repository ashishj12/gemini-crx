import { describe, expect, test } from "bun:test";
import { allowedPath, upstreamPath, sameOrigin } from "./proxy-policy";
describe("same-origin gateway boundary", () => {
  test("allows only supported business routes and bound trace identifiers", () => {
    expect(upstreamPath("chat")).toBe("/api/chat");
    expect(upstreamPath("health")).toBe("/health");
    expect(allowedPath("traces/TRACE-" + "a".repeat(32))).toBe(true);
  });
  test("rejects arbitrary endpoints, traversal and URL injection", () => {
    for (const route of [
      "https://evil.test",
      "../login",
      "accounts/ACC-2002",
      "traces/../../secret",
      "ops/credentials",
      "//evil.test",
    ]) {
      expect(allowedPath(route)).toBe(false);
      expect(() => upstreamPath(route)).toThrow();
    }
  });
});

test("checks the public host instead of the internal Next.js bind address", () => {
  expect(sameOrigin("http://127.0.0.1:3000", "127.0.0.1:3000", "http:")).toBe(
    true,
  );
  expect(sameOrigin("https://evil.test", "127.0.0.1:3000", "http:")).toBe(
    false,
  );
  expect(sameOrigin("http://127.0.0.1:3001", "127.0.0.1:3000", "http:")).toBe(
    false,
  );
  expect(sameOrigin("null", "127.0.0.1:3000", "http:")).toBe(false);
});
