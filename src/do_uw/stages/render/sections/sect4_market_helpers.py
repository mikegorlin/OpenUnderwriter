"""Section 4 helper functions: stock stats table and chart disk embedding.

Extracted from sect4_market.py to keep it under the 500-line limit.

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import add_styled_table
from do_uw.stages.render.formatters import format_percentage, na_if_none
from do_uw.stages.render.peer_context import get_peer_context_line


def render_stock_stats(
    doc: Any,
    stock: Any,
    context: dict[str, Any],
    ds: DesignSystem,
) -> None:
    """Render key stock statistics table.

    Displays current price, 52-week range, returns, drawdown,
    volatility with peer context, and beta.
    """
    if not stock:
        return
    stats: list[list[str]] = []
    if stock.current_price:
        stats.append(["Current Price", f"${stock.current_price.value:.2f}"])
    if stock.high_52w:
        stats.append(["52-Week High", f"${stock.high_52w.value:.2f}"])
    if stock.low_52w:
        stats.append(["52-Week Low", f"${stock.low_52w.value:.2f}"])
    if stock.returns_1y:
        stats.append(["1-Year Return", format_percentage(stock.returns_1y.value)])
    if stock.max_drawdown_1y:
        stats.append([
            "Max Drawdown (1Y)",
            format_percentage(stock.max_drawdown_1y.value),
        ])
    if stock.volatility_90d:
        vol_str = format_percentage(stock.volatility_90d.value)
        # TODO(phase-60): move to context_builders
        state = context["_state"]
        vol_ctx = get_peer_context_line("volatility_90d", state.benchmark)
        if vol_ctx:
            vol_str = f"{vol_str} ({vol_ctx})"
        stats.append(["90-Day Volatility", vol_str])
    if stock.beta:
        stats.append(["Beta (vs S&P 500)", f"{stock.beta.value:.2f}"])
    if stats:
        add_styled_table(doc, ["Metric", "Value"], stats, ds)


def embed_chart_from_disk(
    doc: Any, path: Path, ds: DesignSystem,
) -> bool:
    """Embed a chart PNG from disk into the document.

    Args:
        doc: The python-docx Document.
        path: Path to a PNG file.
        ds: Design system for chart width.

    Returns:
        True if the chart was embedded, False if file not found.
    """
    if path.exists():
        doc.add_picture(str(path), width=ds.chart_width)
        return True
    return False


def sv_str(sv: Any) -> str:
    """Extract string from SourcedValue or return N/A."""
    if sv is None:
        return "N/A"
    return na_if_none(sv.value)


def sv_pct(sv: Any) -> str:
    """Format SourcedValue float as percentage."""
    if sv is None:
        return "N/A"
    return format_percentage(sv.value)


def sv_float(sv: Any) -> str:
    """Format SourcedValue float with 2 decimal places."""
    if sv is None:
        return "N/A"
    return f"{sv.value:.2f}"


__all__ = ["embed_chart_from_disk", "render_stock_stats", "sv_float", "sv_pct", "sv_str"]
