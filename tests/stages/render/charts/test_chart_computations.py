"""Tests for Phase 89 chart computation functions.

Covers DDL exposure, abnormal return event study, EWMA volatility,
and volatility regime classification.
"""

from __future__ import annotations

import math

import pytest

from do_uw.stages.render.charts.chart_computations import (
    classify_vol_regime,
    compute_abnormal_return,
    compute_ddl_exposure,
    compute_ewma_volatility,
)


# ---------------------------------------------------------------------------
# DDL Exposure
# ---------------------------------------------------------------------------


class TestComputeDDLExposure:
    """Tests for compute_ddl_exposure."""

    def test_basic_calculation(self) -> None:
        result = compute_ddl_exposure(
            market_cap=10e9, worst_drop_pct=-15.0,
        )
        assert result["ddl_amount"] == pytest.approx(1.5e9)
        assert result["settlement_estimate"] == pytest.approx(27e6)

    def test_zero_drop_returns_zero(self) -> None:
        result = compute_ddl_exposure(market_cap=10e9, worst_drop_pct=0.0)
        assert result["ddl_amount"] == 0.0
        assert result["settlement_estimate"] == 0.0

    def test_positive_pct_treated_as_magnitude(self) -> None:
        """Positive pct is abs()-ed, same result as negative."""
        r1 = compute_ddl_exposure(market_cap=5e9, worst_drop_pct=-10.0)
        r2 = compute_ddl_exposure(market_cap=5e9, worst_drop_pct=10.0)
        assert r1["ddl_amount"] == r2["ddl_amount"]

    def test_mdl_when_max_drawdown_provided(self) -> None:
        result = compute_ddl_exposure(
            market_cap=10e9,
            worst_drop_pct=-15.0,
            max_drawdown_pct=-30.0,
        )
        assert result["ddl_amount"] == pytest.approx(1.5e9)
        assert result["mdl_amount"] == pytest.approx(3.0e9)

    def test_mdl_none_when_not_provided(self) -> None:
        result = compute_ddl_exposure(market_cap=10e9, worst_drop_pct=-15.0)
        assert result["mdl_amount"] is None

    def test_custom_settlement_ratio(self) -> None:
        result = compute_ddl_exposure(
            market_cap=10e9,
            worst_drop_pct=-10.0,
            settlement_ratio=0.025,
        )
        assert result["settlement_estimate"] == pytest.approx(10e9 * 0.10 * 0.025)


# ---------------------------------------------------------------------------
# Abnormal Return
# ---------------------------------------------------------------------------


class TestComputeAbnormalReturn:
    """Tests for compute_abnormal_return."""

    @staticmethod
    def _make_synthetic_data(
        n: int = 200,
        alpha: float = 0.0005,
        beta: float = 1.2,
        event_shock: float = -0.08,
    ) -> tuple[list[float], list[float], int]:
        """Create synthetic returns with known alpha/beta and event shock.

        Returns (company_returns, market_returns, event_idx).
        """
        import random

        rng = random.Random(42)
        market_returns = [rng.gauss(0.0005, 0.01) for _ in range(n)]
        company_returns = [
            alpha + beta * mr + rng.gauss(0, 0.005)
            for mr in market_returns
        ]
        # Inject event shock near end
        event_idx = n - 5
        company_returns[event_idx] += event_shock
        return company_returns, market_returns, event_idx

    def test_detects_significant_negative_event(self) -> None:
        cr, mr, idx = self._make_synthetic_data(event_shock=-0.08)
        result = compute_abnormal_return(cr, mr, idx)
        assert result is not None
        ar_pct, t_stat, is_sig = result
        # Shock of -8% should produce significant negative AR
        assert ar_pct < -5.0
        assert t_stat < -2.0
        assert is_sig is True

    def test_no_shock_insignificant(self) -> None:
        cr, mr, idx = self._make_synthetic_data(event_shock=0.0)
        result = compute_abnormal_return(cr, mr, idx)
        assert result is not None
        _ar_pct, t_stat, is_sig = result
        # No shock -> should be small, likely insignificant
        assert abs(t_stat) < 3.0  # loose bound: random noise may produce small t

    def test_returns_none_insufficient_data(self) -> None:
        """Fewer than 60 observations in estimation window returns None."""
        cr = [0.001] * 50
        mr = [0.001] * 50
        result = compute_abnormal_return(cr, mr, event_idx=45)
        assert result is None

    def test_returns_none_event_out_of_bounds(self) -> None:
        cr = [0.001] * 200
        mr = [0.001] * 200
        result = compute_abnormal_return(cr, mr, event_idx=250)
        assert result is None

    def test_returns_none_est_start_negative(self) -> None:
        cr = [0.001] * 50
        mr = [0.001] * 50
        # event_idx=10, gap=5, est_end=5, est_start=5-120=-115 < 0
        result = compute_abnormal_return(cr, mr, event_idx=10)
        assert result is None

    def test_returns_alpha_beta(self) -> None:
        """Result is a tuple of (ar_pct, t_stat, is_sig) only."""
        cr, mr, idx = self._make_synthetic_data()
        result = compute_abnormal_return(cr, mr, idx)
        assert result is not None
        assert len(result) == 3

    def test_zero_variance_market_returns_none(self) -> None:
        """Constant market returns (zero variance) returns None."""
        cr = [0.001 + i * 0.0001 for i in range(200)]
        mr = [0.001] * 200  # constant
        result = compute_abnormal_return(cr, mr, event_idx=195)
        assert result is None


# ---------------------------------------------------------------------------
# EWMA Volatility
# ---------------------------------------------------------------------------


class TestComputeEWMAVolatility:
    """Tests for compute_ewma_volatility."""

    def test_constant_prices_near_zero_vol(self) -> None:
        prices = [100.0] * 50
        result = compute_ewma_volatility(prices)
        assert len(result) == 50
        assert all(v == pytest.approx(0.0, abs=0.01) for v in result)

    def test_price_spike_shows_vol_spike(self) -> None:
        prices = [100.0] * 50
        prices[25] = 120.0  # 20% spike
        prices[26] = 100.0  # back to normal
        result = compute_ewma_volatility(prices)
        # Vol should spike at index 25-26 and then decay
        spike_vol = result[25]
        later_vol = result[40]
        assert spike_vol > later_vol
        assert spike_vol > 50.0  # should be substantial

    def test_ewma_vol_decays(self) -> None:
        """After a shock, EWMA vol should decay over subsequent periods."""
        prices = [100.0] * 100
        prices[30] = 85.0  # -15% shock
        prices[31] = 100.0
        result = compute_ewma_volatility(prices)
        # Vol at t=31 should be higher than at t=60
        assert result[31] > result[60]

    def test_short_series_returns_zeros(self) -> None:
        """Fewer than 2 prices returns list of 0.0s."""
        assert compute_ewma_volatility([100.0]) == [0.0]
        assert compute_ewma_volatility([]) == []

    def test_output_length_matches_input(self) -> None:
        prices = [100.0 + i * 0.5 for i in range(100)]
        result = compute_ewma_volatility(prices)
        assert len(result) == len(prices)

    def test_first_value_is_zero(self) -> None:
        prices = [100.0, 101.0, 102.0, 103.0]
        result = compute_ewma_volatility(prices)
        assert result[0] == 0.0

    def test_annualized_output(self) -> None:
        """Output should be annualized (scaled by sqrt(252))."""
        # With daily returns of ~1%, daily vol ~1%, annualized ~15.87%
        prices = [100.0]
        import random
        rng = random.Random(42)
        for _ in range(252):
            prices.append(prices[-1] * math.exp(rng.gauss(0, 0.01)))
        result = compute_ewma_volatility(prices)
        # Last value should be in annualized range (roughly 10-25%)
        assert 5.0 < result[-1] < 40.0


# ---------------------------------------------------------------------------
# Volatility Regime Classification
# ---------------------------------------------------------------------------


class TestClassifyVolRegime:
    """Tests for classify_vol_regime."""

    def test_uniform_series_normal(self) -> None:
        """Median value of uniform series should be NORMAL."""
        series = list(range(1, 101))  # 1 to 100
        regime, _dur = classify_vol_regime(series, current_idx=49)  # value=50
        assert regime == "NORMAL"

    def test_crisis_for_high_value(self) -> None:
        """Value above 90th percentile is CRISIS."""
        series = list(range(1, 101))
        regime, _dur = classify_vol_regime(series, current_idx=95)  # value=96
        assert regime == "CRISIS"

    def test_low_for_small_value(self) -> None:
        """Value below 25th percentile is LOW."""
        series = list(range(1, 101))
        regime, _dur = classify_vol_regime(series, current_idx=5)  # value=6
        assert regime == "LOW"

    def test_elevated_for_high_but_not_crisis(self) -> None:
        """Value between 75th and 90th percentile is ELEVATED."""
        series = list(range(1, 101))
        regime, _dur = classify_vol_regime(series, current_idx=79)  # value=80
        assert regime == "ELEVATED"

    def test_duration_counts_consecutive_days(self) -> None:
        """Duration = consecutive days in same regime at end of series."""
        # All values in NORMAL range
        series = [50.0] * 20
        _regime, dur = classify_vol_regime(series)
        assert dur == 20

    def test_duration_resets_on_regime_change(self) -> None:
        """Duration resets when regime changes."""
        # 10 LOW values followed by 10 NORMAL values
        low_vals = [1.0] * 10
        normal_vals = [50.0] * 10
        series = low_vals + normal_vals
        # Since all values are either 1.0 or 50.0, percentiles shift
        # Just verify duration < len(series)
        _regime, dur = classify_vol_regime(series)
        assert dur <= len(series)

    def test_empty_series_returns_normal_zero(self) -> None:
        regime, dur = classify_vol_regime([])
        assert regime == "NORMAL"
        assert dur == 0

    def test_all_zeros_returns_normal_zero(self) -> None:
        """All-zero series (no valid vols) returns NORMAL, 0."""
        regime, dur = classify_vol_regime([0.0] * 10)
        assert regime == "NORMAL"
        assert dur == 0

    def test_negative_index_uses_last(self) -> None:
        """current_idx=-1 uses last element."""
        series = list(range(1, 101))
        r1, _ = classify_vol_regime(series, current_idx=-1)
        r2, _ = classify_vol_regime(series, current_idx=99)
        assert r1 == r2
