"""10-factor radar/spider chart for risk scoring visualization.

Creates a polar axes chart showing all 10 scoring factors with
navy fill, gold outline, and category labels around the perimeter.
This is the dedicated enhanced version used by Section 7.
"""

from __future__ import annotations

import io
import math
from typing import Any

import matplotlib
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]
from matplotlib.figure import Figure

from do_uw.models.scoring import FactorScore
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.chart_style_registry import get_chart_style, resolve_colors
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.design_system import DesignSystem


def _compute_risk_fractions(
    factor_scores: list[FactorScore],
) -> tuple[list[str], list[float]]:
    """Compute risk fractions for each factor.

    Each factor's risk fraction = points_deducted / max_points,
    clamped to [0, 1]. Labels include factor name and points.

    Returns:
        Tuple of (labels, values) for the radar chart.
    """
    labels: list[str] = []
    values: list[float] = []

    for fs in factor_scores:
        max_pts = fs.max_points if fs.max_points > 0 else 1
        fraction = min(fs.points_deducted / max_pts, 1.0)
        fraction = max(fraction, 0.0)
        label = f"{fs.factor_id}\n{fs.factor_name}\n(-{fs.points_deducted:.0f})"
        labels.append(label)
        values.append(fraction)

    return labels, values


@null_safe_chart
def create_radar_chart(
    factor_scores: list[FactorScore],
    ds: DesignSystem,
    colors: dict[str, str] | None = None,
    format: str = "png",
    show_threshold_rings: bool = False,
    show_mean_ring: bool = False,
) -> io.BytesIO | str | None:
    """Create a 10-factor radar/spider chart.

    Shows risk profile shape with navy fill, gold outline, and
    gray concentric grid circles. Each spoke represents one of
    the 10 scoring factors.

    Args:
        factor_scores: List of FactorScore objects (typically 10).
        ds: Design system for colors and styling.
        colors: Optional color dict for theming. Uses brand colors
            when None. Pass CREDIT_REPORT_LIGHT for light PDF charts.
        format: Output format -- "png" returns BytesIO, "svg" returns str.
        show_threshold_rings: When True, draws 3 concentric reference
            circles at r=0.25, r=0.50, r=0.75 with light gray dashed
            lines and sparse labels. Default False for backward compat.
        show_mean_ring: When True, draws a single ring at the mean of
            all factor fractions with a gold dashed line and "AVG" label.
            Highlights spiky vs round risk profiles. Default False.

    Returns:
        BytesIO with PNG image data, SVG string, or None if no factor scores.
    """
    if not factor_scores:
        return None

    matplotlib.use("Agg")

    # Resolve colors from chart style registry.
    radar_style = get_chart_style("radar")
    rc = radar_style.colors
    c = resolve_colors("radar", format)
    text_color = c.get("text", "#333333")
    text_muted = c.get("text_muted", "#999999")
    grid_color = c.get("grid", "#E0E0E0")
    bg_color = c.get("bg", "#FFFFFF")

    fill_color = str(rc.get("fill", "#1A1446"))
    fill_alpha = float(rc.get("fill_alpha", 0.25))
    outline_color = str(rc.get("outline", "#FFD000"))
    outline_width = float(rc.get("outline_width", 2.5))
    point_color = str(rc.get("point_color", "#1A1446"))
    point_size = int(rc.get("point_size", 50))

    labels, values = _compute_risk_fractions(factor_scores)
    n = len(labels)

    # Compute angles for each category
    angles = [i * 2 * math.pi / n for i in range(n)]
    # Close the polygon
    values_closed = [*values, values[0]]
    angles_closed = [*angles, angles[0]]

    # Full circle of angles for drawing reference rings
    ring_angles = [i * 2 * math.pi / 360 for i in range(361)]

    fig: Figure = plt.figure(figsize=tuple(radar_style.figure_size), dpi=200)  # pyright: ignore[reportUnknownMemberType]
    fig.patch.set_facecolor(bg_color)
    ax: Any = fig.add_subplot(111, polar=True)
    ax.set_facecolor(bg_color)

    # -- Threshold reference rings (drawn BEFORE data polygon) --
    if show_threshold_rings:
        _threshold_ring_color = "#CBD5E1"
        for ring_r, ring_label in [(0.25, "25%"), (0.50, "50%"), (0.75, "75%")]:
            ring_values = [ring_r] * len(ring_angles)
            ax.plot(
                ring_angles, ring_values,
                color=_threshold_ring_color, alpha=0.3,
                linestyle="--", linewidth=0.5, zorder=1,
            )
            # Sparse label at angle 0 (right side)
            ax.text(
                0, ring_r + 0.02, ring_label,
                fontsize=6, color=_threshold_ring_color, alpha=0.6,
                ha="left", va="bottom",
            )

    # -- Mean fraction ring --
    if show_mean_ring and values:
        mean_val = sum(values) / len(values)
        mean_ring_values = [mean_val] * len(ring_angles)
        ax.plot(
            ring_angles, mean_ring_values,
            color="#D4A843", alpha=0.5,
            linestyle=":", linewidth=1.0, zorder=2,
        )
        # Label at angle 0
        ax.text(
            0, mean_val + 0.02, "AVG",
            fontsize=7, fontweight="bold",
            color="#D4A843", alpha=0.7,
            ha="left", va="bottom",
        )

    # Plot the filled area
    ax.fill(angles_closed, values_closed, color=fill_color, alpha=fill_alpha)

    # Plot the outline
    ax.plot(angles_closed, values_closed, color=outline_color, linewidth=outline_width)

    # Plot data points
    ax.scatter(angles, values, color=point_color, s=point_size, zorder=5)

    # Category labels around the perimeter
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontsize=7, color=text_color, ha="center")

    # Radial axis: 0 to 1 scale (0% to 100% risk)
    ax.set_ylim(0, 1.0)
    grid_levels = [0.25, 0.50, 0.75, 1.00]
    ax.set_yticks(grid_levels)
    ax.set_yticklabels(
        ["25%", "50%", "75%", "100%"],
        fontsize=7, color=text_muted,
    )

    # Grid styling
    ax.grid(color=grid_color, linewidth=0.5)
    ax.spines["polar"].set_color(grid_color)

    # Title
    ax.set_title(
        "10-Factor Risk Profile",
        color=fill_color, fontweight="bold", fontsize=13, pad=25,
    )

    fig.tight_layout()
    _ = ds  # reserved for future style extensions
    if format == "svg":
        return save_chart_to_svg(fig)
    return save_chart_to_bytes(fig, dpi=200)


__all__ = ["create_radar_chart"]
