"""Tests for inline SVG sparkline generator (CHART-03).

Covers render_sparkline: pure SVG generation for inline trend indicators.
No matplotlib dependency -- sparklines are pure string-built SVG.
"""

from __future__ import annotations


class TestSparklineEmpty:
    """render_sparkline handles edge cases gracefully."""

    def test_empty_list_returns_empty_string(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        assert render_sparkline([]) == ""

    def test_single_value_returns_svg(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([42.0])
        assert result.strip().startswith("<svg")
        # Single value = horizontal line
        assert "line" in result.lower() or "L" in result or "M" in result


class TestSparklineSvgOutput:
    """render_sparkline returns proper inline SVG."""

    def test_five_values_returns_svg_with_path(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 12, 11, 15, 14])
        assert isinstance(result, str)
        assert result.strip().startswith("<svg")
        assert "<path" in result

    def test_svg_contains_viewbox(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 12, 11, 15, 14])
        assert "viewBox" in result

    def test_svg_does_not_contain_xml_declaration(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 12, 11, 15, 14])
        assert "<?xml" not in result

    def test_custom_width_height_in_viewbox(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 20, 30], width=100, height=24)
        assert 'viewBox="0 0 100 24"' in result

    def test_svg_has_preserve_aspect_ratio(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 20, 30])
        assert "preserveAspectRatio" in result


class TestSparklineDirection:
    """Auto-detect and explicit direction control."""

    def test_auto_up(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 20])
        # Up direction uses green (#16A34A)
        assert "#16A34A" in result or "#16a34a" in result.lower()

    def test_auto_down(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([20, 10])
        # Down direction uses red (#B91C1C)
        assert "#B91C1C" in result or "#b91c1c" in result.lower()

    def test_auto_flat(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 10])
        # Flat direction uses gray (#6B7280)
        assert "#6B7280" in result or "#6b7280" in result.lower()

    def test_explicit_direction_overrides_auto(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        # Data goes up, but force "down" direction
        result = render_sparkline([10, 20], direction="down")
        assert "#B91C1C" in result or "#b91c1c" in result.lower()

    def test_explicit_color_overrides_default(self) -> None:
        from do_uw.stages.render.charts.sparklines import render_sparkline

        result = render_sparkline([10, 20], color="#FF00FF")
        assert "#FF00FF" in result


class TestChartColors:
    """CHART_COLORS unified palette exists in design_system."""

    def test_chart_colors_exists(self) -> None:
        from do_uw.stages.render.design_system import CHART_COLORS

        assert isinstance(CHART_COLORS, dict)

    def test_chart_colors_has_sparkline_keys(self) -> None:
        from do_uw.stages.render.design_system import CHART_COLORS

        assert "sparkline_up" in CHART_COLORS
        assert "sparkline_down" in CHART_COLORS
        assert "sparkline_flat" in CHART_COLORS

    def test_chart_colors_has_core_palette(self) -> None:
        from do_uw.stages.render.design_system import CHART_COLORS

        for key in ("navy", "gold", "positive", "negative", "neutral", "grid", "bg", "text"):
            assert key in CHART_COLORS, f"Missing key: {key}"
