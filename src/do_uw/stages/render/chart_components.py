"""Reusable chart component generators that enforce the style registry.

All chart renderers should import from this module instead of hardcoding
colors, figure sizes, and axis styling. This ensures visual consistency
across all 15 chart types and makes style changes a single-file edit
(chart_styles.yaml).

Usage:
    from do_uw.stages.render.chart_components import (
        apply_styled_axis,
        create_styled_figure,
        create_styled_header,
        create_styled_legend,
    )

    fig, colors = create_styled_figure("stock", "png")
    # ... add chart data ...
    apply_styled_axis(ax, "stock", period="1Y")
"""
from __future__ import annotations

from typing import Any

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from do_uw.stages.render.chart_style_registry import (
    get_chart_style,
    load_chart_styles,
    resolve_colors,
)


def create_styled_figure(
    chart_type: str,
    format: str = "png",
) -> tuple[Figure, dict[str, str]]:
    """Create a matplotlib figure with style registry dimensions and colors.

    Returns (fig, colors_dict) so the caller has resolved colors.
    SVG format always gets light theme (existing behavior preserved).

    Args:
        chart_type: Chart type name from chart_styles.yaml.
        format: Output format ("png", "svg", "pdf").

    Returns:
        Tuple of (Figure, resolved_colors_dict).
    """
    style = get_chart_style(chart_type)
    defaults = load_chart_styles().defaults
    colors = resolve_colors(chart_type, format)

    matplotlib.use("Agg")

    # Apply matplotlib style based on theme
    if style.theme == "dark" and format != "svg":
        plt.style.use("dark_background")  # pyright: ignore[reportUnknownMemberType]
    else:
        plt.style.use("default")  # pyright: ignore[reportUnknownMemberType]

    fig: Figure = plt.figure(  # pyright: ignore[reportUnknownMemberType]
        figsize=tuple(style.figure_size),
        dpi=defaults.dpi,
        facecolor=colors["bg"],
    )

    return fig, colors


def create_styled_header(
    ax: Any,
    title: str,
    stats_items: list[tuple[str, str, str]],
    colors: dict[str, str],
    x_start: float = 0.22,
    x_step: float | None = None,
) -> None:
    """Render a stats header bar above a chart.

    Replaces 4 separate _render_*_header functions across stock_charts,
    drawdown_chart, volatility_chart, and relative_performance_chart.

    Args:
        ax: Axes object for the header area.
        title: Title text for the header left side.
        stats_items: List of (label, value, color) tuples.
        colors: Resolved color dict from resolve_colors.
        x_start: Starting x position for stat items.
        x_step: Step between stat items. Auto-computed if None.
    """
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Draw filled rectangle as background
    bg_rect = Rectangle(
        (0, 0), 1, 1, transform=ax.transAxes,
        facecolor=colors.get("header_bg", "#0B1D3A"),
        edgecolor="none", zorder=0, clip_on=False,
    )
    ax.add_patch(bg_rect)

    # Title text
    ax.text(
        0.02, 0.5, title,
        fontsize=9, fontweight="bold",
        color=colors.get("header_text", "#FFFFFF"),
        va="center",
    )

    # Stat items
    if x_step is None:
        x_step = 0.16 if len(stats_items) <= 5 else 0.13

    for i, (label, value, color) in enumerate(stats_items):
        x = x_start + i * x_step
        ax.text(
            x, 0.72, label,
            fontsize=6, color=colors.get("text_muted", "#6B7280"),
            va="center",
        )
        ax.text(
            x, 0.28, value,
            fontsize=9, fontweight="bold", color=color,
            va="center",
        )


def apply_styled_axis(
    ax: Any,
    colors: dict[str, str],
    period: str | None = None,
    show_xlabel: bool = True,
) -> None:
    """Apply axis styling from the registry: spines, grid, tick params.

    Replaces _apply_bloomberg_style, _apply_dd_style, _apply_axis_style,
    and _apply_rel_style.

    Args:
        ax: matplotlib Axes object.
        colors: Resolved color dict from resolve_colors.
        period: Optional chart period ("1Y" or "5Y") for date formatting.
        show_xlabel: Whether to show x-axis labels.
    """
    defaults = load_chart_styles().defaults

    # Tick styling
    ax.tick_params(
        colors=colors.get("text", "#1F2937"),
        labelsize=defaults.tick_fontsize - 1,  # 7
    )

    # Spine visibility
    for spine in defaults.hide_spines:
        ax.spines[spine].set_visible(False)

    # Visible spine styling
    visible_spines = {"bottom", "left"} - set(defaults.hide_spines)
    for spine in visible_spines:
        ax.spines[spine].set_color(colors.get("grid", "#E5E7EB"))
        ax.spines[spine].set_linewidth(defaults.spine_linewidth)

    # Grid
    ax.grid(
        visible=True, alpha=defaults.grid_alpha,
        color=colors.get("grid", "#E5E7EB"),
        linewidth=defaults.grid_linewidth,
    )

    # Date formatting on x-axis
    if show_xlabel and period is not None:
        if period == "1Y":
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
        else:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", rotation=0)
    elif not show_xlabel:
        ax.set_xticklabels([])


def create_styled_legend(
    ax: Any,
    colors: dict[str, str],
    loc: str = "upper left",
    additional_ax: Any = None,
) -> None:
    """Create legend with registry-specified colors and positioning.

    Combines handles from multiple axes if additional_ax is provided.

    Args:
        ax: Primary axes for the legend.
        colors: Resolved color dict from resolve_colors.
        loc: Legend location string.
        additional_ax: Optional second axes whose legend handles are combined.
    """
    defaults = load_chart_styles().defaults

    handles, labels = ax.get_legend_handles_labels()

    if additional_ax is not None:
        h2, l2 = additional_ax.get_legend_handles_labels()
        handles = handles + h2
        labels = labels + l2

    if not handles:
        return

    ax.legend(
        handles, labels,
        loc=loc, fontsize=defaults.legend_fontsize,
        framealpha=0.6 if "dark" in colors.get("bg", "") else 0.8,
        facecolor=colors["bg"],
        edgecolor=colors.get("grid", "#E5E7EB"),
        labelcolor=colors.get("text", "#1F2937"),
    )


__all__ = [
    "apply_styled_axis",
    "create_styled_figure",
    "create_styled_header",
    "create_styled_legend",
]
