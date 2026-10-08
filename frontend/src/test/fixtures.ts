import type { CreativeIntent, VisualDNA } from "../types";

export const sampleDna: VisualDNA = {
  schema_version: 2,
  reference: {
    reference_type: "photograph",
    reference_type_confidence: "high",
    layout_description: "",
    overall_description: "A portrait with SALE — 50% OFF text",
    analysis_confidence: 0.9,
  },
  subjects: [],
  environment: {},
  composition: {},
  camera: {},
  lighting: {},
  color: { dominant: [], secondary: [], accent: [] },
  style: {},
  mood: {},
  materials: [],
  typography: { present: true, text_content: ["SALE — 50% OFF"] },
  relationships: [],
  elements: [],
  interpretation: {},
  uncertainty: [],
  technical: { aspect_ratio: "3:2", orientation: "landscape" },
};

export const sampleIntent: CreativeIntent = {
  primary_goal: "Recreate a warm editorial portrait",
  aesthetic_direction: "editorial",
  photographic_direction: "natural light",
  composition_strategy: "centered",
  lighting_strategy: "soft key",
  color_strategy: "warm",
  subject_strategy: "single subject",
  environment_strategy: "minimal",
  emotional_direction: "calm",
  preserve: ["warm highlights"],
  flexible: ["background"],
  confidence: "high",
};

export function analyzeSuccess(overrides: Record<string, unknown> = {}) {
  return {
    success: true,
    data: {
      reference_type: "photograph",
      layout_description: null,
      visual_dna: sampleDna,
      creative_intent: sampleIntent,
      prompt: "A warm editorial portrait in soft daylight",
      negative_prompt: "blurry, watermark",
      prompt_error: null,
      prompt_quality: { score: 88, warnings: [], strengths: ["specific lighting"] },
      shots: [],
      panels: [],
      ...overrides,
    },
    error: null,
  };
}
