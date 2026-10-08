import type {
  AnalyzeData,
  FetchedImageData,
  GeneratePromptData,
  Mode,
  PromptQuality,
  RefineData,
  TargetModel,
  VisualDNA,
  CreativeIntent,
} from "../types";
import { AppError } from "./errors";
import { sanitizeApiPayload } from "../utils/sanitize";

export const DEFAULT_MODELS: TargetModel[] = [
  { id: "generic", name: "Generic", supports_negative: true, soft_char_limit: null },
  { id: "gemini", name: "Gemini (Nano Banana)", supports_negative: false, soft_char_limit: null },
  { id: "openai", name: "GPT Image (OpenAI)", supports_negative: false, soft_char_limit: null },
  { id: "flux", name: "FLUX", supports_negative: true, soft_char_limit: null },
  { id: "midjourney", name: "Midjourney", supports_negative: false, soft_char_limit: 1500 },
  { id: "stable_diffusion", name: "Stable Diffusion", supports_negative: true, soft_char_limit: null },
];

/** Empty string = same-origin / Vite proxy. Override with VITE_API_BASE_URL. */
export const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, "") ?? "";

function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export function isAbortError(err: unknown): boolean {
  return (
    (err instanceof DOMException && err.name === "AbortError") ||
    (err instanceof Error && err.name === "AbortError")
  );
}

export interface RequestOptions {
  signal?: AbortSignal;
}

async function post<T extends Record<string, unknown>>(
  path: string,
  body: unknown,
  options: RequestOptions = {}
): Promise<T> {
  let res: Response;
  try {
    res = await fetch(apiUrl(path), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: options.signal,
    });
  } catch (err) {
    if (isAbortError(err) || options.signal?.aborted) {
      throw err instanceof Error ? err : new DOMException("Aborted", "AbortError");
    }
    throw new AppError("network", "Cannot reach the backend.");
  }
  const headerRequestId = res.headers.get("x-request-id") ?? undefined;
  const rawText = await res.text();
  type EnvelopeBody = {
    success?: boolean;
    data?: unknown;
    error?: { code?: string; message?: string; request_id?: string };
  };
  let envelope: EnvelopeBody | null = null;
  try {
    envelope = rawText ? (JSON.parse(rawText) as EnvelopeBody) : null;
  } catch {
    envelope = null;
  }
  if (!res.ok || !envelope || envelope.success !== true) {
    const err = envelope?.error;
    // Non-JSON 500s usually mean the Vite proxy could not reach the API, or the
    // server returned an unhandled HTML/text error outside our envelope.
    const fallbackMessage =
      res.status === 500 && !err
        ? "The API returned an unexpected 500. Make sure the backend is running (uv run uvicorn app.main:app --reload --port 8000)."
        : `Request failed (${res.status}).`;
    throw new AppError(
      err?.code ?? `http_${res.status}`,
      err?.message ?? fallbackMessage,
      err?.request_id ?? headerRequestId
    );
  }
  return sanitizeApiPayload(envelope.data as Record<string, unknown>) as T;
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

export interface ValidatePayload {
  prompt: string;
  model: string;
  visual_dna?: VisualDNA;
}

export const api = {
  async models(options: RequestOptions = {}): Promise<TargetModel[]> {
    try {
      const res = await fetch(apiUrl("/api/models"), { signal: options.signal });
      if (!res.ok) return DEFAULT_MODELS;
      const envelope = await res.json();
      const models = envelope?.data?.models;
      return Array.isArray(models) && models.length > 0 ? models : DEFAULT_MODELS;
    } catch (err) {
      if (isAbortError(err)) throw err;
      return DEFAULT_MODELS;
    }
  },

  analyze: (payload: AnalyzePayload, options?: RequestOptions) =>
    post<AnalyzeData & Record<string, unknown>>("/api/analyze", payload, options),

  generatePrompt: (payload: GeneratePayload, options?: RequestOptions) =>
    post<GeneratePromptData & Record<string, unknown>>("/api/generate-prompt", payload, options),

  refinePrompt: (payload: RefinePayload, options?: RequestOptions) =>
    post<RefineData & Record<string, unknown>>("/api/refine-prompt", payload, options),

  fetchImage: (url: string, options?: RequestOptions) =>
    post<FetchedImageData & Record<string, unknown>>("/api/fetch-image", { url }, options),

  validatePrompt: (payload: ValidatePayload, options?: RequestOptions) =>
    post<{ quality: PromptQuality | null } & Record<string, unknown>>(
      "/api/validate-prompt",
      { prompt: payload.prompt, target_model: payload.model, visual_dna: payload.visual_dna },
      options
    ),
};
