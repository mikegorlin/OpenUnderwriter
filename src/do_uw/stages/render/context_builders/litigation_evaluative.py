"""Litigation evaluative context from signal results.

Extracts defense strength, SEC enforcement, statute of limitations,
reserve adequacy, and overall litigation risk assessments from LIT.*
signal results. Display data (case lists, settlements, provisions,
timelines) stays in litigation.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.context_builders._signal_consumer import (
    SignalResultView,
    signal_to_display_level,
)
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)


def _view_to_flag(view: SignalResultView) -> dict[str, str]:
    """Convert a triggered signal view into a template-ready flag dict."""
    return {
        "signal_id": view.signal_id,
        "display_level": signal_to_display_level(view.status, view.threshold_level),
        "evidence": view.evidence,
        "threshold_context": view.threshold_context,
        "status": view.status,
        "confidence": view.confidence,
        "do_context": view.do_context if view.do_context else "",
    }


def _extract_defense_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract defense strength flags from LIT.DEFENSE.* signals.

    Covers contingent liabilities, forum selection, PSLRA safe harbor
    usage, and other defense-related assessments.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "LIT.DEFENSE.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_sec_enforcement_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract SEC enforcement flags from LIT.REG.* signals.

    Covers SEC active investigations, Wells notices, comment letters,
    cease & desist orders, civil penalties, and other regulatory actions.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "LIT.REG.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_sol_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract statute of limitations flags from LIT.PATTERN.* signals.

    Covers SOL window status, temporal correlations, industry pattern
    contagion, and other pattern-based assessments.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "LIT.PATTERN.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_sca_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract SCA-specific flags from LIT.SCA.* signals.

    Covers active SCAs, class periods, exposure amounts, settlement
    history, dismissal history, and other case-level assessments.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "LIT.SCA.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_other_litigation_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract other litigation flags from LIT.OTHER.* signals.

    Covers employment, antitrust, environmental, product liability,
    cyber breach, whistleblower, and other non-SCA matters.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "LIT.OTHER.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_sector_litigation_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract sector-specific litigation flags from LIT.SECTOR.* signals.

    Covers industry-specific patterns and regulatory database entries.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "LIT.SECTOR.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def extract_litigation_evaluative(
    signal_results: dict[str, Any] | None,
) -> dict[str, Any]:
    """Extract all litigation evaluative content from signal results.

    Returns a dict of signal-backed evaluative data to merge into
    the litigation context. Keys are prefixed with 'signal_' to
    distinguish from display data.
    """
    defense_flags = _extract_defense_signals(signal_results)
    sec_flags = _extract_sec_enforcement_signals(signal_results)
    sol_flags = _extract_sol_signals(signal_results)
    sca_flags = _extract_sca_signals(signal_results)
    other_flags = _extract_other_litigation_signals(signal_results)
    sector_flags = _extract_sector_litigation_signals(signal_results)

    all_flags = defense_flags + sec_flags + sol_flags + sca_flags + other_flags + sector_flags

    # Aggregate litigation signal summary
    critical_count = sum(1 for f in all_flags if f["display_level"] == "Critical")
    warning_count = sum(1 for f in all_flags if f["display_level"] == "Warning")

    # Defense strength from signal
    defense_result = safe_get_result(signal_results, "LIT.DEFENSE.pslra_safe_harbor")
    defense_signal_summary = ""
    if defense_result:
        defense_signal_summary = defense_result.evidence

    # Overall litigation risk classification from aggregated signals
    risk_level = "Low"
    if critical_count >= 3:
        risk_level = "Critical"
    elif critical_count >= 1:
        risk_level = "High"
    elif warning_count >= 3:
        risk_level = "Elevated"
    elif warning_count >= 1:
        risk_level = "Moderate"

    # Build D&O context lookup from all litigation signals (not just triggered)
    do_context_map: dict[str, str] = {}
    for prefix in ("LIT.DEFENSE.", "LIT.REG.", "LIT.PATTERN.",
                    "LIT.SCA.", "LIT.OTHER.", "LIT.SECTOR."):
        for view in safe_get_signals_by_prefix(signal_results, prefix):
            if view.do_context:
                do_context_map[view.signal_id] = view.do_context

    # Aggregate D&O context for SCA and SEC sections
    sca_exposure_sig = safe_get_result(signal_results, "LIT.SCA.exposure")
    sca_do_context = sca_exposure_sig.do_context if sca_exposure_sig and sca_exposure_sig.do_context else ""
    sec_active_sig = safe_get_result(signal_results, "LIT.REG.sec_active")
    sec_do_context = sec_active_sig.do_context if sec_active_sig and sec_active_sig.do_context else ""

    return {
        "signal_defense_flags": defense_flags,
        "signal_sec_flags": sec_flags,
        "signal_sol_flags": sol_flags,
        "signal_sca_flags": sca_flags,
        "signal_other_flags": other_flags,
        "signal_sector_flags": sector_flags,
        "signal_all_litigation_flags": all_flags,
        "signal_litigation_critical_count": critical_count,
        "signal_litigation_warning_count": warning_count,
        "signal_defense_summary": defense_signal_summary,
        "signal_litigation_risk_level": risk_level,
        "signal_do_context_map": do_context_map,
        "signal_sca_do_context": sca_do_context,
        "signal_sec_do_context": sec_do_context,
    }


__all__ = ["extract_litigation_evaluative"]
