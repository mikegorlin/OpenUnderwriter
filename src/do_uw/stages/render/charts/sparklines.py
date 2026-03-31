"""Pure SVG sparkline generator for inline trend indicators (CHART-03).

Generates lightweight inline SVG sparklines for display next to KV metrics.
No matplotlib dependency -- sparklines are too simple for matplotlib overhead.
Uses CHART_COLORS from design_system for consistent coloring.
"""

from __future__ import annotations

from do_uw.stages.render.chart_style_registry import get_chart_style


def render_sparkline(
    values: list[float],
    width: int = 60,
    height: int = 16,
    direction: str = "auto",
    color: str | None = None,
) -> str:
    """Render a list of numeric values as an inline SVG sparkline.

    Args:
        values: Data points to plot. Empty list returns "".
        width: SVG width in pixels (default 60).
        height: SVG height in pixels (default 16).
        direction: Trend direction for color selection.
            "auto" detects from first vs last value.
            "up", "down", "flat" use corresponding palette colors.
        color: Explicit hex color override. If provided, ignores direction.

    Returns:
        SVG markup string for inline embedding, or "" if no data.
    """
    if not values:
        return ""

    # Resolve direction
    if direction == "auto":
        if len(values) < 2:
            direction = "flat"
        elif values[-1] > values[0]:
            direction = "up"
        elif values[-1] < values[0]:
            direction = "down"
        else:
            direction = "flat"

    # Resolve color from chart style registry.
    sparkline_colors = get_chart_style("sparkline").colors
    if color is None:
        color_map = {
            "up": str(sparkline_colors.get("up", "#16A34A")),
            "down": str(sparkline_colors.get("down", "#B91C1C")),
            "flat": str(sparkline_colors.get("flat", "#6B7280")),
        }
        color = color_map.get(direction, str(sparkline_colors.get("flat", "#6B7280")))

    # Resolve area fill color (same hue, 12% opacity via hex alpha)
    area_color_map = {
        "up": str(sparkline_colors.get("area_up", color + "20")),
        "down": str(sparkline_colors.get("area_down", color + "20")),
        "flat": color + "20",
    }
    area_color = area_color_map.get(direction, color + "20")

    # Padding
    pad = 2
    draw_h = height - 2 * pad

    # Single value: horizontal line
    if len(values) == 1:
        y_mid = height / 2
        return (
            f'<svg viewBox="0 0 {width} {height}" '
            f'preserveAspectRatio="none" '
            f'style="width:{width}px;height:{height}px;vertical-align:middle" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<line x1="0" y1="{y_mid}" x2="{width}" y2="{y_mid}" '
            f'stroke="{color}" stroke-width="1.5" />'
            f"</svg>"
        )

    # Normalize values to fit within drawing area
    v_min = min(values)
    v_max = max(values)
    v_range = v_max - v_min if v_max != v_min else 1.0

    n = len(values)
    step = width / (n - 1) if n > 1 else width

    points: list[tuple[float, float]] = []
    for i, v in enumerate(values):
        x = i * step
        # Invert y: SVG y=0 is top, high values should be at top
        y = pad + draw_h - (v - v_min) / v_range * draw_h
        points.append((round(x, 2), round(y, 2)))

    # Build SVG path for the line
    path_d = f"M {points[0][0]},{points[0][1]}"
    for px, py in points[1:]:
        path_d += f" L {px},{py}"

    # Build area fill path (line path + close at bottom)
    area_d = path_d
    area_d += f" L {points[-1][0]},{height}"
    area_d += f" L {points[0][0]},{height} Z"

    return (
        f'<svg viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" '
        f'style="width:{width}px;height:{height}px;vertical-align:middle" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<path d="{area_d}" fill="{area_color}" />'
        f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
        f"</svg>"
    )


__all__ = ["render_sparkline"]
