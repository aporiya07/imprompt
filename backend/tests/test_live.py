"""Optional live AI tests (spec Phase 16).

Run with:  RUN_LIVE_TESTS=1 uv run pytest tests/test_live.py
Requires real keys in backend/.env. Never selected in the default suite.
"""
import pytest

from .conftest import data_url


def _png():
    import io

    from PIL import Image, ImageDraw

    img = Image.new("RGB", (320, 240))
    d = ImageDraw.Draw(img)
    for y in range(240):
        d.line([(0, y), (320, y)], fill=(240 - y // 6, 200 - y // 8, 160 - y // 10))
    d.ellipse([100, 80, 220, 200], fill=(170, 50, 60))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


@pytest.mark.live
def test_live_single_image_pipeline(client):
    from app.config import get_settings

    settings = get_settings()
    if not (settings.gemini_api_key or settings.openai_api_key):
        pytest.skip("No API keys configured")
    r = client.post(
        "/api/analyze",
        json={"image": data_url(_png()), "mode": "recreate", "target_model": "midjourney"},
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["visual_dna"]["reference"]["reference_type"]
    assert data["prompt"], "expected a generated prompt"


@pytest.mark.live
def test_live_refine(client):
    from app.config import get_settings

    settings = get_settings()
    if not (settings.gemini_api_key or settings.openai_api_key):
        pytest.skip("No API keys configured")
    analyze = client.post(
        "/api/analyze",
        json={"image": data_url(_png()), "mode": "recreate", "target_model": "generic"},
    ).json()["data"]
    r = client.post(
        "/api/refine-prompt",
        json={
            "visual_dna": analyze["visual_dna"],
            "creative_intent": analyze["creative_intent"],
            "current_prompt": analyze["prompt"],
            "instruction": "Keep everything but change the lighting to sunset.",
            "mode": "recreate",
            "target_model": "generic",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert "lighting" in [c.lower() for c in data["change"]]
