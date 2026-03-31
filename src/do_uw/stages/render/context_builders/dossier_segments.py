"""Revenue segments and concentration context builder for the Intelligence Dossier.

Extracts segment dossiers and concentration dimensions from DossierData
into template-ready dicts with CSS risk classes.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import na_if_none

_RISK_CSS: dict[str, str] = {
    "HIGH": "risk-high",
    "MEDIUM": "risk-medium",
    "LOW": "risk-low",
}


def extract_revenue_segments(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format segment dossiers and concentration for template rendering.

    Reads from state.dossier for segment_dossiers and concentration_dimensions.
    Returns dict with template-ready lists and availability flags.
    """
    dossier = state.dossier
    if not dossier:
        return {"segments_available": False, "concentration_available": False}

    # Segments
    segments: list[dict[str, Any]] = []
    for seg in dossier.segment_dossiers:
        segments.append({
            "segment_name": na_if_none(seg.segment_name),
            "revenue_pct": na_if_none(seg.revenue_pct),
            "growth_rate": na_if_none(seg.growth_rate),
            "rev_rec_method": na_if_none(seg.rev_rec_method),
            "do_exposure": na_if_none(seg.do_exposure),
            "row_class": _RISK_CSS.get(seg.risk_level, ""),
        })

    # Concentration dimensions
    concentrations: list[dict[str, Any]] = []
    for dim in dossier.concentration_dimensions:
        concentrations.append({
            "dimension": na_if_none(dim.dimension),
            "metric": na_if_none(dim.metric),
            "risk_level": na_if_none(dim.risk_level),
            "do_implication": na_if_none(dim.do_implication),
            "row_class": _RISK_CSS.get(dim.risk_level, ""),
        })

    return {
        "segments_available": len(segments) > 0,
        "segments": segments,
        "concentration_available": len(concentrations) > 0,
        "concentration_dimensions": concentrations,
    }
