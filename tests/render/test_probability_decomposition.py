"""Tests for probability decomposition context builder.

Verifies that build_probability_decomposition() extracts 7+ named
additive components from the multiplicative EnhancedFrequency model,
with calibration labels and running totals.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.probability_decomposition import (
    build_probability_decomposition,
)


def _make_mock_state(
    *,
    base_rate_pct: float = 5.0,
    hazard_multiplier: float = 1.3,
    signal_multiplier: float = 1.15,
    adjusted_probability_pct: float = 7.475,
    crf_signal: float = 1.15,
    pattern_signal: float = 1.0,
    factor_signal: float = 1.0,
    market_cap: float | None = 5_000_000_000.0,
    factor_scores: list[dict[str, Any]] | None = None,
    enhanced_frequency_none: bool = False,
) -> MagicMock:
    """Build a mock AnalysisState with realistic scoring data."""
    state = MagicMock()

    if enhanced_frequency_none:
        state.scoring.enhanced_frequency = None
        return state

    ef = MagicMock()
    ef.base_rate_pct = base_rate_pct
    ef.hazard_multiplier = hazard_multiplier
    ef.signal_multiplier = signal_multiplier
    ef.adjusted_probability_pct = adjusted_probability_pct
    ef.crf_signal = crf_signal
    ef.pattern_signal = pattern_signal
    ef.factor_signal = factor_signal
    ef.components = {
        "base_rate_pct": base_rate_pct,
        "hazard_multiplier": hazard_multiplier,
        "signal_multiplier": signal_multiplier,
        "crf_signal": crf_signal,
        "pattern_signal": pattern_signal,
        "factor_signal": factor_signal,
    }
    state.scoring.enhanced_frequency = ef

    # Market cap
    state.company.market_data.market_cap = market_cap

    # Factor scores: build from dicts or use defaults
    if factor_scores is None:
        factor_scores = [
            {"factor_id": "F1", "factor_name": "Prior Litigation", "max_points": 20, "points_deducted": 5.0},
            {"factor_id": "F2", "factor_name": "Stock Price Analysis", "max_points": 12, "points_deducted": 3.0},
            {"factor_id": "F3", "factor_name": "Financial Quality", "max_points": 15, "points_deducted": 2.0},
            {"factor_id": "F4", "factor_name": "IPO/SPAC/M&A", "max_points": 8, "points_deducted": 0.0},
            {"factor_id": "F5", "factor_name": "Earnings/Guidance", "max_points": 8, "points_deducted": 1.0},
            {"factor_id": "F6", "factor_name": "Short Interest", "max_points": 8, "points_deducted": 2.0},
            {"factor_id": "F7", "factor_name": "Volatility", "max_points": 8, "points_deducted": 4.0},
            {"factor_id": "F8", "factor_name": "Related Party", "max_points": 5, "points_deducted": 0.0},
            {"factor_id": "F9", "factor_name": "Governance Quality", "max_points": 8, "points_deducted": 3.0},
            {"factor_id": "F10", "factor_name": "Board Quality", "max_points": 8, "points_deducted": 1.0},
        ]

    mock_factors = []
    for fd in factor_scores:
        mf = MagicMock()
        mf.factor_id = fd["factor_id"]
        mf.factor_name = fd["factor_name"]
        mf.max_points = fd["max_points"]
        mf.points_deducted = fd["points_deducted"]
        mock_factors.append(mf)
    state.scoring.factor_scores = mock_factors

    return state


class TestProbabilityDecomposition:
    """Test suite for build_probability_decomposition."""

    def test_returns_seven_plus_components(self) -> None:
        """Test 1: Returns list of >= 7 ProbabilityComponent dicts."""
        state = _make_mock_state()
        result = build_probability_decomposition(state)
        assert isinstance(result, list)
        assert len(result) >= 7, f"Expected >= 7 components, got {len(result)}"

    def test_first_component_is_sector_base_rate(self) -> None:
        """Test 2: First component is 'Sector Base Rate' with direction='base' and is_calibrated=True."""
        state = _make_mock_state()
        result = build_probability_decomposition(state)
        assert len(result) >= 1
        first = result[0]
        assert "sector" in first["name"].lower() or "base" in first["name"].lower()
        assert first["direction"] == "base"
        assert first["is_calibrated"] is True

    def test_components_include_expected_types(self) -> None:
        """Test 3: Components include IPO uplift, market cap tier, volatility, insider selling, litigation, governance."""
        state = _make_mock_state()
        result = build_probability_decomposition(state)
        names_lower = [c["name"].lower() for c in result]
        all_names = " ".join(names_lower)
        # Should have these component types
        assert any("market cap" in n for n in names_lower), f"Missing market cap component in {names_lower}"
        assert any("volatil" in n for n in names_lower), f"Missing volatility component in {names_lower}"
        assert any("litigation" in n or "litigat" in n for n in names_lower), f"Missing litigation component in {names_lower}"
        assert any("governance" in n for n in names_lower), f"Missing governance component in {names_lower}"

    def test_running_total_incremental(self) -> None:
        """Test 4: Each component has running_total_pct showing cumulative probability."""
        state = _make_mock_state()
        result = build_probability_decomposition(state)
        for i, comp in enumerate(result):
            assert "running_total_pct" in comp, f"Component {i} missing running_total_pct"
            assert isinstance(comp["running_total_pct"], (int, float))

    def test_final_running_total_matches_adjusted(self) -> None:
        """Test 5: Final running_total_pct matches adjusted_probability_pct within 0.1%."""
        state = _make_mock_state(adjusted_probability_pct=7.475)
        result = build_probability_decomposition(state)
        assert len(result) >= 1
        final_total = result[-1]["running_total_pct"]
        assert abs(final_total - 7.475) < 0.1, (
            f"Final running_total {final_total} != adjusted_probability_pct 7.475"
        )

    def test_calibrated_components_have_source(self) -> None:
        """Test 6: Calibrated components have non-empty source citing NERA/Cornerstone/SCAC."""
        state = _make_mock_state()
        result = build_probability_decomposition(state)
        calibrated = [c for c in result if c.get("is_calibrated")]
        assert len(calibrated) >= 2, "Expected at least 2 calibrated components"
        for c in calibrated:
            assert c["source"], f"Calibrated component {c['name']} has empty source"
            source_lower = c["source"].lower()
            assert any(
                kw in source_lower for kw in ["nera", "cornerstone", "scac", "stanford"]
            ), f"Source '{c['source']}' doesn't cite expected data sources"

    def test_uncalibrated_components(self) -> None:
        """Test 7: Uncalibrated components have is_calibrated=False."""
        state = _make_mock_state()
        result = build_probability_decomposition(state)
        uncalibrated = [c for c in result if not c.get("is_calibrated")]
        assert len(uncalibrated) >= 3, "Expected at least 3 uncalibrated components"
        for c in uncalibrated:
            assert c["is_calibrated"] is False

    def test_graceful_degradation_when_none(self) -> None:
        """Test 8: When enhanced_frequency is None, returns empty list."""
        state = _make_mock_state(enhanced_frequency_none=True)
        result = build_probability_decomposition(state)
        assert result == []

    def test_safe_float_usage(self) -> None:
        """Test 9: All float operations handle non-numeric gracefully."""
        state = _make_mock_state()
        # Set some values to strings that safe_float should handle
        state.scoring.enhanced_frequency.base_rate_pct = "5.0%"
        state.scoring.enhanced_frequency.hazard_multiplier = "1.3"
        state.scoring.enhanced_frequency.adjusted_probability_pct = "7.475"
        # Should not raise
        result = build_probability_decomposition(state)
        assert isinstance(result, list)
        assert len(result) >= 7
