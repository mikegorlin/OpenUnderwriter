"""Tests for render audit framework (Phase 92 -- REND-01/REND-02).

Verifies:
- Render exclusion config loading from YAML
- coverage.py _is_excluded() uses YAML config
- compute_render_audit() classifies fields correctly
- build_render_audit_context() transforms report for templates
"""

from __future__ import annotations

from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Test: load_render_exclusions() returns dict mapping field paths to reasons
# ---------------------------------------------------------------------------


class TestLoadRenderExclusions:
    """Tests for loading render exclusions from YAML config."""

    def test_returns_dict_mapping_paths_to_reasons(self) -> None:
        """load_render_exclusions() returns dict[str, str] with path->reason."""
        from do_uw.stages.render.coverage import load_render_exclusions

        exclusions = load_render_exclusions()
        assert isinstance(exclusions, dict)
        assert len(exclusions) > 0
        # Every key is a string path, every value is a reason string
        for path, reason in exclusions.items():
            assert isinstance(path, str), f"Path should be str: {path}"
            assert isinstance(reason, str), f"Reason should be str for {path}"
            assert len(reason) > 0, f"Reason should not be empty for {path}"

    def test_includes_all_original_exclusion_prefixes(self) -> None:
        """YAML config includes all entries from the original EXCLUSION_PREFIXES."""
        from do_uw.stages.render.coverage import (
            EXCLUSION_PREFIXES,
            load_render_exclusions,
        )

        exclusions = load_render_exclusions()
        exclusion_paths = set(exclusions.keys())

        for prefix in EXCLUSION_PREFIXES:
            assert prefix in exclusion_paths, (
                f"Original EXCLUSION_PREFIXES entry '{prefix}' "
                f"not found in render_exclusions.yaml"
            )

    def test_acquired_data_is_excluded(self) -> None:
        """acquired_data path is present in exclusions."""
        from do_uw.stages.render.coverage import load_render_exclusions

        exclusions = load_render_exclusions()
        assert "acquired_data" in exclusions

    def test_yaml_file_exists(self) -> None:
        """config/render_exclusions.yaml exists on disk."""
        from pathlib import Path

        config_path = (
            Path(__file__).resolve().parent.parent
            / "config"
            / "render_exclusions.yaml"
        )
        assert config_path.exists(), f"Expected YAML at {config_path}"


# ---------------------------------------------------------------------------
# Test: coverage.py _is_excluded() loads from YAML config
# ---------------------------------------------------------------------------


class TestIsExcludedUsesYaml:
    """Tests that _is_excluded() uses YAML config."""

    def test_excluded_path_exact_match(self) -> None:
        """Exact path match against YAML exclusion."""
        from do_uw.stages.render.coverage import _is_excluded

        assert _is_excluded("acquired_data") is True

    def test_excluded_path_prefix_match(self) -> None:
        """Prefix match (path starts with excluded prefix + dot)."""
        from do_uw.stages.render.coverage import _is_excluded

        assert _is_excluded("acquired_data.filings.10-K") is True

    def test_non_excluded_path(self) -> None:
        """Non-excluded path returns False."""
        from do_uw.stages.render.coverage import _is_excluded

        assert _is_excluded("extracted.financials.revenue") is False


# ---------------------------------------------------------------------------
# Test: compute_render_audit()
# ---------------------------------------------------------------------------


class TestComputeRenderAudit:
    """Tests for compute_render_audit() from render_audit.py."""

    def _mock_state(self) -> dict[str, Any]:
        """Build a minimal mock state dict for testing."""
        return {
            "ticker": "AAPL",
            "company": {
                "identity": {
                    "legal_name": {
                        "value": "Apple Inc.",
                        "source": "SEC",
                        "confidence": "HIGH",
                    }
                }
            },
            "acquired_data": {
                "filings": {"10-K": "content"},
            },
            "version": "1.0.0",
            "stages": {"resolve": {"status": "completed"}},
            "extracted": {
                "financials": {
                    "distress": {
                        "altman_z_score": {
                            "score": 5.23,
                            "zone": "safe",
                        }
                    }
                }
            },
        }

    def test_returns_render_audit_report(self) -> None:
        """compute_render_audit returns a RenderAuditReport dataclass."""
        from do_uw.stages.render.render_audit import (
            RenderAuditReport,
            compute_render_audit,
        )

        report = compute_render_audit(self._mock_state(), "AAPL Apple Inc. 5.23")
        assert isinstance(report, RenderAuditReport)

    def test_excluded_fields_listed(self) -> None:
        """Fields excluded by policy appear in excluded_fields."""
        from do_uw.stages.render.render_audit import compute_render_audit

        report = compute_render_audit(self._mock_state(), "AAPL Apple Inc. 5.23 safe")
        excluded_paths = [ef.path for ef in report.excluded_fields]
        # acquired_data, version, stages are all excluded by policy
        assert any("acquired_data" in p for p in excluded_paths) or report.total_excluded > 0

    def test_unrendered_fields_listed(self) -> None:
        """Fields NOT in rendered text and NOT excluded appear in unrendered_fields."""
        from do_uw.stages.render.render_audit import compute_render_audit

        # Rendered text missing the distress zone
        report = compute_render_audit(
            self._mock_state(),
            "AAPL Apple Inc.",  # missing 5.23 and 'safe'
        )
        assert len(report.unrendered_fields) > 0

    def test_classifies_excluded_vs_unrendered(self) -> None:
        """A field excluded by policy is excluded, not unrendered.
        A field missing from rendered text and not excluded is unrendered."""
        from do_uw.stages.render.render_audit import compute_render_audit

        report = compute_render_audit(
            self._mock_state(),
            "AAPL Apple Inc. 5.23 safe",
        )
        excluded_paths = {ef.path for ef in report.excluded_fields}
        unrendered_paths = set(report.unrendered_fields)

        # Excluded and unrendered should be disjoint
        overlap = excluded_paths & unrendered_paths
        assert len(overlap) == 0, f"Fields in both excluded and unrendered: {overlap}"

    def test_excluded_field_in_rendered_text_still_excluded(self) -> None:
        """An excluded field that IS in the rendered text still shows as excluded
        (policy takes precedence over rendering detection)."""
        from do_uw.stages.render.render_audit import compute_render_audit

        state = self._mock_state()
        # Render text contains "1.0.0" which is version (excluded)
        report = compute_render_audit(state, "AAPL Apple Inc. 5.23 safe 1.0.0")
        excluded_paths = {ef.path for ef in report.excluded_fields}
        unrendered_paths = set(report.unrendered_fields)

        # version is excluded by policy, should NOT appear in unrendered
        assert "version" not in unrendered_paths

    def test_report_has_correct_counts(self) -> None:
        """Report total_extracted, total_rendered, total_excluded, coverage_pct are consistent."""
        from do_uw.stages.render.render_audit import compute_render_audit

        report = compute_render_audit(
            self._mock_state(),
            "AAPL Apple Inc. 5.23 safe",
        )
        assert report.total_extracted >= 0
        assert report.total_rendered >= 0
        assert report.total_excluded >= 0
        assert report.total_rendered + len(report.unrendered_fields) + report.total_excluded == report.total_extracted
        assert 0.0 <= report.coverage_pct <= 100.0


# ---------------------------------------------------------------------------
# Test: build_render_audit_context()
# ---------------------------------------------------------------------------


class TestBuildRenderAuditContext:
    """Tests for the context builder that transforms RenderAuditReport for templates."""

    def test_transforms_report_to_dict(self) -> None:
        """build_render_audit_context returns dict with expected keys."""
        from do_uw.stages.render.render_audit import (
            ExcludedField,
            RenderAuditReport,
        )
        from do_uw.stages.render.context_builders.render_audit import (
            build_render_audit_context,
        )

        report = RenderAuditReport(
            excluded_fields=[
                ExcludedField(path="acquired_data", reason="Internal pipeline state"),
            ],
            unrendered_fields=["extracted.some_field"],
            total_extracted=10,
            total_rendered=5,
            total_excluded=4,
            coverage_pct=55.6,
        )

        ctx = build_render_audit_context(report)
        assert isinstance(ctx, dict)
        assert ctx["audit_excluded_count"] == 1
        assert ctx["audit_unrendered_count"] == 1
        assert ctx["audit_total_extracted"] == 10
        assert ctx["audit_coverage_pct"] == 55.6

    def test_excluded_fields_are_dicts(self) -> None:
        """audit_excluded_fields contains dicts with path and reason."""
        from do_uw.stages.render.render_audit import (
            ExcludedField,
            RenderAuditReport,
        )
        from do_uw.stages.render.context_builders.render_audit import (
            build_render_audit_context,
        )

        report = RenderAuditReport(
            excluded_fields=[
                ExcludedField(path="version", reason="Schema metadata"),
            ],
            unrendered_fields=[],
            total_extracted=5,
            total_rendered=4,
            total_excluded=1,
            coverage_pct=80.0,
        )

        ctx = build_render_audit_context(report)
        assert len(ctx["audit_excluded_fields"]) == 1
        item = ctx["audit_excluded_fields"][0]
        assert item["path"] == "version"
        assert item["reason"] == "Schema metadata"

    def test_unrendered_fields_are_paths(self) -> None:
        """audit_unrendered_fields is a list of path strings."""
        from do_uw.stages.render.render_audit import (
            RenderAuditReport,
        )
        from do_uw.stages.render.context_builders.render_audit import (
            build_render_audit_context,
        )

        report = RenderAuditReport(
            excluded_fields=[],
            unrendered_fields=["extracted.field_a", "extracted.field_b"],
            total_extracted=5,
            total_rendered=3,
            total_excluded=0,
            coverage_pct=60.0,
        )

        ctx = build_render_audit_context(report)
        assert ctx["audit_unrendered_fields"] == [
            "extracted.field_a",
            "extracted.field_b",
        ]

    def test_empty_report_returns_zeros(self) -> None:
        """Empty report returns zero counts."""
        from do_uw.stages.render.render_audit import RenderAuditReport
        from do_uw.stages.render.context_builders.render_audit import (
            build_render_audit_context,
        )

        report = RenderAuditReport(
            excluded_fields=[],
            unrendered_fields=[],
            total_extracted=0,
            total_rendered=0,
            total_excluded=0,
            coverage_pct=0.0,
        )

        ctx = build_render_audit_context(report)
        assert ctx["audit_excluded_count"] == 0
        assert ctx["audit_unrendered_count"] == 0
        assert ctx["audit_total_extracted"] == 0
        assert ctx["audit_coverage_pct"] == 0.0
