"""Prompt quality diagnostics (spec Phase 11) — deterministic heuristics only."""
from pydantic import BaseModel, ConfigDict, Field


class PromptQuality(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: int = 100  # 0..100
    warnings: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
