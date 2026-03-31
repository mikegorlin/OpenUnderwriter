"""Brain migration: scoring.json, patterns.json, red_flags.json, sectors.json -> brain.duckdb.

Phase 41 Wave 2: Populates brain_scoring_factors, brain_scoring_meta,
brain_patterns, brain_red_flags, brain_sectors tables from JSON files.

Non-destructive: only inserts rows if not already present at version 1.
"""

# DEPRECATED: 2026-02-25
# This file is no longer called by brain build. Knowledge is now loaded from
# src/do_uw/brain/signals/**/*.yaml via brain_migrate_yaml.py and brain_migrate.py.
# Do not delete — kept for reference and emergency rollback only.
# See src/do_uw/brain/SCHEMA.md for the current architecture.

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

from do_uw.brain.brain_schema import connect_brain_db, create_schema

logger = logging.getLogger(__name__)
_BRAIN_DIR = Path(__file__).parent.parent


def migrate_scoring(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, int]:
    """Migrate scoring.json into brain_scoring_factors + brain_scoring_meta.

    Returns:
        Dict with counts: factors, meta_keys.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()
    create_schema(conn)

    scoring_path = _BRAIN_DIR / "config" / "scoring.json"
    with open(scoring_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    # --- Scoring factors (10 factors) ---
    factors_data = data.get("factors", {})
    factor_count = 0
    for _key, factor in factors_data.items():
        fid = factor["factor_id"]
        existing = conn.execute(
            "SELECT COUNT(*) FROM brain_scoring_factors WHERE factor_id = ? AND version = 1",
            [fid],
        ).fetchone()[0]
        if existing > 0:
            continue
        conn.execute(
            """INSERT INTO brain_scoring_factors (
                factor_id, version, name, max_points, weight_pct,
                description, confidence, historical_lift, rules, modifiers
            ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                fid,
                factor["name"],
                factor["max_points"],
                factor["weight_pct"],
                factor.get("description"),
                factor.get("confidence"),
                factor.get("historical_lift"),
                json.dumps(factor.get("rules", [])),
                json.dumps(factor.get("modifiers")) if factor.get("modifiers") else None,
            ],
        )
        factor_count += 1

    # --- Scoring meta (tiers, total_points, formula, etc.) ---
    meta_keys = [
        ("tiers", data.get("tiers")),
        ("total_points", data.get("total_points")),
        ("scoring_formula", data.get("scoring_formula")),
        ("market_cap_multipliers", data.get("market_cap_multipliers")),
        ("severity_ranges", data.get("severity_ranges")),
        ("crf_ceilings", data.get("crf_ceilings")),
    ]
    meta_count = 0
    for key, value in meta_keys:
        if value is None:
            continue
        existing = conn.execute(
            "SELECT COUNT(*) FROM brain_scoring_meta WHERE meta_key = ? AND version = 1",
            [key],
        ).fetchone()[0]
        if existing > 0:
            continue
        conn.execute(
            """INSERT INTO brain_scoring_meta (meta_key, version, meta_json, description)
            VALUES (?, 1, ?, ?)""",
            [key, json.dumps(value), f"From scoring.json: {key}"],
        )
        meta_count += 1

    if own_conn:
        conn.close()

    logger.info("Migrated %d scoring factors, %d meta keys", factor_count, meta_count)
    return {"factors": factor_count, "meta_keys": meta_count}


def migrate_patterns(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> int:
    """Migrate patterns.json into brain_patterns.

    Returns:
        Number of patterns migrated.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()
    create_schema(conn)

    patterns_path = _BRAIN_DIR / "config" / "patterns.json"
    with open(patterns_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    patterns = data.get("patterns", [])
    count = 0
    for p in patterns:
        pid = p["id"]
        existing = conn.execute(
            "SELECT COUNT(*) FROM brain_patterns WHERE pattern_id = ? AND version = 1",
            [pid],
        ).fetchone()[0]
        if existing > 0:
            continue

        # Collect component signals from trigger conditions
        component_signals: list[str] = []
        for tc in p.get("trigger_conditions", []):
            if "signal_id" in tc:
                component_signals.append(tc["signal_id"])

        conn.execute(
            """INSERT INTO brain_patterns (
                pattern_id, version, name, category, description,
                trigger_conditions, severity_modifiers, score_impact,
                component_signals, allegation_types
            ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                pid,
                p["name"],
                p.get("category", ""),
                p.get("description"),
                json.dumps(p.get("trigger_conditions", [])),
                json.dumps(p.get("severity_modifiers")) if p.get("severity_modifiers") else None,
                json.dumps(p.get("score_impact", {})),
                component_signals or None,
                p.get("allegation_types", []),
            ],
        )
        count += 1

    if own_conn:
        conn.close()

    logger.info("Migrated %d patterns", count)
    return count


def migrate_red_flags(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> int:
    """Migrate red_flags.json into brain_red_flags.

    Returns:
        Number of red flags migrated.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()
    create_schema(conn)

    rf_path = _BRAIN_DIR / "config" / "red_flags.json"
    with open(rf_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    triggers = data.get("escalation_triggers", [])
    count = 0
    for trigger in triggers:
        fid = trigger["id"]
        existing = conn.execute(
            "SELECT COUNT(*) FROM brain_red_flags WHERE flag_id = ? AND version = 1",
            [fid],
        ).fetchone()[0]
        if existing > 0:
            continue

        # Capture extra fields not in the core schema
        extra_fields = {}
        for k in ("legacy_id", "new_business_context", "side_a_note",
                   "notable_sources", "attribution_requirement", "urgency",
                   "detection_logic"):
            if k in trigger:
                extra_fields[k] = trigger[k]

        conn.execute(
            """INSERT INTO brain_red_flags (
                flag_id, version, name, condition, max_tier,
                max_quality_score, source_signal, action, auto_decline, extra
            ) VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                fid,
                trigger["name"],
                trigger["condition"],
                trigger["max_tier"],
                trigger["max_quality_score"],
                trigger.get("source_signal"),
                trigger.get("action"),
                trigger.get("auto_decline", False),
                json.dumps(extra_fields) if extra_fields else None,
            ],
        )
        count += 1

    # Also store processing_rules, renewal_context, binding_decision_protocol as meta
    for meta_key in ("processing_rules", "renewal_context", "binding_decision_protocol"):
        if meta_key in data:
            existing = conn.execute(
                "SELECT COUNT(*) FROM brain_scoring_meta WHERE meta_key = ? AND version = 1",
                [f"red_flags_{meta_key}"],
            ).fetchone()[0]
            if existing == 0:
                conn.execute(
                    """INSERT INTO brain_scoring_meta (meta_key, version, meta_json, description)
                    VALUES (?, 1, ?, ?)""",
                    [f"red_flags_{meta_key}", json.dumps(data[meta_key]),
                     f"From red_flags.json: {meta_key}"],
                )

    if own_conn:
        conn.close()

    logger.info("Migrated %d red flags", count)
    return count


def migrate_sectors(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> int:
    """Migrate sectors.json into brain_sectors.

    Returns:
        Number of sector metric/code rows migrated.
    """
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()
    create_schema(conn)

    sectors_path = _BRAIN_DIR / "config" / "sectors.json"
    with open(sectors_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)

    count = 0
    skip_keys = {"version", "last_updated", "source", "description"}
    for metric_name, metric_data in data.items():
        if metric_name in skip_keys:
            continue
        if not isinstance(metric_data, dict):
            continue

        # Each metric has sector_code -> data entries, plus metadata keys
        meta_keys = {"description", "source", "calculation", "note", "thresholds"}
        for sector_code, sector_data in metric_data.items():
            if sector_code in meta_keys:
                continue
            existing = conn.execute(
                "SELECT COUNT(*) FROM brain_sectors "
                "WHERE metric_name = ? AND sector_code = ? AND version = 1",
                [metric_name, sector_code],
            ).fetchone()[0]
            if existing > 0:
                continue
            conn.execute(
                """INSERT INTO brain_sectors (metric_name, sector_code, version, data)
                VALUES (?, ?, 1, ?)""",
                [metric_name, sector_code, json.dumps(sector_data)],
            )
            count += 1

    if own_conn:
        conn.close()

    logger.info("Migrated %d sector rows", count)
    return count


def migrate_all_scoring(
    conn: duckdb.DuckDBPyConnection | None = None,
) -> dict[str, Any]:
    """Run all Wave 2 migrations: scoring, patterns, red flags, sectors."""
    own_conn = conn is None
    if conn is None:
        conn = connect_brain_db()

    scoring = migrate_scoring(conn)
    patterns = migrate_patterns(conn)
    red_flags = migrate_red_flags(conn)
    sectors = migrate_sectors(conn)

    if own_conn:
        conn.close()

    return {
        "scoring_factors": scoring["factors"],
        "scoring_meta": scoring["meta_keys"],
        "patterns": patterns,
        "red_flags": red_flags,
        "sectors": sectors,
    }
