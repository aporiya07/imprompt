import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { analyzeSuccess, sampleDna, sampleIntent } from "../test/fixtures";
import { DEFAULT_MODELS } from "../services/api";
import type { UploadedImage } from "../types";

vi.mock("../utils/image", async () => {
  const actual = await vi.importActual<typeof import("../utils/image")>("../utils/image");
  return {
    ...actual,
    thumbnailOf: vi.fn(async () => "data:image/jpeg;base64,thumb"),
  };
});

import { analysisReducer, initialAnalysisState, useAnalysis } from "./useAnalysis";

const image: UploadedImage = {
  dataUrl: "data:image/png;base64,iVBORw0KGgo=",
  width: 64,
  height: 64,
  name: "ref.png",
  size: 120,
};

describe("analysisReducer", () => {
  it("RESET restores canonical initial state without a fake image", () => {
    const dirty = {
      ...initialAnalysisState,
      image,
      dna: sampleDna,
      prompt: "x",
      phase: "result" as const,
    };
    const next = analysisReducer(dirty, { type: "RESET" });
    expect(next.image).toBeNull();
    expect(next.dna).toBeNull();
    expect(next.phase).toBe("setup");
    expect(next.prompt).toBe("");
  });
});

describe("useAnalysis", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
  });

  it("retries prompt immediately after analysis using explicit DNA (no stale null)", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes("/api/analyze")) {
        return new Response(
          JSON.stringify(
            analyzeSuccess({
              prompt: null,
              prompt_error: { code: "provider_error", message: "prompt failed" },
              prompt_quality: null,
            })
          ),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      if (url.includes("/api/generate-prompt")) {
        const body = JSON.parse(String(init?.body ?? "{}"));
        expect(body.visual_dna).toBeTruthy();
        return new Response(
          JSON.stringify({
            success: true,
            data: { prompt: "retry prompt ok", negative_prompt: null, quality: { score: 80, warnings: [], strengths: [] } },
            error: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      throw new Error(`unexpected ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const onHistorySaved = vi.fn();
    const { result } = renderHook(() => useAnalysis({ models: DEFAULT_MODELS, onHistorySaved }));

    act(() => {
      result.current.dispatch({ type: "IMAGE_ADOPTED", image });
    });

    await act(async () => {
      await result.current.analyze();
    });

    expect(result.current.state.dna).toEqual(sampleDna);
    expect(result.current.state.errorAction?.label).toBe("Retry prompt");

    await act(async () => {
      result.current.state.errorAction?.run();
    });

    await waitFor(() => {
      expect(result.current.state.prompt).toBe("retry prompt ok");
    });
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes("/api/generate-prompt"))).toBe(true);
  });

  it("persists history creative intent from response data, not stale state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => {
        return new Response(JSON.stringify(analyzeSuccess()), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      })
    );

    // thumbnailOf uses Image/canvas; stub via failing canvas path returns ""
    const onHistorySaved = vi.fn();
    const { result } = renderHook(() => useAnalysis({ models: DEFAULT_MODELS, onHistorySaved }));

    act(() => {
      result.current.dispatch({ type: "IMAGE_ADOPTED", image });
    });

    await act(async () => {
      await result.current.analyze();
    });

    await waitFor(() => expect(onHistorySaved).toHaveBeenCalled());
    const saved = onHistorySaved.mock.calls[0][0][0];
    expect(saved.intent).toEqual(sampleIntent);
  });

  it("aborts prior analyze when a new one starts (stale response ignored)", async () => {
    const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (!url.includes("/api/analyze")) throw new Error(url);
      const analyzeCount = fetchMock.mock.calls.filter(([u]) => String(u).includes("/api/analyze")).length;
      if (analyzeCount === 1) {
        return new Promise<Response>((_resolve, reject) => {
          init?.signal?.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")));
        });
      }
      return Promise.resolve(
        new Response(JSON.stringify(analyzeSuccess({ prompt: "second wins" })), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        })
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAnalysis({ models: DEFAULT_MODELS, onHistorySaved: vi.fn() }));
    act(() => result.current.dispatch({ type: "IMAGE_ADOPTED", image }));

    let first!: Promise<void>;
    act(() => {
      first = result.current.analyze();
    });
    await act(async () => {
      await result.current.analyze();
    });
    await act(async () => {
      await first;
    });

    expect(result.current.state.prompt).toBe("second wins");
    expect(result.current.state.error).toBeNull();
  });

  it("model switch regenerates prompt without calling analyze/vision", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/generate-prompt")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: { prompt: "flux prompt", negative_prompt: "n", quality: { score: 70, warnings: [], strengths: [] } },
            error: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      throw new Error(`unexpected vision call: ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAnalysis({ models: DEFAULT_MODELS, onHistorySaved: vi.fn() }));
    act(() => {
      result.current.dispatch({
        type: "ANALYSIS_SUCCEEDED",
        dna: sampleDna,
        intent: sampleIntent,
        shots: [],
        panels: [],
        layout: null,
        quality: null,
        prompt: "generic prompt",
        negative: null,
        versions: [],
        activeVersionId: null,
        promptError: null,
      });
      result.current.dispatch({ type: "IMAGE_ADOPTED", image });
      // IMAGE_ADOPTED clears analysis; re-apply result state after
    });
    act(() => {
      result.current.dispatch({
        type: "ANALYSIS_SUCCEEDED",
        dna: sampleDna,
        intent: sampleIntent,
        shots: [],
        panels: [],
        layout: null,
        quality: { score: 80, warnings: [], strengths: [] },
        prompt: "generic prompt",
        negative: null,
        versions: [],
        activeVersionId: null,
        promptError: null,
      });
    });

    await act(async () => {
      result.current.onModelChange("flux");
    });

    await waitFor(() => expect(result.current.state.prompt).toBe("flux prompt"));
    expect(result.current.state.targetModel).toBe("flux");
    expect(result.current.state.dna).toEqual(sampleDna);
    expect(fetchMock.mock.calls.every(([u]) => String(u).includes("/api/generate-prompt"))).toBe(true);
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes("/api/analyze"))).toBe(false);
  });

  it("restores history including shots/layout/quality", () => {
    const { result } = renderHook(() => useAnalysis({ models: DEFAULT_MODELS, onHistorySaved: vi.fn() }));
    act(() => {
      result.current.dispatch({
        type: "HISTORY_RESTORED",
        item: {
          historySchemaVersion: 1,
          id: "h1",
          ts: 1,
          mode: "recreate",
          targetModel: "midjourney",
          name: "board.jpg",
          thumbnail: "data:image/jpeg;base64,xx",
          dna: sampleDna,
          intent: sampleIntent,
          prompt: "master",
          negative: null,
          quality: { score: 91, warnings: [], strengths: ["clear"] },
          shots: [{ index: 1, title: "A", prompt: "shot a", negative_prompt: null, quality: null }],
          layout: "3x3 grid",
          panels: [{ index: 1, title: "A", summary: "s", bounds: { x: 0, y: 0, w: 0.3, h: 0.3 } }],
        },
        version: {
          id: "v1",
          source: "analyze",
          ts: 1,
          prompt: "master",
          negative: null,
          targetModel: "midjourney",
        },
      });
    });
    expect(result.current.state.shots).toHaveLength(1);
    expect(result.current.state.layout).toBe("3x3 grid");
    expect(result.current.state.quality?.score).toBe(91);
    expect(result.current.state.panels[0]?.bounds?.w).toBe(0.3);
    expect(result.current.state.phase).toBe("result");
  });

  it("revalidates prompt on manual edit without calling analyze", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/validate-prompt")) {
        return new Response(
          JSON.stringify({
            success: true,
            data: { quality: { score: 66, warnings: ["edited"], strengths: [] } },
            error: null,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }
      throw new Error(`unexpected ${url}`);
    });
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useAnalysis({ models: DEFAULT_MODELS, onHistorySaved: vi.fn() }));
    act(() => {
      result.current.dispatch({
        type: "ANALYSIS_SUCCEEDED",
        dna: sampleDna,
        intent: sampleIntent,
        shots: [],
        panels: [],
        layout: null,
        quality: { score: 90, warnings: [], strengths: [] },
        prompt: "old",
        negative: null,
        versions: [],
        activeVersionId: null,
        promptError: null,
      });
    });

    await act(async () => {
      await result.current.applyEdit("manually edited prompt");
    });

    expect(result.current.state.prompt).toBe("manually edited prompt");
    expect(result.current.state.quality?.score).toBe(66);
    expect(fetchMock.mock.calls.some(([u]) => String(u).includes("/api/analyze"))).toBe(false);
  });
});
