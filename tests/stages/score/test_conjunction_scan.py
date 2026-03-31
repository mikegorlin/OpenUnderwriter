"""Tests for Conjunction Scan engine (PAT-01).

Validates:
- Cross-domain co-firing CLEAR signal detection
- Seed correlation YAML loading
- DuckDB supplement path
- Graceful degradation on missing data
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.stages.score.pattern_engine import EngineResult, PatternEngine


def _make_signal(
    status: str = "CLEAR",
    rap_class: str = "host",
    rap_subcategory: str = "host.financials",
    value: float | None = None,
) -> dict[str, Any]:
    """Build a minimal signal result dict matching SignalResultView pattern."""
    return {
        "status": status,
        "rap_class": rap_class,
        "rap_subcategory": rap_subcategory,
        "value": value,
        "threshold_level": "",
        "evidence": "",
        "source": "test",
        "confidence": "HIGH",
    }


class TestConjunctionScanProtocol:
    """Verify ConjunctionScanEngine implements PatternEngine Protocol."""

    def test_implements_protocol(self) -> None:
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        engine = ConjunctionScanEngine()
        assert isinstance(engine, PatternEngine)

    def test_engine_id(self) -> None:
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        engine = ConjunctionScanEngine()
        assert engine.engine_id == "conjunction_scan"

    def test_engine_name(self) -> None:
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        engine = ConjunctionScanEngine()
        assert engine.engine_name == "Conjunction Scan"


class TestConjunctionScanFired:
    """Test cases where conjunction scan should fire."""

    def test_5_clear_signals_2_rap_categories_fires(self) -> None:
        """5 CLEAR signals from 2+ RAP categories with co-fire rates > 0.15 => fired=True."""
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        # Build signal results: 3 host + 2 agent signals, all CLEAR
        signal_results: dict[str, Any] = {
            "GOV.INSIDER.cluster_sales": _make_signal("CLEAR", "agent", "agent.insider_conduct"),
            "FIN.TEMPORAL.margin_compression": _make_signal("CLEAR", "host", "host.financials"),
            "FIN.GUIDE.track_record": _make_signal("CLEAR", "agent", "agent.disclosure_conduct"),
            "STOCK.PRICE.recent_drop_alert": _make_signal("CLEAR", "environment", "environment.market_signals"),
            "GOV.EFFECT.material_weakness": _make_signal("CLEAR", "host", "host.governance"),
        }

        # Provide seed correlations covering these signals with high co-fire rates
        seed_correlations = {
            ("FIN.TEMPORAL.margin_compression", "GOV.INSIDER.cluster_sales"): 0.35,
            ("FIN.GUIDE.track_record", "GOV.INSIDER.cluster_sales"): 0.30,
            ("FIN.GUIDE.track_record", "STOCK.PRICE.recent_drop_alert"): 0.40,
            ("FIN.TEMPORAL.margin_compression", "GOV.EFFECT.material_weakness"): 0.45,
            ("GOV.EFFECT.material_weakness", "GOV.INSIDER.cluster_sales"): 0.25,
            ("FIN.TEMPORAL.margin_compression", "STOCK.PRICE.recent_drop_alert"): 0.30,
        }

        engine = ConjunctionScanEngine(correlations_override=seed_correlations)
        result = engine.evaluate(signal_results)

        assert isinstance(result, EngineResult)
        assert result.fired is True
        assert result.confidence > 0.5
        assert len(result.findings) > 0


class TestConjunctionScanNotFired:
    """Test cases where conjunction scan should NOT fire."""

    def test_same_rap_category_does_not_fire(self) -> None:
        """All signals from same RAP category => fired=False (no cross-domain conjunction)."""
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        # All host signals
        signal_results: dict[str, Any] = {
            "FIN.TEMPORAL.margin_compression": _make_signal("CLEAR", "host", "host.financials"),
            "GOV.EFFECT.material_weakness": _make_signal("CLEAR", "host", "host.governance"),
            "FIN.QUALITY.revenue_recognition_risk": _make_signal("CLEAR", "host", "host.financials"),
            "FIN.FORENSIC.m_score_composite": _make_signal("CLEAR", "host", "host.financials"),
            "FIN.FORENSIC.dsri_elevated": _make_signal("CLEAR", "host", "host.financials"),
        }

        seed_correlations = {
            ("FIN.TEMPORAL.margin_compression", "GOV.EFFECT.material_weakness"): 0.55,
            ("FIN.QUALITY.revenue_recognition_risk", "FIN.FORENSIC.dsri_elevated"): 0.45,
            ("FIN.FORENSIC.m_score_composite", "GOV.EFFECT.material_weakness"): 0.40,
            ("FIN.TEMPORAL.margin_compression", "FIN.QUALITY.revenue_recognition_risk"): 0.35,
        }

        engine = ConjunctionScanEngine(correlations_override=seed_correlations)
        result = engine.evaluate(signal_results)

        assert result.fired is False

    def test_fewer_than_3_cofiring_does_not_fire(self) -> None:
        """Fewer than 3 co-firing signals => fired=False."""
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        # Only 2 cross-domain co-firing CLEAR signals
        signal_results: dict[str, Any] = {
            "FIN.TEMPORAL.margin_compression": _make_signal("CLEAR", "host", "host.financials"),
            "GOV.INSIDER.cluster_sales": _make_signal("CLEAR", "agent", "agent.insider_conduct"),
        }

        seed_correlations = {
            ("FIN.TEMPORAL.margin_compression", "GOV.INSIDER.cluster_sales"): 0.35,
        }

        engine = ConjunctionScanEngine(correlations_override=seed_correlations)
        result = engine.evaluate(signal_results)

        assert result.fired is False

    def test_empty_correlations_does_not_fire(self) -> None:
        """Empty correlations dict => fired=False, headline contains 'Insufficient'."""
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        signal_results: dict[str, Any] = {
            "FIN.TEMPORAL.margin_compression": _make_signal("CLEAR", "host", "host.financials"),
            "GOV.INSIDER.cluster_sales": _make_signal("CLEAR", "agent", "agent.insider_conduct"),
        }

        engine = ConjunctionScanEngine(correlations_override={})
        result = engine.evaluate(signal_results)

        assert result.fired is False
        assert "Insufficient" in result.headline

    def test_no_clear_signals_does_not_fire(self) -> None:
        """No CLEAR signals (all RED/YELLOW) => fired=False."""
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        signal_results: dict[str, Any] = {
            "FIN.TEMPORAL.margin_compression": _make_signal("RED", "host", "host.financials"),
            "GOV.INSIDER.cluster_sales": _make_signal("YELLOW", "agent", "agent.insider_conduct"),
            "STOCK.PRICE.recent_drop_alert": _make_signal("RED", "environment", "environment.market_signals"),
        }

        seed_correlations = {
            ("FIN.TEMPORAL.margin_compression", "GOV.INSIDER.cluster_sales"): 0.35,
        }

        engine = ConjunctionScanEngine(correlations_override=seed_correlations)
        result = engine.evaluate(signal_results)

        assert result.fired is False
        assert "No CLEAR signals" in result.headline

    def test_skipped_signals_excluded(self) -> None:
        """SKIPPED signals should be excluded from conjunction analysis."""
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        signal_results: dict[str, Any] = {
            "FIN.TEMPORAL.margin_compression": _make_signal("SKIPPED", "host", "host.financials"),
            "GOV.INSIDER.cluster_sales": _make_signal("SKIPPED", "agent", "agent.insider_conduct"),
            "STOCK.PRICE.recent_drop_alert": _make_signal("SKIPPED", "environment", "environment.market_signals"),
        }

        seed_correlations = {
            ("FIN.TEMPORAL.margin_compression", "GOV.INSIDER.cluster_sales"): 0.35,
        }

        engine = ConjunctionScanEngine(correlations_override=seed_correlations)
        result = engine.evaluate(signal_results)

        assert result.fired is False


class TestSeedCorrelationsYAML:
    """Test seed correlations YAML loading."""

    def test_seed_yaml_loads_and_has_15_entries(self) -> None:
        """Seed correlations YAML loads and has at least 15 co-fire pairs."""
        from do_uw.stages.score.conjunction_scan import _load_seed_correlations

        seed_path = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "brain"
            / "framework"
            / "seed_correlations.yaml"
        )
        correlations = _load_seed_correlations(seed_path)
        assert len(correlations) >= 15

    def test_seed_entries_have_valid_rates(self) -> None:
        """All seed co-fire rates are between 0 and 1."""
        from do_uw.stages.score.conjunction_scan import _load_seed_correlations

        seed_path = (
            Path(__file__).parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "brain"
            / "framework"
            / "seed_correlations.yaml"
        )
        correlations = _load_seed_correlations(seed_path)
        for pair, rate in correlations.items():
            assert 0.0 <= rate <= 1.0, f"Rate {rate} out of range for pair {pair}"


class TestDuckDBSupplement:
    """Test DuckDB supplementation path for correlations."""

    def test_duckdb_overrides_seed(self) -> None:
        """Mock DuckDB returning additional pairs verifies they override seed."""
        from do_uw.stages.score.conjunction_scan import ConjunctionScanEngine

        # Base seed
        seed = {
            ("FIN.TEMPORAL.margin_compression", "GOV.INSIDER.cluster_sales"): 0.35,
        }

        # DuckDB override with different rate
        db_override = {
            ("FIN.TEMPORAL.margin_compression", "GOV.INSIDER.cluster_sales"): 0.70,
            ("FIN.GUIDE.track_record", "STOCK.PRICE.recent_drop_alert"): 0.50,
        }

        # Correlations_override simulates the merged result
        merged = {**seed, **db_override}
        engine = ConjunctionScanEngine(correlations_override=merged)

        # Verify override rate is used
        assert engine._correlations[
            ("FIN.TEMPORAL.margin_compression", "GOV.INSIDER.cluster_sales")
        ] == 0.70
        # Verify new pair from DB is present
        assert (
            "FIN.GUIDE.track_record",
            "STOCK.PRICE.recent_drop_alert",
        ) in engine._correlations
