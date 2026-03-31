"""Tests for audit appendix deduplication (Phase 128-01 Task 2).

Verifies:
1. Passing both inputs produces audit_unified_summary
2. Duplicate entries are consolidated (count < sum of individual counts)
3. Backward-compat keys still present
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from do_uw.stages.render.context_builders.audit import build_audit_context


@dataclass
class _FakeExcludedField:
    path: str
    reason: str


@dataclass
class _FakeHealthIssue:
    category: str
    severity: str
    location: str
    message: str
    snippet: str = ""


@dataclass
class _FakeRenderAudit:
    excluded_fields: list[Any] = field(default_factory=list)
    unrendered_fields: list[str] = field(default_factory=list)
    total_extracted: int = 100
    coverage_pct: float = 85.0
    health_issues: list[Any] = field(default_factory=list)


def _make_disposition_summary(
    *,
    total: int = 50,
    triggered_count: int = 10,
    clean_count: int = 30,
    skipped_count: int = 8,
    inactive_count: int = 2,
    dispositions: list[dict[str, Any]] | None = None,
    by_section: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if dispositions is None:
        dispositions = [
            {"signal_id": "FIN.revenue_growth", "signal_name": "Revenue Growth",
             "disposition": "SKIPPED", "skip_reason": "NO_DATA", "skip_detail": "Missing data",
             "section_prefix": "FIN"},
            {"signal_id": "MKT.beta_extreme", "signal_name": "Beta Extreme",
             "disposition": "TRIGGERED", "evidence": "Beta=2.1",
             "section_prefix": "MKT"},
            {"signal_id": "GOV.board_independence", "signal_name": "Board Independence",
             "disposition": "CLEAN", "section_prefix": "GOV"},
            {"signal_id": "LIT.sca_active", "signal_name": "Active SCA",
             "disposition": "SKIPPED", "skip_reason": "DEFERRED",
             "skip_detail": "Not yet wired", "section_prefix": "LIT"},
        ]
    if by_section is None:
        by_section = {
            "FIN": {"triggered": 3, "clean": 10, "skipped": 3, "inactive": 1},
            "MKT": {"triggered": 4, "clean": 8, "skipped": 2, "inactive": 0},
            "GOV": {"triggered": 2, "clean": 7, "skipped": 2, "inactive": 1},
            "LIT": {"triggered": 1, "clean": 5, "skipped": 1, "inactive": 0},
        }
    return {
        "total": total,
        "triggered_count": triggered_count,
        "clean_count": clean_count,
        "skipped_count": skipped_count,
        "inactive_count": inactive_count,
        "dispositions": dispositions,
        "by_section": by_section,
    }


class TestAuditDedup:
    """Test unified audit summary with deduplication."""

    def test_unified_summary_present_when_render_audit_given(self):
        """Passing both disposition_summary and render_audit produces audit_unified_summary."""
        disp = _make_disposition_summary()
        render_audit = _FakeRenderAudit(
            unrendered_fields=["fin.revenue.growth_rate", "mkt.beta.raw"],
            total_extracted=100,
            coverage_pct=85.0,
        )
        result = build_audit_context(disp, render_audit=render_audit)

        assert "audit_unified_summary" in result
        assert "audit_dedup_savings" in result
        summary = result["audit_unified_summary"]
        assert summary["total_signals_checked"] == 50
        assert summary["total_fields_extracted"] == 100
        assert summary["coverage_pct"] == 85.0
        assert isinstance(summary["combined_issues"], list)

    def test_dedup_reduces_count(self):
        """Duplicate entries are consolidated -- combined count < sum of individual."""
        disp = _make_disposition_summary()
        # These unrendered fields overlap with FIN.revenue_growth and MKT.beta_extreme signals
        render_audit = _FakeRenderAudit(
            unrendered_fields=[
                "fin.revenue.growth_rate",  # overlaps with FIN.revenue_growth signal
                "mkt.beta.raw_value",       # overlaps with MKT.beta_extreme signal
                "other.completely.unique",  # no overlap
            ],
            health_issues=[
                _FakeHealthIssue(
                    category="data_quality",
                    severity="warning",
                    location="mkt.beta_extreme.value",  # overlaps with triggered signal
                    message="Stale data",
                ),
                _FakeHealthIssue(
                    category="data_quality",
                    severity="info",
                    location="other.field",
                    message="Minor issue",
                ),
            ],
        )
        result = build_audit_context(disp, render_audit=render_audit)
        savings = result["audit_dedup_savings"]
        assert savings > 0, "Should have deduplicated at least one entry"

        # The combined issues should be less than raw sum
        summary = result["audit_unified_summary"]
        # Raw: 1 skipped signal + 3 unrendered + 2 health = 6
        # After dedup: some unrendered and health entries should be removed
        assert summary["combined_issue_count"] < 6

    def test_backward_compat_keys_preserved(self):
        """All existing audit_* keys remain when render_audit is given."""
        disp = _make_disposition_summary()
        render_audit = _FakeRenderAudit()
        result = build_audit_context(disp, render_audit=render_audit)

        # All backward-compat keys must be present
        required_keys = [
            "audit_total", "audit_triggered", "audit_clean",
            "audit_skipped", "audit_deferred", "audit_inactive",
            "audit_checked", "audit_section_breakdown",
            "audit_skipped_signals", "audit_deferred_signals",
            "audit_triggered_signals",
        ]
        for key in required_keys:
            assert key in result, f"Missing backward-compat key: {key}"

    def test_no_render_audit_no_unified_summary(self):
        """Without render_audit, no unified summary is added."""
        disp = _make_disposition_summary()
        result = build_audit_context(disp)
        assert "audit_unified_summary" not in result
        assert "audit_dedup_savings" not in result

    def test_empty_disposition_with_render_audit(self):
        """Empty disposition + render_audit still produces unified summary."""
        render_audit = _FakeRenderAudit(
            unrendered_fields=["some.field"],
            total_extracted=50,
            coverage_pct=70.0,
        )
        result = build_audit_context(None, render_audit=render_audit)
        assert "audit_unified_summary" in result
        assert result["audit_total"] == 0  # backward compat still works
        summary = result["audit_unified_summary"]
        assert summary["total_signals_checked"] == 0
        assert summary["total_fields_extracted"] == 50

    def test_combined_issues_types(self):
        """Combined issues have correct type labels."""
        disp = _make_disposition_summary()
        render_audit = _FakeRenderAudit(
            unrendered_fields=["unique.field.path"],
            health_issues=[
                _FakeHealthIssue(
                    category="quality",
                    severity="warning",
                    location="unique.location",
                    message="Test issue",
                ),
            ],
        )
        result = build_audit_context(disp, render_audit=render_audit)
        summary = result["audit_unified_summary"]
        types = {i["type"] for i in summary["combined_issues"]}
        # Should have at least skipped_signal and unrendered_field types
        assert "skipped_signal" in types
        assert "unrendered_field" in types
