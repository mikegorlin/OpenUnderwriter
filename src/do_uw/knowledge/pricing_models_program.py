"""SQLAlchemy ORM models for D&O program and policy year tracking.

Defines the Program, PolicyYear, Broker, and Carrier tables for the
enhanced pricing model hierarchy: Program -> PolicyYear -> TowerLayer,
with Broker and Carrier as separate entities linked via FK.

All models use SQLAlchemy 2.0 declarative style with Mapped[] type
annotations for pyright strict compliance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from do_uw.knowledge.models import Base


class Broker(Base):
    """Insurance broker/brokerage contact record.

    Stores brokerage firm and individual producer details.
    Linked from Program via FK for D&O market contact tracking.
    """

    __tablename__ = "brokers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    brokerage_name: Mapped[str] = mapped_column(String, nullable=False)
    producer_name: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    notes_text: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Broker(id={self.id}, brokerage={self.brokerage_name!r}, "
            f"producer={self.producer_name!r})>"
        )


class Carrier(Base):
    """Insurance carrier record with rating and appetite tracking.

    Separate table so the same carrier can appear on multiple layers
    across multiple programs (ventilated carrier pattern per D1/D5).
    """

    __tablename__ = "carriers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    carrier_name: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    am_best_rating: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    appetite_notes: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    notes_text: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<Carrier(id={self.id}, name={self.carrier_name!r})>"
        )


class Program(Base):
    """D&O insurance program for a company.

    Represents a company's D&O liability insurance program across
    multiple policy years. Minimum viable record is just a ticker
    (per D2 decision); all other fields accumulate over time.

    Hierarchy: Program -> PolicyYear -> TowerLayer
    """

    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    ticker: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    company_name: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    anniversary_month: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    anniversary_day: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    broker_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("brokers.id"), nullable=True
    )
    notes_text: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    policy_years: Mapped[list[PolicyYear]] = relationship(
        "PolicyYear",
        back_populates="program",
        cascade="all, delete-orphan",
    )
    broker: Mapped[Broker | None] = relationship("Broker")

    def __repr__(self) -> str:
        return (
            f"<Program(id={self.id}, ticker={self.ticker!r}, "
            f"anniversary={self.anniversary_month}/{self.anniversary_day})>"
        )


class PolicyYear(Base):
    """Single policy year within a D&O program.

    Groups tower layers and pricing data for one renewal cycle.
    Supports partial data: fields like total_limit, total_premium,
    and retention are all nullable to allow fragment-level records.
    """

    __tablename__ = "policy_years"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    program_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("programs.id"), nullable=False
    )
    policy_year: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True
    )
    effective_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    expiration_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    total_limit: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    total_premium: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    retention: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="QUOTED"
    )
    data_completeness: Mapped[str] = mapped_column(
        String, nullable=False, default="FRAGMENT"
    )
    source: Mapped[str] = mapped_column(
        String, nullable=False, default="manual"
    )
    source_document: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    program_rate_on_line: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    notes_text: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    program: Mapped[Program] = relationship(
        "Program", back_populates="policy_years"
    )
    layers: Mapped[list[Any]] = relationship(
        "TowerLayer",
        back_populates="policy_year",
        viewonly=True,
        foreign_keys="[TowerLayer.policy_year_id]",
    )

    def __repr__(self) -> str:
        return (
            f"<PolicyYear(id={self.id}, program_id={self.program_id}, "
            f"year={self.policy_year})>"
        )
