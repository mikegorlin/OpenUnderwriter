"""Tests for >2x XBRL/LLM discrepancy flagging (Phase 128-03, INFRA-05).

Verifies that the XBRL/LLM reconciler detects and flags hallucination-level
divergences (>2x ratio) with DiscrepancyWarning dataclass instances.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.extract.xbrl_llm_reconciler import (
    DiscrepancyWarning,
    ReconciliationReport,
    reconcile_value,
)
from do_uw.stages.render.context_builders.audit import (
    build_reconciliation_audit_context,
)


def _sv(value: float) -> SourcedValue[float]:
    """Helper to create a SourcedValue for testing."""
    return SourcedValue(
        value=value,
        source="XBRL 10-K",
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


# --- Test 1: >2x divergence produces a discrepancy warning ---
class TestDiscrepancyFlagging:
    def test_2_5x_divergence_produces_warning(self) -> None:
        """LLM=1000, XBRL=400 (2.5x) triggers a discrepancy warning."""
        xbrl = _sv(400.0)
        result, messages, _warns = reconcile_value(xbrl, 1000.0, "revenue", "Q1 FY2025")
        assert result is not None
        assert result.value == 400.0  # XBRL wins
        hallucination_msgs = [m for m in messages if "HALLUCINATION_FLAG" in m]
        assert len(hallucination_msgs) == 1
        assert "2.5x" in hallucination_msgs[0]

    # --- Test 2: Sub-threshold does NOT produce warning ---
    def test_1_25x_divergence_no_warning(self) -> None:
        """LLM=500, XBRL=400 (1.25x) does NOT trigger a discrepancy warning."""
        xbrl = _sv(400.0)
        result, messages, _warns = reconcile_value(xbrl, 500.0, "revenue", "Q1 FY2025")
        assert result is not None
        hallucination_msgs = [m for m in messages if "HALLUCINATION_FLAG" in m]
        assert len(hallucination_msgs) == 0

    # --- Test 3: Warning includes concept name and period ---
    def test_warning_contains_concept_and_period(self) -> None:
        """LLM=900, XBRL=400 (2.25x) includes concept and period in message."""
        xbrl = _sv(400.0)
        result, messages, _warns = reconcile_value(xbrl, 900.0, "net_income", "Q3 FY2024")
        hallucination_msgs = [m for m in messages if "HALLUCINATION_FLAG" in m]
        assert len(hallucination_msgs) == 1
        msg = hallucination_msgs[0]
        assert "net_income" in msg
        assert "Q3 FY2024" in msg

    # --- Test 4: ReconciliationReport has discrepancy_warnings field ---
    def test_report_has_discrepancy_warnings_field(self) -> None:
        """ReconciliationReport.discrepancy_warnings is a list of DiscrepancyWarning."""
        report = ReconciliationReport()
        assert hasattr(report, "discrepancy_warnings")
        assert isinstance(report.discrepancy_warnings, list)
        assert len(report.discrepancy_warnings) == 0

    # --- Test 5: reconcile_quarterly accumulates warnings ---
    def test_quarterly_accumulates_warnings(self) -> None:
        """reconcile_quarterly accumulates discrepancy warnings across periods."""
        from do_uw.models.financials import (
            QuarterlyPeriod,
            QuarterlyStatements,
            QuarterlyUpdate,
        )

        # Create XBRL quarters with small revenue
        q1 = QuarterlyPeriod(
            fiscal_year=2025,
            fiscal_quarter=1,
            fiscal_label="Q1 FY2025",
            calendar_period="CY2024Q4",
            period_end="2024-12-28",
            income={"revenue": _sv(100.0)},
        )
        q2 = QuarterlyPeriod(
            fiscal_year=2025,
            fiscal_quarter=2,
            fiscal_label="Q2 FY2025",
            calendar_period="CY2025Q1",
            period_end="2025-03-29",
            income={"revenue": _sv(200.0)},
        )
        xbrl = QuarterlyStatements(quarters=[q1, q2])

        # Create LLM updates with >2x divergence on both
        u1 = QuarterlyUpdate(
            quarter="Q1 FY2025",
            period_end="2024-12-28",
            filing_date="2025-01-30",
            revenue=SourcedValue(
                value=500.0,
                source="LLM",
                confidence=Confidence.MEDIUM,
                as_of=datetime.now(tz=UTC),
            ),
        )
        u2 = QuarterlyUpdate(
            quarter="Q2 FY2025",
            period_end="2025-03-29",
            filing_date="2025-04-30",
            revenue=SourcedValue(
                value=800.0,
                source="LLM",
                confidence=Confidence.MEDIUM,
                as_of=datetime.now(tz=UTC),
            ),
        )

        from do_uw.stages.extract.xbrl_llm_reconciler import reconcile_quarterly

        report = reconcile_quarterly(xbrl, [u1, u2])
        assert len(report.discrepancy_warnings) == 2
        assert all(isinstance(w, DiscrepancyWarning) for w in report.discrepancy_warnings)

    # --- Test 6: XBRL=0, LLM=nonzero flags as discrepancy ---
    def test_xbrl_zero_llm_nonzero_flags(self) -> None:
        """XBRL=0 and LLM=nonzero flags as discrepancy (infinite ratio handled)."""
        xbrl = _sv(0.0)
        result, messages, _warns = reconcile_value(xbrl, 500.0, "eps", "Q1 FY2025")
        hallucination_msgs = [m for m in messages if "HALLUCINATION_FLAG" in m]
        assert len(hallucination_msgs) == 1
        assert "eps" in hallucination_msgs[0]


# --- Test 7-8: build_reconciliation_audit_context ---
class TestReconciliationAuditContext:
    def test_with_warnings(self) -> None:
        """2 warnings returns count=2 and list of dicts."""
        warnings = [
            {
                "concept": "revenue",
                "period": "Q1 FY2025",
                "xbrl_value": 400.0,
                "llm_value": 1000.0,
                "ratio": 2.5,
                "resolution": "XBRL_WINS",
                "message": "test",
            },
            {
                "concept": "net_income",
                "period": "Q2 FY2025",
                "xbrl_value": 100.0,
                "llm_value": 300.0,
                "ratio": 3.0,
                "resolution": "XBRL_WINS",
                "message": "test2",
            },
        ]
        result = build_reconciliation_audit_context(warnings)
        assert result["reconciliation_warning_count"] == 2
        assert len(result["reconciliation_warnings"]) == 2

    def test_empty_warnings(self) -> None:
        """Empty list returns count=0."""
        result = build_reconciliation_audit_context([])
        assert result["reconciliation_warning_count"] == 0
        assert result["reconciliation_warnings"] == []
