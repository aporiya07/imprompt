"""API request/response contracts (spec Phase 12).

Every endpoint returns the strict envelope:
    {"success": true, "data": {...}, "error": null}
    {"success": false, "data": null, "error": {"code", "message", "details", "request_id"}}
No route returns an arbitrary dictionary.
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import PromptMode
from app.models.quality import PromptQuality

DT = TypeVar("DT")

_FLEX = ConfigDict(extra="allow")


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


# ----- analyze -----


class AnalyzeRequest(BaseModel):
    image: str = Field(min_length=1, description="Base64 image bytes or a data URL")
    mode: PromptMode = PromptMode.RECREATE
    target_model: str = "generic"
    instruction: str | None = None
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


# ----- prompt generation -----


class GeneratePromptRequest(BaseModel):
    visual_dna: dict[str, Any]
    creative_intent: dict[str, Any] | None = None
    mode: PromptMode = PromptMode.RECREATE
    target_model: str = "generic"
    instruction: str | None = None


class PromptData(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    quality: PromptQuality | None = None


# ----- refine -----


class RefinePromptRequest(BaseModel):
    visual_dna: dict[str, Any]
    creative_intent: dict[str, Any] | None = None
    current_prompt: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    mode: PromptMode = PromptMode.RECREATE
    target_model: str = "generic"


class RefineData(PromptData):
    keep: list[str] = Field(default_factory=list)
    change: list[str] = Field(default_factory=list)


# ----- media / meta -----


class FetchImageRequest(BaseModel):
    url: str = Field(min_length=1)


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
