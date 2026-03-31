"""Render coverage analysis framework.

Walks the AnalysisState model tree to identify all non-null leaf values,
then checks whether each appears in rendered output using format-aware
matching. Produces a coverage report listing uncovered field paths.

Used by the render coverage test (SC-1) to drive gap closure across
Plans 03-06.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Exclusion loading from YAML config
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "config" / "render_exclusions.yaml"


@functools.cache
def load_render_exclusions() -> dict[str, str]:
    """Load render exclusions from config/render_exclusions.yaml.

    Returns:
        Dict mapping field path prefixes to reason strings.
        Cached at module level after first call.
    """
    if not _CONFIG_PATH.exists():
        return {}
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    exclusions: dict[str, str] = {}
    for entry in data.get("exclusions", []):
        exclusions[entry["path"]] = entry["reason"]
    return exclusions


# ---------------------------------------------------------------------------
# Exclusion paths -- fields NOT expected in rendered output
# Deprecated: use load_render_exclusions() for the authoritative source.
# Kept for backward compatibility with existing tests.
# ---------------------------------------------------------------------------

EXCLUSION_PREFIXES: frozenset[str] = frozenset({
    # Raw acquisition data (internal only)
    "acquired_data",
    # Pipeline stage metadata
    "stages",
    # Schema metadata
    "version",
    "created_at",
    "updated_at",
    # Internal routing
    "active_playbook_id",
    # Individual check results rendered as summaries, not raw
    "analysis.signal_results",
    # Analysis aggregate counters (rendered as summaries / coverage stats)
    "analysis.checks_executed",
    "analysis.checks_passed",
    "analysis.checks_failed",
    "analysis.checks_skipped",
    "analysis.patterns_detected",
    # Governance sub-scores (internal computation, not displayed individually)
    "extracted.governance.governance_score",
    # Classification internal computation fields
    "classification.methodology",
    "classification.ddl_exposure_base_m",
    "classification.cap_filing_multiplier",
    "classification.ipo_multiplier",
    # Tier definition boundaries (internal reference, not rendered)
    "scoring.tier.score_range_low",
    "scoring.tier.score_range_high",
    # Financial statement internal metadata
    "extracted.financials.statements",
})

# SourcedValue metadata keys -- when a dict looks like a SourcedValue,
# we extract .value and skip the metadata fields
_SOURCED_VALUE_KEYS = {"value", "source", "confidence", "as_of", "retrieved_at"}

# Minimum required keys to identify a dict as a SourcedValue
_SOURCED_VALUE_REQUIRED = {"value", "source", "confidence"}


# ---------------------------------------------------------------------------
# State field walker
# ---------------------------------------------------------------------------


def _is_sourced_value(d: dict[str, Any]) -> bool:
    """Check if a dict looks like a serialized SourcedValue."""
    return _SOURCED_VALUE_REQUIRED.issubset(d.keys())


def _is_excluded(path: str) -> bool:
    """Check if a field path should be excluded from coverage analysis.

    Uses the YAML config (config/render_exclusions.yaml) as the
    authoritative source. Falls back to EXCLUSION_PREFIXES if YAML
    is unavailable.
    """
    exclusions = load_render_exclusions()
    prefixes = set(exclusions.keys()) if exclusions else EXCLUSION_PREFIXES
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix + ".") or path.startswith(prefix + "["):
            return True
    return False


def walk_state_values(
    state_dict: dict[str, Any],
    prefix: str = "",
) -> list[tuple[str, Any, type]]:
    """Walk a state dict tree and extract all non-null leaf values.

    Handles SourcedValue dicts by extracting the .value field.
    Skips None, empty collections, empty strings, and excluded paths.

    Args:
        state_dict: Dict from AnalysisState.model_dump(mode='python').
        prefix: Current path prefix for recursion.

    Returns:
        List of (field_path, value, value_type) tuples.
    """
    results: list[tuple[str, Any, type]] = []

    for key, value in state_dict.items():
        path = f"{prefix}.{key}" if prefix else key

        # Check exclusion before descending
        if _is_excluded(path):
            continue

        # Skip None
        if value is None:
            continue

        # Handle dict values
        if isinstance(value, dict):
            # Check if it's a SourcedValue
            if _is_sourced_value(value):
                inner = value["value"]
                if inner is None:
                    continue
                if isinstance(inner, str) and inner == "":
                    continue
                results.append((path, inner, type(inner)))
            elif len(value) == 0:
                continue
            else:
                # Recurse into nested dict
                results.extend(walk_state_values(value, prefix=path))
            continue

        # Handle lists
        if isinstance(value, list):
            if len(value) == 0:
                continue
            for i, item in enumerate(value):
                item_path = f"{path}[{i}]"
                if _is_excluded(item_path):
                    continue
                if item is None:
                    continue
                if isinstance(item, dict):
                    if _is_sourced_value(item):
                        inner = item["value"]
                        if inner is not None:
                            results.append((item_path, inner, type(inner)))
                    else:
                        results.extend(
                            walk_state_values(item, prefix=item_path)
                        )
                elif isinstance(item, str) and item == "":
                    continue
                else:
                    results.append((item_path, item, type(item)))
            continue

        # Skip empty strings
        if isinstance(value, str) and value == "":
            continue

        # Leaf value
        results.append((path, value, type(value)))

    return results


# ---------------------------------------------------------------------------
# Format-aware value matcher
# ---------------------------------------------------------------------------


def _format_compact(value: float) -> str:
    """Format a number in compact notation for matching."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1_000_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000_000:.1f}T"
    if abs_val >= 1_000_000_000:
        return f"{sign}{abs_val / 1_000_000_000:.1f}B"
    if abs_val >= 1_000_000:
        return f"{sign}{abs_val / 1_000_000:.1f}M"
    if abs_val >= 1_000:
        return f"{sign}{abs_val / 1_000:.1f}K"
    return f"{sign}{abs_val:.0f}"


def check_value_rendered(
    path: str,
    value: Any,
    text: str,
) -> bool:
    """Check whether a value appears in rendered text with format-aware matching.

    Tries multiple representations of the value:
    - For floats: raw string, compact notation ($NB), formatted currency
    - For ints: raw string and comma-formatted
    - For bools: "Yes"/"No" or "True"/"False"
    - For strings: case-insensitive substring match
    - For dates: ISO format and common display formats
    - For enums: the .value string

    Args:
        path: Field path (for context, not currently used in matching).
        value: The leaf value to search for.
        text: Rendered text to search in.

    Returns:
        True if the value appears in the text in any recognized format.
    """
    _ = path  # Reserved for path-specific matching heuristics

    if isinstance(value, bool):
        # Must check bool before int (bool is a subclass of int)
        if value:
            return "Yes" in text or "True" in text or "true" in text
        else:
            return "No" in text or "False" in text or "false" in text

    if isinstance(value, int):
        raw = str(value)
        # Check raw integer
        if raw in text:
            return True
        # Check comma-formatted integer
        formatted = f"{value:,}"
        if formatted in text:
            return True
        return False

    if isinstance(value, float):
        # Avoid matching tiny floats against unrelated numbers
        raw = str(value)
        # For very small floats (0-1 range), check multiple representations
        if abs(value) < 1.0:
            # Exact raw match with word boundaries
            if re.search(r'(?<!\d)' + re.escape(raw) + r'(?!\d)', text):
                return True
            # Percentage representation: 0.875 -> "87.5%" (must have % suffix
            # or be a non-round number to avoid false positives like 0.5 -> "50")
            pct_val = value * 100
            for decimals in range(3):
                pct_fmt = f"{pct_val:.{decimals}f}"
                # Always match with % suffix
                if pct_fmt + "%" in text:
                    return True
            # Match without % only if the percentage value has decimal places
            # (e.g., 87.5 is specific enough but 50 is too common)
            if pct_val != int(pct_val):
                pct_fmt_1d = f"{pct_val:.1f}"
                if re.search(
                    r'(?<!\d)' + re.escape(pct_fmt_1d) + r'(?!\d)', text
                ):
                    return True
            return False

        # Check raw float representation
        if raw in text:
            return True

        # Check common decimal representations
        for decimals in range(4):
            fmt = f"{value:.{decimals}f}"
            if fmt in text:
                return True

        # Check compact notation (391.0B, 3.0T, etc.)
        compact = _format_compact(value)
        if compact in text:
            return True

        # Check currency compact ($391.0B)
        if f"${compact}" in text:
            return True

        # Check comma-formatted
        comma_fmt = f"{value:,.0f}"
        if comma_fmt in text:
            return True

        # Check currency comma-formatted ($1,234,567)
        if f"${comma_fmt}" in text:
            return True

        return False

    if isinstance(value, datetime):
        # ISO format
        iso = value.strftime("%Y-%m-%d")
        if iso in text:
            return True
        # Slash format
        slash = value.strftime("%m/%d/%Y")
        if slash in text:
            return True
        # Month name formats
        for fmt in ("%b %d, %Y", "%B %d, %Y", "%b %Y"):
            try:
                formatted = value.strftime(fmt)
                if formatted in text:
                    return True
            except ValueError:
                continue
        return False

    if isinstance(value, date) and not isinstance(value, datetime):
        iso = value.strftime("%Y-%m-%d")
        if iso in text:
            return True
        slash = value.strftime("%m/%d/%Y")
        if slash in text:
            return True
        return False

    if isinstance(value, StrEnum):
        return value.value in text

    if isinstance(value, str):
        if not value:
            return False
        # Case-insensitive substring match
        return value.lower() in text.lower()

    # For any other type, try string conversion
    return str(value) in text


# ---------------------------------------------------------------------------
# Coverage report
# ---------------------------------------------------------------------------


@dataclass
class CoverageReport:
    """Result of a render coverage analysis."""

    total_fields: int = 0
    covered: int = 0
    uncovered_paths: list[str] = field(default_factory=list)
    coverage_pct: float = 0.0


def compute_coverage(
    state_dict: dict[str, Any],
    rendered_text: str,
) -> CoverageReport:
    """Compute render coverage for a state dict against rendered text.

    Walks the state tree, checks each non-null leaf value against the
    rendered text, and produces a coverage report.

    Args:
        state_dict: Dict from AnalysisState.model_dump(mode='python').
        rendered_text: The full rendered Markdown/HTML output string.

    Returns:
        CoverageReport with total fields, covered count, uncovered paths,
        and coverage percentage.
    """
    values = walk_state_values(state_dict)
    total = len(values)

    if total == 0:
        return CoverageReport()

    covered = 0
    uncovered: list[str] = []

    for path, value, _ in values:
        if check_value_rendered(path, value, rendered_text):
            covered += 1
        else:
            uncovered.append(path)

    return CoverageReport(
        total_fields=total,
        covered=covered,
        uncovered_paths=uncovered,
        coverage_pct=(covered / total * 100) if total > 0 else 0.0,
    )


__all__ = [
    "EXCLUSION_PREFIXES",
    "CoverageReport",
    "_is_excluded",
    "check_value_rendered",
    "compute_coverage",
    "load_render_exclusions",
    "walk_state_values",
]
