"""Tests for CLI entry point.

Tests the Typer CLI commands and Rich output integration.
All network calls are mocked to prevent real HTTP requests.
Phase 4/5 sub-orchestrators are mocked at sub-orchestrator level.
"""

from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from do_uw.cli import app
from do_uw.models.governance import GovernanceData
from do_uw.models.litigation import LitigationLandscape
from do_uw.models.market import MarketSignals
from do_uw.models.state import AcquiredData, AnalysisState

runner = CliRunner()

# Sample SEC data for mocking resolve stage network calls.
_MOCK_TICKERS: dict[str, dict[str, Any]] = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    "2": {"cik_str": 1652044, "ticker": "GOOGL", "title": "Alphabet Inc."},
    "3": {"cik_str": 1652044, "ticker": "GOOG", "title": "Alphabet Inc."},
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
    return _MOCK_SUBMISSIONS


def _mock_cache() -> MagicMock:
    """Create a mock AnalysisCache that always returns None."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache


def _mock_acquired_data() -> AcquiredData:
    """Create mock AcquiredData that passes all gates."""
    return AcquiredData(
        filings={
            "10-K": [{"f": 1}],
            "10-Q": [{"f": 2}],
            "DEF 14A": [{"f": 3}],
        },
        market_data={"info": {"marketCap": 1e12}},
        litigation_data={"results": [{"case": "test"}]},
        web_search_results={"news": [{"title": "test"}]},
        gate_results=[
            {
                "gate_name": "annual_report",
                "gate_type": "HARD",
                "passed": True,
                "message": "annual_report: passed",
            },
        ],
    )


def _mock_orchestrator_run(state: AnalysisState) -> AcquiredData:
    """Mock orchestrator run that returns complete acquired data."""
    return _mock_acquired_data()


def _apply_network_patches(stack: ExitStack) -> None:
    """Apply all network mock patches to an ExitStack.

    Includes Phase 4 sub-orchestrator mocks so individual extractors
    are not invoked during CLI integration tests.
    """
    stack.enter_context(patch(
        "do_uw.stages.resolve.ticker_resolver.sec_get",
        side_effect=_mock_sec_get,
    ))
    stack.enter_context(patch(
        "do_uw.stages.resolve.sec_identity.sec_get",
        side_effect=_mock_sec_get,
    ))
    stack.enter_context(patch(
        "do_uw.stages.resolve._enrich_from_yfinance",
    ))
    stack.enter_context(patch(
        "do_uw.stages.resolve.AnalysisCache",
        return_value=_mock_cache(),
    ))
    stack.enter_context(patch(
        "do_uw.stages.acquire.orchestrator."
        "AcquisitionOrchestrator.run",
        side_effect=_mock_orchestrator_run,
    ))
    stack.enter_context(patch(
        "do_uw.stages.acquire.AnalysisCache",
        return_value=_mock_cache(),
    ))
    stack.enter_context(patch(
        "do_uw.stages.extract.peer_group."
        "_fetch_candidates_financedatabase",
        return_value=[],
    ))
    stack.enter_context(patch(
        "do_uw.stages.extract.peer_group."
        "_enrich_candidate_yfinance",
        return_value={"marketCap": 1e12},
    ))
    # Phase 4: Mock sub-orchestrators for market and governance
    stack.enter_context(patch(
        "do_uw.stages.extract.run_market_extractors",
        return_value=MarketSignals(),
    ))
    stack.enter_context(patch(
        "do_uw.stages.extract.run_governance_extractors",
        return_value=GovernanceData(),
    ))
    # Phase 5: Mock sub-orchestrator for litigation
    stack.enter_context(patch(
        "do_uw.stages.extract.run_litigation_extractors",
        return_value=LitigationLandscape(),
    ))


class TestAnalyzeCommand:
    """Test the `do-uw analyze` command."""

    def test_analyze_command_runs(self, tmp_path: Path) -> None:
        """analyze command completes successfully with valid ticker."""
        with ExitStack() as stack:
            _apply_network_patches(stack)
            result = runner.invoke(
                app, ["analyze", "AAPL", "--output", str(tmp_path)]
            )
        assert result.exit_code == 0
        assert "Analysis complete" in result.output

    def test_analyze_creates_state_file(
        self, tmp_path: Path
    ) -> None:
        """analyze command creates state.json in output directory."""
        with ExitStack() as stack:
            _apply_network_patches(stack)
            runner.invoke(
                app,
                ["analyze", "MSFT", "--output", str(tmp_path)],
            )
        # Output dir is date-based: {TICKER}-{YYYY-MM-DD}
        msft_dirs = list(tmp_path.glob("MSFT-*"))
        assert msft_dirs, "No MSFT output directory created"
        state_path = msft_dirs[0] / "state.json"
        assert state_path.exists()

    def test_analyze_ticker_uppercased(
        self, tmp_path: Path
    ) -> None:
        """Ticker is converted to uppercase."""
        with ExitStack() as stack:
            _apply_network_patches(stack)
            result = runner.invoke(
                app,
                ["analyze", "aapl", "--output", str(tmp_path)],
            )
        assert result.exit_code == 0
        # State file is created under uppercase ticker date-based directory
        aapl_dirs = list(tmp_path.glob("AAPL-*"))
        assert aapl_dirs, "No AAPL output directory created"
        assert (aapl_dirs[0] / "state.json").exists()

    def test_analyze_resume_from_state(
        self, tmp_path: Path
    ) -> None:
        """Running analyze twice reuses existing state."""
        with ExitStack() as stack:
            _apply_network_patches(stack)
            runner.invoke(
                app,
                ["analyze", "GOOG", "--output", str(tmp_path)],
            )
        # Output dir is date-based: {TICKER}-{YYYY-MM-DD}
        goog_dirs = list(tmp_path.glob("GOOG-*"))
        assert goog_dirs, "No GOOG output directory created"
        assert (goog_dirs[0] / "state.json").exists()

        # Second run should resume (all stages already completed)
        with ExitStack() as stack:
            _apply_network_patches(stack)
            result = runner.invoke(
                app,
                ["analyze", "GOOG", "--output", str(tmp_path)],
            )
        assert result.exit_code == 0
        assert "Resuming" in result.output

    def test_analyze_peers_flag(self, tmp_path: Path) -> None:
        """--peers flag is accepted and parsed."""
        with ExitStack() as stack:
            _apply_network_patches(stack)
            result = runner.invoke(
                app,
                [
                    "analyze", "AAPL",
                    "--output", str(tmp_path),
                    "--peers", "MSFT,GOOG,AMZN",
                ],
            )
        assert result.exit_code == 0
        assert "Analysis complete" in result.output
