"""Pattern firing panel context builder for worksheet rendering (Phase 109).

Extracts pattern engine and archetype results from AnalysisState into a
template-ready dict for the Jinja2 firing panel section.

Provides a 10-item list: 4 engines + 6 archetypes, each with status,
confidence, headline, and drill-down details. Also computes summary
stats (engines_fired, archetypes_fired, highest_floor).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

__all__ = [
    "build_pattern_context",
]

logger = logging.getLogger(__name__)

# HAETier ordering for determining highest floor
_TIER_ORDER: dict[str, int] = {
    "PREFERRED": 0,
    "STANDARD": 1,
    "ELEVATED": 2,
    "HIGH_RISK": 3,
    "PROHIBITED": 4,
}


def build_pattern_context(state: AnalysisState) -> dict[str, Any]:
    """Build pattern firing panel template context from AnalysisState.

    If pattern data is unavailable (scoring is None or pattern_engine_result
    is None), returns minimal dict with patterns_available=False.

    Args:
        state: AnalysisState with scoring.pattern_engine_result populated.

    Returns:
        Dict with all template data for the 10-card firing panel.
    """
    if state.scoring is None:
        return {"patterns_available": False}

    pattern_result = getattr(state.scoring, "pattern_engine_result", None)
    if pattern_result is None:
        return {"patterns_available": False}

    items: list[dict[str, Any]] = []

    # Build engine items (4)
    for result in pattern_result.engine_results:
        item: dict[str, Any] = {
            "name": result.engine_name,
            "type": "engine",
            "engine_id": result.engine_id,
            "status": "MATCH" if result.fired else "NOT_FIRED",
            "confidence_pct": round(result.confidence * 100),
            "headline": result.headline,
            "findings": result.findings,
            "has_detail": bool(result.findings),
        }
        items.append(item)

    # Build archetype items (6)
    for result in pattern_result.archetype_results:
        item = {
            "name": result.archetype_name,
            "type": "archetype",
            "archetype_id": result.archetype_id,
            "status": "MATCH" if result.fired else "NOT_FIRED",
            "match_badge": f"{result.signals_matched}/{result.signals_required}",
            "confidence_pct": round(result.confidence * 100),
            "recommendation_floor": result.recommendation_floor,
            "matched_signals": result.matched_signal_ids,
            "historical_cases": result.historical_cases,
            "has_detail": result.fired,
        }
        items.append(item)

    # Compute summary stats
    engines_fired = sum(
        1 for r in pattern_result.engine_results if r.fired
    )
    archetypes_fired = sum(
        1 for r in pattern_result.archetype_results if r.fired
    )

    # Find highest recommendation floor from fired archetypes
    highest_floor: str | None = None
    highest_floor_order = -1
    for r in pattern_result.archetype_results:
        if r.fired and r.recommendation_floor:
            order = _TIER_ORDER.get(r.recommendation_floor, -1)
            if order > highest_floor_order:
                highest_floor = r.recommendation_floor
                highest_floor_order = order

    any_pattern_fired = engines_fired > 0 or archetypes_fired > 0

    return {
        "patterns_available": True,
        "items": items,
        "engines_fired": engines_fired,
        "archetypes_fired": archetypes_fired,
        "highest_floor": highest_floor,
        "any_pattern_fired": any_pattern_fired,
        "placement": "after_scoring",
    }
