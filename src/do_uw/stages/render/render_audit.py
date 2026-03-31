"""Render audit engine (Phase 92 -- REND-01/REND-02).

Computes a render audit report by walking the state dict, checking each
field against rendered output and the exclusion config. Classifies every
field as: rendered, excluded-by-policy, or unrendered.

Exports:
    compute_render_audit, RenderAuditReport, ExcludedField
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from do_uw.stages.render.coverage import (
    check_value_rendered,
    load_render_exclusions,
    walk_state_values,
)
from do_uw.stages.render.health_check import HealthIssue, run_health_checks


@dataclass
class ExcludedField:
    """A field excluded from render coverage by policy."""

    path: str
    reason: str


@dataclass
class RenderAuditReport:
    """Result of a render audit analysis."""

    excluded_fields: list[ExcludedField] = field(default_factory=list)
    unrendered_fields: list[str] = field(default_factory=list)
    total_extracted: int = 0
    total_rendered: int = 0
    total_excluded: int = 0
    coverage_pct: float = 0.0
    health_issues: list[HealthIssue] = field(default_factory=list)


def _match_exclusion(path: str, exclusions: dict[str, str]) -> str | None:
    """Check if a field path matches any exclusion prefix.

    Returns the matching exclusion path (key) or None.
    """
    for prefix in exclusions:
        if path == prefix or path.startswith(prefix + ".") or path.startswith(prefix + "["):
            return prefix
    return None


def compute_render_audit(
    state_dict: dict[str, Any],
    rendered_text: str,
) -> RenderAuditReport:
    """Walk state, check each field against rendered text and exclusions.

    Uses walk_state_values from coverage.py for field extraction.
    Uses check_value_rendered for format-aware matching.
    Uses load_render_exclusions for policy exclusions.

    Classifies each field as: rendered, excluded-by-policy, or unrendered.

    Note: walk_state_values already skips excluded fields. To get a complete
    audit including excluded fields, we walk the state dict ourselves for
    the excluded portion.

    Args:
        state_dict: Dict from AnalysisState.model_dump(mode='python').
        rendered_text: The full rendered HTML output string.

    Returns:
        RenderAuditReport with excluded fields, unrendered fields, and counts.
    """
    exclusions = load_render_exclusions()

    # Walk all non-excluded, non-null leaf values (coverage.py already filters excluded)
    renderable_values = walk_state_values(state_dict)

    # Count excluded fields by walking the state dict and finding exclusion matches
    excluded_fields = _collect_excluded_fields(state_dict, exclusions)
    total_excluded = len(excluded_fields)

    # Check which renderable values appear in the rendered text
    rendered_count = 0
    unrendered: list[str] = []

    for path, value, _ in renderable_values:
        if check_value_rendered(path, value, rendered_text):
            rendered_count += 1
        else:
            unrendered.append(path)

    total_extracted = len(renderable_values) + total_excluded

    # Coverage percentage: rendered / (rendered + unrendered) -- excludes excluded fields
    renderable_total = len(renderable_values)
    coverage_pct = (rendered_count / renderable_total * 100) if renderable_total > 0 else 0.0

    # Run health checks if we have rendered content
    health_issues: list[HealthIssue] = []
    if rendered_text:
        health_report = run_health_checks(rendered_text, state_dict)
        health_issues = health_report.issues

    return RenderAuditReport(
        excluded_fields=excluded_fields,
        unrendered_fields=unrendered,
        total_extracted=total_extracted,
        total_rendered=rendered_count,
        total_excluded=total_excluded,
        coverage_pct=round(coverage_pct, 1),
        health_issues=health_issues,
    )


def _collect_excluded_fields(
    state_dict: dict[str, Any],
    exclusions: dict[str, str],
    prefix: str = "",
) -> list[ExcludedField]:
    """Walk state dict and collect fields that match exclusion prefixes.

    Only collects top-level exclusion matches (does not recurse into
    excluded subtrees). Returns one ExcludedField per matching prefix.
    """
    found: list[ExcludedField] = []
    seen_prefixes: set[str] = set()

    for key, value in state_dict.items():
        path = f"{prefix}.{key}" if prefix else key

        if value is None:
            continue

        match = _match_exclusion(path, exclusions)
        if match is not None and match not in seen_prefixes:
            seen_prefixes.add(match)
            found.append(ExcludedField(path=match, reason=exclusions[match]))
            continue

        # Recurse into non-excluded dicts
        if isinstance(value, dict) and len(value) > 0:
            found.extend(_collect_excluded_fields(value, exclusions, prefix=path))

    return found


__all__ = [
    "ExcludedField",
    "HealthIssue",
    "RenderAuditReport",
    "compute_render_audit",
]
