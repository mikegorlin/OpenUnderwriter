"""Chart creation and embedding helpers for Word documents.

Provides matplotlib figure creation, BytesIO pipeline for embedding
charts in python-docx documents, and reusable chart types like the
radar/spider chart for 10-factor scoring visualization.
"""

from __future__ import annotations

import io
import math
import re
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
from docx.shared import Inches  # type: ignore[import-untyped]
from matplotlib.figure import Figure

from do_uw.stages.render.design_system import DesignSystem


def create_figure(
    width: float = 6.5, height: float = 3.5, dpi: int = 200
) -> tuple[Figure, Any]:
    """Create a new matplotlib figure with consistent defaults.

    Uses the Agg backend for headless rendering.

    Args:
        width: Figure width in inches.
        height: Figure height in inches.
        dpi: Resolution in dots per inch.

    Returns:
        Tuple of (Figure, Axes).
    """
    matplotlib.use("Agg")
    fig: Figure
    ax: Any
    fig, ax = plt.subplots(figsize=(width, height), dpi=dpi)  # pyright: ignore[reportUnknownMemberType]
    return fig, ax


def save_chart_to_svg(fig: Figure) -> str:
    """Save a matplotlib figure to an inline SVG string.

    Produces a clean ``<svg>...</svg>`` element suitable for inline
    embedding in HTML.  Strips the XML declaration and DOCTYPE if
    present, and sets ``width="100%"`` on the root element for
    responsive sizing.

    ALWAYS closes the figure after saving to prevent memory leaks.

    Args:
        fig: The matplotlib Figure to render.

    Returns:
        SVG markup string starting with ``<svg``.
    """
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight")
    plt.close(fig)
    raw = buf.getvalue()

    # Strip XML declaration and DOCTYPE, keep only <svg ...>...</svg>
    match = re.search(r"(<svg\b.*</svg>)", raw, re.DOTALL)
    svg = match.group(1) if match else raw

    # Ensure width="100%" for responsive sizing
    if 'width="100%"' not in svg:
        svg = re.sub(r'(<svg\b[^>]*?)(\s*>)', r'\1 width="100%"\2', svg, count=1)

    return svg


def save_chart_to_bytes(fig: Figure, dpi: int = 200) -> io.BytesIO:
    """Save a matplotlib figure to BytesIO as PNG.

    ALWAYS closes the figure after saving to prevent memory leaks.

    Args:
        fig: The matplotlib Figure to save.
        dpi: Resolution for the PNG output.

    Returns:
        BytesIO buffer containing the PNG image data, seeked to 0.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")  # pyright: ignore[reportUnknownMemberType]
    plt.close(fig)
    buf.seek(0)
    return buf


def embed_chart(
    doc: Any, buf: io.BytesIO, width: Inches | None = None
) -> None:
    """Add a chart image from BytesIO to a document.

    Args:
        doc: The python-docx Document.
        buf: BytesIO buffer containing image data.
        width: Optional width for the image. Defaults to chart_width.
    """
    effective_width = width if width is not None else Inches(6.5)
    doc.add_picture(buf, width=effective_width)


def apply_chart_style(
    ax: Any,
    ds: DesignSystem,
    title: str = "",
    ylabel: str = "",
) -> None:
    """Apply consistent chart styling to matplotlib axes.

    Sets navy title, gray grid, white background, and cleans up spines.

    Args:
        ax: matplotlib Axes object.
        ds: Design system for colors and fonts.
        title: Optional chart title.
        ylabel: Optional y-axis label.
    """
    if title:
        ax.set_title(title, color="#1A1446", fontweight="bold", fontsize=11)
    if ylabel:
        ax.set_ylabel(ylabel, color="#333333", fontsize=9)

    # Grid and background
    ax.set_facecolor("white")
    ax.grid(visible=True, alpha=0.3, color="#CCCCCC", linewidth=0.5)

    # Clean up spines
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color("#CCCCCC")
        ax.spines[spine].set_linewidth(0.5)

    # Tick styling
    ax.tick_params(colors="#666666", labelsize=8)
    _ = ds  # ds reserved for future style extensions


def create_radar_chart(
    categories: list[str],
    values: list[float],
    max_value: float,
    title: str,
    ds: DesignSystem,
) -> io.BytesIO:
    """Create a radar/spider chart for 10-factor scoring visualization.

    Uses polar axes with navy fill, gold outline, and category labels
    around the perimeter. Returns BytesIO ready for embedding.

    Args:
        categories: List of category labels (e.g., factor names).
        values: List of numeric values (one per category).
        max_value: Maximum value for the radial axis.
        title: Chart title.
        ds: Design system for colors.

    Returns:
        BytesIO buffer containing the radar chart PNG.
    """
    matplotlib.use("Agg")

    n = len(categories)
    if n == 0:
        # Return an empty chart for degenerate case
        fig: Figure
        fig, _ax = plt.subplots(figsize=(6, 6), dpi=200)  # pyright: ignore[reportUnknownMemberType]
        return save_chart_to_bytes(fig, dpi=200)

    # Compute angles for each category
    angles = [i * 2 * math.pi / n for i in range(n)]
    # Close the polygon
    values_closed = [*values, values[0]]
    angles_closed = [*angles, angles[0]]

    fig: Figure = plt.figure(figsize=(6, 6), dpi=200)  # pyright: ignore[reportUnknownMemberType]
    ax: Any = fig.add_subplot(111, polar=True)

    # Plot the filled area (navy with transparency)
    ax.fill(angles_closed, values_closed, color="#1A1446", alpha=0.15)
    # Plot the outline (gold accent)
    ax.plot(angles_closed, values_closed, color="#FFD000", linewidth=2)
    # Plot data points
    ax.scatter(angles, values, color="#1A1446", s=40, zorder=5)

    # Category labels around the perimeter
    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontsize=8, color="#333333")

    # Radial axis
    ax.set_ylim(0, max_value)
    ax.set_yticks([max_value * i / 4 for i in range(1, 5)])
    ax.set_yticklabels(
        [f"{max_value * i / 4:.0f}" for i in range(1, 5)],
        fontsize=7,
        color="#999999",
    )

    # Grid styling
    ax.grid(color="#E0E0E0", linewidth=0.5)
    ax.spines["polar"].set_color("#CCCCCC")

    # Title
    if title:
        ax.set_title(title, color="#1A1446", fontweight="bold", fontsize=12, pad=20)

    fig.tight_layout()
    _ = ds  # ds reserved for future style extensions
    return save_chart_to_bytes(fig, dpi=200)


__all__ = [
    "apply_chart_style",
    "create_figure",
    "create_radar_chart",
    "embed_chart",
    "save_chart_to_bytes",
    "save_chart_to_svg",
]
