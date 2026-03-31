"""Pydantic models for pricing CLI input/output.

Enums (QuoteStatus, MarketCapTier, LayerType, DataCompleteness, DataSource)
and input/output models for both legacy Quote-based and new Program-based
pricing model hierarchies.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class QuoteStatus(StrEnum):
    """Insurance quote lifecycle status."""

    INDICATION = "INDICATION"
    QUOTED = "QUOTED"
    BOUND = "BOUND"
    EXPIRED = "EXPIRED"
    DECLINED = "DECLINED"


class MarketCapTier(StrEnum):
    """Market capitalization tier classification."""

    MEGA = "MEGA"
    LARGE = "LARGE"
    MID = "MID"
    SMALL = "SMALL"
    MICRO = "MICRO"


class LayerType(StrEnum):
    """Type of insurance layer in the D&O tower.

    PRIMARY: Has retention (SIR/deductible), first layer in ABC tower.
    EXCESS: ABC excess layers stacking above primary (1st, 2nd, 3rd...).
    SIDE_A: Side A layers sitting on top of the ABC tower (D1 decision).
    """

    PRIMARY = "PRIMARY"
    EXCESS = "EXCESS"
    SIDE_A = "SIDE_A"


class DataCompleteness(StrEnum):
    """How much of the policy year data is available.

    FRAGMENT: Just anniversary or one field (minimum viable record).
    PARTIAL: Some layers/pricing but gaps remain.
    COMPLETE: Full tower structure with all premiums known.
    """

    FRAGMENT = "FRAGMENT"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"


class DataSource(StrEnum):
    """Provenance of a data value (D7 transparency decision).

    VERIFIED: From document or manual entry, confirmed accurate.
    INFERRED: Computed from known rate relationships.
    ESTIMATED: Rough estimate, low confidence.
    AI_EXTRACTED: Extracted by LLM from uploaded document.
    """

    VERIFIED = "VERIFIED"
    INFERRED = "INFERRED"
    ESTIMATED = "ESTIMATED"
    AI_EXTRACTED = "AI_EXTRACTED"


class TowerLayerInput(BaseModel):
    """Input model for a single tower layer."""

    model_config = ConfigDict(frozen=False)

    layer_position: str = Field(
        description="Tower position: PRIMARY, LOW_EXCESS, MID_EXCESS, HIGH_EXCESS"
    )
    layer_number: int = Field(description="1-based layer number")
    attachment_point: float = Field(
        description="Attachment point in USD (0 for primary)"
    )
    limit_amount: float = Field(description="Layer limit in USD")
    premium: float = Field(description="Layer premium in USD")
    carrier_name: str = Field(description="Carrier name")
    carrier_rating: str | None = Field(
        default=None, description="AM Best rating"
    )
    is_lead: bool = Field(default=False, description="Whether carrier is lead")
    share_pct: float | None = Field(
        default=None, description="Quota share percentage"
    )


class TowerLayerOutput(BaseModel):
    """Output model for a tower layer with computed fields."""

    model_config = ConfigDict(frozen=False)

    id: int = Field(description="Layer database ID")
    layer_position: str = Field(description="Tower position")
    layer_number: int = Field(description="1-based layer number")
    attachment_point: float = Field(description="Attachment point in USD")
    limit_amount: float = Field(description="Layer limit in USD")
    premium: float = Field(description="Layer premium in USD")
    carrier_name: str = Field(description="Carrier name")
    carrier_rating: str | None = Field(
        default=None, description="AM Best rating"
    )
    rate_on_line: float = Field(
        description="Computed: premium / limit_amount"
    )
    premium_per_million: float = Field(
        description="Computed: premium / (limit_amount / 1e6)"
    )
    is_lead: bool = Field(default=False, description="Whether carrier is lead")
    share_pct: float | None = Field(
        default=None, description="Quota share percentage"
    )


class QuoteInput(BaseModel):
    """Input model for creating a new insurance quote."""

    model_config = ConfigDict(frozen=False)

    ticker: str = Field(description="Stock ticker symbol")
    company_name: str = Field(description="Company name")
    effective_date: datetime = Field(description="Policy effective date")
    expiration_date: datetime | None = Field(
        default=None, description="Policy expiration date"
    )
    quote_date: datetime = Field(description="Date quote was provided")
    status: QuoteStatus = Field(
        default=QuoteStatus.QUOTED, description="Quote lifecycle status"
    )
    total_limit: float = Field(description="Total program limit in USD")
    total_premium: float = Field(description="Total program premium in USD")
    retention: float | None = Field(
        default=None, description="SIR/deductible in USD"
    )
    market_cap_tier: MarketCapTier = Field(
        description="Market cap classification"
    )
    sic_code: str | None = Field(
        default=None, description="SIC industry code"
    )
    sector: str | None = Field(
        default=None, description="Industry sector"
    )
    quality_score: float | None = Field(
        default=None, description="System quality score at quote time"
    )
    tier: str | None = Field(
        default=None, description="System tier at quote time"
    )
    source: str = Field(
        default="manual", description="Data source or who entered the quote"
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )
    layers: list[TowerLayerInput] = Field(
        default_factory=lambda: [],
        description="Tower layer details",
    )


class QuoteOutput(BaseModel):
    """Output model for a quote with all computed fields."""

    model_config = ConfigDict(frozen=False)

    id: int = Field(description="Quote database ID")
    ticker: str = Field(description="Stock ticker symbol")
    company_name: str = Field(description="Company name")
    effective_date: datetime = Field(description="Policy effective date")
    expiration_date: datetime | None = Field(
        default=None, description="Policy expiration date"
    )
    quote_date: datetime = Field(description="Date quote was provided")
    status: str = Field(description="Quote lifecycle status")
    total_limit: float = Field(description="Total program limit in USD")
    total_premium: float = Field(description="Total program premium in USD")
    retention: float | None = Field(
        default=None, description="SIR/deductible in USD"
    )
    market_cap_tier: str = Field(
        description="Market cap classification"
    )
    sic_code: str | None = Field(
        default=None, description="SIC industry code"
    )
    sector: str | None = Field(
        default=None, description="Industry sector"
    )
    quality_score: float | None = Field(
        default=None, description="System quality score at quote time"
    )
    tier: str | None = Field(
        default=None, description="System tier at quote time"
    )
    program_rate_on_line: float = Field(
        description="Computed: total_premium / total_limit"
    )
    source: str = Field(description="Data source")
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )
    created_at: datetime = Field(description="Record creation timestamp")
    layers: list[TowerLayerOutput] = Field(
        default_factory=lambda: [],
        description="Tower layer details",
    )


# -- Enhanced Program-based models (Phase 10.1) --


class BrokerInput(BaseModel):
    """Input model for creating or referencing a broker."""

    model_config = ConfigDict(frozen=False)

    brokerage_name: str = Field(description="Brokerage firm name")
    producer_name: str | None = Field(
        default=None, description="Individual broker/producer name"
    )
    email: str | None = Field(default=None, description="Contact email")
    phone: str | None = Field(default=None, description="Contact phone")
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )


class BrokerOutput(BaseModel):
    """Output model for a broker with database ID."""

    model_config = ConfigDict(frozen=False)

    id: int = Field(description="Broker database ID")
    brokerage_name: str = Field(description="Brokerage firm name")
    producer_name: str | None = Field(
        default=None, description="Individual broker/producer name"
    )
    email: str | None = Field(default=None, description="Contact email")
    phone: str | None = Field(default=None, description="Contact phone")
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )
    created_at: datetime = Field(description="Record creation timestamp")


class CarrierInput(BaseModel):
    """Input model for creating or referencing a carrier."""

    model_config = ConfigDict(frozen=False)

    carrier_name: str = Field(description="Insurance carrier name")
    am_best_rating: str | None = Field(
        default=None, description="AM Best financial strength rating"
    )
    appetite_notes: str | None = Field(
        default=None, description="Carrier appetite and relationship notes"
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )


class CarrierOutput(BaseModel):
    """Output model for a carrier with database ID."""

    model_config = ConfigDict(frozen=False)

    id: int = Field(description="Carrier database ID")
    carrier_name: str = Field(description="Insurance carrier name")
    am_best_rating: str | None = Field(
        default=None, description="AM Best financial strength rating"
    )
    appetite_notes: str | None = Field(
        default=None, description="Carrier appetite and relationship notes"
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )
    created_at: datetime = Field(description="Record creation timestamp")


class EnhancedLayerInput(BaseModel):
    """Input model for a tower layer with D&O-specific semantics.

    Supports partial data: limit_amount, premium, and carrier
    information are all optional to allow fragment-level records.
    """

    model_config = ConfigDict(frozen=False)

    layer_type: LayerType = Field(
        description="Layer type: PRIMARY, EXCESS, or SIDE_A"
    )
    layer_label: str | None = Field(
        default=None,
        description="Human label, e.g. 'Primary', '1st Excess', 'Lead Side A'",
    )
    layer_number: int = Field(description="Ordinal within layer type")
    attachment_point: float | None = Field(
        default=None,
        description="Attachment point in USD (0 for primary)",
    )
    limit_amount: float | None = Field(
        default=None, description="Layer limit in USD"
    )
    premium: float | None = Field(
        default=None, description="Layer premium in USD"
    )
    carrier_name: str | None = Field(
        default=None, description="Carrier name"
    )
    carrier_id: int | None = Field(
        default=None, description="FK to carriers table"
    )
    carrier_rating: str | None = Field(
        default=None, description="AM Best rating"
    )
    is_lead: bool = Field(default=False, description="Whether carrier is lead")
    share_pct: float | None = Field(
        default=None, description="Quota share percentage"
    )
    commission_pct: float | None = Field(
        default=None, description="Commission percentage"
    )
    data_source: DataSource = Field(
        default=DataSource.VERIFIED, description="Data provenance"
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )


class PolicyYearInput(BaseModel):
    """Input model for a single policy year within a program.

    Minimum viable: just policy_year (int). All pricing, dates,
    and layer details are optional to support fragment-level records.
    """

    model_config = ConfigDict(frozen=False)

    policy_year: int = Field(description="Policy year, e.g. 2025")
    effective_date: datetime | None = Field(
        default=None, description="Policy effective date"
    )
    expiration_date: datetime | None = Field(
        default=None, description="Policy expiration date"
    )
    total_limit: float | None = Field(
        default=None, description="Total program limit in USD"
    )
    total_premium: float | None = Field(
        default=None, description="Total program premium in USD"
    )
    retention: float | None = Field(
        default=None, description="SIR/deductible in USD (primary layer)"
    )
    status: QuoteStatus = Field(
        default=QuoteStatus.QUOTED, description="Quote lifecycle status"
    )
    data_completeness: DataCompleteness = Field(
        default=DataCompleteness.FRAGMENT,
        description="How complete the data is",
    )
    source: str = Field(
        default="manual", description="Data source or entry method"
    )
    source_document: str | None = Field(
        default=None, description="Source document filename or reference"
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )
    layers: list[EnhancedLayerInput] = Field(
        default_factory=lambda: [],
        description="Tower layer details",
    )


class PolicyYearOutput(BaseModel):
    """Output model for a policy year with database IDs and computed fields."""

    model_config = ConfigDict(frozen=False)

    id: int = Field(description="PolicyYear database ID")
    program_id: int = Field(description="Parent program ID")
    policy_year: int = Field(description="Policy year, e.g. 2025")
    effective_date: datetime | None = Field(
        default=None, description="Policy effective date"
    )
    expiration_date: datetime | None = Field(
        default=None, description="Policy expiration date"
    )
    total_limit: float | None = Field(
        default=None, description="Total program limit in USD"
    )
    total_premium: float | None = Field(
        default=None, description="Total program premium in USD"
    )
    retention: float | None = Field(
        default=None, description="SIR/deductible in USD"
    )
    status: str = Field(description="Quote lifecycle status")
    data_completeness: str = Field(description="Data completeness level")
    source: str = Field(description="Data source")
    source_document: str | None = Field(
        default=None, description="Source document reference"
    )
    program_rate_on_line: float | None = Field(
        default=None,
        description="Computed: total_premium / total_limit (nullable)",
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )
    created_at: datetime = Field(description="Record creation timestamp")
    layers: list[TowerLayerOutput] = Field(
        default_factory=lambda: [],
        description="Tower layer details",
    )


class ProgramInput(BaseModel):
    """Input model for creating a D&O insurance program.

    Minimum viable record: just ticker (per D2 decision).
    All other fields are optional and accumulate over time.
    """

    model_config = ConfigDict(frozen=False)

    ticker: str = Field(description="Stock ticker symbol")
    company_name: str | None = Field(
        default=None, description="Company name"
    )
    anniversary_month: int | None = Field(
        default=None, description="Anniversary month (1-12)"
    )
    anniversary_day: int | None = Field(
        default=None, description="Anniversary day (1-31)"
    )
    broker: BrokerInput | None = Field(
        default=None, description="Inline broker creation"
    )
    broker_id: int | None = Field(
        default=None, description="Existing broker FK"
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )


class ProgramOutput(BaseModel):
    """Output model for a program with database IDs and relationships."""

    model_config = ConfigDict(frozen=False)

    id: int = Field(description="Program database ID")
    ticker: str = Field(description="Stock ticker symbol")
    company_name: str | None = Field(
        default=None, description="Company name"
    )
    anniversary_month: int | None = Field(
        default=None, description="Anniversary month (1-12)"
    )
    anniversary_day: int | None = Field(
        default=None, description="Anniversary day (1-31)"
    )
    broker_id: int | None = Field(
        default=None, description="Broker FK"
    )
    notes_text: str | None = Field(
        default=None, description="Free-form notes"
    )
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    broker: BrokerOutput | None = Field(
        default=None, description="Associated broker details"
    )
    policy_years: list[PolicyYearOutput] = Field(
        default_factory=lambda: [],
        description="Policy year records",
    )
