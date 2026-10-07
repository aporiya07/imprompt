from app.prompting.adapters.base import PromptTarget

GUIDANCE = """The prompt is written for a generic modern text-to-image model. Use one cohesive
natural-language paragraph, concrete visual language, no parameter flags, no keyword spam.
A short comma-separated negative prompt is supported."""

generic_target = PromptTarget(
    id="generic",
    name="Generic",
    guidance=GUIDANCE,
    supports_negative=True,
    prompt_structure="natural-language paragraph",
    instruction_style="descriptive prose",
    editing_behavior="text-to-image only",
    negative_behavior="separate negative prompt",
    limitations="no model-specific features assumed",
)
