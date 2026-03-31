"""Tests for v6 taxonomy remap: validates Q-old to v6 subsection transition.

Validates that after full migration (v1 -> enrich -> remap):
- All 384 checks have v6 risk_questions (X.Y format, no Q1-Q25)
- brain_taxonomy has exactly 45 risk_question entities (v6 subsections)
- brain_taxonomy has exactly 5 report_section entities (v6 sections)
- brain_changelog has remap entries for all checks
- Remap is idempotent (running twice doesn't create extra versions)
"""

from __future__ import annotations

import re

import duckdb
import pytest

from do_uw.brain.brain_enrich import enrich_brain_signals, remap_to_v6
from do_uw.brain.brain_migrate import migrate_checks_to_brain
from do_uw.brain.brain_schema import connect_brain_db, create_schema


@pytest.fixture
def full_migration_db() -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB with full migration pipeline: v1 -> enrich -> remap."""
    conn = connect_brain_db(":memory:")
    create_schema(conn)
    # Full migration with enrichment + remap
    migrate_checks_to_brain(conn, run_enrichment=True)
    return conn


@pytest.fixture
def enriched_only_db() -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB with migration + enrichment, but no remap."""
    conn = connect_brain_db(":memory:")
    create_schema(conn)
    migrate_checks_to_brain(conn, run_enrichment=False)
    enrich_brain_signals(conn)
    return conn


class TestRemapCreatesV6Rows:
    """Test that remap_to_v6() creates proper version rows."""

    def test_all_checks_present_after_remap(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """All 384 checks should exist in brain_signals_current after remap."""
        count = full_migration_db.execute(
            "SELECT COUNT(*) FROM brain_signals_current"
        ).fetchone()[0]
        assert count == 400, f"Expected 384 current checks, got {count}"

    def test_no_old_q_ids_in_current(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """No Q-old references should remain in brain_signals_current."""
        rows = full_migration_db.execute(
            """SELECT signal_id, risk_questions FROM brain_signals_current
               WHERE risk_questions IS NOT NULL AND len(risk_questions) > 0"""
        ).fetchall()
        for signal_id, questions in rows:
            for q in questions:
                assert not (q.startswith("Q") and q[1:].isdigit()), (
                    f"{signal_id} still has old Q-ID: {q}"
                )

    def test_all_risk_questions_v6_format(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """All risk_question values should match X.Y subsection format."""
        rows = full_migration_db.execute(
            """SELECT signal_id, risk_questions FROM brain_signals_current
               WHERE risk_questions IS NOT NULL AND len(risk_questions) > 0"""
        ).fetchall()
        for signal_id, questions in rows:
            for q in questions:
                assert re.match(r"^\d+\.\d+$", q), (
                    f"{signal_id} has non-v6 question ID: {q}"
                )


class TestTaxonomyV6:
    """Test brain_taxonomy has correct v6 entities."""

    def test_exactly_45_risk_question_entities(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """brain_taxonomy should have exactly 45 risk_question entities (v6 subsections)."""
        count = full_migration_db.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'risk_question'"
        ).fetchone()[0]
        assert count == 45, f"Expected 45 risk_question entities, got {count}"

    def test_all_subsection_ids_are_v6_format(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """All risk_question entity_ids should match X.Y format."""
        rows = full_migration_db.execute(
            """SELECT entity_id FROM brain_taxonomy_current
               WHERE entity_type = 'risk_question'"""
        ).fetchall()
        for row in rows:
            assert re.match(r"^\d+\.\d+$", row[0]), f"Bad entity_id format: {row[0]}"

    def test_no_old_q_ids_in_taxonomy(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """No Q1-Q25 entity_ids should exist in taxonomy."""
        old = full_migration_db.execute(
            """SELECT entity_id FROM brain_taxonomy_current
               WHERE entity_type = 'risk_question'
               AND entity_id LIKE 'Q%'"""
        ).fetchall()
        assert len(old) == 0, f"Old Q-IDs found in taxonomy: {[r[0] for r in old]}"

    def test_exactly_5_report_sections(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """brain_taxonomy should have exactly 5 v6 report_section entities."""
        count = full_migration_db.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'report_section'"
        ).fetchone()[0]
        assert count == 5, f"Expected 5 report_section entities, got {count}"

    def test_report_section_names(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """Report section entity_ids should match v6 section names."""
        rows = full_migration_db.execute(
            """SELECT entity_id FROM brain_taxonomy_current
               WHERE entity_type = 'report_section'
               ORDER BY entity_id"""
        ).fetchall()
        section_ids = [r[0] for r in rows]
        expected = ["company", "financial", "governance", "litigation", "market"]
        assert section_ids == expected, f"Expected {expected}, got {section_ids}"

    def test_subsection_parent_ids(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """Each subsection's parent_id should match its section number."""
        rows = full_migration_db.execute(
            """SELECT entity_id, parent_id FROM brain_taxonomy_current
               WHERE entity_type = 'risk_question'"""
        ).fetchall()
        for entity_id, parent_id in rows:
            expected_parent = entity_id.split(".")[0]
            assert parent_id == expected_parent, (
                f"Subsection {entity_id} parent_id={parent_id}, expected={expected_parent}"
            )

    def test_section_distribution(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """v6 subsection count per section should match QUESTIONS-FINAL.md."""
        rows = full_migration_db.execute(
            """SELECT parent_id, COUNT(*) FROM brain_taxonomy_current
               WHERE entity_type = 'risk_question'
               GROUP BY parent_id ORDER BY parent_id"""
        ).fetchall()
        distribution = {r[0]: r[1] for r in rows}
        # Section 1: 11, Section 2: 8, Section 3: 8, Section 4: 9, Section 5: 9
        assert distribution.get("1") == 11, f"Section 1: {distribution.get('1')}"
        assert distribution.get("2") == 8, f"Section 2: {distribution.get('2')}"
        assert distribution.get("3") == 8, f"Section 3: {distribution.get('3')}"
        assert distribution.get("4") == 9, f"Section 4: {distribution.get('4')}"
        assert distribution.get("5") == 9, f"Section 5: {distribution.get('5')}"

    def test_factors_unchanged(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """Factor entities (F1-F10) should be unchanged."""
        count = full_migration_db.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'factor'"
        ).fetchone()[0]
        assert count == 10, f"Expected 10 factor entities, got {count}"

    def test_hazards_unchanged(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """Hazard entities (HAZ-*) should be unchanged."""
        count = full_migration_db.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'hazard'"
        ).fetchone()[0]
        assert count == 15, f"Expected 15 hazard entities, got {count}"


class TestRemapChangelog:
    """Test that remap documents transitions in brain_changelog."""

    def test_changelog_has_enrichment_entries(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """brain_changelog should have enrichment entries for all 384 checks."""
        count = full_migration_db.execute(
            "SELECT COUNT(*) FROM brain_changelog WHERE triggered_by = 'phase_32_enrichment'"
        ).fetchone()[0]
        assert count == 400, f"Expected 384 enrichment entries, got {count}"

    def test_changelog_entries_are_modified(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """All changelog entries should be MODIFIED type."""
        non_modified = full_migration_db.execute(
            "SELECT COUNT(*) FROM brain_changelog WHERE change_type != 'MODIFIED'"
        ).fetchone()[0]
        assert non_modified == 0, f"{non_modified} non-MODIFIED changelog entries"


class TestRemapIdempotency:
    """Test that remap is idempotent."""

    def test_remap_twice_is_noop(self, enriched_only_db: duckdb.DuckDBPyConnection) -> None:
        """Running remap_to_v6() twice should not create extra version rows."""
        # First remap: since enrichment already used v6, most checks should be already_v6
        stats1 = remap_to_v6(enriched_only_db)

        # Count total rows and current version
        total_after_first = enriched_only_db.execute(
            "SELECT COUNT(*) FROM brain_signals"
        ).fetchone()[0]
        max_ver_after_first = enriched_only_db.execute(
            "SELECT MAX(version) FROM brain_signals_current"
        ).fetchone()[0]

        # Second remap: should be fully idempotent
        stats2 = remap_to_v6(enriched_only_db)

        total_after_second = enriched_only_db.execute(
            "SELECT COUNT(*) FROM brain_signals"
        ).fetchone()[0]
        max_ver_after_second = enriched_only_db.execute(
            "SELECT MAX(version) FROM brain_signals_current"
        ).fetchone()[0]

        # No new rows should be created
        assert total_after_second == total_after_first, (
            f"Second remap created rows: {total_after_first} -> {total_after_second}"
        )
        assert max_ver_after_second == max_ver_after_first, (
            f"Second remap bumped version: {max_ver_after_first} -> {max_ver_after_second}"
        )
        # Second remap should report all as already_v6
        assert stats2["already_v6"] == 400, (
            f"Expected 384 already_v6 on second run, got {stats2['already_v6']}"
        )
        assert stats2["remapped"] == 0, (
            f"Expected 0 remapped on second run, got {stats2['remapped']}"
        )

    def test_full_migration_is_idempotent(self) -> None:
        """Running migrate_checks_to_brain twice should produce identical results."""
        conn = connect_brain_db(":memory:")
        create_schema(conn)

        result1 = migrate_checks_to_brain(conn, run_enrichment=True)
        result2 = migrate_checks_to_brain(conn, run_enrichment=True)

        assert result1 == result2, f"Results differ:\n  run1={result1}\n  run2={result2}"
        conn.close()


class TestBacklogV6:
    """Test that backlog items use v6 IDs."""

    def test_backlog_risk_questions_v6(self, full_migration_db: duckdb.DuckDBPyConnection) -> None:
        """All backlog risk_questions should use v6 X.Y format."""
        rows = full_migration_db.execute(
            "SELECT backlog_id, risk_questions FROM brain_backlog"
        ).fetchall()
        for bid, questions in rows:
            for q in questions:
                assert re.match(r"^\d+\.\d+$", q), (
                    f"Backlog {bid} has non-v6 question ID: {q}"
                )
