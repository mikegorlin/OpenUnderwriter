"""Tests for pipeline orchestrator.

Tests sequential execution, validation gates, resume-from-failure,
state persistence, and callback integration.

All network calls are mocked to prevent real HTTP requests.
Phase 4/5 sub-orchestrators are mocked at sub-orchestrator level.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import StageStatus
from do_uw.models.governance import GovernanceData
from do_uw.models.litigation import LitigationLandscape
from do_uw.models.market import MarketSignals
from do_uw.models.state import (
    PIPELINE_STAGES,
    AcquiredData,
    AnalysisState,
    ExtractedData,
)
from do_uw.pipeline import NullCallbacks, Pipeline, PipelineError

# Sample SEC data for mocking resolve stage network calls.
_MOCK_TICKERS: dict[str, dict[str, Any]] = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 12345, "ticker": "TEST", "title": "Test Corp"},
    "2": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
}

_MOCK_SUBMISSIONS: dict[str, Any] = {
    "cik": "320193",
    "entityType": "operating",
    "sic": "3571",
    "sicDescription": "Electronic Computers",
    "name": "Apple Inc.",
    "tickers": ["AAPL"],
    "exchanges": ["Nasdaq"],
    "stateOfIncorporation": "CA",
    "fiscalYearEnd": "0930",
    "filings": {"recent": {"form": ["10-K", "10-Q"]}, "files": []},
}


def _mock_sec_get(url: str) -> dict[str, Any]:
    """Return mock SEC data based on URL pattern."""
    if "company_tickers" in url:
        return _MOCK_TICKERS
    # Return submissions for any CIK lookup.
    return _MOCK_SUBMISSIONS


def _mock_cache() -> MagicMock:
    """Create a mock AnalysisCache that always returns None (no cache)."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


def _mock_acquired_data() -> AcquiredData:
    """Create mock AcquiredData that passes all gates."""
    return AcquiredData(
        filings={"10-K": [{"f": 1}], "10-Q": [{"f": 2}], "DEF 14A": [{"f": 3}]},
        market_data={"info": {"marketCap": 1e12}},
        litigation_data={"results": [{"case": "test"}]},
        web_search_results={"news": [{"title": "test"}]},
        gate_results=[
            {"gate_name": "annual_report", "gate_type": "HARD", "passed": True,
             "message": "annual_report: passed"},
        ],
    )


def _mock_orchestrator_run(state: AnalysisState) -> AcquiredData:
    """Mock orchestrator run that returns complete acquired data."""
    return _mock_acquired_data()


class TrackingCallbacks:
    """Test callbacks that record all events."""

    def __init__(self) -> None:
        self.events: list[tuple[str, str, int, int]] = []

    def on_stage_start(self, stage_name: str, index: int, total: int) -> None:
        self.events.append(("start", stage_name, index, total))

    def on_stage_complete(
        self, stage_name: str, index: int, total: int, duration: float | None
    ) -> None:
        self.events.append(("complete", stage_name, index, total))

    def on_stage_skip(self, stage_name: str, index: int, total: int) -> None:
        self.events.append(("skip", stage_name, index, total))

    def on_stage_fail(
        self, stage_name: str, index: int, total: int, error: str
    ) -> None:
        self.events.append(("fail", stage_name, index, total))


class TestPipelineExecution:
    """Test pipeline runs all stages correctly."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance",
        return_value={"marketCap": 1e12},
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase",
        return_value=[],
    )
    @patch(
        "do_uw.stages.acquire.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch(
        "do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator.run",
        side_effect=_mock_orchestrator_run,
    )
    @patch(
        "do_uw.stages.resolve.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch("do_uw.stages.resolve._enrich_from_yfinance")
    @patch(
        "do_uw.stages.resolve.sec_identity.sec_get",
        side_effect=_mock_sec_get,
    )
    @patch(
        "do_uw.stages.resolve.ticker_resolver.sec_get",
        side_effect=_mock_sec_get,
    )
    def test_pipeline_runs_all_stages(
        self,
        _mock_tr: MagicMock,
        _mock_si: MagicMock,
        _mock_yf: MagicMock,
        _mock_resolve_cache: MagicMock,
        _mock_orch: MagicMock,
        _mock_acquire_cache: MagicMock,
        _mock_fd: MagicMock,
        _mock_yf_enrich: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """All 7 stages execute in order, each marked COMPLETED."""
        state = AnalysisState(ticker="AAPL")
        pipeline = Pipeline()
        result = pipeline.run(state)

        for stage_name in PIPELINE_STAGES:
            assert result.stages[stage_name].status == StageStatus.COMPLETED
            assert result.stages[stage_name].started_at is not None
            assert result.stages[stage_name].completed_at is not None

    def test_pipeline_stage_order_matches(self) -> None:
        """Built-in stages match PIPELINE_STAGES constant."""
        assert Pipeline.validate_stage_order()

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance",
        return_value={"marketCap": 1e12},
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase",
        return_value=[],
    )
    @patch(
        "do_uw.stages.acquire.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch(
        "do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator.run",
        side_effect=_mock_orchestrator_run,
    )
    @patch(
        "do_uw.stages.resolve.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch("do_uw.stages.resolve._enrich_from_yfinance")
    @patch(
        "do_uw.stages.resolve.sec_identity.sec_get",
        side_effect=_mock_sec_get,
    )
    @patch(
        "do_uw.stages.resolve.ticker_resolver.sec_get",
        side_effect=_mock_sec_get,
    )
    def test_pipeline_callbacks_fire(
        self,
        _mock_tr: MagicMock,
        _mock_si: MagicMock,
        _mock_yf: MagicMock,
        _mock_resolve_cache: MagicMock,
        _mock_orch: MagicMock,
        _mock_acquire_cache: MagicMock,
        _mock_fd: MagicMock,
        _mock_yf_enrich: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
    ) -> None:
        """Callbacks receive start and complete events for each stage."""
        state = AnalysisState(ticker="TEST")
        tracker = TrackingCallbacks()
        pipeline = Pipeline(callbacks=tracker)
        pipeline.run(state)

        starts = [e for e in tracker.events if e[0] == "start"]
        completes = [e for e in tracker.events if e[0] == "complete"]
        assert len(starts) == 7
        assert len(completes) == 7

        # Verify order
        for i, stage_name in enumerate(PIPELINE_STAGES):
            assert starts[i][1] == stage_name
            assert completes[i][1] == stage_name


class TestPipelineResume:
    """Test pipeline resume-from-failure."""

    @patch(
        "do_uw.stages.score.BrainLoader",
    )
    @patch(
        "do_uw.stages.analyze.BrainLoader",
    )
    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance",
        return_value={"marketCap": 1e12},
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase",
        return_value=[],
    )
    @patch(
        "do_uw.stages.acquire.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch(
        "do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator.run",
        side_effect=_mock_orchestrator_run,
    )
    @patch(
        "do_uw.stages.resolve.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch("do_uw.stages.resolve._enrich_from_yfinance")
    @patch(
        "do_uw.stages.resolve.sec_identity.sec_get",
        side_effect=_mock_sec_get,
    )
    @patch(
        "do_uw.stages.resolve.ticker_resolver.sec_get",
        side_effect=_mock_sec_get,
    )
    def test_resume_skips_completed_stages(
        self,
        _mock_tr: MagicMock,
        _mock_si: MagicMock,
        _mock_yf: MagicMock,
        _mock_resolve_cache: MagicMock,
        _mock_orch: MagicMock,
        _mock_acquire_cache: MagicMock,
        _mock_fd: MagicMock,
        _mock_yf_enrich: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
        mock_analyze_config: MagicMock,
        mock_score_config: MagicMock,
    ) -> None:
        """Pipeline skips stages already marked COMPLETED."""
        # Mock BrainLoader for AnalyzeStage and ScoreStage
        mock_brain = MagicMock()
        mock_brain.checks = {"signals": []}
        mock_brain.scoring = {
            "factors": {}, "tiers": [], "severity_ranges": {}, "tower_positions": {}
        }
        mock_brain.red_flags = {"escalation_triggers": []}
        mock_brain.patterns = {"patterns": []}
        mock_brain.sectors = {}
        mock_analyze_config.return_value.load_all.return_value = mock_brain
        mock_score_config.return_value.load_all.return_value = mock_brain

        state = AnalysisState(ticker="AAPL")
        # Mark first 3 stages as completed
        for stage_name in PIPELINE_STAGES[:3]:
            state.mark_stage_running(stage_name)
            state.mark_stage_completed(stage_name)
        # AnalyzeStage now requires extracted data (no longer a stub)
        state.extracted = ExtractedData()

        tracker = TrackingCallbacks()
        pipeline = Pipeline(callbacks=tracker)
        pipeline.run(state)

        skips = [e for e in tracker.events if e[0] == "skip"]
        starts = [e for e in tracker.events if e[0] == "start"]
        assert len(skips) == 3
        assert len(starts) == 4  # remaining 4 stages

    def test_empty_ticker_fails_validation(self) -> None:
        """Pipeline marks resolve as FAILED for empty ticker (catch-and-continue)."""
        state = AnalysisState(ticker="")
        pipeline = Pipeline()
        result = pipeline.run(state)
        assert result.stages["resolve"].status == StageStatus.FAILED


class TestStatePersistence:
    """Test state saves to JSON after each stage."""

    @patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    )
    @patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    )
    @patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    )
    @patch(
        "do_uw.stages.extract.peer_group._enrich_candidate_yfinance",
        return_value={"marketCap": 1e12},
    )
    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase",
        return_value=[],
    )
    @patch(
        "do_uw.stages.acquire.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch(
        "do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator.run",
        side_effect=_mock_orchestrator_run,
    )
    @patch(
        "do_uw.stages.resolve.AnalysisCache",
        return_value=_mock_cache(),
    )
    @patch("do_uw.stages.resolve._enrich_from_yfinance")
    @patch(
        "do_uw.stages.resolve.sec_identity.sec_get",
        side_effect=_mock_sec_get,
    )
    @patch(
        "do_uw.stages.resolve.ticker_resolver.sec_get",
        side_effect=_mock_sec_get,
    )
    def test_state_saved_after_each_stage(
        self,
        _mock_tr: MagicMock,
        _mock_si: MagicMock,
        _mock_yf: MagicMock,
        _mock_resolve_cache: MagicMock,
        _mock_orch: MagicMock,
        _mock_acquire_cache: MagicMock,
        _mock_fd: MagicMock,
        _mock_yf_enrich: MagicMock,
        _mock_market: MagicMock,
        _mock_gov: MagicMock,
        _mock_lit: MagicMock,
        tmp_path: Path,
    ) -> None:
        """State file is written to output directory."""
        state = AnalysisState(ticker="AAPL")
        pipeline = Pipeline(output_dir=tmp_path)
        pipeline.run(state)

        state_path = tmp_path / "state.json"
        assert state_path.exists()

        # Verify it's valid JSON and deserializable
        raw = state_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        loaded = AnalysisState.model_validate(data)
        assert loaded.ticker == "AAPL"
        assert all(
            loaded.stages[s].status == StageStatus.COMPLETED
            for s in PIPELINE_STAGES
        )

    def test_load_state_from_file(self, tmp_path: Path) -> None:
        """Pipeline.load_state deserializes saved state."""
        state = AnalysisState(ticker="MSFT")
        state.mark_stage_running("resolve")
        state.mark_stage_completed("resolve")

        state_path = tmp_path / "state.json"
        state_path.write_text(
            state.model_dump_json(indent=2), encoding="utf-8"
        )

        loaded = Pipeline.load_state(state_path)
        assert loaded.ticker == "MSFT"
        assert loaded.stages["resolve"].status == StageStatus.COMPLETED

    def test_load_nonexistent_state_raises(self, tmp_path: Path) -> None:
        """Loading non-existent state raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Pipeline.load_state(tmp_path / "missing.json")


class TestNullCallbacks:
    """Test NullCallbacks don't raise."""

    def test_null_callbacks_noop(self) -> None:
        """NullCallbacks methods don't raise."""
        cb = NullCallbacks()
        cb.on_stage_start("test", 0, 1)
        cb.on_stage_complete("test", 0, 1, 0.5)
        cb.on_stage_skip("test", 0, 1)
        cb.on_stage_fail("test", 0, 1, "error")
