import base64

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    OpenAIError,
    PermissionDeniedError,
    UnprocessableEntityError,
)
from openai import (
    RateLimitError as OpenAIRateLimitError,
)

from app.utils.errors import (
    MalformedAIResponseError,
    ProviderError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    RateLimitError,
)


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, timeout: float = 120.0):
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout, max_retries=0)

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
        b64 = base64.b64encode(image_bytes).decode("ascii")
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}", "detail": "auto"}},
                ],
            },
        ]
        return await self._create(model, messages, temperature, max_output_tokens)

    async def generate_text(
        self, *, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.8,
        max_output_tokens: int | None = None,
    ) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self._create(model, messages, temperature, max_output_tokens)

    async def _create(self, model: str, messages: list, temperature: float, max_output_tokens: int | None) -> str:
        kwargs: dict = {"model": model, "messages": messages, "response_format": {"type": "json_object"}}
        if max_output_tokens:
            kwargs["max_completion_tokens"] = max_output_tokens
        try:
            try:
                response = await self._client.chat.completions.create(**kwargs, temperature=temperature)
            except BadRequestError as e:
                # Some models reject custom temperature or completion-token parameter names.
                msg = str(e).lower()
                if "temperature" in msg:
                    response = await self._client.chat.completions.create(**kwargs)
                elif "max_completion_tokens" in msg or "max_tokens" in msg:
                    kwargs.pop("max_completion_tokens", None)
                    response = await self._client.chat.completions.create(**kwargs)
                else:
                    raise
        except APITimeoutError:
            raise ProviderTimeoutError("OpenAI call timed out.")
        except APIConnectionError as e:
            raise ProviderUnavailableError(f"Could not reach OpenAI: {e}")
        except OpenAIRateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit hit: {e}")
        except (AuthenticationError, PermissionDeniedError) as e:
            raise ProviderError(f"OpenAI rejected the API key: {e}")
        except NotFoundError as e:
            raise ProviderError(f"OpenAI model not found: {e}")
        except (InternalServerError, UnprocessableEntityError) as e:
            raise ProviderUnavailableError(f"OpenAI server error: {e}")
        except BadRequestError as e:
            raise ProviderError(f"OpenAI rejected the request: {e}")
        except OpenAIError as e:
            raise ProviderError(f"OpenAI error: {e}")
        if response.choices:
            finish = response.choices[0].finish_reason
            if finish == "length":
                raise MalformedAIResponseError("OpenAI response was truncated by the output token limit.")
        content = response.choices[0].message.content if response.choices else None
        return (content or "").strip()
