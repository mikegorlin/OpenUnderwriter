"""Tests for visualization context additions to scorecard_context.py.

Verifies that build_scorecard_context produces waterfall_svg, radar_svg,
probability_components, scenarios, tornado_svg, risk_clusters, and
dominant_cluster keys.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from do_uw.stages.render.context_builders.scorecard_context import (
    build_scorecard_context,
)


def _make_factor_score(
    factor_id: str = "F1",
    factor_name: str = "Prior Litigation",
    points_deducted: float = 5.0,
    max_points: int = 20,
    scoring_method: str = "signal_driven",
) -> MagicMock:
    """Create a mock FactorScore."""
    fs = MagicMock()
    fs.factor_id = factor_id
    fs.factor_name = factor_name
    fs.points_deducted = points_deducted
    fs.max_points = max_points
    fs.scoring_method = scoring_method
    fs.evidence = ["Some evidence"]
    fs.rules_triggered = []
    fs.sub_components = {}
    fs.signal_contributions = []
    fs.signal_coverage = 0.8
    return fs


def _make_state_with_scoring() -> MagicMock:
    """Create a mock state with realistic scoring data."""
    state = MagicMock()

    # Factor scores for all 10 factors
    factor_defs = [
        ("F1", "Prior Litigation", 5.0, 20),
        ("F2", "Stock Decline", 8.0, 15),
        ("F3", "Restatement / Audit", 0.0, 15),
        ("F4", "IPO / SPAC / M&A", 2.0, 8),
        ("F5", "Guidance Misses", 4.0, 10),
        ("F6", "Short Interest", 3.0, 7),
        ("F7", "Volatility", 6.0, 10),
        ("F8", "Financial Distress", 0.0, 5),
        ("F9", "Governance", 2.0, 5),
        ("F10", "Officer Stability", 1.0, 5),
    ]
    factor_scores = [
        _make_factor_score(fid, fname, pts, mx)
        for fid, fname, pts, mx in factor_defs
    ]

    sc = MagicMock()
    sc.factor_scores = factor_scores
    sc.quality_score = 69.0
    sc.tier.tier = "WRITE"
    sc.hae_result = None
    sc.claim_probability = None
    sc.severity_result = None
    sc.tower_recommendation = None
    sc.actuarial_pricing = None
    sc.risk_type = None
    sc.allegation_mapping = None
    sc.severity_scenarios = None

    # Enhanced frequency for probability decomposition
    ef = MagicMock()
    ef.base_rate_pct = 3.8
    ef.hazard_multiplier = 1.2
    ef.signal_multiplier = 1.5
    ef.adjusted_probability_pct = 6.84
    sc.enhanced_frequency = ef

    state.scoring = sc
    state.analysis = MagicMock()
    state.analysis.signal_results = {}
    state.company = MagicMock()
    state.company.market_data = MagicMock()
    state.company.market_data.market_cap = 50_000_000_000.0
    state.company.market_cap = MagicMock()
    state.company.market_cap.value = 50_000_000_000.0
    state.company.employee_count = None
    state.company.years_public = None
    state.extracted = None

    return state


class TestScorecardVisualizationKeys:
    """Test that build_scorecard_context produces all visualization keys."""

    def test_waterfall_svg_present(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "waterfall_svg" in ctx
        assert isinstance(ctx["waterfall_svg"], str)

    def test_waterfall_svg_contains_svg_tag(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "<svg" in ctx["waterfall_svg"]

    def test_radar_svg_present(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "radar_svg" in ctx

    def test_probability_components_present(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "probability_components" in ctx
        assert isinstance(ctx["probability_components"], list)

    def test_probability_components_has_enough_items(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert len(ctx["probability_components"]) >= 7

    def test_scenarios_present(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "scenarios" in ctx
        assert isinstance(ctx["scenarios"], list)

    def test_scenarios_has_enough_items(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert len(ctx["scenarios"]) >= 5

    def test_tornado_svg_present(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "tornado_svg" in ctx
        assert isinstance(ctx["tornado_svg"], str)

    def test_risk_clusters_present(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "risk_clusters" in ctx
        assert isinstance(ctx["risk_clusters"], list)

    def test_dominant_cluster_present(self) -> None:
        state = _make_state_with_scoring()
        ctx = build_scorecard_context(state)
        assert "dominant_cluster" in ctx
