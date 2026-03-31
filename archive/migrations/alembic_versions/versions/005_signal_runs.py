"""Add signal_runs table for per-signal feedback loop.

Records per-signal results from each ANALYZE stage execution for
fire rate tracking, dead signal detection, and anomaly analysis.

Revision ID: 005
Revises: 004
Create Date: 2026-02-15
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    """Create signal_runs table with indices."""
    op.create_table(
        "signal_runs",
        sa.Column(
            "id", sa.Integer, primary_key=True, autoincrement=True
        ),
        sa.Column("run_id", sa.String, nullable=False),
        sa.Column("ticker", sa.String, nullable=False),
        sa.Column("run_date", sa.DateTime, nullable=False),
        sa.Column("signal_id", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("value", sa.String, nullable=True),
        sa.Column("evidence_quality", sa.String, nullable=True),
        sa.Column(
            "data_status",
            sa.String,
            nullable=False,
            server_default="EVALUATED",
        ),
        sa.Column("duration_ms", sa.Integer, nullable=True),
    )
    op.create_index("ix_signal_runs_run_id", "signal_runs", ["run_id"])
    op.create_index("ix_signal_runs_ticker", "signal_runs", ["ticker"])
    op.create_index("ix_signal_runs_signal_id", "signal_runs", ["signal_id"])


def downgrade() -> None:
    """Drop signal_runs table."""
    op.drop_index("ix_signal_runs_signal_id", table_name="signal_runs")
    op.drop_index("ix_signal_runs_ticker", table_name="signal_runs")
    op.drop_index("ix_signal_runs_run_id", table_name="signal_runs")
    op.drop_table("signal_runs")
