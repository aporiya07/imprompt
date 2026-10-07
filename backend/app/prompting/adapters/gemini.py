from app.prompting.adapters.base import PromptTarget

GUIDANCE = """Target: Gemini image generation ("Nano Banana" and successors). These models reason
over prompts like a human art director and are image-EDITING models: when the reference image is
provided alongside the prompt, phrase instructions relative to it ("keep the lighting and wardrobe
from the reference, replace the background with ..."). For pure generation, write rich, unambiguous
natural-language sentences describing scene, layout, lighting and any exact on-image text. Do NOT
use community tags, weights like (word:1.2), or parameter flags such as --ar. Aspect ratio and size
are controlled outside the prompt, so do not mention them. Negative prompts are NOT supported: set
negative_prompt to null, and phrase any critical avoidance inline (e.g. "a clean background with no
visible text")."""

gemini_target = PromptTarget(
    id="gemini",
    name="Gemini (Nano Banana)",
    guidance=GUIDANCE,
    supports_negative=False,
    prompt_structure="conversational natural-language instruction",
    instruction_style="art-director briefing; handles relative instructions when a reference image is attached",
    reference_image_language=(
        "If the reference image is attached, direct edits at it explicitly: state what to keep from the "
        "reference and what to change. Do not re-describe from scratch what the model can see."
    ),
    editing_behavior="image editing + generation (reference image accepted)",
    negative_behavior="inline avoidances only",
    limitations="no separate negative prompt; aspect ratio set outside the prompt; do not use weights or flags",
)
