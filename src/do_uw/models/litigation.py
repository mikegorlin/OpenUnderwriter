"""Litigation data models -- part of EXTRACT stage output.

Captures securities class actions, SEC enforcement pipeline, derivative
suits, regulatory proceedings, deal litigation, defense assessment,
and all SECT6 sub-areas. Populated during EXTRACT stage (Phase 5)
from Stanford SCAC, SEC EDGAR, CourtListener, and web search.

Phase 3 skeleton fields are preserved for backward compatibility.
Phase 5 adds typed sub-models from litigation_details.py.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.common import SourcedValue
from do_uw.models.litigation_details import (
    ContingentLiability,
    DealLitigation,
    DefenseAssessment,
    IndustryClaimPattern,
    LitigationTimelineEvent,
    SOLWindow,
    WhistleblowerIndicator,
    WorkforceProductEnvironmental,
)

# ---------------------------------------------------------------------------
# StrEnum types for litigation classification
# ---------------------------------------------------------------------------


class CoverageType(StrEnum):
    """D&O coverage type classification for claims.

    Maps to how a claim triggers different policy sections
    (Side A = individual, Side B = corporate reimbursement,
    Side C = entity securities, entity = direct entity coverage).
    """

    SCA_SIDE_A = "SCA_SIDE_A"
    SCA_SIDE_B = "SCA_SIDE_B"
    SCA_SIDE_C = "SCA_SIDE_C"
    DERIVATIVE_SIDE_A = "DERIVATIVE_SIDE_A"
    DERIVATIVE_SIDE_B = "DERIVATIVE_SIDE_B"
    SEC_ENFORCEMENT_A = "SEC_ENFORCEMENT_A"
    SEC_ENFORCEMENT_B = "SEC_ENFORCEMENT_B"
    REGULATORY_ENTITY = "REGULATORY_ENTITY"
    EMPLOYMENT_ENTITY = "EMPLOYMENT_ENTITY"
    PRODUCT_ENTITY = "PRODUCT_ENTITY"


class LegalTheory(StrEnum):
    """Legal theory classification for securities and D&O claims."""

    RULE_10B5 = "RULE_10B5"
    SECTION_11 = "SECTION_11"
    SECTION_14A = "SECTION_14A"
    DERIVATIVE_DUTY = "DERIVATIVE_DUTY"
    FCPA = "FCPA"
    ANTITRUST = "ANTITRUST"
    EMPLOYMENT_DISCRIMINATION = "EMPLOYMENT_DISCRIMINATION"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    PRODUCT_LIABILITY = "PRODUCT_LIABILITY"
    CYBER_PRIVACY = "CYBER_PRIVACY"
    ERISA = "ERISA"
    WHISTLEBLOWER = "WHISTLEBLOWER"


class EnforcementStage(StrEnum):
    """SEC enforcement pipeline stage progression.

    Ordered from least to most severe. Each stage represents an
    escalation in regulatory scrutiny.
    """

    NONE = "NONE"
    COMMENT_LETTER = "COMMENT_LETTER"
    INFORMAL_INQUIRY = "INFORMAL_INQUIRY"
    FORMAL_INVESTIGATION = "FORMAL_INVESTIGATION"
    WELLS_NOTICE = "WELLS_NOTICE"
    ENFORCEMENT_ACTION = "ENFORCEMENT_ACTION"


class CaseStatus(StrEnum):
    """Litigation case status."""

    ACTIVE = "ACTIVE"
    SETTLED = "SETTLED"
    DISMISSED = "DISMISSED"
    APPEAL = "APPEAL"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# Case Detail (expanded from Phase 3 skeleton)
# ---------------------------------------------------------------------------


class CaseDetail(BaseModel):
    """Individual litigation case record.

    Used for F1 (Prior Litigation) scoring factor. Each case carries
    full provenance via SourcedValue fields. Phase 5 adds two-layer
    classification (coverage_type + legal_theories) and expanded
    procedural fields.
    """

    model_config = ConfigDict(frozen=False)

    # Phase 3 fields (preserved for backward compatibility)
    case_name: SourcedValue[str] | None = Field(
        default=None,
        description="Case name (e.g. 'In re Acme Corp Securities Lit.')",
    )
    case_number: SourcedValue[str] | None = Field(
        default=None, description="Court case number"
    )
    court: SourcedValue[str] | None = Field(
        default=None, description="Court (e.g. 'S.D.N.Y.')"
    )
    filing_date: SourcedValue[date] | None = Field(
        default=None, description="Date complaint was filed"
    )
    class_period_start: SourcedValue[date] | None = Field(
        default=None, description="Start of alleged class period"
    )
    class_period_end: SourcedValue[date] | None = Field(
        default=None, description="End of alleged class period"
    )
    allegations: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Allegation types: 10b-5, Section 11, Section 12, etc.",
    )
    status: SourcedValue[str] | None = Field(
        default=None,
        description="Case status: ACTIVE, SETTLED, DISMISSED, APPEAL",
    )
    settlement_amount: SourcedValue[float] | None = Field(
        default=None, description="Settlement amount in USD if settled"
    )
    lead_counsel: SourcedValue[str] | None = Field(
        default=None, description="Lead plaintiff counsel firm"
    )
    named_defendants: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Named individual defendants (officers/directors)",
    )

    # Phase 5 expansion: two-layer classification and procedural fields
    coverage_type: SourcedValue[str] | None = Field(
        default=None,
        description="D&O coverage type (CoverageType enum value)",
    )
    legal_theories: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Legal theories (LegalTheory enum values)",
    )
    lead_plaintiff_type: SourcedValue[str] | None = Field(
        default=None,
        description="Lead plaintiff type: institutional, pension, individual",
    )
    lead_counsel_tier: SourcedValue[int] | None = Field(
        default=None,
        description="Lead counsel tier (1, 2, 3 from lead_counsel_tiers.json)",
    )
    class_period_days: int | None = Field(
        default=None, description="Duration of alleged class period in days"
    )
    key_rulings: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Key judicial rulings in the case",
    )
    judge: SourcedValue[str] | None = Field(
        default=None, description="Assigned judge"
    )


# ---------------------------------------------------------------------------
# SEC Enforcement Pipeline (expanded from Phase 3 SECEnforcement)
# ---------------------------------------------------------------------------


class SECEnforcementPipeline(BaseModel):
    """SEC enforcement pipeline profile.

    Tracks position in SEC enforcement pipeline from comment letters
    through formal enforcement actions. Expanded from Phase 3
    SECEnforcement with pipeline stage tracking and comment letter
    analysis. Critical for CRF-01/CRF-02/CRF-03 red flag detection.
    """

    model_config = ConfigDict(frozen=False)

    # Phase 3 fields (preserved for backward compatibility)
    pipeline_position: SourcedValue[str] | None = Field(
        default=None,
        description=(
            "Position in enforcement pipeline: "
            "NONE, INVESTIGATION, WELLS_NOTICE, COMPLAINT, SETTLEMENT"
        ),
    )
    actions: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="SEC actions: type, date, description, release_number",
    )
    aaer_count: SourcedValue[int] | None = Field(
        default=None,
        description="Accounting and Auditing Enforcement Releases count",
    )

    # Phase 5 expansion: pipeline stages and comment letter analysis
    highest_confirmed_stage: SourcedValue[str] | None = Field(
        default=None,
        description="Highest confirmed stage (EnforcementStage enum value)",
    )
    pipeline_signals: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Evidence supporting each pipeline stage determination",
    )
    comment_letter_count: SourcedValue[int] | None = Field(
        default=None, description="Number of SEC comment letters received"
    )
    comment_letter_topics: list[SourcedValue[str]] = Field(
        default_factory=lambda: [],
        description="Topics raised in SEC comment letters",
    )
    industry_sweep_detected: SourcedValue[bool] | None = Field(
        default=None,
        description="Whether SEC industry sweep activity detected",
    )
    enforcement_narrative: SourcedValue[str] | None = Field(
        default=None,
        description="Narrative summary of enforcement posture",
    )


# Backward-compatibility alias for Phase 3 code
SECEnforcement = SECEnforcementPipeline


# ---------------------------------------------------------------------------
# Litigation Landscape (top-level container)
# ---------------------------------------------------------------------------


class LitigationLandscape(BaseModel):
    """Aggregated litigation data from EXTRACT stage.

    Groups all litigation sub-models under one namespace for clean
    state access via state.extracted.litigation. Covers all 12 SECT6
    sub-areas for comprehensive D&O underwriting analysis.
    """

    model_config = ConfigDict(frozen=False)

    # Phase 3 fields (preserved for backward compatibility)
    securities_class_actions: list[CaseDetail] = Field(
        default_factory=lambda: [],
        description="Securities class action lawsuits (10b-5, Section 11)",
    )
    sec_enforcement: SECEnforcementPipeline = Field(
        default_factory=SECEnforcementPipeline,
    )
    derivative_suits: list[CaseDetail] = Field(
        default_factory=lambda: [],
        description="Shareholder derivative lawsuits",
    )
    regulatory_proceedings: list[SourcedValue[dict[str, str]]] = Field(
        default_factory=lambda: [],
        description="Non-SEC regulatory actions: agency, type, date, status",
    )
    defense_assessment: SourcedValue[str] | None = Field(
        default=None,
        description="Overall defense quality: STRONG, MODERATE, WEAK",
    )
    total_litigation_reserve: SourcedValue[float] | None = Field(
        default=None,
        description="Total litigation reserve from financial statements",
    )

    # Phase 5 expansion: SECT6 sub-area models
    deal_litigation: list[DealLitigation] = Field(
        default_factory=lambda: [],
        description="SECT6-03: M&A and deal-related litigation",
    )
    workforce_product_environmental: WorkforceProductEnvironmental = Field(
        default_factory=WorkforceProductEnvironmental,
        description="SECT6-04: Workforce, product, and environmental matters",
    )
    defense: DefenseAssessment = Field(
        default_factory=DefenseAssessment,
        description="SECT6-05: Defense quality assessment",
    )
    industry_patterns: list[IndustryClaimPattern] = Field(
        default_factory=lambda: [],
        description="SECT6-06: Industry-specific claim patterns",
    )
    sol_map: list[SOLWindow] = Field(
        default_factory=lambda: [],
        description="SECT6-07: Statute of limitations window map",
    )
    contingent_liabilities: list[ContingentLiability] = Field(
        default_factory=lambda: [],
        description="SECT6-08: ASC 450 contingent liabilities",
    )
    whistleblower_indicators: list[WhistleblowerIndicator] = Field(
        default_factory=lambda: [],
        description="SECT6-09: Whistleblower risk indicators",
    )
    litigation_summary: SourcedValue[str] | None = Field(
        default=None,
        description="SECT6-01: Overall litigation narrative summary",
    )
    litigation_timeline_events: list[LitigationTimelineEvent] = Field(
        default_factory=lambda: [],
        description="SECT6-10: Chronological litigation timeline",
    )
    active_matter_count: SourcedValue[int] | None = Field(
        default=None,
        description="Count of currently active litigation matters",
    )
    historical_matter_count: SourcedValue[int] | None = Field(
        default=None,
        description="Count of historical (resolved) litigation matters",
    )

    # Phase 140: Unified classifier output fields
    unclassified_reserves: list[CaseDetail] = Field(
        default_factory=lambda: [],
        description="Boilerplate reserves that matched no legal theory (D-07)",
    )
    cases_needing_recovery: list[dict[str, Any]] = Field(
        default_factory=lambda: [],
        description="Cases with missing critical fields queued for ACQUIRE-stage web search recovery (D-06)",
    )
