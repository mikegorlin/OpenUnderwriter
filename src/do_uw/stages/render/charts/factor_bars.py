"""Pure SVG horizontal factor bar generator (INFO-03).

Generates compact inline SVG bars showing points_deducted / max_points
for scoring factors. Color intensity scales with the fill percentage.
Follows the sparklines.py pattern -- pure Python string generation.
"""

from __future__ import annotations


def render_factor_bar(
    points: float,
    max_points: float,
    width: int = 120,
    height: int = 14,
    show_label: bool = True,
) -> str:
    """Render a horizontal bar showing points/max for a scoring factor.

    Args:
        points: Points deducted (0 to max_points).
        max_points: Maximum possible deduction for this factor.
        width: SVG width in pixels.
        height: SVG height in pixels.
        show_label: If True, show "X/Y" label inside the bar.

    Returns:
        SVG markup string for inline embedding.
    """
    if max_points <= 0:
        return ""

    pct = min(1.0, max(0.0, points / max_points))

    # Color based on severity
    if pct >= 0.60:
        fill_color = "#DC2626"  # Critical red
        text_color = "#FFFFFF"
    elif pct >= 0.30:
        fill_color = "#EA580C"  # Elevated orange
        text_color = "#FFFFFF"
    elif pct > 0:
        fill_color = "#D4A843"  # Gold/amber for minor
        text_color = "#1A1446"
    else:
        fill_color = "#E5E7EB"  # Gray for zero
        text_color = "#6B7280"

    bar_width = max(1, pct * (width - 2))
    track_radius = height / 2 - 1

    parts = [
        f'<svg viewBox="0 0 {width} {height}" '
        f'style="width:{width}px;height:{height}px;vertical-align:middle" '
        f'xmlns="http://www.w3.org/2000/svg">',
        # Track background
        f'<rect x="1" y="1" width="{width - 2}" height="{height - 2}" '
        f'rx="{track_radius}" fill="#F3F4F6"/>',
    ]

    # Fill bar
    if pct > 0:
        parts.append(
            f'<rect x="1" y="1" width="{bar_width:.1f}" height="{height - 2}" '
            f'rx="{track_radius}" fill="{fill_color}"/>'
        )

    # Label
    if show_label:
        pts_str = f"{points:.1f}" if points != int(points) else f"{int(points)}"
        max_str = f"{int(max_points)}"
        label = f"{pts_str}/{max_str}"
        label_x = width / 2
        label_y = height / 2 + 3.5
        # Use dark text if bar is less than half
        label_color = text_color if pct >= 0.5 else "#374151"
        parts.append(
            f'<text x="{label_x}" y="{label_y}" text-anchor="middle" '
            f'font-size="9" font-weight="600" fill="{label_color}" '
            f'font-family="system-ui, sans-serif">{label}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def render_factor_bar_set(
    factors: list[dict],
    bar_width: int = 120,
    bar_height: int = 14,
) -> list[dict]:
    """Add SVG bar strings to a list of factor dicts.

    Each factor dict should have 'score' (points deducted) and 'max' keys.
    Returns the same list with 'bar_svg' added to each dict.

    Args:
        factors: List of factor dicts with 'score' and 'max' keys.
        bar_width: Width of each bar SVG.
        bar_height: Height of each bar SVG.

    Returns:
        Same list with 'bar_svg' key added.
    """
    for f in factors:
        pts = float(f.get("score", 0))
        mx = float(f.get("max", 0))
        f["bar_svg"] = render_factor_bar(pts, mx, bar_width, bar_height)
    return factors


__all__ = ["render_factor_bar", "render_factor_bar_set"]
