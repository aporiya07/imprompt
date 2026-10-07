"""Back-compat shim. The contracts now live in focused modules:

- app.models.common   — enums (PromptMode, confidence, reference types)
- app.models.dna      — Visual DNA v2 + normalization
- app.models.intent   — CreativeIntent
- app.models.collage  — collage / moodboard models
- app.models.quality  — PromptQuality
- app.models.contracts — API requests/responses + envelope

Import from those modules directly; this file only re-exports for older callers.
"""
from app.models.collage import (  # noqa: F401
    CollageAnalysis,
    GlobalCreativeDNA,
    PanelRecord,
    ShotRecord,
    collage_from_payload,
)
from app.models.common import PromptMode  # noqa: F401
from app.models.contracts import (  # noqa: F401
    AnalyzeData as AnalyzeResponse,
    AnalyzeRequest,
    FetchedImage,
    FetchImageRequest,
    GeneratePromptRequest,
    PromptData as PromptResponse,
    PromptErrorInfo,
    RefineData as RefineResponse,
    RefinePromptRequest,
    ShotResult,
)
from app.models.dna import (  # noqa: F401
    VisualDNA,
    dna_from_payload,
    normalize_dna_payload,
)
from app.models.intent import CreativeIntent, derive_intent_from_dna  # noqa: F401
