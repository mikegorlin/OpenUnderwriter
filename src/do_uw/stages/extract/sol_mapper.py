"""Statute of limitations window computation (SECT6-11).

Loads claim types from config/claim_types.json and computes SOL
and repose expiry dates from trigger events. Determines which
filing windows remain open for each claim type.

Usage:
    windows, report = compute_sol_map(state)
    state.extracted.litigation.sol_map = windows
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.common import Confidence
from do_uw.models.litigation_details import SOLWindow
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import sourced_str
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

_CONFIG_FILE = "claim_types.json"
_SOURCE = "config/claim_types.json"

EXPECTED_FIELDS: list[str] = [
    "claim_types_evaluated",
    "windows_open",
    "windows_closed",
    "trigger_dates_found",
    "trigger_dates_proxy",
]


def _load_claim_types() -> dict[str, Any]:
    """Load claim_types.json from config directory.

    Returns:
        Parsed JSON dict with 'claim_types' key.
    """
    return load_config("claim_types")


def _today() -> date:
    """Return today's date (UTC)."""
    return datetime.now(tz=UTC).date()


# ---------------------------------------------------------------------------
# Trigger date resolution
# ---------------------------------------------------------------------------

# Claim types triggered by SCA case filings.
_SCA_TRIGGERED: frozenset[str] = frozenset(
    {"10b-5", "Section_11", "Section_14a"}
)

# Claim types triggered by enforcement actions.
_ENFORCEMENT_TRIGGERED: frozenset[str] = frozenset(
    {"FCPA", "antitrust"}
)


def find_trigger_date(
    claim_type: str,
    state: AnalysisState,
    sol_trigger: str = "discovery",
) -> tuple[date | None, str, Confidence]:
    """Find the trigger date for a claim type from state data.

    Uses the config sol_trigger type to determine which date to use:
    - "discovery": class_period_end (corrective disclosure date)
    - "violation": class_period_start (when the alleged fraud began)
    - "demand_refusal": filing_date (derivative demand date)

    Falls back through: event date → filing date → 10-K date proxy.

    Args:
        claim_type: Claim type ID from config.
        state: Analysis state with extracted data.
        sol_trigger: Trigger type from config ("discovery", "violation",
            "demand_refusal").

    Returns:
        Tuple of (trigger_date, description, confidence).
    """
    # --- Try SCA event dates (class period dates) ---
    if claim_type in _SCA_TRIGGERED:
        event_date = _earliest_sca_event_date(state, sol_trigger)
        if event_date is not None:
            desc = {
                "discovery": "Class period end (corrective disclosure)",
                "violation": "Class period start (alleged fraud began)",
            }.get(sol_trigger, f"SCA event date ({sol_trigger})")
            return (event_date, desc, Confidence.HIGH)

        # Fallback: filing date if event dates unavailable
        filing = _earliest_sca_filing_date(state)
        if filing is not None:
            return (
                filing,
                "SCA complaint filing date (event dates unavailable)",
                Confidence.MEDIUM,
            )

    # --- Try enforcement actions ---
    if claim_type in _ENFORCEMENT_TRIGGERED:
        enf_date = _earliest_enforcement_date(state)
        if enf_date is not None:
            return (
                enf_date,
                "Earliest SEC enforcement action date",
                Confidence.MEDIUM,
            )

    # --- Fallback: most recent 10-K filing date ---
    filing_date = _most_recent_10k_date(state)
    if filing_date is not None:
        return (
            filing_date,
            "Most recent annual report date (proxy)",
            Confidence.LOW,
        )

    return (None, "", Confidence.LOW)


def compute_window(
    claim_type: str,
    sol_years: int,
    repose_years: int,
    trigger_date: date,
    trigger_desc: str,
    confidence: Confidence,
    today: date,
) -> SOLWindow:
    """Compute SOL and repose expiry dates and open/closed status.

    Args:
        claim_type: Claim type ID.
        sol_years: Statute of limitations period in years.
        repose_years: Statute of repose period in years.
        trigger_date: Date of the triggering event.
        trigger_desc: Description of the trigger.
        confidence: Confidence level of the trigger date.
        today: Current date for open/closed comparison.

    Returns:
        Populated SOLWindow.
    """
    sol_expiry = trigger_date + timedelta(days=sol_years * 365)
    repose_expiry = trigger_date + timedelta(days=repose_years * 365)

    sol_open = today < sol_expiry
    repose_open = today < repose_expiry
    window_open = sol_open and repose_open

    return SOLWindow(
        claim_type=claim_type,
        trigger_date=trigger_date,
        trigger_description=sourced_str(
            trigger_desc, _SOURCE, confidence
        ),
        sol_years=sol_years,
        repose_years=repose_years,
        sol_expiry=sol_expiry,
        repose_expiry=repose_expiry,
        sol_open=sol_open,
        repose_open=repose_open,
        window_open=window_open,
    )


def sort_windows(windows: list[SOLWindow]) -> list[SOLWindow]:
    """Sort windows: open first, then by repose_expiry ascending.

    Args:
        windows: List of SOLWindow to sort.

    Returns:
        Sorted copy.
    """

    def sort_key(w: SOLWindow) -> tuple[int, date]:
        # Open windows first (0 before 1), then by repose date.
        open_rank = 0 if w.window_open else 1
        expiry = w.repose_expiry if w.repose_expiry else date.max
        return (open_rank, expiry)

    return sorted(windows, key=sort_key)


# ---------------------------------------------------------------------------
# Main function
# ---------------------------------------------------------------------------


def compute_sol_map(
    state: AnalysisState,
) -> tuple[list[SOLWindow], ExtractionReport]:
    """Compute statute of limitations windows for all claim types.

    Loads claim types from config, resolves trigger dates from
    state data, and computes SOL/repose expiry for each.

    Args:
        state: Analysis state with extracted litigation data.

    Returns:
        Tuple of (list[SOLWindow], ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    windows: list[SOLWindow] = []
    today = _today()

    # --- Load config ---
    config = _load_claim_types()
    claim_types_dict = config.get("claim_types", {})
    if not claim_types_dict:
        warnings.append("No claim types loaded from config")
        report = create_report(
            extractor_name="sol_mapper",
            expected=EXPECTED_FIELDS,
            found=found,
            source_filing=_SOURCE,
            warnings=warnings,
        )
        log_report(report)
        return windows, report

    found.append("claim_types_evaluated")

    # --- Process each claim type ---
    open_count = 0
    closed_count = 0
    trigger_found_count = 0
    trigger_proxy_count = 0

    ct_dict = cast(dict[str, Any], claim_types_dict)
    for ct_key, ct_config in ct_dict.items():
        if not isinstance(ct_config, dict):
            continue
        ct = cast(dict[str, Any], ct_config)

        sol_years = int(ct.get("sol_years", 2))
        repose_years = int(ct.get("repose_years", 5))
        sol_trigger = str(ct.get("sol_trigger", "discovery"))

        trigger_date, trigger_desc, confidence = find_trigger_date(
            ct_key, state, sol_trigger=sol_trigger,
        )

        # Only create windows where trigger_date is available.
        if trigger_date is None:
            continue

        if "proxy" in trigger_desc.lower():
            trigger_proxy_count += 1
        else:
            trigger_found_count += 1

        window = compute_window(
            claim_type=ct_key,
            sol_years=sol_years,
            repose_years=repose_years,
            trigger_date=trigger_date,
            trigger_desc=trigger_desc,
            confidence=confidence,
            today=today,
        )
        windows.append(window)

        if window.window_open:
            open_count += 1
        else:
            closed_count += 1

    # --- Sort results ---
    windows = sort_windows(windows)

    # --- Track found fields ---
    if open_count > 0:
        found.append("windows_open")
    if closed_count > 0:
        found.append("windows_closed")
    if trigger_found_count > 0:
        found.append("trigger_dates_found")
    if trigger_proxy_count > 0:
        found.append("trigger_dates_proxy")

    logger.info(
        "SOL mapper: %d windows (%d open, %d closed), "
        "%d actual triggers, %d proxy triggers",
        len(windows),
        open_count,
        closed_count,
        trigger_found_count,
        trigger_proxy_count,
    )

    report = create_report(
        extractor_name="sol_mapper",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=_SOURCE,
        warnings=warnings,
    )
    log_report(report)
    return windows, report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _earliest_sca_event_date(
    state: AnalysisState, sol_trigger: str
) -> date | None:
    """Find the earliest SCA event date based on trigger type.

    For "discovery" trigger: use class_period_end (corrective disclosure).
    For "violation" trigger: use class_period_start (fraud began).
    """
    if state.extracted is None or state.extracted.litigation is None:
        return None
    cases = state.extracted.litigation.securities_class_actions
    earliest: date | None = None
    for case in cases:
        if sol_trigger == "discovery" and case.class_period_end is not None:
            dt = case.class_period_end.value
            if earliest is None or dt < earliest:
                earliest = dt
        elif sol_trigger == "violation" and case.class_period_start is not None:
            dt = case.class_period_start.value
            if earliest is None or dt < earliest:
                earliest = dt
    return earliest


def _earliest_sca_filing_date(state: AnalysisState) -> date | None:
    """Find the earliest SCA complaint filing date (fallback)."""
    if state.extracted is None or state.extracted.litigation is None:
        return None
    cases = state.extracted.litigation.securities_class_actions
    earliest: date | None = None
    for case in cases:
        if case.filing_date is not None:
            fd = case.filing_date.value
            if earliest is None or fd < earliest:
                earliest = fd
    return earliest


def _earliest_enforcement_date(state: AnalysisState) -> date | None:
    """Find the earliest SEC enforcement action date."""
    if state.extracted is None or state.extracted.litigation is None:
        return None
    enforcement = state.extracted.litigation.sec_enforcement
    for action in enforcement.actions:
        action_date_str = action.value.get("date", "")
        if action_date_str:
            try:
                return date.fromisoformat(action_date_str)
            except ValueError:
                continue
    return None


def _most_recent_10k_date(state: AnalysisState) -> date | None:
    """Find the most recent 10-K filing date from acquired data."""
    if state.acquired_data is None:
        return None
    docs = state.acquired_data.filing_documents
    ten_k_docs = docs.get("10-K", [])
    if not ten_k_docs:
        return None
    # First document is assumed to be most recent.
    first = ten_k_docs[0]
    date_str = first.get("filing_date", "")
    if date_str:
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            return None
    return None
