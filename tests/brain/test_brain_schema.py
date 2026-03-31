"""Tests for brain DuckDB schema creation and view logic.

Verifies that the schema module creates all 7 tables, 3 views,
and that view logic correctly returns latest versions and filters
retired checks.
"""

from __future__ import annotations

import duckdb
import pytest

from do_uw.brain.brain_schema import connect_brain_db, create_schema, get_brain_db_path


class TestBrainSchemaCreation:
    """Test schema creation on in-memory DuckDB."""

    @pytest.fixture()
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Create an in-memory DuckDB connection with schema."""
        connection = connect_brain_db(":memory:")
        create_schema(connection)
        return connection

    def test_get_brain_db_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Path should point to brain.duckdb alongside signals.json."""
        monkeypatch.delenv("DO_UW_BRAIN_DB_PATH", raising=False)
        path = get_brain_db_path()
        assert path.name == "brain.duckdb"
        assert path.parent.name == "brain"

    def test_all_tables_exist(self, conn: duckdb.DuckDBPyConnection) -> None:
        """All 21 brain tables must exist after schema creation."""
        result = conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'main' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """).fetchall()
        table_names = sorted([row[0] for row in result])
        expected = sorted([
            "brain_backlog",
            "brain_causal_chains",
            "brain_changelog",
            "brain_correlations",
            "brain_signal_runs",
            "brain_signals",
            "brain_config",
            "brain_effectiveness",
            "brain_feedback",
            "brain_industry",
            "brain_meta",
            "brain_patterns",
            "brain_perils",
            "brain_proposals",
            "brain_red_flags",
            "brain_risk_framework",
            "brain_scoring_factors",
            "brain_scoring_meta",
            "brain_sectors",
            "brain_shadow_evaluations",
            "brain_taxonomy",
        ])
        assert table_names == expected

    def test_all_views_exist(self, conn: duckdb.DuckDBPyConnection) -> None:
        """All 11 brain views must exist after schema creation."""
        result = conn.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'main' AND table_type = 'VIEW'
            ORDER BY table_name
        """).fetchall()
        view_names = sorted([row[0] for row in result])
        expected = sorted([
            "brain_signal_effectiveness",
            "brain_signals_active",
            "brain_signals_current",
            "brain_config_current",
            "brain_coverage_matrix",
            "brain_patterns_current",
            "brain_red_flags_current",
            "brain_scoring_factors_current",
            "brain_scoring_meta_current",
            "brain_sectors_current",
            "brain_taxonomy_current",
        ])
        assert view_names == expected

    def test_schema_creation_idempotent(self, conn: duckdb.DuckDBPyConnection) -> None:
        """Running create_schema twice should not error."""
        create_schema(conn)  # Second call
        result = conn.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'main' AND table_type = 'BASE TABLE'
        """).fetchone()
        assert result is not None
        assert result[0] == 21  # All brain tables including Phase 57 brain_correlations


class TestBrainChecksViews:
    """Test brain_signals_current and brain_signals_active view logic."""

    @pytest.fixture()
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Create an in-memory DuckDB with schema."""
        connection = connect_brain_db(":memory:")
        create_schema(connection)
        return connection

    def _insert_check(
        self,
        conn: duckdb.DuckDBPyConnection,
        signal_id: str,
        version: int,
        lifecycle_state: str = "SCORING",
        name: str = "Test Check",
    ) -> None:
        """Helper to insert a check row with required fields."""
        conn.execute("""
            INSERT INTO brain_signals (
                signal_id, version, name, content_type, lifecycle_state,
                depth, execution_mode, report_section, risk_questions,
                risk_framework_layer, threshold_type, question, created_by
            ) VALUES (?, ?, ?, 'EVALUATIVE_CHECK', ?, 2, 'AUTO',
                      'financials', ['Q6'], 'risk_characteristic',
                      'tiered', 'Is this check active?', 'migration_v1')
        """, [signal_id, version, name, lifecycle_state])

    def test_current_view_returns_single_check(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Inserting one version should appear in current view."""
        self._insert_check(conn, "FIN.LIQ.position", 1)
        result = conn.execute(
            "SELECT signal_id, version FROM brain_signals_current"
        ).fetchall()
        assert len(result) == 1
        assert result[0] == ("FIN.LIQ.position", 1)

    def test_current_view_returns_latest_version(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """With two versions, current view should return only the latest."""
        self._insert_check(conn, "FIN.LIQ.position", 1, name="Version 1")
        self._insert_check(conn, "FIN.LIQ.position", 2, name="Version 2")

        result = conn.execute(
            "SELECT signal_id, version, name FROM brain_signals_current"
        ).fetchall()
        assert len(result) == 1
        assert result[0] == ("FIN.LIQ.position", 2, "Version 2")

    def test_current_view_multiple_checks(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Current view should return latest version of each distinct check."""
        self._insert_check(conn, "FIN.LIQ.position", 1)
        self._insert_check(conn, "FIN.LIQ.position", 2)
        self._insert_check(conn, "GOV.BOARD.independence", 1)

        result = conn.execute(
            "SELECT signal_id, version FROM brain_signals_current ORDER BY signal_id"
        ).fetchall()
        assert len(result) == 2
        assert result[0] == ("FIN.LIQ.position", 2)
        assert result[1] == ("GOV.BOARD.independence", 1)

    def test_active_view_excludes_retired(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Active view must exclude checks with lifecycle_state = RETIRED."""
        self._insert_check(conn, "FIN.LIQ.position", 1, lifecycle_state="SCORING")
        self._insert_check(conn, "GOV.OLD.check", 1, lifecycle_state="RETIRED")

        result = conn.execute(
            "SELECT signal_id FROM brain_signals_active"
        ).fetchall()
        assert len(result) == 1
        assert result[0][0] == "FIN.LIQ.position"

    def test_active_view_excludes_retired_latest_version(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """A check that was active but then retired should not be in active view."""
        self._insert_check(conn, "FIN.LIQ.position", 1, lifecycle_state="SCORING")
        self._insert_check(conn, "FIN.LIQ.position", 2, lifecycle_state="RETIRED")

        result = conn.execute(
            "SELECT signal_id FROM brain_signals_active"
        ).fetchall()
        assert len(result) == 0

    def test_active_includes_non_retired_states(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Active view includes SCORING, MONITORING, INVESTIGATION, BACKLOG."""
        for state in ["SCORING", "MONITORING", "INVESTIGATION", "BACKLOG"]:
            self._insert_check(conn, f"TEST.{state}.check", 1, lifecycle_state=state)

        result = conn.execute(
            "SELECT COUNT(*) FROM brain_signals_active"
        ).fetchone()
        assert result is not None
        assert result[0] == 4


class TestPresentationSpecDoContext:
    """Test PresentationSpec do_context field in brain signal schema."""

    def test_do_context_field_accepted(self) -> None:
        """PresentationSpec should accept do_context dict field."""
        from do_uw.brain.brain_signal_schema import PresentationSpec

        spec = PresentationSpec(do_context={"TRIGGERED_RED": "test"})
        assert spec.do_context == {"TRIGGERED_RED": "test"}

    def test_do_context_defaults_to_empty(self) -> None:
        """PresentationSpec without do_context should default to empty dict."""
        from do_uw.brain.brain_signal_schema import PresentationSpec

        spec = PresentationSpec()
        assert spec.do_context == {}


class TestBrainTaxonomyView:
    """Test brain_taxonomy_current view logic."""

    @pytest.fixture()
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Create an in-memory DuckDB with schema."""
        connection = connect_brain_db(":memory:")
        create_schema(connection)
        return connection

    def test_taxonomy_current_returns_latest(
        self, conn: duckdb.DuckDBPyConnection
    ) -> None:
        """Taxonomy current view returns latest version of each entity."""
        conn.execute("""
            INSERT INTO brain_taxonomy (entity_type, entity_id, version, name, description)
            VALUES ('risk_question', 'Q1', 1, 'Old question', 'Old desc')
        """)
        conn.execute("""
            INSERT INTO brain_taxonomy (entity_type, entity_id, version, name, description)
            VALUES ('risk_question', 'Q1', 2, 'Updated question', 'New desc')
        """)

        result = conn.execute("""
            SELECT entity_id, version, name FROM brain_taxonomy_current
            WHERE entity_type = 'risk_question'
        """).fetchall()
        assert len(result) == 1
        assert result[0] == ("Q1", 2, "Updated question")
