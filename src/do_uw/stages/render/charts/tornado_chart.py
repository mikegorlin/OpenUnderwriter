"""Pure SVG tornado chart for scenario score sensitivity.

Renders horizontal bars extending left (worse) or right (better)
from a center line at the current score. Scenarios sorted by
absolute delta magnitude. Follows the factor_bars.py pure SVG pattern.
"""

from __future__ import annotations

from do_uw.stages.render.charts.chart_guards import null_safe_chart
from do_uw.stages.render.formatters import safe_float


# Directional colors
_RED = "#DC2626"    # Negative delta (worse risk)
_BLUE = "#2563EB"   # Positive delta (better risk)
_CENTER_COLOR = "#1A1446"  # Navy for center line


@null_safe_chart
def render_tornado_chart(
    scenarios: list[dict],
    current_score: float | str,
    width: int = 580,
    height: int = 280,
) -> str:
    """Render a tornado chart showing scenario score sensitivity.

    Horizontal bars extend left (negative/worse) or right (positive/better)
    from a center line at the current score position. Bars are sorted by
    absolute delta magnitude (largest impact at top).

    Args:
        scenarios: List of dicts with keys: name, score_delta, current_score.
        current_score: Current quality score (0-100).
        width: SVG width in pixels.
        height: SVG height in pixels.

    Returns:
        SVG markup string for inline embedding.
    """
    score = safe_float(current_score, 50.0)

    # Parse and sort scenarios by absolute delta
    parsed = []
    for s in scenarios:
        delta = safe_float(s.get("score_delta", 0), 0.0)
        name = str(s.get("name", ""))
        parsed.append({"name": name, "delta": delta})

    parsed.sort(key=lambda x: abs(x["delta"]), reverse=True)

    # Layout constants
    left_margin = 150  # Space for scenario name labels
    right_margin = 50  # Space for delta value labels
    top_margin = 30
    bottom_margin = 25
    chart_width = width - left_margin - right_margin
    n_bars = len(parsed)
    bar_area_height = height - top_margin - bottom_margin
    bar_height = min(28, max(16, bar_area_height // max(n_bars, 1) - 6))
    bar_gap = max(4, (bar_area_height - n_bars * bar_height) // max(n_bars, 1))

    # Score axis: 0 on left, 100 on right
    def score_to_x(s: float) -> float:
        return left_margin + (safe_float(s) / 100.0) * chart_width

    center_x = score_to_x(score)

    # Find max absolute delta for scale
    max_abs_delta = max((abs(p["delta"]) for p in parsed), default=1.0)
    # Scale bars so the largest delta fills ~40% of chart width
    scale = (chart_width * 0.4) / max(max_abs_delta, 1.0)

    parts: list[str] = [
        f'<svg viewBox="0 0 {width} {height}" '
        f'style="width:{width}px;height:{height}px" '
        f'xmlns="http://www.w3.org/2000/svg">',
        # Background
        f'<rect width="{width}" height="{height}" fill="#FFFFFF"/>',
    ]

    # -- Center line (dashed) --
    parts.append(
        f'<line x1="{center_x:.1f}" y1="{top_margin - 5}" '
        f'x2="{center_x:.1f}" y2="{height - bottom_margin + 5}" '
        f'stroke="{_CENTER_COLOR}" stroke-width="1.5" '
        f'stroke-dasharray="4,3"/>'
    )

    # -- Current score label at top --
    parts.append(
        f'<text x="{center_x:.1f}" y="{top_margin - 10}" text-anchor="middle" '
        f'font-size="9" font-weight="700" fill="{_CENTER_COLOR}" '
        f'font-family="system-ui, sans-serif">Current: {int(score) if score == int(score) else score:.1f}</text>'
    )

    # -- Scenario bars --
    for i, p in enumerate(parsed):
        y = top_margin + i * (bar_height + bar_gap)
        delta = p["delta"]
        name = p["name"]
        color = _RED if delta < 0 else _BLUE

        bar_w = abs(delta) * scale
        bar_w = max(2, min(bar_w, chart_width * 0.45))  # Clamp

        if delta < 0:
            # Extends left from center
            x_start = center_x - bar_w
        else:
            # Extends right from center
            x_start = center_x

        # Scenario name label on left margin
        parts.append(
            f'<text x="{left_margin - 8}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="end" font-size="9" fill="#374151" '
            f'font-family="system-ui, sans-serif">{name}</text>'
        )

        # Bar rect
        parts.append(
            f'<rect x="{x_start:.1f}" y="{y}" '
            f'width="{bar_w:.1f}" height="{bar_height}" '
            f'rx="2" fill="{color}" opacity="0.85"/>'
        )

        # Delta value label
        delta_int = int(delta) if delta == int(delta) else delta
        delta_label = f"+{delta_int}" if delta > 0 else f"{delta_int}"
        if delta < 0:
            label_x = x_start - 4
            anchor = "end"
        else:
            label_x = x_start + bar_w + 4
            anchor = "start"
        parts.append(
            f'<text x="{label_x:.1f}" y="{y + bar_height / 2 + 4}" '
            f'text-anchor="{anchor}" font-size="9" font-weight="600" '
            f'fill="{color}" '
            f'font-family="system-ui, sans-serif">{delta_label}</text>'
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

    parts.append("</svg>")
    return "".join(parts)


__all__ = ["render_tornado_chart"]
