"""Tests for provenance tracking and audit trail utilities."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.knowledge.lifecycle import (
    SignalStatus,
    record_field_change,
    transition_signal,
)
from do_uw.knowledge.models import Check
from do_uw.knowledge.provenance import (
    ProvenanceEntry,
    ProvenanceSummary,
    get_signal_history,
    get_deprecation_log,
    get_migration_stats,
    get_provenance_summary,
)
from do_uw.knowledge.store import KnowledgeStore


def _make_store_with_checks() -> KnowledgeStore:
    """Create an in-memory store with test checks and history."""
    store = KnowledgeStore(db_path=None)
    now = datetime.now(UTC)

    checks = [
        Check(
            id="CHK.001",
            name="Revenue Decline Check",
            section=3,
            pillar="P2_WHY_NOW",
            status="ACTIVE",
            required_data=["SEC_10K"],
            data_locations={"SEC_10K": ["item_7_mda"]},
            scoring_factor="F8",
            origin="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
            version=3,
        ),
        Check(
            id="CHK.002",
            name="Board Turnover Check",
            section=4,
            pillar="P1_WHAT_WRONG",
            status="DEPRECATED",
            required_data=["SEC_DEF14A"],
            data_locations={"SEC_DEF14A": ["board_composition"]},
            scoring_factor="F9",
            origin="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
            version=2,
        ),
        Check(
            id="CHK.003",
            name="User Added Check",
            section=5,
            pillar="P3_HOW_BAD",
            status="DEVELOPING",
            required_data=["SCAC_SEARCH"],
            data_locations={"SCAC_SEARCH": ["search_results"]},
            origin="USER_ADDED",
            created_at=now,
            modified_at=now,
            version=1,
        ),
    ]
    store.bulk_insert_checks(checks)

    # Add history entries via lifecycle functions
    with store.get_session() as session:
        # CHK.001: threshold change (version 2) then name change (version 3)
        # Reset version to 1 for lifecycle functions to increment
        chk1 = session.get(Check, "CHK.001")
        assert chk1 is not None
        chk1.version = 1
        session.flush()

        record_field_change(
            session,
            "CHK.001",
            "threshold_value",
            "5",
            "10",
            "developer",
            "Adjusted threshold based on sector analysis",
        )
        record_field_change(
            session,
            "CHK.001",
            "name",
            "Revenue Check",
            "Revenue Decline Check",
            "developer",
            "Clarified naming convention",
        )

        # CHK.002: status transition to DEPRECATED
        chk2 = session.get(Check, "CHK.002")
        assert chk2 is not None
        chk2.version = 1
        chk2.status = "ACTIVE"
        session.flush()

        transition_signal(
            session,
            "CHK.002",
            SignalStatus.DEPRECATED,
            "admin",
            "Replaced by governance_forensics extractor",
        )

    return store


class TestGetCheckHistory:
    """Tests for get_signal_history function."""

    def test_returns_entries_in_version_order(self) -> None:
        """History entries should be sorted by version ascending."""
        store = _make_store_with_checks()
        history = get_signal_history(store, "CHK.001")
        assert len(history) >= 2
        for i in range(len(history) - 1):
            assert history[i].version <= history[i + 1].version

    def test_entry_has_field_details(self) -> None:
        """Each entry should have field_name, old_value, new_value."""
        store = _make_store_with_checks()
        history = get_signal_history(store, "CHK.001")
        threshold_entries = [
            e for e in history if e.field_name == "threshold_value"
        ]
        assert len(threshold_entries) == 1
        entry = threshold_entries[0]
        assert entry.old_value == "5"
        assert entry.new_value == "10"
        assert entry.changed_by == "developer"
        assert entry.reason is not None

    def test_empty_history_returns_empty_list(self) -> None:
        """A check with no history entries returns empty list."""
        store = _make_store_with_checks()
        history = get_signal_history(store, "CHK.003")
        assert history == []

    def test_nonexistent_check_returns_empty(self) -> None:
        """A check ID that doesn't exist returns empty list."""
        store = _make_store_with_checks()
        history = get_signal_history(store, "NONEXISTENT")
        assert history == []

    def test_returns_provenance_entry_type(self) -> None:
        """Results should be ProvenanceEntry instances."""
        store = _make_store_with_checks()
        history = get_signal_history(store, "CHK.001")
        assert all(isinstance(e, ProvenanceEntry) for e in history)


class TestGetProvenanceSummary:
    """Tests for get_provenance_summary function."""

    def test_includes_status_transitions(self) -> None:
        """Summary should include status transition entries."""
        store = _make_store_with_checks()
        summary = get_provenance_summary(store, "CHK.002")
        assert isinstance(summary, ProvenanceSummary)
        assert len(summary.status_transitions) >= 1
        dep_transition = summary.status_transitions[-1]
        assert dep_transition.new_value == "DEPRECATED"
        assert dep_transition.changed_by == "admin"

    def test_includes_origin_and_creation(self) -> None:
        """Summary should include origin and created_at."""
        store = _make_store_with_checks()
        summary = get_provenance_summary(store, "CHK.001")
        assert summary.origin == "BRAIN_MIGRATION"
        assert summary.created_at is not None
        assert summary.signal_name == "Revenue Decline Check"

    def test_recent_changes_last_10(self) -> None:
        """Recent changes should be at most 10 entries."""
        store = _make_store_with_checks()
        summary = get_provenance_summary(store, "CHK.001")
        assert len(summary.recent_changes) <= 10
        assert len(summary.recent_changes) >= 2  # threshold + name changes

    def test_total_modifications_count(self) -> None:
        """Total modifications should match history entry count."""
        store = _make_store_with_checks()
        summary = get_provenance_summary(store, "CHK.001")
        history = get_signal_history(store, "CHK.001")
        assert summary.total_modifications == len(history)

    def test_nonexistent_check_raises(self) -> None:
        """Requesting summary for unknown check raises ValueError."""
        store = _make_store_with_checks()
        with pytest.raises(ValueError, match="Check not found"):
            get_provenance_summary(store, "NONEXISTENT")

    def test_check_with_no_history(self) -> None:
        """A check with no history still returns valid summary."""
        store = _make_store_with_checks()
        summary = get_provenance_summary(store, "CHK.003")
        assert summary.total_modifications == 0
        assert summary.status_transitions == []
        assert summary.recent_changes == []
        assert summary.origin == "USER_ADDED"


class TestGetMigrationStats:
    """Tests for get_migration_stats function."""

    def test_counts_by_origin(self) -> None:
        """Stats should count checks by origin correctly."""
        store = _make_store_with_checks()
        stats = get_migration_stats(store)
        by_origin: dict[str, int] = stats["by_origin"]
        assert by_origin.get("BRAIN_MIGRATION", 0) == 2
        assert by_origin.get("USER_ADDED", 0) == 1

    def test_counts_by_status(self) -> None:
        """Stats should count checks by status correctly."""
        store = _make_store_with_checks()
        stats = get_migration_stats(store)
        by_status: dict[str, int] = stats["by_status"]
        # CHK.001=ACTIVE, CHK.002=DEPRECATED, CHK.003=DEVELOPING
        assert by_status.get("ACTIVE", 0) == 1
        assert by_status.get("DEPRECATED", 0) == 1
        assert by_status.get("DEVELOPING", 0) == 1

    def test_total_signals(self) -> None:
        """Total checks should match sum of all checks."""
        store = _make_store_with_checks()
        stats = get_migration_stats(store)
        assert stats["total_signals"] == 3

    def test_total_history_entries(self) -> None:
        """Total history entries should be > 0 with populated history."""
        store = _make_store_with_checks()
        stats = get_migration_stats(store)
        assert stats["total_history_entries"] >= 3

    def test_empty_store(self) -> None:
        """Empty store returns all zeros."""
        store = KnowledgeStore(db_path=None)
        stats = get_migration_stats(store)
        assert stats["total_signals"] == 0
        assert stats["total_history_entries"] == 0
        assert stats["by_origin"] == {}
        assert stats["by_status"] == {}


class TestGetDeprecationLog:
    """Tests for get_deprecation_log function."""

    def test_includes_deprecated_checks(self) -> None:
        """Deprecation log should include deprecated checks."""
        store = _make_store_with_checks()
        log = get_deprecation_log(store)
        assert len(log) >= 1
        signal_ids = [entry["signal_id"] for entry in log]
        assert "CHK.002" in signal_ids

    def test_includes_deprecation_reason(self) -> None:
        """Deprecation log should include the reason for deprecation."""
        store = _make_store_with_checks()
        log = get_deprecation_log(store)
        chk002_entries = [
            e for e in log if e["signal_id"] == "CHK.002"
        ]
        assert len(chk002_entries) == 1
        entry = chk002_entries[0]
        assert entry["reason"] is not None
        assert "governance_forensics" in entry["reason"]
        assert entry["deprecated_by"] == "admin"

    def test_sorted_by_deprecation_date(self) -> None:
        """Log should be sorted by deprecation date."""
        store = _make_store_with_checks()
        log = get_deprecation_log(store)
        if len(log) >= 2:
            for i in range(len(log) - 1):
                assert log[i]["deprecated_at"] <= log[i + 1]["deprecated_at"]

    def test_empty_when_no_deprecated(self) -> None:
        """No deprecated checks means empty log."""
        store = KnowledgeStore(db_path=None)
        now = datetime.now(UTC)
        check = Check(
            id="ACTIVE.001",
            name="Active Check",
            section=3,
            pillar="P1_WHAT_WRONG",
            status="ACTIVE",
            required_data=["SEC_10K"],
            data_locations={},
            origin="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
            version=1,
        )
        store.bulk_insert_checks([check])
        log = get_deprecation_log(store)
        assert log == []

    def test_deprecated_without_history(self) -> None:
        """A deprecated check without history still appears with defaults."""
        store = KnowledgeStore(db_path=None)
        now = datetime.now(UTC)
        check = Check(
            id="DEP.ORPHAN",
            name="Orphan Deprecated",
            section=3,
            pillar="P1_WHAT_WRONG",
            status="DEPRECATED",
            required_data=["SEC_10K"],
            data_locations={},
            origin="BRAIN_MIGRATION",
            created_at=now,
            modified_at=now,
            version=1,
        )
        store.bulk_insert_checks([check])
        log = get_deprecation_log(store)
        assert len(log) == 1
        assert log[0]["deprecated_by"] == "unknown"
        assert log[0]["reason"] is None
