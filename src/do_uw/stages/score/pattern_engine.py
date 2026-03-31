"""PatternEngine Protocol and shared result models for pattern detection engines.

Defines the pluggable PatternEngine Protocol (mirroring ScoringLens/SeverityLens),
EngineResult (single engine output), and ArchetypeResult (named archetype evaluation).

Phase 109: Pattern Engines + Named Patterns.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from do_uw.models.state import AnalysisState

__all__ = [
    "ArchetypeResult",
    "EngineResult",
    "PatternEngine",
]


class EngineResult(BaseModel):
    """Result from a single pattern engine evaluation.

    Each engine returns one EngineResult per run. The ``fired`` flag
    indicates whether the engine detected a compound risk pattern.
    """

    model_config = ConfigDict(frozen=False)

    engine_id: str = Field(description="Unique engine identifier")
    engine_name: str = Field(description="Human-readable engine name")
    fired: bool = Field(
        default=False,
        description="Whether the engine detected a pattern",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the finding (0.0-1.0)",
    )
    headline: str = Field(
        default="",
        description="One-sentence summary of the finding",
    )
    findings: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed findings from the engine",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific metadata",
    )


class ArchetypeResult(BaseModel):
    """Result from evaluating a named D&O archetype.

    Archetypes are named compound patterns (e.g., 'Accounting Time Bomb')
    with required signal sets. When enough required signals fire, the
    archetype is matched and may impose a recommendation floor.
    """

    model_config = ConfigDict(frozen=False)

    archetype_id: str = Field(description="Archetype identifier")
    archetype_name: str = Field(description="Human-readable archetype name")
    fired: bool = Field(
        default=False,
        description="Whether the archetype matched",
    )
    signals_matched: int = Field(
        default=0,
        description="Number of required signals that matched",
    )
    signals_required: int = Field(
        default=0,
        description="Total required signals for this archetype",
    )
    matched_signal_ids: list[str] = Field(
        default_factory=list,
        description="Signal IDs that matched",
    )
    recommendation_floor: str | None = Field(
        default=None,
        description="Minimum tier when archetype fires (e.g., 'ELEVATED')",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Match confidence (0.0-1.0)",
    )
    historical_cases: list[str] = Field(
        default_factory=list,
        description="Historical case references",
    )


@runtime_checkable
class PatternEngine(Protocol):
    """Protocol for pluggable pattern detection engines.

    All pattern engines implement this interface to detect compound
    risk patterns from signal evaluation results. Mirrors the
    ScoringLens and SeverityLens Protocol patterns.
    """

    @property
    def engine_id(self) -> str: ...

    @property
    def engine_name(self) -> str: ...

    def evaluate(
        self,
        signal_results: dict[str, Any],
        *,
        state: AnalysisState | None = None,
    ) -> EngineResult: ...
