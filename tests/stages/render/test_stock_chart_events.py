"""Tests for litigation event extraction and rendering on stock charts.

Covers:
- ChartData.litigation_events field (default empty list)
- _extract_litigation_events from state litigation data
- Filtering by date range, handling missing data
- render_litigation_markers overlay rendering
- Integration with create_stock_chart
"""

from __future__ import annotations

from dataclasses import fields as dc_fields
from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import SourcedValue
from do_uw.models.litigation import CaseDetail, LitigationLandscape
from do_uw.stages.render.charts.stock_chart_data import (
    ChartData,
    _extract_litigation_events,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv(value: object, source: str = "test") -> SourcedValue:
    """Build a SourcedValue with required fields."""
    return SourcedValue(value=value, source=source, confidence="HIGH", as_of="2025-01-01")


def _make_case(
    name: str,
    filing: date | None,
    case_type: str | None = "SCA",
) -> CaseDetail:
    """Build a minimal CaseDetail with filing_date."""
    return CaseDetail(
        case_name=_sv(name),
        filing_date=_sv(filing) if filing else None,
        coverage_type=_sv(case_type) if case_type else None,
    )


def _make_state_with_litigation(cases: list[CaseDetail]) -> MagicMock:
    """Build a mock AnalysisState with litigation cases."""
    lit = LitigationLandscape(securities_class_actions=cases)
    extracted = MagicMock()
    extracted.litigation = lit
    state = MagicMock()
    state.extracted = extracted
    return state


# ---------------------------------------------------------------------------
# Test 1: ChartData has litigation_events field defaulting to empty list
# ---------------------------------------------------------------------------


def test_chart_data_has_litigation_events_field() -> None:
    """ChartData dataclass includes litigation_events with empty default."""
    field_names = [f.name for f in dc_fields(ChartData)]
    assert "litigation_events" in field_names

    # Default value is empty list
    data = ChartData(
        dates=[datetime(2025, 1, 1)],
        prices=[100.0],
        etf_dates=None,
        etf_prices=None,
        etf_ticker="XLF",
        spy_dates=None,
        spy_prices=None,
        drops=[],
        ticker="TEST",
        period="1Y",
    )
    assert data.litigation_events == []


# ---------------------------------------------------------------------------
# Test 2: extract populates litigation_events from state
# ---------------------------------------------------------------------------


def test_extract_litigation_events_from_state() -> None:
    """Litigation events are extracted from state.extracted.litigation."""
    cases = [
        _make_case("In re Acme Securities Lit.", date(2025, 3, 15), "SCA"),
        _make_case("Smith v. Acme Corp", date(2025, 6, 20), "derivative"),
    ]
    state = _make_state_with_litigation(cases)
    chart_dates = [datetime(2025, 1, 1), datetime(2025, 12, 31)]

    events = _extract_litigation_events(state, chart_dates)

    assert len(events) == 2
    assert events[0]["date"] == datetime(2025, 3, 15)
    assert events[0]["case_name"] == "In re Acme Securities Lit."
    assert events[0]["case_type"] == "SCA"
    assert events[1]["date"] == datetime(2025, 6, 20)


# ---------------------------------------------------------------------------
# Test 3: Cases without filing_date are skipped
# ---------------------------------------------------------------------------


def test_extract_skips_cases_without_filing_date() -> None:
    """Cases with filing_date=None are gracefully skipped."""
    cases = [
        _make_case("Has Date", date(2025, 5, 1), "SCA"),
        _make_case("No Date", None, "SCA"),
    ]
    state = _make_state_with_litigation(cases)
    chart_dates = [datetime(2025, 1, 1), datetime(2025, 12, 31)]

    events = _extract_litigation_events(state, chart_dates)

    assert len(events) == 1
    assert events[0]["case_name"] == "Has Date"


# ---------------------------------------------------------------------------
# Test 4: Cases with filing_date outside chart range are excluded
# ---------------------------------------------------------------------------


def test_extract_filters_by_date_range() -> None:
    """Only events within chart_dates range are included."""
    cases = [
        _make_case("Before", date(2024, 6, 1), "SCA"),
        _make_case("Inside", date(2025, 6, 1), "SCA"),
        _make_case("After", date(2026, 6, 1), "SCA"),
    ]
    state = _make_state_with_litigation(cases)
    chart_dates = [datetime(2025, 1, 1), datetime(2025, 12, 31)]

    events = _extract_litigation_events(state, chart_dates)

    assert len(events) == 1
    assert events[0]["case_name"] == "Inside"


# ---------------------------------------------------------------------------
# Test 5: Each event dict has expected keys
# ---------------------------------------------------------------------------


def test_event_dict_has_required_keys() -> None:
    """Each litigation event dict has date, case_name, case_type."""
    cases = [_make_case("Test Case", date(2025, 4, 10), "SEC enforcement")]
    state = _make_state_with_litigation(cases)
    chart_dates = [datetime(2025, 1, 1), datetime(2025, 12, 31)]

    events = _extract_litigation_events(state, chart_dates)

    assert len(events) == 1
    event = events[0]
    assert "date" in event
    assert "case_name" in event
    assert "case_type" in event
    assert isinstance(event["date"], datetime)
    assert isinstance(event["case_name"], str)


# ---------------------------------------------------------------------------
# Test 6: render_litigation_markers draws vertical lines
# ---------------------------------------------------------------------------


def test_render_litigation_markers_draws_lines() -> None:
    """render_litigation_markers calls axvline for each litigation event."""
    from do_uw.stages.render.charts.stock_chart_overlays import render_litigation_markers

    data = ChartData(
        dates=[datetime(2025, 1, 1), datetime(2025, 12, 31)],
        prices=[100.0, 110.0],
        etf_dates=None,
        etf_prices=None,
        etf_ticker="XLF",
        spy_dates=None,
        spy_prices=None,
        drops=[],
        ticker="TEST",
        period="1Y",
        litigation_events=[
            {"date": datetime(2025, 3, 15), "case_name": "Acme SCA", "case_type": "SCA"},
            {"date": datetime(2025, 8, 1), "case_name": "Smith v. Acme", "case_type": None},
        ],
    )
    ax = MagicMock()
    ax.get_ylim.return_value = (90.0, 120.0)
    c = {"litigation_line": "#FF6D00", "litigation_text": "#FF6D00"}

    render_litigation_markers(ax, data, c)

    # Should draw 2 vertical lines
    assert ax.axvline.call_count == 2


# ---------------------------------------------------------------------------
# Test 7: Uses distinct color and "L" label
# ---------------------------------------------------------------------------


def test_render_litigation_markers_uses_distinct_style() -> None:
    """Markers use orange color and 'L' label (distinct from earnings 'E')."""
    from do_uw.stages.render.charts.stock_chart_overlays import render_litigation_markers

    data = ChartData(
        dates=[datetime(2025, 1, 1), datetime(2025, 12, 31)],
        prices=[100.0, 110.0],
        etf_dates=None,
        etf_prices=None,
        etf_ticker="XLF",
        spy_dates=None,
        spy_prices=None,
        drops=[],
        ticker="TEST",
        period="1Y",
        litigation_events=[
            {"date": datetime(2025, 5, 1), "case_name": "Test Case v. Corp", "case_type": "SCA"},
        ],
    )
    ax = MagicMock()
    ax.get_ylim.return_value = (90.0, 120.0)
    c = {"litigation_line": "#FF6D00", "litigation_text": "#FF6D00"}

    render_litigation_markers(ax, data, c)

    # Check axvline uses dash-dot style and orange color
    call_kwargs = ax.axvline.call_args
    assert call_kwargs.kwargs.get("linestyle") == "-." or call_kwargs[1].get("linestyle") == "-."
    assert call_kwargs.kwargs.get("color") == "#FF6D00" or call_kwargs[1].get("color") == "#FF6D00"

    # Check text call includes "L" label
    text_calls = ax.text.call_args_list
    assert len(text_calls) >= 1
    # First text call should be the "L" label
    first_text_args = text_calls[0]
    assert first_text_args[0][2] == "L"  # Third positional arg is the text


# ---------------------------------------------------------------------------
# Test 8: Empty litigation_events produces no markers
# ---------------------------------------------------------------------------


def test_render_litigation_markers_empty_events() -> None:
    """No crash or markers when litigation_events is empty."""
    from do_uw.stages.render.charts.stock_chart_overlays import render_litigation_markers

    data = ChartData(
        dates=[datetime(2025, 1, 1), datetime(2025, 12, 31)],
        prices=[100.0, 110.0],
        etf_dates=None,
        etf_prices=None,
        etf_ticker="XLF",
        spy_dates=None,
        spy_prices=None,
        drops=[],
        ticker="TEST",
        period="1Y",
        litigation_events=[],
    )
    ax = MagicMock()
    c = {"litigation_line": "#FF6D00", "litigation_text": "#FF6D00"}

    render_litigation_markers(ax, data, c)

    ax.axvline.assert_not_called()
    ax.text.assert_not_called()


# ---------------------------------------------------------------------------
# Test 9: Integration -- create_stock_chart with litigation events renders
# ---------------------------------------------------------------------------


def test_create_stock_chart_with_litigation_events() -> None:
    """create_stock_chart renders successfully when litigation events are present."""
    from do_uw.stages.render.charts.stock_charts import create_stock_chart

    # Build a synthetic state with enough data for chart rendering
    state = MagicMock()
    state.ticker = "TEST"
    state.extracted = MagicMock()
    state.extracted.market = MagicMock()
    state.extracted.market.stock = MagicMock()
    state.extracted.market.stock_drops = MagicMock()
    state.extracted.market.stock_drops.single_day_drops = []
    state.extracted.market.stock_drops.multi_day_drops = []

    # Return decomposition stubs
    for attr in [
        "returns_1y_market", "returns_1y_sector", "returns_1y_company",
        "mdd_ratio_1y", "sector_mdd_1y", "max_drawdown_1y",
    ]:
        setattr(state.extracted.market.stock, attr, None)

    # Litigation data
    cases = [_make_case("Test SCA", date(2025, 6, 15), "SCA")]
    state.extracted.litigation = LitigationLandscape(securities_class_actions=cases)

    # Build price history for 1Y
    dates_str = [f"2025-{m:02d}-01" for m in range(1, 13)]
    prices = [100.0 + i * 2.0 for i in range(12)]
    volumes = [1_000_000.0] * 12

    state.acquired_data = MagicMock()
    state.acquired_data.market_data = {
        "history_1y": {
            "Close": prices,
            "Date": dates_str,
            "Volume": volumes,
        },
        "sector_etf": "XLF",
        "info": {"beta": 1.1},
    }

    result = create_stock_chart(state, period="1Y", format="png")
    # Should return a BytesIO (PNG) without crashing
    assert result is not None
