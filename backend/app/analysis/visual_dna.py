"""Analysis stage: image → validated Visual DNA + CreativeIntent (+ collage analysis).

One vision call produces all three artifacts (no extra API cost). Validation of
the vision output happens inside the executor boundary, so malformed JSON,
truncation, and schema failures all flow through the retry/fallback budget.

Caching is keyed by normalized image hash + vision model + prompt version +
DNA schema version. Results are immutable (deep-copied on every handout) and
identical concurrent requests share a single in-flight vision call.
"""
import asyncio
import hashlib
from dataclasses import dataclass

from app.models.collage import CollageAnalysis, collage_from_payload
from app.models.common import STRUCTURAL_REFERENCE_TYPES
from app.models.dna import DNA_SCHEMA_VERSION, VisualDNA, normalize_dna_payload
from app.models.intent import CreativeIntent, derive_intent_from_dna, intent_from_payload
from app.prompts.loader import load_template
from app.providers.registry import RoleExecutor
from app.services.cache import analysis_cache
from app.services.observability import stage
from app.utils.errors import MalformedAIResponseError
from app.utils.image import aspect_ratio_label, orientation_label
from app.utils.json_utils import extract_json_object

# Bump when prompts/visual_analysis.txt or DNA normalization changes behavior.
VISION_PROMPT_VERSION = "4"
VISION_MAX_OUTPUT_TOKENS = 8192

_inflight: dict[str, asyncio.Future] = {}


@dataclass
class AnalysisResult:
    dna: VisualDNA
    intent: CreativeIntent
    collage: CollageAnalysis | None
    image_hash: str
    provider: str
    model: str
    fallback_used: bool


def _copy(result: AnalysisResult) -> AnalysisResult:
    """Hand out immutable copies so one request can never mutate cached state."""
    return AnalysisResult(
        dna=result.dna.model_copy(deep=True),
        intent=result.intent.model_copy(deep=True),
        collage=result.collage.model_copy(deep=True) if result.collage else None,
        image_hash=result.image_hash,
        provider=result.provider,
        model=result.model,
        fallback_used=result.fallback_used,
    )


def _fill_technical(dna: VisualDNA, width: int, height: int) -> None:
    if not dna.technical.aspect_ratio:
        dna.technical.aspect_ratio = aspect_ratio_label(width, height)
    if not dna.technical.orientation:
        dna.technical.orientation = orientation_label(width, height)


async def analyze_image(
    vision: RoleExecutor, image_bytes: bytes, mime: str, width: int, height: int
) -> AnalysisResult:
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    cache_key = (
        f"analysis:{image_hash}:{vision.cfg.primary_model}:"
        f"{VISION_PROMPT_VERSION}:{DNA_SCHEMA_VERSION}"
    )
    cached = analysis_cache.get(cache_key)
    if cached is not None:
        return _copy(cached)

    existing = _inflight.get(cache_key)
    if existing is not None:
        result = await existing
        return _copy(result)

    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    _inflight[cache_key] = fut
    try:
        result = await _analyze_uncached(vision, image_bytes, mime, width, height, image_hash)
        analysis_cache.set(cache_key, result)
        if not fut.done():
            fut.set_result(result)
        return _copy(result)
    except BaseException as e:
        if not fut.done():
            fut.set_exception(e)
        raise
    finally:
        _inflight.pop(cache_key, None)


def _validate_vision_payload(text: str, width: int, height: int) -> dict:
    """Parse + schema-validate raw vision output. Raises MalformedAIResponseError on failure.

    Runs inside the executor boundary so DNA validation failures participate in
    the same retry/fallback budget as provider errors.
    """
    payload = extract_json_object(text)
    raw_dna = payload.get("visual_dna") if isinstance(payload.get("visual_dna"), dict) else payload
    dna_payload = dict(raw_dna)
    technical = dict(dna_payload.get("technical") or {})
    technical.setdefault("aspect_ratio", "")
    technical.setdefault("orientation", "")
    if not technical["aspect_ratio"]:
        technical["aspect_ratio"] = aspect_ratio_label(width, height)
    if not technical["orientation"]:
        technical["orientation"] = orientation_label(width, height)
    dna_payload["technical"] = technical
    try:
        dna = VisualDNA.model_validate(normalize_dna_payload(dna_payload))
        _fill_technical(dna, width, height)
    except MalformedAIResponseError:
        raise
    except Exception as e:
        summary = (
            "; ".join(
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in e.errors(include_url=False)[:3]
            )
            if hasattr(e, "errors")
            else str(e)
        )
        raise MalformedAIResponseError(f"Visual DNA failed schema validation: {summary}") from e
    return {"dna": dna, "payload": payload}


async def _analyze_uncached(
    vision: RoleExecutor, image_bytes: bytes, mime: str, width: int, height: int, image_hash: str
) -> AnalysisResult:
    system_prompt = load_template("visual_analysis")
    user_prompt = "Analyze the attached image and return the required JSON object now."

    async with stage("vision_analysis"):
        outcome = await vision.run_vision(
            image_bytes=image_bytes,
            mime=mime,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            validate=lambda text: _validate_vision_payload(text, width, height),
            max_output_tokens=VISION_MAX_OUTPUT_TOKENS,
        )

    dna: VisualDNA = outcome.value["dna"]
    payload: dict = outcome.value["payload"]

    async with stage("creative_intent"):
        raw_intent = payload.get("creative_intent")
        try:
            intent = intent_from_payload(raw_intent) if isinstance(raw_intent, dict) else derive_intent_from_dna(dna)
        except Exception:
            # A malformed intent block must never kill an otherwise-good analysis.
            intent = derive_intent_from_dna(dna)

    collage: CollageAnalysis | None = None
    if dna.reference.reference_type in STRUCTURAL_REFERENCE_TYPES and isinstance(
        payload.get("collage_analysis"), dict
    ):
        async with stage("collage_validation"):
            try:
                collage = collage_from_payload(payload["collage_analysis"])
            except Exception:
                collage = None  # collage synthesis degrades to single-image mode

    return AnalysisResult(
        dna=dna,
        intent=intent,
        collage=collage,
        image_hash=image_hash,
        provider=outcome.provider,
        model=outcome.model,
        fallback_used=outcome.fallback_used,
    )
