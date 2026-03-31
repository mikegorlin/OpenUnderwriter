"""Pydantic models for XBRL forensic analysis results.

Provides typed result models for all forensic modules in Phase 69:
- ForensicMetric: Base metric with value, zone, trend, confidence
- BalanceSheetForensics: 5 balance sheet health indicators
- CapitalAllocationForensics: 4 capital deployment indicators
- DebtTaxForensics: 5 debt/tax structure indicators
- RevenueForensics: 4 revenue quality indicators
- BeneishDecomposition: 8-index M-Score breakdown + trajectory
- EarningsQualityDashboard: 4 earnings quality indicators
- MAForensics: M&A pattern analysis
- XBRLForensics: Top-level container for all forensic results
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import Confidence


class ForensicMetric(BaseModel):
    """A single forensic metric with zone classification.

    Every forensic computation produces one of these. The zone
    indicates risk level (safe/warning/danger/insufficient_data).
    """

    model_config = ConfigDict(frozen=False)

    value: float | None = Field(
        default=None, description="Computed metric value"
    )
    zone: str = Field(
        default="insufficient_data",
        description="Risk zone: safe, warning, danger, insufficient_data",
    )
    trend: str | None = Field(
        default=None,
        description="Trend direction: improving, stable, deteriorating",
    )
    confidence: Confidence = Field(
        default=Confidence.LOW,
        description="Composite confidence = min(input confidences)",
    )


class BalanceSheetForensics(BaseModel):
    """Balance sheet forensic indicators (FRNSC-01).

    Goodwill impairment risk, intangible concentration, off-balance-sheet
    exposure, cash conversion cycle, and working capital volatility.
    """

    model_config = ConfigDict(frozen=False)

    goodwill_to_assets: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Goodwill / Total Assets ratio with trend",
    )
    intangible_concentration: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="(Goodwill + Intangibles) / Total Assets",
    )
    off_balance_sheet_ratio: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Operating lease liabilities / Total Assets",
    )
    cash_conversion_cycle: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Inventory days + DSO - DPO",
    )
    working_capital_volatility: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Coefficient of variation of current ratio across periods",
    )


class CapitalAllocationForensics(BaseModel):
    """Capital allocation forensic indicators (FRNSC-02).

    ROIC trend, acquisition effectiveness, buyback timing, dividend
    sustainability.
    """

    model_config = ConfigDict(frozen=False)

    roic: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Return on invested capital trend",
    )
    acquisition_effectiveness: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Goodwill growth vs revenue growth post-acquisition",
    )
    buyback_timing: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Share repurchase timing vs stock price",
    )
    dividend_sustainability: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Dividend payout vs free cash flow coverage",
    )


class DebtTaxForensics(BaseModel):
    """Debt and tax structure forensic indicators (FRNSC-03).

    Interest coverage trajectory, debt maturity concentration, ETR
    anomalies, deferred tax liability growth, pension underfunding.
    """

    model_config = ConfigDict(frozen=False)

    interest_coverage: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="EBIT / Interest expense trajectory",
    )
    debt_maturity_concentration: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Near-term debt / total debt concentration",
    )
    etr_anomaly: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Effective tax rate vs statutory rate divergence",
    )
    deferred_tax_growth: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Deferred tax liability growth rate",
    )
    pension_underfunding: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Pension liability relative to plan assets",
    )


class RevenueForensics(BaseModel):
    """Revenue quality forensic indicators (FRNSC-04).

    Deferred revenue divergence, channel stuffing indicator, margin
    compression, OCF/revenue ratio.
    """

    model_config = ConfigDict(frozen=False)

    deferred_revenue_divergence: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Revenue growth vs deferred revenue growth divergence",
    )
    channel_stuffing_indicator: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="AR growth / revenue growth ratio",
    )
    margin_compression: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Gross margin trend across periods",
    )
    ocf_revenue_ratio: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Operating cash flow / Revenue ratio",
    )


class BeneishDecomposition(BaseModel):
    """Beneish M-Score component decomposition (FRNSC-05).

    Exposes all 8 individual indices that compose the M-Score,
    plus trajectory across periods.
    """

    model_config = ConfigDict(frozen=False)

    composite_score: float | None = Field(
        default=None, description="Overall M-Score composite"
    )
    dsri: float | None = Field(
        default=None, description="Days Sales in Receivables Index"
    )
    gmi: float | None = Field(
        default=None, description="Gross Margin Index"
    )
    aqi: float | None = Field(
        default=None, description="Asset Quality Index"
    )
    sgi: float | None = Field(
        default=None, description="Sales Growth Index"
    )
    depi: float | None = Field(
        default=None, description="Depreciation Index"
    )
    sgai: float | None = Field(
        default=None, description="SGA Expense Index"
    )
    tata: float | None = Field(
        default=None, description="Total Accruals to Total Assets"
    )
    lvgi: float | None = Field(
        default=None, description="Leverage Index"
    )
    zone: str = Field(
        default="insufficient_data",
        description="Overall zone: safe, manipulation_likely, insufficient_data",
    )
    primary_driver: str | None = Field(
        default=None,
        description="Index contributing most to manipulation signal",
    )
    trajectory: list[dict[str, float | str]] = Field(
        default_factory=list,
        description="M-Score trajectory across periods",
    )


class EarningsQualityDashboard(BaseModel):
    """Earnings quality dashboard indicators (FRNSC-09).

    Sloan accruals, cash flow manipulation, SBC/revenue, non-GAAP gap.
    """

    model_config = ConfigDict(frozen=False)

    sloan_accruals: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Sloan accrual anomaly ratio",
    )
    cash_flow_manipulation: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Cash flow quality indicator",
    )
    sbc_revenue_ratio: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="Stock-based compensation / Revenue",
    )
    non_gaap_gap: ForensicMetric = Field(
        default_factory=ForensicMetric,
        description="GAAP vs non-GAAP earnings divergence",
    )


class MAForensics(BaseModel):
    """M&A forensic analysis (FRNSC-08).

    Serial acquirer detection, acquisition pattern analysis.
    """

    model_config = ConfigDict(frozen=False)

    is_serial_acquirer: bool = Field(
        default=False,
        description="True if acquisitions in 3+ of last 5 years",
    )
    acquisition_years: list[str] = Field(
        default_factory=list,
        description="Years with acquisition activity",
    )
    total_acquisition_spend: float | None = Field(
        default=None,
        description="Total acquisition spend across available periods",
    )
    goodwill_growth_rate: float | None = Field(
        default=None,
        description="Goodwill growth rate vs revenue growth rate",
    )
    acquisition_to_revenue: float | None = Field(
        default=None,
        description="Acquisition spend / Revenue ratio",
    )


class XBRLForensics(BaseModel):
    """Top-level container for all XBRL forensic analysis results.

    Aggregates all forensic sub-modules into a single namespace
    stored on state.analysis.xbrl_forensics.
    """

    model_config = ConfigDict(frozen=False)

    balance_sheet: BalanceSheetForensics = Field(
        default_factory=BalanceSheetForensics,
        description="Balance sheet forensic indicators (FRNSC-01)",
    )
    capital_allocation: CapitalAllocationForensics = Field(
        default_factory=CapitalAllocationForensics,
        description="Capital allocation forensic indicators (FRNSC-02)",
    )
    debt_tax: DebtTaxForensics = Field(
        default_factory=DebtTaxForensics,
        description="Debt/tax forensic indicators (FRNSC-03)",
    )
    revenue: RevenueForensics = Field(
        default_factory=RevenueForensics,
        description="Revenue quality forensic indicators (FRNSC-04)",
    )
    beneish: BeneishDecomposition = Field(
        default_factory=BeneishDecomposition,
        description="Beneish M-Score decomposition (FRNSC-05)",
    )
    earnings_quality: EarningsQualityDashboard = Field(
        default_factory=EarningsQualityDashboard,
        description="Earnings quality dashboard (FRNSC-09)",
    )
    ma_forensics: MAForensics = Field(
        default_factory=MAForensics,
        description="M&A forensic analysis (FRNSC-08)",
    )
