"""Validation runner for multi-ticker batch pipeline execution.

Orchestrates sequential pipeline runs across a list of tickers with
checkpointing after each completion, continue-on-failure semantics,
and comprehensive result tracking.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.pipeline import Pipeline, PipelineError
from do_uw.validation.report import (
    TickerResult,
    ValidationReport,
    compute_summary,
)

logger = logging.getLogger(__name__)

# Checkpoint file name written after each ticker completes.
_CHECKPOINT_FILE = ".validation_checkpoint.json"


class ValidationRunner:
    """Run the full pipeline on multiple tickers with checkpointing.

    Features:
    - Sequential ticker execution with Rich progress updates
    - Checkpoint after each ticker (skip completed on restart)
    - Continue-on-failure: individual ticker errors do not halt the batch
    - Per-ticker timing and cost tracking
    - Configurable fresh/resume and LLM modes
    """

    def __init__(
        self,
        tickers: list[str],
        output_dir: Path,
        fresh: bool = True,
        use_llm: bool = True,
        pipeline_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the validation runner.

        Args:
            tickers: List of ticker symbols to validate.
            output_dir: Root output directory (tickers get subdirs).
            fresh: If True, clear ticker output before running.
            use_llm: If True, enable LLM extraction.
            pipeline_config: Additional pipeline configuration dict.
        """
        self._tickers = tickers
        self._output_dir = output_dir
        self._fresh = fresh
        self._use_llm = use_llm
        self._extra_config = pipeline_config or {}

    def run(self) -> ValidationReport:
        """Execute the pipeline on all configured tickers.

        Returns:
            ValidationReport with per-ticker results and summary.
        """
        checkpoint = self._load_checkpoint()
        results: dict[str, TickerResult] = {}

        # Restore previously completed/failed results from checkpoint.
        for ticker, data in checkpoint.get("completed", {}).items():
            results[ticker] = TickerResult(
                status=data.get("status", "PASS"),
                duration_seconds=data.get("duration", 0.0),
                cost_usd=data.get("cost_usd", 0.0),
            )
        for ticker, data in checkpoint.get("failed", {}).items():
            results[ticker] = TickerResult(
                status="FAIL",
                duration_seconds=data.get("duration", 0.0),
                cost_usd=0.0,
                error=data.get("error", "Unknown error"),
                failed_stage=data.get("stage"),
            )

        total = len(self._tickers)

        for idx, ticker in enumerate(self._tickers, 1):
            # Skip already-processed tickers from checkpoint.
            if ticker in results:
                logger.info(
                    "[%d/%d] Skipping %s (already %s)",
                    idx, total, ticker, results[ticker].status,
                )
                continue

            logger.info("[%d/%d] Running pipeline for %s", idx, total, ticker)
            result = self._run_ticker(ticker)
            results[ticker] = result

            # Checkpoint after each ticker.
            self._save_checkpoint(results)
            logger.info(
                "[%d/%d] %s: %s (%.1fs)",
                idx, total, ticker, result.status, result.duration_seconds,
            )

        summary = compute_summary(results)
        return ValidationReport(
            run_date=datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            results=results,
            summary=summary,
        )

    def _run_ticker(self, ticker: str) -> TickerResult:
        """Run the pipeline on a single ticker with error handling.

        Args:
            ticker: Stock ticker symbol.

        Returns:
            TickerResult with status, duration, and error info.
        """
        ticker_dir = self._output_dir / ticker

        if self._fresh and ticker_dir.exists():
            shutil.rmtree(ticker_dir)
            logger.debug("Cleared output directory: %s", ticker_dir)

        ticker_dir.mkdir(parents=True, exist_ok=True)
        state = AnalysisState(ticker=ticker)

        config: dict[str, Any] = {
            "no_llm": not self._use_llm,
            **self._extra_config,
        }
        pipeline = Pipeline(
            output_dir=ticker_dir,
            pipeline_config=config,
        )

        start = time.monotonic()
        try:
            pipeline.run(state)
            duration = time.monotonic() - start
            return TickerResult(
                status="PASS",
                duration_seconds=round(duration, 1),
                cost_usd=0.0,
            )
        except PipelineError as exc:
            duration = time.monotonic() - start
            # Extract failed stage name from error message if possible.
            failed_stage = _extract_failed_stage(str(exc))
            return TickerResult(
                status="FAIL",
                duration_seconds=round(duration, 1),
                cost_usd=0.0,
                error=str(exc),
                failed_stage=failed_stage,
            )
        except Exception as exc:
            duration = time.monotonic() - start
            return TickerResult(
                status="FAIL",
                duration_seconds=round(duration, 1),
                cost_usd=0.0,
                error=f"Unexpected error: {exc}",
                failed_stage=None,
            )

    def _load_checkpoint(self) -> dict[str, Any]:
        """Load checkpoint data from disk.

        Returns:
            Checkpoint dict with "completed" and "failed" sections,
            or empty dict if no checkpoint exists.
        """
        path = self._output_dir / _CHECKPOINT_FILE
        if not path.exists():
            return {}

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            result: dict[str, Any] = raw
            return result
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load checkpoint: %s", exc)
            return {}

    def _save_checkpoint(self, results: dict[str, TickerResult]) -> None:
        """Save checkpoint data to disk after each ticker.

        Args:
            results: Current accumulated results.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        path = self._output_dir / _CHECKPOINT_FILE

        completed: dict[str, dict[str, Any]] = {}
        failed: dict[str, dict[str, Any]] = {}

        for ticker, result in results.items():
            if result.status == "PASS":
                completed[ticker] = {
                    "status": "PASS",
                    "duration": result.duration_seconds,
                    "cost_usd": result.cost_usd,
                }
            else:
                failed[ticker] = {
                    "error": result.error or "Unknown",
                    "stage": result.failed_stage,
                    "duration": result.duration_seconds,
                }

        data = {"completed": completed, "failed": failed}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _extract_failed_stage(error_msg: str) -> str | None:
    """Extract the stage name from a PipelineError message.

    PipelineError messages follow the pattern:
    "Stage <name> failed: ..." or "Validation failed for <name>: ..."

    Args:
        error_msg: The error message string.

    Returns:
        Stage name if extractable, otherwise None.
    """
    if error_msg.startswith("Stage "):
        parts = error_msg.split(" ", 3)
        if len(parts) >= 3:
            return parts[1]
    if error_msg.startswith("Validation failed for "):
        parts = error_msg.removeprefix("Validation failed for ").split(":", 1)
        if parts:
            return parts[0].strip()
    return None
