"""Tests for per-drop return decomposition.

Verifies that individual stock drops are decomposed into market, sector,
and company-specific components using the existing compute_return_decomposition.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import StockDropEvent
from do_uw.stages.extract.stock_drop_decomposition import (
    decompose_drop,
    decompose_drops,
)

AS_OF = datetime(2026, 3, 9, tzinfo=UTC)


def _make_drop(date_str: str, period_days: int = 1) -> StockDropEvent:
    return StockDropEvent(
        date=SourcedValue(value=date_str, source="test", confidence=Confidence.HIGH, as_of=AS_OF),
        drop_pct=SourcedValue(value=-10.0, source="test", confidence=Confidence.HIGH, as_of=AS_OF),
        period_days=period_days,
    )


class TestDecomposeDrop:
    """Tests for decompose_drop."""

    def test_single_day_decomposition(self) -> None:
        """Single-day drop uses idx-1 and idx prices for 2-point window."""
        drop = _make_drop("2026-01-03", period_days=1)
        # Dates: 2026-01-01, 2026-01-02, 2026-01-03
        dates = ["2026-01-01", "2026-01-02", "2026-01-03"]
        # Company drops 10%, market drops 5%, sector drops 7%
        company_prices = [100.0, 100.0, 90.0]
        spy_prices = [100.0, 100.0, 95.0]
        sector_prices = [100.0, 100.0, 93.0]

        result = decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)

        assert result.market_pct is not None
        assert result.sector_pct is not None
        assert result.company_pct is not None
        # market = SPY return = -5%
        assert result.market_pct == pytest.approx(-5.0, abs=0.5)
        # sector = sector_ret - spy_ret = -7% - (-5%) = -2%
        assert result.sector_pct == pytest.approx(-2.0, abs=0.5)
        # company = company_ret - sector_ret = -10% - (-7%) = -3%
        assert result.company_pct == pytest.approx(-3.0, abs=0.5)

    def test_multi_day_uses_endpoints(self) -> None:
        """Multi-day drop uses start and end prices (2-point window)."""
        drop = _make_drop("2026-01-03", period_days=3)
        dates = ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"]
        # 3-day window starting at idx=2 of drop date, so start=2, end=min(2+3,len-1)=4
        company_prices = [100.0, 100.0, 95.0, 90.0, 85.0]
        spy_prices = [100.0, 100.0, 99.0, 98.0, 97.0]
        sector_prices = [100.0, 100.0, 98.0, 96.0, 94.0]

        result = decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)
        # Should use prices at indices that cover the drop period
        assert result.market_pct is not None
        assert result.sector_pct is not None
        assert result.company_pct is not None

    def test_market_driven_flag(self) -> None:
        """is_market_driven=True when market accounts for >50% of absolute drop."""
        drop = _make_drop("2026-01-02", period_days=1)
        dates = ["2026-01-01", "2026-01-02"]
        # Company drops 10%, market drops 8% (80% market-driven)
        company_prices = [100.0, 90.0]
        spy_prices = [100.0, 92.0]
        sector_prices = [100.0, 91.0]

        result = decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)
        assert result.is_market_driven is True

    def test_company_specific_not_market_driven(self) -> None:
        """is_market_driven=False when company-specific is dominant."""
        drop = _make_drop("2026-01-02", period_days=1)
        dates = ["2026-01-01", "2026-01-02"]
        # Company drops 10%, market drops 1% (10% market-driven)
        company_prices = [100.0, 90.0]
        spy_prices = [100.0, 99.0]
        sector_prices = [100.0, 98.5]

        result = decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)
        assert result.is_market_driven is False

    def test_missing_sector_data_returns_none_fields(self) -> None:
        """When sector prices are empty, decomposition fields stay None."""
        drop = _make_drop("2026-01-02", period_days=1)
        dates = ["2026-01-01", "2026-01-02"]
        company_prices = [100.0, 90.0]
        spy_prices = [100.0, 95.0]
        sector_prices: list[float] = []

        result = decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)
        assert result.market_pct is None
        assert result.sector_pct is None
        assert result.company_pct is None

    def test_date_not_in_dates_list(self) -> None:
        """When drop date not found in dates, fields stay None."""
        drop = _make_drop("2026-06-15", period_days=1)
        dates = ["2026-01-01", "2026-01-02"]
        company_prices = [100.0, 90.0]
        spy_prices = [100.0, 95.0]
        sector_prices = [100.0, 93.0]

        result = decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)
        assert result.market_pct is None

    def test_components_sum_to_total(self) -> None:
        """market_pct + sector_pct + company_pct = total company return."""
        drop = _make_drop("2026-01-02", period_days=1)
        dates = ["2026-01-01", "2026-01-02"]
        company_prices = [100.0, 85.0]
        spy_prices = [100.0, 97.0]
        sector_prices = [100.0, 95.0]

        result = decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)
        assert result.market_pct is not None
        assert result.sector_pct is not None
        assert result.company_pct is not None
        total = result.market_pct + result.sector_pct + result.company_pct
        # Total = company return = (85-100)/100*100 = -15%
        assert total == pytest.approx(-15.0, abs=0.1)


class TestDecomposeDrops:
    """Tests for decompose_drops (batch)."""

    def test_processes_list(self) -> None:
        """Processes a list of drops."""
        drops = [_make_drop("2026-01-02"), _make_drop("2026-01-03")]
        dates = ["2026-01-01", "2026-01-02", "2026-01-03"]
        company = [100.0, 90.0, 85.0]
        spy = [100.0, 95.0, 93.0]
        sector = [100.0, 93.0, 90.0]

        result = decompose_drops(drops, company, spy, sector, dates)
        assert len(result) == 2
        # Both should have decomposition fields set
        assert result[0].market_pct is not None
        assert result[1].market_pct is not None

    def test_skips_drops_without_date(self) -> None:
        """Drops without date are passed through unchanged."""
        drop_no_date = StockDropEvent()
        drop_with_date = _make_drop("2026-01-02")
        dates = ["2026-01-01", "2026-01-02"]
        company = [100.0, 90.0]
        spy = [100.0, 95.0]
        sector = [100.0, 93.0]

        result = decompose_drops([drop_no_date, drop_with_date], company, spy, sector, dates)
        assert len(result) == 2
        assert result[0].market_pct is None  # no date, skipped
        assert result[1].market_pct is not None  # decomposed
