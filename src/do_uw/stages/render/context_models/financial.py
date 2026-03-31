"""Typed context model for financial section.

Matches the dict returned by extract_financials() in
context_builders/financials.py plus evaluative helpers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FinancialContext(BaseModel):
    """Typed context for the financial section.

    Covers income statement, balance sheet, cash flow, computed metrics,
    evaluative signals (distress, earnings quality, leverage, tax, liquidity),
    audit data, peers, quarterly, forensics, debt structure, and liquidity detail.

    All fields optional with defaults. extra='allow' for migration safety.
    """

    model_config = ConfigDict(extra="allow")

    # Income statement
    has_income: bool = False
    latest_period: str | None = None
    prior_period: str | None = None
    filing_source: str | None = None
    revenue: str | None = None
    net_income: str | None = None
    prior_revenue: str | None = None
    prior_net_income: str | None = None
    revenue_yoy: str = ""
    net_income_yoy: str = ""
    gross_profit: str | None = None
    gross_margin: str | None = None
    operating_income: str | None = None
    operating_margin: str | None = None
    prior_operating_margin: str | None = None
    operating_margin_yoy: str = ""
    diluted_eps: str | None = None
    prior_diluted_eps: str | None = None
    eps_yoy: str = ""
    rd_expense: str | None = None
    sga_expense: str | None = None

    # Balance sheet
    total_assets: str | None = None
    prior_total_assets: str | None = None
    total_assets_yoy: str = ""
    total_equity: str | None = None
    prior_total_equity: str | None = None
    total_equity_yoy: str = ""
    cash: str | None = None
    total_liabilities: str | None = None

    # Cash flow
    operating_cf: str | None = None
    capex: str | None = None
    buybacks: str | None = None
    dividends: str | None = None

    # Sparklines
    revenue_sparkline: str = ""
    net_income_sparkline: str = ""
    total_assets_sparkline: str = ""

    # Computed metrics (from financials_computed.py)
    goodwill_equity_ratio: str | None = None
    goodwill_equity_flag: bool = False
    capital_allocation: dict[str, Any] = Field(default_factory=dict)
    debt_service_coverage: dict[str, Any] | str | None = None
    debt_service_flag: bool = False
    refinancing_risk: dict[str, Any] = Field(default_factory=dict)
    bankruptcy_composite: dict[str, Any] = Field(default_factory=dict)

    # Evaluative: distress signals
    z_score: str | None = None
    z_zone: str | None = None
    z_do_context: str = ""
    z_trajectory: list[dict[str, Any]] | dict[str, Any] = Field(default_factory=list)
    beneish_score: str | None = None
    beneish_zone: str | None = None
    beneish_level: str | None = None
    beneish_do_context: str = ""
    o_score: str | None = None
    o_zone: str | None = None
    o_do_context: str = ""
    piotroski_score: str | None = None
    piotroski_zone: str | None = None
    piotroski_do_context: str = ""
    piotroski_components: list[dict[str, Any]] | dict[str, Any] = Field(default_factory=list)
    forensic_alert_count: int | None = None

    # Evaluative: earnings quality
    earnings_quality: str | None = None
    earnings_quality_detail: dict[str, Any] | str | None = None
    earnings_quality_level: str | None = None

    # Evaluative: leverage
    debt_summary: str | None = None
    leverage_level: str | None = None
    debt_structure_do_context: str = ""
    debt_coverage_do_context: str = ""

    # Evaluative: tax
    tax_etr: str | None = None
    tax_level: str | None = None
    tax_risk: dict[str, Any] | str | None = None
    etr_do_context: str = ""

    # Evaluative: liquidity
    liquidity: str | None = None
    liquidity_level: str | None = None
    liquidity_do_context: str = ""
    cash_burn_do_context: str = ""

    # Audit
    auditor_name: str = "N/A"
    is_big4: str = "No"
    auditor_tenure: str = "N/A"
    material_weaknesses: int = 0
    going_concern: str = "No"
    audit_mw_do_context: str = ""
    audit_restatement_do_context: str = ""
    audit_gc_do_context: str = ""

    # Audit disclosure alerts (from financials_computed.py)
    audit_alerts: list[dict[str, Any]] = Field(default_factory=list)

    # Peers
    peers: list[dict[str, str]] = Field(default_factory=list)

    # Sub-contexts (complex nested structures -- typed as dict for migration)
    quarterly_updates: dict[str, Any] | list[Any] | None = None
    yfinance_quarterly: dict[str, Any] | list[Any] | None = None
    quarterly_trends: dict[str, Any] | None = None
    forensics: dict[str, Any] | None = None
    peer_percentiles: dict[str, Any] | None = None
    debt_structure: dict[str, Any] = Field(default_factory=dict)
    liquidity_detail: dict[str, Any] = Field(default_factory=dict)
    health_narrative: str = ""

    # Statement rows (from financials_balance.py)
    income_rows: list[dict[str, Any]] = Field(default_factory=list)
    balance_rows: list[dict[str, Any]] = Field(default_factory=list)
    cashflow_rows: list[dict[str, Any]] = Field(default_factory=list)
    income_periods: list[str] = Field(default_factory=list)
    balance_periods: list[str] = Field(default_factory=list)
    cashflow_periods: list[str] = Field(default_factory=list)
