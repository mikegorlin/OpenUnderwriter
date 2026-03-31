"""CRF alert bar context builder (Phase 114-01).

Extracts Critical Risk Factor vetoes and red flags with section links
for the persistent alert bar at the top of the worksheet.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Map CRF/red flag types to worksheet section anchors
_SECTION_LINK_MAP: dict[str, str] = {
    "CRF-RESTATEMENT": "#financial-health",
    "CRF-SEC-ENFORCEMENT": "#litigation",
    "CRF-MATERIAL-WEAKNESS": "#financial-health",
    "CRF-MULTI": "#scoring",
    "CRF-CLASS-ACTION": "#litigation",
    "CRF-BANKRUPTCY": "#financial-health",
}

_DEFAULT_SECTION_LINK = "#scoring"


def build_crf_bar_context(state: AnalysisState) -> dict[str, Any]:
    """Build CRF alert bar data from AnalysisState.

    Extracts CRF vetoes (CRITICAL severity) from hae_result and
    red flags (HIGH severity) from scoring. Maps each to a section anchor.

    Returns dict with alerts list.
    """
    alerts: list[dict[str, Any]] = []

    if state.scoring is None:
        return {"alerts": alerts}

    sc = state.scoring

    # CRF vetoes from H/A/E result — only ACTIVE vetoes
    hae_result = getattr(sc, "hae_result", None)
    if hae_result is not None:
        crf_vetoes = getattr(hae_result, "crf_vetoes", []) or []
        for veto in crf_vetoes:
            # Skip inactive CRF checks
            if not getattr(veto, "is_active", False):
                continue
            crf_id = getattr(veto, "crf_id", "") or ""
            # Suppress insolvency CRF when company is clearly solvent
            if "INSOLVENCY" in crf_id.upper() or "BANKRUPTCY" in crf_id.upper():
                from do_uw.stages.score.red_flag_gates import should_suppress_insolvency
                if should_suppress_insolvency(state):
                    continue
            condition = getattr(veto, "condition", "") or ""
            alerts.append({
                "id": crf_id,
                "name": crf_id.replace("CRF-", "").replace("-", " ").title(),
                "severity": "CRITICAL",
                "section_link": _SECTION_LINK_MAP.get(crf_id, _DEFAULT_SECTION_LINK),
                "source": "CRF Veto",
                "evidence": condition,
            })

    # Red flags from scoring
    for rf in sc.red_flags:
        if not rf.triggered:
            continue
        flag_id = rf.flag_id
        alerts.append({
            "id": flag_id,
            "name": rf.flag_name or flag_id,
            "severity": "HIGH",
            "section_link": _SECTION_LINK_MAP.get(flag_id, _DEFAULT_SECTION_LINK),
            "source": "Red Flag",
            "evidence": "; ".join(rf.evidence) if rf.evidence else "",
        })

    return {"alerts": alerts}


__all__ = ["build_crf_bar_context"]
