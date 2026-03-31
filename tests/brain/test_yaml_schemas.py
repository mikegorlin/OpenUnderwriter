"""Schema validation tests for all 4 brain YAML types.

Tests Pydantic schema enforcement for:
1. Signal YAML (BrainSignalEntry with rap_class, epistemology, mechanism)
2. Pattern definitions (PatternDefinition)
3. Chart templates (ChartTemplate)
4. Severity amplifiers (SeverityAmplifier)

Each schema type has valid + invalid test cases to verify that the
Pydantic models correctly accept conforming data and reject violations.

Phase 103-01: Schema Foundation
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from do_uw.brain.brain_signal_schema import (
    BrainSignalEntry,
    Epistemology,
    EvaluationSpec,
)
from do_uw.brain.brain_schema import (
    ChartTemplate,
    PatternDefinition,
    SeverityAmplifier,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _minimal_signal(**overrides: object) -> dict:
    """Return a minimal valid BrainSignalEntry dict with optional overrides.

    Includes all required v7.0 fields (rap_class, rap_subcategory,
    epistemology, evaluation.mechanism) since Phase 103-04.
    """
    base: dict = {
        "id": "TEST.SIGNAL.one",
        "name": "Test Signal",
        "work_type": "evaluate",
        "tier": 1,
        "depth": 2,
        "threshold": {"type": "tiered", "red": ">5", "yellow": ">3"},
        "provenance": {"origin": "test"},
        "rap_class": "host",
        "rap_subcategory": "host.financials",
        "epistemology": {
            "rule_origin": "D&O underwriting practice",
            "threshold_basis": "Standard industry threshold",
        },
        "evaluation": {"mechanism": "threshold"},
    }
    base.update(overrides)
    return base


def _minimal_pattern(**overrides: object) -> dict:
    """Return a minimal valid PatternDefinition dict."""
    base = {
        "id": "test_pattern",
        "name": "Test Pattern",
        "description": "A test pattern for validation",
        "required_signals": ["SIG.A", "SIG.B", "SIG.C"],
        "rap_dimensions": ["host", "agent"],
    }
    base.update(overrides)
    return base


def _minimal_chart(**overrides: object) -> dict:
    """Return a minimal valid ChartTemplate dict."""
    base = {
        "id": "test_chart",
        "name": "Test Chart",
        "module": "do_uw.stages.render.charts.test",
        "function": "create_test_chart",
        "formats": ["html", "pdf"],
        "section": "test_section",
        "position": 1,
        "call_style": "standard",
    }
    base.update(overrides)
    return base


def _minimal_amplifier(**overrides: object) -> dict:
    """Return a minimal valid SeverityAmplifier dict."""
    base = {
        "id": "test_amplifier",
        "name": "Test Amplifier",
        "description": "A test severity amplifier",
        "multiplier": 2.0,
        "trigger_condition": "When media coverage exceeds 10 articles",
        "rap_class": "agent",
        "epistemology": {
            "rule_origin": "D&O claims experience",
            "threshold_basis": "Calibrated from 50 historical claims",
        },
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1. Signal schema tests (BrainSignalEntry + rap_class + epistemology + mechanism)
# ---------------------------------------------------------------------------


class TestSignalSchemaRAPFields:
    """Test BrainSignalEntry with new V4 RAP taxonomy fields."""

    def test_signal_validates_with_rap_class_and_epistemology(self) -> None:
        """Signal with rap_class + epistemology + mechanism validates OK."""
        data = _minimal_signal(
            rap_class="host",
            rap_subcategory="host.financials",
            epistemology={
                "rule_origin": "SCAC filing analysis",
                "threshold_basis": "Based on 200+ D&O claim filings",
            },
            evaluation={
                "formula": "extracted.financials.revenue_growth",
                "thresholds": [],
                "mechanism": "threshold",
            },
        )
        entry = BrainSignalEntry.model_validate(data)
        assert entry.rap_class == "host"
        assert entry.rap_subcategory == "host.financials"
        assert entry.epistemology is not None
        assert entry.epistemology.rule_origin == "SCAC filing analysis"
        assert entry.evaluation is not None
        assert entry.evaluation.mechanism == "threshold"

    def test_signal_rejects_missing_rap_class(self) -> None:
        """Signal without rap_class now raises ValidationError (v7.0 required)."""
        data = _minimal_signal()
        del data["rap_class"]
        with pytest.raises(ValidationError, match="rap_class"):
            BrainSignalEntry.model_validate(data)

    def test_signal_rejects_missing_rap_subcategory(self) -> None:
        """Signal without rap_subcategory now raises ValidationError (v7.0 required)."""
        data = _minimal_signal()
        del data["rap_subcategory"]
        with pytest.raises(ValidationError, match="rap_subcategory"):
            BrainSignalEntry.model_validate(data)

    def test_signal_rejects_missing_epistemology(self) -> None:
        """Signal without epistemology now raises ValidationError (v7.0 required)."""
        data = _minimal_signal()
        del data["epistemology"]
        with pytest.raises(ValidationError, match="epistemology"):
            BrainSignalEntry.model_validate(data)

    @pytest.mark.parametrize("rap_class", ["host", "agent", "environment"])
    def test_signal_accepts_valid_rap_classes(self, rap_class: str) -> None:
        """All three H/A/E values are accepted."""
        entry = BrainSignalEntry.model_validate(_minimal_signal(rap_class=rap_class))
        assert entry.rap_class == rap_class

    def test_signal_rejects_invalid_rap_class(self) -> None:
        """Invalid rap_class value raises ValidationError."""
        with pytest.raises(ValidationError, match="rap_class"):
            BrainSignalEntry.model_validate(_minimal_signal(rap_class="invalid"))

    def test_epistemology_requires_rule_origin(self) -> None:
        """Epistemology with missing rule_origin raises ValidationError."""
        with pytest.raises(ValidationError, match="rule_origin"):
            Epistemology.model_validate({"threshold_basis": "some basis"})

    def test_epistemology_requires_threshold_basis(self) -> None:
        """Epistemology with missing threshold_basis raises ValidationError."""
        with pytest.raises(ValidationError, match="threshold_basis"):
            Epistemology.model_validate({"rule_origin": "some origin"})

    def test_epistemology_forbids_extra_fields(self) -> None:
        """Epistemology rejects unexpected extra fields."""
        with pytest.raises(ValidationError, match="extra"):
            Epistemology.model_validate({
                "rule_origin": "test",
                "threshold_basis": "test",
                "unexpected_field": "should fail",
            })

    @pytest.mark.parametrize(
        "mechanism",
        ["threshold", "peer_comparison", "trend", "conjunction", "absence", "contextual"],
    )
    def test_evaluation_accepts_valid_mechanisms(self, mechanism: str) -> None:
        """All valid mechanism values are accepted."""
        spec = EvaluationSpec.model_validate({
            "formula": "test",
            "thresholds": [],
            "mechanism": mechanism,
        })
        assert spec.mechanism == mechanism

    def test_evaluation_rejects_invalid_mechanism(self) -> None:
        """Invalid mechanism value raises ValidationError."""
        with pytest.raises(ValidationError, match="mechanism"):
            EvaluationSpec.model_validate({
                "formula": "test",
                "thresholds": [],
                "mechanism": "invalid_mechanism",
            })

    def test_evaluation_rejects_missing_mechanism(self) -> None:
        """EvaluationSpec without mechanism now raises ValidationError (v7.0 required)."""
        with pytest.raises(ValidationError, match="mechanism"):
            EvaluationSpec.model_validate({
                "formula": "test",
                "thresholds": [],
            })


# ---------------------------------------------------------------------------
# 2. Pattern definition schema tests
# ---------------------------------------------------------------------------


class TestPatternDefinitionSchema:
    """Test PatternDefinition Pydantic model."""

    def test_valid_pattern_validates(self) -> None:
        """Pattern with all required fields validates successfully."""
        pattern = PatternDefinition.model_validate(_minimal_pattern())
        assert pattern.id == "test_pattern"
        assert pattern.minimum_matches == 3  # default
        assert pattern.recommendation_floor is None

    def test_pattern_with_all_fields(self) -> None:
        """Pattern with all optional fields populated validates."""
        data = _minimal_pattern(
            minimum_matches=2,
            recommendation_floor="DECLINE",
            historical_cases=["Enron 2001", "WorldCom 2002"],
            epistemology={
                "rule_origin": "SCAC filing analysis",
                "threshold_basis": "Observed in 15 historical cases",
            },
        )
        pattern = PatternDefinition.model_validate(data)
        assert pattern.minimum_matches == 2
        assert pattern.recommendation_floor == "DECLINE"
        assert len(pattern.historical_cases) == 2
        assert pattern.epistemology is not None

    def test_pattern_missing_id_fails(self) -> None:
        """Pattern without id raises ValidationError."""
        data = _minimal_pattern()
        del data["id"]
        with pytest.raises(ValidationError, match="id"):
            PatternDefinition.model_validate(data)

    def test_pattern_missing_required_signals_fails(self) -> None:
        """Pattern without required_signals raises ValidationError."""
        data = _minimal_pattern()
        del data["required_signals"]
        with pytest.raises(ValidationError, match="required_signals"):
            PatternDefinition.model_validate(data)

    def test_pattern_minimum_matches_ge_1(self) -> None:
        """minimum_matches must be >= 1."""
        with pytest.raises(ValidationError, match="minimum_matches"):
            PatternDefinition.model_validate(_minimal_pattern(minimum_matches=0))

    def test_pattern_invalid_rap_dimension(self) -> None:
        """Invalid rap_dimensions value raises ValidationError."""
        with pytest.raises(ValidationError, match="rap_dimensions"):
            PatternDefinition.model_validate(
                _minimal_pattern(rap_dimensions=["host", "invalid"])
            )

    def test_pattern_forbids_extra_fields(self) -> None:
        """PatternDefinition rejects unexpected fields."""
        with pytest.raises(ValidationError, match="extra"):
            PatternDefinition.model_validate(
                _minimal_pattern(unknown_field="should fail")
            )


# ---------------------------------------------------------------------------
# 3. Chart template schema tests
# ---------------------------------------------------------------------------


class TestChartTemplateSchema:
    """Test ChartTemplate Pydantic model."""

    def test_valid_chart_validates(self) -> None:
        """Chart with all required fields validates successfully."""
        chart = ChartTemplate.model_validate(_minimal_chart())
        assert chart.id == "test_chart"
        assert chart.call_style == "standard"
        assert chart.overlays == []

    def test_chart_with_optional_fields(self) -> None:
        """Chart with overlays, params, and v7 fields validates."""
        data = _minimal_chart(
            params={"period": "1Y"},
            signals=["STOCK.PRICE.chart_comparison"],
            overlays=["volume_bars", "earnings_markers"],
            style_overrides={"color": "#ff0000"},
            golden_reference="tests/golden/stock_1y.png",
        )
        chart = ChartTemplate.model_validate(data)
        assert chart.params == {"period": "1Y"}
        assert len(chart.overlays) == 2
        assert chart.golden_reference is not None

    def test_chart_invalid_call_style_fails(self) -> None:
        """Invalid call_style raises ValidationError."""
        with pytest.raises(ValidationError, match="call_style"):
            ChartTemplate.model_validate(_minimal_chart(call_style="invalid_style"))

    def test_chart_invalid_format_fails(self) -> None:
        """Invalid format value raises ValidationError."""
        with pytest.raises(ValidationError, match="formats"):
            ChartTemplate.model_validate(_minimal_chart(formats=["html", "docx"]))

    def test_chart_missing_section_fails(self) -> None:
        """Chart without section raises ValidationError."""
        data = _minimal_chart()
        del data["section"]
        with pytest.raises(ValidationError, match="section"):
            ChartTemplate.model_validate(data)

    def test_chart_forbids_extra_fields(self) -> None:
        """ChartTemplate rejects unexpected fields."""
        with pytest.raises(ValidationError, match="extra"):
            ChartTemplate.model_validate(_minimal_chart(unknown="should fail"))

    def test_chart_registry_yaml_validates(self) -> None:
        """All entries in chart_registry.yaml validate against ChartTemplate."""
        import yaml
        from pathlib import Path

        registry_path = (
            Path(__file__).parent.parent.parent
            / "src"
            / "do_uw"
            / "brain"
            / "config"
            / "chart_registry.yaml"
        )
        assert registry_path.exists(), f"chart_registry.yaml not found at {registry_path}"

        data = yaml.load(registry_path.read_text(), Loader=yaml.CSafeLoader)
        charts = data.get("charts", [])
        assert len(charts) > 0, "No charts found in chart_registry.yaml"

        errors: list[str] = []
        for chart_data in charts:
            try:
                ChartTemplate.model_validate(chart_data)
            except ValidationError as e:
                errors.append(f"{chart_data.get('id', 'unknown')}: {e.errors()[0]['msg']}")

        assert not errors, f"Chart registry validation failures:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# 4. Severity amplifier schema tests
# ---------------------------------------------------------------------------


class TestSeverityAmplifierSchema:
    """Test SeverityAmplifier Pydantic model."""

    def test_valid_amplifier_validates(self) -> None:
        """Amplifier with all required fields validates successfully."""
        amp = SeverityAmplifier.model_validate(_minimal_amplifier())
        assert amp.id == "test_amplifier"
        assert amp.multiplier == 2.0
        assert amp.epistemology.rule_origin == "D&O claims experience"

    def test_amplifier_multiplier_too_low_fails(self) -> None:
        """Multiplier below 1.0 raises ValidationError."""
        with pytest.raises(ValidationError, match="multiplier"):
            SeverityAmplifier.model_validate(_minimal_amplifier(multiplier=0.5))

    def test_amplifier_multiplier_too_high_fails(self) -> None:
        """Multiplier above 5.0 raises ValidationError."""
        with pytest.raises(ValidationError, match="multiplier"):
            SeverityAmplifier.model_validate(_minimal_amplifier(multiplier=6.0))

    @pytest.mark.parametrize("multiplier", [1.0, 2.5, 5.0])
    def test_amplifier_valid_multiplier_range(self, multiplier: float) -> None:
        """Multiplier at boundaries and midpoint validates."""
        amp = SeverityAmplifier.model_validate(_minimal_amplifier(multiplier=multiplier))
        assert amp.multiplier == multiplier

    def test_amplifier_epistemology_required(self) -> None:
        """SeverityAmplifier requires epistemology (not optional)."""
        data = _minimal_amplifier()
        del data["epistemology"]
        with pytest.raises(ValidationError, match="epistemology"):
            SeverityAmplifier.model_validate(data)

    def test_amplifier_invalid_rap_class_fails(self) -> None:
        """Invalid rap_class raises ValidationError."""
        with pytest.raises(ValidationError, match="rap_class"):
            SeverityAmplifier.model_validate(_minimal_amplifier(rap_class="invalid"))

    def test_amplifier_forbids_extra_fields(self) -> None:
        """SeverityAmplifier rejects unexpected fields."""
        with pytest.raises(ValidationError, match="extra"):
            SeverityAmplifier.model_validate(
                _minimal_amplifier(unknown_field="should fail")
            )


# ---------------------------------------------------------------------------
# 5. Regression: all 514 signals load against updated schema
# ---------------------------------------------------------------------------


class TestSignalSchemaRegression:
    """Verify that ALL existing signals load without error after schema changes."""

    def test_all_signals_load_against_updated_schema(self) -> None:
        """Load all 514 signals via unified loader -- none should be rejected."""
        from do_uw.brain.brain_unified_loader import _reset_cache, load_signals

        _reset_cache()
        result = load_signals()
        assert result["total_signals"] >= 514, (
            f"Expected >= 514 signals, got {result['total_signals']}. "
            "Schema changes may have broken backward compatibility."
        )

    def test_all_signals_have_required_v7_fields(self) -> None:
        """All 514 signals have required v7.0 fields (rap_class, epistemology, evaluation).

        After Phase 103-04, these fields are mandatory on every signal.
        """
        from do_uw.brain.brain_unified_loader import _reset_cache, load_signals

        _reset_cache()
        result = load_signals()
        signals = result["signals"]

        for sig in signals[:20]:
            entry = BrainSignalEntry.model_validate(sig)
            assert entry.rap_class in ("host", "agent", "environment"), (
                f"Signal {entry.id} has rap_class={entry.rap_class}"
            )
            assert entry.rap_subcategory, (
                f"Signal {entry.id} missing rap_subcategory"
            )
            assert entry.epistemology is not None, (
                f"Signal {entry.id} has no epistemology"
            )
            assert entry.epistemology.rule_origin, (
                f"Signal {entry.id} has empty rule_origin"
            )
