"""Shared utilities for underwriting question answerers.

Extracted from screening_answers.py and uw_questions.py for reuse
across all domain answerer modules.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.formatters import safe_float


def sv(val: Any) -> Any:
    """Extract .value from SourcedValue or return as-is."""
    return val.value if hasattr(val, "value") else val


def fmt_currency(val: float | None, compact: bool = True) -> str:
    """Format a number as "$X.XB" / "$X.XM" / "$X.XK"."""
    if val is None:
        return "N/A"
    if compact:
        if abs(val) >= 1e12:
            return f"${val / 1e12:.1f}T"
        if abs(val) >= 1e9:
            return f"${val / 1e9:.1f}B"
        if abs(val) >= 1e6:
            return f"${val / 1e6:.1f}M"
        if abs(val) >= 1e3:
            return f"${val / 1e3:.0f}K"
    return f"${val:,.0f}"


def fmt_pct(val: float | None) -> str:
    """Format as 'X.X%'."""
    if val is None:
        return "N/A"
    return f"{val:.1f}%" if abs(val) < 100 else f"{val:,.0f}%"


def safe_float_extract(val: Any, default: float | None = None) -> float | None:
    """Wraps safe_float for answerer use — returns None instead of 0 on failure."""
    if val is None:
        return default
    result = safe_float(val, default=float("nan"))
    if result != result:  # NaN check  # noqa: PLR0124
        return default
    return result


def yf_info(ctx: dict[str, Any]) -> dict[str, Any]:
    """Get yfinance info dict from context state."""
    state = ctx.get("_state")
    if not state:
        return {}
    mkt_data = getattr(state.acquired_data, "market_data", None) or {}
    return mkt_data.get("info", {}) if isinstance(mkt_data, dict) else {}


def signal_results(ctx: dict[str, Any]) -> dict[str, Any]:
    """Get signal_results dict from state analysis or scoring."""
    state = ctx.get("_state")
    if not state:
        return {}
    # Try analysis.disposition_summary first
    if state.analysis and hasattr(state.analysis, "disposition_summary"):
        ds = state.analysis.disposition_summary
        if isinstance(ds, dict) and "signal_results" in ds:
            return ds["signal_results"]
    # Try scoring
    if state.scoring and hasattr(state.scoring, "signal_results"):
        sr = getattr(state.scoring, "signal_results", None)
        if isinstance(sr, dict):
            return sr
    return {}


def triggered_signals(ctx: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    """Get triggered checks from ctx, optionally filtered by signal_id prefix."""
    checks = ctx.get("triggered_checks", [])
    if not prefix:
        return [c for c in checks if isinstance(c, dict)]
    return [
        c
        for c in checks
        if isinstance(c, dict) and str(c.get("signal_id", "")).lower().startswith(prefix.lower())
    ]


def suggest_filing_reference(data_sources: list[str]) -> str:
    """Suggest which filing to check for missing data."""
    refs: list[str] = []
    for ds in data_sources:
        ds_lower = ds.lower()
        if "governance" in ds_lower or "board" in ds_lower:
            refs.append("DEF 14A proxy statement")
        elif "financial" in ds_lower or "revenue" in ds_lower:
            refs.append("10-K Annual Report")
        elif "litigation" in ds_lower or "sca" in ds_lower:
            refs.append("10-K Item 3 Legal Proceedings")
        elif "risk_factor" in ds_lower:
            refs.append("10-K Item 1A Risk Factors")
        elif "sec_filing" in ds_lower:
            refs.append("SEC EDGAR filing history")
        elif "yfinance" in ds_lower or "market" in ds_lower:
            refs.append("Market data provider")
        elif "supabase" in ds_lower:
            refs.append("GorlinBase claims database")
        elif "scoring" in ds_lower:
            refs.append("Pipeline scoring output")
        elif "benchmark" in ds_lower or "peer" in ds_lower:
            refs.append("Peer benchmark data")
        elif "analysis" in ds_lower or "signal" in ds_lower:
            refs.append("Pipeline signal analysis")
    return "; ".join(dict.fromkeys(refs)) if refs else "Check 10-K and proxy statement"


def partial_answer(
    answer: str,
    missing: str,
    filing_ref: str,
) -> dict[str, Any]:
    """Build an answer dict with inline 'Needs Review' flag per D-01.

    Returns a partial answer with the data we have plus a flag for what's missing.
    """
    flagged = f"{answer} [Needs Review: {missing} — check {filing_ref}]"
    return {
        "answer": flagged,
        "verdict": "NEUTRAL",
        "confidence": "LOW",
        "data_found": True,
    }


def no_data() -> dict[str, Any]:
    """Standard NO_DATA response."""
    return {
        "answer": "",
        "evidence": [],
        "verdict": "NO_DATA",
        "confidence": "LOW",
        "data_found": False,
    }
