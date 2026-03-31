"""Chart generators for the D&O underwriting worksheet.

Each module creates a specific chart type as either BytesIO PNG
(for python-docx embedding) or inline SVG string (for HTML/PDF
embedding).  Pass ``format="svg"`` to any chart creator to get
a resolution-independent SVG string instead of a PNG buffer.
"""

from do_uw.stages.render.charts.factor_bars import render_factor_bar, render_factor_bar_set
from do_uw.stages.render.charts.gauge import render_score_gauge
from do_uw.stages.render.charts.kpi_cards import build_kpi_card, build_kpi_strip
from do_uw.stages.render.charts.sparklines import render_sparkline
from do_uw.stages.render.charts.trend_arrows import render_trend_arrow, trend_direction

__all__ = [
    "build_kpi_card",
    "build_kpi_strip",
    "render_factor_bar",
    "render_factor_bar_set",
    "render_score_gauge",
    "render_sparkline",
    "render_trend_arrow",
    "trend_direction",
]
