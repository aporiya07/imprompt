"""Prompt target adapter: model-specific contract for the prompt stage.

Each adapter declares, in structured form (spec Phase 6):
- how prompts should be structured and phrased for this model
- whether/how the model handles attached reference images (editing vs text-only)
- negative-prompt behavior, parameter requirements, and hard limitations
plus the LLM-facing `guidance` text injected into templates, and optional
deterministic post-processing of the finished prompt.

Adding a new target model = one new module exporting a PromptTarget + a registry entry.
"""
from dataclasses import dataclass
from typing import Callable

from app.models.dna import VisualDNA


@dataclass
class PromptTarget:
    id: str
    name: str
    guidance: str
    supports_negative: bool = True
    soft_char_limit: int | None = None
    prompt_structure: str = "natural-language paragraph"
    instruction_style: str = "descriptive prose"
    reference_image_language: str = ""  # how to phrase instructions relative to an attached reference image
    editing_behavior: str = "text-to-image only"  # or "image editing + generation (reference image accepted)"
    negative_behavior: str = "separate negative prompt"  # or "inline avoidances" / "--no parameter"
    parameter_notes: str = ""
    limitations: str = ""
    post_process_fn: Callable[[str, VisualDNA], str] | None = None

    def post_process(self, prompt: str, dna: VisualDNA) -> str:
        cleaned = prompt.strip()
        if self.post_process_fn is not None:
            return self.post_process_fn(cleaned, dna)
        return cleaned
