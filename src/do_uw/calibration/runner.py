"""Calibration runner for check calibration and knowledge enrichment.

Executes the pipeline on the calibration ticker set, collects per-check
detail from state.json, and produces a CalibrationReport with tier
comparisons and check result summaries. Supports checkpointing for
interrupted runs and integrates with the learning infrastructure.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from pydantic import BaseModel, ConfigDict, Field

from do_uw.calibration.config import CalibrationTicker
from do_uw.models.state import AnalysisState
from do_uw.pipeline import Pipeline, PipelineError

logger = logging.getLogger(__name__)

_CHECKPOINT_FILE = ".calibration_checkpoint.json"


def _parse_signal_result(
    signal_id: str, signal_data: dict[str, Any]
) -> SignalResultSummary:
    """Parse a raw check result dict into a SignalResultSummary.

    Args:
        signal_id: Check identifier.
        signal_data: Raw check result dict from state.json.

    Returns:
        Parsed SignalResultSummary.
    """
    tl_raw: Any = signal_data.get("threshold_level")
    tl_val = str(tl_raw) if tl_raw is not None else None
    factors_raw: Any = signal_data.get("factors", [])
    factors_list: list[str] = []
    if isinstance(factors_raw, list):
        typed_factors = cast(list[Any], factors_raw)
        factors_list = [str(f) for f in typed_factors]
    return SignalResultSummary(
        signal_id=signal_id,
        status=str(signal_data.get("status", "UNKNOWN")),
        value=signal_data.get("value"),
        threshold_level=tl_val,
        evidence=str(signal_data.get("evidence", "")),
        factors=factors_list,
    )


class SignalResultSummary(BaseModel):
    """Summary of a single check result from state.json."""

    model_config = ConfigDict(frozen=False)

    signal_id: str = Field(description="Check identifier")
    status: str = Field(
        description="TRIGGERED, CLEAR, SKIPPED, or INFO"
    )
    value: Any = Field(default=None, description="Check value")
    threshold_level: str | None = Field(
        default=None, description="Threshold level if applicable"
    )
    evidence: str = Field(default="", description="Evidence text")
    factors: list[str] = Field(
        default_factory=list,
        description="Factor IDs this check contributes to",
    )


class CalibrationTickerResult(BaseModel):
    """Result of running calibration on a single ticker."""

    model_config = ConfigDict(frozen=False)

    ticker: str = Field(description="Ticker symbol")
    expected_tier: str = Field(
        description="Expected tier from calibration config"
    )
    actual_tier: str | None = Field(
        default=None, description="Actual tier from pipeline scoring"
    )
    quality_score: float | None = Field(
        default=None, description="Quality score from pipeline"
    )
    signal_results: dict[str, SignalResultSummary] = Field(
        default_factory=dict,
        description="Per-check results keyed by check ID",
    )
    patterns_detected: list[str] = Field(
        default_factory=list,
        description="Composite pattern IDs that fired",
    )
    factor_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Factor deductions keyed by factor ID",
    )
    duration_seconds: float = Field(
        default=0.0, description="Pipeline execution time"
    )
    error: str | None = Field(
        default=None, description="Error message if pipeline failed"
    )


class CalibrationReport(BaseModel):
    """Aggregate calibration report across all tickers."""

    model_config = ConfigDict(frozen=False)

    tickers: dict[str, CalibrationTickerResult] = Field(
        default_factory=dict,
        description="Per-ticker calibration results",
    )
    run_date: str = Field(
        default="",
        description="ISO timestamp of the calibration run",
    )
    total_duration: float = Field(
        default=0.0, description="Total wall-clock duration in seconds"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Tickers that failed with error messages",
    )


class CalibrationRunner:
    """Run the pipeline on calibration tickers and collect per-check data.

    Follows the ValidationRunner pattern with checkpointing, continue-
    on-failure semantics, and per-ticker result tracking. After each
    ticker completes, loads state.json to extract check results,
    scoring factors, and tier assignments.
    """

    def __init__(
        self,
        tickers: list[CalibrationTicker],
        output_dir: Path,
        fresh: bool = True,
        use_llm: bool = True,
        top_n: int = 20,
        pipeline_config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the calibration runner.

        Args:
            tickers: List of calibration ticker configs.
            output_dir: Root output directory (tickers get subdirs).
            fresh: If True, clear ticker output before running.
            use_llm: If True, enable LLM extraction.
            top_n: Number of top-impact checks for ground truth.
            pipeline_config: Additional pipeline configuration dict.
        """
        self._tickers = tickers
        self._output_dir = output_dir
        self._fresh = fresh
        self._use_llm = use_llm
        self._top_n = top_n
        self._extra_config = pipeline_config or {}

    def run(self) -> CalibrationReport:
        """Execute the pipeline on all calibration tickers.

        Returns:
            CalibrationReport with per-ticker results and errors.
        """
        checkpoint = self._load_checkpoint()
        results: dict[str, CalibrationTickerResult] = {}
        errors: list[str] = []

        # Restore previously completed results from checkpoint.
        for ticker_sym, data in checkpoint.get("completed", {}).items():
            result = CalibrationTickerResult.model_validate(data)
            results[ticker_sym] = result
            if result.error is not None:
                errors.append(f"{ticker_sym}: {result.error}")

        total = len(self._tickers)
        start_time = time.monotonic()

        for idx, ticker_cfg in enumerate(self._tickers, 1):
            ticker_sym = ticker_cfg["ticker"]

            # Skip already-processed tickers from checkpoint.
            if ticker_sym in results:
                logger.info(
                    "[%d/%d] Skipping %s (already completed)",
                    idx,
                    total,
                    ticker_sym,
                )
                continue

            logger.info(
                "[%d/%d] Running calibration for %s",
                idx,
                total,
                ticker_sym,
            )
            result = self._run_ticker(ticker_cfg)
            results[ticker_sym] = result

            if result.error is not None:
                errors.append(f"{ticker_sym}: {result.error}")

            # Record in learning infrastructure.
            self._record_learning(result)

            # Checkpoint after each ticker.
            self._save_checkpoint(results)
            logger.info(
                "[%d/%d] %s: tier=%s (expected %s) score=%s (%.1fs)",
                idx,
                total,
                ticker_sym,
                result.actual_tier,
                result.expected_tier,
                result.quality_score,
                result.duration_seconds,
            )

        total_duration = time.monotonic() - start_time

        return CalibrationReport(
            tickers=results,
            run_date=datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            total_duration=round(total_duration, 1),
            errors=errors,
        )

    def _run_ticker(
        self, ticker_cfg: CalibrationTicker
    ) -> CalibrationTickerResult:
        """Run pipeline on a single ticker and extract calibration data.

        Args:
            ticker_cfg: Calibration ticker configuration.

        Returns:
            CalibrationTickerResult with check data or error.
        """
        ticker_sym = ticker_cfg["ticker"]
        expected_tier = ticker_cfg["expected_tier"]
        ticker_dir = self._output_dir / ticker_sym

        if self._fresh and ticker_dir.exists():
            shutil.rmtree(ticker_dir)
            logger.debug("Cleared output directory: %s", ticker_dir)

        ticker_dir.mkdir(parents=True, exist_ok=True)
        state = AnalysisState(ticker=ticker_sym)

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

            # Load state.json to extract check detail.
            return self._extract_results(
                ticker_sym, expected_tier, ticker_dir, duration
            )
        except PipelineError as exc:
            duration = time.monotonic() - start
            return CalibrationTickerResult(
                ticker=ticker_sym,
                expected_tier=expected_tier,
                duration_seconds=round(duration, 1),
                error=str(exc),
            )
        except Exception as exc:
            duration = time.monotonic() - start
            return CalibrationTickerResult(
                ticker=ticker_sym,
                expected_tier=expected_tier,
                duration_seconds=round(duration, 1),
                error=f"Unexpected error: {exc}",
            )

    def _extract_results(
        self,
        ticker: str,
        expected_tier: str,
        ticker_dir: Path,
        duration: float,
    ) -> CalibrationTickerResult:
        """Extract calibration data from completed pipeline state.json.

        Args:
            ticker: Ticker symbol.
            expected_tier: Expected tier from config.
            ticker_dir: Directory containing state.json.
            duration: Pipeline execution time in seconds.

        Returns:
            CalibrationTickerResult with full check detail.
        """
        state_path = ticker_dir / "state.json"
        if not state_path.exists():
            return CalibrationTickerResult(
                ticker=ticker,
                expected_tier=expected_tier,
                duration_seconds=round(duration, 1),
                error="state.json not found after pipeline completion",
            )

        try:
            raw = json.loads(state_path.read_text(encoding="utf-8"))
            state = AnalysisState.model_validate(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            return CalibrationTickerResult(
                ticker=ticker,
                expected_tier=expected_tier,
                duration_seconds=round(duration, 1),
                error=f"Failed to parse state.json: {exc}",
            )

        # Extract check results from analysis.
        signal_results: dict[str, SignalResultSummary] = {}
        if state.analysis is not None:
            for signal_id, signal_data_raw in state.analysis.signal_results.items():
                if isinstance(signal_data_raw, dict):
                    cd = cast(dict[str, Any], signal_data_raw)
                    signal_results[signal_id] = _parse_signal_result(
                        signal_id, cd
                    )

        # Extract scoring data.
        actual_tier: str | None = None
        quality_score: float | None = None
        factor_scores: dict[str, float] = {}
        patterns_detected: list[str] = []

        if state.scoring is not None:
            quality_score = state.scoring.quality_score
            if state.scoring.tier is not None:
                actual_tier = state.scoring.tier.tier.value
            for fs in state.scoring.factor_scores:
                factor_scores[fs.factor_id] = fs.points_deducted
            patterns_detected = [
                p.pattern_id
                for p in state.scoring.patterns_detected
                if p.detected
            ]

        return CalibrationTickerResult(
            ticker=ticker,
            expected_tier=expected_tier,
            actual_tier=actual_tier,
            quality_score=quality_score,
            signal_results=signal_results,
            patterns_detected=patterns_detected,
            factor_scores=factor_scores,
            duration_seconds=round(duration, 1),
        )

    def _record_learning(self, result: CalibrationTickerResult) -> None:
        """Record analysis run in the learning infrastructure.

        Args:
            result: Completed ticker result.
        """
        if result.error is not None:
            return  # Don't record failed runs.

        try:
            from do_uw.knowledge.learning import (
                AnalysisOutcome,
                record_analysis_run,
            )
            from do_uw.knowledge.store import KnowledgeStore

            store = KnowledgeStore()
            fired = [
                cid
                for cid, cr in result.signal_results.items()
                if cr.status == "TRIGGERED"
            ]
            clear = [
                cid
                for cid, cr in result.signal_results.items()
                if cr.status == "CLEAR"
            ]

            outcome = AnalysisOutcome(
                ticker=result.ticker,
                run_date=datetime.now(tz=UTC),
                checks_fired=fired,
                checks_clear=clear,
                quality_score=result.quality_score or 0.0,
                tier=result.actual_tier or "UNKNOWN",
            )
            record_analysis_run(store, outcome)
        except Exception as exc:
            logger.warning(
                "Failed to record learning for %s: %s",
                result.ticker,
                exc,
            )

    def _load_checkpoint(self) -> dict[str, Any]:
        """Load checkpoint data from disk.

        Returns:
            Checkpoint dict with "completed" section,
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

    def _save_checkpoint(
        self, results: dict[str, CalibrationTickerResult]
    ) -> None:
        """Save checkpoint data to disk after each ticker.

        Args:
            results: Current accumulated results.
        """
        self._output_dir.mkdir(parents=True, exist_ok=True)
        path = self._output_dir / _CHECKPOINT_FILE

        completed: dict[str, Any] = {}
        for ticker_sym, result in results.items():
            completed[ticker_sym] = result.model_dump()

        data: dict[str, Any] = {"completed": completed}
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
