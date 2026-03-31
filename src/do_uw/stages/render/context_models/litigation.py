"""Typed context model for litigation section.

Matches the dict returned by extract_litigation() in
context_builders/litigation.py plus evaluative helpers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LitigationDashboard(BaseModel):
    """Litigation dashboard summary metrics."""

    model_config = ConfigDict(extra="allow")

    total_matters: int = 0
    active_count: int = 0
    historical_count: int = 0
    derivative_count: int = 0
    regulatory_count: int = 0
    contingent_count: int = 0
    open_sol_windows: int = 0
    total_sol_windows: int = 0
    litigation_reserve: str = "N/A"
    sec_stage: str = "NONE"
    defense_strength: str = "N/A"


class SecEnforcement(BaseModel):
    """SEC enforcement pipeline summary."""

    model_config = ConfigDict(extra="allow")

    highest_stage: str = "NONE"
    wells_notice: str = "No"
    comment_letters: str = "0"
    investigation: str = "No"


class SolAnalysis(BaseModel):
    """Statute of limitations analysis summary."""

    model_config = ConfigDict(extra="allow")

    window_status: str = ""
    earliest_open: str = "N/A"
    repose_deadline: str = "N/A"


class LitigationContext(BaseModel):
    """Typed context for the litigation landscape section.

    Covers case summaries, SCA cases, SOL windows, SEC enforcement,
    derivative suits, regulatory proceedings, defense assessment,
    deal litigation, timeline events, and evaluative signal flags.

    All fields optional with defaults. extra='allow' for migration safety.
    """

    model_config = ConfigDict(extra="allow")

    # Summary
    active_summary: str = ""
    historical_summary: str = ""

    # Cases
    cases: list[dict[str, Any]] = Field(default_factory=list)
    historical_cases: list[dict[str, Any]] = Field(default_factory=list)
    active_matters: list[dict[str, Any]] = Field(default_factory=list)

    # SOL
    sol_windows: list[dict[str, Any]] = Field(default_factory=list)
    open_sol_count: int = 0
    sol_analysis: SolAnalysis | None = None

    # SEC
    sec_enforcement_stage: str = "NONE"
    comment_letters: str = "0"
    sec_enforcement: SecEnforcement | None = None
    comment_letter_topics: list[str] = Field(default_factory=list)

    # Derivative
    derivative_suits: list[dict[str, Any]] = Field(default_factory=list)
    derivative_count: str = "0"

    # Regulatory
    regulatory_proceedings: list[dict[str, str]] = Field(default_factory=list)

    # Defense
    defense: dict[str, str] = Field(default_factory=dict)
    defense_strength: str = "N/A"

    # Reserve
    litigation_reserve: str = "N/A"

    # Dashboard
    dashboard: LitigationDashboard | None = None

    # Contingent / other
    contingent_liabilities: list[dict[str, str]] = Field(default_factory=list)
    workforce_product_env: dict[str, Any] | list[dict[str, str]] = Field(default_factory=dict)
    whistleblower_indicators: list[dict[str, str]] = Field(default_factory=list)

    # Industry patterns
    industry_patterns: list[str] = Field(default_factory=list)

    # Deal litigation
    deal_litigation: list[dict[str, str]] = Field(default_factory=list)
    ma_activity_notes: list[str] = Field(default_factory=list)

    # Timeline
    timeline_events: list[dict[str, str]] = Field(default_factory=list)

    # Settlements
    settlements: list[dict[str, str]] = Field(default_factory=list)

    # Unclassified reserves
    unclassified_reserves: list[dict[str, str]] = Field(default_factory=list)

    # Risk card (from Supabase get_risk_card RPC)
    risk_card_score: int | None = None
    risk_card_score_components: dict[str, int] = Field(default_factory=dict)
    risk_card_repeat_filer: dict[str, Any] = Field(default_factory=dict)
    risk_card_scenario_benchmarks: list[dict[str, Any]] = Field(default_factory=list)
    risk_card_screening_questions: list[dict[str, Any]] = Field(default_factory=list)
    risk_card_filing_history: list[dict[str, Any]] = Field(default_factory=list)
    risk_card_data_note: str = ""

    # Evaluative signal flags (from litigation_evaluative.py)
    signal_defense_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_sec_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_sol_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_sca_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_other_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_sector_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_all_litigation_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_litigation_critical_count: int = 0
    signal_litigation_warning_count: int = 0
    signal_defense_summary: str = ""
    signal_litigation_risk_level: str = "Low"
    signal_do_context_map: dict[str, str] = Field(default_factory=dict)
    signal_sca_do_context: str = ""
    signal_sec_do_context: str = ""
