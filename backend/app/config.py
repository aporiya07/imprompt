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

    gemini_vision_model: str = "gemini-2.5-flash"
    gemini_prompt_model: str = "gemini-2.5-flash"
    openai_vision_model: str = "gpt-4.1"
    openai_prompt_model: str = "gpt-4.1"

    max_image_mb: float = 10.0
    max_image_pixels: int = 2048
    ai_timeout_seconds: float = 120.0
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
