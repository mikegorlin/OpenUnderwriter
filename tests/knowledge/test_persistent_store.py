"""Tests for persistent knowledge store loading and idempotent migration.

Verifies:
1. Idempotent migration -- running migrate_from_json twice produces no
   errors and identical signal_count both times.
2. signal_count() method -- returns 0 on empty, >0 after migration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from do_uw.knowledge.migrate import migrate_from_json
from do_uw.knowledge.store import KnowledgeStore

BRAIN_DIR = Path(__file__).parent.parent.parent / "src" / "do_uw" / "brain"


@pytest.fixture()
def persistent_store(tmp_path: Path) -> KnowledgeStore:
    """Create a persistent SQLite store in tmp_path."""
    db_path = tmp_path / "knowledge.db"
    return KnowledgeStore(db_path=db_path)


@pytest.fixture()
def seeded_store(persistent_store: KnowledgeStore) -> KnowledgeStore:
    """Create a persistent store with migration data."""
    migrate_from_json(BRAIN_DIR, persistent_store)
    return persistent_store


class TestCheckCount:
    """Tests for the signal_count() method."""

    def test_empty_store_returns_zero(self) -> None:
        """signal_count() returns 0 on an empty in-memory store."""
        store = KnowledgeStore(db_path=None)
        assert store.signal_count() == 0

    def test_empty_persistent_store_returns_zero(
        self, persistent_store: KnowledgeStore
    ) -> None:
        """signal_count() returns 0 on an empty persistent store."""
        assert persistent_store.signal_count() == 0

    def test_seeded_store_returns_positive(
        self, seeded_store: KnowledgeStore
    ) -> None:
        """signal_count() returns >0 after migration."""
        count = seeded_store.signal_count()
        assert count > 0
        # Expect ~388 signals from brain/signals.json
        assert count > 300


class TestIdempotentMigration:
    """Tests for idempotent migration (running migrate twice)."""

    def test_double_migration_no_error(
        self, persistent_store: KnowledgeStore
    ) -> None:
        """Running migrate_from_json twice produces no errors."""
        result1 = migrate_from_json(BRAIN_DIR, persistent_store)
        assert len(result1.errors) == 0

        result2 = migrate_from_json(BRAIN_DIR, persistent_store)
        assert len(result2.errors) == 0

    def test_double_migration_same_signal_count(
        self, persistent_store: KnowledgeStore
    ) -> None:
        """signal_count is identical after first and second migration."""
        migrate_from_json(BRAIN_DIR, persistent_store)
        count_after_first = persistent_store.signal_count()

        migrate_from_json(BRAIN_DIR, persistent_store)
        count_after_second = persistent_store.signal_count()

        assert count_after_first == count_after_second
        assert count_after_first > 0

    def test_double_migration_consistent_counts(
        self, persistent_store: KnowledgeStore
    ) -> None:
        """MigrationResult counts are consistent across two runs."""
        result1 = migrate_from_json(BRAIN_DIR, persistent_store)
        result2 = migrate_from_json(BRAIN_DIR, persistent_store)

        assert result1.checks_migrated == result2.checks_migrated
        assert result1.patterns_migrated == result2.patterns_migrated
        assert result1.rules_migrated == result2.rules_migrated
        assert result1.flags_migrated == result2.flags_migrated
        # Sectors use upsert, count should be consistent
        assert result1.sectors_migrated == result2.sectors_migrated
