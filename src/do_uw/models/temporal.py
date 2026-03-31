"""Pydantic models for temporal change detection in the ANALYZE stage.

Provides:
- TemporalClassification: Trend direction enum (IMPROVING through CRITICAL)
- TemporalDataPoint: Single period measurement
- TemporalSignal: Multi-period trend analysis result
- TemporalAnalysisResult: Aggregate of all temporal signals for a company
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class TemporalClassification(StrEnum):
    """Classification of a multi-period trend direction.

    IMPROVING: Consecutive favorable movements
    STABLE: No sustained directional change
    DETERIORATING: Consecutive adverse movements (threshold met)
    CRITICAL: Sustained adverse movements exceeding critical threshold
    """

    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    DETERIORATING = "DETERIORATING"
    CRITICAL = "CRITICAL"


class TemporalDataPoint(BaseModel):
    """A single period measurement for temporal analysis.

    Represents one data point in a time series (e.g., Q3 2024 revenue).
    """

    period: str = Field(description="Period label (e.g., 'Q3 2024', 'FY 2023')")
    value: float = Field(description="Metric value for this period")
    source: str = Field(default="", description="Data source for this measurement")


class TemporalSignal(BaseModel):
    """Result of analyzing a single metric across multiple periods.

    Captures the trend direction, magnitude, and evidence for one
    financial metric (e.g., revenue growth, gross margin, DSO days).
    """

    metric_name: str = Field(description="Name of the metric analyzed")
    periods: list[TemporalDataPoint] = Field(
        default_factory=list,
        description="Ordered data points from oldest to newest",
    )
    classification: TemporalClassification = Field(
        default=TemporalClassification.STABLE,
        description="Trend direction classification",
    )
    consecutive_adverse: int = Field(
        default=0,
        description="Number of consecutive adverse period-over-period changes",
    )
    total_change_pct: float = Field(
        default=0.0,
        description="Total percentage change from first to last period",
    )
    evidence: str = Field(
        default="",
        description="Human-readable explanation of the temporal pattern",
    )
    source_periods: list[str] = Field(
        default_factory=list,
        description="Period labels used in the analysis",
    )


class TemporalAnalysisResult(BaseModel):
    """Aggregate result of all temporal analyses for a company.

    Contains all temporal signals detected across financial metrics,
    plus a summary assessment.
    """

    signals: list[TemporalSignal] = Field(
        default_factory=list,
        description="All temporal signals detected",
    )
    summary: str = Field(
        default="",
        description="Overall temporal assessment summary",
    )


__all__ = [
    "TemporalAnalysisResult",
    "TemporalClassification",
    "TemporalDataPoint",
    "TemporalSignal",
]
