"""Requirements analysis: derive acquisition manifest from check declarations.

Reads all check definitions and produces a structured AcquisitionManifest
describing what data sources, filing sections, and field keys the pipeline
needs to satisfy every check.

Used by PipelineGapDetector (gap_detector.py) and as a standalone
diagnostic tool via the Brain CLI (Plan 07).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AcquisitionManifest(BaseModel):
    """Structured requirements derived from check declarations.

    Built by build_manifest() from the full check corpus. Describes
    what the pipeline needs to acquire and extract to satisfy all checks.
    """

    required_sources: set[str] = Field(default_factory=set)
    """Source types needed (SEC_10K, MARKET_PRICE, etc.)."""

    required_sections: dict[str, set[str]] = Field(default_factory=dict)
    """Per-source section requirements, e.g. {"SEC_10K": {"item_1a", ...}}."""

    source_to_checks: dict[str, list[str]] = Field(default_factory=dict)
    """Which check IDs depend on each source type."""

    checks_by_depth: dict[int, int] = Field(default_factory=dict)
    """Distribution of checks by depth level (1=DISPLAY, 2=COMPUTE, 3=INFER, 4=HUNT)."""

    checks_by_content_type: dict[str, int] = Field(default_factory=dict)
    """Distribution of checks by content type (EVALUATIVE_CHECK, MANAGEMENT_DISPLAY, INFERENCE_PATTERN)."""

    total_signals: int = 0
    """Total checks analyzed (AUTO-mode only)."""

    model_config = {"arbitrary_types_allowed": True}


def build_manifest(checks: list[dict[str, Any]]) -> AcquisitionManifest:
    """Build acquisition manifest from enriched check definitions.

    Filters to execution_mode == "AUTO" checks only. For each check,
    reads required_data (list of source types) and data_locations
    (dict of source -> sections), then aggregates into the manifest.

    Args:
        checks: List of check dicts from signals.json or BrainDBLoader.

    Returns:
        AcquisitionManifest with all requirements aggregated.
    """
    required_sources: set[str] = set()
    required_sections: dict[str, set[str]] = {}
    source_to_checks: dict[str, list[str]] = {}
    checks_by_depth: dict[int, int] = {}
    checks_by_content_type: dict[str, int] = {}
    auto_count = 0

    for check in checks:
        if check.get("execution_mode") != "AUTO":
            continue

        auto_count += 1
        signal_id = check.get("id", "")
        depth = check.get("depth", 2)
        content_type = check.get("content_type", "EVALUATIVE_CHECK")

        # Count distributions
        checks_by_depth[depth] = checks_by_depth.get(depth, 0) + 1
        checks_by_content_type[content_type] = (
            checks_by_content_type.get(content_type, 0) + 1
        )

        # Source requirements from required_data
        for src in check.get("required_data", []):
            required_sources.add(src)
            source_to_checks.setdefault(src, []).append(signal_id)

            # Section-level requirements from data_locations
            data_locs = check.get("data_locations", {})
            if isinstance(data_locs, dict):
                sections = data_locs.get(src, [])
                if isinstance(sections, list):
                    required_sections.setdefault(src, set()).update(sections)

    return AcquisitionManifest(
        required_sources=required_sources,
        required_sections=required_sections,
        source_to_checks=source_to_checks,
        checks_by_depth=checks_by_depth,
        checks_by_content_type=checks_by_content_type,
        total_signals=auto_count,
    )


__all__ = ["AcquisitionManifest", "build_manifest"]
