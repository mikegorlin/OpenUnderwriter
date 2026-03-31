"""Tests for do_context validation in brain health and brain audit CLI.

Verifies:
- brain health reports do_context coverage
- brain audit validates do_context template syntax
- brain audit passes on valid templates
"""

from __future__ import annotations

from do_uw.stages.analyze.do_context_engine import validate_do_context_template


class TestDoContextHealthCoverage:
    """Test do_context coverage counting logic."""

    def test_count_signals_with_do_context(self) -> None:
        """Signals with presentation.do_context should be counted."""
        signals = [
            {"id": "SIG.001", "presentation": {"do_context": {"TRIGGERED": "msg"}}},
            {"id": "SIG.002", "presentation": {"context_templates": {"TRIGGERED": "old"}}},
            {"id": "SIG.003", "presentation": {"do_context": {"CLEAR": "ok"}}},
            {"id": "SIG.004"},
        ]
        with_do_context = sum(
            1
            for s in signals
            if isinstance(s.get("presentation"), dict)
            and s["presentation"].get("do_context")
        )
        assert with_do_context == 2

    def test_empty_do_context_not_counted(self) -> None:
        """Signals with empty do_context dict should not be counted."""
        signals = [
            {"id": "SIG.001", "presentation": {"do_context": {}}},
        ]
        with_do_context = sum(
            1
            for s in signals
            if isinstance(s.get("presentation"), dict)
            and s["presentation"].get("do_context")
        )
        assert with_do_context == 0


class TestDoContextAuditValidation:
    """Test do_context template validation for brain audit."""

    def test_valid_template_passes(self) -> None:
        """Valid templates should return no errors."""
        errors = validate_do_context_template("Score {value} in {zone}")
        assert errors == []

    def test_invalid_template_detected(self) -> None:
        """Unbalanced braces should be detected."""
        errors = validate_do_context_template("Score {value")
        assert len(errors) > 0

    def test_unknown_variable_detected(self) -> None:
        """Unknown variable names should be flagged."""
        errors = validate_do_context_template("{bogus_var}")
        assert len(errors) > 0
        assert any("unknown" in e.lower() for e in errors)

    def test_details_variable_valid(self) -> None:
        """details_* variables should be accepted."""
        errors = validate_do_context_template("{details_components_score}")
        assert errors == []

    def test_audit_loop_finds_errors(self) -> None:
        """Simulate the audit loop over signals with mixed templates."""
        signals = [
            {"id": "SIG.001", "presentation": {"do_context": {"TRIGGERED": "Score {value}"}}},
            {"id": "SIG.002", "presentation": {"do_context": {"TRIGGERED": "Bad {unclosed"}}},
            {"id": "SIG.003", "presentation": {"do_context": {"CLEAR": "{zone} is clear"}}},
        ]
        found_errors: list[tuple[str, str, list[str]]] = []
        for sig in signals:
            pres = sig.get("presentation")
            if not isinstance(pres, dict):
                continue
            do_ctx = pres.get("do_context", {})
            for status_key, tmpl in do_ctx.items():
                issues = validate_do_context_template(tmpl)
                if issues:
                    found_errors.append((sig["id"], status_key, issues))

        assert len(found_errors) == 1
        assert found_errors[0][0] == "SIG.002"
        assert found_errors[0][1] == "TRIGGERED"
