# Pipeline Benchmark (spec Phase 15)

Evaluates the pipeline over representative reference images. Accuracy and
hallucination checks are judgment-based: the harness produces a structured
report; you (or an LLM judge) mark the checklist columns.

## Structure

- `generate_fixtures.py` — deterministic synthetic fixtures for the structural
  cases (collage grid, moodboard, text banner, low-light, product layout,
  landscape gradient). Real-photo cases (portrait, couple, fashion editorial…)
  cannot be synthesized honestly — drop your own images into `images/` using
  the names listed below.
- `run_eval.py` — runs every image in `images/` through the live API and writes
  `eval_report.json` + `eval_report.md` with the DNA, prompts, quality scores
  and an empty manual-checklist per case.

## Image names (drop into `images/`, PNG/JPG/WEBP, ≤10 MB)

```
01_portrait.jpg        06_food.jpg           11_moodboard_3x3.jpg
02_couple.jpg          07_landscape.jpg      12_image_with_text.jpg
03_fashion_editorial.jpg 08_interior.jpg     13_low_light.jpg
04_product_ad.jpg      09_cinematic.jpg      14_complex_composition.jpg
05_architecture.jpg    10_pinterest_collage.jpg  15_multiple_people.jpg
```

## Run

```bash
uv run --project backend python backend/benchmark/generate_fixtures.py   # structural fixtures
uv run --project backend uvicorn app.main:app --port 8000                # backend up (keys in .env)
uv run --project backend python backend/benchmark/run_eval.py            # live eval (costs API calls)
```

## Evaluated dimensions per case

subject / composition / lighting / color / style / spatial-relationship accuracy,
uncertainty handling, prompt usefulness, hallucination rate — recorded as the
manual checklist in the report. The deterministic `prompt_quality` score from the
pipeline is included automatically.
