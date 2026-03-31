"""Pydantic schema for brain/checks YAML check entries.

BrainSignalEntry defines the required and optional fields for each check entry
in brain/signals/**/*.yaml. BrainKnowledgeLoader.load_signals() validates every
entry from brain.duckdb against this schema on load, raising RuntimeError on
schema violations.

Fields derived from audit of all 36 YAML files (400 entries) during Phase 45.
Required fields are those present in every entry. Optional fields have defaults.

Notes on optional fields:
- `factors` is optional (default=[]) because some extract/display checks
  (e.g., BIZ.*, FWRD.DISC.*, NLP.MDA.*) legitimately omit it — they describe
  descriptive panels rather than scored risk factors.
- `layer` is optional (default=None) because brain.duckdb stores this value as
  `_brain_risk_framework_layer` (the DuckDB column is `risk_framework_layer`).
  All 400 YAML source files have `layer` — only the DuckDB output format omits
  it under that key. This does not indicate missing data.
"""
from __future__ import annotations

from typing import Any

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DisplaySpec(BaseModel):
    """Brain-driven rendering specification for a Signal (check).

    These fields drive QA audit table and red flags template rendering:
    - value_format: How to display result.value in QA audit ("numeric_2dp",
      "boolean", "text", "pct_1dp")
    - source_type: Filing type key this check primarily sources from
      ("SEC_10K", "SEC_DEF14A", "WEB", etc.)
    - threshold_context: Human-readable threshold criterion text (pre-filled
      from threshold.red/yellow; populated at eval time by _apply_traceability())
    - deprecation_note: If non-empty, check is permanently unanswerable;
      shown in output as a flag for review
    """

    model_config = ConfigDict(extra="allow")

    value_format: str = Field(
        default="text",
        description="Display format for result.value: 'numeric_2dp', 'boolean', 'text', 'pct_1dp'",
    )
    source_type: str = Field(
        default="",
        description="Primary source key (e.g. 'SEC_10K') for filing date lookup",
    )
    threshold_context: str = Field(
        default="",
        description=(
            "Human-readable threshold criterion; also populated at eval time "
            "by _apply_traceability()"
        ),
    )
    deprecation_note: str = Field(
        default="",
        description=(
            "Non-empty = check is permanently unanswerable; surface in output for review"
        ),
    )


class BrainSignalThreshold(BaseModel):
    """Threshold definition for a check entry.

    type is required. Level strings (red/yellow/clear/triggered) are optional
    since different threshold types use different level keys (e.g., boolean
    thresholds use 'triggered', display thresholds omit all levels).
    """

    model_config = {"extra": "allow"}  # allow additional threshold keys

    type: str  # "tiered", "boolean", "numeric", "percentage", "info", "display", etc.
    red: str | None = None
    yellow: str | None = None
    clear: str | None = None
    triggered: str | None = None  # used by boolean threshold types


class ThresholdProvenance(BaseModel):
    """Source attribution for a signal's threshold values."""

    model_config = ConfigDict(extra="allow")

    source: str = Field(
        default="unattributed",
        description="calibrated|standard|unattributed",
    )
    rationale: str = Field(
        default="",
        description="Why this threshold value",
    )


class BrainSignalProvenance(BaseModel):
    """Provenance metadata for a check entry."""

    model_config = {"extra": "allow"}

    origin: str
    confidence: str | None = None
    last_validated: str | None = None
    source_url: str | None = None
    source_date: str | None = None
    source_author: str | None = None
    added_by: str | None = None

    # V3 audit trail fields (Phase 82)
    formula: str = Field(
        default="",
        description="Evaluation logic description",
    )
    threshold_provenance: ThresholdProvenance | None = Field(
        default=None,
        description="Threshold source and rationale",
    )
    render_target: str = Field(
        default="",
        description="Output location (section/group)",
    )
    data_source: str = Field(
        default="",
        description="Primary data source type (SEC_10K, XBRL, WEB, etc.)",
    )


class SignalDependency(BaseModel):
    """A prerequisite signal dependency for v3 signal execution ordering."""

    model_config = ConfigDict(extra="forbid")

    signal: str = Field(..., description="Prerequisite signal ID")
    field: str = Field(
        default="",
        description="Specific field needed from that signal",
    )


# ---------------------------------------------------------------------------
# V2 Signal Contract sub-models (Phase 54)
# All use extra='forbid' to catch YAML typos immediately.
# ---------------------------------------------------------------------------


class AcquisitionSource(BaseModel):
    """A single data source in the acquisition chain."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        ...,
        description="Source type key (e.g. 'SEC_10K', 'SEC_10Q', 'MARKET_PRICE', 'SCAC_SEARCH')",
    )
    fields: list[str] = Field(
        default_factory=list,
        description="Dotted paths to data (e.g. ['extracted.financials.liquidity'])",
    )
    fallback_to: str | None = Field(
        default=None,
        description="Next source type in the fallback chain",
    )


class AcquisitionSpec(BaseModel):
    """V2 acquisition section: declares data sources and fallback chains."""

    model_config = ConfigDict(extra="forbid")

    sources: list[AcquisitionSource] = Field(
        default_factory=list,
        description="Ordered list of data sources with field paths",
    )


class EvaluationThreshold(BaseModel):
    """A single structured threshold entry for machine-readable evaluation."""

    model_config = ConfigDict(extra="forbid")

    op: Literal["<", ">", "<=", ">=", "==", "!=", "between", "contains"] = Field(
        ...,
        description="Comparison operator",
    )
    value: float | str | list[float] = Field(
        ...,
        description="Threshold value (numeric, string, or [low, high] for 'between')",
    )
    label: Literal["RED", "YELLOW", "CLEAR"] = Field(
        ...,
        description="Severity label when this threshold matches",
    )


class ClearCondition(BaseModel):
    """A qualitative clear condition for non-numeric values.

    Used by signals like FIN.LIQ.cash_burn where "Profitable" text
    means CLEAR without numeric threshold evaluation.
    """

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        ...,
        description="Condition type (e.g. 'qualitative_value')",
    )
    pattern: str = Field(
        ...,
        description="String pattern to match in the value (e.g. 'Profitable')",
    )
    result: str = Field(
        default="CLEAR",
        description="Result when pattern matches (usually 'CLEAR')",
    )


EvaluationMechanism = Literal[
    "threshold", "peer_comparison", "trend", "conjunction", "absence", "contextual"
]


# ---------------------------------------------------------------------------
# Mechanism-specific rule sub-models (Phase 110)
# ---------------------------------------------------------------------------


class ContextAdjustment(BaseModel):
    """A single context-based threshold adjustment."""

    model_config = ConfigDict(extra="forbid")

    threshold_adjustment: float = Field(
        ...,
        description="Multiplier for threshold (0.5 = halve, 1.5 = raise 50%)",
    )
    rationale: str = Field(
        default="",
        description="Why this adjustment is appropriate",
    )


class ConjunctionRuleSpec(BaseModel):
    """Rules for conjunction mechanism: multiple signals must co-fire.

    Evaluates whether 2+ component signals fire together, producing an
    elevated risk assessment. Used for dangerous D&O combinations like
    CEO pay up + performance down + no clawback.
    """

    model_config = ConfigDict(extra="forbid")

    required_signals: list[str] = Field(
        ...,
        description="Signal IDs that must be checked for co-firing",
    )
    minimum_matches: int = Field(
        default=2,
        description="Minimum number of required_signals that must match",
    )
    signal_conditions: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Per-signal expected status override. "
            "Default expectation is TRIGGERED; use CLEAR to check for absence. "
            "Example: {'SIG.CLAWBACK': 'CLEAR'} means clawback NOT present."
        ),
    )
    recommendation_floor: str | None = Field(
        default=None,
        description="Minimum recommendation tier when conjunction fires (e.g. ELEVATED, HIGH_RISK)",
    )


class AbsenceRuleSpec(BaseModel):
    """Rules for absence mechanism: detect missing expected disclosures.

    Evaluates whether an expected disclosure is missing based on company
    profile, peer comparison, or regulatory requirement.
    """

    model_config = ConfigDict(extra="forbid")

    expectation_type: Literal["company_profile", "peer_comparison", "always_expected"] = Field(
        ...,
        description="What drives the expectation: company profile, peer norms, or universal requirement",
    )
    condition: str = Field(
        default="",
        description="Human-readable condition for when this disclosure is expected",
    )
    expected_signals: list[str] = Field(
        ...,
        description="Signal IDs whose presence indicates the disclosure exists",
    )
    expected_status: str = Field(
        default="TRIGGERED",
        description="Status that indicates disclosure is present (usually TRIGGERED or CLEAR)",
    )
    absence_trigger: str = Field(
        default="SKIPPED",
        description="Status that indicates disclosure is absent (usually SKIPPED)",
    )


class ContextualRuleSpec(BaseModel):
    """Rules for contextual mechanism: re-evaluate through company-type lens.

    Re-evaluates a source signal's result through lifecycle/sector/size/product/tower
    context, applying threshold adjustments based on company classification.
    """

    model_config = ConfigDict(extra="forbid")

    source_signal: str = Field(
        ...,
        description="Signal ID to re-evaluate in context",
    )
    context_dimensions: list[str] = Field(
        ...,
        description="Which context dimensions to use (lifecycle_stage, sector, size_tier, etc.)",
    )
    context_adjustments: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Context value -> adjustment mapping. "
            "Each value maps to {threshold_adjustment: float, rationale: str}."
        ),
    )


class EvaluationSpec(BaseModel):
    """V2 evaluation section: formula and structured thresholds."""

    model_config = ConfigDict(extra="forbid")

    formula: str | None = Field(
        default=None,
        description="Field reference or expression to evaluate",
    )
    thresholds: list[EvaluationThreshold] = Field(
        default_factory=list,
        description="Ordered thresholds (check first match, red first)",
    )
    window_years: int | None = Field(
        default=None,
        description="Lookback period in years",
    )
    clear_conditions: list[ClearCondition] = Field(
        default_factory=list,
        description="Qualitative clear conditions for non-numeric values (e.g. 'Profitable')",
    )
    mechanism: EvaluationMechanism = Field(
        ...,
        description="How this signal is evaluated (threshold, peer_comparison, trend, etc.)",
    )

    # Phase 110: Mechanism-specific rule specs (Optional for backward compat)
    conjunction_rules: ConjunctionRuleSpec | None = Field(
        default=None,
        description="Conjunction mechanism rules: required_signals, minimum_matches, conditions",
    )
    absence_rules: AbsenceRuleSpec | None = Field(
        default=None,
        description="Absence mechanism rules: expectation_type, expected_signals, conditions",
    )
    contextual_rules: ContextualRuleSpec | None = Field(
        default=None,
        description="Contextual mechanism rules: source_signal, context_dimensions, adjustments",
    )


class Epistemology(BaseModel):
    """Rule origin and threshold basis documentation for a signal.

    Captures WHERE a signal's logic comes from and WHY specific threshold
    values were chosen. Required for epistemological traceability in the
    RAP taxonomy (Phase 103+).
    """

    model_config = ConfigDict(extra="forbid")

    rule_origin: str = Field(
        ...,
        description=(
            "Where this rule comes from: 'SCAC filing analysis', "
            "'Cornerstone settlement data', 'D&O claims experience', "
            "'SEC enforcement patterns', 'academic research: [citation]', "
            "'industry standard', 'calibrated from [source]'"
        ),
    )
    threshold_basis: str = Field(
        ...,
        description=(
            "Why these specific threshold values: quantitative basis, "
            "empirical source, or expert calibration rationale"
        ),
    )


class ScoringContribution(BaseModel):
    """Per-factor weight override for a signal's scoring contribution."""

    model_config = ConfigDict(extra="forbid")

    factor: str = Field(
        ...,
        description="Factor key (short F1 or long F1_prior_litigation)",
    )
    weight: float = Field(
        default=1.0,
        description="Weight multiplier for this factor (default 1.0)",
    )


class ScoringSpec(BaseModel):
    """Optional scoring specification for a brain signal.

    Allows per-signal weight overrides and per-factor contribution
    specifications. When absent, signals use default weight 1.0
    (or 0.5 for inference signals).
    """

    model_config = ConfigDict(extra="forbid")

    weight: float = Field(
        default=1.0,
        description="Global weight for this signal's scoring contribution",
    )
    contributions: list[ScoringContribution] = Field(
        default_factory=list,
        description="Per-factor weight overrides (optional)",
    )


class PresentationDetailLevel(BaseModel):
    """Content specification at a specific detail level."""

    model_config = ConfigDict(extra="forbid")

    level: Literal["glance", "standard", "deep"] = Field(
        ...,
        description="Detail level identifier",
    )
    template: str = Field(
        default="",
        description="Jinja2-compatible template string for this level",
    )
    fields: list[str] = Field(
        default_factory=list,
        description="Fields to include at this detail level",
    )


class PresentationSpec(BaseModel):
    """V2 presentation section: rendering hints beyond DisplaySpec."""

    model_config = ConfigDict(extra="forbid")

    detail_levels: list[PresentationDetailLevel] = Field(
        default_factory=list,
        description="Content specifications per detail level",
    )
    context_templates: dict[str, str] = Field(
        default_factory=dict,
        description="Status-keyed template strings (e.g. TRIGGERED, CLEAR)",
    )
    do_context: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "D&O commentary templates keyed by signal outcome "
            "(TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR, TRIGGERED, DEFAULT). "
            "Evaluated in ANALYZE via do_context_engine.py. "
            "Variables: {value}, {score}, {zone}, {threshold}, {threshold_level}, "
            "{evidence}, {source}, {confidence}, {company}, {ticker}, {details_*}."
        ),
    )


class BrainSignalEntry(BaseModel):
    """Pydantic model for a single check entry in brain/signals/**/*.yaml.

    Required fields (present in all 400 entries across 36 YAML files and in
    brain.duckdb output): id, name, work_type, tier, depth, threshold, provenance.

    Optional fields with explicit defaults:
    - factors: optional because descriptive checks (BIZ.*, FWRD.DISC.*)
      legitimately omit it; they describe panels rather than scored risk factors.
    - layer: optional because brain.duckdb output stores the value under
      `_brain_risk_framework_layer` (not `layer`). All YAML source files have it.

    Usage:
        entry = BrainSignalEntry.model_validate(raw_dict)
    """

    model_config = {"extra": "allow"}  # accept unknown fields — don't block on new fields

    # Required fields — present in both YAML files and brain.duckdb output
    id: str = Field(..., description="Check identifier (e.g., 'FIN.PROFIT.revenue')")
    name: str = Field(..., description="Human-readable check name")
    work_type: str = Field(..., description="Check work type (evaluate, detect, extract, etc.)")
    tier: int = Field(..., description="Priority tier (1-3)")
    depth: int = Field(..., description="Analysis depth (1-4)")
    threshold: BrainSignalThreshold = Field(..., description="Threshold definition")
    provenance: BrainSignalProvenance = Field(..., description="Origin and audit metadata")

    # Optional: present in YAML files; brain.duckdb stores as _brain_risk_framework_layer
    layer: str | None = Field(
        default=None,
        description="Risk framework layer (signal, peril_confirming, hazard, etc.)",
    )

    # Optional fields with defaults
    factors: list[str] = Field(
        default_factory=list,
        description="Factor IDs this check contributes to (empty for descriptive checks)",
    )
    peril_ids: list[str] = Field(default_factory=list)
    chain_roles: dict[str, Any] = Field(default_factory=dict)
    unlinked: bool = False
    acquisition_tier: str | None = None
    required_data: list[str] = Field(default_factory=list)
    data_locations: dict[str, Any] = Field(default_factory=dict)
    extraction_hints: dict[str, Any] | None = None
    data_strategy: dict[str, Any] | None = None
    plaintiff_lenses: list[str] = Field(default_factory=list)
    v6_subsection_ids: list[str] = Field(default_factory=list)
    worksheet_section: str | None = None
    display_when: str | None = None
    claims_correlation: float | None = None
    critical_red_flag: bool = False
    sector_adjustments: dict[str, Any] | None = None
    display: DisplaySpec | None = Field(
        default=None,
        description="Signal rendering specification (value_format, source_type, etc.)",
    )

    # Correlation metadata (Phase 57 - Learning Loop)
    correlated_signals: list[str] = Field(
        default_factory=list,
        description="Signal IDs discovered to correlate with this signal",
    )

    # V2 Signal Contract fields (Phase 54)
    # All Optional with defaults so 400 existing V1 signals load unchanged.
    schema_version: int = Field(
        default=1,
        description="1=legacy, 2=V2 declarative",
    )
    acquisition: AcquisitionSpec | None = Field(
        default=None,
        description="V2 acquisition section: data sources and fallback chains",
    )
    evaluation: EvaluationSpec = Field(
        description="V2 evaluation section: formula and structured thresholds (required v7.0)",
    )
    presentation: PresentationSpec | None = Field(
        default=None,
        description="V2 presentation section: detail levels and context templates",
    )

    # V3 Signal Contract fields (Phase 82)
    group: str = Field(
        default="",
        description="Fine-grained group ID matching manifest group objects",
    )
    depends_on: list[SignalDependency] = Field(
        default_factory=list,
        description="Prerequisite signals this signal needs",
    )
    field_path: str = Field(
        default="",
        description="Data resolution path (registry key or dotted path)",
    )
    signal_class: Literal["foundational", "evaluative", "inference"] = Field(
        default="evaluative",
        description="Execution tier: foundational -> evaluative -> inference",
    )

    # V4 RAP taxonomy fields (Phase 103 - Schema Foundation)
    # REQUIRED: All signals must have these v7.0 fields. Any new signal added
    # without them will fail at YAML load time.
    rap_class: Literal["host", "agent", "environment"] = Field(
        ...,
        description="H/A/E risk dimension from RAP taxonomy",
    )
    rap_subcategory: str = Field(
        ...,
        description="Subcategory within H/A/E (e.g. 'host.financials', 'agent.executive_conduct')",
    )
    epistemology: Epistemology = Field(
        ...,
        description="Rule origin and threshold basis documentation",
    )

    # V4 scoring fields (Phase 112 - Signal-Driven Scoring)
    scoring: ScoringSpec | None = Field(
        default=None,
        description="Optional scoring weight overrides for signal-driven factor scoring",
    )
