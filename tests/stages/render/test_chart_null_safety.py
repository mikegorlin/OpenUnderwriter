"""Tests for null-safe chart decorator and placeholder generator.

Verifies that chart builders return None (not crash) when given
None/missing data, and that the placeholder generator creates valid PNGs.
"""

from __future__ import annotations

import io
import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.stages.render.charts.chart_guards import (
    create_chart_placeholder,
    null_safe_chart,
)


# ---------------------------------------------------------------------------
# Tests 1-5: Decorator and placeholder unit tests
# ---------------------------------------------------------------------------


def test_null_safe_chart_returns_none_on_attribute_error() -> None:
    """Test 1: @null_safe_chart returns None when inner raises AttributeError."""

    @null_safe_chart
    def bad_chart() -> str:
        raise AttributeError("NoneType has no attribute 'market_data'")

    result = bad_chart()
    assert result is None


def test_null_safe_chart_returns_none_on_type_error() -> None:
    """Test 2: @null_safe_chart returns None when inner raises TypeError."""

    @null_safe_chart
    def bad_chart() -> str:
        raise TypeError("unsupported operand type(s)")

    result = bad_chart()
    assert result is None


def test_null_safe_chart_passes_through_normal_result() -> None:
    """Test 3: @null_safe_chart returns normal result when no exception."""

    @null_safe_chart
    def good_chart() -> str:
        return "chart_data"

    result = good_chart()
    assert result == "chart_data"


def test_null_safe_chart_logs_warning(caplog: pytest.LogCaptureFixture) -> None:
    """Test 4: @null_safe_chart logs warning with function name and exception."""

    @null_safe_chart
    def my_chart_fn() -> str:
        raise KeyError("missing_key")

    with caplog.at_level(logging.WARNING):
        result = my_chart_fn()

    assert result is None
    assert "my_chart_fn" in caplog.text
    assert "missing_key" in caplog.text


def test_create_chart_placeholder_returns_valid_png() -> None:
    """Test 5: create_chart_placeholder returns BytesIO with valid PNG data."""
    buf = create_chart_placeholder(800, 400, "No data available")
    assert isinstance(buf, io.BytesIO)
    data = buf.read()
    # PNG magic bytes
    assert data[:4] == b"\x89PNG"
    assert len(data) > 100  # Non-trivial size


# ---------------------------------------------------------------------------
# Tests 6-10: Integration tests with actual chart builders
# ---------------------------------------------------------------------------


def test_create_stock_chart_none_market_data() -> None:
    """Test 6: create_stock_chart with None market_data returns None."""
    from do_uw.stages.render.charts.stock_charts import create_stock_chart

    state = MagicMock()
    state.acquired_data = None
    result = create_stock_chart(state)
    assert result is None


def test_create_drop_analysis_chart_none_drops() -> None:
    """Test 7: create_drop_analysis_chart with None stock_drops returns None."""
    from do_uw.stages.render.charts.drop_analysis_chart import (
        create_drop_analysis_chart,
    )

    state = MagicMock()
    state.acquired_data = None
    result = create_drop_analysis_chart(state)
    assert result is None


def test_create_radar_chart_none_factor_scores() -> None:
    """Test 8: create_radar_chart with None factor_scores returns None."""
    from do_uw.stages.render.charts.radar_chart import create_radar_chart
    from do_uw.stages.render.design_system import DesignSystem

    ds = DesignSystem()
    # Pass None instead of list[FactorScore]
    result = create_radar_chart(None, ds)  # type: ignore[arg-type]
    assert result is None


def test_create_ownership_chart_none_data() -> None:
    """Test 9: create_ownership_chart with None ownership data returns None."""
    from do_uw.stages.render.charts.ownership_chart import create_ownership_chart
    from do_uw.stages.render.design_system import DesignSystem

    ds = DesignSystem()
    result = create_ownership_chart(None, ds)
    assert result is None


def test_create_litigation_timeline_none_data() -> None:
    """Test 10: create_litigation_timeline with None litigation data returns None."""
    from do_uw.stages.render.charts.timeline_chart import create_litigation_timeline
    from do_uw.stages.render.design_system import DesignSystem

    state = MagicMock()
    state.extracted = None
    state.acquired_data = None
    ds = DesignSystem()
    result = create_litigation_timeline(state, ds)
    assert result is None
