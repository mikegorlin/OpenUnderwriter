"""Tests for compute_mdd_ratio.

Verifies MDD ratio computation (company MDD / sector MDD) and
edge cases (zero sector MDD, empty inputs).
"""

from __future__ import annotations

import pytest

from do_uw.stages.render.charts.chart_computations import (
    compute_mdd_ratio,
)


class TestMDDRatio:
    """Tests for compute_mdd_ratio."""

    def test_known_ratio(self):
        """Company MDD -20%, sector MDD -10% should give ratio 2.0."""
        # Company: 100 -> 80 -> 90 (MDD = -20%)
        # Sector:  100 -> 90 -> 95 (MDD = -10%)
        result = compute_mdd_ratio(
            [100.0, 80.0, 90.0],
            [100.0, 90.0, 95.0],
        )
        assert result is not None
        assert abs(result - 2.0) < 1e-10

    def test_sector_near_zero_mdd_returns_none(self):
        """When sector MDD >= -0.5%, return None (no meaningful drawdown)."""
        # Company: 100 -> 80 -> 90 (MDD = -20%)
        # Sector:  100 -> 99.6 -> 100 (MDD = -0.4%)
        result = compute_mdd_ratio(
            [100.0, 80.0, 90.0],
            [100.0, 99.6, 100.0],
        )
        assert result is None

    def test_empty_company_prices_returns_none(self):
        """Empty company prices should return None."""
        result = compute_mdd_ratio([], [100.0, 90.0, 95.0])
        assert result is None

    def test_empty_sector_prices_returns_none(self):
        """Empty sector prices should return None."""
        result = compute_mdd_ratio([100.0, 80.0, 90.0], [])
        assert result is None

    def test_both_empty_returns_none(self):
        """Both empty should return None."""
        result = compute_mdd_ratio([], [])
        assert result is None

    def test_single_price_returns_none(self):
        """Single price (no drawdown possible) returns None."""
        result = compute_mdd_ratio([100.0], [100.0])
        assert result is None

    def test_ratio_less_than_one(self):
        """Company MDD smaller than sector MDD gives ratio < 1."""
        # Company: 100 -> 95 -> 98 (MDD = -5%)
        # Sector:  100 -> 85 -> 90 (MDD = -15%)
        result = compute_mdd_ratio(
            [100.0, 95.0, 98.0],
            [100.0, 85.0, 90.0],
        )
        assert result is not None
        expected = 5.0 / 15.0  # ~0.333
        assert abs(result - expected) < 1e-10

    def test_flat_sector_returns_none(self):
        """Sector with no drawdown at all returns None."""
        # Sector monotonically increasing — MDD is None.
        result = compute_mdd_ratio(
            [100.0, 90.0, 95.0],
            [100.0, 101.0, 102.0],
        )
        assert result is None
