"""Typed context model for executive summary section.

Matches the dict returned by extract_exec_summary() in
context_builders/company_exec_summary.py.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FindingDetail(BaseModel):
    """A single key finding or positive indicator with SCA theory mapping."""

    model_config = ConfigDict(extra="allow")

    narrative: str = ""
    section: str = ""
    impact: str = ""
    theory: str | None = None
    sca_theory: str | None = None
    sca_defense: str | None = None


class SnapshotContext(BaseModel):
    """Company snapshot summary for exec brief header."""

    model_config = ConfigDict(extra="allow")

    company_name: str = "N/A"
    ticker: str = ""
    exchange: str = "N/A"
    industry: str = "N/A"
    market_cap: str = "N/A"
    revenue: str = "N/A"
    employees: str = "N/A"


class ClaimProbability(BaseModel):
    """SCA claim probability assessment."""

    model_config = ConfigDict(extra="allow")

    band: str = ""
    range: str = ""
    industry_base: str = ""


class TowerRecommendation(BaseModel):
    """D&O tower placement recommendation."""

    model_config = ConfigDict(extra="allow")

    position: str = ""
    min_attachment: str = "N/A"
    side_a: str = "N/A"


class InherentRisk(BaseModel):
    """Inherent risk assessment based on sector and market cap."""

    model_config = ConfigDict(extra="allow")

    sector: str = "N/A"
    market_cap_tier: str = "N/A"
    sector_base_rate: str = "N/A"
    adjusted_rate: str = "N/A"


class ExecSummaryContext(BaseModel):
    """Typed context for the executive summary section.

    All fields are optional with defaults to support partial data.
    extra='allow' permits evaluative helpers to add keys not yet modeled.
    """

    model_config = ConfigDict(extra="allow")

    tier_label: str | None = None
    tier_action: str | None = None
    quality_score: str | None = None
    composite_score: str | None = None
    thesis: str | None = None
    key_findings: list[str] = Field(default_factory=list)
    key_findings_detail: list[FindingDetail] = Field(default_factory=list)
    positive_indicators: list[str] = Field(default_factory=list)
    positive_detail: list[FindingDetail] = Field(default_factory=list)
    snapshot: SnapshotContext | None = None
    claim_probability: ClaimProbability | None = None
    tower_recommendation: TowerRecommendation | None = None
    inherent_risk: InherentRisk | None = None
