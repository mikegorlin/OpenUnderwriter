"""Tests for BrainWriter: CRUD operations with versioning and audit trail.

Verifies insert, update, retire, promote, export_json, and changelog
functionality. All tests use in-memory DuckDB.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb
import pytest

from do_uw.brain.brain_schema import connect_brain_db, create_schema
from do_uw.brain.brain_writer import BrainWriter


@pytest.fixture()
def writer() -> BrainWriter:
    """Create BrainWriter with in-memory DB and schema."""
    w = BrainWriter(db_path=":memory:")
    conn = w._get_conn()
    create_schema(conn)
    return w


def _sample_signal_data(**overrides: Any) -> dict[str, Any]:
    """Return minimal valid check data dict."""
    data: dict[str, Any] = {
        "name": "Test Check",
        "content_type": "EVALUATIVE_CHECK",
        "lifecycle_state": "INVESTIGATION",
        "depth": 2,
        "execution_mode": "AUTO",
        "report_section": "financials",
        "risk_questions": ["Q6"],
        "risk_framework_layer": "risk_modifier",
        "factors": ["F3"],
        "hazards": ["HAZ-SCA"],
        "threshold_type": "tiered",
        "threshold_red": "Below 1.0",
        "threshold_yellow": "Between 1.0 and 1.5",
        "threshold_clear": "Above 1.5",
        "question": "Is liquidity adequate?",
        "required_data": ["current_ratio"],
        "data_locations": {"primary": "xbrl_financials"},
    }
    data.update(overrides)
    return data


class TestInsertCheck:
    """Test BrainWriter.insert_check()."""

    def test_insert_creates_version_1(self, writer: BrainWriter) -> None:
        """insert_check returns version 1."""
        version = writer.insert_check(
            "TEST.NEW.check", _sample_signal_data(), "Test creation",
        )
        assert version == 1

    def test_insert_stores_correct_fields(self, writer: BrainWriter) -> None:
        """Inserted check has correct field values."""
        data = _sample_signal_data(name="Specific Check")
        writer.insert_check("TEST.FIELDS.check", data, "Test fields")

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT name, content_type, lifecycle_state, report_section, "
            "threshold_red, threshold_yellow, threshold_clear "
            "FROM brain_signals WHERE signal_id = 'TEST.FIELDS.check'"
        ).fetchone()
        assert row is not None
        assert row[0] == "Specific Check"
        assert row[1] == "EVALUATIVE_CHECK"
        assert row[2] == "INVESTIGATION"
        assert row[3] == "financials"
        assert row[4] == "Below 1.0"
        assert row[5] == "Between 1.0 and 1.5"
        assert row[6] == "Above 1.5"

    def test_insert_duplicate_raises(self, writer: BrainWriter) -> None:
        """Inserting a check with existing ID raises ValueError."""
        writer.insert_check("TEST.DUP.check", _sample_signal_data(), "First")
        with pytest.raises(ValueError, match="already exists"):
            writer.insert_check("TEST.DUP.check", _sample_signal_data(), "Second")

    def test_insert_creates_changelog(self, writer: BrainWriter) -> None:
        """Insert creates a CREATED changelog entry."""
        writer.insert_check("TEST.LOG.check", _sample_signal_data(), "Created for test")
        log = writer.get_changelog("TEST.LOG.check")
        assert len(log) == 1
        assert log[0]["change_type"] == "CREATED"
        assert log[0]["new_version"] == 1
        assert log[0]["old_version"] is None

    def test_insert_stores_data_locations_as_json(
        self, writer: BrainWriter,
    ) -> None:
        """data_locations dict is stored as JSON string."""
        data = _sample_signal_data(
            data_locations={"primary": "sec_filings", "fallback": "web_search"},
        )
        writer.insert_check("TEST.DLOC.check", data, "Test data locations")

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT data_locations FROM brain_signals WHERE signal_id = 'TEST.DLOC.check'"
        ).fetchone()
        parsed = json.loads(row[0])
        assert parsed["primary"] == "sec_filings"
        assert parsed["fallback"] == "web_search"


class TestUpdateCheck:
    """Test BrainWriter.update_check()."""

    def test_update_increments_version(self, writer: BrainWriter) -> None:
        """update_check creates version 2."""
        writer.insert_check("TEST.UPD.check", _sample_signal_data(), "Initial")
        version = writer.update_check(
            "TEST.UPD.check", {"name": "Updated Check"}, "Name change",
        )
        assert version == 2

    def test_update_preserves_unchanged_fields(
        self, writer: BrainWriter,
    ) -> None:
        """Fields not in changes dict are preserved from previous version."""
        data = _sample_signal_data(name="Original", threshold_red="Below 1.0")
        writer.insert_check("TEST.MERGE.check", data, "Initial")

        writer.update_check(
            "TEST.MERGE.check", {"name": "Changed"}, "Name only",
        )

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT name, threshold_red FROM brain_signals_current "
            "WHERE signal_id = 'TEST.MERGE.check'"
        ).fetchone()
        assert row[0] == "Changed"
        assert row[1] == "Below 1.0"  # Preserved

    def test_update_nonexistent_raises(self, writer: BrainWriter) -> None:
        """Updating a non-existent check raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            writer.update_check(
                "TEST.MISSING.check", {"name": "Nope"}, "No such check",
            )

    def test_multiple_updates_increment_versions(
        self, writer: BrainWriter,
    ) -> None:
        """Three updates produce versions 1, 2, 3, 4."""
        writer.insert_check("TEST.MULTI.check", _sample_signal_data(), "v1")
        v2 = writer.update_check("TEST.MULTI.check", {"depth": 3}, "v2")
        v3 = writer.update_check("TEST.MULTI.check", {"depth": 4}, "v3")
        v4 = writer.update_check("TEST.MULTI.check", {"depth": 5}, "v4")
        assert v2 == 2
        assert v3 == 3
        assert v4 == 4

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT version, depth FROM brain_signals_current "
            "WHERE signal_id = 'TEST.MULTI.check'"
        ).fetchone()
        assert row == (4, 5)

    def test_update_creates_changelog(self, writer: BrainWriter) -> None:
        """Update creates a MODIFIED changelog entry."""
        writer.insert_check("TEST.ULOG.check", _sample_signal_data(), "Init")
        writer.update_check(
            "TEST.ULOG.check", {"name": "New Name"}, "Renamed check",
        )
        log = writer.get_changelog("TEST.ULOG.check")
        assert len(log) == 2  # CREATED + MODIFIED
        # Most recent first
        assert log[0]["change_type"] == "MODIFIED"
        assert log[0]["new_version"] == 2
        assert log[0]["old_version"] == 1
        assert "name" in log[0]["fields_changed"]


class TestRetireCheck:
    """Test BrainWriter.retire_check()."""

    def test_retire_sets_lifecycle_retired(self, writer: BrainWriter) -> None:
        """Retired check has lifecycle_state = RETIRED."""
        writer.insert_check("TEST.RET.check", _sample_signal_data(), "Init")
        writer.retire_check("TEST.RET.check", "No longer needed")

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT lifecycle_state FROM brain_signals_current "
            "WHERE signal_id = 'TEST.RET.check'"
        ).fetchone()
        assert row[0] == "RETIRED"

    def test_retired_excluded_from_active_view(
        self, writer: BrainWriter,
    ) -> None:
        """Retired check does not appear in brain_signals_active."""
        writer.insert_check("TEST.RETA.check", _sample_signal_data(), "Init")
        writer.retire_check("TEST.RETA.check", "Obsolete")

        conn = writer._get_conn()
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_signals_active "
            "WHERE signal_id = 'TEST.RETA.check'"
        ).fetchone()[0]
        assert count == 0

    def test_retire_increments_version(self, writer: BrainWriter) -> None:
        """Retiring creates a new version."""
        writer.insert_check("TEST.RETV.check", _sample_signal_data(), "Init")
        version = writer.retire_check("TEST.RETV.check", "Done")
        assert version == 2

    def test_retire_nonexistent_raises(self, writer: BrainWriter) -> None:
        """Retiring a non-existent check raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            writer.retire_check("TEST.NOPE.check", "No such check")

    def test_retire_already_retired_raises(self, writer: BrainWriter) -> None:
        """Retiring an already retired check raises ValueError."""
        writer.insert_check("TEST.RR.check", _sample_signal_data(), "Init")
        writer.retire_check("TEST.RR.check", "First retire")
        with pytest.raises(ValueError, match="already retired"):
            writer.retire_check("TEST.RR.check", "Second retire")

    def test_retire_creates_changelog(self, writer: BrainWriter) -> None:
        """Retire creates a RETIRED changelog entry."""
        writer.insert_check("TEST.RLOG.check", _sample_signal_data(), "Init")
        writer.retire_check("TEST.RLOG.check", "Obsolete check")
        log = writer.get_changelog("TEST.RLOG.check")
        # Most recent first
        assert log[0]["change_type"] == "RETIRED"

    def test_retire_sets_retired_at(self, writer: BrainWriter) -> None:
        """Retiring sets the retired_at timestamp."""
        writer.insert_check("TEST.RTIME.check", _sample_signal_data(), "Init")
        writer.retire_check("TEST.RTIME.check", "Timed retire")

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT retired_at, retired_reason FROM brain_signals "
            "WHERE signal_id = 'TEST.RTIME.check' AND version = 2"
        ).fetchone()
        assert row[0] is not None  # timestamp set
        assert row[1] == "Timed retire"


class TestPromoteCheck:
    """Test BrainWriter.promote_check()."""

    def test_promote_changes_lifecycle(self, writer: BrainWriter) -> None:
        """Promote changes lifecycle state."""
        data = _sample_signal_data(lifecycle_state="INVESTIGATION")
        writer.insert_check("TEST.PROM.check", data, "Init")
        version = writer.promote_check(
            "TEST.PROM.check", "SCORING", "Ready for scoring",
        )
        assert version == 2

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT lifecycle_state FROM brain_signals_current "
            "WHERE signal_id = 'TEST.PROM.check'"
        ).fetchone()
        assert row[0] == "SCORING"

    def test_promote_preserves_other_fields(
        self, writer: BrainWriter,
    ) -> None:
        """Promotion only changes lifecycle_state, nothing else."""
        data = _sample_signal_data(name="My Check", threshold_red="Bad")
        writer.insert_check("TEST.PROMP.check", data, "Init")
        writer.promote_check("TEST.PROMP.check", "SCORING", "Ready")

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT name, threshold_red FROM brain_signals_current "
            "WHERE signal_id = 'TEST.PROMP.check'"
        ).fetchone()
        assert row[0] == "My Check"
        assert row[1] == "Bad"


class TestExportJson:
    """Test BrainWriter.export_json()."""

    def test_export_creates_file(
        self, writer: BrainWriter, tmp_path: Path,
    ) -> None:
        """export_json creates a valid JSON file."""
        writer.insert_check("TEST.EXP.check", _sample_signal_data(), "For export")
        output = tmp_path / "exported.json"
        count = writer.export_json(output)
        assert count == 1
        assert output.exists()

        with open(output) as f:
            data = json.load(f)
        assert data["$schema"] == "BRAIN_CHECKS_EXPORT"
        assert data["total_signals"] == 1
        assert len(data["signals"]) == 1

    def test_export_excludes_retired(
        self, writer: BrainWriter, tmp_path: Path,
    ) -> None:
        """Retired checks are not in the export."""
        writer.insert_check("TEST.EX1.check", _sample_signal_data(), "Keep")
        writer.insert_check(
            "TEST.EX2.check",
            _sample_signal_data(name="Retired One"),
            "To retire",
        )
        writer.retire_check("TEST.EX2.check", "Obsolete")

        output = tmp_path / "exported.json"
        count = writer.export_json(output)
        assert count == 1

    def test_export_field_structure(
        self, writer: BrainWriter, tmp_path: Path,
    ) -> None:
        """Exported check has expected field structure."""
        data = _sample_signal_data(
            name="Export Test",
            factors=["F1", "F3"],
            field_key="current_ratio",
        )
        writer.insert_check("TEST.EXS.check", data, "Structure test")

        output = tmp_path / "exported.json"
        writer.export_json(output)

        with open(output) as f:
            exported = json.load(f)
        check = exported["signals"][0]
        assert check["id"] == "TEST.EXS.check"
        assert check["name"] == "Export Test"
        assert check["factors"] == ["F1", "F3"]
        assert check["data_strategy"]["field_key"] == "current_ratio"
        assert "type" in check["threshold"]


class TestChangelog:
    """Test BrainWriter.get_changelog()."""

    def test_changelog_ordered_newest_first(
        self, writer: BrainWriter,
    ) -> None:
        """Changelog entries are ordered newest first."""
        writer.insert_check("TEST.CL.check", _sample_signal_data(), "v1")
        writer.update_check("TEST.CL.check", {"depth": 3}, "v2")
        writer.update_check("TEST.CL.check", {"depth": 4}, "v3")

        log = writer.get_changelog("TEST.CL.check")
        assert len(log) == 3
        assert log[0]["new_version"] == 3
        assert log[1]["new_version"] == 2
        assert log[2]["new_version"] == 1

    def test_changelog_global_query(self, writer: BrainWriter) -> None:
        """get_changelog() without signal_id returns all entries."""
        writer.insert_check("TEST.G1.check", _sample_signal_data(), "First")
        writer.insert_check(
            "TEST.G2.check",
            _sample_signal_data(name="Second"),
            "Second",
        )

        log = writer.get_changelog()
        assert len(log) == 2

    def test_changelog_limit(self, writer: BrainWriter) -> None:
        """Changelog respects limit parameter."""
        writer.insert_check("TEST.LIM.check", _sample_signal_data(), "v1")
        for i in range(5):
            writer.update_check(
                "TEST.LIM.check", {"depth": i}, f"update {i}",
            )

        log = writer.get_changelog("TEST.LIM.check", limit=3)
        assert len(log) == 3

    def test_changelog_fields_present(self, writer: BrainWriter) -> None:
        """Changelog entries have all expected fields."""
        writer.insert_check("TEST.CF.check", _sample_signal_data(), "Init")
        log = writer.get_changelog("TEST.CF.check")
        entry = log[0]
        expected_keys = {
            "changelog_id", "signal_id", "old_version", "new_version",
            "change_type", "change_description", "fields_changed",
            "changed_by", "changed_at", "change_reason",
        }
        assert expected_keys.issubset(set(entry.keys()))


class TestVersionHistory:
    """Test that version history is preserved (append-only)."""

    def test_all_versions_in_table(self, writer: BrainWriter) -> None:
        """All version rows are stored in brain_signals (append-only)."""
        writer.insert_check("TEST.VH.check", _sample_signal_data(), "v1")
        writer.update_check("TEST.VH.check", {"name": "v2 name"}, "v2")
        writer.update_check("TEST.VH.check", {"name": "v3 name"}, "v3")

        conn = writer._get_conn()
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_signals WHERE signal_id = 'TEST.VH.check'"
        ).fetchone()[0]
        assert count == 3

    def test_current_view_returns_latest(self, writer: BrainWriter) -> None:
        """brain_signals_current returns only the latest version."""
        writer.insert_check("TEST.CV.check", _sample_signal_data(name="V1"), "v1")
        writer.update_check("TEST.CV.check", {"name": "V2"}, "v2")

        conn = writer._get_conn()
        row = conn.execute(
            "SELECT version, name FROM brain_signals_current "
            "WHERE signal_id = 'TEST.CV.check'"
        ).fetchone()
        assert row == (2, "V2")

    def test_close_connection(self, writer: BrainWriter) -> None:
        """close() should not raise."""
        writer.close()
        # Calling close again should also be safe
        writer.close()
