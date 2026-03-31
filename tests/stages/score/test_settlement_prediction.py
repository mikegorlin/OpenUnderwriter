"""Tests for DDL-based settlement prediction model."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.scoring import Tier, TierClassification
from do_uw.models.scoring_output import SeverityScenarios
from do_uw.stages.score.settlement_prediction import (
    characterize_tower_risk,
    compute_ddl,
    detect_case_characteristics,
    predict_settlement,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CALIBRATION_CONFIG: dict[str, Any] = {
    "base_settlement_pct": 0.01,
    "multipliers": {
        "accounting_fraud": 2.0,
        "restatement": 1.8,
        "insider_selling": 1.3,
        "institutional_lead_plaintiff": 1.5,
        "top_tier_counsel": 1.3,
        "sec_investigation": 1.6,
        "class_period_over_1yr": 1.2,
        "multiple_corrective_disclosures": 1.4,
        "going_concern": 1.7,
        "officer_termination": 1.3,
    },
    "defense_cost_pcts_by_scenario": [0.15, 0.20, 0.25, 0.30],
    "scenario_spread": {
        "favorable_factor": 0.5,
        "median_factor": 1.0,
        "adverse_factor": 2.0,
        "catastrophic_factor": 4.0,
    },
    "needs_calibration": True,
}

ACTUARIAL_CONFIG: dict[str, Any] = {
    "ilf_parameters": {"standard": 0.40},
    "default_tower": {
        "layers": [
            {"layer_type": "primary", "layer_number": 1, "attachment": 0, "limit": 10_000_000},
            {"layer_type": "low_excess", "layer_number": 2, "attachment": 10_000_000, "limit": 10_000_000},
            {"layer_type": "mid_excess", "layer_number": 3, "attachment": 20_000_000, "limit": 10_000_000},
            {"layer_type": "high_excess", "layer_number": 4, "attachment": 30_000_000, "limit": 10_000_000},
        ]
    },
}

NO_CHARS: dict[str, bool] = {
    "accounting_fraud": False,
    "restatement": False,
    "insider_selling": False,
    "institutional_lead_plaintiff": False,
    "top_tier_counsel": False,
    "sec_investigation": False,
    "class_period_over_1yr": False,
    "multiple_corrective_disclosures": False,
    "going_concern": False,
    "officer_termination": False,
}

SOME_CHARS: dict[str, bool] = {
    **NO_CHARS,
    "accounting_fraud": True,
    "insider_selling": True,
}


def _make_drop(pct: float) -> dict[str, Any]:
    """Create a stock drop dict with SourcedValue format."""
    return {"drop_pct": {"value": pct, "source": "test", "confidence": "MEDIUM"}}


def _make_raw_drop(pct: float) -> dict[str, Any]:
    """Create a stock drop dict with raw float."""
    return {"drop_pct": pct}


def _make_tier(tier: Tier = Tier.WRITE) -> TierClassification:
    return TierClassification(
        tier=tier,
        quality_score=60.0,
        tier_label=tier.value,
    )


# ---------------------------------------------------------------------------
# compute_ddl tests
# ---------------------------------------------------------------------------


class TestComputeDDL:
    """Test DDL computation from stock drops."""

    def test_no_drops_returns_zero(self) -> None:
        assert compute_ddl(10e9, []) == 0.0

    def test_single_drop(self) -> None:
        """DDL = market_cap * abs(drop_pct/100)."""
        drops = [_make_drop(-15.0)]
        ddl = compute_ddl(10e9, drops)
        assert ddl == pytest.approx(10e9 * 0.15)

    def test_multiple_drops_uses_max_of_single_and_cumulative(self) -> None:
        """With multiple drops, DDL = max(single_max * mcap, cumulative * mcap)."""
        drops = [_make_drop(-10.0), _make_drop(-20.0)]
        ddl = compute_ddl(10e9, drops)
        # max_single = 0.20, cumulative = 0.30
        # single_ddl = 10e9 * 0.20 = 2e9
        # cumulative_ddl = 10e9 * 0.30 = 3e9
        assert ddl == pytest.approx(10e9 * 0.30)

    def test_raw_float_drops(self) -> None:
        """Handles raw float drop_pct values."""
        drops = [_make_raw_drop(-25.0)]
        ddl = compute_ddl(5e9, drops)
        assert ddl == pytest.approx(5e9 * 0.25)

    def test_ignores_positive_values(self) -> None:
        """Positive 'drops' (gains) are ignored."""
        drops = [_make_drop(5.0), _make_drop(-10.0)]
        ddl = compute_ddl(10e9, drops)
        assert ddl == pytest.approx(10e9 * 0.10)

    def test_zero_market_cap(self) -> None:
        drops = [_make_drop(-10.0)]
        assert compute_ddl(0.0, drops) == 0.0

    def test_missing_drop_pct_ignored(self) -> None:
        drops = [{"other_field": 123}, _make_drop(-5.0)]
        ddl = compute_ddl(10e9, drops)
        assert ddl == pytest.approx(10e9 * 0.05)


# ---------------------------------------------------------------------------
# predict_settlement tests
# ---------------------------------------------------------------------------


class TestPredictSettlement:
    """Test DDL-based settlement prediction."""

    def test_none_market_cap_returns_none(self) -> None:
        result = predict_settlement(
            None, [_make_drop(-10.0)], NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is None

    def test_no_drops_returns_none_for_fallback(self) -> None:
        """Empty stock drops signals fallback to tier model."""
        result = predict_settlement(
            10e9, [], NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is None

    def test_produces_severity_scenarios(self) -> None:
        drops = [_make_drop(-20.0)]
        result = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        assert isinstance(result, SeverityScenarios)
        assert len(result.scenarios) == 4
        assert result.market_cap == 10e9

    def test_ddl_amount_populated(self) -> None:
        drops = [_make_drop(-20.0)]
        result = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        for scenario in result.scenarios:
            assert scenario.ddl_amount > 0

    def test_scenario_labels(self) -> None:
        drops = [_make_drop(-10.0)]
        result = predict_settlement(
            5e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        labels = [s.label for s in result.scenarios]
        assert labels == ["favorable", "median", "adverse", "catastrophic"]

    def test_scenario_percentiles(self) -> None:
        drops = [_make_drop(-10.0)]
        result = predict_settlement(
            5e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        pcts = [s.percentile for s in result.scenarios]
        assert pcts == [25, 50, 75, 95]

    def test_scenario_spread_matches_config(self) -> None:
        """Scenarios follow spread factors: 0.5x, 1.0x, 2.0x, 4.0x."""
        drops = [_make_drop(-20.0)]
        result = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        # DDL = 10e9 * 0.20 = 2e9
        # Base settlement = 2e9 * 0.01 = 20M
        base = 10e9 * 0.20 * 0.01
        expected_settlements = [base * 0.5, base * 1.0, base * 2.0, base * 4.0]
        for scenario, expected in zip(
            result.scenarios, expected_settlements, strict=True,
        ):
            assert scenario.settlement_estimate == pytest.approx(expected)

    def test_defense_costs_applied(self) -> None:
        drops = [_make_drop(-10.0)]
        result = predict_settlement(
            5e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        defense_pcts = [0.15, 0.20, 0.25, 0.30]
        for scenario, dpct in zip(
            result.scenarios, defense_pcts, strict=True,
        ):
            expected_defense = scenario.settlement_estimate * dpct
            assert scenario.defense_cost_estimate == pytest.approx(expected_defense)

    def test_total_exposure_is_sum(self) -> None:
        drops = [_make_drop(-15.0)]
        result = predict_settlement(
            8e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        for scenario in result.scenarios:
            expected_total = (
                scenario.settlement_estimate + scenario.defense_cost_estimate
            )
            assert scenario.total_exposure == pytest.approx(expected_total)

    def test_case_characteristics_increase_settlement(self) -> None:
        """Activating multipliers should increase settlement estimates."""
        drops = [_make_drop(-20.0)]
        result_base = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        result_with_chars = predict_settlement(
            10e9, drops, SOME_CHARS, CALIBRATION_CONFIG,
        )
        assert result_base is not None
        assert result_with_chars is not None
        # accounting_fraud=2.0x, insider_selling=1.3x => combined 2.6x
        for base_s, char_s in zip(
            result_base.scenarios, result_with_chars.scenarios, strict=True,
        ):
            assert char_s.settlement_estimate > base_s.settlement_estimate
            ratio = char_s.settlement_estimate / base_s.settlement_estimate
            assert ratio == pytest.approx(2.0 * 1.3)

    def test_decline_scenarios_present(self) -> None:
        drops = [_make_drop(-10.0)]
        result = predict_settlement(
            5e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert result is not None
        assert "10%" in result.decline_scenarios
        assert "20%" in result.decline_scenarios
        assert "30%" in result.decline_scenarios


# ---------------------------------------------------------------------------
# detect_case_characteristics tests
# ---------------------------------------------------------------------------


class TestDetectCaseCharacteristics:
    """Test case characteristic detection from mock state."""

    def test_empty_state_returns_all_false(self) -> None:
        state = MagicMock()
        state.analysis = None
        state.extracted = None
        state.scoring = None
        chars = detect_case_characteristics(state)
        assert all(v is False for v in chars.values())
        assert len(chars) == 10

    def test_crf01_triggers_accounting_fraud_and_restatement(self) -> None:
        state = MagicMock()
        state.analysis = MagicMock()
        state.analysis.signal_results = {"CRF-01": {"triggered": True}}
        state.extracted = None
        chars = detect_case_characteristics(state)
        assert chars["accounting_fraud"] is True
        assert chars["restatement"] is True

    def test_crf02_triggers_sec_investigation(self) -> None:
        state = MagicMock()
        state.analysis = MagicMock()
        state.analysis.signal_results = {"CRF-02": {"triggered": True}}
        state.extracted = None
        chars = detect_case_characteristics(state)
        assert chars["sec_investigation"] is True

    def test_net_selling_triggers_insider_selling(self) -> None:
        state = MagicMock()
        state.analysis = MagicMock()
        state.analysis.signal_results = {}
        state.extracted = MagicMock()
        state.extracted.market = MagicMock()
        state.extracted.market.insider_trading = MagicMock()
        net_val = MagicMock()
        net_val.value = "NET_SELLING"
        state.extracted.market.insider_trading.net_buying_selling = net_val
        state.extracted.market.insider_trading.cluster_events = []
        state.extracted.governance = None
        state.extracted.financials = None
        state.extracted.litigation = None
        chars = detect_case_characteristics(state)
        assert chars["insider_selling"] is True

    def test_going_concern_detected(self) -> None:
        state = MagicMock()
        state.analysis = MagicMock()
        state.analysis.signal_results = {}
        state.extracted = MagicMock()
        state.extracted.market = None
        state.extracted.governance = None
        state.extracted.litigation = None
        state.extracted.financials = MagicMock()
        gc = MagicMock()
        gc.value = True
        state.extracted.financials.audit = MagicMock()
        state.extracted.financials.audit.going_concern = gc
        chars = detect_case_characteristics(state)
        assert chars["going_concern"] is True


# ---------------------------------------------------------------------------
# characterize_tower_risk tests
# ---------------------------------------------------------------------------


class TestCharacterizeTowerRisk:
    """Test per-layer risk characterization."""

    def test_none_scenarios_returns_empty(self) -> None:
        result = characterize_tower_risk(None, ACTUARIAL_CONFIG)
        assert result == {}

    def test_empty_scenarios_returns_empty(self) -> None:
        scenarios = SeverityScenarios(market_cap=10e9, scenarios=[])
        result = characterize_tower_risk(scenarios, ACTUARIAL_CONFIG)
        assert result == {}

    def test_produces_per_layer_assessments(self) -> None:
        drops = [_make_drop(-20.0)]
        scenarios = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        result = characterize_tower_risk(scenarios, ACTUARIAL_CONFIG)
        assert "primary" in result
        assert "low_excess" in result
        assert "mid_excess" in result
        assert "high_excess" in result

    def test_primary_has_highest_loss_share(self) -> None:
        drops = [_make_drop(-20.0)]
        scenarios = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        result = characterize_tower_risk(scenarios, ACTUARIAL_CONFIG)
        primary_share = result["primary"]["expected_loss_share_pct"]
        for layer_type in ["low_excess", "mid_excess", "high_excess"]:
            assert primary_share > result[layer_type]["expected_loss_share_pct"]

    def test_shares_sum_to_100(self) -> None:
        drops = [_make_drop(-15.0)]
        scenarios = predict_settlement(
            5e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        result = characterize_tower_risk(scenarios, ACTUARIAL_CONFIG)
        total = sum(v["expected_loss_share_pct"] for v in result.values())
        assert total == pytest.approx(100.0, abs=0.5)

    def test_risk_characterization_strings(self) -> None:
        drops = [_make_drop(-10.0)]
        scenarios = predict_settlement(
            8e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        result = characterize_tower_risk(scenarios, ACTUARIAL_CONFIG)
        for layer_type in result:
            assert "expected loss exposure" in result[layer_type]["risk_characterization"]

    def test_expected_loss_amount_present(self) -> None:
        drops = [_make_drop(-20.0)]
        scenarios = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        result = characterize_tower_risk(scenarios, ACTUARIAL_CONFIG)
        for layer_data in result.values():
            assert "expected_loss_amount" in layer_data
            assert layer_data["expected_loss_amount"] >= 0


# ---------------------------------------------------------------------------
# Actuarial compatibility test
# ---------------------------------------------------------------------------


class TestActuarialCompatibility:
    """Verify output is compatible with actuarial_model.compute_expected_loss()."""

    def test_output_compatible_with_actuarial(self) -> None:
        """predict_settlement output works with compute_expected_loss."""
        from do_uw.stages.score.actuarial_model import compute_expected_loss

        drops = [_make_drop(-20.0)]
        scenarios = predict_settlement(
            10e9, drops, NO_CHARS, CALIBRATION_CONFIG,
        )
        assert scenarios is not None

        el = compute_expected_loss(
            filing_probability_pct=5.0,
            severity_scenarios=scenarios,
            case_type="standard_sca",
            actuarial_config=ACTUARIAL_CONFIG,
        )
        assert el.has_data is True
        assert el.total_expected_loss > 0
        assert len(el.scenario_losses) == 4
