"""Provider abstraction: one vendor SDK wrapper implementing both vision and text generation."""
from abc import ABC, abstractmethod


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
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
        """Return the raw model text for an image analysis call (expected to contain JSON).

        Implementations raise MalformedAIResponseError when the provider reports a
        truncated response, so truncation flows through the retry/fallback budget.
        """

    @abstractmethod
    async def generate_text(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.8,
        max_output_tokens: int | None = None,
    ) -> str:
        """Return the raw model text for a text-only call (expected to contain JSON)."""
