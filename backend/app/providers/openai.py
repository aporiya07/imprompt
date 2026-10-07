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
    RateLimitError as OpenAIRateLimitError,
    UnprocessableEntityError,
)

from app.utils.errors import (
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
        self, *, model: str, image_bytes: bytes, mime: str, system_prompt: str, user_prompt: str, temperature: float = 0.2
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
        return await self._create(model, messages, temperature)

    async def generate_text(self, *, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self._create(model, messages, temperature)

    async def _create(self, model: str, messages: list, temperature: float) -> str:
        kwargs = {"model": model, "messages": messages, "response_format": {"type": "json_object"}}
        try:
            try:
                response = await self._client.chat.completions.create(**kwargs, temperature=temperature)
            except BadRequestError as e:
                # Some newer models reject custom temperature values; retry without it.
                if "temperature" in str(e).lower():
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
        content = response.choices[0].message.content if response.choices else None
        return (content or "").strip()
