"""ILF power curve layer pricing and market calibration.

Allocates a total expected loss across tower layers using an Increased
Limits Factor (ILF) power curve: ILF(L) = (L / B)^alpha, where B is
the basic (primary) limit and alpha controls the curve steepness.

Each layer's expected loss = layer_factor * total_expected_loss, where
layer_factor = ILF(attachment + limit) - ILF(attachment) for excess
layers, and 1.0 for the primary.

Premium = expected_loss / target_loss_ratio for each layer.

Market calibration blends model-indicated ROL with observed market
ROL via credibility weighting: z = min(1, sqrt(n / standard)).

All parameters from actuarial.json -- nothing hardcoded.

Orchestrator (build_actuarial_pricing) in actuarial_pricing_builder.py.
"""

from __future__ import annotations

import logging
from math import sqrt
from typing import Any, cast

from do_uw.models.scoring_output import (
    CalibratedPricing,
    ExpectedLoss,
    LayerPricing,
    LayerSpec,
)

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# ILF computation
# -----------------------------------------------------------------------


def compute_ilf(limit: float, basic_limit: float, alpha: float) -> float:
    """Compute Increased Limits Factor for a given limit.

    ILF(L) = (L / B) ^ alpha

    Args:
        limit: Limit to compute ILF for (USD).
        basic_limit: Basic (primary) limit (USD).
        alpha: Power curve exponent (0 < alpha < 1 typically).

    Returns:
        ILF factor. Returns 1.0 for zero/negative inputs.
    """
    if basic_limit <= 0 or limit <= 0:
        return 1.0
    return (limit / basic_limit) ** alpha


def _compute_layer_factor(
    attachment: float,
    layer_limit: float,
    basic_limit: float,
    alpha: float,
) -> float:
    """Compute the ILF-based factor for a single layer.

    Primary layer (attachment=0): factor = 1.0 by definition.
    Excess layers: factor = ILF(attachment + limit) - ILF(attachment).

    Args:
        attachment: Layer attachment point (USD).
        layer_limit: Layer limit (USD).
        basic_limit: Primary layer limit (USD) used as ILF base.
        alpha: Power curve exponent.

    Returns:
        Layer factor (fraction of primary layer expected loss).
    """
    if attachment <= 0:
        return 1.0

    ilf_top = compute_ilf(attachment + layer_limit, basic_limit, alpha)
    ilf_bottom = compute_ilf(attachment, basic_limit, alpha)
    return ilf_top - ilf_bottom


# -----------------------------------------------------------------------
# Alpha lookup
# -----------------------------------------------------------------------


def get_alpha(
    sector: str | None,
    market_cap_tier: str | None,
    actuarial_config: dict[str, Any],
) -> float:
    """Look up ILF alpha exponent from config.

    Tries sector-specific key first, then market-cap-specific,
    then falls back to 'standard'.

    Args:
        sector: Company sector (e.g. 'biotech', 'financial_services').
        market_cap_tier: Market cap tier (e.g. 'large_cap', 'small_cap').
        actuarial_config: Full actuarial.json config dict.

    Returns:
        Alpha exponent for ILF power curve.
    """
    ilf_params = actuarial_config.get("ilf_parameters", {})
    if not isinstance(ilf_params, dict):
        return 0.40

    params = cast(dict[str, Any], ilf_params)

    # Try sector-specific
    if sector is not None:
        sector_key = sector.lower().replace(" ", "_")
        value = params.get(sector_key)
        if isinstance(value, (int, float)):
            return float(value)

    # Try market-cap-tier-specific
    if market_cap_tier is not None:
        tier_key = market_cap_tier.lower().replace(" ", "_")
        value = params.get(tier_key)
        if isinstance(value, (int, float)):
            return float(value)

    # Fallback to standard
    standard = params.get("standard", 0.40)
    if isinstance(standard, (int, float)):
        return float(standard)
    return 0.40


# -----------------------------------------------------------------------
# Tower pricing
# -----------------------------------------------------------------------


def price_tower_layers(
    expected_loss: ExpectedLoss,
    tower_structure: list[LayerSpec],
    alpha: float,
    loss_ratio_targets: dict[str, Any],
    actuarial_config: dict[str, Any],
) -> list[LayerPricing]:
    """Price each layer in a D&O tower using ILF factors.

    For each layer, computes:
      - layer_factor via ILF power curve
      - layer_expected_loss = factor * total_expected_loss
      - indicated_premium = layer_expected_loss / target_loss_ratio
      - ROL = indicated_premium / layer_limit

    Side A layers use primary expected loss (attachment=0, factor=1.0).

    Args:
        expected_loss: Total expected loss from actuarial model.
        tower_structure: List of LayerSpec defining the tower.
        alpha: ILF power curve exponent.
        loss_ratio_targets: Target loss ratios by layer type.
        actuarial_config: Full actuarial.json config dict.

    Returns:
        List of LayerPricing, one per tower layer. Empty if no data.
    """
    if not expected_loss.has_data or not tower_structure:
        return []

    total_el = expected_loss.total_expected_loss

    # Primary limit = first non-side_a layer limit (basic limit for ILF)
    basic_limit = _find_basic_limit(tower_structure)
    if basic_limit <= 0:
        return []

    result: list[LayerPricing] = []

    for spec in tower_structure:
        # Side A layers priced like primary (attachment=0)
        is_side_a = spec.layer_type.lower() == "side_a"

        if is_side_a:
            layer_factor = 1.0
        else:
            layer_factor = _compute_layer_factor(
                spec.attachment, spec.limit, basic_limit, alpha
            )

        layer_el = layer_factor * total_el

        # Look up target loss ratio
        lr_key = _layer_type_key(spec.layer_type)
        target_lr = _get_loss_ratio(lr_key, loss_ratio_targets)

        # Premium = expected_loss / loss_ratio
        indicated_premium = layer_el / target_lr if target_lr > 0 else 0.0

        # ROL = premium / limit
        rol = indicated_premium / spec.limit if spec.limit > 0 else 0.0

        result.append(
            LayerPricing(
                layer_type=spec.layer_type,
                layer_number=spec.layer_number,
                attachment=spec.attachment,
                limit=spec.limit,
                ilf_factor=layer_factor,
                expected_loss=layer_el,
                target_loss_ratio=target_lr,
                indicated_premium=indicated_premium,
                indicated_rol=rol,
                confidence_note=_confidence_note(spec, is_side_a),
            )
        )

    return result


def _find_basic_limit(tower: list[LayerSpec]) -> float:
    """Find the primary layer limit (basic limit for ILF).

    Returns the limit of the first layer with attachment=0
    that is not side_a. Falls back to first layer's limit.
    """
    for spec in tower:
        if spec.attachment == 0 and spec.layer_type.lower() != "side_a":
            return spec.limit
    return tower[0].limit if tower else 0.0


def _layer_type_key(layer_type: str) -> str:
    """Normalize layer_type to loss_ratio_targets key."""
    return layer_type.lower().replace(" ", "_")


def _get_loss_ratio(
    layer_key: str,
    loss_ratio_targets: dict[str, Any],
) -> float:
    """Look up target loss ratio for a layer type.

    Falls back to 'primary' if specific key not found, then 0.50.
    """
    value = loss_ratio_targets.get(layer_key)
    if isinstance(value, (int, float)):
        return float(value)

    primary_val = loss_ratio_targets.get("primary", 0.50)
    if isinstance(primary_val, (int, float)):
        return float(primary_val)
    return 0.50


def _confidence_note(spec: LayerSpec, is_side_a: bool) -> str:
    """Generate confidence note for a layer."""
    if is_side_a:
        return "Side A: priced at primary attachment; actual pricing may differ"
    if spec.attachment == 0:
        return "Primary layer: highest confidence in ILF model"
    return f"Excess layer at ${spec.attachment:,.0f}: ILF extrapolation"


# -----------------------------------------------------------------------
# Market calibration
# -----------------------------------------------------------------------


def calibrate_against_market(
    model_premium: float,
    model_rol: float,
    market_position: Any,
    credibility_config: dict[str, Any],
) -> CalibratedPricing:
    """Blend model-indicated ROL with market-observed ROL.

    Credibility weight z = min(1, sqrt(n / standard)).
    Calibrated ROL = z * market_ROL + (1-z) * model_ROL.

    Args:
        model_premium: Model-indicated premium (USD).
        model_rol: Model-indicated rate on line.
        market_position: MarketPosition (duck-typed) with peer_count,
            confidence_level, median_rate_on_line attributes.
        credibility_config: Config with 'standard' key.

    Returns:
        CalibratedPricing with blend of model and market.
    """
    # If market data insufficient, return model-only
    confidence = getattr(market_position, "confidence_level", "INSUFFICIENT")
    if confidence == "INSUFFICIENT":
        return CalibratedPricing(
            model_indicated_premium=model_premium,
            model_indicated_rol=model_rol,
            market_median_rol=None,
            credibility=0.0,
            calibrated_rol=model_rol,
            calibrated_premium=model_premium,
            calibration_source="Model only (insufficient market data)",
        )

    # Get market ROL
    market_rol = getattr(market_position, "median_rate_on_line", None)
    if market_rol is None or market_rol <= 0:
        return CalibratedPricing(
            model_indicated_premium=model_premium,
            model_indicated_rol=model_rol,
            market_median_rol=None,
            credibility=0.0,
            calibrated_rol=model_rol,
            calibrated_premium=model_premium,
            calibration_source="Model only (no market median ROL)",
        )

    # Compute credibility weight
    n = getattr(market_position, "peer_count", 0)
    standard = credibility_config.get("standard", 50)
    if not isinstance(standard, (int, float)) or standard <= 0:
        standard = 50

    z = min(1.0, sqrt(n / float(standard)))

    # Blend
    calibrated_rol = z * float(market_rol) + (1.0 - z) * model_rol

    # Derive calibrated premium from ROL
    if model_rol > 0:
        implied_limit = model_premium / model_rol
        calibrated_premium = implied_limit * calibrated_rol
    else:
        calibrated_premium = model_premium

    return CalibratedPricing(
        model_indicated_premium=model_premium,
        model_indicated_rol=model_rol,
        market_median_rol=float(market_rol),
        credibility=z,
        calibrated_rol=calibrated_rol,
        calibrated_premium=calibrated_premium,
        calibration_source=f"Credibility-weighted (z={z:.3f}, n={n})",
    )


# -----------------------------------------------------------------------
# Tower structure loader
# -----------------------------------------------------------------------


def load_tower_structure(
    actuarial_config: dict[str, Any],
) -> list[LayerSpec]:
    """Load default tower structure from config.

    Args:
        actuarial_config: Full actuarial.json config dict.

    Returns:
        List of LayerSpec from default_tower.layers config.
    """
    default_tower = actuarial_config.get("default_tower", {})
    if not isinstance(default_tower, dict):
        return []

    tower_dict = cast(dict[str, Any], default_tower)
    layers_raw = tower_dict.get("layers", [])
    if not isinstance(layers_raw, list):
        return []

    typed_layers = cast(list[Any], layers_raw)
    result: list[LayerSpec] = []
    for raw_item in typed_layers:
        if not isinstance(raw_item, dict):
            continue
        item = cast(dict[str, Any], raw_item)
        try:
            result.append(
                LayerSpec(
                    layer_type=str(item.get("layer_type", "unknown")),
                    layer_number=int(item.get("layer_number", 0)),
                    attachment=float(item.get("attachment", 0)),
                    limit=float(item.get("limit", 0)),
                )
            )
        except (TypeError, ValueError):
            logger.warning("Skipping invalid tower layer: %s", item)
            continue

    return result


__all__ = [
    "_compute_layer_factor",
    "calibrate_against_market",
    "compute_ilf",
    "get_alpha",
    "load_tower_structure",
    "price_tower_layers",
]
