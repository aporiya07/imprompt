from app.prompting.adapters.base import PromptTarget

GUIDANCE = """Target: OpenAI GPT Image (gpt-image-1 family). These models follow literal, detailed
natural-language instructions extremely well, including layout, typography and spatial relationships,
and they are image-EDITING models: when the reference image is provided, phrase instructions relative
to it ("preserve the subject's pose and wardrobe; change the lighting to ..."). For pure generation,
write complete descriptive sentences; you may specify the aspect ratio in words (e.g. "a wide 16:9
composition"). No parameter flags and no weights. Negative prompts are NOT supported as a separate
field: set negative_prompt to null and phrase avoidances inline ("no text", "plain seamless
background")."""

openai_image_target = PromptTarget(
    id="openai",
    name="GPT Image (OpenAI)",
    guidance=GUIDANCE,
    supports_negative=False,
    prompt_structure="detailed literal prose",
    instruction_style="explicit and literal; excellent at layout/typography instructions",
    reference_image_language=(
        "If the reference image is attached, anchor edits to it: name what stays, describe precisely "
        "what changes and where."
    ),
    editing_behavior="image editing + generation (reference image accepted)",
    negative_behavior="inline avoidances only",
    limitations="no separate negative prompt; avoid parameter flags and weights",
)
