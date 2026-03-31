"""SQLAlchemy ORM models for the D&O underwriting knowledge store.

Defines the complete schema for signals, patterns, red flags, sectors,
scoring rules, notes, version history, and industry playbooks.

All models use SQLAlchemy 2.0 declarative style with Mapped[] type
annotations for pyright strict compliance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    """Base class for all knowledge store models."""

    type_annotation_map: ClassVar[dict[type, Any]] = {
        dict[str, Any]: JSON,
        list[Any]: JSON,
    }


class Signal(Base):
    """Primary knowledge table for D&O underwriting signals.

    Mirrors the structure of signals.json with additional lifecycle
    and provenance tracking fields. Each signal represents a single
    risk signal that can be evaluated against company data.
    """

    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    section: Mapped[int] = mapped_column(Integer, nullable=False)
    pillar: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str | None] = mapped_column(String, nullable=True)
    execution_mode: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="ACTIVE"
    )
    threshold_type: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    threshold_value: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    required_data: Mapped[Any] = mapped_column(JSON, nullable=False)
    data_locations: Mapped[Any] = mapped_column(JSON, nullable=False)
    scoring_factor: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    scoring_rule: Mapped[str | None] = mapped_column(String, nullable=True)
    output_section: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    origin: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1
    )
    metadata_json: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    # Phase 26 classification fields
    category: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    plaintiff_lenses_json: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    signal_type: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    hazard_or_signal: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    # Phase 31 knowledge model enrichment fields
    content_type: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rationale: Mapped[str | None] = mapped_column(String, nullable=True)
    field_key: Mapped[str | None] = mapped_column(String, nullable=True)
    extraction_path: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    pattern_ref: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    history: Mapped[list[SignalHistory]] = relationship(
        "SignalHistory", back_populates="signal", cascade="all, delete-orphan"
    )
    notes: Mapped[list[Note]] = relationship(
        "Note", back_populates="signal", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Signal(id={self.id!r}, name={self.name!r}, status={self.status!r})>"


# Backward-compat alias
Check = Signal


class SignalHistory(Base):
    """Version history for signal modifications.

    Records every field change with old/new values, timestamps,
    who made the change, and why. Enables full audit trail for
    knowledge evolution.
    """

    __tablename__ = "signal_history"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    signal_id: Mapped[str] = mapped_column(
        String, ForeignKey("signals.id"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    field_name: Mapped[str] = mapped_column(String, nullable=False)
    old_value: Mapped[str | None] = mapped_column(String, nullable=True)
    new_value: Mapped[str | None] = mapped_column(String, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    changed_by: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)

    signal: Mapped[Signal] = relationship("Signal", back_populates="history")

    def __repr__(self) -> str:
        return (
            f"<SignalHistory(signal_id={self.signal_id!r}, "
            f"field={self.field_name!r}, v{self.version})>"
        )


# Backward-compat alias
CheckHistory = SignalHistory


class Pattern(Base):
    """Composite risk patterns from patterns.json.

    Patterns represent multi-signal risk indicators that combine
    several individual signals or data points into a higher-level
    risk assessment.
    """

    __tablename__ = "patterns"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    allegation_types: Mapped[Any] = mapped_column(JSON, nullable=False)
    trigger_conditions: Mapped[Any] = mapped_column(JSON, nullable=False)
    score_impact: Mapped[Any] = mapped_column(JSON, nullable=False)
    severity_modifier: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="ACTIVE"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<Pattern(id={self.id!r}, name={self.name!r})>"


class ScoringRule(Base):
    """Factor scoring rules from scoring.json.

    Each rule maps a condition to point deductions within a
    scoring factor. Rules may trigger critical red flags.
    """

    __tablename__ = "scoring_rules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    factor_id: Mapped[str] = mapped_column(String, nullable=False)
    condition: Mapped[str] = mapped_column(String, nullable=False)
    points: Mapped[float] = mapped_column(Float, nullable=False)
    triggers_crf: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<ScoringRule(id={self.id!r}, factor={self.factor_id!r}, "
            f"points={self.points})>"
        )


class RedFlag(Base):
    """Critical red flag escalation triggers from red_flags.json.

    Red flags represent hard gates that cap the maximum quality
    score and restrict tier placement regardless of other factors.
    """

    __tablename__ = "red_flags"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    condition: Mapped[str] = mapped_column(String, nullable=False)
    detection_logic: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    max_tier: Mapped[str] = mapped_column(String, nullable=False)
    max_quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="ACTIVE"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<RedFlag(id={self.id!r}, name={self.name!r})>"


class Sector(Base):
    """Sector baseline values from sectors.json.

    Stores per-sector baseline metrics used for contextual scoring
    (e.g., what constitutes 'high' short interest varies by sector).
    """

    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    sector_code: Mapped[str] = mapped_column(String, nullable=False)
    metric_name: Mapped[str] = mapped_column(String, nullable=False)
    baseline_value: Mapped[float] = mapped_column(Float, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Sector(code={self.sector_code!r}, "
            f"metric={self.metric_name!r})>"
        )


class Note(Base):
    """Underwriting notes and knowledge artifacts.

    Free-form notes that can be associated with specific signals
    and searched via full-text search (FTS5).
    """

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    signal_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("signals.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    signal: Mapped[Signal | None] = relationship(
        "Signal", back_populates="notes"
    )

    def __repr__(self) -> str:
        return f"<Note(id={self.id}, title={self.title!r})>"


class SignalRun(Base):
    """Per-signal result from a pipeline run for feedback analysis.

    Records the outcome of every signal evaluation during ANALYZE stage
    execution. NO foreign key on signal_id -- dynamic industry signals
    may not exist in the signals table. Uses string + index instead.

    Enables data-driven signal curation: dead signal detection, fire rate
    tracking, skip rate analysis, and anomaly detection across runs.
    """

    __tablename__ = "signal_runs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    run_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False, index=True)
    run_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    signal_id: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False
    )  # TRIGGERED/CLEAR/SKIPPED/INFO
    value: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_quality: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    data_status: Mapped[str] = mapped_column(
        String, nullable=False, default="EVALUATED"
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<SignalRun(run_id={self.run_id!r}, "
            f"signal_id={self.signal_id!r}, status={self.status!r})>"
        )


# Backward-compat alias
CheckRun = SignalRun


class IndustryPlaybook(Base):
    """Industry vertical playbooks for specialized underwriting.

    Each playbook targets a specific industry vertical (e.g.,
    Technology/SaaS, Biotech/Pharma) and provides signal overrides,
    scoring adjustments, and industry-specific risk patterns.
    """

    __tablename__ = "industry_playbooks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    sic_ranges: Mapped[Any] = mapped_column(JSON, nullable=False)
    naics_prefixes: Mapped[Any] = mapped_column(JSON, nullable=False)
    check_overrides: Mapped[Any] = mapped_column(JSON, nullable=True)
    scoring_adjustments: Mapped[Any] = mapped_column(JSON, nullable=True)
    risk_patterns: Mapped[Any] = mapped_column(JSON, nullable=True)
    claim_theories: Mapped[Any] = mapped_column(JSON, nullable=True)
    meeting_questions: Mapped[Any] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="ACTIVE"
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    modified_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return f"<IndustryPlaybook(id={self.id!r}, name={self.name!r})>"
