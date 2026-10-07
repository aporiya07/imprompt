"""Provider construction and role execution with retry + fallback.

Cost rule: the fallback is only attempted after the primary actually fails.
"""
import asyncio
import logging
import time
from dataclasses import dataclass

from app.config import Settings
from app.providers.base import AIProvider
from app.providers.gemini import GeminiProvider
from app.providers.openai import OpenAIProvider
from app.utils.errors import AppError, MissingAPIKeyError, ProviderError

log = logging.getLogger("ipa.providers")

_TRANSIENT_CODES = {"rate_limited", "provider_timeout", "provider_unavailable"}


@dataclass
class RoleConfig:
    role: str  # "vision" | "prompt"
    primary: str
    primary_model: str
    fallback: str | None = None
    fallback_model: str | None = None


class RoleExecutor:
    """Runs one pipeline role (vision or prompt) against its provider chain."""

    def __init__(self, cfg: RoleConfig, providers: dict[str, AIProvider], retry_backoff: float = 1.0):
        self.cfg = cfg
        self.providers = providers
        self.retry_backoff = retry_backoff

    def _chain(self) -> list[tuple[str, str]]:
        chain = [(self.cfg.primary, self.cfg.primary_model)]
        if self.cfg.fallback and self.cfg.fallback != self.cfg.primary:
            chain.append((self.cfg.fallback, self.cfg.fallback_model or self.cfg.primary_model))
        return chain

    async def run_vision(self, *, image_bytes: bytes, mime: str, system_prompt: str, user_prompt: str) -> tuple[str, str, str]:
        return await self._run(image_bytes=image_bytes, mime=mime, system_prompt=system_prompt, user_prompt=user_prompt)

    async def run_text(self, *, system_prompt: str, user_prompt: str) -> tuple[str, str, str]:
        return await self._run(system_prompt=system_prompt, user_prompt=user_prompt)

    async def _run(self, **kwargs) -> tuple[str, str, str]:
        last: Exception | None = None
        missing_keys: list[str] = []
        attempted_call = False
        for provider_id, model in self._chain():
            provider = self.providers.get(provider_id)
            if provider is None:
                hint = "GEMINI_API_KEY" if provider_id == "gemini" else "OPENAI_API_KEY"
                missing_keys.append(f"{self.cfg.role} provider '{provider_id}' is configured but {hint} is not set")
                last = MissingAPIKeyError(f"Provider '{provider_id}' is not available: {hint} is missing.")
                log.warning("role=%s provider=%s unavailable: %s", self.cfg.role, provider_id, hint)
                continue
            for attempt in range(2):
                attempted_call = True
                try:
                    started = time.perf_counter()
                    if "image_bytes" in kwargs:
                        text = await provider.analyze_image(model=model, **kwargs)
                    else:
                        text = await provider.generate_text(model=model, **kwargs)
                    log.info(
                        "ai ok role=%s provider=%s model=%s latency=%.2fs",
                        self.cfg.role, provider_id, model, time.perf_counter() - started,
                    )
                    return text, provider_id, model
                except AppError as e:
                    last = e
                    log.warning(
                        "ai fail role=%s provider=%s model=%s attempt=%s error=%s (%s)",
                        self.cfg.role, provider_id, model, attempt + 1, e.code, e.message,
                    )
                    if e.code in _TRANSIENT_CODES and attempt == 0:
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
        fallback=fallback,
        fallback_model=_pick_model(fallback, role, settings) if fallback else None,
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
