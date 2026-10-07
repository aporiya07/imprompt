import json

from app.main import app
from app.prompting.optimizer import _TEMPLATE_BY_MODE
from app.utils.errors import ProviderError, ProviderUnavailableError

from .conftest import (
    COLLAGE_PROMPT_REPLY,
    FAKE_PROMPT_REPLY,
    FAKE_VISION_REPLY,
    REFINE_REPLY,
    SAMPLE_COLLAGE_VISION_REPLY,
    SAMPLE_DNA_V2,
    SAMPLE_INTENT,
    make_runtime,
    unwrap,
)


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode()


class TestEnvelopeContract:
    """Phase 12: every endpoint uses the strict {success, data, error} envelope."""

    def test_health_envelope(self, client):
        body = client.get("/api/health").json()
        assert set(body) == {"success", "data", "error"}
        assert body["success"] is True and body["error"] is None
        assert body["data"]["status"] == "ok"

    def test_models_envelope(self, client):
        body = client.get("/api/models").json()
        assert body["success"] is True
        ids = {m["id"] for m in body["data"]["models"]}
        assert {"generic", "gemini", "openai", "flux", "midjourney", "stable_diffusion"} <= ids

    def test_error_envelope_includes_request_id(self, client, png_bytes):
        app.state.runtime = make_runtime([], [])[0]
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(b"not an image")})
        body = r.json()
        assert body["success"] is False
        assert body["data"] is None
        assert body["error"]["code"] == "unsupported_format"
        assert body["error"]["request_id"]


class TestAnalyze:
    def test_end_to_end(self, client, png_bytes):
        runtime, provider = make_runtime([FAKE_VISION_REPLY], [FAKE_PROMPT_REPLY])
        app.state.runtime = runtime
        r = client.post(
            "/api/analyze",
            json={"image": "data:image/png;base64," + _b64(png_bytes), "mode": "recreate", "target_model": "midjourney"},
        )
        assert r.status_code == 200, r.text
        data = unwrap(r)
        assert data["reference_type"] == "photograph"
        assert data["visual_dna"]["subjects"][0]["description"].startswith("a young woman")
        assert data["creative_intent"]["primary_goal"].startswith("Recreate")
        assert data["prompt"].endswith("--ar 3:2")  # Midjourney adapter appended the ratio
        assert data["prompt_quality"]["score"] >= 0
        assert data["shots"] == []
        assert provider.vision_calls == 1 and provider.text_calls == 1

    def test_analysis_cached_by_image_hash(self, client, png_bytes):
        runtime, provider = make_runtime([FAKE_VISION_REPLY], [FAKE_PROMPT_REPLY, FAKE_PROMPT_REPLY])
        app.state.runtime = runtime
        image = "data:image/png;base64," + _b64(png_bytes)
        assert client.post("/api/analyze", json={"image": image}).status_code == 200
        assert client.post("/api/analyze", json={"image": image, "target_model": "flux"}).status_code == 200
        assert provider.vision_calls == 1  # second call hit the analysis cache
        assert provider.text_calls == 2  # prompt regenerated for the new target

    def test_collage_end_to_end(self, client, png_bytes):
        runtime, provider = make_runtime([SAMPLE_COLLAGE_VISION_REPLY], [COLLAGE_PROMPT_REPLY])
        app.state.runtime = runtime
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        assert r.status_code == 200, r.text
        data = unwrap(r)
        assert data["reference_type"] == "moodboard"
        assert data["layout_description"] == "3x3 grid of nine photos"
        assert data["prompt"]  # master direction
        assert len(data["shots"]) == 2
        assert data["shots"][0]["quality"] is not None
        assert data["shots"][1]["negative_prompt"] == "distorted hands"
        assert provider.vision_calls == 1 and provider.text_calls == 1

    def test_modify_requires_instruction(self, client, png_bytes):
        app.state.runtime = make_runtime([], [])[0]
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes), "mode": "modify"})
        assert r.status_code == 400
        assert "instruction" in r.json()["error"]["message"].lower()

    def test_new_modes_accepted(self, client, png_bytes):
        runtime, provider = make_runtime([FAKE_VISION_REPLY], [FAKE_PROMPT_REPLY])
        app.state.runtime = runtime
        for mode in ("create_similar", "extract_composition", "extract_lighting", "extract_color", "extract_pose"):
            r = client.post(
                "/api/analyze",
                json={"image": "data:image/png;base64," + _b64(png_bytes), "mode": mode, "generate_prompt": True},
            )
            assert r.status_code == 200, f"{mode}: {r.text}"
            provider.text_replies.append(FAKE_PROMPT_REPLY)

    def test_unknown_target_model(self, client, png_bytes):
        app.state.runtime = make_runtime([], [])[0]
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes), "target_model": "dalle"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "bad_request"

    def test_empty_image_rejected(self, client):
        app.state.runtime = make_runtime([], [])[0]
        r = client.post("/api/analyze", json={"image": "data:image/png;base64,"})
        assert r.status_code == 400
        assert r.json()["error"]["code"] == "invalid_image"

    def test_non_image_bytes_rejected(self, client):
        app.state.runtime = make_runtime([], [])[0]
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(b"this is not an image at all")})
        assert r.status_code == 415

    def test_oversize_rejected(self, client, png_bytes, monkeypatch):
        monkeypatch.setenv("MAX_IMAGE_MB", "0")
        from app.config import get_settings

        get_settings.cache_clear()
        app.state.runtime = make_runtime([], [])[0]
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        assert r.status_code == 413
        assert r.json()["error"]["code"] == "image_too_large"

    def test_dna_returned_when_prompt_stage_fails(self, client, png_bytes):
        runtime, _ = make_runtime([FAKE_VISION_REPLY], [ProviderError("prompt model down")])
        app.state.runtime = runtime
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        assert r.status_code == 200
        data = unwrap(r)
        assert data["visual_dna"]["subjects"]
        assert data["prompt"] is None
        assert data["prompt_error"]["code"] == "provider_error"

    def test_fallback_provider_used_when_primary_missing(self, client, png_bytes):
        runtime, provider = make_runtime(
            [FAKE_VISION_REPLY],
            [FAKE_PROMPT_REPLY],
            register_as="fake",
            vision_primary="gemini",
            vision_fallback="fake",
            text_primary="openai",
            text_fallback="fake",
        )
        app.state.runtime = runtime
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        assert r.status_code == 200, r.text
        assert provider.vision_calls == 1 and provider.text_calls == 1

    def test_transient_error_retries_then_succeeds(self, client, png_bytes):
        runtime, provider = make_runtime(
            [ProviderUnavailableError("blip"), FAKE_VISION_REPLY], [FAKE_PROMPT_REPLY]
        )
        app.state.runtime = runtime
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        assert r.status_code == 200, r.text
        assert provider.vision_calls == 2

    def test_malformed_vision_json_retries_once(self, client, png_bytes):
        runtime, provider = make_runtime(
            ["prose without json", FAKE_VISION_REPLY], [FAKE_PROMPT_REPLY]
        )
        app.state.runtime = runtime
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        assert r.status_code == 200, r.text
        assert provider.vision_calls == 2

    def test_permanently_malformed_json_fails_cleanly(self, client, png_bytes):
        runtime, _ = make_runtime(["no json here", "still no json here"], [FAKE_PROMPT_REPLY])
        app.state.runtime = runtime
        r = client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)})
        assert r.status_code == 502
        assert r.json()["error"]["code"] == "malformed_ai_response"

    def test_aspect_ratio_filled_from_image(self, client, png_bytes):
        import copy

        payload = json.loads(FAKE_VISION_REPLY)
        payload["visual_dna"]["technical"] = {"aspect_ratio": "", "orientation": ""}
        runtime, _ = make_runtime([json.dumps(payload)], [FAKE_PROMPT_REPLY])
        app.state.runtime = runtime
        data = unwrap(client.post("/api/analyze", json={"image": "data:image/png;base64," + _b64(png_bytes)}))
        assert data["visual_dna"]["technical"]["aspect_ratio"] == "16:10"  # 64x40
        assert data["visual_dna"]["technical"]["orientation"] == "landscape"


class TestPromptEndpoints:
    def test_generate_prompt_with_intent(self, client):
        runtime, _ = make_runtime([], [FAKE_PROMPT_REPLY])
        app.state.runtime = runtime
        r = client.post(
            "/api/generate-prompt",
            json={
                "visual_dna": SAMPLE_DNA_V2,
                "creative_intent": SAMPLE_INTENT,
                "mode": "extract_style",
                "target_model": "flux",
            },
        )
        assert r.status_code == 200, r.text
        data = unwrap(r)
        assert data["prompt"].startswith("A young woman")
        assert data["quality"] is not None

    def test_generate_prompt_without_intent_still_works(self, client):
        runtime, _ = make_runtime([], [FAKE_PROMPT_REPLY])
        app.state.runtime = runtime
        r = client.post(
            "/api/generate-prompt",
            json={"visual_dna": SAMPLE_DNA_V2, "mode": "recreate", "target_model": "generic"},
        )
        assert r.status_code == 200, r.text

    def test_generate_prompt_drops_negative_for_gemini(self, client):
        runtime, _ = make_runtime([], [json.dumps({"prompt": "P", "negative_prompt": "blurry"})])
        app.state.runtime = runtime
        r = client.post(
            "/api/generate-prompt",
            json={"visual_dna": SAMPLE_DNA_V2, "mode": "recreate", "target_model": "gemini"},
        )
        assert unwrap(r)["negative_prompt"] is None

    def test_refine_prompt(self, client):
        runtime, _ = make_runtime([], [REFINE_REPLY])
        app.state.runtime = runtime
        r = client.post(
            "/api/refine-prompt",
            json={
                "visual_dna": SAMPLE_DNA_V2,
                "creative_intent": SAMPLE_INTENT,
                "current_prompt": "P1",
                "instruction": "Keep everything but change the lighting to sunset.",
                "mode": "recreate",
                "target_model": "generic",
            },
        )
        assert r.status_code == 200, r.text
        data = unwrap(r)
        assert data["prompt"].startswith("Revised prompt P2")
        assert data["change"] == ["lighting"]
        assert "composition" in data["keep"]
        assert data["quality"] is not None


class TestModeTemplates:
    def test_all_eight_modes_have_templates(self):
        assert len(_TEMPLATE_BY_MODE) == 8
        for mode, (template, _aspect) in _TEMPLATE_BY_MODE.items():
            assert template
