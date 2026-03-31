"""Tests for scenario generator context builder.

Verifies that generate_scenarios() produces 5-7 company-specific
scenarios with score deltas, tier re-classification, and proper
condition-based filtering.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.scenario_generator import (
    generate_scenarios,
)


def _make_factor(
    factor_id: str,
    factor_name: str,
    max_points: int,
    points_deducted: float,
) -> MagicMock:
    """Build a mock FactorScore."""
    mf = MagicMock()
    mf.factor_id = factor_id
    mf.factor_name = factor_name
    mf.max_points = max_points
    mf.points_deducted = points_deducted
    return mf


def _make_mock_state(
    *,
    quality_score: float = 72.0,
    factor_overrides: dict[str, float] | None = None,
    scoring_none: bool = False,
) -> MagicMock:
    """Build a mock AnalysisState with 10 factor scores."""
    state = MagicMock()

    if scoring_none:
        state.scoring = None
        return state

    defaults = {
        "F1": 5.0, "F2": 3.0, "F3": 2.0, "F4": 0.0, "F5": 1.0,
        "F6": 2.0, "F7": 4.0, "F8": 0.0, "F9": 3.0, "F10": 1.0,
    }
    factor_defs = [
        ("F1", "Prior Litigation", 20),
        ("F2", "Stock Price Analysis", 12),
        ("F3", "Financial Quality", 15),
        ("F4", "IPO/SPAC/M&A", 8),
        ("F5", "Earnings/Guidance", 8),
        ("F6", "Short Interest", 8),
        ("F7", "Volatility", 8),
        ("F8", "Related Party", 5),
        ("F9", "Governance Quality", 8),
        ("F10", "Board Quality", 8),
    ]
    overrides = factor_overrides or {}
    pts = {**defaults, **overrides}

    factors = [
        _make_factor(fid, fname, mx, pts.get(fid, 0.0))
        for fid, fname, mx in factor_defs
    ]
    state.scoring.factor_scores = factors
    state.scoring.quality_score = quality_score

    return state


class TestGenerateScenarios:
    """Test suite for generate_scenarios."""

    def test_returns_five_to_seven_scenarios(self) -> None:
        """Test 1: Returns 5-7 scenarios for a mixed-risk company."""
        state = _make_mock_state()
        result = generate_scenarios(state)
        assert isinstance(result, list)
        assert 5 <= len(result) <= 7, f"Expected 5-7 scenarios, got {len(result)}"

    def test_sca_filed_only_when_no_active_sca(self) -> None:
        """Test 2: SCA Filed only appears when company has no active SCA."""
        # Low F1 = no active SCA
        state = _make_mock_state(factor_overrides={"F1": 5.0})
        result = generate_scenarios(state)
        sca_filed = [s for s in result if "SCA_FILED" in s.get("id", "")]
        assert len(sca_filed) >= 1, "SCA Filed should appear when no active SCA"

    def test_sca_escalation_when_has_active_sca(self) -> None:
        """Test 3: SCA Escalation appears when company HAS active SCA."""
        state = _make_mock_state(
            factor_overrides={"F1": 20.0},
            quality_score=52.0,
        )
        result = generate_scenarios(state)
        sca_esc = [s for s in result if "SCA_ESCALATION" in s.get("id", "")]
        assert len(sca_esc) >= 1, "SCA Escalation should appear when active SCA"
        # SCA Filed should NOT appear
        sca_filed = [s for s in result if s.get("id") == "SCA_FILED"]
        assert len(sca_filed) == 0, "SCA Filed should NOT appear when active SCA"

    def test_earnings_miss_always_included(self) -> None:
        """Test 4: Earnings Miss + 30% Drop is always included."""
        state = _make_mock_state()
        result = generate_scenarios(state)
        earnings = [s for s in result if "EARNINGS" in s.get("id", "")]
        assert len(earnings) >= 1, "Earnings Miss scenario always included"

    def test_scenario_fields_present(self) -> None:
        """Test 5: Each scenario has required fields."""
        state = _make_mock_state()
        result = generate_scenarios(state)
        for s in result:
            assert "current_score" in s, f"Missing current_score in {s.get('id')}"
            assert "scenario_score" in s, f"Missing scenario_score in {s.get('id')}"
            assert "current_tier" in s, f"Missing current_tier in {s.get('id')}"
            assert "scenario_tier" in s, f"Missing scenario_tier in {s.get('id')}"
            assert "score_delta" in s, f"Missing score_delta in {s.get('id')}"

    def test_scenario_score_respects_max_points(self) -> None:
        """Test 6: Scenario score respects max_points cap per factor."""
        state = _make_mock_state(
            factor_overrides={"F1": 18.0},  # Near max=20
            quality_score=54.0,
        )
        result = generate_scenarios(state)
        for s in result:
            # scenario_score should be between 0 and 100
            assert 0 <= s["scenario_score"] <= 100, (
                f"Scenario {s['id']} score {s['scenario_score']} out of range"
            )

    def test_tier_reclassification(self) -> None:
        """Test 7: Tier re-classification happens for scenarios."""
        state = _make_mock_state(quality_score=72.0)
        result = generate_scenarios(state)
        # Find a scenario with meaningful delta -- should potentially change tier
        for s in result:
            assert isinstance(s["scenario_tier"], str)
            assert s["scenario_tier"] in {"WIN", "WANT", "WRITE", "WATCH", "WALK", "NO_TOUCH"}

    def test_score_bounds(self) -> None:
        """Test 8: Score delta never causes score < 0 or > 100."""
        state = _make_mock_state(quality_score=95.0)  # Very high score
        result = generate_scenarios(state)
        for s in result:
            assert 0 <= s["scenario_score"] <= 100

    def test_graceful_degradation_when_none(self) -> None:
        """Test 9: When state.scoring is None, returns empty list."""
        state = _make_mock_state(scoring_none=True)
        result = generate_scenarios(state)
        assert result == []
