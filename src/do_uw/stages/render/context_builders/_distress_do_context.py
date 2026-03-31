"""Data builder helpers for distress model indicators.

Builds trajectory and component breakdown data for Altman Z-Score and
Piotroski F-Score template rendering. D&O commentary for all distress
models (Altman, Beneish, Ohlson, Piotroski) lives in brain YAML do_context.
"""

from __future__ import annotations

from typing import Any


def _safe_float(val: Any, default: float = 0.0) -> float:
    """Convert to float, returning *default* on any failure."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default



def build_altman_trajectory(z: Any) -> list[dict[str, str]]:
    """Build Altman Z-Score trajectory for template display."""
    trajectory: list[dict[str, str]] = []
    if z is None:
        return trajectory
    # Historical trajectory from state
    raw_traj = getattr(z, "trajectory", None) or []
    for entry in raw_traj:
        if hasattr(entry, "period"):
            period = entry.period
            t_score = entry.score
            t_zone = entry.zone
        elif isinstance(entry, dict):
            period = entry.get("period", "")
            t_score = entry.get("score")
            t_zone = entry.get("zone", "")
        else:
            continue
        if t_score is not None:
            trajectory.append({
                "period": str(period),
                "score": f"{t_score:.2f}",
                "zone": str(t_zone),
            })
    # Add current score at end
    if z.score is not None:
        trajectory.append({
            "period": "Current",
            "score": f"{z.score:.2f}",
            "zone": str(z.zone) if z.zone else "",
        })
    return trajectory


_PIOTROSKI_LABELS = {
    "positive_ni": "Positive Net Income",
    "improving_roa": "Improving ROA",
    "positive_ocf": "Positive Operating Cash Flow",
    "ocf_exceeds_ni": "OCF Exceeds Net Income",
    "decreasing_leverage": "Decreasing Leverage",
    "improving_current_ratio": "Improving Current Ratio",
    "no_dilution": "No Share Dilution",
    "improving_gross_margin": "Improving Gross Margin",
    "improving_asset_turnover": "Improving Asset Turnover",
}


def build_piotroski_components(p: Any) -> list[dict[str, Any]]:
    """Build Piotroski F-Score component breakdown for template display."""
    components: list[dict[str, Any]] = []
    if p is None:
        return components
    raw_traj = getattr(p, "trajectory", None) or []
    for entry in raw_traj:
        if hasattr(entry, "criterion"):
            criterion = entry.criterion
            score_val = entry.score
        elif isinstance(entry, dict):
            criterion = entry.get("criterion", "")
            score_val = entry.get("score")
        else:
            continue
        components.append({
            "criterion": str(criterion),
            "label": _PIOTROSKI_LABELS.get(
                str(criterion),
                str(criterion).replace("_", " ").title(),
            ),
            "passed": _safe_float(score_val, 0.0) >= 1.0,
        })
    return components


__all__ = [
    "build_altman_trajectory",
    "build_piotroski_components",
]
