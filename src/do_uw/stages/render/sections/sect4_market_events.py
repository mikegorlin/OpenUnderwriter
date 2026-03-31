"""Section 4 sub-module: Stock Drop Events, Insider Trading, 8-K Events.

Renders detailed stock drop event tables with triggering attribution
and sector-relative impact, insider trading analysis with 10b5-1 vs
discretionary breakdown and cluster detection, executive departures
from 8-K events, and capital markets activity.

Called by sect4_market.py via render_market_events().

Phase 60-01: Migrated from state access to shared context dict.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.market import MarketSignals
from do_uw.models.market_events import (
    CapitalMarketsOffering,
    InsiderClusterEvent,
    InsiderTradingAnalysis,
    InsiderTransaction,
    StockDropEvent,
)
from do_uw.stages.render.design_system import DesignSystem
from do_uw.stages.render.docx_helpers import (
    add_risk_indicator,
    add_styled_table,
    set_cell_shading,
)
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
)
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
)


def render_market_events(
    doc: Any,
    context: dict[str, Any],
    ds: DesignSystem,
    *,
    market_clean: bool = False,
) -> None:
    """Render stock drop events, insider trading, 8-K events.

    Called by sect4_market.render_section_4() after the main
    market content (charts, short interest, earnings).

    If market_clean=True, insider trading renders concisely
    (no transaction detail table).
    """
    market = _get_market(context)
    _render_stock_drops(doc, market, ds)
    _render_insider_trading(doc, market, ds, market_clean=market_clean)
    _render_executive_departures(doc, context, ds)
    _render_capital_markets(doc, market, ds)


def _render_stock_drops(
    doc: Any, market: MarketSignals | None, ds: DesignSystem
) -> None:
    """Render stock drop events table with attribution and sector context."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Stock Drop Analysis")

    drops = market.stock_drops if market else None
    all_drops: list[StockDropEvent] = []
    if drops:
        all_drops = [*drops.single_day_drops, *drops.multi_day_drops]
        # Sort by magnitude (most severe first)
        all_drops.sort(
            key=lambda d: abs(d.drop_pct.value) if d.drop_pct else 0,
            reverse=True,
        )

    if not all_drops:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run(
            "Stock Performance: No significant single-day (>5%) or "
            "multi-day (>10%) declines in the analysis period."
        )
        return

    headers = [
        "Date",
        "Magnitude",
        "Type",
        "Trigger / Attribution",
        "Sector Return",
        "Company-Specific",
    ]
    rows: list[list[str]] = []
    for drop in all_drops[:15]:
        date_str = str(drop.date.value) if drop.date else "N/A"
        pct_str = (
            f"{drop.drop_pct.value:+.1f}%"
            if drop.drop_pct
            else "N/A"
        )
        drop_type = drop.drop_type or "N/A"
        if drop.period_days > 1:
            drop_type = f"{drop_type} ({drop.period_days}d)"
        trigger = (
            str(drop.trigger_event.value)
            if drop.trigger_event
            else "Unknown"
        )
        sector_str = (
            f"{drop.sector_return_pct.value:+.1f}%"
            if drop.sector_return_pct
            else "N/A"
        )
        specific = "Yes" if drop.is_company_specific else "No"
        rows.append([
            date_str, pct_str, drop_type, trigger, sector_str, specific,
        ])

    table: Any = add_styled_table(doc, headers, rows, ds)

    # Highlight company-specific drops (amber shading)
    for row_idx, drop in enumerate(all_drops[:15]):
        if drop.is_company_specific:
            specific_cell: Any = table.rows[row_idx + 1].cells[5]
            set_cell_shading(specific_cell, "FFF3CD")  # Amber

    # D&O context: class period potential
    severe_drops = [
        d for d in all_drops
        if d.drop_pct and abs(d.drop_pct.value) >= 10
        and d.is_company_specific
    ]
    company_specific_count = sum(1 for d in all_drops if d.is_company_specific)

    if severe_drops:
        fp: Any = doc.add_paragraph(style="DOBody")
        fp.add_run(
            f"Class Period Potential: {len(severe_drops)} company-specific "
            f"drop(s) exceeding 10% identified. Severe stock drops "
            "that are company-specific (not explained by sector "
            "movement) are the primary anchors for SCA class periods. "
            "Plaintiffs will allege the drop occurred when the 'truth "
            "emerged' following prior misstatements."
        )
        add_risk_indicator(fp, "HIGH", ds)
    elif company_specific_count > 0:
        fp = doc.add_paragraph(style="DOBody")
        fp.add_run(
            f"Company-Specific Drops: {company_specific_count} event(s) "
            "exceeded sector movement. While individually moderate, "
            "a pattern of company-specific drops may indicate emerging "
            "D&O litigation risk."
        )
        add_risk_indicator(fp, "ELEVATED", ds)


def _render_insider_trading(
    doc: Any,
    market: MarketSignals | None,
    ds: DesignSystem,
    *,
    market_clean: bool = False,
) -> None:
    """Render insider trading analysis with transaction detail.

    If market_clean=True and no cluster selling, renders a concise
    summary instead of the full transaction table.
    """
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Insider Trading Analysis")

    insider = market.insider_analysis if market else None
    basic = market.insider_trading if market else None

    if insider is None and basic is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Insider trading data not available.")
        return

    # Concise rendering for clean markets with no cluster events
    if market_clean and not (insider and insider.cluster_events):
        txn_count = len(insider.transactions) if insider else 0
        body = doc.add_paragraph(style="DOBody")
        body.add_run(
            f"Insider Trading: No unusual activity. {txn_count} "
            f"transaction(s) in trailing 12 months, no cluster "
            f"selling identified."
        )
        return

    # Summary metrics table
    _render_insider_summary(doc, insider, basic, ds)

    # Transaction detail table
    if insider and insider.transactions:
        _render_transaction_table(doc, insider.transactions, ds)

    # Cluster events
    if insider and insider.cluster_events:
        _render_cluster_events(doc, insider.cluster_events, ds)


def _render_insider_summary(
    doc: Any,
    insider: InsiderTradingAnalysis | None,
    basic: Any,
    ds: DesignSystem,
) -> None:
    """Render insider trading summary metrics."""
    rows: list[list[str]] = []

    # Net direction
    net_dir = "N/A"
    if insider and insider.net_buying_selling:
        net_dir = str(insider.net_buying_selling.value)
    elif basic and basic.net_buying_selling:
        net_dir = str(basic.net_buying_selling.value)
    rows.append(["Net Direction (12mo)", net_dir])

    # 10b5-1 percentage
    if insider and insider.pct_10b5_1:
        rows.append([
            "10b5-1 Plan %",
            format_percentage(insider.pct_10b5_1.value),
        ])

    # Transaction counts
    if insider and insider.transactions:
        buys = sum(
            1 for t in insider.transactions if t.transaction_type == "BUY"
        )
        sells = sum(
            1 for t in insider.transactions if t.transaction_type == "SELL"
        )
        rows.append(["Buy Transactions", str(buys)])
        rows.append(["Sell Transactions", str(sells)])

    # Total values
    if basic:
        if basic.total_sold_value:
            rows.append([
                "Total Sold (12mo)",
                format_currency(basic.total_sold_value.value, compact=True),
            ])
        if basic.total_bought_value:
            rows.append([
                "Total Bought (12mo)",
                format_currency(basic.total_bought_value.value, compact=True),
            ])

    # Cluster events count
    clusters = insider.cluster_events if insider else []
    rows.append(["Cluster Events", str(len(clusters))])

    add_styled_table(doc, ["Metric", "Value"], rows, ds)


def _render_transaction_table(
    doc: Any,
    transactions: list[InsiderTransaction],
    ds: DesignSystem,
) -> None:
    """Render individual insider transaction detail table."""
    sub_heading: Any = doc.add_paragraph(style="DOHeading3")
    sub_heading.add_run("Transaction Detail")

    headers = [
        "Date",
        "Insider",
        "Title",
        "Type",
        "Shares",
        "Value",
        "10b5-1",
    ]
    rows: list[list[str]] = []
    for txn in transactions[:20]:
        date_str = (
            str(txn.transaction_date.value)
            if txn.transaction_date
            else "N/A"
        )
        name_str = (
            str(txn.insider_name.value) if txn.insider_name else "N/A"
        )
        title_str = str(txn.title.value) if txn.title else "N/A"
        txn_type = txn.transaction_type or "N/A"
        shares_str = (
            f"{txn.shares.value:,.0f}" if txn.shares else "N/A"
        )
        value_str = (
            format_currency(txn.total_value.value, compact=True)
            if txn.total_value
            else "N/A"
        )
        plan_str = _format_10b5_1(txn)
        rows.append([
            date_str, name_str, title_str, txn_type,
            shares_str, value_str, plan_str,
        ])

    table: Any = add_styled_table(doc, headers, rows, ds)

    # Highlight discretionary sells (amber)
    for row_idx, txn in enumerate(transactions[:20]):
        if txn.is_discretionary and txn.transaction_type == "SELL":
            plan_cell: Any = table.rows[row_idx + 1].cells[6]
            set_cell_shading(plan_cell, "FFF3CD")  # Amber


def _format_10b5_1(txn: InsiderTransaction) -> str:
    """Format 10b5-1 plan status for display."""
    if txn.is_10b5_1 is not None:
        if txn.is_10b5_1.value:
            return "Yes (Pre-arranged)"
        return "No (Discretionary)"
    if txn.is_discretionary:
        return "No (Discretionary)"
    return "N/A"


def _render_cluster_events(
    doc: Any,
    clusters: list[InsiderClusterEvent],
    ds: DesignSystem,
) -> None:
    """Render insider cluster selling events with D&O context."""
    sub_heading: Any = doc.add_paragraph(style="DOHeading3")
    sub_heading.add_run("Cluster Selling Events")

    headers = ["Window", "Insiders", "Names", "Total Value"]
    rows: list[list[str]] = []
    for cluster in clusters:
        window = f"{cluster.start_date} to {cluster.end_date}"
        names = ", ".join(cluster.insiders) if cluster.insiders else "N/A"
        value_str = format_currency(cluster.total_value, compact=True)
        rows.append([
            window,
            str(cluster.insider_count),
            names,
            value_str,
        ])

    add_styled_table(doc, headers, rows, ds)

    # D&O context
    fp: Any = doc.add_paragraph(style="DOBody")
    fp.add_run(
        f"Insider Cluster Selling ({len(clusters)} event(s)): "
        "Coordinated insider selling is a key D&O risk signal. "
        "Courts view cluster sales -- where 3+ insiders sell within "
        "a narrow window -- as circumstantial evidence of scienter "
        "(intent to defraud) in securities fraud claims."
    )
    add_risk_indicator(fp, "HIGH", ds)


def _get_signal_results(ctx: dict[str, Any]) -> dict[str, Any] | None:
    """Extract signal_results dict from context."""
    state = ctx.get("_state")
    if state is None or state.analysis is None:
        return None
    return state.analysis.signal_results


def _render_executive_departures(
    doc: Any, context: dict[str, Any], ds: DesignSystem
) -> None:
    """Render executive departures from leadership stability data."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Executive Departures")

    # TODO(phase-60): move to context_builders
    state = context["_state"]
    gov = (
        state.extracted.governance
        if state.extracted
        else None
    )
    departures = (
        gov.leadership.departures_18mo
        if gov and gov.leadership.departures_18mo
        else []
    )

    if not departures:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run(
            "No executive departures identified in the trailing 18 months."
        )
        return

    # Get departure signal do_context for D&O column
    signal_results = _get_signal_results(context)
    dep_sig = safe_get_result(signal_results, "EXEC.DEPARTURE.cfo_departure_timing")
    dep_do_text = dep_sig.do_context if dep_sig and dep_sig.do_context else ""

    headers = ["Name", "Title", "Departure Date", "Type", "D&O Context"]
    rows: list[list[str]] = []
    for dep in departures:
        name = str(dep.name.value) if dep.name else "N/A"
        title = str(dep.title.value) if dep.title else "N/A"
        dep_date = dep.departure_date or "N/A"
        dep_type = dep.departure_type or "N/A"
        # Per-row D&O context: use signal do_context for UNPLANNED, else brief text
        if dep_type == "UNPLANNED" and dep_do_text:
            row_ctx = dep_do_text[:80]  # Truncate for table cell
        elif dep_type == "PLANNED":
            dep_planned_sig = safe_get_result(signal_results, "EXEC.DEPARTURE.cao_departure")
            row_ctx = (
                dep_planned_sig.do_context[:80]
                if dep_planned_sig and dep_planned_sig.do_context
                else "Normal succession"
            )
        else:
            row_ctx = "Monitor for subsequent developments"
        rows.append([name, title, dep_date, dep_type, row_ctx])

    add_styled_table(doc, headers, rows, ds)

    # D&O context for unexpected departures from signal do_context
    unplanned = [d for d in departures if d.departure_type == "UNPLANNED"]
    if unplanned:
        fp: Any = doc.add_paragraph(style="DOBody")
        do_text = dep_do_text if dep_do_text else (
            "Unplanned departures frequently trigger D&O claims."
        )
        fp.add_run(f"Unexpected Executive Departures ({len(unplanned)}): {do_text}")
        add_risk_indicator(fp, "HIGH", ds)


def _render_capital_markets(
    doc: Any, market: MarketSignals | None, ds: DesignSystem
) -> None:
    """Render capital markets activity and Section 11 exposure."""
    para: Any = doc.add_paragraph(style="DOHeading2")
    para.add_run("Capital Markets Activity")

    cm = market.capital_markets if market else None
    if cm is None:
        body: Any = doc.add_paragraph(style="DOBody")
        body.add_run("Capital markets activity data not available.")
        return

    offerings = cm.offerings_3yr
    shelfs = cm.shelf_registrations

    if not offerings and not shelfs and cm.active_section_11_windows == 0:
        body = doc.add_paragraph(style="DOBody")
        body.add_run(
            "No significant capital markets activity identified "
            "in the trailing 3-year period."
        )
        return

    # Offerings table
    if offerings:
        _render_offerings_table(doc, offerings, ds)

    # Section 11 windows
    if cm.active_section_11_windows > 0:
        fp: Any = doc.add_paragraph(style="DOBody")
        fp.add_run(
            f"Active Section 11 Windows: {cm.active_section_11_windows}. "
            "Offerings with open Section 11 statute of limitations create "
            "liability exposure for directors who signed the registration "
            "statement. No scienter required for Section 11 claims."
        )
        add_risk_indicator(fp, "ELEVATED", ds)

    # ATM programs
    if cm.has_atm_program and cm.has_atm_program.value:
        fp = doc.add_paragraph(style="DOBody")
        fp.add_run(
            "Active at-the-market (ATM) program detected. Ongoing "
            "offerings create continuous Section 11/12 liability windows."
        )


def _render_offerings_table(
    doc: Any,
    offerings: list[CapitalMarketsOffering],
    ds: DesignSystem,
) -> None:
    """Render offerings detail table."""
    headers = ["Date", "Type", "Filing", "Amount", "Sec 11 Window"]
    rows: list[list[str]] = []
    for off in offerings[:10]:
        date_str = str(off.date.value) if off.date else "N/A"
        amount_str = (
            format_currency(off.amount.value, compact=True)
            if off.amount
            else "N/A"
        )
        sec11 = off.section_11_window_end or "N/A"
        rows.append([
            date_str,
            off.offering_type or "N/A",
            off.filing_type or "N/A",
            amount_str,
            sec11,
        ])

    add_styled_table(doc, headers, rows, ds)


def _get_market(context: dict[str, Any]) -> MarketSignals | None:
    """Safely extract market data from context."""
    # TODO(phase-60): move to context_builders
    state = context["_state"]
    if state.extracted is None:
        return None
    return state.extracted.market


__all__ = ["render_market_events"]
