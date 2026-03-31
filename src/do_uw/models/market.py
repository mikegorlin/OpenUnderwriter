"""Market data models -- part of EXTRACT stage output.

Captures stock performance, insider trading, short interest, and
analyst sentiment. Populated during EXTRACT stage from market data
APIs and SEC Form 4 filings.

Sub-models for SECT4 detailed extraction are in market_events.py.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue
from do_uw.models.market_events import (
    AdverseEventScore,
    AnalystSentimentProfile,
    CapitalMarketsActivity,
    EarningsGuidanceAnalysis,
    InsiderTradingAnalysis,
    StockDropAnalysis,
)


class StockPerformance(BaseModel):
    """Stock price and return metrics.

    Used for F2 (Stock Decline), F7 (Volatility) scoring factors.
    Data sourced from yfinance / Yahoo Finance.
    """

    model_config = ConfigDict(frozen=False)

    current_price: SourcedValue[float] | None = Field(
        default=None, description="Most recent closing price"
    )
    high_52w: SourcedValue[float] | None = Field(
        default=None, description="52-week high price"
    )
    low_52w: SourcedValue[float] | None = Field(
        default=None, description="52-week low price"
    )
    decline_from_high_pct: SourcedValue[float] | None = Field(
        default=None, description="Decline from 52-week high as percentage"
    )
    returns_1y: SourcedValue[float] | None = Field(
        default=None, description="1-year total return percentage"
    )
    returns_3y: SourcedValue[float] | None = Field(
        default=None, description="3-year total return percentage"
    )
    returns_5y: SourcedValue[float] | None = Field(
        default=None, description="5-year total return percentage"
    )
    returns_ytd: SourcedValue[float] | None = Field(
        default=None, description="Year-to-date total return percentage"
    )
    max_drawdown_1y: SourcedValue[float] | None = Field(
        default=None,
        description="Maximum peak-to-trough drawdown in trailing 1 year",
    )
    max_drawdown_5y: SourcedValue[float] | None = Field(
        default=None,
        description="Maximum peak-to-trough drawdown in trailing 5 years",
    )
    beta: SourcedValue[float] | None = Field(
        default=None, description="Beta vs S&P 500 (1yr)"
    )
    volatility_90d: SourcedValue[float] | None = Field(
        default=None,
        description="90-day annualized volatility (std dev of daily returns)",
    )
    sector_beta: SourcedValue[float] | None = Field(
        default=None,
        description="Sector ETF beta vs S&P 500 (1yr)",
    )
    beta_ratio: SourcedValue[float] | None = Field(
        default=None,
        description="Company beta / sector beta ratio (>1 = more volatile than sector)",
    )
    sector_vol_90d: SourcedValue[float] | None = Field(
        default=None,
        description="Sector ETF 90-day annualized volatility",
    )
    idiosyncratic_vol: SourcedValue[float] | None = Field(
        default=None,
        description="Company-specific (non-market) annualized volatility",
    )
    # --- Return decomposition: 3-component attribution (market, sector, company) ---
    returns_1y_market: SourcedValue[float] | None = Field(
        default=None,
        description="1Y return attributed to broad market (SPY return)",
    )
    returns_1y_sector: SourcedValue[float] | None = Field(
        default=None,
        description="1Y return attributed to sector (sector ETF return minus SPY return)",
    )
    returns_1y_company: SourcedValue[float] | None = Field(
        default=None,
        description="1Y return attributed to company-specific factors (residual)",
    )
    returns_5y_market: SourcedValue[float] | None = Field(
        default=None,
        description="5Y return attributed to broad market (SPY return)",
    )
    returns_5y_sector: SourcedValue[float] | None = Field(
        default=None,
        description="5Y return attributed to sector (sector ETF return minus SPY return)",
    )
    returns_5y_company: SourcedValue[float] | None = Field(
        default=None,
        description="5Y return attributed to company-specific factors (residual)",
    )

    # --- MDD ratio: company drawdown relative to sector ---
    mdd_ratio_1y: SourcedValue[float] | None = Field(
        default=None,
        description="1Y company MDD / sector MDD ratio (>1 = worse than sector)",
    )
    mdd_ratio_5y: SourcedValue[float] | None = Field(
        default=None,
        description="5Y company MDD / sector MDD ratio (>1 = worse than sector)",
    )
    sector_mdd_1y: SourcedValue[float] | None = Field(
        default=None,
        description="Sector ETF maximum drawdown over trailing 1 year",
    )
    sector_mdd_5y: SourcedValue[float] | None = Field(
        default=None,
        description="Sector ETF maximum drawdown over trailing 5 years",
    )

    # --- EWMA volatility and regime classification (Phase 89) ---
    ewma_vol_current: SourcedValue[float] | None = Field(
        default=None,
        description="Current EWMA volatility (annualized %, lambda=0.94)",
    )
    vol_regime: SourcedValue[str] | None = Field(
        default=None,
        description="Volatility regime: LOW / NORMAL / ELEVATED / CRISIS",
    )
    vol_regime_duration_days: int | None = Field(
        default=None,
        description="Trading days in current volatility regime",
    )

    trading_days_available: int | None = Field(
        default=None,
        description="Actual trading days of history available (recent IPOs < 252)",
    )
    first_trading_date: str | None = Field(
        default=None,
        description="First available trading date (YYYY-MM-DD) — IPO/listing date",
    )
    sector_relative_performance: SourcedValue[float] | None = Field(
        default=None,
        description="Performance vs sector ETF over trailing period",
    )
    avg_daily_volume: SourcedValue[int] | None = Field(
        default=None,
        description="Average daily trading volume (10-day) from yfinance",
    )
    single_day_events: list[SourcedValue[dict[str, float | str]]] = Field(
        default_factory=lambda: [],
        description="Days with >5% moves: date, change_pct, trigger",
    )
    volume_spike_count: int = Field(
        default=0,
        description="Number of trading days with volume > 2x 20-day moving average in trailing year",
    )
    volume_spike_events: list[dict[str, Any]] = Field(
        default_factory=lambda: [],
        description="Volume spike events with date, volume, volume_multiple, price_change_pct, catalyst",
    )

    # --- Valuation metrics (populated from yfinance info dict) ---
    pe_ratio: SourcedValue[float] | None = Field(
        default=None, description="Trailing P/E ratio"
    )
    forward_pe: SourcedValue[float] | None = Field(
        default=None, description="Forward P/E ratio"
    )
    ev_ebitda: SourcedValue[float] | None = Field(
        default=None, description="Enterprise Value / EBITDA"
    )
    peg_ratio: SourcedValue[float] | None = Field(
        default=None, description="Price/Earnings to Growth ratio"
    )
    price_to_book: SourcedValue[float] | None = Field(
        default=None, description="Price / Book value ratio"
    )
    price_to_sales: SourcedValue[float] | None = Field(
        default=None, description="Price / Sales (trailing 12 months)"
    )
    enterprise_to_revenue: SourcedValue[float] | None = Field(
        default=None, description="Enterprise Value / Revenue"
    )

    # --- Profitability metrics (populated from yfinance info dict) ---
    profit_margin: SourcedValue[float] | None = Field(
        default=None, description="Net profit margin (0-1 scale)"
    )
    operating_margin: SourcedValue[float] | None = Field(
        default=None, description="Operating margin (0-1 scale)"
    )
    gross_margin: SourcedValue[float] | None = Field(
        default=None, description="Gross margin (0-1 scale)"
    )
    return_on_equity: SourcedValue[float] | None = Field(
        default=None, description="Return on equity (0-1 scale)"
    )
    return_on_assets: SourcedValue[float] | None = Field(
        default=None, description="Return on assets (0-1 scale)"
    )

    # --- Growth metrics (populated from yfinance info dict) ---
    revenue_growth: SourcedValue[float] | None = Field(
        default=None, description="Year-over-year revenue growth (0-1 scale)"
    )
    earnings_growth: SourcedValue[float] | None = Field(
        default=None, description="Year-over-year earnings growth (0-1 scale)"
    )

    # --- Scale metrics (populated from yfinance info dict) ---
    market_cap_yf: SourcedValue[float] | None = Field(
        default=None, description="Market cap from yfinance"
    )
    enterprise_value: SourcedValue[float] | None = Field(
        default=None, description="Enterprise value from yfinance"
    )
    employee_count_yf: SourcedValue[int] | None = Field(
        default=None, description="Full-time employees from yfinance"
    )


class InsiderTradingProfile(BaseModel):
    """Insider trading analysis from SEC Form 4 filings.

    Used as multiplier for F2 (Stock Decline) and for
    INFORMED_TRADING pattern detection.
    """

    model_config = ConfigDict(frozen=False)

    net_buying_selling: SourcedValue[str] | None = Field(
        default=None,
        description="Net direction: NET_BUYING, NET_SELLING, NEUTRAL",
    )
    total_sold_value: SourcedValue[float] | None = Field(
        default=None, description="Total insider selling value in USD (12mo)"
    )
    total_bought_value: SourcedValue[float] | None = Field(
        default=None, description="Total insider buying value in USD (12mo)"
    )
    cluster_events: list[SourcedValue[dict[str, str | float]]] = Field(
        default_factory=lambda: [],
        description="3+ insiders selling in same window",
    )
    ceo_cfo_pct_sold: SourcedValue[float] | None = Field(
        default=None,
        description="Percentage of holdings sold by CEO/CFO (6mo)",
    )
    has_10b5_1_modifications: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether 10b5-1 plans were modified/terminated",
    )


class ShortInterestProfile(BaseModel):
    """Short interest analysis.

    Used for F6 (Short Interest) scoring factor and SHORT_ATTACK pattern.
    Compared against sector baselines from sectors.json.
    """

    model_config = ConfigDict(frozen=False)

    short_pct_float: SourcedValue[float] | None = Field(
        default=None, description="Short interest as percentage of float"
    )
    days_to_cover: SourcedValue[float] | None = Field(
        default=None, description="Days to cover at average volume"
    )
    trend_6m: SourcedValue[str] | None = Field(
        default=None,
        description="6-month trend: RISING, STABLE, DECLINING",
    )
    vs_sector_ratio: SourcedValue[float] | None = Field(
        default=None,
        description="Ratio of company SI to sector average SI",
    )
    shares_short: SourcedValue[int] | None = Field(
        default=None, description="Total shares sold short"
    )
    shares_short_prior: SourcedValue[int] | None = Field(
        default=None, description="Shares sold short prior month"
    )
    short_pct_shares_out: SourcedValue[float] | None = Field(
        default=None, description="Short % of shares outstanding"
    )
    short_seller_reports: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="Named short seller reports: source, date, allegations",
    )


class EightKFiling(BaseModel):
    """A single 8-K filing with parsed Item numbers and D&O classification.

    Combines regex-parsed items from the raw filing text with any
    LLM-extracted items_covered for comprehensive coverage.
    """

    model_config = ConfigDict(frozen=False)

    accession: str = Field(default="", description="SEC accession number")
    filing_date: str = Field(default="", description="Filing date (YYYY-MM-DD)")
    items: list[str] = Field(
        default_factory=list,
        description="Item numbers found in this 8-K (e.g. ['2.02', '9.01'])",
    )
    item_titles: dict[str, str] = Field(
        default_factory=dict,
        description="Item number -> human-readable title mapping",
    )
    do_critical_items: list[str] = Field(
        default_factory=list,
        description="Subset of items that are D&O-critical (4.01, 4.02, 5.02, 2.05, 2.06)",
    )
    do_severity: str = Field(
        default="LOW",
        description="Highest D&O severity across items: CRITICAL, HIGH, MEDIUM, LOW",
    )
    event_summary: str = Field(
        default="",
        description="One-line summary of the 8-K event(s)",
    )


class EightKItemSummary(BaseModel):
    """Aggregated 8-K item analysis across all filings for a company.

    Provides a structured view of what types of 8-K events the company
    has filed in the lookback period, with D&O-critical items flagged.
    """

    model_config = ConfigDict(frozen=False)

    filings: list[EightKFiling] = Field(
        default_factory=list,
        description="Individual 8-K filings with parsed items",
    )
    total_filings: int = Field(default=0, description="Total 8-K filings in period")
    item_frequency: dict[str, int] = Field(
        default_factory=dict,
        description="How many times each item number appeared across all 8-Ks",
    )
    do_critical_count: int = Field(
        default=0,
        description="Number of filings containing at least one D&O-critical item",
    )
    has_restatement: bool = Field(
        default=False,
        description="Whether any 8-K contained Item 4.02 (non-reliance/restatement)",
    )
    has_auditor_change: bool = Field(
        default=False,
        description="Whether any 8-K contained Item 4.01 (auditor change)",
    )
    has_officer_departure: bool = Field(
        default=False,
        description="Whether any 8-K contained Item 5.02 (departure/appointment)",
    )
    has_restructuring: bool = Field(
        default=False,
        description="Whether any 8-K contained Item 2.05 (exit/restructuring costs)",
    )
    has_impairment: bool = Field(
        default=False,
        description="Whether any 8-K contained Item 2.06 (material impairment)",
    )


class MarketSignals(BaseModel):
    """Aggregated market signal data from EXTRACT stage.

    Groups all market sub-models under one namespace for clean
    state access via state.extracted.market.
    """

    model_config = ConfigDict(frozen=False)

    stock: StockPerformance = Field(default_factory=StockPerformance)
    insider_trading: InsiderTradingProfile = Field(
        default_factory=InsiderTradingProfile
    )
    short_interest: ShortInterestProfile = Field(
        default_factory=ShortInterestProfile
    )

    # Phase 4 typed sub-models (populated by Phase 4 extractors)
    stock_drops: StockDropAnalysis = Field(
        default_factory=StockDropAnalysis,
        description="SECT4-03: Stock drop event analysis",
    )
    insider_analysis: InsiderTradingAnalysis = Field(
        default_factory=InsiderTradingAnalysis,
        description="SECT4-04: Detailed insider trading analysis",
    )
    earnings_guidance: EarningsGuidanceAnalysis = Field(
        default_factory=EarningsGuidanceAnalysis,
        description="SECT4-06: Earnings guidance record and analysis",
    )
    analyst: AnalystSentimentProfile = Field(
        default_factory=AnalystSentimentProfile,
        description="SECT4-07: Analyst sentiment profile",
    )
    capital_markets: CapitalMarketsActivity = Field(
        default_factory=CapitalMarketsActivity,
        description="SECT4-08: Capital markets activity and Section 11",
    )
    adverse_events: AdverseEventScore = Field(
        default_factory=AdverseEventScore,
        description="SECT4-09: Composite adverse event scoring",
    )
    eight_k_items: EightKItemSummary = Field(
        default_factory=EightKItemSummary,
        description="SECT4-10: 8-K item classification and D&O flagging",
    )
