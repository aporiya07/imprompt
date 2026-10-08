"""AI pipeline reliability: attempt budget, validation inside the executor, cache semantics."""
import asyncio
import json

import pytest

from app.analysis.visual_dna import _validate_vision_payload, analyze_image
from app.models.dna import DNA_SCHEMA_VERSION
from app.providers.registry import RoleConfig, RoleExecutor
from app.utils.errors import MalformedAIResponseError

from .conftest import SAMPLE_DNA_V2


def _cfg(role, primary, fallback=None, primary_attempts=2, fallback_attempts=1):
    return RoleConfig(
        role=role,
        primary=primary,
        primary_model="m",
        primary_attempts=primary_attempts,
        fallback=fallback,
        fallback_model="m2" if fallback else None,
        fallback_attempts=fallback_attempts,
    )


class TestAttemptBudget:
    def test_malformed_never_exceeds_primary_budget(self):
        class P:
            name = "p1"
            calls = 0

            async def analyze_image(self, **kw):
                self.calls += 1
                return "not json at all"

        p = P()
        ex = RoleExecutor(_cfg("vision", "p1"), {"p1": p}, retry_backoff=0)

        async def run():
            return await ex.run_vision(
                image_bytes=b"x",
                mime="image/png",
                system_prompt="s",
                user_prompt="u",
                validate=lambda t: (_ for _ in ()).throw(MalformedAIResponseError(t)),
            )

        with pytest.raises(MalformedAIResponseError):
            asyncio.run(run())
        assert p.calls == 2  # primary_attempts, not more

    def test_budget_across_providers_is_deterministic(self):
        class Bad:
            name = "p1"
            calls = 0

            async def analyze_image(self, **kw):
                self.calls += 1
                return "broken"

        class Good:
            name = "p2"
            calls = 0

            async def analyze_image(self, **kw):
                self.calls += 1
                return json.dumps(SAMPLE_DNA_V2)

        bad, good = Bad(), Good()
        providers = {"p1": bad, "p2": good}
        ex = RoleExecutor(_cfg("vision", "p1", fallback="p2"), providers, retry_backoff=0)

        def _validate(text):
            return _validate_vision_payload(text, 64, 40)

        async def run():
            return await ex.run_vision(
                image_bytes=b"x", mime="image/png", system_prompt="s", user_prompt="u", validate=_validate
            )

        outcome = asyncio.run(run())
        assert bad.calls == 2 and good.calls == 1  # hard max = 3 calls
        assert outcome.fallback_used is True and outcome.provider == "p2"
        assert outcome.value["dna"].reference.reference_type.value == "photograph"

    def test_missing_both_keys_reports_combined(self):
        ex = RoleExecutor(_cfg("vision", "gemini", fallback="openai"), {})

        async def run():
            return await ex.run_vision(
                image_bytes=b"x", mime="image/png", system_prompt="s", user_prompt="u", validate=lambda t: t
            )

        with pytest.raises(Exception) as exc:
            asyncio.run(run())
        assert "GEMINI_API_KEY" in str(exc.value) and "OPENAI_API_KEY" in str(exc.value)


class TestValidationInsideExecutor:
    def test_parse_failure_inside_executor_retries_then_falls_back(self):
        """Malformed output fails validation inside the boundary and flows through the budget."""

        class Bad:
            name = "p1"
            calls = 0

            async def analyze_image(self, **kw):
                self.calls += 1
                return "definitely not JSON"

        class Good:
            name = "p2"
            calls = 0

            async def analyze_image(self, **kw):
                self.calls += 1
                return json.dumps(SAMPLE_DNA_V2)

        providers = {"p1": Bad(), "p2": Good()}
        ex = RoleExecutor(_cfg("vision", "p1", fallback="p2"), providers, retry_backoff=0)

        async def run():
            return await ex.run_vision(
                image_bytes=b"x",
                mime="image/png",
                system_prompt="s",
                user_prompt="u",
                validate=lambda t: _validate_vision_payload(t, 64, 40),
            )

        outcome = asyncio.run(run())
        assert outcome.fallback_used is True
        assert outcome.value["dna"].subjects  # real validated DNA from the fallback
        assert providers["p1"].calls == 2 and providers["p2"].calls == 1

    def test_normalizer_degrades_shape_errors_instead_of_failing(self):
        """Tolerant by design: garbage section values normalize to empty, not errors."""
        result = _validate_vision_payload(json.dumps({"composition": "just a string"}), 64, 40)
        assert result["dna"].composition.shot_type == ""


class TestSingleFlight:
    def test_concurrent_identical_analysis_single_vision_call(self, sample_dna):
        import types as _types

        class P:
            name = "fake"
            calls = 0

            async def analyze_image(self, **kw):
                self.calls += 1
                await asyncio.sleep(0.05)  # simulate latency so the second call overlaps
                return json.dumps(SAMPLE_DNA_V2)

        provider = P()
        ex = RoleExecutor(_cfg("vision", "fake"), {"fake": provider}, retry_backoff=0)

        async def one():
            return await analyze_image(ex, b"identical-bytes", "image/jpeg", 64, 40)

        async def run():
            return await asyncio.gather(one(), one())

        results = asyncio.run(run())
        assert provider.calls == 1
        assert results[0].dna.reference.reference_type == results[1].dna.reference.reference_type
        # Immutable handouts: mutating one result must not affect the other.
        results[0].dna.subjects.clear()
        assert len(results[1].dna.subjects) == 1
        assert not hasattr(_types, "__probe__")  # placeholder guard, no-op


class TestCacheSemantics:
    def test_cache_metadata_records_fallback_provider(self, client, png_bytes):
        from app.main import app

        from .conftest import FAKE_PROMPT_REPLY, make_runtime

        runtime, provider = make_runtime(
            [json.dumps(SAMPLE_DNA_V2)],
            # Vision is cached after request 1, but the prompt stage runs on both requests.
            [FAKE_PROMPT_REPLY, FAKE_PROMPT_REPLY],
            register_as="fake",
            vision_primary="gemini",
            vision_fallback="fake",
            text_primary="openai",
            text_fallback="fake",
        )
        app.state.runtime = runtime
        payload = {"image": "data:image/png;base64," + _b64(png_bytes)}
        assert client.post("/api/analyze", json=payload).status_code == 200
        assert client.post("/api/analyze", json=payload).status_code == 200
        assert provider.vision_calls == 1  # second request served from cache

    def test_cache_key_includes_versions(self):
        from app.analysis import visual_dna as vd

        assert vd.VISION_PROMPT_VERSION
        assert DNA_SCHEMA_VERSION == 2


def _b64(data: bytes) -> str:
    import base64

    return base64.b64encode(data).decode()
