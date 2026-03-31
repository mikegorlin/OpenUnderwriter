"""Classification models -- Layer 1 of the five-layer analysis architecture.

Captures the objective classification of a company based on exactly 3
variables: market cap tier, industry sector, and IPO age (years public).

The classification is fully deterministic and config-driven -- no
subjective judgment at this layer. All tier boundaries, sector rates,
IPO multipliers, and severity bands come from classification.json.

Used by:
- ClassifyStage: Produces ClassificationResult from 3 inputs
- AnalysisState: Stored as state.classification
- ScoreStage: IES multiplier feeds into filing rate computation
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MarketCapTier(StrEnum):
    """Market capitalization tier for D&O risk classification.

    Tiers and boundaries defined in classification.json.
    Ordered from largest to smallest.
    """

    MEGA = "MEGA"      # >$200B
    LARGE = "LARGE"    # $10-200B
    MID = "MID"        # $2-10B
    SMALL = "SMALL"    # $300M-2B
    MICRO = "MICRO"    # <$300M


class ClassificationResult(BaseModel):
    """Layer 1: Objective classification from 3 variables.

    Produced by classify_company() using only:
    1. Market cap -> tier (Mega/Large/Mid/Small/Micro)
    2. Industry sector (SIC/NAICS -> sector code) -> base rate
    3. IPO age (years since listing) -> age multiplier

    Formula: filing_rate = sector_base_rate * cap_multiplier * ipo_multiplier

    All domain values loaded from classification.json -- zero hardcoded
    thresholds in Python code.
    """

    model_config = ConfigDict(frozen=False)

    market_cap_tier: MarketCapTier = Field(
        description="Market capitalization tier (MEGA/LARGE/MID/SMALL/MICRO)"
    )
    sector_code: str = Field(
        description="Industry sector code (e.g., TECH, BIOT, FINS)"
    )
    sector_name: str = Field(
        default="",
        description="Human-readable sector name",
    )
    years_public: int | None = Field(
        default=None,
        description="Years since IPO. None = unknown (treated as seasoned)",
    )
    base_filing_rate_pct: float = Field(
        description="Annual SCA filing probability (%) from classification",
    )
    severity_band_low_m: float = Field(
        description="Low end of severity band (USD millions)",
    )
    severity_band_high_m: float = Field(
        description="High end of severity band (USD millions)",
    )
    ddl_exposure_base_m: float = Field(
        default=0.0,
        description="Prospective DDL exposure at assumed stock drop (USD millions)",
    )
    ipo_multiplier: float = Field(
        default=1.0,
        description="IPO age multiplier applied (1.0 = seasoned)",
    )
    cap_filing_multiplier: float = Field(
        default=1.0,
        description="Market cap tier filing multiplier",
    )
    methodology: str = Field(
        default="classification_v1",
        description="Classification methodology version identifier",
    )


__all__ = [
    "ClassificationResult",
    "MarketCapTier",
]
