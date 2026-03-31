"""Governance forensic sub-models for SECT5 extraction output.

Provides typed Pydantic models for:
- Leadership forensic profiles (SECT5-02/06)
- Board forensic analysis (SECT5-03)
- Compensation risk analysis (SECT5-05)
- Ownership/activist risk (SECT5-08)
- Sentiment profile (SECT5-04/09)
- Narrative coherence (SECT5-10)
- Governance quality scoring (SECT5-07)

All models use SourcedValue[T] for provenance tracking per CLAUDE.md.
Split from governance.py to stay under 500-line limit.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue

# ---------------------------------------------------------------------------
# SECT5-02/06: Leadership Forensic Profile
# ---------------------------------------------------------------------------


class LeadershipForensicProfile(BaseModel):
    """Individual executive forensic profile.

    Combines DEF 14A bio, prior litigation history (Stanford SCAC),
    SEC enforcement background, and departure analysis (8-K).
    Used for SECT5-02 (executive profiles) and SECT5-06 (stability).
    """

    model_config = ConfigDict(frozen=False)

    name: SourcedValue[str] | None = Field(
        default=None, description="Full name from proxy statement"
    )
    title: SourcedValue[str] | None = Field(
        default=None, description="Current title/role"
    )
    tenure_start: SourcedValue[str] | None = Field(
        default=None, description="Date appointed to current role (ISO format)"
    )
    tenure_years: float | None = Field(
        default=None, description="Calculated tenure in years"
    )
    is_interim: SourcedValue[bool] | None = Field(
        default=None, description="Whether serving in interim capacity"
    )
    bio_summary: SourcedValue[str] | None = Field(
        default=None, description="Biography summary from DEF 14A"
    )
    prior_litigation: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Stanford SCAC hits at prior companies",
    )
    prior_enforcement: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="SEC enforcement actions at prior companies",
    )
    prior_restatements: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Restatements at prior companies",
    )
    shade_factors: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Credential issues, legal issues, pledged shares",
    )
    departure_type: str = Field(
        default="",
        description="PLANNED, UNPLANNED, or ACTIVE (currently serving)",
    )
    departure_date: str | None = Field(
        default=None, description="Departure date (ISO format) if applicable"
    )
    departure_context: SourcedValue[str] | None = Field(
        default=None, description="8-K language and timing analysis"
    )


# ---------------------------------------------------------------------------
# SECT5-06: Leadership Stability
# ---------------------------------------------------------------------------


class LeadershipStability(BaseModel):
    """C-suite turnover and stability assessment.

    Aggregates executive forensic profiles and identifies turnover
    patterns that signal organizational stress (SECT5-06).
    """

    model_config = ConfigDict(frozen=False)

    executives: list[LeadershipForensicProfile] = Field(
        default_factory=lambda: [],
        description="Current C-suite forensic profiles",
    )
    departures_18mo: list[LeadershipForensicProfile] = Field(
        default_factory=lambda: [],
        description="Executive departures in last 18 months",
    )
    avg_tenure_years: SourcedValue[float] | None = Field(
        default=None, description="Average C-suite tenure in years"
    )
    longest_tenured: SourcedValue[str] | None = Field(
        default=None, description="Name of longest-tenured executive"
    )
    shortest_tenured: SourcedValue[str] | None = Field(
        default=None, description="Name of shortest-tenured executive"
    )
    red_flags: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Stability red flags (mass departures, interim officers)",
    )
    stability_score: SourcedValue[float] | None = Field(
        default=None, description="0-100 normalized stability score"
    )
    stability_peer_percentile: SourcedValue[float] | None = Field(
        default=None, description="Percentile vs sector peers"
    )


# ---------------------------------------------------------------------------
# SECT5-03: Board Forensic Profile
# ---------------------------------------------------------------------------


class BoardForensicProfile(BaseModel):
    """Individual board member forensic profile.

    Evaluates true independence, overboarding, interlocks, and
    prior litigation history for each director (SECT5-03).
    """

    model_config = ConfigDict(frozen=False)

    name: SourcedValue[str] | None = Field(
        default=None, description="Full name from proxy statement"
    )
    tenure_years: SourcedValue[float] | None = Field(
        default=None, description="Years on this board"
    )
    is_independent: SourcedValue[bool] | None = Field(
        default=None, description="Independent per proxy disclosure"
    )
    committees: list[str] = Field(
        default_factory=lambda: [],
        description="Committee memberships (Audit, Comp, Nom/Gov)",
    )
    other_boards: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Other public board seats",
    )
    is_overboarded: bool = Field(
        default=False, description="Serves on 4+ total public boards"
    )
    prior_litigation: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Prior securities litigation involvement",
    )
    interlocks: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Interlocking directorates with other company officers",
    )
    relationship_flags: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Family, financial, or professional ties to management",
    )
    true_independence_concerns: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Factors undermining nominal independence",
    )
    qualifications: SourcedValue[str] | None = Field(
        default=None,
        description="Director qualifications and experience from proxy bio",
    )
    qualification_tags: list[str] = Field(
        default_factory=lambda: [],
        description=(
            "Structured qualification tags: industry_expertise, "
            "financial_expert, legal_regulatory, technology, "
            "public_company_experience, prior_c_suite"
        ),
    )
    age: SourcedValue[int] | None = Field(
        default=None, description="Director age from proxy statement"
    )


# ---------------------------------------------------------------------------
# SECT5-05: Compensation Analysis
# ---------------------------------------------------------------------------


class CompensationAnalysis(BaseModel):
    """Executive compensation risk analysis.

    CEO pay breakdown, peer comparison, say-on-pay trends, clawback
    provisions, and related-party transactions (SECT5-05).
    """

    model_config = ConfigDict(frozen=False)

    ceo_total_comp: SourcedValue[float] | None = Field(
        default=None, description="Total CEO compensation from proxy SCT"
    )
    ceo_salary: SourcedValue[float] | None = Field(
        default=None, description="CEO base salary"
    )
    ceo_bonus: SourcedValue[float] | None = Field(
        default=None, description="CEO annual cash bonus/incentive"
    )
    ceo_equity: SourcedValue[float] | None = Field(
        default=None, description="CEO equity awards (options + RSU)"
    )
    ceo_other: SourcedValue[float] | None = Field(
        default=None, description="CEO other compensation"
    )
    ceo_pay_ratio: SourcedValue[float] | None = Field(
        default=None, description="CEO-to-median-worker pay ratio"
    )
    ceo_pay_vs_peer_median: SourcedValue[float] | None = Field(
        default=None,
        description="Ratio of CEO pay to peer group median (>1 = above median)",
    )
    comp_mix: dict[str, float] = Field(
        default_factory=dict,
        description="Compensation percentage breakdown by category",
    )
    performance_metrics: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Incentive plan performance metrics tied to pay",
    )
    say_on_pay_pct: SourcedValue[float] | None = Field(
        default=None, description="Most recent say-on-pay vote support %"
    )
    say_on_pay_trend: SourcedValue[str] | None = Field(
        default=None,
        description="Say-on-pay trend: IMPROVING, STABLE, or DECLINING",
    )
    has_clawback: SourcedValue[bool] | None = Field(
        default=None, description="Whether company has clawback policy"
    )
    clawback_scope: SourcedValue[str] | None = Field(
        default=None,
        description="Clawback scope: DODD_FRANK_MINIMUM or BROADER",
    )
    related_party_transactions: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Related-party transactions from proxy",
    )
    notable_perquisites: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Executive perquisites above peer norms",
    )


# ---------------------------------------------------------------------------
# SECT5-08: Ownership Analysis
# ---------------------------------------------------------------------------


class OwnershipAnalysis(BaseModel):
    """Ownership structure and activist risk assessment.

    Institutional/insider ownership, 13D/13G filings, proxy contests,
    and dual-class structure analysis (SECT5-08).
    """

    model_config = ConfigDict(frozen=False)

    institutional_pct: SourcedValue[float] | None = Field(
        default=None, description="Institutional ownership percentage"
    )
    insider_pct: SourcedValue[float] | None = Field(
        default=None, description="Insider ownership percentage"
    )
    top_holders: list[SourcedValue[dict[str, Any]]] = Field(
        default_factory=lambda: [],
        description="Top institutional holders with position sizes",
    )
    known_activists: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Known activist investors holding positions",
    )
    has_dual_class: SourcedValue[bool] | None = Field(
        default=None, description="Whether company has dual-class shares"
    )
    dual_class_control_pct: SourcedValue[float] | None = Field(
        default=None, description="Voting control percentage of superior class"
    )
    dual_class_economic_pct: SourcedValue[float] | None = Field(
        default=None,
        description="Economic ownership percentage of superior class",
    )
    filings_13d_24mo: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="Schedule 13D filings in last 24 months",
    )
    conversions_13g_to_13d: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="Conversions from passive 13G to activist 13D",
    )
    proxy_contests_3yr: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Proxy contests in last 3 years",
    )
    activist_risk_assessment: SourcedValue[str] | None = Field(
        default=None,
        description="Activist risk level: LOW, MEDIUM, or HIGH",
    )


# ---------------------------------------------------------------------------
# SECT5-04/09: Sentiment Profile
# ---------------------------------------------------------------------------


class SentimentProfile(BaseModel):
    """Multi-source sentiment analysis.

    Combines Loughran-McDonald dictionary analysis of earnings calls
    (SECT5-04), broader sentiment signals (SECT5-09), and Q&A
    evasion metrics from earnings call transcripts.
    """

    model_config = ConfigDict(frozen=False)

    management_tone_trajectory: SourcedValue[str] | None = Field(
        default=None,
        description="Tone trajectory: IMPROVING, STABLE, or DETERIORATING",
    )
    hedging_language_trend: SourcedValue[str] | None = Field(
        default=None,
        description="Hedging language trend: INCREASING, STABLE, or DECLINING",
    )
    ceo_cfo_divergence: SourcedValue[str] | None = Field(
        default=None,
        description="CEO vs CFO tone alignment: ALIGNED or DIVERGENT",
    )
    qa_evasion_score: SourcedValue[float] | None = Field(
        default=None, description="Q&A evasion score (0-1, higher = evasive)"
    )
    specificity_trend: SourcedValue[str] | None = Field(
        default=None,
        description="Specificity trend: INCREASING, STABLE, or DECLINING",
    )
    lm_negative_trend: list[SourcedValue[float]] = Field(
        default_factory=lambda: [],
        description="Loughran-McDonald negative word counts per period",
    )
    lm_uncertainty_trend: list[SourcedValue[float]] = Field(
        default_factory=lambda: [],
        description="Loughran-McDonald uncertainty word counts per period",
    )
    lm_litigious_trend: list[SourcedValue[float]] = Field(
        default_factory=lambda: [],
        description="Loughran-McDonald litigious word counts per period",
    )
    glassdoor_rating: SourcedValue[float] | None = Field(
        default=None, description="Glassdoor overall company rating"
    )
    glassdoor_ceo_approval: SourcedValue[float] | None = Field(
        default=None, description="Glassdoor CEO approval percentage"
    )
    employee_sentiment: SourcedValue[str] | None = Field(
        default=None,
        description="Employee sentiment: POSITIVE, NEUTRAL, or NEGATIVE",
    )
    news_sentiment: SourcedValue[str] | None = Field(
        default=None,
        description="News sentiment: POSITIVE, NEUTRAL, or NEGATIVE",
    )
    social_media_sentiment: SourcedValue[str] | None = Field(
        default=None,
        description="Social media sentiment: POSITIVE, NEUTRAL, or NEGATIVE",
    )


# ---------------------------------------------------------------------------
# SECT5-10: Narrative Coherence
# ---------------------------------------------------------------------------


class NarrativeCoherence(BaseModel):
    """Cross-source narrative coherence assessment.

    Identifies gaps between management narrative and observable data:
    strategy vs results, insider behavior vs stated confidence,
    earnings call tone vs financial trajectory, and employee sentiment
    vs management messaging (SECT5-10).
    """

    model_config = ConfigDict(frozen=False)

    strategy_vs_results: SourcedValue[str] | None = Field(
        default=None,
        description="Strategy-results alignment: ALIGNED or MISALIGNED",
    )
    insider_vs_confidence: SourcedValue[str] | None = Field(
        default=None,
        description="Insider behavior vs stated confidence alignment",
    )
    tone_vs_financials: SourcedValue[str] | None = Field(
        default=None,
        description="Earnings call tone vs financial trajectory alignment",
    )
    employee_vs_management: SourcedValue[str] | None = Field(
        default=None,
        description="Employee sentiment vs management messaging alignment",
    )
    coherence_flags: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Specific narrative coherence gaps identified",
    )
    overall_assessment: SourcedValue[str] | None = Field(
        default=None,
        description="Overall: COHERENT, MINOR_GAPS, or SIGNIFICANT_GAPS",
    )


# ---------------------------------------------------------------------------
# SECT5-07: Governance Quality Score
# ---------------------------------------------------------------------------


class GovernanceQualityScore(BaseModel):
    """Composite governance quality scoring.

    Component scores for board independence, CEO-chair duality,
    board refreshment, overboarding, committee composition,
    say-on-pay results, and tenure balance (SECT5-07).
    """

    model_config = ConfigDict(frozen=False)

    independence_score: float = Field(
        default=0.0, description="Board independence component score"
    )
    ceo_chair_score: float = Field(
        default=0.0,
        description="CEO-chair separation component score",
    )
    refreshment_score: float = Field(
        default=0.0, description="Board refreshment component score"
    )
    overboarding_score: float = Field(
        default=0.0, description="Overboarding risk component score"
    )
    committee_score: float = Field(
        default=0.0,
        description="Committee composition component score",
    )
    say_on_pay_score: float = Field(
        default=0.0, description="Say-on-pay results component score"
    )
    tenure_score: float = Field(
        default=0.0, description="Board tenure balance component score"
    )
    total_score: SourcedValue[float] | None = Field(
        default=None, description="0-100 normalized total governance score"
    )
    peer_percentile: SourcedValue[float] | None = Field(
        default=None, description="Percentile vs sector peers"
    )
