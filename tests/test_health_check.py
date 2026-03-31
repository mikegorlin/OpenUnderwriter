"""Tests for health check heuristics (Phase 92 -- REND-03/REND-04).

Verifies:
- LLM text marker detection in rendered HTML
- Zero placeholder detection with allowlist
- Empty percentage/value detection
- Health check config loading from YAML
- Aggregation into HealthCheckReport
- Integration with RenderAuditReport
"""

from __future__ import annotations

from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Test: detect_llm_markers()
# ---------------------------------------------------------------------------


class TestDetectLlmMarkers:
    """Tests for LLM text marker detection in rendered HTML."""

    def test_detects_based_on_filing(self) -> None:
        """detect_llm_markers finds 'Based on the filing' in rendered text."""
        from do_uw.stages.render.health_check import (
            HealthIssue,
            detect_llm_markers,
            load_health_config,
        )

        config = load_health_config()
        html = '<section id="overview"><p>Based on the filing, the company has strong revenue growth.</p></section>'
        issues = detect_llm_markers(html, config)
        assert len(issues) >= 1
        assert any(i.category == "llm_text" for i in issues)
        assert any(i.severity == "MEDIUM" for i in issues)
        assert any("Based on the filing" in i.snippet for i in issues)

    def test_detects_markdown_formatting(self) -> None:
        """detect_llm_markers finds markdown formatting (## heading, **bold**)."""
        from do_uw.stages.render.health_check import (
            detect_llm_markers,
            load_health_config,
        )

        config = load_health_config()
        html = '<section id="risk"><p>## Risk Factors Overview</p><p>**Important** consideration here.</p></section>'
        issues = detect_llm_markers(html, config)
        assert len(issues) >= 1
        # Should find both ## and **
        snippets = " ".join(i.snippet for i in issues)
        assert "##" in snippets or "**" in snippets

    def test_detects_i_cannot_determine(self) -> None:
        """detect_llm_markers finds 'I cannot determine' pattern."""
        from do_uw.stages.render.health_check import (
            detect_llm_markers,
            load_health_config,
        )

        config = load_health_config()
        html = '<section id="scoring"><p>I cannot determine the exact risk level from available data.</p></section>'
        issues = detect_llm_markers(html, config)
        assert len(issues) >= 1
        assert any("I cannot determine" in i.snippet for i in issues)

    def test_does_not_flag_normal_text(self) -> None:
        """detect_llm_markers does NOT flag normal text that doesn't match markers."""
        from do_uw.stages.render.health_check import (
            detect_llm_markers,
            load_health_config,
        )

        config = load_health_config()
        html = '<section id="overview"><p>Apple Inc. reported strong revenue growth of $394.3B in fiscal 2024.</p></section>'
        issues = detect_llm_markers(html, config)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Test: detect_zero_placeholders()
# ---------------------------------------------------------------------------


class TestDetectZeroPlaceholders:
    """Tests for zero placeholder detection with allowlist."""

    def test_flags_zero_in_non_allowlisted_field(self) -> None:
        """detect_zero_placeholders flags 0.0 in a non-allowlisted field context."""
        from do_uw.stages.render.health_check import (
            detect_zero_placeholders,
            load_health_config,
        )

        config = load_health_config()
        html = '<table><tr><th>Revenue</th><td>0.0</td></tr></table>'
        state_dict: dict[str, Any] = {}
        issues = detect_zero_placeholders(html, state_dict, config)
        assert len(issues) >= 1
        assert any(i.category == "zero_placeholder" for i in issues)

    def test_does_not_flag_zero_in_allowlisted_field(self) -> None:
        """detect_zero_placeholders does NOT flag 0.0 when field context matches allowlist."""
        from do_uw.stages.render.health_check import (
            detect_zero_placeholders,
            load_health_config,
        )

        config = load_health_config()
        # "dividends" is in the allowlist
        html = '<table><tr><th>Dividends</th><td>0.0</td></tr></table>'
        state_dict: dict[str, Any] = {}
        issues = detect_zero_placeholders(html, state_dict, config)
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# Test: detect_empty_percentages()
# ---------------------------------------------------------------------------


class TestDetectEmptyPercentages:
    """Tests for empty percentage/value detection."""

    def test_flags_empty_na_in_percentage_context(self) -> None:
        """detect_empty_percentages flags N/A in percentage-typed table cells."""
        from do_uw.stages.render.health_check import (
            detect_empty_percentages,
            load_health_config,
        )

        config = load_health_config()
        html = '<table><thead><tr><th>Metric</th><th>%</th></tr></thead><tbody><tr><td>Growth</td><td>N/A</td></tr></tbody></table>'
        issues = detect_empty_percentages(html, config)
        assert len(issues) >= 1
        assert any(i.category == "empty_value" for i in issues)

    def test_catches_not_available_in_numeric_context(self) -> None:
        """detect_empty_percentages catches 'Not Available' in numeric contexts."""
        from do_uw.stages.render.health_check import (
            detect_empty_percentages,
            load_health_config,
        )

        config = load_health_config()
        html = '<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody><tr><td>ROE</td><td>Not Available</td></tr></tbody></table>'
        issues = detect_empty_percentages(html, config)
        assert len(issues) >= 1
        assert any("Not Available" in i.snippet for i in issues)


# ---------------------------------------------------------------------------
# Test: run_health_checks() aggregation
# ---------------------------------------------------------------------------


class TestRunHealthChecks:
    """Tests for health check aggregation."""

    def test_aggregates_all_detectors(self) -> None:
        """run_health_checks aggregates all three detectors into a HealthCheckReport."""
        from do_uw.stages.render.health_check import (
            HealthCheckReport,
            run_health_checks,
        )

        html = (
            '<section id="test">'
            "<p>Based on the filing, growth is strong.</p>"
            "<table><tr><th>Revenue</th><td>0.0</td></tr></table>"
            '<table><thead><tr><th>Metric</th><th>%</th></tr></thead>'
            "<tbody><tr><td>Growth</td><td>N/A</td></tr></tbody></table>"
            "</section>"
        )
        state_dict: dict[str, Any] = {}
        report = run_health_checks(html, state_dict)
        assert isinstance(report, HealthCheckReport)
        assert report.llm_text_count >= 1
        assert report.zero_placeholder_count >= 1
        assert report.empty_value_count >= 1
        assert len(report.issues) >= 3


# ---------------------------------------------------------------------------
# Test: health issues integrated into RenderAuditReport
# ---------------------------------------------------------------------------


class TestHealthIssueIntegration:
    """Tests for health issue integration with RenderAuditReport."""

    def test_health_issues_in_render_audit_report(self) -> None:
        """Health issues are added to RenderAuditReport.health_issues."""
        from do_uw.stages.render.render_audit import (
            RenderAuditReport,
        )

        # Verify the field exists on the dataclass
        report = RenderAuditReport()
        assert hasattr(report, "health_issues")
        assert isinstance(report.health_issues, list)
        assert len(report.health_issues) == 0

    def test_health_issues_surfaced_in_context_builder(self) -> None:
        """Health issues are surfaced in context builder output."""
        from do_uw.stages.render.health_check import HealthIssue
        from do_uw.stages.render.render_audit import (
            ExcludedField,
            RenderAuditReport,
        )
        from do_uw.stages.render.context_builders.render_audit import (
            build_render_audit_context,
        )

        issue = HealthIssue(
            category="llm_text",
            severity="MEDIUM",
            location="section#overview",
            message="Raw LLM text detected",
            snippet="Based on the filing...",
        )
        report = RenderAuditReport(
            excluded_fields=[],
            unrendered_fields=[],
            total_extracted=10,
            total_rendered=10,
            total_excluded=0,
            coverage_pct=100.0,
            health_issues=[issue],
        )

        ctx = build_render_audit_context(report)
        assert "audit_health_issues" in ctx
        assert "audit_health_count" in ctx
        assert ctx["audit_health_count"] == 1
        assert len(ctx["audit_health_issues"]) == 1
        hi = ctx["audit_health_issues"][0]
        assert hi["category"] == "llm_text"
        assert hi["severity"] == "MEDIUM"


# ---------------------------------------------------------------------------
# Test: config loading
# ---------------------------------------------------------------------------


class TestHealthCheckConfig:
    """Tests for health check config loading from YAML."""

    def test_config_loads_from_yaml(self) -> None:
        """Health check config loads from config/health_check.yaml."""
        from do_uw.stages.render.health_check import load_health_config

        config = load_health_config()
        assert isinstance(config, dict)
        assert "llm_markers" in config
        assert "zero_valid_fields" in config
        assert "empty_value_patterns" in config

    def test_llm_markers_is_list(self) -> None:
        """llm_markers is a list of pattern strings."""
        from do_uw.stages.render.health_check import load_health_config

        config = load_health_config()
        markers = config["llm_markers"]
        assert isinstance(markers, list)
        assert len(markers) > 0
        assert all(isinstance(m, str) for m in markers)
        # Should include the key patterns
        assert any("Based on the filing" in m for m in markers)

    def test_zero_valid_fields_is_list(self) -> None:
        """zero_valid_fields is a list of field name strings."""
        from do_uw.stages.render.health_check import load_health_config

        config = load_health_config()
        fields = config["zero_valid_fields"]
        assert isinstance(fields, list)
        assert "dividends" in fields
        assert "short_interest" in fields
