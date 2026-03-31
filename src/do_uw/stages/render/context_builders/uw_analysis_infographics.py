"""Inline SVG infographic builders and formatters for the UW Analysis.

Generates decile dots, range sliders, sparklines, composition bars,
EV/Revenue sliders, score bar segments, and number formatting helpers.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState


# ── Number formatters ────────────────────────────────────────────────


def fmt_large_number(val: float | int | None) -> str:
    """Format large numbers compactly: $3.6T, $416.2B, $152.9M."""
    if val is None:
        return "N/A"
    import math
    try:
        v = float(val)
    except (ValueError, TypeError):
        return "N/A"
    if math.isnan(v) or math.isinf(v):
        return "N/A"
    if abs(v) >= 1e12:
        return f"${v / 1e12:.1f}T"
    if abs(v) >= 1e9:
        return f"${v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.1f}M"
    if abs(v) >= 1e3:
        return f"${v / 1e3:.0f}K"
    return f"${v:.0f}"


def fmt_price(val: float | None) -> str:
    """Format as dollar price: $174.08."""
    if val is None:
        return "N/A"
    return f"${val:,.2f}"


def fmt_ratio(val: float | None) -> str:
    """Format as ratio: 5.53x."""
    if val is None:
        return "N/A"
    return f"{val:.2f}x"


def fmt_int(val: int | float | None) -> str:
    """Format as integer with commas: 7,100."""
    if val is None:
        return "N/A"
    return f"{int(val):,}"


# ── Infographic SVG builders ─────────────────────────────────────────


def mcap_label(val: float | None) -> str:
    """Return market cap tier label: Nano/Micro/Small/Mid/Large/Mega."""
    if val is None:
        return ""
    v = float(val)
    if v >= 200e9:
        return "Mega-Cap"
    if v >= 10e9:
        return "Large-Cap"
    if v >= 2e9:
        return "Mid-Cap"
    if v >= 300e6:
        return "Small-Cap"
    if v >= 50e6:
        return "Micro-Cap"
    return "Nano-Cap"


def mcap_decile(val: float | None) -> int:
    """Approximate market cap decile (1-10) among public companies."""
    if val is None:
        return 5
    v = float(val)
    boundaries = [100e6, 300e6, 700e6, 1.5e9, 3e9, 7e9, 15e9, 40e9, 100e9]
    for i, b in enumerate(boundaries):
        if v < b:
            return i + 1
    return 10


def score_bar_cx(score: float) -> float:
    """Map quality score (0-100) to SVG x-position on score bar."""
    return max(0.0, min(200.0, score * 2.0))


def tier_score_segments() -> list[dict[str, Any]]:
    """Score bar segments: RED (left, low score = bad) → GREEN (right, high score = good).

    quality_score 100 = perfect (no risk deductions), 0 = maximum risk.
    """
    return [
        {"x": 0, "w": 20, "fill": "#7F1D1D"},    # 0-10:  NO_TOUCH — darkest red
        {"x": 20, "w": 40, "fill": "#DC2626"},    # 10-30: WALK — red
        {"x": 60, "w": 40, "fill": "#EA580C"},    # 30-50: WATCH low — dark orange
        {"x": 100, "w": 40, "fill": "#F59E0B"},   # 50-70: WATCH high — amber
        {"x": 140, "w": 30, "fill": "#22C55E"},   # 70-85: WRITE — light green
        {"x": 170, "w": 30, "fill": "#16A34A"},   # 85-100: WIN — green
    ]


def build_decile_svg(decile: int, width: int = 120, height: int = 8) -> str:
    """Build a decile bar SVG that stretches to fill container width."""
    # Use percentage-based layout so bar fills tile width
    parts = [
        f'<div style="display:flex;gap:2px;height:{height}px;width:100%">'
    ]
    for i in range(10):
        fill = "#111827" if i < decile else "#E5E7EB"
        parts.append(
            f'<div style="flex:1;background:{fill};border-radius:1.5px"></div>'
        )
    parts.append("</div>")
    return "".join(parts)


def build_ev_revenue_slider_svg(ev_revenue: float | None) -> str:
    """Build an EV/Revenue range slider SVG."""
    if ev_revenue is None:
        return ""
    max_val = 15.0
    pct = min(1.0, max(0.0, (ev_revenue - 1.0) / (max_val - 1.0)))
    left_pct = pct * 100
    return (
        f'<div style="margin-top:4px">'
        f'<div style="display:flex;justify-content:space-between;font-size:5pt;'
        f'color:#9CA3AF;margin-bottom:1px"><span>1x</span><span>5x</span>'
        f'<span>10x</span><span>15x</span></div>'
        f'<div style="height:5px;background:#F3F4F6;border-radius:3px;'
        f'position:relative">'
        f'<div style="position:absolute;left:{left_pct:.0f}%;top:-2px;width:8px;'
        f'height:9px;background:#6366F1;border-radius:3px;margin-left:-4px"></div>'
        f'</div>'
        f'<div style="font-size:6pt;color:#6366F1;font-weight:600;margin-top:2px;'
        f'text-align:center">{ev_revenue:.1f}x EV/Revenue</div></div>'
    )


def build_composition_bar_svg(
    cash: float | None,
    debt: float | None,
    total_assets: float | None,
) -> str:
    """Build a cash/debt composition bar as percentage of total assets."""
    if not total_assets or total_assets <= 0:
        return ""
    cash_pct = ((cash or 0) / total_assets * 100) if cash else 0
    debt_pct = ((debt or 0) / total_assets * 100) if debt else 0
    return (
        f'<div style="display:flex;height:8px;border-radius:4px;overflow:hidden;'
        f'margin-top:4px;background:#F3F4F6">'
        f'<div style="width:{cash_pct:.0f}%;background:#16A34A;opacity:0.6"></div>'
        f'<div style="width:{debt_pct:.0f}%;background:#DC2626;opacity:0.6"></div>'
        f'</div>'
        f'<div style="display:flex;justify-content:space-between;font-size:5.5pt;'
        f'color:#9CA3AF;margin-top:1px">'
        f'<span><span style="color:#16A34A;font-weight:700">&#9632;</span> '
        f'Cash {cash_pct:.0f}%</span>'
        f'<span><span style="color:#DC2626;font-weight:700">&#9632;</span> '
        f'Debt {debt_pct:.0f}%</span>'
        f'<span>of total assets</span></div>'
    )


def build_range_slider_svg(
    current: float | None,
    low: float | None,
    high: float | None,
) -> str:
    """Build a 52-week range slider with green fill + position marker."""
    if not current or not low or not high or high <= low:
        return ""
    pct = max(0.0, min(1.0, (current - low) / (high - low)))
    pct_display = pct * 100
    return (
        f'<div style="display:flex;align-items:center;gap:3px;margin-top:3px">'
        f'<span style="font-size:6.5pt;color:#9CA3AF">${low:,.0f}</span>'
        f'<div style="flex:1;position:relative;height:6px;background:#F3F4F6;'
        f'border-radius:3px">'
        f'<div style="position:absolute;left:0;top:0;width:{pct_display:.0f}%;'
        f'height:100%;background:#16A34A;border-radius:3px;opacity:0.25"></div>'
        f'<div style="position:absolute;left:{pct_display:.0f}%;top:-2px;width:8px;'
        f'height:10px;background:#16A34A;border-radius:3px;margin-left:-4px"></div>'
        f'</div>'
        f'<span style="font-size:6.5pt;color:#9CA3AF">${high:,.0f}</span></div>'
    )


def build_sparkline_svg(
    values: list[float],
    width: int = 120,
    height: int = 32,
    stroke_color: str = "#1D4ED8",
) -> str:
    """Build a mini sparkline SVG string from a list of values."""
    if len(values) < 2:
        return ""
    v_min = min(values)
    v_max = max(values)
    v_range = v_max - v_min if v_max != v_min else 1.0
    n = len(values)
    pad = 4.0
    usable_w = width - 2 * pad
    usable_h = height - 2 * pad

    points = []
    for i, v in enumerate(values):
        x = pad + (i / (n - 1)) * usable_w
        y = pad + (1.0 - (v - v_min) / v_range) * usable_h
        points.append(f"{x:.1f},{y:.1f}")

    last_x = pad + usable_w
    last_y = pad + (1.0 - (values[-1] - v_min) / v_range) * usable_h

    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f'<polyline points="{" ".join(points)}" fill="none" '
        f'stroke="{stroke_color}" stroke-width="1.5" stroke-linejoin="round"/>'
        f'<circle cx="{last_x:.1f}" cy="{last_y:.1f}" r="2.5" '
        f'fill="{stroke_color}"/>'
        f"</svg>"
    )


def extract_revenue_sparkline(state: AnalysisState) -> list[float]:
    """Extract annual revenue values for sparkline (up to 5 years)."""
    return _extract_yfinance_metric(state, "income_stmt", "Total Revenue")


def extract_ebitda_sparkline(state: AnalysisState) -> list[float]:
    """Extract annual EBITDA values for sparkline."""
    return _extract_yfinance_metric(state, "income_stmt", "EBITDA")


def extract_fcf_sparkline(state: AnalysisState) -> list[float]:
    """Extract annual free cash flow values for sparkline."""
    return _extract_yfinance_metric(state, "cashflow", "Free Cash Flow")


def extract_total_assets(state: AnalysisState) -> float | None:
    """Extract most recent total assets from yfinance balance sheet."""
    vals = _extract_yfinance_metric(state, "balance_sheet", "Total Assets")
    return vals[0] if vals else None


def _extract_yfinance_metric(
    state: AnalysisState, stmt_key: str, field_name: str,
) -> list[float]:
    """Extract annual metrics from yfinance data in acquired_data.market_data."""
    try:
        md = state.acquired_data.market_data if state.acquired_data else None
        if not md:
            return []
        if isinstance(md, dict):
            stmt = md.get(stmt_key, {})
        elif hasattr(md, stmt_key):
            stmt = getattr(md, stmt_key, {}) or {}
        else:
            return []
        if not isinstance(stmt, dict):
            return []
        # yfinance stores as {"line_items": {"field": [val1, val2, ...]}}
        line_items = stmt.get("line_items", {})
        if isinstance(line_items, dict):
            raw = line_items.get(field_name, [])
            if isinstance(raw, list):
                values = [float(v) for v in raw if v is not None]
                # Reverse so oldest first (for sparkline left-to-right chronology)
                return list(reversed(values[-5:]))
        return []
    except Exception:
        return []


def format_earnings_date(info: dict[str, Any]) -> str:
    """Extract and format next earnings date from yfinance info."""
    raw = info.get("earningsDate")
    if not raw:
        return "N/A"
    if isinstance(raw, list) and raw:
        raw = raw[0]
    try:
        from datetime import datetime

        if isinstance(raw, (int, float)):
            dt = datetime.fromtimestamp(raw)
        elif hasattr(raw, "strftime"):
            dt = raw
        else:
            return str(raw)
        return dt.strftime("%B %d, %Y")
    except Exception:
        return str(raw)
