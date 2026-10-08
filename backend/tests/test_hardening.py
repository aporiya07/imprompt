"""v0.3 hardening: input limits, validate-prompt endpoint, diagnostics fixes."""
from app.main import app

from .conftest import SAMPLE_DNA_V2, make_runtime


class TestInputLimits:
    def test_oversized_instruction_rejected(self, client):
        r = client.post(
            "/api/analyze",
            json={"image": "data:image/png;base64,AAA", "mode": "modify", "instruction": "x" * 3000},
        )
        assert r.status_code == 422 or r.json()["error"]["code"] == "validation_error"

    def test_oversized_refine_instruction_rejected(self, client):
        r = client.post(
            "/api/refine-prompt",
            json={
                "visual_dna": SAMPLE_DNA_V2,
                "current_prompt": "p",
                "instruction": "y" * 3000,
                "mode": "recreate",
                "target_model": "generic",
            },
        )
        assert r.status_code in (400, 422)

    def test_oversized_current_prompt_rejected(self, client):
        r = client.post(
            "/api/refine-prompt",
            json={
                "visual_dna": SAMPLE_DNA_V2,
                "current_prompt": "p" * 30_000,
                "instruction": "change the light",
                "mode": "recreate",
                "target_model": "generic",
            },
        )
        assert r.status_code in (400, 422)

    def test_oversized_url_rejected(self, client):
        r = client.post("/api/fetch-image", json={"url": "https://example.com/" + "a" * 3000})
        assert r.status_code in (400, 422)

    def test_oversized_dna_payload_rejected(self, client):
        bloated = dict(SAMPLE_DNA_V2)
        bloated["padding"] = "z" * 300_000
        r = client.post(
            "/api/generate-prompt",
            json={"visual_dna": bloated, "mode": "recreate", "target_model": "generic"},
        )
        assert r.status_code in (400, 422)

    def test_oversized_base64_image_rejected_before_decode(self, client, png_bytes):
        import base64

        from app.config import get_settings

        app.state.runtime = make_runtime([], [])[0]
        # Exceed the encoded-payload gate (max_image_bytes * 1.37) before decode runs.
        limit = int(get_settings().max_image_bytes * 1.37) + 1024
        padding = "A" * (limit + 1024)
        huge = "data:image/png;base64," + base64.b64encode(png_bytes).decode() + padding
        r = client.post("/api/analyze", json={"image": huge})
        assert r.status_code == 413
        assert r.json()["error"]["code"] == "image_too_large"

    def test_legitimate_dna_still_accepted(self, client):
        runtime, _ = make_runtime(
            [], ['{"prompt": "A warm portrait at golden hour with soft backlight", "negative_prompt": null}']
        )
        app.state.runtime = runtime
        r = client.post(
            "/api/generate-prompt",
            json={"visual_dna": SAMPLE_DNA_V2, "mode": "recreate", "target_model": "generic"},
        )
        assert r.status_code == 200


class TestValidatePromptEndpoint:
    def test_returns_deterministic_quality(self, client):
        r = client.post(
            "/api/validate-prompt",
            json={"prompt": "masterpiece, stunning, ultra detailed generic scene", "target_model": "generic"},
        )
        assert r.status_code == 200
        quality = r.json()["data"]["quality"]
        assert quality["score"] < 100
        assert any("Filler" in w for w in quality["warnings"])

    def test_with_dna_context(self, client):
        r = client.post(
            "/api/validate-prompt",
            json={
                "prompt": "A young woman with curly red hair in a mustard knit sweater, golden-hour backlight, "
                "shallow depth of field, soft rim light from behind",
                "target_model": "generic",
                "visual_dna": SAMPLE_DNA_V2,
            },
        )
        assert r.status_code == 200
        quality = r.json()["data"]["quality"]
        assert quality["score"] >= 80

    def test_unknown_model_rejected(self, client):
        r = client.post("/api/validate-prompt", json={"prompt": "x", "target_model": "nope"})
        assert r.status_code == 400


class TestWarmCoolDiagnostics:
    def _dna(self, balance):
        import copy

        from app.models.dna import VisualDNA, normalize_dna_payload

        payload = copy.deepcopy(SAMPLE_DNA_V2)
        payload["color"]["warm_cool_balance"] = balance
        return VisualDNA.model_validate(normalize_dna_payload(payload))

    def test_split_lighting_not_flagged(self):
        from app.prompting.adapters import get_target
        from app.prompting.diagnostics import validate_prompt

        prompt = (
            "A portrait with warm highlights and cool shadows, golden-hour backlight raking across the subject, "
            "soft fill from the left, the couple standing close beside the shoreline"
        )
        quality = validate_prompt(prompt, None, get_target("generic"), self._dna("warm"))
        assert not any("contradiction" in w for w in quality.warnings)

    def test_unpaired_contradiction_still_flagged(self):
        from app.prompting.adapters import get_target
        from app.prompting.diagnostics import validate_prompt

        prompt = (
            "A scene with a warm color grade overall. Somewhere far later the shadows are cool toned. "
            "More text to distance the words apart from each other so the pairing heuristic does not fire."
        )
        quality = validate_prompt(prompt, None, get_target("generic"), self._dna("warm"))
        assert any("contradiction" in w for w in quality.warnings)


class TestPanelsExposed:
    def test_collage_response_includes_panel_bounds(self, client, png_bytes):

        from .conftest import COLLAGE_PROMPT_REPLY, SAMPLE_COLLAGE_VISION_REPLY

        runtime, _ = make_runtime([SAMPLE_COLLAGE_VISION_REPLY], [COLLAGE_PROMPT_REPLY])
        app.state.runtime = runtime
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        data = r.json()["data"]
        assert data["panels"], "collage responses must expose panel metadata"
        assert data["panels"][0]["bounds"] is not None
        assert 0.0 <= data["panels"][0]["bounds"]["w"] <= 1.0


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode()
