import pytest

from app.models.schemas import VisualDNA
from app.prompting.adapters import all_targets, get_target
from app.prompting.adapters.midjourney import midjourney_target
from app.prompting.adapters.stable_diffusion import stable_diffusion_target
from app.utils.errors import BadRequestError


@pytest.fixture()
def dna(sample_dna):
    from app.models.dna import normalize_dna_payload

    return VisualDNA.model_validate(normalize_dna_payload(sample_dna))


class TestRegistry:
    def test_six_targets(self):
        ids = {t.id for t in all_targets()}
        assert ids == {"generic", "gemini", "openai", "flux", "midjourney", "stable_diffusion"}

    def test_unknown_raises(self):
        with pytest.raises(BadRequestError):
            get_target("dalle")

    def test_lookup_case_insensitive(self):
        assert get_target("Midjourney").id == "midjourney"


class TestMidjourney:
    def test_appends_ar(self, dna):
        out = midjourney_target.post_process("a woman in a cafe, film grain", dna)
        assert out.endswith("--ar 3:2")

    def test_does_not_duplicate_ar(self, dna):
        out = midjourney_target.post_process("a woman --ar 4:5", dna)
        assert out.endswith("--ar 4:5")
        assert out.count("--ar") == 1

    def test_no_ar_without_ratio(self, dna):
        dna.technical.aspect_ratio = ""
        out = midjourney_target.post_process("a woman in a cafe", dna)
        assert "--ar" not in out

    def test_decimal_ratio(self, dna):
        dna.technical.aspect_ratio = "1.5:1"
        out = midjourney_target.post_process("a woman", dna)
        assert out.endswith("--ar 1.5:1")

    def test_negative_not_supported(self):
        assert midjourney_target.supports_negative is False


class TestStableDiffusion:
    def test_collapses_whitespace(self, dna):
        out = stable_diffusion_target.post_process("a  woman ,  cafe ,   warm light", dna)
        assert out == "a woman, cafe, warm light"

    def test_negative_supported(self):
        assert stable_diffusion_target.supports_negative is True
