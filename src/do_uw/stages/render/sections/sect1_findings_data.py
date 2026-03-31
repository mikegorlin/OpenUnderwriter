"""State data extraction helpers for executive summary narratives.

Safe accessors that pull real numbers from AnalysisState for use
in narrative builders. All functions return None on missing data
rather than raising exceptions.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.sections.sect1_helpers import (
    safe_auditor,
    safe_governance_field,
    safe_short_interest,
)


def safe_sv(obj: Any, *path: str) -> Any:
    """Walk a dotted path through objects, unwrapping SourcedValues."""
    cur = obj
    for key in path:
        if cur is None:
            return None
        if isinstance(cur, dict):
            cur = cur.get(key)
        else:
            cur = getattr(cur, key, None)
    if cur is not None and hasattr(cur, "value"):
        return cur.value
    return cur


def get_company(state: AnalysisState) -> Any:
    """Return the company profile object."""
    return getattr(state, "company", None)


def get_extracted(state: AnalysisState) -> Any:
    """Return the extracted data object."""
    return getattr(state, "extracted", None)


def subsidiary_count(state: AnalysisState) -> int | None:
    """Get total subsidiary count."""
    comp = get_company(state)
    if comp is None:
        return None
    cnt = safe_sv(comp, "subsidiary_count")
    if cnt is not None:
        return int(cnt)
    ss = getattr(comp, "subsidiary_structure", None)
    if ss is not None:
        total = safe_sv(ss, "total_subsidiaries")
        if total is not None:
            return int(total)
        if isinstance(ss, dict):
            total = ss.get("total_subsidiaries")
            if total is not None:
                return int(total)
    return None


def jurisdiction_count(state: AnalysisState) -> int | None:
    """Get number of jurisdictions from subsidiary structure."""
    comp = get_company(state)
    if comp is None:
        return None
    ss = getattr(comp, "subsidiary_structure", None)
    if ss is None:
        return None
    if isinstance(ss, dict):
        return ss.get("jurisdiction_count")
    return getattr(ss, "jurisdiction_count", None)


def employee_count(state: AnalysisState) -> int | None:
    """Get employee count."""
    comp = get_company(state)
    if comp is None:
        return None
    ec = safe_sv(comp, "employee_count")
    if ec is not None:
        return int(ec)
    return None


def market_cap_billions(state: AnalysisState) -> float | None:
    """Get market cap in billions."""
    comp = get_company(state)
    if comp is None:
        return None
    mc = safe_sv(comp, "market_cap")
    if mc is not None:
        return float(mc) / 1e9
    return None


def company_name(state: AnalysisState) -> str:
    """Get company display name, title-cased from SEC EDGAR all-caps."""
    comp = get_company(state)
    if comp is None:
        return "The company"
    ident = getattr(comp, "identity", None)
    if ident is not None:
        name = safe_sv(ident, "legal_name")
        if name:
            raw = str(name).split("/")[0].strip()
            # If all-caps (SEC EDGAR style), title-case it
            if raw == raw.upper() and len(raw) > 3:
                # Preserve known abbreviations
                _KEEP_UPPER = {"RPM", "IBM", "AMD", "HP", "AT&T"}
                words = raw.title().split()
                result = []
                for w in words:
                    if w.upper() in _KEEP_UPPER:
                        result.append(w.upper())
                    elif w.lower() in ("inc", "corp", "ltd", "llc", "co"):
                        result.append(w + ".")
                    else:
                        result.append(w)
                return " ".join(result)
            return raw
    return "The company"


def bs_line_item(state: AnalysisState, concept: str) -> float | None:
    """Get a balance sheet line item value (most recent period)."""
    return _stmt_line_item(state, "balance_sheet", concept)


def is_line_item(state: AnalysisState, concept: str) -> float | None:
    """Get an income statement line item value (most recent period)."""
    return _stmt_line_item(state, "income_statement", concept)


def _stmt_line_item(
    state: AnalysisState, stmt_key: str, concept: str,
) -> float | None:
    """Get a financial statement line item by xbrl_concept."""
    ext = get_extracted(state)
    if ext is None:
        return None
    fin = getattr(ext, "financials", None)
    if fin is None:
        return None
    stmts = getattr(fin, "statements", None)
    if stmts is None:
        return None
    stmt = (
        stmts.get(stmt_key)
        if isinstance(stmts, dict)
        else getattr(stmts, stmt_key, None)
    )
    if stmt is None:
        return None
    items = (
        stmt.get("line_items")
        if isinstance(stmt, dict)
        else getattr(stmt, "line_items", None)
    )
    if not items or not isinstance(items, list):
        return None
    periods = (
        stmt.get("periods")
        if isinstance(stmt, dict)
        else getattr(stmt, "periods", None)
    )
    if not periods:
        periods = ["FY2025", "FY2024", "FY2023"]
    for item in items:
        xbrl = (
            item.get("xbrl_concept", "")
            if isinstance(item, dict)
            else getattr(item, "xbrl_concept", "")
        )
        if xbrl == concept:
            vals = (
                item.get("values", {})
                if isinstance(item, dict)
                else getattr(item, "values", {})
            )
            if not vals:
                continue
            for period in periods:
                if period in vals:
                    v = vals[period]
                    if isinstance(v, dict):
                        return v.get("value")
                    return getattr(v, "value", v)
    return None


def goodwill_ratio(state: AnalysisState) -> float | None:
    """Compute goodwill as percentage of total assets."""
    goodwill = bs_line_item(state, "goodwill")
    total_assets = bs_line_item(state, "total_assets")
    if goodwill is not None and total_assets and total_assets > 0:
        return goodwill / total_assets * 100
    return None


def litigation_counts(state: AnalysisState) -> dict[str, int]:
    """Count active litigation by type.

    For SCAs, counts only active *genuine* securities class actions
    (excluding non-securities cases misclassified by the LLM extractor).
    Uses the same filter as section_assessments.py for consistency.
    """
    ext = get_extracted(state)
    counts: dict[str, int] = {
        "sca": 0, "derivative": 0, "enforcement": 0, "regulatory": 0,
    }
    if ext is None:
        return counts
    lit = getattr(ext, "litigation", None)
    if lit is None:
        return counts

    # SCAs: canonical active genuine SCA count
    from do_uw.stages.render.sca_counter import count_active_genuine_scas

    counts["sca"] = count_active_genuine_scas(state)

    for key, attr in [
        ("derivative", "derivative_suits"),
        ("enforcement", "sec_enforcement"),
        ("regulatory", "regulatory_actions"),
    ]:
        items = getattr(lit, attr, None)
        if items and isinstance(items, list):
            counts[key] = len(items)
    return counts


def factor_score(
    state: AnalysisState, factor_id: str,
) -> dict[str, Any] | None:
    """Get a factor score dict by factor ID (F1..F10)."""
    scoring = getattr(state, "scoring", None)
    if scoring is None:
        return None
    fs = getattr(scoring, "factor_scores", None)
    if not fs or not isinstance(fs, list):
        return None
    for f in fs:
        fid = (
            f.get("factor_id")
            if isinstance(f, dict)
            else getattr(f, "factor_id", None)
        )
        if fid == factor_id:
            return f if isinstance(f, dict) else f.__dict__
    return None


def triggered_signal_ids(factor: dict[str, Any]) -> list[str]:
    """Get list of triggered signal IDs from a factor score."""
    sigs = factor.get("signal_contributions", [])
    return [
        s.get("signal_id", "")
        for s in sigs
        if isinstance(s, dict) and s.get("status") == "TRIGGERED"
    ]


def board_size(state: AnalysisState) -> int | None:
    """Get board size."""
    val = safe_governance_field(state, "size")
    return int(val) if val is not None else None


def classified_board(state: AnalysisState) -> bool | None:
    """Check if board is classified."""
    ext = get_extracted(state)
    if ext is None:
        return None
    gov = getattr(ext, "governance", None)
    if gov is None:
        return None
    board = getattr(gov, "board", None)
    if board is None:
        return None
    val = getattr(board, "classified_board", None)
    if val is None:
        return None
    if hasattr(val, "value"):
        return val.value
    return val


def going_concern(state: AnalysisState) -> bool | None:
    """Check for going concern qualification."""
    ext = get_extracted(state)
    if ext is None:
        return None
    fin = getattr(ext, "financials", None)
    if fin is None:
        return None
    audit = getattr(fin, "audit", None)
    if audit is None:
        return None
    gc = getattr(audit, "going_concern", None)
    if gc is None:
        return None
    if hasattr(gc, "value"):
        return gc.value
    return gc


def ceo_name(state: AnalysisState) -> str | None:
    """Get CEO name from executives."""
    ext = get_extracted(state)
    if ext is None:
        return None
    gov = getattr(ext, "governance", None)
    if gov is None:
        return None
    leadership = getattr(gov, "leadership", None)
    if leadership is None:
        return None
    execs = getattr(leadership, "executives", None)
    if not execs:
        return None
    for ex in execs:
        title = safe_sv(ex, "title") or ""
        if isinstance(title, str) and (
            "ceo" in title.lower()
            or "chief executive" in title.lower()
        ):
            return safe_sv(ex, "name")
    return None


def fmt_billions(val: float | None) -> str | None:
    """Format a dollar value as human-readable."""
    if val is None:
        return None
    if val >= 1e9:
        return f"${val / 1e9:.1f}B"
    if val >= 1e6:
        return f"${val / 1e6:.0f}M"
    return f"${val:,.0f}"


def stock_decline_pct(state: AnalysisState) -> float | None:
    """Get maximum stock decline percentage from market data."""
    ext = get_extracted(state)
    if ext is None:
        return None
    mkt = getattr(ext, "market", None)
    if mkt is None:
        return None
    stock = getattr(mkt, "stock", None)
    if stock is None:
        return None
    val = safe_sv(stock, "decline_from_high_pct")
    if val is not None:
        return float(val)
    # Compute from high/current if available
    high = safe_sv(stock, "high_52w")
    current = safe_sv(stock, "current_price")
    if high and current and high > 0:
        return (high - current) / high * 100
    return None


def stock_decline_prices(
    state: AnalysisState,
) -> tuple[float, float, int] | None:
    """Return (high_price, low_price, trading_days) for the decline period.

    Returns None if price data is unavailable.
    """
    ext = get_extracted(state)
    if ext is None:
        return None
    mkt = getattr(ext, "market", None)
    if mkt is None:
        return None
    stock = getattr(mkt, "stock", None)
    if stock is None:
        return None
    high = safe_sv(stock, "high_52w")
    current = safe_sv(stock, "current_price")
    if high is None or current is None:
        return None
    # Estimate trading days from 52-week window (approx 252 trading days/year)
    # Use a rough estimate; in real data the decline period varies
    return (float(high), float(current), 252)


def ceo_tenure_years(state: AnalysisState) -> float | None:
    """Get CEO tenure in years from governance leadership."""
    ext = get_extracted(state)
    if ext is None:
        return None
    gov = getattr(ext, "governance", None)
    if gov is None:
        return None
    leadership = getattr(gov, "leadership", None)
    if leadership is None:
        return None
    execs = getattr(leadership, "executives", None)
    if not execs:
        return None
    for ex in execs:
        title = safe_sv(ex, "title") or ""
        if isinstance(title, str) and (
            "ceo" in title.lower() or "chief executive" in title.lower()
        ):
            tenure = getattr(ex, "tenure_years", None)
            if tenure is not None:
                return float(tenure)
    return None


def executive_departure_count(state: AnalysisState) -> int | None:
    """Count recent executive departures from governance leadership."""
    ext = get_extracted(state)
    if ext is None:
        return None
    gov = getattr(ext, "governance", None)
    if gov is None:
        return None
    leadership = getattr(gov, "leadership", None)
    if leadership is None:
        return None
    departures = getattr(leadership, "departures_18mo", None)
    if departures is None:
        return None
    return len(departures)


def scoring_tier(state: AnalysisState) -> str | None:
    """Get the scoring tier label (WIN, WANT, WRITE, etc.)."""
    scoring = getattr(state, "scoring", None)
    if scoring is None:
        return None
    tier = getattr(scoring, "tier", None)
    if tier is None:
        return None
    t = getattr(tier, "tier", None)
    if t is None:
        return None
    if hasattr(t, "value"):
        return str(t.value)
    return str(t)


def beneish_m_score(state: AnalysisState) -> float | None:
    """Get Beneish M-Score from distress indicators."""
    ext = get_extracted(state)
    if ext is None:
        return None
    fin = getattr(ext, "financials", None)
    if fin is None:
        return None
    di = getattr(fin, "distress", None)
    if di is None:
        return None
    bm = getattr(di, "beneish_m_score", None)
    if bm is None:
        return None
    return getattr(bm, "score", None)


def piotroski_score(state: AnalysisState) -> int | None:
    """Get Piotroski F-Score from distress indicators."""
    ext = get_extracted(state)
    if ext is None:
        return None
    fin = getattr(ext, "financials", None)
    if fin is None:
        return None
    di = getattr(fin, "distress", None)
    if di is None:
        return None
    pf = getattr(di, "piotroski_f_score", None)
    if pf is None:
        return None
    score = getattr(pf, "score", None)
    return int(score) if score is not None else None


def credibility_score(state: AnalysisState) -> float | None:
    """Get management credibility beat-rate percentage."""
    fl = getattr(state, "forward_looking", None)
    if fl is None:
        return None
    cred = getattr(fl, "credibility", None)
    if cred is None:
        return None
    return getattr(cred, "beat_rate_pct", None)


def guidance_miss_count(state: AnalysisState) -> int | None:
    """Count quarters where guidance was missed."""
    fl = getattr(state, "forward_looking", None)
    if fl is None:
        return None
    cred = getattr(fl, "credibility", None)
    if cred is None:
        return None
    records = getattr(cred, "quarter_records", None)
    if not records:
        # Fall back to inferring from beat rate and total quarters
        total = getattr(cred, "quarters_assessed", 0)
        beat_pct = getattr(cred, "beat_rate_pct", 0)
        if total > 0:
            misses = total - round(total * beat_pct / 100)
            return misses if misses > 0 else 0
        return None
    return sum(
        1 for r in records
        if getattr(r, "beat_or_miss", "") == "MISS"
    )


def ddl_estimate(
    state: AnalysisState, decline_pct: float | None = None,
) -> float | None:
    """Get DDL exposure in billions from the authoritative source.

    Uses the volume-weighted DDL from ddl_context.py as the single
    authoritative value. This is the same number shown on the scorecard
    DDL strip, ensuring narrative text matches.

    Falls back to severity model damages_estimate if price history
    is unavailable for volume-weighted calculation.

    Returns value in billions, or None if unavailable.
    """
    # Priority 1: ddl_context volume-weighted calculation (matches scorecard strip)
    try:
        from do_uw.stages.render.context_builders.ddl_context import (
            build_ddl_context,
        )
        ddl_ctx = build_ddl_context(state)
        if ddl_ctx.get("has_exposure") and ddl_ctx.get("primary"):
            ddl_raw = ddl_ctx["primary"].get("ddl_raw")
            if ddl_raw is not None and ddl_raw > 0:
                return float(ddl_raw) / 1e9
    except Exception:
        pass

    # Priority 2: severity model damages_estimate
    scoring = getattr(state, "scoring", None)
    if scoring is not None:
        sr = getattr(scoring, "severity_result", None)
        if sr is not None:
            primary = getattr(sr, "primary", None)
            if primary is not None:
                damages = getattr(primary, "damages_estimate", None)
                if damages is not None and damages > 0:
                    return float(damages) / 1e9

    return None


def revenue_trend(state: AnalysisState) -> str | None:
    """Determine revenue trend from multi-period data: 'growing', 'declining', or 'flat'."""
    ext = get_extracted(state)
    if ext is None:
        return None
    fin = getattr(ext, "financials", None)
    if fin is None:
        return None
    stmts = getattr(fin, "statements", None)
    if stmts is None:
        return None
    inc = (
        stmts.get("income_statement")
        if isinstance(stmts, dict)
        else getattr(stmts, "income_statement", None)
    )
    if inc is None:
        return None
    items = (
        inc.get("line_items")
        if isinstance(inc, dict)
        else getattr(inc, "line_items", None)
    )
    if not items:
        return None
    for item in items:
        xbrl = (
            item.get("xbrl_concept", "")
            if isinstance(item, dict)
            else getattr(item, "xbrl_concept", "")
        )
        if xbrl == "total_revenue":
            vals = (
                item.get("values", {})
                if isinstance(item, dict)
                else getattr(item, "values", {})
            )
            if not vals:
                continue
            # Extract values in period order
            amounts: list[float] = []
            for _period in sorted(vals.keys()):
                v = vals[_period]
                if isinstance(v, dict):
                    val = v.get("value")
                else:
                    val = getattr(v, "value", v)
                if val is not None:
                    amounts.append(float(val))
            if len(amounts) >= 2:
                if amounts[-1] > amounts[0] * 1.02:
                    return "growing"
                elif amounts[-1] < amounts[0] * 0.98:
                    return "declining"
                else:
                    return "flat"
    return None


def short_interest_pct(state: AnalysisState) -> float | None:
    """Get short interest percentage of float. Re-export for consistency."""
    return safe_short_interest(state)


__all__ = [
    "board_size",
    "beneish_m_score",
    "bs_line_item",
    "ceo_name",
    "ceo_tenure_years",
    "classified_board",
    "company_name",
    "credibility_score",
    "ddl_estimate",
    "employee_count",
    "executive_departure_count",
    "factor_score",
    "fmt_billions",
    "going_concern",
    "goodwill_ratio",
    "guidance_miss_count",
    "is_line_item",
    "jurisdiction_count",
    "litigation_counts",
    "market_cap_billions",
    "piotroski_score",
    "revenue_trend",
    "scoring_tier",
    "short_interest_pct",
    "stock_decline_pct",
    "stock_decline_prices",
    "subsidiary_count",
    "triggered_signal_ids",
]
