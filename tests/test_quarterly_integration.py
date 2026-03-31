"""Tests for quarterly data integration (Phase 38-03).

Covers:
- Empty state produces no updates
- Pre-annual 10-Q filings are filtered out
- Post-annual 10-Q filings are correctly aggregated
- Multiple quarters are sorted most-recent-first
- SourcedValue wrapping with correct source and confidence
- Legal proceedings converted from ExtractedLegalProceeding to strings
- Model round-trip serialization
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.models.common import Confidence
from do_uw.models.financials import ExtractedFinancials, QuarterlyUpdate
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.quarterly_integration import (
    aggregate_quarterly_updates,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_state(
    *,
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    llm_extractions: dict[str, Any] | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState with acquired data for testing."""
    state = AnalysisState(ticker="TEST")
    state.acquired_data = AcquiredData(
        filing_documents=filing_documents or {},
        llm_extractions=llm_extractions or {},
    )
    return state


def _ten_q_extraction(
    *,
    quarter: str = "Q1 FY2026",
    period_end: str = "2025-12-28",
    revenue: float | None = 100_000_000.0,
    net_income: float | None = 10_000_000.0,
    eps: float | None = 1.50,
    new_legal_proceedings: list[dict[str, Any]] | None = None,
    new_risk_factors: list[dict[str, Any]] | None = None,
    management_discussion_highlights: list[str] | None = None,
    going_concern: bool = False,
    material_weaknesses: list[str] | None = None,
    subsequent_events: list[str] | None = None,
) -> dict[str, Any]:
    """Build a serialized TenQExtraction dict for mock data."""
    return {
        "quarter": quarter,
        "period_end": period_end,
        "revenue": revenue,
        "net_income": net_income,
        "eps": eps,
        "new_legal_proceedings": new_legal_proceedings or [],
        "legal_proceedings_updates": [],
        "going_concern": going_concern,
        "going_concern_detail": None,
        "material_weaknesses": material_weaknesses or [],
        "new_risk_factors": new_risk_factors or [],
        "management_discussion_highlights": management_discussion_highlights or [],
        "subsequent_events": subsequent_events or [],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Test behavior when no data is available."""

    def test_no_acquired_data(self) -> None:
        """State with no acquired_data returns empty list."""
        state = AnalysisState(ticker="TEST")
        result = aggregate_quarterly_updates(state)
        assert result == []

    def test_empty_llm_extractions(self) -> None:
        """State with empty llm_extractions returns empty list."""
        state = _make_state()
        result = aggregate_quarterly_updates(state)
        assert result == []

    def test_no_quarterly_extractions(self) -> None:
        """State with only non-quarterly LLM extractions returns empty."""
        state = _make_state(
            llm_extractions={
                "10-K:000123": {"some": "data"},
                "DEF 14A:000456": {"other": "data"},
            },
        )
        result = aggregate_quarterly_updates(state)
        assert result == []


class TestPreAnnualFiltering:
    """Test that 10-Q filings before the 10-K are filtered out."""

    def test_no_post_annual_10q(self) -> None:
        """10-Q filed before 10-K date returns empty list."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {"accession": "annual001", "filing_date": "2025-11-01"},
                ],
                "10-Q": [
                    {"accession": "q1001", "filing_date": "2025-07-15"},
                    {"accession": "q2001", "filing_date": "2025-04-15"},
                ],
            },
            llm_extractions={
                "10-Q:q1001": _ten_q_extraction(
                    quarter="Q3 FY2025", period_end="2025-06-30",
                ),
                "10-Q:q2001": _ten_q_extraction(
                    quarter="Q2 FY2025", period_end="2025-03-31",
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert result == []

    def test_equal_date_not_included(self) -> None:
        """10-Q with same date as 10-K is not included (must be AFTER)."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {"accession": "annual001", "filing_date": "2025-11-01"},
                ],
                "10-Q": [
                    {"accession": "q1001", "filing_date": "2025-11-01"},
                ],
            },
            llm_extractions={
                "10-Q:q1001": _ten_q_extraction(),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert result == []


class TestPostAnnualExtraction:
    """Test successful extraction of post-annual 10-Q data."""

    def test_post_annual_10q_extracted(self) -> None:
        """10-Q filed after 10-K date produces a QuarterlyUpdate."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {"accession": "annual001", "filing_date": "2025-11-01"},
                ],
                "10-Q": [
                    {"accession": "q1post", "filing_date": "2026-01-30"},
                ],
            },
            llm_extractions={
                "10-Q:q1post": _ten_q_extraction(
                    quarter="Q1 FY2026",
                    period_end="2025-12-28",
                    revenue=120_000_000.0,
                    net_income=15_000_000.0,
                    eps=2.00,
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1
        qu = result[0]
        assert qu.quarter == "Q1 FY2026"
        assert qu.period_end == "2025-12-28"
        assert qu.filing_date == "2026-01-30"
        assert qu.accession == "q1post"

    def test_no_annual_all_kept(self) -> None:
        """If no 10-K exists, all 10-Q extractions are kept."""
        state = _make_state(
            filing_documents={
                "10-Q": [
                    {"accession": "q1001", "filing_date": "2025-07-15"},
                ],
            },
            llm_extractions={
                "10-Q:q1001": _ten_q_extraction(),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1

    def test_6k_extraction_supported(self) -> None:
        """6-K filings are also processed for foreign issuers."""
        state = _make_state(
            filing_documents={
                "20-F": [
                    {"accession": "annual001", "filing_date": "2025-06-01"},
                ],
                "6-K": [
                    {"accession": "fk001", "filing_date": "2025-09-15"},
                ],
            },
            llm_extractions={
                "6-K:fk001": _ten_q_extraction(
                    quarter="Q1 2026", period_end="2025-09-01",
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1
        assert result[0].accession == "fk001"


class TestSorting:
    """Test that multiple quarters are sorted most-recent-first."""

    def test_multiple_quarters_sorted(self) -> None:
        """Q1 and Q2 post-annual are sorted by period_end descending."""
        state = _make_state(
            filing_documents={
                "10-K": [
                    {"accession": "annual001", "filing_date": "2025-11-01"},
                ],
                "10-Q": [
                    {"accession": "q1post", "filing_date": "2026-01-30"},
                    {"accession": "q2post", "filing_date": "2026-04-30"},
                ],
            },
            llm_extractions={
                "10-Q:q1post": _ten_q_extraction(
                    quarter="Q1 FY2026", period_end="2025-12-28",
                ),
                "10-Q:q2post": _ten_q_extraction(
                    quarter="Q2 FY2026", period_end="2026-03-28",
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 2
        assert result[0].quarter == "Q2 FY2026"
        assert result[1].quarter == "Q1 FY2026"
        assert result[0].period_end > result[1].period_end


class TestSourcedValueWrapping:
    """Test SourcedValue wrapping on financial fields."""

    def test_sourced_value_wrapping(self) -> None:
        """Revenue, net_income, eps are wrapped in SourcedValue."""
        state = _make_state(
            filing_documents={
                "10-Q": [
                    {"accession": "q001", "filing_date": "2026-01-30"},
                ],
            },
            llm_extractions={
                "10-Q:q001": _ten_q_extraction(
                    revenue=100_000_000.0,
                    net_income=10_000_000.0,
                    eps=1.50,
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1
        qu = result[0]

        assert qu.revenue is not None
        assert qu.revenue.value == 100_000_000.0
        assert qu.revenue.source == "10-Q:q001"
        assert qu.revenue.confidence == Confidence.HIGH

        assert qu.net_income is not None
        assert qu.net_income.value == 10_000_000.0
        assert qu.net_income.source == "10-Q:q001"
        assert qu.net_income.confidence == Confidence.HIGH

        assert qu.eps is not None
        assert qu.eps.value == 1.50
        assert qu.eps.source == "10-Q:q001"
        assert qu.eps.confidence == Confidence.HIGH

    def test_none_values_not_wrapped(self) -> None:
        """None financial values stay as None (not SourcedValue(None))."""
        state = _make_state(
            filing_documents={
                "10-Q": [
                    {"accession": "q001", "filing_date": "2026-01-30"},
                ],
            },
            llm_extractions={
                "10-Q:q001": _ten_q_extraction(
                    revenue=None, net_income=None, eps=None,
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1
        assert result[0].revenue is None
        assert result[0].net_income is None
        assert result[0].eps is None


class TestLegalConversion:
    """Test legal proceedings conversion from structured to strings."""

    def test_legal_proceedings_converted(self) -> None:
        """ExtractedLegalProceeding objects convert to descriptive strings."""
        state = _make_state(
            filing_documents={
                "10-Q": [
                    {"accession": "q001", "filing_date": "2026-01-30"},
                ],
            },
            llm_extractions={
                "10-Q:q001": _ten_q_extraction(
                    new_legal_proceedings=[
                        {
                            "case_name": "Smith v. TestCorp",
                            "allegations": "Securities fraud (10b-5)",
                            "court": "S.D.N.Y.",
                        },
                        {
                            "case_name": "DOJ v. TestCorp",
                            "allegations": "Antitrust violations",
                        },
                    ],
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1
        procs = result[0].new_legal_proceedings
        assert len(procs) == 2
        assert "Smith v. TestCorp" in procs[0]
        assert "Securities fraud (10b-5)" in procs[0]
        assert "DOJ v. TestCorp" in procs[1]

    def test_risk_factors_converted(self) -> None:
        """ExtractedRiskFactor objects convert to title strings."""
        state = _make_state(
            filing_documents={
                "10-Q": [
                    {"accession": "q001", "filing_date": "2026-01-30"},
                ],
            },
            llm_extractions={
                "10-Q:q001": _ten_q_extraction(
                    new_risk_factors=[
                        {"title": "AI regulatory risk", "category": "AI"},
                        {"title": "Cybersecurity incident risk", "category": "CYBER"},
                    ],
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1
        risks = result[0].new_risk_factors
        assert len(risks) == 2
        assert "AI regulatory risk" in risks
        assert "Cybersecurity incident risk" in risks


class TestModelRoundTrip:
    """Test QuarterlyUpdate serialization and deserialization."""

    def test_model_round_trip(self) -> None:
        """QuarterlyUpdate serializes and deserializes correctly."""
        state = _make_state(
            filing_documents={
                "10-Q": [
                    {"accession": "q001", "filing_date": "2026-01-30"},
                ],
            },
            llm_extractions={
                "10-Q:q001": _ten_q_extraction(
                    revenue=100_000_000.0,
                    going_concern=True,
                    material_weaknesses=["Internal controls over financial reporting"],
                    management_discussion_highlights=["Revenue declined 8%"],
                    subsequent_events=["Acquired XYZ Corp for $500M"],
                ),
            },
        )
        result = aggregate_quarterly_updates(state)
        assert len(result) == 1

        # Serialize
        qu = result[0]
        data = qu.model_dump(mode="json")

        # Deserialize
        restored = QuarterlyUpdate.model_validate(data)

        assert restored.quarter == qu.quarter
        assert restored.period_end == qu.period_end
        assert restored.going_concern is True
        assert restored.material_weaknesses == [
            "Internal controls over financial reporting"
        ]
        assert restored.md_a_highlights == ["Revenue declined 8%"]
        assert restored.subsequent_events == ["Acquired XYZ Corp for $500M"]
        assert restored.revenue is not None
        assert restored.revenue.value == 100_000_000.0

    def test_extracted_financials_with_quarterly(self) -> None:
        """ExtractedFinancials serializes with quarterly_updates."""
        ef = ExtractedFinancials()
        assert ef.quarterly_updates == []

        qu = QuarterlyUpdate(
            quarter="Q1 FY2026",
            period_end="2025-12-28",
            filing_date="2026-01-30",
        )
        ef.quarterly_updates = [qu]

        data = ef.model_dump(mode="json")
        restored = ExtractedFinancials.model_validate(data)
        assert len(restored.quarterly_updates) == 1
        assert restored.quarterly_updates[0].quarter == "Q1 FY2026"
