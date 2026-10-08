"""Visual DNA v2 — the typed contract for visual reverse engineering.

Design rules (spec Phases 1–2):
- Typed Pydantic models everywhere; no unstructured dicts in the contract.
- Observation first: every section describes what is VISIBLE, hedged where unsure.
- Interpretation is isolated in `interpretation` and never overwrites observation.
- Uncertainty is representable at three levels: per-section ConfidenceLevel,
  per-element ElementImportance.UNCERTAIN, and the top-level `uncertainty` notes.
- Camera facts are categories ("telephoto-like compression"), never gear claims.

The schema is tolerant on input (types strict, presence lenient) so a vision model
omitting or coercing a field degrades gracefully instead of failing the pipeline.
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import ConfidenceLevel, ElementImportance, ReferenceType
from app.utils.errors import BadRequestError
from app.utils.json_utils import as_str, as_str_list

_FLEX = ConfigDict(extra="allow")

DNA_SCHEMA_VERSION = 2


# ---------- reference metadata ----------

class ReferenceMeta(BaseModel):
    model_config = _FLEX
    reference_type: ReferenceType = ReferenceType.UNKNOWN
    reference_type_confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    layout_description: str = ""  # e.g. "3x3 grid of nine photos"
    overall_description: str = ""
    analysis_confidence: float = 0.0  # 0..1


# ---------- subjects ----------

class BodyPoseRecord(BaseModel):
    """Observable body configuration; empty means the region was not determinable."""

    model_config = _FLEX
    state: str = ""  # standing / sitting / walking / leaning / ...
    torso_orientation: str = ""
    shoulder_orientation: str = ""
    head_orientation: str = ""
    face_orientation: str = ""
    hip_orientation: str = ""
    stance: str = ""
    weight_distribution: str = ""
    leg_position: str = ""
    foot_position: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class GazeRecord(BaseModel):
    model_config = _FLEX
    direction: str = ""
    target: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class LimbRecord(BaseModel):
    model_config = _FLEX
    visibility: str = ""  # visible / partially visible / occluded / outside frame / uncertain
    position: str = ""
    gesture: str = ""
    contact: str = ""
    held_object: str = ""
    relation_to_torso: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class BodyVisibilityRecord(BaseModel):
    model_config = _FLEX
    visible_body_regions: list[str] = Field(default_factory=list)
    occluded_body_regions: list[str] = Field(default_factory=list)
    occlusion_notes: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class SubjectRecord(BaseModel):
    model_config = _FLEX
    label: str = ""  # stable handle, e.g. "subject_1"
    type: str = ""  # person / animal / product / object / vehicle / building / food / other
    count: int = 1
    description: str = ""
    age_category: str = ""  # only when visually relevant
    gender_presentation: str = ""  # only when visually evident
    clothing: str = ""
    accessories: list[str] = Field(default_factory=list)
    pose: str = ""
    body_orientation: str = ""
    body_pose: BodyPoseRecord = Field(default_factory=BodyPoseRecord)
    gaze: GazeRecord = Field(default_factory=GazeRecord)
    facial_expression: str = ""
    gaze_direction: str = ""
    gaze_target: str = ""
    face_visibility: str = ""
    head_position: str = ""
    left_arm: LimbRecord = Field(default_factory=LimbRecord)
    right_arm: LimbRecord = Field(default_factory=LimbRecord)
    left_hand: LimbRecord = Field(default_factory=LimbRecord)
    right_hand: LimbRecord = Field(default_factory=LimbRecord)
    body_visibility: BodyVisibilityRecord = Field(default_factory=BodyVisibilityRecord)
    position_in_frame: str = ""
    relative_scale: str = ""
    depth_position: str = ""
    contact_points: list[str] = Field(default_factory=list)
    distinguishing_characteristics: list[str] = Field(default_factory=list)
    interactions: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- environment ----------

class EnvironmentRecord(BaseModel):
    model_config = _FLEX
    location_type: str = ""
    setting: str = ""  # indoor / outdoor / mixed / ambiguous
    foreground: str = ""
    midground: str = ""
    background: str = ""
    objects: list[str] = Field(default_factory=list)
    architecture: str = ""
    landscape: str = ""
    weather: str = ""
    time_of_day: str = ""
    season: str = ""
    atmosphere: str = ""
    spatial_relationships: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- composition ----------

class CompositionRecord(BaseModel):
    model_config = _FLEX
    shot_type: str = ""
    framing: str = ""
    camera_angle: str = ""
    viewpoint: str = ""
    subject_placement: str = ""
    balance: str = ""  # rule of thirds / centered / symmetrical / asymmetric + where
    negative_space: str = ""
    depth: str = ""
    leading_lines: str = ""
    visual_hierarchy: str = ""
    cropping: str = ""
    subject_scale: str = ""
    perspective: str = ""
    foreground_background_relationship: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- camera ----------

class CameraRecord(BaseModel):
    model_config = _FLEX
    perspective: str = ""
    focal_length_category: str = ""  # "wide-angle appearance", "normal", "short-telephoto appearance"
    depth_of_field: str = ""
    focus_plane: str = ""
    background_blur: str = ""
    motion_blur: str = ""
    shutter_characteristics: str = ""
    perspective_compression: str = ""
    lens_distortion: str = ""
    sharpness: str = ""
    realism_level: str = ""  # photographic / stylized / illustrative
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- lighting ----------

class LightingRecord(BaseModel):
    model_config = _FLEX
    lighting_type: str = ""
    key_light_direction: str = ""
    fill_level: str = ""
    rim_light: str = ""
    quality: str = ""  # hard / soft / mixed
    source: str = ""  # natural / artificial / mixed
    color_temperature: str = ""
    time_based_look: str = ""  # golden hour / blue hour / overcast daylight / studio
    highlights: str = ""
    shadows: str = ""
    contrast: str = ""
    exposure_characteristics: str = ""
    atmospheric_effects: str = ""
    practical_lights: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- color ----------

class Swatch(BaseModel):
    model_config = _FLEX
    name: str = ""
    hex: str = ""  # approximate
    role: str = ""  # dominant / accent / wardrobe / background ...


class ColorRecord(BaseModel):
    model_config = _FLEX
    dominant: list[Swatch] = Field(default_factory=list)
    secondary: list[Swatch] = Field(default_factory=list)
    accent: list[Swatch] = Field(default_factory=list)
    palette_description: str = ""
    warm_cool_balance: str = ""
    saturation: str = ""
    contrast: str = ""
    brightness: str = ""
    color_grading: str = ""
    tonal_characteristics: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- style ----------

class StyleRecord(BaseModel):
    model_config = _FLEX
    photography_style: str = ""
    editorial_style: str = ""
    genre: str = ""
    art_direction: str = ""
    realism_level: str = ""
    cinematic_characteristics: str = ""
    fashion_characteristics: str = ""
    commercial_characteristics: str = ""
    cultural_aesthetic: str = ""
    texture: str = ""
    grain: str = ""
    rendering_style: str = ""
    post_processing: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- mood ----------

class MoodRecord(BaseModel):
    model_config = _FLEX
    description: str = ""
    emotional_tone: list[str] = Field(default_factory=list)
    atmosphere: str = ""
    energy: str = ""
    intimacy: str = ""
    drama: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- materials ----------

class MaterialRecord(BaseModel):
    model_config = _FLEX
    object: str = ""
    material: str = ""
    texture: str = ""
    reflectivity: str = ""
    appearance: str = ""  # e.g. "skin looks natural with visible pores"


# ---------- typography / graphics ----------

class TypographyRecord(BaseModel):
    model_config = _FLEX
    present: bool = False
    text_content: list[str] = Field(default_factory=list)
    placement: str = ""
    typography_style: str = ""
    hierarchy: str = ""
    layout: str = ""
    graphics: list[str] = Field(default_factory=list)  # logos, badges, graphic elements
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- relationships ----------

class RelationshipRecord(BaseModel):
    model_config = _FLEX
    subject: str = ""
    relation: str = ""  # facing / behind / holding / beside / occluded by / lit from behind ...
    object: str = ""
    description: str = ""
    depth_order: str = ""
    distance: str = ""
    contact_points: list[str] = Field(default_factory=list)
    occlusion: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- essential vs incidental ----------

class VisualElement(BaseModel):
    model_config = _FLEX
    description: str = ""
    importance: ElementImportance = ElementImportance.SUPPORTING
    reason: str = ""


# ---------- interpretation (Phase 2) ----------

class InterpretationBlock(BaseModel):
    model_config = _FLEX
    creative_reading: str = ""  # "romantic editorial pre-wedding photography emphasizing intimacy"
    photographic_intent: str = ""
    target_emotion: str = ""
    notes: list[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


# ---------- technical ----------

class TechnicalRecord(BaseModel):
    model_config = _FLEX
    aspect_ratio: str = ""
    orientation: str = ""
    image_quality: str = ""


# ---------- root ----------

class VisualDNA(BaseModel):
    model_config = _FLEX
    schema_version: int = DNA_SCHEMA_VERSION
    reference: ReferenceMeta = Field(default_factory=ReferenceMeta)
    subjects: list[SubjectRecord] = Field(default_factory=list)
    environment: EnvironmentRecord = Field(default_factory=EnvironmentRecord)
    composition: CompositionRecord = Field(default_factory=CompositionRecord)
    camera: CameraRecord = Field(default_factory=CameraRecord)
    lighting: LightingRecord = Field(default_factory=LightingRecord)
    color: ColorRecord = Field(default_factory=ColorRecord)
    style: StyleRecord = Field(default_factory=StyleRecord)
    mood: MoodRecord = Field(default_factory=MoodRecord)
    materials: list[MaterialRecord] = Field(default_factory=list)
    typography: TypographyRecord = Field(default_factory=TypographyRecord)
    relationships: list[RelationshipRecord] = Field(default_factory=list)
    elements: list[VisualElement] = Field(default_factory=list)
    interpretation: InterpretationBlock = Field(default_factory=InterpretationBlock)
    uncertainty: list[str] = Field(default_factory=list)
    technical: TechnicalRecord = Field(default_factory=TechnicalRecord)


# ---------- tolerant normalization ----------

_CONFIDENCE = {c.value for c in ConfidenceLevel}
_IMPORTANCE = {i.value for i in ElementImportance}
_REFERENCE_TYPES = {r.value for r in ReferenceType}


def _confidence(value: Any, default: ConfidenceLevel = ConfidenceLevel.MEDIUM) -> ConfidenceLevel:
    s = as_str(value).lower()
    return ConfidenceLevel(s) if s in _CONFIDENCE else default


def _importance(value: Any) -> ElementImportance:
    s = as_str(value).lower()
    return ElementImportance(s) if s in _IMPORTANCE else ElementImportance.UNCERTAIN


def _reference_type(value: Any) -> ReferenceType:
    s = as_str(value).lower().replace(" ", "_").replace("-", "_")
    return ReferenceType(s) if s in _REFERENCE_TYPES else ReferenceType.UNKNOWN


def _section(value: Any) -> dict[str, Any]:
    """Stringify scalars, keep lists as lists of strings — for simple sections."""
    if not isinstance(value, dict):
        return {}
    out: dict[str, Any] = {}
    for k, v in value.items():
        if isinstance(v, list):
            out[k] = as_str_list(v, split_commas=False)
        elif isinstance(v, dict):
            out[k] = as_str(v)
        else:
            out[k] = as_str(v)
    return out


def _structured_section(value: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    """Normalize a nested observation without stringifying its fields."""
    if not isinstance(value, dict):
        return {}
    out = {field: as_str(value.get(field)) for field in fields}
    out["confidence"] = _confidence(value.get("confidence")).value
    return out


def _body_visibility(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "visible_body_regions": as_str_list(value.get("visible_body_regions"), split_commas=False),
        "occluded_body_regions": as_str_list(value.get("occluded_body_regions"), split_commas=False),
        "occlusion_notes": as_str_list(value.get("occlusion_notes"), split_commas=False),
        "confidence": _confidence(value.get("confidence")).value,
    }


def _swatch(value: Any) -> Swatch | None:
    if isinstance(value, dict):
        name = as_str(value.get("name") or value.get("color"))
        hexv = as_str(value.get("hex") or value.get("value"))
        if not name and not hexv:
            return None
        return Swatch(name=name, hex=hexv, role=as_str(value.get("role")))
    s = as_str(value)
    if not s:
        return None
    if "(#" in s and s.endswith(")"):
        name, _, rest = s[:-1].partition("(#")
        return Swatch(name=name.strip(), hex=rest.strip(), role="")
    if s.startswith("#"):
        return Swatch(name="", hex=s, role="")
    return Swatch(name=s, hex="", role="")


def _swatches(value: Any) -> list[Swatch]:
    if value is None:
        return []
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
    elif isinstance(value, (list, tuple)):
        parts = list(value)
    else:
        parts = [value]
    out = [s for s in (_swatch(p) for p in parts) if s is not None]
    return out


def normalize_dna_payload(raw: Any) -> dict[str, Any]:
    """Coerce a raw vision-model payload into shapes the VisualDNA schema expects."""
    if not isinstance(raw, dict):
        raise ValueError("Visual DNA payload must be a JSON object.")
    out: dict[str, Any] = {"schema_version": 2}

    reference = dict(raw.get("reference") or {})
    confidence = dict(raw.get("confidence") or {})
    ref_type = _reference_type(reference.get("reference_type") or raw.get("reference_type"))
    try:
        analysis_confidence = float(reference.get("analysis_confidence", confidence.get("overall", 0.0)) or 0.0)
    except (TypeError, ValueError):
        analysis_confidence = 0.0
    out["reference"] = {
        "reference_type": ref_type.value,
        "reference_type_confidence": _confidence(reference.get("reference_type_confidence")).value,
        "layout_description": as_str(reference.get("layout_description")),
        "overall_description": as_str(reference.get("overall_description") or raw.get("overall_description")),
        "analysis_confidence": max(0.0, min(1.0, analysis_confidence)),
    }

    subjects_raw = raw.get("subjects")
    if subjects_raw is None and isinstance(raw.get("subject"), dict):
        subjects_raw = [raw["subject"]]
    if not isinstance(subjects_raw, list):
        subjects_raw = [subjects_raw] if subjects_raw else []
    subjects: list[dict[str, Any]] = []
    for i, item in enumerate(subjects_raw, start=1):
        if isinstance(item, str):
            subjects.append({"label": f"subject_{i}", "description": item, "type": "unknown"})
            continue
        if not isinstance(item, dict):
            continue
        s = _section(item)
        s.setdefault("label", as_str(item.get("label")) or f"subject_{i}")
        s.setdefault("type", "unknown")
        if not s.get("description"):
            s["description"] = as_str(item.get("description") or item.get("primary_subject") or item.get("appearance"))
        try:
            s["count"] = max(1, min(50, int(item.get("count") or 1)))
        except (TypeError, ValueError):
            s["count"] = 1
        s["confidence"] = _confidence(item.get("confidence")).value
        s["accessories"] = as_str_list(item.get("accessories"))
        s["distinguishing_characteristics"] = as_str_list(item.get("distinguishing_characteristics"), split_commas=False)
        s["interactions"] = as_str_list(item.get("interactions"), split_commas=False)
        s["body_pose"] = _structured_section(
            item.get("body_pose"),
            (
                "state",
                "torso_orientation",
                "shoulder_orientation",
                "head_orientation",
                "face_orientation",
                "hip_orientation",
                "stance",
                "weight_distribution",
                "leg_position",
                "foot_position",
            ),
        )
        s["gaze"] = _structured_section(item.get("gaze"), ("direction", "target"))
        for limb in ("left_arm", "right_arm", "left_hand", "right_hand"):
            s[limb] = _structured_section(
                item.get(limb),
                ("visibility", "position", "gesture", "contact", "held_object", "relation_to_torso"),
            )
        s["body_visibility"] = _body_visibility(item.get("body_visibility"))
        s["contact_points"] = as_str_list(item.get("contact_points"), split_commas=False)
        subjects.append(s)
    out["subjects"] = subjects

    if isinstance(raw.get("environment"), dict):
        env = _section(raw["environment"])
        env["objects"] = as_str_list(raw["environment"].get("objects"))
        env["spatial_relationships"] = as_str_list(raw["environment"].get("spatial_relationships"), split_commas=False)
        env["confidence"] = _confidence(raw["environment"].get("confidence")).value
        out["environment"] = env

    for key in ("composition", "camera", "lighting", "style"):
        if isinstance(raw.get(key), dict):
            section = _section(raw[key])
            section["confidence"] = _confidence(raw[key].get("confidence")).value
            out[key] = section

    if isinstance(raw.get("color"), dict):
        c = dict(raw["color"])
        out["color"] = {
            "dominant": [s.model_dump() for s in _swatches(c.get("dominant_colors", c.get("dominant")))],
            "secondary": [s.model_dump() for s in _swatches(c.get("secondary_colors", c.get("secondary")))],
            "accent": [s.model_dump() for s in _swatches(c.get("accent_colors", c.get("accent")))],
            "palette_description": as_str(c.get("palette_description")),
            "warm_cool_balance": as_str(c.get("warm_cool_balance") or c.get("color_temperature")),
            "saturation": as_str(c.get("saturation")),
            "contrast": as_str(c.get("contrast")),
            "brightness": as_str(c.get("brightness")),
            "color_grading": as_str(c.get("color_grading")),
            "tonal_characteristics": as_str(c.get("tonal_characteristics")),
            "confidence": _confidence(c.get("confidence")).value,
        }

    if isinstance(raw.get("mood"), dict):
        m = dict(raw["mood"])
        out["mood"] = {
            "description": as_str(m.get("description")),
            "emotional_tone": as_str_list(m.get("emotional_tone", m.get("keywords"))),
            "atmosphere": as_str(m.get("atmosphere")),
            "energy": as_str(m.get("energy")),
            "intimacy": as_str(m.get("intimacy")),
            "drama": as_str(m.get("drama")),
            "confidence": _confidence(m.get("confidence")).value,
        }
    elif raw.get("mood") is not None:
        out["mood"] = {"description": as_str(raw.get("mood"))}

    materials_raw = raw.get("materials", raw.get("materials_and_texture"))
    if materials_raw is None:
        materials_raw = []
    if not isinstance(materials_raw, list):
        materials_raw = [materials_raw]
    materials: list[dict[str, Any]] = []
    for item in materials_raw:
        if isinstance(item, dict):
            materials.append(_section(item))
        elif as_str(item):
            materials.append({"object": as_str(item)})
    out["materials"] = materials

    if isinstance(raw.get("typography"), dict):
        t = dict(raw["typography"])
        text_content = as_str_list(t.get("text_content"), split_commas=False)
        present = bool(t.get("present")) or bool(text_content)
        out["typography"] = {
            "present": present,
            "text_content": text_content if present else [],
            "placement": as_str(t.get("placement")),
            "typography_style": as_str(t.get("typography_style") or t.get("font_characteristics")),
            "hierarchy": as_str(t.get("hierarchy")),
            "layout": as_str(t.get("layout")),
            "graphics": as_str_list(t.get("graphics"), split_commas=False) if present else [],
            "confidence": _confidence(t.get("confidence")).value,
        }

    rel_raw = raw.get("relationships", raw.get("spatial_relationships"))
    if rel_raw is None:
        rel_raw = []
    if not isinstance(rel_raw, list):
        rel_raw = [rel_raw]
    relationships: list[dict[str, Any]] = []
    for item in rel_raw:
        if isinstance(item, dict):
            relationship = _section(item)
            relationship["contact_points"] = as_str_list(item.get("contact_points"), split_commas=False)
            relationship["confidence"] = _confidence(item.get("confidence")).value
            relationships.append(relationship)
        elif as_str(item):
            relationships.append({"description": as_str(item)})
    out["relationships"] = relationships

    elements_raw = raw.get("elements", raw.get("key_elements"))
    if elements_raw is None:
        elements_raw = []
    if not isinstance(elements_raw, list):
        elements_raw = [elements_raw]
    elements: list[dict[str, Any]] = []
    for item in elements_raw:
        if isinstance(item, dict):
            elements.append(
                {
                    "description": as_str(item.get("description") or item.get("element")),
                    "importance": _importance(item.get("importance") or item.get("classification")).value,
                    "reason": as_str(item.get("reason")),
                }
            )
        elif as_str(item):
            elements.append({"description": as_str(item), "importance": ElementImportance.UNCERTAIN.value})
    out["elements"] = elements

    interp = raw.get("interpretation")
    if isinstance(interp, dict):
        out["interpretation"] = {
            "creative_reading": as_str(interp.get("creative_reading")),
            "photographic_intent": as_str(interp.get("photographic_intent")),
            "target_emotion": as_str(interp.get("target_emotion")),
            "notes": as_str_list(interp.get("notes"), split_commas=False),
            "confidence": _confidence(interp.get("confidence")).value,
        }

    out["uncertainty"] = as_str_list(raw.get("uncertainty"), split_commas=False)

    if isinstance(raw.get("technical"), dict):
        out["technical"] = _section(raw["technical"])
    else:
        out["technical"] = {}

    return out


def dna_from_payload(payload: dict[str, Any]) -> VisualDNA:
    """Validate a client-supplied or model-supplied Visual DNA record."""
    try:
        return VisualDNA.model_validate(normalize_dna_payload(payload))
    except Exception as e:
        from pydantic import ValidationError as PydanticValidationError

        if isinstance(e, PydanticValidationError):
            summary = "; ".join(
                f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
                for err in e.errors(include_url=False)[:3]
            )
        else:
            summary = str(e)
        raise BadRequestError(f"The visual_dna payload is not a valid Visual DNA record: {summary}") from e
