"""Damages estimation for severity model (Phase 108).

Computes base damages from market cap, stock price decline, and share
turnover. Applies allegation-type modifiers from severity_model_design.yaml.
Estimates defense costs via hybrid case-characteristic + market-cap-tier
approach. Generates scenario grids across drop levels.

References:
  - Alexander (1991): Damages = market_cap x class_period_return x turnover
  - Cornerstone Research: Allegation-type settlement patterns
  - NERA LEAD model: Stock decline as core damages input
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

__all__ = [
    "apply_allegation_modifier",
    "compute_base_damages",
    "compute_defense_costs",
    "compute_scenario_grid",
    "estimate_turnover_rate",
]

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------
# Module-level caches
# ---------------------------------------------------------------

_DESIGN_YAML_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "brain"
    / "framework"
    / "severity_model_design.yaml"
)
_design_cache: dict[str, Any] | None = None


def _load_design() -> dict[str, Any]:
    """Load severity_model_design.yaml. Cached as module-level singleton."""
    global _design_cache
    if _design_cache is not None:
        return _design_cache
    with open(_DESIGN_YAML_PATH) as f:
        _design_cache = yaml.safe_load(f)
    return _design_cache  # type: ignore[return-value]


def _load_allegation_modifiers() -> dict[str, float]:
    """Extract allegation type modifiers from design YAML.

    Returns dict mapping allegation_type -> multiplier.
    """
    design = _load_design()
    modifiers_list = (
        design.get("damages_estimation", {})
        .get("allegation_type_modifiers", {})
        .get("modifiers", [])
    )
    result: dict[str, float] = {}
    for mod in modifiers_list:
        atype = mod.get("type", "")
        mult = float(mod.get("multiplier", 1.0))
        result[atype] = mult
    return result


# ---------------------------------------------------------------
# Core damages computation
# ---------------------------------------------------------------


def compute_base_damages(
    market_cap: float,
    class_period_return: float,
    turnover_rate: float,
) -> float:
    """Compute base damages from market cap, stock decline, and turnover.

    Formula: base_damages = market_cap * |class_period_return| * min(turnover_rate, 1.0)

    This follows Alexander (1991) and Cornerstone methodology for
    estimating maximum potential damages in securities class actions.

    Args:
        market_cap: Market capitalization at start of class period (USD).
        class_period_return: Absolute stock decline as decimal (e.g., 0.30 for 30%).
        turnover_rate: Share turnover rate (capped at 1.0).

    Returns:
        Base damages estimate in USD.
    """
    return market_cap * abs(class_period_return) * min(turnover_rate, 1.0)


def apply_allegation_modifier(
    base_damages: float,
    allegation_type: str,
) -> float:
    """Apply allegation-type modifier to base damages.

    Modifiers from severity_model_design.yaml. Unknown types default to 1.0.

    Args:
        base_damages: Base damages amount (USD).
        allegation_type: Allegation type key (e.g. "financial_restatement").

    Returns:
        Modified damages amount (USD).
    """
    modifiers = _load_allegation_modifiers()
    multiplier = modifiers.get(allegation_type, 1.0)
    return base_damages * multiplier


def compute_scenario_grid(
    market_cap: float,
    stock_drops_data: list[dict[str, Any]],
    sector_median_drop: float = 0.25,
) -> list[tuple[str, float]]:
    """Generate scenario grid of drop levels for severity estimation.

    Produces three scenarios:
      - worst_actual: Largest absolute drop from stock_drops_data
      - sector_median: Sector median drop (default 25%)
      - catastrophic: Hypothetical 50% drop

    Args:
        market_cap: Market cap (USD) -- used for context, not in output.
        stock_drops_data: List of stock drop dicts with 'drop_pct' field.
        sector_median_drop: Sector median drop as decimal (default 0.25).

    Returns:
        List of (drop_level_label, drop_pct_decimal) tuples.
    """
    # Extract worst actual drop
    worst_drop_pct = 0.0
    for drop in stock_drops_data:
        pct = drop.get("drop_pct")
        if pct is None:
            continue
        if isinstance(pct, dict):
            pct = pct.get("value", 0)
        pct_val = float(pct) if pct is not None else 0.0
        magnitude = abs(pct_val) / 100.0 if abs(pct_val) > 1 else abs(pct_val)
        if magnitude > worst_drop_pct:
            worst_drop_pct = magnitude

    # Default to sector median if no drops available
    if worst_drop_pct == 0.0:
        worst_drop_pct = sector_median_drop

    return [
        ("worst_actual", worst_drop_pct),
        ("sector_median", sector_median_drop),
        ("catastrophic", 0.50),
    ]


# ---------------------------------------------------------------
# Defense costs
# ---------------------------------------------------------------

# Market-cap-tier base defense cost percentages
_DEFENSE_TIERS = [
    (50_000_000_000, 0.15),   # Large cap ($50B+): 15%
    (10_000_000_000, 0.20),   # Mid cap ($10B-$50B): 20%
    (0, 0.25),                 # Small cap (<$10B): 25%
]

# Case characteristic adjustments (additive on base percentage)
_CASE_CHAR_ADJUSTMENTS: dict[str, float] = {
    "multi_defendant": 0.05,
    "gov_investigation": 0.05,
    "long_class_period": 0.05,
}


def compute_defense_costs(
    settlement: float,
    case_chars: dict[str, Any],
    market_cap: float,
) -> float:
    """Estimate defense costs using hybrid approach.

    Base percentage determined by market-cap tier. Adjusted by case
    characteristics (multi-defendant +5%, government investigation +5%,
    long class period +5%).

    Args:
        settlement: Settlement estimate (USD).
        case_chars: Case characteristics dict (key -> bool/value).
        market_cap: Market capitalization (USD).

    Returns:
        Defense cost estimate (USD).
    """
    # Determine base percentage from market-cap tier
    base_pct = 0.25  # default small cap
    for threshold, pct in _DEFENSE_TIERS:
        if market_cap >= threshold:
            base_pct = pct
            break

    # Apply case characteristic adjustments
    total_pct = base_pct
    for char_key, adjustment in _CASE_CHAR_ADJUSTMENTS.items():
        if case_chars.get(char_key):
            total_pct += adjustment

    return settlement * total_pct


def estimate_turnover_rate(
    avg_daily_volume: float,
    shares_outstanding: float,
    class_period_days: int | None = None,
) -> float:
    """Estimate share turnover rate for damages calculation.

    Uses simplified proxy: avg_daily_volume * days / shares_outstanding.
    Capped at 1.0 per Bajaj et al. (2003) proportional trading assumption.

    Args:
        avg_daily_volume: Average daily trading volume.
        shares_outstanding: Total shares outstanding.
        class_period_days: Class period length in days (default 250).

    Returns:
        Turnover rate as decimal, capped at 1.0.
    """
    days = class_period_days if class_period_days is not None else 250
    if shares_outstanding <= 0:
        return 0.0
    raw = avg_daily_volume * days / shares_outstanding
    return min(raw, 1.0)
