"""DDL-based settlement prediction model.

Replaces Phase 12's tier-based severity model with a Dollar-Loss-Damages
(DDL) approach that computes settlement estimates from actual stock drops
and case characteristic multipliers.

The 5-step pipeline:
1. Compute DDL from stock drops (market_cap * max_drop_magnitude)
2. Apply base settlement percentage (~1% of DDL from config)
3. Apply case characteristic multipliers (accounting fraud, insider selling, etc.)
4. Compute percentile scenarios (25th/50th/75th/95th) using spread factors
5. Add defense cost estimates per scenario

Falls back to tier-based model_severity() when no stock drops are available.

Case characteristic detection is in case_characteristics.py (split for
500-line compliance).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.scoring import TierClassification
from do_uw.models.scoring_output import (
    SeverityScenario,
    SeverityScenarios,
)

# Re-export detect_case_characteristics from split module
from do_uw.stages.score.case_characteristics import (
    detect_case_characteristics as detect_case_characteristics,
)

logger = logging.getLogger(__name__)

_SCENARIO_LABELS = ["favorable", "median", "adverse", "catastrophic"]
_SCENARIO_PERCENTILES = [25, 50, 75, 95]


def _load_settlement_config() -> dict[str, Any]:
    """Load settlement_calibration.json from config directory."""
    return load_config("settlement_calibration")


def _get_tiered_base_pct(
    market_cap: float,
    config: dict[str, Any],
) -> float:
    """Get market-cap-tiered base settlement percentage.

    Falls back to the flat base_settlement_pct if no tiers are configured.
    """
    tiers = config.get("market_cap_tiers")
    if not isinstance(tiers, dict):
        return float(config.get("base_settlement_pct", 0.01))

    # Check tiers in descending order of threshold
    for _tier_name in ("mega_cap", "large_cap", "mid_cap", "small_cap"):
        tier = tiers.get(_tier_name)
        if tier is None:
            continue
        threshold = float(tier.get("threshold_usd", 0))
        if market_cap >= threshold:
            return float(tier.get("base_settlement_pct", 0.01))

    return float(config.get("base_settlement_pct", 0.01))


def compute_ddl(
    market_cap: float,
    stock_drops: list[dict[str, Any]],
) -> float:
    """Compute Dollar-Loss-Damages from market cap and stock drops.

    DDL = market_cap * maximum single-drop magnitude.
    Also computes cumulative DDL = market_cap * sum(abs(drops)).
    Returns the maximum of single-event and cumulative.

    Args:
        market_cap: Company market cap in USD.
        stock_drops: List of stock drop event dicts with 'drop_pct' field.
            drop_pct is a SourcedValue dict or a raw float (negative %).

    Returns:
        DDL amount in USD. Returns 0.0 if no valid drops.
    """
    if not stock_drops:
        return 0.0

    magnitudes: list[float] = []
    for drop in stock_drops:
        pct = _extract_drop_pct(drop)
        if pct is not None and pct < 0:
            magnitudes.append(abs(pct) / 100.0)

    if not magnitudes:
        return 0.0

    max_single = max(magnitudes)
    cumulative = sum(magnitudes)

    single_ddl = market_cap * max_single
    cumulative_ddl = market_cap * cumulative

    return max(single_ddl, cumulative_ddl)


def _extract_drop_pct(drop: dict[str, Any]) -> float | None:
    """Extract drop percentage from a stock drop event dict.

    Handles both SourcedValue format {"value": -15.3, ...} and raw float.
    """
    raw = drop.get("drop_pct")
    if raw is None:
        return None
    if isinstance(raw, dict):
        val = raw.get("value")
        if val is not None:
            return float(val)
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def predict_settlement(
    market_cap: float | None,
    stock_drops: list[dict[str, Any]],
    case_characteristics: dict[str, bool],
    calibration_config: dict[str, Any] | None = None,
    tier: TierClassification | None = None,
) -> SeverityScenarios | None:
    """DDL-based settlement prediction -- replaces model_severity().

    5-step pipeline:
    1. Compute DDL from stock drops
    2. Apply base settlement percentage
    3. Apply case characteristic multipliers
    4. Compute percentile scenarios
    5. Add defense cost estimates

    Falls back to tier-based ranges when stock_drops is empty.

    Args:
        market_cap: Company market cap in USD, or None.
        stock_drops: List of stock drop event dicts.
        case_characteristics: Dict of characteristic name -> bool.
        calibration_config: settlement_calibration.json contents.
        tier: Tier classification for fallback path.

    Returns:
        SeverityScenarios with DDL-based estimates, or None if market_cap
        is None or no stock drops (signaling fallback).
    """
    if market_cap is None:
        return None

    if calibration_config is None:
        calibration_config = _load_settlement_config()

    # Step 1: Compute DDL
    ddl = compute_ddl(market_cap, stock_drops)

    # If no DDL (no stock drops), return None to signal fallback
    if ddl <= 0:
        logger.info(
            "No stock drops for DDL computation; signaling fallback to tier model"
        )
        return None

    # Step 2: Base settlement = DDL * base_pct (market-cap-tiered)
    base_pct = _get_tiered_base_pct(market_cap, calibration_config)
    base_settlement = ddl * base_pct

    # Step 3: Apply case characteristic multipliers
    multipliers_config = calibration_config.get("multipliers", {})
    combined_multiplier = 1.0
    active_chars: list[str] = []
    for char_name, is_present in case_characteristics.items():
        if is_present:
            mult = float(multipliers_config.get(char_name, 1.0))
            combined_multiplier *= mult
            active_chars.append(f"{char_name}={mult}x")

    adjusted_settlement = base_settlement * combined_multiplier

    if active_chars:
        logger.info(
            "Settlement multipliers applied: %s (combined=%.2fx)",
            ", ".join(active_chars),
            combined_multiplier,
        )

    # Step 4: Build percentile scenarios with spread factors
    scenarios = _build_scenario_from_settlement(
        adjusted_settlement, ddl, calibration_config
    )

    # Build decline scenarios for backward compatibility
    decline_scenarios = {
        "10%": market_cap * 0.10,
        "20%": market_cap * 0.20,
        "30%": market_cap * 0.30,
    }

    return SeverityScenarios(
        market_cap=market_cap,
        decline_scenarios=decline_scenarios,
        scenarios=scenarios,
        needs_calibration=True,
    )


def _build_scenario_from_settlement(
    base_settlement: float,
    ddl: float,
    calibration_config: dict[str, Any],
) -> list[SeverityScenario]:
    """Build 4 percentile scenarios from base settlement using spread factors.

    Uses scenario_spread factors from config:
      favorable: base * 0.5, median: base * 1.0,
      adverse: base * 2.0, catastrophic: base * 4.0

    Adds defense costs: favorable 15%, median 20%, adverse 25%, catastrophic 30%.

    Args:
        base_settlement: Adjusted base settlement amount.
        ddl: Total DDL for the ddl_amount field.
        calibration_config: Config with spread factors and defense costs.

    Returns:
        List of 4 SeverityScenario objects.
    """
    spread = calibration_config.get("scenario_spread", {})
    spread_factors = [
        float(spread.get("favorable_factor", 0.5)),
        float(spread.get("median_factor", 1.0)),
        float(spread.get("adverse_factor", 2.0)),
        float(spread.get("catastrophic_factor", 4.0)),
    ]

    defense_pcts_raw = calibration_config.get(
        "defense_cost_pcts_by_scenario", [0.15, 0.20, 0.25, 0.30]
    )
    defense_pcts = [float(p) for p in defense_pcts_raw]

    scenarios: list[SeverityScenario] = []
    for i, (pct, label) in enumerate(
        zip(_SCENARIO_PERCENTILES, _SCENARIO_LABELS, strict=True)
    ):
        settlement = base_settlement * spread_factors[i]
        defense = settlement * defense_pcts[i]
        scenarios.append(
            SeverityScenario(
                percentile=pct,
                label=label,
                ddl_amount=ddl,
                settlement_estimate=settlement,
                defense_cost_estimate=defense,
                total_exposure=settlement + defense,
            )
        )

    return scenarios


def characterize_tower_risk(
    severity_scenarios: SeverityScenarios | None,
    actuarial_config: dict[str, Any],
) -> dict[str, Any]:
    """Characterize risk by layer using ILF expected loss share.

    Instead of prescribing attachment points, this function computes
    what percentage of expected loss each layer absorbs, based on
    ILF (Increased Limit Factor) parameters.

    Args:
        severity_scenarios: Settlement scenarios with DDL data.
        actuarial_config: actuarial.json with ilf_parameters.

    Returns:
        Dict with per-layer risk characterization:
        {"primary": {"expected_loss_share_pct": 65.0, ...}, ...}
    """
    if severity_scenarios is None or not severity_scenarios.scenarios:
        return {}

    # Get median settlement for risk distribution
    median_settlement = 0.0
    for s in severity_scenarios.scenarios:
        if s.percentile == 50:
            median_settlement = s.settlement_estimate
            break

    if median_settlement <= 0:
        return {}

    # Use ILF alpha to compute expected loss share per layer
    ilf_params = actuarial_config.get("ilf_parameters", {})
    alpha = float(ilf_params.get("standard", 0.40))

    # Standard tower layers from actuarial config
    tower_layers = actuarial_config.get("default_tower", {}).get("layers", [])
    if not tower_layers:
        tower_layers = [
            {"layer_type": "primary", "attachment": 0, "limit": 10_000_000},
            {"layer_type": "low_excess", "attachment": 10_000_000, "limit": 10_000_000},
            {"layer_type": "mid_excess", "attachment": 20_000_000, "limit": 10_000_000},
            {"layer_type": "high_excess", "attachment": 30_000_000, "limit": 10_000_000},
        ]

    result: dict[str, Any] = {}
    total_ilf = 0.0
    layer_ilfs: list[tuple[str, float]] = []

    for layer in tower_layers:
        layer_type = str(layer.get("layer_type", ""))
        if layer_type == "side_a":
            continue

        attachment = float(layer.get("attachment", 0))
        limit = float(layer.get("limit", 10_000_000))
        top = attachment + limit

        # ILF = (top / base_limit) ^ alpha - (attachment / base_limit) ^ alpha
        base_limit = float(tower_layers[0].get("limit", 10_000_000))
        if base_limit <= 0:
            base_limit = 10_000_000

        ilf_top = (top / base_limit) ** alpha
        ilf_att = (attachment / base_limit) ** alpha if attachment > 0 else 0.0
        layer_ilf = ilf_top - ilf_att

        layer_ilfs.append((layer_type, layer_ilf))
        total_ilf += layer_ilf

    # Convert ILFs to share percentages
    for layer_type, layer_ilf in layer_ilfs:
        share_pct = (layer_ilf / total_ilf * 100.0) if total_ilf > 0 else 0.0
        expected_loss = median_settlement * (share_pct / 100.0)

        characterization = _describe_layer_risk(layer_type, share_pct)

        result[layer_type] = {
            "expected_loss_share_pct": round(share_pct, 1),
            "expected_loss_amount": round(expected_loss, 0),
            "risk_characterization": characterization,
        }

    return result


def _describe_layer_risk(layer_type: str, share_pct: float) -> str:
    """Generate analytical risk characterization for a tower layer."""
    descriptions = {
        "primary": (
            f"Primary layer carries {share_pct:.0f}% of expected loss exposure. "
            "Highest frequency of attachment; most likely to be eroded "
            "in any claim scenario."
        ),
        "low_excess": (
            f"Low excess layer carries {share_pct:.0f}% of expected loss exposure. "
            "Attaches after primary exhaustion; moderate frequency in "
            "adverse scenarios."
        ),
        "mid_excess": (
            f"Mid excess layer carries {share_pct:.0f}% of expected loss exposure. "
            "Attaches in adverse scenarios; lower frequency but higher "
            "severity when reached."
        ),
        "high_excess": (
            f"High excess layer carries {share_pct:.0f}% of expected loss exposure. "
            "Attaches only in catastrophic scenarios; lowest frequency, "
            "highest severity."
        ),
    }
    return descriptions.get(
        layer_type,
        f"Layer carries {share_pct:.0f}% of expected loss exposure.",
    )


__all__ = [
    "characterize_tower_risk",
    "compute_ddl",
    "detect_case_characteristics",
    "predict_settlement",
]
