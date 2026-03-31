"""Contract enforcement tests for facet-template-signal agreement.

Phase 79 Plan 01: CI test suite that catches broken facet-template-signal
chains at build time rather than discovering them in production output.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from do_uw.brain.contract_validator import (
    ContractReport,
    ContractViolation,
    validate_all_contracts,
    validate_facet_template_agreement,
    validate_signal_references,
)
from do_uw.brain.manifest_schema import (
    ManifestFacet,
    ManifestSection,
    OutputManifest,
)


# ---------------------------------------------------------------
# Fixtures: tmp manifest, templates, signals
# ---------------------------------------------------------------


def _make_facet(
    fid: str = "f1",
    template: str = "sections/sec1/f1.html.j2",
    signals: list[str] | None = None,
) -> ManifestFacet:
    return ManifestFacet(
        id=fid,
        name=f"Facet {fid}",
        template=template,
        data_type="extract_display",
        render_as="kv_table",
        signals=signals or [],
    )


def _make_section(
    sid: str = "sec1",
    template: str = "sections/sec1.html.j2",
    facets: list[ManifestFacet] | None = None,
) -> ManifestSection:
    return ManifestSection(
        id=sid,
        name=f"Section {sid}",
        template=template,
        render_mode="required",
        facets=facets or [],
    )


def _make_manifest(sections: list[ManifestSection]) -> OutputManifest:
    return OutputManifest(manifest_version="1.0", sections=sections)


@pytest.fixture()
def tmp_template_root(tmp_path: Path) -> Path:
    """Create a temporary template root with a sections/ subdir."""
    root = tmp_path / "templates" / "html"
    root.mkdir(parents=True)
    return root


# ---------------------------------------------------------------
# Unit tests: validate_facet_template_agreement
# ---------------------------------------------------------------


class TestFacetTemplateAgreement:
    """Tests for validate_facet_template_agreement."""

    def test_happy_path_no_violations(self, tmp_template_root: Path) -> None:
        """All templates exist, no orphans -> zero violations."""
        # Create section wrapper + facet template
        sec_dir = tmp_template_root / "sections" / "sec1"
        sec_dir.mkdir(parents=True)
        (tmp_template_root / "sections" / "sec1.html.j2").touch()
        (sec_dir / "f1.html.j2").touch()

        facet = _make_facet("f1", "sections/sec1/f1.html.j2")
        section = _make_section("sec1", "sections/sec1.html.j2", [facet])
        manifest = _make_manifest([section])

        violations = validate_facet_template_agreement(manifest, tmp_template_root)
        assert violations == []

    def test_missing_facet_template(self, tmp_template_root: Path) -> None:
        """Facet references a template that does not exist on disk."""
        sec_dir = tmp_template_root / "sections" / "sec1"
        sec_dir.mkdir(parents=True)
        (tmp_template_root / "sections" / "sec1.html.j2").touch()
        # Do NOT create the facet template

        facet = _make_facet("f1", "sections/sec1/f1.html.j2")
        section = _make_section("sec1", "sections/sec1.html.j2", [facet])
        manifest = _make_manifest([section])

        violations = validate_facet_template_agreement(manifest, tmp_template_root)
        assert len(violations) == 1
        v = violations[0]
        assert v.violation_type == "missing_template"
        assert v.facet_id == "f1"
        assert "f1.html.j2" in v.detail

    def test_missing_section_template(self, tmp_template_root: Path) -> None:
        """Section references a template that does not exist on disk."""
        sec_dir = tmp_template_root / "sections" / "sec1"
        sec_dir.mkdir(parents=True)
        (sec_dir / "f1.html.j2").touch()
        # Do NOT create section wrapper template

        facet = _make_facet("f1", "sections/sec1/f1.html.j2")
        section = _make_section("sec1", "sections/sec1.html.j2", [facet])
        manifest = _make_manifest([section])

        violations = validate_facet_template_agreement(manifest, tmp_template_root)
        assert len(violations) >= 1
        missing = [v for v in violations if v.violation_type == "missing_template"]
        assert any("sec1.html.j2" in v.detail for v in missing)

    def test_orphaned_template(self, tmp_template_root: Path) -> None:
        """Template on disk not declared in manifest -> orphan violation."""
        sec_dir = tmp_template_root / "sections" / "sec1"
        sec_dir.mkdir(parents=True)
        (tmp_template_root / "sections" / "sec1.html.j2").touch()
        (sec_dir / "f1.html.j2").touch()
        (sec_dir / "orphan.html.j2").touch()  # Not in manifest

        facet = _make_facet("f1", "sections/sec1/f1.html.j2")
        section = _make_section("sec1", "sections/sec1.html.j2", [facet])
        manifest = _make_manifest([section])

        violations = validate_facet_template_agreement(manifest, tmp_template_root)
        orphans = [v for v in violations if v.violation_type == "orphaned_template"]
        assert len(orphans) == 1
        assert "orphan.html.j2" in orphans[0].detail

    def test_excluded_templates_not_flagged(self, tmp_template_root: Path) -> None:
        """base.html.j2, worksheet.html.j2, components/, appendices/ are excluded."""
        sec_dir = tmp_template_root / "sections" / "sec1"
        sec_dir.mkdir(parents=True)
        (tmp_template_root / "sections" / "sec1.html.j2").touch()
        (sec_dir / "f1.html.j2").touch()
        # These should be excluded from orphan detection
        (tmp_template_root / "base.html.j2").touch()
        (tmp_template_root / "worksheet.html.j2").touch()
        comp_dir = tmp_template_root / "components"
        comp_dir.mkdir()
        (comp_dir / "helper.html.j2").touch()
        app_dir = tmp_template_root / "appendices"
        app_dir.mkdir()
        (app_dir / "audit.html.j2").touch()

        facet = _make_facet("f1", "sections/sec1/f1.html.j2")
        section = _make_section("sec1", "sections/sec1.html.j2", [facet])
        manifest = _make_manifest([section])

        violations = validate_facet_template_agreement(manifest, tmp_template_root)
        assert violations == []


# ---------------------------------------------------------------
# Unit tests: validate_signal_references
# ---------------------------------------------------------------


class TestSignalReferences:
    """Tests for validate_signal_references."""

    def test_valid_signal_references(self) -> None:
        """All facet signal IDs exist in the signal set."""
        facet = _make_facet("f1", "sections/sec1/f1.html.j2", signals=["SIG_001", "SIG_002"])
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])

        violations = validate_signal_references(manifest, {"SIG_001", "SIG_002", "SIG_003"})
        assert violations == []

    def test_broken_signal_reference(self) -> None:
        """Facet references a signal that does not exist."""
        facet = _make_facet("f1", "sections/sec1/f1.html.j2", signals=["SIG_001", "SIG_MISSING"])
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])

        violations = validate_signal_references(manifest, {"SIG_001"})
        assert len(violations) == 1
        v = violations[0]
        assert v.violation_type == "broken_signal_reference"
        assert v.facet_id == "f1"
        assert "SIG_MISSING" in v.detail

    def test_empty_signals_list_is_valid(self) -> None:
        """Facets with empty signals list are data-display-only, valid."""
        facet = _make_facet("f1", "sections/sec1/f1.html.j2", signals=[])
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])

        violations = validate_signal_references(manifest, {"SIG_001"})
        assert violations == []


# ---------------------------------------------------------------
# Unit tests: validate_all_contracts
# ---------------------------------------------------------------


class TestValidateAllContracts:
    """Tests for validate_all_contracts (aggregator)."""

    def test_all_valid_returns_passing_report(self, tmp_path: Path) -> None:
        """When everything agrees, report is valid with zero violations."""
        # Set up manifest YAML
        manifest_path = tmp_path / "manifest.yaml"
        template_root = tmp_path / "templates" / "html"
        sec_dir = template_root / "sections" / "sec1"
        sec_dir.mkdir(parents=True)
        (template_root / "sections" / "sec1.html.j2").touch()
        (sec_dir / "f1.html.j2").touch()

        # Set up signal YAML
        signals_dir = tmp_path / "signals"
        signals_dir.mkdir()
        sig_yaml = {
            "signals": [
                {"id": "SIG_001", "name": "Test Signal", "category": "test", "weight": 1.0}
            ]
        }
        (signals_dir / "test.yaml").write_text(yaml.dump(sig_yaml))

        manifest_data = {
            "manifest_version": "1.0",
            "sections": [
                {
                    "id": "sec1",
                    "name": "Section 1",
                    "template": "sections/sec1.html.j2",
                    "render_mode": "required",
                    "facets": [
                        {
                            "id": "f1",
                            "name": "Facet 1",
                            "template": "sections/sec1/f1.html.j2",
                            "data_type": "extract_display",
                            "render_as": "kv_table",
                            "signals": ["SIG_001"],
                        }
                    ],
                }
            ],
        }
        manifest_path.write_text(yaml.dump(manifest_data))

        report = validate_all_contracts(manifest_path, template_root, signals_dir)
        assert isinstance(report, ContractReport)
        assert report.valid is True
        assert report.violations == []

    def test_multiple_violations_aggregated(self, tmp_path: Path) -> None:
        """Report aggregates violations from both validators."""
        manifest_path = tmp_path / "manifest.yaml"
        template_root = tmp_path / "templates" / "html"
        template_root.mkdir(parents=True)
        # No section templates at all

        signals_dir = tmp_path / "signals"
        signals_dir.mkdir()
        # Empty signals dir -- no signal files

        manifest_data = {
            "manifest_version": "1.0",
            "sections": [
                {
                    "id": "sec1",
                    "name": "Section 1",
                    "template": "sections/sec1.html.j2",
                    "render_mode": "required",
                    "facets": [
                        {
                            "id": "f1",
                            "name": "Facet 1",
                            "template": "sections/sec1/f1.html.j2",
                            "data_type": "extract_display",
                            "render_as": "kv_table",
                            "signals": ["SIG_NONEXISTENT"],
                        }
                    ],
                }
            ],
        }
        manifest_path.write_text(yaml.dump(manifest_data))

        report = validate_all_contracts(manifest_path, template_root, signals_dir)
        assert report.valid is False
        # Should have: missing section template + missing facet template + broken signal
        assert len(report.violations) >= 2


# ---------------------------------------------------------------
# Violation message quality
# ---------------------------------------------------------------


class TestViolationMessages:
    """Violation messages must be actionable -- include IDs and paths."""

    def test_missing_template_message_has_facet_and_path(self, tmp_template_root: Path) -> None:
        sec_dir = tmp_template_root / "sections" / "sec1"
        sec_dir.mkdir(parents=True)
        (tmp_template_root / "sections" / "sec1.html.j2").touch()

        facet = _make_facet("my_facet", "sections/sec1/my_facet.html.j2")
        section = _make_section("sec1", "sections/sec1.html.j2", [facet])
        manifest = _make_manifest([section])

        violations = validate_facet_template_agreement(manifest, tmp_template_root)
        assert len(violations) == 1
        v = violations[0]
        assert "my_facet" in v.detail
        assert v.facet_id == "my_facet"
        assert v.section_id == "sec1"

    def test_broken_signal_message_has_signal_id(self) -> None:
        facet = _make_facet("f1", "t.html.j2", signals=["BASE.MISSING_SIGNAL"])
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])

        violations = validate_signal_references(manifest, set())
        assert len(violations) == 1
        assert "BASE.MISSING_SIGNAL" in violations[0].detail


# ---------------------------------------------------------------
# CI Integration tests: real project data
# ---------------------------------------------------------------

# Resolve real paths relative to the project source tree
_SRC_ROOT = Path(__file__).resolve().parent.parent.parent / "src" / "do_uw"
_TEMPLATE_ROOT = _SRC_ROOT / "templates" / "html"
_SIGNALS_DIR = _SRC_ROOT / "brain" / "signals"

# Legacy section templates that exist on disk but are not (yet) declared in the
# output manifest. These pre-date the manifest system and are included directly
# by the HTML renderer or worksheet template. Each should eventually be folded
# into the manifest or removed.
_KNOWN_LEGACY_TEMPLATES: set[str] = {
    "sections/cover.html.j2",
    "sections/financial_statements.html.j2",
    "sections/scoring_hazard.html.j2",
    "sections/scoring_perils.html.j2",
    "sections/scoring_peril_map.html.j2",
    # Phase 122: sections removed from manifest but templates kept on disk
    "sections/alt_data.html.j2",
    "sections/alt_data/esg_risk.html.j2",
    "sections/alt_data/ai_washing.html.j2",
    "sections/alt_data/tariff_exposure.html.j2",
    "sections/alt_data/peer_sca.html.j2",
    "sections/adversarial_critique.html.j2",
    "sections/dossier.html.j2",
    # Pre-existing legacy fragment templates (not referenced by manifest groups)
    "sections/governance/governance_score_breakdown.html.j2",
    "sections/governance/tenure_distribution.html.j2",
    "sections/scoring/factor_detail.html.j2",
    "sections/litigation/litigation_dashboard.html.j2",
    "sections/litigation/regulatory_proceedings.html.j2",
    # Pre-existing standalone/utility templates
    "sections/ai_risk.html.j2",
    "sections/crf_banner.html.j2",
    "sections/decision_record.html.j2",
    "sections/executive_brief.html.j2",
    "sections/key_stats.html.j2",
    "sections/scorecard.html.j2",
    "sections/trigger_matrix.html.j2",
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


class TestRealProjectContracts:
    """Integration tests that validate the REAL project state.

    These are the CI tests that enforce the manifest contract. Running
    `uv run pytest tests/brain/test_contract_enforcement.py` in CI catches
    any broken facet-template-signal chain.
    """

    def test_real_manifest_template_agreement(self) -> None:
        """All manifest templates exist on disk, no orphaned section templates."""
        from do_uw.brain.manifest_schema import load_manifest

        manifest = load_manifest()
        violations = validate_facet_template_agreement(
            manifest, _TEMPLATE_ROOT, exclude_orphans=_KNOWN_LEGACY_TEMPLATES
        )

        if violations:
            lines = ["Contract violations found:"]
            for v in violations:
                lines.append(
                    f"  [{v.violation_type}] section={v.section_id} "
                    f"facet={v.facet_id}: {v.detail}"
                )
            pytest.fail("\n".join(lines))

    def test_real_signal_references(self) -> None:
        """Signal reference validation: zero broken references allowed.

        Phase 80 wired all signal references. Any broken reference is a
        regression that must be fixed immediately.
        """
        from do_uw.brain.contract_validator import _load_signal_ids_from_dir
        from do_uw.brain.manifest_schema import load_manifest

        manifest = load_manifest()
        signal_ids = _load_signal_ids_from_dir(_SIGNALS_DIR)

        violations = validate_signal_references(manifest, signal_ids)

        if violations:
            lines = [
                f"BROKEN SIGNAL REFERENCES: {len(violations)} broken refs found. "
                f"Every manifest signal must exist in brain YAML:"
            ]
            for v in violations:
                lines.append(
                    f"  [{v.violation_type}] section={v.section_id} "
                    f"facet={v.facet_id}: {v.detail}"
                )
            pytest.fail("\n".join(lines))

    def test_zero_orphaned_signals(self) -> None:
        """Every active signal in brain YAML must be assigned to at least one manifest group."""
        from do_uw.brain.brain_unified_loader import load_signals
        from do_uw.brain.contract_validator import _load_signal_ids_from_dir
        from do_uw.brain.manifest_schema import collect_signals_by_group, load_manifest

        manifest = load_manifest()
        signal_ids = _load_signal_ids_from_dir(_SIGNALS_DIR)

        # Build set of all signal IDs assigned to groups (v3: signals self-select)
        sigs = load_signals()["signals"]
        sig_groups = collect_signals_by_group(sigs)

        # Only count signals in groups that exist in the manifest
        manifest_group_ids: set[str] = set()
        for section in manifest.sections:
            for group in section.groups:
                manifest_group_ids.add(group.id)

        assigned: set[str] = set()
        for gid, sig_ids in sig_groups.items():
            if gid in manifest_group_ids:
                assigned.update(sig_ids)

        # Orphaned = in YAML but not in any manifest group
        orphaned = signal_ids - assigned

        if orphaned:
            pytest.fail(
                f"{len(orphaned)} active signals not assigned to any manifest group:\n"
                + "\n".join(f"  {s}" for s in sorted(orphaned))
            )

    def test_every_manifest_group_has_template_on_disk(self) -> None:
        """Explicit per-group check: every group's template path resolves to a file."""
        from do_uw.brain.manifest_schema import load_manifest

        manifest = load_manifest()
        missing: list[str] = []

        for section in manifest.sections:
            for group in section.groups:
                template_path = _TEMPLATE_ROOT / group.template
                if not template_path.exists():
                    missing.append(
                        f"Group {section.id}/{group.id} references template "
                        f"{group.template} which does not exist"
                    )

        if missing:
            pytest.fail("\n".join(missing))


# ---------------------------------------------------------------
# Unit tests: requires field and validate_requires_populated
# ---------------------------------------------------------------


class TestRequiresField:
    """Tests for the requires field on ManifestFacet."""

    def test_facet_accepts_requires_field(self) -> None:
        """ManifestFacet accepts an optional requires list of strings."""
        facet = ManifestFacet(
            id="f1",
            name="Facet 1",
            template="sections/sec1/f1.html.j2",
            data_type="extract_display",
            render_as="kv_table",
            requires=["financials.statements"],
        )
        assert facet.requires == ["financials.statements"]

    def test_facet_requires_defaults_to_empty(self) -> None:
        """Facets without requires field default to empty list (backwards compat)."""
        facet = _make_facet("f1")
        assert facet.requires == []

    def test_facet_with_multiple_requires(self) -> None:
        """Facets can require multiple field paths."""
        facet = ManifestFacet(
            id="f1",
            name="Facet 1",
            template="sections/sec1/f1.html.j2",
            data_type="extract_display",
            render_as="kv_table",
            requires=["financials.statements", "company.name"],
        )
        assert len(facet.requires) == 2


class TestValidateRequiresPopulated:
    """Tests for validate_requires_populated function."""

    def test_populated_field_no_warnings(self) -> None:
        """Facet with requires=['financials.statements'] + context has it -> no warnings."""
        from do_uw.brain.contract_validator import validate_requires_populated

        facet = ManifestFacet(
            id="f1",
            name="Facet 1",
            template="sections/sec1/f1.html.j2",
            data_type="extract_display",
            render_as="kv_table",
            requires=["financials.statements"],
        )
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])
        context = {"financials": {"statements": [{"revenue": 1000}]}}

        warnings = validate_requires_populated(manifest, context)
        assert warnings == []

    def test_missing_field_produces_warning(self) -> None:
        """Facet with requires=['financials.statements'] + context missing it -> warning."""
        from do_uw.brain.contract_validator import validate_requires_populated

        facet = ManifestFacet(
            id="f1",
            name="Facet 1",
            template="sections/sec1/f1.html.j2",
            data_type="extract_display",
            render_as="kv_table",
            requires=["financials.statements"],
        )
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])
        context: dict[str, object] = {}

        warnings = validate_requires_populated(manifest, context)
        assert len(warnings) == 1
        assert warnings[0].field_path == "financials.statements"
        assert warnings[0].facet_id == "f1"
        assert warnings[0].section_id == "sec1"

    def test_empty_requires_no_warnings(self) -> None:
        """Facets with requires=[] produce no warnings (backwards compatible)."""
        from do_uw.brain.contract_validator import validate_requires_populated

        facet = _make_facet("f1")
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])
        context: dict[str, object] = {}

        warnings = validate_requires_populated(manifest, context)
        assert warnings == []

    def test_nested_path_resolution(self) -> None:
        """Dot-notation paths resolve nested dict keys: 'a.b.c' -> context['a']['b']['c']."""
        from do_uw.brain.contract_validator import validate_requires_populated

        facet = ManifestFacet(
            id="f1",
            name="Facet 1",
            template="sections/sec1/f1.html.j2",
            data_type="extract_display",
            render_as="kv_table",
            requires=["a.b.c"],
        )
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])
        context = {"a": {"b": {"c": "value"}}}

        warnings = validate_requires_populated(manifest, context)
        assert warnings == []

    def test_none_value_at_path_produces_warning(self) -> None:
        """None value at required path -> warning."""
        from do_uw.brain.contract_validator import validate_requires_populated

        facet = ManifestFacet(
            id="f1",
            name="Facet 1",
            template="sections/sec1/f1.html.j2",
            data_type="extract_display",
            render_as="kv_table",
            requires=["financials.ratios"],
        )
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])
        context = {"financials": {"ratios": None}}

        warnings = validate_requires_populated(manifest, context)
        assert len(warnings) == 1
        assert warnings[0].field_path == "financials.ratios"

    def test_empty_list_at_path_produces_warning(self) -> None:
        """Empty list at required path -> warning."""
        from do_uw.brain.contract_validator import validate_requires_populated

        facet = ManifestFacet(
            id="f1",
            name="Facet 1",
            template="sections/sec1/f1.html.j2",
            data_type="extract_display",
            render_as="kv_table",
            requires=["litigation.cases"],
        )
        section = _make_section("sec1", facets=[facet])
        manifest = _make_manifest([section])
        context = {"litigation": {"cases": []}}

        warnings = validate_requires_populated(manifest, context)
        assert len(warnings) == 1
        assert warnings[0].field_path == "litigation.cases"

    def test_multiple_facets_multiple_warnings(self) -> None:
        """Multiple facets with missing data produce multiple warnings."""
        from do_uw.brain.contract_validator import validate_requires_populated

        facet1 = ManifestFacet(
            id="f1", name="F1", template="t1.j2",
            data_type="extract_display", render_as="kv_table",
            requires=["a"],
        )
        facet2 = ManifestFacet(
            id="f2", name="F2", template="t2.j2",
            data_type="extract_display", render_as="kv_table",
            requires=["b"],
        )
        section = _make_section("sec1", facets=[facet1, facet2])
        manifest = _make_manifest([section])
        context: dict[str, object] = {}

        warnings = validate_requires_populated(manifest, context)
        assert len(warnings) == 2


# ---------------------------------------------------------------
# Integration tests: real manifest requires blocks
# ---------------------------------------------------------------


class TestRealManifestRequires:
    """Integration tests verifying requires blocks on the real manifest."""

    def test_at_least_10_groups_have_requires(self) -> None:
        """At least 10 groups in the real manifest declare requires blocks."""
        from do_uw.brain.manifest_schema import load_manifest

        manifest = load_manifest()
        groups_with_requires = [
            g
            for s in manifest.sections
            for g in s.groups
            if g.requires
        ]
        assert len(groups_with_requires) >= 10, (
            f"Expected at least 10 groups with requires, found {len(groups_with_requires)}"
        )

    def test_requires_values_are_valid_strings(self) -> None:
        """All requires field values are non-empty strings."""
        from do_uw.brain.manifest_schema import load_manifest

        manifest = load_manifest()
        for section in manifest.sections:
            for group in section.groups:
                for req in group.requires:
                    assert isinstance(req, str), (
                        f"Group {section.id}/{group.id} has non-string requires: {req!r}"
                    )
                    assert len(req) > 0, (
                        f"Group {section.id}/{group.id} has empty string in requires"
                    )

    def test_manifest_still_loads_with_requires(self) -> None:
        """Manifest loads and validates without errors after adding requires blocks."""
        from do_uw.brain.manifest_schema import load_manifest

        manifest = load_manifest()
        assert manifest.manifest_version in ("1.0", "2.0")
        assert len(manifest.sections) > 0


# ---------------------------------------------------------------
# Signal architecture guardrail: evaluative groups must have signals
# ---------------------------------------------------------------


class TestSignalArchitectureGuardrail:
    """Prevent extract→render bypasses for evaluative content.

    The architecture requires: EXTRACT → ANALYZE (signals) → SCORE → RENDER.
    Any manifest group that renders evaluated/scored content (not raw data
    display) MUST have at least one signal self-selecting into it.

    Groups that display raw facts (e.g. balance sheet tables, executive bios)
    are exempt — they are data_type='extract_display' or listed in
    DISPLAY_ONLY_GROUPS.
    """

    # Groups that legitimately display raw extracted data or post-SCORE
    # derivations without direct signal backing. These show facts (names,
    # numbers, dates) or consume outputs from SCORE/BENCHMARK stages.
    #
    # To add a group here, it must fall into one of these categories:
    # 1. DISPLAY_ONLY: Shows raw extracted data (balance sheets, bios, tables)
    # 2. SCORE_DERIVED: Consumes state.scoring output (already signal-evaluated)
    # 3. META: System metadata (QA, calibration, sources, density alerts)
    #
    # IMPORTANT: If a group renders threshold-driven colors, risk judgments,
    # or evaluative content, it MUST have signals — do NOT add it here.
    DISPLAY_ONLY_GROUPS: set[str] = {
        # ── DISPLAY_ONLY: raw fact tables ──
        # Identity & metadata
        "identity_header",
        "company_profile",
        "business_model",
        "structural_complexity",
        "geographic_footprint",
        "workforce_distribution",
        "corporate_events",
        "operational_resilience",
        "company_checks",
        "exposure_factors",
        "subsidiary_structure",
        "risk_factors",
        "company_density_alerts",
        # Financial raw tables
        "annual_comparison",
        "key_metrics",
        "quarterly_updates",
        "financial_statements",
        "financial_trends",
        "tax_analysis",
        "earnings_quality",
        "audit_history",
        "peer_comparison",
        "peer_matrix",
        "peer_percentiles",
        "tax_risk",
        "financial_checks",
        "density_alerts",
        # Market raw tables
        "stock_performance",
        "capital_markets",
        "analyst_consensus",
        "earnings_guidance",
        "ownership_chart",
        "stock_charts",
        # Governance raw tables
        "people_risk",
        "board_composition",
        "board_forensics",
        "executive_profiles",
        "executive_tenure",
        "executive_litigation",
        "executive_insider_trading",
        "governance_structure",
        "ownership_structure",
        "compensation_analysis",
        "activist_shareholder",
        "governance_checks",
        # Litigation raw tables
        "active_matters",
        "sec_enforcement",
        "settlement_history",
        "derivative_suits",
        "contingent_liabilities",
        "defense_strength",
        "whistleblower_indicators",
        "litigation_checks",
        "litigation_timeline",
        # ── SCORE_DERIVED: consume state.scoring (already signal-evaluated) ──
        "ten_factor_scoring",
        "scoring_detail",
        "red_flags",
        "allegation_map",
        "tower_recommendation",
        "premium_analysis",
        "pricing_confidence",
        "peril_map",
        "peril_assessment",
        "coverage_gaps",
        "tier_classification",
        "hazard_profile",
        "pattern_detection",
        "allegation_mapping",
        "claim_probability",
        "severity_scenarios",
        "executive_risk_profile",
        "temporal_signals",
        "nlp_analysis",
        "scoring_checks",
        # Analysis composites (post-ANALYZE, not signal-per-se)
        "forensic_composites",
        "executive_risk_assessment",
        "temporal_signal_analysis",
        "nlp_signal_analysis",
        "executive_summary_content",
        "risk_tier_badge",
        "data_quality_notice",
        "executive_density_alerts",
        "triggered_flags",
        # ── META: system/UI metadata ──
        "ai_risk_assessment",
        "overall_score",
        "dimension_breakdown",
        "competitive_position",
        "forward_assessment",
        "meeting_prep",
        "sources_list",
        "qa_audit",
        "signal_coverage",
        "calibration_notes",
        "classification_summary",
        "hazard_profile_summary",
        # Density alert panels (narrative overlays, not evaluative)
        "market_checks",
        "market_density_alerts",
        "governance_density_alerts",
        "litigation_density_alerts",
        "ai_risk_density_alerts",
        "scoring_density_alerts",
        # Filing analysis
        "filing_analysis_overview",
        "filing_analysis_mda",
        "filing_analysis_risk_factors",
        "filing_analysis_legal",
        "filing_analysis_controls",
        "filing_comparison",
    }

    def test_evaluative_groups_have_signals(self) -> None:
        """Every non-display manifest group must have at least one signal.

        This test prevents the extract→render bypass pattern. When you add
        a new manifest group that renders evaluated content, you MUST also
        create brain signals that self-select into that group (via the
        signal's `group` field in YAML).

        If this test fails, you have two choices:
        1. Create brain signals for the group (correct fix)
        2. Add the group to DISPLAY_ONLY_GROUPS (only if it truly
           displays raw facts with no evaluation/scoring)
        """
        from do_uw.brain.brain_unified_loader import load_signals
        from do_uw.brain.manifest_schema import collect_signals_by_group, load_manifest

        manifest = load_manifest()
        sigs = load_signals()["signals"]
        sig_groups = collect_signals_by_group(sigs)

        # Collect all manifest group IDs
        all_groups: list[tuple[str, str]] = []  # (section_id, group_id)
        for section in manifest.sections:
            for group in section.groups:
                all_groups.append((section.id, group.id))

        # Build set of display_only groups from manifest (authoritative source)
        manifest_display_only = {
            group.id
            for section in manifest.sections
            for group in section.groups
            if group.display_only
        }

        violations: list[str] = []
        for section_id, group_id in all_groups:
            if group_id in self.DISPLAY_ONLY_GROUPS or group_id in manifest_display_only:
                continue
            signal_count = len(sig_groups.get(group_id, []))
            if signal_count == 0:
                violations.append(
                    f"  {section_id}/{group_id}: 0 signals — needs YAML "
                    f"signals with `group: {group_id}` or add to DISPLAY_ONLY_GROUPS"
                )

        if violations:
            pytest.fail(
                f"SIGNAL ARCHITECTURE BYPASS: {len(violations)} manifest group(s) "
                f"render evaluative content without signal backing:\n"
                + "\n".join(violations)
                + "\n\nFix: create brain signals with `group: <group_id>` in YAML, "
                "or if the group truly displays raw facts only, add it to "
                "DISPLAY_ONLY_GROUPS in this test."
            )
