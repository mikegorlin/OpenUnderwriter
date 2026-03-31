"""ASC 606 revenue recognition context builder for the Intelligence Dossier.

Extracts ASC 606 elements and billings-vs-revenue narrative from
DossierData into template-ready dicts with CSS complexity classes.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import na_if_none

_COMPLEXITY_CSS: dict[str, str] = {
    "HIGH": "risk-high",
    "MEDIUM": "risk-medium",
    "LOW": "risk-low",
}


def extract_asc_606(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format ASC 606 elements and billings narrative for template rendering.

    Reads from state.dossier for asc_606_elements and billings_vs_revenue_narrative.
    Returns dict with template-ready element list, narrative, and availability flag.
    """
    dossier = state.dossier
    if not dossier or not dossier.asc_606_elements:
        return {"asc_606_available": False}

    elements: list[dict[str, Any]] = []
    for elem in dossier.asc_606_elements:
        elements.append({
            "element": na_if_none(elem.element),
            "approach": na_if_none(elem.approach),
            "complexity": na_if_none(elem.complexity),
            "do_risk": na_if_none(elem.do_risk),
            "complexity_class": _COMPLEXITY_CSS.get(elem.complexity, ""),
        })

    return {
        "asc_606_available": True,
        "elements": elements,
        "billings_narrative": na_if_none(dossier.billings_vs_revenue_narrative),
    }
