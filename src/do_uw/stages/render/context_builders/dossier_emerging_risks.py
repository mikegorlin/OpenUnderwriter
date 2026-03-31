"""Emerging risks context builder for the Intelligence Dossier.

Extracts emerging risk entries from DossierData into template-ready
dicts with CSS probability classes.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import na_if_none

_PROBABILITY_CSS: dict[str, str] = {
    "HIGH": "risk-high",
    "MEDIUM": "risk-medium",
    "LOW": "risk-low",
}


def extract_emerging_risks(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format emerging risk entries for template rendering.

    Reads from state.dossier.emerging_risks for risk entries.
    Returns dict with template-ready risk list and availability flag.
    """
    dossier = state.dossier
    if not dossier or not dossier.emerging_risks:
        return {"emerging_risks_available": False}

    risks: list[dict[str, Any]] = []
    for risk in dossier.emerging_risks:
        risks.append({
            "risk": na_if_none(risk.risk),
            "probability": na_if_none(risk.probability),
            "impact": na_if_none(risk.impact),
            "timeframe": na_if_none(risk.timeframe),
            "do_factor": na_if_none(risk.do_factor),
            "status": na_if_none(risk.status),
            "probability_class": _PROBABILITY_CSS.get(risk.probability, ""),
        })

    return {
        "emerging_risks_available": True,
        "risks": risks,
    }
