"""Prompt construction stage (spec Phases 5, 7, 9).

Inputs are always typed artifacts — Visual DNA + CreativeIntent (+ CollageAnalysis
for moodboards) + the user's instruction — rendered through editable templates and
finished by the target-model adapter. Outputs are parsed, post-processed, and
validated by the deterministic diagnostics before leaving the backend.
"""
import json
import logging
from typing import Any

from app.models.collage import CollageAnalysis
from app.models.common import PromptMode
from app.models.dna import VisualDNA
from app.models.intent import CreativeIntent, derive_intent_from_dna
from app.models.quality import PromptQuality
from app.models.contracts import ShotResult
from app.prompting.adapters.base import PromptTarget
from app.prompting.diagnostics import validate_prompt
from app.prompts.loader import load_template
from app.providers.registry import RoleExecutor
from app.utils.errors import MalformedAIResponseError
from app.utils.json_utils import as_str, as_str_list, extract_json_object

log = logging.getLogger("ipa.optimizer")

# mode → (template name, extraction aspect or None)
_TEMPLATE_BY_MODE: dict[PromptMode, tuple[str, str | None]] = {
    PromptMode.RECREATE: ("recreate", None),
    PromptMode.CREATE_SIMILAR: ("create_similar", None),
    PromptMode.EXTRACT_STYLE: ("style_extraction", None),
    PromptMode.EXTRACT_COMPOSITION: ("extraction", "composition"),
    PromptMode.EXTRACT_LIGHTING: ("extraction", "lighting"),
    PromptMode.EXTRACT_COLOR: ("extraction", "color"),
    PromptMode.EXTRACT_POSE: ("extraction", "pose"),
    PromptMode.MODIFY: ("modification", None),
}

_ASPECT_GUIDANCE: dict[str, str] = {
    "composition": (
        "Extract the compositional logic only: framing, shot type, camera angle, viewpoint, subject "
        "placement, balance, negative space, depth, leading lines and visual hierarchy. The token "
        "[SUBJECT] replaces the subject so the composition stays transferable. Do not carry over "
        "scene-specific content."
    ),
    "lighting": (
        "Extract the lighting scheme only: key light direction, quality, source, temperature, "
        "time-based look, highlight and shadow behavior, atmospheric effects. Do not carry over "
        "scene or subject content beyond what the light falls on."
    ),
    "color": (
        "Extract the palette and grading only: dominant, secondary and accent colors, saturation, "
        "contrast, brightness, warm/cool balance and grading style. Describe how color is used, "
        "not what specific objects are colored."
    ),
    "pose": (
        "Extract pose and body language only: body orientation, weight distribution, hand and arm "
        "placement, gaze direction, facial expression and interactions between subjects. The token "
        "[SUBJECT] replaces the person(s). Do not carry over identity, wardrobe or scene."
    ),
}


def _render(template_name: str, target: PromptTarget, **tokens: str) -> str:
    text = load_template(template_name)
    text = text.replace("{{MODEL_GUIDANCE}}", target.guidance.strip()).replace(
        "{{TARGET_MODEL}}", target.name
    )
    for key, value in tokens.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def _user_payload(
    dna: VisualDNA,
    intent: CreativeIntent,
    task: str,
    target: PromptTarget,
    instruction: str | None,
    current_prompt: str | None,
    extra: dict[str, Any] | None = None,
) -> str:
    body: dict[str, Any] = {
        "task": task,
        "target_model": {"id": target.id, "name": target.name},
        "visual_dna": json.loads(dna.model_dump_json()),
        "creative_intent": json.loads(intent.model_dump_json()),
        "instruction": instruction,
        "current_prompt": current_prompt,
    }
    if extra:
        body.update(extra)
    return "Apply the system instructions to the following payload and return only the required JSON object:\n" + json.dumps(
        body, ensure_ascii=False, indent=1
    )


def _parse_prompt(payload: dict) -> tuple[str, str | None]:
    prompt = as_str(payload.get("prompt"))
    if not prompt:
        raise MalformedAIResponseError("Prompt result JSON is missing a non-empty 'prompt' string.")
    raw = payload.get("negative_prompt")
    negative = None if raw is None else as_str(raw)
    if not negative or negative.lower() == "null":
        negative = None
    return prompt, negative


def _finish(prompt: str, negative: str | None, target: PromptTarget, dna: VisualDNA) -> tuple[str, str | None, PromptQuality]:
    final_prompt = target.post_process(prompt, dna)
    if not target.supports_negative:
        negative = None
    quality = validate_prompt(final_prompt, negative, target, dna)
    return final_prompt, negative, quality


def _with_intent(dna: VisualDNA, intent: CreativeIntent | None) -> CreativeIntent:
    return intent if intent is not None else derive_intent_from_dna(dna)


async def generate_optimized_prompt(
    executor: RoleExecutor,
    dna: VisualDNA,
    mode: PromptMode,
    target: PromptTarget,
    intent: CreativeIntent | None = None,
    instruction: str | None = None,
) -> tuple[str, str | None, PromptQuality]:
    resolved_intent = _with_intent(dna, intent)
    template_name, aspect = _TEMPLATE_BY_MODE[mode]
    tokens = {}
    if aspect is not None:
        tokens = {"EXTRACT_ASPECT": aspect, "EXTRACT_GUIDANCE": _ASPECT_GUIDANCE[aspect]}
    system = _render(template_name, target, **tokens)
    user = _user_payload(dna, resolved_intent, mode.value, target, instruction, None)
    text, _provider, _model = await executor.run_text(system_prompt=system, user_prompt=user)
    prompt, negative = _parse_prompt(extract_json_object(text))
    return _finish(prompt, negative, target, dna)


async def generate_collage_prompts(
    executor: RoleExecutor,
    dna: VisualDNA,
    collage: CollageAnalysis,
    target: PromptTarget,
    intent: CreativeIntent | None = None,
    instruction: str | None = None,
) -> tuple[str, list[ShotResult]]:
    """Moodboard → master creative direction + per-shot prompts (spec Phase 9)."""
    resolved_intent = _with_intent(dna, intent)
    system = _render("collage", target)
    panels_payload = [
        {
            "index": p.index,
            "title": p.title,
            "summary": p.summary,
            "shot": json.loads(p.shot.model_dump_json()),
        }
        for p in collage.panels
    ]
    user = _user_payload(
        dna,
        resolved_intent,
        "collage_shoot",
        target,
        instruction,
        None,
        extra={
            "collage": {
                "layout_description": collage.layout_description,
                "global_dna": json.loads(collage.global_dna.model_dump_json()),
                "panels": panels_payload,
            }
        },
    )
    text, _provider, _model = await executor.run_text(system_prompt=system, user_prompt=user)
    payload = extract_json_object(text)
    master_direction = as_str(payload.get("master_direction"))
    shots_raw = payload.get("shots")
    if not isinstance(shots_raw, list) or not shots_raw:
        raise MalformedAIResponseError("Collage result JSON is missing a non-empty 'shots' array.")
    shots: list[ShotResult] = []
    for i, item in enumerate(shots_raw, start=1):
        if not isinstance(item, dict):
            continue
        prompt, negative = _parse_prompt(item)
        final_prompt, final_negative, quality = _finish(prompt, negative, target, dna)
        shots.append(
            ShotResult(
                index=int(item.get("index") or i),
                title=as_str(item.get("title")),
                prompt=final_prompt,
                negative_prompt=final_negative,
                quality=quality,
            )
        )
    if not shots:
        raise MalformedAIResponseError("Collage result contained no usable shots.")
    if not master_direction:
        master_direction = collage.global_dna.summary or collage.global_dna.overall_aesthetic
    return master_direction, shots


async def refine_optimized_prompt(
    executor: RoleExecutor,
    dna: VisualDNA,
    mode: PromptMode,
    target: PromptTarget,
    current_prompt: str,
    instruction: str,
    intent: CreativeIntent | None = None,
) -> tuple[list[str], list[str], str, str | None, PromptQuality]:
    """Surgical refinement: keep/change planning, then coherent reconstruction (spec Phase 10)."""
    resolved_intent = _with_intent(dna, intent)
    system = _render("modification", target)
    user = _user_payload(dna, resolved_intent, "refine", target, instruction, current_prompt)
    text, _provider, _model = await executor.run_text(system_prompt=system, user_prompt=user)
    payload = extract_json_object(text)
    prompt, negative = _parse_prompt(payload)
    keep = as_str_list(payload.get("keep"))
    change = as_str_list(payload.get("change"))
    final_prompt, final_negative, quality = _finish(prompt, negative, target, dna)
    return keep, change, final_prompt, final_negative, quality
