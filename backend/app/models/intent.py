"""CreativeIntent — the strategy layer between Visual DNA and prompt construction.

Produced as part of the vision call (no extra API cost) and validated as its own
typed artifact; when absent (e.g. an older client payload), a deterministic
derivation from the DNA fills in so downstream stages always have one.
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import ConfidenceLevel, ElementImportance
from app.models.dna import VisualDNA
from app.utils.json_utils import as_str, as_str_list

_FLEX = ConfigDict(extra="allow")


class CreativeIntent(BaseModel):
    model_config = _FLEX
    primary_goal: str = ""
    aesthetic_direction: str = ""
    photographic_direction: str = ""
    composition_strategy: str = ""
    lighting_strategy: str = ""
    color_strategy: str = ""
    subject_strategy: str = ""
    environment_strategy: str = ""
    emotional_direction: str = ""
    preserve: list[str] = Field(default_factory=list)
    flexible: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


def normalize_intent_payload(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Creative intent payload must be a JSON object.")
    out: dict[str, Any] = {}
    for key in (
        "primary_goal",
        "aesthetic_direction",
        "photographic_direction",
        "composition_strategy",
        "lighting_strategy",
        "color_strategy",
        "subject_strategy",
        "environment_strategy",
        "emotional_direction",
    ):
        out[key] = as_str(raw.get(key))
    out["preserve"] = as_str_list(raw.get("preserve"), split_commas=False)
    out["flexible"] = as_str_list(raw.get("flexible"), split_commas=False)
    conf = as_str(raw.get("confidence")).lower()
    out["confidence"] = conf if conf in {c.value for c in ConfidenceLevel} else ConfidenceLevel.MEDIUM.value
    return out


def intent_from_payload(payload: Any) -> CreativeIntent:
    return CreativeIntent.model_validate(normalize_intent_payload(payload))


def derive_intent_from_dna(dna: VisualDNA) -> CreativeIntent:
    """Deterministic fallback: build a usable intent from the DNA alone.

    Used when the vision model did not return a creative-intent block (or a client
    posts a bare DNA to /api/generate-prompt). Essential elements become the
    preserve-list, incidental/uncertain ones the flexible-list.
    """
    preserve: list[str] = []
    flexible: list[str] = []
    for element in dna.elements:
        if element.importance == ElementImportance.ESSENTIAL:
            preserve.append(element.description)
        elif element.importance in (ElementImportance.INCIDENTAL, ElementImportance.UNCERTAIN):
            flexible.append(element.description)

    reading = dna.interpretation.creative_reading
    goal_parts = [part for part in (reading, dna.reference.overall_description) if part]
    primary_goal = (
        f"Recreate the visual language of {goal_parts[0]}" if len(goal_parts) == 1 and reading
        else "; ".join(goal_parts)
        or "Recreate the important visual characteristics of the reference image."
    )
    if not primary_goal.lower().startswith("recreate") and reading:
        primary_goal = f"Recreate the visual language of the reference: {reading}"

    if dna.lighting.quality or dna.lighting.lighting_type:
        preserve.append(
            " ".join(x for x in (dna.lighting.time_based_look, dna.lighting.lighting_type, dna.lighting.quality) if x)
        )
    if dna.composition.balance or dna.composition.shot_type:
        preserve.append(
            " ".join(x for x in (dna.composition.shot_type, dna.composition.balance) if x)
        )
    for rel in dna.relationships[:4]:
        if rel.description:
            preserve.append(rel.description)
    for material in dna.materials[:4]:
        label = " ".join(
            part for part in (getattr(material, "material", ""), getattr(material, "object", "")) if part
        ).strip()
        if label:
            preserve.append(label)
    for swatch in (dna.color.dominant or [])[:3]:
        if swatch.name:
            preserve.append(swatch.name)
    for subject in dna.subjects[:2]:
        if subject.clothing:
            preserve.append(subject.clothing)

    return CreativeIntent(
        primary_goal=primary_goal,
        aesthetic_direction=dna.style.art_direction or dna.style.photography_style,
        photographic_direction=dna.style.photography_style or dna.camera.perspective,
        composition_strategy=dna.composition.framing or dna.composition.subject_placement,
        lighting_strategy=dna.lighting.lighting_type or dna.lighting.time_based_look,
        color_strategy=dna.color.palette_description or dna.color.color_grading,
        subject_strategy="; ".join(s.description for s in dna.subjects if s.description),
        environment_strategy=dna.environment.location_type or dna.environment.setting,
        emotional_direction=dna.mood.description or ", ".join(dna.mood.emotional_tone),
        preserve=[p for p in preserve if p],
        flexible=[f for f in flexible if f],
        confidence=ConfidenceLevel.MEDIUM,
    )
