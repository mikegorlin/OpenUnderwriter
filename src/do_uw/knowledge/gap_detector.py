"""Pipeline gap detection: compare check requirements to pipeline capabilities.

Produces a GapReport with 3 severity levels across 3 gap types:
  - CRITICAL: Source-level gap (ACQUIRE doesn't fetch a required source)
  - WARNING: Field-level gap (no field_key AND no FIELD_FOR_CHECK entry AND no Phase 26+ mapper)
  - INFO: Mapper-level gap (check prefix has no registered mapper handler)

Used as a standalone CLI tool (Plan 07) and optionally at pipeline startup.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from do_uw.knowledge.requirements import AcquisitionManifest


class PipelineGap(BaseModel):
    """A single gap in the pipeline coverage for a check."""

    signal_id: str
    signal_name: str
    gap_type: str
    """One of: SOURCE_NOT_ACQUIRED, NO_FIELD_ROUTING, NO_MAPPER_HANDLER."""
    detail: str
    severity: str
    """One of: CRITICAL, WARNING, INFO."""


class GapReport(BaseModel):
    """Complete gap analysis for the pipeline."""

    total_signals: int = 0
    """Total AUTO signals analyzed."""

    fully_supported: int = 0
    """Checks with no gaps at any level."""

    gaps: list[PipelineGap] = Field(default_factory=list)
    """All detected gaps."""

    by_type: dict[str, int] = Field(default_factory=dict)
    """Gap count by gap_type."""

    by_severity: dict[str, int] = Field(default_factory=dict)
    """Gap count by severity level."""


# ---------------------------------------------------------------------------
# Pipeline capability constants
# ---------------------------------------------------------------------------

# Known data sources that ACQUIRE can fetch
ACQUIRED_SOURCES: set[str] = {
    "SEC_10K",
    "SEC_10Q",
    "SEC_DEF14A",
    "SEC_8K",
    "SEC_FORM4",
    "SEC_13DG",
    "SEC_S1",
    "SEC_S3",
    "SEC_424B",
    "SEC_FRAMES",
    "REFERENCE_DATA",
    "INSIDER_TRADES",
    "MARKET_PRICE",
    "MARKET_SHORT",
    "SCAC_SEARCH",
    "SEC_ENFORCEMENT",
    "WEB_SEARCH",
}

# Top-level prefixes with registered mapper handlers in signal_mappers.py
HANDLED_PREFIXES: set[str] = {
    "BIZ",
    "STOCK",
    "FIN",
    "LIT",
    "GOV",
    "FWRD",
    "EXEC",
    "NLP",
}

# Prefixes handled by Phase 26+ dedicated mappers (map_phase26_check)
# These checks bypass FIELD_FOR_CHECK and have their own routing logic.
PHASE26_PREFIXES: tuple[str, ...] = (
    "EXEC.",
    "NLP.",
    "FIN.TEMPORAL.",
    "FIN.FORENSIC.",
    "FIN.QUALITY.",
    "FWRD.",
)


def _has_phase26_mapper(signal_id: str) -> bool:
    """Check if a check ID is handled by a Phase 26+ dedicated mapper."""
    return any(signal_id.startswith(p) for p in PHASE26_PREFIXES)


def detect_gaps(
    checks: list[dict[str, Any]],
    manifest: AcquisitionManifest,
) -> GapReport:
    """Compare check requirements to pipeline capabilities.

    Three-level gap analysis:
      1. SOURCE: Is every required data source in ACQUIRED_SOURCES?
      2. FIELD: Does the check have field routing (field_key, FIELD_FOR_CHECK, or Phase 26+ mapper)?
      3. MAPPER: Does the check's prefix have a registered mapper handler?

    Args:
        checks: List of check dicts (from signals.json or BrainDBLoader).
        manifest: AcquisitionManifest built from the same checks.

    Returns:
        GapReport with all detected gaps, aggregated by type and severity.
    """
    from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

    report = GapReport(total_signals=0)

    for check in checks:
        if check.get("execution_mode") != "AUTO":
            continue

        report.total_signals += 1
        signal_id = check.get("id", "")
        signal_name = check.get("name", "")
        check_gaps: list[PipelineGap] = []

        # Level 1: Source availability (CRITICAL)
        for src in check.get("required_data", []):
            if src not in ACQUIRED_SOURCES:
                check_gaps.append(
                    PipelineGap(
                        signal_id=signal_id,
                        signal_name=signal_name,
                        gap_type="SOURCE_NOT_ACQUIRED",
                        detail=f"Required source '{src}' not in ACQUIRE capabilities",
                        severity="CRITICAL",
                    )
                )

        # Level 2: Field routing (WARNING)
        # A check has field routing if ANY of these is true:
        #   a) data_strategy.field_key is set (Phase 31 declarative)
        #   b) signal_id is in FIELD_FOR_CHECK (legacy routing)
        #   c) signal_id is handled by a Phase 26+ dedicated mapper
        ds = check.get("data_strategy", {})
        has_field_key = isinstance(ds, dict) and ds.get("field_key") is not None
        has_legacy_routing = signal_id in FIELD_FOR_CHECK
        has_p26_mapper = _has_phase26_mapper(signal_id)

        if not has_field_key and not has_legacy_routing and not has_p26_mapper:
            check_gaps.append(
                PipelineGap(
                    signal_id=signal_id,
                    signal_name=signal_name,
                    gap_type="NO_FIELD_ROUTING",
                    detail=(
                        "No data_strategy.field_key, no FIELD_FOR_CHECK entry, "
                        "and no Phase 26+ dedicated mapper"
                    ),
                    severity="WARNING",
                )
            )

        # Level 3: Mapper handler (INFO)
        prefix = signal_id.split(".")[0] if "." in signal_id else signal_id
        if prefix not in HANDLED_PREFIXES:
            check_gaps.append(
                PipelineGap(
                    signal_id=signal_id,
                    signal_name=signal_name,
                    gap_type="NO_MAPPER_HANDLER",
                    detail=f"Check prefix '{prefix}' has no registered mapper handler",
                    severity="INFO",
                )
            )

        if not check_gaps:
            report.fully_supported += 1
        report.gaps.extend(check_gaps)

    # Aggregate by type and severity
    for gap in report.gaps:
        report.by_type[gap.gap_type] = report.by_type.get(gap.gap_type, 0) + 1
        report.by_severity[gap.severity] = report.by_severity.get(gap.severity, 0) + 1

    return report


__all__ = [
    "ACQUIRED_SOURCES",
    "HANDLED_PREFIXES",
    "GapReport",
    "PipelineGap",
    "detect_gaps",
]
