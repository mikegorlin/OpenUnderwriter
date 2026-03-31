"""XBRL coverage validation and tag discovery utilities.

Provides visibility into XBRL extraction quality per ticker:
- validate_coverage(): Reports per-concept tag resolution rates with alerts
- discover_tags(): Scans Company Facts for tag research when adding concepts

Usage:
    report = validate_coverage(facts, mapping, "AAPL")
    tags = discover_tags(facts, unit_filter="USD")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from do_uw.stages.extract.xbrl_mapping import (
    XBRLConcept,
    extract_concept_value,
)

logger = logging.getLogger(__name__)

# Alert threshold: statement types below this coverage get flagged.
LOW_COVERAGE_THRESHOLD: float = 60.0


@dataclass
class ConceptResolution:
    """Resolution result for a single XBRL concept."""

    concept_name: str
    resolved_tag: str | None
    tags_tried: int
    value_count: int


@dataclass
class CoverageReport:
    """Coverage validation report for a ticker's XBRL data."""

    ticker: str
    total_concepts: int
    resolved_concepts: int
    coverage_pct: float
    by_statement: dict[str, float]
    resolutions: list[ConceptResolution] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


def validate_coverage(
    facts: dict[str, Any],
    mapping: dict[str, XBRLConcept],
    ticker: str,
    form_type: str = "10-K",
) -> CoverageReport:
    """Validate XBRL extraction coverage for a ticker.

    For each non-derived concept in the mapping, attempts to resolve it
    against the Company Facts data. Tracks per-concept and per-statement
    resolution rates.

    Args:
        facts: Full companyfacts API response.
        mapping: Loaded XBRL concept mapping table.
        ticker: Company ticker for report identification.
        form_type: Filing type to filter by (default ``"10-K"``).

    Returns:
        CoverageReport with per-concept resolution details and alerts.
    """
    # Filter out derived concepts (they have no XBRL tags).
    active_concepts = {
        name: cfg
        for name, cfg in mapping.items()
        if cfg["statement"] != "derived"
    }

    resolutions: list[ConceptResolution] = []
    # Track per-statement counts: {statement: [total, resolved]}
    stmt_counts: dict[str, list[int]] = {}

    for concept_name, cfg in active_concepts.items():
        statement = cfg["statement"]
        if statement not in stmt_counts:
            stmt_counts[statement] = [0, 0]
        stmt_counts[statement][0] += 1

        tags = cfg["xbrl_tags"]
        tags_tried = len(tags)
        resolved_tag: str | None = None
        value_count = 0

        # Try each tag in priority order.
        for tag in tags:
            entries = extract_concept_value(
                facts, tag, form_type, cfg["unit"]
            )
            if entries:
                if resolved_tag is None or len(entries) > value_count:
                    resolved_tag = tag
                    value_count = len(entries)

        if resolved_tag is not None:
            stmt_counts[statement][1] += 1

        resolutions.append(
            ConceptResolution(
                concept_name=concept_name,
                resolved_tag=resolved_tag,
                tags_tried=tags_tried,
                value_count=value_count,
            )
        )

    # Compute totals.
    total = len(active_concepts)
    resolved = sum(1 for r in resolutions if r.resolved_tag is not None)
    coverage_pct = round(resolved / total * 100, 1) if total > 0 else 0.0

    # Compute per-statement coverage.
    by_statement: dict[str, float] = {}
    for stmt, (stmt_total, stmt_resolved) in stmt_counts.items():
        by_statement[stmt] = (
            round(stmt_resolved / stmt_total * 100, 1) if stmt_total > 0 else 0.0
        )

    # Generate alerts for low-coverage statements.
    alerts: list[str] = []
    for stmt, pct in by_statement.items():
        if pct < LOW_COVERAGE_THRESHOLD:
            alerts.append(
                f"{ticker} {stmt} coverage {pct}% is below "
                f"{LOW_COVERAGE_THRESHOLD}% threshold"
            )

    report = CoverageReport(
        ticker=ticker,
        total_concepts=total,
        resolved_concepts=resolved,
        coverage_pct=coverage_pct,
        by_statement=by_statement,
        resolutions=resolutions,
        alerts=alerts,
    )

    logger.info(
        "XBRL coverage for %s: %d/%d concepts (%.1f%%), statements: %s",
        ticker,
        resolved,
        total,
        coverage_pct,
        ", ".join(f"{s}={p}%" for s, p in sorted(by_statement.items())),
    )

    for alert in alerts:
        logger.warning("Coverage alert: %s", alert)

    return report


def discover_tags(
    facts: dict[str, Any],
    unit_filter: str | None = None,
) -> list[tuple[str, int, float | None]]:
    """Discover all XBRL concepts available in Company Facts data.

    Scans the us-gaap namespace and returns tag usage information.
    Useful for researching which tags a company uses when adding
    new concepts to the mapping.

    Args:
        facts: Full companyfacts API response.
        unit_filter: Optional unit type filter (e.g., ``"USD"``,
            ``"shares"``). If None, returns all units.

    Returns:
        List of (tag_name, value_count, latest_value) tuples,
        sorted by value_count descending.
    """
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    results: list[tuple[str, int, float | None]] = []

    for tag_name, concept_data in us_gaap.items():
        units = concept_data.get("units", {})

        for unit_key, entries in units.items():
            if unit_filter is not None and unit_key != unit_filter:
                continue

            if not entries:
                continue

            value_count = len(entries)

            # Get latest value by end date.
            sorted_entries = sorted(
                entries,
                key=lambda e: str(e.get("end", "")),
                reverse=True,
            )
            latest_value: float | None = None
            if sorted_entries:
                val = sorted_entries[0].get("val")
                if val is not None:
                    latest_value = float(val)

            results.append((tag_name, value_count, latest_value))

    # Sort by value_count descending.
    results.sort(key=lambda x: x[1], reverse=True)
    return results
