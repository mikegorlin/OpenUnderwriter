"""Unit tests for _signal_fallback.py graceful degradation wrappers.

Tests all 5 safe_ functions and SignalUnavailable sentinel with
missing signals, None signal_results, SKIPPED signals, and malformed data.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from do_uw.stages.render.context_builders._signal_consumer import SignalResultView
from do_uw.stages.render.context_builders._signal_fallback import (
    SignalUnavailable,
    safe_get_level,
    safe_get_result,
    safe_get_signals_by_prefix,
    safe_get_status,
    safe_get_value,
)

# ---------------------------------------------------------------------------
# Test fixtures
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
        "details": {},
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
        "evidence": "Margins within range",
        "source": "SEC_10K",
        "confidence": "HIGH",
        "threshold_context": "",
        "factors": [],
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
        "evidence": "Data unavailable",
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
}


def _mock_get_brain_signal(signal_id: str) -> dict[str, Any] | None:
    """Return None for all brain lookups (test isolation)."""
    return None


# ---------------------------------------------------------------------------
# SignalUnavailable sentinel
# ---------------------------------------------------------------------------


class TestSignalUnavailable:
    def test_is_falsy(self) -> None:
        u = SignalUnavailable("TEST.SIG", "not_found")
        assert not u
        assert bool(u) is False

    def test_str_contains_id_and_reason(self) -> None:
        u = SignalUnavailable("FIN.PROFIT.revenue", "not_found")
        s = str(u)
        assert "FIN.PROFIT.revenue" in s
        assert "not_found" in s
        assert "Signal unavailable" in s

    def test_str_format(self) -> None:
        u = SignalUnavailable("X.Y", "no_results")
        assert str(u) == "Signal unavailable: X.Y (no_results)"

    def test_is_frozen(self) -> None:
        u = SignalUnavailable("A.B", "test")
        try:
            u.signal_id = "C.D"  # type: ignore[misc]
            assert False, "Should have raised FrozenInstanceError"
        except Exception:
            pass  # Expected


# ---------------------------------------------------------------------------
# safe_get_result
# ---------------------------------------------------------------------------


@patch(
    "do_uw.stages.render.context_builders._signal_consumer._get_brain_signal",
    side_effect=_mock_get_brain_signal,
)
class TestSafeGetResult:
    def test_returns_view(self, _mock: Any) -> None:
        result = safe_get_result(SAMPLE_RESULTS, "FIN.PROFIT.revenue")
        assert isinstance(result, SignalResultView)
        assert result.signal_id == "FIN.PROFIT.revenue"

    def test_missing_returns_unavailable(self, _mock: Any) -> None:
        result = safe_get_result(SAMPLE_RESULTS, "NONEXISTENT")
        assert isinstance(result, SignalUnavailable)
        assert result.reason == "not_found"
        assert not result

    def test_none_results_returns_unavailable(self, _mock: Any) -> None:
        result = safe_get_result(None, "ANY.ID")
        assert isinstance(result, SignalUnavailable)
        assert result.reason == "no_results"
        assert not result

    def test_skipped_returns_view(self, _mock: Any) -> None:
        """SKIPPED is a valid status, not an error -- returns SignalResultView."""
        result = safe_get_result(SAMPLE_RESULTS, "GOV.BOARD.independence")
        assert isinstance(result, SignalResultView)
        assert result.status == "SKIPPED"

    def test_empty_dict_returns_unavailable(self, _mock: Any) -> None:
        result = safe_get_result({}, "ANY.ID")
        assert isinstance(result, SignalUnavailable)
        assert result.reason == "not_found"


# ---------------------------------------------------------------------------
# safe_get_value
# ---------------------------------------------------------------------------


class TestSafeGetValue:
    def test_returns_value(self) -> None:
        assert safe_get_value(SAMPLE_RESULTS, "FIN.PROFIT.revenue") == -0.25

    def test_missing_returns_default(self) -> None:
        assert safe_get_value(SAMPLE_RESULTS, "NONEXISTENT") is None

    def test_none_results_returns_default(self) -> None:
        assert safe_get_value(None, "ANY.ID") is None

    def test_custom_default(self) -> None:
        assert safe_get_value(SAMPLE_RESULTS, "NONEXISTENT", default=0.0) == 0.0

    def test_none_results_custom_default(self) -> None:
        assert safe_get_value(None, "ANY.ID", default="N/A") == "N/A"

    def test_none_value_signal_returns_default(self) -> None:
        """GOV.BOARD.independence has value=None, should return default."""
        assert safe_get_value(SAMPLE_RESULTS, "GOV.BOARD.independence", default=0.0) == 0.0


# ---------------------------------------------------------------------------
# safe_get_status
# ---------------------------------------------------------------------------


class TestSafeGetStatus:
    def test_returns_status(self) -> None:
        assert safe_get_status(SAMPLE_RESULTS, "FIN.PROFIT.revenue") == "TRIGGERED"

    def test_missing_returns_default(self) -> None:
        assert safe_get_status(SAMPLE_RESULTS, "NONEXISTENT") == "SKIPPED"

    def test_none_results_returns_default(self) -> None:
        assert safe_get_status(None, "ANY.ID") == "SKIPPED"

    def test_custom_default(self) -> None:
        assert safe_get_status(SAMPLE_RESULTS, "NONEXISTENT", default="UNKNOWN") == "UNKNOWN"


# ---------------------------------------------------------------------------
# safe_get_level
# ---------------------------------------------------------------------------


class TestSafeGetLevel:
    def test_returns_level(self) -> None:
        assert safe_get_level(SAMPLE_RESULTS, "FIN.PROFIT.revenue") == "red"

    def test_missing_returns_empty(self) -> None:
        assert safe_get_level(SAMPLE_RESULTS, "NONEXISTENT") == ""

    def test_none_results_returns_default(self) -> None:
        assert safe_get_level(None, "ANY.ID") == ""

    def test_custom_default(self) -> None:
        assert safe_get_level(None, "ANY.ID", default="unknown") == "unknown"

    def test_empty_level_returns_default(self) -> None:
        """GOV.BOARD.independence has threshold_level="" -- should return default."""
        assert safe_get_level(SAMPLE_RESULTS, "GOV.BOARD.independence", default="n/a") == "n/a"


# ---------------------------------------------------------------------------
# safe_get_signals_by_prefix
# ---------------------------------------------------------------------------


@patch(
    "do_uw.stages.render.context_builders._signal_consumer._get_brain_signal",
    side_effect=_mock_get_brain_signal,
)
class TestSafeGetSignalsByPrefix:
    def test_returns_list(self, _mock: Any) -> None:
        results = safe_get_signals_by_prefix(SAMPLE_RESULTS, "FIN.")
        assert len(results) == 2
        assert all(isinstance(r, SignalResultView) for r in results)

    def test_none_results_returns_empty(self, _mock: Any) -> None:
        assert safe_get_signals_by_prefix(None, "FIN.") == []

    def test_no_match_returns_empty(self, _mock: Any) -> None:
        assert safe_get_signals_by_prefix(SAMPLE_RESULTS, "NONEXISTENT.") == []

    def test_empty_dict_returns_empty(self, _mock: Any) -> None:
        assert safe_get_signals_by_prefix({}, "FIN.") == []
