"""Phase 119: Context builders for stock catalyst + performance summary.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float


def build_stock_catalyst_context(
    state: AnalysisState,
    *,
    drop_events: list[dict[str, str]] | None = None,
    patterns: list[dict[str, str]] | None = None,
    drop_narrative: str = "",
) -> dict[str, Any]:
    """Build enhanced stock drop context with catalyst + D&O columns.

    Args:
        state: Analysis state (for company context).
        drop_events: Pre-formatted drop event dicts from build_drop_events().
        patterns: Pattern detection results from detect_stock_patterns().
        drop_narrative: Pre-generated narrative string for drop assessment.

    Returns:
        Dict with enhanced_drop_events, stock_patterns, drop_narrative,
        and has_catalyst_data flag.
    """
    return {
        "enhanced_drop_events": drop_events or [],
        "stock_patterns": patterns or [],
        "drop_narrative": drop_narrative,
        "has_catalyst_data": any(d.get("do_assessment") for d in (drop_events or [])),
    }


def build_stock_performance_summary(
    state: AnalysisState,
    *,
    multi_horizon_returns: dict[str, float | None] | None = None,
    analyst_consensus: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build stock performance summary context for template.

    Args:
        state: Analysis state (for company context).
        multi_horizon_returns: Dict mapping horizon label to return %.
        analyst_consensus: Pre-built analyst consensus dict.

    Returns:
        Dict with horizons list, analyst dict, and has_performance_data flag.
    """
    result: dict[str, Any] = {
        "horizons": [],
        "analyst": {},
        "has_performance_data": False,
    }
    if multi_horizon_returns:
        result["horizons"] = [
            {"label": k, "return_pct": f"{v:+.2f}%" if v is not None else "N/A"}
            for k, v in multi_horizon_returns.items()
        ]
        result["has_performance_data"] = True
    if analyst_consensus:
        result["analyst"] = analyst_consensus
        result["has_performance_data"] = True
    return result
