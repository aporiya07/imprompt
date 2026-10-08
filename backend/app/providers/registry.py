"""Provider construction and role execution with validation, retry, and fallback.

Cost rules:
- the fallback is attempted only after the primary actually fails
- every provider response is passed through the caller's `validate` callable
  INSIDE the execution boundary, so malformed JSON, truncation, and schema
  failures all flow through the same retry/fallback strategy as network errors
- the attempt budget is deterministic: primary gets `primary_attempts` calls,
  the fallback gets `fallback_attempts` calls, and that is the hard maximum
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from app.config import Settings
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider
from app.providers.openai import OpenAIProvider
from app.utils.errors import AppError, MissingAPIKeyError, ProviderError

log = logging.getLogger("imprompt.providers")

T = TypeVar("T")

# Errors that are worth retrying or falling back for.
_RETRYABLE_CODES = {"rate_limited", "provider_timeout", "provider_unavailable", "malformed_ai_response"}


@dataclass
class ProviderOutcome:
    value: Any
    provider: str
    model: str
    fallback_used: bool


@dataclass
class RoleConfig:
    role: str  # "vision" | "prompt"
    primary: str
    primary_model: str
    primary_attempts: int = 2
    fallback: str | None = None
    fallback_model: str | None = None
    fallback_attempts: int = 1


class RoleExecutor:
    """Runs one pipeline role (vision or prompt) against its provider chain."""

    def __init__(self, cfg: RoleConfig, providers: dict[str, AIProvider], retry_backoff: float = 1.0):
        self.cfg = cfg
        self.providers = providers
        self.retry_backoff = retry_backoff

    def _chain(self) -> list[tuple[str, str, int]]:
        chain = [(self.cfg.primary, self.cfg.primary_model, self.cfg.primary_attempts)]
        if self.cfg.fallback and self.cfg.fallback != self.cfg.primary:
            chain.append(
                (self.cfg.fallback, self.cfg.fallback_model or self.cfg.primary_model, self.cfg.fallback_attempts)
            )
        return chain

    async def run_vision(
        self,
        *,
        image_bytes: bytes,
        mime: str,
        system_prompt: str,
        user_prompt: str,
        validate: Callable[[str], T],
        max_output_tokens: int | None = None,
    ) -> ProviderOutcome:
        return await self._run(
            image_bytes=image_bytes,
            mime=mime,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            validate=validate,
            max_output_tokens=max_output_tokens,
        )

    async def run_text(
        self, *, system_prompt: str, user_prompt: str, validate: Callable[[str], T], max_output_tokens: int | None = None
    ) -> ProviderOutcome:
        return await self._run(
            system_prompt=system_prompt, user_prompt=user_prompt, validate=validate, max_output_tokens=max_output_tokens
        )

    async def _run(self, **kwargs) -> ProviderOutcome:
        validate: Callable[[str], T] = kwargs.pop("validate")
        max_tokens = kwargs.pop("max_output_tokens", None)
        last: Exception | None = None
        missing_keys: list[str] = []
        attempted_call = False
        total_attempts = 0
        for provider_id, model, attempts in self._chain():
            provider = self.providers.get(provider_id)
            if provider is None:
                hint = "GEMINI_API_KEY" if provider_id == "gemini" else "OPENAI_API_KEY"
                missing_keys.append(
                    f"{self.cfg.role} provider '{provider_id}' is configured but {hint} is not set"
                )
                last = MissingAPIKeyError(f"Provider '{provider_id}' is not available: {hint} is missing.")
                log.warning("role=%s provider=%s unavailable: %s", self.cfg.role, provider_id, hint)
                continue
            for attempt in range(1, max(1, attempts) + 1):
                attempted_call = True
                total_attempts += 1
                try:
                    started = time.perf_counter()
                    if "image_bytes" in kwargs:
                        text = await provider.analyze_image(model=model, max_output_tokens=max_tokens, **kwargs)
                    else:
                        text = await provider.generate_text(model=model, max_output_tokens=max_tokens, **kwargs)
                    value = validate(text)
                    log.info(
                        "ai ok role=%s provider=%s model=%s attempt=%d fallback=%s latency=%.2fs",
                        self.cfg.role, provider_id, model, attempt, provider_id != self.cfg.primary,
                        time.perf_counter() - started,
                    )
                    return ProviderOutcome(
                        value=value, provider=provider_id, model=model, fallback_used=provider_id != self.cfg.primary
                    )
                except AppError as e:
                    last = e
                    log.warning(
                        "ai fail role=%s provider=%s model=%s attempt=%d/%d error=%s (%s)",
                        self.cfg.role, provider_id, model, attempt, attempts, e.code, e.message,
                    )
                    if e.code in _RETRYABLE_CODES and attempt < attempts:
                        await asyncio.sleep(self.retry_backoff)
                        continue
                    break
        if not attempted_call and missing_keys:
            raise MissingAPIKeyError(
                "No API key available for the configured providers. "
                + "; ".join(missing_keys)
                + ". Add the key(s) to backend/.env and restart the server."
            )
        raise last or ProviderError(f"No AI provider is available for the {self.cfg.role} role.")


@dataclass
class Runtime:
    providers: dict[str, AIProvider]
    vision: RoleExecutor
    prompt: RoleExecutor


def _pick_model(provider_id: str, role: str, settings: Settings) -> str:
    if provider_id == "gemini":
        return settings.gemini_vision_model if role == "vision" else settings.gemini_prompt_model
    if provider_id == "openai":
        return settings.openai_vision_model if role == "vision" else settings.openai_prompt_model
    raise ValueError(f"Unknown provider id: {provider_id}")


def _role_config(settings: Settings, role: str) -> RoleConfig:
    primary = (settings.vision_provider if role == "vision" else settings.prompt_provider).strip().lower()
    if primary not in ("gemini", "openai"):
        primary = "gemini" if role == "vision" else "openai"
    fallback = None
    if settings.enable_fallback:
        fallback = "openai" if primary == "gemini" else "gemini"
    return RoleConfig(
        role=role,
        primary=primary,
        primary_model=_pick_model(primary, role, settings),
        primary_attempts=max(1, settings.ai_primary_attempts),
        fallback=fallback,
        fallback_model=_pick_model(fallback, role, settings) if fallback else None,
        fallback_attempts=max(1, settings.ai_fallback_attempts) if fallback else 1,
    )


def build_runtime(settings: Settings) -> Runtime:
    providers: dict[str, AIProvider] = {}
    if settings.gemini_api_key:
        providers["gemini"] = GeminiProvider(settings.gemini_api_key, timeout=settings.ai_timeout_seconds)
    if settings.openai_api_key:
        providers["openai"] = OpenAIProvider(settings.openai_api_key, timeout=settings.ai_timeout_seconds)
    return Runtime(
        providers=providers,
        vision=RoleExecutor(_role_config(settings, "vision"), providers),
        prompt=RoleExecutor(_role_config(settings, "prompt"), providers),
    )
