"""Tests for section-driven rendering dispatch module.

Phase 84-03: Migrated from section YAML to manifest groups + signal self-selection.

Validates:
- build_section_context() produces correct dispatch context from manifest groups
- section_context dict has correct facet structure (id, name, render_as, signals, columns, template)
- manifest_sections list preserves manifest order
- Fragment templates exist on disk at their manifest-declared paths
- section_context wired into build_html_context()
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from do_uw.brain.manifest_schema import load_manifest
from do_uw.stages.render.section_renderer import build_section_context

# Template directory
_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "src" / "do_uw" / "templates" / "html"


class TestBuildSectionContext:
    """build_section_context() manifest-driven dispatch tests."""

    def test_returns_section_context_and_manifest_sections(self) -> None:
        """build_section_context() returns both expected keys."""
        ctx = build_section_context()
        assert "section_context" in ctx
        assert "manifest_sections" in ctx

    def test_section_context_has_all_sections_with_groups(self) -> None:
        """section_context includes every manifest section that has groups."""
        ctx = build_section_context()
        manifest = load_manifest()
        sections_with_groups = [s.id for s in manifest.sections if s.groups]
        for section_id in sections_with_groups:
            assert section_id in ctx["section_context"], (
                f"Section {section_id} missing from section_context"
            )

    def test_section_context_excludes_sections_without_groups(self) -> None:
        """section_context excludes manifest sections that have no groups."""
        ctx = build_section_context()
        manifest = load_manifest()
        sections_without_groups = [s.id for s in manifest.sections if not s.groups]
        for section_id in sections_without_groups:
            assert section_id not in ctx["section_context"], (
                f"Section {section_id} should not be in section_context (no groups)"
            )

    def test_facet_data_shape(self) -> None:
        """Each facet dict has id, name, render_as, signals, columns, template keys."""
        ctx = build_section_context()
        expected_keys = {"id", "name", "render_as", "signals", "columns", "template"}
        for section_id, section_data in ctx["section_context"].items():
            assert "section" in section_data
            assert "facets" in section_data
            for facet_data in section_data["facets"]:
                assert set(facet_data.keys()) == expected_keys, (
                    f"Facet {facet_data.get('id', '?')} in {section_id} "
                    f"has wrong keys: {set(facet_data.keys())}"
                )

    def test_facet_columns_is_list(self) -> None:
        """Each facet has columns as a list (empty default)."""
        ctx = build_section_context()
        for section_id, section_data in ctx["section_context"].items():
            for facet_data in section_data["facets"]:
                assert isinstance(facet_data["columns"], list), (
                    f"Facet {facet_data['id']} in {section_id} columns not a list"
                )

    def test_facet_signals_is_list(self) -> None:
        """Each facet has signals as a list."""
        ctx = build_section_context()
        for section_id, section_data in ctx["section_context"].items():
            for facet_data in section_data["facets"]:
                assert isinstance(facet_data["signals"], list), (
                    f"Facet {facet_data['id']} in {section_id} signals not a list"
                )

    def test_section_field_is_none(self) -> None:
        """section field is None (no SectionSpec needed with manifest groups)."""
        ctx = build_section_context()
        for section_data in ctx["section_context"].values():
            assert section_data["section"] is None

    def test_manifest_sections_count(self) -> None:
        """manifest_sections has same count as manifest.sections."""
        ctx = build_section_context()
        manifest = load_manifest()
        assert len(ctx["manifest_sections"]) == len(manifest.sections)

    def test_manifest_sections_order_matches_manifest(self) -> None:
        """manifest_sections preserves manifest ordering."""
        ctx = build_section_context()
        manifest = load_manifest()
        expected_ids = [s.id for s in manifest.sections]
        actual_ids = [s["id"] for s in ctx["manifest_sections"]]
        assert actual_ids == expected_ids

    def test_manifest_sections_entry_shape(self) -> None:
        """Each manifest_sections entry has id, name, template, render_mode, layer, facets."""
        ctx = build_section_context()
        expected_keys = {"id", "name", "template", "render_mode", "layer", "facets"}
        for entry in ctx["manifest_sections"]:
            assert set(entry.keys()) == expected_keys, (
                f"manifest_sections entry {entry.get('id', '?')} "
                f"has wrong keys: {set(entry.keys())}"
            )

    def test_manifest_sections_facets_from_groups(self) -> None:
        """manifest_sections facets come from manifest groups, not facets."""
        ctx = build_section_context()
        manifest = load_manifest()
        for ms_entry, ms_model in zip(ctx["manifest_sections"], manifest.sections):
            expected_group_ids = [g.id for g in ms_model.groups]
            actual_group_ids = [f["id"] for f in ms_entry["facets"]]
            assert actual_group_ids == expected_group_ids, (
                f"Section {ms_entry['id']}: facets don't match groups"
            )

    def test_accepts_deprecated_sections_dir_kwarg(self) -> None:
        """build_section_context absorbs deprecated sections_dir without error."""
        # Should not raise even though sections_dir is no longer used
        ctx = build_section_context(sections_dir=Path("/nonexistent"))
        assert "section_context" in ctx

    def test_accepts_state_param(self) -> None:
        """build_section_context accepts state parameter."""
        from do_uw.models.state import AnalysisState
        state = AnalysisState(ticker="TEST")
        ctx = build_section_context(state=state)
        assert "section_context" in ctx


class TestAllFragmentTemplatesExist:
    """Verify all fragment templates exist on disk for every manifest group."""

    def test_all_group_template_files_exist(self) -> None:
        """Every manifest group's template path resolves to a real file."""
        manifest = load_manifest()
        for ms in manifest.sections:
            for group in ms.groups:
                template_path = _TEMPLATE_DIR / group.template
                assert template_path.exists(), (
                    f"Fragment template missing: {group.template} "
                    f"(section: {ms.id}, group: {group.id})"
                )

    def test_group_template_path_ends_with_j2(self) -> None:
        """Each group template ends with .html.j2."""
        manifest = load_manifest()
        for ms in manifest.sections:
            for group in ms.groups:
                assert group.template.endswith(".html.j2"), (
                    f"Group {group.id} template doesn't end with .html.j2: {group.template}"
                )

    def test_financial_fragment_count(self) -> None:
        """Exactly 24 fragment files in sections/financial/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "financial").glob("*.html.j2"))
        assert len(fragments) == 24

    def test_governance_fragment_count(self) -> None:
        """Exactly 14 fragment files in sections/governance/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "governance").glob("*.html.j2"))
        assert len(fragments) == 14

    def test_market_fragment_count(self) -> None:
        """Exactly 15 fragment files in sections/market/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "market").glob("*.html.j2"))
        assert len(fragments) == 15

    def test_company_fragment_count(self) -> None:
        """Exactly 20 fragment files in sections/company/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "company").glob("*.html.j2"))
        assert len(fragments) == 20

    def test_litigation_fragment_count(self) -> None:
        """Exactly 16 fragment files in sections/litigation/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "litigation").glob("*.html.j2"))
        assert len(fragments) == 16

    def test_executive_fragment_count(self) -> None:
        """Exactly 7 fragment files in sections/executive/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "executive").glob("*.html.j2"))
        assert len(fragments) == 7

    def test_ai_risk_fragment_count(self) -> None:
        """Exactly 5 fragment files in sections/ai_risk/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "ai_risk").glob("*.html.j2"))
        assert len(fragments) == 5

    def test_scoring_fragment_count(self) -> None:
        """At least 18 fragment files in sections/scoring/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "scoring").glob("*.html.j2"))
        assert len(fragments) >= 18

    def test_forward_looking_fragment_count(self) -> None:
        """At least 11 fragment files in sections/forward_looking/ (5 original + 6 Phase 117)."""
        fragments = list((_TEMPLATE_DIR / "sections" / "forward_looking").glob("*.html.j2"))
        assert len(fragments) >= 11

    def test_executive_risk_fragment_count(self) -> None:
        """Exactly 4 fragment files in sections/executive_risk/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "executive_risk").glob("*.html.j2"))
        assert len(fragments) == 4

    def test_filing_analysis_fragment_count(self) -> None:
        """Exactly 3 fragment files in sections/filing_analysis/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "filing_analysis").glob("*.html.j2"))
        assert len(fragments) == 3

    def test_red_flags_fragment_count(self) -> None:
        """Exactly 1 fragment file in sections/red_flags/."""
        fragments = list((_TEMPLATE_DIR / "sections" / "red_flags").glob("*.html.j2"))
        assert len(fragments) == 1


class TestSectionContextInHtmlContext:
    """section_context wired into build_html_context()."""

    def test_build_html_context_has_section_context(self) -> None:
        from do_uw.stages.render.html_renderer import build_html_context
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="TEST")
        ctx = build_html_context(state)
        assert "section_context" in ctx

    def test_section_context_sections_match_manifest(self) -> None:
        from do_uw.stages.render.html_renderer import build_html_context
        from do_uw.models.state import AnalysisState

        state = AnalysisState(ticker="TEST")
        ctx = build_html_context(state)
        manifest = load_manifest()
        sections_with_groups = {s.id for s in manifest.sections if s.groups}
        for section_id in sections_with_groups:
            assert section_id in ctx["section_context"], (
                f"Section {section_id} missing from html context"
            )
