"""Tests for multi-ticker validation infrastructure.

Tests cover ticker configuration, runner checkpoint/resume,
continue-on-failure, and report generation.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from do_uw.pipeline import PipelineError
from do_uw.validation.config import VALIDATION_TICKERS, get_tickers
from do_uw.validation.report import (
    TickerResult,
    ValidationReport,
    compute_summary,
    load_report,
    print_report,
    save_report,
)
from do_uw.validation.runner import ValidationRunner, _extract_failed_stage


# --- Ticker configuration tests ---


class TestTickerConfig:
    """Tests for VALIDATION_TICKERS constant and get_tickers()."""

    def test_ticker_config_has_24_entries(self) -> None:
        """Verify total ticker count: 18 standard + 5 known-outcome + 1 FPI edge case."""
        assert len(VALIDATION_TICKERS) == 24

    def test_ticker_config_covers_all_industries(self) -> None:
        """Every industry vertical has at least 2 standard tickers."""
        industries = [
            t["industry"]
            for t in VALIDATION_TICKERS
            if t["category"] == "standard"
        ]
        from collections import Counter

        counts = Counter(industries)
        expected_industries = {
            "TECH_SAAS",
            "BIOTECH_PHARMA",
            "ENERGY_UTILITIES",
            "HEALTHCARE",
            "CPG_CONSUMER",
            "MEDIA_ENTERTAINMENT",
            "INDUSTRIALS",
            "REITS",
            "TRANSPORTATION",
        }
        assert set(counts.keys()) == expected_industries
        for industry, count in counts.items():
            assert count >= 2, f"{industry} has only {count} ticker(s)"

    def test_ticker_config_has_known_outcomes(self) -> None:
        """SMCI, RIDE, COIN, LCID, PLUG are present as known-outcome."""
        known = get_tickers("known_outcome")
        for ticker in ("SMCI", "RIDE", "COIN", "LCID", "PLUG"):
            assert ticker in known, f"{ticker} missing from known_outcome"

    def test_ticker_config_has_fpi_edge_case(self) -> None:
        """TSM is present as an edge_case (Foreign Private Issuer)."""
        edge = get_tickers("edge_case")
        assert "TSM" in edge

    def test_get_tickers_filter_standard(self) -> None:
        """get_tickers('standard') returns only standard tickers."""
        standard = get_tickers("standard")
        assert len(standard) == 18

    def test_get_tickers_filter_known_outcome(self) -> None:
        """get_tickers('known_outcome') returns 5 known-outcome tickers."""
        known = get_tickers("known_outcome")
        assert len(known) == 5

    def test_get_tickers_filter_edge_case(self) -> None:
        """get_tickers('edge_case') returns 1 edge-case ticker."""
        edge = get_tickers("edge_case")
        assert len(edge) == 1

    def test_get_tickers_no_filter_returns_all(self) -> None:
        """get_tickers(None) returns all tickers."""
        all_tickers = get_tickers()
        assert len(all_tickers) == 24

    def test_all_tickers_are_unique(self) -> None:
        """No duplicate tickers in the configuration."""
        tickers = [t["ticker"] for t in VALIDATION_TICKERS]
        assert len(tickers) == len(set(tickers))


# --- ValidationRunner tests ---


class TestValidationRunner:
    """Tests for ValidationRunner checkpoint/resume and continue-on-failure."""

    @patch("do_uw.validation.runner.Pipeline")
    def test_runner_runs_all_tickers(
        self, mock_pipeline_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Runner calls Pipeline.run() for each ticker."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        runner = ValidationRunner(
            tickers=["AAPL", "MSFT"],
            output_dir=tmp_path,
            fresh=False,
        )
        report = runner.run()

        assert len(report.results) == 2
        assert report.results["AAPL"].status == "PASS"
        assert report.results["MSFT"].status == "PASS"

    @patch("do_uw.validation.runner.Pipeline")
    def test_runner_checkpoint_skip(
        self, mock_pipeline_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Completed tickers in checkpoint are skipped on restart."""
        # Pre-seed a checkpoint with AAPL completed.
        checkpoint = {
            "completed": {
                "AAPL": {"status": "PASS", "duration": 100.0, "cost_usd": 0.50}
            },
            "failed": {},
        }
        checkpoint_path = tmp_path / ".validation_checkpoint.json"
        checkpoint_path.write_text(json.dumps(checkpoint))

        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        runner = ValidationRunner(
            tickers=["AAPL", "MSFT"],
            output_dir=tmp_path,
            fresh=False,
        )
        report = runner.run()

        # AAPL should be restored from checkpoint, MSFT should run.
        assert len(report.results) == 2
        assert report.results["AAPL"].status == "PASS"
        assert report.results["AAPL"].duration_seconds == 100.0
        assert report.results["MSFT"].status == "PASS"

        # Pipeline should only be called once (for MSFT).
        assert mock_pipeline_cls.call_count == 1

    @patch("do_uw.validation.runner.Pipeline")
    def test_runner_continue_on_failure(
        self, mock_pipeline_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Pipeline failure for one ticker does not halt the batch."""
        mock_pipeline = MagicMock()
        call_count = 0

        def run_side_effect(state: MagicMock) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if state.ticker == "AAPL":
                msg = "Stage extract failed: some error"
                raise PipelineError(msg)
            return state

        mock_pipeline.run.side_effect = run_side_effect
        mock_pipeline_cls.return_value = mock_pipeline

        runner = ValidationRunner(
            tickers=["AAPL", "MSFT", "GOOG"],
            output_dir=tmp_path,
            fresh=False,
        )
        report = runner.run()

        assert len(report.results) == 3
        assert report.results["AAPL"].status == "FAIL"
        assert report.results["AAPL"].failed_stage == "extract"
        assert report.results["MSFT"].status == "PASS"
        assert report.results["GOOG"].status == "PASS"

    @patch("do_uw.validation.runner.Pipeline")
    def test_runner_fresh_clears_output(
        self, mock_pipeline_cls: MagicMock, tmp_path: Path
    ) -> None:
        """With fresh=True, existing ticker output dirs are cleared."""
        # Create a pre-existing ticker directory.
        ticker_dir = tmp_path / "AAPL"
        ticker_dir.mkdir()
        (ticker_dir / "old_file.txt").write_text("stale data")

        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        runner = ValidationRunner(
            tickers=["AAPL"],
            output_dir=tmp_path,
            fresh=True,
        )
        runner.run()

        # Old file should be gone (dir recreated).
        assert not (ticker_dir / "old_file.txt").exists()

    @patch("do_uw.validation.runner.Pipeline")
    def test_checkpoint_file_written(
        self, mock_pipeline_cls: MagicMock, tmp_path: Path
    ) -> None:
        """Checkpoint file is written after each ticker."""
        mock_pipeline = MagicMock()
        mock_pipeline_cls.return_value = mock_pipeline

        runner = ValidationRunner(
            tickers=["AAPL"],
            output_dir=tmp_path,
            fresh=False,
        )
        runner.run()

        checkpoint_path = tmp_path / ".validation_checkpoint.json"
        assert checkpoint_path.exists()
        data = json.loads(checkpoint_path.read_text())
        assert "AAPL" in data["completed"]


# --- Report tests ---


class TestValidationReport:
    """Tests for report generation, serialization, and display."""

    def test_compute_summary(self) -> None:
        """compute_summary calculates correct aggregate stats."""
        results = {
            "AAPL": TickerResult(status="PASS", duration_seconds=100.0, cost_usd=1.00),
            "MSFT": TickerResult(status="PASS", duration_seconds=200.0, cost_usd=1.50),
            "GOOG": TickerResult(
                status="FAIL", duration_seconds=50.0, cost_usd=0.50,
                error="Stage extract failed", failed_stage="extract",
            ),
        }
        summary = compute_summary(results)
        assert summary.total == 3
        assert summary.passed == 2
        assert summary.failed == 1
        assert summary.total_cost_usd == 3.0
        # avg = (100 + 200 + 50) / 3 = 116.666...
        assert abs(summary.avg_duration_seconds - 116.7) < 0.1

    def test_report_json_round_trip(self, tmp_path: Path) -> None:
        """ValidationReport survives JSON serialization/deserialization."""
        results = {
            "AAPL": TickerResult(status="PASS", duration_seconds=100.0, cost_usd=1.00),
            "MSFT": TickerResult(
                status="FAIL", duration_seconds=50.0, cost_usd=0.50,
                error="test error", failed_stage="resolve",
            ),
        }
        summary = compute_summary(results)
        report = ValidationReport(
            run_date="2026-02-11T00:00:00Z",
            results=results,
            summary=summary,
        )

        report_path = tmp_path / "report.json"
        save_report(report, report_path)

        loaded = load_report(report_path)
        assert loaded.run_date == "2026-02-11T00:00:00Z"
        assert len(loaded.results) == 2
        assert loaded.results["AAPL"].status == "PASS"
        assert loaded.results["MSFT"].error == "test error"
        assert loaded.summary.total == 2
        assert loaded.summary.passed == 1

    def test_print_report_no_crash(self, capsys: pytest.CaptureFixture[str]) -> None:
        """print_report() executes without errors."""
        results = {
            "AAPL": TickerResult(status="PASS", duration_seconds=100.0, cost_usd=1.00),
            "MSFT": TickerResult(
                status="FAIL", duration_seconds=50.0, cost_usd=0.50,
                error="Some pipeline error that is quite long and needs truncation " * 3,
                failed_stage="extract",
            ),
        }
        summary = compute_summary(results)
        report = ValidationReport(
            run_date="2026-02-11T00:00:00Z",
            results=results,
            summary=summary,
        )
        # Should not raise.
        print_report(report)

    def test_report_empty_results(self) -> None:
        """compute_summary handles empty results dict."""
        summary = compute_summary({})
        assert summary.total == 0
        assert summary.passed == 0
        assert summary.avg_duration_seconds == 0.0


# --- Utility tests ---


class TestExtractFailedStage:
    """Tests for _extract_failed_stage helper."""

    def test_stage_pattern(self) -> None:
        assert _extract_failed_stage("Stage extract failed: timeout") == "extract"

    def test_validation_pattern(self) -> None:
        assert _extract_failed_stage("Validation failed for resolve: missing ticker") == "resolve"

    def test_unknown_pattern(self) -> None:
        assert _extract_failed_stage("Something went wrong") is None
