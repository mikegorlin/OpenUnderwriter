"""Tests for monitoring trigger computation with company-specific thresholds.

Phase 117 Plan 03 Task 2.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.forward_looking import MonitoringTrigger
from do_uw.models.market import InsiderTradingProfile, MarketSignals, StockPerformance
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.benchmark.monitoring_triggers import compute_monitoring_triggers

_NOW = datetime.now(tz=UTC)


def _sv(val: object, source: str = "test") -> SourcedValue:
    """Build a SourcedValue for testing."""
    return SourcedValue(value=val, source=source, confidence=Confidence.HIGH, as_of=_NOW)


def _make_state_with_market(
    year_low: float = 50.0,
    current_price: float = 100.0,
    total_sold_12m: float = 2_000_000.0,
    sic_code: str = "3674",
    company_name: str = "Test Corp",
) -> AnalysisState:
    """Build AnalysisState with market data for monitoring trigger tests."""
    identity = CompanyIdentity(
        ticker="TEST",
        legal_name=_sv(company_name),
        sic_code=_sv(sic_code),
    )
    company = CompanyProfile(identity=identity)

    stock = StockPerformance(
        low_52w=_sv(year_low),
        current_price=_sv(current_price),
    )
    insider = InsiderTradingProfile(
        total_sold_value=_sv(total_sold_12m),
    )
    market = MarketSignals(stock=stock, insider_trading=insider)

    return AnalysisState(
        ticker="TEST",
        company=company,
        extracted=ExtractedData(market=market),
    )


def _make_minimal_state() -> AnalysisState:
    """Build minimal AnalysisState without market data."""
    return AnalysisState(ticker="TEST")


class TestComputeMonitoringTriggers:
    def test_returns_six_triggers(self) -> None:
        state = _make_state_with_market()
        triggers = compute_monitoring_triggers(state)

        assert len(triggers) == 6
        assert all(isinstance(t, MonitoringTrigger) for t in triggers)

    def test_stock_trigger_uses_actual_52_week_low(self) -> None:
        state = _make_state_with_market(year_low=42.50)
        triggers = compute_monitoring_triggers(state)

        stock_triggers = [t for t in triggers if "Stock" in t.trigger_name]
        assert len(stock_triggers) >= 1
        assert "42.50" in stock_triggers[0].threshold

    def test_insider_selling_uses_actual_yearly_rate(self) -> None:
        state = _make_state_with_market(total_sold_12m=4_800_000.0)
        triggers = compute_monitoring_triggers(state)

        insider_triggers = [
            t
            for t in triggers
            if "insider" in t.trigger_name.lower() or "Insider" in t.trigger_name
        ]
        assert len(insider_triggers) >= 1
        # Quarterly rate = 4_800_000 / 4 = 1_200_000; threshold = 2x = 2_400_000
        assert "2,400,000" in insider_triggers[0].threshold

    def test_eps_miss_threshold(self) -> None:
        state = _make_state_with_market()
        triggers = compute_monitoring_triggers(state)

        eps_triggers = [t for t in triggers if "EPS" in t.trigger_name]
        assert len(eps_triggers) >= 1
        assert "10%" in eps_triggers[0].threshold

    def test_peer_sca_uses_sic_code(self) -> None:
        state = _make_state_with_market(sic_code="7372")
        triggers = compute_monitoring_triggers(state)

        peer_triggers = [t for t in triggers if "Peer" in t.trigger_name]
        assert len(peer_triggers) >= 1
        assert "7372" in peer_triggers[0].threshold

    def test_minimal_state_still_returns_triggers(self) -> None:
        state = _make_minimal_state()
        triggers = compute_monitoring_triggers(state)

        assert len(triggers) == 6
        assert all(t.trigger_name != "" for t in triggers)
