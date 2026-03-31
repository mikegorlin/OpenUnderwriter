"""Peril mapping models for Phase 27 "who sues" assessment.

Provides:
- PerilProbabilityBand / PerilSeverityBand: Enums for peril assessment
- PlaintiffAssessment: Per-lens plaintiff assessment with probability/severity
- EvidenceItem: Individual evidence item from check results
- BearCase: Constructed litigation narrative with evidence chain
- PlaintiffFirmMatch: Matched plaintiff firm from config tiers
- PerilMap: Root container aggregating all 7-lens assessments
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

# -----------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------


class PerilProbabilityBand(StrEnum):
    """Probability band for peril assessment.

    Separate from scoring_output.ProbabilityBand because peril probability
    uses a different scale (VERY_LOW through HIGH) vs claim probability
    (LOW through VERY_HIGH).
    """

    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"


class PerilSeverityBand(StrEnum):
    """Severity band for peril assessment.

    Maps to expected settlement/loss ranges:
    NUISANCE: < $5M
    MINOR: $5M - $25M
    MODERATE: $25M - $100M
    SIGNIFICANT: $100M - $500M
    SEVERE: > $500M
    """

    NUISANCE = "NUISANCE"
    MINOR = "MINOR"
    MODERATE = "MODERATE"
    SIGNIFICANT = "SIGNIFICANT"
    SEVERE = "SEVERE"


# -----------------------------------------------------------------------
# Assessment Models
# -----------------------------------------------------------------------


class PlaintiffAssessment(BaseModel):
    """Assessment for a single plaintiff lens (1 of 7).

    Shareholders and regulators get FULL modeling depth (probabilistic
    modeling from claim probability + severity scenarios). Other 5 lenses
    get PROPORTIONAL treatment (count-based estimation).
    """

    model_config = ConfigDict(frozen=False)

    plaintiff_type: str = Field(
        description="PlaintiffLens value: SHAREHOLDERS, REGULATORS, etc."
    )
    probability_band: str = Field(
        description="PerilProbabilityBand value"
    )
    severity_band: str = Field(
        description="PerilSeverityBand value"
    )
    triggered_signal_count: int = Field(
        default=0,
        description="Number of checks triggered (risk signal detected)",
    )
    total_signal_count: int = Field(
        default=0,
        description="Total number of checks mapped to this lens",
    )
    evaluated_signal_count: int = Field(
        default=0,
        description="Checks that actually had data (not SKIPPED)",
    )
    key_findings: list[str] = Field(
        default_factory=lambda: [],
        description="Top 3-5 evidence items from triggered checks",
    )
    modeling_depth: str = Field(
        default="PROPORTIONAL",
        description="FULL (shareholders/regulators) or PROPORTIONAL (others)",
    )


class EvidenceItem(BaseModel):
    """Individual evidence item from a check result.

    Links a specific check to the peril assessment with full provenance.
    """

    model_config = ConfigDict(frozen=False)

    signal_id: str = Field(description="Check identifier (e.g., 'FIN.ACCT.restatement')")
    description: str = Field(description="Human-readable description of the finding")
    source: str = Field(description="Data source for this evidence")
    severity: str = Field(description="Severity level: CRITICAL, HIGH, MODERATE, LOW")
    data_status: str = Field(
        description="Three-state status: EVALUATED, DATA_UNAVAILABLE, NOT_APPLICABLE"
    )


class BearCase(BaseModel):
    """Constructed litigation narrative for a specific allegation theory.

    Evidence-gated: only created when sufficient triggered checks exist
    to support a plausible litigation narrative. Varies by company.
    """

    model_config = ConfigDict(frozen=False)

    theory: str = Field(
        description="AllegationTheory value: A_DISCLOSURE, B_GUIDANCE, etc."
    )
    plaintiff_type: str = Field(
        description="Primary PlaintiffLens for this bear case"
    )
    committee_summary: str = Field(
        description="2-3 sentence summary for underwriting committee"
    )
    evidence_chain: list[EvidenceItem] = Field(
        default_factory=lambda: [],
        description="Ordered evidence items supporting this bear case",
    )
    severity_estimate: str = Field(
        description="PerilSeverityBand value for estimated severity"
    )
    defense_assessment: str | None = Field(
        default=None,
        description="Company-specific defense assessment, ONLY if defense exists",
    )
    probability_band: str = Field(
        description="PerilProbabilityBand value for this bear case"
    )
    supporting_signal_count: int = Field(
        default=0,
        description="Number of checks supporting this bear case",
    )


class PlaintiffFirmMatch(BaseModel):
    """Matched plaintiff firm from tier configuration.

    Indicates a known plaintiff firm has been identified in the company's
    litigation data, with severity multiplier from firm tier.
    """

    model_config = ConfigDict(frozen=False)

    firm_name: str = Field(description="Matched plaintiff firm name")
    tier: int = Field(description="Firm tier: 1 (elite), 2 (major), 3 (regional)")
    severity_multiplier: float = Field(
        description="Severity multiplier from plaintiff_firms.json"
    )
    match_source: str = Field(
        description="Where the match was found (e.g., 'securities_class_actions[0].lead_counsel')"
    )


# -----------------------------------------------------------------------
# Root Container
# -----------------------------------------------------------------------


class PerilMap(BaseModel):
    """Root container for 7-lens peril assessment.

    Aggregates PlaintiffAssessments (exactly 7, one per lens),
    evidence-gated BearCases, plaintiff firm matches, and coverage gaps.
    Stored serialized as dict on AnalysisResults.peril_map.
    """

    model_config = ConfigDict(frozen=False)

    assessments: list[PlaintiffAssessment] = Field(
        default_factory=lambda: [],
        description="Exactly 7 assessments, one per PlaintiffLens",
    )
    bear_cases: list[BearCase] = Field(
        default_factory=lambda: [],
        description="Evidence-gated bear cases (varies by company, populated by Plan 04)",
    )
    plaintiff_firm_matches: list[PlaintiffFirmMatch] = Field(
        default_factory=lambda: [],
        description="Matched plaintiff firms from litigation data",
    )
    overall_peril_rating: str = Field(
        default=PerilProbabilityBand.VERY_LOW,
        description="Highest probability_band across all assessments",
    )
    coverage_gaps: list[str] = Field(
        default_factory=lambda: [],
        description="Checks with DATA_UNAVAILABLE status for coverage gap reporting",
    )


__all__ = [
    "BearCase",
    "EvidenceItem",
    "PerilMap",
    "PerilProbabilityBand",
    "PerilSeverityBand",
    "PlaintiffAssessment",
    "PlaintiffFirmMatch",
]
