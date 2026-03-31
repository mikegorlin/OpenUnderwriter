"""Financial data models -- part of EXTRACT stage output.

Captures financial statements, distress indicators, peer group, and
audit profile extracted from SEC filings (10-K, 10-Q). Populated
during EXTRACT stage (Phase 3).

Expanded in Phase 3 with typed statement models, distress result
structures, peer group models, and SECT3 analysis fields.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue

# ---------------------------------------------------------------------------
# Financial statement models (typed replacements for dict[str, Any])
# ---------------------------------------------------------------------------


class FinancialLineItem(BaseModel):
    """A single line item on a financial statement.

    Each line item has a display label, values keyed by period label
    (e.g., "FY2024", "FY2023"), the XBRL concept used for extraction,
    and optionally a year-over-year change percentage.
    """

    model_config = ConfigDict(frozen=False)

    label: str = Field(description="Display name (e.g., 'Total Revenue')")
    values: dict[str, SourcedValue[float] | None] = Field(
        default_factory=dict,
        description="Values keyed by period label ('FY2024', 'Q3 2024')",
    )
    xbrl_concept: str | None = Field(
        default=None, description="Which XBRL tag was used for extraction"
    )
    yoy_change: float | None = Field(
        default=None, description="Year-over-year change percentage"
    )


class FinancialStatement(BaseModel):
    """A single financial statement (income, balance sheet, cash flow).

    Contains ordered line items, period labels, and filing source info.
    """

    model_config = ConfigDict(frozen=False)

    statement_type: str = Field(
        description="Statement type: 'income', 'balance_sheet', 'cash_flow'"
    )
    periods: list[str] = Field(
        default_factory=lambda: [],
        description="Period labels in column order (e.g., ['FY2024', 'FY2023'])",
    )
    line_items: list[FinancialLineItem] = Field(
        default_factory=lambda: [],
        description="Ordered list of line items on this statement",
    )
    filing_source: str = Field(
        default="",
        description="Accession number / filing reference",
    )
    extraction_date: datetime | None = Field(
        default=None, description="When this statement was extracted"
    )


class FinancialStatements(BaseModel):
    """Structured financial statement data extracted from SEC filings.

    Uses typed FinancialStatement models instead of dict[str, Any].
    """

    model_config = ConfigDict(frozen=False)

    income_statement: FinancialStatement | None = Field(
        default=None,
        description="Income statement from 10-K/10-Q",
    )
    balance_sheet: FinancialStatement | None = Field(
        default=None,
        description="Balance sheet from 10-K/10-Q",
    )
    cash_flow: FinancialStatement | None = Field(
        default=None,
        description="Cash flow statement from 10-K/10-Q",
    )
    periods_available: int = Field(
        default=0, description="Number of reporting periods loaded"
    )


# ---------------------------------------------------------------------------
# Distress indicator models (expanded with zone + trajectory)
# ---------------------------------------------------------------------------


class DistressZone(StrEnum):
    """Classification zone for distress indicators."""

    SAFE = "safe"
    GREY = "grey"
    DISTRESS = "distress"
    NOT_APPLICABLE = "not_applicable"


class DistressResult(BaseModel):
    """Result of a single distress model computation.

    Captures the score, zone classification, partial computation flag,
    missing inputs, model variant used, and 4-quarter trajectory.
    """

    model_config = ConfigDict(frozen=False)

    score: float | None = Field(
        default=None, description="Computed distress score"
    )
    zone: DistressZone = Field(
        default=DistressZone.NOT_APPLICABLE,
        description="Classification zone: safe/grey/distress",
    )
    is_partial: bool = Field(
        default=False,
        description="True if computed with incomplete inputs",
    )
    missing_inputs: list[str] = Field(
        default_factory=lambda: [],
        description="List of missing input names",
    )
    model_variant: str = Field(
        default="",
        description="Model variant used: 'original', 'z_double_prime', etc.",
    )
    trajectory: list[dict[str, float | str]] = Field(
        default_factory=lambda: [],
        description="4-quarter trajectory: [{period, score, zone}]",
    )
    components: dict[str, float | None] = Field(
        default_factory=dict,
        description="Individual model components (e.g., Beneish: DSRI, GMI, ...)",
    )


class DistressIndicators(BaseModel):
    """Financial distress scoring models.

    Uses DistressResult for rich zone + trajectory info instead of
    plain SourcedValue[float].
    """

    model_config = ConfigDict(frozen=False)

    altman_z_score: DistressResult | None = Field(
        default=None,
        description=(
            "Altman Z-Score: <1.81 distress, 1.81-2.99 grey, >2.99 safe"
        ),
    )
    beneish_m_score: DistressResult | None = Field(
        default=None,
        description="Beneish M-Score: >-1.78 suggests earnings manipulation",
    )
    ohlson_o_score: DistressResult | None = Field(
        default=None,
        description=(
            "Ohlson O-Score: higher = greater bankruptcy probability"
        ),
    )
    piotroski_f_score: DistressResult | None = Field(
        default=None,
        description="Piotroski F-Score: 0-9, higher = stronger fundamentals",
    )


# ---------------------------------------------------------------------------
# Peer group models
# ---------------------------------------------------------------------------


class PeerCompany(BaseModel):
    """A single peer company for benchmarking."""

    model_config = ConfigDict(frozen=False)

    ticker: str = Field(description="Peer company ticker symbol")
    name: str = Field(description="Peer company name")
    sic_code: str | None = Field(
        default=None, description="SIC code of the peer"
    )
    industry: str | None = Field(
        default=None, description="Industry classification"
    )
    market_cap: float | None = Field(
        default=None, description="Market capitalization in USD"
    )
    revenue: float | None = Field(
        default=None, description="Annual revenue in USD"
    )
    peer_score: float = Field(
        default=0.0,
        description="Composite peer similarity score 0-100",
    )
    peer_tier: str = Field(
        default="",
        description="Peer tier: 'primary_sic', 'sector_etf', 'market_cap_cohort'",
    )


class PeerGroup(BaseModel):
    """Constructed peer group for benchmarking.

    Multi-signal composite approach combining SIC, industry, market
    cap, revenue magnitude, and business similarity.
    """

    model_config = ConfigDict(frozen=False)

    target_ticker: str = Field(description="Target company ticker")
    peers: list[PeerCompany] = Field(
        default_factory=lambda: [],
        description="List of peer companies ranked by similarity",
    )
    construction_method: str = Field(
        default="",
        description="Description of how peers were selected",
    )
    sector_etf: str | None = Field(
        default=None, description="Sector benchmark ETF ticker"
    )


# ---------------------------------------------------------------------------
# Audit profile
# ---------------------------------------------------------------------------


class AuditProfile(BaseModel):
    """Auditor and audit quality information from 10-K.

    Critical for F3 (Restatement/Audit) scoring factor.
    """

    model_config = ConfigDict(frozen=False)

    auditor_name: SourcedValue[str] | None = Field(
        default=None, description="Current auditor name"
    )
    is_big4: SourcedValue[bool] | None = Field(
        default=None, description="Whether auditor is Big 4 firm"
    )
    tenure_years: SourcedValue[int] | None = Field(
        default=None, description="Years with current auditor"
    )
    opinion_type: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "Audit opinion: unqualified, qualified, adverse, disclaimer"
        ),
    )
    going_concern: SourcedValue[bool] | None = Field(
        default=None, description="Going concern qualification present"
    )
    material_weaknesses: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Material weaknesses in internal controls (SOX 404)",
    )
    significant_deficiencies: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Significant deficiencies in internal controls",
    )
    remediation_status: SourcedValue[str] | None = Field(
        default=None,
        description="Status of remediation for material weaknesses or significant deficiencies",
    )
    restatements: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="Restatement history: date, type, impact",
    )
    critical_audit_matters: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="CAMs from auditor report (PCAOB AS 3101)",
    )
    amendment_filing_10k_count: int = Field(
        default=0,
        description="Count of 10-K/A amendment filings (restatement indicator)",
    )
    amendment_filing_10q_count: int = Field(
        default=0,
        description="Count of 10-Q/A amendment filings (quarterly amendment indicator)",
    )


# ---------------------------------------------------------------------------
# Quarterly XBRL models (8-quarter trend data from Company Facts API)
# ---------------------------------------------------------------------------


class QuarterlyPeriod(BaseModel):
    """A single fiscal quarter of XBRL financial data.

    Holds income, balance sheet, and cash flow data for one quarter,
    with both fiscal (fy/fp) and calendar (frame) period labeling.
    """

    model_config = ConfigDict(frozen=False)

    fiscal_year: int = Field(description="Fiscal year (from fy field)")
    fiscal_quarter: int = Field(
        description="Fiscal quarter 1-4 (from fp field)", ge=1, le=4
    )
    fiscal_label: str = Field(
        description="Display label, e.g. 'Q1 FY2025'"
    )
    calendar_period: str = Field(
        description="Calendar period from frame, e.g. 'CY2024Q4'"
    )
    period_end: str = Field(description="Period end date YYYY-MM-DD")
    period_start: str | None = Field(
        default=None,
        description="Period start date for duration concepts (None for instant-only)",
    )
    income: dict[str, SourcedValue[float]] = Field(
        default_factory=dict,
        description="Income statement items keyed by concept name",
    )
    balance: dict[str, SourcedValue[float]] = Field(
        default_factory=dict,
        description="Balance sheet items keyed by concept name",
    )
    cash_flow: dict[str, SourcedValue[float]] = Field(
        default_factory=dict,
        description="Cash flow items keyed by concept name",
    )


class QuarterlyStatements(BaseModel):
    """Container for up to 8 quarters of XBRL financial data.

    Provides HIGH-confidence quarterly financials from XBRL Company
    Facts API, eliminating LLM hallucination risk for quarterly numbers.
    """

    model_config = ConfigDict(frozen=False)

    quarters: list[QuarterlyPeriod] = Field(
        default_factory=list,
        description="Up to 8 quarters, most recent first",
    )
    fiscal_year_end_month: int | None = Field(
        default=None,
        description="Fiscal year end month (1-12), e.g. 9 for Sep FY",
    )
    extraction_date: datetime | None = Field(
        default=None,
        description="When quarterly data was extracted",
    )
    concepts_resolved: int = Field(
        default=0,
        description="Number of XBRL concepts successfully resolved",
    )
    concepts_attempted: int = Field(
        default=0,
        description="Number of XBRL concepts attempted",
    )


# ---------------------------------------------------------------------------
# Aggregated financial data (top-level EXTRACT output)
# ---------------------------------------------------------------------------


class QuarterlyUpdate(BaseModel):
    """Single quarterly report data extracted from 10-Q.

    Bridges LLM extraction results (TenQExtraction) and the structured
    state model consumed by the renderer. One instance per post-annual
    10-Q filing, sorted most-recent-first in
    ``ExtractedFinancials.quarterly_updates``.
    """

    model_config = ConfigDict(frozen=False)

    quarter: str  # e.g., "Q1 FY2026"
    period_end: str  # e.g., "2025-12-28"
    filing_date: str  # e.g., "2026-01-30"
    accession: str = ""  # Source filing accession number
    revenue: SourcedValue[float] | None = None
    net_income: SourcedValue[float] | None = None
    eps: SourcedValue[float] | None = None
    prior_year_revenue: float | None = None  # Same YTD period, prior year
    prior_year_net_income: float | None = None
    prior_year_eps: float | None = None
    new_legal_proceedings: list[str] = Field(default_factory=list)
    legal_proceedings_updates: list[str] = Field(default_factory=list)
    going_concern: bool = False
    going_concern_detail: str | None = None
    material_weaknesses: list[str] = Field(default_factory=list)
    new_risk_factors: list[str] = Field(default_factory=list)
    md_a_highlights: list[str] = Field(default_factory=list)
    subsequent_events: list[str] = Field(default_factory=list)


class ExtractedFinancials(BaseModel):
    """Aggregated financial data from EXTRACT stage.

    Groups all financial sub-models under one namespace for clean
    state access via state.extracted.financials.
    """

    model_config = ConfigDict(frozen=False)

    statements: FinancialStatements = Field(
        default_factory=FinancialStatements
    )
    distress: DistressIndicators = Field(
        default_factory=DistressIndicators
    )
    audit: AuditProfile = Field(default_factory=AuditProfile)
    peer_group: PeerGroup | None = Field(
        default=None,
        description="Constructed peer group for benchmarking",
    )
    quarterly_updates: list[QuarterlyUpdate] = Field(
        default_factory=lambda: [],
        description="Post-annual 10-Q quarterly updates, most recent first",
    )
    yfinance_quarterly: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Up to 8 quarters of key metrics from yfinance (revenue, "
            "net income, margins, debt, cash flow). Most recent first."
        ),
    )
    quarterly_xbrl: QuarterlyStatements | None = Field(
        default=None,
        description="8-quarter XBRL financial data for trend analysis",
    )
    reconciliation_warnings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="XBRL vs LLM discrepancy warnings from cross-validation",
    )

    # SECT3 analysis fields (populated in EXTRACT stage)
    liquidity: SourcedValue[dict[str, float | None]] | None = Field(
        default=None,
        description=(
            "Liquidity ratios: current_ratio, quick_ratio, "
            "cash_ratio (SECT3-08)"
        ),
    )
    leverage: SourcedValue[dict[str, float | None]] | None = Field(
        default=None,
        description=(
            "Leverage ratios: debt_to_equity, debt_to_ebitda, "
            "interest_coverage (SECT3-09)"
        ),
    )
    debt_structure: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Debt structure: maturity schedule, rates, "
            "covenants (SECT3-10)"
        ),
    )
    refinancing_risk: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Refinancing risk: upcoming maturities, "
            "coverage ratios (SECT3-11)"
        ),
    )
    tax_indicators: SourcedValue[dict[str, Any]] | None = Field(
        default=None,
        description=(
            "Tax indicators: ETR, deferred tax, "
            "haven exposure (SECT3-13)"
        ),
    )
    earnings_quality: SourcedValue[dict[str, float | None]] | None = Field(
        default=None,
        description=(
            "Earnings quality: accruals_ratio, ocf_to_ni, "
            "revenue_quality (SECT3-06)"
        ),
    )
    financial_health_narrative: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "3-5 sentence financial health summary synthesizing "
            "revenue trends, profitability, liquidity, leverage, "
            "and key concerns (SECT3-01)"
        ),
    )
