"""Common types used across all D&O underwriting models.

Provides:
- SourcedValue[T]: Generic wrapper enforcing source + confidence on every data point
- Confidence: Data quality tier enum
- StageStatus / StageResult: Pipeline stage tracking
- DataFreshness: Temporal data quality indicator
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import TypeVar

from pydantic import BaseModel, ConfigDict, Field


class Confidence(StrEnum):
    """Data quality tier.

    HIGH: Audited/official (SEC filings, exchange data)
    MEDIUM: Unaudited/estimates (press releases, analyst data)
    LOW: Derived/web (news, web search, single source)
    """

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


T = TypeVar("T")


class SourcedValue[T](BaseModel):
    """Every data point carries provenance. NON-NEGOTIABLE per CLAUDE.md.

    Wraps any value type with mandatory source attribution and confidence
    level. This is the foundational data integrity pattern for the entire
    system.
    """

    model_config = ConfigDict(frozen=False)

    value: T
    source: str = Field(description="Filing type + date + URL/CIK reference")
    confidence: Confidence
    as_of: datetime = Field(description="When this data was valid")
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC)
    )


class StageStatus(StrEnum):
    """Pipeline stage execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StageResult(BaseModel):
    """Tracks execution status of a single pipeline stage."""

    model_config = ConfigDict(frozen=False)

    stage: str
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    error: str | None = None


class DataFreshness(StrEnum):
    """Temporal data quality indicator.

    CURRENT: Data retrieved within last 90 days
    AGING: Data is 90-180 days old
    STALE: Data is over 180 days old
    """

    CURRENT = "CURRENT"
    AGING = "AGING"
    STALE = "STALE"
