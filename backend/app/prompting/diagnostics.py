"""Deterministic prompt-quality heuristics (spec Phase 11).

No LLM calls: pure pattern checks so the score is stable and explainable.
Every warning is actionable; strengths note what the prompt does well.

Also computes visual_coverage against available Visual DNA so a grammatically
beautiful but information-poor prompt is scored as incomplete.
"""
from __future__ import annotations

import re

from app.models.dna import VisualDNA
from app.models.quality import PromptQuality
from app.prompting.adapters.base import PromptTarget

FILLER = re.compile(
    r"\b(masterpiece|best quality|top quality|8k|4k|ultra detailed|highly detailed|"
    r"award[- ]winning|stunning|gorgeous|amazing|incredible|breathtaking)\b",
    re.IGNORECASE,
)
TECH_CLAIM = re.compile(r"\b(\d{2,3}\s?mm\b|\bf/[12](\.\d)?\b|\bISO\s?\d{3,5}\b|\b1/\d{3,4}\s?s\b)", re.IGNORECASE)
VAGUE = re.compile(r"\b(nice|beautiful|good looking|well composed|very aesthetic|lovely)\b", re.IGNORECASE)
POETIC = re.compile(
    r"\b(quietly romantic|dreamy|soulful|magical|ethereal|whisper(?:ing)?|"
    r"poetic|elegantly|breathtakingly)\b",
    re.IGNORECASE,
)
SPATIAL = re.compile(
    r"\b(behind|beside|in front of|above|below|left of|right of|framed by|occlu\w+|"
    r"next to|around|facing|embrac\w*|holding|touching|waist|shoulder|arm)\b",
    re.IGNORECASE,
)
LIGHTING_WORDS = re.compile(
    r"\b(backlight\w*|rim light|rim illumination|golden hour|blue hour|soft light|"
    r"hard light|key light|window light|studio light|side light|overcast|"
    r"diffused|ambient fill|lifted shadows|highlight|warm amber)\b",
    re.IGNORECASE,
)
COMPOSITION_WORDS = re.compile(
    r"\b(rule of thirds|negative space|leading lines?|symmetr\w+|asymmetric\w*|"
    r"centered|off[- ]center|close[- ]?up|wide shot|medium shot|full[- ]body|"
    r"waist[- ]up|portrait|framing|crop|three[- ]quarter)\b",
    re.IGNORECASE,
)
MATERIAL_WORDS = re.compile(
    r"\b(fabric|silk|leather|metal|glass|wood|stone|knit|denim|satin|linen|wool|"
    r"skin|texture|matte|glossy|reflect\w+|woven|sheen|jewelry|gold|kurta|saree|"
    r"sari|textile)\b",
    re.IGNORECASE,
)
WARDROBE_WORDS = re.compile(
    r"\b(wear(?:s|ing)?|dressed|clothing|wardrobe|outfit|dress|saree|sari|kurta|"
    r"shirt|jacket|suit|jewelry|bangles?|border|silk|ivory|crimson|red)\b",
    re.IGNORECASE,
)
POSE_WORDS = re.compile(
    r"\b(pose|standing|seated|sitting|walking|facing|turned|gaze|looking|"
    r"expression|smile|embrace|embracing|hand|hands|arm|arms|forehead|"
    r"profile|orientation)\b",
    re.IGNORECASE,
)
ORIENTATION_WORDS = re.compile(
    r"\b(torso|shoulder|body|head|face|profile|three[- ]quarter|facing|turned|"
    r"orientation|angled|front(?:al)?|away from|toward)\b",
    re.IGNORECASE,
)
GAZE_WORDS = re.compile(
    r"\b(gaze|looking|look(?:s|ing)?|eyes?|eye contact|stare|glance|"
    r"directly at camera|toward (?:her|him|them|the camera|partner))\b",
    re.IGNORECASE,
)
HAND_ARM_WORDS = re.compile(
    r"\b(left|right)?\s*(?:hand|hands|arm|arms|wrist|forearm|elbow)|"
    r"\b(holding|touching|wrapped|rests?|reaches?|clasped|interlocked|"
    r"around (?:the )?(?:waist|shoulder|arm))\b",
    re.IGNORECASE,
)
BODY_VISIBILITY_WORDS = re.compile(
    r"\b(occlud\w+|overlap\w*|partially visible|not visible|cropped|"
    r"lower body|legs?|feet|foot|torso|shoulders?)\b",
    re.IGNORECASE,
)
ENV_WORDS = re.compile(
    r"\b(beach|shore|shoreline|coastal|sea|ocean|sand|sky|horizon|water|"
    r"indoor|outdoor|room|street|forest|landscape|environment|background|"
    r"foreground|vegetation|surf)\b",
    re.IGNORECASE,
)
COLOR_WORDS = re.compile(
    r"\b(palette|crimson|ivory|amber|gold|muted|warm|cool|desaturat\w*|"
    r"grading|tone|tones|color|colour|blue[- ]grey|blue[- ]gray|cream)\b",
    re.IGNORECASE,
)
DEPTH_WORDS = re.compile(
    r"\b(shallow depth|depth of field|bokeh|background blur|softly separated|"
    r"compressed background|foreground|midground|background)\b",
    re.IGNORECASE,
)
SERIES_WORDS = re.compile(
    r"\b(series|editorial|moodboard|across (?:the )?frames?|recurring|"
    r"same couple|wardrobe continuity|consistent|shot variation|"
    r"intimate portraits?|environmental frames?)\b",
    re.IGNORECASE,
)

# Weights for expected categories (sum ≈ 100 when all present in DNA).
_COVERAGE_WEIGHTS: dict[str, int] = {
    "subject": 15,
    "wardrobe": 10,
    "pose_expression": 10,
    "relationship_spatial": 10,
    "composition": 15,
    "environment": 10,
    "lighting": 10,
    "color": 8,
    "materials": 5,
    "depth_background": 4,
    "style_mood": 3,
    "human_orientation": 5,
    "human_gaze": 5,
    "human_hands": 5,
    "human_relationship": 5,
}


def _has_any(text: str, *needles: str) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles if n)


def _dna_expects(dna: VisualDNA) -> dict[str, bool]:
    """Which coverage categories are expected given available DNA."""
    has_subjects = bool(dna.subjects)
    wardrobe = any((s.clothing or s.accessories) for s in dna.subjects)
    pose = any(
        (s.pose or s.body_orientation or s.facial_expression or s.gaze_direction or s.interactions)
        for s in dna.subjects
    )
    relationships = bool(dna.relationships) or any(s.interactions for s in dna.subjects) or bool(
        dna.environment.spatial_relationships
    )
    composition = any(
        [
            dna.composition.shot_type,
            dna.composition.framing,
            dna.composition.subject_placement,
            dna.composition.balance,
            dna.composition.negative_space,
            dna.composition.depth,
        ]
    )
    environment = any(
        [
            dna.environment.location_type,
            dna.environment.setting,
            dna.environment.background,
            dna.environment.landscape,
            dna.environment.atmosphere,
        ]
    )
    lighting = any(
        [
            dna.lighting.lighting_type,
            dna.lighting.key_light_direction,
            dna.lighting.quality,
            dna.lighting.rim_light,
            dna.lighting.time_based_look,
            dna.lighting.atmospheric_effects,
        ]
    )
    color = bool(dna.color.dominant or dna.color.palette_description or dna.color.color_grading)
    materials = bool(dna.materials)
    depth = bool(dna.camera.depth_of_field or dna.camera.background_blur or dna.composition.depth)
    style = bool(
        dna.style.photography_style
        or dna.style.editorial_style
        or dna.mood.description
        or dna.mood.emotional_tone
    )
    human_subjects = [s for s in dna.subjects if s.type.lower() in {"person", "couple", "group"}]
    human_orientation = any(
        s.body_orientation
        or s.body_pose.torso_orientation
        or s.body_pose.shoulder_orientation
        or s.body_pose.head_orientation
        or s.body_pose.face_orientation
        for s in human_subjects
    )
    human_gaze = any(s.gaze_direction or s.gaze.direction or s.gaze.target or s.gaze_target for s in human_subjects)
    human_hands = any(
        s.left_arm.position
        or s.right_arm.position
        or s.left_hand.position
        or s.right_hand.position
        or s.left_hand.gesture
        or s.right_hand.gesture
        for s in human_subjects
    )
    human_relationship = bool(dna.relationships) and len(human_subjects) > 1
    return {
        "subject": has_subjects,
        "wardrobe": wardrobe,
        "pose_expression": pose,
        "relationship_spatial": relationships,
        "composition": composition,
        "environment": environment,
        "lighting": lighting,
        "color": color,
        "materials": materials,
        "depth_background": depth,
        "style_mood": style,
        "human_orientation": human_orientation,
        "human_gaze": human_gaze,
        "human_hands": human_hands,
        "human_relationship": human_relationship,
    }


def compute_visual_coverage(prompt: str, dna: VisualDNA) -> tuple[int, dict[str, bool], list[str]]:
    """Return (coverage_score 0..100, per-category hits among expected, warnings)."""
    text = prompt.strip()
    expected = _dna_expects(dna)
    hits: dict[str, bool] = {}
    warnings: list[str] = []

    def check(category: str, covered: bool) -> None:
        if not expected.get(category):
            return
        hits[category] = covered

    # Subject: match DNA subject terms when available, else generic presence.
    subject_terms: list[str] = []
    stopwords = {"with", "that", "this", "from", "into", "over", "near", "wearing", "while", "also", "young"}
    for subject in dna.subjects[:3]:
        subject_terms.extend(
            term
            for term in re.findall(r"[a-z']{4,}", (subject.description + " " + subject.type).lower())
            if term not in stopwords
        )
    if expected["subject"]:
        if subject_terms:
            check("subject", any(term in text.lower() for term in subject_terms))
        else:
            check("subject", bool(re.search(r"\b(woman|man|couple|person|model|subject)\b", text, re.I)))

    if expected["wardrobe"]:
        clothing_bits = [s.clothing for s in dna.subjects if s.clothing]
        accessory_bits = [a for s in dna.subjects for a in (s.accessories or [])]
        specific = any(_has_any(text, *re.findall(r"[a-z']{4,}", c.lower())) for c in clothing_bits) or any(
            _has_any(text, a) for a in accessory_bits
        )
        check("wardrobe", specific or bool(WARDROBE_WORDS.search(text)))

    if expected["pose_expression"]:
        check("pose_expression", bool(POSE_WORDS.search(text)))

    if expected["human_orientation"]:
        check("human_orientation", bool(ORIENTATION_WORDS.search(text)))

    if expected["human_gaze"]:
        check("human_gaze", bool(GAZE_WORDS.search(text)))

    if expected["human_hands"]:
        check("human_hands", bool(HAND_ARM_WORDS.search(text)))

    if expected["human_relationship"]:
        check(
            "human_relationship",
            bool(SPATIAL.search(text) and (BODY_VISIBILITY_WORDS.search(text) or HAND_ARM_WORDS.search(text))),
        )

    if expected["relationship_spatial"]:
        rel_ok = bool(SPATIAL.search(text))
        for rel in dna.relationships or []:
            if rel.description and rel.description.lower()[:24] in text.lower():
                rel_ok = True
        check("relationship_spatial", rel_ok)

    if expected["composition"]:
        check("composition", bool(COMPOSITION_WORDS.search(text)))

    if expected["environment"]:
        env_bits = [
            dna.environment.location_type,
            dna.environment.setting,
            dna.environment.landscape,
            dna.environment.background,
        ]
        specific = any(_has_any(text, b) for b in env_bits if b)
        check("environment", specific or bool(ENV_WORDS.search(text)))

    if expected["lighting"]:
        check("lighting", bool(LIGHTING_WORDS.search(text)))

    if expected["color"]:
        swatch_names = [sw.name for sw in (dna.color.dominant or []) if sw.name]
        specific = any(_has_any(text, n) for n in swatch_names) or _has_any(
            text, dna.color.palette_description or "", dna.color.color_grading or ""
        )
        check("color", specific or bool(COLOR_WORDS.search(text)))

    if expected["materials"]:
        mat_names = []
        for m in dna.materials or []:
            mat_names.extend([getattr(m, "material", "") or "", getattr(m, "texture", "") or ""])
        specific = any(_has_any(text, n) for n in mat_names if n)
        check("materials", specific or bool(MATERIAL_WORDS.search(text)))

    if expected["depth_background"]:
        check("depth_background", bool(DEPTH_WORDS.search(text)))

    if expected["style_mood"]:
        style_bits = [
            dna.style.photography_style,
            dna.style.editorial_style,
            dna.mood.description,
            *(dna.mood.emotional_tone or []),
        ]
        specific = any(_has_any(text, b) for b in style_bits if b)
        check(
            "style_mood",
            specific
            or bool(re.search(r"\b(editorial|photographic|cinematic|intimate|romantic|mood)\b", text, re.I)),
        )

    # Series continuity: bonus category when reference is collage/moodboard.
    is_series = str(dna.reference.reference_type).lower() in {"collage", "moodboard"} or bool(
        dna.reference.layout_description and "grid" in dna.reference.layout_description.lower()
    )
    if is_series:
        expected_series = True
        hits["series_continuity"] = bool(SERIES_WORDS.search(text))
    else:
        expected_series = False

    total_w = 0
    earned = 0
    for cat, weight in _COVERAGE_WEIGHTS.items():
        if not expected.get(cat):
            continue
        total_w += weight
        if hits.get(cat):
            earned += weight
    if expected_series:
        total_w += 8
        if hits.get("series_continuity"):
            earned += 8

    score = int(round(100 * earned / total_w)) if total_w else 100

    missing = [cat for cat, ok in hits.items() if not ok]
    if missing and score < 70:
        warnings.append(
            "Prompt is under-representing available visual information "
            f"(missing: {', '.join(missing)})."
        )
    elif missing and score < 85:
        warnings.append(
            f"Visual coverage could be stronger; underused: {', '.join(missing)}."
        )

    word_count = len(re.findall(r"\b\w+\b", text))
    rich_dna = sum(1 for v in expected.values() if v) >= 6
    if rich_dna and word_count < 90 and score < 85:
        warnings.append(
            "Prompt is short relative to the available Visual DNA; "
            "prefer concrete visual clauses over brief creative summary."
        )
    human_expected = any(
        expected.get(category)
        for category in ("human_orientation", "human_gaze", "human_hands", "human_relationship")
    )
    human_missing = [
        category
        for category in ("human_orientation", "human_gaze", "human_hands", "human_relationship")
        if expected.get(category) and not hits.get(category)
    ]
    if human_expected and human_missing:
        warnings.append(
            "Human pose information is underrepresented in the generated prompt "
            f"(missing: {', '.join(human_missing)})."
        )

    return score, hits, warnings


def validate_prompt(
    prompt: str, negative: str | None, target: PromptTarget, dna: VisualDNA
) -> PromptQuality:
    score = 100
    warnings: list[str] = []
    strengths: list[str] = []
    text = prompt.strip()

    if not text:
        return PromptQuality(
            score=0,
            warnings=["Prompt is empty."],
            strengths=[],
            visual_coverage_score=0,
            coverage={},
        )

    if len(text) < 60:
        warnings.append("Prompt is very thin: important visual information is likely missing.")
        score -= 25

    fillers = sorted({m.group(0).lower() for m in FILLER.finditer(text)})
    if fillers:
        warnings.append(f"Filler words that add little control: {', '.join(fillers)}")
        score -= 6 * len(fillers)

    claims = sorted({m.group(0) for m in TECH_CLAIM.finditer(text)})
    if claims:
        warnings.append(f"Unsupported technical claims (no evidence in the analysis): {', '.join(claims)}")
        score -= 10

    vague = sorted({m.group(0).lower() for m in VAGUE.finditer(text)})
    if vague:
        warnings.append(f"Vague language: {', '.join(vague)}")
        score -= 5 * len(vague)

    poetic = sorted({m.group(0).lower() for m in POETIC.finditer(text)})
    if len(poetic) >= 2:
        warnings.append(
            "Prompt leans on poetic mood language; replace with concrete visual behavior "
            f"where possible ({', '.join(poetic[:4])})."
        )
        score -= 4

    words = re.findall(r"[a-z']+", text.lower())
    shingles = [" ".join(words[i : i + 5]) for i in range(len(words) - 4)]
    seen: set[str] = set()
    repeated: set[str] = set()
    for shingle in shingles:
        if shingle in seen:
            repeated.add(shingle)
        seen.add(shingle)
    if repeated:
        warnings.append("Contains repeated phrases: tighten the wording so every clause earns its place.")
        score -= 6

    subject_terms: list[str] = []
    stopwords = {"with", "that", "this", "from", "into", "over", "near", "wearing", "while", "also"}
    for subject in dna.subjects[:3]:
        subject_terms.extend(
            term
            for term in re.findall(r"[a-z']{4,}", (subject.description + " " + subject.clothing).lower())
            if term not in stopwords
        )
    if subject_terms and not any(term in text.lower() for term in subject_terms):
        warnings.append("The analyzed subject does not appear to be described in the prompt.")
        score -= 15

    if negative:
        neg_fillers = sorted({m.group(0).lower() for m in FILLER.finditer(negative)})
        if neg_fillers:
            warnings.append(f"Negative prompt contains filler terms: {', '.join(neg_fillers)}")
            score -= 4
        if len(negative.split(",")) > 12:
            warnings.append("Negative prompt is a long boilerplate list: keep it specific to this image.")
            score -= 4

    if target.soft_char_limit and len(text) > target.soft_char_limit:
        warnings.append(f"Prompt exceeds the ~{target.soft_char_limit}-character comfort zone for {target.name}.")
        score -= 5

    prompt_temps: set[str] = set()
    if re.search(r"\bwarm\b", text, re.IGNORECASE):
        prompt_temps.add("warm")
    if re.search(r"\bcool\b", text, re.IGNORECASE):
        prompt_temps.add("cool")
    if len(prompt_temps) == 2:
        paired = bool(re.search(r"\bwarm\b[^.!?]{0,60}\bcool\b|\bcool\b[^.!?]{0,60}\bwarm\b", text, re.IGNORECASE))
        dna_temp = dna.color.warm_cool_balance.lower()
        if not paired and dna_temp in ("warm", "cool"):
            warnings.append(
                "Possible color-temperature contradiction: the analysis calls the image "
                f"'{dna.color.warm_cool_balance}'."
            )
            score -= 4

    coverage_score, coverage, coverage_warnings = compute_visual_coverage(text, dna)
    warnings.extend(coverage_warnings)

    # Fold coverage into overall score: under-coverage pulls quality down.
    if coverage_score < 55:
        score -= 18
    elif coverage_score < 70:
        score -= 10
    elif coverage_score < 85:
        score -= 4
    elif coverage_score >= 90:
        strengths.append("High visual information coverage relative to Visual DNA")

    if LIGHTING_WORDS.search(text):
        strengths.append("Concrete lighting direction present")
    if COMPOSITION_WORDS.search(text):
        strengths.append("Composition is described, not implied")
    if SPATIAL.search(text):
        strengths.append("Spatial relationships are explicit")
    if MATERIAL_WORDS.search(text):
        strengths.append("Materials/textures are specified")
    if WARDROBE_WORDS.search(text):
        strengths.append("Wardrobe is specified")

    return PromptQuality(
        score=max(0, min(100, score)),
        warnings=warnings,
        strengths=strengths,
        visual_coverage_score=coverage_score,
        coverage=coverage,
    )
