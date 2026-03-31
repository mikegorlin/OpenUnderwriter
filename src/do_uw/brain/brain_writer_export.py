"""Brain writer export/changelog functions.

Split from brain_writer.py for file length compliance (<500 lines).
Contains the export_json, get_changelog, and log_change logic used by BrainWriter.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


def _parse_json_col(val: Any) -> Any:
    """Parse a JSON string column, returning None on failure."""
    if val is None:
        return None
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return None


def export_checks_json(
    conn: duckdb.DuckDBPyConnection,
    output_path: Path,
) -> int:
    """Export brain_signals_active to signals.json format.

    Generates a signals.json-compatible file from the current active
    checks in brain.duckdb. This is the backward-compatibility
    export for systems that still read signals.json directly.

    Args:
        conn: Active DuckDB connection.
        output_path: Where to write the JSON file.

    Returns:
        Number of checks exported.
    """
    rows = conn.execute(
        """SELECT signal_id, name, content_type, depth, execution_mode,
                  report_section, factors, required_data, data_locations,
                  threshold_type, threshold_red, threshold_yellow,
                  threshold_clear, pattern_ref, field_key,
                  pillar, category, signal_type, hazard_or_signal,
                  plaintiff_lenses, claims_correlation, amplifier,
                  amplifier_bonus_points, tier, section_number,
                  sector_adjustments, v6_subsection_ids, data_strategy,
                  threshold_full, extraction_hints, rationale
           FROM brain_signals_active
           ORDER BY signal_id"""
    ).fetchall()

    section_map = {
        "company": 1, "market": 2, "financials": 3,
        "governance": 4, "litigation": 5,
        "disclosure": 4, "forward": 1,
    }

    checks = []
    for row in rows:
        # Parse JSON columns
        data_locs = _parse_json_col(row[8]) or {}
        sector_adj = _parse_json_col(row[25])
        data_strat = _parse_json_col(row[27])
        threshold_full = _parse_json_col(row[28])
        extraction_hints = _parse_json_col(row[29])

        # Prefer threshold_full for fidelity, fall back to columns
        if threshold_full:
            threshold = threshold_full
        else:
            threshold: dict[str, Any] = {"type": row[9]}
            if row[10]:
                threshold["red"] = row[10]
            if row[11]:
                threshold["yellow"] = row[11]
            if row[12]:
                threshold["clear"] = row[12]

        check: dict[str, Any] = {
            "id": row[0],
            "name": row[1],
            "content_type": row[2],
            "depth": row[3],
            "execution_mode": row[4],
            "section": row[24] or section_map.get(row[5], 0),
            "factors": row[6] or [],
            "required_data": row[7] or [],
            "data_locations": data_locs,
            "threshold": threshold,
        }
        if row[13]:
            check["pattern_ref"] = row[13]
        if data_strat:
            check["data_strategy"] = data_strat
        elif row[14]:
            check["data_strategy"] = {"field_key": row[14]}
        if row[15]:
            check["pillar"] = row[15]
        if row[16]:
            check["category"] = row[16]
        if row[17]:
            check["signal_type"] = row[17]
        if row[18]:
            check["hazard_or_signal"] = row[18]
        if row[19]:
            check["plaintiff_lenses"] = list(row[19])
        if row[20] is not None:
            check["claims_correlation"] = row[20]
        if row[21]:
            check["amplifier"] = row[21]
        if row[22] is not None:
            check["amplifier_bonus_points"] = row[22]
        if row[23] is not None:
            check["tier"] = row[23]
        if sector_adj:
            check["sector_adjustments"] = sector_adj
        if row[26]:
            check["v6_subsection_ids"] = list(row[26])
        if extraction_hints:
            check["extraction_hints"] = extraction_hints
        if row[30]:
            check["rationale"] = row[30]

        checks.append(check)

    output = {
        "$schema": "BRAIN_CHECKS_EXPORT",
        "version": "exported",
        "description": "Exported from brain.duckdb",
        "total_signals": len(checks),
        "signals": checks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    logger.info("Exported %d signals to %s", len(checks), output_path)
    return len(checks)


def query_changelog(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Return changelog entries, optionally filtered by signal_id.

    Args:
        conn: Active DuckDB connection.
        signal_id: Filter to a single check. None = all.
        limit: Max entries to return.

    Returns:
        List of changelog entry dicts, newest first.
    """
    if signal_id:
        rows = conn.execute(
            """SELECT changelog_id, signal_id, old_version, new_version,
                      change_type, change_description, fields_changed,
                      changed_by, changed_at, change_reason
               FROM brain_changelog
               WHERE signal_id = ?
               ORDER BY changelog_id DESC
               LIMIT ?""",
            [signal_id, limit],
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT changelog_id, signal_id, old_version, new_version,
                      change_type, change_description, fields_changed,
                      changed_by, changed_at, change_reason
               FROM brain_changelog
               ORDER BY changelog_id DESC
               LIMIT ?""",
            [limit],
        ).fetchall()

    return [
        {
            "changelog_id": row[0],
            "signal_id": row[1],
            "old_version": row[2],
            "new_version": row[3],
            "change_type": row[4],
            "change_description": row[5],
            "fields_changed": row[6] or [],
            "changed_by": row[7],
            "changed_at": str(row[8]) if row[8] else None,
            "change_reason": row[9],
        }
        for row in rows
    ]


def log_change(
    conn: duckdb.DuckDBPyConnection,
    signal_id: str,
    old_version: int | None,
    new_version: int,
    change_type: str,
    description: str,
    changed_by: str,
    fields_changed: list[str],
) -> None:
    """Insert a changelog entry."""
    conn.execute(
        """INSERT INTO brain_changelog (
            signal_id, old_version, new_version,
            change_type, change_description, fields_changed,
            changed_by, change_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            signal_id,
            old_version,
            new_version,
            change_type,
            description,
            fields_changed,
            changed_by,
            description,
        ],
    )
