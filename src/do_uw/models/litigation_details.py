"""Litigation detail sub-models for SECT6 extraction output.

Provides typed Pydantic models for:
- Regulatory proceedings (SECT6-02)
- Deal litigation (SECT6-03)
- Workforce/product/environmental matters (SECT6-04)
- Forum provisions and defense assessment (SECT6-05)
- Industry claim patterns (SECT6-06)
- Statute of limitations windows (SECT6-07)
- Contingent liabilities (SECT6-08)
- Whistleblower indicators (SECT6-09)
- Litigation timeline events (SECT6-10)

All models use SourcedValue[T] for provenance tracking per CLAUDE.md.
Split from litigation.py to stay under 500-line limit.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue

# ---------------------------------------------------------------------------
# SECT6-02: Regulatory Proceedings
# ---------------------------------------------------------------------------


class RegulatoryProceeding(BaseModel):
    """Non-SEC regulatory action record.

    Captures DOJ, FTC, EPA, CFPB, state AG, and other regulatory
    proceedings that may trigger D&O coverage or signal entity risk.
    """

    model_config = ConfigDict(frozen=False)

    agency: SourcedValue[str] | None = Field(
        default=None,
        description="Regulatory agency (DOJ, FTC, EPA, CFPB, state AG, etc.)",
    )
    proceeding_type: SourcedValue[str] | None = Field(
        default=None,
        description="Type: investigation, enforcement, penalty",
    )
    description: SourcedValue[str] | None = Field(
        default=None, description="Description of the proceeding"
    )
    status: SourcedValue[str] | None = Field(
        default=None,
        description="Status: active, resolved, settled",
    )
    date_initiated: SourcedValue[date] | None = Field(
        default=None, description="Date the proceeding was initiated"
    )
    penalties: SourcedValue[float] | None = Field(
        default=None, description="Penalties or fines in USD"
    )
    do_implications: SourcedValue[str] | None = Field(
        default=None,
        description="D&O insurance implications of the proceeding",
    )
    coverage_type: SourcedValue[str] | None = Field(
        default=None,
        description="D&O coverage type (CoverageType enum value)",
    )


# ---------------------------------------------------------------------------
# SECT6-03: Deal Litigation
# ---------------------------------------------------------------------------


class DealLitigation(BaseModel):
    """M&A/deal-related litigation record.

    Captures merger objection, appraisal, disclosure-only, Revlon,
    and fiduciary duty claims arising from corporate transactions.
    """

    model_config = ConfigDict(frozen=False)

    deal_name: SourcedValue[str] | None = Field(
        default=None, description="Name or description of the deal"
    )
    litigation_type: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "Type: merger_objection, appraisal, disclosure_only, "
            "revlon, fiduciary"
        ),
    )
    status: SourcedValue[str] | None = Field(
        default=None, description="Case status"
    )
    filing_date: SourcedValue[date] | None = Field(
        default=None, description="Date the complaint was filed"
    )
    court: SourcedValue[str] | None = Field(
        default=None, description="Court where case is pending"
    )
    description: SourcedValue[str] | None = Field(
        default=None, description="Description of the litigation"
    )
    settlement_amount: SourcedValue[float] | None = Field(
        default=None, description="Settlement amount in USD if settled"
    )


# ---------------------------------------------------------------------------
# SECT6-04: Workforce, Product & Environmental
# ---------------------------------------------------------------------------


class WorkforceProductEnvironmental(BaseModel):
    """Workforce, product, and environmental litigation matters.

    Aggregates employment, product liability, environmental, and
    cybersecurity matters that may trigger entity-level D&O coverage.
    """

    model_config = ConfigDict(frozen=False)

    employment_matters: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="General employment litigation matters",
    )
    eeoc_charges: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="EEOC discrimination charges",
    )
    whistleblower_complaints: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Whistleblower-related complaints",
    )
    warn_notices: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="WARN Act notices (mass layoff/plant closure)",
    )
    product_recalls: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Product recall events",
    )
    mass_tort_exposure: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Mass tort exposure (asbestos, opioid, etc.)",
    )
    environmental_actions: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Environmental regulatory actions (CERCLA, Clean Air/Water)",
    )
    cybersecurity_incidents: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Cybersecurity breach or data privacy incidents",
    )


# ---------------------------------------------------------------------------
# SECT6-05: Forum Provisions & Defense Assessment
# ---------------------------------------------------------------------------


class ForumProvisions(BaseModel):
    """Charter/bylaw forum selection provisions.

    Federal Forum Provision (FFP) and Exclusive Forum Provision (EFP)
    can significantly affect securities litigation outcomes by
    controlling venue selection.
    """

    model_config = ConfigDict(frozen=False)

    has_federal_forum: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether charter/bylaws include federal forum provision",
    )
    federal_forum_details: SourcedValue[str] | None = Field(
        default=None, description="Details of federal forum provision"
    )
    has_exclusive_forum: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether charter/bylaws include exclusive forum provision",
    )
    exclusive_forum_details: SourcedValue[str] | None = Field(
        default=None, description="Details of exclusive forum provision"
    )
    source_document: SourcedValue[str] | None = Field(
        default=None,
        description="Source document (charter, bylaws, proxy)",
    )


class DefenseAssessment(BaseModel):
    """Overall litigation defense quality assessment.

    Evaluates forum provisions, PSLRA safe harbor usage, judicial
    track record, and prior dismissal success to gauge defense
    strength for underwriting purposes.
    """

    model_config = ConfigDict(frozen=False)

    forum_provisions: ForumProvisions = Field(
        default_factory=ForumProvisions,
        description="Charter/bylaw forum selection provisions",
    )
    pslra_safe_harbor_usage: SourcedValue[str] | None = Field(
        default=None,
        description="PSLRA safe harbor usage: STRONG, MODERATE, WEAK, NONE",
    )
    truth_on_market_viability: SourcedValue[str] | None = Field(
        default=None,
        description="Viability of truth-on-the-market defense",
    )
    judge_track_record: SourcedValue[str] | None = Field(
        default=None,
        description="Assigned judge track record for D&O cases",
    )
    prior_dismissal_success: SourcedValue[str] | None = Field(
        default=None,
        description="Prior success in obtaining dismissals",
    )
    overall_defense_strength: SourcedValue[str] | None = Field(
        default=None,
        description="Overall defense strength: STRONG, MODERATE, WEAK",
    )
    defense_narrative: SourcedValue[str] | None = Field(
        default=None,
        description="Narrative summary of defense posture",
    )


# ---------------------------------------------------------------------------
# SECT6-06: Industry Claim Patterns
# ---------------------------------------------------------------------------


class IndustryClaimPattern(BaseModel):
    """Industry-specific claim pattern record.

    Maps SIC-range industries to common legal theories and tracks
    whether this company is exposed to peer-observed claim patterns
    (contagion risk).
    """

    model_config = ConfigDict(frozen=False)

    legal_theory: SourcedValue[str] | None = Field(
        default=None,
        description="Legal theory (LegalTheory enum value)",
    )
    description: SourcedValue[str] | None = Field(
        default=None, description="Description of the claim pattern"
    )
    peer_examples: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Peer companies with similar claims",
    )
    sic_range: SourcedValue[str] | None = Field(
        default=None, description="SIC code range for this pattern"
    )
    this_company_exposed: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether this company is exposed to this pattern",
    )
    exposure_rationale: SourcedValue[str] | None = Field(
        default=None,
        description="Rationale for exposure determination",
    )
    contagion_risk: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether peer claims create contagion risk",
    )


# ---------------------------------------------------------------------------
# SECT6-07: Statute of Limitations Windows
# ---------------------------------------------------------------------------


class SOLWindow(BaseModel):
    """Statute of limitations and repose window for a claim type.

    Calculates SOL and repose expiry dates from a trigger event
    and determines whether the filing window remains open.
    """

    model_config = ConfigDict(frozen=False)

    claim_type: str = Field(description="Claim type ID from claim_types.json")
    trigger_date: date | None = Field(
        default=None, description="Date of the triggering event"
    )
    trigger_description: SourcedValue[str] | None = Field(
        default=None, description="Description of the triggering event"
    )
    sol_years: int = Field(
        description="Statute of limitations period in years"
    )
    repose_years: int = Field(
        description="Statute of repose period in years"
    )
    sol_expiry: date | None = Field(
        default=None, description="SOL expiry date (trigger + sol_years)"
    )
    repose_expiry: date | None = Field(
        default=None, description="Repose expiry date (trigger + repose_years)"
    )
    sol_open: bool = Field(
        default=True, description="Whether SOL window is still open"
    )
    repose_open: bool = Field(
        default=True, description="Whether repose window is still open"
    )
    window_open: bool = Field(
        default=True, description="Whether any filing window remains open"
    )


# ---------------------------------------------------------------------------
# SECT6-08: Contingent Liabilities
# ---------------------------------------------------------------------------


class ContingentLiability(BaseModel):
    """ASC 450 contingent liability from financial statement notes.

    Tracks loss contingency classification (probable, reasonably
    possible, remote), accrued amounts, and disclosed ranges.
    """

    model_config = ConfigDict(frozen=False)

    description: SourcedValue[str] | None = Field(
        default=None, description="Description of the contingency"
    )
    contingency_type: SourcedValue[str] | None = Field(
        default=None,
        description="Type: litigation, regulatory, warranty, tax, environmental, other",
    )
    asc_450_classification: SourcedValue[str] | None = Field(
        default=None,
        description="ASC 450 classification: probable, reasonably_possible, remote",
    )
    accrued_amount: SourcedValue[float] | None = Field(
        default=None,
        description="Amount accrued for this contingency in USD",
    )
    range_low: SourcedValue[float] | None = Field(
        default=None,
        description="Low end of disclosed range of possible loss",
    )
    range_high: SourcedValue[float] | None = Field(
        default=None,
        description="High end of disclosed range of possible loss",
    )
    source_note: SourcedValue[str] | None = Field(
        default=None,
        description="Financial statement note reference",
    )


# ---------------------------------------------------------------------------
# SECT6-09: Whistleblower Indicators
# ---------------------------------------------------------------------------


class WhistleblowerIndicator(BaseModel):
    """Whistleblower-related risk indicator.

    Tracks SEC whistleblower, qui tam (False Claims Act), and
    internal whistleblower signals that may precede enforcement
    actions or litigation.
    """

    model_config = ConfigDict(frozen=False)

    indicator_type: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "Type: sec_whistleblower, qui_tam, false_claims, internal"
        ),
    )
    description: SourcedValue[str] | None = Field(
        default=None, description="Description of the indicator"
    )
    date_identified: SourcedValue[date] | None = Field(
        default=None, description="Date the indicator was identified"
    )
    significance: SourcedValue[str] | None = Field(
        default=None,
        description="Significance level: HIGH, MEDIUM, LOW",
    )
    source: SourcedValue[str] | None = Field(
        default=None, description="Source of the indicator"
    )


# ---------------------------------------------------------------------------
# SECT6-10: Litigation Timeline Events
# ---------------------------------------------------------------------------


class LitigationTimelineEvent(BaseModel):
    """Event in the litigation/regulatory timeline.

    Provides a unified chronological view of case filings,
    settlements, enforcement actions, regulatory events, stock
    drops, and executive changes for timeline overlay analysis.
    """

    model_config = ConfigDict(frozen=False)

    event_date: date | None = Field(
        default=None, description="Date of the event"
    )
    event_type: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "Type: case_filing, settlement, enforcement_action, "
            "regulatory, stock_drop, executive_change"
        ),
    )
    description: SourcedValue[str] | None = Field(
        default=None, description="Description of the event"
    )
    severity: SourcedValue[str] | None = Field(
        default=None,
        description="Severity: HIGH, MEDIUM, LOW",
    )
    related_case: SourcedValue[str] | None = Field(
        default=None,
        description="Related case name or identifier",
    )
