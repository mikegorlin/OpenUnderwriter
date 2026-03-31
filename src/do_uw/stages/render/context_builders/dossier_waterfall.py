"""Revenue waterfall context builder for the Intelligence Dossier.

Extracts YoY revenue waterfall rows and narrative from DossierData
into template-ready dicts.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import na_if_none


def extract_revenue_waterfall(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format revenue waterfall rows for template rendering.

    Reads from state.dossier for waterfall_rows and waterfall_narrative.
    Returns dict with template-ready row list, narrative, and availability flag.
    """
    dossier = state.dossier
    if not dossier or not dossier.waterfall_rows:
        return {"waterfall_available": False}

    rows: list[dict[str, Any]] = []
    for row in dossier.waterfall_rows:
        rows.append({
            "label": na_if_none(row.label),
            "value": na_if_none(row.value),
            "delta": na_if_none(row.delta),
            "narrative": na_if_none(row.narrative),
        })

    return {
        "waterfall_available": True,
        "rows": rows,
        "narrative": na_if_none(dossier.waterfall_narrative),
    }
