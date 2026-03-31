"""Composite evaluation engine for brain-layer signal grouping.

Reads member signal results and produces CompositeResults with structured
analytical conclusions. Each composite has a named evaluator function that
contains domain-specific logic.

Key design principle: Composites are graceful with missing data. If a member
signal was SKIPPED or has no details, the composite still produces a result --
it just notes the data gap in its conclusion.

Phase 50 Plan 04: Initial engine with default + 3 stock evaluators.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from do_uw.brain.brain_composite_schema import CompositeDefinition, CompositeResult

logger = logging.getLogger(__name__)


def evaluate_composites(
    composite_defs: dict[str, CompositeDefinition],
    signal_results: dict[str, Any],
) -> dict[str, CompositeResult]:
    """Evaluate all composites against signal results.

    Args:
        composite_defs: Loaded composite definitions keyed by composite_id.
        signal_results: Signal results dict keyed by signal_id.
            Values are dicts with at minimum: status, value, details.

    Returns:
        Dict of composite_id -> CompositeResult.
    """
    results: dict[str, CompositeResult] = {}

    for comp_id, comp_def in composite_defs.items():
        try:
            # Collect member signal results
            member_results: dict[str, dict[str, Any]] = {}
            for sig_id in comp_def.member_signals:
                if sig_id in signal_results:
                    member_results[sig_id] = signal_results[sig_id]

            # Dispatch to named evaluator
            evaluator_fn = _EVALUATORS.get(comp_def.evaluator, _evaluate_default)
            result = evaluator_fn(comp_def, member_results)
            results[comp_id] = result

        except Exception:
            logger.warning(
                "Composite %s evaluation failed; producing CLEAR fallback",
                comp_id,
                exc_info=True,
            )
            results[comp_id] = CompositeResult(
                composite_id=comp_id,
                name=comp_def.name,
                member_results={},
                conclusion={"error": "Evaluation failed"},
                narrative=f"{comp_def.name}: evaluation failed, treating as clear.",
                severity="CLEAR",
                member_count=len(comp_def.member_signals),
                triggered_count=0,
                skipped_count=len(comp_def.member_signals),
            )

    return results


# ---------------------------------------------------------------------------
# Evaluator functions
# ---------------------------------------------------------------------------


def _get_status(result: dict[str, Any]) -> str:
    """Extract status from a signal result dict, defaulting to SKIPPED."""
    return str(result.get("status", "SKIPPED"))


def _get_details(result: dict[str, Any]) -> dict[str, Any]:
    """Extract details from a signal result dict, defaulting to empty."""
    details = result.get("details", {})
    return details if isinstance(details, dict) else {}


def _count_statuses(member_results: dict[str, dict[str, Any]], member_signals: list[str]) -> tuple[int, int, int, int]:
    """Count member statuses. Returns (total, triggered, clear, skipped)."""
    total = len(member_signals)
    triggered = 0
    clear = 0
    skipped = 0
    for sig_id in member_signals:
        status = _get_status(member_results.get(sig_id, {}))
        if status == "TRIGGERED":
            triggered += 1
        elif status == "CLEAR":
            clear += 1
        else:
            skipped += 1
    return total, triggered, clear, skipped


def _evaluate_default(
    definition: CompositeDefinition,
    member_results: dict[str, dict[str, Any]],
) -> CompositeResult:
    """Generic evaluator: count statuses, generate basic narrative.

    Severity:
    - RED: >50% of available (non-skipped) members TRIGGERED
    - YELLOW: >0% of available members TRIGGERED
    - CLEAR: no members TRIGGERED or all SKIPPED
    """
    total, triggered, clear, skipped = _count_statuses(
        member_results, definition.member_signals
    )
    available = total - skipped

    # Determine severity
    if available == 0:
        severity = "CLEAR"
    elif triggered > available * 0.5:
        severity = "RED"
    elif triggered > 0:
        severity = "YELLOW"
    else:
        severity = "CLEAR"

    # Build conclusion
    conclusion: dict[str, Any] = {
        "member_summary": {
            "total": total,
            "triggered": triggered,
            "clear": clear,
            "skipped": skipped,
        },
    }

    # Copy member details into conclusion
    for sig_id in definition.member_signals:
        if sig_id in member_results:
            details = _get_details(member_results[sig_id])
            if details:
                conclusion[sig_id] = details

    # Generate narrative
    if available == 0:
        narrative = f"{definition.name}: no data available ({skipped} member signals skipped)."
    elif triggered == 0:
        narrative = f"{definition.name}: all {available} evaluated signals clear."
    else:
        narrative = (
            f"{definition.name}: {triggered} of {available} evaluated "
            f"signals triggered ({skipped} skipped)."
        )

    return CompositeResult(
        composite_id=definition.id,
        name=definition.name,
        member_results=member_results,
        conclusion=conclusion,
        narrative=narrative,
        severity=severity,
        member_count=total,
        triggered_count=triggered,
        skipped_count=skipped,
    )


def _evaluate_stock_drop(
    definition: CompositeDefinition,
    member_results: dict[str, dict[str, Any]],
) -> CompositeResult:
    """Domain evaluator for COMP.STOCK.drop_analysis.

    Reads details from:
    - STOCK.PRICE.single_day_events: details.events (list of drop events)
    - STOCK.PRICE.attribution: details about company vs sector attribution
    - STOCK.PATTERN.peer_divergence: details about peer gap
    - STOCK.PRICE.recovery: details about post-drop recovery
    - STOCK.INSIDER.cluster_timing: details about insider selling timing

    Falls back to default evaluator if details are not populated.
    """
    total, triggered, clear, skipped = _count_statuses(
        member_results, definition.member_signals
    )

    # Check if we have rich details to analyze
    events_result = member_results.get("STOCK.PRICE.single_day_events", {})
    events_details = _get_details(events_result)
    events = events_details.get("events", [])

    # If no structured details available, fall back to default evaluator
    if not events and not events_details:
        return _evaluate_default(definition, member_results)

    # Extract details from member signals
    attribution_details = _get_details(
        member_results.get("STOCK.PRICE.attribution", {})
    )
    peer_details = _get_details(
        member_results.get("STOCK.PATTERN.peer_divergence", {})
    )
    recovery_details = _get_details(
        member_results.get("STOCK.PRICE.recovery", {})
    )
    insider_details = _get_details(
        member_results.get("STOCK.INSIDER.cluster_timing", {})
    )

    # Group events by pattern
    events_by_pattern: dict[str, list[Any]] = {}
    company_specific_count = 0
    total_events = len(events) if isinstance(events, list) else 0

    for event in (events if isinstance(events, list) else []):
        pattern = "unknown"
        if isinstance(event, dict):
            pattern = event.get("trigger", event.get("pattern", "unknown"))
            if event.get("company_specific", False):
                company_specific_count += 1
        events_by_pattern.setdefault(pattern, []).append(event)

    # Attribution summary
    attribution_summary = attribution_details.get(
        "summary",
        f"{company_specific_count} company-specific, "
        f"{total_events - company_specific_count} sector-wide"
        if total_events > 0
        else "no significant drops",
    )

    # Recovery assessment
    recovery_assessment = recovery_details.get(
        "assessment", "recovery data not available"
    )

    # Insider correlation
    has_insider_correlation = bool(insider_details.get("clusters", []))
    insider_correlation = insider_details.get(
        "summary",
        "insider selling preceded drops" if has_insider_correlation else "no insider correlation detected",
    )

    # Build conclusion
    conclusion: dict[str, Any] = {
        "events_by_pattern": events_by_pattern,
        "attribution_summary": attribution_summary,
        "recovery_assessment": recovery_assessment,
        "insider_correlation": insider_correlation,
        "total_events": total_events,
        "company_specific_events": company_specific_count,
    }

    # Generate narrative
    narrative_parts: list[str] = []
    ticker = events_details.get("ticker", "Company")

    if total_events > 0:
        narrative_parts.append(
            f"{ticker} experienced {total_events} significant drop(s)"
        )
        if company_specific_count > 0:
            pattern_types = sorted(events_by_pattern.keys())
            narrative_parts.append(
                f": {company_specific_count} company-specific "
                f"({', '.join(pattern_types)})"
            )
            sector_count = total_events - company_specific_count
            if sector_count > 0:
                narrative_parts.append(f" and {sector_count} sector-wide")
        narrative_parts.append(". ")
        narrative_parts.append(f"Recovery: {recovery_assessment}. ")
        narrative_parts.append(f"Insider activity: {insider_correlation}.")
    else:
        narrative_parts.append(
            f"{ticker}: no significant drop events detected."
        )

    narrative = "".join(narrative_parts)

    # Severity determination
    if (
        company_specific_count > 0
        and "no recovery" in str(recovery_assessment).lower()
        and has_insider_correlation
    ):
        severity = "RED"
    elif company_specific_count > 0:
        severity = "YELLOW"
    else:
        severity = "CLEAR"

    return CompositeResult(
        composite_id=definition.id,
        name=definition.name,
        member_results=member_results,
        conclusion=conclusion,
        narrative=narrative,
        severity=severity,
        member_count=total,
        triggered_count=triggered,
        skipped_count=skipped,
    )


def _evaluate_stock_short(
    definition: CompositeDefinition,
    member_results: dict[str, dict[str, Any]],
) -> CompositeResult:
    """Domain evaluator for COMP.STOCK.short_analysis.

    Reads details from:
    - STOCK.SHORT.position: short interest as % of float
    - STOCK.SHORT.trend: increasing/decreasing/stable
    - STOCK.SHORT.report: published short seller report presence
    - STOCK.PATTERN.short_attack: coordinated short attack indicators

    Falls back to default evaluator if details not populated.
    """
    total, triggered, clear, skipped = _count_statuses(
        member_results, definition.member_signals
    )

    position_details = _get_details(
        member_results.get("STOCK.SHORT.position", {})
    )
    trend_details = _get_details(
        member_results.get("STOCK.SHORT.trend", {})
    )
    report_details = _get_details(
        member_results.get("STOCK.SHORT.report", {})
    )
    attack_details = _get_details(
        member_results.get("STOCK.PATTERN.short_attack", {})
    )

    # If no details at all, fall back to default
    if not any([position_details, trend_details, report_details, attack_details]):
        return _evaluate_default(definition, member_results)

    # Extract key metrics
    position_level = position_details.get("short_interest_pct", "unknown")
    trend_direction = trend_details.get("direction", "unknown")
    has_report = bool(report_details.get("report_found", False))
    has_attack_pattern = bool(attack_details.get("attack_detected", False))

    # Build conclusion
    conclusion: dict[str, Any] = {
        "position_level": position_level,
        "trend_direction": trend_direction,
        "attack_indicators": has_attack_pattern,
        "report_presence": has_report,
    }

    # Severity
    position_str = str(position_level)
    high_position = False
    if position_str not in ("unknown", ""):
        try:
            high_position = float(position_str) > 10.0
        except (ValueError, TypeError):
            pass

    increasing_trend = str(trend_direction).lower() in ("increasing", "rising")

    if high_position and increasing_trend and has_attack_pattern:
        severity = "RED"
    elif high_position or increasing_trend or has_report:
        severity = "YELLOW"
    else:
        severity = "CLEAR"

    # Narrative
    parts: list[str] = [f"Short interest: {position_level}% of float"]
    parts.append(f", trend {trend_direction}")
    if has_report:
        parts.append(". Published short seller report present")
    if has_attack_pattern:
        parts.append(". Coordinated short attack pattern detected")
    parts.append(".")

    return CompositeResult(
        composite_id=definition.id,
        name=definition.name,
        member_results=member_results,
        conclusion=conclusion,
        narrative="".join(parts),
        severity=severity,
        member_count=total,
        triggered_count=triggered,
        skipped_count=skipped,
    )


def _evaluate_stock_insider(
    definition: CompositeDefinition,
    member_results: dict[str, dict[str, Any]],
) -> CompositeResult:
    """Domain evaluator for COMP.STOCK.insider_analysis.

    Reads details from:
    - STOCK.INSIDER.cluster_timing: insider transaction clusters before events
    - STOCK.INSIDER.notable_activity: large/unusual transactions
    - STOCK.INSIDER.summary: overall insider trading patterns

    Falls back to default evaluator if details not populated.
    """
    total, triggered, clear, skipped = _count_statuses(
        member_results, definition.member_signals
    )

    cluster_details = _get_details(
        member_results.get("STOCK.INSIDER.cluster_timing", {})
    )
    notable_details = _get_details(
        member_results.get("STOCK.INSIDER.notable_activity", {})
    )
    summary_details = _get_details(
        member_results.get("STOCK.INSIDER.summary", {})
    )

    # If no details at all, fall back to default
    if not any([cluster_details, notable_details, summary_details]):
        return _evaluate_default(definition, member_results)

    # Extract key metrics
    clusters = cluster_details.get("clusters", [])
    cluster_count = len(clusters) if isinstance(clusters, list) else 0
    notable_transactions = notable_details.get("transactions", [])
    notable_count = len(notable_transactions) if isinstance(notable_transactions, list) else 0

    # Timing assessment
    has_pre_drop_cluster = any(
        isinstance(c, dict) and c.get("precedes_drop", False)
        for c in (clusters if isinstance(clusters, list) else [])
    )

    # Build conclusion
    conclusion: dict[str, Any] = {
        "cluster_detection": (
            f"{cluster_count} insider transaction cluster(s) detected"
            if cluster_count > 0
            else "no unusual clusters detected"
        ),
        "notable_transactions": (
            f"{notable_count} notable transaction(s)"
            if notable_count > 0
            else "no notable transactions"
        ),
        "timing_assessment": (
            "insider selling cluster precedes price drop"
            if has_pre_drop_cluster
            else "no suspicious timing patterns detected"
        ),
    }

    # Severity
    if has_pre_drop_cluster and cluster_count > 0:
        severity = "RED"
    elif cluster_count > 0 or notable_count > 0:
        severity = "YELLOW"
    else:
        severity = "CLEAR"

    # Narrative
    parts: list[str] = []
    if cluster_count > 0:
        parts.append(
            f"Detected {cluster_count} insider transaction cluster(s)"
        )
        if has_pre_drop_cluster:
            parts.append(" preceding price drops")
    else:
        parts.append("No unusual insider transaction clusters")

    if notable_count > 0:
        parts.append(f". {notable_count} notable transaction(s) flagged")

    parts.append(".")

    return CompositeResult(
        composite_id=definition.id,
        name=definition.name,
        member_results=member_results,
        conclusion=conclusion,
        narrative="".join(parts),
        severity=severity,
        member_count=total,
        triggered_count=triggered,
        skipped_count=skipped,
    )


# ---------------------------------------------------------------------------
# Evaluator registry
# ---------------------------------------------------------------------------

_EVALUATORS: dict[str, Callable[..., CompositeResult]] = {
    "default": _evaluate_default,
    "stock_drop_analysis": _evaluate_stock_drop,
    "stock_short_analysis": _evaluate_stock_short,
    "stock_insider_analysis": _evaluate_stock_insider,
}


__all__ = ["evaluate_composites"]
