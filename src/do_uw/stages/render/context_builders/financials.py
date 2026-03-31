"""Income statement and financial context builders.

Format-agnostic extractors that build template-ready dicts from AnalysisState.
Both HTML and Word renderers consume these same context builders.

Tabular/display data extracted directly from state. Evaluative content
(distress, earnings quality, leverage, tax, liquidity) sourced from
signal results via financials_evaluative.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.sparklines import render_sparkline
from do_uw.stages.render.context_builders._financials_display import (
    build_quarterly_context,
    build_yfinance_quarterly_context,
    extract_peer_matrix,
)
from do_uw.stages.render.context_builders.financials_balance import (
    _build_statement_rows,
)
from do_uw.stages.render.context_builders.financials_evaluative import (
    _extract_distress_signals,
    _extract_earnings_quality_signals,
    _extract_leverage_signals,
    _extract_liquidity_signals,
    _extract_tax_signals,
)
from do_uw.stages.render.context_builders.financials_forensic import (
    build_forensic_dashboard_context,
)
from do_uw.stages.render.context_builders.financials_peers import (
    build_peer_percentile_context,
)
from do_uw.stages.render.context_builders.financials_computed import (
    build_audit_disclosure_alerts,
    build_bankruptcy_composite,
    build_capital_allocation,
    build_debt_service_coverage,
    build_goodwill_equity_ratio,
    build_refinancing_risk,
)
from do_uw.stages.render.context_builders.financials_quarterly import (
    build_quarterly_trend_context,
)
from do_uw.stages.render.formatters import (
    format_change_indicator,
    format_currency,
    format_percentage,
    sv_val,
)


def _margin_change(
    op: float | None, rev: float | None,
    prior_op: float | None, prior_rev: float | None,
) -> str:
    """Compute margin change as basis points string (e.g., '+120 bps')."""
    if (
        op is not None and rev is not None and rev > 0
        and prior_op is not None and prior_rev is not None and prior_rev > 0
    ):
        current_margin = op / rev * 100
        prior_margin = prior_op / prior_rev * 100
        return f"{(current_margin - prior_margin) * 100:+.0f} bps"
    return ""


def find_line_item_value(
    items: list[Any], label: str, period_idx: int = 0,
) -> float | None:
    """Find a line item by label and return a specific period's value."""
    search = label.lower().replace(" ", "_")
    for item in items:
        normalized = item.label.lower().replace(" ", "_")
        if normalized == search or search in normalized:
            vals = list(item.values.values())
            if len(vals) > period_idx and vals[period_idx] is not None:
                return float(vals[period_idx].value)
    return None


def _build_income_context(stmts: Any, result: dict[str, Any]) -> None:
    """Extract income statement display data into result dict."""
    if stmts.income_statement is None:
        return
    result["has_income"] = True
    items = stmts.income_statement.line_items
    rev_val = find_line_item_value(items, "total_revenue")
    ni_val = find_line_item_value(items, "net_income")
    result["revenue"] = format_currency(rev_val, compact=True)
    result["net_income"] = format_currency(ni_val, compact=True)

    prior_rev = find_line_item_value(items, "total_revenue", 1)
    prior_ni = find_line_item_value(items, "net_income", 1)
    result["prior_revenue"] = format_currency(prior_rev, compact=True) if prior_rev else None
    result["prior_net_income"] = format_currency(prior_ni, compact=True) if prior_ni else None
    result["revenue_yoy"] = (
        format_change_indicator(rev_val, prior_rev)
        if rev_val is not None and prior_rev is not None and prior_rev != 0 else ""
    )
    result["net_income_yoy"] = (
        format_change_indicator(ni_val, prior_ni)
        if ni_val is not None and prior_ni is not None and prior_ni != 0 else ""
    )

    gp_val = find_line_item_value(items, "gross_profit")
    result["gross_profit"] = format_currency(gp_val, compact=True) if gp_val else None
    if gp_val and rev_val and rev_val > 0:
        result["gross_margin"] = format_percentage(gp_val / rev_val * 100)
    op_val = find_line_item_value(items, "operating_income")
    if op_val is None:
        op_val = find_line_item_value(items, "income_from_operations")
    result["operating_income"] = format_currency(op_val, compact=True) if op_val else None
    if op_val and rev_val and rev_val > 0:
        result["operating_margin"] = format_percentage(op_val / rev_val * 100)
    prior_op = find_line_item_value(items, "operating_income", 1)
    if prior_op is None:
        prior_op = find_line_item_value(items, "income_from_operations", 1)
    result["prior_operating_margin"] = (
        format_percentage(prior_op / prior_rev * 100)
        if prior_op and prior_rev and prior_rev > 0 else None
    )
    result["operating_margin_yoy"] = _margin_change(op_val, rev_val, prior_op, prior_rev)

    eps_val = find_line_item_value(items, "diluted_earnings")
    result["diluted_eps"] = f"${eps_val:.2f}" if eps_val else None
    prior_eps = find_line_item_value(items, "diluted_earnings", 1)
    result["prior_diluted_eps"] = f"${prior_eps:.2f}" if prior_eps else None
    result["eps_yoy"] = (
        format_change_indicator(eps_val, prior_eps)
        if eps_val is not None and prior_eps is not None and prior_eps != 0 else ""
    )

    rd_val = find_line_item_value(items, "research_and_development")
    result["rd_expense"] = format_currency(rd_val, compact=True) if rd_val else None
    sga_val = find_line_item_value(items, "selling_general")
    result["sga_expense"] = format_currency(sga_val, compact=True) if sga_val else None

    rev_item = next((it for it in items if "revenue" in it.label.lower()), None)
    if rev_item and rev_item.values:
        period_keys = list(rev_item.values.keys())
        if period_keys:
            result["latest_period"] = period_keys[0]
        if len(period_keys) >= 2:
            result["prior_period"] = period_keys[1]

    src = stmts.income_statement.filing_source
    if src:
        result["filing_source"] = src


def _build_sparklines(stmts: Any, result: dict[str, Any]) -> None:
    """Build financial sparklines from multi-period data."""
    result["revenue_sparkline"] = ""
    result["net_income_sparkline"] = ""
    result["total_assets_sparkline"] = ""
    try:
        if stmts.income_statement is not None:
            items = stmts.income_statement.line_items
            for item in items:
                if "revenue" in item.label.lower().replace(" ", "_"):
                    vals = [v.value for v in item.values.values() if v is not None]
                    if len(vals) >= 2:
                        result["revenue_sparkline"] = render_sparkline(list(reversed(vals)))
                    break
            for item in items:
                if "net_income" in item.label.lower().replace(" ", "_"):
                    vals = [v.value for v in item.values.values() if v is not None]
                    if len(vals) >= 2:
                        result["net_income_sparkline"] = render_sparkline(list(reversed(vals)))
                    break
    except Exception:
        pass


def _build_balance_sheet(stmts: Any, result: dict[str, Any]) -> None:
    """Extract balance sheet display data."""
    if stmts.balance_sheet is None:
        return
    bs = stmts.balance_sheet.line_items
    ta_val = find_line_item_value(bs, "total_assets")
    result["total_assets"] = format_currency(ta_val, compact=True)
    prior_ta = find_line_item_value(bs, "total_assets", 1)
    result["prior_total_assets"] = format_currency(prior_ta, compact=True) if prior_ta else None
    result["total_assets_yoy"] = (
        format_change_indicator(ta_val, prior_ta)
        if ta_val is not None and prior_ta is not None and prior_ta != 0 else ""
    )
    equity = find_line_item_value(bs, "stockholders_equity")
    if equity is None:
        equity = find_line_item_value(bs, "stockholders")
    result["total_equity"] = format_currency(equity, compact=True)
    prior_eq = find_line_item_value(bs, "stockholders_equity", 1)
    if prior_eq is None:
        prior_eq = find_line_item_value(bs, "stockholders", 1)
    result["prior_total_equity"] = format_currency(prior_eq, compact=True) if prior_eq else None
    result["total_equity_yoy"] = (
        format_change_indicator(equity, prior_eq)
        if equity is not None and prior_eq is not None and prior_eq != 0 else ""
    )
    try:
        for item in bs:
            if "total_assets" in item.label.lower().replace(" ", "_"):
                vals = [v.value for v in item.values.values() if v is not None]
                if len(vals) >= 2:
                    result["total_assets_sparkline"] = render_sparkline(list(reversed(vals)))
                break
    except Exception:
        pass
    result["cash"] = format_currency(find_line_item_value(bs, "cash_and_cash"), compact=True)
    result["total_liabilities"] = format_currency(find_line_item_value(bs, "total_liabilities"), compact=True)


def _build_cash_flow(stmts: Any, result: dict[str, Any]) -> None:
    """Extract cash flow display data."""
    if stmts.cash_flow is None:
        return
    cf = stmts.cash_flow.line_items
    result["operating_cf"] = format_currency(find_line_item_value(cf, "operating_activities"), compact=True)
    result["capex"] = format_currency(find_line_item_value(cf, "capital_expenditures"), compact=True)
    buyback = find_line_item_value(cf, "share_repurchases")
    result["buybacks"] = format_currency(buyback, compact=True) if buyback else None
    divs = find_line_item_value(cf, "dividends_paid")
    result["dividends"] = format_currency(divs, compact=True) if divs else None


def _build_debt_structure(fin: Any) -> dict[str, Any]:
    """Build debt structure context from LLM-extracted debt data."""
    import re as _re

    ds_sv = getattr(fin, "debt_structure", None)
    if ds_sv is None:
        return {}
    ds = ds_sv.value if hasattr(ds_sv, "value") else ds_sv
    if not isinstance(ds, dict):
        return {}

    result: dict[str, Any] = {}

    # Parse LLM debt instruments into table rows
    instruments_raw = ds.get("llm_debt_instruments", [])
    instruments: list[dict[str, str]] = []
    for inst in instruments_raw:
        # Handle SourcedValue objects, dicts, and plain strings
        if isinstance(inst, dict):
            val = inst.get("value", "")
        elif hasattr(inst, "value") and not isinstance(inst, (str, int, float, bool)):
            val = inst.value  # SourcedValue — extract the inner value
        else:
            val = inst
        name = str(val) if val else ""
        # Infer rate and maturity from instrument name like "$4.75% Notes due 2026"
        rate_match = _re.search(r"(\d+\.?\d*)\s*%", name)
        rate = f"{rate_match.group(1)}%" if rate_match else "N/A"
        year_match = _re.search(r"due\s+(\d{4})", name, _re.IGNORECASE)
        maturity = year_match.group(1) if year_match else "N/A"
        # Clean up the name (strip leading $)
        clean_name = _re.sub(r"^\$", "", name).strip()
        instruments.append({"name": clean_name, "rate": rate, "maturity": maturity})
    if instruments:
        result["instruments"] = instruments

    # Maturity schedule — group instruments by maturity year
    from datetime import datetime
    current_year = datetime.now().year
    maturity_by_year: dict[int, list[str]] = {}
    for inst in instruments:
        if inst["maturity"] != "N/A":
            yr = int(inst["maturity"])
            maturity_by_year.setdefault(yr, []).append(inst["name"])
    if maturity_by_year:
        maturity_schedule: list[dict[str, Any]] = []
        total_instruments = len([i for i in instruments if i["maturity"] != "N/A"])
        for yr in sorted(maturity_by_year.keys()):
            count = len(maturity_by_year[yr])
            is_near_term = yr <= current_year + 2
            maturity_schedule.append({
                "year": str(yr),
                "instrument_count": count,
                "instruments": maturity_by_year[yr],
                "is_near_term": is_near_term,
            })
        near_term_count = sum(
            len(maturity_by_year[yr])
            for yr in maturity_by_year
            if yr <= current_year + 2
        )
        near_term_pct = (near_term_count / total_instruments * 100) if total_instruments > 0 else 0
        result["maturity_schedule"] = maturity_schedule
        result["near_term_maturity_pct"] = near_term_pct
        result["near_term_maturity_flag"] = near_term_pct > 20

    # Interest rate summary
    rates_data = ds.get("interest_rates", {})
    if isinstance(rates_data, dict):
        fixed = rates_data.get("fixed_rates", [])
        has_floating = rates_data.get("has_floating", False)
        if fixed:
            lo = min(fixed)
            hi = max(fixed)
            summary = f"{len(fixed)} fixed rates ranging {lo}%–{hi}%"
            if has_floating:
                summary += "; floating rate exposure: Yes"
            else:
                summary += "; floating rate exposure: No"
            result["interest_summary"] = summary

    # Covenant status
    cov = ds.get("covenants", {})
    if isinstance(cov, dict):
        cov_status = cov.get("covenant_status", {})
        if isinstance(cov_status, dict):
            val = cov_status.get("value", "")
            if val:
                result["covenant_status"] = str(val)
        elif hasattr(cov_status, "value") and not isinstance(cov_status, (str, int, float, bool)):
            result["covenant_status"] = str(cov_status.value)
        elif cov_status:
            result["covenant_status"] = str(cov_status)

    # Credit facility
    cf = ds.get("credit_facility", {})
    if isinstance(cf, dict):
        llm_detail = cf.get("llm_detail", {})
        if isinstance(llm_detail, dict):
            val = llm_detail.get("value", "")
            if val:
                result["credit_facility"] = str(val)
        elif hasattr(llm_detail, "value") and not isinstance(llm_detail, (str, int, float, bool)):
            result["credit_facility"] = str(llm_detail.value)
        elif llm_detail:
            result["credit_facility"] = str(llm_detail)

    return result


def _build_liquidity_detail(fin: Any) -> dict[str, Any]:
    """Build liquidity detail card with all 5 metrics and risk colors."""
    from do_uw.stages.render.formatters import safe_float

    if fin.liquidity is None:
        return {}
    liq = fin.liquidity.value if hasattr(fin.liquidity, "value") else fin.liquidity
    if not isinstance(liq, dict):
        return {}

    metrics: list[dict[str, Any]] = []

    cr = liq.get("current_ratio")
    if cr is not None:
        cr_f = safe_float(cr)
        color = "red" if cr_f < 0.5 else ("amber" if cr_f < 1.0 else "green")
        metrics.append({"label": "Current Ratio", "value": f"{cr_f:.2f}", "color": color})

    qr = liq.get("quick_ratio")
    if qr is not None:
        qr_f = safe_float(qr)
        color = "red" if qr_f < 0.5 else ("amber" if qr_f < 1.0 else "green")
        metrics.append({"label": "Quick Ratio", "value": f"{qr_f:.2f}", "color": color})

    cash_r = liq.get("cash_ratio")
    if cash_r is not None:
        cash_f = safe_float(cash_r)
        color = "red" if cash_f < 0.1 else ("amber" if cash_f < 0.3 else "green")
        metrics.append({"label": "Cash Ratio", "value": f"{cash_f:.3f}", "color": color})

    wc = liq.get("working_capital")
    if wc is not None:
        wc_f = safe_float(wc)
        color = "amber" if wc_f < 0 else "green"
        metrics.append({
            "label": "Working Capital",
            "value": format_currency(wc_f, compact=True),
            "color": color,
        })

    dch = liq.get("days_cash_on_hand")
    if dch is not None:
        dch_f = safe_float(dch)
        color = "red" if dch_f < 30 else ("amber" if dch_f < 90 else "green")
        metrics.append({"label": "Days Cash on Hand", "value": f"{dch_f:.0f}", "color": color})

    if not metrics:
        return {}
    return {"metrics": metrics}


def _extract_health_narrative(fin: Any) -> str:
    """Extract financial health narrative from state."""
    nar = getattr(fin, "financial_health_narrative", None)
    if nar is None:
        return ""
    val = nar.value if hasattr(nar, "value") else nar
    return str(val) if val else ""


def extract_financials(
    state: AnalysisState, *, signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract financial data for template."""
    ext = state.extracted
    if ext is None or ext.financials is None:
        return {}
    fin = ext.financials
    result: dict[str, Any] = {
        "has_income": False, "latest_period": None,
        "prior_period": None, "filing_source": None,
    }

    stmts = fin.statements
    _build_income_context(stmts, result)
    _build_sparklines(stmts, result)
    _build_balance_sheet(stmts, result)
    _build_cash_flow(stmts, result)

    # Tier A computed metrics
    build_goodwill_equity_ratio(stmts, result)
    build_capital_allocation(stmts, result)
    build_debt_service_coverage(stmts, fin, result)
    build_refinancing_risk(stmts, fin, result)
    build_bankruptcy_composite(fin, result)

    # Evaluative content from signals (with state fallback)
    sic_code = None
    if state.company and state.company.identity and state.company.identity.sic_code:
        sic_raw = state.company.identity.sic_code
        sic_code = str(sic_raw.value) if hasattr(sic_raw, "value") else str(sic_raw)
    result.update(_extract_distress_signals(signal_results, fin, sic_code=sic_code))
    result.update(_extract_earnings_quality_signals(signal_results, fin))
    result.update(_extract_leverage_signals(signal_results, fin))
    result.update(_extract_tax_signals(signal_results, fin))
    result.update(_extract_liquidity_signals(signal_results, fin))

    # Audit (display data + D&O context)
    audit = fin.audit
    result["auditor_name"] = str(sv_val(audit.auditor_name, "N/A"))
    result["is_big4"] = "Yes" if audit.is_big4 and audit.is_big4.value else "No"
    result["auditor_tenure"] = f"{audit.tenure_years.value} years" if audit.tenure_years else "N/A"
    result["material_weaknesses"] = len(audit.material_weaknesses)
    result["going_concern"] = "Yes" if audit.going_concern and audit.going_concern.value else "No"

    # Audit disclosure alerts (restatements, auditor change, MW, Q4 loading)
    build_audit_disclosure_alerts(signal_results, fin, result)

    # D&O context for audit risk items
    from do_uw.stages.render.context_builders._signal_fallback import safe_get_result as _safe_get
    _mw_sig = _safe_get(signal_results, "FIN.ACCT.material_weakness")
    result["audit_mw_do_context"] = _mw_sig.do_context if _mw_sig and _mw_sig.do_context else ""
    _restate_sig = _safe_get(signal_results, "FIN.ACCT.restatement")
    result["audit_restatement_do_context"] = _restate_sig.do_context if _restate_sig and _restate_sig.do_context else ""
    _gc_sig = _safe_get(signal_results, "FIN.ACCT.internal_controls")
    result["audit_gc_do_context"] = _gc_sig.do_context if _gc_sig and _gc_sig.do_context else ""

    # Peer group (display data)
    peer_group = fin.peer_group
    peers_list: list[dict[str, str]] = []
    if peer_group is not None and peer_group.peers:
        for peer in peer_group.peers[:8]:
            peers_list.append({
                "ticker": peer.ticker, "name": peer.name,
                "market_cap": format_currency(peer.market_cap, compact=True) if peer.market_cap else "N/A",
                "score": f"{peer.peer_score:.0f}",
            })
    result["peers"] = peers_list

    # Statement tables, quarterly, trends, forensics, peer percentiles
    result.update(_build_statement_rows(stmts))
    result["quarterly_updates"] = build_quarterly_context(fin)
    result["yfinance_quarterly"] = build_yfinance_quarterly_context(fin)
    result["quarterly_trends"] = build_quarterly_trend_context(state)
    result["forensics"] = build_forensic_dashboard_context(state, signal_results)
    result["peer_percentiles"] = build_peer_percentile_context(state)

    # Debt structure (from LLM extraction)
    result["debt_structure"] = _build_debt_structure(fin)

    # Liquidity detail card (all 5 metrics from state)
    result["liquidity_detail"] = _build_liquidity_detail(fin)

    # Financial health narrative
    result["health_narrative"] = _extract_health_narrative(fin)

    return result


__all__ = ["extract_financials", "extract_peer_matrix", "find_line_item_value"]
