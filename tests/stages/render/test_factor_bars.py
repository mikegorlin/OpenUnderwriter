"""Tests for SVG horizontal factor bar generator (INFO-03).

Covers render_factor_bar and render_factor_bar_set: pure SVG bar generation
for scoring factor visualization in the worksheet.
"""

from __future__ import annotations

from do_uw.stages.render.charts.factor_bars import (
    render_factor_bar,
    render_factor_bar_set,
)


class TestFactorBarBasic:
    """render_factor_bar produces valid SVG."""

    def test_returns_svg_string(self) -> None:
        result = render_factor_bar(5.0, 10.0)
        assert result.strip().startswith("<svg")
        assert result.strip().endswith("</svg>")

    def test_zero_max_returns_empty(self) -> None:
        result = render_factor_bar(0.0, 0.0)
        assert result == ""

    def test_negative_max_returns_empty(self) -> None:
        result = render_factor_bar(5.0, -1.0)
        assert result == ""

    def test_contains_viewbox(self) -> None:
        result = render_factor_bar(3.0, 8.0)
        assert "viewBox" in result


class TestFactorBarColors:
    """Different severity levels use correct colors."""

    def test_critical_color_above_60pct(self) -> None:
        result = render_factor_bar(7.0, 10.0)
        assert "#DC2626" in result  # Critical red

    def test_elevated_color_30_to_60pct(self) -> None:
        result = render_factor_bar(4.0, 10.0)
        assert "#EA580C" in result  # Elevated orange

    def test_minor_color_above_zero(self) -> None:
        result = render_factor_bar(1.0, 10.0)
        assert "#D4A843" in result  # Gold/amber

    def test_zero_shows_track_only(self) -> None:
        result = render_factor_bar(0.0, 10.0)
        assert "#F3F4F6" in result  # Track background only
        # No fill bar beyond the track
        assert result.count("<rect") == 1  # Only the track rect


class TestFactorBarLabel:
    """Label display options."""

    def test_shows_label_by_default(self) -> None:
        result = render_factor_bar(5.0, 10.0)
        assert "5/10" in result

    def test_no_label_when_disabled(self) -> None:
        result = render_factor_bar(5.0, 10.0, show_label=False)
        assert "5/10" not in result

    def test_decimal_points_shown(self) -> None:
        result = render_factor_bar(3.5, 8.0)
        assert "3.5/8" in result

    def test_integer_no_decimal(self) -> None:
        result = render_factor_bar(3.0, 8.0)
        assert "3/8" in result


class TestFactorBarSet:
    """render_factor_bar_set adds SVG to factor dicts."""

    def test_adds_bar_svg_key(self) -> None:
        factors = [
            {"score": 5.0, "max": 10.0},
            {"score": 0.0, "max": 8.0},
        ]
        result = render_factor_bar_set(factors)
        assert all("bar_svg" in f for f in result)

    def test_nonzero_factor_has_svg(self) -> None:
        factors = [{"score": 5.0, "max": 10.0}]
        result = render_factor_bar_set(factors)
        assert result[0]["bar_svg"].startswith("<svg")

    def test_zero_max_factor_empty_svg(self) -> None:
        factors = [{"score": 0.0, "max": 0.0}]
        result = render_factor_bar_set(factors)
        assert result[0]["bar_svg"] == ""

    def test_preserves_original_keys(self) -> None:
        factors = [{"score": 3.0, "max": 8.0, "name": "F1"}]
        result = render_factor_bar_set(factors)
        assert result[0]["name"] == "F1"


class TestFactorBarCustomSize:
    """Custom width/height respected."""

    def test_custom_dimensions(self) -> None:
        result = render_factor_bar(5.0, 10.0, width=200, height=20)
        assert "viewBox=\"0 0 200 20\"" in result
        assert "width:200px" in result
