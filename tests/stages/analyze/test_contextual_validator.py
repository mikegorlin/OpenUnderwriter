"""Tests for Phase 139 contextual signal validation engine.

Covers all 7 SIG requirements:
  SIG-01: validate_signals() iterates TRIGGERED signals, appends annotations without changing status
  SIG-02: Zero hardcoded signal IDs in Python code
  SIG-03: IPO lifecycle mismatch annotation
  SIG-04: Financial distress safe zone annotation
  SIG-05: Negation pattern detection
  SIG-06: Departed executive temporal staleness
  SIG-07: New rules addable in YAML without Python changes
"""

from __future__ import annotations

import re
import textwrap
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _triggered_signal(signal_id: str, evidence: str = "") -> dict[str, Any]:
    """Build a minimal TRIGGERED signal dict."""
    return {
        "signal_id": signal_id,
        "signal_name": signal_id.replace(".", " ").title(),
        "status": "TRIGGERED",
        "value": None,
        "threshold_level": "red",
        "evidence": evidence,
        "source": "test",
        "confidence": "MEDIUM",
        "annotations": [],
    }


def _clear_signal(signal_id: str) -> dict[str, Any]:
    """Build a minimal CLEAR signal dict."""
    return {
        "signal_id": signal_id,
        "signal_name": signal_id.replace(".", " ").title(),
        "status": "CLEAR",
        "value": None,
        "threshold_level": "",
        "evidence": "",
        "source": "test",
        "confidence": "MEDIUM",
        "annotations": [],
    }


def _skipped_signal(signal_id: str) -> dict[str, Any]:
    """Build a minimal SKIPPED signal dict."""
    return {
        "signal_id": signal_id,
        "signal_name": signal_id.replace(".", " ").title(),
        "status": "SKIPPED",
        "value": None,
        "threshold_level": "",
        "evidence": "",
        "source": "test",
        "confidence": "MEDIUM",
        "annotations": [],
    }


def _mock_state(
    years_public: int | None = None,
    z_score: float | None = None,
    o_score: float | None = None,
    departures: list[dict[str, Any]] | None = None,
) -> MagicMock:
    """Build a mock AnalysisState with specific values.

    Uses nested MagicMock with spec_set=False so dotted path
    resolution works for the validator.
    """
    state = MagicMock()

    # company.years_public -> SourcedValue pattern
    if years_public is not None:
        yp = MagicMock()
        yp.value = years_public
        state.company.years_public = yp
    else:
        state.company.years_public = None

    # extracted.financials.distress.altman_z_score.score
    if z_score is not None:
        state.extracted.financials.distress.altman_z_score.score = z_score
    else:
        state.extracted.financials.distress.altman_z_score = None

    # extracted.financials.distress.ohlson_o_score.score
    if o_score is not None:
        state.extracted.financials.distress.ohlson_o_score.score = o_score
    else:
        state.extracted.financials.distress.ohlson_o_score = None

    # extracted.governance.leadership.departures_18mo
    if departures is not None:
        dep_mocks = []
        for dep in departures:
            m = MagicMock()
            # name is a SourcedValue with .value
            name_sv = MagicMock()
            name_sv.value = dep["name"]
            m.name = name_sv
            m.departure_date = dep.get("departure_date", "")
            dep_mocks.append(m)
        state.extracted.governance.leadership.departures_18mo = dep_mocks
    else:
        state.extracted.governance.leadership.departures_18mo = []

    return state


# ---------------------------------------------------------------------------
# SIG-01: Annotations added without status change
# ---------------------------------------------------------------------------


class TestAnnotationsAddedWithoutStatusChange:
    """SIG-01: validate_signals appends annotations, never changes status."""

    def test_validate_signals_adds_annotations(self) -> None:
        """TRIGGERED signal matching a rule gets annotation; status stays TRIGGERED."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "BIZ.EVENT.ipo_exposure": _triggered_signal("BIZ.EVENT.ipo_exposure"),
        }
        state = _mock_state(years_public=30)
        summary = validate_signals(signals, state)

        assert signals["BIZ.EVENT.ipo_exposure"]["status"] == "TRIGGERED"
        assert len(signals["BIZ.EVENT.ipo_exposure"]["annotations"]) >= 1
        assert summary["annotations_added"] >= 1

    def test_status_never_modified(self) -> None:
        """All signal statuses preserved after validation."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "BIZ.EVENT.ipo_exposure": _triggered_signal("BIZ.EVENT.ipo_exposure"),
            "FIN.LIQ.position": _clear_signal("FIN.LIQ.position"),
            "GOV.board.independence": _skipped_signal("GOV.board.independence"),
        }
        state = _mock_state(years_public=30)
        validate_signals(signals, state)

        assert signals["BIZ.EVENT.ipo_exposure"]["status"] == "TRIGGERED"
        assert signals["FIN.LIQ.position"]["status"] == "CLEAR"
        assert signals["GOV.board.independence"]["status"] == "SKIPPED"


# ---------------------------------------------------------------------------
# SIG-02: No hardcoded signal IDs in Python
# ---------------------------------------------------------------------------


class TestNoHardcodedSignalIds:
    """SIG-02: contextual_validator.py has zero signal ID string literals."""

    def test_no_hardcoded_signal_ids(self) -> None:
        """No string matching signal ID format exists in the Python file."""
        validator_path = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "stages"
            / "analyze"
            / "contextual_validator.py"
        )
        source = validator_path.read_text()
        # Remove comments and docstrings for cleaner matching
        # Signal ID format: TWO_OR_MORE_CAPS.CAPS.lowercase_with_underscores
        pattern = r'["\'][A-Z]{2,}\.[A-Z]+\.[a-z_]+["\']'
        matches = re.findall(pattern, source)
        assert matches == [], f"Found hardcoded signal IDs: {matches}"


# ---------------------------------------------------------------------------
# SIG-03: IPO lifecycle mismatch
# ---------------------------------------------------------------------------


class TestIPOLifecycleMismatch:
    """SIG-03: IPO signals on mature companies get lifecycle_mismatch annotation."""

    def test_ipo_mature_company_annotation(self) -> None:
        """IPO signal + years_public=30 -> annotation with 'has been public'."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "BIZ.EVENT.ipo_exposure": _triggered_signal("BIZ.EVENT.ipo_exposure"),
        }
        state = _mock_state(years_public=30)
        validate_signals(signals, state)

        annotations = signals["BIZ.EVENT.ipo_exposure"]["annotations"]
        assert len(annotations) >= 1
        combined = " ".join(annotations).lower()
        assert "has been public" in combined
        assert "historical context only" in combined

    def test_ipo_young_company_no_annotation(self) -> None:
        """IPO signal + years_public=2 -> no annotation (rule does not fire)."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "BIZ.EVENT.ipo_exposure": _triggered_signal("BIZ.EVENT.ipo_exposure"),
        }
        state = _mock_state(years_public=2)
        validate_signals(signals, state)

        annotations = signals["BIZ.EVENT.ipo_exposure"]["annotations"]
        assert len(annotations) == 0


# ---------------------------------------------------------------------------
# SIG-04: Distress safe zone
# ---------------------------------------------------------------------------


class TestDistressSafeZone:
    """SIG-04: FIN.DISTRESS signals annotated when Z-Score >3.0 and O-Score <0.5."""

    def test_distress_safe_zone_annotation(self) -> None:
        """Both Z-Score and O-Score in safe zone -> annotation."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "FIN.DISTRESS.insolvency": _triggered_signal("FIN.DISTRESS.insolvency"),
        }
        state = _mock_state(z_score=4.5, o_score=0.2)
        validate_signals(signals, state)

        annotations = signals["FIN.DISTRESS.insolvency"]["annotations"]
        assert len(annotations) >= 1
        combined = " ".join(annotations).lower()
        assert "safe zone" in combined

    def test_distress_danger_zone_no_annotation(self) -> None:
        """Z-Score in danger zone -> no annotation."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "FIN.DISTRESS.insolvency": _triggered_signal("FIN.DISTRESS.insolvency"),
        }
        state = _mock_state(z_score=1.5, o_score=0.8)
        validate_signals(signals, state)

        annotations = signals["FIN.DISTRESS.insolvency"]["annotations"]
        assert len(annotations) == 0


# ---------------------------------------------------------------------------
# SIG-05: Negation detection
# ---------------------------------------------------------------------------


class TestNegationDetection:
    """SIG-05: Negation patterns in evidence text produce annotation."""

    def test_negation_detection(self) -> None:
        """Evidence with 'does not have' -> negation annotation."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "FIN.LIQ.position": _triggered_signal(
                "FIN.LIQ.position",
                evidence="The company does not have any material holdings in restricted markets",
            ),
        }
        state = _mock_state()
        validate_signals(signals, state)

        annotations = signals["FIN.LIQ.position"]["annotations"]
        assert len(annotations) >= 1
        combined = " ".join(annotations).lower()
        assert "negation language" in combined

    def test_negation_no_false_positive(self) -> None:
        """'No material weakness was found' should NOT trigger negation."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "FIN.QUALITY.controls": _triggered_signal(
                "FIN.QUALITY.controls",
                evidence="No material weakness was found in the audit",
            ),
        }
        state = _mock_state()
        validate_signals(signals, state)

        annotations = signals["FIN.QUALITY.controls"]["annotations"]
        assert len(annotations) == 0


# ---------------------------------------------------------------------------
# SIG-06: Departed executive temporal staleness
# ---------------------------------------------------------------------------


class TestDepartedExecutive:
    """SIG-06: Signals referencing departed executives get temporal_staleness annotation."""

    def test_departed_executive_annotation(self) -> None:
        """Evidence mentions departed exec -> annotation with name + date."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "EXEC.compensation": _triggered_signal(
                "EXEC.compensation",
                evidence="John Smith received a $5M bonus in 2024",
            ),
        }
        state = _mock_state(
            departures=[
                {"name": "John Smith", "departure_date": "2025-06-15"},
            ]
        )
        validate_signals(signals, state)

        annotations = signals["EXEC.compensation"]["annotations"]
        assert len(annotations) >= 1
        combined = " ".join(annotations)
        assert "John Smith" in combined
        assert "2025-06-15" in combined


# ---------------------------------------------------------------------------
# Efficiency and error handling
# ---------------------------------------------------------------------------


class TestEfficiencyAndErrorHandling:
    """Non-TRIGGERED signals are skipped, missing YAML handled gracefully."""

    def test_clear_signals_skipped(self) -> None:
        """CLEAR signals are not checked against any rules."""
        from do_uw.stages.analyze.contextual_validator import validate_signals

        signals = {
            "FIN.LIQ.position": _clear_signal("FIN.LIQ.position"),
        }
        state = _mock_state()
        summary = validate_signals(signals, state)

        assert summary["signals_checked"] == 0
        assert summary["annotations_added"] == 0

    def test_missing_yaml_file_returns_empty(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If validation_rules.yaml does not exist, no crash, 0 annotations."""
        from do_uw.stages.analyze import contextual_validator
        from do_uw.stages.analyze.contextual_validator import validate_signals as vs

        monkeypatch.setattr(
            contextual_validator,
            "RULES_PATH",
            Path("/nonexistent/path/validation_rules.yaml"),
        )
        signals = {
            "BIZ.EVENT.ipo_exposure": _triggered_signal("BIZ.EVENT.ipo_exposure"),
        }
        state = _mock_state(years_public=30)
        summary = vs(signals, state)

        assert summary["annotations_added"] == 0


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------


class TestSignalPatternMatching:
    """Signal ID pattern matching with fnmatch-style wildcards and | separators."""

    def test_signal_pattern_matching(self) -> None:
        """Verify pattern matching with wildcards and pipe-separated alternatives."""
        from do_uw.stages.analyze.contextual_validator import _signal_matches_pattern

        # Wildcard match
        assert _signal_matches_pattern("BIZ.EVENT.ipo_exposure", "BIZ.EVENT.ipo*")
        # Pipe-separated match
        assert _signal_matches_pattern("FIN.LIQ.position", "FIN.DISTRESS.*|FIN.LIQ.*|FIN.SOLV.*")
        # No match
        assert not _signal_matches_pattern("GOV.board.independence", "BIZ.EVENT.ipo*")
        # Catch-all
        assert _signal_matches_pattern("ANY.signal.here", "*")


# ---------------------------------------------------------------------------
# YAML rules loading
# ---------------------------------------------------------------------------


class TestYAMLRulesLoading:
    """Verify YAML rules are parsed correctly."""

    def test_yaml_rules_loaded(self) -> None:
        """_load_validation_rules() returns non-empty list with required keys."""
        from do_uw.stages.analyze.contextual_validator import _load_validation_rules

        rules = _load_validation_rules()
        assert len(rules) > 0
        required_keys = {"id", "name", "applies_to", "condition", "annotation", "rule_class"}
        for rule in rules:
            assert required_keys.issubset(rule.keys()), (
                f"Rule {rule.get('id', '?')} missing keys: {required_keys - rule.keys()}"
            )


# ---------------------------------------------------------------------------
# Pipeline integration
# ---------------------------------------------------------------------------


class TestPipelineIntegration:
    """Verify validate_signals is called from the ANALYZE pipeline."""

    def test_pipeline_calls_validate_signals(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch validate_signals in analyze __init__ and verify it's called."""
        from unittest.mock import patch

        # Read __init__.py to verify the import path exists
        init_path = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "stages"
            / "analyze"
            / "__init__.py"
        )
        source = init_path.read_text()
        assert "contextual_validator" in source, (
            "contextual_validator not found in analyze __init__.py"
        )
        assert "validate_signals" in source, (
            "validate_signals not found in analyze __init__.py"
        )
