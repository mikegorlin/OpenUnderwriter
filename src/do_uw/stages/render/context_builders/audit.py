"""Context builder for signal disposition audit appendix (Phase 78 -- AUDIT-02).

Transforms state.analysis.disposition_summary into template-ready context
for the Signal Disposition Audit appendix in HTML output.

Also provides unified audit summary merging disposition and render audit
data with deduplication (Phase 128-01 Task 2).

Exports:
    build_audit_context
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def build_audit_context(
    disposition_summary: dict[str, Any] | None,
    render_audit: Any | None = None,
) -> dict[str, Any]:
    """Transform disposition_summary into template-ready context.

    Args:
        disposition_summary: The disposition_summary dict from
            state.analysis.disposition_summary (model_dump of DispositionSummary).
            May be None or empty.
        render_audit: Optional RenderAuditReport for unified audit summary.
            When provided, a deduplicated ``audit_unified_summary`` key is added.

    Returns:
        Dict with keys:
        - audit_total, audit_triggered, audit_clean, audit_skipped, audit_inactive
        - audit_checked: triggered + clean (signals actually evaluated)
        - audit_section_breakdown: list of dicts sorted by section prefix
          [{section, triggered, clean, skipped, inactive, total}]
        - audit_skipped_signals: list of dicts for SKIPPED dispositions
          [{signal_id, signal_name, reason, detail, section}]
        - audit_triggered_signals: list of dicts for TRIGGERED dispositions
          [{signal_id, signal_name, evidence, section}]
        - audit_unified_summary: (when render_audit provided) merged summary
        - audit_dedup_savings: (when render_audit provided) count of consolidated entries
    """
    if not disposition_summary:
        ctx = _empty_context()
        if render_audit is not None:
            ctx.update(_build_unified_summary(None, render_audit, [], [], []))
        return ctx

    total = disposition_summary.get("total", 0)
    triggered = disposition_summary.get("triggered_count", 0)
    clean = disposition_summary.get("clean_count", 0)
    skipped = disposition_summary.get("skipped_count", 0)
    inactive = disposition_summary.get("inactive_count", 0)

    # Per-signal lists
    dispositions = disposition_summary.get("dispositions", [])

    # Separate DEFERRED from SKIPPED (Phase 111-03)
    skipped_signals = [
        {
            "signal_id": d.get("signal_id", ""),
            "signal_name": d.get("signal_name", ""),
            "reason": d.get("skip_reason", ""),
            "detail": d.get("skip_detail", ""),
            "section": d.get("section_prefix", ""),
        }
        for d in dispositions
        if d.get("disposition") == "SKIPPED"
        and d.get("skip_reason") != "DEFERRED"
    ]

    deferred_signals = [
        {
            "signal_id": d.get("signal_id", ""),
            "signal_name": d.get("signal_name", ""),
            "reason": d.get("skip_detail", "Data source not yet wired in pipeline"),
            "section": d.get("section_prefix", ""),
        }
        for d in dispositions
        if d.get("disposition") == "SKIPPED"
        and d.get("skip_reason") == "DEFERRED"
    ]

    triggered_signals = [
        {
            "signal_id": d.get("signal_id", ""),
            "signal_name": d.get("signal_name", ""),
            "evidence": d.get("evidence", ""),
            "section": d.get("section_prefix", ""),
        }
        for d in dispositions
        if d.get("disposition") == "TRIGGERED"
    ]

    # Section breakdown from by_section dict
    by_section = disposition_summary.get("by_section", {})
    section_breakdown = []
    for section_prefix in sorted(by_section.keys()):
        sec = by_section[section_prefix]
        t = sec.get("triggered", 0)
        c = sec.get("clean", 0)
        s = sec.get("skipped", 0)
        i = sec.get("inactive", 0)
        section_breakdown.append({
            "section": section_prefix,
            "triggered": t,
            "clean": c,
            "skipped": s,
            "inactive": i,
            "total": t + c + s + i,
        })

    # DEFERRED count: subtract deferred from skipped for accurate display
    deferred_count = len(deferred_signals)
    actual_skipped = skipped - deferred_count

    result = {
        "audit_total": total,
        "audit_triggered": triggered,
        "audit_clean": clean,
        "audit_skipped": actual_skipped,
        "audit_deferred": deferred_count,
        "audit_inactive": inactive,
        "audit_checked": triggered + clean,
        "audit_section_breakdown": section_breakdown,
        "audit_skipped_signals": skipped_signals,
        "audit_deferred_signals": deferred_signals,
        "audit_triggered_signals": triggered_signals,
    }

    if render_audit is not None:
        result.update(_build_unified_summary(
            disposition_summary, render_audit,
            skipped_signals, triggered_signals, deferred_signals,
        ))

    return result


def _signal_id_to_field_prefix(signal_id: str) -> str:
    """Convert signal_id like 'FIN.revenue_growth' to a field path prefix like 'fin.revenue'."""
    parts = signal_id.lower().split(".")
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1].split('_')[0]}"
    return signal_id.lower()


def _build_unified_summary(
    disposition_summary: dict[str, Any] | None,
    render_audit: Any,
    skipped_signals: list[dict[str, Any]],
    triggered_signals: list[dict[str, Any]],
    deferred_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a unified audit summary merging disposition and render audit data.

    Deduplicates entries where:
    - SKIPPED signals and unrendered fields refer to the same data path
    - TRIGGERED signals that also appear as health_issues get merged
    """
    from do_uw.stages.render.context_builders.render_audit import build_render_audit_context

    render_ctx = build_render_audit_context(render_audit)

    # Collect signal ID prefixes for dedup matching
    signal_prefixes: set[str] = set()
    for sig in [*skipped_signals, *triggered_signals, *deferred_signals]:
        sid = sig.get("signal_id", "")
        if sid:
            signal_prefixes.add(_signal_id_to_field_prefix(sid))

    # Deduplicate unrendered fields that overlap with signal dispositions
    unrendered = render_ctx.get("audit_unrendered_fields", [])
    deduplicated_unrendered = []
    dedup_count = 0
    for field_path in unrendered:
        field_lower = field_path.lower()
        matched = False
        for prefix in signal_prefixes:
            if prefix in field_lower or field_lower.startswith(prefix.split(".")[0]):
                matched = True
                break
        if matched:
            dedup_count += 1
        else:
            deduplicated_unrendered.append(field_path)

    # Deduplicate health issues that overlap with triggered signals
    health_issues = render_ctx.get("audit_health_issues", [])
    triggered_ids = {s.get("signal_id", "").lower() for s in triggered_signals}
    deduplicated_health = []
    for issue in health_issues:
        location = (issue.get("location", "") or "").lower()
        matched = any(tid and tid in location for tid in triggered_ids if tid)
        if matched:
            dedup_count += 1
        else:
            deduplicated_health.append(issue)

    # Build unified summary
    total_signals = (disposition_summary or {}).get("total", 0)
    total_fields = render_ctx.get("audit_total_extracted", 0)
    coverage_pct = render_ctx.get("audit_coverage_pct", 0.0)

    # Combined issues list (deduplicated)
    combined_issues: list[dict[str, str]] = []
    for sig in skipped_signals:
        combined_issues.append({
            "type": "skipped_signal",
            "id": sig.get("signal_id", ""),
            "name": sig.get("signal_name", ""),
            "detail": sig.get("reason", ""),
        })
    for field_path in deduplicated_unrendered:
        combined_issues.append({
            "type": "unrendered_field",
            "id": field_path,
            "name": field_path.rsplit(".", 1)[-1] if "." in field_path else field_path,
            "detail": "Extracted but not rendered",
        })
    for issue in deduplicated_health:
        combined_issues.append({
            "type": "health_issue",
            "id": issue.get("location", ""),
            "name": issue.get("category", ""),
            "detail": issue.get("message", ""),
        })

    return {
        "audit_unified_summary": {
            "total_signals_checked": total_signals,
            "total_fields_extracted": total_fields,
            "coverage_pct": coverage_pct,
            "combined_issues": combined_issues,
            "combined_issue_count": len(combined_issues),
        },
        "audit_dedup_savings": dedup_count,
    }


def _empty_context() -> dict[str, Any]:
    """Return safe zero-value defaults when no disposition data is available."""
    return {
        "audit_total": 0,
        "audit_triggered": 0,
        "audit_clean": 0,
        "audit_skipped": 0,
        "audit_deferred": 0,
        "audit_inactive": 0,
        "audit_checked": 0,
        "audit_section_breakdown": [],
        "audit_skipped_signals": [],
        "audit_deferred_signals": [],
        "audit_triggered_signals": [],
    }


def build_reconciliation_audit_context(
    warnings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Transform reconciliation warnings into template-ready audit context.

    Args:
        warnings: List of dicts from state.extracted.financials.reconciliation_warnings

    Returns:
        Dict with keys:
        - reconciliation_warning_count: int
        - reconciliation_warnings: list of dicts with concept/period/xbrl_value/llm_value/ratio/resolution/message
    """
    return {
        "reconciliation_warning_count": len(warnings),
        "reconciliation_warnings": warnings,
    }


__all__ = ["build_audit_context", "build_reconciliation_audit_context"]
