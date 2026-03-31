"""Competitive landscape models for D&O underwriting worksheet.

Phase 119: Stock Drop Catalysts, Competitive Landscape, Alt Data

Provides models for peer comparison and moat/competitive position analysis.
Used in Intelligence Dossier section 5.7.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PeerRow(BaseModel):
    """Single peer company row in the competitive landscape table.

    Captures key financial and risk metrics for a competitor,
    including their SCA history for contagion risk assessment.
    """

    model_config = ConfigDict(frozen=False)

    company_name: str = Field(default="", description="Peer company name")
    ticker: str = Field(default="", description="Peer stock ticker")
    market_cap: str = Field(default="", description="Market capitalization")
    revenue: str = Field(default="", description="Annual revenue")
    margin: str = Field(default="", description="Operating or net margin")
    growth_rate: str = Field(default="", description="Revenue growth rate")
    rd_spend: str = Field(default="", description="R&D spend or percentage")
    market_share: str = Field(default="", description="Estimated market share")
    stock_performance: str = Field(default="", description="Stock performance over analysis period")
    sca_history: str = Field(default="", description="SCA filings against this peer")
    do_relevance: str = Field(default="", description="D&O risk relevance of this peer")


class MoatDimension(BaseModel):
    """Single competitive moat dimension assessment.

    Evaluates one aspect of the company's competitive defenses
    and the D&O risk if that moat erodes.
    """

    model_config = ConfigDict(frozen=False)

    dimension: str = Field(default="", description="Moat type: Data Advantage, Switching Costs, etc.")
    present: bool = Field(default=False, description="Whether this moat dimension is present")
    strength: str = Field(default="", description="Strength: Strong, Moderate, Weak")
    durability: str = Field(default="", description="Durability: High, Medium, Low")
    evidence: str = Field(default="", description="Evidence supporting the assessment")
    do_risk: str = Field(default="", description="D&O risk if moat erodes")


class CompetitiveLandscape(BaseModel):
    """Competitive landscape and moat assessment (Dossier section 5.7).

    Aggregates peer comparison data and moat dimensions for
    the competitive position section of the intelligence dossier.
    """

    model_config = ConfigDict(frozen=False)

    peers: list[PeerRow] = Field(default_factory=list, description="Peer company comparison rows")
    moat_dimensions: list[MoatDimension] = Field(
        default_factory=list, description="Competitive moat dimension assessments"
    )
    competitive_position_narrative: str = Field(
        default="", description="Narrative describing competitive position"
    )
    do_commentary: str = Field(
        default="", description="Overall competitive D&O risk narrative"
    )
