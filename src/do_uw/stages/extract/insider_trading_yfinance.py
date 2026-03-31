"""yfinance fallback extraction for insider trading.

Split from insider_trading.py for 500-line compliance (Phase 71).
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import InsiderTransaction
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_market_data,
    now,
    sourced_str,
)

logger = logging.getLogger(__name__)

# Patterns that indicate a 10b5-1 pre-arranged trading plan in yfinance Text.
_10B5_1_PATTERNS = re.compile(
    r"10b5[\-\s]?1|rule\s*10b[\-\s]?5|pre[\-\s]?arranged\s+(?:trading\s+)?plan|"
    r"trading\s+plan|written\s+plan\s+for\s+trading",
    re.IGNORECASE,
)


def detect_10b5_1_from_text(text: str) -> bool | None:
    """Detect 10b5-1 plan indicator from yfinance transaction text.

    Returns True if text mentions a 10b5-1 / pre-arranged trading plan,
    False if text explicitly says "not pursuant to" a plan,
    None if no indicator found.
    """
    if not text:
        return None
    lower = text.lower()
    # Check for explicit negation first
    if "not pursuant" in lower or "not under" in lower:
        if _10B5_1_PATTERNS.search(text):
            return False
    elif _10B5_1_PATTERNS.search(text):
        return True
    return None


def _extract_from_yfinance(state: AnalysisState) -> list[InsiderTransaction]:
    """Fallback extraction from yfinance insider_transactions data."""
    market = get_market_data(state)
    raw = market.get("insider_transactions")
    if not raw or not isinstance(raw, dict):
        return []

    insider_dict = cast(dict[str, Any], raw)
    names = _get_column(insider_dict, "Insider Trading", "insider")
    shares_list = _get_column(insider_dict, "Shares", "shares")
    values_list = _get_column(insider_dict, "Value", "value")
    dates_list = _get_column(insider_dict, "Start Date", "Date", "index")
    text_list = _get_column(insider_dict, "Text", "text")

    if not names:
        return []

    transactions: list[InsiderTransaction] = []
    source = "yfinance insider_transactions"

    for i in range(len(names)):
        name = str(names[i]) if i < len(names) else ""
        date_val = str(dates_list[i]) if i < len(dates_list) else ""
        text_val = str(text_list[i]) if i < len(text_list) else ""
        shares_raw = shares_list[i] if i < len(shares_list) else None
        value_raw = values_list[i] if i < len(values_list) else None
        shares_f = _safe_float(str(shares_raw)) if shares_raw else None
        value_f = _safe_float(str(value_raw)) if value_raw else None

        tx_type = classify_yfinance_text(text_val)
        tx_code = "S" if tx_type == "SELL" else ("P" if tx_type == "BUY" else "")
        date_str = normalize_date(date_val)

        # Detect 10b5-1 plan from transaction text description
        is_10b5_1 = detect_10b5_1_from_text(text_val)

        tx = InsiderTransaction(
            insider_name=(
                sourced_str(name, source, Confidence.MEDIUM) if name else None
            ),
            transaction_date=(
                sourced_str(date_str, source, Confidence.MEDIUM) if date_str else None
            ),
            transaction_type=tx_type,
            transaction_code=tx_code,
            shares=(
                SourcedValue[float](
                    value=shares_f, source=source,
                    confidence=Confidence.MEDIUM, as_of=now(),
                ) if shares_f is not None else None
            ),
            total_value=(
                SourcedValue[float](
                    value=value_f, source=source,
                    confidence=Confidence.MEDIUM, as_of=now(),
                ) if value_f is not None else None
            ),
            is_10b5_1=(
                SourcedValue[bool](
                    value=is_10b5_1, source=source,
                    confidence=Confidence.MEDIUM, as_of=now(),
                )
                if is_10b5_1 is not None else None
            ),
            is_discretionary=not is_10b5_1 if is_10b5_1 is not None else True,
        )
        transactions.append(tx)

    logger.info("Extracted %d transactions from yfinance fallback", len(transactions))
    return transactions


def _get_column(data: dict[str, Any], *keys: str) -> list[Any]:
    """Get a list column from dict by trying multiple key names."""
    for key in keys:
        val = data.get(key)
        if isinstance(val, list):
            return cast(list[Any], val)
    return []


def classify_yfinance_text(text: str) -> str:
    """Classify yfinance transaction text into BUY/SELL/OTHER."""
    lower = text.lower()
    if "sale" in lower or "sold" in lower or "sell" in lower:
        return "SELL"
    if "purchase" in lower or "buy" in lower or "bought" in lower:
        return "BUY"
    if "exercise" in lower or "option" in lower:
        return "EXERCISE"
    if "gift" in lower:
        return "GIFT"
    return "OTHER"


def normalize_date(date_str: str) -> str:
    """Normalize a date string to YYYY-MM-DD format."""
    if not date_str:
        return ""
    if len(date_str) >= 10 and date_str[4] == "-" and date_str[7] == "-":
        return date_str[:10]
    for fmt in ("%m/%d/%Y", "%b %d, %Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(date_str[:19], fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str[:10] if len(date_str) >= 10 else date_str


def _safe_float(val: str) -> float | None:
    """Safely parse a string to float."""
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None
