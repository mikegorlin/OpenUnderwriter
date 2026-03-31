"""Tests for AltDataAssessments Pydantic models.

Phase 119: Stock Drop Catalysts, Competitive Landscape, Alt Data
Plan 01: Data model definitions.
"""

from __future__ import annotations

import json

from do_uw.models.alt_data import (
    AIWashingRisk,
    AltDataAssessments,
    ESGRisk,
    PeerSCACheck,
    TariffExposure,
)


class TestESGRiskDefaults:
    """ESGRisk() has controversies list, ratings dict, greenwashing_indicators list."""

    def test_instantiates_with_defaults(self) -> None:
        e = ESGRisk()
        assert e.controversies == []
        assert e.ratings == {}
        assert e.greenwashing_indicators == []
        assert e.mission_alignment == ""
        assert e.risk_level == "LOW"
        assert e.do_relevance == ""

    def test_populated(self) -> None:
        e = ESGRisk(
            controversies=["Water pollution incident"],
            ratings={"MSCI": "BBB", "ISS": "3"},
            greenwashing_indicators=["Unsubstantiated net-zero claim"],
            mission_alignment="Misaligned",
            risk_level="HIGH",
            do_relevance="ESG-related SCA risk from greenwashing",
        )
        assert len(e.controversies) == 1
        assert e.ratings["MSCI"] == "BBB"
        assert e.ratings["ISS"] == "3"
        assert len(e.greenwashing_indicators) == 1
        assert e.risk_level == "HIGH"


class TestAIWashingRiskDefaults:
    """AIWashingRisk() has indicators list, scienter_risk str, do_relevance str."""

    def test_instantiates_with_defaults(self) -> None:
        a = AIWashingRisk()
        assert a.ai_claims_present is False
        assert a.indicators == []
        assert a.scienter_risk == "LOW"
        assert a.do_relevance == ""

    def test_populated(self) -> None:
        a = AIWashingRisk(
            ai_claims_present=True,
            indicators=[{"claim": "AI-powered analytics", "evidence": "No ML patents", "risk": "HIGH"}],
            scienter_risk="MEDIUM",
            do_relevance="SEC AI-washing enforcement risk",
        )
        assert a.ai_claims_present is True
        assert len(a.indicators) == 1
        assert a.indicators[0]["claim"] == "AI-powered analytics"
        assert a.scienter_risk == "MEDIUM"


class TestTariffExposureDefaults:
    """TariffExposure() has supply_chain_exposure, manufacturing_exposure fields."""

    def test_instantiates_with_defaults(self) -> None:
        t = TariffExposure()
        assert t.supply_chain_exposure == ""
        assert t.manufacturing_locations == []
        assert t.international_revenue_pct == ""
        assert t.tariff_risk_factors == []
        assert t.risk_level == "LOW"
        assert t.do_relevance == ""

    def test_populated(self) -> None:
        t = TariffExposure(
            supply_chain_exposure="Heavy China dependency",
            manufacturing_locations=["Shenzhen", "Taipei"],
            international_revenue_pct="62%",
            tariff_risk_factors=["Section 301 tariffs", "CHIPS Act compliance"],
            risk_level="HIGH",
            do_relevance="Tariff impact on margins may trigger 10b-5 exposure",
        )
        assert len(t.manufacturing_locations) == 2
        assert len(t.tariff_risk_factors) == 2
        assert t.risk_level == "HIGH"


class TestPeerSCACheckDefaults:
    """PeerSCACheck() has peer_scas list, sector str, contagion_risk str."""

    def test_instantiates_with_defaults(self) -> None:
        p = PeerSCACheck()
        assert p.peer_scas == []
        assert p.sector == ""
        assert p.contagion_risk == "LOW"
        assert p.do_relevance == ""

    def test_populated(self) -> None:
        p = PeerSCACheck(
            peer_scas=[
                {"company": "PeerCo", "filing_date": "2025-06-01", "allegation": "Revenue miss"},
            ],
            sector="Technology",
            contagion_risk="MEDIUM",
            do_relevance="Sector SCA wave increases filing probability",
        )
        assert len(p.peer_scas) == 1
        assert p.peer_scas[0]["company"] == "PeerCo"
        assert p.contagion_risk == "MEDIUM"


class TestAltDataAssessmentsDefaults:
    """AltDataAssessments() instantiates with empty sub-model defaults."""

    def test_instantiates_with_defaults(self) -> None:
        a = AltDataAssessments()
        assert isinstance(a.esg, ESGRisk)
        assert isinstance(a.ai_washing, AIWashingRisk)
        assert isinstance(a.tariff, TariffExposure)
        assert isinstance(a.peer_sca, PeerSCACheck)
        # Sub-models have their defaults
        assert a.esg.controversies == []
        assert a.ai_washing.ai_claims_present is False
        assert a.tariff.manufacturing_locations == []
        assert a.peer_sca.peer_scas == []


class TestAltDataAssessmentsSerialization:
    """AltDataAssessments round-trip JSON serialization."""

    def test_round_trip_json(self) -> None:
        a = AltDataAssessments(
            esg=ESGRisk(
                controversies=["Emissions scandal"],
                ratings={"MSCI": "CCC"},
                risk_level="HIGH",
            ),
            ai_washing=AIWashingRisk(ai_claims_present=True),
            tariff=TariffExposure(
                manufacturing_locations=["Vietnam"],
                risk_level="MEDIUM",
            ),
            peer_sca=PeerSCACheck(
                peer_scas=[{"company": "X", "filing_date": "2025-01-01", "allegation": "Fraud"}],
                contagion_risk="HIGH",
            ),
        )
        json_str = a.model_dump_json()
        data = json.loads(json_str)
        restored = AltDataAssessments.model_validate(data)
        assert restored.esg.controversies == ["Emissions scandal"]
        assert restored.esg.ratings["MSCI"] == "CCC"
        assert restored.ai_washing.ai_claims_present is True
        assert restored.tariff.manufacturing_locations == ["Vietnam"]
        assert restored.peer_sca.peer_scas[0]["company"] == "X"
        assert restored.peer_sca.contagion_risk == "HIGH"


class TestAltDataAssessmentsJsonSchema:
    """JSON schema generation works."""

    def test_json_schema(self) -> None:
        schema = AltDataAssessments.model_json_schema()
        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "esg" in schema["properties"]
        assert "ai_washing" in schema["properties"]
        assert "tariff" in schema["properties"]
        assert "peer_sca" in schema["properties"]
