"""CompositeDefinition and CompositeResult schemas for brain composites.

Composites are a BRAIN-layer concept (analysis, NOT display). They group
related signals and produce analytical conclusions from their structured
details fields.

Three-layer architecture:
  Signals (atomic evaluation) -> Composites (brain analysis) -> Facets (display)

Phase 50 Plan 04: Initial schema and YAML loading.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class CompositeDefinition(BaseModel):
    """Schema for a brain/composites/*.yaml file.

    Declares which signals a composite reads and what analytical
    conclusion it produces.
    """

    model_config = ConfigDict(extra="allow")

    id: str = Field(description="Composite ID, e.g. 'COMP.STOCK.drop_analysis'")
    name: str = Field(description="Human-readable composite name")
    description: str = Field(default="", description="What this composite analyzes")
    member_signals: list[str] = Field(
        description="Signal IDs that this composite reads"
    )
    conclusion_schema: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Maps field_name -> description of what that field contains. "
            "e.g. {'events_by_pattern': 'grouped by: earnings, litigation, sector, company-specific'}"
        ),
    )
    evaluator: str = Field(
        default="default",
        description=(
            "Which evaluation function to use. 'default' uses generic "
            "aggregation. Named evaluators use domain-specific logic."
        ),
    )
    severity_rules: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "How to determine composite severity (RED/YELLOW/CLEAR). "
            "e.g. {'red': 'any member TRIGGERED with company_specific=true'}"
        ),
    )


class CompositeResult(BaseModel):
    """Result of evaluating a composite.

    Produced by the evaluation engine after reading member signal results.
    Contains both structured analytical conclusions and a narrative summary.
    """

    model_config = ConfigDict(frozen=False)

    composite_id: str = Field(description="Composite ID that was evaluated")
    name: str = Field(description="Human-readable composite name")
    member_results: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="signal_id -> {status, value, details, ...} for each member",
    )
    conclusion: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured analytical conclusion per conclusion_schema",
    )
    narrative: str = Field(
        default="",
        description="One-paragraph summary for display",
    )
    severity: str = Field(
        default="CLEAR",
        description="RED, YELLOW, or CLEAR",
    )
    member_count: int = Field(default=0, description="Total member signals")
    triggered_count: int = Field(default=0, description="Members with TRIGGERED status")
    skipped_count: int = Field(default=0, description="Members with SKIPPED status")


def load_composite(path: Path) -> CompositeDefinition:
    """Load and validate a single brain/composites/*.yaml file."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return CompositeDefinition.model_validate(raw)


def load_all_composites(composites_dir: Path) -> dict[str, CompositeDefinition]:
    """Load all *.yaml files from brain/composites/ and return {composite_id: CompositeDefinition}."""
    composites: dict[str, CompositeDefinition] = {}
    if not composites_dir.exists():
        return composites
    for yaml_path in sorted(composites_dir.glob("*.yaml")):
        composite = load_composite(yaml_path)
        composites[composite.id] = composite
    return composites


__all__ = [
    "CompositeDefinition",
    "CompositeResult",
    "load_all_composites",
    "load_composite",
]
