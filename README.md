# VISURA

**Image → Prompt AI** — visual reverse engineering.

Upload a reference image (file or any public image URL) → **visual reverse engineering** → a structured **Visual DNA** (subjects, composition, camera, lighting, color, materials, typography, spatial relationships, essential-vs-incidental elements, explicit uncertainty) → a **Creative Intent** strategy layer → a **generation-ready prompt** engineered for your target model, with a deterministic **quality score**, negative prompt where supported, surgical **refinement**, version history — and **moodboard/collage support**: a 3×3 Pinterest board becomes a master creative direction plus per-shot prompts.

This is not captioning. The system answers *"What makes this image look like this?"* — not *"What is in this image?"*

## Pipeline

```
Reference Image (upload / URL, SSRF-guarded fetch)
  → Image Preprocessing (magic-byte validation, size cap, ≤2048px JPEG)
  → Vision Analysis (Gemini, ONE call → Visual DNA + CreativeIntent + CollageAnalysis)
  → Validation / Normalization (typed Pydantic models, tolerant to omissions)
      [analysis cached by image hash — retries never re-pay the vision call]
  → Prompt Construction (OpenAI, mode template + intent)
  → Deterministic Prompt Validator (score / warnings / strengths)
  → Model Adapter (Gemini/Nano Banana · GPT Image · FLUX · Midjourney · Stable Diffusion · Generic)
  → Final Prompt (+ negative prompt where the model supports one)
```

Reference intents: **Recreate · Create Similar · Extract Style · Extract Composition · Extract Lighting · Extract Color · Extract Pose · Modify** — the intent changes what the prompt preserves. Collages/moodboards are detected as such and never treated as one photographic scene: per-panel analysis → recurring-language synthesis → master direction + shot list.

## Project structure

```
backend/
  app/
    main.py                  # FastAPI app; strict {success,data,error} envelopes; static UI serving
    config.py                # pydantic-settings (backend/.env)
    api/
      routes_analysis.py     # POST /api/analyze, /api/fetch-image
      routes_prompt.py       # /api/generate-prompt, /api/refine-prompt, /api/models, /api/health
    providers/               # AIProvider ABC; gemini/openai wrappers; registry with retry+fallback
    analysis/visual_dna.py   # vision stage → typed artifacts (cached)
    prompting/
      optimizer.py           # mode templates, collage shot generation, refinement
      diagnostics.py         # deterministic prompt quality heuristics
      adapters/              # 6 targets with structured capability metadata
    models/                  # common | dna (v2) | intent | collage | quality | contracts | schemas(shim)
    services/                # cache (TTL), observability (per-stage logging)
    utils/                   # image validation, JSON repair, SSRF-guarded URL fetch, errors
    prompts/                 # EDITABLE templates: visual_analysis, recreate, create_similar,
                             #   style_extraction, extraction, modification, collage
  benchmark/                 # fixture generator + live eval harness (see benchmark/README.md)
  tests/                     # 96 hermetic tests + optional live tier (RUN_LIVE_TESTS=1)
  live_check.py              # one-command live verification of the whole pipeline
frontend/                    # React + TS + Vite; DNA viewer, creative direction, quality card,
                             #   shot list, editable prompt, version history, URL ingest, dark/light
```

## Setup

Requires Python 3.12+ (uv) and Node 18+.

```bash
cd backend && uv sync && cp .env.example .env   # fill in GEMINI_API_KEY / OPENAI_API_KEY
cd ../frontend && npm install
```

Models (all env-overridable, checked 2026-10-07): vision `gemini-3.8-flash` ($0.75/$3.75 per 1M until 2026-12-31), prompt `gpt-6-luna` ($0.10/$0.50); fallbacks `gemini-3.1-flash-lite` / `gpt-6-luna`. See `.env.example`.

## Run

```bash
cd backend  && uv run uvicorn app.main:app --reload --port 8000   # also serves frontend/dist if built
cd frontend && npm run dev                                        # http://localhost:5173 (proxies /api)
```

Port 8000 busy? Use `--port 8010` and update `frontend/vite.config.ts`.

## API (all responses are strict envelopes: `{"success", "data", "error"}`; errors carry `request_id`)

| Endpoint | Body → data |
|---|---|
| `POST /api/analyze` | `{image, mode, target_model?, instruction?, generate_prompt?}` → `{reference_type, layout_description?, visual_dna, creative_intent, prompt?, negative_prompt?, prompt_quality?, shots[]?, prompt_error?}` |
| `POST /api/generate-prompt` | `{visual_dna, creative_intent?, mode, target_model, instruction?}` → `{prompt, negative_prompt?, quality?}` |
| `POST /api/refine-prompt` | `{visual_dna, creative_intent?, current_prompt, instruction, mode, target_model}` → `{keep[], change[], prompt, negative_prompt?, quality?}` |
| `POST /api/fetch-image` | `{url}` → `{image, width, height}` (SSRF-guarded) |
| `GET /api/models` | target models incl. `supports_negative`, `soft_char_limit` |
| `GET /api/health` | provider config status |

Error codes: `invalid_image`, `unsupported_format`, `image_too_large`, `missing_api_key`, `rate_limited`, `provider_timeout`, `provider_unavailable`, `provider_error`, `malformed_ai_response`, `bad_request`, `validation_error`.

## Verification

```bash
cd backend
uv run pytest tests                              # 96 hermetic tests (mocked providers, no cost)
RUN_LIVE_TESTS=1 uv run pytest tests/test_live.py  # optional live tier (real keys)
uv run python live_check.py                      # full live walkthrough: single + collage + refine
uv run python benchmark/generate_fixtures.py     # synthetic structural fixtures
uv run python benchmark/run_eval.py              # live benchmark report (costs API calls)
```

## Known limitations

- Prompt-quality heuristics are deterministic patterns, not semantic understanding — warnings are advisory.
- Per-panel analysis happens in the single vision call: very dense boards (12+ tiny panels) may lose panel detail; the DNA/uncertainty fields surface this.
- URL fetch has a known DNS-rebinding TOCTOU window — fine for localhost, revisit before exposing the API.
- No database: history lives in `localStorage` (12 items); analysis cache is in-process TTL.
- No auth/rate limiting — localhost tool.

## Next steps

1. Chrome extension (right-click analyze → the API is extension-ready).
2. Postgres persistence behind the same API.
3. Node-based workflow canvas — researched and archived in [docs/IDEAS.md](docs/IDEAS.md).
4. Original build spec: [docs/PIPELINE_UPGRADE_SPEC.md](docs/PIPELINE_UPGRADE_SPEC.md).
