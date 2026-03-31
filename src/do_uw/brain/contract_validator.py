"""Contract validation for facet-template-signal agreement.

Phase 79 Plan 01: Validates that the output manifest, Jinja2 templates on disk,
and brain signal YAML files are in agreement. Catches broken chains at CI time.

Three validators:
1. validate_facet_template_agreement - templates exist and no orphans
2. validate_signal_references - signal IDs in facets exist in brain YAML
3. validate_all_contracts - aggregator that runs both and returns a report
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field

from do_uw.brain.manifest_schema import OutputManifest, load_manifest


class DataWarning(BaseModel):
    """A warning about missing data for a facet's requires declaration.

    Unlike ContractViolation, these are informational warnings -- the pipeline
    should still render, but the facet may produce incomplete output.
    """

    model_config = ConfigDict(extra="forbid")

    facet_id: str = Field(
        ...,
        description="Facet ID that requires this data",
    )
    section_id: str = Field(
        ...,
        description="Section ID containing the facet",
    )
    field_path: str = Field(
        ...,
        description="Dot-notation field path that is missing or empty",
    )
    detail: str = Field(
        ...,
        description="Human-readable description of what data is expected",
    )


class ContractViolation(BaseModel):
    """A single contract violation between manifest, templates, and signals."""

    model_config = ConfigDict(extra="forbid")

    violation_type: str = Field(
        ...,
        description="Type: missing_template, orphaned_template, broken_signal_reference",
    )
    section_id: str = Field(
        default="",
        description="Section ID where the violation occurred",
    )
    facet_id: str = Field(
        default="",
        description="Facet ID where the violation occurred (empty for section-level)",
    )
    detail: str = Field(
        ...,
        description="Human-readable description with actionable context",
    )


class ContractReport(BaseModel):
    """Result of running all contract validators."""

    model_config = ConfigDict(extra="forbid")

    valid: bool = Field(
        ...,
        description="True if no violations found",
    )
    violations: list[ContractViolation] = Field(
        default_factory=list,
        description="All violations found across validators",
    )


def validate_facet_template_agreement(
    manifest: OutputManifest,
    template_root: Path,
    *,
    exclude_orphans: set[str] | None = None,
) -> list[ContractViolation]:
    """Check that manifest templates exist on disk and no templates are orphaned.

    Args:
        manifest: Loaded output manifest.
        template_root: Root directory for HTML templates (e.g. src/do_uw/templates/html/).
        exclude_orphans: Optional set of relative template paths to exclude from
            orphan detection (e.g. known legacy templates not yet in manifest).

    Returns:
        List of violations (empty if all agree).
    """
    violations: list[ContractViolation] = []

    # Collect all template paths declared in the manifest
    declared_templates: set[str] = set()

    for section in manifest.sections:
        # Check section wrapper template
        section_path = template_root / section.template
        declared_templates.add(section.template)
        if not section_path.exists():
            violations.append(
                ContractViolation(
                    violation_type="missing_template",
                    section_id=section.id,
                    facet_id="",
                    detail=(
                        f"Section '{section.id}' references template "
                        f"'{section.template}' which does not exist at "
                        f"{section_path}"
                    ),
                )
            )

        # Check group templates (v3) or facet templates (legacy)
        # Use groups if present (preferred); fall back to facets
        sub_items = section.groups if section.groups else section.facets
        for item in sub_items:
            item_path = template_root / item.template
            declared_templates.add(item.template)
            if not item_path.exists():
                label = "Group" if section.groups else "Facet"
                violations.append(
                    ContractViolation(
                        violation_type="missing_template",
                        section_id=section.id,
                        facet_id=item.id,
                        detail=(
                            f"{label} '{section.id}/{item.id}' references template "
                            f"'{item.template}' which does not exist at "
                            f"{item_path}"
                        ),
                    )
                )

    # Scan for orphaned templates in sections/ subdirectories
    excluded = exclude_orphans or set()
    sections_dir = template_root / "sections"
    if sections_dir.exists():
        for j2_file in sections_dir.rglob("*.html.j2"):
            rel_path = str(j2_file.relative_to(template_root))
            if rel_path not in declared_templates and rel_path not in excluded:
                violations.append(
                    ContractViolation(
                        violation_type="orphaned_template",
                        section_id="",
                        facet_id="",
                        detail=(
                            f"Template '{rel_path}' exists on disk but is not "
                            f"declared in any manifest section or facet"
                        ),
                    )
                )

    return violations


def validate_signal_references(
    manifest: OutputManifest,
    signals_by_id: set[str],
) -> list[ContractViolation]:
    """Check that all signal IDs referenced by facets exist in brain YAML.

    Facets with empty signals lists are valid (data-display-only).

    Args:
        manifest: Loaded output manifest.
        signals_by_id: Set of all known signal IDs from brain YAML.

    Returns:
        List of violations (empty if all signal references are valid).
    """
    violations: list[ContractViolation] = []

    # Check facet signal lists (legacy path: facets embed signal IDs)
    for section in manifest.sections:
        for facet in section.facets:
            for signal_id in facet.signals:
                if signal_id not in signals_by_id:
                    violations.append(
                        ContractViolation(
                            violation_type="broken_signal_reference",
                            section_id=section.id,
                            facet_id=facet.id,
                            detail=(
                                f"Facet '{section.id}/{facet.id}' references signal "
                                f"'{signal_id}' which does not exist in brain YAML"
                            ),
                        )
                    )

    # V3 path: also check that signals with groups reference valid manifest groups
    manifest_group_ids = {g.id for s in manifest.sections for g in s.groups}
    if manifest_group_ids and signals_by_id:
        from do_uw.brain.brain_unified_loader import load_signals

        try:
            sigs = load_signals()["signals"]
        except Exception:
            sigs = []
        for sig in sigs:
            if sig["id"] not in signals_by_id:
                continue  # Only check signals in the provided set
            gid = sig.get("group", "")
            if gid and gid not in manifest_group_ids:
                violations.append(
                    ContractViolation(
                        violation_type="broken_signal_reference",
                        section_id="",
                        facet_id=gid,
                        detail=(
                            f"Signal '{sig['id']}' references group "
                            f"'{gid}' which does not exist in manifest"
                        ),
                    )
                )

    return violations


def _load_signal_ids_from_dir(signals_dir: Path) -> set[str]:
    """Load all signal IDs from YAML files in a directory.

    Supports both formats:
    - Flat list of dicts with 'id' key
    - Dict with 'signals' key containing list of dicts with 'id' key
    """
    signal_ids: set[str] = set()

    if not signals_dir.exists():
        return signal_ids

    for yaml_file in sorted(signals_dir.rglob("*.yaml")):
        try:
            raw = yaml.safe_load(yaml_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if raw is None:
            continue

        # Handle dict with 'signals' key
        if isinstance(raw, dict) and "signals" in raw:
            entries = raw["signals"]
        elif isinstance(raw, list):
            entries = raw
        else:
            continue

        if isinstance(entries, list):
            for entry in entries:
                if isinstance(entry, dict) and "id" in entry:
                    signal_ids.add(entry["id"])

    return signal_ids


def validate_all_contracts(
    manifest_path: Path,
    template_root: Path,
    signals_dir: Path,
) -> ContractReport:
    """Run all contract validators and produce an aggregate report.

    Args:
        manifest_path: Path to output_manifest.yaml.
        template_root: Root directory for HTML templates.
        signals_dir: Directory containing brain signal YAML files.

    Returns:
        ContractReport with valid=True if no violations, else all violations.
    """
    manifest = load_manifest(manifest_path)
    signal_ids = _load_signal_ids_from_dir(signals_dir)

    violations: list[ContractViolation] = []
    violations.extend(validate_facet_template_agreement(manifest, template_root))
    violations.extend(validate_signal_references(manifest, signal_ids))

    return ContractReport(
        valid=len(violations) == 0,
        violations=violations,
    )


def _resolve_field_path(context: dict[str, Any], path: str) -> Any:
    """Resolve a dot-notation field path against a nested dict.

    Returns the value at the path, or a sentinel _MISSING if any key
    along the path does not exist.
    """
    current: Any = context
    for key in path.split("."):
        if not isinstance(current, dict) or key not in current:
            return _MISSING
        current = current[key]
    return current


# Sentinel for missing keys (distinct from None)
_MISSING = object()


def _is_populated(value: Any) -> bool:
    """Check whether a value counts as 'populated'.

    None, empty list, empty dict, empty string, and missing keys
    all count as not populated. Everything else is populated.
    """
    if value is _MISSING or value is None:
        return False
    if isinstance(value, (list, dict, str)) and len(value) == 0:
        return False
    return True


def validate_requires_populated(
    manifest: OutputManifest,
    context: dict[str, Any],
) -> list[DataWarning]:
    """Check whether required data fields are populated in the render context.

    This is a WARNING system, not a hard failure. The pipeline should still
    render; this function identifies facets that may produce incomplete output.

    Args:
        manifest: Loaded output manifest with requires annotations.
        context: The render context dict (from build_html_context).

    Returns:
        List of DataWarning for each facet/field combination that is missing.
    """
    warnings: list[DataWarning] = []

    for section in manifest.sections:
        # Use groups (v3) or facets (legacy)
        items = section.groups if section.groups else section.facets
        for item in items:
            for field_path in item.requires:
                value = _resolve_field_path(context, field_path)
                if not _is_populated(value):
                    warnings.append(
                        DataWarning(
                            facet_id=item.id,
                            section_id=section.id,
                            field_path=field_path,
                            detail=(
                                f"Group '{section.id}/{item.id}' requires "
                                f"'{field_path}' but it is missing or empty "
                                f"in the render context"
                            ),
                        )
                    )

    return warnings


__all__ = [
    "ContractReport",
    "ContractViolation",
    "DataWarning",
    "validate_all_contracts",
    "validate_facet_template_agreement",
    "validate_requires_populated",
    "validate_signal_references",
]
