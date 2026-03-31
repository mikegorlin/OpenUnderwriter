"""Alternative data assessment models for D&O underwriting worksheet.

Phase 119: Stock Drop Catalysts, Competitive Landscape, Alt Data

Provides models for ESG risk, AI-washing risk, tariff exposure,
and peer SCA contagion checks -- alternative data signals that
augment traditional financial analysis.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ESGRisk(BaseModel):
    """ESG risk assessment for D&O exposure.

    Captures ESG controversies, ratings, and greenwashing indicators
    that may create securities litigation surface.
    """

    model_config = ConfigDict(frozen=False)

    controversies: list[str] = Field(default_factory=list, description="ESG controversies identified")
    ratings: dict[str, str] = Field(
        default_factory=dict, description="ESG ratings by provider (e.g., MSCI: BBB, ISS: 3)"
    )
    greenwashing_indicators: list[str] = Field(
        default_factory=list, description="Greenwashing/ESG-washing indicators"
    )
    mission_alignment: str = Field(default="", description="Assessment of stated vs actual ESG alignment")
    risk_level: str = Field(default="LOW", description="Risk level: HIGH, MEDIUM, LOW")
    do_relevance: str = Field(default="", description="D&O relevance of ESG risk findings")


class AIWashingRisk(BaseModel):
    """AI-washing risk assessment.

    Evaluates whether the company's AI claims are substantiated,
    relevant to SEC enforcement focus on AI-washing in securities filings.
    """

    model_config = ConfigDict(frozen=False)

    ai_claims_present: bool = Field(default=False, description="Whether company makes AI claims")
    indicators: list[dict[str, str]] = Field(
        default_factory=list,
        description="AI-washing indicators: [{claim, evidence, risk}]",
    )
    scienter_risk: str = Field(default="LOW", description="Scienter risk level: HIGH, MEDIUM, LOW")
    do_relevance: str = Field(default="", description="D&O relevance of AI-washing risk")


class TariffExposure(BaseModel):
    """Tariff and trade exposure assessment.

    Evaluates supply chain and manufacturing exposure to tariff risk
    that may impact financial performance and create D&O litigation surface.
    """

    model_config = ConfigDict(frozen=False)

    supply_chain_exposure: str = Field(default="", description="Supply chain tariff exposure assessment")
    manufacturing_locations: list[str] = Field(
        default_factory=list, description="Key manufacturing locations"
    )
    international_revenue_pct: str = Field(
        default="", description="Percentage of revenue from international operations"
    )
    tariff_risk_factors: list[str] = Field(
        default_factory=list, description="Specific tariff risk factors identified"
    )
    risk_level: str = Field(default="LOW", description="Risk level: HIGH, MEDIUM, LOW")
    do_relevance: str = Field(default="", description="D&O relevance of tariff exposure")


class PeerSCACheck(BaseModel):
    """Peer SCA contagion check.

    Tracks securities class action filings against sector peers
    to assess contagion risk for the subject company.
    """

    model_config = ConfigDict(frozen=False)

    peer_scas: list[dict[str, str]] = Field(
        default_factory=list,
        description="Peer SCAs: [{company, filing_date, allegation}]",
    )
    sector: str = Field(default="", description="Sector for peer comparison")
    contagion_risk: str = Field(default="LOW", description="Contagion risk level: HIGH, MEDIUM, LOW")
    do_relevance: str = Field(default="", description="D&O relevance of peer SCA contagion")


class AltDataAssessments(BaseModel):
    """Top-level alternative data assessments container.

    Aggregates ESG, AI-washing, tariff, and peer SCA assessments.
    Placed as a top-level field on AnalysisState (not part of DossierData)
    because alt data is a separate analytical concern.
    """

    model_config = ConfigDict(frozen=False)

    esg: ESGRisk = Field(default_factory=ESGRisk, description="ESG risk assessment")
    ai_washing: AIWashingRisk = Field(default_factory=AIWashingRisk, description="AI-washing risk assessment")
    tariff: TariffExposure = Field(default_factory=TariffExposure, description="Tariff exposure assessment")
    peer_sca: PeerSCACheck = Field(default_factory=PeerSCACheck, description="Peer SCA contagion check")
