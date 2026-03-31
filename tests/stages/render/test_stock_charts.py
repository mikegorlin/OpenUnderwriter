"""Tests for Bloomberg dark theme stock chart generation pipeline.

Covers chart data extraction (correct key usage), PNG output,
5Y weekly aggregation, graceful ETF fallback, stats computation,
backward-compatible exports, and template chart embedding.
"""

from __future__ import annotations

import io
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.market import MarketSignals
from do_uw.models.market_events import StockDropAnalysis
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.render.charts.stock_chart_data import (
    ChartData,
    aggregate_weekly,
    compute_chart_stats,
    extract_chart_data,
)
from do_uw.stages.render.charts.stock_charts import (
    create_stock_chart,
    create_stock_performance_chart,
    create_stock_performance_chart_5y,
)
from do_uw.stages.render.design_system import configure_matplotlib_defaults

# Configure matplotlib once for all tests
configure_matplotlib_defaults()

_NOW = datetime(2025, 6, 15, tzinfo=UTC)

# PNG file signature (first 8 bytes).
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------


def _make_price_history(
    n_days: int,
    start_price: float = 100.0,
    daily_return: float = 0.001,
) -> dict[str, Any]:
    """Generate column-oriented price history dict.

    Args:
        n_days: Number of trading days.
        start_price: Starting price.
        daily_return: Daily fractional return (e.g., 0.001 = 0.1%/day).

    Returns:
        Dict with Date (ISO strings) and Close (float) lists.
    """
    from datetime import timedelta

    base_date = datetime(2024, 3, 1)
    dates: list[str] = []
    prices: list[float] = []
    price = start_price

    day_offset = 0
    for _ in range(n_days):
        # Skip weekends.
        current = base_date + timedelta(days=day_offset)
        while current.weekday() >= 5:
            day_offset += 1
            current = base_date + timedelta(days=day_offset)

        dates.append(current.strftime("%Y-%m-%d"))
        prices.append(round(price, 4))
        price *= 1 + daily_return
        day_offset += 1

    return {"Date": dates, "Close": prices}


def _sv(value: Any, source: str = "TEST") -> SourcedValue[Any]:
    """Create a test SourcedValue."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=Confidence.HIGH,
        as_of=_NOW,
    )


def _make_state_with_market(
    market_data: dict[str, Any],
    include_extracted: bool = False,
) -> AnalysisState:
    """Create AnalysisState with market_data in acquired_data.

    Args:
        market_data: Dict to place in acquired_data.market_data.
        include_extracted: If True, include ExtractedData with
            empty MarketSignals for drop filtering.
    """
    identity = CompanyIdentity(
        ticker="TEST",
        legal_name=_sv("Test Corp Inc."),
        cik=_sv("0001234567"),
        sic_code=_sv("7372"),
        sic_description=_sv("Software"),
        exchange=_sv("NASDAQ"),
        state_of_incorporation=_sv("DE"),
    )
    company = CompanyProfile(
        identity=identity,
        business_description=_sv("Test Corp."),
    )
    acquired = AcquiredData(market_data=market_data)

    extracted = None
    if include_extracted:
        extracted = ExtractedData(
            market=MarketSignals(stock_drops=StockDropAnalysis()),
        )

    return AnalysisState(
        ticker="TEST",
        company=company,
        acquired_data=acquired,
        extracted=extracted,
    )


# ---------------------------------------------------------------------------
# Test: correct key usage
# ---------------------------------------------------------------------------


class TestExtractChartDataKeys:
    """Verify extract_chart_data reads the correct market_data keys."""

    def test_extract_chart_data_correct_keys(self) -> None:
        """Reads history_1y (not price_history) for 1Y chart data."""
        hist = _make_price_history(30, start_price=100.0)
        etf_hist = _make_price_history(30, start_price=50.0)
        spy_hist = _make_price_history(30, start_price=450.0)

        market_data = {
            "history_1y": hist,
            "sector_history_1y": etf_hist,
            "spy_history_1y": spy_hist,
            "sector_etf": "XLK",
        }
        state = _make_state_with_market(market_data, include_extracted=True)
        data = extract_chart_data(state, "1Y")

        assert data is not None
        assert len(data.dates) == 30
        assert len(data.prices) == 30
        assert data.etf_prices is not None
        assert len(data.etf_prices) == 30
        assert data.spy_prices is not None
        assert len(data.spy_prices) == 30
        assert data.etf_ticker == "XLK"
        assert data.ticker == "TEST"
        assert data.period == "1Y"

    def test_extract_chart_data_no_data_returns_none(self) -> None:
        """Empty market_data returns None."""
        state = _make_state_with_market({}, include_extracted=True)
        data = extract_chart_data(state, "1Y")
        assert data is None

    def test_extract_chart_data_no_acquired_data(self) -> None:
        """State with acquired_data=None returns None."""
        identity = CompanyIdentity(
            ticker="TEST",
            legal_name=_sv("Test Corp Inc."),
            cik=_sv("0001234567"),
            sic_code=_sv("7372"),
            sic_description=_sv("Software"),
            exchange=_sv("NASDAQ"),
            state_of_incorporation=_sv("DE"),
        )
        state = AnalysisState(
            ticker="TEST",
            company=CompanyProfile(identity=identity, business_description=_sv("X")),
            acquired_data=None,
        )
        data = extract_chart_data(state, "1Y")
        assert data is None

    def test_extract_chart_data_insufficient_points(self) -> None:
        """Fewer than 5 data points returns None."""
        hist = _make_price_history(3, start_price=100.0)
        state = _make_state_with_market({"history_1y": hist}, include_extracted=True)
        data = extract_chart_data(state, "1Y")
        assert data is None


# ---------------------------------------------------------------------------
# Test: chart PNG generation
# ---------------------------------------------------------------------------


class TestChartGeneratesPng:
    """Verify create_stock_chart produces valid PNG BytesIO."""

    def test_chart_generates_png(self) -> None:
        """252-day history produces a PNG image."""
        hist = _make_price_history(252, start_price=150.0, daily_return=0.0005)
        etf_hist = _make_price_history(252, start_price=50.0, daily_return=0.0003)
        spy_hist = _make_price_history(252, start_price=450.0, daily_return=0.0004)

        market_data = {
            "history_1y": hist,
            "sector_history_1y": etf_hist,
            "spy_history_1y": spy_hist,
            "sector_etf": "XLK",
        }
        state = _make_state_with_market(market_data, include_extracted=True)
        result = create_stock_chart(state, "1Y")

        assert result is not None
        assert isinstance(result, io.BytesIO)
        # Check PNG signature.
        header = result.read(8)
        assert header == _PNG_SIGNATURE

    def test_chart_handles_missing_etf_gracefully(self) -> None:
        """Chart without sector ETF data still produces PNG."""
        hist = _make_price_history(30, start_price=100.0)
        spy_hist = _make_price_history(30, start_price=450.0)

        market_data = {
            "history_1y": hist,
            "spy_history_1y": spy_hist,
            # No sector_history_1y, no sector_etf
        }
        state = _make_state_with_market(market_data, include_extracted=True)
        result = create_stock_chart(state, "1Y")

        assert result is not None
        assert isinstance(result, io.BytesIO)
        header = result.read(8)
        assert header == _PNG_SIGNATURE

    def test_chart_no_spy_no_etf(self) -> None:
        """Chart with only company history still produces PNG."""
        hist = _make_price_history(30, start_price=100.0)
        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data, include_extracted=True)
        result = create_stock_chart(state, "1Y")

        assert result is not None
        assert isinstance(result, io.BytesIO)
        header = result.read(8)
        assert header == _PNG_SIGNATURE


# ---------------------------------------------------------------------------
# Test: 5Y weekly aggregation
# ---------------------------------------------------------------------------


class TestChart5YWeeklyAggregation:
    """Verify 5Y charts aggregate daily data to weekly."""

    def test_chart_5y_weekly_aggregation(self) -> None:
        """1260 daily data points -> ~260 weekly points after aggregation."""
        hist = _make_price_history(1260, start_price=100.0, daily_return=0.0002)
        market_data = {"history_5y": hist}
        state = _make_state_with_market(market_data, include_extracted=True)

        data = extract_chart_data(state, "5Y")
        assert data is not None
        # 1260 trading days / ~5 per week = ~252 weeks
        # With slight variation, should be roughly 245-260
        assert 240 <= len(data.dates) <= 265, f"Expected ~252 weekly points, got {len(data.dates)}"
        assert len(data.dates) == len(data.prices)

    def test_aggregate_weekly_preserves_order(self) -> None:
        """aggregate_weekly keeps last entry per ISO week, in order."""
        dates = [
            datetime(2025, 1, 6),   # Mon wk 2
            datetime(2025, 1, 7),   # Tue wk 2
            datetime(2025, 1, 8),   # Wed wk 2
            datetime(2025, 1, 13),  # Mon wk 3
            datetime(2025, 1, 14),  # Tue wk 3
        ]
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]

        w_dates, w_prices = aggregate_weekly(dates, prices)

        assert len(w_dates) == 2
        # Week 2: last is Wed Jan 8 -> 102.0
        assert w_dates[0] == datetime(2025, 1, 8)
        assert w_prices[0] == 102.0
        # Week 3: last is Tue Jan 14 -> 104.0
        assert w_dates[1] == datetime(2025, 1, 14)
        assert w_prices[1] == 104.0


# ---------------------------------------------------------------------------
# Test: compute_chart_stats
# ---------------------------------------------------------------------------


class TestComputeChartStats:
    """Verify stats computation from ChartData."""

    def test_compute_chart_stats(self) -> None:
        """Known prices produce correct stats."""
        data = ChartData(
            dates=[datetime(2025, 1, i) for i in range(1, 6)],
            prices=[100.0, 110.0, 90.0, 95.0, 120.0],
            etf_dates=[datetime(2025, 1, i) for i in range(1, 6)],
            etf_prices=[50.0, 51.0, 49.0, 50.0, 55.0],
            etf_ticker="XLK",
            spy_dates=None,
            spy_prices=None,
            drops=[],
            ticker="TEST",
            period="1Y",
        )
        stats = compute_chart_stats(data)

        # current_price = last price = 120.0
        assert stats["current_price"] == 120.0
        # high_52w = 120.0, low_52w = 90.0
        assert stats["high_52w"] == 120.0
        assert stats["low_52w"] == 90.0
        # total_return = (120 - 100) / 100 * 100 = 20.0%
        assert stats["total_return_pct"] == 20.0
        # sector_return = (55 - 50) / 50 * 100 = 10.0%
        assert stats["sector_return_pct"] == 10.0
        # alpha = 20.0 - 10.0 = 10.0%
        assert stats["alpha_pct"] == 10.0

    def test_compute_chart_stats_empty_prices(self) -> None:
        """Empty price list returns N/A."""
        data = ChartData(
            dates=[], prices=[],
            etf_dates=None, etf_prices=None, etf_ticker="",
            spy_dates=None, spy_prices=None,
            drops=[], ticker="TEST", period="1Y",
        )
        stats = compute_chart_stats(data)
        assert stats["current_price"] == "N/A"

    def test_compute_chart_stats_no_etf(self) -> None:
        """No ETF data -> sector_return_pct and alpha are None."""
        data = ChartData(
            dates=[datetime(2025, 1, i) for i in range(1, 6)],
            prices=[100.0, 110.0, 90.0, 95.0, 120.0],
            etf_dates=None, etf_prices=None, etf_ticker="",
            spy_dates=None, spy_prices=None,
            drops=[], ticker="TEST", period="1Y",
        )
        stats = compute_chart_stats(data)
        assert stats["sector_return_pct"] is None
        assert stats["alpha_pct"] is None
        assert stats["total_return_pct"] == 20.0


# ---------------------------------------------------------------------------
# Test: backward-compatible exports
# ---------------------------------------------------------------------------


class TestBackwardCompatExports:
    """Verify old function names still work."""

    def test_backward_compat_exports(self) -> None:
        """create_stock_performance_chart and _5y are importable."""
        # Just verify they exist and are callable.
        assert callable(create_stock_performance_chart)
        assert callable(create_stock_performance_chart_5y)

    def test_backward_compat_1y_delegates(self) -> None:
        """create_stock_performance_chart delegates to create_stock_chart."""
        hist = _make_price_history(30, start_price=100.0)
        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data, include_extracted=True)

        result = create_stock_performance_chart(state, period="1Y")
        assert result is not None
        assert isinstance(result, io.BytesIO)

    def test_backward_compat_5y_delegates(self) -> None:
        """create_stock_performance_chart_5y delegates to create_stock_chart."""
        hist = _make_price_history(30, start_price=100.0)
        market_data = {"history_5y": hist}
        state = _make_state_with_market(market_data, include_extracted=True)

        result = create_stock_performance_chart_5y(state)
        assert result is not None
        assert isinstance(result, io.BytesIO)


# ---------------------------------------------------------------------------
# Test: date/price length mismatch regression
# ---------------------------------------------------------------------------


class TestDatePriceMismatch:
    """Regression: yfinance can return different counts for dates vs prices."""

    def test_more_dates_than_prices(self) -> None:
        """Chart renders when dates list is longer than prices list."""
        # Simulate yfinance returning 252 dates but 251 prices
        hist = _make_price_history(252, start_price=180.0)
        hist["Date"].append("2025-03-01")  # Extra date with no price

        assert len(hist["Date"]) == 253
        assert len(hist["Close"]) == 252

        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data, include_extracted=True)

        result = create_stock_chart(state, period="1Y")
        assert result is not None
        assert isinstance(result, io.BytesIO)
        assert result.getvalue()[:8] == _PNG_SIGNATURE

    def test_more_prices_than_dates(self) -> None:
        """Chart renders when prices list is longer than dates list."""
        hist = _make_price_history(252, start_price=180.0)
        hist["Close"].append(200.0)  # Extra price with no date

        assert len(hist["Date"]) == 252
        assert len(hist["Close"]) == 253

        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data, include_extracted=True)

        result = create_stock_chart(state, period="1Y")
        assert result is not None
        assert isinstance(result, io.BytesIO)

    def test_equal_lengths_still_work(self) -> None:
        """Normal case: dates and prices have equal length."""
        hist = _make_price_history(252, start_price=180.0)
        assert len(hist["Date"]) == len(hist["Close"])

        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data, include_extracted=True)

        result = create_stock_chart(state, period="1Y")
        assert result is not None


# ---------------------------------------------------------------------------
# Test: template chart embedding
# ---------------------------------------------------------------------------


def _project_root() -> Path:
    """Find the project root by locating pyproject.toml."""
    p = Path(__file__).resolve().parent
    while p != p.parent:
        if (p / "pyproject.toml").exists():
            return p
        p = p.parent
    msg = "Could not find project root"
    raise RuntimeError(msg)


class TestTemplateChartEmbedding:
    """Verify MD and HTML templates reference chart images."""

    def test_md_template_embeds_chart_images(self) -> None:
        """market.md.j2 (included by worksheet) references stock_1y.png and stock_5y.png."""
        root = _project_root()
        # Chart refs live in the market section partial, not the root worksheet
        template_path = root / "src" / "do_uw" / "templates" / "markdown" / "sections" / "market.md.j2"
        assert template_path.exists(), f"Template not found: {template_path}"
        content = template_path.read_text()

        assert "stock_1y.png" in content, "MD market template missing stock_1y.png reference"
        assert "stock_5y.png" in content, "MD market template missing stock_5y.png reference"
        # Both should be conditional on chart_dir
        assert "chart_dir" in content, "MD market template missing chart_dir conditional"

    def test_html_template_embeds_chart_images(self) -> None:
        """HTML market stock_charts fragment references stock_1y (5Y moved to audit overflow)."""
        root = _project_root()
        # Phase 56-04: chart embeds moved to fragment file
        # Phase 123-02: condensed to 1Y only in main body; 5Y in audit overflow
        template_path = root / "src" / "do_uw" / "templates" / "html" / "sections" / "market" / "stock_charts.html.j2"
        assert template_path.exists(), f"Template not found: {template_path}"
        content = template_path.read_text()

        assert "stock_1y" in content, "HTML template missing stock_1y reference"
        assert "embed_chart" in content, "HTML template missing embed_chart macro"

        # stock_5y is in main body charts, not duplicated in audit overflow
        assert "stock_5y" in content, "HTML template missing stock_5y reference"

    def test_pdf_template_embeds_chart_images(self) -> None:
        """PDF template references stock_1y chart image."""
        root = _project_root()
        template_path = root / "src" / "do_uw" / "templates" / "pdf" / "worksheet.html.j2"
        assert template_path.exists(), f"Template not found: {template_path}"
        content = template_path.read_text()

        assert "stock_1y" in content, "PDF template missing stock_1y reference"
