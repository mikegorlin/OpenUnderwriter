"""Pure SVG waterfall chart for scoring factor buildup.

Renders a vertical waterfall showing how each scoring factor deducts
points from the starting score of 100, with tier threshold reference
lines. Follows the factor_bars.py pure SVG pattern -- no matplotlib.
"""

from __future__ import annotations

from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.formatters import safe_float


# Severity color thresholds (same as factor_bars.py)
_RED = "#DC2626"      # >=60% of max
_ORANGE = "#EA580C"   # >=30% of max
_GOLD = "#D4A843"     # >0% of max
_SUMMARY_COLOR = "#1A1446"  # Navy for final score bar

# Tier threshold line styling
_TIER_LINE_COLOR = "#94A3B8"
_TIER_LABEL_COLOR = "#64748B"


def _severity_color(points: float, max_points: float) -> str:
    """Return fill color based on deduction severity."""
    if max_points <= 0:
        return _GOLD
    pct = points / max_points
    if pct >= 0.60:
        return _RED
    if pct >= 0.30:
        return _ORANGE
    return _GOLD


@null_safe_chart
def render_waterfall_chart(
    factors: list[dict],
    total_score: float | str,
    tier_thresholds: list[dict],
    width: int = 580,
    height: int = 320,
) -> str:
    """Render a waterfall chart showing scoring factor deductions.

    Each non-zero factor renders as a horizontal bar showing its point
    deduction. Bars stack top-to-bottom starting from score=100. Dashed
    vertical lines mark tier thresholds (WIN, WANT, WRITE, etc.).

    Args:
        factors: List of dicts with keys: id, name, points_deducted, max_points.
        total_score: Final quality score (0-100).
        tier_thresholds: List of dicts with keys: tier, min_score.
        width: SVG width in pixels.
        height: SVG height in pixels.

    Returns:
        SVG markup string for inline embedding.
    """
    total = safe_float(total_score, 0.0)

    # Filter to non-zero factors only
    active = []
    for f in factors:
        pts = safe_float(f.get("points_deducted", 0), 0.0)
        if pts > 0:
            active.append({
                "id": str(f.get("id", "")),
                "name": str(f.get("name", "")),
                "points": pts,
                "max_points": safe_float(f.get("max_points", 0), 1.0),
            })

    # Layout constants
    left_margin = 160  # Space for factor labels
    right_margin = 20
    top_margin = 30   # Space for tier labels
    bottom_margin = 40  # Space for score axis + summary
    chart_width = width - left_margin - right_margin
    n_bars = len(active) + 1  # +1 for summary bar
    bar_area_height = height - top_margin - bottom_margin
    bar_height = min(24, max(14, bar_area_height // max(n_bars, 1) - 4))
    bar_gap = max(2, (bar_area_height - n_bars * bar_height) // max(n_bars, 1))

    # Score axis: 0 on left, 100 on right
    def score_to_x(score: float) -> float:
        return left_margin + (safe_float(score) / 100.0) * chart_width

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" '
        f'style="width:{width}px;height:{height}px" '
        f'xmlns="http://www.w3.org/2000/svg">',
        # Background
        f'<rect width="{width}" height="{height}" fill="#FFFFFF"/>',
    ]

    # -- Tier threshold dashed lines --
    for t in tier_thresholds:
        min_score = safe_float(t.get("min_score", 0), 0.0)
        x = score_to_x(min_score)
        tier_name = str(t.get("tier", ""))
        # Dashed vertical line
        parts.append(
            f'<line x1="{x:.1f}" y1="{top_margin}" '
            f'x2="{x:.1f}" y2="{height - bottom_margin + 10}" '
            f'stroke="{_TIER_LINE_COLOR}" stroke-width="1" '
            f'stroke-dasharray="4,3" opacity="0.6"/>'
        )
        # Tier label at top
        parts.append(
            f'<text x="{x:.1f}" y="{top_margin - 8}" text-anchor="middle" '
            f'font-size="8" font-weight="600" fill="{_TIER_LABEL_COLOR}" '
            f'font-family="system-ui, sans-serif">{tier_name}</text>'
        )

    # -- Score axis at bottom --
    axis_y = height - bottom_margin + 15
    for tick in [0, 25, 50, 75, 100]:
        x = score_to_x(tick)
        parts.append(
            f'<text x="{x:.1f}" y="{axis_y}" text-anchor="middle" '
            f'font-size="8" fill="#94A3B8" '
            f'font-family="system-ui, sans-serif">{tick}</text>'
        )

    # -- Factor bars (top to bottom, cumulative) --
    running_score = 100.0
    for i, f in enumerate(active):
        y = top_margin + i * (bar_height + bar_gap)
        pts = f["points"]
        color = _severity_color(pts, f["max_points"])

        # Bar extends from (running_score - pts) to running_score
        new_score = running_score - pts
        x_start = score_to_x(new_score)
        x_end = score_to_x(running_score)
        bar_w = max(1, x_end - x_start)

        # Factor label on left
        label = f"{f['id']} {f['name']}"
        parts.append(
            f'<text x="{left_margin - 8}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="end" font-size="9" fill="#374151" '
            f'font-family="system-ui, sans-serif">{label}</text>'
        )

        # Bar rect
        parts.append(
            f'<rect x="{x_start:.1f}" y="{y}" '
            f'width="{bar_w:.1f}" height="{bar_height}" '
            f'rx="2" fill="{color}" opacity="0.85"/>'
        )

        # Points label centered in bar — round to 1 decimal
        pts_label = f"-{pts:.1f}"
        # Choose text color based on bar width
        label_color = "#FFFFFF" if bar_w > 30 else "#374151"
        label_x = x_start + bar_w / 2 if bar_w > 30 else x_start + bar_w + 4
        anchor = "middle" if bar_w > 30 else "start"
        parts.append(
            f'<text x="{label_x:.1f}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="{anchor}" font-size="9" font-weight="600" '
            f'fill="{label_color}" '
            f'font-family="system-ui, sans-serif">{pts_label}</text>'
        )

        running_score = new_score

    # -- Summary bar (final score) --
    summary_y = top_margin + len(active) * (bar_height + bar_gap)
    x_zero = score_to_x(0)
    x_score = score_to_x(total)
    summary_w = max(1, x_score - x_zero)

    parts.append(
        f'<text x="{left_margin - 8}" y="{summary_y + bar_height / 2 + 4}" '
        f'text-anchor="end" font-size="9" font-weight="700" fill="{_SUMMARY_COLOR}" '
        f'font-family="system-ui, sans-serif">Final Score</text>'
    )
    parts.append(
        f'<rect x="{x_zero:.1f}" y="{summary_y}" '
        f'width="{summary_w:.1f}" height="{bar_height}" '
        f'rx="2" fill="{_SUMMARY_COLOR}" opacity="0.9"/>'
    )
    score_label = f"{int(total)}" if total == int(total) else f"{total:.1f}"
    parts.append(
        f'<text x="{x_zero + summary_w / 2:.1f}" y="{summary_y + bar_height / 2 + 4}" '
        f'text-anchor="middle" font-size="10" font-weight="700" fill="#FFFFFF" '
        f'font-family="system-ui, sans-serif">{score_label}</text>'
    )

    parts.append("</svg>")
    return "".join(parts)


__all__ = ["render_waterfall_chart"]
