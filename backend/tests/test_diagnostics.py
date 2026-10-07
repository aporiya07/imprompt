from app.models.dna import VisualDNA, normalize_dna_payload
from app.models.quality import PromptQuality
from app.prompting.adapters import get_target
from app.prompting.diagnostics import validate_prompt

from .conftest import SAMPLE_DNA_V2


def dna():
    return VisualDNA.model_validate(normalize_dna_payload(SAMPLE_DNA_V2))


class TestDiagnostics:
    def test_clean_prompt_scores_high(self):
        prompt = (
            "A young woman with curly red hair in a mustard knit sweater, seated at an outdoor cafe "
            "terrace, waist-up portrait placed on the left third with open negative space, golden-hour "
            "backlight with soft falloff, warm cream and brown palette, shallow depth of field with the "
            "porcelain cup beside her in the foreground"
        )
        quality = validate_prompt(prompt, "distorted hands", get_target("generic"), dna())
        assert quality.score >= 80
        assert quality.strengths  # lighting/composition/spatial/materials strengths
        assert all("Filler" not in w for w in quality.warnings)

    def test_filler_words_penalized(self):
        prompt = "A masterpiece, stunning, ultra detailed photo of a masterpiece scene. " + "x" * 40
        quality = validate_prompt(prompt, None, get_target("generic"), dna())
        assert any("Filler" in w for w in quality.warnings)
        assert quality.score < 100

    def test_technical_claims_flagged(self):
        prompt = "A woman seated at a cafe, shot on 85mm f/1.4, ISO 400. " + "x" * 60
        quality = validate_prompt(prompt, None, get_target("generic"), dna())
        assert any("Unsupported technical claims" in w for w in quality.warnings)

    def test_missing_subject_detected(self):
        prompt = "An outdoor scene with trees, a table, and warm light everywhere in frame. " + "x" * 40
        quality = validate_prompt(prompt, None, get_target("generic"), dna())
        assert any("subject" in w.lower() for w in quality.warnings)

    def test_empty_prompt(self):
        quality = validate_prompt("   ", None, get_target("generic"), dna())
        assert quality.score == 0
        assert isinstance(quality, PromptQuality)

    def test_repetition_detected(self):
        prompt = ("the woman sits at the table and the woman sits at the table and the woman sits "
                  "at the table and more text follows here to pad the length out fully")
        quality = validate_prompt(prompt, None, get_target("generic"), dna())
        assert any("repeated phrases" in w for w in quality.warnings)

    def test_char_limit_warning_for_midjourney(self):
        prompt = ("a woman " * 260).strip()
        quality = validate_prompt(prompt, None, get_target("midjourney"), dna())
        assert any("comfort zone" in w for w in quality.warnings)

    def test_negative_boilerplate_flagged(self):
        prompt = "A young woman with curly red hair in a mustard knit sweater seated outdoors in warm light"
        negative = ", ".join(["blurry", "low quality", "bad anatomy", "watermark", "text", "jpeg artifacts",
                              "cropped", "out of frame", "duplicate", "morbid", "disfigured", "mutation", "ugly"])
        quality = validate_prompt(prompt, negative, get_target("generic"), dna())
        assert any("Negative prompt" in w for w in quality.warnings)
