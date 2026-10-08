import asyncio
import base64
import logging

from fastapi import APIRouter, Request

from app.analysis.visual_dna import analyze_image
from app.config import get_settings
from app.models.common import PromptMode
from app.models.contracts import (
    AnalyzeData,
    AnalyzeRequest,
    ApiEnvelope,
    FetchedImage,
    FetchImageRequest,
    PanelInfo,
    PromptErrorInfo,
)
from app.prompting.adapters import get_target
from app.prompting.optimizer import generate_collage_prompts, generate_optimized_prompt
from app.providers.registry import Runtime
from app.services.observability import stage
from app.utils.errors import AppError, BadRequestError, ImageTooLargeError
from app.utils.image import decode_data_url, validate_and_normalize
from app.utils.url_fetch import download_image

log = logging.getLogger("imprompt.analyze")
router = APIRouter()


@router.post("/api/fetch-image", response_model=ApiEnvelope[FetchedImage])
async def fetch_image(req: FetchImageRequest):
    """Fetch a reference image from a public URL (SSRF-guarded) as an alternative to uploading."""
    async with stage("fetch_image"):
        settings = get_settings()
        jpeg, _mime, width, height = await download_image(
            req.url,
            max_bytes=settings.max_image_bytes,
            max_pixels=settings.max_image_pixels,
            max_side=settings.max_image_side,
        )
    return ApiEnvelope(
        data=FetchedImage(
            image="data:image/jpeg;base64," + base64.b64encode(jpeg).decode(),
            width=width,
            height=height,
        )
    )


@router.post("/api/analyze", response_model=ApiEnvelope[AnalyzeData])
async def analyze(req: AnalyzeRequest, request: Request):
    settings = get_settings()
    if req.mode == PromptMode.MODIFY and not (req.instruction or "").strip():
        raise BadRequestError("An instruction is required when prompt mode is 'modify'.")
    target = get_target(req.target_model)
    runtime: Runtime = request.app.state.runtime

    async with stage("image_validation"):
        # Reject oversized base64 payloads before spending memory on decoding.
        base64_limit = int(settings.max_image_bytes * 1.37) + 1024
        if len(req.image) > base64_limit:
            raise ImageTooLargeError(
                f"Image payload is {len(req.image) / 1_048_576:.1f} MB encoded; "
                f"the limit is {settings.max_image_mb:.0f} MB."
            )
        raw, _declared_mime = decode_data_url(req.image)
        image_bytes, mime, width, height = await asyncio.to_thread(
            validate_and_normalize,
            raw,
            settings.max_image_bytes,
            settings.max_image_pixels,
            settings.max_image_side,
        )
    log.info("image accepted: %dx%d, %.0f KB re-encoded as %s", width, height, len(image_bytes) / 1024, mime)

    # Vision → DNA → intent (cached by versioned image hash; collage analysis when detected).
    result = await analyze_image(runtime.vision, image_bytes, mime, width, height)

    data = AnalyzeData(
        reference_type=result.dna.reference.reference_type.value,
        layout_description=(
            result.collage.layout_description if result.collage else result.dna.reference.layout_description
        )
        or None,
        visual_dna=result.dna.model_dump(mode="json"),
        creative_intent=result.intent.model_dump(mode="json"),
    )
    if result.collage is not None:
        data.panels = [
            PanelInfo(
                index=p.index,
                title=p.title,
                summary=p.summary,
                bounds=p.bounds.model_dump() if p.bounds else None,
            )
            for p in result.collage.panels
        ]

    if req.generate_prompt:
        try:
            async with stage("prompt_generation"):
                if result.collage is not None:
                    master_direction, shots = await generate_collage_prompts(
                        runtime.prompt, result.dna, result.collage, target, result.intent, req.instruction
                    )
                    data.prompt = master_direction
                    data.shots = shots
                else:
                    prompt, negative, quality = await generate_optimized_prompt(
                        runtime.prompt, result.dna, req.mode, target, result.intent, req.instruction
                    )
                    data.prompt = prompt
                    data.negative_prompt = negative
                    data.prompt_quality = quality
        except AppError as e:
            # The expensive vision stage succeeded: hand back the artifacts plus the failure.
            log.warning("prompt stage failed, visual DNA recovered: %s", e.code)
            data.prompt_error = PromptErrorInfo(code=e.code, message=e.message)

    return ApiEnvelope(data=data)
