"""Add knowledge model enrichment columns to checks table.

Adds content_type, depth, rationale, field_key, extraction_path, and
pattern_ref columns for the enriched check schema. All columns are
nullable for backward compatibility with existing data.

Revision ID: 006
Revises: 005
Create Date: 2026-02-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    """Add enrichment columns to checks table."""
    op.add_column(
        "signals", sa.Column("content_type", sa.String, nullable=True)
    )
    op.add_column(
        "signals", sa.Column("depth", sa.Integer, nullable=True)
    )
    op.add_column(
        "signals", sa.Column("rationale", sa.String, nullable=True)
    )
    op.add_column(
        "signals", sa.Column("field_key", sa.String, nullable=True)
    )
    op.add_column(
        "signals", sa.Column("extraction_path", sa.String, nullable=True)
    )
    op.add_column(
        "signals", sa.Column("pattern_ref", sa.String, nullable=True)
    )


def downgrade() -> None:
    """Drop enrichment columns from checks table."""
    op.drop_column("signals", "pattern_ref")
    op.drop_column("signals", "extraction_path")
    op.drop_column("signals", "field_key")
    op.drop_column("signals", "rationale")
    op.drop_column("signals", "depth")
    op.drop_column("signals", "content_type")
