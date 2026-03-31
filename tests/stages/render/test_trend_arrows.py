"""Tests for SVG trend arrow generator (INFO-04).

Covers render_trend_arrow and trend_direction helper.
"""

from __future__ import annotations

from do_uw.stages.render.charts.trend_arrows import (
    render_trend_arrow,
    trend_direction,
)


class TestTrendArrowOutput:
    """render_trend_arrow produces valid SVG."""

    def test_up_returns_svg(self) -> None:
        result = render_trend_arrow("up")
        assert result.strip().startswith("<svg")
        assert "<path" in result

    def test_down_returns_svg(self) -> None:
        result = render_trend_arrow("down")
        assert result.strip().startswith("<svg")
        assert "<path" in result

    def test_flat_returns_svg_with_line(self) -> None:
        result = render_trend_arrow("flat")
        assert result.strip().startswith("<svg")
        assert "<line" in result

    def test_invalid_direction_returns_empty(self) -> None:
        result = render_trend_arrow("sideways")
        assert result == ""

    def test_empty_direction_returns_empty(self) -> None:
        result = render_trend_arrow("")
        assert result == ""


class TestTrendArrowColors:
    """Arrow colors match expected semantics."""

    def test_up_uses_green(self) -> None:
        result = render_trend_arrow("up")
        assert "#059669" in result

    def test_down_uses_red(self) -> None:
        result = render_trend_arrow("down")
        assert "#DC2626" in result

    def test_flat_uses_gray(self) -> None:
        result = render_trend_arrow("flat")
        assert "#6B7280" in result

    def test_inverted_up_uses_red(self) -> None:
        result = render_trend_arrow("up", inverted=True)
        assert "#DC2626" in result

    def test_inverted_down_uses_green(self) -> None:
        result = render_trend_arrow("down", inverted=True)
        assert "#059669" in result

    def test_custom_color_overrides(self) -> None:
        result = render_trend_arrow("up", color="#FF00FF")
        assert "#FF00FF" in result


class TestTrendArrowOptions:
    """Size and label options."""

    def test_custom_size(self) -> None:
        result = render_trend_arrow("up", size=20)
        assert "viewBox=\"0 0 20 20\"" in result
        assert "width:20px" in result

    def test_label_as_title(self) -> None:
        result = render_trend_arrow("up", label="Revenue trending up")
        assert 'title="Revenue trending up"' in result

    def test_no_label_no_title(self) -> None:
        result = render_trend_arrow("up")
        assert "title=" not in result


class TestTrendDirection:
    """trend_direction detects direction from two values."""

    def test_increase_returns_up(self) -> None:
        assert trend_direction(110.0, 100.0) == "up"

    def test_decrease_returns_down(self) -> None:
        assert trend_direction(90.0, 100.0) == "down"

    def test_small_change_returns_flat(self) -> None:
        assert trend_direction(101.0, 100.0) == "flat"

    def test_none_current_returns_flat(self) -> None:
        assert trend_direction(None, 100.0) == "flat"

    def test_none_previous_returns_flat(self) -> None:
        assert trend_direction(100.0, None) == "flat"

    def test_zero_previous_positive_current(self) -> None:
        assert trend_direction(10.0, 0.0) == "up"

    def test_zero_previous_negative_current(self) -> None:
        assert trend_direction(-5.0, 0.0) == "down"

    def test_zero_previous_zero_current(self) -> None:
        assert trend_direction(0.0, 0.0) == "flat"

    def test_custom_threshold(self) -> None:
        # 5% change with 10% threshold = flat
        assert trend_direction(105.0, 100.0, threshold_pct=10.0) == "flat"
        # 15% change with 10% threshold = up
        assert trend_direction(115.0, 100.0, threshold_pct=10.0) == "up"
