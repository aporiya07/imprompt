"""Prompt quality diagnostics: deterministic heuristics only."""
from pydantic import BaseModel, ConfigDict, Field


class PromptQuality(BaseModel):
    model_config = ConfigDict(extra="allow")
    score: int = 100  # 0..100 overall quality
    warnings: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    # Backwards-compatible extensions for visual fidelity diagnostics.
    visual_coverage_score: int | None = None  # 0..100 when computed
    coverage: dict[str, bool] | None = None
