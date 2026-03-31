"""Severity context builder for worksheet rendering (Phase 108).

Extracts severity computation results from AnalysisState into a
template-ready dict for the Jinja2 worksheet severity section.

Provides two data layers:
  - Main section: damages breakdown, fired amplifiers, P x S chart,
    scenario table, expected loss, layer erosion metrics
  - Appendix: full amplifier table (all 11, fired/not-fired/not-evaluated)

Also provides legacy comparison data for side-by-side display.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

__all__ = [
    "build_severity_context",
]

logger = logging.getLogger(__name__)


def _format_dollars(amount: float) -> str:
    """Format dollar amount as human-readable $XM or $XB string."""
    if amount >= 1e9:
        return f"${amount / 1e9:.1f}B"
    if amount >= 1e6:
        return f"${amount / 1e6:.1f}M"
    if amount >= 1e3:
        return f"${amount / 1e3:.0f}K"
    return f"${amount:,.0f}"


def build_severity_context(state: AnalysisState) -> dict[str, Any]:
    """Build severity template context from AnalysisState.

    If severity data is unavailable (scoring is None or severity_result
    is None), returns minimal dict with severity_available=False.

    Args:
        state: AnalysisState with scoring.severity_result populated.

    Returns:
        Dict with all template data for severity section + appendix.
    """
    if state.scoring is None:
        return {"severity_available": False}

    severity_result = getattr(state.scoring, "severity_result", None)
    if severity_result is None:
        return {"severity_available": False}

    primary = severity_result.primary
    if primary is None:
        return {"severity_available": False}

    # -- Damages breakdown --
    metadata = primary.metadata or {}
    damages_breakdown = {
        "market_cap": metadata.get("market_cap", 0),
        "class_period_return": metadata.get("class_period_return", 0),
        "turnover_rate": metadata.get("turnover_rate", 0),
        "base_damages": primary.damages_estimate,
        "allegation_modifier": metadata.get("primary_allegation_type", "unknown"),
        "modified_damages": primary.estimated_settlement,
        "regression_estimate": metadata.get("regression_estimate", 0),
        "combined_multiplier": metadata.get("combined_amplifier_multiplier", 1.0),
    }

    # -- Amplifiers (fired only for main section) --
    amplifiers_fired = [
        {
            "name": a.name,
            "multiplier": a.multiplier,
            "explanation": a.explanation,
            "trigger_signals": a.trigger_signals_matched,
        }
        for a in primary.amplifier_results
        if a.fired
    ]

    # -- Amplifiers (all for appendix) --
    amplifiers_full = [
        {
            "amplifier_id": a.amplifier_id,
            "name": a.name,
            "fired": a.fired,
            "multiplier": a.multiplier,
            "explanation": a.explanation,
            "trigger_signals": a.trigger_signals_matched,
            "status": "fired" if a.fired else "not_fired",
        }
        for a in primary.amplifier_results
    ]

    # -- P x S chart (base64 PNG) --
    pxs_chart_b64 = ""
    try:
        from do_uw.stages.render.charts.pxs_matrix_chart import (
            render_pxs_matrix_html,
        )
        pxs_chart_b64 = render_pxs_matrix_html(severity_result)
    except Exception:
        logger.warning("Failed to render P x S chart", exc_info=True)

    # -- Scenario table --
    scenario_table = [
        {
            "allegation_type": s.allegation_type,
            "drop_level": s.drop_level,
            "base_damages": s.base_damages,
            "settlement_estimate": s.settlement_estimate,
            "amplified_settlement": s.amplified_settlement,
            "defense_costs": s.defense_cost_estimate,
            "total_exposure": s.total_exposure,
        }
        for s in severity_result.scenario_table
    ]

    # -- Layer erosion --
    layer_erosion: dict[str, Any] | None = None
    if primary.layer_erosion and len(primary.layer_erosion) > 0:
        e = primary.layer_erosion[0]
        layer_erosion = {
            "attachment": e.attachment,
            "limit": e.limit,
            "product": e.product,
            "penetration_probability": e.penetration_probability,
            "liberty_severity": e.liberty_severity,
            "effective_el": e.effective_expected_loss,
        }

    # -- Legacy comparison --
    legacy_comparison: dict[str, Any] | None = None
    legacy = severity_result.legacy
    if legacy is not None and legacy.estimated_settlement > 0:
        delta = primary.estimated_settlement - legacy.estimated_settlement
        legacy_comparison = {
            "legacy_lens_name": legacy.lens_name,
            "legacy_estimate": legacy.estimated_settlement,
            "legacy_estimate_fmt": _format_dollars(legacy.estimated_settlement),
            "delta": delta,
            "delta_fmt": _format_dollars(abs(delta)),
            "delta_direction": "higher" if delta > 0 else "lower",
        }

    # -- Zone color mapping --
    zone_colors = {
        "GREEN": "#2b8a3e",
        "YELLOW": "#e67700",
        "ORANGE": "#c92a2a",
        "RED": "#862e9c",
    }

    return {
        "severity_available": True,
        "damages_breakdown": damages_breakdown,
        "amplifiers_fired": amplifiers_fired,
        "amplifiers_full": amplifiers_full,
        "pxs_chart_b64": pxs_chart_b64,
        "scenario_table": scenario_table,
        "expected_loss": _format_dollars(severity_result.expected_loss),
        "expected_loss_raw": severity_result.expected_loss,
        "probability": severity_result.probability,
        "severity": severity_result.severity,
        "severity_fmt": _format_dollars(severity_result.severity),
        "zone": {
            "name": severity_result.zone.value,
            "color": zone_colors.get(severity_result.zone.value, "#333"),
        },
        "defense_costs_total": _format_dollars(primary.defense_costs),
        "defense_costs_raw": primary.defense_costs,
        "layer_erosion": layer_erosion,
        "legacy_comparison": legacy_comparison,
        "primary_allegation_type": metadata.get("primary_allegation_type", "unknown"),
    }
