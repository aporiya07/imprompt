"""Collage / moodboard contracts (spec Phases 8–9).

A collage is never treated as one photographic scene. The vision call detects the
structure, describes each panel, and synthesizes a GLOBAL creative direction from
recurring characteristics — plus per-panel shot records for shot-specific prompts.
"""
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.common import ConfidenceLevel
from app.utils.json_utils import as_str, as_str_list

_FLEX = ConfigDict(extra="allow")


class PanelBounds(BaseModel):
    model_config = _FLEX
    x: float = 0.0  # normalized 0..1
    y: float = 0.0
    w: float = 0.0
    h: float = 0.0


class ShotRecord(BaseModel):
    """Shot-specific DNA for one panel — what a single generated photo should look like."""

    model_config = _FLEX
    shot_type: str = ""
    pose: str = ""
    composition: str = ""
    lighting: str = ""
    palette: str = ""
    style: str = ""
    wardrobe: str = ""
    environment: str = ""
    notes: str = ""


class PanelRecord(BaseModel):
    model_config = _FLEX
    index: int = 0
    title: str = ""
    summary: str = ""
    bounds: PanelBounds | None = None
    shot: ShotRecord = Field(default_factory=ShotRecord)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM


class GlobalCreativeDNA(BaseModel):
    """Cross-panel synthesis: the moodboard's shared visual language."""

    model_config = _FLEX
    overall_aesthetic: str = ""
    color_palette: list[str] = Field(default_factory=list)
    palette_description: str = ""
    lighting: str = ""
    mood: str = ""
    photography_style: str = ""
    wardrobe_direction: str = ""
    environment: str = ""
    recurring_motifs: list[str] = Field(default_factory=list)
    composition_patterns: list[str] = Field(default_factory=list)
    summary: str = ""


class CollageAnalysis(BaseModel):
    model_config = _FLEX
    layout_description: str = ""
    panels: list[PanelRecord] = Field(default_factory=list)
    global_dna: GlobalCreativeDNA = Field(default_factory=GlobalCreativeDNA)


def _shot(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {k: as_str(v) for k, v in value.items()}


def normalize_collage_payload(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise ValueError("Collage payload must be a JSON object.")
    out: dict[str, Any] = {"layout_description": as_str(raw.get("layout_description"))}

    panels_raw = raw.get("panels")
    if not isinstance(panels_raw, list):
        panels_raw = []
    panels: list[dict[str, Any]] = []
    for i, item in enumerate(panels_raw, start=1):
        if isinstance(item, str):
            panels.append({"index": i, "title": item[:80], "summary": item})
            continue
        if not isinstance(item, dict):
            continue
        bounds = item.get("bounds")
        panel: dict[str, Any] = {
            "index": int(item.get("index") or i),
            "title": as_str(item.get("title")),
            "summary": as_str(item.get("summary")),
            "shot": _shot(item.get("shot")),
            "confidence": (
                as_str(item.get("confidence")).lower()
                if as_str(item.get("confidence")).lower() in {c.value for c in ConfidenceLevel}
                else ConfidenceLevel.MEDIUM.value
            ),
        }
        if isinstance(bounds, dict):
            try:
                panel["bounds"] = {
                    "x": max(0.0, min(1.0, float(bounds.get("x", 0)))),
                    "y": max(0.0, min(1.0, float(bounds.get("y", 0)))),
                    "w": max(0.0, min(1.0, float(bounds.get("w", 0)))),
                    "h": max(0.0, min(1.0, float(bounds.get("h", 0)))),
                }
            except (TypeError, ValueError):
                pass
        panels.append(panel)
    out["panels"] = panels

    g = raw.get("global_dna") if isinstance(raw.get("global_dna"), dict) else {}
    out["global_dna"] = {
        "overall_aesthetic": as_str(g.get("overall_aesthetic")),
        "color_palette": as_str_list(g.get("color_palette")),
        "palette_description": as_str(g.get("palette_description")),
        "lighting": as_str(g.get("lighting")),
        "mood": as_str(g.get("mood")),
        "photography_style": as_str(g.get("photography_style")),
        "wardrobe_direction": as_str(g.get("wardrobe_direction")),
        "environment": as_str(g.get("environment")),
        "recurring_motifs": as_str_list(g.get("recurring_motifs"), split_commas=False),
        "composition_patterns": as_str_list(g.get("composition_patterns"), split_commas=False),
        "summary": as_str(g.get("summary")),
    }
    return out


def collage_from_payload(payload: Any) -> CollageAnalysis:
    return CollageAnalysis.model_validate(normalize_collage_payload(payload))
