"""Add classification columns to checks table for Phase 26.

Adds four new nullable columns for multi-dimensional check classification:
- category: DECISION_DRIVING, CONTEXT_DISPLAY, or FUTURE_RESEARCH
- plaintiff_lenses_json: JSON array of plaintiff lenses
- signal_type: LEVEL, DELTA, PATTERN, FORENSIC, NLP, STRUCTURAL, EVENT
- hazard_or_signal: HAZARD, SIGNAL, or PERIL_CONFIRMING

Revision ID: 004
Revises: 003
Create Date: 2026-02-12
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    """Add classification columns to checks table."""
    with op.batch_alter_table("signals") as batch_op:
        batch_op.add_column(
            sa.Column("category", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("plaintiff_lenses_json", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("signal_type", sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("hazard_or_signal", sa.String(), nullable=True)
        )


def downgrade() -> None:
    """Remove classification columns from checks table."""
    with op.batch_alter_table("signals") as batch_op:
        batch_op.drop_column("hazard_or_signal")
        batch_op.drop_column("signal_type")
        batch_op.drop_column("plaintiff_lenses_json")
        batch_op.drop_column("category")
