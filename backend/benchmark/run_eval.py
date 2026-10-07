"""Live evaluation harness (spec Phase 15/16) — costs API calls; run deliberately.

Runs every image in benchmark/images/ through the live API and writes
eval_report.json + eval_report.md with pipeline artifacts and an empty manual
checklist (accuracy/hallucination columns) for judgment-based scoring.
"""
import base64
import json
import sys
import time
from pathlib import Path

import httpx

API = "http://localhost:8000"
IMAGES_DIR = Path(__file__).parent / "images"
OUT_DIR = Path(__file__).parent

CHECKLIST = [
    "subject accuracy",
    "composition accuracy",
    "lighting accuracy",
    "color accuracy",
    "style accuracy",
    "spatial relationship accuracy",
    "uncertainty handled honestly",
    "prompt usefulness (1-5)",
    "hallucinations observed (describe or 'none')",
]


def data_url(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def main() -> int:
    images = sorted(p for p in IMAGES_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
    if not images:
        print(f"No images in {IMAGES_DIR} — run generate_fixtures.py and/or add real photos.")
        return 1

    results = []
    with httpx.Client(timeout=300.0) as client:
        for path in images:
            print(f"analyzing {path.name} …", flush=True)
            entry: dict = {"image": path.name, "status": "error"}
            started = time.perf_counter()
            try:
                resp = client.post(
                    f"{API}/api/analyze",
                    json={"image": data_url(path), "mode": "recreate", "target_model": "generic"},
                )
                body = resp.json()
                if resp.status_code == 200 and body.get("success"):
                    data = body["data"]
                    entry.update(
                        {
                            "status": "ok",
                            "latency_s": round(time.perf_counter() - started, 1),
                            "reference_type": data["reference_type"],
                            "layout": data.get("layout_description"),
                            "overall_description": data["visual_dna"]["reference"]["overall_description"],
                            "subjects": [s["description"] for s in data["visual_dna"]["subjects"]],
                            "essential_elements": [
                                e["description"]
                                for e in data["visual_dna"]["elements"]
                                if e["importance"] == "essential"
                            ],
                            "uncertainty": data["visual_dna"]["uncertainty"],
                            "prompt": data["prompt"],
                            "negative_prompt": data["negative_prompt"],
                            "prompt_quality": data["prompt_quality"],
                            "shots": [{"index": s["index"], "title": s["title"], "prompt": s["prompt"]} for s in data["shots"]],
                            "checklist": {item: "" for item in CHECKLIST},
                        }
                    )
                else:
                    entry["error"] = body.get("error", {})
            except Exception as e:  # noqa: BLE001
                entry["error"] = f"{type(e).__name__}: {e}"
            results.append(entry)

    (OUT_DIR / "eval_report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["# Pipeline Evaluation Report", ""]
    for entry in results:
        lines += [f"## {entry['image']} — {entry['status']}", ""]
        if entry["status"] != "ok":
            lines += [f"Error: `{entry.get('error')}`", ""]
            continue
        lines += [
            f"- latency: {entry['latency_s']}s · reference_type: {entry['reference_type']}"
            + (f" · layout: {entry['layout']}" if entry["layout"] else ""),
            f"- overall: {entry['overall_description']}",
            f"- subjects: {'; '.join(entry['subjects']) or '—'}",
            f"- essential: {'; '.join(entry['essential_elements']) or '—'}",
            f"- uncertainty: {'; '.join(entry['uncertainty']) or '—'}",
            f"- prompt_quality: {json.dumps(entry['prompt_quality'])}",
            "",
            "**Prompt:**", "", "```", entry["prompt"] or "", "```",
        ]
        if entry["shots"]:
            lines += ["", "**Shots:**"]
            for shot in entry["shots"]:
                lines += [f"- Shot {shot['index']} ({shot['title']}): {shot['prompt']}"]
        lines += ["", "| checklist item | your judgment |", "|---|---|"]
        for item in CHECKLIST:
            lines.append(f"| {item} | {entry['checklist'][item]} |")
        lines.append("")

    (OUT_DIR / "eval_report.md").write_text("\n".join(lines), encoding="utf-8")
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"\n{ok}/{len(results)} succeeded → eval_report.json / eval_report.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
