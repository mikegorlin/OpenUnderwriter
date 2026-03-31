"""Pipeline stages for D&O underwriting analysis.

Provides the Stage protocol and stage registry. All concrete stages
implement this protocol.
"""

from __future__ import annotations

from typing import Protocol

from do_uw.models.state import AnalysisState


class Stage(Protocol):
    """Protocol that every pipeline stage must implement.

    Each stage:
    1. Has a name matching one of PIPELINE_STAGES
    2. Validates that preconditions are met (previous stages completed)
    3. Runs the stage logic, mutating AnalysisState in place
    """

    @property
    def name(self) -> str:
        """Stage name (must match one of PIPELINE_STAGES)."""
        ...

    def validate_input(self, state: AnalysisState) -> None:
        """Check preconditions. Raises ValueError if not met."""
        ...

    def run(self, state: AnalysisState) -> None:
        """Execute stage logic, mutating state in place."""
        ...


__all__ = ["Stage"]
