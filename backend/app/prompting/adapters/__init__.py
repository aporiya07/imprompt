from app.prompting.adapters.base import PromptTarget
from app.prompting.adapters.flux import flux_target
from app.prompting.adapters.gemini import gemini_target
from app.prompting.adapters.generic import generic_target
from app.prompting.adapters.midjourney import midjourney_target
from app.prompting.adapters.openai import openai_image_target
from app.prompting.adapters.stable_diffusion import stable_diffusion_target
from app.utils.errors import BadRequestError

_TARGETS: dict[str, PromptTarget] = {
    t.id: t
    for t in (
        generic_target,
        gemini_target,
        openai_image_target,
        flux_target,
        midjourney_target,
        stable_diffusion_target,
    )
}


def get_target(target_id: str) -> PromptTarget:
    target = _TARGETS.get((target_id or "").strip().lower())
    if target is None:
        known = ", ".join(sorted(_TARGETS))
        raise BadRequestError(f"Unknown target model '{target_id}'. Available: {known}.")
    return target


def all_targets() -> list[PromptTarget]:
    return list(_TARGETS.values())
