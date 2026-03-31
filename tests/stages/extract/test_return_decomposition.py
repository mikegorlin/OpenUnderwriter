"""Tests for compute_return_decomposition.

Verifies the 3-component return decomposition:
  total_return = market_contribution + sector_contribution + company_residual
"""

from __future__ import annotations

import pytest

from do_uw.stages.render.charts.chart_computations import (
    compute_return_decomposition,
)


class TestReturnDecomposition:
    """Tests for compute_return_decomposition."""

    def test_components_sum_to_total(self):
        """market + sector + company should equal total return."""
        # Company: 100 -> 110 = +10%
        # SPY:     100 -> 105 = +5%
        # Sector:  100 -> 108 = +8%
        result = compute_return_decomposition(
            [100.0, 110.0], [100.0, 105.0], [100.0, 108.0],
        )
        assert result is not None
        total = result["total_return"]
        parts = (
            result["market_contribution"]
            + result["sector_contribution"]
            + result["company_residual"]
        )
        assert abs(total - parts) < 1e-10, (
            f"Components {parts} != total {total}"
        )

    def test_known_values(self):
        """Verify specific decomposition values."""
        # Company: 100 -> 110 = +10%
        # SPY:     100 -> 105 = +5%  (market contribution = 5%)
        # Sector:  100 -> 108 = +8%  (sector contribution = 8% - 5% = 3%)
        # Residual: 10% - 8% = 2%
        result = compute_return_decomposition(
            [100.0, 110.0], [100.0, 105.0], [100.0, 108.0],
        )
        assert result is not None
        assert abs(result["total_return"] - 10.0) < 1e-10
        assert abs(result["market_contribution"] - 5.0) < 1e-10
        assert abs(result["sector_contribution"] - 3.0) < 1e-10
        assert abs(result["company_residual"] - 2.0) < 1e-10

    def test_empty_lists_returns_none(self):
        """Empty price lists should return None."""
        assert compute_return_decomposition([], [], []) is None

    def test_single_element_returns_none(self):
        """Single-element lists (no return possible) should return None."""
        assert compute_return_decomposition([100.0], [100.0], [100.0]) is None

    def test_zero_start_price_returns_none(self):
        """Zero starting price (division by zero) should return None."""
        result = compute_return_decomposition(
            [0.0, 100.0], [100.0, 105.0], [100.0, 108.0],
        )
        assert result is None

    def test_negative_returns(self):
        """Components should sum correctly even with negative returns."""
        # Company: 100 -> 80 = -20%
        # SPY:     100 -> 95 = -5%
        # Sector:  100 -> 90 = -10%
        result = compute_return_decomposition(
            [100.0, 80.0], [100.0, 95.0], [100.0, 90.0],
        )
        assert result is not None
        assert abs(result["total_return"] - (-20.0)) < 1e-10
        assert abs(result["market_contribution"] - (-5.0)) < 1e-10
        assert abs(result["sector_contribution"] - (-5.0)) < 1e-10
        assert abs(result["company_residual"] - (-10.0)) < 1e-10

    def test_multi_period_prices(self):
        """Should use first and last prices for return calc."""
        # Company: 100 -> 105 -> 95 -> 112 = +12%
        # SPY:     100 -> 102 -> 101 -> 106 = +6%
        # Sector:  100 -> 103 -> 99 -> 109 = +9%
        result = compute_return_decomposition(
            [100.0, 105.0, 95.0, 112.0],
            [100.0, 102.0, 101.0, 106.0],
            [100.0, 103.0, 99.0, 109.0],
        )
        assert result is not None
        total = result["total_return"]
        parts = (
            result["market_contribution"]
            + result["sector_contribution"]
            + result["company_residual"]
        )
        assert abs(total - parts) < 1e-10
        assert abs(total - 12.0) < 1e-10
