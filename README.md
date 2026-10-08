# ImPrompt

**Image to Prompt AI**: visual reverse engineering.

Upload a reference image (file or any public image URL) → **visual reverse engineering** → a structured **Visual DNA** (subjects, composition, camera, lighting, color, materials, typography, spatial relationships, essential-vs-incidental elements, explicit uncertainty) → a **Creative Intent** strategy layer → a **generation-ready prompt** engineered for your target model, with a deterministic **quality score**, negative prompt where supported, surgical **refinement**, version history, and **moodboard/collage support**: a 3×3 Pinterest board becomes a master creative direction plus per-shot prompts.

This is not captioning. The system answers *"What makes this image look like this?"*, not *"What is in this image?"*

## Pipeline

```
Reference Image (upload / URL, SSRF-guarded fetch)
  → Image Preprocessing (magic-byte validation, size cap, ≤2048px JPEG)
  → Vision Analysis (Gemini, ONE call → Visual DNA + CreativeIntent + CollageAnalysis)
  → Validation / Normalization (typed Pydantic models, tolerant to omissions)
      [analysis cached by image hash; retries never re-pay the vision call]
  → Prompt Construction (OpenAI, mode template + intent)
  → Deterministic Prompt Validator (score / warnings / strengths)
  → Model Adapter (Gemini/Nano Banana · GPT Image · FLUX · Midjourney · Stable Diffusion · Generic)
  → Final Prompt (+ negative prompt where the model supports one)
```

Reference intents: **Recreate · Create Similar · Extract Style · Extract Composition · Extract Lighting · Extract Color · Extract Pose · Modify**. Collages/moodboards are detected as such and never treated as one photographic scene.

## Project structure

```
backend/
  app/
    main.py                  # FastAPI app; strict {success,data,error} envelopes; static UI serving
    config.py                # pydantic-settings (backend/.env)
    api/
      routes_analysis.py     # POST /api/analyze, /api/fetch-image
      routes_prompt.py       # generate/refine/validate-prompt, /api/models, /api/health
    providers/               # AIProvider ABC; gemini/openai wrappers; registry with retry+fallback
    analysis/visual_dna.py   # vision stage → typed artifacts (cached)
    prompting/
      optimizer.py           # mode templates, collage shot generation, refinement
      diagnostics.py         # deterministic prompt quality heuristics
      adapters/              # 6 targets with structured capability metadata
    models/                  # common | dna (v2) | intent | collage | quality | contracts
    services/                # cache (TTL), observability (per-stage logging)
    utils/                   # image validation, JSON repair, SSRF-guarded URL fetch, errors
    prompts/                 # EDITABLE templates
  tests/                     # hermetic tests + optional live tier (RUN_LIVE_TESTS=1)
frontend/                    # React + TS + Vite
```

## Setup

Requires Python 3.12+ (uv) and Node 18+.

```bash
cd backend && uv sync && cp .env.example .env   # fill in GEMINI_API_KEY / OPENAI_API_KEY
cd ../frontend && npm install
```

Model defaults (env-overridable; see `backend/.env.example` and `backend/app/config.py`):
vision `gemini-3.8-flash`, prompt `gpt-6-luna`, with fallbacks configured in the provider registry.

## Run

```bash
cd backend  && uv run uvicorn app.main:app --reload --port 8000   # also serves frontend/dist if built
cd frontend && npm run dev                                        # http://localhost:5173 (proxies /api)
```

Port 8000 busy? Use `--port 8010` and set `VITE_DEV_PROXY_TARGET=http://localhost:8010` in `frontend/.env` (see `frontend/.env.example`).

## API

All responses use strict envelopes: `{"success", "data", "error"}`; errors carry `request_id`.

| Endpoint | Body → data |
|---|---|
| `POST /api/analyze` | `{image, mode, target_model?, instruction?, generate_prompt?}` → DNA, intent, prompt, quality, shots, panels |
| `POST /api/generate-prompt` | `{visual_dna, creative_intent?, mode, target_model, instruction?}` → `{prompt, negative_prompt?, quality?}` |
| `POST /api/refine-prompt` | `{visual_dna, creative_intent?, current_prompt, instruction, mode, target_model}` → refined prompt |
| `POST /api/validate-prompt` | `{prompt, target_model, visual_dna?}` → `{quality}` (no AI calls) |
| `POST /api/fetch-image` | `{url}` → `{image, width, height}` (SSRF-guarded) |
| `GET /api/models` | target models incl. `supports_negative`, `soft_char_limit` |
| `GET /api/health` | provider config status |

## Verification

```bash
cd backend
uv run pytest tests                              # hermetic tests (mocked providers, no cost)
uv run ruff check app tests
RUN_LIVE_TESTS=1 uv run pytest tests/test_live.py  # optional live tier

cd ../frontend
npm run lint
npm run typecheck
npm test
npm run build
```

## Known limitations

- Prompt-quality heuristics are deterministic patterns, not semantic understanding.
- URL fetch has a known DNS-rebinding TOCTOU window; fine for localhost, revisit before exposing the API.
- Analysis cache single-flight is in-process only (multi-worker needs distributed locking).
- No database: history lives in `localStorage`; analysis cache is in-process TTL.
- No auth/rate limiting: localhost tool.

## Version

ImPrompt **v0.3.0** (see `backend/app/version.py` and `frontend/package.json`).
