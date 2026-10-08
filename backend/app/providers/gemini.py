import asyncio

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.utils.errors import (
    AppError,
    MalformedAIResponseError,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, timeout: float = 120.0):
        self._client = genai.Client(api_key=api_key)
        self._timeout = timeout

    async def analyze_image(
        self,
        *,
        model: str,
        image_bytes: bytes,
        mime: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_output_tokens: int | None = None,
    ) -> str:
        contents: list = [types.Part.from_bytes(data=image_bytes, mime_type=mime), user_prompt]
        return await self._call(model, contents, system_prompt, temperature, max_output_tokens)

    async def generate_text(
        self, *, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.8,
        max_output_tokens: int | None = None,
    ) -> str:
        return await self._call(model, user_prompt, system_prompt, temperature, max_output_tokens)

    async def _call(
        self, model: str, contents, system_prompt: str, temperature: float, max_output_tokens: int | None
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            response_mime_type="application/json",
            max_output_tokens=max_output_tokens,
        )
        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(model=model, contents=contents, config=config),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError:
            raise ProviderTimeoutError(f"Gemini call timed out after {self._timeout:.0f}s.")
        except genai_errors.APIError as e:
            raise self._map(e)
        except AppError:
            raise
        except Exception as e:
            raise ProviderUnavailableError(f"Gemini call failed: {type(e).__name__}: {e}")
        if response is not None and response.candidates:
            finish = getattr(response.candidates[0], "finish_reason", None)
            if finish is not None and "MAX_TOKENS" in str(finish):
                raise MalformedAIResponseError("Gemini response was truncated by the output token limit.")
        text = (response.text or "").strip() if response is not None else ""
        if not text:
            raise ProviderError("Gemini returned an empty response.")
        return text

    @staticmethod
    def _map(e: genai_errors.APIError) -> AppError:
        code = getattr(e, "code", None) or 0
        message = str(getattr(e, "message", None) or e)
        if code == 429:
            return RateLimitError(f"Gemini rate limit hit: {message}")
        if code == 404:
            return ProviderError(f"Gemini model not found or unavailable: {message}")
        if code in (401, 403):
            return ProviderError(f"Gemini rejected the API key: {message}")
        if code >= 500:
            return ProviderUnavailableError(f"Gemini server error ({code}): {message}")
        return ProviderError(f"Gemini error ({code}): {message}")
