"""SignalDefinition Pydantic model for enriched check metadata.

Defines the schema for enriched checks with content types, depth levels,
data strategy, evaluation criteria, and presentation hints. All new fields
are optional with backward-compatible defaults so existing signals.json
validates without modification.

Models:
    ContentType: What kind of information a check represents
    DepthLevel: How complex the data acquisition/processing is (1-4)
    DataStrategy: How to acquire and locate the data for a check
    EvaluationCriteria: Structured evaluation metadata (thresholds, direction)
    PresentationHint: Display formatting hints for the worksheet renderer
    SignalDefinition: Complete enriched check schema (superset of signals.json)
"""

from __future__ import annotations

from enum import IntEnum, StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContentType(StrEnum):
    """What kind of information a check represents.

    MANAGEMENT_DISPLAY: Extract & display — governance/context info shown as-is
    EVALUATIVE_CHECK: Extract & evaluate — data point with pass/fail/tiered logic
    INFERENCE_PATTERN: Multi-signal inference — combines multiple data points
    """

    MANAGEMENT_DISPLAY = "MANAGEMENT_DISPLAY"
    EVALUATIVE_CHECK = "EVALUATIVE_CHECK"
    INFERENCE_PATTERN = "INFERENCE_PATTERN"


class DepthLevel(IntEnum):
    """How complex the data acquisition and processing pipeline is.

    Maps to the Data Complexity Spectrum:
    1. DISPLAY: Extract & display — get number, show it
    2. COMPUTE: Extract & compute — get inputs, apply formula
    3. INFER: Extract & infer — pattern recognition across data points
    4. HUNT: Hunt & analyze — broad search, aggregation, deduplication
    """

    DISPLAY = 1
    COMPUTE = 2
    INFER = 3
    HUNT = 4


class DataStrategy(BaseModel):
    """How to acquire and locate the data for a check.

    Describes the primary data source, extraction path into the
    ExtractedData model, field key for evaluators, fallback sources,
    and optional computation function for derived values.
    """

    model_config = ConfigDict(extra="forbid")

    primary_source: str
    """Primary data source identifier (e.g., 'SEC_10K')."""

    extraction_path: str | None = None
    """Dotted path into ExtractedData (e.g., 'financials.liquidity.current_ratio')."""

    field_key: str | None = None
    """The field key the evaluator sees (e.g., 'current_ratio')."""

    narrative_key: str | None = None
    """LLM narrative field key for dual-source signals (Phase 70)."""

    fallback_sources: list[str] = Field(default_factory=list)
    """Ordered list of fallback source identifiers."""

    computation: str | None = None
    """Name of computation function for complex derivations."""


class EvaluationCriteria(BaseModel):
    """Structured evaluation metadata for a check.

    Defines how a check result is evaluated: the threshold type,
    what metric is measured, directionality, and threshold values
    for red/yellow/clear classification.
    """

    model_config = ConfigDict(extra="forbid")

    type: str
    """Threshold type (e.g., 'tiered', 'boolean', 'percentage')."""

    metric: str | None = None
    """What is being measured (e.g., 'current_ratio', 'short_interest_pct')."""

    direction: str | None = None
    """Directionality: 'lower_is_worse', 'higher_is_worse', 'presence_is_bad'."""

    thresholds: dict[str, Any] | None = None
    """Structured thresholds for classification (red/yellow/clear levels)."""


class PresentationHint(BaseModel):
    """Display formatting hints for the worksheet renderer.

    Optional metadata that tells the renderer how to format and
    place check results in the output worksheet.
    """

    model_config = ConfigDict(extra="allow")

    display_format: str | None = None
    """Format type: 'ratio', 'percentage', 'currency', 'boolean', 'narrative'."""

    worksheet_label: str | None = None
    """Human-readable label override for the worksheet."""

    section_placement: str | None = None
    """Human-readable section name for placement in the worksheet."""


class SignalDefinition(BaseModel):
    """Complete enriched check schema — superset of signals.json.

    Preserves all existing fields from signals.json with their original
    names and types, and adds optional enrichment fields with backward-
    compatible defaults. Uses extra='allow' so unknown fields in
    signals.json (like amplifier, sector_adjustments) don't cause
    validation errors.
    """

    model_config = ConfigDict(extra="allow")

    # --- Existing fields (from signals.json / YAML) ---
    id: str
    name: str
    section: int = 0
    pillar: str = ""
    factors: list[str] = Field(default_factory=list)
    required_data: list[str] = Field(default_factory=list)
    data_locations: dict[str, Any] = Field(default_factory=dict)
    threshold: dict[str, Any] = Field(default_factory=dict)
    execution_mode: str = "AUTO"
    claims_correlation: float | None = None
    tier: int = 1

    # Phase 26 classification fields
    category: str | None = None
    signal_type: str | None = None
    hazard_or_signal: str | None = None
    plaintiff_lenses: list[str] = Field(default_factory=list)

    # --- New enrichment fields (all optional, backward-compatible) ---
    content_type: ContentType = ContentType.EVALUATIVE_CHECK
    """What kind of information this check represents."""

    depth: DepthLevel = DepthLevel.COMPUTE
    """How complex the data acquisition/processing is (1-4)."""

    rationale: str | None = None
    """Why this check matters for D&O underwriting."""

    data_strategy: DataStrategy | None = None
    """How to acquire and locate the data for this check."""

    evaluation_criteria: EvaluationCriteria | None = None
    """Structured evaluation metadata (thresholds, direction)."""

    presentation: PresentationHint | None = None
    """Display formatting hints for the worksheet renderer."""

    pattern_ref: str | None = None
    """For INFERENCE_PATTERN checks, reference to patterns.json ID."""

    @classmethod
    def from_signal_dict(cls, data: dict[str, Any]) -> SignalDefinition:
        """Create a SignalDefinition from a raw check dictionary.

        Validates the dict through Pydantic model_validate, applying
        defaults for any missing enrichment fields.
        """
        return cls.model_validate(data)

    def to_signal_dict(self) -> dict[str, Any]:
        """Export to a plain dict, excluding None values.

        Returns a dict suitable for JSON serialization, with None
        fields omitted for clean output.
        """
        return self.model_dump(exclude_none=True)
