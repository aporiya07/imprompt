import { describe, expect, it } from "vitest";
import { sanitizeApiPayload } from "./sanitize";
import { sampleDna } from "../test/fixtures";

describe("sanitizeApiPayload", () => {
  it("does not mutate factual Visual DNA typography", () => {
    const payload = sanitizeApiPayload({
      prompt: "Warm light — soft shadows",
      visual_dna: sampleDna,
    });
    expect(payload.prompt).toBe("Warm light, soft shadows");
    expect((payload.visual_dna as typeof sampleDna).typography.text_content?.[0]).toBe("SALE — 50% OFF");
    expect((payload.visual_dna as typeof sampleDna).reference.overall_description).toContain("SALE — 50% OFF");
  });
});
