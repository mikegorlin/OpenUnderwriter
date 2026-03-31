"""Context builder for render audit appendix (Phase 92 -- REND-01/REND-02).

Transforms a RenderAuditReport into a template-ready dict for the
Data Audit appendix in the HTML worksheet.

Exports:
    build_render_audit_context
"""

from __future__ import annotations

from typing import Any

from do_uw.stages.render.render_audit import RenderAuditReport


def build_render_audit_context(audit: RenderAuditReport) -> dict[str, Any]:
    """Transform RenderAuditReport into template-ready dict.

    Args:
        audit: The computed render audit report.

    Returns:
        Dict with keys: audit_excluded_count, audit_unrendered_count,
        audit_excluded_fields (list of {path, reason}),
        audit_unrendered_fields (list of paths),
        audit_total_extracted, audit_coverage_pct.
    """
    health_issues = getattr(audit, "health_issues", [])
    return {
        "audit_excluded_count": len(audit.excluded_fields),
        "audit_unrendered_count": len(audit.unrendered_fields),
        "audit_excluded_fields": [
            {"path": ef.path, "reason": ef.reason}
            for ef in audit.excluded_fields
        ],
        "audit_unrendered_fields": list(audit.unrendered_fields),
        "audit_total_extracted": audit.total_extracted,
        "audit_coverage_pct": audit.coverage_pct,
        "audit_health_issues": [
            {
                "category": hi.category,
                "severity": hi.severity,
                "location": hi.location,
                "message": hi.message,
                "snippet": hi.snippet,
            }
            for hi in health_issues
        ],
        "audit_health_count": len(health_issues),
    }


__all__ = ["build_render_audit_context"]
