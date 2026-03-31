"""Tests for chart style registry YAML loading and validation (CHART-01).

Verifies that chart_styles.yaml loads correctly, contains entries for all
chart type families, and produces color dicts identical to current hardcoded
values (regression safety).
"""
from __future__ import annotations

import pytest


class TestChartStylesYAMLLoading:
    """Test that chart_styles.yaml loads without error."""

    def test_load_chart_styles_succeeds(self) -> None:
        from do_uw.stages.render.chart_style_registry import load_chart_styles

        registry = load_chart_styles()
        assert registry is not None

    def test_chart_styles_has_defaults(self) -> None:
        from do_uw.stages.render.chart_style_registry import load_chart_styles

        registry = load_chart_styles()
        assert registry.defaults is not None
        assert registry.defaults.dpi == 200

    def test_chart_styles_has_themes(self) -> None:
        from do_uw.stages.render.chart_style_registry import load_chart_styles

        registry = load_chart_styles()
        assert "light" in registry.themes
        assert "dark" in registry.themes


class TestChartTypeFamilies:
    """Every chart type family must have a matching style entry."""

    REQUIRED_FAMILIES = [
        "stock", "drawdown", "volatility", "drop_analysis",
        "relative_performance", "radar", "ownership", "timeline", "sparkline",
    ]

    def test_all_families_present(self) -> None:
        from do_uw.stages.render.chart_style_registry import load_chart_styles

        registry = load_chart_styles()
        for family in self.REQUIRED_FAMILIES:
            assert family in registry.chart_types, f"Missing chart type family: {family}"

    @pytest.mark.parametrize("family", REQUIRED_FAMILIES)
    def test_family_has_colors(self, family: str) -> None:
        from do_uw.stages.render.chart_style_registry import get_chart_style

        style = get_chart_style(family)
        assert style.colors is not None
        assert len(style.colors) > 0


class TestChartTypeStyleValidation:
    """ChartTypeStyle validates required fields."""

    def test_get_chart_style_returns_valid_type(self) -> None:
        from do_uw.stages.render.chart_style_registry import (
            ChartTypeStyle,
            get_chart_style,
        )

        style = get_chart_style("stock")
        assert isinstance(style, ChartTypeStyle)

    def test_get_chart_style_nonexistent_raises(self) -> None:
        from do_uw.stages.render.chart_style_registry import get_chart_style

        with pytest.raises(KeyError):
            get_chart_style("nonexistent_chart_type")

    def test_stock_style_has_figure_size(self) -> None:
        from do_uw.stages.render.chart_style_registry import get_chart_style

        style = get_chart_style("stock")
        assert style.figure_size is not None
        assert len(style.figure_size) == 2

    def test_stock_style_has_theme(self) -> None:
        from do_uw.stages.render.chart_style_registry import get_chart_style

        style = get_chart_style("stock")
        assert style.theme == "dark"


class TestResolveColors:
    """resolve_colors produces correct color dicts."""

    def test_svg_always_light_theme(self) -> None:
        from do_uw.stages.render.chart_style_registry import resolve_colors

        colors = resolve_colors("stock", "svg")
        # SVG always uses light theme regardless of chart's native theme
        assert colors["bg"] == "#FFFFFF"

    def test_stock_dark_colors_match_yaml_dark_theme(self) -> None:
        """Regression: resolved stock dark colors must match chart_styles.yaml dark theme."""
        from do_uw.stages.render.chart_style_registry import (
            get_theme_colors,
            resolve_colors,
        )

        colors = resolve_colors("stock", "png")
        dark = get_theme_colors("dark")
        # Stock uses dark theme; chart-specific overrides take precedence
        assert colors["bg"] == dark["bg"]
        assert colors["grid"] == dark["grid"]
        assert colors["text"] == dark["text"]
        # price_up/price_down come from chart-specific colors, matching dark theme
        assert colors["price_up"] == "#D4A843"
        assert colors["price_down"] == "#E57373"

    def test_drawdown_light_colors_match_yaml_light_theme(self) -> None:
        """Regression: resolved light colors must match chart_styles.yaml light theme."""
        from do_uw.stages.render.chart_style_registry import (
            get_theme_colors,
            resolve_colors,
        )

        colors = resolve_colors("drawdown", "png")
        light = get_theme_colors("light")
        assert colors["bg"] == light["bg"]
        assert colors["grid"] == light["grid"]
        assert colors["text"] == light["text"]

    def test_get_theme_colors_light(self) -> None:
        from do_uw.stages.render.chart_style_registry import get_theme_colors

        colors = get_theme_colors("light")
        assert colors["bg"] == "#FFFFFF"

    def test_get_theme_colors_dark(self) -> None:
        from do_uw.stages.render.chart_style_registry import get_theme_colors

        colors = get_theme_colors("dark")
        assert colors["bg"] == "#0B1D3A"
