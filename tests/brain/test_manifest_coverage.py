"""CI contract test: manifest-to-template coverage.

Validates that every group in the output manifest has a corresponding
template file on disk. Complements test_template_facet_audit.py which
tests from the template-side; this tests from the manifest-side.

Phase 100-03: CI contract tests for brain portability.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from do_uw.brain.manifest_schema import load_manifest

# Templates base directory
_TEMPLATES_BASE = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "templates" / "html"


def _collect_group_entries() -> list[tuple[str, str, str]]:
    """Collect (section_id, group_id, template_path) for all manifest groups."""
    manifest = load_manifest()
    entries: list[tuple[str, str, str]] = []
    for section in manifest.sections:
        for group in section.groups:
            if group.template:
                entries.append((section.id, group.id, group.template))
    return entries


@pytest.mark.parametrize(
    "section_id,group_id,template_path",
    _collect_group_entries(),
    ids=[f"{s}-{g}" for s, g, _ in _collect_group_entries()],
)
def test_manifest_group_template_exists(
    section_id: str, group_id: str, template_path: str
) -> None:
    """Every manifest group template must resolve to an existing file on disk."""
    full_path = _TEMPLATES_BASE / template_path
    assert full_path.exists(), (
        f"Manifest group '{group_id}' in section '{section_id}' references "
        f"template '{template_path}' which does not exist at {full_path}"
    )


def test_manifest_section_templates_exist() -> None:
    """Every section-level template must exist on disk."""
    manifest = load_manifest()
    missing: list[str] = []
    for section in manifest.sections:
        if section.template:
            full_path = _TEMPLATES_BASE / section.template
            if not full_path.exists():
                missing.append(f"  {section.id}: {section.template}")

    assert not missing, (
        f"Section templates missing on disk:\n" + "\n".join(missing)
    )


def test_manifest_has_minimum_sections() -> None:
    """Guard against manifest being accidentally truncated.

    As of v6.0 there are 13 sections in the manifest.
    """
    manifest = load_manifest()
    assert len(manifest.sections) >= 10, (
        f"Expected at least 10 manifest sections, found {len(manifest.sections)}. "
        "Manifest may have been truncated."
    )


def test_manifest_group_count_minimum() -> None:
    """Guard against losing manifest groups during refactoring.

    As of v6.0 there are 100+ groups across all sections.
    """
    manifest = load_manifest()
    total_groups = sum(len(s.groups) for s in manifest.sections)
    assert total_groups >= 80, (
        f"Expected at least 80 manifest groups, found {total_groups}. "
        "Groups may have been lost during refactoring."
    )
