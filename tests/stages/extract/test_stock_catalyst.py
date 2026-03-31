"""Tests for stock drop catalyst enrichment and pattern detection.

Phase 119-02 Task 1: TDD tests for enrich_drops_with_prices_and_volume()
and detect_stock_patterns().
"""

from __future__ import annotations

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import DropType, StockDropEvent
from do_uw.stages.extract.stock_catalyst import (
    detect_stock_patterns,
    enrich_drops_with_prices_and_volume,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.MEDIUM, as_of="2025-01-01",
    )


def _sourced_float(val: float) -> SourcedValue[float]:
    return SourcedValue[float](
        value=val, source="test", confidence=Confidence.MEDIUM, as_of="2025-01-01",
    )


def _make_drop(
    date: str,
    drop_pct: float = -5.0,
    close_price: float | None = None,
    period_days: int = 1,
    drop_type: str = "SINGLE_DAY",
) -> StockDropEvent:
    return StockDropEvent(
        date=_sourced_str(date),
        drop_pct=_sourced_float(drop_pct),
        drop_type=drop_type,
        period_days=period_days,
        close_price=close_price,
    )


def _make_history(dates: list[str], closes: list[float], volumes: list[int]) -> dict:
    """Build yfinance-style history dict."""
    return {
        "Date": dates,
        "Close": closes,
        "Volume": volumes,
    }


# ---------------------------------------------------------------------------
# enrich_drops_with_prices_and_volume
# ---------------------------------------------------------------------------


class TestEnrichDrops:
    """Tests for enrich_drops_with_prices_and_volume."""

    def test_empty_drops(self) -> None:
        """No-op on empty list."""
        drops: list[StockDropEvent] = []
        enrich_drops_with_prices_and_volume(drops, {})
        assert drops == []

    def test_single_drop_enrichment(self) -> None:
        """Populates from_price (prior day close) and volume on drop date."""
        history = _make_history(
            dates=["2025-01-13", "2025-01-14", "2025-01-15"],
            closes=[100.0, 105.0, 95.0],
            volumes=[1000, 2000, 5000],
        )
        drop = _make_drop("2025-01-15", drop_pct=-9.5, close_price=95.0)
        enrich_drops_with_prices_and_volume([drop], history)

        assert drop.from_price == 105.0  # prior day close
        assert drop.volume == 5000  # volume on drop date

    def test_multi_day_drop_enrichment(self) -> None:
        """For multi-day drops, from_price = close before period start, volume = max over period."""
        history = _make_history(
            dates=["2025-01-10", "2025-01-13", "2025-01-14", "2025-01-15", "2025-01-16"],
            closes=[110.0, 105.0, 100.0, 95.0, 90.0],
            volumes=[1000, 2000, 8000, 3000, 4000],
        )
        # Multi-day drop ending on 2025-01-16, period_days=3
        drop = _make_drop(
            "2025-01-16", drop_pct=-14.3, close_price=90.0,
            period_days=3, drop_type="MULTI_DAY",
        )
        enrich_drops_with_prices_and_volume([drop], history)

        # from_price = close of day before 3-day period start
        # 3-day period ending 2025-01-16 starts at 2025-01-14 (index 2)
        # prior day = 2025-01-13 (index 1) -> 105.0
        assert drop.from_price == 105.0
        # volume = max over the 3-day period (indices 2,3,4): max(8000,3000,4000)
        assert drop.volume == 8000

    def test_missing_date_handling(self) -> None:
        """Drop with no date is skipped (no crash)."""
        drop = StockDropEvent(
            drop_pct=_sourced_float(-5.0),
            drop_type="SINGLE_DAY",
        )
        history = _make_history(
            dates=["2025-01-15"],
            closes=[100.0],
            volumes=[1000],
        )
        enrich_drops_with_prices_and_volume([drop], history)
        assert drop.from_price is None
        assert drop.volume is None

    def test_drop_date_not_in_history(self) -> None:
        """Drop date missing from history: from_price and volume stay None."""
        history = _make_history(
            dates=["2025-01-13", "2025-01-14"],
            closes=[100.0, 105.0],
            volumes=[1000, 2000],
        )
        drop = _make_drop("2025-01-20", drop_pct=-5.0)
        enrich_drops_with_prices_and_volume([drop], history)

        assert drop.from_price is None
        assert drop.volume is None

    def test_first_date_drop_no_prior(self) -> None:
        """Drop on first date in history has no prior: from_price=None."""
        history = _make_history(
            dates=["2025-01-13", "2025-01-14"],
            closes=[100.0, 95.0],
            volumes=[1000, 2000],
        )
        drop = _make_drop("2025-01-13", drop_pct=-5.0)
        enrich_drops_with_prices_and_volume([drop], history)

        assert drop.from_price is None
        assert drop.volume == 1000

    def test_mutates_in_place(self) -> None:
        """Function returns None (mutates drops in-place)."""
        history = _make_history(
            dates=["2025-01-13", "2025-01-14"],
            closes=[100.0, 95.0],
            volumes=[1000, 2000],
        )
        drop = _make_drop("2025-01-14")
        result = enrich_drops_with_prices_and_volume([drop], history)
        assert result is None


# ---------------------------------------------------------------------------
# detect_stock_patterns
# ---------------------------------------------------------------------------


class TestDetectPatterns:
    """Tests for detect_stock_patterns."""

    def test_empty_drops(self) -> None:
        """No drops -> no patterns."""
        assert detect_stock_patterns([]) == []

    def test_post_ipo_arc(self) -> None:
        """Detects post-IPO arc: <500 trading days, >3 drops in first 180 calendar days."""
        # IPO-like: all drops in first 180 days, trading_days < 500
        drops = [
            _make_drop("2025-01-15", close_price=90.0),
            _make_drop("2025-02-10", close_price=85.0),
            _make_drop("2025-03-05", close_price=80.0),
            _make_drop("2025-04-01", close_price=75.0),
        ]
        patterns = detect_stock_patterns(drops, trading_days_available=200)
        types = [p["type"] for p in patterns]
        assert "post_ipo_arc" in types

    def test_no_post_ipo_arc_established_company(self) -> None:
        """No post-IPO arc when trading_days >= 500."""
        drops = [
            _make_drop("2025-01-15"),
            _make_drop("2025-02-10"),
            _make_drop("2025-03-05"),
            _make_drop("2025-04-01"),
        ]
        patterns = detect_stock_patterns(drops, trading_days_available=600)
        types = [p["type"] for p in patterns]
        assert "post_ipo_arc" not in types

    def test_multi_day_cluster(self) -> None:
        """Detects multi-day cluster: >=2 drops within 5 calendar days."""
        drops = [
            _make_drop("2025-03-10", close_price=100.0),
            _make_drop("2025-03-12", close_price=90.0),
        ]
        patterns = detect_stock_patterns(drops)
        types = [p["type"] for p in patterns]
        assert "multi_day_cluster" in types

    def test_no_cluster_when_far_apart(self) -> None:
        """No cluster when drops are >5 days apart."""
        drops = [
            _make_drop("2025-03-01", close_price=100.0),
            _make_drop("2025-03-20", close_price=90.0),
        ]
        patterns = detect_stock_patterns(drops)
        types = [p["type"] for p in patterns]
        assert "multi_day_cluster" not in types

    def test_support_level(self) -> None:
        """Detects support level: >=2 drops bounce near same price (+/-3%)."""
        drops = [
            _make_drop("2025-01-15", close_price=100.0),
            _make_drop("2025-03-20", close_price=101.5),  # within 3% of 100
        ]
        patterns = detect_stock_patterns(drops)
        types = [p["type"] for p in patterns]
        assert "support_level" in types

    def test_no_support_level_different_prices(self) -> None:
        """No support level when close prices differ by >3%."""
        drops = [
            _make_drop("2025-01-15", close_price=100.0),
            _make_drop("2025-03-20", close_price=120.0),  # >3% apart
        ]
        patterns = detect_stock_patterns(drops)
        types = [p["type"] for p in patterns]
        assert "support_level" not in types

    def test_lockup_expiry(self) -> None:
        """Detects lockup expiry: drop near 180 days post-IPO (170-190 range)."""
        # First drop is near start, second is around 180 days later
        drops = [
            _make_drop("2025-01-15", close_price=100.0),
            _make_drop("2025-07-14", close_price=80.0),  # ~180 days from first drop
        ]
        patterns = detect_stock_patterns(drops, trading_days_available=200)
        types = [p["type"] for p in patterns]
        assert "lockup_expiry" in types

    def test_pattern_dict_structure(self) -> None:
        """Each pattern dict has required keys: type, description, dates, do_relevance."""
        drops = [
            _make_drop("2025-03-10", close_price=100.0),
            _make_drop("2025-03-12", close_price=90.0),
        ]
        patterns = detect_stock_patterns(drops)
        assert len(patterns) > 0
        for p in patterns:
            assert "type" in p
            assert "description" in p
            assert "dates" in p
            assert "do_relevance" in p
