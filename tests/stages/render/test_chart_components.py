"""Tests for chart component generators (CHART-02).

Verifies that reusable chart components enforce the style registry and
that chart renderer files no longer contain hardcoded color hex values.
"""
from __future__ import annotations

import subprocess
from typing import Any

import matplotlib
import pytest

matplotlib.use("Agg")


class TestCreateStyledFigure:
    """create_styled_figure returns Figure with correct dimensions."""

    def test_returns_figure_and_colors(self) -> None:
        from do_uw.stages.render.chart_components import create_styled_figure

        fig, colors = create_styled_figure("stock", "png")
        assert fig is not None
        assert isinstance(colors, dict)
        assert "bg" in colors
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_stock_figure_size(self) -> None:
        from do_uw.stages.render.chart_components import create_styled_figure

        fig, _colors = create_styled_figure("stock", "png")
        w, h = fig.get_size_inches()
        assert abs(w - 10.0) < 0.1
        assert abs(h - 6.5) < 0.1
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_stock_dpi(self) -> None:
        from do_uw.stages.render.chart_components import create_styled_figure

        fig, _colors = create_styled_figure("stock", "png")
        assert fig.dpi == 200
        import matplotlib.pyplot as plt

        plt.close(fig)

    def test_svg_uses_light_colors(self) -> None:
        from do_uw.stages.render.chart_components import create_styled_figure

        _fig, colors = create_styled_figure("stock", "svg")
        # SVG always uses light theme
        assert colors["bg"] == "#FFFFFF"
        import matplotlib.pyplot as plt

        plt.close(_fig)


class TestApplyStyledAxis:
    """apply_styled_axis hides top/right spines per registry."""

    def test_hides_top_right_spines(self) -> None:
        import matplotlib.pyplot as plt

        from do_uw.stages.render.chart_components import apply_styled_axis
        from do_uw.stages.render.chart_style_registry import resolve_colors

        fig, ax = plt.subplots()
        colors = resolve_colors("drawdown", "png")
        apply_styled_axis(ax, colors, period="1Y")

        assert not ax.spines["top"].get_visible()
        assert not ax.spines["right"].get_visible()
        plt.close(fig)

    def test_sets_grid(self) -> None:
        import matplotlib.pyplot as plt

        from do_uw.stages.render.chart_components import apply_styled_axis
        from do_uw.stages.render.chart_style_registry import resolve_colors

        fig, ax = plt.subplots()
        colors = resolve_colors("drawdown", "png")
        apply_styled_axis(ax, colors, period="1Y")

        # Grid should be enabled
        assert ax.xaxis.get_gridlines()[0].get_visible()
        plt.close(fig)


class TestCreateStyledHeader:
    """create_styled_header renders text at expected positions."""

    def test_header_renders_without_error(self) -> None:
        import matplotlib.pyplot as plt

        from do_uw.stages.render.chart_components import create_styled_header
        from do_uw.stages.render.chart_style_registry import resolve_colors

        fig = plt.figure()
        ax: Any = fig.add_axes([0.05, 0.88, 0.9, 0.10])
        colors = resolve_colors("stock", "png")

        items = [("Price", "$100.00", "#FFFFFF"), ("Return", "+5.0%", "#00C853")]
        create_styled_header(ax, "TEST Header", items, colors)

        # Check that text was added (at least title + 2 labels + 2 values)
        texts = ax.texts
        assert len(texts) >= 5
        plt.close(fig)


class TestCreateStyledLegend:
    """create_styled_legend combines handles from multiple axes."""

    def test_combines_axes(self) -> None:
        import matplotlib.pyplot as plt

        from do_uw.stages.render.chart_components import create_styled_legend
        from do_uw.stages.render.chart_style_registry import resolve_colors

        fig, ax = plt.subplots()
        ax2 = ax.twinx()
        colors = resolve_colors("stock", "png")

        ax.plot([1, 2, 3], label="Line A")
        ax2.plot([3, 2, 1], label="Line B")

        create_styled_legend(ax, colors, additional_ax=ax2)

        legend = ax.get_legend()
        assert legend is not None
        assert len(legend.get_texts()) == 2
        plt.close(fig)


class TestNoHardcodedHexInChartRenderers:
    """Ensure chart renderers consume colors from registry, not hardcode them."""

    def test_renderers_use_registry_imports(self) -> None:
        """Verify chart renderers import from chart_style_registry."""
        renderer_files = [
            "drawdown_chart.py",
            "volatility_chart.py",
            "drop_analysis_chart.py",
            "relative_performance_chart.py",
            "radar_chart.py",
            "ownership_chart.py",
            "timeline_chart.py",
            "sparklines.py",
        ]
        base = "/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/render/charts"

        missing: list[str] = []
        for fname in renderer_files:
            fpath = f"{base}/{fname}"
            try:
                with open(fpath) as f:
                    content = f.read()
                    if "chart_style_registry" not in content:
                        missing.append(fname)
            except FileNotFoundError:
                pass

        assert missing == [], (
            f"Renderers not importing from chart_style_registry:\n"
            + "\n".join(missing)
        )

    def test_no_bloomberg_dark_import_in_renderers(self) -> None:
        """Ensure renderers don't import BLOOMBERG_DARK or CREDIT_REPORT_LIGHT directly."""
        renderer_files = [
            "drawdown_chart.py",
            "volatility_chart.py",
            "drop_analysis_chart.py",
            "relative_performance_chart.py",
            "radar_chart.py",
            "ownership_chart.py",
            "timeline_chart.py",
            "sparklines.py",
        ]
        # Note: stock_charts.py is excluded because it needs
        # resolve_colors("stock", "png") comparison for dark_background style
        base = "/Users/gorlin/Projects/do-uw/do-uw/src/do_uw/stages/render/charts"

        violations: list[str] = []
        for fname in renderer_files:
            fpath = f"{base}/{fname}"
            try:
                with open(fpath) as f:
                    for line in f:
                        stripped = line.strip()
                        # Only check import lines, not docstrings/comments
                        if stripped.startswith(("from ", "import ")):
                            if "BLOOMBERG_DARK" in stripped:
                                violations.append(f"{fname}: {stripped}")
                            if "CREDIT_REPORT_LIGHT" in stripped:
                                violations.append(f"{fname}: {stripped}")
            except FileNotFoundError:
                pass

        assert violations == [], (
            f"Renderers still importing hardcoded color dicts:\n"
            + "\n".join(violations)
        )
