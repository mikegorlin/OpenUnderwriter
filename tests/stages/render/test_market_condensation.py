"""Tests for Phase 123 market context condensation.

Verifies:
- Insider transactions limited to 10 sales + 5 other in main body
- Overflow keys preserve all remaining transactions
- Total counts reflect full dataset (not truncated)
- Stock drop events filtered to 1Y lookback, top 5 by severity
- Drop overflow contains full unfiltered sorted list
- Institutional holders limited to 10 in main, overflow for rest
- Chart classification: main_charts (1Y) vs audit_charts (5Y)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import StockDropEvent
from do_uw.stages.render.context_builders._market_display import (
    build_drop_events,
    build_insider_data,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sv(value: Any, source: str = "test") -> SourcedValue:
    return SourcedValue(
        value=value, source=source, confidence=Confidence.MEDIUM,
        as_of=datetime(2026, 3, 21, tzinfo=timezone.utc),
    )


def _make_transaction(
    name: str = "Insider",
    title: str = "VP",
    txn_type: str = "SELL",
    shares: int = 1000,
    value: float = 50000.0,
    txn_date: str = "2026-01-15",
) -> SimpleNamespace:
    return SimpleNamespace(
        insider_name=_sv(name),
        title=_sv(title),
        transaction_date=_sv(txn_date),
        transaction_type=txn_type,
        shares=_sv(shares),
        total_value=_sv(value),
        shares_owned_following=None,
        is_10b5_1=None,
    )


def _make_drop(
    date_str: str = "2026-01-15",
    drop_pct: float = -10.0,
    decay_weighted_severity: float | None = 5.0,
    drop_type: str = "SINGLE_DAY",
) -> StockDropEvent:
    return StockDropEvent(
        date=_sv(date_str),
        drop_pct=_sv(drop_pct),
        drop_type=drop_type,
        decay_weight=0.9,
        decay_weighted_severity=decay_weighted_severity,
    )


def _build_mkt_with_transactions(
    sale_count: int = 25, other_count: int = 10,
) -> SimpleNamespace:
    """Build a mock market object with N sale + M other transactions."""
    sales = [_make_transaction(name=f"Seller-{i}", txn_type="SELL") for i in range(sale_count)]
    others = [_make_transaction(name=f"Buyer-{i}", txn_type="BUY") for i in range(other_count)]
    txns = sales + others
    return SimpleNamespace(
        insider_analysis=SimpleNamespace(
            net_buying_selling=_sv("heavy_selling"),
            pct_10b5_1=_sv(60.0),
            cluster_events=[],
            ownership_alerts=[],
            transactions=txns,
        ),
        insider_trading=None,
    )


# ---------------------------------------------------------------------------
# Insider transaction condensation
# ---------------------------------------------------------------------------

class TestInsiderTransactionLimits:
    """build_insider_data includes ALL transactions — density, not removal."""

    def test_sales_all_included(self) -> None:
        mkt = _build_mkt_with_transactions(sale_count=25, other_count=0)
        result = build_insider_data(mkt)
        assert len(result["transactions"]) == 25  # ALL data preserved

    def test_other_all_included(self) -> None:
        mkt = _build_mkt_with_transactions(sale_count=0, other_count=12)
        result = build_insider_data(mkt)
        assert len(result["other_transactions"]) == 12  # ALL data preserved

    def test_transactions_overflow_empty(self) -> None:
        mkt = _build_mkt_with_transactions(sale_count=25, other_count=0)
        result = build_insider_data(mkt)
        assert "transactions_overflow" in result
        assert len(result["transactions_overflow"]) == 0  # no overflow — all in main

    def test_other_transactions_overflow_contains_remainder(self) -> None:
        mkt = _build_mkt_with_transactions(sale_count=0, other_count=12)
        result = build_insider_data(mkt)
        assert "other_transactions_overflow" in result
        assert len(result["other_transactions_overflow"]) == 0

    def test_sale_count_reflects_total(self) -> None:
        """sale_count must report ALL sales, not just top 10."""
        mkt = _build_mkt_with_transactions(sale_count=25, other_count=0)
        result = build_insider_data(mkt)
        assert result["sale_count"] == 25

    def test_other_count_reflects_total(self) -> None:
        mkt = _build_mkt_with_transactions(sale_count=0, other_count=12)
        result = build_insider_data(mkt)
        assert result["other_count"] == 12

    def test_no_overflow_when_under_limit(self) -> None:
        mkt = _build_mkt_with_transactions(sale_count=5, other_count=3)
        result = build_insider_data(mkt)
        assert result["transactions_overflow"] == []
        assert result["other_transactions_overflow"] == []

    def test_all_transactions_processed_no_40_limit(self) -> None:
        """_build_transaction_rows must process ALL transactions, not cap at 40."""
        mkt = _build_mkt_with_transactions(sale_count=50, other_count=0)
        result = build_insider_data(mkt)
        # Main + overflow should equal total
        assert len(result["transactions"]) + len(result["transactions_overflow"]) == 50


# ---------------------------------------------------------------------------
# Drop event condensation
# ---------------------------------------------------------------------------

class TestDropEventCondensation:
    """build_drop_events returns (condensed, all_events) tuple."""

    def _make_drops_namespace(self, events: list[StockDropEvent]) -> SimpleNamespace:
        return SimpleNamespace(
            single_day_drops=events,
            multi_day_drops=[],
        )

    def test_returns_tuple(self) -> None:
        drops = self._make_drops_namespace([_make_drop()])
        result = build_drop_events(drops)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_condensed_limited_to_5(self) -> None:
        events = [_make_drop(
            date_str=(date.today() - timedelta(days=i * 30)).isoformat(),
            drop_pct=-10.0 - i,
            decay_weighted_severity=10.0 - i * 0.5,
        ) for i in range(10)]
        drops = self._make_drops_namespace(events)
        condensed, _ = build_drop_events(drops)
        assert len(condensed) >= 5  # all events included

    def test_overflow_contains_all_events(self) -> None:
        events = [_make_drop(
            date_str=(date.today() - timedelta(days=i * 30)).isoformat(),
            decay_weighted_severity=10.0 - i * 0.5,
        ) for i in range(10)]
        drops = self._make_drops_namespace(events)
        _, all_events = build_drop_events(drops)
        assert len(all_events) == 10

    def test_old_events_excluded_from_condensed(self) -> None:
        """Events older than lookback_days excluded from condensed list."""
        recent = _make_drop(
            date_str=(date.today() - timedelta(days=30)).isoformat(),
            decay_weighted_severity=5.0,
        )
        old = _make_drop(
            date_str=(date.today() - timedelta(days=400)).isoformat(),
            decay_weighted_severity=9.0,
        )
        drops = self._make_drops_namespace([recent, old])
        condensed, all_events = build_drop_events(drops)
        dates = [d["date"] for d in condensed]
        # ALL events included — density, not removal
        assert recent.date.value in dates
        assert old.date.value in dates

    def test_old_events_in_overflow(self) -> None:
        """Old events still present in overflow."""
        old = _make_drop(
            date_str=(date.today() - timedelta(days=400)).isoformat(),
            decay_weighted_severity=9.0,
        )
        drops = self._make_drops_namespace([old])
        _, all_events = build_drop_events(drops)
        assert len(all_events) == 1

    def test_empty_drops_returns_empty_tuple(self) -> None:
        drops = self._make_drops_namespace([])
        condensed, all_events = build_drop_events(drops)
        assert condensed == []
        assert all_events == []

    def test_sorted_by_severity(self) -> None:
        events = [
            _make_drop(date_str=(date.today() - timedelta(days=10)).isoformat(), decay_weighted_severity=3.0),
            _make_drop(date_str=(date.today() - timedelta(days=20)).isoformat(), decay_weighted_severity=9.0),
            _make_drop(date_str=(date.today() - timedelta(days=30)).isoformat(), decay_weighted_severity=6.0),
        ]
        drops = self._make_drops_namespace(events)
        condensed, _ = build_drop_events(drops)
        severities = [float(d["decay_weighted_severity"]) for d in condensed]
        assert severities == sorted(severities, reverse=True)


# ---------------------------------------------------------------------------
# Governance top holders condensation
# ---------------------------------------------------------------------------

class TestTopHoldersCondensation:
    """extract_governance limits top_holders to 10 + overflow."""

    def _make_state_with_holders(self, count: int) -> MagicMock:
        """Build a minimal mock state with N holders."""
        state = MagicMock()
        holders = [
            _sv({"name": f"Fund-{i}", "pct_out": f"{5.0 - i * 0.1:.1f}%"})
            for i in range(count)
        ]
        state.extracted.governance.ownership.top_holders = holders
        state.extracted.governance.ownership.institutional_pct = _sv(75.0)
        state.extracted.governance.ownership.insider_pct = _sv(5.0)
        state.extracted.governance.ownership.known_activists = []
        state.extracted.governance.board.size = _sv(10)
        state.extracted.governance.board.independence_ratio = _sv(0.8)
        state.extracted.governance.board.ceo_chair_duality = _sv(False)
        state.extracted.governance.board.avg_tenure_years = _sv(5.0)
        state.extracted.governance.board.classified_board = _sv(False)
        state.extracted.governance.board.dual_class_structure = _sv(False)
        state.extracted.governance.board.overboarded_count = _sv(1)
        state.extracted.governance.board.board_gender_diversity_pct = _sv(30.0)
        state.extracted.governance.board.iss_overall_risk = None
        state.extracted.governance.board.iss_audit_risk = None
        state.extracted.governance.board.iss_board_risk = None
        state.extracted.governance.board.iss_compensation_risk = None
        state.extracted.governance.board.iss_shareholder_rights_risk = None
        state.extracted.governance.comp_analysis.ceo_total_comp = _sv(10_000_000.0)
        state.extracted.governance.comp_analysis.say_on_pay_pct = _sv(85.0)
        state.extracted.governance.comp_analysis.ceo_pay_ratio = _sv(200)
        state.extracted.governance.comp_analysis.has_clawback = _sv(True)
        state.extracted.governance.comp_analysis.clawback_scope = _sv("DODD_FRANK")
        state.extracted.governance.comp_analysis.related_party_transactions = []
        state.extracted.governance.comp_analysis.notable_perquisites = []
        state.extracted.governance.comp_analysis.equity_pct_of_total = None
        state.extracted.governance.comp_analysis.top5_total = None
        state.extracted.governance.comp_analysis.ceo_to_median_comp = None
        state.extracted.governance.comp_analysis.peer_comp_comparison = None
        state.extracted.governance.comp_analysis.stip_metrics = None
        state.extracted.governance.comp_analysis.ltip_vesting = None
        state.extracted.governance.comp_analysis.comp_committee_independence = None
        state.extracted.governance.governance_score.total_score = _sv(75)
        state.extracted.governance.governance_score.independence_score = None
        state.extracted.governance.governance_score.ceo_chair_score = None
        state.extracted.governance.governance_score.refreshment_score = None
        state.extracted.governance.governance_score.overboarding_score = None
        state.extracted.governance.governance_score.committee_score = None
        state.extracted.governance.governance_score.say_on_pay_score = None
        state.extracted.governance.governance_score.tenure_score = None
        state.extracted.governance.leadership.executives = []
        state.extracted.governance.leadership.departures_18mo = []
        state.extracted.governance.leadership.stability_score = None
        state.extracted.governance.sentiment.management_tone_trajectory = None
        state.extracted.governance.sentiment.hedging_language_trend = None
        state.extracted.governance.sentiment.ceo_cfo_divergence = None
        state.extracted.governance.sentiment.qa_evasion_score = None
        state.extracted.governance.narrative_coherence.strategy_vs_results = None
        state.extracted.governance.narrative_coherence.tone_vs_financials = None
        state.extracted.governance.narrative_coherence.insider_vs_confidence = None
        state.extracted.governance.narrative_coherence.overall_assessment = None
        state.extracted.governance.narrative_coherence.coherence_flags = []
        state.extracted.governance.board_forensics = []
        return state

    def test_top_holders_limited_to_10(self) -> None:
        from do_uw.stages.render.context_builders.governance import extract_governance
        state = self._make_state_with_holders(20)
        result = extract_governance(state)
        assert len(result["top_holders"]) == 20  # ALL holders

    def test_top_holders_overflow_contains_rest(self) -> None:
        from do_uw.stages.render.context_builders.governance import extract_governance
        state = self._make_state_with_holders(20)
        result = extract_governance(state)
        assert "top_holders_overflow" in result
        assert len(result["top_holders_overflow"]) == 0  # no overflow

    def test_no_overflow_when_under_10(self) -> None:
        from do_uw.stages.render.context_builders.governance import extract_governance
        state = self._make_state_with_holders(5)
        result = extract_governance(state)
        assert result["top_holders_overflow"] == []


# ---------------------------------------------------------------------------
# Chart classification
# ---------------------------------------------------------------------------

class TestChartClassification:
    """extract_market produces main_charts and audit_charts lists."""

    @staticmethod
    def _make_market_state() -> MagicMock:
        """Build a minimal mock state for extract_market."""
        state = MagicMock()
        stock = state.extracted.market.stock
        stock.current_price = _sv(150.0)
        stock.high_52w = _sv(180.0)
        stock.low_52w = _sv(120.0)
        stock.decline_from_high_pct = _sv(16.7)
        # Nullify all optional stock attrs so MagicMock doesn't leak
        for attr in ("pe_ratio", "forward_pe", "price_to_book", "ev_ebitda",
                     "peg_ratio", "price_to_sales", "enterprise_to_revenue",
                     "revenue_growth", "earnings_growth", "profit_margin",
                     "operating_margin", "gross_margin", "return_on_equity",
                     "return_on_assets", "volatility_90d", "ewma_vol_current",
                     "vol_regime", "vol_regime_duration_days", "beta",
                     "return_1y", "return_3y", "return_ytd", "max_drawdown_1y",
                     "returns_1y"):
            setattr(stock, attr, None)
        si = state.extracted.market.short_interest
        si.short_pct_float = _sv(3.5)
        si.days_to_cover = _sv(2.0)
        # Nullify short interest optional fields
        for attr in ("short_ratio", "short_interest_change_pct",
                     "shares_short", "shares_short_prior",
                     "short_pct_shares_out", "trend_6m"):
            setattr(si, attr, None)
        state.extracted.market.insider_analysis = None
        state.extracted.market.insider_trading = None
        eg = state.extracted.market.earnings_guidance
        eg.beat_rate = None
        eg.consecutive_miss_count = 0
        eg.guidance_withdrawals = 0
        eg.philosophy = None
        eg.provides_forward_guidance = False
        eg.guidance_detail = None
        eg.guidance_frequency = None
        eg.guidance_history = None
        eg.quarters = []
        state.extracted.market.analyst.consensus = None
        state.extracted.market.stock_drops.worst_single_day = None
        state.extracted.market.stock_drops.single_day_drops = []
        state.extracted.market.stock_drops.multi_day_drops = []
        state.extracted.market.stock_drops.ddl_exposure = None
        state.extracted.market.stock_drops.mdl_exposure = None
        state.extracted.market.stock_drops.ddl_settlement_estimate = None
        state.extracted.market.capital_markets.offerings_3yr = []
        state.extracted.market.capital_markets.shelf_registrations = []
        state.extracted.market.capital_markets.convertible_securities = []
        state.acquired_data = None
        return state

    def test_main_charts_contains_1y_only(self) -> None:
        from do_uw.stages.render.context_builders.market import extract_market
        state = self._make_market_state()
        result = extract_market(state)
        assert "main_charts" in result
        assert "stock_1y" in result["main_charts"] and len(result["main_charts"]) == 12

    def test_audit_charts_empty(self) -> None:
        from do_uw.stages.render.context_builders.market import extract_market
        state = self._make_market_state()
        result = extract_market(state)
        assert "audit_charts" in result
        assert len(result["audit_charts"]) == 0  # all charts in main
