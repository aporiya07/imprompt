from app.prompting.adapters.base import PromptTarget

GUIDANCE = """Target: FLUX (FLUX.1 family). FLUX understands fluent, naturally flowing descriptive
prose far better than keyword lists; long, specific prompts work well. Avoid quality-boosting
spam words entirely; describe materials, light and atmosphere concretely. Do not use parameter
flags or weights. A short comma-separated negative prompt is supported by many FLUX UIs —
keep it under ~15 terms."""

flux_target = PromptTarget(
    id="flux",
    name="FLUX",
    guidance=GUIDANCE,
    supports_negative=True,
    prompt_structure="flowing descriptive prose (long prompts work well)",
    instruction_style="concrete, atmosphere-rich prose; no keyword spam",
    editing_behavior="text-to-image only (editing variants exist but are not assumed)",
    negative_behavior="separate negative prompt (short, many UIs only)",
    limitations="no parameter flags; avoid quality-spam words entirely",
)
