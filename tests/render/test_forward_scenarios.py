"""Tests for forward scenarios context builder.

Verifies that build_forward_scenarios() enhances existing scenario
generator output with probability badges, severity estimates, and
company-specific catalysts.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.stages.render.context_builders._forward_scenarios import (
    build_forward_scenarios,
)


def _make_factor(
    factor_id: str,
    max_points: int,
    points_deducted: float,
) -> MagicMock:
    """Build a mock FactorScore."""
    mf = MagicMock()
    mf.factor_id = factor_id
    mf.factor_name = factor_id
    mf.max_points = max_points
    mf.points_deducted = points_deducted
    return mf


def _make_mock_state(
    *,
    quality_score: float = 72.0,
    market_cap: float = 5e9,
    ticker: str = "TEST",
    company_name: str = "Test Corp",
    factor_overrides: dict[str, float] | None = None,
    scoring_none: bool = False,
) -> MagicMock:
    """Build a mock AnalysisState with scoring and company data."""
    state = MagicMock()

    if scoring_none:
        state.scoring = None
        return state

    defaults = {
        "F1": 5.0, "F2": 3.0, "F3": 2.0, "F4": 0.0, "F5": 1.0,
        "F6": 2.0, "F7": 4.0, "F8": 0.0, "F9": 3.0, "F10": 1.0,
    }
    max_pts = {
        "F1": 20, "F2": 15, "F3": 15, "F4": 10, "F5": 8,
        "F6": 8, "F7": 8, "F8": 5, "F9": 6, "F10": 5,
    }
    if factor_overrides:
        defaults.update(factor_overrides)

    factors = [
        _make_factor(fid, max_pts[fid], pts)
        for fid, pts in defaults.items()
    ]
    state.scoring.factor_scores = factors
    state.scoring.quality_score = quality_score

    # Company info for catalysts and severity
    state.company.ticker = ticker
    state.company.company_name = company_name
    state.extracted.market.stock.market_cap = MagicMock()
    state.extracted.market.stock.market_cap.value = market_cap

    return state


class TestBuildForwardScenarios:
    """Tests for build_forward_scenarios."""

    def test_returns_dict_with_required_keys(self) -> None:
        state = _make_mock_state()
        result = build_forward_scenarios(state)
        assert isinstance(result, dict)
        assert "scenarios_available" in result
        assert "scenarios" in result
        assert "scenario_count" in result
        assert "current_tier" in result
        assert "current_score" in result

    def test_scenarios_available_true_when_data_exists(self) -> None:
        state = _make_mock_state()
        result = build_forward_scenarios(state)
        assert result["scenarios_available"] is True
        assert result["scenario_count"] > 0

    def test_scenarios_available_false_when_no_scoring(self) -> None:
        state = _make_mock_state(scoring_none=True)
        result = build_forward_scenarios(state)
        assert result["scenarios_available"] is False
        assert result["scenarios"] == []

    def test_each_scenario_has_required_keys(self) -> None:
        state = _make_mock_state()
        result = build_forward_scenarios(state)
        required_keys = {
            "name", "probability", "severity_estimate",
            "score_delta", "catalyst", "current_tier",
            "scenario_tier", "description", "probability_color",
        }
        for scenario in result["scenarios"]:
            assert required_keys.issubset(scenario.keys()), (
                f"Missing keys: {required_keys - scenario.keys()}"
            )

    def test_probability_normalized_to_high_medium_low(self) -> None:
        state = _make_mock_state()
        result = build_forward_scenarios(state)
        valid_probs = {"HIGH", "MEDIUM", "LOW"}
        for scenario in result["scenarios"]:
            assert scenario["probability"] in valid_probs, (
                f"Invalid probability: {scenario['probability']}"
            )

    def test_severity_estimate_is_dollar_string(self) -> None:
        state = _make_mock_state(market_cap=10e9)
        result = build_forward_scenarios(state)
        for scenario in result["scenarios"]:
            sev = scenario["severity_estimate"]
            assert sev.startswith("$"), f"Severity should be dollar string: {sev}"

    def test_catalyst_references_company_data(self) -> None:
        """Catalysts should be company-specific, not generic template text."""
        state = _make_mock_state(ticker="ACME", company_name="Acme Corp")
        result = build_forward_scenarios(state)
        # At least one scenario should reference the company
        has_specific = any(
            "ACME" in s["catalyst"] or "Acme" in s["catalyst"]
            for s in result["scenarios"]
        )
        assert has_specific, "At least one catalyst should reference company"

    def test_max_7_scenarios_sorted_by_score_delta(self) -> None:
        state = _make_mock_state()
        result = build_forward_scenarios(state)
        scenarios = result["scenarios"]
        assert len(scenarios) <= 7
        # Verify sorted by abs(score_delta) descending
        deltas = [abs(s["score_delta"]) for s in scenarios]
        assert deltas == sorted(deltas, reverse=True)

    def test_probability_color_mapping(self) -> None:
        state = _make_mock_state()
        result = build_forward_scenarios(state)
        color_map = {
            "HIGH": "#DC2626",
            "MEDIUM": "#D97706",
            "LOW": "#16A34A",
        }
        for scenario in result["scenarios"]:
            expected_color = color_map[scenario["probability"]]
            assert scenario["probability_color"] == expected_color

    def test_excluded_when_condition_false(self) -> None:
        """SCA_ESCALATION should not appear when F1 < 15 (no active SCA)."""
        state = _make_mock_state(factor_overrides={"F1": 5.0})
        result = build_forward_scenarios(state)
        ids = [s["id"] for s in result["scenarios"]]
        assert "SCA_ESCALATION" not in ids
