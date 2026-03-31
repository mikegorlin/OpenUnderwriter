"""Integration tests for LLM 8-K event enrichment in market extraction.

Tests that 8-K events (departures, agreements, acquisitions, restatements,
earnings) are processed and stored for cross-domain downstream access.
Falls back to existing market extraction when no 8-K data is available.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from do_uw.models.market import MarketSignals
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.llm.schemas.eight_k import EightKExtraction
from do_uw.stages.extract.validation import ExtractionReport


def _eight_k_dict(**kwargs: Any) -> dict[str, object]:
    """Build an EightKExtraction as a dict."""
    return EightKExtraction(**kwargs).model_dump()


def _make_state(
    eight_k_dicts: list[dict[str, object]] | None = None,
) -> AnalysisState:
    """Create state with optional LLM 8-K extractions."""
    state = AnalysisState(ticker="TEST")
    llm_extractions: dict[str, object] = {}
    if eight_k_dicts:
        for i, d in enumerate(eight_k_dicts):
            llm_extractions[f"8-K:0001-24-{i:06d}"] = d
    state.acquired_data = AcquiredData(llm_extractions=llm_extractions)
    return state


def _run_market(state: AnalysisState) -> tuple[MarketSignals, list[ExtractionReport]]:
    """Run market extractors with all individual extractors mocked."""
    reports: list[ExtractionReport] = []
    mock = MagicMock()
    with (
        patch("do_uw.stages.extract.extract_market._run_stock_performance",
              return_value=(MagicMock(), MagicMock())),
        patch("do_uw.stages.extract.extract_market._run_insider_trading",
              return_value=MagicMock()),
        patch("do_uw.stages.extract.extract_market._run_short_interest",
              return_value=MagicMock()),
        patch("do_uw.stages.extract.extract_market._run_earnings_guidance",
              return_value=MagicMock()),
        patch("do_uw.stages.extract.extract_market._run_analyst_sentiment",
              return_value=MagicMock()),
        patch("do_uw.stages.extract.extract_market._run_capital_markets",
              return_value=MagicMock()),
        patch("do_uw.stages.extract.extract_market._run_adverse_events",
              return_value=mock),
    ):
        from do_uw.stages.extract.extract_market import run_market_extractors

        signals = run_market_extractors(state, reports)
    return signals, reports


class TestMarketWithLLMDepartures:
    """8-K departures processed and logged."""

    def test_departures_counted(self) -> None:
        """Departure count stored in market_data."""
        state = _make_state(eight_k_dicts=[
            _eight_k_dict(
                departing_officer="Jane Doe",
                departing_officer_title="CFO",
                departure_reason="resignation",
                event_date="2024-06-15",
            ),
            _eight_k_dict(
                departing_officer="John Smith",
                departing_officer_title="CTO",
                is_termination=True,
                event_date="2024-09-01",
            ),
        ])
        _run_market(state)

        assert state.acquired_data is not None
        events = state.acquired_data.market_data.get("eight_k_events")
        assert isinstance(events, dict)
        assert events["departure_count"] == 2


class TestMarketWithLLMRestatements:
    """Restatements cross-populated to audit risk flag."""

    def test_restatement_flagged(self) -> None:
        """has_restatement flag set when restatements found."""
        state = _make_state(eight_k_dicts=[
            _eight_k_dict(
                restatement_periods=["Q1 2024", "Q2 2024"],
                restatement_reason="Revenue recognition error",
                event_date="2024-11-15",
            ),
        ])
        _run_market(state)

        assert state.acquired_data is not None
        assert state.acquired_data.market_data.get("has_restatement") is True
        details = state.acquired_data.market_data.get("restatement_details")
        assert isinstance(details, list)
        assert len(details) == 1
        assert details[0]["reason"] == "Revenue recognition error"
        assert "Q1 2024" in details[0]["periods"]


class TestMarketWithoutEightK:
    """Falls back to existing market extraction when no 8-K data."""

    def test_no_eight_k_no_events(self) -> None:
        """No 8-K events stored when LLM extractions are empty."""
        state = _make_state(eight_k_dicts=None)
        _run_market(state)

        assert state.acquired_data is not None
        assert "eight_k_events" not in state.acquired_data.market_data
        assert "has_restatement" not in state.acquired_data.market_data


class TestMarketMixedEightKEvents:
    """Multiple 8-K event types processed correctly."""

    def test_mixed_events_all_counted(self) -> None:
        """All event types counted in summary."""
        state = _make_state(eight_k_dicts=[
            _eight_k_dict(
                departing_officer="Jane Doe",
                departing_officer_title="CFO",
                event_date="2024-06-15",
            ),
            _eight_k_dict(
                agreement_type="Credit Agreement",
                counterparty="Bank of America",
                event_date="2024-07-01",
            ),
            _eight_k_dict(
                transaction_type="acquisition",
                target_name="DataCo Inc.",
                transaction_value=500_000_000.0,
                event_date="2024-08-15",
            ),
            _eight_k_dict(
                revenue=2_500_000_000.0,
                eps=3.45,
                guidance_update="Raised FY2025 guidance",
                event_date="2024-10-28",
            ),
        ])
        _run_market(state)

        assert state.acquired_data is not None
        events = state.acquired_data.market_data.get("eight_k_events")
        assert isinstance(events, dict)
        assert events["departure_count"] == 1
        assert events["agreement_count"] == 1
        assert events["acquisition_count"] == 1
        assert events["earnings_event_count"] == 1
        assert events["restatement_count"] == 0
