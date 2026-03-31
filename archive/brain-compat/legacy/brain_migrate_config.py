"""Brain migration: config/ JSON files + knowledge.db check_runs -> brain.duckdb.

Phase 41 Wave 3:
- Imports 22 config/ JSON files into brain_config KV table.
- Migrates 353K+ check_runs from knowledge.db (SQLite) to brain_signal_runs.

Non-destructive: only inserts rows if not already present.
"""

# DEPRECATED: 2026-02-25
# This file is no longer called by brain build. Knowledge is now loaded from
# src/do_uw/brain/signals/**/*.yaml via brain_migrate_yaml.py and brain_migrate.py.
# Do not delete — kept for reference and emergency rollback only.
# See src/do_uw/brain/SCHEMA.md for the current architecture.

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

import duckdb

from do_uw.brain.brain_schema import connect_brain_db, create_schema

logger = logging.getLogger(__name__)
_CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
_KNOWLEDGE_DB = Path(__file__).parent.parent.parent / "knowledge" / "knowledge.db"

# All 22 config files to import
_CONFIG_FILES: list[tuple[str, str]] = [
    ("actuarial", "actuarial.json"),
    ("executive_scoring", "executive_scoring.json"),
    ("governance_weights", "governance_weights.json"),
    ("hazard_weights", "hazard_weights.json"),
    ("hazard_interactions", "hazard_interactions.json"),
    ("claim_types", "claim_types.json"),
    ("classification", "classification.json"),
    ("ai_risk_weights", "ai_risk_weights.json"),
    ("adverse_events", "adverse_events.json"),
    ("activist_investors", "activist_investors.json"),
    ("forensic_models", "forensic_models.json"),
    ("industry_theories", "industry_theories.json"),
    ("lead_counsel_tiers", "lead_counsel_tiers.json"),
    ("plaintiff_firms", "plaintiff_firms.json"),
    ("rate_decay", "rate_decay.json"),
    ("render_thresholds", "render_thresholds.json"),
    ("settlement_calibration", "settlement_calibration.json"),
    ("sic_gics_mapping", "sic_gics_mapping.json"),
    ("tax_havens", "tax_havens.json"),
    ("temporal_thresholds", "temporal_thresholds.json"),
    ("xbrl_concepts", "xbrl_concepts.json"),
    ("signal_classification", "signal_classification.json"),
]


def _file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def migrate_configs(
    conn: duckdb.DuckDBPyConnection | None = None,
    config_dir: Path | None = None,
) -> int:
    """Import all config/ JSON files into brain_config.

    Non-destructive: checks file_hash against existing entries.
    Only inserts a new version if the file content has changed.

    Returns:
        Number of config entries imported.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()
    create_schema(conn)

    if config_dir is None:
        config_dir = _CONFIG_DIR

    count = 0
    for config_key, filename in _CONFIG_FILES:
        path = config_dir / filename
        if not path.exists():
            logger.warning("Config file not found: %s", path)
            continue

        content_hash = _file_hash(path)

        # Check if we already have this exact version
        existing = conn.execute(
            "SELECT file_hash FROM brain_config_current WHERE config_key = ?",
            [config_key],
        ).fetchone()

        if existing and existing[0] == content_hash:
            continue  # No change

        # Determine next version
        max_ver = conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM brain_config WHERE config_key = ?",
            [config_key],
        ).fetchone()[0]
        next_ver = max_ver + 1

        with open(path, encoding="utf-8") as f:
            config_json = json.load(f)

        conn.execute(
            """INSERT INTO brain_config (config_key, version, config_json,
                source_file, file_hash)
            VALUES (?, ?, ?, ?, ?)""",
            [config_key, next_ver, json.dumps(config_json),
             f"config/{filename}", content_hash],
        )
        count += 1

    if own_conn:
        conn.close()

    logger.info("Imported %d config entries", count)
    return count


def migrate_check_runs(
    conn: duckdb.DuckDBPyConnection | None = None,
    knowledge_db_path: Path | None = None,
    batch_size: int = 10000,
) -> int:
    """Migrate check_runs from knowledge.db (SQLite) to brain_signal_runs.

    Reads in batches of batch_size to handle 353K+ rows efficiently.
    Non-destructive: skips rows where (run_id, signal_id) already exists.

    Returns:
        Number of rows migrated.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()
    create_schema(conn)

    if knowledge_db_path is None:
        knowledge_db_path = _KNOWLEDGE_DB

    if not knowledge_db_path.exists():
        logger.warning("knowledge.db not found at %s", knowledge_db_path)
        return 0

    sqlite_conn = sqlite3.connect(str(knowledge_db_path))
    cursor = sqlite_conn.cursor()

    # Check if check_runs table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='check_runs'"
    )
    if not cursor.fetchone():
        logger.warning("check_runs table not found in knowledge.db")
        sqlite_conn.close()
        return 0

    # Count total rows for progress
    total = cursor.execute("SELECT COUNT(*) FROM check_runs").fetchone()[0]
    logger.info("Migrating %d check_runs from knowledge.db", total)

    # Check existing count to skip if already migrated
    existing = conn.execute(
        "SELECT COUNT(*) FROM brain_signal_runs"
    ).fetchone()[0]
    if existing >= total:
        logger.info("brain_signal_runs already has %d rows (>= %d), skipping", existing, total)
        sqlite_conn.close()
        if own_conn:
            conn.close()
        return 0

    migrated = 0
    offset = 0
    while offset < total:
        rows = cursor.execute(
            "SELECT run_id, signal_id, status, value, ticker, run_date "
            "FROM check_runs ORDER BY id LIMIT ? OFFSET ?",
            (batch_size, offset),
        ).fetchall()

        if not rows:
            break

        values: list[tuple[Any, ...]] = []
        for run_id, signal_id, status, value, ticker, run_date in rows:
            values.append((
                run_id,
                signal_id,
                1,  # signal_version (default, not tracked in SQLite)
                status,
                value,
                None,  # evidence
                ticker,
                run_date,
                False,  # is_backtest
            ))

        try:
            conn.executemany(
                """INSERT OR IGNORE INTO brain_signal_runs (
                    run_id, signal_id, signal_version, status, value,
                    evidence, ticker, run_date, is_backtest
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                values,
            )
        except duckdb.ConstraintException:
            # Batch had duplicates, insert one by one
            for v in values:
                try:
                    conn.execute(
                        """INSERT INTO brain_signal_runs (
                            run_id, signal_id, signal_version, status, value,
                            evidence, ticker, run_date, is_backtest
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        list(v),
                    )
                    migrated += 1
                except duckdb.ConstraintException:
                    pass  # Skip duplicates
            offset += batch_size
            continue

        migrated += len(values)
        offset += batch_size

        if offset % 50000 == 0:
            logger.info("  migrated %d/%d check_runs", migrated, total)

    sqlite_conn.close()
    if own_conn:
        conn.close()

    logger.info("Migrated %d check_runs total", migrated)
    return migrated


def populate_brain_meta(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> None:
    """Populate brain_meta with current schema version and table stats.

    Non-destructive: upserts meta_key rows.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()
    create_schema(conn)

    # Gather stats
    stats: dict[str, str] = {
        "schema_version": "41.6",
        "signal_count": str(
            conn.execute("SELECT COUNT(*) FROM brain_signals_active").fetchone()[0]
        ),
        "total_signals_all_versions": str(
            conn.execute("SELECT COUNT(*) FROM brain_signals").fetchone()[0]
        ),
        "scoring_factors": str(
            conn.execute("SELECT COUNT(*) FROM brain_scoring_factors").fetchone()[0]
        ),
        "patterns": str(
            conn.execute("SELECT COUNT(*) FROM brain_patterns").fetchone()[0]
        ),
        "red_flags": str(
            conn.execute("SELECT COUNT(*) FROM brain_red_flags").fetchone()[0]
        ),
        "config_entries": str(
            conn.execute("SELECT COUNT(DISTINCT config_key) FROM brain_config").fetchone()[0]
        ),
        "check_runs": str(
            conn.execute("SELECT COUNT(*) FROM brain_signal_runs").fetchone()[0]
        ),
    }

    for key, value in stats.items():
        # DuckDB upsert: delete + insert
        conn.execute("DELETE FROM brain_meta WHERE meta_key = ?", [key])
        conn.execute(
            """INSERT INTO brain_meta (meta_key, meta_value, updated_at)
            VALUES (?, ?, current_timestamp)""",
            [key, value],
        )

    if own_conn:
        conn.close()

    logger.info("Populated brain_meta: %d entries", len(stats))


def migrate_all_config(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, int]:
    """Run all Wave 3 migrations: config files + check_runs + meta."""
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()

    configs = migrate_configs(conn)
    check_runs = migrate_check_runs(conn)
    populate_brain_meta(conn)

    if own_conn:
        conn.close()

    return {"configs": configs, "check_runs": check_runs}
