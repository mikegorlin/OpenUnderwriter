"""Pipeline orchestrator for the 7-stage D&O underwriting analysis.

Runs stages sequentially with validation gates, state persistence,
and resume-from-failure support. The pipeline is the execution engine;
the CLI provides the user interface.

Per CLAUDE.md: State is serialized to JSON after each stage for
caching and resumption.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Protocol

from do_uw.models.common import StageStatus
from do_uw.models.state import PIPELINE_STAGES, AnalysisState
from do_uw.stages.acquire import AcquireStage
from do_uw.stages.analyze import AnalyzeStage
from do_uw.stages.benchmark import BenchmarkStage
from do_uw.stages.extract import ExtractStage
from do_uw.stages.render import RenderStage
from do_uw.stages.resolve import ResolveStage
from do_uw.stages.score import ScoreStage

logger = logging.getLogger(__name__)


class StageCallbacks(Protocol):
    """Callbacks for pipeline progress reporting."""

    def on_stage_start(self, stage_name: str, index: int, total: int) -> None:
        """Called when a stage begins execution."""
        ...

    def on_stage_complete(
        self, stage_name: str, index: int, total: int, duration: float | None
    ) -> None:
        """Called when a stage completes successfully."""
        ...

    def on_stage_skip(self, stage_name: str, index: int, total: int) -> None:
        """Called when a stage is skipped (already completed)."""
        ...

    def on_stage_fail(self, stage_name: str, index: int, total: int, error: str) -> None:
        """Called when a stage fails."""
        ...


class NullCallbacks:
    """No-op callbacks for when no progress reporting is needed."""

    def on_stage_start(self, stage_name: str, index: int, total: int) -> None:
        """No-op."""

    def on_stage_complete(
        self, stage_name: str, index: int, total: int, duration: float | None
    ) -> None:
        """No-op."""

    def on_stage_skip(self, stage_name: str, index: int, total: int) -> None:
        """No-op."""

    def on_stage_fail(self, stage_name: str, index: int, total: int, error: str) -> None:
        """No-op."""


def _build_default_stages(
    config: dict[str, Any] | None = None,
    output_dir: Path | None = None,
) -> list[
    ResolveStage
    | AcquireStage
    | ExtractStage
    | AnalyzeStage
    | ScoreStage
    | BenchmarkStage
    | RenderStage
]:
    """Create the default ordered stage list.

    Args:
        config: Optional pipeline configuration dict. Used to pass
            settings like search_budget to individual stages.
        output_dir: Optional output directory for RenderStage.
    """
    cfg = config or {}
    search_budget: int = cfg.get("search_budget", 50)
    search_fn: Any = cfg.get("search_fn")
    peers: list[str] | None = cfg.get("peers")
    use_llm: bool = not cfg.get("no_llm", False)
    progress_fn: Any = cfg.get("progress_fn")
    output_formats: list[str] | None = cfg.get("output_formats")
    return [
        ResolveStage(),
        AcquireStage(search_budget=search_budget, search_fn=search_fn),
        ExtractStage(peers=peers, use_llm=use_llm, progress_fn=progress_fn),
        AnalyzeStage(),
        ScoreStage(
            liberty_attachment=cfg.get("liberty_attachment"),
            liberty_product=cfg.get("liberty_product"),
        ),
        BenchmarkStage(),
        RenderStage(output_dir=output_dir, formats=output_formats),
    ]


class Pipeline:
    """Orchestrates the 7-stage D&O underwriting pipeline.

    Features:
    - Sequential execution with validation gates between stages
    - State persistence to JSON after each stage completion
    - Resume-from-failure: skips already-COMPLETED stages
    - Callbacks for CLI progress display
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        callbacks: StageCallbacks | None = None,
        pipeline_config: dict[str, Any] | None = None,
    ) -> None:
        self._stages = _build_default_stages(pipeline_config, output_dir)
        self._output_dir = output_dir
        self._callbacks: StageCallbacks = callbacks or NullCallbacks()

    @property
    def stage_names(self) -> list[str]:
        """Return ordered list of stage names."""
        return [s.name for s in self._stages]

    def run(self, state: AnalysisState) -> AnalysisState:
        """Run all pipeline stages sequentially.

        Skips stages that are already COMPLETED (resume support).
        Continues through failures (catch-and-continue).
        Persists state to JSON after each stage completion or failure.

        Args:
            state: The analysis state to process.

        Returns:
            The updated state after all stages complete (or fail).
        """
        total = len(self._stages)

        for index, stage in enumerate(self._stages):
            stage_result = state.stages.get(stage.name)
            print(
                f"DEBUG PIPELINE: stage={stage.name}, index={index}, status={stage_result.status if stage_result else 'None'}, stage_result exists? {stage_result is not None}"
            )

            # Resume support: skip completed stages
            if stage_result is not None and stage_result.status == StageStatus.COMPLETED:
                self._callbacks.on_stage_skip(stage.name, index, total)
                logger.info("Skipping completed stage: %s", stage.name)
                print(f"DEBUG PIPELINE: Skipping completed stage {stage.name}")
                continue

            # Validate preconditions
            try:
                print(f"DEBUG PIPELINE: Before validate_input for {stage.name}")
                stage.validate_input(state)
                print(f"DEBUG PIPELINE: validate_input passed for {stage.name}")
            except ValueError as exc:
                error_msg = f"Validation failed for {stage.name}: {exc}"
                print(f"DEBUG PIPELINE: Validation failed: {error_msg}")
                state.mark_stage_failed(stage.name, error_msg)
                self._callbacks.on_stage_fail(stage.name, index, total, error_msg)
                self._save_state(state)
                logger.warning(error_msg)
                continue  # catch-and-continue

            # Execute stage
            self._callbacks.on_stage_start(stage.name, index, total)
            try:
                print(f"DEBUG PIPELINE: Before stage.run for {stage.name}")
                stage.run(state)
                print(f"DEBUG PIPELINE: stage.run completed for {stage.name}")
            except Exception as exc:
                error_msg = f"Stage {stage.name} failed: {exc}"
                print(f"DEBUG PIPELINE: Stage {stage.name} failed: {exc}")
                state.mark_stage_failed(stage.name, str(exc))
                self._callbacks.on_stage_fail(stage.name, index, total, error_msg)
                self._save_state(state)
                logger.warning(error_msg)
                continue  # catch-and-continue

            # Report completion
            duration = state.stages[stage.name].duration_seconds
            self._callbacks.on_stage_complete(stage.name, index, total, duration)
            logger.info(
                "Completed stage: %s (%.2fs)",
                stage.name,
                duration or 0.0,
            )

            # Log LLM cost summary after extraction stage
            llm_cost = state.pipeline_metadata.get("llm_cost")
            if llm_cost and stage.name == "extract":
                logger.info(
                    "[EXTRACT] LLM tokens: %d->%d, estimated cost: $%.4f (%d extractions)",
                    llm_cost.get("input_tokens", 0),
                    llm_cost.get("output_tokens", 0),
                    llm_cost.get("total_cost_usd", 0.0),
                    llm_cost.get("extractions", 0),
                )

            # Persist state after each stage
            self._save_state(state)

        # Post-pipeline render audit (Phase 92 -- REND-01/REND-02)
        # Run full render audit against state + rendered HTML and inject into state
        try:
            self._inject_render_audit(state)
        except Exception:
            logger.debug("Render audit injection failed", exc_info=True)

        # Log pipeline metadata summary at completion
        if state.pipeline_metadata:
            meta = state.pipeline_metadata
            parts: list[str] = []
            if meta.get("data_freshness_date"):
                parts.append(f"data_freshness={meta['data_freshness_date']}")
            llm_cost = meta.get("llm_cost")
            if llm_cost:
                parts.append(f"llm_cost=${llm_cost.get('total_cost_usd', 0.0):.4f}")
            if parts:
                logger.info("Pipeline metadata: %s", ", ".join(parts))

        # Post-pipeline learning: generate calibration + lifecycle proposals
        try:
            from do_uw.brain.post_pipeline import run_post_pipeline_learning

            learning = run_post_pipeline_learning(
                (
                    state.company.identity.ticker
                    if state.company and state.company.identity
                    else None
                )
                or state.ticker
                or "UNKNOWN"
            )
            if learning.get("total_proposals", 0) > 0:
                logger.info(
                    "Post-pipeline learning: %d proposals generated "
                    "(run 'brain apply-proposal' to review)",
                    learning["total_proposals"],
                )
        except Exception:
            logger.debug("Post-pipeline learning skipped", exc_info=True)

        return state

    def _inject_render_audit(self, state: AnalysisState) -> None:
        """Run full render audit and inject results into pipeline_metadata.

        Reads the rendered HTML from the output directory (if available),
        runs compute_render_audit against it, and stores the result in
        state.pipeline_metadata["render_audit"].

        Phase 92 -- REND-01/REND-02.
        """
        from do_uw.stages.render.render_audit import compute_render_audit

        state_dict = state.model_dump(mode="python")
        rendered_text = ""

        # Try to read the rendered HTML from output
        if self._output_dir:
            ticker = state.ticker or "output"
            html_path = self._output_dir / f"{ticker}.html"
            if html_path.exists():
                try:
                    rendered_text = html_path.read_text(encoding="utf-8")
                except Exception:
                    pass

        audit = compute_render_audit(state_dict, rendered_text)

        state.pipeline_metadata["render_audit"] = {
            "excluded": [{"path": ef.path, "reason": ef.reason} for ef in audit.excluded_fields],
            "unrendered": audit.unrendered_fields,
            "total_extracted": audit.total_extracted,
            "total_rendered": audit.total_rendered,
            "total_excluded": audit.total_excluded,
            "coverage_pct": audit.coverage_pct,
        }

        logger.info(
            "Render audit: %d/%d fields rendered (%.1f%%), %d excluded, %d unrendered",
            audit.total_rendered,
            audit.total_extracted,
            audit.coverage_pct,
            audit.total_excluded,
            len(audit.unrendered_fields),
        )

        # Re-save state with render_audit metadata
        self._save_state(state)

    def _save_state(self, state: AnalysisState) -> Path | None:
        """Save state to JSON in output directory.

        Strips large transient blobs (Company Facts XBRL ~4MB) from the
        filings dict before serialization. These are cached in SQLite and
        re-fetched on next run. The in-memory state is not modified.

        Returns the path to the saved file, or None if no output_dir.
        """
        if self._output_dir is None:
            return None

        self._output_dir.mkdir(parents=True, exist_ok=True)
        state_path = self._output_dir / "state.json"

        # Strip large blobs before serialization, restore after.
        stripped = _strip_filings_blobs(state)
        try:
            state_json = state.model_dump_json(indent=2)
            state_path.write_text(state_json, encoding="utf-8")
        finally:
            _restore_filings_blobs(state, stripped)

        logger.debug("State saved to %s", state_path)
        return state_path

    @staticmethod
    def load_state(state_path: Path) -> AnalysisState:
        """Load state from a JSON file for pipeline resumption.

        Args:
            state_path: Path to state.json file.

        Returns:
            Deserialized AnalysisState.

        Raises:
            FileNotFoundError: If state file doesn't exist.
            ValueError: If state file is invalid.
        """
        if not state_path.exists():
            msg = f"State file not found: {state_path}"
            raise FileNotFoundError(msg)

        try:
            raw = state_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            return AnalysisState.model_validate(data)
        except Exception as exc:
            msg = f"Invalid state file {state_path}: {exc}"
            raise ValueError(msg) from exc

    @staticmethod
    def validate_stage_order() -> bool:
        """Verify that built-in stages match PIPELINE_STAGES order."""
        stages = _build_default_stages()
        return [s.name for s in stages] == PIPELINE_STAGES


# Keys to strip from acquired_data.filings before serialization.
# These are large transient blobs cached in SQLite. Stripping them
# keeps state.json under ~2MB instead of 15+MB.
_FILINGS_STRIP_KEYS = ("company_facts", "filing_texts", "exhibit_21")


def _strip_filings_blobs(
    state: AnalysisState,
) -> dict[str, Any]:
    """Remove large blobs from filings dict before serialization.

    Returns the stripped values so they can be restored after.
    """
    stripped: dict[str, Any] = {}
    if state.acquired_data is None:
        return stripped

    filings = state.acquired_data.filings
    for key in _FILINGS_STRIP_KEYS:
        if key in filings:
            stripped[key] = filings.pop(key)

    return stripped


def _restore_filings_blobs(
    state: AnalysisState,
    stripped: dict[str, Any],
) -> None:
    """Restore stripped blobs to filings dict after serialization."""
    if not stripped or state.acquired_data is None:
        return

    for key, value in stripped.items():
        state.acquired_data.filings[key] = value


class PipelineError(Exception):
    """Raised when a pipeline stage fails."""
