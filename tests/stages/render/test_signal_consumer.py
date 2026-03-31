"""Unit tests for _signal_consumer.py typed extraction functions.

Tests all 7 consumer functions with realistic signal data structures
matching the format stored in state.analysis.signal_results.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any
from unittest.mock import patch

import pytest

from do_uw.stages.render.context_builders._signal_consumer import (
    SignalResultView,
    get_signal_epistemology,
    get_signal_level,
    get_signal_result,
    get_signal_status,
    get_signal_value,
    get_signals_by_prefix,
    signal_to_display_level,
)

# ---------------------------------------------------------------------------
# Realistic test fixtures
# ---------------------------------------------------------------------------

SAMPLE_RESULTS: dict[str, Any] = {
    "FIN.PROFIT.revenue": {
        "signal_id": "FIN.PROFIT.revenue",
        "signal_name": "Revenue Analysis",
        "status": "TRIGGERED",
        "value": -0.25,
        "threshold_level": "red",
        "evidence": "Revenue declined 25% YoY",
        "source": "SEC_10K",
        "confidence": "HIGH",
        "threshold_context": "red: Revenue decline >20%",
        "factors": ["F6"],
        "section": 3,
        "details": {"yoy_change": -0.25},
        "data_status": "EVALUATED",
        "content_type": "EVALUATIVE_CHECK",
        "category": "DECISION_DRIVING",
    },
    "FIN.PROFIT.margins": {
        "signal_id": "FIN.PROFIT.margins",
        "signal_name": "Margin Analysis",
        "status": "CLEAR",
        "value": 0.15,
        "threshold_level": "clear",
        "evidence": "Gross margin at 15%, within normal range",
        "source": "SEC_10K",
        "confidence": "HIGH",
        "threshold_context": "",
        "factors": ["F6"],
        "section": 3,
        "details": {},
        "data_status": "EVALUATED",
        "content_type": "EVALUATIVE_CHECK",
        "category": "DECISION_DRIVING",
    },
    "GOV.BOARD.independence": {
        "signal_id": "GOV.BOARD.independence",
        "signal_name": "Board Independence",
        "status": "SKIPPED",
        "value": None,
        "threshold_level": "",
        "evidence": "Proxy data not available",
        "source": "",
        "confidence": "LOW",
        "threshold_context": "",
        "factors": [],
        "section": 4,
        "details": {},
        "data_status": "DATA_UNAVAILABLE",
        "content_type": "EVALUATIVE_CHECK",
        "category": "DECISION_DRIVING",
    },
    "MKT.PRICE.info_metric": {
        "signal_id": "MKT.PRICE.info_metric",
        "signal_name": "Market Price Info",
        "status": "INFO",
        "value": 142.50,
        "threshold_level": "",
        "evidence": "Current share price $142.50",
        "source": "MARKET_PRICE",
        "confidence": "HIGH",
        "threshold_context": "",
        "factors": [],
        "section": 2,
        "details": {},
        "data_status": "EVALUATED",
        "content_type": "EVALUATIVE_CHECK",
        "category": "CONTEXT_DISPLAY",
    },
}

MOCK_BRAIN_SIGNAL: dict[str, Any] = {
    "id": "FIN.PROFIT.revenue",
    "rap_class": "host",
    "rap_subcategory": "host.financials",
    "evaluation": {"mechanism": "threshold"},
    "epistemology": {
        "rule_origin": "SCAC filing analysis",
        "threshold_basis": "Revenue decline >20% correlates with 3x SCA frequency",
    },
}


def _mock_get_brain_signal(signal_id: str) -> dict[str, Any] | None:
    """Mock brain signal lookup returning controlled data."""
    if signal_id == "FIN.PROFIT.revenue":
        return MOCK_BRAIN_SIGNAL
    return None


# ---------------------------------------------------------------------------
# get_signal_result
# ---------------------------------------------------------------------------


@patch(
    "do_uw.stages.render.context_builders._signal_consumer._get_brain_signal",
    side_effect=_mock_get_brain_signal,
)
class TestGetSignalResult:
    def test_returns_view(self, _mock: Any) -> None:
        view = get_signal_result(SAMPLE_RESULTS, "FIN.PROFIT.revenue")
        assert view is not None
        assert isinstance(view, SignalResultView)
        assert view.signal_id == "FIN.PROFIT.revenue"
        assert view.status == "TRIGGERED"
        assert view.value == -0.25
        assert view.threshold_level == "red"
        assert view.evidence == "Revenue declined 25% YoY"
        assert view.source == "SEC_10K"
        assert view.confidence == "HIGH"
        assert view.factors == ("F6",)
        assert view.data_status == "EVALUATED"
        assert view.content_type == "EVALUATIVE_CHECK"
        assert view.category == "DECISION_DRIVING"

    def test_missing_returns_none(self, _mock: Any) -> None:
        result = get_signal_result(SAMPLE_RESULTS, "NONEXISTENT.SIGNAL")
        assert result is None

    def test_non_dict_returns_none(self, _mock: Any) -> None:
        bad_results: dict[str, Any] = {"BAD.SIG": "not_a_dict"}
        result = get_signal_result(bad_results, "BAD.SIG")
        assert result is None


# ---------------------------------------------------------------------------
# get_signal_value
# ---------------------------------------------------------------------------


class TestGetSignalValue:
    def test_returns_value(self) -> None:
        assert get_signal_value(SAMPLE_RESULTS, "FIN.PROFIT.revenue") == -0.25

    def test_returns_float(self) -> None:
        assert get_signal_value(SAMPLE_RESULTS, "MKT.PRICE.info_metric") == 142.50

    def test_missing_returns_none(self) -> None:
        assert get_signal_value(SAMPLE_RESULTS, "NONEXISTENT") is None

    def test_none_value_returns_none(self) -> None:
        assert get_signal_value(SAMPLE_RESULTS, "GOV.BOARD.independence") is None


# ---------------------------------------------------------------------------
# get_signal_status
# ---------------------------------------------------------------------------


class TestGetSignalStatus:
    def test_returns_status(self) -> None:
        assert get_signal_status(SAMPLE_RESULTS, "FIN.PROFIT.revenue") == "TRIGGERED"

    def test_returns_clear(self) -> None:
        assert get_signal_status(SAMPLE_RESULTS, "FIN.PROFIT.margins") == "CLEAR"

    def test_returns_skipped(self) -> None:
        assert get_signal_status(SAMPLE_RESULTS, "GOV.BOARD.independence") == "SKIPPED"

    def test_missing_returns_none(self) -> None:
        assert get_signal_status(SAMPLE_RESULTS, "NONEXISTENT") is None


# ---------------------------------------------------------------------------
# get_signal_level
# ---------------------------------------------------------------------------


class TestGetSignalLevel:
    def test_returns_level(self) -> None:
        assert get_signal_level(SAMPLE_RESULTS, "FIN.PROFIT.revenue") == "red"

    def test_returns_clear(self) -> None:
        assert get_signal_level(SAMPLE_RESULTS, "FIN.PROFIT.margins") == "clear"

    def test_missing_returns_empty(self) -> None:
        assert get_signal_level(SAMPLE_RESULTS, "NONEXISTENT") == ""

    def test_empty_level_returns_empty(self) -> None:
        assert get_signal_level(SAMPLE_RESULTS, "GOV.BOARD.independence") == ""


# ---------------------------------------------------------------------------
# get_signals_by_prefix
# ---------------------------------------------------------------------------


@patch(
    "do_uw.stages.render.context_builders._signal_consumer._get_brain_signal",
    side_effect=_mock_get_brain_signal,
)
class TestGetSignalsByPrefix:
    def test_fin_prefix(self, _mock: Any) -> None:
        views = get_signals_by_prefix(SAMPLE_RESULTS, "FIN.")
        assert len(views) == 2
        ids = {v.signal_id for v in views}
        assert ids == {"FIN.PROFIT.revenue", "FIN.PROFIT.margins"}

    def test_fin_profit_prefix(self, _mock: Any) -> None:
        views = get_signals_by_prefix(SAMPLE_RESULTS, "FIN.PROFIT.")
        assert len(views) == 2

    def test_no_match(self, _mock: Any) -> None:
        views = get_signals_by_prefix(SAMPLE_RESULTS, "NONEXISTENT.")
        assert views == []

    def test_empty_dict(self, _mock: Any) -> None:
        views = get_signals_by_prefix({}, "FIN.")
        assert views == []


# ---------------------------------------------------------------------------
# signal_to_display_level
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "level", "expected"),
    [
        ("TRIGGERED", "red", "Critical"),
        ("TRIGGERED", "yellow", "Warning"),
        ("TRIGGERED", "", "Elevated"),
        ("CLEAR", "", "Clear"),
        ("CLEAR", "clear", "Clear"),
        ("SKIPPED", "", "Unavailable"),
        ("SKIPPED", "red", "Unavailable"),
        ("INFO", "", "Info"),
        ("INFO", "red", "Info"),
        ("UNKNOWN_STATUS", "", "Unknown"),
    ],
)
def test_signal_to_display_level(status: str, level: str, expected: str) -> None:
    assert signal_to_display_level(status, level) == expected


# ---------------------------------------------------------------------------
# SignalResultView properties
# ---------------------------------------------------------------------------


@patch(
    "do_uw.stages.render.context_builders._signal_consumer._get_brain_signal",
    side_effect=_mock_get_brain_signal,
)
class TestSignalResultViewProperties:
    def test_view_has_rap_class(self, _mock: Any) -> None:
        view = get_signal_result(SAMPLE_RESULTS, "FIN.PROFIT.revenue")
        assert view is not None
        assert view.rap_class == "host"
        assert view.rap_subcategory == "host.financials"

    def test_view_has_mechanism(self, _mock: Any) -> None:
        view = get_signal_result(SAMPLE_RESULTS, "FIN.PROFIT.revenue")
        assert view is not None
        assert view.mechanism == "threshold"

    def test_view_has_epistemology(self, _mock: Any) -> None:
        view = get_signal_result(SAMPLE_RESULTS, "FIN.PROFIT.revenue")
        assert view is not None
        assert view.epistemology_rule_origin == "SCAC filing analysis"
        assert "Revenue decline" in view.epistemology_threshold_basis

    def test_view_is_frozen(self, _mock: Any) -> None:
        view = get_signal_result(SAMPLE_RESULTS, "FIN.PROFIT.revenue")
        assert view is not None
        with pytest.raises(FrozenInstanceError):
            view.status = "CLEAR"  # type: ignore[misc]

    def test_view_no_brain_def_has_empty_fields(self, _mock: Any) -> None:
        view = get_signal_result(SAMPLE_RESULTS, "FIN.PROFIT.margins")
        assert view is not None
        assert view.rap_class == ""
        assert view.mechanism == ""
        assert view.epistemology_rule_origin == ""


# ---------------------------------------------------------------------------
# get_signal_epistemology
# ---------------------------------------------------------------------------


@patch(
    "do_uw.stages.render.context_builders._signal_consumer._get_brain_signal",
    side_effect=_mock_get_brain_signal,
)
class TestGetSignalEpistemology:
    def test_returns_tuple(self, _mock: Any) -> None:
        result = get_signal_epistemology(SAMPLE_RESULTS, "FIN.PROFIT.revenue")
        assert result is not None
        assert result == ("SCAC filing analysis", "Revenue decline >20% correlates with 3x SCA frequency")

    def test_missing_signal_returns_none(self, _mock: Any) -> None:
        result = get_signal_epistemology(SAMPLE_RESULTS, "NONEXISTENT")
        assert result is None

    def test_no_brain_def_returns_none(self, _mock: Any) -> None:
        result = get_signal_epistemology(SAMPLE_RESULTS, "FIN.PROFIT.margins")
        assert result is None
