"""Tests for Phase 3 extraction foundation: validation, XBRL resolver, Company Facts.

Tests the extraction validation framework (ExtractionReport), XBRL
concept resolver (xbrl_mapping), and Company Facts acquisition
(SECFilingClient.acquire_company_facts).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from do_uw.models.common import Confidence
from do_uw.stages.extract.validation import (
    create_report,
    log_report,
    merge_reports,
    validate_no_imputation,
)
from do_uw.stages.extract.xbrl_mapping import (
    extract_concept_value,
    get_latest_value,
    get_period_values,
    load_xbrl_mapping,
    resolve_concept,
)

# -----------------------------------------------------------------------
# Extraction validation framework tests
# -----------------------------------------------------------------------


class TestExtractionReportFullCoverage:
    """100% coverage produces HIGH confidence."""

    def test_full_coverage_high_confidence(self) -> None:
        expected = ["revenue", "net_income", "gross_profit"]
        found = ["revenue", "net_income", "gross_profit"]

        report = create_report(
            extractor_name="income_statement",
            expected=expected,
            found=found,
            source_filing="10-K 2024-02-28 0001193125-24-012345",
        )

        assert report.coverage_pct == 100.0
        assert report.confidence == Confidence.HIGH
        assert report.missing_fields == []
        assert len(report.found_fields) == 3

    def test_full_coverage_with_extras(self) -> None:
        expected = ["revenue", "net_income"]
        found = ["revenue", "net_income", "extra_field"]

        report = create_report(
            extractor_name="income_statement",
            expected=expected,
            found=found,
            source_filing="10-K 2024-02-28 accn",
        )

        assert report.coverage_pct == 100.0
        assert report.confidence == Confidence.HIGH
        assert "extra_field" in report.unexpected_fields


class TestExtractionReportPartialCoverage:
    """50-79% coverage produces MEDIUM confidence."""

    def test_medium_coverage(self) -> None:
        expected = ["revenue", "net_income", "gross_profit", "ebit", "ebitda"]
        found = ["revenue", "net_income", "gross_profit"]

        report = create_report(
            extractor_name="income_statement",
            expected=expected,
            found=found,
            source_filing="10-K 2024-02-28 accn",
        )

        assert report.coverage_pct == 60.0
        assert report.confidence == Confidence.MEDIUM
        assert "ebit" in report.missing_fields
        assert "ebitda" in report.missing_fields


class TestExtractionReportLowCoverage:
    """<50% coverage produces LOW confidence."""

    def test_low_coverage(self) -> None:
        expected = [
            "revenue", "net_income", "gross_profit",
            "ebit", "ebitda", "operating_income",
            "eps_basic", "eps_diluted", "cost_of_revenue",
            "interest_expense",
        ]
        found = ["revenue", "net_income", "gross_profit"]

        report = create_report(
            extractor_name="income_statement",
            expected=expected,
            found=found,
            source_filing="10-K 2024-02-28 accn",
        )

        assert report.coverage_pct == 30.0
        assert report.confidence == Confidence.LOW
        assert len(report.missing_fields) == 7


class TestMergeReports:
    """Multiple reports merge correctly."""

    def test_merge_two_reports(self) -> None:
        r1 = create_report(
            extractor_name="income",
            expected=["revenue", "net_income"],
            found=["revenue", "net_income"],
            source_filing="10-K 2024 accn1",
        )
        r2 = create_report(
            extractor_name="balance_sheet",
            expected=["total_assets", "total_liabilities"],
            found=["total_assets"],
            source_filing="10-K 2024 accn2",
        )

        merged = merge_reports([r1, r2])

        assert "income+balance_sheet" == merged.extractor_name
        assert len(merged.expected_fields) == 4
        assert len(merged.found_fields) == 3
        assert "total_liabilities" in merged.missing_fields
        assert merged.coverage_pct == 75.0
        assert merged.confidence == Confidence.MEDIUM

    def test_merge_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            merge_reports([])


class TestValidateNoImputation:
    """Anti-imputation validation catches fabricated data."""

    def test_no_imputation_clean(self) -> None:
        extracted = {"revenue": 1000, "net_income": 200}
        source = {"revenue": 1000, "net_income": 200, "extra": 500}
        violations = validate_no_imputation(extracted, source)
        assert violations == []

    def test_imputation_detected(self) -> None:
        extracted = {"revenue": 1000, "net_income": 200, "fake_field": 999}
        source = {"revenue": 1000, "net_income": 200}
        violations = validate_no_imputation(extracted, source)
        assert "fake_field" in violations


class TestLogReport:
    """Log report outputs at appropriate level."""

    def test_log_report_does_not_raise(self) -> None:
        report = create_report(
            extractor_name="test",
            expected=["a", "b"],
            found=["a"],
            source_filing="test-filing",
        )
        # Should not raise
        log_report(report)


# -----------------------------------------------------------------------
# XBRL concept resolver tests
# -----------------------------------------------------------------------


def _make_company_facts(
    concept: str, entries: list[dict[str, Any]], unit: str = "USD"
) -> dict[str, Any]:
    """Helper to build a minimal companyfacts response."""
    return {
        "facts": {
            "us-gaap": {
                concept: {
                    "units": {
                        unit: entries,
                    }
                }
            }
        }
    }


class TestLoadXBRLMapping:
    """XBRL mapping table loads correctly."""

    def test_load_mapping(self) -> None:
        mapping = load_xbrl_mapping()
        assert len(mapping) >= 40
        assert "revenue" in mapping
        assert "net_income" in mapping
        assert mapping["revenue"]["unit"] == "USD"
        assert len(mapping["revenue"]["xbrl_tags"]) >= 3


class TestResolveConceptFirstTag:
    """First tag matches, returns data."""

    def test_first_tag_hits(self) -> None:
        facts = _make_company_facts("Revenues", [
            {"val": 1000, "end": "2024-12-31", "fy": 2024, "fp": "FY",
             "form": "10-K", "filed": "2025-02-15"},
        ])
        mapping = load_xbrl_mapping()
        result = resolve_concept(facts, mapping, "revenue")

        assert result is not None
        assert len(result) == 1
        assert result[0]["val"] == 1000


class TestResolveConceptFallbackTag:
    """First tag misses, second matches."""

    def test_fallback_to_second_tag(self) -> None:
        # "Revenues" is NOT in the facts, but the 2nd tag is.
        second_tag = load_xbrl_mapping()["revenue"]["xbrl_tags"][1]
        facts = _make_company_facts(second_tag, [
            {"val": 2000, "end": "2024-12-31", "fy": 2024, "fp": "FY",
             "form": "10-K", "filed": "2025-02-15"},
        ])
        result = resolve_concept(facts, load_xbrl_mapping(), "revenue")

        assert result is not None
        assert result[0]["val"] == 2000


class TestResolveConceptNotFound:
    """No tags match, returns None."""

    def test_no_match(self) -> None:
        facts: dict[str, Any] = {"facts": {"us-gaap": {}}}
        mapping = load_xbrl_mapping()
        result = resolve_concept(facts, mapping, "revenue")
        assert result is None


class TestExtractConceptDeduplication:
    """Duplicate entries are deduplicated."""

    def test_dedup_by_end_fy_fp(self) -> None:
        entries = [
            {"val": 1000, "end": "2024-12-31", "fy": 2024, "fp": "FY",
             "form": "10-K", "filed": "2025-02-15"},
            {"val": 1000, "end": "2024-12-31", "fy": 2024, "fp": "FY",
             "form": "10-K", "filed": "2025-03-01"},  # Later filing, same period
            {"val": 900, "end": "2023-12-31", "fy": 2023, "fp": "FY",
             "form": "10-K", "filed": "2024-02-15"},
        ]
        facts = _make_company_facts("Revenues", entries)
        result = extract_concept_value(facts, "Revenues", "10-K", "USD")

        assert len(result) == 2  # Deduplicated: 2 unique periods
        # Later filing wins for 2024 period
        fy2024 = [e for e in result if e["fy"] == 2024]
        assert len(fy2024) == 1
        assert fy2024[0]["filed"] == "2025-03-01"


class TestGetLatestValue:
    """Returns most recent entry."""

    def test_latest_is_last(self) -> None:
        entries = [
            {"val": 900, "end": "2023-12-31"},
            {"val": 1000, "end": "2024-12-31"},
        ]
        latest = get_latest_value(entries)
        assert latest is not None
        assert latest["val"] == 1000

    def test_empty_returns_none(self) -> None:
        assert get_latest_value([]) is None


class TestGetPeriodValues:
    """Returns correct number of periods."""

    def test_three_periods(self) -> None:
        entries = [
            {"val": 800, "end": "2022-12-31"},
            {"val": 900, "end": "2023-12-31"},
            {"val": 1000, "end": "2024-12-31"},
            {"val": 1100, "end": "2025-12-31"},
        ]
        result = get_period_values(entries, 3)
        assert len(result) == 3
        assert result[0]["val"] == 900
        assert result[-1]["val"] == 1100

    def test_fewer_than_requested(self) -> None:
        entries = [{"val": 1000, "end": "2024-12-31"}]
        result = get_period_values(entries, 3)
        assert len(result) == 1


# -----------------------------------------------------------------------
# Company Facts acquisition tests
# -----------------------------------------------------------------------


class TestSECClientCompanyFacts:
    """Company Facts API acquisition via SECFilingClient."""

    @patch("do_uw.stages.acquire.clients.sec_client.sec_get")
    def test_acquire_company_facts_success(
        self, mock_sec_get: Any
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client import SECFilingClient

        mock_response = {
            "cik": 320193,
            "entityName": "Apple Inc.",
            "facts": {
                "us-gaap": {
                    "Revenues": {
                        "units": {
                            "USD": [
                                {"val": 394328000000, "end": "2024-09-28",
                                 "fy": 2024, "fp": "FY",
                                 "form": "10-K", "filed": "2024-11-01"},
                            ]
                        }
                    }
                }
            },
        }
        mock_sec_get.return_value = mock_response

        client = SECFilingClient()
        result = client.acquire_company_facts("0000320193")

        assert result is not None
        assert result["entityName"] == "Apple Inc."
        mock_sec_get.assert_called_once_with(
            "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
        )

    @patch("do_uw.stages.acquire.clients.sec_client.sec_get")
    def test_acquire_company_facts_404_returns_none(
        self, mock_sec_get: Any
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client import SECFilingClient

        mock_sec_get.side_effect = Exception("404 Not Found")

        client = SECFilingClient()
        result = client.acquire_company_facts("0000000001")

        assert result is None

    @patch("do_uw.stages.acquire.clients.sec_client.sec_get")
    def test_company_facts_url_construction(
        self, mock_sec_get: Any
    ) -> None:
        from do_uw.stages.acquire.clients.sec_client import SECFilingClient

        mock_sec_get.return_value = {"facts": {}}

        client = SECFilingClient()
        client.acquire_company_facts("0000320193")

        expected_url = (
            "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json"
        )
        mock_sec_get.assert_called_with(expected_url)
