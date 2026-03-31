"""Company identity and profile models -- RESOLVE stage output.

Populated during the RESOLVE stage (Phase 2). Maps a ticker symbol to
full company identity including SEC identifiers, exchange info, and
business profile. Expanded in Phase 3 with SECT2 requirements.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import Confidence, SourcedValue


class CompanyIdentity(BaseModel):
    """Core company identification from SEC and exchange data.

    Populated in RESOLVE stage from EdgarTools MCP / SEC EDGAR.
    """

    model_config = ConfigDict(frozen=False)

    ticker: str = Field(description="Stock ticker symbol")
    legal_name: SourcedValue[str] | None = Field(
        default=None, description="Legal entity name from SEC filings"
    )
    cik: SourcedValue[str] | None = Field(
        default=None, description="SEC Central Index Key"
    )
    sic_code: SourcedValue[str] | None = Field(
        default=None, description="Standard Industrial Classification code"
    )
    naics_code: SourcedValue[str] | None = Field(
        default=None, description="North American Industry Classification code"
    )
    exchange: SourcedValue[str] | None = Field(
        default=None, description="Primary exchange (NYSE, NASDAQ, etc.)"
    )
    sector: SourcedValue[str] | None = Field(
        default=None,
        description="Sector code (TECH, HLTH, FINS, etc.) per sector_baselines.json",
    )
    state_of_incorporation: SourcedValue[str] | None = Field(
        default=None, description="State/jurisdiction of incorporation"
    )
    fiscal_year_end: SourcedValue[str] | None = Field(
        default=None, description="Fiscal year end month-day (e.g. '12-31')"
    )
    is_fpi: bool = Field(
        default=False,
        description=(
            "Foreign private issuer "
            "(files 20-F/6-K instead of 10-K/10-Q)"
        ),
    )
    entity_type: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "SEC entity type "
            "(operating, foreign-private-issuer, etc.)"
        ),
    )
    sic_description: SourcedValue[str] | None = Field(
        default=None, description="SIC code description"
    )
    all_tickers: list[str] = Field(
        default_factory=list,
        description=(
            "All ticker symbols for this entity "
            "(e.g., GOOG, GOOGL)"
        ),
    )


class CompanyProfile(BaseModel):
    """Full company profile combining identity with business overview.

    Identity is populated in RESOLVE stage. Business details are enriched
    in EXTRACT stage from 10-K Item 1 and Item 7.
    """

    model_config = ConfigDict(frozen=False)

    identity: CompanyIdentity
    business_description: SourcedValue[str] | None = Field(
        default=None, description="Business description from 10-K Item 1"
    )
    market_cap: SourcedValue[float] | None = Field(
        default=None, description="Market capitalization in USD"
    )
    employee_count: SourcedValue[int] | None = Field(
        default=None, description="Total employees from most recent 10-K"
    )
    filer_category: SourcedValue[str] | None = Field(
        default=None,
        description="SEC filer category: large accelerated, accelerated, etc.",
    )
    years_public: SourcedValue[int] | None = Field(
        default=None, description="Years since IPO"
    )
    revenue_segments: list[SourcedValue[dict[str, str | float]]] = Field(
        default_factory=lambda: [],
        description="Revenue breakdown by segment from 10-K",
    )
    geographic_footprint: list[SourcedValue[dict[str, str | float]]] = Field(
        default_factory=lambda: [],
        description="Revenue breakdown by geography from 10-K",
    )
    subsidiary_count: SourcedValue[int] | None = Field(
        default=None, description="Number of subsidiaries from Exhibit 21"
    )
    gics_code: SourcedValue[str] | None = Field(
        default=None,
        description="8-digit GICS industry code (from yfinance or SIC mapping)",
    )

    # --- SECT2 fields (populated in EXTRACT stage, Phase 3) ---
    industry_classification: SourcedValue[str] | None = Field(
        default=None,
        description="Industry classification from yfinance (SECT2-08)",
    )
    business_model_description: SourcedValue[str] | None = Field(
        default=None,
        description="Business model narrative from 10-K Item 1 (SECT2-02)",
    )
    customer_concentration: list[SourcedValue[dict[str, str | float]]] = Field(
        default_factory=lambda: [],
        description="Major customers with revenue % (SECT2-04)",
    )
    supplier_concentration: list[SourcedValue[dict[str, str | float]]] = Field(
        default_factory=lambda: [],
        description="Major suppliers with dependency info (SECT2-04)",
    )
    operational_complexity: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Operational complexity indicators: VIEs, dual-class, "
            "special structures (SECT2-05)"
        ),
    )
    workforce_distribution: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description="Workforce distribution: domestic/international headcount, unionization % (OPS-03)",
    )
    operational_resilience: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description="Operational resilience: geographic concentration, facility risk, supply chain depth (OPS-04)",
    )
    subsidiary_structure: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description="Subsidiary structure: jurisdiction counts with regulatory regime classification (OPS-02)",
    )
    business_changes: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description=(
            "Major business changes: pivots, acquisitions, "
            "divestitures (SECT2-06)"
        ),
    )

    # --- Business Model Dimensions (v6.0 BMOD) ---
    revenue_model_type: SourcedValue[str] | None = Field(
        default=None,
        description="Revenue model classification: RECURRING, PROJECT, TRANSACTION, HYBRID (BMOD-01)",
    )
    key_person_risk: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Key person dependency data: {is_founder_led, ceo_tenure_years, "
            "has_succession_plan, risk_score} (BMOD-03)"
        ),
    )
    segment_lifecycle: list[SourcedValue[dict[str, str | float]]] = Field(
        default_factory=lambda: [],
        description="Segment lifecycle stages: [{name, stage, growth_rate}] (BMOD-04)",
    )
    disruption_risk: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Disruption risk assessment: {level: HIGH/MODERATE/LOW, "
            "threats: [...], threat_count} (BMOD-05)"
        ),
    )
    segment_margins: list[SourcedValue[dict[str, str | float]]] = Field(
        default_factory=lambda: [],
        description="Segment margins: [{name, margin_pct, prior_margin_pct, change_bps}] (BMOD-06)",
    )

    # --- M&A Profile ---
    goodwill_balance: SourcedValue[float] | None = Field(
        default=None,
        description="Total goodwill on balance sheet in USD",
    )
    acquisitions_total_spend: SourcedValue[float] | None = Field(
        default=None,
        description="Total cash paid for acquisitions during the fiscal year in USD",
    )
    acquisitions: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="List of acquisitions with company name, date, value, rationale",
    )
    goodwill_change_description: SourcedValue[str] | None = Field(
        default=None,
        description="Summary of goodwill changes during the year",
    )

    do_exposure_factors: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="Mapped D&O exposure factors (SECT2-07)",
    )
    event_timeline: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="Chronological event timeline (SECT2-10)",
    )
    section_summary: SourcedValue[str] | None = Field(
        default=None,
        description="Generated company profile summary paragraph (SECT2-11)",
    )

    # D&O risk classification (populated in ANALYZE stage)
    risk_classification: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "Primary D&O risk class: BINARY_EVENT, GROWTH_DARLING, "
            "GUIDANCE_DEPENDENT, REGULATORY_SENSITIVE, TRANSFORMATION, "
            "MATURE_STABLE, FINANCIAL_ENGINEERING"
        ),
    )
    risk_classification_confidence: Confidence | None = Field(
        default=None,
        description="Confidence in the risk classification assignment",
    )
