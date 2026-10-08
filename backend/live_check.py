"""Live end-to-end check against the real AI providers (v0.3 pipeline).

Runs three checks:
  1. single image: analyze → Visual DNA v2 + CreativeIntent + prompt (Midjourney format)
  2. collage:      analyze of the generated 3x3 fixture → moodboard detection + shot list
  3. refine:       "Keep everything but change the lighting to sunset." on the single-image result

Run: uv run --project backend python backend/live_check.py
"""
import base64
import io
import json
import sys
from pathlib import Path

import httpx
from PIL import Image, ImageDraw

API = "http://localhost:8000"
COLLAGE_FIXTURE = Path(__file__).parent / "benchmark" / "images" / "10_pinterest_collage.jpg"


def data_url(path: Path) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode()


def make_test_image() -> str:
    img = Image.new("RGB", (640, 480))
    d = ImageDraw.Draw(img)
    for y in range(480):
        d.line([(0, y), (640, y)], fill=(235 - y // 6, 210 - y // 8, 190 - y // 10))
    d.ellipse([430, 60, 540, 170], fill=(248, 140, 60))
    d.rectangle([0, 390, 640, 480], fill=(58, 92, 70))
    d.ellipse([140, 230, 330, 410], fill=(176, 44, 52))
    d.ellipse([170, 255, 220, 300], fill=(230, 120, 120))
    d.rectangle([20, 20, 240, 72], fill=(28, 28, 32))
    from PIL import ImageFont

    try:
        font = ImageFont.load_default(size=30)
    except TypeError:
        font = ImageFont.load_default()
    d.text((34, 30), "SALE 50%", fill=(255, 255, 255), font=font)

    buf = io.BytesIO()
    img.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def show(title: str, text, limit: int = 360) -> None:
    print(f"\n=== {title} ===")
    if text:
        s = str(text)
        print(s[:limit] + ("…" if len(s) > limit else ""))


def main() -> int:
    failures = 0
    with httpx.Client(timeout=300.0) as client:
        # 1. single image
        r = client.post(
            f"{API}/api/analyze",
            json={"image": make_test_image(), "mode": "recreate", "target_model": "midjourney"},
        )
        body = r.json()
        print(f"analyze status: {r.status_code} success={body.get('success')}")
        if r.status_code != 200 or not body.get("success"):
            print(json.dumps(body.get("error"), indent=2)[:800])
            return 1
        data = body["data"]
        dna = data["visual_dna"]
        show("reference", f"{dna['reference']['reference_type']} · confidence {dna['reference']['analysis_confidence']}")
        show("subjects", json.dumps(dna["subjects"], ensure_ascii=False)[:400])
        show("typography", json.dumps(dna["typography"], ensure_ascii=False))
        show("essential elements", json.dumps(dna["elements"], ensure_ascii=False)[:400])
        show("uncertainty", json.dumps(dna["uncertainty"], ensure_ascii=False))
        show("creative intent", data["creative_intent"]["primary_goal"])
        show("prompt quality", json.dumps(data["prompt_quality"], ensure_ascii=False))
        show("Midjourney prompt", data["prompt"])
        if not data["prompt"] or not data["visual_dna"]["subjects"]:
            failures += 1

        # 2. collage / moodboard
        if COLLAGE_FIXTURE.exists():
            rc = client.post(
                f"{API}/api/analyze",
                json={"image": data_url(COLLAGE_FIXTURE), "mode": "recreate", "target_model": "generic"},
            )
            cbody = rc.json()
            print(f"\ncollage analyze status: {rc.status_code} success={cbody.get('success')}")
            if rc.status_code == 200 and cbody.get("success"):
                cdata = cbody["data"]
                show("detected", f"{cdata['reference_type']} · {cdata.get('layout_description')}")
                show("panels", ", ".join(f"{s['index']}:{s['title']}" for s in cdata["shots"]) or "(no shots)")
                show("master direction", cdata["prompt"], 500)
                show("shot 01 prompt", cdata["shots"][0]["prompt"] if cdata["shots"] else None)
                if cdata["reference_type"] not in ("moodboard", "collage", "screenshot") or not cdata["shots"]:
                    failures += 1
            else:
                print(json.dumps(cbody.get("error"), indent=2)[:600])
                failures += 1

        # 3. refine
        rr = client.post(
            f"{API}/api/refine-prompt",
            json={
                "visual_dna": dna,
                "creative_intent": data["creative_intent"],
                "current_prompt": data["prompt"],
                "instruction": "Keep everything but change the lighting to sunset.",
                "mode": "recreate",
                "target_model": "midjourney",
            },
        )
        rbody = rr.json()
        print(f"\nrefine status: {rr.status_code} success={rbody.get('success')}")
        if rr.status_code == 200 and rbody.get("success"):
            rdata = rbody["data"]
            show("keep", rdata["keep"])
            show("change", rdata["change"])
            show("refined prompt", rdata["prompt"])
            show("quality", json.dumps(rdata["quality"], ensure_ascii=False))
        else:
            print(json.dumps(rbody.get("error"), indent=2)[:600])
            failures += 1

    print(f"\n{'ALL LIVE CHECKS PASSED' if failures == 0 else f'{failures} LIVE CHECK(S) FAILED'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
