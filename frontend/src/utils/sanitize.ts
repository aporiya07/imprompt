/**
 * Typography guardrails for application-generated copy (no em dash in product UI).
 * Must NOT be applied to factual Visual DNA / observed reference typography.
 */
const DASH_RE = /\s*[—―]\s*/g;

export function sanitizeText(text: string): string {
  return text.replace(DASH_RE, ", ").replace(/\s{2,}/g, " ").trim();
}

export function sanitizeDeep<T>(value: T): T {
  if (typeof value === "string") {
    return sanitizeText(value) as unknown as T;
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeDeep(item)) as unknown as T;
  }
  if (value !== null && typeof value === "object") {
    const out: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value as Record<string, unknown>)) {
      out[key] = sanitizeDeep(val);
    }
    return out as T;
  }
  return value;
}

/** Sanitize only presentation fields; leave visual_dna and factual panel text intact. */
export function sanitizeApiPayload<T extends Record<string, unknown>>(data: T): T {
  const out: Record<string, unknown> = { ...data };
  if (typeof out.prompt === "string") out.prompt = sanitizeText(out.prompt);
  if (typeof out.negative_prompt === "string") out.negative_prompt = sanitizeText(out.negative_prompt);
  if (typeof out.layout_description === "string") out.layout_description = sanitizeText(out.layout_description);
  if (out.prompt_quality && typeof out.prompt_quality === "object") {
    out.prompt_quality = sanitizeDeep(out.prompt_quality);
  }
  if (out.quality && typeof out.quality === "object") {
    out.quality = sanitizeDeep(out.quality);
  }
  if (Array.isArray(out.shots)) {
    out.shots = out.shots.map((shot) => {
      if (!shot || typeof shot !== "object") return shot;
      const s = { ...(shot as Record<string, unknown>) };
      if (typeof s.prompt === "string") s.prompt = sanitizeText(s.prompt);
      if (typeof s.negative_prompt === "string") s.negative_prompt = sanitizeText(s.negative_prompt);
      if (typeof s.title === "string") s.title = sanitizeText(s.title);
      if (s.quality && typeof s.quality === "object") s.quality = sanitizeDeep(s.quality);
      return s;
    });
  }
  if (out.creative_intent && typeof out.creative_intent === "object") {
    out.creative_intent = sanitizeDeep(out.creative_intent);
  }
  // visual_dna and panels[].summary/title from observation stay untouched
  return out as T;
}
