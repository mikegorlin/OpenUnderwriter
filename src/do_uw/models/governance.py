"""Governance data models -- part of EXTRACT stage output.

Captures board composition, compensation flags, and forensic sub-models.
Populated during EXTRACT stage from proxy statements (DEF 14A) and 10-K
disclosures.

Phase 3 aggregate fields (board, compensation) remain primary because they
hold aggregate board/comp metrics not duplicated by Phase 4 models.

Phase 4 forensic sub-models (from governance_forensics.py) are the primary
data path for all new code.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    GovernanceQualityScore,
    LeadershipStability,
    NarrativeCoherence,
    OwnershipAnalysis,
    SentimentProfile,
)


class BoardProfile(BaseModel):
    """Board of directors composition and quality.

    Used for F9 (Governance) scoring factor and PROXY_ADVISOR_RISK
    pattern detection.
    """

    model_config = ConfigDict(frozen=False)

    size: SourcedValue[int] | None = Field(
        default=None, description="Total number of board members"
    )
    independence_ratio: SourcedValue[float] | None = Field(
        default=None,
        description="Percentage of independent directors (0-1)",
    )
    avg_tenure_years: SourcedValue[float] | None = Field(
        default=None, description="Average director tenure in years"
    )
    ceo_chair_duality: SourcedValue[bool] | None = Field(
        default=None, description="CEO also serves as board chair"
    )
    overboarded_count: SourcedValue[int] | None = Field(
        default=None,
        description="Directors serving on 4+ public boards",
    )
    dual_class_structure: SourcedValue[bool] | None = Field(
        default=None, description="Company has dual-class share structure"
    )
    classified_board: SourcedValue[bool] | None = Field(
        default=None, description="Board has staggered election terms"
    )

    # Diversity (populated from DEF14AExtraction)
    board_gender_diversity_pct: SourcedValue[float] | None = None
    board_racial_diversity_pct: SourcedValue[float] | None = None

    # Meeting attendance (populated from DEF14AExtraction)
    board_meetings_held: SourcedValue[int] | None = None
    board_attendance_pct: SourcedValue[float] | None = None
    directors_below_75_pct_attendance: SourcedValue[int] | None = None

    # ISS governance risk scores (populated from yfinance, scale 1-10)
    iss_audit_risk: SourcedValue[int] | None = None
    iss_board_risk: SourcedValue[int] | None = None
    iss_compensation_risk: SourcedValue[int] | None = None
    iss_shareholder_rights_risk: SourcedValue[int] | None = None
    iss_overall_risk: SourcedValue[int] | None = None

    # Anti-takeover provisions (populated from DEF14AExtraction)
    poison_pill: SourcedValue[bool] | None = None
    supermajority_voting: SourcedValue[bool] | None = None
    blank_check_preferred: SourcedValue[bool] | None = None
    forum_selection_clause: SourcedValue[str] | None = None
    exclusive_forum_provision: SourcedValue[bool] | None = None
    shareholder_proposal_count: SourcedValue[int] | None = None

    # Additional governance provisions (populated from DEF14AExtraction)
    proxy_access_threshold: SourcedValue[str] | None = None
    special_meeting_threshold: SourcedValue[str] | None = None
    written_consent_allowed: SourcedValue[bool] | None = None
    cumulative_voting: SourcedValue[bool] | None = None
    bylaw_amendment_provisions: SourcedValue[str] | None = None
    ceo_succession_plan: SourcedValue[bool] | None = None
    hedging_prohibition: SourcedValue[bool] | None = None
    pledging_prohibition: SourcedValue[bool] | None = None


class CompensationFlags(BaseModel):
    """Compensation-related governance concerns.

    Flagged items indicate potential Caremark or waste claims.
    """

    model_config = ConfigDict(frozen=False)

    say_on_pay_support_pct: SourcedValue[float] | None = Field(
        default=None, description="Most recent say-on-pay vote support %"
    )
    ceo_pay_ratio: SourcedValue[float] | None = Field(
        default=None, description="CEO pay ratio from proxy"
    )
    excessive_perquisites: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Flagged perquisites above peer norms",
    )
    golden_parachute_value: SourcedValue[float] | None = Field(
        default=None,
        description="Total change-in-control payments from proxy",
    )


class GovernanceData(BaseModel):
    """Aggregated governance data from EXTRACT stage.

    Groups all governance sub-models under one namespace for clean
    state access via state.extracted.governance.
    """

    model_config = ConfigDict(frozen=False)

    # -- Phase 3 aggregate fields (remain primary, not duplicated) ----------
    board: BoardProfile = Field(default_factory=BoardProfile)
    compensation: CompensationFlags = Field(default_factory=CompensationFlags)

    # Phase 4 forensic sub-models (SECT5)
    leadership: LeadershipStability = Field(
        default_factory=LeadershipStability,
        description="SECT5-01/02/06: C-suite forensic profiles and stability",
    )
    board_forensics: list[BoardForensicProfile] = Field(
        default_factory=lambda: [],
        description="SECT5-03: Individual board member forensic profiles",
    )
    comp_analysis: CompensationAnalysis = Field(
        default_factory=CompensationAnalysis,
        description="SECT5-05: Executive compensation risk analysis",
    )
    ownership: OwnershipAnalysis = Field(
        default_factory=OwnershipAnalysis,
        description="SECT5-08: Ownership structure and activist risk",
    )
    sentiment: SentimentProfile = Field(
        default_factory=SentimentProfile,
        description="SECT5-04/09: Multi-source sentiment analysis",
    )
    narrative_coherence: NarrativeCoherence = Field(
        default_factory=NarrativeCoherence,
        description="SECT5-10: Cross-source narrative coherence",
    )
    governance_score: GovernanceQualityScore = Field(
        default_factory=GovernanceQualityScore,
        description="SECT5-07: Composite governance quality score",
    )
    governance_summary: SourcedValue[str] | None = Field(
        default=None,
        description="SECT5-01: Overall governance narrative summary",
    )
    ecd: dict[str, object] = Field(
        default_factory=dict,
        description=(
            "ECD inline XBRL data from DEF 14A — Pay-vs-Performance, "
            "insider trading policy, award timing flags (HIGH confidence)"
        ),
    )
