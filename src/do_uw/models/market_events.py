"""Market event sub-models for SECT4 extraction output.

Provides typed Pydantic models for:
- Stock drop events and analysis (SECT4-03)
- Insider transactions and cluster events (SECT4-04)
- Earnings guidance records (SECT4-06)
- Analyst sentiment profiles (SECT4-07)
- Capital markets activity (SECT4-08)
- Adverse event scoring (SECT4-09)

These models are referenced by MarketSignals in market.py.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue

# ---------------------------------------------------------------------------
# SECT4-03: Stock Drop Events
# ---------------------------------------------------------------------------


class DropType(StrEnum):
    """Classification of stock price decline events."""

    SINGLE_DAY = "SINGLE_DAY"
    MULTI_DAY = "MULTI_DAY"


class StockDropEvent(BaseModel):
    """A significant stock price decline event.

    Used for F2 (Stock Decline) scoring factor. Captures both
    single-day crashes and multi-day slide periods that may
    trigger D&O litigation.
    """

    model_config = ConfigDict(frozen=False)

    date: SourcedValue[str] | None = Field(
        default=None, description="Date of the drop event (YYYY-MM-DD)"
    )
    drop_pct: SourcedValue[float] | None = Field(
        default=None,
        description="Percentage decline (negative number, e.g. -15.3)",
    )
    drop_type: str = Field(default="", description="SINGLE_DAY or MULTI_DAY classification")
    period_days: int = Field(default=1, description="Duration of decline in trading days")
    sector_return_pct: SourcedValue[float] | None = Field(
        default=None,
        description="Sector ETF return over same period for comparison",
    )
    is_company_specific: bool = Field(
        default=False,
        description="True if drop exceeds sector decline (company-specific)",
    )
    trigger_event: SourcedValue[str] | None = Field(
        default=None,
        description="Identified catalyst: earnings miss, restatement, etc.",
    )
    close_price: float | None = Field(default=None, description="Closing price on drop date")
    recovery_days: int | None = Field(
        default=None,
        description="Trading days until stock recovered to pre-drop price level",
    )
    is_market_wide: bool = Field(
        default=False,
        description="True if SPY dropped >3% on same day (market-wide event)",
    )
    trigger_source_url: str = Field(
        default="",
        description="URL to 8-K filing or news article explaining trigger",
    )
    trigger_description: str | None = Field(
        default="",
        description="One-line description of what caused the drop (from 8-K content or web search)",
    )
    trigger_category: str = Field(
        default="",
        description=(
            "Categorization of drop cause: earnings_miss, guidance_cut, "
            "litigation, analyst_downgrade, regulatory, management_departure, "
            "restatement, acquisition, market_wide, unknown"
        ),
    )
    trigger_8k_items: list[str] = Field(
        default_factory=lambda: [],
        description="8-K item numbers found near this drop (e.g., ['2.02', '5.02'])",
    )
    cumulative_pct: float | None = Field(
        default=None,
        description="For grouped events: total decline from first to last day",
    )
    # --- Phase 89: Abnormal return event study fields ---
    abnormal_return_pct: float | None = Field(
        default=None,
        description="Abnormal return on drop day via market model (%)",
    )
    abnormal_return_t_stat: float | None = Field(
        default=None,
        description="T-statistic for abnormal return",
    )
    is_statistically_significant: bool = Field(
        default=False,
        description="True if |t-stat| >= 1.96",
    )
    market_model_alpha: float | None = Field(
        default=None,
        description="Market model alpha from estimation window",
    )
    market_model_beta: float | None = Field(
        default=None,
        description="Market model beta from estimation window",
    )
    # --- Phase 90: Drop enhancement fields ---
    decay_weight: float | None = Field(
        default=None,
        description="Time-decay weight (1.0=today, 0.5=180d ago, 0.25=360d ago)",
    )
    decay_weighted_severity: float | None = Field(
        default=None,
        description="abs(drop_pct) * decay_weight for recency-adjusted ranking",
    )
    market_pct: float | None = Field(
        default=None,
        description="Market (SPY) contribution to drop (%)",
    )
    sector_pct: float | None = Field(
        default=None,
        description="Sector contribution to drop (sector - market) (%)",
    )
    company_pct: float | None = Field(
        default=None,
        description="Company-specific residual (company - sector) (%)",
    )
    is_market_driven: bool = Field(
        default=False,
        description="True if market contribution >50% of absolute total drop",
    )
    corrective_disclosure_type: str = Field(
        default="",
        description="Type of corrective disclosure found: '8-K', 'news', or ''",
    )
    corrective_disclosure_lag_days: int | None = Field(
        default=None,
        description="Days between drop and corrective disclosure (1-14)",
    )
    corrective_disclosure_url: str = Field(
        default="",
        description="URL of the corrective disclosure document",
    )
    # --- Phase 119: Catalyst + D&O assessment fields ---
    from_price: float | None = Field(
        default=None, description="Price at start of drop period (close of prior day)"
    )
    volume: int | None = Field(
        default=None, description="Trading volume on drop date (or total over multi-day period)"
    )
    do_assessment: str = Field(
        default="", description="D&O litigation risk assessment for this drop catalyst"
    )


class StockDropAnalysis(BaseModel):
    """Container for stock drop event analysis (SECT4-03).

    Aggregates all significant stock declines over the analysis
    period, identifying worst events and company-specific drops
    that may indicate D&O risk.
    """

    model_config = ConfigDict(frozen=False)

    single_day_drops: list[StockDropEvent] = Field(
        default_factory=lambda: [],
        description="Single-day drops exceeding threshold (e.g. >5%)",
    )
    multi_day_drops: list[StockDropEvent] = Field(
        default_factory=lambda: [],
        description="Multi-day slide periods exceeding threshold",
    )
    analysis_period_months: int = Field(default=18, description="Lookback period in months")
    worst_single_day: StockDropEvent | None = Field(
        default=None, description="Largest single-day decline"
    )
    worst_multi_day: StockDropEvent | None = Field(
        default=None, description="Worst multi-day slide period"
    )
    # --- Phase 89: DDL/MDL exposure fields ---
    ddl_exposure: SourcedValue[float] | None = Field(
        default=None,
        description="DDL exposure: market_cap x worst_drop magnitude (USD)",
    )
    mdl_exposure: SourcedValue[float] | None = Field(
        default=None,
        description="MDL exposure: market_cap x max_drawdown magnitude (USD)",
    )
    ddl_settlement_estimate: SourcedValue[float] | None = Field(
        default=None,
        description="Estimated settlement: DDL x 1.8% (USD)",
    )


# ---------------------------------------------------------------------------
# SECT4-04: Insider Trading
# ---------------------------------------------------------------------------


class InsiderTransaction(BaseModel):
    """Individual insider transaction from SEC Form 4 filings.

    Captures buy/sell activity by officers and directors, including
    10b5-1 plan status which affects D&O risk assessment.
    """

    model_config = ConfigDict(frozen=False)

    insider_name: SourcedValue[str] | None = Field(default=None, description="Name of the insider")
    title: SourcedValue[str] | None = Field(
        default=None, description="Title/role (CEO, CFO, Director, etc.)"
    )
    transaction_date: SourcedValue[str] | None = Field(
        default=None, description="Date of transaction (YYYY-MM-DD)"
    )
    transaction_type: str = Field(default="", description="BUY, SELL, EXERCISE, GIFT, etc.")
    transaction_code: str = Field(
        default="",
        description="SEC transaction code (P=purchase, S=sale, etc.)",
    )
    shares: SourcedValue[float] | None = Field(
        default=None, description="Number of shares transacted"
    )
    price_per_share: SourcedValue[float] | None = Field(
        default=None, description="Price per share in USD"
    )
    total_value: SourcedValue[float] | None = Field(
        default=None, description="Total transaction value in USD"
    )
    is_10b5_1: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether transaction was under 10b5-1 plan",
    )
    is_discretionary: bool = Field(
        default=False,
        description="True if not under 10b5-1 plan (discretionary sale)",
    )
    plan_adoption_date: str | None = Field(
        default=None,
        description="Date the 10b5-1 plan was adopted (YYYY-MM-DD), from Form 4 footnotes",
    )
    # --- Phase 71 enhancements ---
    shares_owned_following: SourcedValue[float] | None = Field(
        default=None,
        description="Post-transaction shares owned (non-derivative or derivative)",
    )
    is_director: bool = Field(default=False, description="reportingOwnerRelationship isDirector")
    is_officer: bool = Field(default=False, description="reportingOwnerRelationship isOfficer")
    is_ten_pct_owner: bool = Field(
        default=False, description="reportingOwnerRelationship isTenPercentOwner"
    )
    ownership_nature: str = Field(default="D", description="D=direct, I=indirect")
    indirect_ownership_explanation: str = Field(
        default="", description="e.g. 'By Trust', 'By LLC'"
    )
    accession_number: str = Field(default="", description="SEC accession number for dedup")
    is_amendment: bool = Field(default=False, description="True if from Form 4/A filing")
    is_superseded: bool = Field(
        default=False, description="True if original replaced by 4/A amendment"
    )


class OwnershipConcentrationAlert(BaseModel):
    """Alert when insider sells significant portion of holdings."""

    model_config = ConfigDict(frozen=False)

    insider_name: str = Field(default="")
    role: str = Field(default="", description="CEO, CFO, Director, etc.")
    severity: str = Field(
        default="INFORMATIONAL",
        description="RED_FLAG, WARNING, INFORMATIONAL, POSITIVE",
    )
    personal_pct_sold: float = Field(default=0.0, description="% of own holdings sold in window")
    outstanding_pct: float | None = Field(
        default=None, description="% of shares outstanding (if available)"
    )
    shares_sold: float = Field(default=0.0)
    shares_remaining: float = Field(default=0.0)
    lookback_months: int = Field(default=6)
    is_10b5_1: bool = Field(default=False)
    is_c_suite: bool = Field(default=False)
    compounds_with_cluster: bool = Field(
        default=False, description="True if cluster selling overlaps"
    )


class OwnershipTrajectoryPoint(BaseModel):
    """Single point in insider ownership timeline."""

    model_config = ConfigDict(frozen=False)

    date: str = Field(default="")
    shares_owned: float = Field(default=0.0)
    transaction_type: str = Field(default="")
    change: float = Field(default=0.0, description="positive=buy, negative=sell")


class InsiderClusterEvent(BaseModel):
    """Cluster of insider selling activity in a narrow window.

    When 3+ insiders sell in the same period, it is a significant
    D&O risk signal (INFORMED_TRADING pattern).
    """

    model_config = ConfigDict(frozen=False)

    start_date: str = Field(default="", description="Start of cluster window (YYYY-MM-DD)")
    end_date: str = Field(default="", description="End of cluster window (YYYY-MM-DD)")
    insider_count: int = Field(default=0, description="Number of insiders in cluster")
    insiders: list[str] = Field(
        default_factory=lambda: [],
        description="Names of insiders in the cluster",
    )
    total_value: float = Field(default=0.0, description="Combined dollar value of cluster sales")


class ExerciseSellEvent(BaseModel):
    """Exercise-and-sell pattern: insider exercises options and sells same/adjacent day."""

    model_config = ConfigDict(frozen=False)

    owner: str = Field(default="", description="Insider name")
    date: str = Field(default="", description="Date of exercise-sell (YYYY-MM-DD)")
    exercised_shares: float = Field(default=0.0)
    sold_shares: float = Field(default=0.0)
    sold_value: float = Field(default=0.0)
    severity: str = Field(default="AMBER", description="Always AMBER per user decision")
    is_10b5_1: bool = Field(default=False)


class FilingTimingSuspect(BaseModel):
    """Insider transaction suspiciously timed relative to material 8-K filing."""

    model_config = ConfigDict(frozen=False)

    insider_name: str = Field(default="")
    transaction_date: str = Field(default="")
    transaction_type: str = Field(default="", description="SELL or BUY")
    filing_date: str = Field(default="", description="8-K filing date")
    filing_item: str = Field(default="", description="8-K item number (e.g. 2.02)")
    filing_sentiment: str = Field(default="", description="NEGATIVE, POSITIVE")
    days_before_filing: int = Field(default=0)
    transaction_value: float = Field(default=0.0)
    severity: str = Field(
        default="AMBER",
        description="RED_FLAG if sell-before-negative, AMBER if buy-before-positive",
    )


class InsiderTradingAnalysis(BaseModel):
    """Container for insider trading analysis (SECT4-04).

    Aggregates individual transactions and identifies cluster
    events that indicate coordinated selling.
    """

    model_config = ConfigDict(frozen=False)

    transactions: list[InsiderTransaction] = Field(
        default_factory=lambda: [],
        description="Individual insider transactions in period",
    )
    cluster_events: list[InsiderClusterEvent] = Field(
        default_factory=lambda: [],
        description="Cluster selling events detected",
    )
    net_buying_selling: SourcedValue[str] | None = Field(
        default=None,
        description="Net direction: NET_BUYING, NET_SELLING, NEUTRAL",
    )
    pct_10b5_1: SourcedValue[float] | None = Field(
        default=None,
        description="Percentage of sales under 10b5-1 plans",
    )
    ownership_alerts: list[OwnershipConcentrationAlert] = Field(
        default_factory=lambda: [],
        description="Ownership concentration alerts per insider",
    )
    ownership_trajectories: dict[str, list[OwnershipTrajectoryPoint]] = Field(
        default_factory=dict,
        description="Ownership timeline keyed by insider_name",
    )
    insider_purchases: list[InsiderTransaction] = Field(
        default_factory=lambda: [],
        description="Open-market purchases (positive signal)",
    )
    exercise_sell_events: list[ExerciseSellEvent] = Field(
        default_factory=lambda: [],
        description="Exercise-and-sell patterns detected",
    )
    timing_suspects: list[FilingTimingSuspect] = Field(
        default_factory=lambda: [],
        description="Pre-announcement trading suspects",
    )


# ---------------------------------------------------------------------------
# SECT4-06: Earnings Guidance
# ---------------------------------------------------------------------------


class EarningsResult(StrEnum):
    """Earnings vs guidance outcome."""

    BEAT = "BEAT"
    MISS = "MISS"
    MEET = "MEET"


class EarningsQuarterRecord(BaseModel):
    """Earnings performance for a single quarter (SECT4-06).

    Tracks guidance vs actual results and market reaction,
    used for F3 (Earnings Volatility) scoring and
    GUIDANCE_MANIPULATION pattern detection.
    """

    model_config = ConfigDict(frozen=False)

    quarter: str = Field(default="", description="Quarter label (e.g. Q3 2025)")
    consensus_eps_low: SourcedValue[float] | None = Field(
        default=None, description="Low end of analyst consensus EPS estimate"
    )
    consensus_eps_high: SourcedValue[float] | None = Field(
        default=None, description="High end of analyst consensus EPS estimate"
    )
    guidance_revenue_low: SourcedValue[float] | None = Field(
        default=None, description="Low end of revenue guidance (millions)"
    )
    guidance_revenue_high: SourcedValue[float] | None = Field(
        default=None, description="High end of revenue guidance (millions)"
    )
    actual_eps: SourcedValue[float] | None = Field(default=None, description="Actual reported EPS")
    actual_revenue: SourcedValue[float] | None = Field(
        default=None, description="Actual reported revenue (millions)"
    )
    result: str = Field(default="", description="BEAT, MISS, or MEET")
    miss_magnitude_pct: SourcedValue[float] | None = Field(
        default=None,
        description="How much the miss was as pct of guidance midpoint",
    )
    stock_reaction_pct: SourcedValue[float] | None = Field(
        default=None,
        description="Stock price change on earnings day (next trading day)",
    )
    next_day_return_pct: SourcedValue[float] | None = Field(
        default=None,
        description="Stock price change from pre-earnings close to next-day close (%)",
    )
    week_return_pct: SourcedValue[float] | None = Field(
        default=None,
        description="Stock price change from pre-earnings close to T+5 trading days close (%)",
    )


class GuidancePhilosophy(StrEnum):
    """Company's guidance approach classification."""

    CONSERVATIVE = "CONSERVATIVE"
    AGGRESSIVE = "AGGRESSIVE"
    NO_GUIDANCE = "NO_GUIDANCE"
    MIXED = "MIXED"


class EarningsGuidanceAnalysis(BaseModel):
    """Container for earnings guidance analysis (SECT4-06).

    Tracks beat/miss record over trailing quarters, identifies
    patterns like consecutive misses or guidance withdrawals.
    """

    model_config = ConfigDict(frozen=False)

    provides_forward_guidance: bool = Field(
        default=False,
        description=(
            "Whether the company provides explicit forward earnings/revenue guidance. "
            "Determined from 10-K/10-Q language analysis, not from analyst estimates."
        ),
    )
    quarters: list[EarningsQuarterRecord] = Field(
        default_factory=lambda: [],
        description="Per-quarter earnings records (most recent first)",
    )
    beat_rate: SourcedValue[float] | None = Field(
        default=None,
        description="Percentage of quarters that beat guidance",
    )
    consecutive_miss_count: int = Field(
        default=0,
        description="Current streak of consecutive misses (0 = no streak)",
    )
    guidance_withdrawals: int = Field(
        default=0,
        description="Number of guidance withdrawals in analysis period",
    )
    philosophy: str = Field(
        default="",
        description="CONSERVATIVE, AGGRESSIVE, NO_GUIDANCE, or MIXED",
    )
    guidance_detail: str | None = Field(
        default=None,
        description=(
            "What the company guides on: 'EPS only', 'Revenue + EPS', "
            "'Full P&L', etc. None if company does not provide guidance."
        ),
    )
    guidance_frequency: str | None = Field(
        default=None,
        description=(
            "How often guidance is issued: 'quarterly', 'annual', 'none'. None if not determined."
        ),
    )
    guidance_history: list[str] = Field(
        default_factory=lambda: [],
        description=("Key guidance changes: 'Withdrew Q2 2024', 'Narrowed Q3 2024', etc."),
    )


# ---------------------------------------------------------------------------
# SECT4-07: Analyst Sentiment
# ---------------------------------------------------------------------------


class AnalystSentimentProfile(BaseModel):
    """Analyst coverage and sentiment data (SECT4-07).

    Used for overall risk context -- declining analyst sentiment
    or target price cuts often precede D&O claims.
    """

    model_config = ConfigDict(frozen=False)

    coverage_count: SourcedValue[int] | None = Field(
        default=None, description="Number of analysts covering the stock"
    )
    analyst_count: SourcedValue[int] | None = Field(
        default=None,
        description="Number of analyst opinions (from yfinance numberOfAnalystOpinions)",
    )
    consensus: SourcedValue[str] | None = Field(
        default=None,
        description="Consensus recommendation: BUY, HOLD, SELL, etc.",
    )
    recommendation_mean: SourcedValue[float] | None = Field(
        default=None,
        description="Mean recommendation score (1=Strong Buy, 5=Sell)",
    )
    target_price_mean: SourcedValue[float] | None = Field(
        default=None, description="Mean analyst target price"
    )
    target_price_high: SourcedValue[float] | None = Field(
        default=None, description="Highest analyst target price"
    )
    target_price_low: SourcedValue[float] | None = Field(
        default=None, description="Lowest analyst target price"
    )
    recent_upgrades: int = Field(default=0, description="Upgrades in trailing 90 days")
    recent_downgrades: int = Field(default=0, description="Downgrades in trailing 90 days")


# ---------------------------------------------------------------------------
# SECT4-08: Capital Markets Activity
# ---------------------------------------------------------------------------


class CapitalMarketsOffering(BaseModel):
    """Individual capital markets offering or registration (SECT4-08).

    Tracks offerings that create Section 11 liability windows
    for D&O insurance purposes.
    """

    model_config = ConfigDict(frozen=False)

    offering_type: str = Field(
        default="",
        description="IPO, SECONDARY, FOLLOW_ON, ATM, CONVERTIBLE, etc.",
    )
    filing_type: str = Field(
        default="",
        description="SEC filing type: S-1, S-3, F-1, F-3, etc.",
    )
    date: SourcedValue[str] | None = Field(
        default=None, description="Offering/filing date (YYYY-MM-DD)"
    )
    amount: SourcedValue[float] | None = Field(default=None, description="Offering amount in USD")
    section_11_window_end: str = Field(
        default="",
        description="End of Section 11 statute of limitations (YYYY-MM-DD)",
    )


class CapitalMarketsActivity(BaseModel):
    """Container for capital markets activity (SECT4-08).

    Tracks shelf registrations, recent offerings, and active
    Section 11 liability windows.
    """

    model_config = ConfigDict(frozen=False)

    shelf_registrations: list[CapitalMarketsOffering] = Field(
        default_factory=lambda: [],
        description="Active shelf registration statements",
    )
    offerings_3yr: list[CapitalMarketsOffering] = Field(
        default_factory=lambda: [],
        description="Offerings in trailing 3-year period",
    )
    has_atm_program: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether company has active at-the-market program",
    )
    convertible_securities: list[CapitalMarketsOffering] = Field(
        default_factory=lambda: [],
        description="Outstanding convertible securities",
    )
    active_section_11_windows: int = Field(
        default=0,
        description="Count of offerings with open Section 11 windows",
    )


# ---------------------------------------------------------------------------
# SECT4-09: Adverse Event Scoring
# ---------------------------------------------------------------------------


class SeverityLevel(StrEnum):
    """Adverse event severity classification."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AdverseEventScore(BaseModel):
    """Composite adverse event score (SECT4-09).

    Aggregates all negative market signals into a single
    risk score for comparison against peers.
    """

    model_config = ConfigDict(frozen=False)

    total_score: SourcedValue[float] | None = Field(
        default=None, description="Composite adverse event score (0-100)"
    )
    event_count: int = Field(default=0, description="Total adverse events identified")
    severity_breakdown: dict[str, int] = Field(
        default_factory=dict,
        description="Count by severity: LOW, MEDIUM, HIGH, CRITICAL",
    )
    peer_rank: SourcedValue[int] | None = Field(
        default=None,
        description="Rank within peer group (1=most events)",
    )
    peer_percentile: SourcedValue[float] | None = Field(
        default=None,
        description="Percentile within peer group (0-100, lower=worse)",
    )
