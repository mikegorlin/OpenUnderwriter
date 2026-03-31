"""Typed context model for market section.

Matches the dict returned by extract_market() in
context_builders/market.py plus evaluative helpers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MarketContext(BaseModel):
    """Typed context for the stock & market section.

    Covers price/valuation, short interest, insider trading, evaluative
    signals, stock drops, DDL/MDL, capital markets, charts, earnings,
    analyst data, and Phase 133 intelligence displays.

    All fields optional with defaults. extra='allow' for migration safety.
    """

    model_config = ConfigDict(extra="allow")

    # Price basics
    current_price: str | None = None
    high_52w: str | None = None
    low_52w: str | None = None
    pct_off_high: str | None = None

    # Short interest
    short_pct: str | None = None
    days_to_cover: str | None = None

    # Insider trading
    insider_summary: str = ""
    insider_data: dict[str, Any] | None = None

    # Evaluative: volatility
    volatility_signal_level: str | None = None
    volatility_signal_evidence: str | None = None
    volatility_do_context: str = ""
    volatility_90d: str | None = None
    ewma_vol: str | None = None
    vol_regime: str | None = None
    vol_regime_source: str | None = None
    vol_regime_duration: str | None = None

    # Evaluative: short interest signals
    short_signal_level: str | None = None
    short_signal_evidence: str | None = None
    short_do_context: str = ""
    short_trend_signal: str | None = None
    shares_short: str | None = None
    shares_short_prior: str | None = None
    short_pct_shares_out: str | None = None
    short_trend_6m: str | None = None

    # Evaluative: insider signals
    insider_signal_level: str | None = None
    insider_signal_evidence: str | None = None
    insider_do_context: str = ""
    cluster_timing_do_context: str = ""
    cluster_timing_alert: str | None = None
    notable_insider_activity: str | None = None

    # Evaluative: guidance signals
    guidance_signal_level: str | None = None
    guidance_signal_evidence: str | None = None
    guidance_do_context: str = ""
    earnings_reaction_alert: str | None = None
    revision_pattern_alert: str | None = None
    guidance_alert_count: int | None = None

    # Evaluative: returns / beta
    beta_do_context: str = ""
    returns_do_context: str = ""
    beta_signal_level: str | None = None
    beta_signal_evidence: str | None = None
    returns_signal_level: str | None = None
    returns_signal_evidence: str | None = None
    return_1y: str | None = None
    max_drawdown_1y: str | None = None
    beta: str | None = None

    # Valuation, growth, profitability sub-dicts
    valuation: dict[str, str] | None = None
    growth: dict[str, str] | None = None
    profitability: dict[str, str] | None = None

    # Earnings guidance
    earnings_guidance: dict[str, Any] | None = None

    # Analyst
    analyst_consensus: str | None = None
    analyst_upgrades: str | None = None
    analyst_downgrades: str | None = None

    # Stock drops
    worst_drop_pct: str | None = None
    worst_drop_date: str | None = None
    worst_drop_trigger: str | None = None
    drop_events: list[dict[str, Any]] | None = None
    drop_events_overflow: list[dict[str, Any]] = Field(default_factory=list)

    # DDL / MDL exposure
    ddl_exposure: str | None = None
    mdl_exposure: str | None = None
    ddl_settlement_estimate: str | None = None

    # Capital markets
    capital_markets: dict[str, Any] | None = None

    # Charts
    main_charts: list[str] = Field(default_factory=list)
    audit_charts: list[str] = Field(default_factory=list)

    # Stock sparkline
    stock_sparkline: str = ""

    # Capital returns (dividends + buybacks)
    capital_returns: dict[str, Any] = Field(default_factory=dict)

    # 8-K events
    eight_k_events: dict[str, Any] = Field(default_factory=dict)

    # Next earnings
    next_earnings: str = ""

    # Additional market data from acquired_data
    earnings_history: list[dict[str, Any]] | None = None
    recommendation_breakdown: dict[str, Any] | None = None
    news_articles: list[dict[str, Any]] | None = None
    upgrades_downgrades: list[dict[str, Any]] | None = None
    forward_estimates: dict[str, Any] | None = None

    # Phase 133: stock intelligence
    eps_revision_trends: dict[str, Any] | None = None
    analyst_targets: dict[str, Any] | None = None
    earnings_trust: dict[str, Any] | None = None
    volume_anomalies: dict[str, Any] | None = None
    correlation_metrics: dict[str, Any] | None = None
