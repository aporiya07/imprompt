"""Regression tests for prompt information density and visual coverage.

Validates the coastal 3x3 moodboard quality problem: short poetic summaries
must score worse than concrete generation specifications that preserve
wardrobe, relationships, lighting, composition, and series continuity.
"""
from __future__ import annotations

from app.models.common import PromptMode
from app.models.dna import VisualDNA, normalize_dna_payload
from app.models.intent import derive_intent_from_dna
from app.prompting.adapters import get_target
from app.prompting.diagnostics import compute_visual_coverage, validate_prompt
from app.prompting.prompt_spec import build_prompt_spec
from app.prompts.loader import load_template

# Rich Visual DNA approximating the supplied 3x3 South Asian coastal moodboard.
COASTAL_MOODBOARD_DNA = {
    "reference": {
        "reference_type": "moodboard",
        "reference_type_confidence": "high",
        "layout_description": "3x3 grid of nine editorial photographs",
        "overall_description": (
            "A nine-panel South Asian coastal pre-wedding editorial moodboard "
            "following the same couple across intimate portraits and shoreline frames."
        ),
        "analysis_confidence": 0.9,
    },
    "subjects": [
        {
            "label": "subject_1",
            "type": "person",
            "count": 1,
            "description": "South Asian woman with long dark hair and warm skin",
            "clothing": "rich crimson silk saree with narrow gold border",
            "accessories": ["traditional gold jewelry", "red and gold bangles"],
            "pose": "standing close to partner, turning slightly toward him",
            "body_orientation": "three-quarter toward partner",
            "facial_expression": "soft natural smile",
            "gaze_direction": "looking up toward partner's face",
            "position_in_frame": "slightly forward of partner",
            "interactions": ["embraced from behind", "hand contact"],
            "confidence": "high",
        },
        {
            "label": "subject_2",
            "type": "person",
            "count": 1,
            "description": "South Asian man with short styled dark hair",
            "clothing": "ivory textured traditional kurta",
            "pose": "standing slightly behind the woman",
            "body_orientation": "facing her, bodies aligned diagonally",
            "facial_expression": "warm natural expression",
            "gaze_direction": "looking at her face",
            "interactions": ["arm around her waist", "protective embrace from behind"],
            "confidence": "high",
        },
    ],
    "environment": {
        "location_type": "open beach shoreline",
        "setting": "outdoor",
        "foreground": "soft wet sand",
        "midground": "couple on the shoreline",
        "background": "muted pale blue-grey sea and pale sky at the horizon",
        "landscape": "calm water, shallow surf, sparse coastal vegetation",
        "atmosphere": "soft haze with gentle atmospheric diffusion",
        "time_of_day": "late afternoon / sunset",
        "spatial_relationships": [
            "couple near waterline with open horizon behind",
            "pale shoreline creating negative space around subjects",
        ],
        "confidence": "high",
    },
    "composition": {
        "shot_type": "mixed editorial series: intimate close, medium, environmental wide",
        "framing": "alternating waist-up portraits and full-body environmental frames",
        "camera_angle": "eye-level",
        "viewpoint": "eye-level shoreline perspective",
        "subject_placement": "often slightly off-center with open coastal negative space",
        "balance": "asymmetric with horizon as stabilizing line",
        "negative_space": "open pale sea and sky around the couple",
        "depth": "shallow separation in close shots; deeper environmental depth in wides",
        "subject_scale": "varies from close portrait crop to full-body",
        "foreground_background_relationship": "soft background separation from shoreline horizon",
        "confidence": "high",
    },
    "camera": {
        "perspective": "eye-level",
        "focal_length_category": "short-telephoto appearance in portraits",
        "depth_of_field": "shallow in close shots",
        "background_blur": "soft coastal background separation",
        "perspective_compression": "mild compression on intimate portraits",
        "realism_level": "photographic",
        "confidence": "medium",
    },
    "lighting": {
        "lighting_type": "natural sunset-inspired backlight",
        "key_light_direction": "soft low-angle backlight from the setting sun",
        "fill_level": "diffused ambient sky fill across faces",
        "rim_light": "subtle warm rim along hair and shoulders",
        "quality": "soft",
        "source": "natural",
        "color_temperature": "warm amber highlights",
        "time_based_look": "sunset / late afternoon",
        "highlights": "soft highlight rolloff; restrained specular on jewelry and silk",
        "shadows": "lifted facial shadows",
        "contrast": "restrained low contrast",
        "atmospheric_effects": "gentle atmospheric haze",
        "confidence": "high",
    },
    "color": {
        "dominant": [
            {"name": "crimson", "hex": "#9B1B2E", "role": "wardrobe anchor"},
            {"name": "ivory", "hex": "#F3EDE3", "role": "wardrobe anchor"},
            {"name": "muted sand", "hex": "#C9B8A0", "role": "environment"},
        ],
        "secondary": [{"name": "pale blue-grey", "hex": "#A8B4BE", "role": "sea and sky"}],
        "accent": [{"name": "warm amber", "role": "highlights"}, {"name": "restrained gold", "role": "jewelry"}],
        "palette_description": "crimson and ivory wardrobe anchors against muted coastal blue-grey and sand",
        "warm_cool_balance": "mixed",
        "saturation": "low environmental saturation; wardrobe accents richer",
        "color_grading": "muted creamy editorial grade",
        "tonal_characteristics": "creamy highlights, subdued environment",
        "confidence": "high",
    },
    "style": {
        "photography_style": "luxury pre-wedding editorial photography",
        "editorial_style": "coastal romantic editorial series",
        "cultural_aesthetic": "South Asian festive traditional attire on a minimal modern shoreline",
        "art_direction": "intimate affectionate rather than exaggerated posing",
        "confidence": "high",
    },
    "mood": {
        "description": "intimate romantic calm",
        "emotional_tone": ["affectionate", "serene", "tender"],
        "atmosphere": "soft haze",
        "intimacy": "high",
        "confidence": "high",
    },
    "materials": [
        {"object": "saree", "material": "silk", "texture": "soft sheen", "appearance": "visible silk drape"},
        {"object": "kurta", "material": "woven textile", "texture": "visible fabric weave"},
        {"object": "jewelry", "material": "metallic gold", "reflectivity": "restrained specular highlights"},
        {"object": "sand", "material": "wet sand", "appearance": "soft reflective shoreline"},
        {"object": "skin", "material": "skin", "appearance": "warm natural skin rendering"},
        {"object": "hair", "material": "natural hair", "appearance": "soft dark hair with rim light"},
    ],
    "typography": {"present": False},
    "relationships": [
        {
            "subject": "subject_2",
            "relation": "behind",
            "object": "subject_1",
            "description": "man stands slightly behind the woman with one arm around her waist",
        },
        {
            "subject": "subject_1",
            "relation": "facing",
            "object": "subject_2",
            "description": "couple face-to-face with forehead/temple proximity and eye contact",
        },
        {
            "subject": "subject_1",
            "relation": "holding",
            "object": "subject_2",
            "description": "gentle hand interaction and natural affectionate touch",
        },
    ],
    "elements": [
        {"description": "crimson silk saree with gold border", "importance": "essential"},
        {"description": "ivory textured kurta", "importance": "essential"},
        {"description": "sunset backlight with warm rim", "importance": "essential"},
        {"description": "muted coastal shoreline environment", "importance": "essential"},
        {"description": "editorial series continuity across panels", "importance": "essential"},
        {"description": "sparse coastal vegetation", "importance": "supporting"},
        {"description": "occasional tree branches", "importance": "incidental"},
    ],
    "interpretation": {
        "creative_reading": "intimate South Asian coastal pre-wedding editorial series",
        "confidence": "high",
    },
    "technical": {"aspect_ratio": "1:1", "orientation": "square"},
}


def coastal_dna() -> VisualDNA:
    return VisualDNA.model_validate(normalize_dna_payload(COASTAL_MOODBOARD_DNA))


# Current-problem style: poetic, short, abstract.
SHORT_POETIC = (
    "Create a quietly romantic coastal editorial series that pairs traditional South Asian "
    "festive attire with a minimal, modern shoreline. Keep the woman in a rich crimson silk "
    "saree with gold accents and the man in an ivory textured kurta, set against muted sand, "
    "sea, and pale sky warmed by sunset amber. Use soft natural backlight, a subtle golden rim, "
    "gentle ambient fill, lifted shadows, and shallow depth of field for a dreamy, polished "
    "photographic finish. Across intimate portraits, tactile details, and wider environmental "
    "frames, emphasize sincere micro-expressions and tender touch without losing the calm, serene mood."
)

# Target-style: dense generation specification.
DENSE_SPEC = (
    "An intimate South Asian coastal pre-wedding editorial series following the same couple "
    "across romantic shoreline portraits and environmental frames. The woman wears a rich crimson "
    "silk saree with a narrow gold border, traditional gold jewelry and red-gold bangles; the man "
    "wears an ivory textured kurta with visible woven fabric. Their interactions stay natural and "
    "affectionate: he often stands slightly behind her with an arm around her waist, or they stand "
    "face-to-face with forehead proximity and eye contact, gentle hand contact, walking and seated "
    "shoreline compositions. Environment stays minimal and coastal—muted pale blue-grey sea and sky, "
    "soft wet sand, shallow surf and sparse vegetation—with open negative space around the couple. "
    "Lighting remains soft late-day backlight from the setting sun, a subtle warm amber rim along "
    "hair and shoulders, diffused ambient fill keeping facial shadows lifted, restrained jewelry "
    "speculars and gentle atmospheric haze. Grade stays muted and creamy so crimson, ivory and "
    "restrained gold remain anchors while the environment falls into subdued sand and blue-grey. "
    "Photography alternates waist-up intimate portraits, medium interaction frames and wider "
    "full-body environmental compositions while preserving wardrobe continuity, palette, emotional "
    "tone and soft editorial rendering with realistic skin texture and visible textile weave."
)

DENSE_SHOT = (
    "Medium close portrait of the same South Asian couple at the shoreline, the woman in a crimson "
    "silk saree with a narrow gold border and traditional bangles, the man in an ivory textured kurta "
    "standing close behind her with one arm around her waist. She turns slightly toward him while "
    "looking upward with a soft natural smile; his gaze rests on her face. Frame from approximately "
    "the waist upward, using shallow depth of field and keeping the pale sea and hazy horizon softly "
    "separated in the background. Diffused late-day backlight creates a subtle warm rim along their "
    "hair and shoulders while soft ambient fill keeps facial shadows lifted. Preserve the muted "
    "coastal palette of pale blue-grey, sand and warm amber, with crimson and ivory as the dominant "
    "wardrobe anchors. Maintain a restrained luxury pre-wedding editorial finish, realistic skin "
    "texture, visible textile weave, delicate jewelry highlights and gentle atmospheric haze."
)


class TestPromptSpec:
    def test_assembles_priority_facts_from_dna(self):
        dna = coastal_dna()
        intent = derive_intent_from_dna(dna)
        spec = build_prompt_spec(dna, intent, PromptMode.RECREATE)
        assert spec["subjects"]
        assert any("crimson" in (s.get("clothing") or "").lower() for s in spec["subjects"])
        assert any("kurta" in (s.get("clothing") or "").lower() for s in spec["subjects"])
        assert spec["composition"].get("framing") or spec["composition"].get("shot_type")
        assert spec["lighting"].get("rim_light") or spec["lighting"].get("key_light_direction")
        assert spec["materials"]
        assert spec["relationships"]
        assert spec["relationship_graph"]
        assert "priority_order" in spec
        assert "series_continuity" in spec
        assert "anti_patterns" in spec

    def test_intent_preserves_wardrobe_and_relationships(self):
        intent = derive_intent_from_dna(coastal_dna())
        joined = " ".join(intent.preserve).lower()
        assert "crimson" in joined or "saree" in joined or "sari" in joined
        assert "kurta" in joined or "ivory" in joined
        assert any("behind" in p.lower() or "arm" in p.lower() or "face" in p.lower() for p in intent.preserve)


class TestVisualCoverage:
    def test_human_geometry_is_scored_when_dna_contains_it(self):
        dna = coastal_dna()
        woman = dna.subjects[0]
        woman.body_pose.torso_orientation = "three-quarter toward camera"
        woman.body_pose.head_orientation = "turned toward subject_2"
        woman.gaze.direction = "looking toward subject_2"
        woman.gaze.target = "subject_2"
        woman.left_hand.position = "resting over his forearm"
        woman.left_hand.contact = "hand contact"
        woman.right_hand.visibility = "occluded"
        prompt = (
            "The woman stands slightly in front of the man, her torso three-quarter toward the camera "
            "and her head turned toward subject_2. Her gaze looks toward his face; her left hand rests "
            "over his forearm while her right hand is occluded. The man stands behind her with one arm "
            "around her waist; their bodies overlap and the woman is closer to camera."
        )
        quality = validate_prompt(prompt, None, get_target("generic"), dna)
        assert quality.coverage
        assert quality.coverage.get("human_orientation") is True
        assert quality.coverage.get("human_gaze") is True
        assert quality.coverage.get("human_hands") is True
        assert quality.coverage.get("human_relationship") is True
        assert not any("Human pose information is underrepresented" in w for w in quality.warnings)

    def test_short_poetic_underrepresents_rich_dna(self):
        dna = coastal_dna()
        score, hits, warnings = compute_visual_coverage(SHORT_POETIC, dna)
        quality = validate_prompt(SHORT_POETIC, None, get_target("generic"), dna)
        # Poetic summary may hit some keywords but should not be treated as excellent coverage.
        assert quality.visual_coverage_score is not None
        assert any(
            "under-representing" in w.lower()
            or "short relative" in w.lower()
            or "poetic" in w.lower()
            or "coverage" in w.lower()
            for w in quality.warnings
        ) or score < 90
        # Dense prompt must beat the thin poetic one on coverage.
        dense_score, _, _ = compute_visual_coverage(DENSE_SPEC, dna)
        assert dense_score > score
        assert dense_score >= 85

    def test_dense_spec_covers_required_coastal_concepts(self):
        dna = coastal_dna()
        quality = validate_prompt(DENSE_SPEC, None, get_target("generic"), dna)
        assert quality.visual_coverage_score is not None
        assert quality.visual_coverage_score >= 85
        assert quality.score >= 75
        assert quality.coverage
        for key in (
            "subject",
            "wardrobe",
            "pose_expression",
            "relationship_spatial",
            "composition",
            "environment",
            "lighting",
            "color",
            "materials",
        ):
            assert quality.coverage.get(key) is True, f"expected coverage hit for {key}"
        assert quality.coverage.get("series_continuity") is True

    def test_dense_shot_prompt_covers_shot_controls(self):
        dna = coastal_dna()
        score, hits, _ = compute_visual_coverage(DENSE_SHOT, dna)
        assert score >= 80
        assert hits.get("wardrobe")
        assert hits.get("pose_expression")
        assert hits.get("lighting")
        assert hits.get("composition")

    def test_missing_category_not_punished_when_dna_empty(self):
        bare = VisualDNA.model_validate(
            normalize_dna_payload(
                {
                    "reference": {"reference_type": "photograph", "overall_description": "abstract light study"},
                    "subjects": [],
                    "lighting": {"lighting_type": "soft window light", "quality": "soft", "confidence": "high"},
                    "color": {"palette_description": "cool blue grade", "warm_cool_balance": "cool"},
                }
            )
        )
        prompt = (
            "Soft window light from camera-left with gentle falloff across a cool blue grade, "
            "restrained contrast and creamy highlight rolloff for a quiet photographic study."
        )
        score, hits, warnings = compute_visual_coverage(prompt, bare)
        assert "wardrobe" not in hits
        assert "subject" not in hits
        assert score >= 70
        assert not any("under-representing" in w for w in warnings)

    def test_repetitive_long_prompt_not_rewarded_over_dense(self):
        dna = coastal_dna()
        padded = (
            "beautiful dreamy cinematic elegant romantic coastal scene, "
            "stunning beautiful amazing gorgeous masterpiece ultra detailed highly detailed, "
        ) * 12 + " woman man beach"
        quality_pad = validate_prompt(padded, None, get_target("generic"), dna)
        quality_dense = validate_prompt(DENSE_SPEC, None, get_target("generic"), dna)
        assert quality_dense.score > quality_pad.score
        assert quality_dense.visual_coverage_score >= (quality_pad.visual_coverage_score or 0)


class TestOptimizerTemplates:
    def test_recreate_template_has_anti_summarization_rules(self):
        text = load_template("recreate")
        assert "Compress redundancy, not visual information" in text
        assert "GENERATION SPECIFICATION" in text or "generation specification" in text.lower()
        assert "not an image caption" in text.lower() or "not an image caption" in text

    def test_collage_template_requires_series_and_shot_density(self):
        text = load_template("collage")
        assert "Do NOT flatten the collage" in text or "do NOT flatten" in text
        assert "wardrobe continuity" in text.lower()
        assert "100-220" in text or "100–220" in text
        assert "Compress redundancy, not visual information" in text

    def test_create_similar_has_density_rules(self):
        text = load_template("create_similar")
        assert "Compress redundancy, not visual information" in text
        assert "generation specification" in text.lower()
