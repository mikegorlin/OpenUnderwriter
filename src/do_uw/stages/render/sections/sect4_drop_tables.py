"""Section 4 sub-module: Detailed drop event tables with severity tiers.

Renders detailed stock drop event tables below the stock charts in
Section 4: Market & Trading. Includes severity coloring (yellow for
5-10%, red for 10%+), recovery time, trigger attribution, market-wide
event tagging, and source links.

Called by sect4_market.py after chart embedding.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.market_events import StockDropEvent
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.formatters import safe_float
from do_uw.stages.render.docx_helpers import (
    add_styled_table,
    set_cell_shading,
)

logger = logging.getLogger(__name__)

# Severity thresholds for row highlighting
_NOTABLE_THRESHOLD = -5.0   # 5-10%: yellow (notable)
_CRITICAL_THRESHOLD = -10.0  # 10%+: red (critical)


def render_drop_detail_table(
    doc: Any,
    drops: list[StockDropEvent],
    period: str,
    ds: DesignSystem,
) -> None:
    """Render a detailed drop event table with summary line.

    Args:
        doc: The python-docx Document.
        drops: List of StockDropEvent objects to render.
        period: Period label ("1Y" or "5Y") for the summary line.
        ds: Design system for colors and styling.
    """
    if not drops:
        return

    # Sort by decay-weighted severity (Phase 90), falling back to date
    sorted_drops = sorted(
        drops,
        key=lambda d: (
            d.decay_weighted_severity
            if d.decay_weighted_severity is not None
            else abs(d.drop_pct.value) if d.drop_pct else 0
        ),
        reverse=True,
    )

    # Summary line before the table
    _render_summary_line(doc, sorted_drops, period)

    # Check if any drops have decomposition or disclosure data (Phase 90)
    has_decomp = any(d.market_pct is not None for d in sorted_drops)
    has_disclosure = any(bool(d.corrective_disclosure_type) for d in sorted_drops)

    # Table headers
    headers = [
        "Date",
        "Drop %",
        "Recency",
        "Recovery",
        "Trigger Event",
        "Type",
    ]
    if has_decomp:
        headers.extend(["Market", "Sector", "Company"])
    if has_disclosure:
        headers.append("Disclosure")
    headers.append("Source")

    # Build rows
    rows: list[list[str]] = []
    for drop in sorted_drops:
        date_str = _format_date(drop)
        pct_str = _format_drop_pct(drop)
        recency_str = f"{drop.decay_weight:.0%}" if drop.decay_weight is not None else "N/A"
        recovery_str = _format_recovery(drop.recovery_days)
        trigger_str = _format_trigger(drop)
        type_str = _format_type(drop)
        row = [date_str, pct_str, recency_str, recovery_str, trigger_str, type_str]
        if has_decomp:
            market_str = f"{drop.market_pct:+.1f}%" if drop.market_pct is not None else "N/A"
            sector_str = f"{drop.sector_pct:+.1f}%" if drop.sector_pct is not None else "N/A"
            company_str = f"{drop.company_pct:+.1f}%" if drop.company_pct is not None else "N/A"
            if drop.is_market_driven:
                company_str += " (Mkt)"
            row.extend([market_str, sector_str, company_str])
        if has_disclosure:
            disclosure_str = _format_disclosure(drop)
            row.append(disclosure_str)
        source_str = _format_source(drop)
        row.append(source_str)
        rows.append(row)

    table: Any = add_styled_table(doc, headers, rows, ds)

    # Apply severity coloring to rows
    for row_idx, drop in enumerate(sorted_drops):
        color = _severity_color(drop)
        if color:
            for cell_idx in range(len(headers)):
                cell: Any = table.rows[row_idx + 1].cells[cell_idx]
                set_cell_shading(cell, color)


def _render_summary_line(
    doc: Any,
    drops: list[StockDropEvent],
    period: str,
) -> None:
    """Render a brief summary line above the drop table.

    Example: "4 significant stock decline events detected in the 1Y period:
    1 critical (>10%), 3 notable (5-10%). 2 were company-specific, 2 were
    market-wide."
    """
    total = len(drops)
    critical_count = sum(1 for d in drops if _get_effective_pct(d) <= _CRITICAL_THRESHOLD)
    notable_count = total - critical_count

    company_specific = sum(1 for d in drops if d.is_company_specific)
    market_wide = sum(1 for d in drops if d.is_market_wide)

    parts: list[str] = [
        f"{total} significant stock decline event{'s' if total != 1 else ''} "
        f"detected in the {period} period",
    ]

    severity_parts: list[str] = []
    if critical_count > 0:
        severity_parts.append(f"{critical_count} critical (>10%)")
    if notable_count > 0:
        severity_parts.append(f"{notable_count} notable (5-10%)")
    if severity_parts:
        parts.append(": " + ", ".join(severity_parts))

    type_parts: list[str] = []
    if company_specific > 0:
        type_parts.append(
            f"{company_specific} {'were' if company_specific > 1 else 'was'} company-specific"
        )
    if market_wide > 0:
        type_parts.append(
            f"{market_wide} {'were' if market_wide > 1 else 'was'} market-wide"
        )
    if type_parts:
        parts.append(". " + ", ".join(type_parts))

    parts.append(".")

    para: Any = doc.add_paragraph(style="DOBody")
    para.add_run("".join(parts))


def _format_date(drop: StockDropEvent) -> str:
    """Format date with multi-day duration indicator."""
    date_str = str(drop.date.value) if drop.date else "N/A"
    if drop.period_days > 1:
        date_str = f"{date_str} ({drop.period_days}d)"
    return date_str


def _format_drop_pct(drop: StockDropEvent) -> str:
    """Format drop percentage, preferring cumulative for grouped events."""
    if drop.cumulative_pct is not None:
        return f"{drop.cumulative_pct:+.1f}%"
    if drop.drop_pct:
        return f"{drop.drop_pct.value:+.1f}%"
    return "N/A"


def _format_recovery(days: int | None) -> str:
    """Format recovery time as trading days or 'Not recovered'."""
    if days is None:
        return "Not recovered"
    if days == 0:
        return "Same day"
    return f"{days} days"


def _format_trigger(drop: StockDropEvent) -> str:
    """Format trigger event text."""
    if drop.trigger_event and drop.trigger_event.value:
        trigger = str(drop.trigger_event.value)
        # Clean up internal trigger codes for display
        trigger = trigger.replace("_", " ").replace("8-K filing", "8-K Filing")
        return trigger.capitalize() if trigger.islower() else trigger
    return "Unconfirmed -- Requires Investigation"


def _format_type(drop: StockDropEvent) -> str:
    """Format drop type as Market-Wide or Company-Specific."""
    if drop.is_market_wide:
        return "Market-Wide Event"
    if drop.is_company_specific:
        return "Company-Specific"
    return "Unclassified"


def _format_disclosure(drop: StockDropEvent) -> str:
    """Format corrective disclosure badge for Word table."""
    if not drop.corrective_disclosure_type:
        return "--"
    label = drop.corrective_disclosure_type
    lag = f"+{drop.corrective_disclosure_lag_days}d" if drop.corrective_disclosure_lag_days else ""
    return f"{label} {lag}".strip()


def _format_source(drop: StockDropEvent) -> str:
    """Format source link."""
    if drop.trigger_source_url:
        # Truncate long URLs for table display
        url = drop.trigger_source_url
        if len(url) > 50:
            return url[:47] + "..."
        return url
    return "--"


def _get_effective_pct(drop: StockDropEvent) -> float:
    """Get the effective drop percentage for severity comparison."""
    if drop.cumulative_pct is not None:
        return drop.cumulative_pct
    if drop.drop_pct:
        return safe_float(drop.drop_pct.value)
    return 0.0


def _severity_color(drop: StockDropEvent) -> str:
    """Return highlight color hex for the row based on drop severity.

    Returns:
        Hex color string without '#' prefix, or empty string for no highlight.
        - "FCE8E6" (light red) for 10%+ drops
        - "FFF3CD" (light amber) for 5-10% drops
        - "" for drops under 5%
    """
    pct = _get_effective_pct(drop)
    if pct <= _CRITICAL_THRESHOLD:
        return "FCE8E6"  # ds.highlight_bad -- light red
    if pct <= _NOTABLE_THRESHOLD:
        return "FFF3CD"  # ds.highlight_warn -- light amber
    return ""


def get_drops_for_period(
    market: Any, period: str,
) -> list[StockDropEvent]:
    """Get filtered drop events appropriate for a given chart period.

    For 1Y: all drops with drop_pct <= -5% (notable and critical).
    For 5Y: only drops with drop_pct <= -10% or cumulative_pct <= -15%.

    Args:
        market: MarketSignals instance with stock_drops.
        period: "1Y" or "5Y".

    Returns:
        Filtered list of StockDropEvent objects.
    """
    drops = market.stock_drops
    all_drops: list[StockDropEvent] = [*drops.single_day_drops, *drops.multi_day_drops]

    if period == "1Y":
        return [
            d for d in all_drops
            if (d.drop_pct and d.drop_pct.value <= -5.0)
            or (d.cumulative_pct is not None and d.cumulative_pct <= -5.0)
        ]

    # 5Y: higher threshold -- only significant events
    return [
        d for d in all_drops
        if (d.drop_pct and d.drop_pct.value <= -10.0)
        or (d.cumulative_pct is not None and d.cumulative_pct <= -15.0)
    ]


__all__ = ["get_drops_for_period", "render_drop_detail_table"]
