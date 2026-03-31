"""Tests for OutputSanitizer — post-render HTML sanitization safety net."""

from __future__ import annotations

import time

import pytest


class TestMarkdownSanitization:
    """Category: markdown artifacts stripped from HTML text nodes."""

    def test_strips_bold_markers(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>Revenue is **$3.2B** for the year</p>"
        result, log = sanitizer.sanitize(html)
        assert "**" not in result
        assert "$3.2B" in result
        assert log.total_substitutions >= 1

    def test_strips_heading_markers(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>### Financial Overview</p>"
        result, _log = sanitizer.sanitize(html)
        assert "###" not in result
        assert "Financial Overview" in result

    def test_strips_horizontal_rules(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>---</p>"
        result, _log = sanitizer.sanitize(html)
        assert "---" not in result

    def test_strips_backtick_code_markers(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>The `revenue` metric shows growth</p>"
        result, _log = sanitizer.sanitize(html)
        assert "`" not in result
        assert "revenue" in result


class TestPythonSerialSanitization:
    """Category: raw Python serialization patterns."""

    def test_strips_python_list_single_quotes(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<td>['item1', 'item2']</td>"
        result, log = sanitizer.sanitize(html)
        assert "['item1'" not in result
        assert "item1, item2" in result
        assert log.total_substitutions >= 1

    def test_strips_python_list_double_quotes(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = '<td>["item1", "item2"]</td>'
        result, _log = sanitizer.sanitize(html)
        assert '["item1"' not in result
        assert "item1, item2" in result

    def test_strips_python_dict(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<td>{'key': 'val'}</td>"
        result, _log = sanitizer.sanitize(html)
        assert "{'key'" not in result

    def test_strips_python_dict_double_quotes(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = '<td>{"key": "value"}</td>'
        result, _log = sanitizer.sanitize(html)
        assert '{"key"' not in result

    def test_replaces_standalone_none(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<td>None</td>"
        result, _log = sanitizer.sanitize(html)
        assert ">N/A<" in result

    def test_preserves_none_in_prose(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>None of the directors resigned</p>"
        result, _log = sanitizer.sanitize(html)
        assert "None of the" in result

    def test_replaces_standalone_true_false(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<td>True</td><td>False</td>"
        result, _log = sanitizer.sanitize(html)
        assert "Yes" in result
        assert "No" in result


class TestJargonSanitization:
    """Category: system jargon that leaked past Jinja filters."""

    def test_strips_known_codes(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>DATA_UNAVAILABLE</p>"
        result, _log = sanitizer.sanitize(html)
        assert "DATA_UNAVAILABLE" not in result
        assert "N/A" in result

    def test_strips_factor_code_patterns(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>F.7 = 5/8 indicates elevated risk</p>"
        result, _log = sanitizer.sanitize(html)
        assert "F.7 = 5/8" not in result
        # The meaningful content should remain
        assert "elevated risk" in result or "risk" in result

    def test_strips_signal_count_jargon(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>19 signals triggered in this category</p>"
        result, _log = sanitizer.sanitize(html)
        assert "signals triggered" not in result

    def test_strips_threshold_context(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        # In real HTML, < would be &lt; — test with a realistic threshold
        html = "<p>Cash ratio is low (threshold: Cash Ratio &lt; 0.5)</p>"
        result, _log = sanitizer.sanitize(html)
        assert "(threshold:" not in result
        assert "Cash ratio is low" in result

    def test_strips_evaluation_method(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>evaluation_method: threshold_compare</p>"
        result, _log = sanitizer.sanitize(html)
        assert "evaluation_method:" not in result

    def test_strips_schema_version(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>schema_version: 4</p>"
        result, _log = sanitizer.sanitize(html)
        assert "schema_version:" not in result

    def test_strips_coverage_display(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>coverage=100% across all checks</p>"
        result, _log = sanitizer.sanitize(html)
        assert "coverage=100%" not in result


class TestDebugSanitization:
    """Category: debug/development artifacts."""

    def test_strips_class_repr(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p><class 'do_uw.models.state.AnalysisState'></p>"
        result, _log = sanitizer.sanitize(html)
        assert "<class '" not in result

    def test_strips_traceback(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>Traceback (most recent call last)</p>"
        result, _log = sanitizer.sanitize(html)
        assert "Traceback" not in result


class TestPreservation:
    """Sanitizer must NOT modify certain elements."""

    def test_preserves_script_content(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = '<script>var x = ["a", "b"]; if (x === None) {}</script>'
        result, log = sanitizer.sanitize(html)
        assert '["a", "b"]' in result
        assert log.total_substitutions == 0

    def test_preserves_style_content(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<style>.bold { font-weight: **bold**; }</style>"
        result, log = sanitizer.sanitize(html)
        assert "**bold**" in result
        assert log.total_substitutions == 0

    def test_preserves_data_attributes(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = '<div data-config=\'{"key": "val"}\'>Clean text</div>'
        result, log = sanitizer.sanitize(html)
        assert '{"key": "val"}' in result
        assert log.total_substitutions == 0

    def test_no_false_positive_on_clean_text(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>Revenue is $3.2B</p>"
        result, log = sanitizer.sanitize(html)
        assert result.strip() == html.strip() or "Revenue is $3.2B" in result
        assert log.total_substitutions == 0


class TestSanitizationLog:
    """SanitizationLog records substitutions with context."""

    def test_log_records_entries(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>**bold text** and DATA_UNAVAILABLE</p>"
        _result, log = sanitizer.sanitize(html)
        assert log.total_substitutions >= 2
        assert len(log.entries) >= 2
        categories = {e.category for e in log.entries}
        assert "markdown" in categories
        assert "jargon" in categories

    def test_log_entry_has_fields(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<p>**bold**</p>"
        _result, log = sanitizer.sanitize(html)
        entry = log.entries[0]
        assert entry.category == "markdown"
        assert entry.pattern_name
        assert entry.matched_text
        assert entry.replacement is not None
        assert entry.line_context

    def test_sanitize_returns_tuple(self):
        from do_uw.stages.render.output_sanitizer import (
            OutputSanitizer,
            SanitizationLog,
        )

        sanitizer = OutputSanitizer.from_defaults()
        result = sanitizer.sanitize("<p>clean</p>")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], SanitizationLog)

    def test_log_summary(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        _result, log = sanitizer.sanitize("<p>**bold** and ['list']</p>")
        summary = log.summary()
        assert isinstance(summary, str)
        assert len(summary) > 0


class TestEdgeCases:
    """Edge cases for robustness."""

    def test_empty_string(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        result, log = sanitizer.sanitize("")
        assert result == ""
        assert log.total_substitutions == 0

    def test_html_with_no_text_nodes(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<div><img src='x.png'/><br/></div>"
        result, log = sanitizer.sanitize(html)
        assert log.total_substitutions == 0

    def test_nested_tags_mixed_content(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = "<div><p>Clean text</p><p>**dirty** text</p><p>Also clean</p></div>"
        result, log = sanitizer.sanitize(html)
        assert "**" not in result
        assert "Clean text" in result
        assert "dirty" in result
        assert "Also clean" in result

    def test_preserves_data_raw_escape_hatch(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        html = '<div data-raw="true">**intentional markdown**</div>'
        result, _log = sanitizer.sanitize(html)
        assert "**intentional markdown**" in result

    def test_performance_large_html(self):
        from do_uw.stages.render.output_sanitizer import OutputSanitizer

        sanitizer = OutputSanitizer.from_defaults()
        # Build ~500KB of HTML
        chunk = "<p>Revenue is $3.2B for the fiscal year ending December 2025. " * 20 + "</p>"
        html = chunk * 200  # ~500KB
        start = time.time()
        result, _log = sanitizer.sanitize(html)
        elapsed = time.time() - start
        assert elapsed < 2.0, f"Sanitization took {elapsed:.2f}s (> 2s budget)"
        assert len(result) > 0
