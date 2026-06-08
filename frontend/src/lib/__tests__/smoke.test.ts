import { describe, it, expect } from "vitest";

describe("app smoke test", () => {
  it("should pass sanity check", () => {
    expect(1 + 1).toBe(2);
  });
});
