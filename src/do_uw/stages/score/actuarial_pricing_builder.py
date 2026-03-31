"""Actuarial pricing orchestrator.

Combines expected loss computation (actuarial_model.py) with ILF
layer pricing and market calibration (actuarial_layer_pricing.py)
to produce a complete ActuarialPricing result.

Split from actuarial_layer_pricing.py for 500-line compliance.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.scoring_output import (
    ActuarialPricing,
    CalibratedPricing,
    ExpectedLoss,
    LayerSpec,
    SeverityScenarios,
)
from do_uw.stages.score.actuarial_layer_pricing import (
    calibrate_against_market,
    get_alpha,
    load_tower_structure,
    price_tower_layers,
)
from do_uw.stages.score.actuarial_model import compute_expected_loss

logger = logging.getLogger(__name__)


def build_actuarial_pricing(
    filing_probability_pct: float,
    severity_scenarios: SeverityScenarios | None,
    case_type: str,
    sector: str | None,
    market_cap_tier: str | None,
    market_position: Any | None,
    actuarial_config: dict[str, Any],
) -> ActuarialPricing:
    """Build complete actuarial pricing from inputs.

    Pipeline:
      1. compute_expected_loss (from actuarial_model)
      2. price_tower_layers (ILF allocation)
      3. calibrate_against_market (optional, if market data exists)
      4. Assemble ActuarialPricing result

    Args:
        filing_probability_pct: Filing probability as percentage.
        severity_scenarios: Severity model output or None.
        case_type: Case type for defense cost lookup.
        sector: Company sector for alpha lookup.
        market_cap_tier: Market cap tier for alpha lookup.
        market_position: MarketPosition (duck-typed) or None.
        actuarial_config: Full actuarial.json config dict.

    Returns:
        ActuarialPricing with complete tower pricing and calibration.
    """
    model_label = str(
        actuarial_config.get(
            "model_label",
            "MODEL-INDICATED: Not prescriptive. Underwriter sets final price.",
        )
    )

    # Step 1: Compute expected loss
    el = compute_expected_loss(
        filing_probability_pct=filing_probability_pct,
        severity_scenarios=severity_scenarios,
        case_type=case_type,
        actuarial_config=actuarial_config,
    )

    if not el.has_data:
        return ActuarialPricing(
            has_data=False,
            expected_loss=el,
            methodology_note=model_label,
        )

    # Step 2: Load tower and price layers
    tower = load_tower_structure(actuarial_config)
    alpha = get_alpha(sector, market_cap_tier, actuarial_config)
    lr_targets = actuarial_config.get("loss_ratio_targets", {})
    if not isinstance(lr_targets, dict):
        lr_targets = {}

    layers = price_tower_layers(
        el, tower, alpha, cast(dict[str, Any], lr_targets), actuarial_config
    )

    total_premium = sum(lp.indicated_premium for lp in layers)

    # Step 3: Calibrate primary layer against market (if available)
    calibrated: CalibratedPricing | None = None
    if market_position is not None and layers:
        primary = layers[0]
        calibrated = calibrate_against_market(
            model_premium=primary.indicated_premium,
            model_rol=primary.indicated_rol,
            market_position=market_position,
            credibility_config=actuarial_config.get("credibility", {}),
        )

    # Step 4: Build tower description
    tower_desc = _build_tower_description(tower)

    # Step 5: Assemble assumptions
    assumptions = _build_assumptions(
        el, alpha, case_type, sector, market_cap_tier
    )

    logger.info(
        "Actuarial pricing: %d layers, total premium $%.0f, alpha=%.2f",
        len(layers),
        total_premium,
        alpha,
    )

    return ActuarialPricing(
        has_data=True,
        expected_loss=el,
        layer_pricing=layers,
        calibrated_primary=calibrated,
        total_indicated_premium=total_premium,
        tower_structure_used=tower_desc,
        methodology_note=model_label,
        assumptions=assumptions,
    )


def _build_tower_description(tower: list[LayerSpec]) -> str:
    """Build human-readable tower structure description.

    Args:
        tower: List of LayerSpec.

    Returns:
        Description like "5-layer tower: $10M primary + 3x $10M excess".
    """
    if not tower:
        return "No tower structure"

    n = len(tower)
    parts: list[str] = [f"{n}-layer tower:"]

    # Primary
    primary = _find_primary(tower)
    if primary is not None:
        parts.append(f"${primary.limit / 1e6:.0f}M primary")

    # Excess
    excess_layers = _find_excess(tower)
    if excess_layers:
        first_ex = excess_layers[0]
        parts.append(
            f"{len(excess_layers)}x ${first_ex.limit / 1e6:.0f}M excess"
        )

    # Side A
    side_a = _find_side_a(tower)
    if side_a is not None:
        parts.append(f"${side_a.limit / 1e6:.0f}M Side A")

    return " + ".join(parts)


def _find_primary(tower: list[LayerSpec]) -> LayerSpec | None:
    """Find the primary layer (attachment=0, not side_a)."""
    for s in tower:
        if s.attachment == 0 and s.layer_type.lower() != "side_a":
            return s
    return None


def _find_excess(tower: list[LayerSpec]) -> list[LayerSpec]:
    """Find all excess layers (attachment>0, not side_a)."""
    return [
        s
        for s in tower
        if s.attachment > 0 and s.layer_type.lower() != "side_a"
    ]


def _find_side_a(tower: list[LayerSpec]) -> LayerSpec | None:
    """Find the first Side A layer."""
    for s in tower:
        if s.layer_type.lower() == "side_a":
            return s
    return None


def _build_assumptions(
    el: ExpectedLoss,
    alpha: float,
    case_type: str,
    sector: str | None,
    market_cap_tier: str | None,
) -> list[str]:
    """Build list of key assumptions used in pricing.

    Args:
        el: Expected loss results.
        alpha: ILF alpha used.
        case_type: Case type used.
        sector: Sector used for alpha lookup.
        market_cap_tier: Market cap tier used for alpha lookup.

    Returns:
        List of assumption strings.
    """
    assumptions: list[str] = [
        f"Filing probability: {el.filing_probability_pct:.2f}%",
        f"Median severity: ${el.median_severity:,.0f}",
        f"Defense cost: {el.defense_cost_pct * 100:.0f}% of indemnity",
        f"ILF alpha: {alpha:.2f} (power curve exponent)",
        f"Case type: {case_type}",
    ]

    if sector:
        assumptions.append(f"Sector: {sector}")
    if market_cap_tier:
        assumptions.append(f"Market cap tier: {market_cap_tier}")

    assumptions.append("All values MODEL-INDICATED, not prescriptive")

    return assumptions


__all__ = ["build_actuarial_pricing"]
