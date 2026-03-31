"""BrainWriter: write check modifications to brain.duckdb with versioning.

All write operations are append-only (new version rows) with automatic
changelog entries. Nothing is ever deleted — retired checks get
lifecycle_state='RETIRED'.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import duckdb

from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path
from do_uw.brain.brain_writer_export import (
    export_checks_json,
    log_change,
    query_changelog,
)

logger = logging.getLogger(__name__)


class BrainWriter:
    """Programmatic check management with auto-versioning and audit trail.

    All modifications create new version rows and changelog entries.
    The brain_signals_current view always picks the latest version.

    Args:
        db_path: Path to brain.duckdb. None = default location.
    """

    def __init__(self, db_path: Path | str | None = None) -> None:
        self._db_path = db_path or get_brain_db_path()
        self._conn: duckdb.DuckDBPyConnection | None = None

    def _get_conn(self) -> duckdb.DuckDBPyConnection:
        """Lazy-connect to brain.duckdb."""
        if self._conn is not None:
            return self._conn
        self._conn = connect_brain_db(self._db_path)
        return self._conn

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Insert
    # ------------------------------------------------------------------

    def insert_check(
        self,
        signal_id: str,
        signal_data: dict[str, Any],
        reason: str,
        created_by: str = "brain_writer",
    ) -> int:
        """Insert a new check as version 1.

        If signal_data includes lifecycle_state='INCUBATING', the check will
        be invisible to the pipeline (excluded from brain_signals_active view)
        until promoted to ACTIVE via promote_check(). Similarly, INACTIVE
        checks are excluded from the active view.

        Args:
            signal_id: Unique check identifier (e.g., "BIZ.NEW.check").
            signal_data: Dict with check fields (name, content_type, etc.).
                Supports lifecycle_state='INCUBATING' for proposed checks
                that need human approval before entering the pipeline.
            reason: Why this check was created.
            created_by: Who/what created it.

        Returns:
            Version number (always 1 for new checks).

        Raises:
            ValueError: If signal_id already exists.
        """
        conn = self._get_conn()

        # Verify check doesn't already exist
        existing = conn.execute(
            "SELECT COUNT(*) FROM brain_signals WHERE signal_id = ?",
            [signal_id],
        ).fetchone()[0]
        if existing > 0:
            msg = f"Check {signal_id} already exists. Use update_check() instead."
            raise ValueError(msg)

        version = 1
        self._insert_version(conn, signal_id, version, signal_data, created_by, reason)
        self._log_change(
            conn, signal_id, None, version, "CREATED", reason, created_by,
            list(signal_data.keys()),
        )

        logger.info("Inserted check %s v%d: %s", signal_id, version, reason)
        return version

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_check(
        self,
        signal_id: str,
        changes: dict[str, Any],
        reason: str,
        changed_by: str = "brain_writer",
    ) -> int:
        """Update an existing check by creating a new version.

        Reads the current version, merges changes, creates version N+1.

        Args:
            signal_id: Check to update.
            changes: Dict of field -> new_value to merge.
            reason: Why the change was made.
            changed_by: Who/what made the change.

        Returns:
            New version number.

        Raises:
            ValueError: If signal_id doesn't exist.
        """
        conn = self._get_conn()

        # Read current version
        current = self._get_current(conn, signal_id)
        if current is None:
            msg = f"Check {signal_id} not found. Use insert_check() for new checks."
            raise ValueError(msg)

        old_version = current["version"]
        new_version = old_version + 1

        # Merge changes into current data
        merged = dict(current)
        merged.update(changes)

        self._insert_version(
            conn, signal_id, new_version, merged, changed_by, reason,
        )
        self._log_change(
            conn, signal_id, old_version, new_version, "MODIFIED",
            reason, changed_by, list(changes.keys()),
        )

        logger.info(
            "Updated check %s v%d→v%d: %s",
            signal_id, old_version, new_version, reason,
        )
        return new_version

    # ------------------------------------------------------------------
    # Retire
    # ------------------------------------------------------------------

    def retire_check(
        self,
        signal_id: str,
        reason: str,
        retired_by: str = "brain_writer",
    ) -> int:
        """Retire a check (set lifecycle_state=RETIRED).

        Creates a new version with RETIRED state. The check disappears
        from brain_signals_active but remains in brain_signals with
        full history.

        Args:
            signal_id: Check to retire.
            reason: Why it's being retired.
            retired_by: Who/what retired it.

        Returns:
            New version number.

        Raises:
            ValueError: If signal_id doesn't exist or is already retired.
        """
        conn = self._get_conn()

        current = self._get_current(conn, signal_id)
        if current is None:
            msg = f"Check {signal_id} not found."
            raise ValueError(msg)

        if current.get("lifecycle_state") == "RETIRED":
            msg = f"Check {signal_id} is already retired."
            raise ValueError(msg)

        old_version = current["version"]
        new_version = old_version + 1

        merged = dict(current)
        merged["lifecycle_state"] = "RETIRED"

        self._insert_version(
            conn, signal_id, new_version, merged, retired_by, reason,
        )

        # Set retired_at timestamp
        conn.execute(
            """UPDATE brain_signals
               SET retired_at = current_timestamp, retired_reason = ?
               WHERE signal_id = ? AND version = ?""",
            [reason, signal_id, new_version],
        )

        self._log_change(
            conn, signal_id, old_version, new_version, "RETIRED",
            reason, retired_by, ["lifecycle_state"],
        )

        logger.info("Retired check %s v%d: %s", signal_id, new_version, reason)
        return new_version

    # ------------------------------------------------------------------
    # Promote
    # ------------------------------------------------------------------

    def promote_check(
        self,
        signal_id: str,
        new_lifecycle: str,
        reason: str,
        promoted_by: str = "brain_writer",
    ) -> int:
        """Change lifecycle state (e.g., INVESTIGATION -> SCORING).

        Args:
            signal_id: Check to promote.
            new_lifecycle: New lifecycle state.
            reason: Why the promotion.
            promoted_by: Who/what promoted it.

        Returns:
            New version number.

        Raises:
            ValueError: If signal_id doesn't exist.
        """
        return self.update_check(
            signal_id,
            {"lifecycle_state": new_lifecycle},
            reason,
            promoted_by,
        )

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_json(self, output_path: Path) -> int:
        """Export brain_signals_active to signals.json format.

        Delegates to brain_writer_export.export_checks_json().

        Args:
            output_path: Where to write the JSON file.

        Returns:
            Number of checks exported.
        """
        return export_checks_json(self._get_conn(), output_path)

    # ------------------------------------------------------------------
    # Changelog
    # ------------------------------------------------------------------

    def get_changelog(
        self,
        signal_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Return changelog entries, optionally filtered by signal_id.

        Delegates to brain_writer_export.query_changelog().

        Args:
            signal_id: Filter to a single check. None = all.
            limit: Max entries to return.

        Returns:
            List of changelog entry dicts, newest first.
        """
        return query_changelog(self._get_conn(), signal_id=signal_id, limit=limit)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_current(
        self, conn: duckdb.DuckDBPyConnection, signal_id: str,
    ) -> dict[str, Any] | None:
        """Read the current version of a check."""
        row = conn.execute(
            """SELECT signal_id, version, name, content_type, lifecycle_state,
                      depth, execution_mode, report_section, risk_questions,
                      risk_framework_layer, factors, hazards,
                      characteristic_direction, characteristic_strength,
                      threshold_type, threshold_red, threshold_yellow,
                      threshold_clear, pattern_ref, question, rationale,
                      interpretation, field_key, required_data,
                      data_locations, acquisition_type,
                      industry_scope, applicable_industries,
                      industry_threshold_overrides, expected_fire_rate,
                      last_calibrated, calibration_notes,
                      pillar, category, signal_type, hazard_or_signal,
                      plaintiff_lenses, claims_correlation, amplifier,
                      amplifier_bonus_points, tier, section_number,
                      sector_adjustments, v6_subsection_ids, data_strategy,
                      threshold_full
               FROM brain_signals_current
               WHERE signal_id = ?""",
            [signal_id],
        ).fetchone()

        if row is None:
            return None

        return {
            "signal_id": row[0],
            "version": row[1],
            "name": row[2],
            "content_type": row[3],
            "lifecycle_state": row[4],
            "depth": row[5],
            "execution_mode": row[6],
            "report_section": row[7],
            "risk_questions": row[8] or [],
            "risk_framework_layer": row[9],
            "factors": row[10] or [],
            "hazards": row[11] or [],
            "characteristic_direction": row[12],
            "characteristic_strength": row[13],
            "threshold_type": row[14],
            "threshold_red": row[15],
            "threshold_yellow": row[16],
            "threshold_clear": row[17],
            "pattern_ref": row[18],
            "question": row[19],
            "rationale": row[20],
            "interpretation": row[21],
            "field_key": row[22],
            "required_data": row[23] or [],
            "data_locations": row[24],
            "acquisition_type": row[25],
            "industry_scope": row[26],
            "applicable_industries": row[27] or [],
            "industry_threshold_overrides": row[28],
            "expected_fire_rate": row[29],
            "last_calibrated": row[30],
            "calibration_notes": row[31],
            "pillar": row[32],
            "category": row[33],
            "signal_type": row[34],
            "hazard_or_signal": row[35],
            "plaintiff_lenses": row[36] or [],
            "claims_correlation": row[37],
            "amplifier": row[38],
            "amplifier_bonus_points": row[39],
            "tier": row[40],
            "section_number": row[41],
            "sector_adjustments": row[42],
            "v6_subsection_ids": row[43] or [],
            "data_strategy": row[44],
            "threshold_full": row[45],
        }

    @staticmethod
    def _insert_version(
        conn: duckdb.DuckDBPyConnection,
        signal_id: str,
        version: int,
        data: dict[str, Any],
        created_by: str,
        change_description: str,
    ) -> None:
        """Insert a single check version row."""
        # Handle JSON-serializable fields — may be dict or JSON string
        data_locs = data.get("data_locations")
        if isinstance(data_locs, dict):
            data_locs = json.dumps(data_locs)
        sector_adj = data.get("sector_adjustments")
        if isinstance(sector_adj, dict):
            sector_adj = json.dumps(sector_adj)
        data_strat = data.get("data_strategy")
        if isinstance(data_strat, dict):
            data_strat = json.dumps(data_strat)
        threshold_full = data.get("threshold_full")
        if isinstance(threshold_full, dict):
            threshold_full = json.dumps(threshold_full)

        conn.execute(
            """INSERT INTO brain_signals (
                signal_id, version, name, content_type, lifecycle_state,
                depth, execution_mode, report_section, risk_questions,
                risk_framework_layer, factors, hazards,
                characteristic_direction, characteristic_strength,
                threshold_type, threshold_red, threshold_yellow,
                threshold_clear, pattern_ref, question, rationale,
                interpretation, field_key, required_data,
                data_locations, acquisition_type,
                industry_scope, applicable_industries,
                industry_threshold_overrides, expected_fire_rate,
                last_calibrated, calibration_notes,
                pillar, category, signal_type, hazard_or_signal,
                plaintiff_lenses, claims_correlation, amplifier,
                amplifier_bonus_points, tier, section_number,
                sector_adjustments, v6_subsection_ids, data_strategy,
                threshold_full,
                created_by, change_description
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )""",
            [
                signal_id,
                version,
                data.get("name", ""),
                data.get("content_type", "EVALUATIVE_CHECK"),
                data.get("lifecycle_state", "INVESTIGATION"),
                data.get("depth", 2),
                data.get("execution_mode", "AUTO"),
                data.get("report_section", "company"),
                data.get("risk_questions", []),
                data.get("risk_framework_layer", "risk_modifier"),
                data.get("factors", []),
                data.get("hazards", []),
                data.get("characteristic_direction"),
                data.get("characteristic_strength"),
                data.get("threshold_type", "tiered"),
                data.get("threshold_red"),
                data.get("threshold_yellow"),
                data.get("threshold_clear"),
                data.get("pattern_ref"),
                data.get("question", data.get("name", "")),
                data.get("rationale"),
                data.get("interpretation"),
                data.get("field_key"),
                data.get("required_data", []),
                data_locs,
                data.get("acquisition_type", "structured"),
                data.get("industry_scope", "universal"),
                data.get("applicable_industries"),
                data.get("industry_threshold_overrides"),
                data.get("expected_fire_rate"),
                data.get("last_calibrated"),
                data.get("calibration_notes"),
                data.get("pillar"),
                data.get("category"),
                data.get("signal_type"),
                data.get("hazard_or_signal"),
                data.get("plaintiff_lenses", []),
                data.get("claims_correlation"),
                data.get("amplifier"),
                data.get("amplifier_bonus_points"),
                data.get("tier"),
                data.get("section_number"),
                sector_adj,
                data.get("v6_subsection_ids", []),
                data_strat,
                threshold_full,
                created_by,
                change_description,
            ],
        )

    @staticmethod
    def _log_change(
        conn: duckdb.DuckDBPyConnection,
        signal_id: str,
        old_version: int | None,
        new_version: int,
        change_type: str,
        description: str,
        changed_by: str,
        fields_changed: list[str],
    ) -> None:
        """Insert a changelog entry (delegates to brain_writer_export)."""
        log_change(
            conn, signal_id, old_version, new_version,
            change_type, description, changed_by, fields_changed,
        )
