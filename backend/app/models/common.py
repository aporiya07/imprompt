"""Shared enums and small types for the pipeline contracts."""
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class ElementImportance(str, Enum):
    ESSENTIAL = "essential"
    SUPPORTING = "supporting"
    INCIDENTAL = "incidental"
    UNCERTAIN = "uncertain"


class ReferenceType(str, Enum):
    SINGLE_IMAGE = "single_image"
    COLLAGE = "collage"
    MOODBOARD = "moodboard"
    SCREENSHOT = "screenshot"
    PHOTOGRAPH = "photograph"
    ILLUSTRATION = "illustration"
    ADVERTISEMENT = "advertisement"
    PRODUCT_IMAGE = "product_image"
    UNKNOWN = "unknown"


STRUCTURAL_REFERENCE_TYPES = {
    ReferenceType.COLLAGE,
    ReferenceType.MOODBOARD,
    ReferenceType.SCREENSHOT,
}


class PromptMode(str, Enum):
    """Reference intent — how the reference should be used (Phase 7)."""

    RECREATE = "recreate"
    CREATE_SIMILAR = "create_similar"
    EXTRACT_STYLE = "extract_style"
    EXTRACT_COMPOSITION = "extract_composition"
    EXTRACT_LIGHTING = "extract_lighting"
    EXTRACT_COLOR = "extract_color"
    EXTRACT_POSE = "extract_pose"
    MODIFY = "modify"


MODE_DESCRIPTIONS: dict[PromptMode, str] = {
    PromptMode.RECREATE: "Preserve the visual structure and important characteristics of the reference.",
    PromptMode.CREATE_SIMILAR: "Use the visual language but create a new composition.",
    PromptMode.EXTRACT_STYLE: "Do not reproduce the exact scene; extract the aesthetic language.",
    PromptMode.EXTRACT_COMPOSITION: "Extract the compositional logic; leave subject and scene open.",
    PromptMode.EXTRACT_LIGHTING: "Extract the lighting scheme; leave subject and scene open.",
    PromptMode.EXTRACT_COLOR: "Extract the palette and grading; leave subject and scene open.",
    PromptMode.EXTRACT_POSE: "Extract pose and body language; leave identity and scene open.",
    PromptMode.MODIFY: "Preserve the reference unless explicitly instructed to change something.",
}
