"""Narrative generation for D&O underwriting worksheet.

Produces analyst-quality interpretive text from typed AnalysisState data.
Each function accepts typed state data (or backward-compatible dicts),
cites specific dollar amounts, percentages, filing dates, and draws
D&O-specific underwriting conclusions.

Financial, market, and insider narratives live here.
Governance, litigation, scoring, and company narratives are in
md_narrative_sections.py (split for 500-line compliance).
Financial sub-narratives are in md_narrative_helpers.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import format_currency, format_percentage, safe_float
from do_uw.stages.render.md_narrative_helpers import (
    audit_narrative,
    distress_narrative,
    earnings_quality_narrative,
    financial_do_conclusion,
    financial_narrative_from_dict,
    insider_narrative_from_dict,
    leverage_narrative,
    market_narrative_from_dict,
)

# Re-export section narratives for backward compatibility
from do_uw.stages.render.md_narrative_sections import (
    company_narrative as company_narrative,
)
from do_uw.stages.render.md_narrative_sections import (
    governance_narrative as governance_narrative,
)
from do_uw.stages.render.md_narrative_sections import (
    litigation_narrative as litigation_narrative,
)
from do_uw.stages.render.md_narrative_sections import (
    scoring_narrative as scoring_narrative,
)


def _find_line_item(
    items: list[Any], label: str, period_idx: int = 0,
) -> float | None:
    """Find a financial line item by label and return a period's value."""
    search = label.lower().replace(" ", "_")
    for item in items:
        normalized = item.label.lower().replace(" ", "_")
        if normalized == search or search in normalized:
            vals = list(item.values.values())
            if len(vals) > period_idx and vals[period_idx] is not None:
                return safe_float(vals[period_idx].value)
    return None


def _period_label(items: list[Any], hint: str = "revenue") -> str | None:
    """Extract the first period label from line items."""
    h = hint.lower()
    for item in items:
        if h in item.label.lower() and item.values:
            return next(iter(item.values.keys()), None)
    return None


def _filing_ref(fin: Any) -> str:
    """Build a filing reference string from financials."""
    stmts = fin.statements
    src = ""
    if stmts.income_statement and stmts.income_statement.filing_source:
        src = stmts.income_statement.filing_source
    period = ""
    if stmts.income_statement and stmts.income_statement.line_items:
        p = _period_label(stmts.income_statement.line_items)
        if p:
            period = p
    if src and period:
        return f" (per {period} 10-K, {src})"
    if period:
        return f" (per {period} 10-K)"
    return ""


# ---------------------------------------------------------------------------
# Financial narrative
# ---------------------------------------------------------------------------

def financial_narrative(state_or_dict: AnalysisState | dict[str, Any]) -> str:
    """Generate analyst-quality financial narrative.

    Accepts AnalysisState (primary) or a flat dict for backward compat.
    """
    if isinstance(state_or_dict, dict):
        return financial_narrative_from_dict(state_or_dict)
    return _financial_narrative_from_state(state_or_dict)


def _financial_narrative_from_state(state: AnalysisState) -> str:
    """Generate financial narrative from typed state data."""
    if not state.extracted or not state.extracted.financials:
        return ""
    fin = state.extracted.financials
    stmts = fin.statements
    parts: list[str] = []
    ref = _filing_ref(fin)
    # Revenue and income trajectory
    if stmts.income_statement and stmts.income_statement.line_items:
        items = stmts.income_statement.line_items
        rev = _find_line_item(items, "total_revenue")
        ni = _find_line_item(items, "net_income")
        prior_rev = _find_line_item(items, "total_revenue", 1)
        prior_ni = _find_line_item(items, "net_income", 1)
        if rev is not None and ni is not None:
            parts.append(
                f"The company reported revenue of"
                f" {format_currency(rev, compact=True)} and net income"
                f" of {format_currency(ni, compact=True)}{ref}."
            )
            if prior_rev is not None and prior_rev != 0:
                chg = ((rev - prior_rev) / abs(prior_rev)) * 100
                d = "grew" if chg > 0 else "declined"
                parts.append(
                    f"Revenue {d} {abs(chg):.1f}% year-over-year"
                    f" (from {format_currency(prior_rev, compact=True)})."
                )
            if prior_ni is not None and prior_ni != 0:
                ni_chg = ((ni - prior_ni) / abs(prior_ni)) * 100
                if ni_chg < -30:
                    parts.append(
                        f"Net income declined {abs(ni_chg):.1f}% YoY,"
                        " a material deterioration that may attract"
                        " plaintiff scrutiny."
                    )
            if rev > 0:
                margin = (ni / rev) * 100
                if margin < 0:
                    parts.append(
                        f"The company is operating at a net loss"
                        f" (margin: {margin:.1f}%), increasing"
                        " financial distress risk."
                    )
                elif margin < 5:
                    parts.append(
                        f"Net margin of {margin:.1f}% is thin, leaving"
                        " limited buffer against earnings volatility."
                    )
    parts.extend(distress_narrative(fin))
    parts.extend(leverage_narrative(fin))
    parts.extend(earnings_quality_narrative(fin))
    parts.extend(audit_narrative(fin))
    if parts:
        parts.append(financial_do_conclusion(fin))
    return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Market narrative
# ---------------------------------------------------------------------------

def market_narrative(state_or_dict: AnalysisState | dict[str, Any]) -> str:
    """Generate stock performance D&O narrative."""
    if isinstance(state_or_dict, dict):
        return market_narrative_from_dict(state_or_dict)
    return _market_narrative_from_state(state_or_dict)


def _market_narrative_from_state(state: AnalysisState) -> str:
    """Generate market narrative from typed state data."""
    if not state.extracted or not state.extracted.market:
        return ""
    mkt = state.extracted.market
    stock = mkt.stock
    si = mkt.short_interest
    parts: list[str] = []
    # Stock performance vs 52-week high
    if stock.decline_from_high_pct is not None:
        pct_val = abs(safe_float(stock.decline_from_high_pct.value))
        high = format_currency(
            stock.high_52w.value if stock.high_52w else None, compact=True,
        )
        cur = format_currency(
            stock.current_price.value if stock.current_price else None,
            compact=True,
        )
        pct_str = format_percentage(pct_val)
        if pct_val < 15:
            parts.append(
                f"The stock trades {pct_str} below its 52-week high"
                f" ({high}), within normal trading variance."
            )
        elif pct_val < 30:
            parts.append(
                f"The stock trades {pct_str} below its 52-week high"
                f" ({high} to current {cur}), entering the range where"
                " SCA filings become economically viable."
            )
        elif pct_val < 50:
            parts.append(
                f"The stock has declined {pct_str} from its 52-week"
                f" high ({high} to {cur}), substantially increasing"
                " SCA filing probability."
            )
        else:
            parts.append(
                f"The stock has suffered a severe {pct_str} decline"
                f" from its 52-week high ({high} to {cur}). Declines"
                " of this magnitude almost invariably attract"
                " securities litigation."
            )
    # Sector-relative performance
    if stock.sector_relative_performance:
        rel = safe_float(stock.sector_relative_performance.value)
        if rel < -10:
            parts.append(
                f"The stock underperformed its sector by"
                f" {format_percentage(abs(rel))}, indicating"
                " company-specific weakness."
            )
    # Significant drop events
    drops = mkt.stock_drops
    if drops.worst_single_day and drops.worst_single_day.drop_pct:
        dp = safe_float(drops.worst_single_day.drop_pct.value)
        dt = drops.worst_single_day.date
        trigger = ""
        if drops.worst_single_day.trigger_event:
            trigger = f" triggered by {drops.worst_single_day.trigger_event.value}"
        date_str = f" on {dt.value}" if dt else ""
        parts.append(
            f"Worst single-day decline:"
            f" {format_percentage(abs(dp))}{date_str}{trigger}."
        )
    # Short interest
    if si.short_pct_float is not None:
        si_val = si.short_pct_float.value
        si_str = format_percentage(si_val)
        trend = ""
        if si.trend_6m and si.trend_6m.value:
            trend = f" (6-month trend: {si.trend_6m.value})"
        if si_val > 10:
            parts.append(
                f"Short interest of {si_str} of float is"
                f" elevated{trend}, indicating institutional"
                " bearish conviction."
            )
        elif si_val < 3:
            parts.append(
                f"Short interest of {si_str} of float is"
                f" low{trend}."
            )
        else:
            parts.append(f"Short interest: {si_str} of float{trend}.")
    # Analyst context
    analyst = mkt.analyst
    if analyst.consensus and analyst.consensus.value:
        cons = analyst.consensus.value
        changes = ""
        if analyst.recent_downgrades > 0 or analyst.recent_upgrades > 0:
            changes = (
                f" (recent: {analyst.recent_upgrades} upgrades,"
                f" {analyst.recent_downgrades} downgrades)"
            )
        parts.append(f"Analyst consensus: {cons}{changes}.")
    # D&O conclusion on stock-drop risk
    if parts and stock.decline_from_high_pct and stock.decline_from_high_pct.value:
        d = abs(stock.decline_from_high_pct.value)
        if d >= 50:
            parts.append("Stock-drop litigation risk is severe.")
        elif d >= 30:
            parts.append("Stock-drop litigation risk is elevated.")
    return " ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Insider narrative
# ---------------------------------------------------------------------------

def insider_narrative(state_or_dict: AnalysisState | dict[str, Any]) -> str:
    """Generate insider trading pattern narrative."""
    if isinstance(state_or_dict, dict):
        return insider_narrative_from_dict(state_or_dict)
    return _insider_narrative_from_state(state_or_dict)


def _insider_narrative_from_state(state: AnalysisState) -> str:
    """Generate insider narrative from typed state data."""
    if not state.extracted or not state.extracted.market:
        return ""
    mkt = state.extracted.market
    ia = mkt.insider_analysis
    parts: list[str] = []
    nbs = ia.net_buying_selling
    if nbs and nbs.value:
        direction = nbs.value
        if direction == "NET_SELLING":
            parts.append("Insiders are net sellers over the measured period.")
        elif direction == "NET_BUYING":
            parts.append(
                "Insiders are net buyers -- a positive signal indicating"
                " management confidence. Net insider buying is among the"
                " strongest contrarian indicators for D&O underwriting."
            )
        else:
            parts.append("Insider trading activity is neutral.")
    pct = ia.pct_10b5_1
    if pct is not None:
        pv = safe_float(pct.value)
        if pv > 80:
            parts.append(
                f"{pv:.0f}% of insider sales are governed by pre-arranged"
                " Rule 10b5-1 trading plans, substantially reducing"
                " insider-trading SCA risk."
            )
        elif pv < 50:
            parts.append(
                f"Only {pv:.0f}% of insider sales are governed by"
                " Rule 10b5-1 plans. Majority discretionary selling"
                " increases scrutiny of insider timing."
            )
        else:
            parts.append(
                f"{pv:.0f}% of insider sales are under 10b5-1 plans."
            )
    clusters = ia.cluster_events
    if clusters:
        n = len(clusters)
        recent = clusters[0]
        names = ", ".join(recent.insiders[:3])
        if len(recent.insiders) > 3:
            names += f" +{len(recent.insiders) - 3} more"
        val = format_currency(recent.total_value, compact=True)
        parts.append(
            f"{n} insider cluster event(s) detected. Most recent:"
            f" {recent.insider_count} insiders ({names}) sold {val}"
            f" total between {recent.start_date} and {recent.end_date}."
        )
        if n >= 3:
            parts.append(
                "Multiple cluster events warrant close review for"
                " proximity to material corporate announcements."
            )
    if state.extracted.governance:
        gov = state.extracted.governance
        departures = gov.leadership.departures_18mo
        unplanned = [d for d in departures if d.departure_type == "UNPLANNED"]
        if unplanned:
            dep_names = [d.name.value for d in unplanned if d.name][:3]
            parts.append(
                f"{len(unplanned)} unplanned executive departure(s)"
                " in the last 18 months"
                + (f" ({', '.join(dep_names)})" if dep_names else "")
                + ". Unplanned departures combined with insider selling"
                " heighten D&O exposure."
            )
    return " ".join(p for p in parts if p)


__all__ = [
    "company_narrative",
    "financial_narrative",
    "governance_narrative",
    "insider_narrative",
    "litigation_narrative",
    "market_narrative",
    "scoring_narrative",
]
