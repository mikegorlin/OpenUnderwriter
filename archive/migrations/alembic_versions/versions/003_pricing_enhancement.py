"""Enhanced pricing schema: programs, policy years, brokers, carriers.

Creates brokers, carriers, programs, and policy_years tables with
FK relationships, adds new columns to tower_layers, and migrates
existing quote data into the new program/policy_year structure.

Revision ID: 003
Revises: 002
Create Date: 2026-02-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Column, DateTime, Float, Integer, String

revision: str = "003"
down_revision: str | None = "002"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def _create_brokers_table() -> None:
    """Create the brokers table (no FK dependencies)."""
    op.create_table(
        "brokers",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("brokerage_name", String, nullable=False),
        Column("producer_name", String, nullable=True),
        Column("email", String, nullable=True),
        Column("phone", String, nullable=True),
        Column("notes_text", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )


def _create_carriers_table() -> None:
    """Create the carriers table (no FK dependencies)."""
    op.create_table(
        "carriers",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("carrier_name", String, nullable=False),
        Column("am_best_rating", String, nullable=True),
        Column("appetite_notes", String, nullable=True),
        Column("notes_text", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )


def _create_programs_table() -> None:
    """Create the programs table (FK to brokers)."""
    op.create_table(
        "programs",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("ticker", String, nullable=False),
        Column("company_name", String, nullable=True),
        Column("anniversary_month", Integer, nullable=True),
        Column("anniversary_day", Integer, nullable=True),
        Column("broker_id", Integer, nullable=True),
        Column("notes_text", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("updated_at", DateTime, nullable=False),
    )
    with op.batch_alter_table("programs") as batch_op:
        batch_op.create_foreign_key(
            "fk_programs_broker_id",
            "brokers",
            ["broker_id"],
            ["id"],
        )


def _create_policy_years_table() -> None:
    """Create the policy_years table (FK to programs)."""
    op.create_table(
        "policy_years",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("program_id", Integer, nullable=False),
        Column("policy_year", Integer, nullable=False),
        Column("effective_date", DateTime, nullable=True),
        Column("expiration_date", DateTime, nullable=True),
        Column("total_limit", Float(), nullable=True),
        Column("total_premium", Float(), nullable=True),
        Column("retention", Float(), nullable=True),
        Column(
            "status", String, nullable=False, server_default="QUOTED"
        ),
        Column(
            "data_completeness",
            String,
            nullable=False,
            server_default="FRAGMENT",
        ),
        Column(
            "source", String, nullable=False, server_default="manual"
        ),
        Column("source_document", String, nullable=True),
        Column("program_rate_on_line", Float(), nullable=True),
        Column("notes_text", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )
    with op.batch_alter_table("policy_years") as batch_op:
        batch_op.create_foreign_key(
            "fk_policy_years_program_id",
            "programs",
            ["program_id"],
            ["id"],
        )


def _modify_tower_layers() -> None:
    """Add new columns to tower_layers via batch_alter_table."""
    with op.batch_alter_table("tower_layers") as batch_op:
        batch_op.add_column(
            Column("layer_type", String, nullable=True)
        )
        batch_op.add_column(
            Column("layer_label", String, nullable=True)
        )
        batch_op.add_column(
            Column("commission_pct", Float(), nullable=True)
        )
        batch_op.add_column(
            Column("data_source", String, nullable=True)
        )
        batch_op.add_column(
            Column("carrier_id", Integer, nullable=True)
        )
        batch_op.add_column(
            Column("policy_year_id", Integer, nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_tower_layers_carrier_id",
            "carriers",
            ["carrier_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_tower_layers_policy_year_id",
            "policy_years",
            ["policy_year_id"],
            ["id"],
        )


def _create_indexes() -> None:
    """Create indexes for common query patterns."""
    op.create_index(
        "ix_programs_ticker", "programs", ["ticker"]
    )
    op.create_index(
        "ix_policy_years_program_id",
        "policy_years",
        ["program_id"],
    )
    op.create_index(
        "ix_policy_years_policy_year",
        "policy_years",
        ["policy_year"],
    )
    op.create_index(
        "ix_carriers_carrier_name",
        "carriers",
        ["carrier_name"],
    )
    op.create_index(
        "ix_brokers_brokerage_name",
        "brokers",
        ["brokerage_name"],
    )
    op.create_index(
        "ix_tower_layers_policy_year_id",
        "tower_layers",
        ["policy_year_id"],
    )
    op.create_index(
        "ix_tower_layers_carrier_id",
        "tower_layers",
        ["carrier_id"],
    )
    op.create_index(
        "ix_tower_layers_layer_type",
        "tower_layers",
        ["layer_type"],
    )


def _migrate_existing_quotes() -> None:
    """Migrate existing quote data into program/policy_year structure.

    Groups quotes by ticker to create one Program per ticker,
    then creates PolicyYear records from each quote, and links
    existing tower_layers to the new policy_year records.
    """
    bind = op.get_bind()

    # Create one program per unique ticker from existing quotes
    bind.execute(
        sa.text(
            "INSERT INTO programs "
            "(ticker, company_name, created_at, updated_at) "
            "SELECT DISTINCT q.ticker, "
            "  (SELECT q2.company_name FROM quotes q2 "
            "   WHERE q2.ticker = q.ticker "
            "   ORDER BY q2.effective_date DESC LIMIT 1), "
            "  MIN(q.created_at), MIN(q.created_at) "
            "FROM quotes q "
            "GROUP BY q.ticker"
        )
    )

    # Create policy years from existing quotes
    bind.execute(
        sa.text(
            "INSERT INTO policy_years "
            "(program_id, policy_year, effective_date, "
            "expiration_date, total_limit, total_premium, "
            "retention, status, data_completeness, source, "
            "program_rate_on_line, created_at) "
            "SELECT p.id, "
            "  CAST(strftime('%Y', q.effective_date) AS INTEGER), "
            "  q.effective_date, q.expiration_date, "
            "  q.total_limit, q.total_premium, q.retention, "
            "  q.status, 'COMPLETE', q.source, "
            "  q.program_rate_on_line, q.created_at "
            "FROM quotes q "
            "JOIN programs p ON p.ticker = q.ticker"
        )
    )

    # Link tower_layers to the new policy_year records
    bind.execute(
        sa.text(
            "UPDATE tower_layers SET policy_year_id = ("
            "  SELECT py.id FROM policy_years py "
            "  JOIN programs p ON py.program_id = p.id "
            "  JOIN quotes q ON q.ticker = p.ticker "
            "  WHERE tower_layers.quote_id = q.id "
            "  AND py.effective_date = q.effective_date "
            "  LIMIT 1"
            ")"
        )
    )


def upgrade() -> None:
    """Create enhanced pricing tables and migrate existing data."""
    _create_brokers_table()
    _create_carriers_table()
    _create_programs_table()
    _create_policy_years_table()
    _modify_tower_layers()
    _create_indexes()
    _migrate_existing_quotes()


def downgrade() -> None:
    """Drop enhanced pricing tables and remove new columns."""
    # Drop indexes first
    op.drop_index("ix_tower_layers_layer_type", "tower_layers")
    op.drop_index("ix_tower_layers_carrier_id", "tower_layers")
    op.drop_index(
        "ix_tower_layers_policy_year_id", "tower_layers"
    )
    op.drop_index("ix_brokers_brokerage_name", "brokers")
    op.drop_index("ix_carriers_carrier_name", "carriers")
    op.drop_index(
        "ix_policy_years_policy_year", "policy_years"
    )
    op.drop_index(
        "ix_policy_years_program_id", "policy_years"
    )
    op.drop_index("ix_programs_ticker", "programs")

    # Remove new columns from tower_layers
    with op.batch_alter_table("tower_layers") as batch_op:
        batch_op.drop_constraint(
            "fk_tower_layers_policy_year_id", type_="foreignkey"
        )
        batch_op.drop_constraint(
            "fk_tower_layers_carrier_id", type_="foreignkey"
        )
        batch_op.drop_column("policy_year_id")
        batch_op.drop_column("carrier_id")
        batch_op.drop_column("data_source")
        batch_op.drop_column("commission_pct")
        batch_op.drop_column("layer_label")
        batch_op.drop_column("layer_type")

    # Drop tables in reverse FK order
    op.drop_table("policy_years")
    op.drop_table("programs")
    op.drop_table("carriers")
    op.drop_table("brokers")
