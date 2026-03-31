"""Financial metric resolvers for the canonical metrics registry.

XBRL balance sheet and income statement resolvers that extract values
with XBRL-first source priority and yfinance fallback.

Split from _canonical_resolvers.py to keep files under 500 lines per CLAUDE.md.
"""

from __future__ import annotations

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._key_stats_helpers import (
    fmt_large_number,
)
from do_uw.stages.render.formatters import safe_float
from do_uw.stages.render.canonical_metrics import MetricValue
from do_uw.stages.render._canonical_resolvers import (
    _sv,
    _xbrl_fiscal_year,
    _xbrl_line_item,
    _yfinance_info,
)


# ---------------------------------------------------------------------------
# Income statement resolvers
# ---------------------------------------------------------------------------


def resolve_revenue(state: AnalysisState) -> MetricValue:
    """XBRL income_statement > yfinance totalRevenue."""
    val, period = _xbrl_line_item(
        state, "income_statement", ("total_revenue", "revenue", "net_sales")
    )
    if val is not None:
        fy = _xbrl_fiscal_year(period)
        return MetricValue(
            raw=val, formatted=fmt_large_number(val),
            source=f"xbrl:10-K:{fy}", confidence="HIGH", as_of=fy,
        )
    info = _yfinance_info(state)
    yf_rev = info.get("totalRevenue")
    if yf_rev is not None:
        v = safe_float(yf_rev, None)
        if v is not None:
            return MetricValue(
                raw=v, formatted=fmt_large_number(v),
                source="yfinance:info", confidence="MEDIUM", as_of="TTM",
            )
    return MetricValue()


def resolve_net_income(state: AnalysisState) -> MetricValue:
    """XBRL income_statement > yfinance netIncomeToCommon."""
    val, period = _xbrl_line_item(
        state, "income_statement", ("net_income", "net_income_loss")
    )
    if val is not None:
        fy = _xbrl_fiscal_year(period)
        return MetricValue(
            raw=val, formatted=fmt_large_number(val),
            source=f"xbrl:10-K:{fy}", confidence="HIGH", as_of=fy,
        )
    info = _yfinance_info(state)
    yf_ni = info.get("netIncomeToCommon")
    if yf_ni is not None:
        v = safe_float(yf_ni, None)
        if v is not None:
            return MetricValue(
                raw=v, formatted=fmt_large_number(v),
                source="yfinance:info", confidence="MEDIUM", as_of="TTM",
            )
    return MetricValue()


def resolve_revenue_growth(state: AnalysisState) -> MetricValue:
    """Derive from multi-period XBRL revenue > yfinance revenueGrowth."""
    ext = state.extracted
    if ext and getattr(ext, "financials", None):
        fin = ext.financials
        if fin and fin.statements:
            stmt = getattr(fin.statements, "income_statement", None)
            if stmt and stmt.line_items:
                for term in ("total_revenue", "revenue", "net_sales"):
                    for li in stmt.line_items:
                        label_normalized = li.label.lower().replace(" ", "_")
                        if term in label_normalized and isinstance(li.values, dict) and len(li.values) >= 2:
                            period_keys = list(li.values.keys())
                            v_current = li.values.get(period_keys[0])
                            v_prior = li.values.get(period_keys[1])
                            cur = safe_float(_sv(v_current), None) if v_current else None
                            pri = safe_float(_sv(v_prior), None) if v_prior else None
                            if cur and pri and pri != 0:
                                growth = ((cur - pri) / abs(pri)) * 100
                                fy = _xbrl_fiscal_year(period_keys[0])
                                return MetricValue(
                                    raw=round(growth, 1),
                                    formatted=f"{growth:+.1f}%",
                                    source=f"xbrl:10-K:{fy}",
                                    confidence="HIGH",
                                    as_of=fy,
                                )
                            break
                    else:
                        continue
                    break

    info = _yfinance_info(state)
    yf_growth = info.get("revenueGrowth")
    if yf_growth is not None:
        v = safe_float(yf_growth, None)
        if v is not None:
            pct = v * 100
            return MetricValue(
                raw=round(pct, 1), formatted=f"{pct:+.1f}%",
                source="yfinance:info", confidence="MEDIUM", as_of="TTM",
            )
    return MetricValue()


# ---------------------------------------------------------------------------
# Balance sheet resolvers
# ---------------------------------------------------------------------------


def resolve_total_assets(state: AnalysisState) -> MetricValue:
    """XBRL balance_sheet > yfinance totalAssets."""
    val, period = _xbrl_line_item(state, "balance_sheet", ("total_assets",))
    if val is not None:
        fy = _xbrl_fiscal_year(period)
        return MetricValue(
            raw=val, formatted=fmt_large_number(val),
            source=f"xbrl:10-K:{fy}", confidence="HIGH", as_of=fy,
        )
    info = _yfinance_info(state)
    yf_ta = info.get("totalAssets")
    if yf_ta is not None:
        v = safe_float(yf_ta, None)
        if v is not None:
            return MetricValue(
                raw=v, formatted=fmt_large_number(v),
                source="yfinance:info", confidence="MEDIUM", as_of="TTM",
            )
    return MetricValue()


def resolve_total_liabilities(state: AnalysisState) -> MetricValue:
    """XBRL balance_sheet total_liabilities."""
    val, period = _xbrl_line_item(state, "balance_sheet", ("total_liabilities",))
    if val is not None:
        fy = _xbrl_fiscal_year(period)
        return MetricValue(
            raw=val, formatted=fmt_large_number(val),
            source=f"xbrl:10-K:{fy}", confidence="HIGH", as_of=fy,
        )
    return MetricValue()


def resolve_total_debt(state: AnalysisState) -> MetricValue:
    """XBRL balance_sheet > yfinance totalDebt."""
    val, period = _xbrl_line_item(
        state, "balance_sheet", ("long_term_debt", "total_debt", "long-term_debt")
    )
    if val is not None:
        fy = _xbrl_fiscal_year(period)
        return MetricValue(
            raw=val, formatted=fmt_large_number(val),
            source=f"xbrl:10-K:{fy}", confidence="HIGH", as_of=fy,
        )
    info = _yfinance_info(state)
    yf_td = info.get("totalDebt")
    if yf_td is not None:
        v = safe_float(yf_td, None)
        if v is not None:
            return MetricValue(
                raw=v, formatted=fmt_large_number(v),
                source="yfinance:info", confidence="MEDIUM", as_of="TTM",
            )
    return MetricValue()


def resolve_cash(state: AnalysisState) -> MetricValue:
    """XBRL balance_sheet cash > yfinance totalCash."""
    val, period = _xbrl_line_item(
        state, "balance_sheet", ("cash_and_equivalents", "cash_and_cash_equivalents", "cash")
    )
    if val is not None:
        fy = _xbrl_fiscal_year(period)
        return MetricValue(
            raw=val, formatted=fmt_large_number(val),
            source=f"xbrl:10-K:{fy}", confidence="HIGH", as_of=fy,
        )
    info = _yfinance_info(state)
    yf_cash = info.get("totalCash")
    if yf_cash is not None:
        v = safe_float(yf_cash, None)
        if v is not None:
            return MetricValue(
                raw=v, formatted=fmt_large_number(v),
                source="yfinance:info", confidence="MEDIUM", as_of="TTM",
            )
    return MetricValue()


def resolve_shares_outstanding(state: AnalysisState) -> MetricValue:
    """XBRL balance_sheet > yfinance sharesOutstanding."""
    val, period = _xbrl_line_item(
        state, "balance_sheet",
        ("shares_outstanding", "common_shares_outstanding", "common_stock_shares_outstanding"),
    )
    if val is not None:
        formatted = f"{val / 1e9:.2f}B" if val >= 1e9 else f"{val / 1e6:.0f}M"
        fy = _xbrl_fiscal_year(period)
        return MetricValue(
            raw=val, formatted=formatted,
            source=f"xbrl:10-K:{fy}", confidence="HIGH", as_of=fy,
        )
    info = _yfinance_info(state)
    yf_shares = info.get("sharesOutstanding")
    if yf_shares is not None:
        v = safe_float(yf_shares, None)
        if v is not None and v > 0:
            formatted = f"{v / 1e9:.2f}B" if v >= 1e9 else f"{v / 1e6:.0f}M"
            return MetricValue(
                raw=v, formatted=formatted,
                source="yfinance:info", confidence="MEDIUM", as_of="current",
            )
    return MetricValue()
