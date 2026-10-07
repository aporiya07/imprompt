import re

from app.models.dna import VisualDNA
from app.prompting.adapters.base import PromptTarget

GUIDANCE = """Target: Stable Diffusion (SD 1.5 / SDXL / SD3 family). Write the prompt as a
comma-separated list of visual keyword tags ordered by importance: medium/style first, then
subject, then composition/camera, lighting, environment, materials, color, mood. Use natural
keyword phrasing ("young woman, studio portrait, soft rim light") rather than full sentences;
emphasis syntax like (term:1.2) may be used sparingly for the few most important elements.
Negative prompts are strongly supported and expected: return a focused comma-separated negative
list relevant to this image."""


def _post(prompt: str, dna: VisualDNA) -> str:
    p = re.sub(r"\s+", " ", prompt.strip())
    p = re.sub(r"\s*,\s*", ", ", p)
    return p.strip(" ,")


stable_diffusion_target = PromptTarget(
    id="stable_diffusion",
    name="Stable Diffusion",
    guidance=GUIDANCE,
    supports_negative=True,
    prompt_structure="comma-separated keyword tags ordered by importance",
    instruction_style="keyword phrasing with optional (term:1.2) emphasis",
    editing_behavior="text-to-image (ControlNet/IP-Adapter workflows exist but are not assumed)",
    negative_behavior="separate negative prompt (strongly supported and expected)",
    limitations="tag-style prompts; no prose reasoning; emphasis syntax sparingly",
    post_process_fn=_post,
)
