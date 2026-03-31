"""Tests for the do_context template evaluation engine.

Verifies:
- Template variable substitution from SignalResult fields
- Compound key fallback chain (TRIGGERED_RED -> TRIGGERED -> DEFAULT -> empty)
- Safe missing-variable handling (no crash on missing keys)
- Flattened details dict access via details_* keys
- Template validation for brain health/audit
"""

from __future__ import annotations

import pytest

from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus


# ---------------------------------------------------------------------------
# Helper to create SignalResult with specific fields
# ---------------------------------------------------------------------------

def _make_result(
    *,
    status: str = "TRIGGERED",
    value: str | float | None = None,
    threshold_level: str = "",
    evidence: str = "",
    source: str = "",
    confidence: str = "MEDIUM",
    threshold_context: str = "",
    details: dict | None = None,
) -> SignalResult:
    return SignalResult(
        signal_id="TEST.SIG.001",
        signal_name="Test Signal",
        status=SignalStatus(status),
        value=value,
        threshold_level=threshold_level,
        evidence=evidence,
        source=source,
        confidence=confidence,
        threshold_context=threshold_context,
        details=details or {},
    )


# ---------------------------------------------------------------------------
# PresentationSpec do_context field tests
# ---------------------------------------------------------------------------


class TestPresentationSpecDoContext:
    """Test PresentationSpec accepts do_context field."""

    def test_do_context_validates(self) -> None:
        from do_uw.brain.brain_signal_schema import PresentationSpec

        spec = PresentationSpec(do_context={"TRIGGERED_RED": "test template"})
        assert spec.do_context == {"TRIGGERED_RED": "test template"}

    def test_do_context_defaults_to_empty_dict(self) -> None:
        from do_uw.brain.brain_signal_schema import PresentationSpec

        spec = PresentationSpec()
        assert spec.do_context == {}

    def test_backward_compat_context_templates_only(self) -> None:
        from do_uw.brain.brain_signal_schema import PresentationSpec

        spec = PresentationSpec(context_templates={"TRIGGERED": "old template"})
        assert spec.context_templates == {"TRIGGERED": "old template"}
        assert spec.do_context == {}


# ---------------------------------------------------------------------------
# SignalResult do_context field tests
# ---------------------------------------------------------------------------


class TestSignalResultDoContext:
    """Test SignalResult has do_context field."""

    def test_default_empty_string(self) -> None:
        result = _make_result()
        assert result.do_context == ""

    def test_set_do_context(self) -> None:
        result = _make_result()
        result.do_context = "Score 2.5 in distress zone"
        assert result.do_context == "Score 2.5 in distress zone"


# ---------------------------------------------------------------------------
# render_do_context tests
# ---------------------------------------------------------------------------


class TestRenderDoContext:
    """Test template rendering with variable substitution."""

    def test_basic_substitution(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result(value=2.5, threshold_level="distress")
        rendered = render_do_context("Score {value} in {zone}", result)
        assert rendered == "Score 2.5 in distress"

    def test_missing_variable_returns_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result()
        rendered = render_do_context("Missing {nonexistent}", result)
        assert rendered == "Missing "

    def test_details_flattened_access(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result(details={"components": {"profitability": 0.75}})
        rendered = render_do_context("{details_components_profitability}", result)
        assert rendered == "0.75"

    def test_company_and_ticker(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result(value=3.1)
        rendered = render_do_context(
            "{company} ({ticker}) score: {value}",
            result,
            company_name="Acme Corp",
            ticker="ACME",
        )
        assert rendered == "Acme Corp (ACME) score: 3.1"

    def test_none_value_renders_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result(value=None)
        rendered = render_do_context("Value: {value}", result)
        assert rendered == "Value: "

    def test_evidence_and_source(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result(evidence="Revenue declined 15%", source="SEC_10K")
        rendered = render_do_context("{evidence} (from {source})", result)
        assert rendered == "Revenue declined 15% (from SEC_10K)"

    def test_escaped_braces(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result(value="42")
        rendered = render_do_context("Value is {{literal}} and {value}", result)
        assert rendered == "Value is {literal} and 42"

    def test_score_alias_for_value(self) -> None:
        from do_uw.stages.analyze.do_context_engine import render_do_context

        result = _make_result(value=5.5)
        rendered = render_do_context("Score: {score}", result)
        assert rendered == "Score: 5.5"


# ---------------------------------------------------------------------------
# _select_template tests
# ---------------------------------------------------------------------------


class TestSelectTemplate:
    """Test compound key fallback chain for template selection."""

    def test_triggered_red_exact_match(self) -> None:
        from do_uw.stages.analyze.do_context_engine import _select_template

        templates = {"TRIGGERED_RED": "red msg", "TRIGGERED": "generic msg"}
        assert _select_template(templates, "TRIGGERED", "red") == "red msg"

    def test_triggered_fallback_to_generic(self) -> None:
        from do_uw.stages.analyze.do_context_engine import _select_template

        templates = {"TRIGGERED": "generic msg"}
        assert _select_template(templates, "TRIGGERED", "red") == "generic msg"

    def test_default_fallback(self) -> None:
        from do_uw.stages.analyze.do_context_engine import _select_template

        templates = {"DEFAULT": "default msg"}
        assert _select_template(templates, "TRIGGERED", "red") == "default msg"

    def test_empty_dict_returns_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import _select_template

        assert _select_template({}, "TRIGGERED", "red") == ""

    def test_clear_status(self) -> None:
        from do_uw.stages.analyze.do_context_engine import _select_template

        templates = {"CLEAR": "clear msg"}
        assert _select_template(templates, "CLEAR", "") == "clear msg"

    def test_info_status(self) -> None:
        from do_uw.stages.analyze.do_context_engine import _select_template

        templates = {"INFO": "info msg", "DEFAULT": "default msg"}
        assert _select_template(templates, "INFO", "") == "info msg"

    def test_skipped_returns_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import _select_template

        templates = {"SKIPPED": "skip msg", "DEFAULT": "default msg"}
        assert _select_template(templates, "SKIPPED", "") == ""


# ---------------------------------------------------------------------------
# apply_do_context tests
# ---------------------------------------------------------------------------


class TestApplyDoContext:
    """Test end-to-end apply_do_context on SignalResult."""

    def test_populates_do_context(self) -> None:
        from do_uw.stages.analyze.do_context_engine import apply_do_context

        result = _make_result(status="TRIGGERED", value=2.5, threshold_level="red")
        sig = {
            "presentation": {
                "do_context": {
                    "TRIGGERED_RED": "Risk score {value} exceeds threshold",
                }
            }
        }
        updated = apply_do_context(result, sig, company_name="Acme", ticker="ACME")
        assert updated.do_context == "Risk score 2.5 exceeds threshold"

    def test_no_do_context_leaves_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import apply_do_context

        result = _make_result(status="TRIGGERED", value=2.5)
        sig = {"presentation": {"context_templates": {"TRIGGERED": "old"}}}
        updated = apply_do_context(result, sig)
        assert updated.do_context == ""

    def test_no_presentation_leaves_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import apply_do_context

        result = _make_result(status="TRIGGERED")
        sig = {}
        updated = apply_do_context(result, sig)
        assert updated.do_context == ""

    def test_none_presentation_leaves_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import apply_do_context

        result = _make_result(status="TRIGGERED")
        sig = {"presentation": None}
        updated = apply_do_context(result, sig)
        assert updated.do_context == ""


# ---------------------------------------------------------------------------
# validate_do_context_template tests
# ---------------------------------------------------------------------------


class TestValidateDoContextTemplate:
    """Test template syntax validation."""

    def test_valid_template_returns_empty(self) -> None:
        from do_uw.stages.analyze.do_context_engine import validate_do_context_template

        errors = validate_do_context_template("Score {value} in {zone}")
        assert errors == []

    def test_unbalanced_braces_returns_error(self) -> None:
        from do_uw.stages.analyze.do_context_engine import validate_do_context_template

        errors = validate_do_context_template("Score {value")
        assert len(errors) > 0
        assert any("format" in e.lower() for e in errors)

    def test_unknown_variable_returns_warning(self) -> None:
        from do_uw.stages.analyze.do_context_engine import validate_do_context_template

        errors = validate_do_context_template("Score {nonexistent_var}")
        assert len(errors) > 0
        assert any("unknown" in e.lower() for e in errors)

    def test_empty_template_is_valid(self) -> None:
        from do_uw.stages.analyze.do_context_engine import validate_do_context_template

        errors = validate_do_context_template("")
        assert errors == []

    def test_details_wildcard_valid(self) -> None:
        from do_uw.stages.analyze.do_context_engine import validate_do_context_template

        errors = validate_do_context_template("{details_components_profitability}")
        assert errors == []

    def test_escaped_braces_valid(self) -> None:
        from do_uw.stages.analyze.do_context_engine import validate_do_context_template

        errors = validate_do_context_template("Literal {{brace}} and {value}")
        assert errors == []
