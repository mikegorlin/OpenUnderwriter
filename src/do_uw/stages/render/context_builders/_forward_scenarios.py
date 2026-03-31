"""Forward scenarios context builder.

Enhances existing scenario_generator output with probability badges,
severity estimates, and company-specific catalysts for template rendering.

Phase 136: Forward-Looking and Integration
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

from do_uw.stages.render.formatters_humanize import humanize_factor
from do_uw.stages.render.context_builders.scenario_generator import (
    generate_scenarios,
)
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Probability normalization
# ---------------------------------------------------------------------------

_PROB_NORMALIZE: dict[str, str] = {
    "VERY_HIGH": "HIGH",
    "HIGH": "HIGH",
    "CRITICAL": "HIGH",
    "ELEVATED": "MEDIUM",
    "MODERATE": "MEDIUM",
    "MEDIUM": "MEDIUM",
    "LOW": "LOW",
    "VERY_LOW": "LOW",
}

_PROB_COLOR: dict[str, str] = {
    "HIGH": "#DC2626",
    "MEDIUM": "#D97706",
    "LOW": "#16A34A",
}

# Severity as fraction of market cap by probability
_SEVERITY_FRACTION: dict[str, float] = {
    "HIGH": 0.02,   # 50th percentile settlement
    "MEDIUM": 0.01,  # 25th percentile settlement
    "LOW": 0.005,    # 10th percentile settlement
}


def _format_dollar(amount: float) -> str:
    """Format dollar amount as $X.XM or $X.XB."""
    if amount >= 1e9:
        return f"${amount / 1e9:.1f}B"
    if amount >= 1e6:
        return f"${amount / 1e6:.1f}M"
    if amount >= 1e3:
        return f"${amount / 1e3:.0f}K"
    return f"${amount:.0f}"


def _get_market_cap(state: AnalysisState) -> float:
    """Extract market cap from state, with fallbacks."""
    try:
        mc_sv = state.extracted.market.stock.market_cap
        if mc_sv is not None:
            val = getattr(mc_sv, "value", mc_sv)
            mc = safe_float(val, 0.0)
            if mc > 0:
                return mc
    except (AttributeError, TypeError):
        pass

    # Fallback: try acquired_data
    try:
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            mc = safe_float(md.get("marketCap", 0), 0.0)
            if mc > 0:
                return mc
    except (AttributeError, TypeError):
        pass

    return 5e9  # Default $5B if unavailable


def _build_catalyst(
    scenario: dict[str, Any],
    state: AnalysisState,
) -> str:
    """Build company-specific catalyst string from scoring data."""
    ticker = state.ticker or "the company"
    company_name = ""
    if state.company and state.company.identity:
        _id = state.company.identity
        company_name = (_id.legal_name.value if _id.legal_name else "") or ""
    if not company_name and state.acquired_data and isinstance(state.acquired_data.market_data, dict):
        info = state.acquired_data.market_data.get("info", {})
        company_name = info.get("shortName", "") or info.get("longName", "")

    display_name = company_name or ticker

    sid = scenario.get("id", "")
    score_delta = scenario.get("score_delta", 0)
    current_tier = scenario.get("current_tier", "")
    scenario_tier = scenario.get("scenario_tier", "")

    tier_change = ""
    if current_tier != scenario_tier:
        tier_change = f", shifting tier from {current_tier} to {scenario_tier}"

    factor_details = scenario.get("factor_deltas", [])
    affected_factors = ", ".join(
        humanize_factor(f.get("factor_id", "")) for f in factor_details if isinstance(f, dict)
    )

    # Build scenario-specific catalyst text
    if sid == "SCA_FILED":
        return (
            f"{display_name} currently has no active securities class action. "
            f"A new filing would impact score by {score_delta:+.1f} points"
            f"{tier_change}."
        )
    if sid == "SCA_ESCALATION":
        return (
            f"{display_name} has an active SCA that could escalate through "
            f"class certification, impacting score by {score_delta:+.1f} points"
            f"{tier_change}."
        )
    if sid == "EARNINGS_MISS_DROP":
        return (
            f"An earnings miss with significant stock decline for {display_name} "
            f"would impact score by {score_delta:+.1f} points"
            f"{tier_change}."
        )
    if sid == "RESTATEMENT":
        return (
            f"A financial restatement at {display_name} would severely impact "
            f"score by {score_delta:+.1f} points{tier_change}, "
            f"affecting factors {affected_factors}."
        )
    if sid == "INSIDER_DUMP":
        return (
            f"Accelerated insider selling at {display_name} would signal "
            f"reduced confidence, impacting score by {score_delta:+.1f} points"
            f"{tier_change}."
        )
    if sid == "REGULATORY_ACTION":
        return (
            f"An SEC investigation into {display_name} disclosures would "
            f"impact score by {score_delta:+.1f} points{tier_change}."
        )
    if sid == "GOVERNANCE_CRISIS":
        return (
            f"Abrupt leadership changes at {display_name} would destabilize "
            f"governance, impacting score by {score_delta:+.1f} points"
            f"{tier_change}."
        )
    if sid == "POSITIVE_RESOLUTION":
        return (
            f"Favorable resolution of {display_name}'s active litigation "
            f"would improve score by {score_delta:+.1f} points{tier_change}."
        )

    # Generic fallback (should not typically happen)
    return (
        f"This scenario would impact {display_name}'s score by "
        f"{score_delta:+.1f} points{tier_change}."
    )


def build_forward_scenarios(state: AnalysisState) -> dict[str, Any]:
    """Build enhanced forward scenarios with probability, severity, catalysts.

    Wraps existing generate_scenarios() and enhances each scenario with:
    - probability: Normalized to HIGH/MEDIUM/LOW
    - probability_color: Hex color for template badges
    - severity_estimate: Dollar string derived from market cap
    - catalyst: Company-specific catalyst description

    Returns:
        Dict with scenarios_available, scenarios list, scenario_count,
        current_tier, current_score.
    """
    base_scenarios = generate_scenarios(state)

    if not base_scenarios:
        return {
            "scenarios_available": False,
            "scenarios": [],
            "scenario_count": 0,
            "current_tier": "",
            "current_score": 0.0,
        }

    market_cap = _get_market_cap(state)

    enhanced: list[dict[str, Any]] = []
    for scenario in base_scenarios:
        raw_prob = scenario.get("probability_impact", "MEDIUM")
        prob = _PROB_NORMALIZE.get(raw_prob, "MEDIUM")
        prob_color = _PROB_COLOR.get(prob, "#D97706")

        severity_frac = _SEVERITY_FRACTION.get(prob, 0.01)
        severity_amount = market_cap * severity_frac
        severity_str = _format_dollar(severity_amount)

        catalyst = _build_catalyst(scenario, state)

        # Humanize factor names in factor_deltas
        factor_deltas = scenario.get("factor_deltas", [])
        for fd in factor_deltas:
            if isinstance(fd, dict):
                fid = fd.get("factor_id", "")
                fd["factor_name"] = humanize_factor(fid)

        enhanced.append({
            **scenario,
            "probability": prob,
            "probability_color": prob_color,
            "severity_estimate": severity_str,
            "catalyst": catalyst,
        })

    current_tier = enhanced[0].get("current_tier", "") if enhanced else ""
    current_score = enhanced[0].get("current_score", 0.0) if enhanced else 0.0

    return {
        "scenarios_available": True,
        "scenarios": enhanced,
        "scenario_count": len(enhanced),
        "current_tier": current_tier,
        "current_score": current_score,
    }


__all__ = ["build_forward_scenarios"]
