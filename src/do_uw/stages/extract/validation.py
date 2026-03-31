"""Extraction validation framework -- anti-imputation and completeness.

The CRITICAL trust mechanism for the extraction pipeline. Every extraction
operation must produce an ExtractionReport documenting what was expected,
found, and missing. This prevents the two known failure modes:
1. Silent incompleteness: extracting 3 of 12 items and calling it done
2. Silent imputation: generating data that doesn't exist in the source

Usage:
    report = create_report(
        extractor_name="income_statement",
        expected=["revenue", "net_income", "gross_profit"],
        found=["revenue", "net_income"],
        source_filing="10-K 2024-02-28 0001193125-24-012345",
    )
    log_report(report)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from do_uw.models.common import Confidence

logger = logging.getLogger(__name__)


@dataclass
class ExtractionReport:
    """Validation report for a single extraction operation.

    Documents completeness of extraction: what was expected vs. found.
    Every extraction function must produce one of these.
    """

    extractor_name: str
    expected_fields: list[str]
    found_fields: list[str]
    missing_fields: list[str]
    unexpected_fields: list[str]
    coverage_pct: float
    confidence: Confidence
    source_filing: str
    fallbacks_used: list[str] = field(default_factory=lambda: [])
    warnings: list[str] = field(default_factory=lambda: [])


def _compute_confidence(coverage_pct: float) -> Confidence:
    """Determine confidence level from extraction coverage percentage.

    Thresholds:
    - >= 80%: HIGH confidence
    - 50-79%: MEDIUM confidence
    - < 50%: LOW confidence
    """
    if coverage_pct >= 80.0:
        return Confidence.HIGH
    if coverage_pct >= 50.0:
        return Confidence.MEDIUM
    return Confidence.LOW


def create_report(
    extractor_name: str,
    expected: list[str],
    found: list[str],
    source_filing: str,
    fallbacks_used: list[str] | None = None,
    warnings: list[str] | None = None,
    unexpected: list[str] | None = None,
) -> ExtractionReport:
    """Create an ExtractionReport with computed derived fields.

    Args:
        extractor_name: Name of the extractor (e.g., "income_statement").
        expected: List of expected field names.
        found: List of actually found field names.
        source_filing: Filing reference (type + date + accession).
        fallbacks_used: Optional list of fallback strategies employed.
        warnings: Optional list of warnings detected during extraction.
        unexpected: Optional list of unexpected fields found.

    Returns:
        ExtractionReport with coverage and confidence computed.
    """
    expected_set = set(expected)
    found_set = set(found)

    missing = sorted(expected_set - found_set)
    unexpected_fields = sorted(
        set(unexpected or []) | (found_set - expected_set)
    )

    coverage = (
        (len(found_set & expected_set) / len(expected_set) * 100.0)
        if expected_set
        else 100.0
    )

    confidence = _compute_confidence(coverage)

    return ExtractionReport(
        extractor_name=extractor_name,
        expected_fields=sorted(expected_set),
        found_fields=sorted(found_set),
        missing_fields=missing,
        unexpected_fields=unexpected_fields,
        coverage_pct=round(coverage, 1),
        confidence=confidence,
        source_filing=source_filing,
        fallbacks_used=fallbacks_used or [],
        warnings=warnings or [],
    )


def validate_no_imputation(
    extracted_values: dict[str, Any],
    source_values: dict[str, Any],
) -> list[str]:
    """Verify that all extracted values exist in the source data.

    Checks that no value was fabricated or imputed. Returns a list
    of field names where extracted data has no source backing.

    Args:
        extracted_values: Fields extracted and their values.
        source_values: Fields present in the source filing.

    Returns:
        List of field names that appear in extracted but not in source
        (potential imputation violations).
    """
    source_keys = set(source_values.keys())
    extracted_keys = set(extracted_values.keys())
    return sorted(extracted_keys - source_keys)


def merge_reports(reports: list[ExtractionReport]) -> ExtractionReport:
    """Merge multiple extraction reports into a single summary report.

    Combines all expected, found, missing, and unexpected fields.
    Recalculates coverage and confidence from merged totals.

    Args:
        reports: List of ExtractionReport instances to merge.

    Returns:
        A merged ExtractionReport summarizing all sub-reports.

    Raises:
        ValueError: If reports list is empty.
    """
    if not reports:
        msg = "Cannot merge empty list of reports"
        raise ValueError(msg)

    all_expected: set[str] = set()
    all_found: set[str] = set()
    all_unexpected: set[str] = set()
    all_fallbacks: list[str] = []
    all_warnings: list[str] = []
    sources: list[str] = []

    for report in reports:
        all_expected.update(report.expected_fields)
        all_found.update(report.found_fields)
        all_unexpected.update(report.unexpected_fields)
        all_fallbacks.extend(report.fallbacks_used)
        all_warnings.extend(report.warnings)
        sources.append(report.source_filing)

    missing = sorted(all_expected - all_found)
    coverage = (
        (len(all_found & all_expected) / len(all_expected) * 100.0)
        if all_expected
        else 100.0
    )
    confidence = _compute_confidence(coverage)

    extractor_names = [r.extractor_name for r in reports]
    merged_name = "+".join(extractor_names)

    return ExtractionReport(
        extractor_name=merged_name,
        expected_fields=sorted(all_expected),
        found_fields=sorted(all_found),
        missing_fields=missing,
        unexpected_fields=sorted(all_unexpected),
        coverage_pct=round(coverage, 1),
        confidence=confidence,
        source_filing="; ".join(dict.fromkeys(sources)),
        fallbacks_used=all_fallbacks,
        warnings=all_warnings,
    )


def log_report(report: ExtractionReport) -> None:
    """Log extraction report at appropriate level.

    WARNING if coverage < 50%, INFO otherwise.

    Args:
        report: The extraction report to log.
    """
    found_count = len(set(report.found_fields) & set(report.expected_fields))
    total_count = len(report.expected_fields)

    msg = (
        "Extraction [%s]: %d/%d fields (%.1f%% coverage, %s confidence) "
        "from %s"
    )
    args = (
        report.extractor_name,
        found_count,
        total_count,
        report.coverage_pct,
        report.confidence.value,
        report.source_filing,
    )

    if report.coverage_pct < 50.0:
        logger.warning(msg, *args)
        if report.missing_fields:
            logger.warning(
                "  Missing fields: %s", ", ".join(report.missing_fields)
            )
    else:
        logger.info(msg, *args)

    if report.fallbacks_used:
        logger.info(
            "  Fallbacks used: %s", ", ".join(report.fallbacks_used)
        )
    if report.warnings:
        for warning in report.warnings:
            logger.warning("  Warning: %s", warning)
