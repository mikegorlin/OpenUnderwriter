"""Pure SVG semi-circular gauge for risk score display (INFO-01).

Generates a lightweight inline SVG gauge showing a 0-100 risk score
with tier label. No external dependencies -- pure Python SVG string
generation following the sparklines.py pattern.
"""

from __future__ import annotations

# Tier color mapping: tier label -> hex color
_TIER_COLORS: dict[str, str] = {
    "WIN": "#047857",
    "PREFERRED": "#047857",
    "WANT": "#2563EB",
    "STANDARD": "#2563EB",
    "WRITE": "#D4A843",
    "WATCH": "#D97706",
    "ELEVATED": "#D97706",
    "WALK": "#B91C1C",
    "HIGH_RISK": "#B91C1C",
    "NO TOUCH": "#7F1D1D",
    "PROHIBITED": "#7F1D1D",
}

# Arc gradient stops for the gauge background
_ARC_STOPS = [
    (0.0, "#7F1D1D"),   # 0 - worst
    (0.25, "#B91C1C"),  # 25
    (0.50, "#D97706"),  # 50
    (0.75, "#2563EB"),  # 75
    (1.0, "#047857"),   # 100 - best
]


def render_score_gauge(
    score: float,
    tier: str = "",
    width: int = 200,
    height: int = 120,
) -> str:
    """Render a semi-circular gauge SVG showing a 0-100 risk score.

    The gauge is a 180-degree arc from left to right. The needle
    points to the score position. Tier label is displayed below.

    Args:
        score: Risk quality score 0-100 (higher = better).
        tier: Tier label (e.g., "WIN", "WALK"). Displayed below gauge.
        width: SVG width in pixels.
        height: SVG height in pixels.

    Returns:
        SVG markup string for inline embedding.
    """
    import math

    # Clamp score
    score = max(0.0, min(100.0, float(score)))

    cx = width / 2
    cy = height - 10  # Center of the arc at bottom
    radius = min(cx - 10, cy - 10)
    inner_radius = radius * 0.72

    # Build arc background with gradient segments
    arc_segments = _build_arc_segments(cx, cy, radius, inner_radius)

    # Needle angle: 0 = left (score 0), 180 = right (score 100)
    angle_deg = 180 * (score / 100)
    angle_rad = math.radians(180 - angle_deg)  # SVG coordinate system

    needle_x = cx + (radius * 0.85) * math.cos(angle_rad)
    needle_y = cy - (radius * 0.85) * math.sin(angle_rad)

    # Tier color for needle and score text
    tier_color = _TIER_COLORS.get(tier.upper().replace(" ", "_"), "#6B7280")

    # Score text position (center of arc)
    score_text = f"{score:.0f}" if score == int(score) else f"{score:.1f}"

    parts = [
        f'<svg viewBox="0 0 {width} {height}" '
        f'style="width:{width}px;height:{height}px" '
        f'xmlns="http://www.w3.org/2000/svg">',
        # Gradient definition
        f'<defs>'
        f'<linearGradient id="gauge-grad" x1="0%" y1="0%" x2="100%" y2="0%">',
    ]
    for offset, color in _ARC_STOPS:
        parts.append(
            f'<stop offset="{offset * 100}%" stop-color="{color}"/>'
        )
    parts.append('</linearGradient></defs>')

    # Background arc (full semi-circle)
    parts.append(arc_segments)

    # Tick marks at 0, 25, 50, 75, 100
    for tick_score in [0, 25, 50, 75, 100]:
        tick_angle = math.radians(180 - 180 * (tick_score / 100))
        tx1 = cx + radius * math.cos(tick_angle)
        ty1 = cy - radius * math.sin(tick_angle)
        tx2 = cx + (radius + 4) * math.cos(tick_angle)
        ty2 = cy - (radius + 4) * math.sin(tick_angle)
        parts.append(
            f'<line x1="{tx1:.1f}" y1="{ty1:.1f}" '
            f'x2="{tx2:.1f}" y2="{ty2:.1f}" '
            f'stroke="#9CA3AF" stroke-width="1.5"/>'
        )

    # Needle
    parts.append(
        f'<line x1="{cx}" y1="{cy}" '
        f'x2="{needle_x:.1f}" y2="{needle_y:.1f}" '
        f'stroke="{tier_color}" stroke-width="2.5" stroke-linecap="round"/>'
    )
    # Needle hub
    parts.append(
        f'<circle cx="{cx}" cy="{cy}" r="4" fill="{tier_color}"/>'
    )

    # Score text
    parts.append(
        f'<text x="{cx}" y="{cy - 14}" text-anchor="middle" '
        f'font-size="22" font-weight="800" fill="{tier_color}" '
        f'font-family="system-ui, sans-serif">{score_text}</text>'
    )

    # Tier label
    if tier:
        parts.append(
            f'<text x="{cx}" y="{cy + 2}" text-anchor="middle" '
            f'font-size="9" font-weight="600" fill="#6B7280" '
            f'font-family="system-ui, sans-serif">{tier.upper()}</text>'
        )

    parts.append("</svg>")
    return "".join(parts)


def _build_arc_segments(
    cx: float, cy: float, outer_r: float, inner_r: float
) -> str:
    """Build the colored arc background as a single gradient-filled path."""
    import math

    # Semi-circle arc path (left to right)
    # Outer arc: from (cx - outer_r, cy) to (cx + outer_r, cy)
    # Inner arc: from (cx + inner_r, cy) to (cx - inner_r, cy)
    path = (
        f'<path d="'
        f"M {cx - outer_r:.1f},{cy:.1f} "
        f"A {outer_r:.1f},{outer_r:.1f} 0 0 1 {cx + outer_r:.1f},{cy:.1f} "
        f"L {cx + inner_r:.1f},{cy:.1f} "
        f"A {inner_r:.1f},{inner_r:.1f} 0 0 0 {cx - inner_r:.1f},{cy:.1f} "
        f'Z" fill="url(#gauge-grad)" opacity="0.85"/>'
    )
    return path


__all__ = ["render_score_gauge"]
