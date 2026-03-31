"""Initial knowledge store schema.

Creates all core and support tables for the D&O underwriting
knowledge store, plus indexes and FTS5 full-text search.

Revision ID: 001
Revises: None
Create Date: 2026-02-09
"""

from __future__ import annotations

import logging

from alembic import op
from sqlalchemy import Column, DateTime, Float, Integer, String, text
from sqlalchemy.types import JSON

revision: str = "001"
down_revision: str | None = None
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None

logger = logging.getLogger(__name__)


def _create_core_tables() -> None:
    """Create primary knowledge tables with FK relationships."""
    # checks -- primary knowledge table
    op.create_table(
        "signals",
        Column("id", String, primary_key=True),
        Column("name", String, nullable=False),
        Column("section", Integer, nullable=False),
        Column("pillar", String, nullable=False),
        Column("severity", String, nullable=True),
        Column("execution_mode", String, nullable=True),
        Column("status", String, nullable=False, server_default="ACTIVE"),
        Column("threshold_type", String, nullable=True),
        Column("threshold_value", String, nullable=True),
        Column("required_data", JSON, nullable=False),
        Column("data_locations", JSON, nullable=False),
        Column("scoring_factor", String, nullable=True),
        Column("scoring_rule", String, nullable=True),
        Column("output_section", String, nullable=True),
        Column("origin", String, nullable=False),
        Column("created_at", DateTime, nullable=False),
        Column("modified_at", DateTime, nullable=False),
        Column("version", Integer, nullable=False, server_default="1"),
        Column("metadata_json", String, nullable=True),
    )

    # signal_history -- version history for checks
    op.create_table(
        "signal_history",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("signal_id", String, nullable=False),
        Column("version", Integer, nullable=False),
        Column("field_name", String, nullable=False),
        Column("old_value", String, nullable=True),
        Column("new_value", String, nullable=True),
        Column("changed_at", DateTime, nullable=False),
        Column("changed_by", String, nullable=False),
        Column("reason", String, nullable=True),
    )
    # FK added via batch for SQLite compatibility
    with op.batch_alter_table("signal_history") as batch_op:
        batch_op.create_foreign_key(
            "fk_signal_history_signal_id",
            "signals",
            ["signal_id"],
            ["id"],
        )

    # patterns -- composite risk patterns
    op.create_table(
        "patterns",
        Column("id", String, primary_key=True),
        Column("name", String, nullable=False),
        Column("category", String, nullable=False),
        Column("description", String, nullable=True),
        Column("allegation_types", JSON, nullable=False),
        Column("trigger_conditions", JSON, nullable=False),
        Column("score_impact", JSON, nullable=False),
        Column("severity_modifier", String, nullable=True),
        Column("status", String, nullable=False, server_default="ACTIVE"),
        Column("created_at", DateTime, nullable=False),
        Column("modified_at", DateTime, nullable=False),
    )

    # scoring_rules -- factor scoring rules
    op.create_table(
        "scoring_rules",
        Column("id", String, primary_key=True),
        Column("factor_id", String, nullable=False),
        Column("condition", String, nullable=False),
        Column("points", Float(), nullable=False),
        Column("triggers_crf", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )

    # red_flags -- critical red flag gates
    op.create_table(
        "red_flags",
        Column("id", String, primary_key=True),
        Column("name", String, nullable=False),
        Column("condition", String, nullable=False),
        Column("detection_logic", String, nullable=True),
        Column("max_tier", String, nullable=False),
        Column("max_quality_score", Float(), nullable=False),
        Column("status", String, nullable=False, server_default="ACTIVE"),
        Column("created_at", DateTime, nullable=False),
    )


def _create_support_tables() -> None:
    """Create independent lookup and storage tables."""
    # sectors -- sector baseline values
    op.create_table(
        "sectors",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("sector_code", String, nullable=False),
        Column("metric_name", String, nullable=False),
        Column("baseline_value", Float(), nullable=False),
        Column("metadata_json", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
    )

    # notes -- underwriting notes and knowledge
    op.create_table(
        "notes",
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("title", String, nullable=False),
        Column("content", String, nullable=False),
        Column("tags", String, nullable=True),
        Column("source", String, nullable=True),
        Column("signal_id", String, nullable=True),
        Column("created_at", DateTime, nullable=False),
        Column("modified_at", DateTime, nullable=False),
    )
    with op.batch_alter_table("notes") as batch_op:
        batch_op.create_foreign_key(
            "fk_notes_signal_id",
            "signals",
            ["signal_id"],
            ["id"],
        )

    # industry_playbooks -- industry vertical playbooks
    op.create_table(
        "industry_playbooks",
        Column("id", String, primary_key=True),
        Column("name", String, nullable=False),
        Column("description", String, nullable=True),
        Column("sic_ranges", JSON, nullable=False),
        Column("naics_prefixes", JSON, nullable=False),
        Column("check_overrides", JSON, nullable=True),
        Column("scoring_adjustments", JSON, nullable=True),
        Column("risk_patterns", JSON, nullable=True),
        Column("claim_theories", JSON, nullable=True),
        Column("meeting_questions", JSON, nullable=True),
        Column("status", String, nullable=False, server_default="ACTIVE"),
        Column("created_at", DateTime, nullable=False),
        Column("modified_at", DateTime, nullable=False),
    )


def _create_indexes() -> None:
    """Create indexes for common query patterns."""
    op.create_index("ix_checks_status", "signals", ["status"])
    op.create_index("ix_checks_section", "signals", ["section"])
    op.create_index(
        "ix_checks_scoring_factor", "signals", ["scoring_factor"]
    )
    op.create_index("ix_patterns_category", "patterns", ["category"])
    op.create_index(
        "ix_sectors_code_metric",
        "sectors",
        ["sector_code", "metric_name"],
    )
    op.create_index("ix_notes_signal_id", "notes", ["signal_id"])
    op.create_index(
        "ix_signal_history_signal_id", "signal_history", ["signal_id"]
    )


def _fts5_available() -> bool:
    """Check if FTS5 extension is available in the SQLite build."""
    bind = op.get_bind()
    try:
        result = bind.execute(text("PRAGMA compile_options"))
        options = [row[0] for row in result]
        return "ENABLE_FTS5" in options
    except Exception:
        return False


def _create_fts5() -> None:
    """Create FTS5 virtual table for notes full-text search.

    Includes triggers to keep the FTS index synchronized with
    the notes table on INSERT, UPDATE, and DELETE operations.
    Degrades gracefully if FTS5 is not available.
    """
    if not _fts5_available():
        logger.warning(
            "FTS5 not available in SQLite build. "
            "Skipping full-text search index for notes."
        )
        return

    bind = op.get_bind()

    # Create FTS5 virtual table
    bind.execute(
        text(
            "CREATE VIRTUAL TABLE notes_fts USING fts5("
            "title, content, tags, "
            "content='notes', content_rowid='id'"
            ")"
        )
    )

    # Trigger: keep FTS in sync on INSERT
    bind.execute(
        text(
            "CREATE TRIGGER notes_ai AFTER INSERT ON notes BEGIN "
            "INSERT INTO notes_fts(rowid, title, content, tags) "
            "VALUES (new.id, new.title, new.content, new.tags); "
            "END"
        )
    )

    # Trigger: keep FTS in sync on DELETE
    bind.execute(
        text(
            "CREATE TRIGGER notes_ad AFTER DELETE ON notes BEGIN "
            "INSERT INTO notes_fts(notes_fts, rowid, title, content, tags) "
            "VALUES ('delete', old.id, old.title, old.content, old.tags); "
            "END"
        )
    )

    # Trigger: keep FTS in sync on UPDATE
    bind.execute(
        text(
            "CREATE TRIGGER notes_au AFTER UPDATE ON notes BEGIN "
            "INSERT INTO notes_fts(notes_fts, rowid, title, content, tags) "
            "VALUES ('delete', old.id, old.title, old.content, old.tags); "
            "INSERT INTO notes_fts(rowid, title, content, tags) "
            "VALUES (new.id, new.title, new.content, new.tags); "
            "END"
        )
    )

    logger.info("FTS5 full-text search index created for notes.")


def upgrade() -> None:
    """Create all knowledge store tables, indexes, and FTS."""
    _create_core_tables()
    _create_support_tables()
    _create_indexes()
    _create_fts5()


def downgrade() -> None:
    """Drop all knowledge store tables."""
    bind = op.get_bind()

    # Drop FTS triggers and virtual table if they exist
    for trigger in ["notes_ai", "notes_ad", "notes_au"]:
        bind.execute(text(f"DROP TRIGGER IF EXISTS {trigger}"))
    bind.execute(text("DROP TABLE IF EXISTS notes_fts"))

    # Drop tables in reverse dependency order
    op.drop_table("industry_playbooks")
    op.drop_table("notes")
    op.drop_table("sectors")
    op.drop_table("red_flags")
    op.drop_table("scoring_rules")
    op.drop_table("patterns")
    op.drop_table("signal_history")
    op.drop_table("signals")
