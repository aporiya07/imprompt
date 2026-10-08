import base64
import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.config import get_settings
from app.main import app
from app.providers.registry import RoleConfig, RoleExecutor, Runtime

SAMPLE_DNA_V2 = {
    "reference": {
        "reference_type": "photograph",
        "reference_type_confidence": "high",
        "overall_description": "An outdoor lifestyle portrait at golden hour.",
        "analysis_confidence": 0.9,
    },
    "subjects": [
        {
            "label": "subject_1",
            "type": "person",
            "description": "a young woman with curly red hair",
            "clothing": "mustard knit sweater",
            "pose": "seated, relaxed",
            "position_in_frame": "left third",
            "confidence": "high",
        }
    ],
    "environment": {
        "location_type": "cafe terrace",
        "setting": "outdoor",
        "background": "blurred street with warm bokeh",
        "objects": ["porcelain cup"],
        "confidence": "high",
    },
    "composition": {
        "shot_type": "portrait",
        "framing": "waist-up",
        "balance": "asymmetric, subject on the left third",
        "confidence": "high",
    },
    "camera": {
        "focal_length_category": "short-telephoto appearance",
        "depth_of_field": "shallow",
        "confidence": "medium",
    },
    "lighting": {
        "lighting_type": "natural window-like light",
        "quality": "soft",
        "time_based_look": "golden hour",
        "confidence": "high",
    },
    "color": {
        "dominant": [{"name": "mustard yellow", "hex": "#D4A017"}, {"name": "warm brown"}],
        "accent": ["muted teal"],
        "warm_cool_balance": "warm",
        "confidence": "high",
    },
    "style": {"photography_style": "editorial portrait", "confidence": "medium"},
    "mood": {"description": "relaxed and warm", "emotional_tone": ["calm", "intimate"], "confidence": "medium"},
    "materials": [{"object": "sweater", "material": "wool knit", "texture": "chunky"}],
    "typography": {"present": False},
    "relationships": [
        {"subject": "subject_1", "relation": "beside", "object": "porcelain cup", "description": "cup on the table in front of her"}
    ],
    "elements": [
        {"description": "golden-hour backlight", "importance": "essential", "reason": "defines the mood"},
        {"description": "small rock near the table leg", "importance": "incidental"},
    ],
    "interpretation": {
        "creative_reading": "romantic lifestyle editorial portrait emphasizing warmth",
        "confidence": "medium",
    },
    "uncertainty": ["exact lens category could be normal instead of short-telephoto"],
    "technical": {"aspect_ratio": "3:2", "orientation": "landscape"},
}

SAMPLE_INTENT = {
    "primary_goal": "Recreate the visual language of a warm lifestyle editorial portrait",
    "preserve": ["golden-hour backlight", "mustard knit wardrobe"],
    "flexible": ["background details"],
}

FAKE_VISION_REPLY = json.dumps({"visual_dna": SAMPLE_DNA_V2, "creative_intent": SAMPLE_INTENT})

FAKE_PROMPT_REPLY = json.dumps(
    {
        "prompt": "A young woman with curly red hair in a mustard knit sweater, seated at an outdoor cafe terrace, golden-hour backlight, shallow depth of field",
        "negative_prompt": "distorted hands, extra fingers",
    }
)

REFINE_REPLY = json.dumps(
    {
        "keep": ["composition", "subject", "environment"],
        "change": ["lighting"],
        "prompt": "Revised prompt P2 with sunset lighting",
        "negative_prompt": None,
    }
)

SAMPLE_COLLAGE_VISION_REPLY = json.dumps(
    {
        "visual_dna": {
            "reference": {
                "reference_type": "moodboard",
                "reference_type_confidence": "high",
                "layout_description": "3x3 grid of nine photos",
                "overall_description": "A nine-panel moodboard of a romantic beach editorial shoot.",
                "analysis_confidence": 0.85,
            },
            "subjects": [{"label": "subject_1", "type": "couple", "description": "a couple on a beach"}],
            "technical": {"aspect_ratio": "1:1"},
        },
        "creative_intent": {
            "primary_goal": "Recreate the visual language of a romantic golden-hour beach editorial",
            "preserve": ["golden-hour backlight", "beach environment"],
            "flexible": ["specific poses"],
        },
        "collage_analysis": {
            "layout_description": "3x3 grid of nine photos",
            "panels": [
                {
                    "index": 1,
                    "title": "close-up portrait",
                    "summary": "close-up of the woman with wind-blown hair",
                    "bounds": {"x": 0.0, "y": 0.0, "w": 0.33, "h": 0.33},
                    "shot": {"shot_type": "close-up", "lighting": "golden hour backlight", "palette": "warm cream"},
                },
                {
                    "index": 2,
                    "title": "couple walking",
                    "summary": "the couple walking along the shoreline",
                    "bounds": {"x": 0.33, "y": 0.0, "w": 0.33, "h": 0.33},
                    "shot": {"shot_type": "full-body", "pose": "walking hand in hand"},
                },
            ],
            "global_dna": {
                "overall_aesthetic": "romantic golden-hour beach editorial",
                "color_palette": ["warm cream", "burnt orange", "soft gold"],
                "lighting": "golden-hour backlight across panels",
                "recurring_motifs": ["beach", "flowing dress", "bare feet"],
                "composition_patterns": ["subject off-center with open negative space"],
                "summary": "A warm, intimate beach editorial in golden-hour light.",
            },
        },
    }
)

COLLAGE_PROMPT_REPLY = json.dumps(
    {
        "master_direction": "A romantic golden-hour beach editorial: warm cream and burnt-orange palette, consistent golden-hour backlight, intimate posing.",
        "shots": [
            {
                "index": 1,
                "title": "close-up portrait",
                "prompt": "Close-up portrait of a woman with wind-blown hair at golden hour, warm cream palette, beach bokeh behind",
                "negative_prompt": None,
            },
            {
                "index": 2,
                "title": "couple walking",
                "prompt": "Full-body shot of a couple walking hand in hand along the shoreline at golden hour",
                "negative_prompt": "distorted hands",
            },
        ],
    }
)


class FakeProvider:
    name = "fake"

    def __init__(self, vision_replies=(), text_replies=()):
        self.vision_replies = list(vision_replies)
        self.text_replies = list(text_replies)
        self.vision_calls = 0
        self.text_calls = 0

    async def analyze_image(self, **kwargs):
        self.vision_calls += 1
        reply = self.vision_replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    async def generate_text(self, **kwargs):
        self.text_calls += 1
        reply = self.text_replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def make_runtime(
    vision_replies,
    text_replies,
    *,
    register_as="fake",
    vision_primary="fake",
    text_primary="fake",
    vision_fallback=None,
    text_fallback=None,
    backoff=0.0,
):
    provider = FakeProvider(vision_replies, text_replies)
    providers = {register_as: provider}
    vision_cfg = RoleConfig(
        role="vision", primary=vision_primary, primary_model="v-model",
        fallback=vision_fallback, fallback_model=None,
    )
    text_cfg = RoleConfig(
        role="prompt", primary=text_primary, primary_model="t-model",
        fallback=text_fallback, fallback_model=None,
    )
    runtime = Runtime(
        providers=providers,
        vision=RoleExecutor(vision_cfg, providers, retry_backoff=backoff),
        prompt=RoleExecutor(text_cfg, providers, retry_backoff=backoff),
    )
    return runtime, provider


def data_url(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode()


def unwrap(response) -> dict:
    """Assert the strict envelope (Phase 12) and return the data payload."""
    body = response.json()
    assert body["success"] is True, body
    assert body["error"] is None, body
    assert body["data"] is not None, body
    return body["data"]


@pytest.fixture()
def sample_dna():
    return json.loads(json.dumps(SAMPLE_DNA_V2))


@pytest.fixture()
def png_bytes():
    buf = io.BytesIO()
    Image.new("RGB", (64, 40), (120, 30, 200)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture(autouse=True)
def _clean_settings(monkeypatch):
    import os

    from app.services.cache import analysis_cache

    if os.environ.get("RUN_LIVE_TESTS") == "1":
        # Live tier: let the developer's backend/.env provide real keys.
        get_settings.cache_clear()
        yield
        get_settings.cache_clear()
        return
    # Force-empty the keys so tests are hermetic even when the developer's
    # backend/.env contains real keys (env vars outrank the dotenv file).
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.delenv("MAX_IMAGE_MB", raising=False)
    get_settings.cache_clear()
    analysis_cache.clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
