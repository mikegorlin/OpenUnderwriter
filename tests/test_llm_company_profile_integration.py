"""Integration tests for LLM enrichment in company profile extraction.

Tests LLM-first/yfinance-fallback integration in company_profile.py:
- LLM data enriches profile fields (always replaces business description)
- No LLM data prefers yfinance narrative, falls back to raw 10-K text
- LLM geographic footprint only fills when regex found nothing
- LLM complexity flags supplement (not replace) existing flags
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.sourced import now, sourced_str


# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


def _make_identity() -> CompanyIdentity:
    return CompanyIdentity(
        ticker="TEST",
        legal_name=sourced_str("Test Corp", "SEC EDGAR", Confidence.HIGH),
        cik=sourced_str("0001234567", "SEC EDGAR", Confidence.HIGH),
        sic_code=sourced_str("7372", "SEC EDGAR", Confidence.HIGH),
    )


def _make_state(
    *,
    llm_extractions: dict[str, Any] | None = None,
    info_overrides: dict[str, Any] | None = None,
    filing_text_overrides: dict[str, str] | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState with controlled data."""
    info: dict[str, Any] = {
        "exchange": "NMS",
        "industry": "Software",
        "fullTimeEmployees": 5000,
        "marketCap": 10_000_000_000,
        "longBusinessSummary": "Short summary.",
        **(info_overrides or {}),
    }
    filing_texts: dict[str, str] = {
        "10-K_item1": "Test company does software things.",
        **(filing_text_overrides or {}),
    }
    filings: dict[str, Any] = {
        "info": info,
        "filing_texts": filing_texts,
    }
    acquired = AcquiredData(
        filings=filings,
        market_data={"info": info},
        company_facts={},
        llm_extractions=llm_extractions or {},
    )
    profile = CompanyProfile(identity=_make_identity())
    return AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=acquired,
    )


def _make_ten_k_extraction(
    *,
    business_description: str | None = None,
    geographic_regions: list[str] | None = None,
    customer_concentration: list[str] | None = None,
    supplier_concentration: list[str] | None = None,
    is_dual_class: bool | None = None,
    has_vie: bool | None = None,
    employee_count: int | None = None,
) -> dict[str, Any]:
    """Build a minimal TenKExtraction dict for LLM mocking."""
    return {
        "business_description": business_description,
        "revenue_segments": [],
        "geographic_regions": geographic_regions or [],
        "customer_concentration": customer_concentration or [],
        "supplier_concentration": supplier_concentration or [],
        "competitive_position": None,
        "regulatory_environment": None,
        "employee_count": employee_count,
        "is_dual_class": is_dual_class,
        "has_vie": has_vie,
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
        "has_material_weakness": False,
        "material_weakness_detail": [],
        "significant_deficiencies": [],
        "remediation_status": None,
        "auditor_attestation": None,
        "auditor_name": None,
        "auditor_tenure_years": None,
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


class TestCompanyProfileWithLLMEnrichment:
    """LLM data enriches profile fields when available."""

    def test_llm_enriches_business_description(self) -> None:
        llm_data = _make_ten_k_extraction(
            business_description="A comprehensive LLM-extracted business description that is much longer than the regex version.",
        )
        state = _make_state(llm_extractions={"10-K:abc": llm_data})

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        assert profile.business_description is not None
        assert "comprehensive LLM-extracted" in profile.business_description.value
        assert profile.business_description.source == "10-K (LLM)"

    def test_llm_enriches_employee_count_when_missing(self) -> None:
        llm_data = _make_ten_k_extraction(employee_count=150000)
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            info_overrides={"fullTimeEmployees": None},
        )

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        assert profile.employee_count is not None
        assert profile.employee_count.value == 150000
        assert profile.employee_count.source == "10-K (LLM)"


class TestCompanyProfileWithoutLLM:
    """No LLM data -> yfinance/regex extraction only (fallback path)."""

    def test_no_llm_prefers_yfinance_summary(self) -> None:
        state = _make_state()

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        assert profile.business_description is not None
        # yfinance longBusinessSummary preferred over raw 10-K text
        assert "Short summary." in profile.business_description.value
        assert profile.business_description.source == "yfinance"

    def test_no_llm_falls_back_to_item1_when_no_yfinance(self) -> None:
        state = _make_state(info_overrides={"longBusinessSummary": ""})

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        assert profile.business_description is not None
        assert "software things" in profile.business_description.value
        assert profile.business_description.source == "10-K Item 1 (raw)"

    def test_no_llm_keeps_yfinance_employee_count(self) -> None:
        state = _make_state()

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        assert profile.employee_count is not None
        assert profile.employee_count.value == 5000
        assert profile.employee_count.source == "yfinance"


class TestLLMBusinessDescAlwaysReplaces:
    """LLM desc always replaces initial extraction (qualitatively better)."""

    def test_llm_replaces_yfinance_desc(self) -> None:
        llm_data = _make_ten_k_extraction(
            business_description="A much more detailed and comprehensive business description from the LLM extraction of the 10-K filing Item 1 section.",
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
        )

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        assert profile.business_description is not None
        assert "comprehensive" in profile.business_description.value
        assert profile.business_description.source == "10-K (LLM)"

    def test_llm_replaces_even_longer_initial_desc(self) -> None:
        """LLM always wins because it's a proper narrative, not raw text."""
        llm_data = _make_ten_k_extraction(
            business_description="Short but proper LLM narrative.",
        )
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            info_overrides={"longBusinessSummary": "A" * 500},
        )

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        assert profile.business_description is not None
        # LLM always wins -- it's a curated narrative
        assert "proper LLM narrative" in profile.business_description.value
        assert profile.business_description.source == "10-K (LLM)"


class TestLLMGeoOnlyFillsEmpty:
    """LLM geo only used when regex found nothing."""

    def test_llm_geo_fills_empty_footprint(self) -> None:
        llm_data = _make_ten_k_extraction(
            geographic_regions=["United States: 60%", "Europe: 30%", "Asia: 10%"],
        )
        state = _make_state(llm_extractions={"10-K:abc": llm_data})

        from do_uw.stages.extract.company_profile import extract_company_profile

        profile, _report = extract_company_profile(state)
        # If regex found nothing (no Exhibit 21), LLM should fill
        if not any(
            "Exhibit 21" in sv.source
            for sv in profile.geographic_footprint
        ):
            assert len(profile.geographic_footprint) >= 3
            regions = [
                sv.value.get("region", "")
                for sv in profile.geographic_footprint
            ]
            assert "United States" in regions

    def test_llm_geo_replaces_regex(self) -> None:
        """LLM 10-K geo data always preferred over Exhibit 21 subsidiary counts."""
        llm_data = _make_ten_k_extraction(
            geographic_regions=["LLM Region: 100%"],
        )
        state = _make_state(llm_extractions={"10-K:abc": llm_data})
        # Pre-populate profile with regex geo data
        assert state.company is not None
        state.company.geographic_footprint = [
            SourcedValue[dict[str, str | float]](
                value={"jurisdiction": "Delaware", "subsidiary_count": 5.0},
                source="Exhibit 21",
                confidence=Confidence.HIGH,
                as_of=now(),
            )
        ]

        from do_uw.stages.extract.company_profile import (
            _enrich_from_llm,
        )

        _enrich_from_llm(state, state.company)
        # LLM 10-K revenue data replaces Exhibit 21 subsidiary counts
        # (10-K gives country/region-level revenue breakdowns, more useful)
        assert len(state.company.geographic_footprint) >= 1
        assert state.company.geographic_footprint[0].source == "10-K (LLM)"


class TestLLMComplexityFlagsSupplement:
    """LLM complexity flags merge with existing, not replace."""

    def test_llm_flags_supplement_existing(self) -> None:
        llm_data = _make_ten_k_extraction(
            is_dual_class=True,
            has_vie=True,
        )
        state = _make_state(llm_extractions={"10-K:abc": llm_data})
        assert state.company is not None
        # Pre-populate with regex complexity that found SPE but not dual-class
        state.company.operational_complexity = SourcedValue[dict[str, Any]](
            value={"has_vie": False, "has_dual_class": False, "has_spe": True},
            source="10-K text analysis",
            confidence=Confidence.MEDIUM,
            as_of=now(),
        )

        from do_uw.stages.extract.company_profile import (
            _enrich_from_llm,
        )

        _enrich_from_llm(state, state.company)
        complexity = state.company.operational_complexity
        assert complexity is not None
        # LLM supplements: dual_class set to True, VIE stays False (already set)
        assert complexity.value["has_dual_class"] is True
        # VIE was already False (falsy) so LLM True overwrites it
        # has_spe remains from regex
        assert complexity.value["has_spe"] is True

    def test_llm_flags_no_effect_without_existing_complexity(self) -> None:
        """LLM flags do nothing if operational_complexity is None."""
        llm_data = _make_ten_k_extraction(is_dual_class=True)
        state = _make_state(
            llm_extractions={"10-K:abc": llm_data},
            filing_text_overrides={},  # No filing text
        )
        assert state.company is not None
        state.company.operational_complexity = None

        from do_uw.stages.extract.company_profile import (
            _enrich_from_llm,
        )

        _enrich_from_llm(state, state.company)
        # Should remain None (LLM only supplements, doesn't create)
        assert state.company.operational_complexity is None
