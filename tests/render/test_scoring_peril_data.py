"""Tests for peril scoring data extraction.

Verifies chain activation logic, risk level computation, peril aggregation,
and graceful fallback behavior.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

from do_uw.stages.render.scoring_peril_data import (
    _aggregate_peril,
    _check_fired,
    _evaluate_chain,
    extract_peril_scoring,
)

# -- Helpers --


def _make_signal_result(
    status: str = "CLEAR",
    threshold_level: str = "",
    evidence: str = "",
) -> dict[str, Any]:
    """Create a mock check result dict."""
    return {
        "status": status,
        "threshold_level": threshold_level,
        "evidence": evidence,
    }


def _make_chain(
    chain_id: str = "chain_1",
    name: str = "Test Chain",
    peril_id: str = "PERIL_1",
    trigger_signals: list[str] | None = None,
    amplifier_signals: list[str] | None = None,
    mitigator_signals: list[str] | None = None,
    evidence_signals: list[str] | None = None,
    red_flags: list[str] | None = None,
) -> dict[str, Any]:
    """Create a mock causal chain dict."""
    return {
        "chain_id": chain_id,
        "name": name,
        "peril_id": peril_id,
        "description": f"Test chain {chain_id}",
        "trigger_signals": trigger_signals or [],
        "amplifier_signals": amplifier_signals or [],
        "mitigator_signals": mitigator_signals or [],
        "evidence_signals": evidence_signals or [],
        "red_flags": red_flags or [],
        "historical_filing_rate": 0.05,
        "median_severity_usd": 10_000_000.0,
    }


def _make_peril(
    peril_id: str = "PERIL_1",
    name: str = "Test Peril",
) -> dict[str, Any]:
    """Create a mock peril dict."""
    return {
        "peril_id": peril_id,
        "name": name,
        "description": f"Test peril {peril_id}",
        "frequency": "MODERATE",
        "severity": "HIGH",
        "typical_settlement_range": "$5M-$50M",
        "key_drivers": ["driver_1", "driver_2"],
        "haz_codes": ["HAZ.1"],
    }


# -- Test: _check_fired --


class TestCheckFired:
    """Test check fired detection logic."""

    def test_check_fired_triggered(self) -> None:
        """TRIGGERED status detected as fired."""
        results = {"CHK.1": _make_signal_result(status="TRIGGERED")}
        assert _check_fired("CHK.1", results) is True

    def test_check_fired_red_threshold(self) -> None:
        """Red threshold_level detected as fired."""
        results = {
            "CHK.1": _make_signal_result(
                status="TRIGGERED",
                threshold_level="red",
            )
        }
        assert _check_fired("CHK.1", results) is True

    def test_check_fired_yellow_threshold(self) -> None:
        """Yellow threshold_level detected as fired."""
        results = {
            "CHK.1": _make_signal_result(
                status="TRIGGERED",
                threshold_level="yellow",
            )
        }
        assert _check_fired("CHK.1", results) is True

    def test_check_fired_clear(self) -> None:
        """CLEAR status NOT detected as fired."""
        results = {"CHK.1": _make_signal_result(status="CLEAR")}
        assert _check_fired("CHK.1", results) is False

    def test_check_fired_skipped(self) -> None:
        """SKIPPED status NOT detected as fired."""
        results = {"CHK.1": _make_signal_result(status="SKIPPED")}
        assert _check_fired("CHK.1", results) is False

    def test_check_fired_missing(self) -> None:
        """Missing signal_id returns False."""
        assert _check_fired("NONEXISTENT", {}) is False

    def test_check_fired_pydantic_object(self) -> None:
        """Handles Pydantic-like object (SimpleNamespace)."""
        result = SimpleNamespace(status="TRIGGERED", threshold_level="red", evidence="test")
        results: dict[str, Any] = {"CHK.1": result}
        assert _check_fired("CHK.1", results) is True

    def test_check_fired_info(self) -> None:
        """INFO status NOT detected as fired."""
        results = {"CHK.1": _make_signal_result(status="INFO")}
        assert _check_fired("CHK.1", results) is False


# -- Test: _evaluate_chain --


class TestEvaluateChain:
    """Test chain evaluation logic."""

    def test_chain_no_triggers_is_inactive(self) -> None:
        """Chain with no fired triggers is inactive with LOW risk."""
        chain = _make_chain(trigger_signals=["CHK.1", "CHK.2"])
        results = {
            "CHK.1": _make_signal_result(status="CLEAR"),
            "CHK.2": _make_signal_result(status="CLEAR"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["active"] is False
        assert evaluated["risk_level"] == "LOW"

    def test_chain_single_trigger_moderate(self) -> None:
        """Single trigger = MODERATE risk."""
        chain = _make_chain(trigger_signals=["CHK.1", "CHK.2"])
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "CHK.2": _make_signal_result(status="CLEAR"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["active"] is True
        assert evaluated["risk_level"] == "MODERATE"
        assert evaluated["triggered_triggers"] == ["CHK.1"]

    def test_chain_trigger_with_amplifiers_elevated(self) -> None:
        """Trigger + amplifier = ELEVATED risk."""
        chain = _make_chain(
            trigger_signals=["CHK.1"],
            amplifier_signals=["AMP.1"],
        )
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "AMP.1": _make_signal_result(status="TRIGGERED"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["active"] is True
        assert evaluated["risk_level"] == "ELEVATED"
        assert evaluated["active_amplifiers"] == ["AMP.1"]

    def test_chain_multiple_triggers_high(self) -> None:
        """2+ triggers = HIGH risk."""
        chain = _make_chain(trigger_signals=["CHK.1", "CHK.2"])
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "CHK.2": _make_signal_result(status="TRIGGERED"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["active"] is True
        assert evaluated["risk_level"] == "HIGH"

    def test_mitigator_reduces_high_to_elevated(self) -> None:
        """Mitigator reduces HIGH to ELEVATED."""
        chain = _make_chain(
            trigger_signals=["CHK.1", "CHK.2"],
            mitigator_signals=["MIT.1"],
        )
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "CHK.2": _make_signal_result(status="TRIGGERED"),
            "MIT.1": _make_signal_result(status="TRIGGERED"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["active"] is True
        assert evaluated["risk_level"] == "ELEVATED"

    def test_mitigator_reduces_elevated_to_moderate(self) -> None:
        """Mitigator reduces ELEVATED to MODERATE."""
        chain = _make_chain(
            trigger_signals=["CHK.1"],
            amplifier_signals=["AMP.1"],
            mitigator_signals=["MIT.1"],
        )
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "AMP.1": _make_signal_result(status="TRIGGERED"),
            "MIT.1": _make_signal_result(status="TRIGGERED"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["active"] is True
        assert evaluated["risk_level"] == "MODERATE"

    def test_mitigator_no_effect_on_moderate(self) -> None:
        """Mitigator does NOT reduce MODERATE (only HIGH/ELEVATED)."""
        chain = _make_chain(
            trigger_signals=["CHK.1"],
            mitigator_signals=["MIT.1"],
        )
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "MIT.1": _make_signal_result(status="TRIGGERED"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["risk_level"] == "MODERATE"

    def test_evidence_summary_collected(self) -> None:
        """Evidence from evidence_signals is collected."""
        chain = _make_chain(
            trigger_signals=["CHK.1"],
            evidence_signals=["EV.1", "EV.2"],
        )
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "EV.1": _make_signal_result(evidence="Stock dropped 15%"),
            "EV.2": _make_signal_result(evidence=""),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["evidence_summary"] == ["Stock dropped 15%"]

    def test_red_flag_triggers_high(self) -> None:
        """Red flag associated with chain triggers HIGH risk."""
        chain = _make_chain(
            trigger_signals=["CHK.1"],
            red_flags=["RF.1"],
        )
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "RF.1": _make_signal_result(status="TRIGGERED"),
        }
        evaluated = _evaluate_chain(chain, results)
        assert evaluated["risk_level"] == "HIGH"


# -- Test: _aggregate_peril --


class TestAggregatePeril:
    """Test peril-level aggregation."""

    def test_peril_highest_chain_risk(self) -> None:
        """Peril risk = highest chain risk."""
        peril = _make_peril()
        chains = [
            _make_chain(
                chain_id="c1",
                trigger_signals=["CHK.1"],
            ),
            _make_chain(
                chain_id="c2",
                trigger_signals=["CHK.2", "CHK.3"],
            ),
        ]
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "CHK.2": _make_signal_result(status="TRIGGERED"),
            "CHK.3": _make_signal_result(status="TRIGGERED"),
        }
        agg = _aggregate_peril(peril, chains, results)
        assert agg["risk_level"] == "HIGH"  # c2 has 2 triggers = HIGH
        assert agg["active_chain_count"] == 2
        assert agg["total_chain_count"] == 2

    def test_peril_no_active_chains(self) -> None:
        """Peril with no active chains has LOW risk."""
        peril = _make_peril()
        chains = [_make_chain(trigger_signals=["CHK.1"])]
        results = {"CHK.1": _make_signal_result(status="CLEAR")}
        agg = _aggregate_peril(peril, chains, results)
        assert agg["risk_level"] == "LOW"
        assert agg["active_chain_count"] == 0

    def test_peril_evidence_deduplicated(self) -> None:
        """Evidence from multiple chains is deduplicated."""
        peril = _make_peril()
        chains = [
            _make_chain(
                chain_id="c1",
                trigger_signals=["CHK.1"],
                evidence_signals=["EV.1"],
            ),
            _make_chain(
                chain_id="c2",
                trigger_signals=["CHK.2"],
                evidence_signals=["EV.1"],  # Same evidence check
            ),
        ]
        results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "CHK.2": _make_signal_result(status="TRIGGERED"),
            "EV.1": _make_signal_result(evidence="Same evidence"),
        }
        agg = _aggregate_peril(peril, chains, results)
        assert len(agg["key_evidence"]) == 1  # Deduplicated


# -- Test: extract_peril_scoring --


class TestExtractPerilScoring:
    """Test top-level extraction function."""

    def test_no_brain_returns_empty(self) -> None:
        """Returns empty dict when brain signals unavailable."""
        state = SimpleNamespace(analysis=None)
        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            side_effect=ImportError("No brain"),
        ):
            result = extract_peril_scoring(state)
        assert result == {}

    def test_no_perils_returns_empty(self) -> None:
        """Returns empty dict when no perils found."""
        state = SimpleNamespace(analysis=None)
        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            return_value=[],
        ), patch(
            "do_uw.brain.brain_unified_loader.load_causal_chains",
            return_value=[],
        ):
            result = extract_peril_scoring(state)
        assert result == {}

    def test_inactive_perils_excluded_from_perils_list(self) -> None:
        """Perils with no active chains excluded from 'perils' (active only)."""
        signal_results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "CHK.2": _make_signal_result(status="CLEAR"),
        }
        state = SimpleNamespace(
            analysis=SimpleNamespace(signal_results=signal_results),
        )

        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            return_value=[
                _make_peril("P1", "Active Peril"),
                _make_peril("P2", "Inactive Peril"),
            ],
        ), patch(
            "do_uw.brain.brain_unified_loader.load_causal_chains",
            return_value=[
                _make_chain("c1", peril_id="P1", trigger_signals=["CHK.1"]),
                _make_chain("c2", peril_id="P2", trigger_signals=["CHK.2"]),
            ],
        ):
            result = extract_peril_scoring(state)

        assert result["active_count"] == 1
        assert len(result["perils"]) == 1
        assert result["perils"][0]["peril_id"] == "P1"
        assert len(result["all_perils"]) == 2
        assert result["highest_peril"] == "P1"

    def test_full_extraction_with_multiple_perils(self) -> None:
        """Full extraction with multiple active perils sorted by risk."""
        signal_results = {
            "CHK.1": _make_signal_result(status="TRIGGERED"),
            "CHK.2": _make_signal_result(status="TRIGGERED"),
            "CHK.3": _make_signal_result(status="TRIGGERED"),
        }
        state = SimpleNamespace(
            analysis=SimpleNamespace(signal_results=signal_results),
        )

        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            return_value=[
                _make_peril("P1", "Low Peril"),
                _make_peril("P2", "High Peril"),
            ],
        ), patch(
            "do_uw.brain.brain_unified_loader.load_causal_chains",
            return_value=[
                _make_chain("c1", peril_id="P1", trigger_signals=["CHK.1"]),
                _make_chain(
                    "c2",
                    peril_id="P2",
                    trigger_signals=["CHK.2", "CHK.3"],
                ),
            ],
        ):
            result = extract_peril_scoring(state)

        assert result["active_count"] == 2
        # P2 (HIGH) should be first, P1 (MODERATE) second
        assert result["perils"][0]["peril_id"] == "P2"
        assert result["perils"][0]["risk_level"] == "HIGH"
        assert result["perils"][1]["peril_id"] == "P1"
        assert result["perils"][1]["risk_level"] == "MODERATE"
        assert result["highest_peril"] == "P2"

    def test_no_analysis_returns_all_low(self) -> None:
        """State with no analysis returns all perils with LOW risk."""
        state = SimpleNamespace(analysis=None)

        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            return_value=[_make_peril("P1", "Test")],
        ), patch(
            "do_uw.brain.brain_unified_loader.load_causal_chains",
            return_value=[
                _make_chain("c1", peril_id="P1", trigger_signals=["CHK.1"]),
            ],
        ):
            result = extract_peril_scoring(state)

        assert result["active_count"] == 0
        assert len(result["perils"]) == 0
        assert len(result["all_perils"]) == 1
        assert result["all_perils"][0]["risk_level"] == "LOW"
        assert result["highest_peril"] is None
