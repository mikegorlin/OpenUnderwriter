"""Key dates calendar context builder.

Collects forward-looking dates from multiple state paths and classifies
urgency with color coding for template rendering.

Phase 136: Forward-Looking and Integration
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Urgency classification
# ---------------------------------------------------------------------------

_URGENCY_THRESHOLDS: list[tuple[int, str, str]] = [
    (30, "HIGH", "#DC2626"),     # Within 30 days = red
    (90, "MEDIUM", "#D97706"),   # 30-90 days = amber
    (999999, "LOW", "#9CA3AF"),  # Beyond 90 days = gray
]

# Events that should trigger re-underwriting review
_MONITORING_EVENTS = {
    "Next Earnings",
    "Annual Meeting",
    "Lockup Expiry",
    "10-K Filing Due",
}


def _classify_urgency(target_date: date) -> tuple[str, str]:
    """Classify urgency based on days until target date.

    Returns:
        Tuple of (urgency_level, urgency_color).
    """
    days_until = (target_date - date.today()).days
    for threshold, level, color in _URGENCY_THRESHOLDS:
        if days_until <= threshold:
            return level, color
    return "LOW", "#9CA3AF"


def _format_date_display(d: date) -> str:
    """Format date as 'Mon DD, YYYY'."""
    return d.strftime("%b %d, %Y")


def _parse_date(date_str: str) -> date | None:
    """Parse a date string to date object, handling various formats."""
    if not date_str or not isinstance(date_str, str):
        return None
    # Strip any time component
    date_str = date_str.strip()[:10]
    try:
        return date.fromisoformat(date_str)
    except (ValueError, TypeError):
        pass
    # Try common formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            from datetime import datetime
            return datetime.strptime(date_str, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _add_date_entry(
    entries: list[dict[str, Any]],
    event: str,
    target_date: date,
    source: str,
    do_relevance: str,
) -> None:
    """Add a date entry with urgency classification."""
    # Skip dates in the past
    if target_date < date.today():
        return
    urgency, urgency_color = _classify_urgency(target_date)
    entries.append({
        "date": target_date.isoformat(),
        "date_display": _format_date_display(target_date),
        "event": event,
        "source": source,
        "urgency": urgency,
        "urgency_color": urgency_color,
        "do_relevance": do_relevance,
    })


def _collect_market_dates(state: AnalysisState, entries: list[dict[str, Any]]) -> None:
    """Collect dates from acquired market data calendar."""
    if not state.acquired_data or not state.acquired_data.market_data:
        return
    md = state.acquired_data.market_data
    if not isinstance(md, dict):
        return
    cal = md.get("calendar", {})
    if not isinstance(cal, dict):
        return

    # Next earnings
    earnings = cal.get("Earnings Date", [])
    if isinstance(earnings, list) and earnings:
        d = _parse_date(str(earnings[0]))
        if d:
            _add_date_entry(
                entries, "Next Earnings", d, "yfinance",
                "Earnings announcements are the primary catalyst for SCA filings; "
                "a miss can trigger securities fraud claims.",
            )
    elif isinstance(earnings, str) and earnings:
        d = _parse_date(earnings)
        if d:
            _add_date_entry(
                entries, "Next Earnings", d, "yfinance",
                "Earnings announcements are the primary catalyst for SCA filings.",
            )

    # Ex-dividend
    ex_div = cal.get("Ex-Dividend Date", "")
    if ex_div:
        d = _parse_date(str(ex_div))
        if d:
            _add_date_entry(
                entries, "Ex-Dividend", d, "yfinance",
                "Dividend changes can signal financial stress and trigger shareholder claims.",
            )

    # Dividend date
    div_date = cal.get("Dividend Date", "")
    if div_date:
        d = _parse_date(str(div_date))
        if d:
            _add_date_entry(
                entries, "Dividend Payment", d, "yfinance",
                "Dividend payment date for income-focused institutional holders.",
            )


def _collect_governance_dates(state: AnalysisState, entries: list[dict[str, Any]]) -> None:
    """Collect annual meeting date from governance data."""
    if not state.extracted or not state.extracted.governance:
        return
    meeting_date = getattr(state.extracted.governance, "annual_meeting_date", None)
    if meeting_date:
        d = _parse_date(str(meeting_date))
        if d:
            _add_date_entry(
                entries, "Annual Meeting", d, "DEF 14A",
                "Annual meetings involve proxy votes, board elections, "
                "and say-on-pay — all governance risk events.",
            )


def _collect_ipo_dates(state: AnalysisState, entries: list[dict[str, Any]]) -> None:
    """Collect IPO-related milestone dates for recent IPOs."""
    if not state.extracted or not getattr(state.extracted, "company_profile", None):
        return
    ipo_date_str = getattr(state.extracted.company_profile, "ipo_date", None)
    years_public = safe_float(
        getattr(state.extracted.company_profile, "years_public", 99), 99
    )

    if not ipo_date_str or years_public >= 5:
        return

    ipo_date = _parse_date(str(ipo_date_str))
    if not ipo_date:
        return

    # Lockup expiry (typically 180 days post-IPO)
    lockup_date = ipo_date + timedelta(days=180)
    if lockup_date >= date.today():
        _add_date_entry(
            entries, "Lockup Expiry", lockup_date, "IPO filing",
            "Lockup expiration allows insider selling, often causing stock drops. "
            "Key Section 11 trigger.",
        )

    # 1-year IPO anniversary (statute of limitations marker)
    anniversary_1y = ipo_date + timedelta(days=365)
    if anniversary_1y >= date.today():
        _add_date_entry(
            entries, "IPO 1-Year Anniversary", anniversary_1y, "IPO filing",
            "Section 11 claims have a 1-year statute of limitations from "
            "discovery of misstatement, max 3 years from offering.",
        )

    # 3-year IPO anniversary (Section 11 outer limit)
    anniversary_3y = ipo_date + timedelta(days=365 * 3)
    if anniversary_3y >= date.today():
        _add_date_entry(
            entries, "IPO 3-Year Statute Limit", anniversary_3y, "IPO filing",
            "Absolute outer limit for Section 11 claims from the offering date.",
        )


def build_forward_calendar(state: AnalysisState) -> dict[str, Any]:
    """Build key dates calendar with urgency classification.

    Collects dates from:
    - yfinance calendar (earnings, dividends)
    - Governance data (annual meeting)
    - IPO milestones (for companies public < 5 years)

    Returns:
        Dict with calendar_available, dates list (sorted chronologically),
        monitoring_triggers list, and date_count.
    """
    entries: list[dict[str, Any]] = []

    _collect_market_dates(state, entries)
    _collect_governance_dates(state, entries)
    _collect_ipo_dates(state, entries)

    # Sort chronologically
    entries.sort(key=lambda e: e["date"])

    # Build monitoring triggers (subset that should trigger re-underwriting)
    monitoring_triggers = [
        e for e in entries if e["event"] in _MONITORING_EVENTS
    ]

    if not entries:
        return {
            "calendar_available": False,
            "dates": [],
            "monitoring_triggers": [],
            "date_count": 0,
        }

    return {
        "calendar_available": True,
        "dates": entries,
        "monitoring_triggers": monitoring_triggers,
        "date_count": len(entries),
    }


__all__ = ["build_forward_calendar"]
