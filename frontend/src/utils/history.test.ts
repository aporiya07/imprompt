import { beforeEach, describe, expect, it } from "vitest";
import { clearHistory, isValidHistoryItem, loadHistory, saveHistoryItem } from "./history";
import { sampleDna, sampleIntent } from "../test/fixtures";

describe("history", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("rejects malformed entries", () => {
    expect(isValidHistoryItem(null)).toBe(false);
    expect(isValidHistoryItem({ id: 1 })).toBe(false);
    expect(isValidHistoryItem({ id: "x", ts: 1, mode: "recreate", targetModel: "generic", name: "a", thumbnail: "", prompt: "p", dna: {}, negative: null })).toBe(true);
  });

  it("ignores malformed localStorage payloads", () => {
    localStorage.setItem("imprompt.history.v1", JSON.stringify([{ broken: true }, "nope"]));
    expect(loadHistory()).toEqual([]);
  });

  it("migrates legacy ipa.history.v1 and persists intent", () => {
    const legacy = [
      {
        id: "legacy-1",
        ts: 1,
        mode: "recreate",
        targetModel: "generic",
        name: "shot.jpg",
        thumbnail: "data:image/jpeg;base64,xx",
        dna: sampleDna,
        intent: sampleIntent,
        prompt: "hello",
        negative: null,
      },
    ];
    localStorage.setItem("ipa.history.v1", JSON.stringify(legacy));
    const loaded = loadHistory();
    expect(loaded).toHaveLength(1);
    expect(loaded[0].intent?.primary_goal).toBe(sampleIntent.primary_goal);
    expect(loaded[0].historySchemaVersion).toBe(1);
    expect(localStorage.getItem("imprompt.history.v1")).toBeTruthy();
  });

  it("round-trips restore fields including creative intent", () => {
    const items = saveHistoryItem({
      historySchemaVersion: 1,
      id: "h1",
      ts: Date.now(),
      mode: "recreate",
      targetModel: "flux",
      name: "a.jpg",
      thumbnail: "data:image/jpeg;base64,xx",
      dna: sampleDna,
      intent: sampleIntent,
      prompt: "prompt text",
      negative: "blur",
      quality: { score: 90, warnings: [], strengths: [] },
      shots: [],
      layout: null,
      panels: [],
    });
    expect(items[0].intent).toEqual(sampleIntent);
    clearHistory();
    expect(loadHistory()).toEqual([]);
  });
});
