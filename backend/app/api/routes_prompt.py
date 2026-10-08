import logging

from fastapi import APIRouter, Request

from app.config import get_settings
from app.models.common import PromptMode
from app.models.contracts import (
    ApiEnvelope,
    GeneratePromptRequest,
    HealthData,
    ModelsData,
    PromptData,
    QualityData,
    RefineData,
    RefinePromptRequest,
    TargetModelInfo,
    ValidatePromptRequest,
)
from app.models.dna import dna_from_payload
from app.models.intent import intent_from_payload
from app.prompting.adapters import all_targets, get_target
from app.prompting.diagnostics import validate_prompt
from app.prompting.optimizer import generate_optimized_prompt, refine_optimized_prompt
from app.providers.registry import Runtime
from app.services.observability import stage
from app.utils.errors import BadRequestError
from app.version import APP_VERSION

log = logging.getLogger("imprompt.prompt")
router = APIRouter()


@router.get("/api/models", response_model=ApiEnvelope[ModelsData])
async def list_models():
    return ApiEnvelope(
        data=ModelsData(
            models=[
                TargetModelInfo(
                    id=t.id,
                    name=t.name,
                    supports_negative=t.supports_negative,
                    soft_char_limit=t.soft_char_limit,
                )
                for t in all_targets()
            ]
        )
    )


@router.get("/api/health", response_model=ApiEnvelope[HealthData])
async def health(request: Request):
    runtime: Runtime = request.app.state.runtime
    settings = get_settings()
    return ApiEnvelope(
        data=HealthData(
            status="ok",
            version=APP_VERSION,
            configured_providers={
                "gemini": bool(settings.gemini_api_key),
                "openai": bool(settings.openai_api_key),
            },
            available_providers=sorted(runtime.providers),
            vision_provider=runtime.vision.cfg.primary,
            prompt_provider=runtime.prompt.cfg.primary,
            fallback_enabled=settings.enable_fallback,
        )
    )


def _intent_or_none(payload):
    if payload is None:
        return None
    try:
        return intent_from_payload(payload)
    except Exception:
        return None  # a malformed intent degrades to the deterministic derivation


def _dna_or_error(payload):
    try:
        return dna_from_payload(payload)
    except ValueError as e:
        raise BadRequestError(str(e))


@router.post("/api/generate-prompt", response_model=ApiEnvelope[PromptData])
async def generate_prompt(req: GeneratePromptRequest, request: Request):
    if req.mode == PromptMode.MODIFY and not (req.instruction or "").strip():
        raise BadRequestError("An instruction is required when prompt mode is 'modify'.")
    target = get_target(req.target_model)
    dna = _dna_or_error(req.visual_dna)
    intent = _intent_or_none(req.creative_intent)
    runtime: Runtime = request.app.state.runtime
    async with stage("prompt_generation"):
        prompt, negative, quality = await generate_optimized_prompt(
            runtime.prompt, dna, req.mode, target, intent, req.instruction
        )
    return ApiEnvelope(data=PromptData(prompt=prompt, negative_prompt=negative, quality=quality))


@router.post("/api/refine-prompt", response_model=ApiEnvelope[RefineData])
async def refine_prompt(req: RefinePromptRequest, request: Request):
    target = get_target(req.target_model)
    dna = _dna_or_error(req.visual_dna)
    intent = _intent_or_none(req.creative_intent)
    runtime: Runtime = request.app.state.runtime
    async with stage("prompt_refinement"):
        keep, change, prompt, negative, quality = await refine_optimized_prompt(
            runtime.prompt, dna, req.mode, target, req.current_prompt, req.instruction, intent
        )
    return ApiEnvelope(
        data=RefineData(prompt=prompt, negative_prompt=negative, quality=quality, keep=keep, change=change)
    )


@router.post("/api/validate-prompt", response_model=ApiEnvelope[QualityData])
async def validate_prompt_route(req: ValidatePromptRequest):
    """Deterministic re-validation for manually edited prompts. No AI calls."""
    from app.models.dna import VisualDNA

    target = get_target(req.target_model)
    if req.visual_dna is not None:
        dna = _dna_or_error(req.visual_dna)
    else:
        dna = VisualDNA()
    quality = validate_prompt(req.prompt.strip(), None, target, dna)
    return ApiEnvelope(data=QualityData(quality=quality))
