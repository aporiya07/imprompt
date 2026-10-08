"""API request/response contracts (spec Phase 12).

Every endpoint returns the strict envelope:
    {"success": true, "data": {...}, "error": null}
    {"success": false, "data": null, "error": {"code", "message", "details", "request_id"}}
No route returns an arbitrary dictionary.
"""
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.common import PromptMode
from app.models.quality import PromptQuality

DT = TypeVar("DT")

_FLEX = ConfigDict(extra="allow")

# Input limits (spec Phase 4): generous enough for legitimate analysis payloads,
# tight enough that a hostile client cannot feed arbitrary text to the LLMs.
INSTRUCTION_MAX_CHARS = 2000
PROMPT_MAX_CHARS = 24000
URL_MAX_CHARS = 2048
MODEL_ID_MAX_CHARS = 64
DNA_PAYLOAD_MAX_CHARS = 200_000
INTENT_PAYLOAD_MAX_CHARS = 100_000


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None
    request_id: str | None = None


class ApiEnvelope(BaseModel, Generic[DT]):
    success: bool = True
    data: DT | None = None
    error: ErrorBody | None = None


# ----- shared pieces -----


class PromptErrorInfo(BaseModel):
    code: str
    message: str


class ShotResult(BaseModel):
    index: int
    title: str = ""
    prompt: str
    negative_prompt: str | None = None
    quality: PromptQuality | None = None


class PanelInfo(BaseModel):
    index: int
    title: str = ""
    summary: str = ""
    bounds: dict[str, float] | None = None


class LimitedPayloadRequest(BaseModel):
    """Rejects oversized structured payloads before they can reach an AI call."""

    _PAYLOAD_LIMITS: ClassVar[dict[str, int]] = {}

    @model_validator(mode="before")
    @classmethod
    def _enforce_payload_limits(cls, values):
        import json

        if not isinstance(values, dict):
            return values
        for field, max_chars in cls._PAYLOAD_LIMITS.items():
            raw = values.get(field)
            if raw is not None and len(json.dumps(raw, ensure_ascii=False)) > max_chars:
                raise ValueError(f"{field} payload is too large (limit {max_chars} characters)")
        return values


# ----- analyze -----


class AnalyzeRequest(BaseModel):
    image: str = Field(min_length=1, description="Base64 image bytes or a data URL")
    mode: PromptMode = PromptMode.RECREATE
    target_model: str = Field(default="generic", max_length=MODEL_ID_MAX_CHARS)
    instruction: str | None = Field(default=None, max_length=INSTRUCTION_MAX_CHARS)
    generate_prompt: bool = True


class AnalyzeData(BaseModel):
    reference_type: str
    layout_description: str | None = None
    visual_dna: dict[str, Any]
    creative_intent: dict[str, Any]
    prompt: str | None = None
    negative_prompt: str | None = None
    prompt_error: PromptErrorInfo | None = None
    prompt_quality: PromptQuality | None = None
    shots: list[ShotResult] = Field(default_factory=list)
    panels: list[PanelInfo] = Field(default_factory=list)


# ----- prompt generation -----


class GeneratePromptRequest(LimitedPayloadRequest):
    visual_dna: dict[str, Any]
    creative_intent: dict[str, Any] | None = None
    mode: PromptMode = PromptMode.RECREATE
    target_model: str = Field(default="generic", max_length=MODEL_ID_MAX_CHARS)
    instruction: str | None = Field(default=None, max_length=INSTRUCTION_MAX_CHARS)

    _PAYLOAD_LIMITS: ClassVar[dict[str, int]] = {
        "visual_dna": DNA_PAYLOAD_MAX_CHARS,
        "creative_intent": INTENT_PAYLOAD_MAX_CHARS,
    }


class PromptData(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    quality: PromptQuality | None = None


# ----- refine -----


class RefinePromptRequest(LimitedPayloadRequest):
    visual_dna: dict[str, Any]
    creative_intent: dict[str, Any] | None = None
    current_prompt: str = Field(min_length=1, max_length=PROMPT_MAX_CHARS)
    instruction: str = Field(min_length=1, max_length=INSTRUCTION_MAX_CHARS)
    mode: PromptMode = PromptMode.RECREATE
    target_model: str = Field(default="generic", max_length=MODEL_ID_MAX_CHARS)

    _PAYLOAD_LIMITS: ClassVar[dict[str, int]] = {
        "visual_dna": DNA_PAYLOAD_MAX_CHARS,
        "creative_intent": INTENT_PAYLOAD_MAX_CHARS,
    }


class RefineData(PromptData):
    keep: list[str] = Field(default_factory=list)
    change: list[str] = Field(default_factory=list)


# ----- media / meta -----


class FetchImageRequest(BaseModel):
    url: str = Field(min_length=1, max_length=URL_MAX_CHARS)


class FetchedImage(BaseModel):
    image: str
    width: int
    height: int


class TargetModelInfo(BaseModel):
    id: str
    name: str
    supports_negative: bool
    soft_char_limit: int | None = None


class ModelsData(BaseModel):
    models: list[TargetModelInfo]


class HealthData(BaseModel):
    status: str
    version: str
    configured_providers: dict[str, bool]
    available_providers: list[str]
    vision_provider: str
    prompt_provider: str
    fallback_enabled: bool


# ----- diagnostics -----


class ValidatePromptRequest(LimitedPayloadRequest):
    prompt: str = Field(min_length=1, max_length=PROMPT_MAX_CHARS)
    target_model: str = Field(default="generic", max_length=MODEL_ID_MAX_CHARS)
    visual_dna: dict[str, Any] | None = None

    _PAYLOAD_LIMITS: ClassVar[dict[str, int]] = {"visual_dna": DNA_PAYLOAD_MAX_CHARS}


class QualityData(BaseModel):
    quality: PromptQuality | None = None
