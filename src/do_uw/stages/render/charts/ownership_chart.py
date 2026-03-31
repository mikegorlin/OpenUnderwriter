"""VIS-02: Ownership breakdown donut chart.

Creates a donut/pie chart showing institutional vs insider vs retail
float percentages. Annotates top holders and dual-class structure
when available.
"""

from __future__ import annotations

import io
from typing import Any

import matplotlib
import matplotlib.pyplot as plt  # pyright: ignore[reportUnknownMemberType]
from matplotlib.figure import Figure

from do_uw.models.governance_forensics import OwnershipAnalysis
from do_uw.stages.render.chart_helpers import save_chart_to_bytes, save_chart_to_svg
from do_uw.stages.render.chart_style_registry import get_chart_style, resolve_colors
from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.design_system import DesignSystem


def _extract_ownership_slices(
    ownership: OwnershipAnalysis,
) -> tuple[list[str], list[float], list[str]]:
    """Extract pie chart data from ownership model.

    Returns:
        Tuple of (labels, values, colors) for the chart slices.
    """
    own_colors = get_chart_style("ownership").colors
    labels: list[str] = []
    values: list[float] = []
    colors: list[str] = []

    inst_pct = ownership.institutional_pct
    insider_pct = ownership.insider_pct

    inst_val = inst_pct.value if inst_pct is not None else None
    insider_val = insider_pct.value if insider_pct is not None else None

    if inst_val is not None and inst_val > 0:
        labels.append(f"Institutional ({inst_val:.1f}%)")
        values.append(inst_val)
        colors.append(str(own_colors.get("institutional", "#1A1446")))

    if insider_val is not None and insider_val > 0:
        labels.append(f"Insider ({insider_val:.1f}%)")
        values.append(insider_val)
        colors.append(str(own_colors.get("insider", "#FFD000")))

    # Compute retail float as remainder
    known = sum(values)
    if known < 100.0:
        retail = 100.0 - known
        labels.append(f"Retail Float ({retail:.1f}%)")
        values.append(retail)
        colors.append(str(own_colors.get("retail", "#B0B0B0")))

    return labels, values, colors


def _format_top_holders(ownership: OwnershipAnalysis) -> list[str]:
    """Extract top holder names from ownership data."""
    holder_lines: list[str] = []
    for sv_holder in ownership.top_holders[:5]:
        holder_dict: dict[str, Any] = sv_holder.value
        name = holder_dict.get("name", "Unknown")
        pct = holder_dict.get("pct_out") or holder_dict.get("pct") or holder_dict.get("percentage") or 0.0
        if isinstance(pct, (int, float)) and pct > 0:
            holder_lines.append(f"{name}: {pct:.1f}%")
        else:
            holder_lines.append(str(name))
    return holder_lines


@null_safe_chart
def create_ownership_chart(
    ownership: OwnershipAnalysis | None,
    ds: DesignSystem,
    colors: dict[str, str] | None = None,
    format: str = "png",
) -> io.BytesIO | str | None:
    """Create a donut chart showing ownership breakdown (VIS-02).

    Shows institutional vs insider vs retail float as a donut chart
    with center text and top holder annotations.

    Args:
        ownership: Ownership analysis data, or None.
        ds: Design system for colors and styling.
        colors: Optional color dict for theming. Uses brand colors
            when None. Pass CREDIT_REPORT_LIGHT for light PDF charts.
        format: Output format -- "png" returns BytesIO, "svg" returns str.

    Returns:
        BytesIO with PNG image data, SVG string, or None if no data available.
    """
    if ownership is None:
        return None

    labels, values, slice_colors = _extract_ownership_slices(ownership)
    if not values or all(lbl.startswith("Retail") for lbl in labels):
        # No meaningful data if only retail float (computed as remainder)
        return None

    # Resolve theme colors from chart style registry.
    own_style = get_chart_style("ownership")
    c = resolve_colors("ownership", format)
    text_color = c.get("text", "#333333")
    bg_color = c.get("bg", "#FFFFFF")
    grid_color = c.get("grid", "#CCCCCC")

    matplotlib.use("Agg")
    fig: Figure = plt.figure(figsize=tuple(own_style.figure_size), dpi=200)  # pyright: ignore[reportUnknownMemberType]
    fig.patch.set_facecolor(bg_color)
    ax: Any = fig.add_subplot(111)
    ax.set_facecolor(bg_color)

    # Create donut chart (pie with center hole)
    wedges: Any
    _texts: Any
    autotexts: Any
    wedges, _texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=slice_colors,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.78,
        wedgeprops={"width": 0.4, "edgecolor": "white", "linewidth": 2},
    )

    # Style autopct text
    for autotext in autotexts:
        autotext.set_fontsize(8)
        autotext.set_color("white")
        autotext.set_fontweight("bold")

    # Center text
    center_text = "Ownership\nStructure"
    own_clrs = get_chart_style("ownership").colors
    ax.text(
        0, 0, center_text,
        ha="center", va="center",
        fontsize=10, fontweight="bold",
        color=str(own_clrs.get("institutional", "#1A1446")),
    )

    # Legend
    ax.legend(
        wedges, labels,
        loc="center left", bbox_to_anchor=(1.0, 0.5),
        fontsize=8, frameon=False,
    )

    # Dual-class annotation
    has_dual = ownership.has_dual_class
    if has_dual is not None and has_dual.value:
        control_pct = ownership.dual_class_control_pct
        note = "Dual-class structure"
        if control_pct is not None:
            note += f" ({control_pct.value:.0f}% voting control)"
        ax.annotate(
            note,
            xy=(0, -0.55), fontsize=7,
            color=str(own_clrs.get("dual_class_warning", "#CC0000")),
            ha="center", fontstyle="italic",
        )

    # Top holders annotation
    top_holders = _format_top_holders(ownership)
    if top_holders:
        holder_text = "Top Holders:\n" + "\n".join(top_holders)
        ax.annotate(
            holder_text,
            xy=(1.0, -0.15), xycoords="axes fraction",
            fontsize=6.5, color=text_color,
            va="top", ha="left",
            bbox={"boxstyle": "round,pad=0.3", "fc": bg_color, "ec": grid_color},
        )

    ax.set_title(
        "Ownership Structure",
        color=str(own_clrs.get("institutional", "#1A1446")),
        fontweight="bold", fontsize=12, pad=15,
    )

    fig.tight_layout()
    _ = ds  # reserved for future use
    if format == "svg":
        return save_chart_to_svg(fig)
    return save_chart_to_bytes(fig, dpi=200)


__all__ = ["create_ownership_chart"]
