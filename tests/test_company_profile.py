"""Tests for company profile extraction (03-02).

Tests the company profile extraction pipeline covering SECT2-01 through
SECT2-11 (except SECT2-09 peer group). Verifies identity enrichment,
revenue segments, geographic footprint, concentration, operational
complexity, business changes, D&O exposure mapping, event timeline,
and anti-imputation guarantees.
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.models.common import Confidence
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.company_profile import (
    extract_company_profile,
)
from do_uw.stages.extract.profile_helpers import (
    extract_concentration,
    extract_geographic_footprint,
)
from do_uw.stages.extract.sourced import sourced_str
from do_uw.stages.extract.validation import create_report

# -----------------------------------------------------------------------
# Test data factories
# -----------------------------------------------------------------------


def _make_identity() -> CompanyIdentity:
    """Build a resolved CompanyIdentity for testing."""
    return CompanyIdentity(
        ticker="TEST",
        legal_name=sourced_str("Test Corp", "SEC EDGAR", Confidence.HIGH),
        cik=sourced_str("0001234567", "SEC EDGAR", Confidence.HIGH),
        sic_code=sourced_str("7372", "SEC EDGAR", Confidence.HIGH),
        sector=sourced_str("TECH", "SEC EDGAR", Confidence.HIGH),
    )


def _make_yfinance_info() -> dict[str, Any]:
    """Build a yfinance-style info dict."""
    return {
        "exchange": "NMS",
        "industry": "Software - Application",
        "fullTimeEmployees": 15000,
        "marketCap": 25_000_000_000,
        "longBusinessSummary": "Test Corp is a leading SaaS provider.",
        "firstTradeDateEpochUtc": 946684800,  # 2000-01-01
    }


def _make_company_facts_with_segments() -> dict[str, Any]:
    """Build Company Facts with 3 revenue segments."""
    return {
        "facts": {
            "us-gaap": {
                "RevenueFromContractWithCustomerExcludingAssessedTax": {
                    "units": {
                        "USD": [
                            {
                                "val": 5_000_000_000,
                                "end": "2024-12-31",
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-02-15",
                                "frame": "CY2024_CloudSegmentMember",
                            },
                            {
                                "val": 3_000_000_000,
                                "end": "2024-12-31",
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-02-15",
                                "frame": "CY2024_LicenseSegmentMember",
                            },
                            {
                                "val": 2_000_000_000,
                                "end": "2024-12-31",
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-02-15",
                                "frame": "CY2024_ServicesSegmentMember",
                            },
                        ]
                    }
                }
            },
            "dei": {
                "EntityFilerCategory": {
                    "units": {
                        "": [
                            {
                                "val": "Large Accelerated Filer",
                                "end": "2024-12-31",
                                "fy": 2024,
                                "fp": "FY",
                            }
                        ]
                    }
                }
            },
        }
    }


def _make_company_facts_no_segments() -> dict[str, Any]:
    """Build Company Facts with no segment data."""
    return {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {
                                "val": 10_000_000_000,
                                "end": "2024-12-31",
                                "fy": 2024,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2025-02-15",
                                "frame": "CY2024",
                            },
                        ]
                    }
                }
            },
            "dei": {},
        }
    }


def _make_filing_texts() -> dict[str, str]:
    """Build sample filing texts with concentration and complexity keywords."""
    item1 = (
        "Test Corp is a leading provider of enterprise software solutions. "
        "The company develops cloud-based applications for businesses. "
        "A single customer represented 25% of revenue in the fiscal year. "
        "The company has a variable interest entity in its financing operations. "
        "Test Corp has Class A and Class B common stock outstanding with "
        "differential voting rights. "
        "The company recently completed the acquisition of SmallCo Inc. "
    )
    item7 = (
        "Revenue increased 15% year over year. "
        "The company restructured its European operations. "
        "The company depends on a single source supplier for key components. "
    )
    return {
        "10-K_item1": item1,
        "10-K_item7": item7,
    }


def _make_exhibit21_html() -> str:
    """Build sample Exhibit 21 HTML table."""
    return """
    <html><body>
    <table>
    <tr><td>Name of Subsidiary</td><td>Jurisdiction</td></tr>
    <tr><td>Test Corp UK Ltd</td><td>United Kingdom</td></tr>
    <tr><td>Test Corp GmbH</td><td>Germany</td></tr>
    <tr><td>Test Corp Ireland</td><td>Ireland</td></tr>
    <tr><td>Test Corp Delaware LLC</td><td>Delaware</td></tr>
    <tr><td>Test Corp Cayman</td><td>Cayman Islands</td></tr>
    <tr><td>Test Corp Singapore Pte</td><td>Singapore</td></tr>
    </table>
    </body></html>
    """


def _make_exhibit21_text() -> str:
    """Build sample Exhibit 21 text format (no HTML table)."""
    return (
        "EXHIBIT 21\n"
        "SUBSIDIARIES OF THE REGISTRANT\n\n"
        "Name of Subsidiary                    State or Country\n"
        "Test Corp West LLC                    California\n"
        "Test Corp East Inc                    New York\n"
        "Test Corp Japan KK                    Japan\n"
        "Test Corp Bermuda Ltd                 Bermuda\n"
    )


def _make_eight_k_filings() -> list[dict[str, str]]:
    """Build sample 8-K filing list."""
    return [
        {"filing_date": "2024-06-15", "form_type": "8-K"},
        {"filing_date": "2024-03-01", "form_type": "8-K"},
    ]


def _make_test_state(
    *,
    with_segments: bool = True,
    exhibit_21_html: bool = True,
) -> AnalysisState:
    """Build a complete AnalysisState for testing.

    Args:
        with_segments: If True, include XBRL segment data.
        exhibit_21_html: If True, use HTML table format; else text.
    """
    identity = _make_identity()
    profile = CompanyProfile(identity=identity)

    facts = (
        _make_company_facts_with_segments()
        if with_segments
        else _make_company_facts_no_segments()
    )
    exhibit = (
        _make_exhibit21_html()
        if exhibit_21_html
        else _make_exhibit21_text()
    )
    filing_texts = _make_filing_texts()

    filings: dict[str, Any] = {
        "company_facts": facts,
        "filing_texts": filing_texts,
        "exhibit_21": exhibit,
        "8-K": _make_eight_k_filings(),
    }

    market_data: dict[str, Any] = {
        "info": _make_yfinance_info(),
    }

    acquired = AcquiredData(
        filings=filings,
        market_data=market_data,
    )

    return AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=acquired,
    )


# -----------------------------------------------------------------------
# Test 1: Identity enrichment
# -----------------------------------------------------------------------


class TestExtractCompanyProfilePopulatesIdentity:
    """Verify identity enrichment fills exchange, industry, market_cap."""

    def test_identity_fields_populated(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        assert profile.identity.exchange is not None
        assert profile.identity.exchange.value == "NMS"
        assert profile.identity.exchange.confidence == Confidence.MEDIUM

        assert profile.industry_classification is not None
        assert profile.industry_classification.value == "Software - Application"

        assert profile.market_cap is not None
        assert profile.market_cap.value == 25_000_000_000

        assert profile.employee_count is not None
        assert profile.employee_count.value == 15000

    def test_filer_category_from_dei(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        assert profile.filer_category is not None
        assert profile.filer_category.value == "Large Accelerated Filer"
        assert profile.filer_category.confidence == Confidence.HIGH


# -----------------------------------------------------------------------
# Test 2-3: Revenue segments
# -----------------------------------------------------------------------


class TestExtractRevenueSegmentsMatchesFiling:
    """Given XBRL data with 3 segments, verify exactly 3 extracted."""

    def test_three_segments_extracted(self) -> None:
        state = _make_test_state(with_segments=True)
        profile, _report = extract_company_profile(state)

        assert len(profile.revenue_segments) == 3
        segment_names = [
            str(s.value.get("segment", "")) for s in profile.revenue_segments
        ]
        assert "CloudSegmentMember" in segment_names
        assert "LicenseSegmentMember" in segment_names
        assert "ServicesSegmentMember" in segment_names

    def test_segment_values_match(self) -> None:
        state = _make_test_state(with_segments=True)
        profile, _report = extract_company_profile(state)

        values = {
            str(s.value.get("segment", "")): s.value.get("revenue", 0)
            for s in profile.revenue_segments
        }
        assert values["CloudSegmentMember"] == 5_000_000_000
        assert values["LicenseSegmentMember"] == 3_000_000_000
        assert values["ServicesSegmentMember"] == 2_000_000_000


class TestExtractRevenueSegmentsSingleSegment:
    """Company with no segment data returns empty list."""

    def test_no_segments_returns_empty(self) -> None:
        state = _make_test_state(with_segments=False)
        profile, _report = extract_company_profile(state)

        assert profile.revenue_segments == []


# -----------------------------------------------------------------------
# Test 4-5: Geographic footprint
# -----------------------------------------------------------------------


class TestExtractGeographicFootprintHtmlTable:
    """Exhibit 21 with HTML table parsed correctly."""

    def test_html_table_parsed(self) -> None:
        state = _make_test_state(exhibit_21_html=True)
        geo, _report = extract_geographic_footprint(state)

        assert len(geo) > 0
        jurisdictions = [
            str(g.value.get("jurisdiction", "")) for g in geo
        ]
        assert "United Kingdom" in jurisdictions
        assert "Germany" in jurisdictions
        assert "Delaware" in jurisdictions

    def test_tax_haven_flagged(self) -> None:
        state = _make_test_state(exhibit_21_html=True)
        geo, _report = extract_geographic_footprint(state)

        cayman_entries = [
            g for g in geo
            if "cayman" in str(g.value.get("jurisdiction", "")).lower()
        ]
        assert len(cayman_entries) == 1
        assert cayman_entries[0].value.get("tax_haven") == "true"

    def test_subsidiary_count_set(self) -> None:
        state = _make_test_state(exhibit_21_html=True)
        extract_geographic_footprint(state)

        assert state.company is not None
        assert state.company.subsidiary_count is not None
        assert state.company.subsidiary_count.value == 6


class TestExtractGeographicFootprintTextFormat:
    """Exhibit 21 with text format parsed correctly."""

    def test_text_format_parsed(self) -> None:
        state = _make_test_state(exhibit_21_html=False)
        geo, _report = extract_geographic_footprint(state)

        assert len(geo) > 0
        jurisdictions = [
            str(g.value.get("jurisdiction", "")).lower() for g in geo
        ]
        # At least some US states should be detected
        found_any = any(
            j in str(jurisdictions)
            for j in ["california", "new york", "japan", "bermuda"]
        )
        assert found_any, f"Expected jurisdictions not found: {jurisdictions}"


# -----------------------------------------------------------------------
# Test 6: Operational complexity
# -----------------------------------------------------------------------


class TestExtractOperationalComplexityDetectsVIE:
    """Filing text mentioning VIE triggers flags."""

    def test_vie_detected(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        assert profile.operational_complexity is not None
        complexity = profile.operational_complexity.value
        assert complexity["has_vie"] is True

    def test_dual_class_detected(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        assert profile.operational_complexity is not None
        complexity = profile.operational_complexity.value
        assert complexity["has_dual_class"] is True


# -----------------------------------------------------------------------
# Test 7: Customer concentration
# -----------------------------------------------------------------------


class TestExtractCustomerConcentration:
    """Filing text with concentration data extracts correctly."""

    def test_customer_concentration_extracted(self) -> None:
        state = _make_test_state()
        customers, _suppliers, _report = extract_concentration(state)

        assert len(customers) > 0
        pct_values = [c.value.get("revenue_pct", 0) for c in customers]
        assert 25.0 in pct_values

    def test_supplier_concentration_extracted(self) -> None:
        state = _make_test_state()
        _customers, suppliers, _report = extract_concentration(state)

        assert len(suppliers) > 0
        # Should detect the "single source supplier" phrase
        supplier_names = [
            str(s.value.get("supplier", "")) for s in suppliers
        ]
        assert "Sole Source Dependency" in supplier_names


# -----------------------------------------------------------------------
# Test 8: D&O exposure factor mapping
# -----------------------------------------------------------------------


class TestMapDOExposureFactors:
    """Profile with specific attributes maps correct exposure types."""

    def test_exposure_factors_mapped(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        factors = profile.do_exposure_factors
        factor_names = [
            str(f.value.get("factor", "")) for f in factors
        ]

        # Employee count > 10K -> EMPLOYMENT_LITIGATION_RISK
        assert "EMPLOYMENT_LITIGATION_RISK" in factor_names

        # Tech sector -> IP_LITIGATION_RISK
        assert "IP_LITIGATION_RISK" in factor_names

        # M&A activity detected -> TRANSACTION_LITIGATION_RISK
        assert "TRANSACTION_LITIGATION_RISK" in factor_names

    def test_exposure_factors_low_confidence(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        for factor in profile.do_exposure_factors:
            assert factor.confidence == Confidence.LOW

    def test_customer_concentration_risk(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        factor_names = [
            str(f.value.get("factor", "")) for f in profile.do_exposure_factors
        ]
        assert "CUSTOMER_CONCENTRATION_RISK" in factor_names

    def test_international_ops_risk(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        factor_names = [
            str(f.value.get("factor", "")) for f in profile.do_exposure_factors
        ]
        # With 5 non-US out of 6 total, >30% -> REGULATORY_MULTI_JURISDICTION
        assert "REGULATORY_MULTI_JURISDICTION" in factor_names


# -----------------------------------------------------------------------
# Test 9: Extraction report coverage
# -----------------------------------------------------------------------


class TestExtractionReportCoverage:
    """ExtractionReport shows correct coverage counts."""

    def test_merged_report_coverage(self) -> None:
        state = _make_test_state()
        _profile, report = extract_company_profile(state)

        # The merged report should have expected and found fields
        assert len(report.expected_fields) > 0
        assert len(report.found_fields) > 0
        assert report.coverage_pct > 0.0
        assert report.confidence in (
            Confidence.HIGH,
            Confidence.MEDIUM,
            Confidence.LOW,
        )

    def test_individual_report_fields(self) -> None:
        report = create_report(
            extractor_name="test",
            expected=["field_a", "field_b", "field_c"],
            found=["field_a", "field_b"],
            source_filing="test-filing",
        )
        assert abs(report.coverage_pct - 66.7) < 0.1
        assert report.confidence == Confidence.MEDIUM
        assert "field_c" in report.missing_fields


# -----------------------------------------------------------------------
# Test 10: Anti-imputation
# -----------------------------------------------------------------------


class TestNoImputation:
    """Verify empty/missing data returns empty values, never fabricated."""

    def test_empty_acquired_data_no_fabrication(self) -> None:
        """With minimal acquired data, no fields should be fabricated."""
        identity = _make_identity()
        profile = CompanyProfile(identity=identity)

        empty_acquired = AcquiredData(
            filings={},
            market_data={},
        )

        state = AnalysisState(
            ticker="TEST",
            company=profile,
            acquired_data=empty_acquired,
        )

        result_profile, _report = extract_company_profile(state)

        # With no market data, yfinance fields should NOT be populated
        assert result_profile.industry_classification is None
        assert result_profile.market_cap is None
        assert result_profile.employee_count is None

        # With no filing text, business description should be None
        assert result_profile.business_description is None

        # Revenue segments should be empty (not fabricated)
        assert result_profile.revenue_segments == []

        # Geographic footprint should be empty (no Exhibit 21)
        assert result_profile.geographic_footprint == []

        # Operational complexity should be None (no text to analyze)
        assert result_profile.operational_complexity is None

    def test_no_company_raises(self) -> None:
        """extract_company_profile with no company raises ValueError."""
        state = AnalysisState(ticker="TEST")

        with pytest.raises(ValueError, match="CompanyProfile"):
            extract_company_profile(state)

    def test_all_sourced_values_have_source(self) -> None:
        """Every SourcedValue in the result has a non-empty source."""
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        sourced_fields = [
            profile.business_description,
            profile.market_cap,
            profile.employee_count,
            profile.industry_classification,
            profile.filer_category,
            profile.operational_complexity,
            profile.section_summary,
        ]
        for field in sourced_fields:
            if field is not None:
                assert field.source, f"Empty source on {field}"
                assert field.confidence in (
                    Confidence.HIGH,
                    Confidence.MEDIUM,
                    Confidence.LOW,
                )


# -----------------------------------------------------------------------
# Test: Event timeline and section summary
# -----------------------------------------------------------------------


class TestEventTimelineAndSummary:
    """Event timeline and section summary are populated."""

    def test_event_timeline_has_entries(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        assert len(profile.event_timeline) > 0
        # Should include 8-K events
        event_types = [
            str(e.value.get("type", "")) for e in profile.event_timeline
        ]
        assert "material_event" in event_types

    def test_event_timeline_includes_ipo(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        event_types = [
            str(e.value.get("type", "")) for e in profile.event_timeline
        ]
        assert "ipo" in event_types

    def test_event_timeline_sorted(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        dates = [
            str(e.value.get("date", "")) for e in profile.event_timeline
        ]
        assert dates == sorted(dates)

    def test_section_summary_generated(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        assert profile.section_summary is not None
        assert "Test Corp" in profile.section_summary.value
        assert profile.section_summary.confidence == Confidence.LOW


# -----------------------------------------------------------------------
# Test: Business changes
# -----------------------------------------------------------------------


class TestBusinessChanges:
    """Business changes are detected from 8-K and text keywords."""

    def test_business_changes_from_8k(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        assert len(profile.business_changes) > 0
        sources = [c.source for c in profile.business_changes]
        assert any("8-K" in s for s in sources)

    def test_business_changes_from_keywords(self) -> None:
        state = _make_test_state()
        profile, _report = extract_company_profile(state)

        keyword_changes = [
            c for c in profile.business_changes
            if "keyword" in c.value.lower()
        ]
        assert len(keyword_changes) > 0


# -----------------------------------------------------------------------
# Test: Operational complexity flags always reported as found
# -----------------------------------------------------------------------


class TestOperationalComplexityAlwaysFound:
    """Complexity flags are reported as 'found' even when absent."""

    def test_no_complexity_still_reports_found(self) -> None:
        """Company without VIE/dual-class/SPE still has flags as found."""
        identity = _make_identity()
        profile = CompanyProfile(identity=identity)
        filing_texts = {
            "10-K_item1": "Normal company with no complex structures.",
            "10-K_item7": "Revenue increased year over year.",
        }
        filings: dict[str, Any] = {
            "company_facts": _make_company_facts_with_segments(),
            "filing_texts": filing_texts,
            "exhibit_21": _make_exhibit21_html(),
            "8-K": [],
        }
        acquired = AcquiredData(
            filings=filings,
            market_data={"info": _make_yfinance_info()},
        )
        state = AnalysisState(
            ticker="TEST", company=profile, acquired_data=acquired,
        )
        result_profile, report = extract_company_profile(state)

        # All three flags should be in found fields.
        assert "vie_flag" in report.found_fields
        assert "dual_class_flag" in report.found_fields
        assert "spe_flag" in report.found_fields

        # Complexity result should exist with all False values.
        assert result_profile.operational_complexity is not None
        assert result_profile.operational_complexity.value["has_vie"] is False
        assert result_profile.operational_complexity.value["has_dual_class"] is False
        assert result_profile.operational_complexity.value["has_spe"] is False


# -----------------------------------------------------------------------
# Test: Filer category fallback from market cap
# -----------------------------------------------------------------------


class TestFilerCategoryFallback:
    """Filer category inferred from market cap when DEI is absent."""

    def test_large_accelerated_from_market_cap(self) -> None:
        """Market cap > $700M -> Large Accelerated Filer."""
        state = _make_test_state(with_segments=False)
        profile, _report = extract_company_profile(state)

        assert profile.filer_category is not None
        # No DEI in _make_company_facts_no_segments, falls back to market cap
        # market cap is 25B -> Large Accelerated Filer
        assert "Large Accelerated Filer" in profile.filer_category.value

    def test_dei_preferred_over_market_cap(self) -> None:
        """DEI data is preferred when available."""
        state = _make_test_state(with_segments=True)
        profile, _report = extract_company_profile(state)

        assert profile.filer_category is not None
        assert profile.filer_category.source == "SEC EDGAR Company Facts DEI"
        assert profile.filer_category.confidence == Confidence.HIGH


# -----------------------------------------------------------------------
# Test: Revenue segment text fallback
# -----------------------------------------------------------------------


class TestRevenueSegmentTextFallback:
    """Segment revenue parsed from Item 7 text when XBRL lacks segments."""

    def test_text_fallback_extracts_segments(self) -> None:
        """Item 7 with 'segment revenue $XX,XXX' is parsed."""
        identity = _make_identity()
        profile = CompanyProfile(identity=identity)
        filing_texts = {
            "10-K_item1": "Company overview.",
            "10-K_item7": (
                "Total automotive & services segment revenue 82,056 "
                "Energy generation segment revenue 12,771 "
            ),
        }
        filings: dict[str, Any] = {
            "company_facts": _make_company_facts_no_segments(),
            "filing_texts": filing_texts,
            "exhibit_21": _make_exhibit21_html(),
            "8-K": [],
        }
        acquired = AcquiredData(
            filings=filings,
            market_data={"info": _make_yfinance_info()},
        )
        state = AnalysisState(
            ticker="TEST", company=profile, acquired_data=acquired,
        )
        result_profile, report = extract_company_profile(state)

        assert len(result_profile.revenue_segments) == 2
        assert "revenue_segments" in report.found_fields
        assert "10-K_item7_text_parsing" in report.fallbacks_used

    def test_xbrl_preferred_over_text(self) -> None:
        """XBRL segment data is preferred when available."""
        state = _make_test_state(with_segments=True)
        profile, _report = extract_company_profile(state)

        assert len(profile.revenue_segments) == 3
        assert profile.revenue_segments[0].confidence == Confidence.HIGH


# -----------------------------------------------------------------------
# Test: Exhibit 21 continuous (single-line) format
# -----------------------------------------------------------------------


class TestExhibit21ContinuousFormat:
    """Exhibit 21 as single-line text is parsed correctly."""

    def test_continuous_format_parsed(self) -> None:
        """Single-line exhibit 21 extracts subsidiaries."""
        from do_uw.stages.extract.profile_helpers import (
            extract_geographic_footprint,
        )

        identity = _make_identity()
        profile = CompanyProfile(identity=identity)
        exhibit = (
            "Exhibit 21 SUBSIDIARIES OF TEST CORP "
            "Name of Subsidiary Jurisdiction of Incorporation or "
            "Organization "
            "Test Sub LLC Delaware "
            "Test GmbH Germany "
            "Test UK Ltd United Kingdom "
            "Test Canada Inc Canada "
            "Test Cayman Cayman Islands "
        )
        filings: dict[str, Any] = {
            "company_facts": {},
            "filing_texts": {},
            "exhibit_21": exhibit,
            "8-K": [],
        }
        acquired = AcquiredData(
            filings=filings,
            market_data={"info": {}},
        )
        state = AnalysisState(
            ticker="TEST", company=profile, acquired_data=acquired,
        )
        geo, report = extract_geographic_footprint(state)

        assert len(geo) >= 4
        jurisdictions = [
            str(g.value.get("jurisdiction", "")).lower() for g in geo
        ]
        assert any("delaware" in j for j in jurisdictions)
        assert any("germany" in j for j in jurisdictions)
        assert "geographic_footprint" in report.found_fields


# -----------------------------------------------------------------------
# Test: Supplier concentration single-source patterns
# -----------------------------------------------------------------------


class TestSupplierConcentrationSingleSource:
    """Additional single-source supplier patterns are detected."""

    def test_sourced_from_single_suppliers(self) -> None:
        """'sourced from single suppliers' is detected."""
        from do_uw.stages.extract.profile_helpers import (
            extract_concentration,
        )

        identity = _make_identity()
        profile = CompanyProfile(identity=identity)
        filing_texts = {
            "10-K_item1": (
                "Components and systems are sourced from single suppliers."
            ),
        }
        filings: dict[str, Any] = {
            "company_facts": {},
            "filing_texts": filing_texts,
            "exhibit_21": "",
            "8-K": [],
        }
        acquired = AcquiredData(
            filings=filings,
            market_data={"info": {}},
        )
        state = AnalysisState(
            ticker="TEST", company=profile, acquired_data=acquired,
        )
        _customers, suppliers, _report = extract_concentration(state)

        assert len(suppliers) > 0
        supplier_names = [
            str(s.value.get("supplier", "")) for s in suppliers
        ]
        assert "Sole Source Dependency" in supplier_names

    def test_single_source_direct_supplier(self) -> None:
        """'single-source direct suppliers' is detected."""
        from do_uw.stages.extract.profile_helpers import (
            extract_concentration,
        )

        identity = _make_identity()
        profile = CompanyProfile(identity=identity)
        filing_texts = {
            "10-K_item1": (
                "We source from single-source direct suppliers."
            ),
        }
        filings: dict[str, Any] = {
            "company_facts": {},
            "filing_texts": filing_texts,
            "exhibit_21": "",
            "8-K": [],
        }
        acquired = AcquiredData(
            filings=filings,
            market_data={"info": {}},
        )
        state = AnalysisState(
            ticker="TEST", company=profile, acquired_data=acquired,
        )
        _customers, suppliers, _report = extract_concentration(state)

        assert len(suppliers) > 0


# -----------------------------------------------------------------------
# Test: Employee count validation
# -----------------------------------------------------------------------


class TestValidateEmployeeCount:
    """Tests for _validate_employee_count post-extraction validation."""

    def test_truncated_count_detected_via_yfinance(self) -> None:
        """LLM returns 62, yfinance has 62000 -> use yfinance."""
        from do_uw.stages.extract.company_profile_items import (
            _validate_employee_count,
        )

        result = _validate_employee_count(
            llm_count=62,
            revenue=None,
            yfinance_count=62000,
        )
        assert result == 62000

    def test_truncated_count_detected_via_revenue(self) -> None:
        """LLM returns 62, no yfinance, $300B revenue -> 62 * 1000."""
        from do_uw.stages.extract.company_profile_items import (
            _validate_employee_count,
        )

        result = _validate_employee_count(
            llm_count=62,
            revenue=300_000_000_000,
            yfinance_count=None,
        )
        assert result == 62000

    def test_reasonable_count_passes_through(self) -> None:
        """LLM returns 62000, yfinance has 61500 -> keep LLM."""
        from do_uw.stages.extract.company_profile_items import (
            _validate_employee_count,
        )

        result = _validate_employee_count(
            llm_count=62000,
            revenue=300_000_000_000,
            yfinance_count=61500,
        )
        assert result == 62000

    def test_none_llm_falls_back_to_yfinance(self) -> None:
        """LLM returns None -> use yfinance."""
        from do_uw.stages.extract.company_profile_items import (
            _validate_employee_count,
        )

        result = _validate_employee_count(
            llm_count=None,
            revenue=300_000_000_000,
            yfinance_count=62000,
        )
        assert result == 62000

    def test_both_none_returns_none(self) -> None:
        """No LLM or yfinance -> None."""
        from do_uw.stages.extract.company_profile_items import (
            _validate_employee_count,
        )

        result = _validate_employee_count(
            llm_count=None,
            revenue=None,
            yfinance_count=None,
        )
        assert result is None

    def test_small_company_low_count_ok(self) -> None:
        """Small company with 50 employees and $5M revenue is valid."""
        from do_uw.stages.extract.company_profile_items import (
            _validate_employee_count,
        )

        result = _validate_employee_count(
            llm_count=50,
            revenue=5_000_000,
            yfinance_count=None,
        )
        assert result == 50

    def test_yfinance_small_count_skips_ratio_check(self) -> None:
        """yfinance count <= 100 skips ratio check."""
        from do_uw.stages.extract.company_profile_items import (
            _validate_employee_count,
        )

        result = _validate_employee_count(
            llm_count=50,
            revenue=None,
            yfinance_count=50,
        )
        assert result == 50
