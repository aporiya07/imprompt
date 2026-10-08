import pytest

from app.models.dna import VisualDNA, dna_from_payload, normalize_dna_payload
from app.models.intent import CreativeIntent, derive_intent_from_dna, intent_from_payload
from app.utils.errors import BadRequestError


class TestNormalizeDNAv2:
    def test_subjects_from_single_flat_subject(self):
        out = normalize_dna_payload({"subject": {"primary_subject": "a woman", "pose": "seated"}})
        assert len(out["subjects"]) == 1
        assert out["subjects"][0]["label"] == "subject_1"
        assert out["subjects"][0]["description"] == "a woman"

    def test_structured_human_pose_is_preserved(self):
        out = normalize_dna_payload(
            {
                "subjects": [
                    {
                        "label": "subject_1",
                        "type": "person",
                        "body_pose": {
                            "state": "standing",
                            "torso_orientation": "three-quarter toward camera",
                            "head_orientation": "turned toward subject_2",
                            "confidence": "high",
                        },
                        "gaze": {"direction": "downward", "target": "subject_2"},
                        "left_hand": {
                            "visibility": "visible",
                            "position": "resting on subject_2's forearm",
                            "contact": "hand contact",
                        },
                        "body_visibility": {
                            "visible_body_regions": ["head", "torso", "left hand"],
                            "occluded_body_regions": ["feet"],
                        },
                    }
                ],
                "relationships": [
                    {
                        "subject": "subject_1",
                        "relation": "in front of",
                        "object": "subject_2",
                        "depth_order": "foreground",
                        "occlusion": "subject_2 partly occluded",
                        "contact_points": ["left hand to forearm"],
                    }
                ],
            }
        )
        subject = out["subjects"][0]
        assert subject["body_pose"]["torso_orientation"] == "three-quarter toward camera"
        assert subject["gaze"]["target"] == "subject_2"
        assert subject["left_hand"]["contact"] == "hand contact"
        assert subject["body_visibility"]["occluded_body_regions"] == ["feet"]
        assert out["relationships"][0]["depth_order"] == "foreground"

        dna = VisualDNA.model_validate(out)
        assert dna.subjects[0].body_pose.head_orientation == "turned toward subject_2"
        assert dna.relationships[0].contact_points == ["left hand to forearm"]

    def test_subject_from_plain_string(self):
        out = normalize_dna_payload({"subjects": "a red sphere"})
        assert out["subjects"] == [{"label": "subject_1", "description": "a red sphere", "type": "unknown"}]

    def test_swatch_from_string_with_hex(self):
        out = normalize_dna_payload({"color": {"dominant": ["sage green (#8A9A5B)"]}})
        assert out["color"]["dominant"] == [{"name": "sage green", "hex": "8A9A5B", "role": ""}]

    def test_swatch_from_dict(self):
        out = normalize_dna_payload({"color": {"dominant": [{"name": "teal", "hex": "#4a7c7e", "role": "accent"}]}})
        assert out["color"]["dominant"][0]["role"] == "accent"

    def test_confidence_clamped(self):
        out = normalize_dna_payload({"reference": {"analysis_confidence": 5}})
        assert out["reference"]["analysis_confidence"] == 1.0

    def test_reference_type_coerced(self):
        out = normalize_dna_payload({"reference": {"reference_type": "Moodboard"}})
        assert out["reference"]["reference_type"] == "moodboard"

    def test_unknown_reference_type_falls_back(self):
        out = normalize_dna_payload({"reference": {"reference_type": "hologram"}})
        assert out["reference"]["reference_type"] == "unknown"

    def test_elements_importance(self):
        out = normalize_dna_payload(
            {"elements": [{"description": "golden backlight", "importance": "ESSENTIAL"}, "a rock"]}
        )
        assert out["elements"][0]["importance"] == "essential"
        assert out["elements"][1]["importance"] == "uncertain"

    def test_typography_present_from_text(self):
        out = normalize_dna_payload({"typography": {"text_content": ["SALE 50%"]}})
        assert out["typography"]["present"] is True
        assert out["typography"]["text_content"] == ["SALE 50%"]

    def test_mood_from_string(self):
        out = normalize_dna_payload({"mood": "calm and warm"})
        assert out["mood"]["description"] == "calm and warm"

    def test_relationships_from_strings(self):
        out = normalize_dna_payload({"relationships": ["subject_1 facing subject_2"]})
        assert out["relationships"] == [{"description": "subject_1 facing subject_2"}]

    def test_section_confidence_defaults(self):
        out = normalize_dna_payload({"lighting": {"lighting_type": "soft window light"}})
        assert out["lighting"]["confidence"] == "medium"

    def test_materials_from_string(self):
        out = normalize_dna_payload({"materials": "oak table"})
        assert out["materials"] == [{"object": "oak table"}]


class TestVisualDNAv2:
    def test_empty_dict_is_valid(self):
        dna = VisualDNA.model_validate(normalize_dna_payload({}))
        assert dna.subjects == []
        assert dna.reference.reference_type.value == "unknown"
        assert dna.interpretation.creative_reading == ""

    def test_full_sample(self, sample_dna):
        dna = VisualDNA.model_validate(normalize_dna_payload(sample_dna))
        assert dna.subjects[0].description.startswith("a young woman")
        assert dna.color.dominant[0].hex == "#D4A017"
        assert dna.elements[0].importance.value == "essential"
        assert dna.lighting.time_based_look == "golden hour"

    def test_roundtrip_through_payload(self, sample_dna):
        raw = VisualDNA.model_validate(normalize_dna_payload(sample_dna)).model_dump(mode="json")
        dna = dna_from_payload(raw)
        assert dna.lighting.quality == "soft"

    def test_rejects_non_dict(self):
        with pytest.raises(BadRequestError):
            dna_from_payload("not an object")  # type: ignore[arg-type]

    def test_bad_count_degrades_to_one(self):
        dna = dna_from_payload({"subjects": [{"count": "way too many"}]})
        assert dna.subjects[0].count == 1


class TestCreativeIntent:
    def test_from_payload(self):
        intent = intent_from_payload(
            {"primary_goal": "Recreate a beach editorial", "preserve": ["golden-hour backlight"], "confidence": "low"}
        )
        assert intent.primary_goal.startswith("Recreate")
        assert intent.confidence.value == "low"

    def test_derivation_from_dna(self, sample_dna):
        dna = VisualDNA.model_validate(normalize_dna_payload(sample_dna))
        intent = derive_intent_from_dna(dna)
        assert "golden-hour backlight" in intent.preserve
        assert "small rock near the table leg" in intent.flexible
        assert intent.lighting_strategy
        assert intent.subject_strategy.startswith("a young woman")

    def test_derivation_on_empty_dna(self):
        dna = VisualDNA.model_validate(normalize_dna_payload({}))
        intent = derive_intent_from_dna(dna)
        assert intent.primary_goal  # still a usable goal
        assert isinstance(intent, CreativeIntent)
