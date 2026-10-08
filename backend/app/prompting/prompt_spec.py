"""Structured PromptSpec: Visual DNA + Creative Intent → generation-oriented facts.

This is an intermediate assembly layer. It does NOT replace Visual DNA.
It surfaces concrete, priority-ordered visual facts so the prompt LLM
compresses redundancy rather than discarding visual information.
"""
from __future__ import annotations

from typing import Any

from app.models.common import PromptMode
from app.models.dna import VisualDNA
from app.models.intent import CreativeIntent


def _join(*parts: str, sep: str = ", ") -> str:
    return sep.join(p.strip() for p in parts if p and str(p).strip())


def _subject_block(dna: VisualDNA) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for s in dna.subjects:
        block = {
            "label": s.label,
            "type": s.type,
            "count": s.count,
            "description": s.description,
            "clothing": s.clothing,
            "accessories": list(s.accessories or []),
            "pose": s.pose,
            "body_orientation": s.body_orientation,
            "body_pose": s.body_pose.model_dump(exclude_defaults=True, mode="json"),
            "facial_expression": s.facial_expression,
            "gaze_direction": s.gaze_direction,
            "gaze": s.gaze.model_dump(exclude_defaults=True, mode="json"),
            "gaze_target": s.gaze_target,
            "face_visibility": s.face_visibility,
            "head_position": s.head_position,
            "left_arm": s.left_arm.model_dump(exclude_defaults=True, mode="json"),
            "right_arm": s.right_arm.model_dump(exclude_defaults=True, mode="json"),
            "left_hand": s.left_hand.model_dump(exclude_defaults=True, mode="json"),
            "right_hand": s.right_hand.model_dump(exclude_defaults=True, mode="json"),
            "body_visibility": s.body_visibility.model_dump(exclude_defaults=True, mode="json"),
            "position_in_frame": s.position_in_frame,
            "relative_scale": s.relative_scale,
            "depth_position": s.depth_position,
            "contact_points": list(s.contact_points or []),
            "interactions": list(s.interactions or []),
            "distinguishing_characteristics": list(s.distinguishing_characteristics or []),
        }
        # Drop empty values to keep the payload dense.
        out.append({k: v for k, v in block.items() if v not in ("", None, [], 0)})
    return out


def _composition_block(dna: VisualDNA) -> dict[str, str]:
    c = dna.composition
    fields = {
        "shot_type": c.shot_type,
        "framing": c.framing,
        "camera_angle": c.camera_angle,
        "viewpoint": c.viewpoint,
        "subject_placement": c.subject_placement,
        "balance": c.balance,
        "negative_space": c.negative_space,
        "depth": c.depth,
        "leading_lines": c.leading_lines,
        "visual_hierarchy": c.visual_hierarchy,
        "cropping": c.cropping,
        "subject_scale": c.subject_scale,
        "perspective": c.perspective,
        "foreground_background_relationship": c.foreground_background_relationship,
    }
    return {k: v for k, v in fields.items() if v}


def _lighting_block(dna: VisualDNA) -> dict[str, Any]:
    lit = dna.lighting
    fields = {
        "lighting_type": lit.lighting_type,
        "key_light_direction": lit.key_light_direction,
        "fill_level": lit.fill_level,
        "rim_light": lit.rim_light,
        "quality": lit.quality,
        "source": lit.source,
        "color_temperature": lit.color_temperature,
        "time_based_look": lit.time_based_look,
        "highlights": lit.highlights,
        "shadows": lit.shadows,
        "contrast": lit.contrast,
        "exposure_characteristics": lit.exposure_characteristics,
        "atmospheric_effects": lit.atmospheric_effects,
        "practical_lights": list(lit.practical_lights or []),
    }
    return {k: v for k, v in fields.items() if v not in ("", None, [])}


def _color_block(dna: VisualDNA) -> dict[str, Any]:
    col = dna.color

    def _swatches(items) -> list[str]:
        names: list[str] = []
        for sw in items or []:
            name = getattr(sw, "name", "") or ""
            role = getattr(sw, "role", "") or ""
            label = _join(name, f"({role})" if role else "")
            if label:
                names.append(label)
        return names

    fields = {
        "dominant": _swatches(col.dominant),
        "secondary": _swatches(col.secondary),
        "accent": _swatches(col.accent),
        "palette_description": col.palette_description,
        "warm_cool_balance": col.warm_cool_balance,
        "saturation": col.saturation,
        "contrast": col.contrast,
        "brightness": col.brightness,
        "color_grading": col.color_grading,
        "tonal_characteristics": col.tonal_characteristics,
    }
    return {k: v for k, v in fields.items() if v not in ("", None, [])}


def _camera_block(dna: VisualDNA) -> dict[str, str]:
    cam = dna.camera
    fields = {
        "perspective": cam.perspective,
        "focal_length_category": cam.focal_length_category,
        "depth_of_field": cam.depth_of_field,
        "focus_plane": cam.focus_plane,
        "background_blur": cam.background_blur,
        "perspective_compression": cam.perspective_compression,
        "realism_level": cam.realism_level,
        "sharpness": cam.sharpness,
    }
    return {k: v for k, v in fields.items() if v}


def _environment_block(dna: VisualDNA) -> dict[str, Any]:
    env = dna.environment
    fields = {
        "location_type": env.location_type,
        "setting": env.setting,
        "foreground": env.foreground,
        "midground": env.midground,
        "background": env.background,
        "objects": list(env.objects or []),
        "architecture": env.architecture,
        "landscape": env.landscape,
        "weather": env.weather,
        "time_of_day": env.time_of_day,
        "season": env.season,
        "atmosphere": env.atmosphere,
        "spatial_relationships": list(env.spatial_relationships or []),
    }
    return {k: v for k, v in fields.items() if v not in ("", None, [])}


def _materials_block(dna: VisualDNA) -> list[str]:
    lines: list[str] = []
    for m in dna.materials or []:
        line = _join(
            getattr(m, "object", "") or "",
            getattr(m, "material", "") or "",
            getattr(m, "texture", "") or "",
            getattr(m, "appearance", "") or "",
            sep=": ",
        )
        # Prefer readable "silk saree with soft sheen" style when possible.
        obj = getattr(m, "object", "") or ""
        mat = getattr(m, "material", "") or ""
        tex = getattr(m, "texture", "") or ""
        app = getattr(m, "appearance", "") or ""
        if mat and obj:
            line = _join(f"{mat} {obj}", tex, app)
        elif mat:
            line = _join(mat, tex, app)
        if line:
            lines.append(line)
    return lines


def _relationships_block(dna: VisualDNA) -> list[str]:
    lines: list[str] = []
    for rel in dna.relationships or []:
        desc = getattr(rel, "description", "") or ""
        details = _join(
            desc,
            rel.depth_order,
            rel.distance,
            _join(*rel.contact_points, sep="; "),
            rel.occlusion,
        )
        if details:
            lines.append(details)
            continue
        subj = getattr(rel, "subject", "") or ""
        relation = getattr(rel, "relation", "") or ""
        obj = getattr(rel, "object", "") or ""
        if subj and relation and obj:
            lines.append(f"{subj} {relation} {obj}")
        elif relation:
            lines.append(relation)
    return lines


def _relationship_graph(dna: VisualDNA) -> list[dict[str, Any]]:
    graph: list[dict[str, Any]] = []
    for rel in dna.relationships:
        item = {
            "subject": rel.subject,
            "relation": rel.relation,
            "object": rel.object,
            "description": rel.description,
            "depth_order": rel.depth_order,
            "distance": rel.distance,
            "contact_points": list(rel.contact_points or []),
            "occlusion": rel.occlusion,
            "confidence": rel.confidence.value,
        }
        graph.append({key: value for key, value in item.items() if value not in ("", None, [], {})})
    return graph


def _elements_by_importance(dna: VisualDNA) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "essential": [],
        "supporting": [],
        "incidental": [],
        "uncertain": [],
    }
    for el in dna.elements or []:
        desc = el.description.strip()
        if not desc:
            continue
        key = el.importance.value if hasattr(el.importance, "value") else str(el.importance)
        if key in buckets:
            buckets[key].append(desc)
        else:
            buckets["supporting"].append(desc)
    return {k: v for k, v in buckets.items() if v}


def _priority_checklist(mode: PromptMode) -> list[str]:
    """Hard-constraint order when the model must compress."""
    base = [
        "subject identity/type",
        "wardrobe",
        "relative position and depth",
        "torso / shoulder / head / face orientation",
        "pose / stance / leg and foot position",
        "arm / hand placement and physical contact",
        "gaze direction and gaze target",
        "major composition / framing",
        "spatial relationships and occlusion",
        "key lighting (direction, quality, rim/fill)",
        "palette / grading anchors",
        "environment",
        "materials / textures",
        "depth / background rendering",
        "style / photographic character",
    ]
    if mode in (PromptMode.EXTRACT_COMPOSITION,):
        return [
            "framing / shot type",
            "subject placement / balance",
            "viewpoint / camera angle",
            "negative space / depth",
            "perspective",
        ]
    if mode in (PromptMode.EXTRACT_LIGHTING,):
        return [
            "key light direction",
            "quality / softness",
            "fill / rim",
            "temperature / time-based look",
            "highlight / shadow behavior",
            "atmospheric effects",
        ]
    if mode in (PromptMode.EXTRACT_COLOR,):
        return [
            "dominant / secondary / accent colors",
            "warm/cool balance",
            "saturation / contrast",
            "grading / tonal character",
        ]
    if mode in (PromptMode.EXTRACT_POSE,):
        return [
            "body orientation",
            "pose / hand placement",
            "gaze / expression",
            "interactions between subjects",
        ]
    if mode in (PromptMode.EXTRACT_STYLE, PromptMode.CREATE_SIMILAR):
        return [
            "palette / grading",
            "lighting character",
            "photographic / editorial style",
            "materials / rendering",
            "composition habits",
            "mood / atmosphere",
        ]
    return base


def build_prompt_spec(
    dna: VisualDNA,
    intent: CreativeIntent,
    mode: PromptMode,
) -> dict[str, Any]:
    """Assemble a model-independent PromptSpec from typed artifacts."""
    mood_bits = [
        dna.mood.description,
        ", ".join(dna.mood.emotional_tone or []),
        dna.mood.atmosphere,
        dna.mood.intimacy,
    ]
    style_bits = [
        dna.style.photography_style,
        dna.style.editorial_style,
        dna.style.art_direction,
        dna.style.genre,
        dna.style.cultural_aesthetic,
        dna.style.rendering_style,
        dna.style.post_processing,
    ]
    typography: dict[str, Any] | None = None
    if dna.typography.present:
        typography = {
            "text_content": list(dna.typography.text_content or []),
            "placement": dna.typography.placement,
            "typography_style": dna.typography.typography_style,
            "graphics": list(dna.typography.graphics or []),
        }
        typography = {k: v for k, v in typography.items() if v not in ("", None, [])}

    spec: dict[str, Any] = {
        "mode": mode.value,
        "intent": {
            "primary_goal": intent.primary_goal,
            "aesthetic_direction": intent.aesthetic_direction,
            "photographic_direction": intent.photographic_direction,
            "composition_strategy": intent.composition_strategy,
            "lighting_strategy": intent.lighting_strategy,
            "color_strategy": intent.color_strategy,
            "subject_strategy": intent.subject_strategy,
            "environment_strategy": intent.environment_strategy,
            "emotional_direction": intent.emotional_direction,
            "preserve": list(intent.preserve or []),
            "flexible": list(intent.flexible or []),
        },
        "subjects": _subject_block(dna),
        "environment": _environment_block(dna),
        "composition": _composition_block(dna),
        "camera_character": _camera_block(dna),
        "lighting": _lighting_block(dna),
        "color": _color_block(dna),
        "materials": _materials_block(dna),
        "relationships": _relationships_block(dna),
        "relationship_graph": _relationship_graph(dna),
        "atmosphere_mood": _join(*mood_bits),
        "style": _join(*style_bits),
        "elements": _elements_by_importance(dna),
        "typography": typography,
        "reference_overview": dna.reference.overall_description,
        "reference_type": dna.reference.reference_type,
        "layout_description": dna.reference.layout_description,
        "priority_order": _priority_checklist(mode),
        "density_guidance": {
            "single_image_words": "120-280 typical; up to ~350 for complex scenes",
            "collage_master_words": "150-300",
            "collage_shot_words": "100-220",
            "rule": "Prefer higher visual information per sentence over poetic adjectives. Compress redundancy, not visual facts.",
        },
        "anti_patterns": [
            "Do not summarize rich visual information into generic creative language.",
            "The output is a generation specification, not an image caption, marketing description, creative brief, or social-media caption.",
            "Compress redundancy, not visual information.",
        ],
        "human_analysis_priority": [
            "Describe each visible person independently before describing the pair.",
            "Keep body orientation, head/face orientation, and eye gaze as separate facts.",
            "Use only visible limbs, gestures, contacts, and body regions; state cropped or occluded parts as not visible.",
            "Describe front/behind, left/right, depth, overlap, and contact geometry explicitly.",
        ],
    }
    ref_type = (dna.reference.reference_type or "").lower()
    layout = (dna.reference.layout_description or "").lower()
    if ref_type in {"collage", "moodboard"} or "grid" in layout:
        spec["series_continuity"] = {
            "preserve_across_shots": [
                "same subjects / couple",
                "same wardrobe family",
                "same palette and grading anchors",
                "same location / environment family",
                "same lighting family",
                "same emotional tone",
                "same photographic / editorial language",
            ],
            "vary_per_shot": [
                "framing / shot type",
                "pose / body language",
                "viewpoint / camera angle",
                "interaction detail",
                "subject scale / distance",
                "environment emphasis (detail vs wide)",
            ],
        }
    # Remove empty top-level containers.
    return {k: v for k, v in spec.items() if v not in ("", None, [], {})}
