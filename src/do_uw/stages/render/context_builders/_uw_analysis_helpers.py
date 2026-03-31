"""Private helpers for uw_analysis context builder — card builders, badges, etc."""
from __future__ import annotations

import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.uw_analysis_infographics import (
    build_composition_bar_svg,
    build_decile_svg,
    build_ev_revenue_slider_svg,
    build_range_slider_svg,
    build_sparkline_svg,
    extract_ebitda_sparkline,
    extract_fcf_sparkline,
    extract_revenue_sparkline,
    extract_total_assets,
    fmt_int,
    fmt_large_number,
    fmt_price,
    fmt_ratio,
    format_earnings_date,
    mcap_decile,
    mcap_label,
)
from do_uw.stages.render.context_builders.uw_analysis_charts import (
    build_earnings_beat_circles,
)
from do_uw.stages.render.formatters import safe_float


def get_yfinance_info(state: AnalysisState) -> dict[str, Any]:
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            return md.get("info", {})
        if hasattr(md, "info"):
            return getattr(md, "info", {}) or {}
    return {}


def resolve_name(info: dict[str, Any], state: AnalysisState, ticker: str) -> str:
    n = info.get("longName") or info.get("shortName") or str(
        getattr(state.company, "legal_name", None) or ticker)
    return n.get("value", ticker) if isinstance(n, dict) else str(n)


def get_scoring_dict(state: AnalysisState) -> dict[str, Any]:
    if hasattr(state, "scoring") and state.scoring:
        sc = state.scoring
        if isinstance(sc, dict):
            return sc
        return sc.model_dump() if hasattr(sc, "model_dump") else {}
    return {}


def get_analysis_date(state: AnalysisState) -> str:
    """Get the analysis/pipeline run date."""
    try:
        from datetime import datetime
        if state.stages and hasattr(state.stages, "render"):
            r = state.stages.render
            ts = getattr(r, "completed_at", None) or getattr(r, "started_at", None)
            if ts:
                if isinstance(ts, str):
                    return ts[:10]
                if hasattr(ts, "strftime"):
                    return ts.strftime("%Y-%m-%d")
        return datetime.now().strftime("%Y-%m-%d")
    except Exception:
        return ""


def parse_tier(td: Any) -> tuple[str, str, str]:
    if isinstance(td, dict):
        return td.get("tier", "?"), td.get("action", ""), td.get("probability_range", "")
    return (str(td) if td else "?", "", "")


def xbrl_line_item(state: AnalysisState, stmt_attr: str, terms: tuple[str, ...]) -> float | None:
    """Extract first matching XBRL line item value from a financial statement."""
    ext = state.extracted
    if not ext or not getattr(ext, "financials", None):
        return None
    fin = ext.financials  # type: ignore[union-attr]
    stmt = getattr(fin.statements, stmt_attr, None) if fin.statements else None
    if not stmt:
        return None
    for term in terms:
        for li in (stmt.line_items or []):
            if term in li.label.lower().replace(" ", "_"):
                if isinstance(li.values, dict) and li.values:
                    v = next(iter(li.values.values()))
                    if v is not None:
                        raw = v.value if hasattr(v, "value") else v
                        return safe_float(raw, None)
    return None


def extract_xbrl_revenue(state: AnalysisState) -> float | None:
    """XBRL FY revenue (audited). Falls through to None if unavailable."""
    return xbrl_line_item(state, "income_statement", ("total_revenue", "revenue", "net_sales"))


def extract_xbrl_shares(state: AnalysisState) -> float | None:
    """XBRL shares outstanding (audited). Falls through to None if unavailable."""
    return xbrl_line_item(
        state, "balance_sheet",
        ("shares_outstanding", "common_shares_outstanding", "common_stock_shares_outstanding"),
    )


def card_mcap(ctx: dict[str, Any], mc: Any, rev: Any, price: Any, emp: Any, cash: Any, debt: Any) -> None:
    ctx["market_cap"] = fmt_large_number(mc)
    ctx["market_cap_raw"] = mc
    ctx["mcap_label"] = mcap_label(mc)
    dec = mcap_decile(mc)
    ctx["mcap_decile"] = dec
    ctx["mcap_decile_svg"] = build_decile_svg(dec)
    ev = (mc or 0) + (debt or 0) - (cash or 0) if mc else None
    ctx["enterprise_value"] = fmt_large_number(ev)
    evr = ev / rev if ev and rev and rev > 0 else None
    ctx["ev_revenue"] = f"{evr:.1f}x" if evr else "N/A"
    ctx["ev_revenue_raw"] = evr
    ctx["ev_revenue_slider_svg"] = build_ev_revenue_slider_svg(evr)
    shares = int(mc / price) if mc and price and price > 0 else None
    ctx["shares_outstanding"] = f"{shares / 1e6:.0f}M" if shares else "N/A"
    rpe = rev / emp if rev and emp else None
    ctx["rev_per_employee"] = f"${rpe / 1000:.0f}K" if rpe else "N/A"
    ctx["employees"] = fmt_int(emp)


def card_stock(ctx: dict[str, Any], price: Any, h52: Any, l52: Any, info: dict[str, Any]) -> None:
    ctx["stock_price"] = fmt_price(price)
    ctx["high_52w"] = fmt_price(h52)
    ctx["low_52w"] = fmt_price(l52)
    pfh = ((price - h52) / h52 * 100) if price and h52 and h52 > 0 else None
    ctx["pct_from_high"] = f"{pfh:+.0f}% from high" if pfh is not None else ""
    ctx["pct_from_high_raw"] = pfh
    ctx["price_position_pct"] = (
        (price - l52) / (h52 - l52) * 100 if price and h52 and l52 and h52 > l52 else 50
    )
    ctx["range_slider_svg"] = build_range_slider_svg(price, l52, h52)
    ctx["next_earnings"] = format_earnings_date(info)


def _xbrl_fiscal_year(state: AnalysisState) -> str | None:
    """Extract the fiscal year label from the most recent XBRL income statement period."""
    ext = state.extracted
    if not ext or not getattr(ext, "financials", None):
        return None
    fin = ext.financials  # type: ignore[union-attr]
    stmt = getattr(fin.statements, "income_statement", None) if fin.statements else None
    if not stmt or not stmt.line_items:
        return None
    for li in stmt.line_items:
        if isinstance(li.values, dict) and li.values:
            # First key is the most recent period — may be "FY2025" or "2024-09-28"
            period_key = next(iter(li.values.keys()), None)
            if period_key and isinstance(period_key, str):
                # Extract year from various formats: "FY2025", "2024-09-28", "FY24"
                import re as _re
                m = _re.search(r"(\d{4})", period_key)
                if m:
                    return m.group(1)
    return None


def card_revenue(ctx: dict[str, Any], rev: Any, state: AnalysisState) -> None:
    ctx["revenue"] = fmt_large_number(rev)
    # Fix 2: Track revenue source for display label (XBRL=audited FY vs yfinance=TTM)
    xbrl_rev = extract_xbrl_revenue(state)
    if xbrl_rev is not None:
        fy = _xbrl_fiscal_year(state) or ""
        ctx["revenue_source_label"] = f"(FY {fy}, XBRL)" if fy else "(XBRL)"
    else:
        ctx["revenue_source_label"] = "(TTM)"
    ctx["revenue_sparkline_svg"] = build_sparkline_svg(
        extract_revenue_sparkline(state), stroke_color="#1D4ED8")


def card_profit(ctx: dict[str, Any], ebitda: Any, rev: Any, info: dict[str, Any], state: AnalysisState) -> None:
    ctx["ebitda"] = fmt_large_number(ebitda)
    m = (ebitda / rev * 100) if ebitda and rev and rev > 0 else None
    ctx["ebitda_margin"] = f"{m:.1f}%" if m else "N/A"
    ctx["ebitda_sparkline_svg"] = build_sparkline_svg(
        extract_ebitda_sparkline(state), width=120, height=24, stroke_color="#DC2626")
    ctx["free_cashflow"] = fmt_large_number(info.get("freeCashflow"))
    ctx["fcf_sparkline_svg"] = build_sparkline_svg(
        extract_fcf_sparkline(state), width=120, height=24, stroke_color="#6B7280")
    _beats_svg, _beats_summary = build_earnings_beat_circles(state)
    ctx["earnings_beats_svg"] = _beats_svg
    ctx["earnings_beats_summary"] = _beats_summary


def card_balance(
    ctx: dict[str, Any],
    cash: Any,
    debt: Any,
    assets: Any,
    info: dict[str, Any],
    ebitda: Any = None,
    state: AnalysisState | None = None,
) -> None:
    """Card 5: Balance Sheet — enriched with risk indicators and leverage profile."""
    ctx["total_cash"] = fmt_large_number(cash)
    ctx["total_debt"] = fmt_large_number(debt)
    ctx["total_assets"] = fmt_large_number(assets)
    net = (cash or 0) - (debt or 0) if cash is not None else None
    ctx["net_cash"] = fmt_large_number(net) if net is not None else "N/A"
    ctx["net_cash_raw"] = net
    ctx["current_ratio"] = fmt_ratio(info.get("currentRatio"))
    de = safe_float(info.get("debtToEquity"), None)
    ctx["debt_to_equity"] = f"{de:.0f}%" if de is not None else "N/A"
    ctx["debt_to_equity_raw"] = de

    # Equity
    equity = safe_float(info.get("totalStockholderEquity"), None)
    if equity is None:
        bv = safe_float(info.get("bookValue"), None)
        shares = safe_float(info.get("sharesOutstanding"), None)
        if bv is not None and shares is not None and shares > 0:
            equity = bv * shares
    ctx["total_equity"] = fmt_large_number(equity)
    ctx["total_equity_raw"] = equity

    # Total liabilities
    total_liab = (assets - equity) if assets and equity else None
    ctx["total_liabilities"] = fmt_large_number(total_liab)

    # Quick ratio
    qr = safe_float(info.get("quickRatio"), None)
    ctx["quick_ratio"] = f"{qr:.2f}" if qr is not None else "N/A"

    # Goodwill — absolute + % of equity (D&O critical: impairment risk)
    gw = safe_float(info.get("goodwill"), None)
    if gw is None and assets:
        nta = safe_float(info.get("netTangibleAssets"), None)
        if nta is not None and assets > 0:
            gw = assets - nta
            if gw <= 0:
                gw = 0
    gw_pct_assets = gw / assets * 100 if gw and assets and assets > 0 else None
    ctx["goodwill_pct"] = f"{gw_pct_assets:.1f}%" if gw_pct_assets else ("Minimal" if gw is not None and gw == 0 else "N/A")
    ctx["goodwill_raw"] = gw
    ctx["goodwill_amt"] = fmt_large_number(gw)
    gw_pct_equity = gw / equity * 100 if gw and equity and equity > 0 else None
    ctx["goodwill_pct_equity"] = f"{gw_pct_equity:.0f}%" if gw_pct_equity is not None else "N/A"
    ctx["goodwill_pct_equity_raw"] = gw_pct_equity

    # Working capital = current assets - current liabilities
    ca = safe_float(info.get("totalCurrentAssets"), None)
    cl = safe_float(info.get("totalCurrentLiabilities"), None)
    # Try yfinance balance sheet line items if info dict doesn't have them
    if ca is None and state:
        from do_uw.stages.render.context_builders.uw_analysis_infographics import (
            _extract_yfinance_metric,
        )
        ca_vals = _extract_yfinance_metric(state, "balance_sheet", "Current Assets")
        ca = ca_vals[-1] if ca_vals else None
    if cl is None and state:
        from do_uw.stages.render.context_builders.uw_analysis_infographics import (
            _extract_yfinance_metric,
        )
        cl_vals = _extract_yfinance_metric(state, "balance_sheet", "Current Liabilities")
        cl = cl_vals[-1] if cl_vals else None
    wc = (ca - cl) if ca is not None and cl is not None else None
    ctx["working_capital"] = fmt_large_number(wc)
    ctx["working_capital_raw"] = wc

    # Interest coverage = EBITDA / Interest Expense
    int_exp = safe_float(info.get("interestExpense"), None)
    # yfinance reports interestExpense as negative sometimes
    if int_exp is not None and int_exp < 0:
        int_exp = abs(int_exp)
    ebitda_val = safe_float(ebitda, None)
    int_cov = ebitda_val / int_exp if ebitda_val and int_exp and int_exp > 0 else None
    ctx["interest_coverage"] = f"{int_cov:.1f}x" if int_cov is not None else "N/A"
    ctx["interest_coverage_raw"] = int_cov

    # Net debt / EBITDA
    net_debt = (debt or 0) - (cash or 0) if debt is not None else None
    nd_ebitda = net_debt / ebitda_val if net_debt is not None and ebitda_val and ebitda_val > 0 else None
    ctx["net_debt_ebitda"] = f"{nd_ebitda:.1f}x" if nd_ebitda is not None else "N/A"
    ctx["net_debt_ebitda_raw"] = nd_ebitda

    # D&O balance sheet context — one-liner explaining what this means for underwriting
    ctx["bs_do_context"] = _build_bs_do_context(
        gw_pct_equity=gw_pct_equity,
        goodwill=gw,
        equity=equity,
        cash=cash,
        debt=debt,
        wc=wc,
        int_cov=int_cov,
        nd_ebitda=nd_ebitda,
        de=de,
    )

    ctx["composition_bar_svg"] = build_composition_bar_svg(cash, debt, assets)


def _build_bs_do_context(
    *,
    gw_pct_equity: float | None,
    goodwill: float | None,
    equity: float | None,
    cash: float | None,
    debt: float | None,
    wc: float | None,
    int_cov: float | None,
    nd_ebitda: float | None,
    de: float | None,
) -> str:
    """Generate a one-line D&O risk context from balance sheet data."""
    parts: list[str] = []

    # Goodwill impairment risk — the #1 balance sheet SCA trigger
    if gw_pct_equity is not None and gw_pct_equity > 40:
        gw_str = fmt_large_number(goodwill)
        parts.append(
            f"Goodwill at {gw_pct_equity:.0f}% of equity ({gw_str}) creates "
            f"impairment write-down risk — a common SCA trigger"
        )

    # Leverage concerns
    if nd_ebitda is not None and nd_ebitda > 4.0:
        parts.append(f"Leverage elevated at {nd_ebitda:.1f}x net debt/EBITDA — covenant breach risk")
    elif de is not None and de > 200:
        parts.append(f"High leverage (D/E {de:.0f}%) increases going-concern disclosure risk")

    # Liquidity stress
    if wc is not None and wc < 0:
        wc_str = fmt_large_number(abs(wc))
        parts.append(f"Negative working capital ({wc_str} deficit) — near-term liquidity pressure")
    elif int_cov is not None and int_cov < 2.0:
        parts.append(f"Thin interest coverage ({int_cov:.1f}x) — debt service under pressure")

    # Strong balance sheet (positive signal for underwriter)
    if not parts:
        if cash and debt and cash > debt:
            parts.append(
                f"Net cash position ({fmt_large_number(cash)} cash vs {fmt_large_number(debt)} debt) "
                f"reduces going-concern SCA exposure"
            )
        elif int_cov is not None and int_cov > 8.0:
            parts.append(f"Strong interest coverage ({int_cov:.1f}x) — low financial distress risk")
        elif nd_ebitda is not None and nd_ebitda < 1.5:
            parts.append(f"Conservative leverage ({nd_ebitda:.1f}x net debt/EBITDA) — low covenant risk")

    return "; ".join(parts) if parts else ""


def card_valuation(ctx: dict[str, Any], info: dict[str, Any]) -> None:
    """Card 6: Valuation multiples from yfinance info."""
    tpe = safe_float(info.get("trailingPE"), None)
    fpe = safe_float(info.get("forwardPE"), None)
    teps = safe_float(info.get("trailingEps"), None)
    feps = safe_float(info.get("forwardEps"), None)
    evr = safe_float(info.get("enterpriseToRevenue"), None)
    eve = safe_float(info.get("enterpriseToEbitda"), None)
    ptb = safe_float(info.get("priceToBook"), None)
    peg = safe_float(info.get("pegRatio"), None)
    pts = safe_float(info.get("priceToSalesTrailing12Months"), None)

    ctx["val_trailing_pe"] = f"{tpe:.1f}x" if tpe is not None else "N/A"
    ctx["val_forward_pe"] = f"{fpe:.1f}x" if fpe is not None else "N/A"
    ctx["val_trailing_eps"] = f"${teps:.2f}" if teps is not None else "N/A"
    ctx["val_forward_eps"] = f"${feps:.2f}" if feps is not None else "N/A"
    ctx["val_ev_revenue"] = f"{evr:.1f}x" if evr is not None else "N/A"
    ctx["val_ev_ebitda"] = f"{eve:.1f}x" if eve is not None else "N/A"
    ctx["val_price_to_book"] = f"{ptb:.1f}x" if ptb is not None else "N/A"
    ctx["val_peg_ratio"] = f"{peg:.2f}" if peg is not None else "N/A"
    ctx["val_price_to_sales"] = f"{pts:.1f}x" if pts is not None else "N/A"


def badges(ctx: dict[str, Any], info: dict[str, Any], price: Any, h52: Any) -> None:
    sp = info.get("shortPercentOfFloat")
    ctx["short_interest_pct"] = f"{sp * 100:.1f}%" if sp else "N/A"
    beta = info.get("beta")
    ctx["beta"] = f"{beta:.1f}x" if beta else "N/A"
    ctx["vol_label"] = f"{beta:.1f}x sector" if beta else ""
    ctx["vol_color"] = ("#DC2626" if beta and beta > 1.5 else "#D97706" if beta and beta > 1.0 else "#374151")
    pfh = ((price - h52) / h52 * 100) if price and h52 and h52 > 0 else None
    ctx["max_drop"] = f"{pfh:+.1f}%" if pfh is not None else "N/A"
    ctx["max_drop_color"] = "#DC2626" if pfh and pfh < -15 else "#374151"
    ins = info.get("heldPercentInsiders")
    ctx["insider_held_pct"] = f"{ins * 100:.1f}%" if ins else "N/A"


def is_system_jargon(text: str) -> bool:
    """Check if evidence text contains system internals jargon."""
    jargon_markers = ("signal", "coverage=", "scoring:")
    t = text.lower()
    return any(m in t for m in jargon_markers)


# findings() and supporting functions extracted to _uw_analysis_findings.py
from do_uw.stages.render.context_builders._uw_analysis_findings import (  # noqa: E402
    findings,
    _categorize_signal,
    _RISK_CATEGORIES,
)


def _fmt_signal_value(v: Any) -> str:
    """Format a signal value for human display."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (int, float)):
        abs_v = abs(v)
        if abs_v >= 1e9:
            return f"${v / 1e9:.1f}B"
        if abs_v >= 1e6:
            return f"${v / 1e6:.1f}M"
        if abs_v > 100:
            return f"{v:,.0f}"
        if 0 < abs_v < 1:
            return f"{v:.2f}"
        return f"{v:.1f}" if isinstance(v, float) else str(v)
    return str(v)




def litigation(ctx: dict[str, Any], state: AnalysisState, scoring: dict[str, Any]) -> None:
    from do_uw.stages.render.sca_counter import get_active_genuine_scas

    active_scas = get_active_genuine_scas(state)
    active = [str(getattr(s.case_name, "value", s.case_name) if hasattr(s, "case_name") else "?")
              for s in active_scas]
    ctx["active_sca_count"] = len(active)
    ctx["active_sca_names"] = active[:3]

    # Non-SCA active litigation (product liability, consumer, regulatory class actions)
    # These are cases stored under securities_class_actions but not genuine SCAs
    active_sca_set = set(id(s) for s in active_scas)
    other_active: list[dict[str, str]] = []
    if state.extracted and state.extracted.litigation:
        all_scas = getattr(state.extracted.litigation, "securities_class_actions", None) or []
        for case in all_scas:
            if id(case) in active_sca_set:
                continue  # already counted as genuine SCA
            status_val = ""
            if hasattr(case, "status"):
                sv = case.status
                status_val = (sv.value if hasattr(sv, "value") else str(sv)).upper() if sv else ""
            if "ACTIVE" not in status_val:
                continue
            case_name_val = ""
            if hasattr(case, "case_name"):
                sv = case.case_name
                case_name_val = sv.value if hasattr(sv, "value") else str(sv) if sv else ""
            # Determine case type from allegations
            allegations = []
            if hasattr(case, "allegations"):
                alleg = case.allegations
                if hasattr(alleg, "value"):
                    alleg = alleg.value
                if isinstance(alleg, list):
                    allegations = [str(a.value if hasattr(a, "value") else a) for a in alleg]
                elif isinstance(alleg, str):
                    allegations = [alleg]
            alleg_text = " ".join(allegations).lower()
            if "product" in alleg_text or "defect" in alleg_text or "certification" in alleg_text:
                case_type = "Product Liability"
            elif "consumer" in alleg_text or "protection" in alleg_text:
                case_type = "Consumer Protection"
            elif "employment" in alleg_text or "discrimination" in alleg_text:
                case_type = "Employment"
            else:
                case_type = "Class Action"
            # Short name for display
            if " v. " in case_name_val:
                parts = case_name_val.split(" v. ")
                short = parts[0].split(" on behalf")[0].strip() + " v. " + parts[-1].split(",")[0].strip()
            else:
                short = case_name_val[:60] if case_name_val else "Unknown"
            other_active.append({"type": case_type, "name": short})

    ctx["other_active_cases"] = other_active
    ctx["has_any_active_litigation"] = len(active) > 0 or len(other_active) > 0

    agencies = ["DOJ / Criminal", "State AG", "SEC Enforcement", "FDA", "TCPA / Consumer"]
    factors = scoring.get("factor_scores", [])
    f1_ev: list[str] = []
    for f in factors:
        if f.get("factor_id") in ("F1", "F.1"):
            f1_ev = f.get("evidence", [])
            break
    ev_text = " ".join(str(e) for e in f1_ev).lower()
    ctx["reg_agencies_active"] = [a for a in agencies if a.lower().split("/")[0].strip() in ev_text]
    ctx["reg_agencies_clear"] = [a for a in agencies if a.lower().split("/")[0].strip() not in ev_text]

    lp, lm = 0.0, 20.0
    for f in factors:
        if f.get("factor_id") in ("F1", "F.1"):
            lp = safe_float(f.get("points_deducted", 0), 0)
            lm = safe_float(f.get("max_points", 20), 20)
            break

    # Build human-readable litigation summary from ACTUAL case data, not signal counts.
    # An underwriter needs: how many SCAs, derivative suits, active matters — not "19 of 70 signals".
    lit_parts: list[str] = []

    # Active SCAs (already extracted above)
    sca_count = ctx.get("active_sca_count", 0)
    if sca_count > 0:
        names = ctx.get("active_sca_names", [])
        if names:
            lit_parts.append(f"{sca_count} active SCA{'s' if sca_count > 1 else ''}: {', '.join(names[:2])}")
        else:
            lit_parts.append(f"{sca_count} active securities class action{'s' if sca_count > 1 else ''}")

    # Active non-SCA cases (product liability, consumer class actions, etc.)
    if state.extracted and state.extracted.litigation:
        raw_scas = getattr(state.extracted.litigation, "securities_class_actions", None) or []
        for case in raw_scas:
            status_val = ""
            case_name_val = ""
            if hasattr(case, "status"):
                sv = case.status
                status_val = (sv.value if hasattr(sv, "value") else str(sv)).upper() if sv else ""
            if hasattr(case, "case_name"):
                sv = case.case_name
                case_name_val = sv.value if hasattr(sv, "value") else str(sv) if sv else ""
            if "ACTIVE" in status_val and case_name_val and sca_count == 0:
                # This is an active case classified as SCA but filtered by genuine-SCA check
                # (e.g., product liability class action, consumer protection)
                short_name = case_name_val.split(" v. ")[0] + " v. " + case_name_val.split(" v. ")[-1].split(",")[0] if " v. " in case_name_val else case_name_val[:60]
                lit_parts.append(f"1 active class action: {short_name}")

    # Derivative suits — require case name OR filing date (court alone = ghost shell)
    deriv_count = 0
    if state.extracted and state.extracted.litigation:
        derivs = state.extracted.litigation.derivative_suits or []
        for ds in derivs:
            cn = getattr(ds.case_name, "value", None) if hasattr(ds, "case_name") else None
            fd = getattr(ds.filing_date, "value", None) if hasattr(ds, "filing_date") else None
            has_name = cn and cn not in ("Unknown", "N/A", "")
            has_date = fd and fd not in ("N/A", "")
            if has_name or has_date:
                deriv_count += 1
    if deriv_count > 0:
        lit_parts.append(f"{deriv_count} derivative suit{'s' if deriv_count > 1 else ''}")

    # Active regulatory/enforcement matters
    reg_active = ctx.get("reg_agencies_active", [])
    if reg_active:
        lit_parts.append(f"regulatory: {', '.join(reg_active[:2])}")

    # Historical cases from SCAC or other sources
    hist_count = 0
    if state.extracted and state.extracted.litigation:
        hist_cases = getattr(state.extracted.litigation, "historical_cases", None) or []
        hist_count = len(hist_cases)
    if hist_count > 0 and sca_count == 0:
        lit_parts.append(f"{hist_count} historical case{'s' if hist_count > 1 else ''}")

    # Build the summary
    if lit_parts:
        ls = "; ".join(lit_parts)
    elif lp > 0:
        ls = "Litigation risk factors present but no active cases identified"
    else:
        ls = "No active litigation identified"

    r = lp / lm if lm > 0 else 0
    tier, color = (("CRITICAL", "#DC2626") if r >= 0.5 else ("WATCH", "#D97706") if r >= 0.2
                   else ("MONITOR", "#6366F1") if lp > 0 else ("CLEAR", "#16A34A"))
    ctx["lit_summary"] = ls
    ctx["lit_tier"] = tier
    ctx["lit_tier_color"] = color
    ctx["lit_factor_score"] = f"F.1: {lp:.0f}/{lm:.0f}"
    ctx["derivative_count"] = deriv_count


def valuation_multiples_list(ctx: dict[str, Any]) -> list[dict[str, str]]:
    """Build ordered list of valuation multiples for Stock & Market section."""
    items = [
        ("Forward P/E", ctx.get("val_forward_pe", "N/A")),
        ("PEG Ratio", ctx.get("val_peg_ratio", "N/A")),
        ("EV/EBITDA", ctx.get("val_ev_ebitda", "N/A")),
        ("P/Book", ctx.get("val_price_to_book", "N/A")),
        ("P/Sales", ctx.get("val_price_to_sales", "N/A")),
        ("PEG Ratio", ctx.get("val_peg_ratio", "N/A")),
        ("Trailing P/E", ctx.get("val_trailing_pe", "N/A")),
    ]
    return [{"label": label, "value": value} for label, value in items if value != "N/A"]


def build_sector_industry_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build context for Manifest Section 7: Sector & Industry.

    Enriches with 10-K extracted data: competitive position, regulatory
    environment, disruption threats, geographic exposure, and related-party
    transactions — all critical for sector-specific D&O underwriting.
    """
    info = get_yfinance_info(state)
    sector = info.get("sector", "")
    industry = info.get("industry", "")
    if not sector and not industry:
        return None

    ctx: dict[str, Any] = {
        "sector_name": sector or industry,
    }

    scoring = get_scoring_dict(state)
    factors = scoring.get("factor_scores", [])
    for f in factors:
        fid = f.get("factor_id", "")
        if fid in ("F9", "F.9"):
            ev = f.get("evidence", [])
            clean_ev = [str(e) for e in ev if not is_system_jargon(str(e))]
            if clean_ev:
                ctx["competitive_narrative"] = clean_ev[0]
            break

    # --- Enrich from 10-K LLM extraction ---
    if state.acquired_data:
        llm_ext = state.acquired_data.llm_extractions or {}
        # Find the most recent 10-K extraction
        ten_k_data: dict[str, Any] = {}
        for key in sorted(llm_ext.keys(), reverse=True):
            if key.startswith("10-K:"):
                ten_k_data = llm_ext[key] if isinstance(llm_ext[key], dict) else {}
                break

        if ten_k_data:
            # Competitive position
            comp_pos = ten_k_data.get("competitive_position", "")
            if comp_pos and not ctx.get("competitive_narrative"):
                ctx["competitive_narrative"] = str(comp_pos)

            # Regulatory environment (critical for TIC, pharma, financial services)
            reg_env = ten_k_data.get("regulatory_environment", "")
            if reg_env:
                ctx["regulatory_environment"] = str(reg_env)

            # Disruption threats
            threats = ten_k_data.get("disruption_threats", [])
            if isinstance(threats, list) and threats:
                ctx["disruption_threats"] = [str(t) for t in threats[:5]]

            # Geographic exposure (D&O jurisdictional risk)
            geo = ten_k_data.get("geographic_regions", [])
            if isinstance(geo, list) and geo:
                ctx["geographic_exposure"] = [str(g) for g in geo]

            # Related party transactions (governance red flag)
            rpt = ten_k_data.get("related_party_transactions", [])
            if isinstance(rpt, list) and rpt:
                ctx["related_party_transactions"] = [str(r) for r in rpt]

            # Key financial concerns from management
            concerns = ten_k_data.get("key_financial_concerns", [])
            if isinstance(concerns, list) and concerns:
                ctx["key_financial_concerns"] = [str(c) for c in concerns[:5]]

            # Critical accounting estimates (audit risk indicator)
            estimates = ten_k_data.get("critical_accounting_estimates", [])
            if isinstance(estimates, list) and estimates:
                ctx["critical_accounting_estimates"] = [str(e) for e in estimates[:4]]

    if hasattr(state, "pre_computed_commentary") and state.pre_computed_commentary:
        pcc = state.pre_computed_commentary
        if isinstance(pcc, dict):
            si_comm = pcc.get("sector_industry") or pcc.get("ai_risk")
            if si_comm and isinstance(si_comm, dict):
                ctx["commentary_factual"] = si_comm.get("factual", "")
                ctx["commentary_bullets"] = si_comm.get("commentary", "")
        elif hasattr(pcc, "sections"):
            for sec in getattr(pcc, "sections", []):
                if getattr(sec, "section_key", "") in ("sector_industry", "ai_risk"):
                    ctx["commentary_factual"] = getattr(sec, "factual_summary", "")
                    ctx["commentary_bullets"] = getattr(sec, "commentary_bullets", "")
                    break

    # --- Industry-specific analysis modules ---
    try:
        from do_uw.stages.render.context_builders.industry_biotech import (
            build_biotech_industry_context,
        )
        biotech_ctx = build_biotech_industry_context(state)
        if biotech_ctx:
            ctx["biotech_industry"] = biotech_ctx
    except Exception:
        logger.debug("Biotech industry context skipped", exc_info=True)

    return ctx
