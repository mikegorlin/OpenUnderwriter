"""Tests for quarterly XBRL extraction models and logic.

Covers:
- QuarterlyPeriod / QuarterlyStatements model instantiation
- ExtractedFinancials.quarterly_xbrl field
- Frame-based YTD disambiguation (select_standalone_quarters)
- Fiscal period alignment (non-calendar FY companies)
- SourcedValue provenance
- Edge cases (empty data, deduplication)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    ExtractedFinancials,
    QuarterlyPeriod,
    QuarterlyStatements,
)


# ---------------------------------------------------------------------------
# Task 1: Model instantiation tests
# ---------------------------------------------------------------------------


class TestQuarterlyPeriod:
    """Test QuarterlyPeriod model creation and fields."""

    def test_basic_instantiation(self) -> None:
        """QuarterlyPeriod can be created with required fields + empty dicts."""
        qp = QuarterlyPeriod(
            fiscal_year=2025,
            fiscal_quarter=1,
            fiscal_label="Q1 FY2025",
            calendar_period="CY2024Q4",
            period_end="2024-12-28",
        )
        assert qp.fiscal_year == 2025
        assert qp.fiscal_quarter == 1
        assert qp.fiscal_label == "Q1 FY2025"
        assert qp.calendar_period == "CY2024Q4"
        assert qp.period_end == "2024-12-28"
        assert qp.income == {}
        assert qp.balance == {}
        assert qp.cash_flow == {}

    def test_period_start_optional(self) -> None:
        """period_start is optional (None for instant-only quarters)."""
        qp = QuarterlyPeriod(
            fiscal_year=2025,
            fiscal_quarter=1,
            fiscal_label="Q1 FY2025",
            calendar_period="CY2024Q4",
            period_end="2024-12-28",
        )
        assert qp.period_start is None

    def test_with_statement_data(self) -> None:
        """QuarterlyPeriod holds SourcedValue dicts for each statement type."""
        sv = SourcedValue[float](
            value=1_000_000.0,
            source="XBRL:10-Q:2024-12-28:CIK320193:accn:0000320193-25-000001",
            confidence=Confidence.HIGH,
            as_of=datetime(2024, 12, 28, tzinfo=UTC),
        )
        qp = QuarterlyPeriod(
            fiscal_year=2025,
            fiscal_quarter=1,
            fiscal_label="Q1 FY2025",
            calendar_period="CY2024Q4",
            period_end="2024-12-28",
            period_start="2024-09-29",
            income={"revenue": sv},
            balance={"total_assets": sv},
            cash_flow={"operating_cash_flow": sv},
        )
        assert qp.income["revenue"].value == 1_000_000.0
        assert qp.balance["total_assets"].confidence == Confidence.HIGH
        assert qp.period_start == "2024-09-29"


class TestQuarterlyStatements:
    """Test QuarterlyStatements container model."""

    def test_holds_up_to_8_quarters(self) -> None:
        """QuarterlyStatements accepts a list of up to 8 QuarterlyPeriod."""
        quarters = [
            QuarterlyPeriod(
                fiscal_year=2025,
                fiscal_quarter=i % 4 + 1,
                fiscal_label=f"Q{i % 4 + 1} FY2025",
                calendar_period=f"CY2024Q{i % 4 + 1}",
                period_end=f"2024-0{i + 1}-28",
            )
            for i in range(8)
        ]
        qs = QuarterlyStatements(
            quarters=quarters,
            concepts_resolved=50,
            concepts_attempted=60,
        )
        assert len(qs.quarters) == 8
        assert qs.concepts_resolved == 50
        assert qs.concepts_attempted == 60

    def test_fiscal_year_end_month_and_extraction_date(self) -> None:
        """QuarterlyStatements has fiscal_year_end_month and extraction_date."""
        qs = QuarterlyStatements(
            quarters=[],
            fiscal_year_end_month=9,
            extraction_date=datetime(2025, 3, 6, tzinfo=UTC),
            concepts_resolved=0,
            concepts_attempted=0,
        )
        assert qs.fiscal_year_end_month == 9
        assert qs.extraction_date is not None
        assert qs.extraction_date.year == 2025

    def test_defaults(self) -> None:
        """QuarterlyStatements has sensible defaults."""
        qs = QuarterlyStatements(
            concepts_resolved=0,
            concepts_attempted=0,
        )
        assert qs.quarters == []
        assert qs.fiscal_year_end_month is None
        assert qs.extraction_date is None


class TestExtractedFinancialsQuarterlyField:
    """Test that ExtractedFinancials has quarterly_xbrl field."""

    def test_quarterly_xbrl_default_none(self) -> None:
        """quarterly_xbrl defaults to None."""
        ef = ExtractedFinancials()
        assert ef.quarterly_xbrl is None

    def test_quarterly_xbrl_accepts_quarterly_statements(self) -> None:
        """quarterly_xbrl can hold a QuarterlyStatements instance."""
        qs = QuarterlyStatements(
            quarters=[],
            concepts_resolved=10,
            concepts_attempted=20,
        )
        ef = ExtractedFinancials(quarterly_xbrl=qs)
        assert ef.quarterly_xbrl is not None
        assert ef.quarterly_xbrl.concepts_resolved == 10


# ---------------------------------------------------------------------------
# Task 2: Extraction logic tests
# ---------------------------------------------------------------------------

from do_uw.stages.extract.xbrl_quarterly import (
    extract_quarterly_xbrl,
    select_standalone_quarters,
)


def _make_entry(
    val: float,
    end: str,
    start: str | None = None,
    fy: int = 2024,
    fp: str = "Q1",
    form: str = "10-Q",
    filed: str = "2024-02-01",
    frame: str | None = None,
    accn: str = "0000320193-24-000001",
) -> dict[str, Any]:
    """Helper to build a synthetic XBRL fact entry."""
    entry: dict[str, Any] = {
        "val": val,
        "end": end,
        "fy": fy,
        "fp": fp,
        "form": form,
        "filed": filed,
        "accn": accn,
    }
    if start is not None:
        entry["start"] = start
    if frame is not None:
        entry["frame"] = frame
    return entry


class TestSelectStandaloneQuarters:
    """Test frame-based YTD disambiguation."""

    def test_duration_filters_by_frame_pattern(self) -> None:
        """Duration entries are selected when frame matches CY####Q# pattern."""
        entries = [
            # Standalone Q1 (has frame)
            _make_entry(100, "2024-03-30", start="2024-01-01", frame="CY2024Q1", fp="Q1"),
            # YTD 6-month (no frame)
            _make_entry(250, "2024-06-29", start="2024-01-01", fp="Q2"),
            # Standalone Q2 (has frame)
            _make_entry(150, "2024-06-29", start="2024-04-01", frame="CY2024Q2", fp="Q2"),
        ]
        result = select_standalone_quarters(entries, "duration")
        assert len(result) == 2
        assert result[0]["frame"] == "CY2024Q1"
        assert result[1]["frame"] == "CY2024Q2"

    def test_instant_filters_by_frame_i_pattern(self) -> None:
        """Instant entries are selected when frame matches CY####Q#I pattern."""
        entries = [
            _make_entry(5000, "2024-03-30", frame="CY2024Q1I", fp="Q1"),
            _make_entry(6000, "2024-06-29", frame="CY2024Q2I", fp="Q2"),
            # Annual entry (should be excluded)
            _make_entry(7000, "2024-12-31", frame="CY2024", fp="FY"),
        ]
        result = select_standalone_quarters(entries, "instant")
        assert len(result) == 2
        assert result[0]["frame"] == "CY2024Q1I"
        assert result[1]["frame"] == "CY2024Q2I"

    def test_dedup_prefers_most_recently_filed(self) -> None:
        """When multiple entries share same frame, prefer most recently filed."""
        entries = [
            _make_entry(100, "2024-03-30", frame="CY2024Q1", filed="2024-04-15"),
            _make_entry(105, "2024-03-30", frame="CY2024Q1", filed="2024-07-20"),  # amended
        ]
        result = select_standalone_quarters(entries, "duration")
        assert len(result) == 1
        assert result[0]["val"] == 105  # amended value wins

    def test_fallback_duration_filter(self) -> None:
        """When no framed entries exist for duration, filter by start/end span."""
        entries = [
            # ~90-day standalone quarter (no frame)
            _make_entry(100, "2024-03-30", start="2024-01-01", fp="Q1"),
            # ~180-day YTD (no frame)
            _make_entry(250, "2024-06-29", start="2024-01-01", fp="Q2"),
            # ~90-day standalone Q2 (no frame)
            _make_entry(150, "2024-06-29", start="2024-04-01", fp="Q2"),
        ]
        result = select_standalone_quarters(entries, "duration")
        assert len(result) == 2
        # Should get the ~90-day entries only
        vals = [r["val"] for r in result]
        assert 100 in vals
        assert 150 in vals
        assert 250 not in vals

    def test_sorted_by_end_date(self) -> None:
        """Results are sorted ascending by end date."""
        entries = [
            _make_entry(200, "2024-06-29", frame="CY2024Q2"),
            _make_entry(100, "2024-03-30", frame="CY2024Q1"),
            _make_entry(300, "2024-09-28", frame="CY2024Q3"),
        ]
        result = select_standalone_quarters(entries, "duration")
        assert [r["end"] for r in result] == ["2024-03-30", "2024-06-29", "2024-09-28"]


def _build_aapl_facts(
    include_frames: bool = True,
) -> dict[str, Any]:
    """Build synthetic Company Facts mimicking AAPL (Sep FY).

    AAPL's fiscal year ends in September.
    Fiscal Q1 = Oct-Dec (calendar Q4).
    """
    revenue_entries: list[dict[str, Any]] = []
    total_assets_entries: list[dict[str, Any]] = []

    # 4 quarters of revenue (duration concept) -- AAPL Sep FY
    quarter_data = [
        # Fiscal Q1 FY2025 = Oct-Dec 2024 = CY2024Q4
        {"val": 124_000, "start": "2024-09-29", "end": "2024-12-28",
         "fy": 2025, "fp": "Q1", "frame": "CY2024Q4", "filed": "2025-01-30"},
        # Fiscal Q2 FY2025 = Jan-Mar 2025 = CY2025Q1
        {"val": 95_000, "start": "2024-12-29", "end": "2025-03-29",
         "fy": 2025, "fp": "Q2", "frame": "CY2025Q1", "filed": "2025-05-01"},
        # Fiscal Q1 FY2024 = Oct-Dec 2023 = CY2023Q4
        {"val": 119_000, "start": "2023-10-01", "end": "2023-12-30",
         "fy": 2024, "fp": "Q1", "frame": "CY2023Q4", "filed": "2024-02-01"},
        # Fiscal Q2 FY2024 = Jan-Mar 2024 = CY2024Q1
        {"val": 91_000, "start": "2023-12-31", "end": "2024-03-30",
         "fy": 2024, "fp": "Q2", "frame": "CY2024Q1", "filed": "2024-05-02"},
    ]

    # Also add a YTD cumulative that should be excluded
    ytd_entry = {
        "val": 219_000, "start": "2024-09-29", "end": "2025-03-29",
        "fy": 2025, "fp": "Q2", "form": "10-Q", "filed": "2025-05-01",
        "accn": "0000320193-25-000002",
    }

    for qd in quarter_data:
        entry: dict[str, Any] = {
            "val": qd["val"],
            "start": qd["start"],
            "end": qd["end"],
            "fy": qd["fy"],
            "fp": qd["fp"],
            "form": "10-Q",
            "filed": qd["filed"],
            "accn": "0000320193-25-000001",
        }
        if include_frames:
            entry["frame"] = qd["frame"]
        revenue_entries.append(entry)

    revenue_entries.append(ytd_entry)

    # Balance sheet (instant concept)
    for qd in quarter_data:
        ta_entry: dict[str, Any] = {
            "val": 350_000 + qd["val"],  # arbitrary
            "end": qd["end"],
            "fy": qd["fy"],
            "fp": qd["fp"],
            "form": "10-Q",
            "filed": qd["filed"],
            "accn": "0000320193-25-000001",
        }
        if include_frames:
            ta_entry["frame"] = qd["frame"] + "I"  # e.g. CY2024Q4I
        total_assets_entries.append(ta_entry)

    return {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {"USD": revenue_entries},
                },
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {"USD": []},
                },
                "Assets": {
                    "units": {"USD": total_assets_entries},
                },
            },
        },
    }


class TestExtractQuarterlyXbrl:
    """Test the main extract_quarterly_xbrl function."""

    def test_returns_quarterly_statements_with_quarters(self) -> None:
        """extract_quarterly_xbrl returns QuarterlyStatements with populated quarters."""
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193", max_quarters=8)
        assert isinstance(result, QuarterlyStatements)
        assert len(result.quarters) > 0
        assert result.concepts_attempted > 0

    def test_fiscal_alignment_aapl(self) -> None:
        """AAPL fiscal Q1 (Oct-Dec) maps to calendar CY####Q4."""
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193")
        # Find the FY2025 Q1 quarter
        q1_fy25 = None
        for q in result.quarters:
            if q.fiscal_year == 2025 and q.fiscal_quarter == 1:
                q1_fy25 = q
                break
        assert q1_fy25 is not None
        assert q1_fy25.calendar_period == "CY2024Q4"
        assert q1_fy25.fiscal_label == "Q1 FY2025"

    def test_sourced_value_provenance(self) -> None:
        """Every SourcedValue has XBRL:10-Q provenance at HIGH confidence."""
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193")
        for q in result.quarters:
            for concept, sv in q.income.items():
                assert "XBRL:10-Q:" in sv.source
                assert "CIK320193" in sv.source
                assert sv.confidence == Confidence.HIGH
            for concept, sv in q.balance.items():
                assert "XBRL:10-Q:" in sv.source
                assert sv.confidence == Confidence.HIGH

    def test_balance_sheet_no_period_start(self) -> None:
        """Balance sheet items (instant) have no period_start on the entry."""
        # period_start on QuarterlyPeriod is for duration concepts.
        # When only instant concepts populate a quarter, period_start may be None.
        # But when mixed, period_start comes from duration entries.
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193")
        # At least some quarters should have period_start set (from duration entries)
        has_start = any(q.period_start is not None for q in result.quarters)
        assert has_start

    def test_empty_facts_returns_empty(self) -> None:
        """Returns empty QuarterlyStatements when no 10-Q data exists."""
        facts: dict[str, Any] = {"facts": {"us-gaap": {}}}
        result = extract_quarterly_xbrl(facts, cik="320193")
        assert isinstance(result, QuarterlyStatements)
        assert len(result.quarters) == 0

    def test_max_quarters_limit(self) -> None:
        """Respects max_quarters parameter."""
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193", max_quarters=2)
        assert len(result.quarters) <= 2

    def test_most_recent_first(self) -> None:
        """Quarters are returned most recent first."""
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193")
        if len(result.quarters) >= 2:
            assert result.quarters[0].period_end >= result.quarters[1].period_end

    def test_ytd_excluded(self) -> None:
        """YTD cumulative entries are excluded from standalone quarters."""
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193")
        # We added a YTD entry with val=219000 -- should not appear
        for q in result.quarters:
            for sv in q.income.values():
                assert sv.value != 219_000

    def test_concepts_resolved_tracked(self) -> None:
        """concepts_resolved and concepts_attempted are tracked."""
        facts = _build_aapl_facts()
        result = extract_quarterly_xbrl(facts, cik="320193")
        assert result.concepts_attempted > 0
        assert result.concepts_resolved > 0
        assert result.concepts_resolved <= result.concepts_attempted
