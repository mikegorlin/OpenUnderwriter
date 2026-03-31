"""Revenue model card context builder for the Intelligence Dossier.

Extracts revenue model card rows from DossierData into template-ready
dicts with CSS risk classes.

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


def extract_revenue_model_card(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format revenue model card rows for template rendering.

    Reads from state.dossier.revenue_card for attribute/value/risk rows.
    Returns dict with template-ready row list and availability flag.
    """
    dossier = state.dossier
    if not dossier or not dossier.revenue_card:
        return {"revenue_card_available": False}

    rows: list[dict[str, Any]] = []
    for row in dossier.revenue_card:
        rows.append({
            "attribute": na_if_none(row.attribute),
            "value": na_if_none(row.value),
            "do_risk": na_if_none(row.do_risk),
            "row_class": _RISK_CSS.get(row.risk_level, ""),
        })

    return {
        "revenue_card_available": True,
        "rows": rows,
    }
