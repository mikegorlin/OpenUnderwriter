"""Tests for brain migration: signals.json to brain.duckdb.

Verifies that migration correctly loads all 384 checks, populates
75 taxonomy entities (45 v6 subsections + 10 factors + 15 hazards + 5 sections),
seeds 7 backlog items, maps fields correctly, and is idempotent.
"""

from __future__ import annotations

import duckdb
import pytest

from do_uw.brain.brain_migrate import migrate_checks_to_brain
from do_uw.brain.brain_schema import connect_brain_db, create_schema


@pytest.fixture()
def conn() -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB with schema and run migration."""
    connection = connect_brain_db(":memory:")
    create_schema(connection)
    migrate_checks_to_brain(connection)
    return connection


class TestMigrationCounts:
    """Verify correct counts after migration."""

    def test_checks_count(self, conn: duckdb.DuckDBPyConnection) -> None:
        """brain_signals_current must have exactly 400 rows.

        400 checks: 388 original - 4 stubs + 12 new (phase 33-03) + 4 governance (phase 40).
        """
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_signals_current"
        ).fetchone()[0]
        assert count == 400

    def test_taxonomy_risk_questions(self, conn: duckdb.DuckDBPyConnection) -> None:
        """brain_taxonomy must have 45 v6 risk question subsections (X.Y format)."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'risk_question'"
        ).fetchone()[0]
        assert count == 45

    def test_taxonomy_factors(self, conn: duckdb.DuckDBPyConnection) -> None:
        """brain_taxonomy must have 10 scoring factors (F1-F10)."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'factor'"
        ).fetchone()[0]
        assert count == 10

    def test_taxonomy_hazards(self, conn: duckdb.DuckDBPyConnection) -> None:
        """brain_taxonomy must have 15 hazard codes."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'hazard'"
        ).fetchone()[0]
        assert count == 15

    def test_taxonomy_sections(self, conn: duckdb.DuckDBPyConnection) -> None:
        """brain_taxonomy must have 5 v6 report sections."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current WHERE entity_type = 'report_section'"
        ).fetchone()[0]
        assert count == 5

    def test_taxonomy_total(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Total taxonomy entities: 45 + 10 + 15 + 5 = 75."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current"
        ).fetchone()[0]
        assert count == 75

    def test_backlog_count(self, conn: duckdb.DuckDBPyConnection) -> None:
        """brain_backlog must have 7 entries."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_backlog"
        ).fetchone()[0]
        assert count == 7


class TestCheckFieldMappings:
    """Spot-check field mappings for known checks."""

    def test_fin_liq_position(self, conn: duckdb.DuckDBPyConnection) -> None:
        """FIN.LIQ.position should map to financial section with correct fields."""
        row = conn.execute(
            "SELECT report_section, content_type, threshold_type, field_key "
            "FROM brain_signals_current WHERE signal_id = 'FIN.LIQ.position'"
        ).fetchone()
        assert row is not None
        assert row[0] == "financial"
        assert row[1] == "EVALUATIVE_CHECK"
        assert row[2] == "tiered"
        # field_key from data_strategy
        assert row[3] is not None

    def test_gov_board_independence(self, conn: duckdb.DuckDBPyConnection) -> None:
        """GOV.BOARD.independence should map to governance section."""
        row = conn.execute(
            "SELECT report_section, content_type, lifecycle_state "
            "FROM brain_signals_current WHERE signal_id = 'GOV.BOARD.independence'"
        ).fetchone()
        assert row is not None
        assert row[0] == "governance"
        assert row[1] == "EVALUATIVE_CHECK"

    def test_lit_sca_active(self, conn: duckdb.DuckDBPyConnection) -> None:
        """LIT.SCA.active should map to litigation section."""
        row = conn.execute(
            "SELECT report_section, content_type, threshold_type "
            "FROM brain_signals_current WHERE signal_id = 'LIT.SCA.active'"
        ).fetchone()
        assert row is not None
        assert row[0] == "litigation"
        assert row[1] == "EVALUATIVE_CHECK"

    def test_exec_prefix_maps_to_governance(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """EXEC.* checks should map to governance report section."""
        rows = conn.execute(
            "SELECT DISTINCT report_section FROM brain_signals_current "
            "WHERE signal_id LIKE 'EXEC.%'"
        ).fetchall()
        sections = {r[0] for r in rows}
        assert sections == {"governance"}


class TestLifecycleDistribution:
    """Verify lifecycle state distribution is reasonable."""

    def test_monitoring_matches_management_display(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """MONITORING count should match MANAGEMENT_DISPLAY content type count."""
        monitoring = conn.execute(
            "SELECT COUNT(*) FROM brain_signals_current "
            "WHERE lifecycle_state = 'MONITORING'"
        ).fetchone()[0]
        # 64 MANAGEMENT_DISPLAY + display/info/classification/search types
        assert monitoring >= 64

    def test_scoring_has_threshold_criteria(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """All SCORING checks should have at least one threshold criterion."""
        no_criteria = conn.execute(
            "SELECT COUNT(*) FROM brain_signals_current "
            "WHERE lifecycle_state = 'SCORING' "
            "AND threshold_red IS NULL AND threshold_yellow IS NULL AND threshold_clear IS NULL"
        ).fetchone()[0]
        assert no_criteria == 0, f"{no_criteria} SCORING checks lack threshold criteria"

    def test_all_three_states_populated(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Migration should produce checks in SCORING, INVESTIGATION, and MONITORING."""
        states = conn.execute(
            "SELECT DISTINCT lifecycle_state FROM brain_signals_current ORDER BY lifecycle_state"
        ).fetchall()
        state_set = {r[0] for r in states}
        assert "SCORING" in state_set
        assert "INVESTIGATION" in state_set
        assert "MONITORING" in state_set

    def test_state_counts_sum_to_384(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """All lifecycle state counts should sum to 400."""
        total = conn.execute(
            "SELECT SUM(cnt) FROM ("
            "SELECT COUNT(*) as cnt FROM brain_signals_current GROUP BY lifecycle_state"
            ")"
        ).fetchone()[0]
        assert total == 400


class TestTaxonomyContent:
    """Verify taxonomy entity content."""

    def test_question_3_1_has_correct_name(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """v6 subsection 3.1 (Liquidity & Solvency) should have correct name."""
        row = conn.execute(
            "SELECT name FROM brain_taxonomy_current "
            "WHERE entity_type = 'risk_question' AND entity_id = '3.1'"
        ).fetchone()
        assert row is not None
        assert "liquidity" in row[0].lower()

    def test_factor_f1_has_weight(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """F1 (Prior Litigation) should have weight 0.20."""
        row = conn.execute(
            "SELECT name, weight FROM brain_taxonomy_current "
            "WHERE entity_type = 'factor' AND entity_id = 'F1'"
        ).fetchone()
        assert row is not None
        assert row[0] == "Prior Litigation"
        assert abs(row[1] - 0.20) < 0.001

    def test_hazard_sca_has_trend(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """HAZ-SCA should have frequency_trend and severity_range."""
        row = conn.execute(
            "SELECT frequency_trend, severity_range FROM brain_taxonomy_current "
            "WHERE entity_type = 'hazard' AND entity_id = 'HAZ-SCA'"
        ).fetchone()
        assert row is not None
        assert row[0] == "stable"
        assert "settlement" in row[1].lower()

    def test_questions_have_domain(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """All risk questions should have a domain set."""
        null_domain = conn.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current "
            "WHERE entity_type = 'risk_question' AND domain IS NULL"
        ).fetchone()[0]
        assert null_domain == 0

    def test_questions_have_parent(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """All risk questions should have a parent_id (pillar)."""
        null_parent = conn.execute(
            "SELECT COUNT(*) FROM brain_taxonomy_current "
            "WHERE entity_type = 'risk_question' AND parent_id IS NULL"
        ).fetchone()[0]
        assert null_parent == 0


class TestBacklogContent:
    """Verify backlog item content."""

    def test_backlog_all_high_priority(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """All 7 backlog items should have HIGH priority."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_backlog WHERE priority = 'HIGH'"
        ).fetchone()[0]
        assert count == 7

    def test_backlog_all_open(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """All 7 backlog items should have OPEN status."""
        count = conn.execute(
            "SELECT COUNT(*) FROM brain_backlog WHERE status = 'OPEN'"
        ).fetchone()[0]
        assert count == 7

    def test_backlog_has_gap_references(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """All backlog items should have gap_reference G1-G7."""
        refs = conn.execute(
            "SELECT gap_reference FROM brain_backlog ORDER BY gap_reference"
        ).fetchall()
        gap_refs = [r[0] for r in refs]
        assert gap_refs == ["G1", "G2", "G3", "G4", "G5", "G6", "G7"]

    def test_backlog_has_hazards(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Backlog items should have hazard arrays."""
        rows = conn.execute(
            "SELECT backlog_id, hazards FROM brain_backlog "
            "WHERE hazards IS NOT NULL AND len(hazards) > 0"
        ).fetchall()
        assert len(rows) == 7, "All 7 backlog items should have hazards"


class TestIdempotency:
    """Verify migration is idempotent."""

    def test_running_twice_produces_same_results(self) -> None:
        """Running migration twice should produce identical counts."""
        conn = connect_brain_db(":memory:")
        create_schema(conn)

        result1 = migrate_checks_to_brain(conn)
        result2 = migrate_checks_to_brain(conn)

        assert result1 == result2


class TestMigrationReturnValue:
    """Verify the return dict structure."""

    def test_return_dict_keys(self) -> None:
        """migrate_checks_to_brain should return expected keys."""
        conn = connect_brain_db(":memory:")
        create_schema(conn)
        result = migrate_checks_to_brain(conn)

        expected_keys = {
            "signals", "taxonomy_questions", "taxonomy_factors",
            "taxonomy_hazards", "taxonomy_sections", "backlog",
        }
        assert set(result.keys()) == expected_keys

    def test_return_dict_values(self) -> None:
        """Return values should match expected v6 counts."""
        conn = connect_brain_db(":memory:")
        create_schema(conn)
        result = migrate_checks_to_brain(conn)

        assert result["signals"] == 400
        assert result["taxonomy_questions"] == 45
        assert result["taxonomy_factors"] == 10
        assert result["taxonomy_hazards"] == 15
        assert result["taxonomy_sections"] == 5
        assert result["backlog"] == 7
