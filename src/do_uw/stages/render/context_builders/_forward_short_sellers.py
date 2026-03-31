"""Short-seller report detection and conviction label builder.

Scans existing web search results for named short-seller firm reports
and derives conviction direction from short interest trend data.

Phase 136: Forward-Looking and Integration
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Named short-seller firms to monitor
# ---------------------------------------------------------------------------

SHORT_SELLER_FIRMS: list[str] = [
    "Citron Research",
    "Hindenburg Research",
    "Spruce Point Capital",
    "Muddy Waters Research",
    "Kerrisdale Capital",
]

# Keywords that should co-occur to reduce false positives
_REPORT_KEYWORDS = {"report", "short", "target", "fraud", "overvalued", "sell"}

_CONVICTION_COLOR: dict[str, str] = {
    "Rising": "#DC2626",
    "Stable": "#D97706",
    "Declining": "#16A34A",
}


def _scan_results_dict(
    results_dict: dict[str, Any],
    ticker: str,
    company_name: str,
) -> list[dict[str, Any]]:
    """Scan a results dict for short-seller firm mentions with co-occurrence."""
    reports: list[dict[str, Any]] = []
    if not isinstance(results_dict, dict):
        return reports

    # Collect all search result entries
    all_entries: list[dict[str, Any]] = []
    for _key, val in results_dict.items():
        if isinstance(val, dict):
            entries = val.get("results", [])
            if isinstance(entries, list):
                all_entries.extend(
                    e for e in entries if isinstance(e, dict)
                )
            # Also check if val itself looks like a result
            if "title" in val or "snippet" in val:
                all_entries.append(val)
        elif isinstance(val, list):
            all_entries.extend(
                e for e in val if isinstance(e, dict)
            )

    ticker_lower = ticker.lower()
    company_lower = company_name.lower()

    for entry in all_entries:
        title = str(entry.get("title", "")).lower()
        snippet = str(entry.get("snippet", "")).lower()
        url = str(entry.get("url", ""))
        combined = f"{title} {snippet}"

        # Check for company co-occurrence
        has_company = ticker_lower in combined or company_lower in combined
        if not has_company:
            continue

        # Check for firm name AND report keywords
        for firm in SHORT_SELLER_FIRMS:
            if firm.lower() in combined:
                # Require at least one report keyword
                has_keyword = any(kw in combined for kw in _REPORT_KEYWORDS)
                if has_keyword:
                    reports.append({
                        "firm": firm,
                        "title": entry.get("title", "Unknown"),
                        "date": entry.get("date", "Unknown"),
                        "url": url,
                        "summary": entry.get("snippet", ""),
                    })

    return reports


def build_short_seller_alerts(state: AnalysisState) -> dict[str, Any]:
    """Detect short-seller reports from named firms in web search results.

    Scans acquired_data for web search results where a named short-seller
    firm AND the company ticker/name co-occur.

    Returns:
        Dict with alerts_available, reports list, report_count,
        firms_checked.
    """
    ticker = ""
    company_name = ""
    if state.company:
        ticker = getattr(state.company, "ticker", "") or ""
        company_name = getattr(state.company, "company_name", "") or ""

    reports: list[dict[str, Any]] = []

    if state.acquired_data:
        ad = state.acquired_data

        # Scan web_search_results
        if isinstance(ad.web_search_results, dict):
            reports.extend(_scan_results_dict(ad.web_search_results, ticker, company_name))

        # Scan blind_spot_results
        if isinstance(ad.blind_spot_results, dict):
            reports.extend(_scan_results_dict(ad.blind_spot_results, ticker, company_name))

    # Deduplicate by firm + title
    seen: set[str] = set()
    unique_reports: list[dict[str, Any]] = []
    for r in reports:
        key = f"{r['firm']}|{r.get('title', '')}"
        if key not in seen:
            seen.add(key)
            unique_reports.append(r)

    return {
        "alerts_available": len(unique_reports) > 0,
        "reports": unique_reports,
        "report_count": len(unique_reports),
        "firms_checked": list(SHORT_SELLER_FIRMS),
    }


def derive_short_conviction(state: AnalysisState) -> dict[str, Any]:
    """Derive short interest conviction direction from trend data.

    Uses shares_short vs shares_short_prior for percentage change:
    - >10% increase = Rising
    - >10% decrease = Declining
    - Within +/- 10% = Stable

    Falls back to trend_6m text when share counts unavailable.

    Returns:
        Dict with conviction, conviction_color, conviction_rationale,
        short_pct, days_to_cover, shares_short, shares_short_prior,
        pct_change.
    """
    si = None
    if state.extracted and state.extracted.market:
        si = state.extracted.market.short_interest

    if si is None:
        return {
            "conviction": "Stable",
            "conviction_color": _CONVICTION_COLOR["Stable"],
            "conviction_rationale": "No short interest data available.",
            "short_pct": None,
            "days_to_cover": None,
            "shares_short": None,
            "shares_short_prior": None,
            "pct_change": None,
        }

    # Extract values from SourcedValue wrappers
    def _sv_val(sv: Any, default: Any = None) -> Any:
        if sv is None:
            return default
        return getattr(sv, "value", sv)

    current = _sv_val(si.shares_short)
    prior = _sv_val(si.shares_short_prior)
    trend_6m = _sv_val(si.trend_6m, "")
    short_pct = _sv_val(si.short_pct_float)
    dtc = _sv_val(si.days_to_cover)

    current_int = int(safe_float(current, 0)) if current is not None else None
    prior_int = int(safe_float(prior, 0)) if prior is not None else None
    short_pct_float = safe_float(short_pct, None) if short_pct is not None else None
    days_to_cover_float = safe_float(dtc, None) if dtc is not None else None

    conviction = "Stable"
    rationale = ""
    pct_change: float | None = None

    if current_int is not None and prior_int is not None and prior_int > 0:
        pct_change = (current_int - prior_int) / prior_int
        if pct_change > 0.10:
            conviction = "Rising"
            rationale = (
                f"Short interest increased {pct_change:.1%} "
                f"({prior_int:,} to {current_int:,} shares)."
            )
        elif pct_change < -0.10:
            conviction = "Declining"
            rationale = (
                f"Short interest decreased {abs(pct_change):.1%} "
                f"({prior_int:,} to {current_int:,} shares)."
            )
        else:
            conviction = "Stable"
            rationale = (
                f"Short interest changed {pct_change:+.1%} "
                f"({prior_int:,} to {current_int:,} shares), within normal range."
            )
    elif trend_6m:
        trend_upper = str(trend_6m).upper()
        if "UP" in trend_upper or "INCREAS" in trend_upper or "RISING" in trend_upper:
            conviction = "Rising"
            rationale = f"6-month trend indicates rising short interest ({trend_6m})."
        elif "DOWN" in trend_upper or "DECREAS" in trend_upper or "DECLINING" in trend_upper:
            conviction = "Declining"
            rationale = f"6-month trend indicates declining short interest ({trend_6m})."
        else:
            conviction = "Stable"
            rationale = f"6-month trend indicates stable short interest ({trend_6m})."
    else:
        rationale = "No short interest trend data available."

    return {
        "conviction": conviction,
        "conviction_color": _CONVICTION_COLOR.get(conviction, "#D97706"),
        "conviction_rationale": rationale,
        "short_pct": short_pct_float,
        "days_to_cover": days_to_cover_float,
        "shares_short": current_int,
        "shares_short_prior": prior_int,
        "pct_change": pct_change,
    }


__all__ = ["build_short_seller_alerts", "derive_short_conviction"]
