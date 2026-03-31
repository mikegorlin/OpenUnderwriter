"""Tests for ILF layer pricing and market calibration.

RED phase: Tests written before implementation.
"""

from __future__ import annotations

import json
from math import sqrt
from pathlib import Path
from typing import Any

import pytest

from do_uw.models.scoring_output import (
    ExpectedLoss,
    LayerSpec,
    SeverityScenario,
    SeverityScenarios,
)

# Load actual config for integration-level tests
_CONFIG_PATH = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config" / "actuarial.json"


def _load_config() -> dict[str, Any]:
    """Load actuarial.json config."""
    with open(_CONFIG_PATH) as f:
        return json.load(f)  # type: ignore[no-any-return]


def _make_expected_loss(
    total: float = 2_488_320.0,
    has_data: bool = True,
) -> ExpectedLoss:
    """Create ExpectedLoss with controllable total."""
    return ExpectedLoss(
        has_data=has_data,
        filing_probability_pct=7.68,
        median_severity=27_000_000.0,
        defense_cost_pct=0.20,
        expected_indemnity=total / 1.20,
        expected_defense=total - total / 1.20,
        total_expected_loss=total,
        methodology_note="MODEL-INDICATED",
    )


def _make_tower() -> list[LayerSpec]:
    """Create 5-layer default tower matching actuarial.json."""
    lim = 10_000_000
    return [
        LayerSpec(layer_type="primary", layer_number=1, attachment=0, limit=lim),
        LayerSpec(
            layer_type="low_excess", layer_number=2, attachment=lim, limit=lim
        ),
        LayerSpec(
            layer_type="mid_excess", layer_number=3, attachment=2 * lim, limit=lim
        ),
        LayerSpec(
            layer_type="high_excess", layer_number=4, attachment=3 * lim, limit=lim
        ),
        LayerSpec(layer_type="side_a", layer_number=5, attachment=0, limit=lim),
    ]


def _make_severity_scenarios(
    median_settlement: float = 27_000_000.0,
) -> SeverityScenarios:
    """Create SeverityScenarios with controllable median."""
    return SeverityScenarios(
        market_cap=10_000_000_000.0,
        scenarios=[
            SeverityScenario(
                percentile=25,
                label="favorable",
                settlement_estimate=median_settlement * 0.5,
                defense_cost_estimate=median_settlement * 0.5 * 0.15,
                total_exposure=median_settlement * 0.5 * 1.15,
            ),
            SeverityScenario(
                percentile=50,
                label="median",
                settlement_estimate=median_settlement,
                defense_cost_estimate=median_settlement * 0.20,
                total_exposure=median_settlement * 1.20,
            ),
            SeverityScenario(
                percentile=75,
                label="adverse",
                settlement_estimate=median_settlement * 2.0,
                defense_cost_estimate=median_settlement * 2.0 * 0.25,
                total_exposure=median_settlement * 2.0 * 1.25,
            ),
            SeverityScenario(
                percentile=95,
                label="catastrophic",
                settlement_estimate=median_settlement * 4.0,
                defense_cost_estimate=median_settlement * 4.0 * 0.30,
                total_exposure=median_settlement * 4.0 * 1.30,
            ),
        ],
    )


# Stub MarketPosition-like dataclass for calibration tests
class _FakeMarketPosition:
    """Minimal duck-typed MarketPosition for calibration tests."""

    def __init__(
        self,
        peer_count: int = 25,
        confidence_level: str = "MEDIUM",
        median_rate_on_line: float | None = 0.035,
    ) -> None:
        self.peer_count = peer_count
        self.confidence_level = confidence_level
        self.median_rate_on_line = median_rate_on_line


# -----------------------------------------------------------------------
# ILF computation tests
# -----------------------------------------------------------------------


class TestComputeILF:
    """Tests for compute_ilf function."""

    def test_compute_ilf_basic(self) -> None:
        """ILF(10M, 10M, 0.40) = (10/10)^0.40 = 1.0."""
        from do_uw.stages.score.actuarial_layer_pricing import compute_ilf

        result = compute_ilf(10_000_000, 10_000_000, 0.40)
        assert result == pytest.approx(1.0)

    def test_compute_ilf_excess(self) -> None:
        """ILF(20M, 10M, 0.40) = 2.0^0.40 = 1.3195..."""
        from do_uw.stages.score.actuarial_layer_pricing import compute_ilf

        result = compute_ilf(20_000_000, 10_000_000, 0.40)
        expected = 2.0**0.40  # 1.31950791...
        assert result == pytest.approx(expected, rel=1e-6)

    def test_compute_ilf_zero_limit(self) -> None:
        """Returns 1.0 for zero/negative inputs."""
        from do_uw.stages.score.actuarial_layer_pricing import compute_ilf

        assert compute_ilf(0, 10_000_000, 0.40) == 1.0
        assert compute_ilf(-5_000_000, 10_000_000, 0.40) == 1.0
        assert compute_ilf(10_000_000, 0, 0.40) == 1.0
        assert compute_ilf(10_000_000, -1, 0.40) == 1.0


# -----------------------------------------------------------------------
# Layer factor tests
# -----------------------------------------------------------------------


class TestComputeLayerFactor:
    """Tests for _compute_layer_factor function."""

    def test_compute_layer_factor_primary(self) -> None:
        """Primary layer (attachment=0) factor = 1.0."""
        from do_uw.stages.score.actuarial_layer_pricing import _compute_layer_factor

        result = _compute_layer_factor(
            attachment=0,
            layer_limit=10_000_000,
            basic_limit=10_000_000,
            alpha=0.40,
        )
        assert result == pytest.approx(1.0)

    def test_compute_layer_factor_first_excess(self) -> None:
        """$10M xs $10M: ILF(20M) - ILF(10M) = 2^0.40 - 1.0 = 0.3195..."""
        from do_uw.stages.score.actuarial_layer_pricing import _compute_layer_factor

        result = _compute_layer_factor(
            attachment=10_000_000,
            layer_limit=10_000_000,
            basic_limit=10_000_000,
            alpha=0.40,
        )
        expected = 2.0**0.40 - 1.0  # 0.31950791...
        assert result == pytest.approx(expected, rel=1e-6)

    def test_compute_layer_factor_decreasing(self) -> None:
        """Each successive layer has a smaller factor than the one below."""
        from do_uw.stages.score.actuarial_layer_pricing import _compute_layer_factor

        alpha = 0.40
        basic = 10_000_000

        factor_1xs1 = _compute_layer_factor(10_000_000, 10_000_000, basic, alpha)
        factor_2xs2 = _compute_layer_factor(20_000_000, 10_000_000, basic, alpha)
        factor_3xs3 = _compute_layer_factor(30_000_000, 10_000_000, basic, alpha)

        assert factor_1xs1 > factor_2xs2
        assert factor_2xs2 > factor_3xs3
        assert factor_3xs3 > 0  # Still positive


# -----------------------------------------------------------------------
# price_tower_layers tests
# -----------------------------------------------------------------------


class TestPriceTowerLayers:
    """Tests for price_tower_layers function."""

    def test_price_tower_basic(self) -> None:
        """5-layer tower: all layers get pricing, ROLs decrease up the tower."""
        from do_uw.stages.score.actuarial_layer_pricing import price_tower_layers

        config = _load_config()
        el = _make_expected_loss(2_488_320.0)
        tower = _make_tower()
        alpha = 0.40
        lr_targets = config["loss_ratio_targets"]

        layers = price_tower_layers(el, tower, alpha, lr_targets, config)

        assert len(layers) == 5

        # Primary, low_excess, mid_excess, high_excess should have decreasing ROL
        excess_layers = [lp for lp in layers if lp.layer_type != "side_a"]
        rols = [lp.indicated_rol for lp in excess_layers]
        for i in range(len(rols) - 1):
            assert rols[i] > rols[i + 1], (
                f"ROL[{i}]={rols[i]} should be > ROL[{i + 1}]={rols[i + 1]}"
            )

    def test_price_tower_no_data(self) -> None:
        """expected_loss.has_data=False -> returns empty list."""
        from do_uw.stages.score.actuarial_layer_pricing import price_tower_layers

        config = _load_config()
        el = _make_expected_loss(has_data=False)
        tower = _make_tower()
        alpha = 0.40
        lr_targets = config["loss_ratio_targets"]

        layers = price_tower_layers(el, tower, alpha, lr_targets, config)
        assert layers == []

    def test_price_tower_empty_structure(self) -> None:
        """Empty tower -> returns empty list."""
        from do_uw.stages.score.actuarial_layer_pricing import price_tower_layers

        config = _load_config()
        el = _make_expected_loss(2_488_320.0)
        alpha = 0.40
        lr_targets = config["loss_ratio_targets"]

        layers = price_tower_layers(el, [], alpha, lr_targets, config)
        assert layers == []

    def test_premium_equals_loss_div_lr(self) -> None:
        """Verify indicated_premium = expected_loss / target_loss_ratio for primary."""
        from do_uw.stages.score.actuarial_layer_pricing import price_tower_layers

        config = _load_config()
        el = _make_expected_loss(2_488_320.0)
        tower = _make_tower()
        alpha = 0.40
        lr_targets = config["loss_ratio_targets"]

        layers = price_tower_layers(el, tower, alpha, lr_targets, config)

        primary = layers[0]
        assert primary.layer_type == "primary"
        # Premium = expected_loss / loss_ratio
        assert primary.indicated_premium == pytest.approx(
            primary.expected_loss / primary.target_loss_ratio, rel=1e-6
        )

    def test_rol_equals_premium_div_limit(self) -> None:
        """Verify ROL = premium / limit for all layers."""
        from do_uw.stages.score.actuarial_layer_pricing import price_tower_layers

        config = _load_config()
        el = _make_expected_loss(2_488_320.0)
        tower = _make_tower()
        alpha = 0.40
        lr_targets = config["loss_ratio_targets"]

        layers = price_tower_layers(el, tower, alpha, lr_targets, config)

        for lp in layers:
            expected_rol = lp.indicated_premium / lp.limit if lp.limit > 0 else 0.0
            assert lp.indicated_rol == pytest.approx(expected_rol, rel=1e-6), (
                f"Layer {lp.layer_type}: ROL {lp.indicated_rol} != premium/limit {expected_rol}"
            )


# -----------------------------------------------------------------------
# calibrate_against_market tests
# -----------------------------------------------------------------------


class TestCalibrateAgainstMarket:
    """Tests for calibrate_against_market function."""

    def test_calibrate_no_market(self) -> None:
        """INSUFFICIENT confidence -> returns model-only."""
        from do_uw.stages.score.actuarial_layer_pricing import calibrate_against_market

        config = _load_config()
        market = _FakeMarketPosition(
            peer_count=2,
            confidence_level="INSUFFICIENT",
            median_rate_on_line=0.035,
        )

        result = calibrate_against_market(
            model_premium=100_000.0,
            model_rol=0.010,
            market_position=market,
            credibility_config=config.get("credibility", {}),
        )

        assert result.credibility == 0.0
        assert result.calibrated_rol == pytest.approx(0.010)
        assert result.model_indicated_rol == pytest.approx(0.010)
        assert result.market_median_rol is None

    def test_calibrate_with_market(self) -> None:
        """n=25, standard=50 -> z=sqrt(0.5)=0.707, calibrated = blend."""
        from do_uw.stages.score.actuarial_layer_pricing import calibrate_against_market

        config = _load_config()
        market = _FakeMarketPosition(
            peer_count=25,
            confidence_level="MEDIUM",
            median_rate_on_line=0.035,
        )

        model_rol = 0.025
        model_premium = 250_000.0

        result = calibrate_against_market(
            model_premium=model_premium,
            model_rol=model_rol,
            market_position=market,
            credibility_config=config.get("credibility", {}),
        )

        z = sqrt(25 / 50)  # 0.70710678...
        expected_rol = z * 0.035 + (1 - z) * model_rol
        assert result.credibility == pytest.approx(z, rel=1e-4)
        assert result.calibrated_rol == pytest.approx(expected_rol, rel=1e-4)
        assert result.market_median_rol == pytest.approx(0.035)

    def test_calibrate_full_credibility(self) -> None:
        """n=100 >= standard=50 -> z=1.0 -> fully market-weighted."""
        from do_uw.stages.score.actuarial_layer_pricing import calibrate_against_market

        config = _load_config()
        market = _FakeMarketPosition(
            peer_count=100,
            confidence_level="HIGH",
            median_rate_on_line=0.040,
        )

        result = calibrate_against_market(
            model_premium=100_000.0,
            model_rol=0.010,
            market_position=market,
            credibility_config=config.get("credibility", {}),
        )

        assert result.credibility == pytest.approx(1.0)
        assert result.calibrated_rol == pytest.approx(0.040, rel=1e-4)

    def test_calibrate_zero_model_rol(self) -> None:
        """model_rol=0 -> handle gracefully, calibration still works."""
        from do_uw.stages.score.actuarial_layer_pricing import calibrate_against_market

        config = _load_config()
        market = _FakeMarketPosition(
            peer_count=25,
            confidence_level="MEDIUM",
            median_rate_on_line=0.035,
        )

        result = calibrate_against_market(
            model_premium=0.0,
            model_rol=0.0,
            market_position=market,
            credibility_config=config.get("credibility", {}),
        )

        # Should not crash; calibrated ROL blends 0 model with market
        z = sqrt(25 / 50)
        expected_rol = z * 0.035 + (1 - z) * 0.0
        assert result.calibrated_rol == pytest.approx(expected_rol, rel=1e-4)


# -----------------------------------------------------------------------
# build_actuarial_pricing orchestrator tests
# -----------------------------------------------------------------------


class TestBuildActuarialPricing:
    """Tests for build_actuarial_pricing orchestrator."""

    def test_build_actuarial_pricing_happy_path(self) -> None:
        """Full pipeline: expected loss -> layers -> calibrated -> ActuarialPricing."""
        from do_uw.stages.score.actuarial_pricing_builder import build_actuarial_pricing

        config = _load_config()
        scenarios = _make_severity_scenarios(27_000_000.0)

        result = build_actuarial_pricing(
            filing_probability_pct=7.68,
            severity_scenarios=scenarios,
            case_type="standard_sca",
            sector=None,
            market_cap_tier=None,
            market_position=None,
            actuarial_config=config,
        )

        assert result.has_data is True
        assert result.expected_loss is not None
        assert result.expected_loss.has_data is True
        assert len(result.layer_pricing) == 5
        assert result.total_indicated_premium > 0
        assert "MODEL-INDICATED" in result.methodology_note
        assert len(result.assumptions) > 0

    def test_build_actuarial_pricing_no_data(self) -> None:
        """No severity data -> ActuarialPricing(has_data=False)."""
        from do_uw.stages.score.actuarial_pricing_builder import build_actuarial_pricing

        config = _load_config()

        result = build_actuarial_pricing(
            filing_probability_pct=7.68,
            severity_scenarios=None,
            case_type="standard_sca",
            sector=None,
            market_cap_tier=None,
            market_position=None,
            actuarial_config=config,
        )

        assert result.has_data is False
        assert result.expected_loss is not None
        assert result.expected_loss.has_data is False
        assert result.layer_pricing == []
        assert result.total_indicated_premium == 0.0
