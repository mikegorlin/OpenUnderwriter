"""Pricing and market intelligence tables.

Creates quotes and tower_layers tables with indexes for the
market pricing intelligence subsystem.

Revision ID: 002
Revises: 001
Create Date: 2026-02-09
"""

from __future__ import annotations

from alembic import op
from sqlalchemy import Column, DateTime, Float, Integer, String

revision: str = "002"
down_revision: str | None = "001"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def _create_quotes_table() -> None:
    """Create the quotes table for insurance pricing data."""
    op.create_table(
        "quotes",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("ticker", String, nullable=False),
        Column("company_name", String, nullable=False),
        Column("effective_date", DateTime, nullable=False),
        Column("expiration_date", DateTime, nullable=True),
        Column("quote_date", DateTime, nullable=False),
        Column("status", String, nullable=False, server_default="QUOTED"),
        Column("total_limit", Float(), nullable=False),
        Column("total_premium", Float(), nullable=False),
        Column("retention", Float(), nullable=True),
        Column("market_cap_tier", String, nullable=False),
        Column("sic_code", String, nullable=True),
        Column("sector", String, nullable=True),
        Column("quality_score", Float(), nullable=True),
        Column("tier", String, nullable=True),
        Column("program_rate_on_line", Float(), nullable=False),
        Column("source", String, nullable=False),
        Column("notes_text", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("metadata_json", String, nullable=True),
    )


def _create_tower_layers_table() -> None:
    """Create the tower_layers table for layer-by-layer structure."""
    op.create_table(
        "tower_layers",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("quote_id", Integer, nullable=False),
        Column("layer_position", String, nullable=False),
        Column("layer_number", Integer, nullable=False),
        Column("attachment_point", Float(), nullable=False),
        Column("limit_amount", Float(), nullable=False),
        Column("premium", Float(), nullable=False),
        Column("carrier_name", String, nullable=False),
        Column("carrier_rating", String, nullable=True),
        Column("rate_on_line", Float(), nullable=False),
        Column("premium_per_million", Float(), nullable=False),
        Column("is_lead", Integer, nullable=False, server_default="0"),
        Column("share_pct", Float(), nullable=True),
    )
    # FK via batch_alter_table for SQLite compatibility
    with op.batch_alter_table("tower_layers") as batch_op:
        batch_op.create_foreign_key(
            "fk_tower_layers_quote_id",
            "quotes",
            ["quote_id"],
            ["id"],
        )


def _create_indexes() -> None:
    """Create indexes for common pricing query patterns."""
    op.create_index("ix_quotes_ticker", "quotes", ["ticker"])
    op.create_index(
        "ix_quotes_effective_date", "quotes", ["effective_date"]
    )
    op.create_index(
        "ix_quotes_market_cap_tier", "quotes", ["market_cap_tier"]
    )
    op.create_index("ix_quotes_sector", "quotes", ["sector"])
    op.create_index("ix_quotes_status", "quotes", ["status"])
    op.create_index(
        "ix_tower_layers_quote_id", "tower_layers", ["quote_id"]
    )
    op.create_index(
        "ix_tower_layers_carrier_name",
        "tower_layers",
        ["carrier_name"],
    )


def upgrade() -> None:
    """Create pricing tables and indexes."""
    _create_quotes_table()
    _create_tower_layers_table()
    _create_indexes()


def downgrade() -> None:
    """Drop pricing tables."""
    op.drop_table("tower_layers")
    op.drop_table("quotes")
