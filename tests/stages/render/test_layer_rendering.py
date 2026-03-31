"""Tests for layer-based worksheet rendering (Phase 122-02).

Validates:
- Every manifest section has a valid layer field
- Decision, analysis, and audit layer assignments are correct
- Analysis layer sections appear in narrative story order
- Company operations section includes both business_profile and dossier groups
- Deleted sections are not present in manifest
"""

from __future__ import annotations

from pathlib import Path

from do_uw.brain.manifest_schema import load_manifest

# Template directories
_TEMPLATE_DIR = Path(__file__).parent.parent.parent.parent / "src" / "do_uw" / "templates" / "html"

VALID_LAYERS = {"decision", "analysis", "audit"}


class TestManifestLayers:
    """Layer field validation on manifest sections."""

    def test_manifest_sections_have_layer(self) -> None:
        """Every manifest section must have a layer in (decision, analysis, audit)."""
        manifest = load_manifest()
        for section in manifest.sections:
            assert section.layer in VALID_LAYERS, (
                f"Section '{section.id}' has invalid layer: {section.layer!r}"
            )

    def test_decision_layer_sections(self) -> None:
        """Decision layer contains identity, executive_summary, red_flags."""
        manifest = load_manifest()
        decision_ids = {s.id for s in manifest.sections if s.layer == "decision"}
        expected = {"identity", "executive_summary", "red_flags"}
        assert decision_ids == expected, (
            f"Decision layer mismatch: got {decision_ids}, expected {expected}"
        )

    def test_analysis_layer_order(self) -> None:
        """Analysis layer sections appear in narrative story order."""
        manifest = load_manifest()
        analysis_ids = [s.id for s in manifest.sections if s.layer == "analysis"]
        expected_order = [
            "company_operations",
            "financial_health",
            "litigation",
            "governance",
            "market_activity",
            "forward_looking",
            "scoring",
        ]
        assert analysis_ids == expected_order, (
            f"Analysis layer order mismatch:\n  got:      {analysis_ids}\n  expected: {expected_order}"
        )

    def test_audit_layer_sections(self) -> None:
        """Audit layer contains meeting_prep, sources, qa_audit, market_overflow, coverage."""
        manifest = load_manifest()
        audit_ids = {s.id for s in manifest.sections if s.layer == "audit"}
        expected = {"meeting_prep", "sources", "qa_audit", "market_overflow", "coverage"}
        assert audit_ids == expected, (
            f"Audit layer mismatch: got {audit_ids}, expected {expected}"
        )

    def test_litigation_before_governance(self) -> None:
        """Litigation must appear before governance in the analysis layer."""
        manifest = load_manifest()
        analysis_ids = [s.id for s in manifest.sections if s.layer == "analysis"]
        lit_idx = analysis_ids.index("litigation")
        gov_idx = analysis_ids.index("governance")
        assert lit_idx < gov_idx, (
            f"Litigation (idx={lit_idx}) must come before governance (idx={gov_idx})"
        )


class TestCompanyOperationsMerge:
    """Verify company_operations includes both business_profile and dossier groups."""

    def test_company_operations_has_dossier_groups(self) -> None:
        """company_operations section contains groups from both old business_profile and intelligence_dossier."""
        manifest = load_manifest()
        co_section = next(s for s in manifest.sections if s.id == "company_operations")
        group_ids = {g.id for g in co_section.groups}

        # Business profile groups
        assert "business_description" in group_ids
        assert "business_model" in group_ids
        assert "revenue_segments" in group_ids
        assert "exposure_factors" in group_ids

        # Dossier groups
        assert "dossier_what_company_does" in group_ids
        assert "dossier_money_flows" in group_ids
        assert "dossier_revenue_model_card" in group_ids
        assert "dossier_competitive_landscape" in group_ids
        assert "dossier_emerging_risk_radar" in group_ids
        assert "dossier_asc_606" in group_ids

    def test_company_template_includes_dossier(self) -> None:
        """company.html.j2 template includes dossier sub-template references."""
        template_path = _TEMPLATE_DIR / "sections" / "company.html.j2"
        content = template_path.read_text()
        assert "dossier/what_company_does.html.j2" in content
        assert "dossier/money_flows.html.j2" in content
        assert "dossier/revenue_model_card.html.j2" in content
        assert "dossier/competitive_landscape.html.j2" in content


class TestDeletedSections:
    """Verify removed sections are not in manifest."""

    def test_no_deleted_sections(self) -> None:
        """alternative_data, adversarial_critique, ai_risk should not be in manifest."""
        manifest = load_manifest()
        section_ids = {s.id for s in manifest.sections}
        deleted = {"alternative_data", "adversarial_critique", "ai_risk"}
        found = section_ids & deleted
        assert not found, f"Deleted sections still in manifest: {found}"


class TestWorksheetTemplateStructure:
    """Verify worksheet template has layer-aware rendering."""

    def test_worksheet_has_layer_filters(self) -> None:
        """worksheet.html.j2 filters sections by layer field."""
        template_path = _TEMPLATE_DIR / "worksheet.html.j2"
        content = template_path.read_text()
        assert "section.layer == 'decision'" in content
        assert "section.layer == 'analysis'" in content
        assert "section.layer == 'audit'" in content

    def test_audit_layer_collapsed(self) -> None:
        """Audit layer sections are wrapped in a <details> element."""
        template_path = _TEMPLATE_DIR / "worksheet.html.j2"
        content = template_path.read_text()
        assert "<details" in content
        assert "audit-layer" in content
        # The audit section loop must be inside the details element
        details_start = content.index("<details")
        audit_loop = content.index("section.layer == 'audit'")
        details_end = content.index("</details>")
        assert details_start < audit_loop < details_end, (
            "Audit layer loop must be inside <details> element"
        )
