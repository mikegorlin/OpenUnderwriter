"""Decision record context builder (Phase 114-01).

Provides tier distribution reference data and underwriting posture
fields for the decision record page of the worksheet.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Industry-standard D&O tier distribution percentages
# Source: D&O market studies, underwriting practice reference data
_TIER_DISTRIBUTION: dict[str, float] = {
    "PREFERRED": 15.0,
    "STANDARD": 40.0,
    "ELEVATED": 25.0,
    "HIGH_RISK": 15.0,
    "PROHIBITED": 5.0,
}


def build_decision_context(state: AnalysisState) -> dict[str, Any]:
    """Build decision record context from AnalysisState.

    Returns dict with decision_available, tier_distribution,
    current_tier, posture_fields, and source metadata.
    """
    if state.scoring is None:
        return {"decision_available": False}

    sc = state.scoring
    current_tier = sc.tier.tier if sc.tier else "N/A"

    return {
        "decision_available": True,
        "tier_distribution": dict(_TIER_DISTRIBUTION),
        "current_tier": current_tier,
        "posture_fields": {},
        "source": "Industry Reference",
    }


__all__ = ["build_decision_context"]
