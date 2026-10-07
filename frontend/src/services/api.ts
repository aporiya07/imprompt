import type {
  AnalyzeData,
  FetchedImageData,
  GeneratePromptData,
  Mode,
  RefineData,
  TargetModel,
  VisualDNA,
  CreativeIntent,
} from "../types";
import { AppError } from "./errors";

export const DEFAULT_MODELS: TargetModel[] = [
  { id: "generic", name: "Generic", supports_negative: true, soft_char_limit: null },
  { id: "gemini", name: "Gemini (Nano Banana)", supports_negative: false, soft_char_limit: null },
  { id: "openai", name: "GPT Image (OpenAI)", supports_negative: false, soft_char_limit: null },
  { id: "flux", name: "FLUX", supports_negative: true, soft_char_limit: null },
  { id: "midjourney", name: "Midjourney", supports_negative: false, soft_char_limit: 1500 },
  { id: "stable_diffusion", name: "Stable Diffusion", supports_negative: true, soft_char_limit: null },
];

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new AppError("network", "Cannot reach the backend.");
  }
  const envelope = await res.json().catch(() => null);
  if (!res.ok || !envelope || envelope.success !== true) {
    const err = envelope?.error;
    const code = err?.code ?? `http_${res.status}`;
    const message = err?.message ?? `Request failed (${res.status}).`;
    throw new AppError(code, message);
  }
  return envelope.data as T;
}

export interface AnalyzePayload {
  image: string;
  mode: Mode;
  target_model: string;
  instruction?: string;
  generate_prompt: boolean;
}

export interface GeneratePayload {
  visual_dna: VisualDNA;
  creative_intent?: CreativeIntent;
  mode: Mode;
  target_model: string;
  instruction?: string;
}

export interface RefinePayload {
  visual_dna: VisualDNA;
  creative_intent?: CreativeIntent;
  current_prompt: string;
  instruction: string;
  mode: Mode;
  target_model: string;
}

export const api = {
  async models(): Promise<TargetModel[]> {
    try {
      const res = await fetch("/api/models");
      if (!res.ok) return DEFAULT_MODELS;
      const envelope = await res.json();
      const models = envelope?.data?.models;
      return Array.isArray(models) && models.length > 0 ? models : DEFAULT_MODELS;
    } catch {
      return DEFAULT_MODELS;
    }
  },

  analyze: (payload: AnalyzePayload) => post<AnalyzeData>("/api/analyze", payload),
  generatePrompt: (payload: GeneratePayload) => post<GeneratePromptData>("/api/generate-prompt", payload),
  refinePrompt: (payload: RefinePayload) => post<RefineData>("/api/refine-prompt", payload),
  fetchImage: (url: string) => post<FetchedImageData>("/api/fetch-image", { url }),
};
