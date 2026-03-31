"""Tests for officer background extraction, serial defendant detection,
date overlap logic, per-insider aggregation.

Covers GOV-01, GOV-02, GOV-05 extraction requirements.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_intelligence import (
    OfficerBackground,
    OfficerSCAExposure,
    PriorCompany,
)
from do_uw.models.market_events import InsiderTransaction


def _sv_str(val: str) -> SourcedValue[str]:
    return SourcedValue(
        value=val,
        source="test",
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _sv_float(val: float) -> SourcedValue[float]:
    return SourcedValue(
        value=val,
        source="test",
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _sv_bool(val: bool) -> SourcedValue[bool]:
    return SourcedValue(
        value=val,
        source="test",
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


class TestExtractPriorCompaniesFromBio:
    """Test regex extraction of prior companies from bio text."""

    def test_simple_served_as_pattern(self) -> None:
        from do_uw.stages.extract.officer_background import extract_prior_companies_from_bio

        bio = "Ms. Doe served as CFO of Acme Corp from 2015 to 2020."
        result = extract_prior_companies_from_bio(bio)
        assert len(result) >= 1
        assert any(pc.company_name == "Acme Corp" for pc in result)
        match = [pc for pc in result if pc.company_name == "Acme Corp"][0]
        assert match.role == "CFO"
        assert match.start_year == 2015
        assert match.end_year == 2020

    def test_multiple_companies(self) -> None:
        from do_uw.stages.extract.officer_background import extract_prior_companies_from_bio

        bio = (
            "Mr. Smith served as CEO of Alpha Inc from 2010 to 2015 "
            "and served as CFO of Beta Corp from 2005 to 2009."
        )
        result = extract_prior_companies_from_bio(bio)
        assert len(result) >= 2
        names = {pc.company_name for pc in result}
        assert "Alpha Inc" in names
        assert "Beta Corp" in names

    def test_empty_bio(self) -> None:
        from do_uw.stages.extract.officer_background import extract_prior_companies_from_bio

        assert extract_prior_companies_from_bio("") == []
        assert extract_prior_companies_from_bio("No prior history.") == []


class TestDateRangesOverlap:
    """Test date overlap logic for serial defendant detection."""

    def test_overlap_true(self) -> None:
        from do_uw.stages.extract.officer_background import date_ranges_overlap

        # Officer at company 2015-2020, class period 2018-03 to 2019-11
        assert date_ranges_overlap(2015, 2020, "2018-03-15", "2019-11-30") is True

    def test_overlap_false_before(self) -> None:
        from do_uw.stages.extract.officer_background import date_ranges_overlap

        # Officer left in 2014, class period starts 2018
        assert date_ranges_overlap(2010, 2014, "2018-03-15", "2019-11-30") is False

    def test_overlap_false_after(self) -> None:
        from do_uw.stages.extract.officer_background import date_ranges_overlap

        # Officer started 2021, class period ends 2019
        assert date_ranges_overlap(2021, 2023, "2018-03-15", "2019-11-30") is False

    def test_overlap_edge_same_year(self) -> None:
        from do_uw.stages.extract.officer_background import date_ranges_overlap

        # Officer tenure ends 2018, class starts 2018-03
        # officer_end = 2018-12-31 >= class_start 2018-03-15 = overlap
        assert date_ranges_overlap(2015, 2018, "2018-03-15", "2019-11-30") is True

    def test_overlap_single_year_tenure(self) -> None:
        from do_uw.stages.extract.officer_background import date_ranges_overlap

        # Officer there only in 2019
        assert date_ranges_overlap(2019, 2019, "2018-03-15", "2019-11-30") is True

    def test_none_dates_graceful(self) -> None:
        from do_uw.stages.extract.officer_background import date_ranges_overlap

        # Empty/None class period dates should return False
        assert date_ranges_overlap(2015, 2020, "", "") is False
        assert date_ranges_overlap(2015, 2020, "", "2019-11-30") is False


class TestDetectSerialDefendants:
    """Test serial defendant detection via SCA cross-reference."""

    def test_serial_defendant_flagged(self) -> None:
        from do_uw.stages.extract.officer_background import detect_serial_defendants

        officers = [
            OfficerBackground(
                name="Jane Doe",
                title="CFO",
                prior_companies=[
                    PriorCompany(
                        company_name="FailCo",
                        role="CFO",
                        years="2015-2020",
                        start_year=2015,
                        end_year=2020,
                    )
                ],
            )
        ]
        sca_results = [
            {
                "company_name": "FailCo Inc",
                "filing_date": "2019-06-15",
                "class_period_start": "2018-03-15",
                "class_period_end": "2019-11-30",
                "settlement_amount_m": 25.0,
                "case_summary": "In re FailCo Securities Litigation",
            }
        ]
        result = detect_serial_defendants(officers, sca_results)
        assert len(result) == 1
        assert result[0].is_serial_defendant is True
        assert len(result[0].sca_exposures) >= 1

    def test_no_serial_defendant_no_overlap(self) -> None:
        from do_uw.stages.extract.officer_background import detect_serial_defendants

        officers = [
            OfficerBackground(
                name="John Smith",
                title="CEO",
                prior_companies=[
                    PriorCompany(
                        company_name="GoodCo",
                        role="CEO",
                        years="2010-2014",
                        start_year=2010,
                        end_year=2014,
                    )
                ],
            )
        ]
        sca_results = [
            {
                "company_name": "GoodCo",
                "filing_date": "2019-06-15",
                "class_period_start": "2018-03-15",
                "class_period_end": "2019-11-30",
            }
        ]
        result = detect_serial_defendants(officers, sca_results)
        assert result[0].is_serial_defendant is False

    def test_empty_inputs(self) -> None:
        from do_uw.stages.extract.officer_background import detect_serial_defendants

        assert detect_serial_defendants([], []) == []
        officers = [OfficerBackground(name="Test", title="CEO")]
        result = detect_serial_defendants(officers, [])
        assert result[0].is_serial_defendant is False


class TestAssessSuitability:
    """Test suitability assessment (data completeness indicator)."""

    def test_high_suitability(self) -> None:
        from do_uw.stages.extract.officer_background import assess_suitability

        officer = OfficerBackground(name="Test", title="CEO")
        level, reason = assess_suitability(officer, has_full_bio=True, has_litigation_search=True)
        assert level == "HIGH"

    def test_medium_suitability(self) -> None:
        from do_uw.stages.extract.officer_background import assess_suitability

        officer = OfficerBackground(name="Test", title="CEO")
        level, reason = assess_suitability(officer, has_full_bio=True, has_litigation_search=False)
        assert level == "MEDIUM"

    def test_low_suitability(self) -> None:
        from do_uw.stages.extract.officer_background import assess_suitability

        officer = OfficerBackground(name="Test", title="CEO")
        level, reason = assess_suitability(officer, has_full_bio=False, has_litigation_search=False)
        assert level == "LOW"


class TestAggregatePerInsider:
    """Test per-insider transaction aggregation."""

    def _make_tx(
        self,
        name: str,
        tx_type: str = "SELL",
        code: str = "S",
        value: float = 10000.0,
        date: str = "2025-06-15",
        is_10b5_1: bool = False,
        title: str = "CEO",
    ) -> InsiderTransaction:
        return InsiderTransaction(
            insider_name=_sv_str(name),
            title=_sv_str(title),
            transaction_date=_sv_str(date),
            transaction_type=tx_type,
            transaction_code=code,
            total_value=_sv_float(value),
            is_10b5_1=_sv_bool(is_10b5_1),
            is_director=False,
            is_officer=True,
        )

    def test_basic_aggregation(self) -> None:
        from do_uw.stages.extract.officer_background import aggregate_per_insider

        txs = [
            self._make_tx("John Smith", value=50000.0, date="2025-01-15"),
            self._make_tx("John Smith", value=30000.0, date="2025-03-20"),
            self._make_tx("Jane Doe", value=100000.0, date="2025-02-10"),
        ]
        result = aggregate_per_insider(txs)
        assert len(result) == 2
        # Sorted by total_sold descending
        assert result[0].name == "Jane Doe"
        assert result[0].total_sold_usd == 100000.0
        assert result[1].name == "John Smith"
        assert result[1].total_sold_usd == 80000.0

    def test_10b5_1_detection(self) -> None:
        from do_uw.stages.extract.officer_background import aggregate_per_insider

        txs = [
            self._make_tx("Test Person", is_10b5_1=True, value=10000.0),
            self._make_tx("Test Person", is_10b5_1=False, value=5000.0),
        ]
        result = aggregate_per_insider(txs)
        assert len(result) == 1
        assert result[0].has_10b5_1 is True

    def test_compensation_codes_excluded(self) -> None:
        from do_uw.stages.extract.officer_background import aggregate_per_insider

        txs = [
            self._make_tx("John Smith", value=50000.0, code="S"),
            self._make_tx("John Smith", value=10000.0, code="A"),  # Award - excluded
            self._make_tx("John Smith", value=5000.0, code="F"),  # Tax withhold - excluded
        ]
        result = aggregate_per_insider(txs)
        assert len(result) == 1
        assert result[0].total_sold_usd == 50000.0
        assert result[0].tx_count == 1

    def test_pct_os_calculation(self) -> None:
        from do_uw.stages.extract.officer_background import aggregate_per_insider

        txs = [
            self._make_tx("Test", value=100000.0),
        ]
        # 100k shares at some price; shares_outstanding = 1_000_000
        # We need to set shares for proper calc
        txs[0].shares = _sv_float(1000.0)
        result = aggregate_per_insider(txs, shares_outstanding=1_000_000.0)
        assert len(result) == 1
        assert result[0].total_sold_pct_os is not None

    def test_empty_transactions(self) -> None:
        from do_uw.stages.extract.officer_background import aggregate_per_insider

        assert aggregate_per_insider([]) == []

    def test_only_buys_included(self) -> None:
        from do_uw.stages.extract.officer_background import aggregate_per_insider

        txs = [
            self._make_tx("Buyer", tx_type="BUY", code="P", value=50000.0),
        ]
        # BUY transactions should not appear in sell aggregation
        result = aggregate_per_insider(txs)
        assert len(result) == 0
