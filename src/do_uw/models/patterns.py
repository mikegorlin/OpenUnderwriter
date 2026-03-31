"""Pattern engine Pydantic models for state.scoring integration.

Defines PatternEngineResult (aggregated output from all engines) and
CaseLibraryEntry (schema for case library YAML entries).

Phase 109: Pattern Engines + Named Patterns.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from do_uw.stages.score.pattern_engine import ArchetypeResult, EngineResult

__all__ = [
    "CaseLibraryEntry",
    "PatternEngineResult",
]


class CaseLibraryEntry(BaseModel):
    """A single case library entry for Precedent Match similarity.

    Represents a historical D&O case with its reconstructed signal
    profile (the "fingerprint" at filing time) and outcome data.
    """

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(
        ..., description="Unique identifier (e.g., 'ENRON-2001')"
    )
    company_name: str = Field(
        ..., description="Company name at time of filing"
    )
    ticker: str = Field(
        ..., description="Stock ticker at time of filing"
    )
    filing_date: str = Field(
        ..., description="Date of initial SCA/enforcement filing (YYYY-MM-DD)"
    )
    claim_type: str = Field(
        ..., description="Primary claim type from SCAC taxonomy"
    )
    market_cap_at_filing: float = Field(
        ..., description="Market capitalization in USD at filing date"
    )
    sector: str = Field(
        ..., description="GICS sector at time of filing"
    )
    signal_profile: dict[str, str] = Field(
        ..., description="Map of signal_id to status at filing (RED/YELLOW/CLEAR/UNKNOWN)"
    )
    outcome: dict[str, object] = Field(
        ..., description="Case outcome: settlement_amount, dismissed, ongoing, etc."
    )
    signal_profile_confidence: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        ..., description="Confidence in reconstructed signal profile"
    )
    notes: str = Field(
        default="", description="Free-text context for underwriters"
    )


class PatternEngineResult(BaseModel):
    """Aggregated output from all pattern engines.

    Stored on state.scoring.pattern_engine_result. Contains results
    from all four engines and all six named archetypes.
    """

    model_config = ConfigDict(frozen=False)

    engine_results: list[EngineResult] = Field(
        default_factory=list,
        description="Results from each pattern engine",
    )
    archetype_results: list[ArchetypeResult] = Field(
        default_factory=list,
        description="Results from each named archetype evaluation",
    )
    computed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when pattern engines were run",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def any_fired(self) -> bool:
        """Whether any engine or archetype fired."""
        return any(r.fired for r in self.engine_results) or any(
            r.fired for r in self.archetype_results
        )
