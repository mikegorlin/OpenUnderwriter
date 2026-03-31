"""Tests for underwriting posture generation, ZER-001 verification, and watch items.

Tests the BENCHMARK-stage posture engine that consumes scoring results and brain
YAML config to produce algorithmic underwriting posture recommendations.

Phase 117 Plan 03 Task 1.
"""

from __future__ import annotations

import pytest

from do_uw.models.forward_looking import (
    ForwardLookingData,
    ForwardStatement,
    PostureElement,
    PostureRecommendation,
    QuickScreenResult,
    WatchItem,
)
from do_uw.models.scoring import FactorScore, ScoringResult, Tier, TierClassification
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.underwriting_posture import (
    generate_posture,
    generate_watch_items,
    load_posture_config,
    verify_zero_factors,
)


# ---------------------------------------------------------------------------
# Helpers to build test fixtures
# ---------------------------------------------------------------------------


def _make_factor(factor_id: str, name: str, max_points: int, deducted: float = 0.0) -> FactorScore:
    return FactorScore(
        factor_id=factor_id,
        factor_name=name,
        max_points=max_points,
        points_deducted=deducted,
    )


def _make_scoring(
    quality_score: float,
    tier: Tier,
    factor_overrides: dict[str, float] | None = None,
) -> ScoringResult:
    """Build a ScoringResult with standard factors and optional deduction overrides."""
    factors = [
        _make_factor("F.1", "Prior Litigation", 20),
        _make_factor("F.2", "Stock Decline", 15),
        _make_factor("F.3", "Restatement/Audit Issues", 12),
        _make_factor("F.4", "IPO/SPAC/M&A", 10),
        _make_factor("F.5", "Guidance Misses", 10),
        _make_factor("F.6", "Short Interest", 8),
        _make_factor("F.7", "Stock Volatility", 9),
        _make_factor("F.8", "Financial Distress", 8),
        _make_factor("F.9", "Governance Issues", 6),
        _make_factor("F.10", "Officer Stability", 2),
    ]
    if factor_overrides:
        for f in factors:
            if f.factor_id in factor_overrides:
                f.points_deducted = factor_overrides[f.factor_id]

    tier_boundaries = {
        Tier.WIN: (86, 100),
        Tier.WANT: (71, 85),
        Tier.WRITE: (51, 70),
        Tier.WATCH: (31, 50),
        Tier.WALK: (11, 30),
        Tier.NO_TOUCH: (0, 10),
    }
    low, high = tier_boundaries[tier]
    tier_cls = TierClassification(tier=tier, score_range_low=low, score_range_high=high)
    total_deducted = sum(f.points_deducted for f in factors)

    return ScoringResult(
        quality_score=quality_score,
        composite_score=quality_score,
        total_risk_points=total_deducted,
        factor_scores=factors,
        tier=tier_cls,
    )


def _make_state(**kwargs: object) -> AnalysisState:
    """Build minimal AnalysisState for posture tests."""
    return AnalysisState(ticker="TEST", **kwargs)


# ---------------------------------------------------------------------------
# Test: load_posture_config
# ---------------------------------------------------------------------------


class TestLoadPostureConfig:
    def test_loads_yaml_and_has_posture_matrix(self) -> None:
        config = load_posture_config()
        assert "posture_matrix" in config
        assert "WIN" in config["posture_matrix"]
        assert "NO_TOUCH" in config["posture_matrix"]

    def test_has_factor_overrides(self) -> None:
        config = load_posture_config()
        assert "factor_overrides" in config
        assert len(config["factor_overrides"]) >= 3


# ---------------------------------------------------------------------------
# Test: generate_posture
# ---------------------------------------------------------------------------


class TestGeneratePosture:
    def test_win_tier_full_terms(self) -> None:
        scoring = _make_scoring(92.0, Tier.WIN)
        state = _make_state()
        posture = generate_posture(scoring, state)

        assert isinstance(posture, PostureRecommendation)
        assert posture.tier == "WIN"
        # Find decision element
        decisions = [e for e in posture.elements if e.element == "decision"]
        assert len(decisions) == 1
        assert decisions[0].recommendation == "Full terms"
        # Retention
        retentions = [e for e in posture.elements if e.element == "retention"]
        assert retentions[0].recommendation == "Standard"
        # Pricing
        pricings = [e for e in posture.elements if e.element == "pricing"]
        assert pricings[0].recommendation == "At-model"

    def test_watch_tier_restricted_terms(self) -> None:
        scoring = _make_scoring(40.0, Tier.WATCH)
        state = _make_state()
        posture = generate_posture(scoring, state)

        assert posture.tier == "WATCH"
        decisions = [e for e in posture.elements if e.element == "decision"]
        assert decisions[0].recommendation == "Restricted terms"
        retentions = [e for e in posture.elements if e.element == "retention"]
        assert retentions[0].recommendation == "High retention"
        pricings = [e for e in posture.elements if e.element == "pricing"]
        assert "+25-50%" in pricings[0].recommendation

    def test_no_touch_tier_decline(self) -> None:
        scoring = _make_scoring(5.0, Tier.NO_TOUCH)
        state = _make_state()
        posture = generate_posture(scoring, state)

        assert posture.tier == "NO_TOUCH"
        decisions = [e for e in posture.elements if e.element == "decision"]
        assert decisions[0].recommendation == "Decline"

    def test_f1_active_sca_adds_litigation_exclusion(self) -> None:
        scoring = _make_scoring(65.0, Tier.WRITE, factor_overrides={"F.1": 15.0})
        state = _make_state()
        posture = generate_posture(scoring, state)

        # Should have override applied
        assert len(posture.overrides_applied) >= 1
        has_litigation = any("Litigation exclusion" in o for o in posture.overrides_applied)
        assert has_litigation, f"Expected litigation exclusion in overrides: {posture.overrides_applied}"

    def test_f7_insider_selling_adds_monitoring(self) -> None:
        scoring = _make_scoring(65.0, Tier.WRITE, factor_overrides={"F.7": 6.0})
        state = _make_state()
        posture = generate_posture(scoring, state)

        has_insider = any("insider" in o.lower() for o in posture.overrides_applied)
        assert has_insider, f"Expected insider monitoring override: {posture.overrides_applied}"

    def test_multiple_overrides_stack(self) -> None:
        scoring = _make_scoring(45.0, Tier.WATCH, factor_overrides={"F.3": 5.0, "F.7": 6.0})
        state = _make_state()
        posture = generate_posture(scoring, state)

        # Both F.3 and F.7 overrides should fire
        assert len(posture.overrides_applied) >= 2

    def test_posture_rationale_references_tier(self) -> None:
        scoring = _make_scoring(78.0, Tier.WANT)
        state = _make_state()
        posture = generate_posture(scoring, state)

        # Check that at least one element rationale mentions the tier and score
        all_rationales = " ".join(e.rationale for e in posture.elements)
        assert "WANT" in all_rationales
        assert "78" in all_rationales


# ---------------------------------------------------------------------------
# Test: verify_zero_factors
# ---------------------------------------------------------------------------


class TestVerifyZeroFactors:
    def test_all_zero_returns_verifications(self) -> None:
        scoring = _make_scoring(100.0, Tier.WIN)
        state = _make_state()
        verifications = verify_zero_factors(scoring, state)

        # All 10 factors are 0, should get verifications for key ones
        assert len(verifications) >= 3  # At least F.1, F.3, F.9

    def test_f1_zero_has_evidence(self) -> None:
        scoring = _make_scoring(100.0, Tier.WIN)
        state = _make_state()
        verifications = verify_zero_factors(scoring, state)

        f1_ver = [v for v in verifications if v["factor_id"] == "F.1"]
        assert len(f1_ver) == 1
        assert "evidence" in f1_ver[0]
        assert f1_ver[0]["evidence"] != ""

    def test_nonzero_factor_excluded(self) -> None:
        scoring = _make_scoring(80.0, Tier.WANT, factor_overrides={"F.1": 15.0})
        state = _make_state()
        verifications = verify_zero_factors(scoring, state)

        # F.1 should NOT be in verifications (it's non-zero)
        f1_ids = [v["factor_id"] for v in verifications]
        assert "F.1" not in f1_ids
        # But F.3 and F.9 should still be there
        assert "F.3" in f1_ids
        assert "F.9" in f1_ids


# ---------------------------------------------------------------------------
# Test: generate_watch_items
# ---------------------------------------------------------------------------


class TestGenerateWatchItems:
    def test_significant_deduction_creates_watch_item(self) -> None:
        # F.2 = 10/15 (67% deduction -> significant)
        scoring = _make_scoring(65.0, Tier.WRITE, factor_overrides={"F.2": 10.0})
        state = _make_state()
        items = generate_watch_items(scoring, state)

        assert len(items) >= 1
        assert isinstance(items[0], WatchItem)
        assert items[0].item != ""

    def test_all_clean_returns_empty(self) -> None:
        scoring = _make_scoring(100.0, Tier.WIN)
        state = _make_state()
        items = generate_watch_items(scoring, state)

        assert len(items) == 0

    def test_high_deduction_has_monthly_review(self) -> None:
        # F.1 = 15/20 (75% deduction -> high)
        scoring = _make_scoring(50.0, Tier.WATCH, factor_overrides={"F.1": 15.0})
        state = _make_state()
        items = generate_watch_items(scoring, state)

        high_items = [i for i in items if "Monthly" in i.re_evaluation]
        assert len(high_items) >= 1

    def test_forward_statement_high_risk_creates_watch_item(self) -> None:
        scoring = _make_scoring(80.0, Tier.WANT)
        fwd = ForwardLookingData(
            forward_statements=[
                ForwardStatement(
                    metric_name="Revenue",
                    guidance_claim="$10B",
                    miss_risk="HIGH",
                    miss_risk_rationale="Significant gap",
                ),
            ]
        )
        state = _make_state(forward_looking=fwd)
        items = generate_watch_items(scoring, state)

        assert len(items) >= 1
        has_fwd = any("Revenue" in i.item or "guidance" in i.item.lower() for i in items)
        assert has_fwd
