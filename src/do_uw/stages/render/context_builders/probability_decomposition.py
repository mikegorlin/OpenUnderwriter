"""Probability decomposition context builder.

Transforms the multiplicative EnhancedFrequency model (base * hazard * signal)
into 7+ additive display components, each with calibration labels and source
citations. This is display-only logic -- no new scores are computed.

Each component shows its marginal impact on the running probability total,
converting multiplicative effects into additive percentage adjustments.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.scoring import _rename_f4
from do_uw.stages.render.formatters import safe_float


def _get_f4_display_name(factor_scores: list[Any]) -> str:
    """Get dynamic display name for F4 factor based on what actually triggered."""
    for fs in factor_scores:
        fid = getattr(fs, "factor_id", "")
        if fid in ("F4", "F.4"):
            fname = getattr(fs, "factor_name", "") or ""
            if "IPO" in fname:
                return _rename_f4(fs) + " Uplift"
            return fname + " Uplift" if fname else "Transaction Risk Uplift"
    return "Transaction Risk Uplift"


def _get_factor_deduction(
    factor_scores: list[Any],
    factor_id: str,
) -> tuple[float, float]:
    """Return (points_deducted, max_points) for a factor, safely.

    Returns (0.0, 1.0) if factor not found (avoid division by zero).
    """
    for fs in factor_scores:
        fid = getattr(fs, "factor_id", "")
        if fid == factor_id:
            pts = safe_float(getattr(fs, "points_deducted", 0.0))
            mx = safe_float(getattr(fs, "max_points", 1.0))
            return pts, max(mx, 1.0)
    return 0.0, 1.0


def _market_cap_adjustment(market_cap: float | None) -> tuple[float, str]:
    """Compute market cap tier probability adjustment.

    Based on SCAC data: smaller companies have higher filing rates.
    Returns (adjustment_pct, tier_label).
    """
    if market_cap is None or market_cap <= 0:
        return 0.0, "Unknown"

    cap_b = market_cap / 1e9
    if cap_b < 0.3:
        return 3.0, "Micro (<$300M)"
    if cap_b < 2.0:
        return 1.5, "Small ($300M-$2B)"
    if cap_b < 10.0:
        return 0.5, "Mid ($2B-$10B)"
    return -0.5, "Large (>$10B)"


def build_probability_decomposition(
    state: AnalysisState,
) -> list[dict[str, Any]]:
    """Decompose filing probability into 7+ named additive components.

    Reads the multiplicative EnhancedFrequency model from state and
    converts each multiplicative factor into an additive percentage
    adjustment, producing a waterfall of probability components.

    Args:
        state: Full analysis state with scoring.enhanced_frequency populated.

    Returns:
        List of component dicts, each with:
        - name: str
        - value_pct: float (additive adjustment)
        - direction: "base" | "increase" | "decrease"
        - is_calibrated: bool
        - source: str (citation for calibrated items)
        - running_total_pct: float (cumulative after this component)
    """
    scoring = getattr(state, "scoring", None)
    if scoring is None:
        return []

    ef = getattr(scoring, "enhanced_frequency", None)
    if ef is None:
        return []

    base_rate = safe_float(getattr(ef, "base_rate_pct", 0.0))
    hazard_mult = safe_float(getattr(ef, "hazard_multiplier", 1.0))
    signal_mult = safe_float(getattr(ef, "signal_multiplier", 1.0))
    adjusted_prob = safe_float(getattr(ef, "adjusted_probability_pct", 0.0))
    factor_scores = getattr(scoring, "factor_scores", []) or []

    components: list[dict[str, Any]] = []
    running_total = 0.0

    # ---- Component 1: Sector Base Rate ----
    running_total = base_rate
    components.append({
        "name": "Sector Base Rate",
        "value_pct": round(base_rate, 3),
        "direction": "base",
        "is_calibrated": True,
        "source": "NERA 2024 Recent Trends in Securities Class Action Litigation / Cornerstone Research",
        "running_total_pct": round(running_total, 3),
    })

    # ---- Component 2: Market Cap Tier ----
    market_cap = None
    try:
        market_cap = safe_float(
            getattr(
                getattr(
                    getattr(state, "company", None),
                    "market_data",
                    None,
                ),
                "market_cap",
                None,
            )
        )
        if market_cap == 0.0:
            market_cap = None
    except (TypeError, AttributeError):
        market_cap = None

    cap_adj, cap_label = _market_cap_adjustment(market_cap)
    if cap_adj != 0.0:
        running_total += cap_adj
        running_total = max(running_total, 0.1)  # Floor at 0.1%
    components.append({
        "name": f"Market Cap Tier ({cap_label})",
        "value_pct": round(cap_adj, 3),
        "direction": "increase" if cap_adj > 0 else ("decrease" if cap_adj < 0 else "base"),
        "is_calibrated": True,
        "source": "SCAC 2023 Annual Report (market cap filing rates by tier)",
        "running_total_pct": round(running_total, 3),
    })

    # ---- Component 3: IPO Uplift (from F4 factor score) ----
    f4_pts, f4_max = _get_factor_deduction(factor_scores, "F4")
    ipo_ratio = f4_pts / f4_max
    ipo_adj = running_total * ipo_ratio * 0.5 if ipo_ratio > 0 else 0.0
    running_total += ipo_adj
    f4_display = _get_f4_display_name(factor_scores)
    components.append({
        "name": f4_display,
        "value_pct": round(ipo_adj, 3),
        "direction": "increase" if ipo_adj > 0 else "base",
        "is_calibrated": False,
        "source": "Estimated from F4 factor score",
        "running_total_pct": round(running_total, 3),
    })

    # ---- Component 4: Volatility Adjustment (from F7 factor score) ----
    f7_pts, f7_max = _get_factor_deduction(factor_scores, "F7")
    vol_ratio = f7_pts / f7_max
    vol_adj = running_total * vol_ratio * 0.3 if vol_ratio > 0 else 0.0
    running_total += vol_adj
    components.append({
        "name": "Volatility Adjustment",
        "value_pct": round(vol_adj, 3),
        "direction": "increase" if vol_adj > 0 else "base",
        "is_calibrated": False,
        "source": "Estimated from F7 factor score",
        "running_total_pct": round(running_total, 3),
    })

    # ---- Component 5: Insider Selling Signal (from F6) ----
    f6_pts, f6_max = _get_factor_deduction(factor_scores, "F6")
    insider_ratio = f6_pts / f6_max
    insider_adj = running_total * insider_ratio * 0.2 if insider_ratio > 0 else 0.0
    running_total += insider_adj
    components.append({
        "name": "Insider Selling Signal",
        "value_pct": round(insider_adj, 3),
        "direction": "increase" if insider_adj > 0 else "base",
        "is_calibrated": False,
        "source": "Estimated from F6 factor score",
        "running_total_pct": round(running_total, 3),
    })

    # ---- Component 6: Litigation History (from F1) ----
    f1_pts, f1_max = _get_factor_deduction(factor_scores, "F1")
    lit_ratio = f1_pts / f1_max
    # Active SCA (F1 >= 15 points) is a major uplift
    if f1_pts >= 15:
        lit_adj = running_total * 0.8  # Near-doubles probability
    elif f1_pts >= 10:
        lit_adj = running_total * 0.4
    else:
        lit_adj = running_total * lit_ratio * 0.3
    running_total += lit_adj
    components.append({
        "name": "Litigation History",
        "value_pct": round(lit_adj, 3),
        "direction": "increase" if lit_adj > 0 else "base",
        "is_calibrated": True,
        "source": "Stanford SCA Database (filing rates by prior litigation history)",
        "running_total_pct": round(running_total, 3),
    })

    # ---- Component 7: Governance Quality (from F9 + F10) ----
    f9_pts, f9_max = _get_factor_deduction(factor_scores, "F9")
    f10_pts, f10_max = _get_factor_deduction(factor_scores, "F10")
    gov_ratio = (f9_pts + f10_pts) / (f9_max + f10_max)
    gov_adj = running_total * gov_ratio * 0.25 if gov_ratio > 0 else 0.0
    running_total += gov_adj
    components.append({
        "name": "Governance Quality",
        "value_pct": round(gov_adj, 3),
        "direction": "increase" if gov_adj > 0 else "base",
        "is_calibrated": False,
        "source": "Estimated from F9 + F10 factor scores",
        "running_total_pct": round(running_total, 3),
    })

    # ---- Residual: Model Interaction ----
    # The multiplicative model produces interaction effects that don't map
    # cleanly to additive components. Add residual to reconcile.
    residual = adjusted_prob - running_total
    if abs(residual) > 0.01:
        direction = "increase" if residual > 0 else "decrease"
        running_total += residual
        components.append({
            "name": "Model Interaction",
            "value_pct": round(residual, 3),
            "direction": direction,
            "is_calibrated": False,
            "source": "Multiplicative model interaction effects",
            "running_total_pct": round(running_total, 3),
        })
    else:
        # Snap the last component's running total to adjusted_prob
        if components:
            components[-1]["running_total_pct"] = round(adjusted_prob, 3)

    return components


__all__ = ["build_probability_decomposition"]
