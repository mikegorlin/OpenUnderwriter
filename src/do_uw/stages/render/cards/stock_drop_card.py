"""Stock Drop Analysis Card — standalone visual component.

Generates a self-contained HTML card with:
- Dark header with stats (events, worst drop, attribution rate)
- SVG price chart with numbered drop markers
- V9 gradient severity table (bg intensity = drop magnitude, left color accent)
- Per-event distinct colors matching chart markers to legend rows

This is the REFERENCE CARD for the card-based worksheet redesign.
All other cards should follow this pattern.
"""

from __future__ import annotations

import html
import math
from typing import Any


def render_stock_drop_card(
    svg_chart: str,
    legend_data: list[dict[str, Any]],
    ticker: str = "",
    company_name: str = "",
    sector: str = "",
) -> str:
    """Render the complete Stock Drop Analysis Card as HTML.

    Args:
        svg_chart: SVG string from create_unified_drop_chart(format="svg").
        legend_data: List of dicts from build_drop_legend_data().
        ticker: Stock ticker symbol.
        company_name: Short company name.
        sector: Sector/industry label.

    Returns:
        Complete HTML string (no doctype — embeddable fragment or standalone).
    """
    event_count = len(legend_data)
    worst_pct = min((d["drop_pct_raw"] for d in legend_data), default=0)
    attributed = sum(
        1 for d in legend_data
        if d["category"] != "unknown" and d["category_label"] != "—"
    )

    header = _render_header(
        ticker, company_name, sector, event_count, worst_pct, attributed,
    )
    chart = _render_chart_area(svg_chart)
    table = _render_legend_table(legend_data)
    footer = _render_footer()

    return f"""<div style="max-width:1200px;margin:0 auto;font-family:Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<div style="background:white;border-radius:16px;overflow:hidden;border:1px solid #E2E8F0;box-shadow:0 2px 16px rgba(0,0,0,0.06)">
{header}
{chart}
{table}
{footer}
</div>
</div>"""


def render_stock_drop_card_standalone(
    svg_chart: str,
    legend_data: list[dict[str, Any]],
    ticker: str = "",
    company_name: str = "",
    sector: str = "",
) -> str:
    """Render as a full standalone HTML page (with doctype, head, styles)."""
    card = render_stock_drop_card(
        svg_chart, legend_data, ticker, company_name, sector,
    )
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Stock Drop Analysis — {html.escape(ticker)}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
body {{
  font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #F1F5F9;
  padding: 40px 20px;
  margin: 0;
}}
svg {{ width: 100%; height: auto; }}
</style>
</head>
<body>
{card}
</body></html>"""


# ---------------------------------------------------------------------------
# Header — dark bar with key stats
# ---------------------------------------------------------------------------

def _render_header(
    ticker: str,
    company_name: str,
    sector: str,
    event_count: int,
    worst_pct: float,
    attributed: int,
) -> str:
    subtitle = f"{ticker}"
    if company_name:
        subtitle += f" · {html.escape(company_name)}"
    if sector:
        subtitle += f" · {html.escape(sector)}"

    return f"""<div style="background:#16132B;padding:18px 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
  <div style="display:flex;align-items:center;gap:16px">
    <div>
      <div style="font-size:15pt;font-weight:800;color:white;letter-spacing:0.3px">Stock Drop Analysis</div>
      <div style="font-size:8pt;color:#94A3B8;margin-top:2px">{subtitle}</div>
    </div>
    <div style="display:flex;align-items:center;gap:6px;padding:5px 14px;background:rgba(56,189,248,0.1);border:1px solid rgba(56,189,248,0.15);border-radius:8px">
      <div style="width:40px;height:4px;background:rgba(255,255,255,0.08);border-radius:2px;overflow:hidden"><div style="width:100%;height:100%;background:#38BDF8;border-radius:2px"></div></div>
      <span style="font-size:8pt;color:#38BDF8;font-weight:700">2 Year</span>
    </div>
  </div>
  <div style="display:flex;gap:28px;align-items:center">
    <div style="text-align:center">
      <div style="font-size:26pt;font-weight:900;color:white;line-height:1">{event_count}</div>
      <div style="font-size:6pt;color:#64748B;text-transform:uppercase;letter-spacing:1.5px;margin-top:3px">Events</div>
    </div>
    <div style="width:1px;height:36px;background:rgba(255,255,255,0.06)"></div>
    <div style="text-align:center">
      <div style="font-size:26pt;font-weight:900;color:#F43F5E;line-height:1">{worst_pct:+.0f}%</div>
      <div style="font-size:6pt;color:#64748B;text-transform:uppercase;letter-spacing:1.5px;margin-top:3px">Worst</div>
    </div>
    <div style="width:1px;height:36px;background:rgba(255,255,255,0.06)"></div>
    <div style="text-align:center">
      <div style="font-size:26pt;font-weight:900;color:#38BDF8;line-height:1">{attributed}<span style="font-size:14pt;color:#475569">/{event_count}</span></div>
      <div style="font-size:6pt;color:#64748B;text-transform:uppercase;letter-spacing:1.5px;margin-top:3px">Attributed</div>
    </div>
  </div>
</div>"""


# ---------------------------------------------------------------------------
# Chart area
# ---------------------------------------------------------------------------

def _render_chart_area(svg_chart: str) -> str:
    return f"""<div style="padding:2px 4px;background:#16132B">{svg_chart}</div>"""


# ---------------------------------------------------------------------------
# Legend table — V9 gradient severity design
# ---------------------------------------------------------------------------

def _severity_opacity(drop_pct_raw: float) -> float:
    """Map drop magnitude to background opacity (0.02 to 0.12)."""
    pct = abs(drop_pct_raw)
    if pct >= 30:
        return 0.10
    if pct >= 20:
        return 0.08
    if pct >= 10:
        return 0.06
    if pct >= 5:
        return 0.04
    return 0.02


def _drop_color(drop_pct_raw: float) -> str:
    """Color for drop percentage text by severity."""
    pct = abs(drop_pct_raw)
    if pct >= 20:
        return "#DC2626"  # Red-600
    if pct >= 10:
        return "#EA580C"  # Orange-600
    if pct >= 5:
        return "#D97706"  # Amber-600
    return "#475569"  # Slate-600


def _drop_font_size(drop_pct_raw: float) -> str:
    """Larger font for bigger drops — visual weight scales with severity."""
    pct = abs(drop_pct_raw)
    if pct >= 30:
        return "15pt"
    if pct >= 15:
        return "14pt"
    if pct >= 8:
        return "12pt"
    return "11pt"


def _format_date_short(date_str: str) -> str:
    """Convert 2024-05-10 to 5/10 '24, and ranges to 5/10 – 7/2 '24."""
    def _single(d: str) -> tuple[str, str]:
        parts = d.strip().split("-")
        if len(parts) == 3:
            y, m, day = parts
            return f"{int(m)}/{int(day)}", f"'{y[2:]}"
        return d, ""

    if " – " in date_str:
        left, right = date_str.split(" – ", 1)
        l_date, _ = _single(left)
        r_date, r_year = _single(right)
        return f"{l_date} – {r_date} {r_year}"

    d, yr = _single(date_str)
    return f"{d} {yr}"


def _render_legend_table(legend_data: list[dict[str, Any]]) -> str:
    # Table header — compact Bloomberg-density styling
    header = """<table style="width:100%;border-collapse:collapse">
  <thead><tr style="background:#F8FAFC;border-top:1px solid #F1F5F9">
    <th style="padding:3px 6px;text-align:center;font-size:6pt;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;width:32px">#</th>
    <th style="padding:3px 6px;text-align:left;font-size:6pt;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;width:90px">Period</th>
    <th style="padding:3px 6px;text-align:right;font-size:6pt;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;width:55px">Drop</th>
    <th style="padding:3px 6px;text-align:right;font-size:6pt;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;width:45px">Sector</th>
    <th style="padding:3px 6px;text-align:center;font-size:6pt;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;width:55px">Type</th>
    <th style="padding:3px 8px;text-align:left;font-size:6pt;color:#94A3B8;text-transform:uppercase;letter-spacing:1px">Catalyst</th>
  </tr></thead>
  <tbody>"""

    rows: list[str] = []
    for d in legend_data:
        opacity = _severity_opacity(d["drop_pct_raw"])
        color = d["category_color"]
        drop_color = _drop_color(d["drop_pct_raw"])
        is_cluster = d.get("is_cluster", False)
        date_display = _format_date_short(d["date"])

        # Marker shape: circle for single-day, rounded-square for cluster
        border_radius = "3px" if is_cluster else "50%"

        # Duration label
        days = d.get("cluster_days", 1)
        duration = f"{days}d" if days and days > 1 else ""

        # Category badge
        cat_label = d.get("category_label", "—")
        badge_bg = color if d.get("is_company_specific", True) else "#94A3B8"

        # Trigger text
        trigger = html.escape(d.get("trigger", "—"))

        # Sector comparison
        sector_pct = d.get("sector_pct", "—")

        rows.append(f"""    <tr style="border-bottom:1px solid #F1F5F9;background:rgba(244,63,94,{opacity:.3f})">
      <td style="padding:4px 6px;text-align:center;vertical-align:middle">
        <span style="display:inline-flex;width:20px;height:20px;border-radius:{border_radius};align-items:center;justify-content:center;font-weight:800;font-size:7pt;color:white;background:{color}">{d['number']}</span>
      </td>
      <td style="padding:4px 6px;vertical-align:middle;font-variant-numeric:tabular-nums">
        <span style="font-size:7.5pt;color:#1E293B;font-weight:600">{date_display}</span>
        {f'<span style="font-size:6pt;color:#94A3B8;margin-left:4px">{duration}</span>' if duration else ''}
      </td>
      <td style="padding:4px 6px;text-align:right;vertical-align:middle;white-space:nowrap;font-variant-numeric:tabular-nums">
        <span style="font-size:9pt;font-weight:800;color:{drop_color}">{d['drop_pct']}</span>
      </td>
      <td style="padding:4px 6px;text-align:right;vertical-align:middle;font-variant-numeric:tabular-nums">
        <span style="font-size:7pt;color:#94A3B8">{sector_pct}</span>
      </td>
      <td style="padding:4px 6px;text-align:center;vertical-align:middle">
        <span style="font-size:6pt;font-weight:700;padding:2px 6px;border-radius:8px;background:{badge_bg};color:white">{html.escape(cat_label)}</span>
      </td>
      <td style="padding:4px 8px;color:#475569;font-size:7.5pt;line-height:1.3;vertical-align:middle;border-left:3px solid {color}">{trigger}</td>
    </tr>""")

    footer = """  </tbody>
</table>"""

    return header + "\n".join(rows) + "\n" + footer


# ---------------------------------------------------------------------------
# Footer — legend key
# ---------------------------------------------------------------------------

def _render_footer() -> str:
    return """<div style="padding:6px 16px 10px;display:flex;justify-content:space-between;align-items:center;border-top:1px solid #F1F5F9">
  <span style="font-size:7pt;color:#94A3B8">\u25cf Single-day \u00b7 \u25a0 Multi-day cluster \u00b7 Background intensity = severity \u00b7 Left accent = event color</span>
  <span style="font-size:7pt;color:#CBD5E1">Angry Dolphin Underwriting</span>
</div>"""


__all__ = ["render_stock_drop_card", "render_stock_drop_card_standalone"]
