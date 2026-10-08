export class AppError extends Error {
  constructor(
    public code: string,
    message: string,
    public requestId?: string
  ) {
    super(message);
    this.name = "AppError";
  }
}

const FRIENDLY: Record<string, string> = {
  invalid_image: "That file doesn't look like a valid image. Try a different PNG, JPG or WEBP.",
  unsupported_format: "Only PNG, JPG/JPEG and WEBP images are supported.",
  image_too_large: "That image is too large. Please use an image under 10 MB.",
  missing_api_key:
    "The backend is missing an AI API key. Add GEMINI_API_KEY / OPENAI_API_KEY to backend/.env and restart the server.",
  rate_limited: "The AI provider is rate-limiting requests. Wait a few seconds and try again.",
  provider_timeout: "The AI provider took too long to respond. Please try again.",
  provider_unavailable: "The AI provider is temporarily unavailable. Retrying may help.",
  provider_error: "The AI provider returned an error. Retrying may help; check the backend logs for details.",
  malformed_ai_response: "The AI returned an unexpected response. Trying again usually fixes this.",
  bad_request: "The request was rejected. Check the input and try again.",
  network:
    "Cannot reach the backend. Make sure the API server is running (uv run uvicorn app.main:app --reload --port 8000 inside backend/).",
  http_500:
    "The API returned an unexpected 500. Make sure the backend is running on the proxy target (default port 8000).",
  internal_error: "Unexpected server error. Check the backend logs for details.",
};

export function friendlyMessage(err: unknown): string {
  if (err instanceof AppError) {
    return FRIENDLY[err.code] ?? err.message;
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Something went wrong.";
}

export function requestIdOf(err: unknown): string | undefined {
  return err instanceof AppError ? err.requestId : undefined;
}

export function errorCodeOf(err: unknown): string | undefined {
  return err instanceof AppError ? err.code : undefined;
}
