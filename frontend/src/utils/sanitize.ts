/**
 * Typography guardrails for AI-generated copy (UI rules: no em dash in the product).
 * Applied to every API payload before it reaches the UI, so generated text can
 * never surface a banned character. Punctuation is chosen contextually rather
 * than blindly substituting a hyphen. The regex below necessarily contains the
 * banned characters; they are removed, never displayed.
 */
const DASH_RE = /\s*[—―]\s*/g; // em dash and horizontal bar, the characters this filter strips

export function sanitizeText(text: string): string {
  // An em dash used as an aside or list separator reads best as a comma.
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
