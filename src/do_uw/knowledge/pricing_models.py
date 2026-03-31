"""SQLAlchemy ORM models for D&O pricing and market intelligence.

Defines the Quote and TowerLayer tables for storing historical
pricing data, tower structures, and rate-on-line metrics.

All models use SQLAlchemy 2.0 declarative style with Mapped[] type
annotations for pyright strict compliance.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

import do_uw.knowledge.pricing_models_program as _program_models  # noqa: F401  # pyright: ignore[reportUnusedImport]
from do_uw.knowledge.models import Base


class Quote(Base):
    """Insurance quote record with pricing and classification data.

    Stores per-program pricing: total limit, premium, retention,
    rate-on-line, market cap tier, and quality score snapshot.
    Linked to tower layers for detailed structure analysis.
    """

    __tablename__ = "quotes"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    ticker: Mapped[str] = mapped_column(String, nullable=False, index=True)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    effective_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    expiration_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    quote_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(
        String, nullable=False, default="QUOTED", index=True
    )
    total_limit: Mapped[float] = mapped_column(Float(), nullable=False)
    total_premium: Mapped[float] = mapped_column(Float(), nullable=False)
    retention: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    market_cap_tier: Mapped[str] = mapped_column(
        String, nullable=False, index=True
    )
    sic_code: Mapped[str | None] = mapped_column(String, nullable=True)
    sector: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    quality_score: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    tier: Mapped[str | None] = mapped_column(String, nullable=True)
    program_rate_on_line: Mapped[float] = mapped_column(
        Float(), nullable=False
    )
    source: Mapped[str] = mapped_column(String, nullable=False)
    notes_text: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metadata_json: Mapped[str | None] = mapped_column(
        String, nullable=True
    )

    layers: Mapped[list[TowerLayer]] = relationship(
        "TowerLayer",
        back_populates="quote",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Quote(id={self.id}, ticker={self.ticker!r}, "
            f"status={self.status!r}, premium={self.total_premium})>"
        )


class TowerLayer(Base):
    """Individual layer within an insurance tower structure.

    Each layer has an attachment point, limit, premium, and carrier.
    Rate-on-line and premium-per-million are auto-computed on insert.
    """

    __tablename__ = "tower_layers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    quote_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("quotes.id"), nullable=False
    )
    layer_position: Mapped[str] = mapped_column(String, nullable=False)
    layer_number: Mapped[int] = mapped_column(Integer, nullable=False)
    attachment_point: Mapped[float] = mapped_column(
        Float(), nullable=False
    )
    limit_amount: Mapped[float] = mapped_column(Float(), nullable=False)
    premium: Mapped[float] = mapped_column(Float(), nullable=False)
    carrier_name: Mapped[str] = mapped_column(String, nullable=False)
    carrier_rating: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    rate_on_line: Mapped[float] = mapped_column(Float(), nullable=False)
    premium_per_million: Mapped[float] = mapped_column(
        Float(), nullable=False
    )
    is_lead: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=False
    )
    share_pct: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    layer_type: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    layer_label: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    commission_pct: Mapped[float | None] = mapped_column(
        Float(), nullable=True
    )
    data_source: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    carrier_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("carriers.id"), nullable=True
    )
    policy_year_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("policy_years.id"), nullable=True
    )

    quote: Mapped[Quote] = relationship("Quote", back_populates="layers")
    policy_year: Mapped[Any] = relationship(
        "PolicyYear",
        viewonly=True,
        foreign_keys=[policy_year_id],
    )

    def __repr__(self) -> str:
        return (
            f"<TowerLayer(id={self.id}, quote_id={self.quote_id}, "
            f"carrier={self.carrier_name!r}, layer={self.layer_number})>"
        )
