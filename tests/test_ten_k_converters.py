"""Unit tests for 10-K converter functions.

Tests all 13 converter functions covering Items 1, 7, 8, and 9A,
verifying SourcedValue wrapping, confidence, source, and edge cases.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.ten_k_converters import (
    convert_business_description,
    convert_competitive_position,
    convert_controls_assessment,
    convert_customer_concentration,
    convert_debt_enrichment,
    convert_employee_count,
    convert_geographic_footprint,
    convert_mda_qualitative,
    convert_operational_complexity_flags,
    convert_regulatory_environment,
    convert_revenue_segments,
    convert_stock_comp_detail,
    convert_supplier_concentration,
)

_SOURCE = "10-K (LLM)"


def _make_extraction(**overrides: Any) -> TenKExtraction:
    """Create a TenKExtraction with realistic TSLA-like data."""
    defaults: dict[str, Any] = {
        "business_description": (
            "Tesla designs, develops, manufactures, and sells "
            "electric vehicles and energy generation and storage systems."
        ),
        "revenue_segments": ["Automotive: 82%", "Energy: 11%", "Services: 7%"],
        "geographic_regions": [
            "United States: 48%",
            "China: 22%",
            "Other: 30%",
        ],
        "employee_count": 140000,
        "customer_concentration": [],
        "supplier_concentration": [
            "Panasonic supplies majority of battery cells"
        ],
        "competitive_position": "Market leader in electric vehicles globally",
        "regulatory_environment": (
            "Subject to NHTSA, EPA, and international automotive regulations"
        ),
        "is_dual_class": False,
        "has_vie": False,
        "revenue_trend": (
            "Revenue increased 12% YoY driven by price reductions "
            "offset by volume growth"
        ),
        "margin_trend": (
            "Gross margin declined from 26% to 18% due to price reductions"
        ),
        "key_financial_concerns": [
            "Margin pressure from pricing strategy and competition"
        ],
        "critical_accounting_estimates": [
            "Revenue recognition for FSD deferred revenue",
            "Warranty reserves",
        ],
        "non_gaap_measures": [
            "Free cash flow",
            "Non-GAAP net income",
            "Adjusted EBITDA",
        ],
        "guidance_language": "No formal guidance provided",
        "debt_instruments": [
            "2024 Convertible Notes: $1.8B at 2.0%",
            "Vehicle financing: $4.8B",
        ],
        "credit_facility_detail": "No revolving credit facility",
        "covenant_status": "No financial covenants",
        "tax_rate_notes": "Effective tax rate 11% due to federal R&D credits",
        "stock_comp_detail": (
            "Stock-based compensation expense $2.1B in FY2025"
        ),
        "has_material_weakness": False,
        "material_weakness_detail": [],
        "significant_deficiencies": [],
        "remediation_status": None,
        "auditor_attestation": (
            "PricewaterhouseCoopers issued unqualified opinion"
        ),
        "auditor_name": "PricewaterhouseCoopers LLP",
        "auditor_tenure_years": 5,
    }
    defaults.update(overrides)
    return TenKExtraction(**defaults)


# ------------------------------------------------------------------
# Item 1: Business
# ------------------------------------------------------------------


class TestConvertBusinessDescription:
    """Tests for convert_business_description."""

    def test_non_empty(self) -> None:
        ext = _make_extraction()
        result = convert_business_description(ext)
        assert result is not None
        assert result.value.startswith("Tesla designs")
        assert result.source == _SOURCE
        assert result.confidence == Confidence.HIGH

    def test_none_input(self) -> None:
        ext = _make_extraction(business_description=None)
        assert convert_business_description(ext) is None

    def test_empty_string(self) -> None:
        ext = _make_extraction(business_description="")
        assert convert_business_description(ext) is None


class TestConvertRevenueSegments:
    """Tests for convert_revenue_segments."""

    def test_parses_colon_format(self) -> None:
        ext = _make_extraction()
        result = convert_revenue_segments(ext)
        assert len(result) == 3
        assert result[0].value == {"segment": "Automotive", "percentage": "82%"}
        assert result[0].source == _SOURCE
        assert result[0].confidence == Confidence.HIGH
        assert result[1].value == {"segment": "Energy", "percentage": "11%"}
        assert result[2].value == {"segment": "Services", "percentage": "7%"}

    def test_empty_list(self) -> None:
        ext = _make_extraction(revenue_segments=[])
        assert convert_revenue_segments(ext) == []

    def test_no_colon_fallback(self) -> None:
        ext = _make_extraction(revenue_segments=["Cloud Services"])
        result = convert_revenue_segments(ext)
        assert len(result) == 1
        assert result[0].value == {"segment": "Cloud Services", "percentage": ""}


class TestConvertGeographicFootprint:
    """Tests for convert_geographic_footprint."""

    def test_parses_regions(self) -> None:
        ext = _make_extraction()
        result = convert_geographic_footprint(ext)
        assert len(result) == 3
        assert result[0].value == {
            "region": "United States",
            "percentage": "48%",
        }
        assert result[0].source == _SOURCE
        assert result[0].confidence == Confidence.HIGH

    def test_empty_list(self) -> None:
        ext = _make_extraction(geographic_regions=[])
        assert convert_geographic_footprint(ext) == []


class TestConvertCustomerConcentration:
    """Tests for convert_customer_concentration."""

    def test_wraps_strings(self) -> None:
        ext = _make_extraction(
            customer_concentration=["Customer A is 15% of revenue"]
        )
        result = convert_customer_concentration(ext)
        assert len(result) == 1
        assert result[0].value == "Customer A is 15% of revenue"
        assert result[0].source == _SOURCE
        assert result[0].confidence == Confidence.HIGH

    def test_empty_list(self) -> None:
        ext = _make_extraction(customer_concentration=[])
        assert convert_customer_concentration(ext) == []


class TestConvertSupplierConcentration:
    """Tests for convert_supplier_concentration."""

    def test_wraps_strings(self) -> None:
        ext = _make_extraction()
        result = convert_supplier_concentration(ext)
        assert len(result) == 1
        assert result[0].value == "Panasonic supplies majority of battery cells"
        assert result[0].source == _SOURCE

    def test_empty_list(self) -> None:
        ext = _make_extraction(supplier_concentration=[])
        assert convert_supplier_concentration(ext) == []


class TestConvertOperationalComplexityFlags:
    """Tests for convert_operational_complexity_flags."""

    def test_both_present(self) -> None:
        ext = _make_extraction(is_dual_class=True, has_vie=True)
        result = convert_operational_complexity_flags(ext)
        assert "has_dual_class" in result
        assert result["has_dual_class"].value is True
        assert result["has_dual_class"].source == _SOURCE
        assert result["has_dual_class"].confidence == Confidence.HIGH
        assert "has_vie" in result
        assert result["has_vie"].value is True

    def test_false_values(self) -> None:
        ext = _make_extraction(is_dual_class=False, has_vie=False)
        result = convert_operational_complexity_flags(ext)
        assert result["has_dual_class"].value is False
        assert result["has_vie"].value is False

    def test_both_none(self) -> None:
        ext = _make_extraction(is_dual_class=None, has_vie=None)
        result = convert_operational_complexity_flags(ext)
        assert result == {}

    def test_partial_none(self) -> None:
        ext = _make_extraction(is_dual_class=True, has_vie=None)
        result = convert_operational_complexity_flags(ext)
        assert "has_dual_class" in result
        assert "has_vie" not in result


class TestConvertEmployeeCount:
    """Tests for convert_employee_count."""

    def test_integer_value(self) -> None:
        ext = _make_extraction()
        result = convert_employee_count(ext)
        assert result is not None
        assert result.value == 140000
        assert result.source == _SOURCE
        assert result.confidence == Confidence.HIGH

    def test_none_value(self) -> None:
        ext = _make_extraction(employee_count=None)
        assert convert_employee_count(ext) is None


class TestConvertCompetitivePosition:
    """Tests for convert_competitive_position."""

    def test_non_empty(self) -> None:
        ext = _make_extraction()
        result = convert_competitive_position(ext)
        assert result is not None
        assert result.value == "Market leader in electric vehicles globally"
        assert result.source == _SOURCE

    def test_none_input(self) -> None:
        ext = _make_extraction(competitive_position=None)
        assert convert_competitive_position(ext) is None


class TestConvertRegulatoryEnvironment:
    """Tests for convert_regulatory_environment."""

    def test_non_empty(self) -> None:
        ext = _make_extraction()
        result = convert_regulatory_environment(ext)
        assert result is not None
        assert "NHTSA" in result.value
        assert result.source == _SOURCE

    def test_none_input(self) -> None:
        ext = _make_extraction(regulatory_environment=None)
        assert convert_regulatory_environment(ext) is None


# ------------------------------------------------------------------
# Item 7: MD&A
# ------------------------------------------------------------------


class TestConvertMdaQualitative:
    """Tests for convert_mda_qualitative."""

    def test_all_fields_populated(self) -> None:
        ext = _make_extraction()
        result = convert_mda_qualitative(ext)

        # Scalar string fields.
        rev = result["revenue_trend"]
        assert isinstance(rev, SourcedValue)
        assert "12% YoY" in rev.value
        assert rev.source == _SOURCE
        assert rev.confidence == Confidence.HIGH

        margin = result["margin_trend"]
        assert isinstance(margin, SourcedValue)
        assert "26% to 18%" in margin.value

        guidance = result["guidance_language"]
        assert isinstance(guidance, SourcedValue)
        assert guidance.value == "No formal guidance provided"

        # List fields.
        concerns = result["key_financial_concerns"]
        assert isinstance(concerns, list)
        assert len(concerns) == 1
        assert concerns[0].value == (
            "Margin pressure from pricing strategy and competition"
        )

        estimates = result["critical_accounting_estimates"]
        assert isinstance(estimates, list)
        assert len(estimates) == 2

        non_gaap = result["non_gaap_measures"]
        assert isinstance(non_gaap, list)
        assert len(non_gaap) == 3

    def test_partial_none(self) -> None:
        ext = _make_extraction(
            revenue_trend=None,
            margin_trend=None,
            guidance_language=None,
            key_financial_concerns=[],
            critical_accounting_estimates=[],
            non_gaap_measures=[],
        )
        result = convert_mda_qualitative(ext)
        assert result["revenue_trend"] is None
        assert result["margin_trend"] is None
        assert result["guidance_language"] is None
        assert result["key_financial_concerns"] == []
        assert result["critical_accounting_estimates"] == []
        assert result["non_gaap_measures"] == []


# ------------------------------------------------------------------
# Item 8: Financial Statements
# ------------------------------------------------------------------


class TestConvertDebtEnrichment:
    """Tests for convert_debt_enrichment."""

    def test_all_fields_populated(self) -> None:
        ext = _make_extraction()
        result = convert_debt_enrichment(ext)

        instruments = result["debt_instruments"]
        assert isinstance(instruments, list)
        assert len(instruments) == 2
        assert "Convertible Notes" in instruments[0].value
        assert instruments[0].source == _SOURCE
        assert instruments[0].confidence == Confidence.HIGH

        credit = result["credit_facility_detail"]
        assert isinstance(credit, SourcedValue)
        assert credit.value == "No revolving credit facility"

        covenant = result["covenant_status"]
        assert isinstance(covenant, SourcedValue)
        assert covenant.value == "No financial covenants"

        tax = result["tax_rate_notes"]
        assert isinstance(tax, SourcedValue)
        assert "11%" in tax.value

    def test_empty_and_none(self) -> None:
        ext = _make_extraction(
            debt_instruments=[],
            credit_facility_detail=None,
            covenant_status=None,
            tax_rate_notes=None,
        )
        result = convert_debt_enrichment(ext)
        assert result["debt_instruments"] == []
        assert result["credit_facility_detail"] is None
        assert result["covenant_status"] is None
        assert result["tax_rate_notes"] is None


class TestConvertStockCompDetail:
    """Tests for convert_stock_comp_detail."""

    def test_non_empty(self) -> None:
        ext = _make_extraction()
        result = convert_stock_comp_detail(ext)
        assert result is not None
        assert "$2.1B" in result.value
        assert result.source == _SOURCE
        assert result.confidence == Confidence.HIGH

    def test_none_input(self) -> None:
        ext = _make_extraction(stock_comp_detail=None)
        assert convert_stock_comp_detail(ext) is None

    def test_empty_string(self) -> None:
        ext = _make_extraction(stock_comp_detail="")
        assert convert_stock_comp_detail(ext) is None


# ------------------------------------------------------------------
# Item 9A: Controls and Procedures
# ------------------------------------------------------------------


class TestConvertControlsAssessment:
    """Tests for convert_controls_assessment."""

    def test_no_issues(self) -> None:
        ext = _make_extraction()
        result = convert_controls_assessment(ext)

        mw = result["has_material_weakness"]
        assert isinstance(mw, SourcedValue)
        assert mw.value is False
        assert mw.source == _SOURCE
        assert mw.confidence == Confidence.HIGH

        assert result["material_weakness_detail"] == []
        assert result["significant_deficiencies"] == []
        assert result["remediation_status"] is None

        attestation = result["auditor_attestation"]
        assert isinstance(attestation, SourcedValue)
        assert "unqualified" in attestation.value

        auditor = result["auditor_name"]
        assert isinstance(auditor, SourcedValue)
        assert auditor.value == "PricewaterhouseCoopers LLP"

        tenure = result["auditor_tenure_years"]
        assert isinstance(tenure, SourcedValue)
        assert tenure.value == 5

    def test_with_material_weakness(self) -> None:
        ext = _make_extraction(
            has_material_weakness=True,
            material_weakness_detail=[
                "Ineffective IT general controls",
                "Revenue recognition process weakness",
            ],
            significant_deficiencies=[
                "Inadequate segregation of duties"
            ],
            remediation_status="Remediation plan in progress, expected Q2 2025",
        )
        result = convert_controls_assessment(ext)

        assert result["has_material_weakness"].value is True

        mw_detail = result["material_weakness_detail"]
        assert len(mw_detail) == 2
        assert mw_detail[0].value == "Ineffective IT general controls"
        assert mw_detail[0].source == _SOURCE

        sd = result["significant_deficiencies"]
        assert len(sd) == 1
        assert sd[0].value == "Inadequate segregation of duties"

        remediation = result["remediation_status"]
        assert isinstance(remediation, SourcedValue)
        assert "Q2 2025" in remediation.value

    def test_auditor_none_fields(self) -> None:
        ext = _make_extraction(
            auditor_attestation=None,
            auditor_name=None,
            auditor_tenure_years=None,
        )
        result = convert_controls_assessment(ext)
        assert result["auditor_attestation"] is None
        assert result["auditor_name"] is None
        assert result["auditor_tenure_years"] is None
