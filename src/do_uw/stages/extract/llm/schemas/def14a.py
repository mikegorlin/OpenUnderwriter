"""DEF 14A proxy statement extraction schema.

Comprehensive Pydantic model for extracting ALL D&O-relevant data from
a DEF 14A proxy statement in a single LLM API call. Covers board
composition, executive compensation, governance provisions,
anti-takeover measures, and ownership.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from do_uw.stages.extract.llm.schemas.common import (
    ExtractedCompensation,
    ExtractedDirector,
)


class DEF14AExtraction(BaseModel):
    """Complete extraction schema for DEF 14A proxy statements.

    One model, one API call. All fields optional with defaults.
    Fields organized by proxy statement section for clarity.
    """

    # ------------------------------------------------------------------
    # Board of Directors
    # ------------------------------------------------------------------
    directors: list[ExtractedDirector] = Field(
        default_factory=lambda: [],
        description="All director nominees with biographical information",
    )
    board_size: int | None = Field(
        default=None,
        description="Total number of board members",
    )
    independent_count: int | None = Field(
        default=None,
        description="Number of independent directors",
    )
    classified_board: bool | None = Field(
        default=None,
        description="Whether the board has staggered terms (classified board)",
    )
    annual_election: bool | None = Field(
        default=None,
        description="Whether all directors are elected annually",
    )
    lead_independent_director: str | None = Field(
        default=None,
        description="Name of the lead independent director, if any",
    )
    ceo_chair_combined: bool | None = Field(
        default=None,
        description="Whether the CEO also serves as board chair",
    )
    ceo_name: str | None = Field(
        default=None,
        description="Name of the Chief Executive Officer",
    )
    chair_name: str | None = Field(
        default=None,
        description="Name of the Board Chair",
    )

    # Board diversity (aggregate — not per-director; per-director is in ExtractedDirector)
    board_gender_diversity_pct: float | None = Field(
        default=None,
        description=(
            "Percentage of female/women directors on the board (0-100). "
            "Extract from proxy diversity section or director biography table. "
            "Example: 'Women represent 36% of our board' → 36.0"
        ),
    )
    board_racial_diversity_pct: float | None = Field(
        default=None,
        description=(
            "Percentage of racially/ethnically diverse directors (0-100). "
            "Extract from proxy diversity section if explicitly disclosed. "
            "Set to None if not disclosed."
        ),
    )

    # Board meeting attendance
    board_meetings_held: int | None = Field(
        default=None,
        description="Total number of board of directors meetings held during the fiscal year.",
    )
    board_attendance_pct: float | None = Field(
        default=None,
        description=(
            "Aggregate board meeting attendance percentage (0-100). "
            "Usually disclosed as 'directors attended X% of meetings' or aggregate attendance rate. "
            "Example: '98% of directors attended 75%+ of meetings' is NOT the same as attendance_pct — "
            "look for aggregate attendance like '99.1% average attendance'."
        ),
    )
    directors_below_75_pct_attendance: int | None = Field(
        default=None,
        description="Number of directors who attended less than 75% of board meetings during the year.",
    )

    # ------------------------------------------------------------------
    # Committee Membership
    # ------------------------------------------------------------------
    audit_committee_members: list[str] = Field(
        default_factory=lambda: [],
        description="Names of audit committee members",
    )
    compensation_committee_members: list[str] = Field(
        default_factory=lambda: [],
        description="Names of compensation committee members",
    )
    nominating_committee_members: list[str] = Field(
        default_factory=lambda: [],
        description="Names of nominating/governance committee members",
    )

    # ------------------------------------------------------------------
    # Anti-Takeover Provisions
    # ------------------------------------------------------------------
    poison_pill: bool | None = Field(
        default=None,
        description="Whether a shareholder rights plan (poison pill) is in effect",
    )
    supermajority_voting: bool | None = Field(
        default=None,
        description=(
            "Whether supermajority voting is required for "
            "charter/bylaw amendments or mergers"
        ),
    )
    blank_check_preferred: bool | None = Field(
        default=None,
        description="Whether the board can issue blank check preferred stock",
    )
    forum_selection_clause: str | None = Field(
        default=None,
        description=(
            "Forum selection clause details, e.g. 'Delaware Chancery Court' "
            "or 'Federal district courts for Securities Act claims'"
        ),
    )
    exclusive_forum_provision: bool | None = Field(
        default=None,
        description="Whether an exclusive forum provision exists in the charter",
    )

    # ------------------------------------------------------------------
    # Executive Compensation
    # ------------------------------------------------------------------
    named_executive_officers: list[ExtractedCompensation] = Field(
        default_factory=lambda: [],
        description=(
            "Named executive officers from the Summary Compensation Table "
            "(typically 5 executives)"
        ),
    )
    ceo_pay_ratio: str | None = Field(
        default=None,
        description="CEO pay ratio, e.g. '123:1'",
    )
    golden_parachute_total: float | None = Field(
        default=None,
        description=(
            "Total golden parachute (change-in-control) payments in USD "
            "across all NEOs"
        ),
    )
    has_clawback: bool | None = Field(
        default=None,
        description="Whether the company has a compensation clawback policy",
    )
    clawback_scope: str | None = Field(
        default=None,
        description="Clawback scope: 'DODD_FRANK_MINIMUM' or 'BROADER'",
    )

    # ------------------------------------------------------------------
    # Say-on-Pay
    # ------------------------------------------------------------------
    say_on_pay_approval_pct: float | None = Field(
        default=None,
        description="Most recent say-on-pay advisory vote approval percentage",
    )
    say_on_pay_frequency: str | None = Field(
        default=None,
        description="Say-on-pay frequency: 'annual', 'biennial', 'triennial'",
    )

    # ------------------------------------------------------------------
    # Shareholder Proposals
    # ------------------------------------------------------------------
    shareholder_proposals: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Brief description of each shareholder proposal, "
            "e.g. ['Independent board chair', 'Climate risk report']"
        ),
    )
    shareholder_proposal_count: int | None = Field(
        default=None,
        description="Total number of shareholder proposals",
    )

    # ------------------------------------------------------------------
    # Ownership
    # ------------------------------------------------------------------
    officers_directors_ownership_pct: float | None = Field(
        default=None,
        description=(
            "Aggregate beneficial ownership percentage of all "
            "officers and directors"
        ),
    )
    top_5_holders: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Top 5 beneficial holders with ownership percentage, "
            "e.g. ['Vanguard Group: 8.2%', 'BlackRock: 7.1%']"
        ),
    )

    # ------------------------------------------------------------------
    # Additional Governance Provisions (for GOV.RIGHTS.* signals)
    # ------------------------------------------------------------------
    proxy_access_threshold: str | None = Field(
        default=None,
        description=(
            "Proxy access threshold: percentage of shares and holding period "
            "required for shareholders to nominate directors, e.g. '3% for 3 years'"
        ),
    )
    special_meeting_threshold: str | None = Field(
        default=None,
        description=(
            "Percentage of shares required to call a special meeting, "
            "e.g. '25%' or 'Not permitted'"
        ),
    )
    written_consent_allowed: bool | None = Field(
        default=None,
        description="Whether shareholders can act by written consent without a meeting",
    )
    bylaw_amendment_provisions: str | None = Field(
        default=None,
        description=(
            "Who can amend bylaws and requirements, e.g. 'Board only' "
            "or 'Board or shareholders with simple majority'"
        ),
    )
    ceo_succession_plan: bool | None = Field(
        default=None,
        description="Whether a CEO succession plan is disclosed",
    )
    hedging_prohibition: bool | None = Field(
        default=None,
        description="Whether officers/directors are prohibited from hedging company stock",
    )
    pledging_prohibition: bool | None = Field(
        default=None,
        description="Whether officers/directors are prohibited from pledging company stock",
    )

    # ------------------------------------------------------------------
    # D&O Insurance and Indemnification
    # ------------------------------------------------------------------
    do_coverage_mentioned: bool | None = Field(
        default=None,
        description="Whether D&O insurance coverage is mentioned in the proxy",
    )
    do_indemnification: bool | None = Field(
        default=None,
        description=(
            "Whether indemnification agreements with "
            "directors/officers are disclosed"
        ),
    )
    indemnification_detail: str | None = Field(
        default=None,
        description="Details of indemnification provisions, max 300 chars",
    )

    # ------------------------------------------------------------------
    # Brain-requested fields (dynamic extraction targets)
    # ------------------------------------------------------------------
    brain_fields: dict[str, object] = Field(
        default_factory=dict,
        description=(
            "Additional fields requested by the underwriting brain. "
            "Extract as key-value pairs if found in the document."
        ),
    )
