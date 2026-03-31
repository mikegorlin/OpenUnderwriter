"""Brain-to-acquisition requirement derivation.

Thin adapter that reads active signals from brain.duckdb at ACQUIRE startup,
builds an AcquisitionManifest describing what data sources and filing sections
the checks need, and provides post-acquisition validation.

Used by AcquireStage to make acquisition brain-aware (SC-1 closure).
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.knowledge.requirements import AcquisitionManifest, build_manifest

logger = logging.getLogger(__name__)


def derive_brain_requirements() -> AcquisitionManifest | None:
    """Load active signals from brain.duckdb and build an AcquisitionManifest.

    Returns None (with INFO log) if brain.duckdb is unavailable or any
    error occurs. ACQUIRE must never be blocked by brain failures.

    Returns:
        AcquisitionManifest if brain is available, else None.
    """
    try:
        # Lazy import to avoid circular imports and hard dependency on DuckDB
        from do_uw.brain.brain_unified_loader import BrainLoader

        loader = BrainLoader()
        checks_data: dict[str, Any] = loader.load_signals()
        checks_list: list[dict[str, Any]] = checks_data.get("signals", [])

        if not checks_list:
            logger.info("Brain returned no active checks; skipping manifest build")
            return None

        manifest = build_manifest(checks_list)

        # Log structured summary of brain requirements
        source_summary = ", ".join(
            f"{src} ({len(manifest.source_to_checks.get(src, []))} checks)"
            for src in sorted(manifest.required_sources)
        )
        logger.info(
            "Brain requires %d sources from %d active checks: %s",
            len(manifest.required_sources),
            manifest.total_signals,
            source_summary,
        )

        return manifest

    except Exception:
        logger.info(
            "Brain unavailable for requirement derivation; "
            "ACQUIRE will proceed without brain guidance",
            exc_info=True,
        )
        return None


def validate_acquisition_coverage(
    manifest: AcquisitionManifest, acquired_sources: set[str]
) -> dict[str, Any]:
    """Compare manifest requirements against actually acquired sources.

    Args:
        manifest: AcquisitionManifest with required sources.
        acquired_sources: Set of source type names actually fetched.

    Returns:
        Dict with keys: satisfied (list[str]), missing (list[str]),
        coverage_pct (float 0.0-100.0).
    """
    required = manifest.required_sources
    satisfied = sorted(required & acquired_sources)
    missing = sorted(required - acquired_sources)

    coverage_pct = (
        (len(satisfied) / len(required) * 100.0) if required else 100.0
    )

    for src in missing:
        signal_count = len(manifest.source_to_checks.get(src, []))
        logger.warning(
            "Brain requires source %s (%d signals depend on it) "
            "but ACQUIRE did not fetch it",
            src,
            signal_count,
        )

    if satisfied:
        logger.info(
            "Brain acquisition coverage: %.1f%% (%d/%d sources satisfied)",
            coverage_pct,
            len(satisfied),
            len(required),
        )

    return {
        "satisfied": satisfied,
        "missing": missing,
        "coverage_pct": coverage_pct,
    }


def log_section_requirements(manifest: AcquisitionManifest) -> None:
    """Log per-source section requirements from the manifest.

    For each source that has required_sections, logs the specific
    filing sections/fields needed and how many checks rely on them.

    Args:
        manifest: AcquisitionManifest with section-level requirements.
    """
    for src in sorted(manifest.required_sections):
        sections = sorted(manifest.required_sections[src])
        signal_count = len(manifest.source_to_checks.get(src, []))
        if sections:
            logger.info(
                "%s requires sections: %s (from %d signals)",
                src,
                ", ".join(sections),
                signal_count,
            )


__all__ = [
    "derive_brain_requirements",
    "log_section_requirements",
    "validate_acquisition_coverage",
]
