"""Market data and table context builders.

Format-agnostic extractors that build template-ready dicts from AnalysisState.
Both HTML and Word renderers consume these same context builders.

Display data (prices, volumes, holders, transactions) from direct state reads.
Evaluative content (volatility, short interest, insider verdict, guidance,
returns) sourced from signal results via market_evaluative.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.sparklines import render_sparkline
from do_uw.stages.render.context_builders._market_acquired_data import (
    build_analyst_targets as _build_analyst_targets,
    build_earnings_history as _build_earnings_history,
    build_earnings_trust as _build_earnings_trust,
    build_eight_k_from_llm as _build_eight_k_from_llm,
    build_eps_revision_trends as _build_eps_revision_trends,
    build_forward_estimates as _build_forward_estimates,
    build_news_articles as _build_news_articles,
    build_recommendation_breakdown as _build_recommendation_breakdown,
    build_upgrades_downgrades as _build_upgrades_downgrades,
)
from do_uw.stages.render.context_builders._market_correlation import (
    build_correlation_metrics as _build_correlation_metrics,
)
from do_uw.stages.render.context_builders._market_volume import (
    build_volume_anomalies as _build_volume_anomalies,
)
from do_uw.stages.render.context_builders._market_display import (
    _format_disclosure_badge,
    build_drop_events,
    build_earnings_guidance,
    build_insider_data,
)
from do_uw.stages.render.context_builders.market_evaluative import (
    _extract_guidance_signals,
    _extract_insider_signals,
    _extract_return_signals,
    _extract_short_interest_signals,
    _extract_volatility_signals,
)
from do_uw.stages.render.formatters import (
    format_currency,
    format_percentage,
    na_if_none,
)

_DIM_DISPLAY_NAMES = {
    "revenue_displacement": "Revenue Displacement",
    "cost_structure": "Cost Structure",
    "competitive_moat": "Competitive Moat",
    "workforce_automation": "Workforce Automation",
    "regulatory_ip": "Regulatory/IP",
}


def dim_display_name(value: str) -> str:
    """Jinja2 filter: convert AI risk dimension ID to display name."""
    return _DIM_DISPLAY_NAMES.get(value, value.replace("_", " ").title())


def _build_insider_summary(mkt: Any) -> str:
    """Build insider trading summary from market data."""
    parts: list[str] = []
    ia = mkt.insider_analysis
    if ia is not None:
        if ia.net_buying_selling is not None:
            parts.append(f"**Net Activity:** {ia.net_buying_selling.value}")
        if ia.pct_10b5_1 is not None:
            parts.append(f"**10b5-1 Plan Coverage:** {ia.pct_10b5_1.value:.0f}%")
        if ia.cluster_events:
            parts.append(f"**Cluster Events:** {len(ia.cluster_events)} detected")
            r = ia.cluster_events[0]
            names = ", ".join(r.insiders[:3])
            if len(r.insiders) > 3:
                names += f" +{len(r.insiders) - 3} more"
            parts.append(f"  Most recent: {r.insider_count} insiders ({names}), {format_currency(r.total_value, compact=True)} total")
    elif mkt.insider_trading is not None and mkt.insider_trading.net_buying_selling is not None:
        parts.append(f"**Net Activity:** {mkt.insider_trading.net_buying_selling.value}")
    return "\n".join(parts) if parts else "*No insider trading data available.*"


def extract_market(
    state: AnalysisState, *, signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract market data for template."""
    ext = state.extracted
    if ext is None or ext.market is None:
        return {}
    mkt = ext.market
    stock = mkt.stock
    si = mkt.short_interest

    result: dict[str, Any] = {
        "current_price": format_currency(stock.current_price.value if stock.current_price else None),
        "high_52w": format_currency(stock.high_52w.value if stock.high_52w else None),
        "low_52w": format_currency(stock.low_52w.value if stock.low_52w else None),
        "pct_off_high": format_percentage(stock.decline_from_high_pct.value if stock.decline_from_high_pct else None),
        "short_pct": format_percentage(si.short_pct_float.value if si.short_pct_float else None),
        "days_to_cover": na_if_none(f"{si.days_to_cover.value:.1f}" if si.days_to_cover else None),
        "insider_summary": _build_insider_summary(mkt),
    }

    # Structured insider trading data
    insider_data = build_insider_data(mkt)
    if insider_data:
        result["insider_data"] = insider_data

    # Evaluative content from signals (with state fallback)
    result.update(_extract_volatility_signals(signal_results, stock))
    result.update(_extract_short_interest_signals(signal_results, si))
    result.update(_extract_insider_signals(signal_results, mkt))
    result.update(_extract_return_signals(signal_results, stock))

    # Valuation ratios (display data)
    valuation: dict[str, str] = {}
    if stock.pe_ratio:
        valuation["pe_ratio"] = f"{stock.pe_ratio.value:.1f}"
    if stock.forward_pe:
        valuation["forward_pe"] = f"{stock.forward_pe.value:.1f}"
    if stock.price_to_book:
        valuation["price_to_book"] = f"{stock.price_to_book.value:.1f}"
    if stock.ev_ebitda:
        valuation["ev_ebitda"] = f"{stock.ev_ebitda.value:.1f}"
    if stock.peg_ratio:
        valuation["peg_ratio"] = f"{stock.peg_ratio.value:.2f}"
    if stock.price_to_sales:
        valuation["price_to_sales"] = f"{stock.price_to_sales.value:.1f}"
    if stock.enterprise_to_revenue:
        valuation["enterprise_to_revenue"] = f"{stock.enterprise_to_revenue.value:.1f}"
    if valuation:
        result["valuation"] = valuation

    # Growth metrics (display data)
    growth: dict[str, str] = {}
    if stock.revenue_growth:
        growth["revenue_growth"] = format_percentage(stock.revenue_growth.value * 100)
    if stock.earnings_growth:
        growth["earnings_growth"] = format_percentage(stock.earnings_growth.value * 100)
    if growth:
        result["growth"] = growth

    # Profitability metrics (display data)
    profitability: dict[str, str] = {}
    if stock.profit_margin:
        profitability["profit_margin"] = format_percentage(stock.profit_margin.value * 100)
    if stock.operating_margin:
        profitability["operating_margin"] = format_percentage(stock.operating_margin.value * 100)
    if stock.gross_margin:
        profitability["gross_margin"] = format_percentage(stock.gross_margin.value * 100)
    if stock.return_on_equity:
        profitability["roe"] = format_percentage(stock.return_on_equity.value * 100)
    if stock.return_on_assets:
        profitability["roa"] = format_percentage(stock.return_on_assets.value * 100)
    if profitability:
        result["profitability"] = profitability

    # Earnings guidance
    eg = mkt.earnings_guidance
    eg_data = build_earnings_guidance(eg)
    # Enrich with signal data
    eg_data.update(_extract_guidance_signals(signal_results, mkt))
    if eg_data:
        result["earnings_guidance"] = eg_data

    # Analyst consensus (display data)
    analyst = mkt.analyst
    if analyst.consensus and analyst.consensus.value:
        result["analyst_consensus"] = str(analyst.consensus.value)
        result["analyst_upgrades"] = str(analyst.recent_upgrades)
        result["analyst_downgrades"] = str(analyst.recent_downgrades)

    # Stock drops
    drops = mkt.stock_drops
    if drops.worst_single_day and drops.worst_single_day.drop_pct:
        dp = float(drops.worst_single_day.drop_pct.value)
        dt = drops.worst_single_day.date
        trigger = ""
        if drops.worst_single_day.trigger_event:
            trigger = f" triggered by {drops.worst_single_day.trigger_event.value}"
        result["worst_drop_pct"] = format_percentage(abs(dp))
        result["worst_drop_date"] = str(dt.value) if dt else "N/A"
        result["worst_drop_trigger"] = trigger
    condensed_drops, all_drops = build_drop_events(drops)
    if condensed_drops:
        result["drop_events"] = condensed_drops
    result["drop_events_overflow"] = all_drops

    # DDL/MDL exposure
    if drops.ddl_exposure is not None:
        result["ddl_exposure"] = format_currency(drops.ddl_exposure.value, compact=True)
    if drops.mdl_exposure is not None:
        result["mdl_exposure"] = format_currency(drops.mdl_exposure.value, compact=True)
    if drops.ddl_settlement_estimate is not None:
        result["ddl_settlement_estimate"] = format_currency(drops.ddl_settlement_estimate.value, compact=True)

    # Capital markets activity
    cm = mkt.capital_markets
    if cm.offerings_3yr or cm.shelf_registrations or cm.convertible_securities:
        cap_mkt: dict[str, Any] = {
            "active_s11_windows": str(cm.active_section_11_windows),
            "has_atm": "Yes" if (cm.has_atm_program and cm.has_atm_program.value) else "No",
        }
        offerings: list[dict[str, str]] = []
        for off in cm.offerings_3yr[:8]:
            offerings.append({
                "type": off.offering_type or "N/A", "filing": off.filing_type or "N/A",
                "date": str(off.date.value) if off.date else "N/A",
                "amount": format_currency(off.amount.value, compact=True) if off.amount else "N/A",
                "s11_window_end": off.section_11_window_end or "N/A",
            })
        cap_mkt["offerings"] = offerings
        shelves: list[dict[str, str]] = []
        for shelf in cm.shelf_registrations[:4]:
            shelves.append({
                "filing": shelf.filing_type or "N/A",
                "date": str(shelf.date.value) if shelf.date else "N/A",
                "amount": format_currency(shelf.amount.value, compact=True) if shelf.amount else "N/A",
            })
        cap_mkt["shelf_registrations"] = shelves
        result["capital_markets"] = cap_mkt

    # ALL charts in main body — density, not removal
    result["main_charts"] = [
        "stock_1y", "stock_5y", "drop_analysis_1y", "drop_analysis_5y",
        "drawdown_1y", "drawdown_5y", "volatility_1y", "volatility_5y",
        "relative_1y", "relative_5y", "drop_scatter_1y", "drop_scatter_5y",
    ]
    result["audit_charts"] = []

    # Stock price sparkline
    result["stock_sparkline"] = ""
    try:
        if state.acquired_data and state.acquired_data.market_data:
            md = state.acquired_data.market_data
            hist = md.get("history_1y", {})
            closes: list[float] = hist.get("Close", []) if isinstance(hist, dict) else []
            if len(closes) >= 2:
                step = max(1, len(closes) // 12)
                sampled = closes[::step]
                if len(sampled) >= 2:
                    result["stock_sparkline"] = render_sparkline(sampled)
    except Exception:
        pass

    # Capital returns (dividends + buybacks)
    result["capital_returns"] = _build_capital_returns(state)

    # 8-K event classification — try extracted data first, fall back to LLM extractions
    eight_k = _build_eight_k_events(mkt)
    if not eight_k or not eight_k.get("filings"):
        eight_k = _build_eight_k_from_llm(state)
    result["eight_k_events"] = eight_k

    # Next earnings date from yfinance info
    result["next_earnings"] = _extract_next_earnings(state)

    # --- Additional market data from acquired_data.market_data ---
    result.update(_build_earnings_history(state))
    result.update(_build_recommendation_breakdown(state))
    result.update(_build_news_articles(state))
    result.update(_build_upgrades_downgrades(state))
    result.update(_build_forward_estimates(state))

    # --- Phase 133: Stock intelligence displays ---
    result.update(_build_eps_revision_trends(state))
    result.update(_build_analyst_targets(state))
    result.update(_build_earnings_trust(state))
    result.update(_build_volume_anomalies(state))
    result.update(_build_correlation_metrics(state))

    # --- Unified drop chart legend data (numbered events + catalysts) ---
    try:
        from do_uw.stages.render.charts.unified_drop_chart import build_drop_legend_data
        result["drop_legend_1y"] = build_drop_legend_data(state, period="1Y")
        result["drop_legend_5y"] = build_drop_legend_data(state, period="5Y")
    except Exception:
        result["drop_legend_1y"] = []
        result["drop_legend_5y"] = []

    # Update main charts list to include new chart types
    result["main_charts"] = [
        "stock_1y", "stock_5y",
        "unified_drop_1y", "unified_drop_5y",
        "insider_timeline_1y", "insider_timeline_5y",
        "drop_analysis_1y", "drop_analysis_5y",
        "drawdown_1y", "drawdown_5y", "volatility_1y", "volatility_5y",
        "relative_1y", "relative_5y", "drop_scatter_1y", "drop_scatter_5y",
    ]

    return result


def _extract_next_earnings(state: AnalysisState) -> str:
    """Extract next earnings date from yfinance info dict."""
    try:
        if state.acquired_data and state.acquired_data.market_data:
            md = state.acquired_data.market_data
            info: dict[str, Any] = {}
            if isinstance(md, dict):
                info = md.get("info", {})
            elif hasattr(md, "info"):
                info = getattr(md, "info", {}) or {}
            if not isinstance(info, dict):
                return ""
            raw = info.get("earningsDate")
            if not raw:
                return ""
            if isinstance(raw, list) and raw:
                raw = raw[0]
            from datetime import datetime

            if isinstance(raw, (int, float)):
                dt = datetime.fromtimestamp(raw)
            elif hasattr(raw, "strftime"):
                dt = raw
            else:
                return str(raw)
            return dt.strftime("%B %d, %Y")
    except Exception:
        pass
    return ""


def _build_capital_returns(state: AnalysisState) -> dict[str, Any]:
    """Build dividend & buyback context from yfinance info + XBRL cash flow."""
    from do_uw.stages.render.formatters import safe_float

    result: dict[str, Any] = {}

    # yfinance dividend data
    info: dict[str, Any] = {}
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            info = md.get("info", {})
        elif hasattr(md, "info"):
            info = getattr(md, "info", {}) or {}

    div_rate = safe_float(info.get("dividendRate"), None)
    div_yield = safe_float(info.get("dividendYield"), None)
    avg_yield = safe_float(info.get("fiveYearAvgDividendYield"), None)
    payout = safe_float(info.get("payoutRatio"), None)
    ex_date = info.get("exDividendDate")

    if div_rate is not None:
        result["dividend_rate"] = f"${div_rate:.2f}"
    if div_yield is not None:
        # yfinance dividendYield: if < 0.20 it's a fraction (0.0041 = 0.41%); otherwise it's already a percentage
        if div_yield < 0.20:
            result["dividend_yield"] = f"{div_yield * 100:.2f}%"
        else:
            result["dividend_yield"] = f"{div_yield:.2f}%"
    if avg_yield is not None:
        result["five_yr_avg_yield"] = f"{avg_yield:.2f}%"
    if payout is not None:
        # yfinance payoutRatio: stored as fraction (0.13 = 13%)
        result["payout_ratio"] = f"{payout * 100:.1f}%" if payout < 1 else f"{payout:.1f}%"
    if ex_date:
        try:
            from datetime import datetime
            if isinstance(ex_date, (int, float)):
                dt = datetime.fromtimestamp(ex_date)
                result["ex_dividend_date"] = dt.strftime("%Y-%m-%d")
            else:
                result["ex_dividend_date"] = str(ex_date)
        except Exception:
            result["ex_dividend_date"] = str(ex_date)

    # XBRL cash flow: dividends paid + share repurchases (per period)
    ext = state.extracted
    if ext and ext.financials and ext.financials.statements and ext.financials.statements.cash_flow:
        cf_items = ext.financials.statements.cash_flow.line_items or []
        for item in cf_items:
            lbl = item.label.lower().replace(" ", "_")
            if "dividend" in lbl and "ratio" not in lbl:
                # Get up to 3 periods
                periods: list[dict[str, str]] = []
                for period_key, sv in list(item.values.items())[:3]:
                    val = sv.value if hasattr(sv, "value") else sv
                    fval = safe_float(val, None)
                    if fval is not None:
                        periods.append({
                            "period": period_key,
                            "value": format_currency(abs(fval), compact=True),
                        })
                if periods:
                    result["dividends_paid"] = periods
            elif "repurchase" in lbl or "buyback" in lbl:
                periods_bb: list[dict[str, str]] = []
                for period_key, sv in list(item.values.items())[:3]:
                    val = sv.value if hasattr(sv, "value") else sv
                    fval = safe_float(val, None)
                    if fval is not None:
                        periods_bb.append({
                            "period": period_key,
                            "value": format_currency(abs(fval), compact=True),
                        })
                if periods_bb:
                    result["share_repurchases"] = periods_bb

    return result


def _build_eight_k_events(mkt: Any) -> dict[str, Any]:
    """Build 8-K event classification context from extracted market data."""
    ek = mkt.eight_k_items
    if not ek or not ek.filings:
        return {}

    result: dict[str, Any] = {
        "total_filings": ek.total_filings,
        "do_critical_count": ek.do_critical_count,
        "has_restatement": ek.has_restatement,
        "has_auditor_change": ek.has_auditor_change,
        "has_officer_departure": getattr(ek, "has_officer_departure", False),
    }

    # Build filings table (most recent first, limit to 15)
    filings: list[dict[str, Any]] = []
    for f in ek.filings[:15]:
        # Handle both Pydantic model and dict (from JSON/LLM extraction)
        if isinstance(f, dict):
            items_list = f.get("items", []) or f.get("items_covered", [])
            if not isinstance(items_list, list):
                items_list = []
            item_titles_map = f.get("item_titles", {}) or {}
            filing_date = f.get("filing_date", "")
            do_severity = f.get("do_severity", "LOW")
            do_critical_items = f.get("do_critical_items", []) or []
        else:
            items_list = f.items if isinstance(f.items, list) else []
            item_titles_map = f.item_titles if hasattr(f, "item_titles") else {}
            filing_date = f.filing_date
            do_severity = f.do_severity
            do_critical_items = f.do_critical_items if hasattr(f, "do_critical_items") else []

        items_display = ", ".join(str(i) for i in items_list) if items_list else "N/A"
        titles = [item_titles_map.get(i, i) for i in items_list[:3]]
        titles_display = "; ".join(str(t) for t in titles)
        filings.append({
            "date": filing_date,
            "items": items_display,
            "titles": titles_display,
            "do_severity": do_severity,
            "is_critical": do_severity in ("CRITICAL", "HIGH"),
            "do_critical_items": ", ".join(str(i) for i in do_critical_items) if do_critical_items else "",
        })
    result["filings"] = filings

    # Item frequency summary
    freq: list[dict[str, Any]] = []
    for item_num, count in sorted(ek.item_frequency.items(), key=lambda x: x[1], reverse=True):
        # Map item numbers to descriptions
        item_desc = _EIGHT_K_ITEM_NAMES.get(item_num, item_num)
        is_do = item_num in ("4.01", "4.02", "5.02", "2.05", "2.06")
        freq.append({"item": item_num, "description": item_desc, "count": count, "is_do_critical": is_do})
    result["item_frequency"] = freq

    # D&O flags summary
    flags: list[str] = []
    if ek.has_restatement:
        flags.append("Restatement/Non-Reliance (Item 4.02)")
    if ek.has_auditor_change:
        flags.append("Auditor Change (Item 4.01)")
    if getattr(ek, "has_officer_departure", False):
        flags.append("Officer Departure (Item 5.02)")
    result["do_flags"] = flags

    return result


# 8-K item number descriptions
_EIGHT_K_ITEM_NAMES: dict[str, str] = {
    "1.01": "Entry into Material Agreement",
    "1.02": "Termination of Material Agreement",
    "1.03": "Bankruptcy/Receivership",
    "2.01": "Completion of Acquisition/Disposition",
    "2.02": "Results of Operations (Earnings)",
    "2.03": "Creation of Direct Financial Obligation",
    "2.04": "Triggering of Off-Balance Sheet Arrangement",
    "2.05": "Costs for Exit/Disposal Activities",
    "2.06": "Material Impairments",
    "3.01": "Notice of Delisting/Listing Transfer",
    "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders",
    "4.01": "Changes in Registrant's Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financials",
    "5.01": "Changes in Control of Registrant",
    "5.02": "Departure/Appointment of Directors or Officers",
    "5.03": "Amendments to Articles/Bylaws",
    "5.04": "Temporary Suspension of Trading Under EBP",
    "5.05": "Amendments to Code of Ethics",
    "5.06": "Change in Shell Company Status",
    "5.07": "Submission of Matters to Vote of Security Holders",
    "5.08": "Shareholder Nominations (Proxy Access)",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements and Exhibits",
}


__all__ = ["_format_disclosure_badge", "dim_display_name", "extract_market"]

