import re

from app.models.dna import VisualDNA
from app.prompting.adapters.base import PromptTarget

GUIDANCE = """Target: Midjourney. Write dense, SPECIFIC, comma-separated visual phrases (not poetic
mood fillers). Midjourney weights early words more strongly, so subject, wardrobe, composition and
spatial relationships come first, then lighting, palette, materials and depth. Do NOT sacrifice
concrete subject/environment/lighting detail for brevity or evocative adjectives. Do NOT mention
camera brands or lens models. Do NOT write long typography instructions; Midjourney renders text
poorly. End the prompt with Midjourney parameters: the aspect ratio parameter --ar W:H (derived
from the Visual DNA's technical.aspect_ratio) is REQUIRED. A separate negative prompt is NOT
supported: set negative_prompt to null; only if something is critical to exclude, append a
--no item1, item2 parameter to the prompt itself (at most 2 items). Prefer staying under ~1500
characters by compressing redundancy, not by deleting wardrobe, pose, lighting or palette."""

_AR = re.compile(r"(\d+(?:\.\d+)?)\s*[:x/]\s*(\d+(?:\.\d+)?)")


def _fmt(x: float) -> str:
    return str(int(x)) if float(x).is_integer() else str(round(x, 2))


def _post(prompt: str, dna: VisualDNA) -> str:
    p = prompt.strip()
    if "--ar" in p:
        return p
    match = _AR.match((dna.technical.aspect_ratio or "").strip())
    if not match:
        return p
    w, h = float(match.group(1)), float(match.group(2))
    if w <= 0 or h <= 0:
        return p
    return f"{p} --ar {_fmt(w)}:{_fmt(h)}"


midjourney_target = PromptTarget(
    id="midjourney",
    name="Midjourney",
    guidance=GUIDANCE,
    supports_negative=False,
    soft_char_limit=1500,
    prompt_structure="dense comma-separated visual phrases, most important first",
    instruction_style="specific concrete phrases; early words weighted more",
    reference_image_language=(
        "Midjourney accepts image prompts by URL at the start of the prompt; the web UI also supports "
        "omni-reference for style/character. Do not assume the model can see our reference image unless "
        "the user attached it that way."
    ),
    editing_behavior="text-to-image (image-prompt URLs supported)",
    negative_behavior="--no parameter (max ~2 items) inside the prompt",
    parameter_notes="--ar W:H is REQUIRED and appended from the DNA aspect ratio",
    limitations="renders text poorly; no separate negative field; camera brands/lens claims discouraged",
    post_process_fn=_post,
)
