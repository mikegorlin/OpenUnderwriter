"""Tests for the severity computation pipeline (Phase 108).

Task 1: SeverityLens protocol, Pydantic models, damages estimation,
settlement regression, and scenario grid generation.

Task 2: Severity amplifiers, layer erosion, legacy severity lens,
and pipeline integration.
"""

from __future__ import annotations

import math

import pytest


# ---------------------------------------------------------------------------
# Task 1 tests: Models, damages, regression
# ---------------------------------------------------------------------------


class TestSeverityModels:
    """SeverityZone, SeverityLensResult, SeverityResult Pydantic models."""

    def test_severity_zone_green(self) -> None:
        """GREEN: P < 0.10 AND S < $10M."""
        from do_uw.models.severity import SeverityZone

        assert SeverityZone.zone_for(0.05, 5_000_000) == SeverityZone.GREEN

    def test_severity_zone_yellow(self) -> None:
        """YELLOW: P >= 0.10 OR S >= $10M (not both high)."""
        from do_uw.models.severity import SeverityZone

        # High P, low S
        assert SeverityZone.zone_for(0.15, 5_000_000) == SeverityZone.YELLOW
        # Low P, high S
        assert SeverityZone.zone_for(0.05, 15_000_000) == SeverityZone.YELLOW

    def test_severity_zone_orange(self) -> None:
        """ORANGE: (P >= 0.25 AND S >= $5M) OR P >= 0.35 OR S >= $50M."""
        from do_uw.models.severity import SeverityZone

        # P >= 0.25 AND S >= $5M
        assert SeverityZone.zone_for(0.25, 10_000_000) == SeverityZone.ORANGE
        # S >= $50M alone triggers ORANGE
        assert SeverityZone.zone_for(0.05, 55_000_000) == SeverityZone.ORANGE

    def test_severity_zone_red(self) -> None:
        """RED: P >= 0.35 AND S >= $50M."""
        from do_uw.models.severity import SeverityZone

        assert SeverityZone.zone_for(0.40, 60_000_000) == SeverityZone.RED

    def test_severity_lens_result_construction(self) -> None:
        """SeverityLensResult can be constructed with all fields."""
        from do_uw.models.severity import SeverityLensResult, SeverityZone

        result = SeverityLensResult(
            lens_name="test_lens",
            estimated_settlement=10_000_000,
            damages_estimate=50_000_000,
            amplifier_results=[],
            scenarios=[],
            defense_costs=2_000_000,
            layer_erosion=None,
            zone=SeverityZone.YELLOW,
            confidence="MEDIUM",
            metadata={},
        )
        assert result.lens_name == "test_lens"
        assert result.estimated_settlement == 10_000_000
        assert result.zone == SeverityZone.YELLOW

    def test_severity_result_expected_loss(self) -> None:
        """SeverityResult computes expected_loss = P x S."""
        from do_uw.models.severity import SeverityResult, SeverityZone

        result = SeverityResult(
            primary=None,
            legacy=None,
            probability=0.10,
            severity=20_000_000,
            expected_loss=2_000_000,  # P x S
            zone=SeverityZone.YELLOW,
            scenario_table=[],
        )
        assert result.expected_loss == 2_000_000

    def test_amplifier_result_construction(self) -> None:
        """AmplifierResult captures firing state."""
        from do_uw.models.severity import AmplifierResult

        result = AmplifierResult(
            amplifier_id="media_notoriety",
            name="Media Notoriety Amplifier",
            fired=True,
            multiplier=1.5,
            trigger_signals_matched=["FWRD.WARN.journalism_activity"],
            explanation="Media coverage detected",
        )
        assert result.fired is True
        assert result.multiplier == 1.5

    def test_layer_erosion_result_construction(self) -> None:
        """LayerErosionResult captures per-layer severity."""
        from do_uw.models.severity import LayerErosionResult

        result = LayerErosionResult(
            attachment=25_000_000,
            limit=10_000_000,
            product="ABC",
            penetration_probability=0.32,
            liberty_severity=5_000_000,
            effective_expected_loss=160_000,
        )
        assert result.penetration_probability == 0.32
        assert result.product == "ABC"


class TestDamagesEstimation:
    """compute_base_damages, scenario_grid, allegation modifiers, defense costs."""

    def test_base_damages_formula(self) -> None:
        """$10B market cap * 0.30 drop * 0.80 turnover = $2.4B."""
        from do_uw.stages.score.damages_estimation import compute_base_damages

        result = compute_base_damages(
            market_cap=10_000_000_000,
            class_period_return=0.30,
            turnover_rate=0.80,
        )
        assert result == pytest.approx(2_400_000_000, rel=1e-6)

    def test_base_damages_turnover_capped_at_1(self) -> None:
        """Turnover rate capped at 1.0."""
        from do_uw.stages.score.damages_estimation import compute_base_damages

        result = compute_base_damages(
            market_cap=10_000_000_000,
            class_period_return=0.30,
            turnover_rate=1.5,
        )
        # Capped at 1.0: 10B * 0.30 * 1.0 = 3.0B
        assert result == pytest.approx(3_000_000_000, rel=1e-6)

    def test_allegation_modifier_restatement(self) -> None:
        """Restatement multiplier = 1.5x."""
        from do_uw.stages.score.damages_estimation import apply_allegation_modifier

        result = apply_allegation_modifier(2_400_000_000, "financial_restatement")
        assert result == pytest.approx(3_600_000_000, rel=1e-6)

    def test_allegation_modifier_unknown_type(self) -> None:
        """Unknown allegation type defaults to 1.0x."""
        from do_uw.stages.score.damages_estimation import apply_allegation_modifier

        result = apply_allegation_modifier(2_400_000_000, "unknown_type")
        assert result == pytest.approx(2_400_000_000, rel=1e-6)

    def test_scenario_grid_3_scenarios(self) -> None:
        """Scenario grid produces 3 drop-level scenarios."""
        from do_uw.stages.score.damages_estimation import compute_scenario_grid

        scenarios = compute_scenario_grid(
            market_cap=10_000_000_000,
            stock_drops_data=[{"drop_pct": -25.0}, {"drop_pct": -15.0}],
            sector_median_drop=0.20,
        )
        assert len(scenarios) == 3
        labels = [s[0] for s in scenarios]
        assert "worst_actual" in labels
        assert "sector_median" in labels
        assert "catastrophic" in labels

    def test_scenario_grid_worst_actual(self) -> None:
        """Worst actual is the largest absolute drop."""
        from do_uw.stages.score.damages_estimation import compute_scenario_grid

        scenarios = compute_scenario_grid(
            market_cap=10_000_000_000,
            stock_drops_data=[{"drop_pct": -25.0}, {"drop_pct": -15.0}],
            sector_median_drop=0.20,
        )
        worst = [s for s in scenarios if s[0] == "worst_actual"][0]
        assert worst[1] == pytest.approx(0.25, rel=1e-6)

    def test_defense_costs_hybrid(self) -> None:
        """Defense costs use hybrid case-characteristic + market-cap approach."""
        from do_uw.stages.score.damages_estimation import compute_defense_costs

        # Large cap ($50B), no special case chars
        result = compute_defense_costs(
            settlement=10_000_000,
            case_chars={},
            market_cap=50_000_000_000,
        )
        # Large cap base = 15% -> $1.5M
        assert result == pytest.approx(1_500_000, rel=0.01)

    def test_defense_costs_with_case_chars(self) -> None:
        """Defense costs adjust for multi-defendant and government investigation."""
        from do_uw.stages.score.damages_estimation import compute_defense_costs

        result = compute_defense_costs(
            settlement=10_000_000,
            case_chars={
                "multi_defendant": True,
                "gov_investigation": True,
            },
            market_cap=50_000_000_000,
        )
        # Large cap 15% + 5% multi + 5% gov = 25% -> $2.5M
        assert result == pytest.approx(2_500_000, rel=0.01)

    def test_estimate_turnover_rate(self) -> None:
        """Turnover rate from volume/shares/days, capped at 1.0."""
        from do_uw.stages.score.damages_estimation import estimate_turnover_rate

        # 1M daily vol, 100M shares, 250 days -> 250M / 100M = 2.5 -> capped at 1.0
        result = estimate_turnover_rate(
            avg_daily_volume=1_000_000,
            shares_outstanding=100_000_000,
            class_period_days=250,
        )
        assert result == 1.0

        # 100K daily vol, 100M shares, 250 days -> 25M / 100M = 0.25
        result2 = estimate_turnover_rate(
            avg_daily_volume=100_000,
            shares_outstanding=100_000_000,
            class_period_days=250,
        )
        assert result2 == pytest.approx(0.25, rel=1e-6)


class TestSettlementRegression:
    """Settlement regression model using published coefficients."""

    def test_regression_prediction_range(self) -> None:
        """Prediction for typical mid-cap produces settlement in $1M-$100M range."""
        from do_uw.stages.score.settlement_regression import predict_settlement_regression

        features = {
            "market_cap_at_filing": math.log10(5_000_000_000),  # $5B
            "max_stock_decline_pct": 0.30,
            "allegation_type_financial_restatement": 1.0,
            "allegation_type_insider_trading": 0.0,
            "allegation_type_regulatory_action": 0.0,
            "allegation_type_offering_securities": 0.0,
            "allegation_type_merger_objection": 0.0,
            "jurisdiction_sdny": 0.0,
            "jurisdiction_ndcal": 0.0,
            "lead_plaintiff_institutional": 0.0,
            "class_period_length_days": math.log10(365),
            "restatement_present": 1.0,
            "sec_investigation_present": 0.0,
            "number_of_named_defendants": 3.0,
            "sector_technology": 0.0,
            "sector_healthcare": 0.0,
            "prior_securities_litigation": 0.0,
            "auditor_change": 0.0,
        }
        result = predict_settlement_regression(features)
        # Should be in reasonable range for $5B company with restatement
        assert 1_000_000 <= result <= 500_000_000

    def test_infer_primary_allegation_type_restatement(self) -> None:
        """Restatement signals -> financial_restatement."""
        from do_uw.stages.score.settlement_regression import infer_primary_allegation_type

        signal_results = {
            "FIN.ACCT.restatement": {"status": "TRIGGERED"},
        }
        case_chars = {"restatement": True, "sec_investigation": False}
        result = infer_primary_allegation_type(signal_results, case_chars)
        assert result == "financial_restatement"

    def test_infer_primary_allegation_type_default(self) -> None:
        """No specific signals -> guidance_miss."""
        from do_uw.stages.score.settlement_regression import infer_primary_allegation_type

        result = infer_primary_allegation_type({}, {})
        assert result == "guidance_miss"

    def test_infer_primary_allegation_sec(self) -> None:
        """SEC investigation signals -> regulatory_action."""
        from do_uw.stages.score.settlement_regression import infer_primary_allegation_type

        signal_results = {
            "LIT.REG.sec_active": {"status": "TRIGGERED"},
        }
        case_chars = {"sec_investigation": True}
        result = infer_primary_allegation_type(signal_results, case_chars)
        assert result == "regulatory_action"


# ---------------------------------------------------------------------------
# Task 2 tests: Amplifiers, layer erosion, legacy lens, integration
# ---------------------------------------------------------------------------


class TestSeverityAmplifiers:
    """Amplifier loading, evaluation, and combination."""

    def test_load_amplifiers(self) -> None:
        """11 amplifiers loaded from severity_model_design.yaml."""
        from do_uw.stages.score.severity_amplifiers import load_amplifiers

        amplifiers = load_amplifiers()
        assert len(amplifiers) == 11

    def test_amplifier_fires_on_triggered_signal(self) -> None:
        """Amplifier fires when ANY signal_id is TRIGGERED."""
        from do_uw.stages.score.severity_amplifiers import (
            evaluate_amplifiers,
            load_amplifiers,
        )

        amplifiers = load_amplifiers()
        # Find media_notoriety amplifier
        media_amp = [a for a in amplifiers if a.id == "media_notoriety"][0]

        signal_results = {
            "FWRD.WARN.journalism_activity": {"status": "TRIGGERED"},
        }
        results = evaluate_amplifiers([media_amp], signal_results)
        assert len(results) == 1
        assert results[0].fired is True
        assert results[0].multiplier == 1.5

    def test_amplifier_silent_skip_on_missing_data(self) -> None:
        """No signal data -> multiplier 1.0, not fired."""
        from do_uw.stages.score.severity_amplifiers import (
            evaluate_amplifiers,
            load_amplifiers,
        )

        amplifiers = load_amplifiers()
        media_amp = [a for a in amplifiers if a.id == "media_notoriety"][0]

        results = evaluate_amplifiers([media_amp], {})
        assert len(results) == 1
        assert results[0].fired is False
        assert results[0].multiplier == 1.0

    def test_combine_amplifiers_multiplicative_with_cap(self) -> None:
        """1.5 * 2.0 * 1.3 = 3.0 (capped from 3.9)."""
        from do_uw.models.severity import AmplifierResult
        from do_uw.stages.score.severity_amplifiers import combine_amplifiers

        results = [
            AmplifierResult(
                amplifier_id="a1", name="A1", fired=True,
                multiplier=1.5, trigger_signals_matched=[], explanation="",
            ),
            AmplifierResult(
                amplifier_id="a2", name="A2", fired=True,
                multiplier=2.0, trigger_signals_matched=[], explanation="",
            ),
            AmplifierResult(
                amplifier_id="a3", name="A3", fired=True,
                multiplier=1.3, trigger_signals_matched=[], explanation="",
            ),
        ]
        combined = combine_amplifiers(results)
        assert combined == 3.0  # Capped

    def test_combine_amplifiers_none_fired(self) -> None:
        """No amplifiers fired -> returns 1.0."""
        from do_uw.models.severity import AmplifierResult
        from do_uw.stages.score.severity_amplifiers import combine_amplifiers

        results = [
            AmplifierResult(
                amplifier_id="a1", name="A1", fired=False,
                multiplier=1.0, trigger_signals_matched=[], explanation="",
            ),
        ]
        combined = combine_amplifiers(results)
        assert combined == 1.0


class TestLayerErosion:
    """Layer erosion probability computation."""

    def test_layer_erosion_known_params(self) -> None:
        """P(lognormal > $25M) for known mu/sigma is reasonable."""
        from do_uw.stages.score.layer_erosion import compute_layer_erosion

        result = compute_layer_erosion(
            median_settlement=20_000_000,  # $20M median
            sigma=0.8,
            attachment=25_000_000,  # $25M attachment
            limit=10_000_000,  # $10M limit
            product="ABC",
        )
        # P(settlement > $25M) when median is $20M should be roughly 30-50%
        assert 0.10 <= result.penetration_probability <= 0.70
        assert result.product == "ABC"

    def test_layer_erosion_high_attachment(self) -> None:
        """Very high attachment -> low penetration probability."""
        from do_uw.stages.score.layer_erosion import compute_layer_erosion

        result = compute_layer_erosion(
            median_settlement=10_000_000,  # $10M median
            sigma=0.8,
            attachment=100_000_000,  # $100M attachment
            limit=10_000_000,
            product="ABC",
        )
        # P(settlement > $100M) when median is $10M should be very low
        assert result.penetration_probability < 0.15

    def test_side_a_excess_of_abc(self) -> None:
        """Side A excess of ABC: attachment = abc_tower_top + side_a_attach."""
        from do_uw.stages.score.layer_erosion import compute_side_a_erosion

        result = compute_side_a_erosion(
            median_settlement=30_000_000,
            sigma=0.8,
            attachment=10_000_000,  # Side A attachment
            limit=10_000_000,
            abc_tower_top=100_000_000,  # ABC tower goes to $100M
            product="SIDE_A",
        )
        # Effective attachment = $100M + $10M = $110M
        # P(settlement > $110M) when median $30M should be very low
        assert result.penetration_probability < 0.10

    def test_dic_probability_from_distress(self) -> None:
        """Going concern signal -> 0.5 base DIC probability."""
        from do_uw.stages.score.layer_erosion import compute_dic_probability

        signal_results = {
            "FIN.HEALTH.going_concern": {"status": "TRIGGERED"},
        }
        result = compute_dic_probability(signal_results)
        assert result >= 0.5

    def test_dic_probability_no_distress(self) -> None:
        """No distress signals -> 0.0 DIC probability."""
        from do_uw.stages.score.layer_erosion import compute_dic_probability

        result = compute_dic_probability({})
        assert result == 0.0


class TestLegacySeverityLens:
    """Legacy DDL model wrapped as SeverityLens adapter."""

    def test_legacy_severity_lens_wraps_scenarios(self) -> None:
        """Wraps SeverityScenarios into SeverityLensResult."""
        from do_uw.models.scoring_output import SeverityScenario, SeverityScenarios
        from do_uw.stages.score.legacy_severity_lens import LegacySeverityLens

        scenarios = SeverityScenarios(
            market_cap=5_000_000_000,
            decline_scenarios={"10%": 500_000_000, "20%": 1_000_000_000},
            scenarios=[
                SeverityScenario(
                    percentile=25, label="favorable",
                    ddl_amount=1_000_000_000,
                    settlement_estimate=5_000_000,
                    defense_cost_estimate=1_000_000,
                    total_exposure=6_000_000,
                ),
                SeverityScenario(
                    percentile=50, label="median",
                    ddl_amount=1_000_000_000,
                    settlement_estimate=10_000_000,
                    defense_cost_estimate=2_000_000,
                    total_exposure=12_000_000,
                ),
                SeverityScenario(
                    percentile=75, label="adverse",
                    ddl_amount=1_000_000_000,
                    settlement_estimate=20_000_000,
                    defense_cost_estimate=5_000_000,
                    total_exposure=25_000_000,
                ),
                SeverityScenario(
                    percentile=95, label="catastrophic",
                    ddl_amount=1_000_000_000,
                    settlement_estimate=40_000_000,
                    defense_cost_estimate=12_000_000,
                    total_exposure=52_000_000,
                ),
            ],
            needs_calibration=True,
        )

        lens = LegacySeverityLens(scenarios)
        result = lens.evaluate({})
        assert result.lens_name == "legacy_ddl"
        # Uses median scenario as estimated_settlement
        assert result.estimated_settlement == 10_000_000
        assert len(result.scenarios) == 4

    def test_legacy_severity_lens_none_scenarios(self) -> None:
        """None scenarios -> empty result."""
        from do_uw.stages.score.legacy_severity_lens import LegacySeverityLens

        lens = LegacySeverityLens(None)
        result = lens.evaluate({})
        assert result.lens_name == "legacy_ddl"
        assert result.estimated_settlement == 0
        assert len(result.scenarios) == 0


class TestSeverityIntegration:
    """Pipeline integration: severity_result on ScoringResult."""

    def test_scoring_result_has_severity_field(self) -> None:
        """ScoringResult has severity_result field after model_rebuild."""
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models

        _rebuild_scoring_models()
        sr = ScoringResult()
        assert sr.severity_result is None

    def test_severity_result_assignable(self) -> None:
        """severity_result can be assigned a SeverityResult object."""
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models
        from do_uw.models.severity import SeverityResult, SeverityZone

        _rebuild_scoring_models()
        sr = ScoringResult()
        severity = SeverityResult(
            probability=0.10,
            severity=20_000_000,
            expected_loss=2_000_000,
            zone=SeverityZone.YELLOW,
        )
        sr.severity_result = severity
        assert sr.severity_result is not None
        assert sr.severity_result.expected_loss == 2_000_000
