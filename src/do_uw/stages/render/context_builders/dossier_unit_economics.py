"""Unit economics context builder for the Intelligence Dossier.

Extracts unit economics metrics and narrative from DossierData
into template-ready dicts.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import na_if_none


def extract_unit_economics(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format unit economics metrics for template rendering.

    Reads from state.dossier for unit_economics and unit_economics_narrative.
    Returns dict with template-ready metric list, narrative, and availability flag.
    """
    dossier = state.dossier
    if not dossier or not dossier.unit_economics:
        return {"unit_economics_available": False}

    metrics: list[dict[str, Any]] = []
    for m in dossier.unit_economics:
        metrics.append({
            "metric": na_if_none(m.metric),
            "value": na_if_none(m.value),
            "benchmark": na_if_none(m.benchmark),
            "assessment": na_if_none(m.assessment),
            "do_risk": na_if_none(m.do_risk),
        })

    return {
        "unit_economics_available": True,
        "metrics": metrics,
        "narrative": na_if_none(dossier.unit_economics_narrative),
    }
