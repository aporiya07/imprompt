from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    gemini_api_key: str = ""
    openai_api_key: str = ""

    vision_provider: str = "gemini"
    prompt_provider: str = "openai"
    enable_fallback: bool = True

    # Defaults match backend/.env.example; override via env for other deployments.
    gemini_vision_model: str = "gemini-3.8-flash"
    gemini_prompt_model: str = "gemini-3.1-flash-lite"
    openai_vision_model: str = "gpt-6-luna"
    openai_prompt_model: str = "gpt-6-luna"

    max_image_mb: float = 10.0
    # Decoded pixel budget (width * height), enforced before full decode.
    max_image_pixels: int = 24_000_000
    # Longest allowed side after normalization (API cost control, not a security limit).
    max_image_side: int = 2048
    ai_timeout_seconds: float = 120.0
    # Deterministic AI call budget: primary gets two attempts (transient error or
    # malformed output), the fallback provider gets one. Worst case = 3 calls.
    ai_primary_attempts: int = 2
    ai_fallback_attempts: int = 1
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_image_bytes(self) -> int:
        return int(self.max_image_mb * 1024 * 1024)


@lru_cache
def get_settings() -> Settings:
    return Settings()
