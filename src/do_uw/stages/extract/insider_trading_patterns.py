"""Exercise-sell pattern detection and filing timing analysis.

Split from insider_trading.py for 500-line compliance (Phase 71-02).
Detects:
- Exercise-and-sell patterns (code M + code S, same owner, same/adjacent day)
- Pre-announcement trading (insider trades within 60 days before material 8-K)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from do_uw.models.market_events import (
    ExerciseSellEvent,
    FilingTimingSuspect,
    InsiderTransaction,
)
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 8-K filing data extraction
# ---------------------------------------------------------------------------


def get_eight_k_filings(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract 8-K filing metadata for timing analysis.

    Pulls from state.acquired_data.filings["8-K"] and normalizes
    into the format expected by analyze_filing_timing.
    """
    filings: list[dict[str, Any]] = []
    raw_8k = state.acquired_data.filings.get("8-K", [])
    for f in raw_8k:
        filing_date = f.get("filing_date", "")
        items = f.get("items", [])
        if not items:
            item_num = f.get("item_number", "")
            if item_num:
                items = [item_num]
        if filing_date and items:
            filings.append({"filing_date": filing_date, "items": items})
    return filings


# Codes excluded from timing analysis (gifts, estate, compensation).
_EXCLUDED_TIMING_CODES: set[str] = {"G", "W", "A", "F"}

# 8-K item classifications (deterministic, no LLM).
# Expanded to cover all material items for insider timing analysis.
_NEGATIVE_ITEMS: set[str] = {
    "1.02",  # Termination of material agreement
    "1.03",  # Bankruptcy
    "2.02",  # Earnings results (often negative surprise)
    "2.04",  # Triggering events accelerating obligations
    "2.05",  # Restructuring / exit costs
    "2.06",  # Material impairments
    "3.01",  # Delisting notice
    "3.03",  # Modification to shareholder rights
    "4.01",  # Auditor change
    "4.02",  # Restatement / non-reliance
    "5.02",  # Officer/director departure
    "5.05",  # Code of ethics change/waiver
}
_POSITIVE_ITEMS: set[str] = {
    "1.01",  # Entry into material agreement
    "2.01",  # Completion of acquisition
    "5.01",  # Change in control (can be positive for acquiree)
}


# ---------------------------------------------------------------------------
# 8-K item classification
# ---------------------------------------------------------------------------


def classify_8k_item(item_number: str) -> str:
    """Classify 8-K item number as NEGATIVE, POSITIVE, or NEUTRAL.

    NEGATIVE: Items that typically indicate adverse events (restatements,
    departures, impairments, restructuring, delisting, auditor changes).
    POSITIVE: Material agreements, acquisitions, change in control.
    NEUTRAL: Routine disclosures (Reg FD, exhibits, shareholder votes).
    """
    item = item_number.strip()
    if item in _NEGATIVE_ITEMS:
        return "NEGATIVE"
    if item in _POSITIVE_ITEMS:
        return "POSITIVE"
    return "NEUTRAL"


# ---------------------------------------------------------------------------
# Exercise-sell pattern detection
# ---------------------------------------------------------------------------


def detect_exercise_sell_patterns(
    transactions: list[InsiderTransaction],
) -> list[ExerciseSellEvent]:
    """Detect exercise-and-sell patterns (code M + code S, same owner, T+0 or T+1).

    Groups transactions by owner. For each owner, finds exercises (code M)
    and sells (code S) on same or adjacent day. Creates ExerciseSellEvent
    with combined totals. Severity always AMBER per user decision.
    """
    # Group by owner name
    by_owner: dict[str, list[InsiderTransaction]] = defaultdict(list)
    for tx in transactions:
        name = tx.insider_name.value if tx.insider_name else ""
        if name and tx.transaction_code in ("M", "S"):
            by_owner[name].append(tx)

    events: list[ExerciseSellEvent] = []

    for owner, txns in by_owner.items():
        exercises = [t for t in txns if t.transaction_code == "M"]
        sells = [t for t in txns if t.transaction_code == "S"]

        if not exercises or not sells:
            continue

        # Build date-indexed groups with 1-day tolerance
        matched_exercises: set[int] = set()
        matched_sells: set[int] = set()

        for ei, ex in enumerate(exercises):
            ex_date_str = ex.transaction_date.value if ex.transaction_date else ""
            if not ex_date_str:
                continue
            try:
                ex_date = datetime.strptime(ex_date_str, "%Y-%m-%d")
            except ValueError:
                continue

            for si, sl in enumerate(sells):
                sl_date_str = sl.transaction_date.value if sl.transaction_date else ""
                if not sl_date_str:
                    continue
                try:
                    sl_date = datetime.strptime(sl_date_str, "%Y-%m-%d")
                except ValueError:
                    continue

                delta = abs((sl_date - ex_date).days)
                if delta <= 1:
                    matched_exercises.add(ei)
                    matched_sells.add(si)

        if not matched_exercises or not matched_sells:
            continue

        # Aggregate matched transactions
        exercised_shares = sum(
            (exercises[i].shares.value if exercises[i].shares else 0.0)
            for i in matched_exercises
        )
        sold_shares = sum(
            (sells[i].shares.value if sells[i].shares else 0.0)
            for i in matched_sells
        )
        sold_value = sum(
            (sells[i].total_value.value if sells[i].total_value else 0.0)
            for i in matched_sells
        )

        # 10b5-1 status from sell transactions
        is_10b5_1 = any(
            sells[i].is_10b5_1 and sells[i].is_10b5_1.value is True
            for i in matched_sells
        )

        # Use earliest date
        dates = []
        for i in matched_exercises:
            if exercises[i].transaction_date:
                dates.append(exercises[i].transaction_date.value)
        event_date = min(dates) if dates else ""

        events.append(ExerciseSellEvent(
            owner=owner,
            date=event_date,
            exercised_shares=exercised_shares,
            sold_shares=sold_shares,
            sold_value=sold_value,
            severity="AMBER",
            is_10b5_1=is_10b5_1,
        ))

    return events


# ---------------------------------------------------------------------------
# Filing timing analysis
# ---------------------------------------------------------------------------


def analyze_filing_timing(
    transactions: list[InsiderTransaction],
    eight_k_filings: list[dict[str, Any]],
    window_days: int = 60,
) -> list[FilingTimingSuspect]:
    """Analyze insider transaction timing relative to material 8-K filings.

    Detects:
    - SELL transactions within window_days BEFORE negative 8-K filings -> RED_FLAG
    - BUY transactions within window_days BEFORE positive 8-K filings -> AMBER

    Uses filing_date as conservative proxy (per Pitfall 5).
    Excludes gift/estate/compensation codes.
    """
    suspects: list[FilingTimingSuspect] = []

    # Filter to actionable transactions
    actionable = [
        tx for tx in transactions
        if tx.transaction_code not in _EXCLUDED_TIMING_CODES
        and tx.transaction_date is not None
        and tx.insider_name is not None
    ]

    for filing in eight_k_filings:
        filing_date_str = filing.get("filing_date", "")
        items = filing.get("items", [])

        if not filing_date_str or not items:
            continue

        try:
            filing_date = datetime.strptime(filing_date_str, "%Y-%m-%d")
        except ValueError:
            continue

        # Classify each item; use most severe
        sentiments = [classify_8k_item(item) for item in items]
        has_negative = "NEGATIVE" in sentiments
        has_positive = "POSITIVE" in sentiments

        if not has_negative and not has_positive:
            continue

        window_start = filing_date - timedelta(days=window_days)

        for tx in actionable:
            tx_date_str = tx.transaction_date.value if tx.transaction_date else ""
            if not tx_date_str:
                continue
            try:
                tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d")
            except ValueError:
                continue

            # Must be within window BEFORE filing (not on or after)
            if tx_date < window_start or tx_date >= filing_date:
                continue

            days_before = (filing_date - tx_date).days
            tx_type = tx.transaction_type
            tx_value = tx.total_value.value if tx.total_value else 0.0
            tx_name = tx.insider_name.value if tx.insider_name else ""

            # SELL before negative -> RED_FLAG
            if has_negative and tx_type == "SELL":
                neg_item = next(
                    (items[i] for i, s in enumerate(sentiments) if s == "NEGATIVE"),
                    items[0],
                )
                suspects.append(FilingTimingSuspect(
                    insider_name=tx_name,
                    transaction_date=tx_date_str,
                    transaction_type="SELL",
                    filing_date=filing_date_str,
                    filing_item=neg_item,
                    filing_sentiment="NEGATIVE",
                    days_before_filing=days_before,
                    transaction_value=tx_value,
                    severity="RED_FLAG",
                ))

            # BUY before positive -> AMBER
            if has_positive and tx_type == "BUY":
                pos_item = next(
                    (items[i] for i, s in enumerate(sentiments) if s == "POSITIVE"),
                    items[0],
                )
                suspects.append(FilingTimingSuspect(
                    insider_name=tx_name,
                    transaction_date=tx_date_str,
                    transaction_type="BUY",
                    filing_date=filing_date_str,
                    filing_item=pos_item,
                    filing_sentiment="POSITIVE",
                    days_before_filing=days_before,
                    transaction_value=tx_value,
                    severity="AMBER",
                ))

    return suspects
