"""Integration tests for Phase 89 statistical computations in stock_performance.py.

Tests that EWMA/regime, abnormal returns, and DDL exposure are properly
wired from chart_computations into the extraction pipeline.
"""

from __future__ import annotations

import math
from typing import Any
from unittest.mock import patch

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market import StockPerformance
from do_uw.models.market_events import StockDropAnalysis, StockDropEvent
from do_uw.stages.extract.stock_performance import (
    _compute_abnormal_returns_for_drops,
    _compute_ddl_for_drops,
    _compute_ewma_and_regime,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_history(prices: list[float]) -> dict[str, Any]:
    """Build a minimal history dict from a price list."""
    dates = [f"2025-01-{i + 1:02d}" for i in range(len(prices))]
    return {"Close": prices, "Date": dates}


def _sourced_float(val: float) -> SourcedValue[float]:
    """Quick sourced float factory."""
    from datetime import UTC, datetime

    return SourcedValue[float](
        value=val,
        source="test",
        confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )


def _sourced_str(val: str) -> SourcedValue[str]:
    from datetime import UTC, datetime

    return SourcedValue[str](
        value=val,
        source="test",
        confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )


# ---------------------------------------------------------------------------
# EWMA + Regime tests
# ---------------------------------------------------------------------------


class TestEwmaAndRegime:
    """Test _compute_ewma_and_regime populates StockPerformance fields."""

    def test_populates_ewma_vol_current(self) -> None:
        """EWMA vol current is populated from price data."""
        # 100 prices with some volatility
        prices = [100.0 + i * 0.5 + ((-1) ** i) * 2.0 for i in range(200)]
        history = _make_history(prices)

        perf = StockPerformance()
        _compute_ewma_and_regime(perf, history)

        assert perf.ewma_vol_current is not None
        assert perf.ewma_vol_current.value > 0

    def test_populates_vol_regime(self) -> None:
        """Vol regime label is populated."""
        prices = [100.0 + i * 0.1 for i in range(200)]
        history = _make_history(prices)

        perf = StockPerformance()
        _compute_ewma_and_regime(perf, history)

        assert perf.vol_regime is not None
        assert perf.vol_regime.value in ("LOW", "NORMAL", "ELEVATED", "CRISIS")

    def test_populates_regime_duration(self) -> None:
        """Vol regime duration days is populated."""
        prices = [100.0 + i * 0.1 for i in range(200)]
        history = _make_history(prices)

        perf = StockPerformance()
        _compute_ewma_and_regime(perf, history)

        assert perf.vol_regime_duration_days is not None
        assert perf.vol_regime_duration_days >= 0

    def test_insufficient_data_no_crash(self) -> None:
        """With too few prices, fields remain None."""
        history = _make_history([100.0, 101.0])

        perf = StockPerformance()
        _compute_ewma_and_regime(perf, history)

        assert perf.ewma_vol_current is None


# ---------------------------------------------------------------------------
# Abnormal return tests
# ---------------------------------------------------------------------------


class TestAbnormalReturns:
    """Test _compute_abnormal_returns_for_drops populates AR fields."""

    def _make_long_prices(
        self, n: int = 500, base: float = 100.0, seed: int = 0,
    ) -> list[float]:
        """Generate prices with enough data for AR estimation window.

        Uses a deterministic pseudo-random pattern based on seed
        so company and market have different return series.
        """
        prices = [base]
        for i in range(1, n):
            # Deterministic pseudo-random daily return
            x = ((i + seed) * 2654435761) % 1000  # hash-like spread
            daily_ret = (x - 500) / 50000.0  # returns in [-1%, +1%]
            prices.append(prices[-1] * (1 + daily_ret))
        return prices

    def test_populates_abnormal_return_fields(self) -> None:
        """AR fields populated when sufficient data exists."""
        n = 500
        company_prices = self._make_long_prices(n, seed=0)
        spy_prices = self._make_long_prices(n, base=200.0, seed=42)

        # Insert a big drop at index 300
        company_prices[300] = company_prices[299] * 0.85  # 15% drop

        dates = [f"2024-{(i // 30) + 1:02d}-{(i % 28) + 1:02d}" for i in range(n)]
        drop_date = dates[300]

        drop_evt = StockDropEvent(
            date=_sourced_str(drop_date),
            drop_pct=_sourced_float(-15.0),
        )
        drops = StockDropAnalysis(
            single_day_drops=[drop_evt],
        )

        drop_history: dict[str, Any] = {"Close": company_prices, "Date": dates}
        market_data: dict[str, Any] = {
            "spy_history_2y": {"Close": spy_prices, "Date": dates},
        }

        _compute_abnormal_returns_for_drops(drops, drop_history, market_data)

        assert drop_evt.abnormal_return_pct is not None
        assert drop_evt.abnormal_return_t_stat is not None
        # A 15% drop should produce a large negative AR
        assert drop_evt.abnormal_return_pct < 0

    def test_insufficient_spy_data_no_crash(self) -> None:
        """When SPY data is missing, AR fields remain None."""
        drop_evt = StockDropEvent(
            date=_sourced_str("2025-01-15"),
            drop_pct=_sourced_float(-8.0),
        )
        drops = StockDropAnalysis(single_day_drops=[drop_evt])

        drop_history = _make_history([100.0] * 50)
        market_data: dict[str, Any] = {}

        _compute_abnormal_returns_for_drops(drops, drop_history, market_data)

        assert drop_evt.abnormal_return_pct is None

    def test_drop_without_date_skipped(self) -> None:
        """Drops without dates are safely skipped."""
        drop_evt = StockDropEvent(drop_pct=_sourced_float(-10.0))
        drops = StockDropAnalysis(single_day_drops=[drop_evt])

        prices = self._make_long_prices(300)
        dates = [f"2024-01-{(i % 28) + 1:02d}" for i in range(300)]
        drop_history: dict[str, Any] = {"Close": prices, "Date": dates}
        spy_data: dict[str, Any] = {"Close": prices, "Date": dates}
        market_data: dict[str, Any] = {"spy_history_2y": spy_data}

        _compute_abnormal_returns_for_drops(drops, drop_history, market_data)

        assert drop_evt.abnormal_return_pct is None


# ---------------------------------------------------------------------------
# DDL exposure tests
# ---------------------------------------------------------------------------


class TestDdlExposure:
    """Test _compute_ddl_for_drops populates DDL/MDL fields."""

    def test_populates_ddl_and_settlement(self) -> None:
        """DDL exposure and settlement estimate are populated."""
        drop_evt = StockDropEvent(
            date=_sourced_str("2025-01-15"),
            drop_pct=_sourced_float(-10.0),
        )
        drops = StockDropAnalysis(
            single_day_drops=[drop_evt],
            worst_single_day=drop_evt,
        )

        perf = StockPerformance()
        perf.market_cap_yf = _sourced_float(10_000_000_000.0)  # $10B
        perf.max_drawdown_1y = _sourced_float(-20.0)

        _compute_ddl_for_drops(drops, perf)

        assert drops.ddl_exposure is not None
        # DDL = $10B * 10% = $1B
        assert abs(drops.ddl_exposure.value - 1_000_000_000.0) < 1.0

        assert drops.ddl_settlement_estimate is not None
        # Settlement = $1B * 1.8% = $18M
        assert abs(drops.ddl_settlement_estimate.value - 18_000_000.0) < 1.0

        assert drops.mdl_exposure is not None
        # MDL = $10B * 20% = $2B
        assert abs(drops.mdl_exposure.value - 2_000_000_000.0) < 1.0

    def test_no_market_cap_no_ddl(self) -> None:
        """When market cap is missing, DDL fields remain None."""
        drop_evt = StockDropEvent(
            date=_sourced_str("2025-01-15"),
            drop_pct=_sourced_float(-10.0),
        )
        drops = StockDropAnalysis(
            single_day_drops=[drop_evt],
            worst_single_day=drop_evt,
        )

        perf = StockPerformance()  # No market_cap_yf

        _compute_ddl_for_drops(drops, perf)

        assert drops.ddl_exposure is None

    def test_no_worst_drop_no_ddl(self) -> None:
        """When no worst drop exists, DDL fields remain None."""
        drops = StockDropAnalysis()
        perf = StockPerformance()
        perf.market_cap_yf = _sourced_float(5_000_000_000.0)

        _compute_ddl_for_drops(drops, perf)

        assert drops.ddl_exposure is None

    def test_no_max_drawdown_mdl_is_none(self) -> None:
        """When max drawdown is missing, MDL is None but DDL is populated."""
        drop_evt = StockDropEvent(
            date=_sourced_str("2025-01-15"),
            drop_pct=_sourced_float(-5.0),
        )
        drops = StockDropAnalysis(
            single_day_drops=[drop_evt],
            worst_single_day=drop_evt,
        )

        perf = StockPerformance()
        perf.market_cap_yf = _sourced_float(1_000_000_000.0)
        # No max_drawdown_1y

        _compute_ddl_for_drops(drops, perf)

        assert drops.ddl_exposure is not None
        assert drops.mdl_exposure is None
        assert drops.ddl_settlement_estimate is not None
