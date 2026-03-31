"""Tests for H/A/E multiplicative scoring model.

Covers: scoring lens protocol, Pydantic models, composite computation,
multiplicative model, CRF ELECTRE discordance, tier assignment, and
Liberty calibration.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------
# Task 1: Scoring lens protocol + Pydantic models
# ---------------------------------------------------------------


class TestHAETier:
    """HAETier enum ordering and comparison."""

    def test_tier_values(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        assert HAETier.PREFERRED == "PREFERRED"
        assert HAETier.STANDARD == "STANDARD"
        assert HAETier.ELEVATED == "ELEVATED"
        assert HAETier.HIGH_RISK == "HIGH_RISK"
        assert HAETier.PROHIBITED == "PROHIBITED"

    def test_tier_count(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        assert len(HAETier) == 5

    def test_tier_ordering_preferred_less_than_prohibited(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        assert HAETier.PREFERRED < HAETier.PROHIBITED

    def test_tier_ordering_standard_less_than_high_risk(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        assert HAETier.STANDARD < HAETier.HIGH_RISK

    def test_tier_ordering_elevated_less_than_prohibited(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        assert HAETier.ELEVATED < HAETier.PROHIBITED

    def test_tier_max_returns_most_restrictive(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        result = max(HAETier.PREFERRED, HAETier.ELEVATED, HAETier.STANDARD)
        assert result == HAETier.ELEVATED

    def test_tier_ge_operator(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        assert HAETier.PROHIBITED >= HAETier.HIGH_RISK
        assert HAETier.STANDARD >= HAETier.STANDARD

    def test_tier_le_operator(self) -> None:
        from do_uw.stages.score.scoring_lens import HAETier

        assert HAETier.PREFERRED <= HAETier.STANDARD
        assert HAETier.ELEVATED <= HAETier.ELEVATED


class TestScoringLensResult:
    """ScoringLensResult Pydantic model construction."""

    def test_construction_all_fields(self) -> None:
        from do_uw.stages.score.scoring_lens import (
            CRFVetoResult,
            HAETier,
            ScoringLensResult,
        )

        result = ScoringLensResult(
            lens_name="hae_multiplicative",
            tier=HAETier.STANDARD,
            composites={"host": 0.3, "agent": 0.2, "environment": 0.1},
            product_score=0.006,
            confidence="HIGH",
            recommendations={
                "pricing_guidance": "Market ROL.",
                "layer_comfort": "Comfortable in most positions.",
                "terms_conditions": "Standard terms.",
                "monitoring_triggers": "Standard monitoring.",
                "referral_criteria": "No referral needed.",
                "communication_pattern": "Professional.",
            },
            crf_vetoes=[],
            tier_source="composite",
            individual_tier=HAETier.STANDARD,
            composite_tier=HAETier.STANDARD,
        )
        assert result.lens_name == "hae_multiplicative"
        assert result.tier == HAETier.STANDARD
        assert result.composites["host"] == 0.3
        assert result.product_score == 0.006
        assert result.confidence == "HIGH"
        assert len(result.recommendations) == 6
        assert result.crf_vetoes == []
        assert result.tier_source == "composite"

    def test_crf_veto_result_construction(self) -> None:
        from do_uw.stages.score.scoring_lens import CRFVetoResult, HAETier

        veto = CRFVetoResult(
            crf_id="CRF-FRAUD",
            condition="Active SEC enforcement action",
            veto_target=HAETier.PROHIBITED,
            signals_matched=["LIT.REG.sec_active"],
            is_active=True,
            time_context="recent",
            claim_status="NO_CLAIM",
        )
        assert veto.crf_id == "CRF-FRAUD"
        assert veto.veto_target == HAETier.PROHIBITED
        assert veto.is_active is True
        assert veto.time_context == "recent"


class TestScoringResultExtension:
    """ScoringResult model extended with hae_result field."""

    def test_hae_result_defaults_to_none(self) -> None:
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models

        _rebuild_scoring_models()
        result = ScoringResult()
        assert result.hae_result is None

    def test_hae_result_accepts_scoring_lens_result(self) -> None:
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models
        from do_uw.stages.score.scoring_lens import (
            HAETier,
            ScoringLensResult,
        )

        _rebuild_scoring_models()

        lens_result = ScoringLensResult(
            lens_name="hae_multiplicative",
            tier=HAETier.PREFERRED,
            composites={"host": 0.0, "agent": 0.0, "environment": 0.0},
            product_score=0.000125,
            confidence="HIGH",
            recommendations={},
            crf_vetoes=[],
            tier_source="composite",
            individual_tier=HAETier.PREFERRED,
            composite_tier=HAETier.PREFERRED,
        )
        result = ScoringResult(hae_result=lens_result)
        assert result.hae_result is not None
        assert result.hae_result.tier == HAETier.PREFERRED


class TestScoringLensProtocol:
    """ScoringLens Protocol compliance."""

    def test_protocol_has_evaluate_method(self) -> None:
        from do_uw.stages.score.scoring_lens import ScoringLens

        assert hasattr(ScoringLens, "evaluate")


# ---------------------------------------------------------------
# Task 2: H/A/E composite computation + multiplicative model
# ---------------------------------------------------------------


class TestSignalScore:
    """Signal evaluation to numeric score mapping."""

    def test_red_triggered_returns_1(self) -> None:
        from do_uw.stages.score.hae_scoring import _signal_score

        assert _signal_score("TRIGGERED", "red") == 1.0

    def test_yellow_triggered_returns_half(self) -> None:
        from do_uw.stages.score.hae_scoring import _signal_score

        assert _signal_score("TRIGGERED", "yellow") == 0.5

    def test_clear_returns_0(self) -> None:
        from do_uw.stages.score.hae_scoring import _signal_score

        assert _signal_score("CLEAR", "") == 0.0

    def test_skipped_returns_none(self) -> None:
        from do_uw.stages.score.hae_scoring import _signal_score

        assert _signal_score("SKIPPED", "") is None

    def test_info_returns_none(self) -> None:
        from do_uw.stages.score.hae_scoring import _signal_score

        assert _signal_score("INFO", "") is None


class TestSubcategoryScore:
    """Subcategory score computation from signal results."""

    def test_all_clear_returns_zero(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_subcategory_score

        signal_results = {
            "SIG.A": {"status": "CLEAR", "threshold_level": ""},
            "SIG.B": {"status": "CLEAR", "threshold_level": ""},
        }
        rap_mapping = {
            "SIG.A": ("host", "host.identity"),
            "SIG.B": ("host", "host.identity"),
        }
        result = compute_subcategory_score(
            signal_results, "host.identity", rap_mapping, {}
        )
        assert result == 0.0

    def test_all_skipped_returns_none(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_subcategory_score

        signal_results = {
            "SIG.A": {"status": "SKIPPED", "threshold_level": ""},
            "SIG.B": {"status": "SKIPPED", "threshold_level": ""},
        }
        rap_mapping = {
            "SIG.A": ("host", "host.identity"),
            "SIG.B": ("host", "host.identity"),
        }
        result = compute_subcategory_score(
            signal_results, "host.identity", rap_mapping, {}
        )
        assert result is None

    def test_mixed_signals_weighted_average(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_subcategory_score

        signal_results = {
            "SIG.A": {"status": "TRIGGERED", "threshold_level": "red"},
            "SIG.B": {"status": "CLEAR", "threshold_level": ""},
        }
        rap_mapping = {
            "SIG.A": ("host", "host.identity"),
            "SIG.B": ("host", "host.identity"),
        }
        # Equal weight: (1.0 + 0.0) / 2 = 0.5
        result = compute_subcategory_score(
            signal_results, "host.identity", rap_mapping, {}
        )
        assert result == pytest.approx(0.5)

    def test_crf_signals_get_3x_weight(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_subcategory_score

        signal_results = {
            "SIG.A": {"status": "TRIGGERED", "threshold_level": "red"},
            "SIG.B": {"status": "CLEAR", "threshold_level": ""},
        }
        rap_mapping = {
            "SIG.A": ("host", "host.identity"),
            "SIG.B": ("host", "host.identity"),
        }
        brain_signals = {
            "SIG.A": {"id": "SIG.A", "critical_red_flag": True},
        }
        # SIG.A: weight=3.0, score=1.0 -> 3.0
        # SIG.B: weight=1.0, score=0.0 -> 0.0
        # total: 3.0 / 4.0 = 0.75
        result = compute_subcategory_score(
            signal_results, "host.identity", rap_mapping, brain_signals
        )
        assert result == pytest.approx(0.75)

    def test_missing_signals_excluded(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_subcategory_score

        # SIG.A is in mapping but NOT in signal_results
        signal_results = {
            "SIG.B": {"status": "TRIGGERED", "threshold_level": "red"},
        }
        rap_mapping = {
            "SIG.A": ("host", "host.identity"),
            "SIG.B": ("host", "host.identity"),
        }
        result = compute_subcategory_score(
            signal_results, "host.identity", rap_mapping, {}
        )
        assert result == pytest.approx(1.0)


class TestCategoryComposite:
    """Category composite computation from subcategory scores."""

    def test_excludes_null_subcategories(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_category_composite

        subcategory_scores: dict[str, float | None] = {
            "host.identity": 0.8,
            "host.structure": None,
            "host.financials": 0.2,
        }
        weights = {
            "host.identity": {"weight": 0.25},
            "host.structure": {"weight": 0.15},
            "host.financials": {"weight": 0.20},
        }
        # Only host.identity and host.financials contribute
        # (0.8*0.25 + 0.2*0.20) / (0.25 + 0.20) = 0.24 / 0.45
        result = compute_category_composite(subcategory_scores, weights)
        expected = (0.8 * 0.25 + 0.2 * 0.20) / (0.25 + 0.20)
        assert result == pytest.approx(expected, abs=1e-6)

    def test_all_null_returns_zero(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_category_composite

        subcategory_scores: dict[str, float | None] = {
            "host.identity": None,
            "host.structure": None,
        }
        weights = {
            "host.identity": {"weight": 0.25},
            "host.structure": {"weight": 0.15},
        }
        result = compute_category_composite(subcategory_scores, weights)
        assert result == 0.0


class TestMultiplicativeProduct:
    """P = H x A x E product with floor."""

    def test_all_low_near_zero(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_multiplicative_product

        # H=A=E=0.0 -> floor applied -> 0.05^3
        result = compute_multiplicative_product(0.0, 0.0, 0.0)
        assert result == pytest.approx(0.05**3, abs=1e-6)

    def test_floor_cubed(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_multiplicative_product

        result = compute_multiplicative_product(0.0, 0.0, 0.0)
        assert result == pytest.approx(0.000125, abs=1e-6)

    def test_all_high_0_8(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_multiplicative_product

        result = compute_multiplicative_product(0.8, 0.8, 0.8)
        assert result == pytest.approx(0.512, abs=1e-6)

    def test_mixed_scores(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_multiplicative_product

        # H=0.8, A=0.8, E=0.2 -> 0.128
        result = compute_multiplicative_product(0.8, 0.8, 0.2)
        assert result == pytest.approx(0.128, abs=1e-6)

    def test_floor_prevents_zero_domination(self) -> None:
        from do_uw.stages.score.hae_scoring import compute_multiplicative_product

        # H=0.8, A=0.8, E=0.0 -> max(0.0, 0.05)=0.05
        # 0.8*0.8*0.05 = 0.032
        result = compute_multiplicative_product(0.8, 0.8, 0.0)
        assert result == pytest.approx(0.032, abs=1e-6)


class TestTierFromP:
    """Tier classification from composite P score."""

    def test_preferred(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_p
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_p(0.005) == HAETier.PREFERRED

    def test_standard(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_p
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_p(0.05) == HAETier.STANDARD

    def test_elevated(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_p
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_p(0.12) == HAETier.ELEVATED

    def test_high_risk(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_p
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_p(0.35) == HAETier.HIGH_RISK

    def test_prohibited(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_p
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_p(0.6) == HAETier.PROHIBITED

    def test_boundary_0_01(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_p
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_p(0.01) == HAETier.STANDARD

    def test_boundary_1_0(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_p
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_p(1.0) == HAETier.PROHIBITED


class TestTierFromIndividual:
    """Tier classification from individual dimension criteria."""

    def test_preferred_all_low(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_individual
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_individual(0.2, 0.15, 0.25) == HAETier.PREFERRED

    def test_standard_moderate(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_individual
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_individual(0.4, 0.35, 0.45) == HAETier.STANDARD

    def test_elevated_any_above_50(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_individual
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_individual(0.55, 0.1, 0.1) == HAETier.ELEVATED

    def test_high_risk_any_above_70(self) -> None:
        from do_uw.stages.score.hae_scoring import classify_tier_from_individual
        from do_uw.stages.score.scoring_lens import HAETier

        assert classify_tier_from_individual(0.75, 0.1, 0.1) == HAETier.HIGH_RISK

    def test_individual_override_high_host(self) -> None:
        """High single dimension should elevate tier even if P is low."""
        from do_uw.stages.score.hae_scoring import classify_tier_from_individual
        from do_uw.stages.score.scoring_lens import HAETier

        # H=0.75 -> HIGH_RISK from individual criteria
        result = classify_tier_from_individual(0.75, 0.1, 0.1)
        assert result == HAETier.HIGH_RISK


class TestLibertyCalibration:
    """Liberty calibration adjusts composites by attachment and product."""

    def test_high_attachment_increases_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_scoring

        # Mock the scoring model config
        mock_config = {
            "liberty_calibration": {
                "attachment_weight_adjustments": {
                    "high_attachment": {
                        "host_weight_multiplier": 1.30,
                        "agent_weight_multiplier": 0.80,
                        "environment_weight_multiplier": 0.90,
                    },
                    "mid_attachment": {
                        "host_weight_multiplier": 1.15,
                        "agent_weight_multiplier": 0.95,
                        "environment_weight_multiplier": 0.90,
                    },
                    "low_attachment": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                },
                "product_weight_adjustments": {
                    "ABC": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                    "Side_A": {
                        "host_weight_multiplier": 0.85,
                        "agent_weight_multiplier": 1.25,
                        "environment_weight_multiplier": 0.90,
                    },
                },
            }
        }
        monkeypatch.setattr(hae_scoring, "_scoring_model_cache", mock_config)

        h, a, e = hae_scoring.apply_liberty_calibration(
            0.5, 0.5, 0.5, attachment=60.0, product="ABC"
        )
        # high attachment: host * 1.30 = 0.65, agent * 0.80 = 0.40, env * 0.90 = 0.45
        assert h == pytest.approx(0.65, abs=1e-2)
        assert a == pytest.approx(0.40, abs=1e-2)
        assert e == pytest.approx(0.45, abs=1e-2)

    def test_side_a_increases_agent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_scoring

        mock_config = {
            "liberty_calibration": {
                "attachment_weight_adjustments": {
                    "high_attachment": {
                        "host_weight_multiplier": 1.30,
                        "agent_weight_multiplier": 0.80,
                        "environment_weight_multiplier": 0.90,
                    },
                    "mid_attachment": {
                        "host_weight_multiplier": 1.15,
                        "agent_weight_multiplier": 0.95,
                        "environment_weight_multiplier": 0.90,
                    },
                    "low_attachment": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                },
                "product_weight_adjustments": {
                    "ABC": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                    "Side_A": {
                        "host_weight_multiplier": 0.85,
                        "agent_weight_multiplier": 1.25,
                        "environment_weight_multiplier": 0.90,
                    },
                },
            }
        }
        monkeypatch.setattr(hae_scoring, "_scoring_model_cache", mock_config)

        h, a, e = hae_scoring.apply_liberty_calibration(
            0.5, 0.5, 0.5, attachment=5.0, product="Side_A"
        )
        # low attachment + Side_A: host * 1.0 * 0.85 = 0.425, agent * 1.0 * 1.25 = 0.625
        assert h == pytest.approx(0.425, abs=1e-2)
        assert a == pytest.approx(0.625, abs=1e-2)

    def test_clamped_to_1(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_scoring

        mock_config = {
            "liberty_calibration": {
                "attachment_weight_adjustments": {
                    "high_attachment": {
                        "host_weight_multiplier": 1.30,
                        "agent_weight_multiplier": 0.80,
                        "environment_weight_multiplier": 0.90,
                    },
                    "mid_attachment": {
                        "host_weight_multiplier": 1.15,
                        "agent_weight_multiplier": 0.95,
                        "environment_weight_multiplier": 0.90,
                    },
                    "low_attachment": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                },
                "product_weight_adjustments": {
                    "ABC": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                    "Side_A": {
                        "host_weight_multiplier": 0.85,
                        "agent_weight_multiplier": 1.25,
                        "environment_weight_multiplier": 0.90,
                    },
                },
            }
        }
        monkeypatch.setattr(hae_scoring, "_scoring_model_cache", mock_config)

        h, a, e = hae_scoring.apply_liberty_calibration(
            0.9, 0.9, 0.9, attachment=60.0, product="ABC"
        )
        # host * 1.30 = 1.17 -> clamped to 1.0
        assert h <= 1.0
        assert a <= 1.0
        assert e <= 1.0


class TestFullLensEvaluate:
    """End-to-end HAEScoringLens.evaluate()."""

    def test_full_lens_all_clear(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_scoring
        from do_uw.stages.score.hae_scoring import HAEScoringLens
        from do_uw.stages.score.scoring_lens import HAETier

        # Mock all config loaders
        mock_scoring_model = {
            "composites": {
                "host_subcategory_weights": {
                    "weights": {
                        "host.identity": {"weight": 0.5},
                        "host.financials": {"weight": 0.5},
                    }
                },
                "agent_subcategory_weights": {
                    "weights": {
                        "agent.financial_conduct": {"weight": 0.5},
                        "agent.executive_conduct": {"weight": 0.5},
                    }
                },
                "environment_subcategory_weights": {
                    "weights": {
                        "environment.market_signals": {"weight": 0.5},
                        "environment.peer_context": {"weight": 0.5},
                    }
                },
            },
            "interaction_model": {"floor_adjustment": {"floor_value": 0.05}},
            "liberty_calibration": {
                "attachment_weight_adjustments": {
                    "low_attachment": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                    "mid_attachment": {
                        "host_weight_multiplier": 1.15,
                        "agent_weight_multiplier": 0.95,
                        "environment_weight_multiplier": 0.90,
                    },
                    "high_attachment": {
                        "host_weight_multiplier": 1.30,
                        "agent_weight_multiplier": 0.80,
                        "environment_weight_multiplier": 0.90,
                    },
                },
                "product_weight_adjustments": {
                    "ABC": {
                        "host_weight_multiplier": 1.0,
                        "agent_weight_multiplier": 1.0,
                        "environment_weight_multiplier": 1.0,
                    },
                },
            },
        }

        mock_decision_framework = {
            "recommendation_outputs": {
                "pricing_guidance": {"by_tier": {"PREFERRED": "ROL discount"}},
                "layer_comfort": {"by_tier": {"PREFERRED": "Comfortable anywhere"}},
                "terms_conditions": {"by_tier": {"PREFERRED": "Standard terms"}},
                "monitoring_triggers": {"by_tier": {"PREFERRED": "Standard monitoring"}},
                "referral_criteria": {"by_tier": {"PREFERRED": "No referral"}},
                "communication_pattern": {"by_tier": {"PREFERRED": "Enthusiastic"}},
            }
        }

        mock_rap_mapping = {
            "SIG.H1": ("host", "host.identity"),
            "SIG.H2": ("host", "host.financials"),
            "SIG.A1": ("agent", "agent.financial_conduct"),
            "SIG.A2": ("agent", "agent.executive_conduct"),
            "SIG.E1": ("environment", "environment.market_signals"),
            "SIG.E2": ("environment", "environment.peer_context"),
        }

        monkeypatch.setattr(hae_scoring, "_scoring_model_cache", mock_scoring_model)
        monkeypatch.setattr(hae_scoring, "_decision_framework_cache", mock_decision_framework)
        monkeypatch.setattr(hae_scoring, "_rap_mapping_cache", mock_rap_mapping)
        monkeypatch.setattr(hae_scoring, "_brain_signals_cache", {})

        signal_results = {
            "SIG.H1": {"status": "CLEAR", "threshold_level": ""},
            "SIG.H2": {"status": "CLEAR", "threshold_level": ""},
            "SIG.A1": {"status": "CLEAR", "threshold_level": ""},
            "SIG.A2": {"status": "CLEAR", "threshold_level": ""},
            "SIG.E1": {"status": "CLEAR", "threshold_level": ""},
            "SIG.E2": {"status": "CLEAR", "threshold_level": ""},
        }

        lens = HAEScoringLens()
        result = lens.evaluate(signal_results)

        assert result.tier == HAETier.PREFERRED
        assert result.composites["host"] == 0.0
        assert result.composites["agent"] == 0.0
        assert result.composites["environment"] == 0.0
        # Floor cubed: 0.05^3 = 0.000125
        assert result.product_score == pytest.approx(0.000125, abs=1e-6)
        assert result.lens_name == "hae_multiplicative"


# ---------------------------------------------------------------
# Task 3: CRF ELECTRE discordance
# ---------------------------------------------------------------

# Helper to build a mock CRF catalog for tests
_MOCK_CRF_CATALOG = [
    {
        "id": "CRF-FRAUD",
        "condition": "Active SEC enforcement",
        "veto_target": "PROHIBITED",
        "signals": ["LIT.REG.sec_active", "LIT.REG.sec_investigation", "LIT.REG.wells_notice"],
    },
    {
        "id": "CRF-RESTATEMENT",
        "condition": "Material restatement",
        "veto_target": "HIGH_RISK",  # Per CONTEXT.md override
        "signals": ["FIN.ACCT.restatement", "FIN.ACCT.restatement_magnitude"],
    },
    {
        "id": "CRF-INSOLVENCY",
        "condition": "Zone of insolvency",
        "veto_target": "PROHIBITED",
        "signals": ["FWRD.WARN.zone_of_insolvency", "FIN.LIQ.cash_burn", "FIN.LIQ.position"],
    },
    {
        "id": "CRF-DOJ",
        "condition": "Active DOJ criminal investigation",
        "veto_target": "PROHIBITED",
        "signals": ["LIT.REG.doj_investigation"],
    },
    {
        "id": "CRF-MULTI",
        "condition": "3+ CRFs active simultaneously",
        "veto_target": "HIGH_RISK",
        "signals": [],
    },
    {
        "id": "CRF-MATERIAL-WEAKNESS",
        "condition": "Material weakness in internal controls",
        "veto_target": "ELEVATED",
        "signals": ["FIN.ACCT.material_weakness", "FIN.ACCT.internal_controls", "GOV.EFFECT.material_weakness"],
    },
]


class TestCRFNoActive:
    """When no CRFs fire, tier is unchanged."""

    def test_no_crf_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import evaluate_crf_discordance
        from do_uw.stages.score.scoring_lens import HAETier

        monkeypatch.setattr(hae_crf, "_crf_catalog_cache", _MOCK_CRF_CATALOG)

        signal_results = {
            "LIT.REG.sec_active": {"status": "CLEAR", "threshold_level": ""},
            "FIN.ACCT.restatement": {"status": "CLEAR", "threshold_level": ""},
        }
        tier, vetoes = evaluate_crf_discordance(signal_results, HAETier.STANDARD)
        assert tier == HAETier.STANDARD
        # Active vetoes should be empty (all evaluated but none active)
        active_vetoes = [v for v in vetoes if v.is_active]
        assert len(active_vetoes) == 0


class TestCRFFraud:
    """CRF-FRAUD veto to PROHIBITED."""

    def test_fraud_crf_recent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import evaluate_crf_discordance
        from do_uw.stages.score.scoring_lens import HAETier

        monkeypatch.setattr(hae_crf, "_crf_catalog_cache", _MOCK_CRF_CATALOG)

        signal_results = {
            "LIT.REG.sec_active": {"status": "TRIGGERED", "threshold_level": "red"},
        }
        tier, vetoes = evaluate_crf_discordance(signal_results, HAETier.PREFERRED)
        assert tier == HAETier.PROHIBITED
        active = [v for v in vetoes if v.is_active]
        assert any(v.crf_id == "CRF-FRAUD" for v in active)


class TestCRFRestatement:
    """CRF-RESTATEMENT veto to HIGH_RISK (per CONTEXT.md)."""

    def test_restatement_crf_recent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import evaluate_crf_discordance
        from do_uw.stages.score.scoring_lens import HAETier

        monkeypatch.setattr(hae_crf, "_crf_catalog_cache", _MOCK_CRF_CATALOG)

        signal_results = {
            "FIN.ACCT.restatement": {"status": "TRIGGERED", "threshold_level": "red"},
        }
        tier, vetoes = evaluate_crf_discordance(signal_results, HAETier.STANDARD)
        assert tier == HAETier.HIGH_RISK


class TestCRFInsolvency:
    """CRF-INSOLVENCY veto to PROHIBITED."""

    def test_insolvency_crf(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import evaluate_crf_discordance
        from do_uw.stages.score.scoring_lens import HAETier

        monkeypatch.setattr(hae_crf, "_crf_catalog_cache", _MOCK_CRF_CATALOG)

        signal_results = {
            "FWRD.WARN.zone_of_insolvency": {"status": "TRIGGERED", "threshold_level": "red"},
        }
        tier, vetoes = evaluate_crf_discordance(signal_results, HAETier.STANDARD)
        assert tier == HAETier.PROHIBITED


class TestCRFMaterialWeakness:
    """CRF-MATERIAL-WEAKNESS veto to ELEVATED."""

    def test_material_weakness_crf(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import evaluate_crf_discordance
        from do_uw.stages.score.scoring_lens import HAETier

        monkeypatch.setattr(hae_crf, "_crf_catalog_cache", _MOCK_CRF_CATALOG)

        signal_results = {
            "FIN.ACCT.material_weakness": {"status": "TRIGGERED", "threshold_level": "red"},
        }
        tier, vetoes = evaluate_crf_discordance(signal_results, HAETier.STANDARD)
        assert tier == HAETier.ELEVATED


class TestCRFMulti:
    """CRF-MULTI fires when 3+ CRFs are active simultaneously."""

    def test_multi_crf_3_active(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import evaluate_crf_discordance
        from do_uw.stages.score.scoring_lens import HAETier

        monkeypatch.setattr(hae_crf, "_crf_catalog_cache", _MOCK_CRF_CATALOG)

        # Trigger 3 different CRFs (fraud + restatement + material weakness)
        signal_results = {
            "LIT.REG.sec_active": {"status": "TRIGGERED", "threshold_level": "red"},
            "FIN.ACCT.restatement": {"status": "TRIGGERED", "threshold_level": "red"},
            "FIN.ACCT.material_weakness": {"status": "TRIGGERED", "threshold_level": "red"},
        }
        tier, vetoes = evaluate_crf_discordance(signal_results, HAETier.STANDARD)
        # FRAUD -> PROHIBITED already, but MULTI should also be active
        active = [v for v in vetoes if v.is_active]
        multi_active = [v for v in active if v.crf_id == "CRF-MULTI"]
        assert len(multi_active) == 1
        # Overall tier driven by FRAUD PROHIBITED
        assert tier == HAETier.PROHIBITED


class TestCRFTimeDecay:
    """Time-aware CRF veto decay."""

    def test_crf_time_decay_aging(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import _adjust_veto_for_time_and_claims
        from do_uw.stages.score.scoring_lens import HAETier

        # Aging + NO_CLAIM: reduce by 1 tier
        result = _adjust_veto_for_time_and_claims(
            HAETier.HIGH_RISK, "aging", "NO_CLAIM"
        )
        assert result == HAETier.ELEVATED

    def test_crf_time_decay_expired_no_claim(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score.hae_crf import _adjust_veto_for_time_and_claims
        from do_uw.stages.score.scoring_lens import HAETier

        # Expired + NO_CLAIM: reduce by 2 tiers
        result = _adjust_veto_for_time_and_claims(
            HAETier.PROHIBITED, "expired", "NO_CLAIM"
        )
        assert result == HAETier.ELEVATED

    def test_crf_claim_filed_no_decay(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score.hae_crf import _adjust_veto_for_time_and_claims
        from do_uw.stages.score.scoring_lens import HAETier

        # Aging + CLAIM_FILED: full veto maintained
        result = _adjust_veto_for_time_and_claims(
            HAETier.HIGH_RISK, "aging", "CLAIM_FILED"
        )
        assert result == HAETier.HIGH_RISK

    def test_crf_resolved_expired(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score.hae_crf import _adjust_veto_for_time_and_claims
        from do_uw.stages.score.scoring_lens import HAETier

        # Expired + CLAIM_RESOLVED: no veto (STANDARD floor)
        result = _adjust_veto_for_time_and_claims(
            HAETier.HIGH_RISK, "expired", "CLAIM_RESOLVED"
        )
        assert result == HAETier.STANDARD

    def test_never_reduces_below_standard(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score.hae_crf import _adjust_veto_for_time_and_claims
        from do_uw.stages.score.scoring_lens import HAETier

        # Even with max decay, never below STANDARD
        result = _adjust_veto_for_time_and_claims(
            HAETier.ELEVATED, "expired", "NO_CLAIM"
        )
        assert result >= HAETier.STANDARD


class TestCRFOverrideMax:
    """Multiple CRFs: highest veto wins."""

    def test_crf_override_max(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from do_uw.stages.score import hae_crf
        from do_uw.stages.score.hae_crf import evaluate_crf_discordance
        from do_uw.stages.score.scoring_lens import HAETier

        monkeypatch.setattr(hae_crf, "_crf_catalog_cache", _MOCK_CRF_CATALOG)

        # Restatement -> HIGH_RISK and Material Weakness -> ELEVATED
        signal_results = {
            "FIN.ACCT.restatement": {"status": "TRIGGERED", "threshold_level": "red"},
            "FIN.ACCT.material_weakness": {"status": "TRIGGERED", "threshold_level": "red"},
        }
        tier, vetoes = evaluate_crf_discordance(signal_results, HAETier.STANDARD)
        # HIGH_RISK > ELEVATED, so HIGH_RISK wins
        assert tier == HAETier.HIGH_RISK
