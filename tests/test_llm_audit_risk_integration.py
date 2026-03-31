"""Integration tests for LLM enrichment in audit risk extraction.

Tests LLM-first/regex-fallback integration in audit_risk.py:
- LLM controls data enriches audit profile
- Regex-only fallback when LLM is absent
- XBRL going concern is never overridden by LLM
- LLM significant deficiencies and remediation populate new fields
- Auditor methodology boilerplate is filtered from material weaknesses
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.sourced import sourced_str


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


def _make_state(
    *,
    llm_extractions: dict[str, Any] | None = None,
    item8_text: str = "",
    item9a_text: str = "",
) -> AnalysisState:
    """Build a minimal AnalysisState for audit risk testing."""
    filing_texts: dict[str, str] = {}
    if item8_text:
        filing_texts["10-K_item8"] = item8_text
    if item9a_text:
        filing_texts["10-K_item9a"] = item9a_text

    filings: dict[str, Any] = {
        "info": {},
        "filing_texts": filing_texts,
    }
    identity = CompanyIdentity(
        ticker="TEST",
        legal_name=sourced_str("Test Corp", "SEC EDGAR", Confidence.HIGH),
        cik=sourced_str("0001234567", "SEC EDGAR", Confidence.HIGH),
    )
    return AnalysisState(
        ticker="TEST",
        company=CompanyProfile(identity=identity),
        acquired_data=AcquiredData(
            filings=filings,
            market_data={"info": {}},
            company_facts={},
            llm_extractions=llm_extractions or {},
        ),
    )


def _make_ten_k_extraction(
    *,
    has_material_weakness: bool = False,
    material_weakness_detail: list[str] | None = None,
    significant_deficiencies: list[str] | None = None,
    remediation_status: str | None = None,
    auditor_attestation: str | None = None,
    auditor_name: str | None = None,
    auditor_tenure_years: int | None = None,
) -> dict[str, Any]:
    """Build a minimal TenKExtraction dict for LLM mocking."""
    return {
        "business_description": None,
        "revenue_segments": [],
        "geographic_regions": [],
        "customer_concentration": [],
        "supplier_concentration": [],
        "competitive_position": None,
        "regulatory_environment": None,
        "employee_count": None,
        "is_dual_class": None,
        "has_vie": None,
        "revenue_trend": None,
        "margin_trend": None,
        "key_financial_concerns": [],
        "guidance_language": None,
        "critical_accounting_estimates": [],
        "non_gaap_measures": [],
        "debt_instruments": [],
        "credit_facility_detail": None,
        "covenant_status": None,
        "tax_rate_notes": None,
        "stock_comp_detail": None,
        "has_material_weakness": has_material_weakness,
        "material_weakness_detail": material_weakness_detail or [],
        "significant_deficiencies": significant_deficiencies or [],
        "remediation_status": remediation_status,
        "auditor_attestation": auditor_attestation,
        "auditor_name": auditor_name,
        "auditor_tenure_years": auditor_tenure_years,
        "going_concern": False,
        "going_concern_detail": None,
        "material_weaknesses": [],
        "fiscal_year_end": None,
        "period_of_report": None,
        "risk_factors": [],
        "contingent_liabilities": [],
    }


# ------------------------------------------------------------------
# Tests
# ------------------------------------------------------------------


class TestAuditRiskWithLLMControls:
    """LLM material weakness detail populates audit profile."""

    def test_llm_material_weakness_detail(self) -> None:
        llm_data = _make_ten_k_extraction(
            has_material_weakness=True,
            material_weakness_detail=[
                "Deficiency in revenue recognition controls",
                "Insufficient IT general controls over financial reporting",
            ],
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "Presents fairly, in all material respects.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        # Regex didn't find MW (no "material weakness" in text),
        # so LLM detail should populate
        assert len(profile.material_weaknesses) == 2
        assert "revenue recognition" in profile.material_weaknesses[0].value
        assert profile.material_weaknesses[0].source == "10-K (LLM)"


class TestAuditRiskWithoutLLM:
    """Falls back to regex when LLM data is absent."""

    def test_regex_only_extraction(self) -> None:
        state = _make_state(
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "PricewaterhouseCoopers LLP. "
                       "Presents fairly, in all material respects.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert profile.auditor_name is not None
        assert "PricewaterhouseCoopers" in profile.auditor_name.value
        assert profile.opinion_type is not None
        assert profile.opinion_type.value == "unqualified"


class TestAuditRiskLLMNoOverrideGoingConcern:
    """XBRL/regex going concern is never overridden by LLM."""

    def test_going_concern_from_regex_preserved(self) -> None:
        llm_data = _make_ten_k_extraction()
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="There is substantial doubt about the company's "
                       "ability to continue as a going concern.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert profile.going_concern is not None
        assert profile.going_concern.value is True
        # Source should be regex, not LLM
        assert "10-K" in profile.going_concern.source

    def test_opinion_type_from_regex_preserved(self) -> None:
        """LLM auditor_attestation does not override regex opinion_type."""
        llm_data = _make_ten_k_extraction(
            auditor_attestation="unqualified with emphasis of matter",
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "Presents fairly, in all material respects. "
                       "PricewaterhouseCoopers.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        # Regex found "unqualified" -- LLM should NOT override
        assert profile.opinion_type is not None
        assert profile.opinion_type.value == "unqualified"
        assert "10-K" in profile.opinion_type.source


class TestAuditRiskLLMNewFields:
    """Significant deficiencies and remediation status populated from LLM."""

    def test_significant_deficiencies_populated(self) -> None:
        llm_data = _make_ten_k_extraction(
            significant_deficiencies=[
                "Deficiency in segregation of duties for AP",
            ],
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "Presents fairly, in all material respects.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert len(profile.significant_deficiencies) == 1
        assert "segregation of duties" in profile.significant_deficiencies[0].value

    def test_remediation_status_populated(self) -> None:
        llm_data = _make_ten_k_extraction(
            remediation_status="Management is implementing enhanced controls; "
                               "expected completion Q2 2026.",
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "Presents fairly, in all material respects.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert profile.remediation_status is not None
        assert "Q2 2026" in profile.remediation_status.value

    def test_llm_auditor_name_supplements_empty(self) -> None:
        """LLM auditor name fills when regex/XBRL found nothing."""
        llm_data = _make_ten_k_extraction(
            auditor_name="Grant Thornton LLP",
            auditor_tenure_years=5,
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Generic auditor report text without firm name.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert profile.auditor_name is not None
        assert "Grant Thornton" in profile.auditor_name.value
        assert profile.auditor_name.source == "10-K (LLM)"
        assert profile.tenure_years is not None
        assert profile.tenure_years.value == 5


# ------------------------------------------------------------------
# Boilerplate filter tests (regex path)
# ------------------------------------------------------------------


class TestRegexBoilerplateFilter:
    """Auditor methodology boilerplate is filtered from regex extraction."""

    def test_visa_auditor_methodology_filtered(self) -> None:
        """Visa-style PCAOB methodology language is NOT a material weakness."""
        visa_boilerplate = (
            "Report of Independent Registered Public Accounting Firm. "
            "PricewaterhouseCoopers LLP. "
            "Presents fairly, in all material respects. "
            "Our audit of internal control over financial reporting included "
            "obtaining an understanding of internal control over financial "
            "reporting, assessing the risk that a material weakness exists, "
            "and testing and evaluating the design and operating effectiveness "
            "of internal control based on the assessed risk."
        )
        state = _make_state(item8_text=visa_boilerplate)

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert len(profile.material_weaknesses) == 0

    def test_definition_of_material_weakness_filtered(self) -> None:
        """Standard definition language is not a finding."""
        definition_text = (
            "Report of Independent Registered Public Accounting Firm. "
            "PricewaterhouseCoopers LLP. "
            "Presents fairly, in all material respects. "
            "A material weakness is a deficiency, or a combination of "
            "deficiencies, in internal control over financial reporting, "
            "such that there is a reasonable possibility that a material "
            "misstatement of the annual or interim financial statements "
            "will not be prevented or detected on a timely basis."
        )
        state = _make_state(item8_text=definition_text)

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert len(profile.material_weaknesses) == 0

    def test_actual_material_weakness_preserved(self) -> None:
        """Real material weakness findings pass through the filter."""
        real_weakness_text = (
            "Report of Independent Registered Public Accounting Firm. "
            "PricewaterhouseCoopers LLP. "
            "Presents fairly, in all material respects. "
            "We identified a material weakness in the Company's internal "
            "control over financial reporting related to the income tax "
            "provision process. "
            "Management identified a material weakness in controls over "
            "revenue recognition for contracts with multiple deliverables."
        )
        state = _make_state(item8_text=real_weakness_text)

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert len(profile.material_weaknesses) == 2
        # Verify the actual findings are captured
        values = [mw.value for mw in profile.material_weaknesses]
        assert any("income tax" in v for v in values)
        assert any("revenue recognition" in v for v in values)

    def test_mix_of_boilerplate_and_real_findings(self) -> None:
        """Only real findings survive when mixed with boilerplate."""
        mixed_text = (
            "Report of Independent Registered Public Accounting Firm. "
            "PricewaterhouseCoopers LLP. "
            "Presents fairly, in all material respects. "
            "Our audit of internal control over financial reporting included "
            "assessing the risk that a material weakness exists. "
            "A material weakness is a deficiency, or a combination of "
            "deficiencies, in internal control over financial reporting. "
            "We identified a material weakness in the Company's internal "
            "control over financial reporting related to IT general controls."
        )
        state = _make_state(item8_text=mixed_text)

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        # Only the actual finding should survive
        assert len(profile.material_weaknesses) == 1
        assert "IT general controls" in profile.material_weaknesses[0].value


# ------------------------------------------------------------------
# Boilerplate filter tests (LLM path)
# ------------------------------------------------------------------


class TestLLMBoilerplateFilter:
    """Auditor methodology boilerplate is filtered from LLM extraction."""

    def test_llm_boilerplate_filtered(self) -> None:
        """LLM-extracted methodology text is filtered out."""
        llm_data = _make_ten_k_extraction(
            has_material_weakness=False,
            material_weakness_detail=[
                "Our audit of internal control over financial reporting included "
                "obtaining an understanding of internal control over financial "
                "reporting, assessing the risk that a material weakness exists",
            ],
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "Presents fairly, in all material respects.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert len(profile.material_weaknesses) == 0

    def test_llm_real_weakness_preserved(self) -> None:
        """Genuine LLM-extracted weakness passes through filter."""
        llm_data = _make_ten_k_extraction(
            has_material_weakness=True,
            material_weakness_detail=[
                "Ineffective IT general controls over financial reporting",
                "Deficiency in revenue recognition controls",
            ],
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "Presents fairly, in all material respects.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert len(profile.material_weaknesses) == 2

    def test_llm_mixed_boilerplate_and_real(self) -> None:
        """LLM output with mix of boilerplate and real findings."""
        llm_data = _make_ten_k_extraction(
            has_material_weakness=True,
            material_weakness_detail=[
                "A material weakness is a deficiency, or a combination of "
                "deficiencies, in internal control over financial reporting",
                "Ineffective controls over the financial close process",
            ],
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            item8_text="Report of Independent Registered Public Accounting Firm. "
                       "Presents fairly, in all material respects.",
        )

        from do_uw.stages.extract.audit_risk import extract_audit_risk

        profile, _report = extract_audit_risk(state)
        assert len(profile.material_weaknesses) == 1
        assert "financial close process" in profile.material_weaknesses[0].value
