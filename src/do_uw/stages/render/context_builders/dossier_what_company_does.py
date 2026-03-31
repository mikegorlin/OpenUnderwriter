"""What-the-company-does context builder for the Intelligence Dossier.

Extracts business description and core D&O exposure narrative from
DossierData into template-ready dicts.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 118: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import na_if_none


def extract_what_company_does(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format business description and D&O exposure for template rendering.

    Reads from state.dossier for business description and core D&O exposure.
    Returns dict with template-ready strings and availability flag.
    """
    dossier = state.dossier
    if not dossier or (not dossier.business_description_plain and not dossier.core_do_exposure):
        return {"what_company_does_available": False}

    return {
        "what_company_does_available": True,
        "business_description": na_if_none(dossier.business_description_plain),
        "core_do_exposure": na_if_none(dossier.core_do_exposure),
    }
