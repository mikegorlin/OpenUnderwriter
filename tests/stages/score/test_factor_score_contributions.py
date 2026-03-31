"""Tests for factor contribution display in scoring context builder.

Verifies that the scoring context builder includes signal attribution
data per factor (top-3 signals, confidence bar, factor weights) and
degrades gracefully for rule-based factors.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.scoring import (
    FactorScore,
    ScoringResult,
    Tier,
    TierClassification,
    _rebuild_scoring_models,
)
from do_uw.stages.render.context_builders.scoring import extract_scoring

# Resolve forward refs so ScoringResult can be instantiated
_rebuild_scoring_models()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_factor(
    factor_id: str = "F1",
    factor_name: str = "Prior Litigation",
    max_points: int = 20,
    points_deducted: float = 8.0,
    scoring_method: str = "signal_driven",
    signal_coverage: float = 0.75,
    signal_contributions: list[dict[str, Any]] | None = None,
) -> FactorScore:
    """Create a FactorScore with configurable signal attribution."""
    if signal_contributions is None:
        signal_contributions = [
            {
                "signal_id": "host.litigation.active_sca",
                "status": "TRIGGERED",
                "threshold_level": "red",
                "severity": 1.0,
                "weight": 1.0,
                "contribution": 1.0,
            },
            {
                "signal_id": "host.litigation.settlement_history",
                "status": "TRIGGERED",
                "threshold_level": "yellow",
                "severity": 0.5,
                "weight": 1.0,
                "contribution": 0.5,
            },
            {
                "signal_id": "host.litigation.regulatory_action",
                "status": "TRIGGERED",
                "threshold_level": "yellow",
                "severity": 0.5,
                "weight": 0.8,
                "contribution": 0.4,
            },
            {
                "signal_id": "host.litigation.derivative_suits",
                "status": "CLEAR",
                "threshold_level": "clear",
                "severity": 0.0,
                "weight": 1.0,
                "contribution": 0.0,
            },
            {
                "signal_id": "host.litigation.whistleblower",
                "status": "CLEAR",
                "threshold_level": "clear",
                "severity": 0.0,
                "weight": 1.0,
                "contribution": 0.0,
            },
        ]
    return FactorScore(
        factor_name=factor_name,
        factor_id=factor_id,
        max_points=max_points,
        points_deducted=points_deducted,
        signal_contributions=signal_contributions,
        signal_coverage=signal_coverage,
        scoring_method=scoring_method,
    )


def _make_state(factors: list[FactorScore] | None = None) -> MagicMock:
    """Create a minimal AnalysisState mock with scoring data."""
    state = MagicMock()
    scoring = ScoringResult(
        composite_score=75.0,
        quality_score=75.0,
        total_risk_points=25.0,
        factor_scores=factors or [_make_factor()],
        tier=TierClassification(
            tier=Tier.WRITE,
            score_range_low=71,
            score_range_high=85,
        ),
    )
    state.scoring = scoring
    state.extracted = None
    return state


# ---------------------------------------------------------------------------
# Tests: signal_attribution per factor
# ---------------------------------------------------------------------------


class TestSignalAttribution:
    """Test signal attribution data in scoring context."""

    def test_signal_driven_factor_includes_attribution(self) -> None:
        """Signal-driven factors should include signal_attribution dict."""
        state = _make_state()
        result = extract_scoring(state)
        assert result, "Expected non-empty scoring context"

        factor = result["factors"][0]
        assert "signal_attribution" in factor
        attr = factor["signal_attribution"]
        assert attr["scoring_method"] == "signal_driven"
        assert "top_3_signals" in attr
        assert "confidence_pct" in attr

    def test_top_3_signals_sorted_by_contribution(self) -> None:
        """Top 3 signals should be the 3 highest contribution values."""
        state = _make_state()
        result = extract_scoring(state)
        factor = result["factors"][0]
        top_3 = factor["signal_attribution"]["top_3_signals"]

        assert len(top_3) == 3
        # Verify sorted descending by contribution
        contributions = [s["contribution"] for s in top_3]
        assert contributions == sorted(contributions, reverse=True)
        # Verify the actual top 3 signal IDs
        assert top_3[0]["signal_id"] == "host.litigation.active_sca"
        assert top_3[1]["signal_id"] == "host.litigation.settlement_history"
        assert top_3[2]["signal_id"] == "host.litigation.regulatory_action"

    def test_confidence_bar_format(self) -> None:
        """Confidence bar should show evaluated/total and percentage."""
        factor = _make_factor(signal_coverage=0.75)
        state = _make_state([factor])
        result = extract_scoring(state)
        attr = result["factors"][0]["signal_attribution"]

        assert attr["confidence_pct"] == "75%"
        assert attr["signal_coverage"] == 0.75
        # full_signal_count = total signals in contributions list
        assert attr["full_signal_count"] == 5

    def test_evaluated_count_from_contributions(self) -> None:
        """Evaluated count should be signals with non-zero status."""
        factor = _make_factor(signal_coverage=0.60)
        state = _make_state([factor])
        result = extract_scoring(state)
        attr = result["factors"][0]["signal_attribution"]
        # All 5 signals have a status (TRIGGERED or CLEAR), so all evaluated
        assert attr["evaluated_count"] == 5

    def test_fewer_than_3_signals_returns_all(self) -> None:
        """When fewer than 3 signal contributions, return all of them."""
        contribs = [
            {
                "signal_id": "host.lit.sca",
                "status": "TRIGGERED",
                "threshold_level": "red",
                "severity": 1.0,
                "weight": 1.0,
                "contribution": 1.0,
            },
        ]
        factor = _make_factor(signal_contributions=contribs)
        state = _make_state([factor])
        result = extract_scoring(state)
        top_3 = result["factors"][0]["signal_attribution"]["top_3_signals"]
        assert len(top_3) == 1


# ---------------------------------------------------------------------------
# Tests: factor weights
# ---------------------------------------------------------------------------


class TestFactorWeights:
    """Test factor weight data in scoring context."""

    def test_factor_weight_pct_present(self) -> None:
        """Each factor should have a factor_weight_pct field."""
        factors = [
            _make_factor(factor_id="F1", max_points=20),
            _make_factor(factor_id="F2", factor_name="Stock Decline", max_points=15),
        ]
        state = _make_state(factors)
        result = extract_scoring(state)

        for f in result["factors"]:
            assert "factor_weight_pct" in f, f"Missing factor_weight_pct on {f['id']}"

    def test_factor_weight_pct_values(self) -> None:
        """Factor weight percentages should be max_points / 100 formatted."""
        factors = [
            _make_factor(factor_id="F1", max_points=20),
            _make_factor(factor_id="F2", factor_name="Stock Decline", max_points=15),
        ]
        state = _make_state(factors)
        result = extract_scoring(state)

        # Total max_points across these 2 factors = 35
        # F1 weight = 20/35 = 57.1%, F2 = 15/35 = 42.9%
        # But the actual weight is max_points / 100 (the total budget)
        f1 = result["factors"][0]
        assert f1["factor_weight_pct"] == "20%"

        f2 = result["factors"][1]
        assert f2["factor_weight_pct"] == "15%"


# ---------------------------------------------------------------------------
# Tests: backward compatibility (rule_based)
# ---------------------------------------------------------------------------


class TestRuleBasedBackwardCompat:
    """Test that rule-based factors don't get signal_attribution."""

    def test_rule_based_factor_no_attribution(self) -> None:
        """Rule-based factors should NOT have signal_attribution key."""
        factor = _make_factor(
            scoring_method="rule_based",
            signal_contributions=[],
            signal_coverage=0.0,
        )
        state = _make_state([factor])
        result = extract_scoring(state)
        f = result["factors"][0]
        assert "signal_attribution" not in f

    def test_mixed_factors_correct_attribution(self) -> None:
        """Mix of signal-driven and rule-based factors."""
        f_signal = _make_factor(
            factor_id="F1", scoring_method="signal_driven", signal_coverage=0.8
        )
        f_rule = _make_factor(
            factor_id="F9",
            factor_name="Governance Issues",
            max_points=6,
            scoring_method="rule_based",
            signal_contributions=[],
            signal_coverage=0.0,
        )
        state = _make_state([f_signal, f_rule])
        result = extract_scoring(state)

        assert "signal_attribution" in result["factors"][0]
        assert "signal_attribution" not in result["factors"][1]


# ---------------------------------------------------------------------------
# Tests: empty/edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Test edge cases for signal attribution."""

    def test_empty_signal_contributions_no_attribution(self) -> None:
        """signal_driven with empty contributions still works."""
        factor = _make_factor(
            scoring_method="signal_driven",
            signal_contributions=[],
            signal_coverage=0.6,
        )
        state = _make_state([factor])
        result = extract_scoring(state)
        attr = result["factors"][0]["signal_attribution"]
        assert attr["top_3_signals"] == []
        assert attr["full_signal_count"] == 0
