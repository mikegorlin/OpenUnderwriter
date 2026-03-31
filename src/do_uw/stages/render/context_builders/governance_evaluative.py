"""Governance evaluative context from signal results.

Extracts board quality, compensation flags, structural governance,
and narrative coherence assessments from GOV.* signal results.
Display data (director lists, holders, departures) stays in governance.py.
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


def _extract_board_quality_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract board quality flags from GOV.BOARD.* signals.

    Returns list of triggered board flags with signal_id, display_level,
    evidence, and threshold_context.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "GOV.BOARD.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_compensation_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract compensation red flags from GOV.PAY.* signals.

    Covers excessive pay, pay-performance disconnect, golden parachutes,
    hedging policy, related-party transactions.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "GOV.PAY.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_structural_governance_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract structural governance flags from GOV.RIGHTS.* signals.

    Covers dual-class stock, classified board, poison pills, supermajority
    requirements, forum selection clauses, and other takeover defenses.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "GOV.RIGHTS.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_governance_effectiveness_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract governance effectiveness flags from GOV.EFFECT.* signals.

    Covers audit committee issues, material weakness, auditor changes,
    ISS scores, late filings, SOX 404 issues.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "GOV.EFFECT.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_insider_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract insider trading flags from GOV.INSIDER.* signals.

    Covers cluster sales, unusual timing, trading pattern deviations,
    option exercise patterns, ownership concentration.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "GOV.INSIDER.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_executive_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract executive risk flags from GOV.EXEC.* signals.

    Covers CEO/CFO profiles, departure context, turnover patterns,
    key person risk, succession status, officer litigation.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "GOV.EXEC.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def _extract_activist_signals(
    signal_results: dict[str, Any] | None,
) -> list[dict[str, str]]:
    """Extract activist risk flags from GOV.ACTIVIST.* signals.

    Covers 13D filings, proxy contests, board seat demands, wolf pack
    activity, consent solicitations, short activism.
    """
    flags: list[dict[str, str]] = []
    views = safe_get_signals_by_prefix(signal_results, "GOV.ACTIVIST.")
    for view in views:
        if view.status == "TRIGGERED":
            flags.append(_view_to_flag(view))
    return flags


def extract_governance_evaluative(
    signal_results: dict[str, Any] | None,
) -> dict[str, Any]:
    """Extract all governance evaluative content from signal results.

    Returns a dict of signal-backed evaluative data to merge into
    the governance context. Keys are prefixed with 'signal_' to
    distinguish from display data.
    """
    board_flags = _extract_board_quality_signals(signal_results)
    comp_flags = _extract_compensation_signals(signal_results)
    structural_flags = _extract_structural_governance_signals(signal_results)
    effectiveness_flags = _extract_governance_effectiveness_signals(signal_results)
    insider_flags = _extract_insider_signals(signal_results)
    exec_flags = _extract_executive_signals(signal_results)
    activist_flags = _extract_activist_signals(signal_results)

    all_flags = (
        board_flags + comp_flags + structural_flags
        + effectiveness_flags + insider_flags + exec_flags + activist_flags
    )

    # Aggregate governance signal summary
    critical_count = sum(1 for f in all_flags if f["display_level"] == "Critical")
    warning_count = sum(1 for f in all_flags if f["display_level"] == "Warning")

    # Board quality signal summary
    board_result = safe_get_result(signal_results, "GOV.BOARD.independence")
    board_quality_summary = ""
    if board_result:
        board_quality_summary = board_result.evidence

    # Build D&O context lookup from all governance signals (not just triggered)
    do_context_map: dict[str, str] = {}
    for prefix in ("GOV.BOARD.", "GOV.PAY.", "GOV.RIGHTS.", "GOV.EFFECT.",
                    "GOV.INSIDER.", "GOV.EXEC.", "GOV.ACTIVIST."):
        for view in safe_get_signals_by_prefix(signal_results, prefix):
            if view.do_context:
                do_context_map[view.signal_id] = view.do_context

    return {
        "signal_board_flags": board_flags,
        "signal_comp_flags": comp_flags,
        "signal_structural_flags": structural_flags,
        "signal_effectiveness_flags": effectiveness_flags,
        "signal_insider_flags": insider_flags,
        "signal_exec_flags": exec_flags,
        "signal_activist_flags": activist_flags,
        "signal_all_governance_flags": all_flags,
        "signal_governance_critical_count": critical_count,
        "signal_governance_warning_count": warning_count,
        "signal_board_quality_summary": board_quality_summary,
        "signal_do_context_map": do_context_map,
    }


__all__ = ["extract_governance_evaluative"]
