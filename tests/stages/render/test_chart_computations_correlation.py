"""Tests for correlation and R-squared computations in chart_computations.py.

Tests compute_correlation() and compute_r_squared() which operate on
price series to compute Pearson correlation and R-squared of daily returns.
"""

from __future__ import annotations

import math

import pytest

from do_uw.stages.render.charts.chart_computations import (
    compute_correlation,
    compute_r_squared,
)


# ---------------------------------------------------------------------------
# Test 1: Identical series -> correlation ~1.0
# ---------------------------------------------------------------------------


def test_correlation_identical_series() -> None:
    """Identical price series should have correlation ~1.0."""
    prices = [100.0 + i * 0.5 + (i % 3) * 0.2 for i in range(50)]
    corr = compute_correlation(prices, prices)
    assert corr is not None
    assert abs(corr - 1.0) < 0.001


# ---------------------------------------------------------------------------
# Test 2: Inverse series -> correlation ~-1.0
# ---------------------------------------------------------------------------


def test_correlation_inverse_series() -> None:
    """Inversely moving series should have negative correlation."""
    # Use multiplicative returns: when A goes up by r%, B goes down by r%
    prices_a = [100.0]
    prices_b = [100.0]
    for i in range(49):
        r = 0.005 + (i % 5) * 0.001  # daily return 0.5%-0.9%
        prices_a.append(prices_a[-1] * (1 + r))
        prices_b.append(prices_b[-1] * (1 - r))
    corr = compute_correlation(prices_a, prices_b)
    assert corr is not None
    assert corr < -0.9  # Should be close to -1


# ---------------------------------------------------------------------------
# Test 3: <30 data points -> None
# ---------------------------------------------------------------------------


def test_correlation_insufficient_data() -> None:
    """Fewer than 30 data points should return None."""
    prices = [100.0 + i for i in range(25)]
    assert compute_correlation(prices, prices) is None


# ---------------------------------------------------------------------------
# Test 4: Zero-variance series -> None
# ---------------------------------------------------------------------------


def test_correlation_zero_variance() -> None:
    """Constant price series (zero variance returns) should return None."""
    flat = [100.0] * 50
    prices = [100.0 + i for i in range(50)]
    assert compute_correlation(flat, prices) is None


# ---------------------------------------------------------------------------
# Test 5: R-squared = correlation^2
# ---------------------------------------------------------------------------


def test_r_squared_is_correlation_squared() -> None:
    """R-squared should equal correlation squared."""
    prices_a = [100.0 + i * 0.5 + (i % 7) * 0.3 for i in range(50)]
    prices_b = [100.0 + i * 0.3 + (i % 5) * 0.4 for i in range(50)]

    corr = compute_correlation(prices_a, prices_b)
    r2 = compute_r_squared(prices_a, prices_b)

    assert corr is not None
    assert r2 is not None
    assert abs(r2 - corr ** 2) < 0.001


# ---------------------------------------------------------------------------
# Test 6: R-squared with <30 data points -> None
# ---------------------------------------------------------------------------


def test_r_squared_insufficient_data() -> None:
    """R-squared with fewer than 30 data points should return None."""
    prices = [100.0 + i for i in range(20)]
    assert compute_r_squared(prices, prices) is None


# ---------------------------------------------------------------------------
# Test 7: Correlation with real-ish data is bounded [-1, 1]
# ---------------------------------------------------------------------------


def test_correlation_bounded() -> None:
    """Correlation with varied price data is in [-1, 1]."""
    import random
    random.seed(42)
    prices_a = [100.0]
    prices_b = [50.0]
    for _ in range(60):
        prices_a.append(prices_a[-1] * (1 + random.gauss(0.001, 0.02)))
        prices_b.append(prices_b[-1] * (1 + random.gauss(0.0005, 0.015)))

    corr = compute_correlation(prices_a, prices_b)
    assert corr is not None
    assert -1.0 <= corr <= 1.0


# ---------------------------------------------------------------------------
# Test: R-squared is always between 0 and 1
# ---------------------------------------------------------------------------


def test_r_squared_bounded() -> None:
    """R-squared should be between 0 and 1."""
    import random
    random.seed(99)
    prices_a = [100.0]
    prices_b = [200.0]
    for _ in range(60):
        prices_a.append(prices_a[-1] * (1 + random.gauss(0.001, 0.02)))
        prices_b.append(prices_b[-1] * (1 + random.gauss(0.0, 0.03)))

    r2 = compute_r_squared(prices_a, prices_b)
    assert r2 is not None
    assert 0.0 <= r2 <= 1.0
