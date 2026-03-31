"""Tests for output manifest schema and loader.

Phase 76 Plan 01: Validates ManifestFacet, ManifestSection, OutputManifest
models and the load_manifest() function.

Phase 84 Plan 01: Adds ManifestGroup model tests, backward-compat facets->groups
auto-population, collect_signals_by_group, and duplicate group ID detection.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from do_uw.brain.manifest_schema import (
    ManifestFacet,
    ManifestGroup,
    ManifestSection,
    OutputManifest,
    collect_signals_by_group,
    get_facet_order,
    get_section_order,
    load_manifest,
)


# ---------------------------------------------------------------------------
# ManifestFacet tests
# ---------------------------------------------------------------------------


class TestManifestFacet:
    def test_valid_facet(self) -> None:
        facet = ManifestFacet(
            id="annual_comparison",
            name="Annual Financial Comparison",
            template="sections/financial/annual_comparison.html.j2",
            data_type="extract_display",
            render_as="financial_table",
        )
        assert facet.id == "annual_comparison"
        assert facet.signals == []

    def test_all_data_types(self) -> None:
        for dt in ("extract_display", "extract_compute", "extract_infer", "hunt_analyze"):
            facet = ManifestFacet(
                id="test",
                name="Test",
                template="t.html.j2",
                data_type=dt,
                render_as="table",
            )
            assert facet.data_type == dt

    def test_invalid_data_type(self) -> None:
        with pytest.raises(ValidationError, match="data_type"):
            ManifestFacet(
                id="test",
                name="Test",
                template="t.html.j2",
                data_type="invalid_type",
                render_as="table",
            )

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ManifestFacet(
                id="test",
                name="Test",
                template="t.html.j2",
                data_type="extract_display",
                render_as="table",
                bogus_field="nope",
            )

    def test_signals_default_empty(self) -> None:
        facet = ManifestFacet(
            id="test",
            name="Test",
            template="t.html.j2",
            data_type="extract_display",
            render_as="table",
        )
        assert facet.signals == []

    def test_signals_populated(self) -> None:
        facet = ManifestFacet(
            id="test",
            name="Test",
            template="t.html.j2",
            data_type="extract_display",
            render_as="table",
            signals=["FIN.001", "FIN.002"],
        )
        assert facet.signals == ["FIN.001", "FIN.002"]


# ---------------------------------------------------------------------------
# ManifestSection tests
# ---------------------------------------------------------------------------


class TestManifestSection:
    def test_valid_section_no_facets(self) -> None:
        section = ManifestSection(
            id="identity",
            name="Cover & Identity",
            template="sections/identity.html.j2",
        )
        assert section.render_mode == "required"
        assert section.facets == []

    def test_render_mode_optional(self) -> None:
        section = ManifestSection(
            id="test",
            name="Test",
            template="t.html.j2",
            render_mode="optional",
        )
        assert section.render_mode == "optional"

    def test_invalid_render_mode(self) -> None:
        with pytest.raises(ValidationError, match="render_mode"):
            ManifestSection(
                id="test",
                name="Test",
                template="t.html.j2",
                render_mode="sometimes",
            )

    def test_section_with_facets(self) -> None:
        section = ManifestSection(
            id="financial_health",
            name="Financial Health",
            template="sections/financial.html.j2",
            facets=[
                ManifestFacet(
                    id="annual_comparison",
                    name="Annual Financial Comparison",
                    template="sections/financial/annual_comparison.html.j2",
                    data_type="extract_display",
                    render_as="financial_table",
                ),
                ManifestFacet(
                    id="distress_indicators",
                    name="Distress Model Indicators",
                    template="sections/financial/distress_indicators.html.j2",
                    data_type="extract_compute",
                    render_as="scorecard",
                ),
            ],
        )
        assert len(section.facets) == 2
        assert section.facets[0].id == "annual_comparison"
        assert section.facets[1].id == "distress_indicators"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ManifestSection(
                id="test",
                name="Test",
                template="t.html.j2",
                unknown="bad",
            )


# ---------------------------------------------------------------------------
# OutputManifest tests
# ---------------------------------------------------------------------------


class TestOutputManifest:
    def test_valid_manifest(self) -> None:
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(id="identity", name="Cover", template="t.html.j2"),
                ManifestSection(id="scoring", name="Scoring", template="s.html.j2"),
            ],
        )
        assert manifest.manifest_version == "1.0"
        assert len(manifest.sections) == 2

    def test_section_order_preserved(self) -> None:
        ids = ["c", "a", "b"]
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(id=sid, name=sid.upper(), template=f"{sid}.j2")
                for sid in ids
            ],
        )
        assert [s.id for s in manifest.sections] == ids

    def test_duplicate_section_ids_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate section"):
            OutputManifest(
                manifest_version="1.0",
                sections=[
                    ManifestSection(id="same", name="A", template="a.j2"),
                    ManifestSection(id="same", name="B", template="b.j2"),
                ],
            )

    def test_duplicate_facet_ids_within_section_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate facet"):
            OutputManifest(
                manifest_version="1.0",
                sections=[
                    ManifestSection(
                        id="fin",
                        name="Financial",
                        template="f.j2",
                        facets=[
                            ManifestFacet(
                                id="dup",
                                name="A",
                                template="a.j2",
                                data_type="extract_display",
                                render_as="table",
                            ),
                            ManifestFacet(
                                id="dup",
                                name="B",
                                template="b.j2",
                                data_type="extract_display",
                                render_as="table",
                            ),
                        ],
                    ),
                ],
            )

    def test_duplicate_facet_ids_across_sections_ok(self) -> None:
        """Same facet ID in different sections is allowed."""
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(
                    id="sec1",
                    name="Section 1",
                    template="s1.j2",
                    facets=[
                        ManifestFacet(
                            id="checks",
                            name="Checks",
                            template="c.j2",
                            data_type="extract_infer",
                            render_as="check_summary",
                        ),
                    ],
                ),
                ManifestSection(
                    id="sec2",
                    name="Section 2",
                    template="s2.j2",
                    facets=[
                        ManifestFacet(
                            id="checks",
                            name="Checks",
                            template="c2.j2",
                            data_type="extract_infer",
                            render_as="check_summary",
                        ),
                    ],
                ),
            ],
        )
        assert len(manifest.sections) == 2


# ---------------------------------------------------------------------------
# get_section_order / get_facet_order
# ---------------------------------------------------------------------------


class TestOrderHelpers:
    def test_get_section_order(self) -> None:
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(id="a", name="A", template="a.j2"),
                ManifestSection(id="b", name="B", template="b.j2"),
                ManifestSection(id="c", name="C", template="c.j2"),
            ],
        )
        assert get_section_order(manifest) == ["a", "b", "c"]

    def test_get_facet_order(self) -> None:
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(
                    id="fin",
                    name="Financial",
                    template="f.j2",
                    facets=[
                        ManifestFacet(
                            id="x", name="X", template="x.j2",
                            data_type="extract_display", render_as="table",
                        ),
                        ManifestFacet(
                            id="y", name="Y", template="y.j2",
                            data_type="extract_compute", render_as="scorecard",
                        ),
                    ],
                ),
            ],
        )
        assert get_facet_order(manifest, "fin") == ["x", "y"]

    def test_get_facet_order_unknown_section(self) -> None:
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[],
        )
        assert get_facet_order(manifest, "nonexistent") == []

    def test_get_facet_order_no_facets(self) -> None:
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(id="identity", name="Identity", template="i.j2"),
            ],
        )
        assert get_facet_order(manifest, "identity") == []


# ---------------------------------------------------------------------------
# load_manifest
# ---------------------------------------------------------------------------


class TestLoadManifest:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="output_manifest.yaml"):
            load_manifest(tmp_path / "nonexistent.yaml")

    def test_load_from_file(self, tmp_path: Path) -> None:
        manifest_data = {
            "manifest_version": "1.0",
            "sections": [
                {
                    "id": "test_section",
                    "name": "Test Section",
                    "template": "test.html.j2",
                    "render_mode": "required",
                    "facets": [
                        {
                            "id": "test_facet",
                            "name": "Test Facet",
                            "template": "test/facet.html.j2",
                            "data_type": "extract_display",
                            "render_as": "kv_table",
                        },
                    ],
                },
            ],
        }
        yaml_path = tmp_path / "output_manifest.yaml"
        yaml_path.write_text(yaml.dump(manifest_data))
        manifest = load_manifest(yaml_path)
        assert manifest.manifest_version == "1.0"
        assert len(manifest.sections) == 1
        assert manifest.sections[0].facets[0].data_type == "extract_display"

    def test_load_default_manifest(self) -> None:
        """The real manifest at the default path should load successfully."""
        manifest = load_manifest()
        assert manifest.manifest_version in ("1.0", "2.0")
        assert len(manifest.sections) >= 10
        # After migration, groups is the primary field
        total_groups = sum(len(s.groups) for s in manifest.sections)
        assert total_groups >= 90


# ---------------------------------------------------------------------------
# ManifestGroup tests (Phase 84 Plan 01)
# ---------------------------------------------------------------------------


class TestManifestGroup:
    def test_valid_group(self) -> None:
        group = ManifestGroup(
            id="business_description",
            name="Business Description",
            template="sections/company/business_description.html.j2",
            render_as="kv_table",
        )
        assert group.id == "business_description"
        assert group.requires == []

    def test_group_with_requires(self) -> None:
        group = ManifestGroup(
            id="annual_comparison",
            name="Annual Financial Comparison",
            template="sections/financial/annual_comparison.html.j2",
            render_as="financial_table",
            requires=["financials.statements"],
        )
        assert group.requires == ["financials.statements"]

    def test_group_extra_fields_forbidden(self) -> None:
        with pytest.raises(ValidationError):
            ManifestGroup(
                id="test",
                name="Test",
                template="t.html.j2",
                render_as="table",
                bogus_field="nope",
            )

    def test_group_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            ManifestGroup(
                id="test",
                name="Test",
                # missing template and render_as
            )


# ---------------------------------------------------------------------------
# ManifestSection groups + backward-compat (Phase 84 Plan 01)
# ---------------------------------------------------------------------------


class TestManifestSectionGroups:
    def test_section_with_groups(self) -> None:
        section = ManifestSection(
            id="financial_health",
            name="Financial Health",
            template="sections/financial.html.j2",
            groups=[
                ManifestGroup(
                    id="annual_comparison",
                    name="Annual Financial Comparison",
                    template="sections/financial/annual_comparison.html.j2",
                    render_as="financial_table",
                ),
            ],
        )
        assert len(section.groups) == 1
        assert section.groups[0].id == "annual_comparison"

    def test_backward_compat_facets_to_groups(self) -> None:
        """When groups is empty and facets is non-empty, groups auto-populates."""
        section = ManifestSection(
            id="financial_health",
            name="Financial Health",
            template="sections/financial.html.j2",
            facets=[
                ManifestFacet(
                    id="annual_comparison",
                    name="Annual Financial Comparison",
                    template="sections/financial/annual_comparison.html.j2",
                    data_type="extract_display",
                    render_as="financial_table",
                    requires=["financials.statements"],
                ),
            ],
        )
        # groups should be auto-populated from facets
        assert len(section.groups) == 1
        assert section.groups[0].id == "annual_comparison"
        assert section.groups[0].render_as == "financial_table"
        assert section.groups[0].requires == ["financials.statements"]

    def test_groups_not_overwritten_when_provided(self) -> None:
        """When groups is explicitly provided, facets don't override it."""
        section = ManifestSection(
            id="test",
            name="Test",
            template="t.html.j2",
            groups=[
                ManifestGroup(
                    id="g1", name="G1", template="g1.j2", render_as="table",
                ),
            ],
            facets=[
                ManifestFacet(
                    id="f1", name="F1", template="f1.j2",
                    data_type="extract_display", render_as="table",
                ),
            ],
        )
        # groups should remain as explicitly provided
        assert len(section.groups) == 1
        assert section.groups[0].id == "g1"

    def test_empty_section_has_empty_groups(self) -> None:
        section = ManifestSection(
            id="identity",
            name="Cover & Identity",
            template="sections/identity.html.j2",
        )
        assert section.groups == []


# ---------------------------------------------------------------------------
# Duplicate group ID detection (Phase 84 Plan 01)
# ---------------------------------------------------------------------------


class TestDuplicateGroupIds:
    def test_duplicate_group_ids_within_section_rejected(self) -> None:
        with pytest.raises(ValidationError, match="Duplicate group"):
            OutputManifest(
                manifest_version="1.0",
                sections=[
                    ManifestSection(
                        id="fin",
                        name="Financial",
                        template="f.j2",
                        groups=[
                            ManifestGroup(
                                id="dup", name="A", template="a.j2", render_as="table",
                            ),
                            ManifestGroup(
                                id="dup", name="B", template="b.j2", render_as="table",
                            ),
                        ],
                    ),
                ],
            )


# ---------------------------------------------------------------------------
# get_facet_order returns group IDs (Phase 84 Plan 01)
# ---------------------------------------------------------------------------


class TestGetFacetOrderWithGroups:
    def test_get_facet_order_returns_group_ids(self) -> None:
        manifest = OutputManifest(
            manifest_version="1.0",
            sections=[
                ManifestSection(
                    id="fin",
                    name="Financial",
                    template="f.j2",
                    groups=[
                        ManifestGroup(
                            id="x", name="X", template="x.j2", render_as="table",
                        ),
                        ManifestGroup(
                            id="y", name="Y", template="y.j2", render_as="scorecard",
                        ),
                    ],
                ),
            ],
        )
        assert get_facet_order(manifest, "fin") == ["x", "y"]


# ---------------------------------------------------------------------------
# collect_signals_by_group (Phase 84 Plan 01)
# ---------------------------------------------------------------------------


class TestCollectSignalsByGroup:
    def test_basic_grouping(self) -> None:
        signals = [
            {"id": "FIN.001", "group": "annual_comparison"},
            {"id": "FIN.002", "group": "annual_comparison"},
            {"id": "GOV.001", "group": "board_composition"},
        ]
        result = collect_signals_by_group(signals)
        assert result == {
            "annual_comparison": ["FIN.001", "FIN.002"],
            "board_composition": ["GOV.001"],
        }

    def test_empty_group_excluded(self) -> None:
        signals = [
            {"id": "FIN.001", "group": "annual_comparison"},
            {"id": "FIN.002", "group": ""},
            {"id": "FIN.003"},  # no group key at all
        ]
        result = collect_signals_by_group(signals)
        assert result == {"annual_comparison": ["FIN.001"]}

    def test_empty_signals_list(self) -> None:
        assert collect_signals_by_group([]) == {}

    def test_all_empty_groups(self) -> None:
        signals = [{"id": "A", "group": ""}, {"id": "B"}]
        assert collect_signals_by_group(signals) == {}


# ---------------------------------------------------------------------------
# ManifestSection layer field (Phase 122 Plan 01)
# ---------------------------------------------------------------------------


class TestManifestSectionLayer:
    def test_layer_decision(self) -> None:
        section = ManifestSection(
            id="identity", name="Cover", template="t.j2", layer="decision",
        )
        assert section.layer == "decision"

    def test_layer_analysis(self) -> None:
        section = ManifestSection(
            id="fin", name="Financial", template="t.j2", layer="analysis",
        )
        assert section.layer == "analysis"

    def test_layer_audit(self) -> None:
        section = ManifestSection(
            id="qa", name="QA", template="t.j2", layer="audit",
        )
        assert section.layer == "audit"

    def test_layer_invalid_rejected(self) -> None:
        with pytest.raises(ValidationError, match="layer"):
            ManifestSection(
                id="test", name="Test", template="t.j2", layer="invalid",
            )

    def test_layer_defaults_to_analysis(self) -> None:
        """Backward compat: sections without explicit layer default to analysis."""
        section = ManifestSection(
            id="test", name="Test", template="t.j2",
        )
        assert section.layer == "analysis"

    def test_load_manifest_sections_have_layer(self) -> None:
        """Every section in the real manifest has a valid layer field."""
        manifest = load_manifest()
        valid_layers = {"decision", "analysis", "audit"}
        for section in manifest.sections:
            assert section.layer in valid_layers, (
                f"Section {section.id!r} has invalid layer {section.layer!r}"
            )
