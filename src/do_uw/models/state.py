"""AnalysisState -- THE single source of truth for the entire analysis.

This is the root model for the 7-stage pipeline. Every stage reads from
and writes to this model. There is NO other state representation.

Per CLAUDE.md: "Single state file (AnalysisState), not multiple competing
state representations."
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from do_uw.models.ai_risk import AIRiskAssessment
from do_uw.models.alt_data import AltDataAssessments
from do_uw.models.classification import ClassificationResult
from do_uw.models.common import StageResult, StageStatus
from do_uw.models.company import CompanyProfile
from do_uw.models.density import (
    PreComputedCommentary,
    PreComputedNarratives,
    SectionDensity,
)
from do_uw.models.dossier import DossierData
from do_uw.models.executive_summary import ExecutiveSummary
from do_uw.models.financials import ExtractedFinancials
from do_uw.models.forward_looking import ForwardLookingData
from do_uw.models.governance import GovernanceData
from do_uw.models.hazard_profile import HazardProfile
from do_uw.models.litigation import LitigationLandscape
from do_uw.models.market import MarketSignals
from do_uw.models.scoring import BenchmarkResult, ScoringResult
from do_uw.models.ten_k_comparison import TenKYoYComparison

PIPELINE_STAGES: list[str] = [
    "resolve",
    "acquire",
    "extract",
    "analyze",
    "score",
    "benchmark",
    "render",
]
"""The 7-stage pipeline in execution order."""


class AcquiredData(BaseModel):
    """Raw data acquired in ACQUIRE stage.

    Holds raw filing content, market data snapshots, and litigation
    search results before they are parsed in EXTRACT stage.
    """

    model_config = ConfigDict(frozen=False)

    # Core data fields (populated by individual clients).
    filings: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw SEC filings keyed by type (10-K, 10-Q, DEF14A, etc.)",
    )
    market_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw market data (stock prices, short interest, etc.)",
    )
    litigation_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw litigation search results (SCAC, CourtListener, etc.)",
    )
    web_search_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Blind spot detection web search results",
    )
    regulatory_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Regulatory data (FDA, EPA, DOJ, etc.)",
    )
    reference_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Static reference data (sector hazard tiers, claim patterns, etc.)",
    )
    filing_documents: dict[str, list[dict[str, str]]] = Field(
        default_factory=dict,
        description=(
            "Full filing documents keyed by form type, each a list "
            "of FilingDocument dicts (accession, filing_date, "
            "form_type, full_text)"
        ),
    )

    # Acquisition metadata (populated by orchestrator).
    acquisition_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=("Per-source metadata: timestamps, confidence, tier used, errors"),
    )
    gate_results: list[dict[str, Any]] = Field(
        default_factory=lambda: [],
        description="Gate check results from ACQUIRE stage",
    )
    search_budget_used: int = Field(
        default=0,
        description="Web searches used in this analysis",
    )
    blind_spot_results: dict[str, Any] = Field(
        default_factory=dict,
        description=("Blind spot discovery search results (pre and post structured acquisition)"),
    )
    llm_extractions: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "LLM extraction results keyed by 'form_type:accession'. "
            "Values are serialized Pydantic model dicts."
        ),
    )
    patent_data: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Raw USPTO AI patent search results fetched in ACQUIRE stage",
    )
    company_logo_b64: str = Field(
        default="",
        description="Company favicon as base64-encoded PNG/ICO, fetched during ACQUIRE",
    )
    brain_targeted_search: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Gap search results keyed by signal_id. "
            "Populated by Phase E of ACQUIRE for checks with "
            "data_status_reason='Data mapping not configured'. "
            "Format: {signal_id: {query, results_count, keywords_matched, "
            "suggested_status, domain, confidence}}"
        ),
    )


class RiskFactorProfile(BaseModel):
    """Structured risk factor from Item 1A extraction.

    Spans governance and litigation domains. Stored at the top-level
    ExtractedData because risk factors are cross-domain.
    """

    title: str = ""
    category: str = "OTHER"  # LITIGATION, REGULATORY, FINANCIAL, CYBER, ESG, AI, OTHER
    severity: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    is_new_this_year: bool = False
    do_relevance: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    source_passage: str = ""
    source: str = ""
    classification: str = "STANDARD"  # STANDARD, NOVEL, ELEVATED
    do_implication: str = ""  # D&O litigation theory this factor maps to


class ExtractedData(BaseModel):
    """Structured facts extracted in EXTRACT stage.

    Parses raw AcquiredData into strongly-typed sub-models.
    Each field corresponds to a domain area.
    """

    model_config = ConfigDict(frozen=False)

    financials: ExtractedFinancials | None = None
    market: MarketSignals | None = None
    governance: GovernanceData | None = None
    litigation: LitigationLandscape | None = None
    ai_risk: AIRiskAssessment | None = None
    risk_factors: list[RiskFactorProfile] = Field(
        default_factory=lambda: [],
        description="Item 1A risk factors, structured and categorized",
    )
    text_signals: dict[str, Any] = Field(
        default_factory=dict,
        description="Topic presence signals extracted from 10-K filing text sections",
    )
    ten_k_yoy: TenKYoYComparison | None = Field(
        default=None,
        description="Year-over-year 10-K comparison (risk factors, controls, legal)",
    )


class AnalysisResults(BaseModel):
    """Check execution results from ANALYZE stage.

    Tracks which of the 359 checks were executed and their results.
    """

    model_config = ConfigDict(frozen=False)

    checks_executed: int = Field(default=0, description="Number of checks that ran")
    checks_passed: int = Field(default=0, description="Checks that passed (no issue found)")
    checks_failed: int = Field(default=0, description="Checks that failed (issue detected)")
    checks_skipped: int = Field(default=0, description="Checks skipped due to missing data")
    gap_search_summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Gap search re-evaluation summary: {updated, triggered, clear}",
    )
    signal_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Individual check results keyed by check ID",
    )
    patterns_detected: list[str] = Field(
        default_factory=lambda: [],
        description="Composite pattern IDs that fired",
    )

    # Phase 26: Enhanced analytical engine outputs (stored as dicts to avoid coupling)
    temporal_signals: dict[str, Any] | None = Field(
        default=None,
        description="TemporalAnalysisResult serialized from temporal engine",
    )
    forensic_composites: dict[str, Any] | None = Field(
        default=None,
        description="FIS, RQS, CFQS composite forensic scores serialized",
    )
    executive_risk: dict[str, Any] | None = Field(
        default=None,
        description="BoardAggregateRisk from executive forensics serialized",
    )
    nlp_signals: dict[str, Any] | None = Field(
        default=None,
        description="NLP signal analysis results (readability, tone, risk factors)",
    )
    xbrl_forensics: dict[str, Any] | None = Field(
        default=None,
        description="XBRL-based forensic analysis results (Phase 69)",
    )

    # Phase 27: Peril mapping and settlement prediction outputs
    peril_map: dict[str, Any] | None = Field(
        default=None,
        description="Phase 27 peril map serialized from PerilMap model",
    )
    settlement_prediction: dict[str, Any] | None = Field(
        default=None,
        description="Phase 27 settlement prediction replacing Phase 12 severity",
    )

    # Phase 35: Three-tier density assessment (replaces boolean *_clean fields)
    section_densities: dict[str, SectionDensity] = Field(
        default_factory=dict,
        description=(
            "Three-tier density assessment per section, "
            "computed in ANALYZE. Keys are section names "
            "(governance, litigation, financial, market, company, scoring)."
        ),
    )
    pre_computed_narratives: PreComputedNarratives | None = Field(
        default=None,
        description="LLM-generated narratives pre-computed in BENCHMARK",
    )
    pre_computed_commentary: PreComputedCommentary | None = Field(
        default=None,
        description="LLM-generated dual-voice commentary pre-computed in BENCHMARK",
    )

    # Phase 50: Signal composite evaluation results
    composite_results: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Composite evaluation results keyed by composite_id. "
            "Each value is a serialized CompositeResult dict with "
            "conclusion, narrative, severity, member_results."
        ),
    )

    # Phase 78: Signal disposition audit trail
    disposition_summary: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Signal disposition audit trail: total, triggered, clean, "
            "skipped, inactive counts plus per-signal dispositions. "
            "Populated by build_dispositions after signal evaluation."
        ),
    )


def _default_stages() -> dict[str, StageResult]:
    """Create default stage results for all 7 pipeline stages."""
    return {stage: StageResult(stage=stage) for stage in PIPELINE_STAGES}


class AnalysisState(BaseModel):
    """THE single source of truth for the entire D&O analysis.

    Every pipeline stage reads from and writes to this model.
    Serializes to JSON for caching and resumption.

    Lifecycle:
    1. RESOLVE: Populates company
    2. ACQUIRE: Populates acquired_data
    3. EXTRACT: Populates extracted (financials, market, governance, litigation)
    4. ANALYZE: Populates analysis (check results, pattern matches)
    5. SCORE: Populates scoring (factor scores, red flags, tier)
    6. BENCHMARK: Populates benchmark (peer comparisons)
    7. RENDER: Reads all of the above to generate output documents
    """

    model_config = ConfigDict(frozen=False)

    # Metadata
    version: str = Field(default="1.0.0", description="State schema version")
    ticker: str = Field(description="Stock ticker being analyzed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))

    # Pipeline progress -- all 7 stages start PENDING
    stages: dict[str, StageResult] = Field(default_factory=_default_stages)

    # Stage outputs
    company: CompanyProfile | None = Field(default=None, description="RESOLVE stage output")
    acquired_data: AcquiredData | None = Field(default=None, description="ACQUIRE stage output")
    extracted: ExtractedData | None = Field(default=None, description="EXTRACT stage output")
    analysis: AnalysisResults | None = Field(default=None, description="ANALYZE stage output")
    scoring: ScoringResult | None = Field(default=None, description="SCORE stage output")
    benchmark: BenchmarkResult | None = Field(default=None, description="BENCHMARK stage output")
    executive_summary: ExecutiveSummary | None = Field(
        default=None,
        description="BENCHMARK stage output: executive summary",
    )

    # Classification & Hazard Profile (Layers 1-2, run between EXTRACT and ANALYZE)
    classification: ClassificationResult | None = Field(
        default=None,
        description="Layer 1: Objective classification (3 variables -> filing rate)",
    )
    hazard_profile: HazardProfile | None = Field(
        default=None,
        description="Layer 2: Hazard profile (IES from 47 dimensions)",
    )

    # Cross-stage metadata (set by RESOLVE, consumed by downstream stages)
    active_playbook_id: str | None = Field(
        default=None,
        description=(
            "Industry playbook ID activated during RESOLVE stage "
            "(e.g., TECH_SAAS, BIOTECH_PHARMA). Used by ANALYZE for "
            "industry-specific checks."
        ),
    )

    # Forward-looking risk framework (Phase 117)
    # Top-level on AnalysisState because forward-looking data spans
    # extraction through benchmark stages.
    forward_looking: ForwardLookingData = Field(
        default_factory=ForwardLookingData,
        description="Forward-looking risk analysis: statements, credibility, posture, quick screen",
    )

    # Company intelligence dossier (Phase 118)
    # Top-level on AnalysisState because dossier data spans
    # extraction through rendering stages.
    dossier: DossierData = Field(
        default_factory=DossierData,
        description="Company intelligence dossier: revenue model, unit economics, emerging risks, ASC 606",
    )

    # Alternative data assessments (Phase 119)
    # Top-level on AnalysisState because alt data is a separate
    # analytical concern, not part of the intelligence dossier.
    alt_data: AltDataAssessments = Field(
        default_factory=AltDataAssessments,
        description="Alternative data risk assessments (Phase 119)",
    )

    # Phase 119: Transient inter-stage pipeline data
    # Populated in EXTRACT, consumed in BENCHMARK/RENDER.
    # Must be explicit fields -- Pydantic v2 silently ignores arbitrary attrs.
    stock_patterns: list[dict[str, str]] = Field(
        default_factory=list,
        description="Phase 119: Detected stock patterns (EXTRACT -> BENCHMARK/RENDER)",
    )
    multi_horizon_returns: dict[str, float | None] = Field(
        default_factory=dict,
        description="Phase 119: Multi-horizon return percentages (EXTRACT -> RENDER)",
    )
    analyst_consensus: dict[str, Any] = Field(
        default_factory=dict,
        description="Phase 119: Structured analyst consensus data (EXTRACT -> RENDER)",
    )
    drop_narrative: str = Field(
        default="",
        description="Phase 119: D&O underwriting implication narrative (BENCHMARK -> RENDER)",
    )

    # Pipeline run metadata (costs, timestamps, data freshness)
    pipeline_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Per-run metadata: LLM token counts/costs, data freshness date, "
            "extraction timestamps. Populated by EXTRACT, consumed by RENDER "
            "for worksheet footer. Using dict (not typed model) because "
            "metadata content varies by run configuration."
        ),
    )

    def mark_stage_running(self, stage: str) -> None:
        """Mark a pipeline stage as running."""
        if stage not in self.stages:
            msg = f"Unknown stage: {stage}. Valid: {PIPELINE_STAGES}"
            raise ValueError(msg)
        self.stages[stage].status = StageStatus.RUNNING
        self.stages[stage].started_at = datetime.now(tz=UTC)
        self.updated_at = datetime.now(tz=UTC)

    def mark_stage_completed(self, stage: str) -> None:
        """Mark a pipeline stage as completed with duration."""
        if stage not in self.stages:
            msg = f"Unknown stage: {stage}. Valid: {PIPELINE_STAGES}"
            raise ValueError(msg)
        result = self.stages[stage]
        result.status = StageStatus.COMPLETED
        result.completed_at = datetime.now(tz=UTC)
        if result.started_at is not None:
            delta = result.completed_at - result.started_at
            result.duration_seconds = delta.total_seconds()
        self.updated_at = datetime.now(tz=UTC)

    def mark_stage_failed(self, stage: str, error: str) -> None:
        """Mark a pipeline stage as failed with error message."""
        if stage not in self.stages:
            msg = f"Unknown stage: {stage}. Valid: {PIPELINE_STAGES}"
            raise ValueError(msg)
        result = self.stages[stage]
        result.status = StageStatus.FAILED
        result.completed_at = datetime.now(tz=UTC)
        result.error = error
        if result.started_at is not None:
            delta = result.completed_at - result.started_at
            result.duration_seconds = delta.total_seconds()
        self.updated_at = datetime.now(tz=UTC)
