"""Data extraction bridge for executive forensics scoring.

Pulls executive-related data from AnalysisState into a standardized
format for the executive forensics scorer. Per CONTEXT.md: "only score
dimensions where data already exists in state."

Data sources:
- state.extracted.governance.leadership.executives (LeadershipForensicProfile)
- state.extracted.governance.board_forensics (BoardForensicProfile)
- state.extracted.market.insider_analysis.transactions (InsiderTransaction)
- state.extracted.governance.board (BoardProfile aggregate)
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def _load_config() -> dict[str, Any]:
    """Load executive scoring config from JSON."""
    return load_config("executive_scoring")


def _extract_role_from_title(title: str, role_weights: dict[str, float]) -> str:
    """Map common titles to canonical roles.

    Uses role_weights keys as the canonical role set. Matches by
    checking if canonical keywords appear in the title string.

    Args:
        title: Raw title string (e.g., "Chief Executive Officer")
        role_weights: Dict of canonical roles to weights from config

    Returns:
        Canonical role string (e.g., "CEO") or "Other"
    """
    if not title:
        return "Other"

    title_upper = title.upper()
    title_words = set(title_upper.split())

    # Mappings: (phrase_keywords, word_keywords, role)
    # phrase_keywords use substring match; word_keywords use whole-word match
    mappings: list[tuple[list[str], list[str], str]] = [
        (["CHIEF EXECUTIVE"], ["CEO"], "CEO"),
        (["CHIEF FINANCIAL"], ["CFO"], "CFO"),
        (["CHIEF OPERATING"], ["COO"], "COO"),
        (["GENERAL COUNSEL", "CHIEF LEGAL"], ["CLO"], "GC"),
        (["CHIEF ACCOUNTING", "PRINCIPAL ACCOUNTING"], ["CAO"], "CAO"),
        (["CHIEF TECHNOLOGY"], ["CTO"], "CTO"),
        (["CHIEF RISK"], ["CRO"], "CRO"),
        (["CHIEF INFORMATION SECURITY"], ["CISO"], "CISO"),
        (["LEAD INDEPENDENT"], [], "Lead Independent Director"),
        (["CHAIRMAN", "CHAIR OF THE BOARD"], [], "Chairman"),
        (["PRESIDENT"], [], "COO"),
        ([], ["DIRECTOR"], "Director"),
    ]

    for phrase_kws, word_kws, role in mappings:
        matched = any(kw in title_upper for kw in phrase_kws)
        if not matched:
            matched = any(kw in title_words for kw in word_kws)
        if matched:
            return role if role in role_weights else "Other"

    return "Other"


def _match_insider_to_executive(
    exec_name: str,
    insider_trades: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Fuzzy name matching to associate Form 4 trades with executives.

    Uses first-word + last-word comparison (case insensitive) to handle
    middle names, initials, and suffixes. E.g., "John A. Smith" matches
    "John Smith" in insider filings.

    Args:
        exec_name: Executive's full name
        insider_trades: List of dicts with insider_name and trade details

    Returns:
        List of matching trade dicts
    """
    if not exec_name or not insider_trades:
        return []

    name_parts = exec_name.strip().split()
    if len(name_parts) < 2:
        return []

    exec_first = name_parts[0].upper()
    exec_last = name_parts[-1].upper()

    matches = []
    for trade in insider_trades:
        trade_name = trade.get("insider_name", "")
        if not trade_name:
            continue

        trade_parts = trade_name.strip().split()
        if len(trade_parts) < 2:
            continue

        trade_first = trade_parts[0].upper()
        trade_last = trade_parts[-1].upper()

        if exec_first == trade_first and exec_last == trade_last:
            matches.append(trade)

    return matches


def _sourced_value_str(sv: Any) -> str:
    """Safely extract string value from a SourcedValue or return empty string."""
    if sv is None:
        return ""
    if hasattr(sv, "value"):
        return str(sv.value)
    return str(sv)


def _sourced_value_float(sv: Any) -> float | None:
    """Safely extract float value from a SourcedValue or return None."""
    if sv is None:
        return None
    if hasattr(sv, "value"):
        try:
            return float(sv.value)
        except (TypeError, ValueError):
            return None
    try:
        return float(sv)
    except (TypeError, ValueError):
        return None


def _extract_insider_trades_flat(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract insider transactions as flat dicts for name matching.

    Pulls from state.extracted.market.insider_analysis.transactions.
    """
    if state.extracted is None or state.extracted.market is None:
        return []

    transactions = state.extracted.market.insider_analysis.transactions
    flat: list[dict[str, Any]] = []

    for txn in transactions:
        flat.append({
            "insider_name": _sourced_value_str(txn.insider_name),
            "title": _sourced_value_str(txn.title),
            "transaction_date": _sourced_value_str(txn.transaction_date),
            "transaction_type": txn.transaction_type,
            "shares": _sourced_value_float(txn.shares),
            "total_value": _sourced_value_float(txn.total_value),
            "is_10b5_1": txn.is_10b5_1.value if txn.is_10b5_1 is not None else None,
            "is_discretionary": txn.is_discretionary,
        })

    return flat


def extract_executive_data(state: AnalysisState) -> list[dict[str, Any]]:
    """Extract executive data from AnalysisState for forensics scoring.

    Pulls data from governance leadership profiles, board forensics,
    and insider trading transactions. Returns a list of dicts, one per
    executive, with standardized fields for the scorer.

    Args:
        state: The AnalysisState with extracted data

    Returns:
        List of dicts with keys: name, role, role_weight, insider_trades,
        years_tenure, prior_litigation, prior_enforcement, prior_failures,
        bio_summary, officer_change_recent, departure_type
    """
    if state.extracted is None or state.extracted.governance is None:
        logger.info("No governance data available for executive extraction")
        return []

    config = _load_config()
    role_weights = config.get("role_weights", {})
    governance = state.extracted.governance
    insider_trades = _extract_insider_trades_flat(state)

    executives: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    # Extract from leadership forensic profiles (primary source)
    for profile in governance.leadership.executives:
        name = _sourced_value_str(profile.name)
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        title = _sourced_value_str(profile.title)
        role = _extract_role_from_title(title, role_weights)
        weight = role_weights.get(role, 1.0)

        # Match insider trades for this person
        matched_trades = _match_insider_to_executive(name, insider_trades)

        # Extract bio for prior-company issues
        bio = _sourced_value_str(profile.bio_summary)

        executives.append({
            "name": name,
            "role": role,
            "role_weight": weight,
            "title": title,
            "insider_trades": matched_trades,
            "years_tenure": profile.tenure_years,
            "prior_litigation": [_sourced_value_str(x) for x in profile.prior_litigation],
            "prior_enforcement": [_sourced_value_str(x) for x in profile.prior_enforcement],
            "prior_restatements": [_sourced_value_str(x) for x in profile.prior_restatements],
            "shade_factors": [_sourced_value_str(x) for x in profile.shade_factors],
            "bio_summary": bio,
            "officer_change_recent": profile.departure_type == "ACTIVE"
            and profile.tenure_years is not None
            and profile.tenure_years < 1.0,
            "departure_type": profile.departure_type,
            "is_interim": profile.is_interim.value
            if profile.is_interim is not None
            else False,
        })

    # Extract from board forensic profiles (directors not in leadership)
    for board_member in governance.board_forensics:
        name = _sourced_value_str(board_member.name)
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        role = "Director"
        weight = role_weights.get(role, 1.0)
        matched_trades = _match_insider_to_executive(name, insider_trades)

        tenure = _sourced_value_float(board_member.tenure_years)

        executives.append({
            "name": name,
            "role": role,
            "role_weight": weight,
            "title": "Director",
            "insider_trades": matched_trades,
            "years_tenure": tenure,
            "prior_litigation": [
                _sourced_value_str(x) for x in board_member.prior_litigation
            ],
            "prior_enforcement": [],
            "prior_restatements": [],
            "shade_factors": [],
            "bio_summary": "",
            "officer_change_recent": False,
            "departure_type": "ACTIVE",
            "is_interim": False,
        })

    logger.info(
        "Extracted %d executives for forensics scoring (%d with trades)",
        len(executives),
        sum(1 for e in executives if e["insider_trades"]),
    )
    return executives


__all__ = [
    "extract_executive_data",
]
