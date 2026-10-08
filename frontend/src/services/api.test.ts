import { describe, expect, it, vi } from "vitest";
import { api, isAbortError } from "./api";

describe("api AbortController", () => {
  it("propagates AbortError without wrapping as network failure", async () => {
    const ctrl = new AbortController();
    vi.stubGlobal(
      "fetch",
      vi.fn((_url: RequestInfo | URL, init?: RequestInit) => {
        return new Promise((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => {
            reject(new DOMException("Aborted", "AbortError"));
          });
        });
      })
    );
    const pending = api.analyze(
      {
        image: "data:image/png;base64,xx",
        mode: "recreate",
        target_model: "generic",
        generate_prompt: true,
      },
      { signal: ctrl.signal }
    );
    ctrl.abort();
    await expect(pending).rejects.toSatisfy((err) => isAbortError(err));
  });
});
