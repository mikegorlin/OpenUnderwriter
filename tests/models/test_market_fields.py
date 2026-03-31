"""Tests for Phase 89 model field additions.

Verifies new fields on StockPerformance, StockDropEvent, and StockDropAnalysis
default to None/False and are backward-compatible with existing serialized state.
"""

from __future__ import annotations

from do_uw.models.market import StockPerformance
from do_uw.models.market_events import StockDropAnalysis, StockDropEvent


class TestStockPerformancePhase89Fields:
    """StockPerformance has ewma_vol_current, vol_regime, vol_regime_duration_days."""

    def test_ewma_vol_current_default_none(self) -> None:
        sp = StockPerformance()
        assert sp.ewma_vol_current is None

    def test_vol_regime_default_none(self) -> None:
        sp = StockPerformance()
        assert sp.vol_regime is None

    def test_vol_regime_duration_days_default_none(self) -> None:
        sp = StockPerformance()
        assert sp.vol_regime_duration_days is None

    def test_backward_compatible_no_new_fields(self) -> None:
        """Creating from empty dict still works (backward compat)."""
        sp = StockPerformance.model_validate({})
        assert sp.ewma_vol_current is None
        assert sp.vol_regime is None
        assert sp.vol_regime_duration_days is None


class TestStockDropEventPhase89Fields:
    """StockDropEvent has abnormal return fields."""

    def test_abnormal_return_pct_default_none(self) -> None:
        ev = StockDropEvent()
        assert ev.abnormal_return_pct is None

    def test_abnormal_return_t_stat_default_none(self) -> None:
        ev = StockDropEvent()
        assert ev.abnormal_return_t_stat is None

    def test_is_statistically_significant_default_false(self) -> None:
        ev = StockDropEvent()
        assert ev.is_statistically_significant is False

    def test_market_model_alpha_default_none(self) -> None:
        ev = StockDropEvent()
        assert ev.market_model_alpha is None

    def test_market_model_beta_default_none(self) -> None:
        ev = StockDropEvent()
        assert ev.market_model_beta is None

    def test_backward_compatible_no_new_fields(self) -> None:
        ev = StockDropEvent.model_validate({})
        assert ev.abnormal_return_pct is None
        assert ev.abnormal_return_t_stat is None
        assert ev.is_statistically_significant is False
        assert ev.market_model_alpha is None
        assert ev.market_model_beta is None


class TestStockDropAnalysisPhase89Fields:
    """StockDropAnalysis has DDL exposure fields."""

    def test_ddl_exposure_default_none(self) -> None:
        da = StockDropAnalysis()
        assert da.ddl_exposure is None

    def test_mdl_exposure_default_none(self) -> None:
        da = StockDropAnalysis()
        assert da.mdl_exposure is None

    def test_ddl_settlement_estimate_default_none(self) -> None:
        da = StockDropAnalysis()
        assert da.ddl_settlement_estimate is None

    def test_backward_compatible_no_new_fields(self) -> None:
        da = StockDropAnalysis.model_validate({})
        assert da.ddl_exposure is None
        assert da.mdl_exposure is None
        assert da.ddl_settlement_estimate is None
