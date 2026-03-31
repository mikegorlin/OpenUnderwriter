"""Typed context model for governance section.

Matches the dict returned by extract_governance() in
context_builders/governance.py plus evaluative helpers.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class GovernanceContext(BaseModel):
    """Typed context for the governance & leadership section.

    Covers board metrics, compensation, ownership, leadership, sentiment,
    anti-takeover, bylaws, narrative coherence, board forensics, governance
    score breakdown, tenure distribution, skills matrix, committee detail,
    and evaluative signal flags.

    All fields optional with defaults. extra='allow' for migration safety.
    """

    model_config = ConfigDict(extra="allow")

    # Board basics
    board_size: str | None = None
    independence_ratio: str | None = None
    ceo_duality: str | None = None
    avg_tenure: str = "N/A"
    classified_board: str | None = None
    dual_class: str | None = None
    overboarded_count: str | None = None
    governance_score: str | None = None

    # ISS scores
    iss_scores: dict[str, str] | None = None

    # Board meeting data
    board_meetings_held: str | None = None
    board_attendance_pct: str | None = None
    directors_below_75_pct: int | None = None
    shareholder_proposals: list[dict[str, Any]] = Field(default_factory=list)

    # Compensation
    ceo_comp: str | None = None
    say_on_pay: str | None = None
    ceo_pay_ratio: str | None = None
    has_clawback: str | None = None
    clawback_scope: str | None = None
    golden_parachute: str | None = None

    # Ownership
    institutional_pct: str | None = None
    insider_pct: str | None = None
    top_holders: list[dict[str, str]] = Field(default_factory=list)
    top_holders_overflow: list[dict[str, str]] = Field(default_factory=list)
    known_activists: list[str] = Field(default_factory=list)

    # Activist signals
    filings_13d_24mo: list[dict[str, str]] = Field(default_factory=list)
    conversions_13g_to_13d: list[dict[str, str]] = Field(default_factory=list)
    proxy_contests_3yr: list[str] = Field(default_factory=list)

    # Leadership
    executives: list[dict[str, Any]] = Field(default_factory=list)
    departures_18mo: list[dict[str, str]] = Field(default_factory=list)
    leadership_red_flags: list[str] = Field(default_factory=list)
    stability_score: str | None = None
    leaders: list[dict[str, Any]] | None = None

    # Sentiment
    has_sentiment_data: bool = False
    management_tone: str = ""
    hedging_language: str = ""
    qa_evasion: str = ""

    # Anti-takeover
    anti_takeover: list[dict[str, str]] = Field(default_factory=list)
    anti_takeover_provisions: list[str] | None = None

    # Bylaws
    bylaws_provisions: list[dict[str, str]] = Field(default_factory=list)

    # Related party and perquisites
    related_party_transactions: list[str] = Field(default_factory=list)
    notable_perquisites: list[str] = Field(default_factory=list)

    # Narrative coherence
    narrative_coherence: dict[str, str] | None = None
    coherence_flags: list[str] | None = None

    # Board forensics detail
    board_members: list[dict[str, Any]] = Field(default_factory=list)
    board_has_any_age: bool = False
    board_has_any_other_boards: bool = False
    board_has_any_flags: bool = False
    board_has_any_detail: bool = False

    # Nested summary dicts (HTML template compat)
    board: dict[str, Any] = Field(default_factory=dict)
    compensation: dict[str, str] | None = None
    compensation_analysis: dict[str, Any] = Field(default_factory=dict)

    # Visual display
    score_breakdown: list[dict[str, Any]] | None = None
    tenure_distribution: list[dict[str, Any]] | None = None
    skills_matrix: dict[str, Any] | None = None
    committee_detail: dict[str, Any] | list[dict[str, Any]] | None = None

    # Evaluative signal flags (from governance_evaluative.py)
    signal_board_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_comp_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_structural_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_effectiveness_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_insider_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_exec_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_activist_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_all_governance_flags: list[dict[str, str]] = Field(default_factory=list)
    signal_governance_critical_count: int = 0
    signal_governance_warning_count: int = 0
    signal_board_quality_summary: str = ""
    signal_do_context_map: dict[str, str] = Field(default_factory=dict)

    # Governance intelligence
    officer_backgrounds: list[dict[str, Any]] = Field(default_factory=list)
    has_officer_backgrounds: bool = False
    serial_defendant_count: int = 0
    shareholder_rights: dict[str, Any] = Field(default_factory=dict)
    has_shareholder_rights: bool = False
    per_insider_activity: list[dict[str, Any]] = Field(default_factory=list)
    has_per_insider_activity: bool = False
    insider_count: int = 0
