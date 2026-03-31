"""CI tests for template-facet integrity.

Validates that:
1. Every group template reference resolves to an existing file on disk.
2. Every section-level template file is either group-referenced or a known wrapper.
3. All wrapper templates exist on disk.
4. All sections have at least one group.
5. Group IDs are unique within each section.

Phase 84-04: Migrated from section YAML to manifest groups.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from do_uw.brain.manifest_schema import load_manifest

# Paths
_TEMPLATES_BASE = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "templates" / "html"
_TEMPLATES_SECTIONS = _TEMPLATES_BASE / "sections"

# Section-level wrapper templates that are NOT referenced by groups but are valid
# (they wrap/include group templates). These are the top-level section entry points.
WRAPPER_TEMPLATES: set[str] = {
    # Active section-level wrappers (referenced by manifest sections)
    "sections/company.html.j2",
    "sections/governance.html.j2",
    "sections/litigation.html.j2",
    "sections/market.html.j2",
    "sections/financial.html.j2",
    "sections/scoring.html.j2",
    "sections/executive.html.j2",
    "sections/ai_risk.html.j2",
    "sections/red_flags.html.j2",
    "sections/identity.html.j2",
    "sections/forward_looking.html.j2",
    # Legacy wrapper/section templates (on disk, not in manifest groups)
    "sections/cover.html.j2",
    "sections/financial_statements.html.j2",
    "sections/scoring_hazard.html.j2",
    "sections/scoring_perils.html.j2",
    "sections/scoring_peril_map.html.j2",
    "sections/dossier.html.j2",
    "sections/adversarial_critique.html.j2",
    "sections/alt_data.html.j2",
    "sections/alt_data/esg_risk.html.j2",
    "sections/alt_data/ai_washing.html.j2",
    "sections/alt_data/tariff_exposure.html.j2",
    "sections/alt_data/peer_sca.html.j2",
    # Standalone/utility templates (not section wrappers, not group fragments)
    "sections/crf_banner.html.j2",
    "sections/decision_record.html.j2",
    "sections/executive_brief.html.j2",
    "sections/key_stats.html.j2",
    "sections/scorecard.html.j2",
    "sections/trigger_matrix.html.j2",
    "sections/governance/governance_score_breakdown.html.j2",
    "sections/governance/tenure_distribution.html.j2",
    "sections/litigation/litigation_dashboard.html.j2",
    "sections/litigation/regulatory_proceedings.html.j2",
    "sections/scoring/factor_detail.html.j2",
    # UW analysis parent + per-section decomposition (included via {% include %})
    "sections/uw_analysis.html.j2",
    "sections/report/page0_dashboard.html.j2",
    "sections/report/exec_brief.html.j2",
    "sections/report/company.html.j2",
    "sections/report/stock_market.html.j2",
    "sections/report/financial.html.j2",
    "sections/report/governance.html.j2",
    "sections/report/litigation.html.j2",
    "sections/report/forward_looking.html.j2",
    "sections/report/sector_industry.html.j2",
    "sections/report/scoring.html.j2",
    "sections/report/meeting_prep.html.j2",
    "sections/report/audit_trail.html.j2",
}


def _load_manifest_sections() -> list:
    """Load all sections from the output manifest."""
    manifest = load_manifest()
    return manifest.sections


def _collect_group_templates(sections: list) -> set[str]:
    """Collect all template paths referenced by groups across all sections."""
    templates: set[str] = set()
    for section in sections:
        for group in section.groups:
            if group.template:
                templates.add(group.template)
    return templates


def _collect_disk_templates() -> set[str]:
    """Collect all *.html.j2 files under templates/html/sections/ as relative paths."""
    templates: set[str] = set()
    for path in _TEMPLATES_SECTIONS.rglob("*.html.j2"):
        rel = path.relative_to(_TEMPLATES_BASE)
        templates.add(str(rel))
    return templates


# ---------- Fixtures ----------

@pytest.fixture(scope="module")
def manifest_sections():
    return _load_manifest_sections()


@pytest.fixture(scope="module")
def group_templates(manifest_sections):
    return _collect_group_templates(manifest_sections)


@pytest.fixture(scope="module")
def disk_templates():
    return _collect_disk_templates()


# ---------- Test 1: No dangling group template references ----------

def _dangling_params():
    """Generate (section_id, group_id, template) tuples for parametrize."""
    sections = _load_manifest_sections()
    params = []
    for section in sections:
        for group in section.groups:
            if group.template:
                params.append((section.id, group.id, group.template))
    return params


@pytest.mark.parametrize("section_id,group_id,template", _dangling_params())
def test_no_dangling_group_templates(section_id: str, group_id: str, template: str) -> None:
    """Every group template reference must resolve to an existing file."""
    full_path = _TEMPLATES_BASE / template
    assert full_path.exists(), (
        f"Dangling template reference in section '{section_id}', "
        f"group '{group_id}': {template} does not exist at {full_path}"
    )


# ---------- Test 2: No orphaned section templates ----------

def test_no_orphaned_group_templates(group_templates: set[str], disk_templates: set[str]) -> None:
    """Every non-wrapper template on disk must be referenced by at least one group."""
    orphaned = disk_templates - group_templates - WRAPPER_TEMPLATES
    assert not orphaned, (
        f"Orphaned templates (not referenced by any group and not a wrapper): "
        f"{sorted(orphaned)}"
    )


# ---------- Test 3: Wrapper templates exist on disk ----------

@pytest.mark.parametrize("wrapper", sorted(WRAPPER_TEMPLATES))
def test_wrapper_templates_exist(wrapper: str) -> None:
    """Every template in WRAPPER_TEMPLATES must exist on disk."""
    full_path = _TEMPLATES_BASE / wrapper
    assert full_path.exists(), (
        f"Stale wrapper entry: {wrapper} does not exist at {full_path}"
    )


# ---------- Test 4: All sections have groups ----------

# Structural sections that render as single template blocks without signal groups.
# These are non-signal sections (identity, cover, sources, etc.)
STRUCTURAL_SECTIONS: set[str] = {
    "coverage",
    "identity",
    "meeting_prep",
    "qa_audit",
    "sources",
}


def test_all_signal_sections_have_groups(manifest_sections: list) -> None:
    """Every signal-bearing section must have at least one group defined.

    Structural sections (identity, sources, etc.) are exempt -- they render
    as single template blocks without brain signal grouping.
    """
    empty = [
        s.id for s in manifest_sections
        if not s.groups and s.id not in STRUCTURAL_SECTIONS
    ]
    assert not empty, (
        f"Signal sections with no groups defined: {sorted(empty)}"
    )


# ---------- Test 5: Group IDs unique within section ----------

def test_group_ids_unique_within_section(manifest_sections: list) -> None:
    """Within each section, all group IDs must be unique."""
    duplicates: dict[str, list[str]] = {}
    for section in manifest_sections:
        ids = [g.id for g in section.groups]
        seen: set[str] = set()
        dupes: list[str] = []
        for gid in ids:
            if gid in seen:
                dupes.append(gid)
            seen.add(gid)
        if dupes:
            duplicates[section.id] = dupes
    assert not duplicates, (
        f"Duplicate group IDs within sections: {duplicates}"
    )
