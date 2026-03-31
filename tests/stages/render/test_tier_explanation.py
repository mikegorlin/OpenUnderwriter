"""Tests for algorithmic 'Why TIER, not ADJACENT_TIER' narrative generation.

Validates tier explanation contains score, top factor, counterfactual
analysis, boundary warnings, and edge cases (WIN tier, no deductions).
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.models.scoring import FactorScore, ScoringResult, Tier, TierClassification
from do_uw.stages.render.context_builders.scoring_evaluative import (
    generate_tier_explanation,
)


def _make_factor(
    factor_id: str = "F.1",
    factor_name: str = "Prior Litigation",
    max_points: int = 20,
    points_deducted: float = 0.0,
) -> FactorScore:
    """Create a test FactorScore."""
    return FactorScore(
        factor_id=factor_id,
        factor_name=factor_name,
        max_points=max_points,
        points_deducted=points_deducted,
    )


def _make_scoring(
    score: float,
    tier: Tier,
    tier_low: int,
    tier_high: int,
    factors: list[FactorScore] | None = None,
) -> ScoringResult:
    """Create a ScoringResult for testing."""
    return ScoringResult(
        composite_score=score,
        quality_score=score,
        total_risk_points=100.0 - score,
        factor_scores=factors or [],
        tier=TierClassification(
            tier=tier,
            score_range_low=tier_low,
            score_range_high=tier_high,
        ),
    )


class TestTierExplanation:
    """Test generate_tier_explanation()."""

    def test_tier_explanation_contains_score(self) -> None:
        """Explanation contains the quality score."""
        scoring = _make_scoring(
            score=65.2, tier=Tier.WRITE, tier_low=51, tier_high=70,
            factors=[_make_factor(points_deducted=10.0)],
        )
        result = generate_tier_explanation(scoring)
        assert "65.2" in result
        assert "WRITE" in result

    def test_tier_explanation_contains_top_factor(self) -> None:
        """Top drag factor is identified by ID and name."""
        factors = [
            _make_factor("F.1", "Prior Litigation", 20, 12.0),
            _make_factor("F.7", "Market Volatility", 8, 5.0),
            _make_factor("F.3", "Regulatory Risk", 10, 3.0),
        ]
        scoring = _make_scoring(
            score=80.0, tier=Tier.WANT, tier_low=71, tier_high=85,
            factors=factors,
        )
        result = generate_tier_explanation(scoring)
        assert "F.1" in result
        assert "Prior Litigation" in result
        assert "Heaviest drag" in result

    def test_tier_explanation_counterfactual_reaches_above(self) -> None:
        """Counterfactual shows if removing factor would reach above tier."""
        # Score 68, need 71 for WANT. F.7 = 5/8. If clean: 68+5=73 = WANT.
        factors = [
            _make_factor("F.1", "Prior Litigation", 20, 20.0),
            _make_factor("F.7", "Market Volatility", 8, 5.0),
            _make_factor("F.3", "Regulatory Risk", 10, 7.0),
        ]
        scoring = _make_scoring(
            score=68.0, tier=Tier.WRITE, tier_low=51, tier_high=70,
            factors=factors,
        )
        result = generate_tier_explanation(scoring)
        # Removing F.1 (20 pts) would give 88 = WIN, but F.1 is checked first
        # since it has highest deduction. 68+20=88 reaches WIN tier.
        assert "were clean" in result
        assert "WANT" in result or "WIN" in result

    def test_tier_explanation_counterfactual_does_not_reach(self) -> None:
        """No false counterfactual when removing top factor still insufficient."""
        # Score 55, need 71 for WANT. Top factor = 5. 55+5=60 < 71.
        factors = [
            _make_factor("F.1", "Prior Litigation", 20, 5.0),
            _make_factor("F.3", "Regulatory Risk", 10, 5.0),
            _make_factor("F.5", "Insider Activity", 6, 5.0),
        ]
        scoring = _make_scoring(
            score=55.0, tier=Tier.WRITE, tier_low=51, tier_high=70,
            factors=factors,
        )
        result = generate_tier_explanation(scoring)
        # None of the individual factors reach WANT (71)
        # 55+5=60, not enough
        assert "were clean" not in result or "WANT" in result
        # Actually let's check: only show counterfactual if it reaches above
        # 55+5=60 < 71, so no counterfactual should appear
        # But let's be specific: count occurrences of "were clean"
        # If any factor removal would reach 71, it should appear.
        # 55+5=60, 55+5=60, 55+5=60 -- none reach 71.
        assert result.count("were clean") == 0

    def test_tier_explanation_near_boundary_warning(self) -> None:
        """Warning when score is close to lower tier boundary."""
        # Score 52, WRITE tier (51-70). Only 2 points above WATCH (31-50 max).
        factors = [_make_factor(points_deducted=48.0)]
        scoring = _make_scoring(
            score=52.0, tier=Tier.WRITE, tier_low=51, tier_high=70,
            factors=factors,
        )
        result = generate_tier_explanation(scoring)
        assert "Warning" in result
        assert "WATCH" in result

    def test_tier_explanation_win_tier_no_above(self) -> None:
        """WIN tier has no 'To reach' since it's the highest."""
        factors = [_make_factor(points_deducted=5.0)]
        scoring = _make_scoring(
            score=95.0, tier=Tier.WIN, tier_low=86, tier_high=100,
            factors=factors,
        )
        result = generate_tier_explanation(scoring)
        assert "95.0" in result
        assert "WIN" in result
        assert "To reach" not in result

    def test_tier_explanation_no_deductions(self) -> None:
        """Clean explanation when no deductions exist."""
        factors = [
            _make_factor("F.1", "Prior Litigation", 20, 0.0),
            _make_factor("F.2", "Stock Drop", 12, 0.0),
        ]
        scoring = _make_scoring(
            score=100.0, tier=Tier.WIN, tier_low=86, tier_high=100,
            factors=factors,
        )
        result = generate_tier_explanation(scoring)
        assert "100.0" in result
        assert "No risk deductions" in result

    def test_tier_explanation_no_tier(self) -> None:
        """Handles missing tier gracefully."""
        scoring = ScoringResult(
            composite_score=50.0,
            quality_score=50.0,
            total_risk_points=50.0,
            tier=None,
        )
        result = generate_tier_explanation(scoring)
        assert "50.0" in result
        assert "not available" in result

    def test_tier_explanation_percentage_of_deductions(self) -> None:
        """Top factor shows percentage of total deductions."""
        factors = [
            _make_factor("F.1", "Prior Litigation", 20, 15.0),
            _make_factor("F.7", "Market Volatility", 8, 5.0),
        ]
        scoring = _make_scoring(
            score=80.0, tier=Tier.WANT, tier_low=71, tier_high=85,
            factors=factors,
        )
        result = generate_tier_explanation(scoring)
        assert "75%" in result  # 15/20 = 75% of total deductions
