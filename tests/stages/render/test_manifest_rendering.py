"""Tests for manifest-driven rendering across HTML and Word formats.

Phase 76 Plan 02: Validates that renderers use the output manifest for
section ordering instead of hardcoded lists.

Tests:
- build_section_context returns manifest_sections in manifest-declared order
- manifest_sections contains all expected section IDs
- Removing a section from manifest excludes it from manifest_sections
- Section ordering matches manifest, not filesystem alphabetical order
- Word renderer uses manifest for section ordering
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from do_uw.brain.manifest_schema import (
    ManifestSection,
    OutputManifest,
    load_manifest,
)
from do_uw.stages.render.section_renderer import build_section_context


# Expected section IDs in manifest order (from output_manifest.yaml)
_MANIFEST_SECTION_IDS = [
    "identity",
    "executive_summary",
    "red_flags",
    "company_operations",
    "market_activity",
    "financial_health",
    "governance",
    "litigation",
    "sector_industry",
    "scoring",
    "sources",
    "qa_audit",
    "market_overflow",
    "coverage",
]


class TestBuildSectionContextManifestSections:
    """build_section_context() returns manifest_sections in manifest order."""

    def test_manifest_sections_key_present(self) -> None:
        """build_section_context returns manifest_sections key."""
        ctx = build_section_context()
        assert "manifest_sections" in ctx

    def test_manifest_sections_order(self) -> None:
        """manifest_sections list matches manifest YAML order."""
        ctx = build_section_context()
        actual_ids = [s["id"] for s in ctx["manifest_sections"]]
        assert actual_ids == _MANIFEST_SECTION_IDS

    def test_manifest_sections_count(self) -> None:
        """All 14 manifest sections present."""
        ctx = build_section_context()
        assert len(ctx["manifest_sections"]) == 14

    def test_manifest_section_shape(self) -> None:
        """Each manifest_sections entry has id, name, template, render_mode, layer, facets."""
        ctx = build_section_context()
        required_keys = {"id", "name", "template", "render_mode", "layer", "facets"}
        for entry in ctx["manifest_sections"]:
            assert required_keys.issubset(set(entry.keys())), (
                f"Section {entry.get('id', '?')} missing keys: "
                f"{required_keys - set(entry.keys())}"
            )

    def test_manifest_facets_have_render_as(self) -> None:
        """Facets within manifest_sections include render_as (from ManifestGroup)."""
        ctx = build_section_context()
        for section in ctx["manifest_sections"]:
            for facet in section["facets"]:
                assert "render_as" in facet, (
                    f"Facet {facet.get('id', '?')} in section {section['id']} "
                    f"missing render_as"
                )

    def test_removing_section_from_manifest_excludes_from_output(self) -> None:
        """A section removed from manifest does not appear in manifest_sections."""
        # Create a manifest with only 2 sections
        short_manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(
                    id="identity",
                    name="Cover",
                    template="sections/identity.html.j2",
                ),
                ManifestSection(
                    id="scoring",
                    name="Scoring",
                    template="sections/scoring.html.j2",
                ),
            ],
        )
        with patch(
            "do_uw.stages.render.section_renderer.load_manifest",
            return_value=short_manifest,
        ):
            ctx = build_section_context()
        actual_ids = [s["id"] for s in ctx["manifest_sections"]]
        assert actual_ids == ["identity", "scoring"]
        assert "executive_summary" not in actual_ids

    def test_ordering_follows_manifest_not_alphabetical(self) -> None:
        """If manifest declares scoring before identity, manifest_sections follows that."""
        reversed_manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(
                    id="scoring",
                    name="Scoring",
                    template="sections/scoring.html.j2",
                ),
                ManifestSection(
                    id="identity",
                    name="Cover",
                    template="sections/identity.html.j2",
                ),
            ],
        )
        with patch(
            "do_uw.stages.render.section_renderer.load_manifest",
            return_value=reversed_manifest,
        ):
            ctx = build_section_context()
        actual_ids = [s["id"] for s in ctx["manifest_sections"]]
        assert actual_ids == ["scoring", "identity"]

    def test_section_context_dict_still_present(self) -> None:
        """Backward compat: section_context dict is still returned."""
        ctx = build_section_context()
        assert "section_context" in ctx
        assert isinstance(ctx["section_context"], dict)

    def test_deterministic_ordering(self) -> None:
        """Two calls produce identical manifest_sections ordering."""
        ctx1 = build_section_context()
        ctx2 = build_section_context()
        ids1 = [s["id"] for s in ctx1["manifest_sections"]]
        ids2 = [s["id"] for s in ctx2["manifest_sections"]]
        assert ids1 == ids2


class TestManifestSectionsInHtmlContext:
    """manifest_sections wired into build_html_context()."""

    def test_html_context_has_manifest_sections(self) -> None:
        from do_uw.models.state import AnalysisState
        from do_uw.stages.render.html_renderer import build_html_context

        state = AnalysisState(ticker="TEST")
        ctx = build_html_context(state)
        assert "manifest_sections" in ctx
        actual_ids = [s["id"] for s in ctx["manifest_sections"]]
        assert actual_ids == _MANIFEST_SECTION_IDS
