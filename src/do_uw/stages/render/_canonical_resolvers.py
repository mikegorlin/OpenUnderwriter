"""Individual metric resolvers for the canonical metrics registry.

Each resolver function takes an AnalysisState and returns a MetricValue.
Follows XBRL-first source priority: XBRL > state fields > yfinance > fallback.

Financial resolvers (income statement, balance sheet) are in _canonical_resolvers_fin.py.
This module contains: identity, market, scoring resolvers and shared helpers.

Split from canonical_metrics.py to keep files under 500 lines per CLAUDE.md.
"""

from __future__ import annotations

import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float
from do_uw.stages.render.canonical_metrics import MetricValue


# ---------------------------------------------------------------------------
# Shared helpers (used by both resolver modules)
# ---------------------------------------------------------------------------


def _sv(obj: Any) -> Any:
    """Unwrap SourcedValue to its primitive .value, or return raw."""
    if obj is None:
        return None
    return getattr(obj, "value", obj)


def _xbrl_line_item(
    state: AnalysisState,
    stmt_attr: str,
    field_names: tuple[str, ...],
) -> tuple[float | None, str]:
    """Extract a value from XBRL financial statements.

    Navigates state.extracted.financials.statements -> stmt_attr -> line_items
    to find the first matching field name from field_names.

    Returns (value, period_label) or (None, "").
    """
    ext = state.extracted
    if not ext or not getattr(ext, "financials", None):
        return None, ""
    fin = ext.financials
    if fin is None:
        return None, ""
    stmts = fin.statements
    if stmts is None:
        return None, ""
    stmt = getattr(stmts, stmt_attr, None)
    if stmt is None:
        return None, ""

    for term in field_names:
        for li in stmt.line_items or []:
            label_normalized = li.label.lower().replace(" ", "_")
            if term in label_normalized:
                if isinstance(li.values, dict) and li.values:
                    period_key = next(iter(li.values.keys()))
                    v = li.values[period_key]
                    if v is not None:
                        raw = v.value if hasattr(v, "value") else v
                        val = safe_float(raw, None)
                        if val is not None:
                            return val, period_key
    return None, ""


def _xbrl_fiscal_year(period_key: str) -> str:
    """Extract fiscal year from period key like 'FY2025' or '2024-09-28'."""
    if not period_key:
        return ""
    m = re.search(r"(\d{4})", period_key)
    return f"FY{m.group(1)}" if m else period_key


def _yfinance_info(state: AnalysisState) -> dict[str, Any]:
    """Extract yfinance info dict from acquired market data."""
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            return md.get("info", {})
        if hasattr(md, "info"):
            return getattr(md, "info", {}) or {}
    return {}


# ---------------------------------------------------------------------------
# Identity resolvers
# ---------------------------------------------------------------------------


def resolve_company_name(state: AnalysisState) -> MetricValue:
    """Company legal name from state."""
    if state.company and state.company.identity:
        name = _sv(state.company.identity.legal_name)
        if name:
            return MetricValue(
                raw=str(name), formatted=str(name),
                source="sec:edgar", confidence="HIGH", as_of="current",
            )
    info = _yfinance_info(state)
    yf_name = info.get("longName") or info.get("shortName")
    if yf_name:
        return MetricValue(
            raw=str(yf_name), formatted=str(yf_name),
            source="yfinance:info", confidence="MEDIUM", as_of="current",
        )
    return MetricValue()


def resolve_ticker(state: AnalysisState) -> MetricValue:
    """Ticker from state."""
    if state.ticker:
        return MetricValue(
            raw=state.ticker, formatted=state.ticker,
            source="input", confidence="HIGH", as_of="current",
        )
    return MetricValue()


def resolve_sic_code(state: AnalysisState) -> MetricValue:
    """SIC code from company identity."""
    if state.company and state.company.identity:
        sic = _sv(state.company.identity.sic_code)
        if sic:
            return MetricValue(
                raw=str(sic), formatted=str(sic),
                source="sec:edgar", confidence="HIGH", as_of="current",
            )
    return MetricValue()


def resolve_sic_description(state: AnalysisState) -> MetricValue:
    """SIC description from company identity."""
    if state.company and state.company.identity:
        desc = _sv(state.company.identity.sic_description)
        if desc:
            return MetricValue(
                raw=str(desc), formatted=str(desc),
                source="sec:edgar", confidence="HIGH", as_of="current",
            )
    return MetricValue()


def resolve_exchange(state: AnalysisState) -> MetricValue:
    """state.company.identity.exchange (SourcedValue) > yfinance exchange."""
    if state.company and state.company.identity:
        ex = _sv(state.company.identity.exchange)
        if ex:
            return MetricValue(
                raw=str(ex), formatted=str(ex),
                source="sec:edgar", confidence="HIGH", as_of="current",
            )
    info = _yfinance_info(state)
    yf_ex = info.get("exchange")
    if yf_ex:
        return MetricValue(
            raw=str(yf_ex), formatted=str(yf_ex),
            source="yfinance:info", confidence="MEDIUM", as_of="current",
        )
    return MetricValue()


def resolve_ceo_name(state: AnalysisState) -> MetricValue:
    """ECD ceo_name > scan executives list for CEO title."""
    ext = state.extracted
    if ext and ext.governance:
        gov = ext.governance
        ecd = getattr(gov, "ecd", {}) or {}
        ceo = _sv(ecd.get("ceo_name"))
        if ceo and str(ceo).strip():
            return MetricValue(
                raw=str(ceo), formatted=str(ceo),
                source="sec:DEF14A:ecd", confidence="HIGH", as_of="latest proxy",
            )
        leadership = getattr(gov, "leadership", None)
        if leadership:
            for ex in getattr(leadership, "executives", []) or []:
                title = str(_sv(getattr(ex, "title", None)) or "").lower()
                if "ceo" in title or "chief executive" in title:
                    name = _sv(getattr(ex, "name", None))
                    if name:
                        return MetricValue(
                            raw=str(name), formatted=str(name),
                            source="sec:DEF14A:officers", confidence="HIGH",
                            as_of="latest proxy",
                        )
    return MetricValue()


def resolve_employees(state: AnalysisState) -> MetricValue:
    """state.company.employee_count (SourcedValue) > yfinance fullTimeEmployees."""
    if state.company and state.company.employee_count:
        emp = _sv(state.company.employee_count)
        if emp is not None:
            v = int(safe_float(emp, 0))
            if v > 0:
                return MetricValue(
                    raw=v, formatted=f"{v:,}",
                    source="sec:10-K", confidence="HIGH", as_of="latest filing",
                )
    info = _yfinance_info(state)
    yf_emp = info.get("fullTimeEmployees")
    if yf_emp is not None:
        v = int(safe_float(yf_emp, 0))
        if v > 0:
            return MetricValue(
                raw=v, formatted=f"{v:,}",
                source="yfinance:info", confidence="MEDIUM", as_of="current",
            )
    return MetricValue()


# ---------------------------------------------------------------------------
# Market resolvers
# ---------------------------------------------------------------------------


def resolve_stock_price(state: AnalysisState) -> MetricValue:
    """state.extracted.market.stock.current_price > yfinance currentPrice."""
    ext = state.extracted
    if ext and ext.market and ext.market.stock:
        cp = _sv(ext.market.stock.current_price)
        if cp is not None:
            v = safe_float(cp, None)
            if v is not None and v > 0:
                return MetricValue(
                    raw=v, formatted=f"${v:,.2f}",
                    source="market:stock", confidence="MEDIUM", as_of="current",
                )
    info = _yfinance_info(state)
    yf_price = info.get("currentPrice") or info.get("previousClose")
    if yf_price is not None:
        v = safe_float(yf_price, None)
        if v is not None and v > 0:
            return MetricValue(
                raw=v, formatted=f"${v:,.2f}",
                source="yfinance:info", confidence="MEDIUM", as_of="current",
            )
    return MetricValue()


def resolve_high_52w(state: AnalysisState) -> MetricValue:
    """52-week high from extracted market data."""
    ext = state.extracted
    if ext and ext.market and ext.market.stock:
        h = _sv(ext.market.stock.high_52w)
        if h is not None:
            v = safe_float(h, None)
            if v is not None and v > 0:
                return MetricValue(
                    raw=v, formatted=f"${v:,.2f}",
                    source="market:stock", confidence="MEDIUM", as_of="trailing 52w",
                )
    info = _yfinance_info(state)
    yf_h = info.get("fiftyTwoWeekHigh")
    if yf_h is not None:
        v = safe_float(yf_h, None)
        if v is not None and v > 0:
            return MetricValue(
                raw=v, formatted=f"${v:,.2f}",
                source="yfinance:info", confidence="MEDIUM", as_of="trailing 52w",
            )
    return MetricValue()


def resolve_low_52w(state: AnalysisState) -> MetricValue:
    """52-week low from extracted market data."""
    ext = state.extracted
    if ext and ext.market and ext.market.stock:
        lo = _sv(ext.market.stock.low_52w)
        if lo is not None:
            v = safe_float(lo, None)
            if v is not None and v > 0:
                return MetricValue(
                    raw=v, formatted=f"${v:,.2f}",
                    source="market:stock", confidence="MEDIUM", as_of="trailing 52w",
                )
    info = _yfinance_info(state)
    yf_l = info.get("fiftyTwoWeekLow")
    if yf_l is not None:
        v = safe_float(yf_l, None)
        if v is not None and v > 0:
            return MetricValue(
                raw=v, formatted=f"${v:,.2f}",
                source="yfinance:info", confidence="MEDIUM", as_of="trailing 52w",
            )
    return MetricValue()


def resolve_market_cap(state: AnalysisState) -> MetricValue:
    """state.company.market_cap (SourcedValue) > yfinance marketCap."""
    from do_uw.stages.render.context_builders._key_stats_helpers import fmt_large_number

    if state.company and state.company.market_cap:
        mc_raw = _sv(state.company.market_cap)
        if mc_raw is not None:
            v = safe_float(mc_raw, None)
            if v is not None:
                src_obj = state.company.market_cap
                src = getattr(src_obj, "source", "company_profile") if src_obj else "company_profile"
                return MetricValue(
                    raw=v, formatted=fmt_large_number(v),
                    source=f"sec:{src}" if not str(src).startswith(("sec:", "yfinance:")) else str(src),
                    confidence="MEDIUM", as_of="current",
                )
    info = _yfinance_info(state)
    yf_mc = info.get("marketCap")
    if yf_mc is not None:
        v = safe_float(yf_mc, None)
        if v is not None:
            return MetricValue(
                raw=v, formatted=fmt_large_number(v),
                source="yfinance:info", confidence="MEDIUM", as_of="current",
            )
    return MetricValue()


def resolve_beta(state: AnalysisState) -> MetricValue:
    """Beta from yfinance info."""
    info = _yfinance_info(state)
    yf_beta = info.get("beta")
    if yf_beta is not None:
        v = safe_float(yf_beta, None)
        if v is not None:
            return MetricValue(
                raw=round(v, 2), formatted=f"{v:.2f}",
                source="yfinance:info", confidence="MEDIUM", as_of="current",
            )
    return MetricValue()


# ---------------------------------------------------------------------------
# Scoring resolvers
# ---------------------------------------------------------------------------


def resolve_overall_score(state: AnalysisState) -> MetricValue:
    """Overall quality score from scoring."""
    if state.scoring:
        qs = state.scoring.quality_score
        if qs is not None:
            return MetricValue(
                raw=round(qs, 1), formatted=f"{qs:.0f}/100",
                source="scoring:engine", confidence="HIGH", as_of="current analysis",
            )
    return MetricValue()


def resolve_tier(state: AnalysisState) -> MetricValue:
    """Tier classification from scoring."""
    if state.scoring and state.scoring.tier:
        t = state.scoring.tier
        tier_name = getattr(t, "tier", None)
        if tier_name:
            tier_str = str(tier_name.value) if hasattr(tier_name, "value") else str(tier_name)
            return MetricValue(
                raw=tier_str, formatted=tier_str,
                source="scoring:engine", confidence="HIGH", as_of="current analysis",
            )
    return MetricValue()
