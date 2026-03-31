"""Acquire stage: Data acquisition from SEC, stock, litigation, and sentiment sources.

Orchestrates all data acquisition clients via AcquisitionOrchestrator.
Populates state.acquired_data with raw data, metadata, and gate results.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import StageStatus
from do_uw.models.state import AnalysisState
from do_uw.stages.acquire.orchestrator import AcquisitionOrchestrator

logger = logging.getLogger(__name__)


class AcquireStage:
    """Acquire raw data from external sources.

    Delegates to AcquisitionOrchestrator which coordinates SEC, market,
    litigation, news clients and blind spot discovery searches.
    """

    def __init__(
        self,
        search_budget: int = 50,
        search_fn: Any | None = None,
    ) -> None:
        """Initialize with configurable search budget and search function.

        Args:
            search_budget: Maximum web searches per analysis run.
            search_fn: Optional callable for web search. Takes a query
                string, returns list of dicts with title/url/snippet.
        """
        self._search_budget = search_budget
        self._search_fn = search_fn

    @property
    def name(self) -> str:
        """Stage name."""
        return "acquire"

    def validate_input(self, state: AnalysisState) -> None:
        """Verify resolve stage is complete and company identity exists."""
        resolve = state.stages.get("resolve")
        if resolve is None or resolve.status != StageStatus.COMPLETED:
            msg = "Resolve stage must be completed before acquire"
            raise ValueError(msg)
        if state.company is None:
            msg = "Company profile must be populated before acquire"
            raise ValueError(msg)
        if state.company.identity.cik is None:
            msg = "Company CIK must be resolved before acquire"
            raise ValueError(msg)

    def run(self, state: AnalysisState) -> None:
        """Run acquisition orchestrator and populate state.

        Derives brain requirements before creating the orchestrator so
        acquisition is brain-aware. Brain failures never block acquisition.
        """
        state.mark_stage_running(self.name)
        try:
            # Derive brain-driven acquisition requirements.
            brain_manifest = None
            try:
                from do_uw.stages.acquire.brain_requirements import (
                    derive_brain_requirements,
                )

                brain_manifest = derive_brain_requirements()
            except Exception:
                logger.info(
                    "Brain requirement derivation failed; "
                    "proceeding without brain guidance",
                    exc_info=True,
                )

            cache = AnalysisCache()
            try:
                orchestrator = AcquisitionOrchestrator(
                    cache=cache,
                    search_budget=self._search_budget,
                    search_fn=self._search_fn,
                    brain_manifest=brain_manifest,
                )
                acquired_data = orchestrator.run(state)
                state.acquired_data = acquired_data
                state.mark_stage_completed(self.name)
            finally:
                cache.close()
        except Exception as exc:
            if state.stages[self.name].status != StageStatus.COMPLETED:
                state.mark_stage_failed(self.name, str(exc))
            raise


__all__ = ["AcquireStage"]
