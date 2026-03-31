"""Tests for SVG chart output pipeline (CHART-01, CHART-02, CHART-05).

Covers save_chart_to_svg helper, SVG format parameter for stock/radar/ownership
charts, and backward compatibility with PNG BytesIO output.
"""

from __future__ import annotations

import io
import re
from datetime import UTC, datetime
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.market import MarketSignals
from do_uw.models.market_events import StockDropAnalysis
from do_uw.models.scoring import FactorScore
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.render.design_system import configure_matplotlib_defaults

# Configure matplotlib once for all tests
configure_matplotlib_defaults()

_NOW = datetime(2025, 6, 15, tzinfo=UTC)
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------


def _sv(value: Any, source: str = "TEST") -> SourcedValue[Any]:
    """Create a test SourcedValue."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=Confidence.HIGH,
        as_of=_NOW,
    )


def _make_price_history(
    n_days: int,
    start_price: float = 100.0,
    daily_return: float = 0.001,
) -> dict[str, Any]:
    """Generate column-oriented price history dict."""
    from datetime import timedelta

    base_date = datetime(2024, 3, 1)
    dates: list[str] = []
    prices: list[float] = []
    price = start_price

    day_offset = 0
    for _ in range(n_days):
        current = base_date + timedelta(days=day_offset)
        while current.weekday() >= 5:
            day_offset += 1
            current = base_date + timedelta(days=day_offset)
        dates.append(current.strftime("%Y-%m-%d"))
        prices.append(round(price, 4))
        price *= 1 + daily_return
        day_offset += 1

    return {"Date": dates, "Close": prices}


def _make_state_with_market(
    market_data: dict[str, Any],
) -> AnalysisState:
    """Create AnalysisState with market_data in acquired_data."""
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
    extracted = ExtractedData(
        market=MarketSignals(stock_drops=StockDropAnalysis()),
    )
    return AnalysisState(
        ticker="TEST",
        company=company,
        acquired_data=acquired,
        extracted=extracted,
    )


def _make_factor_scores() -> list[FactorScore]:
    """Create minimal factor scores for radar chart testing."""
    return [
        FactorScore(
            factor_id=f"F{i}",
            factor_name=f"Factor {i}",
            max_points=10.0,
            points_deducted=float(i),
        )
        for i in range(1, 6)
    ]


# ---------------------------------------------------------------------------
# Test: save_chart_to_svg helper
# ---------------------------------------------------------------------------


class TestSaveChartToSvg:
    """Verify save_chart_to_svg returns clean inline SVG strings."""

    def test_returns_string_starting_with_svg(self) -> None:
        """save_chart_to_svg returns a string that starts with '<svg'."""
        from do_uw.stages.render.chart_helpers import save_chart_to_svg

        matplotlib.use("Agg")
        fig: Figure
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])

        result = save_chart_to_svg(fig)
        assert isinstance(result, str)
        assert result.strip().startswith("<svg")

    def test_svg_contains_viewbox(self) -> None:
        """SVG output contains a viewBox attribute for responsive sizing."""
        from do_uw.stages.render.chart_helpers import save_chart_to_svg

        matplotlib.use("Agg")
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])

        result = save_chart_to_svg(fig)
        assert "viewBox" in result

    def test_svg_does_not_contain_xml_declaration(self) -> None:
        """SVG string does NOT contain XML declaration for inline embedding."""
        from do_uw.stages.render.chart_helpers import save_chart_to_svg

        matplotlib.use("Agg")
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])

        result = save_chart_to_svg(fig)
        assert "<?xml" not in result

    def test_svg_has_width_100_percent(self) -> None:
        """SVG root has width='100%' for responsive sizing."""
        from do_uw.stages.render.chart_helpers import save_chart_to_svg

        matplotlib.use("Agg")
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])

        result = save_chart_to_svg(fig)
        assert 'width="100%"' in result

    def test_closes_figure_after_save(self) -> None:
        """save_chart_to_svg closes the figure to prevent memory leaks."""
        from do_uw.stages.render.chart_helpers import save_chart_to_svg

        matplotlib.use("Agg")
        fig, ax = plt.subplots(figsize=(4, 3))
        ax.plot([1, 2, 3], [1, 4, 9])

        _ = save_chart_to_svg(fig)
        # After close, fig.get_axes() should return empty or raise
        assert len(fig.get_axes()) == 0 or not plt.fignum_exists(fig.number)


# ---------------------------------------------------------------------------
# Test: stock chart SVG format
# ---------------------------------------------------------------------------


class TestStockChartSvgFormat:
    """Verify create_stock_chart with format='svg' returns SVG string."""

    def test_svg_format_returns_string(self) -> None:
        """create_stock_chart with format='svg' returns str type."""
        from do_uw.stages.render.charts.stock_charts import create_stock_chart

        hist = _make_price_history(30, start_price=100.0)
        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data)

        result = create_stock_chart(state, period="1Y", format="svg")
        assert result is not None
        assert isinstance(result, str)
        assert result.strip().startswith("<svg")

    def test_png_format_returns_bytesio(self) -> None:
        """create_stock_chart with format='png' still returns BytesIO."""
        from do_uw.stages.render.charts.stock_charts import create_stock_chart

        hist = _make_price_history(30, start_price=100.0)
        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data)

        result = create_stock_chart(state, period="1Y", format="png")
        assert result is not None
        assert isinstance(result, io.BytesIO)
        header = result.read(8)
        assert header == _PNG_SIGNATURE

    def test_default_format_is_png(self) -> None:
        """create_stock_chart without format param returns BytesIO (PNG)."""
        from do_uw.stages.render.charts.stock_charts import create_stock_chart

        hist = _make_price_history(30, start_price=100.0)
        market_data = {"history_1y": hist}
        state = _make_state_with_market(market_data)

        result = create_stock_chart(state, period="1Y")
        assert result is not None
        assert isinstance(result, io.BytesIO)

    def test_aliases_pass_through_format(self) -> None:
        """Backward-compat aliases support format parameter."""
        from do_uw.stages.render.charts.stock_charts import (
            create_stock_performance_chart,
            create_stock_performance_chart_5y,
        )

        hist = _make_price_history(30, start_price=100.0)
        state_1y = _make_state_with_market({"history_1y": hist})
        result_1y = create_stock_performance_chart(state_1y, format="svg")
        assert result_1y is not None
        assert isinstance(result_1y, str)

        state_5y = _make_state_with_market({"history_5y": hist})
        result_5y = create_stock_performance_chart_5y(state_5y, format="svg")
        assert result_5y is not None
        assert isinstance(result_5y, str)


# ---------------------------------------------------------------------------
# Test: radar chart SVG format
# ---------------------------------------------------------------------------


class TestRadarChartSvgFormat:
    """Verify create_radar_chart with format='svg' returns SVG string."""

    def test_svg_format_returns_string(self) -> None:
        """create_radar_chart with format='svg' returns str type."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart
        from do_uw.stages.render.design_system import DesignSystem

        ds = DesignSystem()
        factor_scores = _make_factor_scores()

        result = create_radar_chart(factor_scores, ds, format="svg")
        assert result is not None
        assert isinstance(result, str)
        assert result.strip().startswith("<svg")

    def test_png_format_returns_bytesio(self) -> None:
        """create_radar_chart with format='png' still returns BytesIO."""
        from do_uw.stages.render.charts.radar_chart import create_radar_chart
        from do_uw.stages.render.design_system import DesignSystem

        ds = DesignSystem()
        factor_scores = _make_factor_scores()

        result = create_radar_chart(factor_scores, ds, format="png")
        assert result is not None
        assert isinstance(result, io.BytesIO)


# ---------------------------------------------------------------------------
# Test: ownership chart SVG format
# ---------------------------------------------------------------------------


class TestOwnershipChartSvgFormat:
    """Verify create_ownership_chart with format='svg' returns SVG string."""

    def test_svg_format_returns_string(self) -> None:
        """create_ownership_chart with format='svg' returns str type."""
        from do_uw.stages.render.charts.ownership_chart import (
            create_ownership_chart,
        )
        from do_uw.stages.render.design_system import DesignSystem
        from do_uw.models.governance_forensics import OwnershipAnalysis

        ds = DesignSystem()
        ownership = OwnershipAnalysis(
            institutional_pct=_sv(65.0),
            insider_pct=_sv(10.0),
            top_holders=[],
        )

        result = create_ownership_chart(ownership, ds, format="svg")
        assert result is not None
        assert isinstance(result, str)
        assert result.strip().startswith("<svg")

    def test_png_format_returns_bytesio(self) -> None:
        """create_ownership_chart with format='png' still returns BytesIO."""
        from do_uw.stages.render.charts.ownership_chart import (
            create_ownership_chart,
        )
        from do_uw.stages.render.design_system import DesignSystem
        from do_uw.models.governance_forensics import OwnershipAnalysis

        ds = DesignSystem()
        ownership = OwnershipAnalysis(
            institutional_pct=_sv(65.0),
            insider_pct=_sv(10.0),
            top_holders=[],
        )

        result = create_ownership_chart(ownership, ds, format="png")
        assert result is not None
        assert isinstance(result, io.BytesIO)


# ---------------------------------------------------------------------------
# Test: timeline chart SVG format (CHART-06)
# ---------------------------------------------------------------------------


class TestTimelineChartSvgFormat:
    """Verify timeline chart supports SVG output format."""

    def test_timeline_svg_format_parameter(self) -> None:
        """create_litigation_timeline accepts format='svg' without error."""
        from do_uw.stages.render.charts.timeline_chart import (
            create_litigation_timeline,
        )
        from do_uw.stages.render.design_system import (
            CREDIT_REPORT_LIGHT,
            DesignSystem,
        )

        # State with no timeline events returns None
        state = _make_state_with_market({})
        ds = DesignSystem()
        result = create_litigation_timeline(
            state, ds, colors=CREDIT_REPORT_LIGHT, format="svg",
        )
        # No events = None, but format param accepted
        assert result is None


# ---------------------------------------------------------------------------
# Test: sparkline context builder integration (CHART-03)
# ---------------------------------------------------------------------------


class TestSparklineContextIntegration:
    """Verify sparkline SVGs flow through context builders."""

    def test_market_extract_includes_stock_sparkline_key(self) -> None:
        """extract_market returns stock_sparkline key."""
        from do_uw.stages.render.context_builders.market import extract_market

        hist = _make_price_history(60, start_price=100.0)
        state = _make_state_with_market({"history_1y": hist})
        ctx = extract_market(state)
        assert "stock_sparkline" in ctx
        # With 60 days of data, sparkline should be non-empty
        assert ctx["stock_sparkline"] != ""
        assert ctx["stock_sparkline"].startswith("<svg")

    def test_market_extract_empty_history(self) -> None:
        """extract_market returns empty sparkline with no history."""
        from do_uw.stages.render.context_builders.market import extract_market

        state = _make_state_with_market({})
        ctx = extract_market(state)
        assert ctx.get("stock_sparkline") == ""
