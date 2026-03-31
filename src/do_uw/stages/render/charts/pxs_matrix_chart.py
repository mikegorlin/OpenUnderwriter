"""P x S risk matrix chart for severity visualization (Phase 108).

Renders a 2D chart with:
  - X-axis: Claim Probability (P), linear 0-1 scale
  - Y-axis: Estimated Severity (S), log10 scale $100K to $10B
  - 4 zone backgrounds (GREEN, YELLOW, ORANGE, RED) with alpha fills
  - Primary scenario as large dot at (P, S_primary)
  - Range bar from min to max across all scenarios (vertical line at P)
  - Labels: P value, S value, EL = P x S, zone name
  - Liberty attachment line: horizontal dashed orange line (if provided)

Zone colors from severity_model_design.yaml:
  GREEN:  #2b8a3e
  YELLOW: #e67700
  ORANGE: #c92a2a
  RED:    #862e9c
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from do_uw.models.severity import SeverityResult, SeverityZone

matplotlib.use("Agg")

__all__ = [
    "render_pxs_matrix",
    "render_pxs_matrix_html",
]

logger = logging.getLogger(__name__)

# Zone colors from severity_model_design.yaml
_ZONE_COLORS: dict[str, str] = {
    "GREEN": "#2b8a3e",
    "YELLOW": "#e67700",
    "ORANGE": "#c92a2a",
    "RED": "#862e9c",
}

# Zone boundaries (log10 scale for S)
_S_MIN = 1e5       # $100K
_S_MAX = 1e10      # $10B
_P_MIN = 0.0
_P_MAX = 1.0


def _format_dollars(amount: float) -> str:
    """Format dollar amount as $XM or $XB."""
    if amount >= 1e9:
        return f"${amount / 1e9:.1f}B"
    if amount >= 1e6:
        return f"${amount / 1e6:.1f}M"
    if amount >= 1e3:
        return f"${amount / 1e3:.0f}K"
    return f"${amount:,.0f}"


def render_pxs_matrix(
    severity_result: SeverityResult,
    output_format: str = "png",
    chart_styles: dict[str, Any] | None = None,
) -> bytes:
    """Render P x S risk matrix chart as PNG bytes.

    Args:
        severity_result: SeverityResult with P, S, scenarios, zone.
        output_format: Output format (currently only "png").
        chart_styles: Optional style overrides.

    Returns:
        PNG image bytes.
    """
    fig, ax = plt.subplots(figsize=(8, 6), dpi=150)

    # Draw zone backgrounds
    _draw_zone_backgrounds(ax)

    # Plot scenario dots and range bar
    _draw_scenarios(ax, severity_result)

    # Plot primary dot
    _draw_primary_dot(ax, severity_result)

    # Liberty attachment line
    _draw_attachment_line(ax, severity_result)

    # Annotations
    _draw_annotations(ax, severity_result)

    # Axis formatting
    ax.set_xlim(_P_MIN, _P_MAX)
    ax.set_ylim(_S_MIN, _S_MAX)
    ax.set_yscale("log")
    ax.set_xlabel("Claim Probability (P)", fontsize=10, color="#333")
    ax.set_ylabel("Estimated Severity (S)", fontsize=10, color="#333")
    ax.set_title(
        "P x S Risk Matrix",
        fontsize=12, fontweight="bold", color="#1A1446",
    )

    # Y-axis dollar labels
    yticks = [1e5, 1e6, 1e7, 1e8, 1e9, 1e10]
    ax.set_yticks(yticks)
    ax.set_yticklabels([_format_dollars(v) for v in yticks], fontsize=8)

    # X-axis labels
    xticks = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.80, 1.0]
    ax.set_xticks(xticks)
    ax.set_xticklabels([f"{v:.0%}" for v in xticks], fontsize=8)

    # Grid and styling
    ax.grid(visible=True, alpha=0.2, color="#999", linewidth=0.5)
    ax.set_facecolor("white")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("bottom", "left"):
        ax.spines[spine].set_color("#CCCCCC")
        ax.spines[spine].set_linewidth(0.5)
    ax.tick_params(colors="#666666", labelsize=8)

    fig.tight_layout()

    # Save to bytes
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def render_pxs_matrix_html(
    severity_result: SeverityResult,
    chart_styles: dict[str, Any] | None = None,
) -> str:
    """Render P x S matrix as base64 PNG for HTML embedding.

    Args:
        severity_result: SeverityResult with P, S, scenarios, zone.
        chart_styles: Optional style overrides.

    Returns:
        HTML <img> tag with base64-encoded PNG src.
    """
    png_bytes = render_pxs_matrix(severity_result, chart_styles=chart_styles)
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return (
        f'<img src="data:image/png;base64,{b64}" '
        f'alt="P x S Risk Matrix" '
        f'style="max-width:100%;height:auto;" />'
    )


# ---------------------------------------------------------------------------
# Internal drawing helpers
# ---------------------------------------------------------------------------


def _draw_zone_backgrounds(ax: Any) -> None:
    """Draw 4 colored zone rectangles on the axes.

    Zones are drawn in order from GREEN (bottom-left) to RED (top-right).
    Uses log-scale Y coordinates.
    """
    # GREEN: P < 0.10, S < $10M
    ax.add_patch(Rectangle(
        (0, _S_MIN), 0.10, 10_000_000 - _S_MIN,
        facecolor=_ZONE_COLORS["GREEN"], alpha=0.12,
        edgecolor="none", zorder=0,
    ))

    # YELLOW: covers the remaining non-orange/red area
    # Left band: P < 0.10, S >= $10M up to $50M
    ax.add_patch(Rectangle(
        (0, 10_000_000), 0.10, 40_000_000,
        facecolor=_ZONE_COLORS["YELLOW"], alpha=0.10,
        edgecolor="none", zorder=0,
    ))
    # Middle band: 0.10 <= P < 0.25, S < $5M
    ax.add_patch(Rectangle(
        (0.10, _S_MIN), 0.15, 5_000_000 - _S_MIN,
        facecolor=_ZONE_COLORS["YELLOW"], alpha=0.10,
        edgecolor="none", zorder=0,
    ))
    # Middle band: 0.10 <= P < 0.25, $5M <= S < $50M
    ax.add_patch(Rectangle(
        (0.10, 5_000_000), 0.15, 45_000_000,
        facecolor=_ZONE_COLORS["YELLOW"], alpha=0.10,
        edgecolor="none", zorder=0,
    ))

    # ORANGE: (P >= 0.25 AND S >= $5M) OR P >= 0.35 OR S >= $50M
    # But not RED (P >= 0.35 AND S >= $50M)
    # P >= 0.25, $5M <= S < $50M
    ax.add_patch(Rectangle(
        (0.25, 5_000_000), 0.10, 45_000_000,
        facecolor=_ZONE_COLORS["ORANGE"], alpha=0.12,
        edgecolor="none", zorder=0,
    ))
    # P >= 0.35, S < $50M
    ax.add_patch(Rectangle(
        (0.35, _S_MIN), 0.65, 50_000_000 - _S_MIN,
        facecolor=_ZONE_COLORS["ORANGE"], alpha=0.12,
        edgecolor="none", zorder=0,
    ))
    # S >= $50M, P < 0.35
    ax.add_patch(Rectangle(
        (0, 50_000_000), 0.35, _S_MAX - 50_000_000,
        facecolor=_ZONE_COLORS["ORANGE"], alpha=0.12,
        edgecolor="none", zorder=0,
    ))

    # RED: P >= 0.35 AND S >= $50M
    ax.add_patch(Rectangle(
        (0.35, 50_000_000), 0.65, _S_MAX - 50_000_000,
        facecolor=_ZONE_COLORS["RED"], alpha=0.12,
        edgecolor="none", zorder=0,
    ))

    # Zone labels (positioned in zone centers)
    zone_labels = [
        (0.05, 3_000_000, "GREEN", _ZONE_COLORS["GREEN"]),
        (0.17, 15_000_000, "YELLOW", _ZONE_COLORS["YELLOW"]),
        (0.50, 20_000_000, "ORANGE", _ZONE_COLORS["ORANGE"]),
        (0.65, 500_000_000, "RED", _ZONE_COLORS["RED"]),
    ]
    for x, y, label, color in zone_labels:
        ax.text(
            x, y, label,
            fontsize=9, fontweight="bold", color=color,
            alpha=0.5, ha="center", va="center", zorder=1,
        )


def _draw_scenarios(ax: Any, severity_result: SeverityResult) -> None:
    """Draw scenario dots and range bar."""
    if not severity_result.scenario_table:
        return

    p = severity_result.probability
    settlements = [
        max(s.amplified_settlement, _S_MIN)
        for s in severity_result.scenario_table
    ]

    if not settlements:
        return

    s_min = min(settlements)
    s_max = max(settlements)

    # Range bar (vertical line from min to max at x=P)
    ax.plot(
        [p, p], [s_min, s_max],
        color="#666", linewidth=2, zorder=3,
        solid_capstyle="round",
    )

    # Scenario dots (smaller markers)
    for s in severity_result.scenario_table:
        s_val = max(s.amplified_settlement, _S_MIN)
        ax.scatter(
            p, s_val,
            s=30, color="#999", alpha=0.6, zorder=4,
            edgecolors="#666", linewidths=0.5,
        )


def _draw_primary_dot(ax: Any, severity_result: SeverityResult) -> None:
    """Draw the primary scenario dot at (P, S_primary)."""
    p = severity_result.probability
    s = max(severity_result.severity, _S_MIN)

    zone = severity_result.zone
    color = _ZONE_COLORS.get(zone.value, "#333")

    ax.scatter(
        p, s,
        s=200, color=color, zorder=5,
        edgecolors="white", linewidths=2,
    )


def _draw_attachment_line(ax: Any, severity_result: SeverityResult) -> None:
    """Draw horizontal dashed line at Liberty attachment (if available)."""
    if severity_result.primary is None:
        return

    erosion = severity_result.primary.layer_erosion
    if erosion is None or len(erosion) == 0:
        return

    attachment = erosion[0].attachment
    if attachment <= 0:
        return

    ax.axhline(
        y=attachment,
        color="#e65100", linestyle="--", linewidth=1.5,
        alpha=0.8, zorder=2,
    )
    ax.text(
        _P_MAX * 0.98, attachment * 1.3,
        f"Liberty Attachment: {_format_dollars(attachment)}",
        fontsize=8, color="#e65100", ha="right", va="bottom",
        fontweight="bold", zorder=2,
    )


def _draw_annotations(ax: Any, severity_result: SeverityResult) -> None:
    """Draw P, S, and EL annotation boxes."""
    p = severity_result.probability
    s = max(severity_result.severity, _S_MIN)
    el = severity_result.expected_loss
    zone = severity_result.zone

    # EL annotation near the dot
    el_text = f"EL = {_format_dollars(el)}"
    ax.annotate(
        el_text,
        xy=(p, s),
        xytext=(p + 0.05, s * 2),
        fontsize=9, fontweight="bold", color="#1A1446",
        arrowprops={"arrowstyle": "->", "color": "#999", "lw": 0.8},
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white",
              "edgecolor": "#ddd", "alpha": 0.9},
        zorder=6,
    )

    # P annotation box (top-left area)
    p_text = f"P = {p:.2f}"
    ax.text(
        0.02, 0.98, p_text,
        transform=ax.transAxes,
        fontsize=9, fontweight="bold", color="#333",
        va="top", ha="left",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#f0f0f0",
              "edgecolor": "#ccc"},
        zorder=6,
    )

    # S annotation box
    s_text = f"S = {_format_dollars(severity_result.severity)}"
    ax.text(
        0.02, 0.91, s_text,
        transform=ax.transAxes,
        fontsize=9, fontweight="bold", color="#333",
        va="top", ha="left",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "#f0f0f0",
              "edgecolor": "#ccc"},
        zorder=6,
    )

    # Zone label
    zone_color = _ZONE_COLORS.get(zone.value, "#333")
    ax.text(
        0.02, 0.84, f"Zone: {zone.value}",
        transform=ax.transAxes,
        fontsize=9, fontweight="bold", color=zone_color,
        va="top", ha="left",
        zorder=6,
    )
