"""Company intelligence data models.

Pydantic v2 models for the company intelligence sub-sections:
concentration risk, supply chain dependencies, peer SCA contagion,
and sector-specific D&O concerns.

Created in Phase 134 (company-intelligence), Plan 01.
"""

from __future__ import annotations

from pydantic import BaseModel


class ConcentrationDimension(BaseModel):
    """Business concentration risk dimension.

    Captures customer, geographic, product/service, and channel
    concentration that creates D&O exposure if undisclosed or
    if concentration loss triggers revenue miss.
    """

    dimension: str  # "Customer", "Geographic", "Product/Service", "Channel"
    level: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    key_data: str = ""  # e.g., "Top customer = 15% revenue"
    do_implication: str = ""  # D&O litigation theory
    source: str = ""


class SupplyChainDependency(BaseModel):
    """Supply chain dependency extracted from 10-K.

    Sole-source and limited-source dependencies create D&O exposure
    when supply disruption causes revenue miss and management failed
    to disclose the concentration risk.
    """

    provider: str = ""
    dependency_type: str = ""  # "sole-source", "limited-source", "diversified"
    concentration: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    switching_cost: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    do_exposure: str = ""  # D&O implication
    source: str = ""


class PeerSCARecord(BaseModel):
    """Securities class action filing for a peer company.

    Used for peer SCA contagion analysis: if peers in the same
    sector are getting sued, the risk profile elevates.
    """

    ticker: str = ""
    company_name: str = ""
    case_caption: str = ""
    filing_date: str = ""
    status: str = ""  # "active", "settled", "dismissed"
    settlement_amount_m: float | None = None
    allegation_type: str = ""


class SectorDOConcern(BaseModel):
    """Sector-specific D&O concern from config.

    Loaded from config/sector_do_concerns.json. Each concern maps
    a sector-level risk to a specific D&O litigation theory.
    """

    concern: str = ""
    sector_relevance: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    company_exposure: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    do_implication: str = ""


__all__ = [
    "ConcentrationDimension",
    "PeerSCARecord",
    "SectorDOConcern",
    "SupplyChainDependency",
]
