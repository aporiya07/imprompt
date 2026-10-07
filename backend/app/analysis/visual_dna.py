"""Analysis stage: image → validated Visual DNA + CreativeIntent (+ collage analysis).

One vision call produces all three artifacts (no extra API cost, spec §17 of the
original MVP + Phase 17 here); each is validated as its own typed contract.
Results are cached by normalized-image hash so retries and re-generations never
pay for the same vision call twice.
"""
import hashlib
from dataclasses import dataclass

from pydantic import ValidationError as PydanticValidationError

from app.models.collage import CollageAnalysis, collage_from_payload
from app.models.common import STRUCTURAL_REFERENCE_TYPES
from app.models.dna import VisualDNA, normalize_dna_payload
from app.models.intent import CreativeIntent, derive_intent_from_dna, intent_from_payload
from app.prompts.loader import load_template
from app.providers.registry import RoleExecutor
from app.services.cache import analysis_cache
from app.services.observability import stage
from app.utils.errors import MalformedAIResponseError
from app.utils.image import aspect_ratio_label, orientation_label
from app.utils.json_utils import extract_json_object


@dataclass
class AnalysisResult:
    dna: VisualDNA
    intent: CreativeIntent
    collage: CollageAnalysis | None
    image_hash: str


def _fill_technical(dna: VisualDNA, width: int, height: int) -> None:
    if not dna.technical.aspect_ratio:
        dna.technical.aspect_ratio = aspect_ratio_label(width, height)
    if not dna.technical.orientation:
        dna.technical.orientation = orientation_label(width, height)


async def analyze_image(
    vision: RoleExecutor, image_bytes: bytes, mime: str, width: int, height: int
) -> AnalysisResult:
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    cache_key = f"analysis:{image_hash}:{vision.cfg.primary_model}"
    cached = analysis_cache.get(cache_key)
    if cached is not None:
        dna, intent, collage = cached
        return AnalysisResult(dna=dna, intent=intent, collage=collage, image_hash=image_hash)

    system_prompt = load_template("visual_analysis")
    user_prompt = "Analyze the attached image and return the required JSON object now."

    async with stage("vision_analysis"):
        payload: dict | None = None
        last_err: MalformedAIResponseError | None = None
        for _attempt in (1, 2):
            text, _provider, _model = await vision.run_vision(
                image_bytes=image_bytes,
                mime=mime,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            try:
                payload = extract_json_object(text)
                break
            except MalformedAIResponseError as err:
                last_err = err
        if payload is None:
            raise last_err or MalformedAIResponseError("Vision analysis returned no usable JSON.")

    async with stage("dna_validation"):
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
        except (PydanticValidationError, ValueError) as e:
            if isinstance(e, PydanticValidationError):
                summary = "; ".join(
                    f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                    for err in e.errors(include_url=False)[:3]
                )
            else:
                summary = str(e)
            raise MalformedAIResponseError(f"Visual DNA failed schema validation — {summary}") from e
        _fill_technical(dna, width, height)

    async with stage("creative_intent"):
        raw_intent = payload.get("creative_intent")
        try:
            intent = intent_from_payload(raw_intent) if isinstance(raw_intent, dict) else derive_intent_from_dna(dna)
        except (PydanticValidationError, ValueError) as e:
            # A malformed intent block must never kill an otherwise-good analysis.
            intent = derive_intent_from_dna(dna)

    collage: CollageAnalysis | None = None
    if dna.reference.reference_type in STRUCTURAL_REFERENCE_TYPES and isinstance(
        payload.get("collage_analysis"), dict
    ):
        async with stage("collage_validation"):
            try:
                collage = collage_from_payload(payload["collage_analysis"])
            except (PydanticValidationError, ValueError):
                collage = None  # collage synthesis degrades to single-image mode

    analysis_cache.set(cache_key, (dna, intent, collage))
    return AnalysisResult(dna=dna, intent=intent, collage=collage, image_hash=image_hash)
