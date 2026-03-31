"""Tests for alternative data signal extraction from existing state.

Phase 119: Stock Drop Catalysts, Competitive Landscape, Alt Data
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.alt_data import (
    AIWashingRisk,
    AltDataAssessments,
    ESGRisk,
    PeerSCACheck,
    TariffExposure,
)


def _make_state(
    *,
    esg_gap_score: int = 0,
    geopolitical_risk_score: int = 0,
    ai_risk: Any | None = None,
    geographic_footprint: list[Any] | None = None,
    web_search_results: list[dict[str, str]] | None = None,
    sic_code: str = "7372",
    litigation_cases: list[Any] | None = None,
) -> Any:
    """Build a minimal mock AnalysisState for alt data extraction tests."""
    state = MagicMock()
    state.alt_data = AltDataAssessments()

    # Company identity
    state.company.identity.sic_code.value = sic_code
    state.company.identity.sector.value = "Technology"

    # Environment assessment
    env_dict = {
        "esg_gap_score": esg_gap_score,
        "geopolitical_risk_score": geopolitical_risk_score,
        "esg_gap_details": {
            "esg_risk_factor_count": 2 if esg_gap_score > 0 else 0,
            "esg_litigation_present": esg_gap_score >= 3,
        },
        "geopolitical_details": {
            "sanctioned_countries": [],
            "high_risk_countries": ["China"] if geopolitical_risk_score > 0 else [],
        },
    }
    state.extracted.environment_assessment = env_dict

    # AI risk assessment
    state.extracted.ai_risk = ai_risk

    # Geographic footprint
    if geographic_footprint is not None:
        state.company.geographic_footprint = geographic_footprint
    else:
        state.company.geographic_footprint = []

    # Web search results
    if web_search_results is not None:
        state.acquired_data.web_search_results = web_search_results
    else:
        state.acquired_data.web_search_results = []

    # Litigation
    if litigation_cases is not None:
        state.extracted.litigation.securities_class_actions = litigation_cases
    else:
        state.extracted.litigation.securities_class_actions = []

    return state


class TestExtractAltDataEmpty:
    """Test graceful handling of empty state."""

    def test_empty_state_no_crash(self) -> None:
        """Function returns safely with default AltDataAssessments on empty state."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state()
        extract_alt_data(state)

        assert isinstance(state.alt_data, AltDataAssessments)
        assert isinstance(state.alt_data.esg, ESGRisk)
        assert isinstance(state.alt_data.ai_washing, AIWashingRisk)
        assert isinstance(state.alt_data.tariff, TariffExposure)
        assert isinstance(state.alt_data.peer_sca, PeerSCACheck)

    def test_default_risk_levels_are_low(self) -> None:
        """All risk levels default to LOW when no data."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state()
        extract_alt_data(state)

        assert state.alt_data.esg.risk_level == "LOW"
        assert state.alt_data.ai_washing.scienter_risk == "LOW"
        assert state.alt_data.tariff.risk_level == "LOW"
        assert state.alt_data.peer_sca.contagion_risk == "LOW"


class TestExtractESG:
    """Test ESG risk extraction from environment assessment."""

    def test_high_esg_score_maps_to_high(self) -> None:
        """esg_gap_score >= 7 maps to HIGH risk level."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(esg_gap_score=8)
        extract_alt_data(state)

        assert state.alt_data.esg.risk_level == "HIGH"

    def test_medium_esg_score_maps_to_medium(self) -> None:
        """esg_gap_score 4-6 maps to MEDIUM risk level."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(esg_gap_score=5)
        extract_alt_data(state)

        assert state.alt_data.esg.risk_level == "MEDIUM"

    def test_low_esg_score_maps_to_low(self) -> None:
        """esg_gap_score < 4 maps to LOW risk level."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(esg_gap_score=2)
        extract_alt_data(state)

        assert state.alt_data.esg.risk_level == "LOW"

    def test_esg_do_relevance_populated(self) -> None:
        """D&O relevance narrative is populated for non-LOW ESG risk."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(esg_gap_score=7)
        extract_alt_data(state)

        assert state.alt_data.esg.do_relevance != ""
        assert len(state.alt_data.esg.do_relevance) > 10


class TestExtractAIWashing:
    """Test AI-washing risk extraction from AI risk assessment."""

    def test_ai_risk_present_sets_claims_flag(self) -> None:
        """When AIRiskAssessment exists, ai_claims_present is True."""
        from do_uw.models.ai_risk import AIDisclosureData, AIRiskAssessment
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        ai_risk = AIRiskAssessment(
            overall_score=65.0,
            disclosure_data=AIDisclosureData(
                mention_count=15,
                opportunity_mentions=10,
                threat_mentions=2,
                sentiment="OPPORTUNITY",
            ),
        )
        state = _make_state(ai_risk=ai_risk)
        extract_alt_data(state)

        assert state.alt_data.ai_washing.ai_claims_present is True

    def test_no_ai_risk_keeps_defaults(self) -> None:
        """No AI risk assessment keeps ai_claims_present False."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(ai_risk=None)
        extract_alt_data(state)

        assert state.alt_data.ai_washing.ai_claims_present is False

    def test_high_opportunity_low_threat_flags_scienter(self) -> None:
        """High opportunity + low threat AI sentiment increases scienter risk."""
        from do_uw.models.ai_risk import AIDisclosureData, AIRiskAssessment
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        ai_risk = AIRiskAssessment(
            overall_score=75.0,
            disclosure_data=AIDisclosureData(
                mention_count=30,
                opportunity_mentions=25,
                threat_mentions=1,
                sentiment="OPPORTUNITY",
            ),
        )
        state = _make_state(ai_risk=ai_risk)
        extract_alt_data(state)

        # High opportunity vs low threat ratio suggests AI-washing risk
        assert state.alt_data.ai_washing.scienter_risk in ("MEDIUM", "HIGH")


class TestExtractTariff:
    """Test tariff exposure extraction from geopolitical data."""

    def test_high_geopolitical_maps_to_high_tariff(self) -> None:
        """geopolitical_risk_score >= 3 (sanctioned countries) maps to HIGH."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(geopolitical_risk_score=3)
        extract_alt_data(state)

        assert state.alt_data.tariff.risk_level == "HIGH"

    def test_medium_geopolitical_maps_to_medium_tariff(self) -> None:
        """geopolitical_risk_score 1-2 maps to MEDIUM."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(geopolitical_risk_score=2)
        extract_alt_data(state)

        assert state.alt_data.tariff.risk_level == "MEDIUM"

    def test_zero_geopolitical_maps_to_low_tariff(self) -> None:
        """geopolitical_risk_score 0 maps to LOW."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(geopolitical_risk_score=0)
        extract_alt_data(state)

        assert state.alt_data.tariff.risk_level == "LOW"

    def test_geographic_footprint_populates_locations(self) -> None:
        """Geographic footprint data populates manufacturing_locations."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        geo_fp = [
            MagicMock(value={"jurisdiction": "China", "revenue": "30%"}),
            MagicMock(value={"jurisdiction": "United States", "revenue": "50%"}),
        ]
        state = _make_state(geographic_footprint=geo_fp, geopolitical_risk_score=1)
        extract_alt_data(state)

        assert len(state.alt_data.tariff.manufacturing_locations) > 0

    def test_tariff_do_relevance_populated(self) -> None:
        """D&O relevance is populated for non-LOW tariff risk."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(geopolitical_risk_score=2)
        extract_alt_data(state)

        assert state.alt_data.tariff.do_relevance != ""


class TestExtractPeerSCA:
    """Test peer SCA contagion check from web search + litigation."""

    def test_peer_sca_in_web_results_flags_contagion(self) -> None:
        """Web search results mentioning peer SCA increases contagion risk."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        web_results = [
            {
                "title": "Beta Corp faces securities class action over earnings miss",
                "snippet": "Shareholders of Beta Corp filed a securities class action alleging misrepresentation of revenue growth.",
            },
            {
                "title": "Tech sector sees wave of SCA filings",
                "snippet": "Multiple technology companies sued for securities fraud.",
            },
        ]
        state = _make_state(web_search_results=web_results, sic_code="7372")
        extract_alt_data(state)

        assert len(state.alt_data.peer_sca.peer_scas) > 0
        assert state.alt_data.peer_sca.contagion_risk in ("MEDIUM", "HIGH")

    def test_no_sca_results_stays_low(self) -> None:
        """No SCA mentions in web results keeps contagion risk LOW."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        web_results = [
            {"title": "Tech earnings beat expectations", "snippet": "Strong quarter."},
        ]
        state = _make_state(web_search_results=web_results)
        extract_alt_data(state)

        assert state.alt_data.peer_sca.contagion_risk == "LOW"

    def test_sector_populated_from_sic(self) -> None:
        """Sector field populated from SIC code."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(sic_code="7372")
        extract_alt_data(state)

        assert state.alt_data.peer_sca.sector != ""

    def test_peer_sca_do_relevance_populated(self) -> None:
        """D&O relevance populated when peer SCAs found."""
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        web_results = [
            {
                "title": "Competitor hit with securities class action",
                "snippet": "securities class action filed against major competitor.",
            },
        ]
        state = _make_state(web_search_results=web_results)
        extract_alt_data(state)

        if state.alt_data.peer_sca.peer_scas:
            assert state.alt_data.peer_sca.do_relevance != ""


class TestExtractAltDataOrchestration:
    """Test the top-level extract_alt_data orchestrator."""

    def test_populates_all_four_sub_assessments(self) -> None:
        """Orchestrator populates all 4 sub-assessments."""
        from do_uw.models.ai_risk import AIRiskAssessment
        from do_uw.stages.extract.alt_data_extraction import extract_alt_data

        state = _make_state(
            esg_gap_score=5,
            geopolitical_risk_score=2,
            ai_risk=AIRiskAssessment(overall_score=50.0),
        )
        extract_alt_data(state)

        assert isinstance(state.alt_data.esg, ESGRisk)
        assert isinstance(state.alt_data.ai_washing, AIWashingRisk)
        assert isinstance(state.alt_data.tariff, TariffExposure)
        assert isinstance(state.alt_data.peer_sca, PeerSCACheck)

    def test_no_http_calls(self) -> None:
        """Module contains no httpx, fetch, brave, or playwright imports."""
        import inspect

        import do_uw.stages.extract.alt_data_extraction as mod

        source = inspect.getsource(mod)
        for banned in ("httpx", "brave", "playwright", "fetch"):
            assert banned not in source, f"Found banned import: {banned}"
