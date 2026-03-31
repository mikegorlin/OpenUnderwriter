"""Tests for knowledge governance CLI commands.

Tests all 5 governance commands: review, promote, history,
drift, and deprecation-log. Uses brain.duckdb file-based
temporary database for isolation.

Phase 45: Commands ported to brain.duckdb. Tests use a
temporary file-based DuckDB seeded with test data.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from do_uw.cli import app

runner = CliRunner()


def _make_tmp_brain_db(
    checks: list[dict[str, Any]] | None = None,
    scoring_factors: list[dict[str, Any]] | None = None,
    changelog_entries: list[dict[str, Any]] | None = None,
) -> Path:
    """Create a temporary brain.duckdb file pre-seeded with test data.

    Returns the path to the temporary file.
    Caller is responsible for cleanup (use tmp_path fixture or tempfile).
    """
    import duckdb

    from do_uw.brain.brain_schema import create_schema

    # Create a temp file
    tmpfile = tempfile.mktemp(suffix=".duckdb")
    conn = duckdb.connect(tmpfile)
    create_schema(conn)

    if checks:
        for c in checks:
            conn.execute(
                """INSERT INTO brain_signals (
                    signal_id, version, name, content_type,
                    lifecycle_state, depth, execution_mode,
                    report_section, risk_questions, risk_framework_layer,
                    threshold_type, question, created_by,
                    retired_at, retired_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    c.get("id", "TEST-001"),
                    c.get("version", 1),
                    c.get("name", "Test Check"),
                    c.get("content_type", "EVALUATIVE_CHECK"),
                    c.get("status", "INCUBATING"),
                    c.get("depth", 2),
                    c.get("execution_mode", "AUTO"),
                    c.get("section", "BIZ"),
                    [],
                    c.get("risk_framework_layer", "DIRECT"),
                    c.get("threshold_type", "BOOLEAN"),
                    c.get("question", "Test question?"),
                    c.get("created_by", "test"),
                    c.get("retired_at"),
                    c.get("retired_reason"),
                ],
            )

    if scoring_factors:
        for f in scoring_factors:
            conn.execute(
                """INSERT INTO brain_scoring_factors (
                    factor_id, version, name, max_points, weight_pct, rules
                ) VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    f["factor_id"],
                    f.get("version", 1),
                    f["name"],
                    f["max_points"],
                    f.get("weight_pct", 0),
                    json.dumps({}),
                ],
            )

    if changelog_entries:
        for e in changelog_entries:
            conn.execute(
                """INSERT INTO brain_changelog (
                    signal_id, old_version, new_version, change_type,
                    change_description, changed_by, change_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [
                    e["signal_id"],
                    e.get("old_version", 1),
                    e.get("new_version", 2),
                    e.get("change_type", "UPDATE"),
                    e.get("change_description", ""),
                    e.get("changed_by", "test"),
                    e.get("change_reason"),
                ],
            )

    conn.close()
    return Path(tmpfile)


def _patch_brain_path(db_path: Path) -> Any:
    """Patch get_brain_db_path to return the test database path."""
    return patch(
        "do_uw.brain.brain_schema.get_brain_db_path",
        return_value=db_path,
    )


# --- review command tests ---


def test_review_shows_incubating_checks() -> None:
    """Insert 3 INCUBATING checks, verify review lists them."""
    db_path = _make_tmp_brain_db([
        {"id": "INC-01", "name": "First check", "status": "INCUBATING"},
        {"id": "INC-02", "name": "Second check", "status": "INCUBATING"},
        {"id": "INC-03", "name": "Third check", "status": "INCUBATING"},
    ])
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(app, ["knowledge", "govern", "review"])
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "INC-01" in result.output
        assert "INC-02" in result.output
        assert "INC-03" in result.output
        assert "3 results" in result.output
    finally:
        db_path.unlink(missing_ok=True)


def test_review_filters_by_status() -> None:
    """Mixed statuses -- only ACTIVE shown when filtered."""
    db_path = _make_tmp_brain_db([
        {"id": "A-01", "name": "Active check", "status": "ACTIVE"},
        {"id": "I-01", "name": "Incubating check", "status": "INCUBATING"},
    ])
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(
                app, ["knowledge", "govern", "review", "--status", "ACTIVE"]
            )
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "A-01" in result.output
        assert "I-01" not in result.output
    finally:
        db_path.unlink(missing_ok=True)


def test_review_empty() -> None:
    """No checks with the requested status shows message."""
    db_path = _make_tmp_brain_db([])  # Empty database
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(app, ["knowledge", "govern", "review"])
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "No checks found" in result.output
    finally:
        db_path.unlink(missing_ok=True)


# --- promote command tests ---
# promote is a stub (brain YAML workflow not yet implemented)


def test_promote_returns_not_available() -> None:
    """Promote command informs user to use brain YAML workflow."""
    result = runner.invoke(
        app, ["knowledge", "govern", "promote", "P-01", "DEVELOPING"]
    )
    assert result.exit_code != 0
    # Message should tell user to use brain YAML
    assert "brain" in result.output.lower() or "yaml" in result.output.lower()


def test_promote_deprecated_returns_not_available() -> None:
    """Deprecating without --reason still returns not-available."""
    result = runner.invoke(
        app, ["knowledge", "govern", "promote", "P-03", "DEPRECATED"]
    )
    assert result.exit_code != 0


# --- history command tests ---


def test_history_shows_check_info() -> None:
    """Check in brain.duckdb shows basic header info."""
    db_path = _make_tmp_brain_db([
        {"id": "H-01", "name": "History check", "status": "ACTIVE"},
    ])
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(
                app, ["knowledge", "govern", "history", "H-01"]
            )
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "History check" in result.output
        assert "H-01" in result.output
    finally:
        db_path.unlink(missing_ok=True)


def test_history_check_not_found() -> None:
    """Non-existent check ID shows error."""
    db_path = _make_tmp_brain_db([])
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(
                app, ["knowledge", "govern", "history", "NOPE-99"]
            )
        assert result.exit_code != 0
        assert "not found" in result.output.lower()
    finally:
        db_path.unlink(missing_ok=True)


def test_history_shows_changelog() -> None:
    """Check with changelog entries shows history table."""
    db_path = _make_tmp_brain_db(
        checks=[
            {"id": "H-02", "name": "Changelog Check", "status": "ACTIVE"},
        ],
        changelog_entries=[
            {
                "signal_id": "H-02",
                "old_version": 1,
                "new_version": 2,
                "change_type": "UPDATE",
                "change_description": "Calibrated threshold",
                "changed_by": "governance-review",
                "change_reason": "accuracy",
            }
        ],
    )
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(
                app, ["knowledge", "govern", "history", "H-02"]
            )
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "Changelog Check" in result.output
        # Changelog table should be shown (at minimum a 1-entry table header)
        assert "Modification History" in result.output
    finally:
        db_path.unlink(missing_ok=True)


# --- drift command tests ---


def _make_scoring_config() -> dict[str, Any]:
    """Create a minimal scoring config for drift tests."""
    return {
        "factors": {
            "F1_prior_litigation": {
                "factor_id": "F.1",
                "name": "Prior Litigation",
                "max_points": 20,
                "weight_pct": 20,
            },
            "F2_stock_decline": {
                "factor_id": "F.2",
                "name": "Stock Decline",
                "max_points": 15,
                "weight_pct": 15,
            },
        }
    }


def _run_drift_test(
    db_path: Path, config: dict[str, Any]
) -> Any:
    """Run drift command with patched brain.duckdb path and config."""
    with (
        _patch_brain_path(db_path),
        patch("do_uw.cli_knowledge_governance.json.load", return_value=config),
        patch("do_uw.cli_knowledge_governance.Path.exists", return_value=True),
        patch("builtins.open", create=True),
    ):
        return runner.invoke(app, ["knowledge", "govern", "drift"])


def test_drift_shows_ok_when_synced() -> None:
    """Config and brain.duckdb factors match -- all OK."""
    db_path = _make_tmp_brain_db(
        scoring_factors=[
            {"factor_id": "F.1", "name": "Prior Litigation", "max_points": 20},
            {"factor_id": "F.2", "name": "Stock Decline", "max_points": 15},
        ]
    )
    try:
        result = _run_drift_test(db_path, _make_scoring_config())
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "No drift" in result.output
    finally:
        db_path.unlink(missing_ok=True)


def test_drift_detects_mismatch() -> None:
    """Brain.duckdb has different max points -- DRIFT flagged."""
    db_path = _make_tmp_brain_db(
        scoring_factors=[
            {"factor_id": "F.1", "name": "Prior Litigation", "max_points": 10},
            {"factor_id": "F.2", "name": "Stock Decline", "max_points": 15},
        ]
    )
    try:
        result = _run_drift_test(db_path, _make_scoring_config())
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "Drift detected" in result.output
    finally:
        db_path.unlink(missing_ok=True)


# --- deprecation-log command tests ---


def test_deprecation_log_shows_retired() -> None:
    """RETIRED check appears in deprecation log."""
    db_path = _make_tmp_brain_db([
        {
            "id": "D-01",
            "name": "To deprecate",
            "status": "RETIRED",
            "retired_at": "2026-01-15 10:00:00",
            "retired_reason": "superseded by D-02",
        }
    ])
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(
                app, ["knowledge", "govern", "deprecation-log"]
            )
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "D-01" in result.output
        assert "To deprecate" in result.output
    finally:
        db_path.unlink(missing_ok=True)


def test_deprecation_log_empty() -> None:
    """No retired checks shows message."""
    db_path = _make_tmp_brain_db([
        {"id": "ACTIVE-01", "name": "Active check", "status": "ACTIVE"},
    ])
    try:
        with _patch_brain_path(db_path):
            result = runner.invoke(
                app, ["knowledge", "govern", "deprecation-log"]
            )
        assert result.exit_code == 0, f"Output: {result.output}"
        assert "No retired" in result.output or "No deprecated" in result.output
    finally:
        db_path.unlink(missing_ok=True)
