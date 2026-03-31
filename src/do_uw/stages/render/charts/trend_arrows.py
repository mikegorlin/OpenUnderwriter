"""Pure SVG trend arrow generator (INFO-04).

Generates small colored up/down/flat SVG arrows for inline display
next to key metrics. Follows the sparklines.py pattern.
"""

from __future__ import annotations


# Default colors: green up, red down, gray flat
_ARROW_COLORS: dict[str, str] = {
    "up": "#059669",
    "down": "#DC2626",
    "flat": "#6B7280",
}

# Inverted colors for metrics where down is good (e.g., expenses, debt)
_ARROW_COLORS_INVERTED: dict[str, str] = {
    "up": "#DC2626",
    "down": "#059669",
    "flat": "#6B7280",
}


def render_trend_arrow(
    direction: str = "flat",
    size: int = 12,
    inverted: bool = False,
    color: str | None = None,
    label: str = "",
) -> str:
    """Render a small SVG trend arrow for inline metric display.

    Args:
        direction: "up", "down", or "flat".
        size: Arrow size in pixels (square viewbox).
        inverted: If True, up=bad (red), down=good (green).
            Use for metrics like expenses where decrease is positive.
        color: Explicit color override (hex). Ignores direction/inverted.
        label: Optional tooltip text.

    Returns:
        SVG markup string for inline embedding, or "" for invalid direction.
    """
    direction = direction.strip().lower()
    if direction not in ("up", "down", "flat"):
        return ""

    # Resolve color
    if color is None:
        palette = _ARROW_COLORS_INVERTED if inverted else _ARROW_COLORS
        color = palette[direction]

    title_attr = f' title="{label}"' if label else ""

    if direction == "up":
        # Upward pointing triangle
        path = f"M {size * 0.2} {size * 0.75} L {size * 0.5} {size * 0.2} L {size * 0.8} {size * 0.75} Z"
    elif direction == "down":
        # Downward pointing triangle
        path = f"M {size * 0.2} {size * 0.25} L {size * 0.5} {size * 0.8} L {size * 0.8} {size * 0.25} Z"
    else:
        # Flat: horizontal dash
        y_mid = size * 0.5
        return (
            f'<svg viewBox="0 0 {size} {size}" '
            f'style="width:{size}px;height:{size}px;vertical-align:middle;display:inline-block" '
            f'xmlns="http://www.w3.org/2000/svg"{title_attr}>'
            f'<line x1="{size * 0.15}" y1="{y_mid}" '
            f'x2="{size * 0.85}" y2="{y_mid}" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round"/>'
            f"</svg>"
        )

    return (
        f'<svg viewBox="0 0 {size} {size}" '
        f'style="width:{size}px;height:{size}px;vertical-align:middle;display:inline-block" '
        f'xmlns="http://www.w3.org/2000/svg"{title_attr}>'
        f'<path d="{path}" fill="{color}"/>'
        f"</svg>"
    )


def trend_direction(
    current: float | None,
    previous: float | None,
    threshold_pct: float = 2.0,
) -> str:
    """Determine trend direction from two values.

    Args:
        current: Current period value.
        previous: Prior period value.
        threshold_pct: Minimum % change to count as up/down (default 2%).

    Returns:
        "up", "down", or "flat".
    """
    if current is None or previous is None:
        return "flat"
    if previous == 0:
        return "up" if current > 0 else ("down" if current < 0 else "flat")

    pct_change = ((current - previous) / abs(previous)) * 100
    if pct_change > threshold_pct:
        return "up"
    elif pct_change < -threshold_pct:
        return "down"
    return "flat"


__all__ = ["render_trend_arrow", "trend_direction"]
