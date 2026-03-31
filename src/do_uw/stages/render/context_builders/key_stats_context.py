"""Key Stats Overview context builder.

Consolidates identity, scale, market position, classification.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._key_stats_helpers import (
    build_litigation_summary,
    build_mountain_chart,
    build_regulatory_oversight,
    build_risk_pulse,
    build_strengths_vulnerabilities,
    describe_revenue_model,
    extract_customer_list,
    extract_geo_regions,
    extract_segment_list,
    extract_segments_text,
    extract_top_customer,
    fmt_employees,
    fmt_large_number,
    governing_insight,
    maturity_label,
    size_tier,
    spectrum_pct,
    sv,
)
from do_uw.stages.render.formatters import clean_company_name

logger = logging.getLogger(__name__)

# US state code → full name (subset for D&O-relevant states)
_US_STATE_NAMES: dict[str, str] = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming", "DC": "District of Columbia",
}


def _state_full_name(code: str) -> str:
    """Convert US state abbreviation to full name."""
    return _US_STATE_NAMES.get(code.upper().strip(), code)


def build_key_stats_context(
    state: AnalysisState,
    *,
    canonical: Any | None = None,
) -> dict[str, Any]:
    """Build consolidated Key Stats Overview from AnalysisState.

    Args:
        state: The analysis state.
        canonical: Optional CanonicalMetrics object from the canonical registry.
            When provided, cross-section metrics (revenue, market_cap, employees,
            exchange) are read from canonical for consistency. Falls back to legacy
            extraction when canonical is None (e.g. md_renderer path).
    """
    if state.company is None:
        return {"available": False}

    c = state.company
    ident = c.identity

    # Prefer canonical for cross-section metrics when available
    if canonical is not None:
        market_cap_raw = canonical.market_cap.raw
        employees_raw = canonical.employees.raw
    else:
        market_cap_raw = sv(c.market_cap)
        employees_raw = sv(c.employee_count)
    years_pub = sv(c.years_public)
    subs = sv(c.subsidiary_count)
    industry = sv(c.industry_classification) or "\u2014"
    filer = sv(c.filer_category) or "\u2014"
    rev_model = sv(c.revenue_model_type) or "\u2014"
    business_desc = sv(c.business_description) or ""

    sub_struct = sv(c.subsidiary_structure) or {}
    jurisdiction_count = sub_struct.get("jurisdiction_count", "\u2014") if isinstance(sub_struct, dict) else "\u2014"
    high_reg = sub_struct.get("high_regulatory_count", 0) if isinstance(sub_struct, dict) else 0

    stock_price, high_52w, low_52w = 0.0, 0.0, 0.0
    ext = state.extracted
    if ext and ext.market and ext.market.stock:
        s = ext.market.stock
        stock_price = sv(s.current_price) or 0.0
        high_52w = sv(s.high_52w) or 0.0
        low_52w = sv(s.low_52w) or 0.0

    pct_off_high = round((1 - stock_price / high_52w) * 100) if high_52w > 0 else 0
    range_span = high_52w - low_52w
    price_pct_in_range = round((stock_price - low_52w) / range_span * 100) if range_span > 0 else 50

    chart_1y, chart_5y = "", ""
    chart_1y_label, chart_5y_label = "1-Year", "5-Year"
    is_recent_ipo = False
    ipo_months = 0

    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        closes_1y = md.get("history_1y", {}).get("Close", [])
        closes_5y = md.get("history_5y", {}).get("Close", [])

        # Detect recent IPO: 5Y data same length as 1Y, or years_public < 2
        yp = years_pub if isinstance(years_pub, (int, float)) else 0
        ratio = len(closes_5y) / max(len(closes_1y), 1) if closes_1y else 5.0
        if ratio < 2.0 or yp < 2:
            is_recent_ipo = True
            ipo_months = round(len(closes_5y) / 21) if closes_5y else 0  # ~21 trading days/month

        if closes_1y and len(closes_1y) > 10:
            chart_1y = build_mountain_chart(closes_1y)
            if is_recent_ipo:
                chart_1y_label = f"Since IPO ({ipo_months}mo)"

        if closes_5y and len(closes_5y) > 10 and not is_recent_ipo:
            # Only show 5Y chart if company has been public long enough
            chart_5y = build_mountain_chart(closes_5y)
        elif closes_5y and len(closes_5y) > 10 and is_recent_ipo:
            # For recent IPO, don't show a misleading "5-Year" chart
            chart_5y = ""

    # Revenue: canonical (XBRL-first) > legacy extraction
    if canonical is not None and canonical.revenue.raw is not None:
        revenue_raw = canonical.revenue.raw
    else:
        revenue_raw = _extract_revenue(ext)
    geo_mix = _build_geo_mix(c)

    tier, quality_score = "\u2014", 0.0
    if state.scoring:
        tier = state.scoring.tier.tier if state.scoring.tier else "\u2014"
        quality_score = state.scoring.quality_score or 0.0

    entity_type = (sv(ident.entity_type) or "operating").title()
    gov = _extract_governance(ext)

    kpr = sv(c.key_person_risk) or {}
    ceo_tenure = "\u2014"
    has_succession = False
    if isinstance(kpr, dict):
        ct = kpr.get("ceo_tenure_years")
        if ct:
            ceo_tenure = f"CEO: {ct} yrs"
        has_succession = kpr.get("has_succession_plan", False)

    lit = _extract_litigation_legacy(ext, state)
    red_flags_triggered = sum(1 for r in state.scoring.red_flags if r.triggered) if state.scoring else 0

    size = size_tier(market_cap_raw)
    maturity = maturity_label(years_pub)

    scale_metrics = [
        {"label": "Market Cap", "value": fmt_large_number(market_cap_raw), "tier": size,
         "pct": spectrum_pct(market_cap_raw, [50e6, 300e6, 2e9, 10e9, 200e9])},
        {"label": "Revenue", "value": fmt_large_number(revenue_raw),
         "tier": size_tier(revenue_raw) if revenue_raw else "\u2014",
         "pct": spectrum_pct(revenue_raw, [10e6, 100e6, 1e9, 5e9, 50e9])},
        {"label": "Employees", "value": fmt_employees(employees_raw),
         "tier": "Large" if (employees_raw or 0) >= 10000 else "Mid" if (employees_raw or 0) >= 1000 else "Small",
         "pct": spectrum_pct(employees_raw, [100, 500, 1000, 10000, 100000])},
        {"label": "Years Public", "value": str(years_pub) if years_pub else "\u2014", "tier": maturity,
         "pct": spectrum_pct(years_pub, [1, 3, 10, 30, 50]), "inverted": True},
    ]

    geo_regions, geo_breakdown = extract_geo_regions(c)

    return {
        "available": True,
        "legal_name": clean_company_name(sv(ident.legal_name) or ""), "ticker": ident.ticker,
        "exchange": (canonical.exchange.formatted if canonical and canonical.exchange.raw else sv(ident.exchange)),
        "cik": sv(ident.cik),
        "sic_code": sv(ident.sic_code), "sic_description": sv(ident.sic_description),
        "naics_code": sv(ident.naics_code), "state_of_inc": sv(ident.state_of_incorporation),
        "state_of_inc_full": _state_full_name(sv(ident.state_of_incorporation) or ""),
        "fy_end": sv(ident.fiscal_year_end), "is_fpi": sv(ident.is_fpi) or False,
        "sector": sv(ident.sector) or "\u2014", "industry": industry, "filer_category": filer,
        "market_cap_fmt": fmt_large_number(market_cap_raw),
        "revenue_fmt": fmt_large_number(revenue_raw),
        "employees_fmt": fmt_employees(employees_raw),
        "years_public": years_pub or "\u2014", "subsidiary_count": subs or "\u2014",
        "jurisdiction_count": jurisdiction_count, "high_reg_jurisdictions": high_reg,
        "size_tier": size, "maturity_label": maturity,
        "stock_price": stock_price, "high_52w": high_52w, "low_52w": low_52w,
        "pct_off_high": pct_off_high, "price_pct_in_range": price_pct_in_range,
        "chart_1y": chart_1y, "chart_5y": chart_5y,
        "chart_1y_label": chart_1y_label, "chart_5y_label": chart_5y_label,
        "is_recent_ipo": is_recent_ipo, "ipo_months": ipo_months,
        "scale_metrics": scale_metrics,
        "revenue_model": describe_revenue_model(rev_model, business_desc),
        "geo_mix": geo_mix, "entity_type": entity_type,
        "analysis_date": state.pipeline_metadata.get("started_at", "\u2014") if state.pipeline_metadata else "\u2014",
        **gov, **lit,
        "ceo_tenure": ceo_tenure, "has_succession": has_succession,
        "red_flags_triggered": red_flags_triggered,
        "customer_concentration": extract_top_customer(c),
        "segment_info": extract_segments_text(c),
        "customer_list": extract_customer_list(c),
        "segment_list": extract_segment_list(c),
        "geo_regions": geo_regions, "geo_breakdown": geo_breakdown,
        "litigation_summary": build_litigation_summary(state),
        "regulatory_oversight": build_regulatory_oversight(state),
        "comparison_sector": _extract_comparison_sector(state),
        "competitors": _extract_competitors(state),
        "tier": tier, "quality_score": quality_score,
        "business_description": business_desc,
        "governing_insight": governing_insight(sv(ident.legal_name), size, maturity, industry, subs),
        "risk_pulse": build_risk_pulse(state),
        "sv": build_strengths_vulnerabilities(state),
    }


def _extract_revenue(ext: object | None) -> float | None:
    """Extract most recent revenue — matches financials.py find_line_item_value('total_revenue')."""
    if not ext or not getattr(ext, "financials", None):
        return None
    fin = ext.financials  # type: ignore[union-attr]
    if not fin.statements or not fin.statements.income_statement:
        return None
    items = fin.statements.income_statement.line_items or []
    # Priority: total_revenue > revenue > net_sales (consistent with Financial Health section)
    for term in ("total_revenue", "revenue", "net_sales"):
        for li in items:
            if term in li.label.lower().replace(" ", "_"):
                if isinstance(li.values, dict) and li.values:
                    v = next(iter(li.values.values()))
                    if v is not None:
                        return sv(v)
    return None


def _build_geo_mix(company: object) -> str:
    """Build legacy geographic mix text string."""
    geo_raw = getattr(company, "geographic_footprint", None) or []
    parts = []
    for g in geo_raw:
        gv = sv(g) if hasattr(g, "value") else g
        if isinstance(gv, dict):
            region = gv.get("country", gv.get("region", ""))
            pct = gv.get("revenue_pct", gv.get("percentage", ""))
            if region and pct:
                parts.append(f"{region} {pct}%")
    return " | ".join(parts[:3]) if parts else "\u2014"


def _extract_governance(ext: object | None) -> dict[str, Any]:
    """Extract governance stats into a flat dict."""
    r: dict[str, Any] = {
        "board_size": "\u2014", "governance_score": "", "ceo_comp": "\u2014",
        "say_on_pay": "\u2014", "institutional_pct": "\u2014",
    }
    if not ext or not getattr(ext, "governance", None):
        return r
    g = ext.governance  # type: ignore[union-attr]
    if g.board:
        bs = sv(getattr(g.board, "size", None))
        if bs:
            r["board_size"] = bs
    if g.governance_score:
        gs = getattr(g.governance_score, "overall_score", None)
        if gs:
            r["governance_score"] = f"{gs:.0f}/100"
    if g.comp_analysis:
        cc = sv(getattr(g.comp_analysis, "ceo_total_comp", None))
        if cc:
            r["ceo_comp"] = fmt_large_number(cc).replace("$", "$")
    if g.compensation:
        sop = sv(getattr(g.compensation, "say_on_pay_support_pct", None))
        if sop:
            r["say_on_pay"] = f"{sop:.0f}%"
    if g.ownership:
        ip = sv(getattr(g.ownership, "institutional_pct", None))
        if ip:
            r["institutional_pct"] = f"{ip:.1f}%"
    return r


def _extract_litigation_legacy(ext: object | None, state: AnalysisState | None = None) -> dict[str, str]:
    """Extract legacy individual litigation stats."""
    r: dict[str, str] = {
        "active_litigation": "0", "historical_litigation": "0",
        "sca_count": "0", "derivative_count": "0", "sec_enforcement": "None",
    }
    if not ext or not getattr(ext, "litigation", None):
        return r
    lit = ext.litigation  # type: ignore[union-attr]
    am = sv(getattr(lit, "active_matter_count", None))
    r["active_litigation"] = str(am) if am is not None else "0"
    hm = sv(getattr(lit, "historical_matter_count", None))
    r["historical_litigation"] = str(hm) if hm is not None else "0"
    from do_uw.stages.render.sca_counter import count_active_genuine_scas

    r["sca_count"] = str(count_active_genuine_scas(state))
    r["derivative_count"] = str(len(getattr(lit, "derivative_suits", None) or []))
    if lit.sec_enforcement:
        se = sv(getattr(lit.sec_enforcement, "pipeline_position", None))
        r["sec_enforcement"] = se or "None"
    return r


def _extract_comparison_sector(state: AnalysisState) -> str:
    """Extract sector ETF and industry for comparison context."""
    etf = state.acquired_data.market_data.get("sector_etf", "") if state.acquired_data and state.acquired_data.market_data else ""
    ind = sv(state.company.industry_classification) if state.company and state.company.industry_classification else ""
    parts = ([ind] if ind else []) + ([f"(ETF: {etf})"] if etf else [])
    return " ".join(parts)


def _extract_competitors(state: AnalysisState) -> list[str]:
    """Extract top peer competitors as ticker-name strings."""
    ext = state.extracted
    if not ext or not ext.financials:
        return []
    pg = getattr(ext.financials, "peer_group", None)
    if not pg:
        return []
    peers = getattr(pg, "peers", None) or []
    result = []
    for p in peers[:6]:
        ticker = getattr(p, "ticker", "") or ""
        name = getattr(p, "name", "") or ""
        if ticker:
            short = name.split(",")[0].split(" Inc")[0].split(" Corp")[0] if name else ""
            result.append(f"{ticker} ({short})" if short else ticker)
    return result

__all__ = ["build_key_stats_context"]
