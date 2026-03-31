"""Tests for the Brain CLI sub-app commands.

Each test mocks BrainLoader or module-level functions to avoid requiring
a live brain.duckdb database. Tests confirm exit code 0 and basic
output content for all commands.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import duckdb
from typer.testing import CliRunner

from do_uw.cli import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_file_brain_db(db_path: Path) -> None:
    """Create a file-backed DuckDB with brain schema and test data."""
    from do_uw.brain.brain_schema import create_schema

    conn = duckdb.connect(str(db_path))
    create_schema(conn)

    conn.execute(
        """INSERT INTO brain_signals (
            signal_id, version, name, content_type, lifecycle_state,
            depth, execution_mode, report_section, risk_questions,
            risk_framework_layer, threshold_type, question,
            created_by, change_description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            "TEST.check_1", 1, "Test Check", "EVALUATIVE_CHECK", "SCORING",
            2, "AUTO", "company", [], "risk_modifier", "tiered",
            "Test?", "test", "test",
        ],
    )
    conn.close()


# Mock targets -- functions are imported inside CLI functions from brain_unified_loader
_UL = "do_uw.brain.brain_unified_loader"


# ---------------------------------------------------------------------------
# Tests: brain status
# ---------------------------------------------------------------------------


class TestBrainStatus:
    """Test the brain status CLI command."""

    def test_status_with_data(self, tmp_path: Path) -> None:
        """Status command with valid signals shows summary."""
        mock_signals = {
            "signals": [
                {
                    "id": "TEST.check_1",
                    "name": "Test Check",
                    "content_type": "EVALUATIVE_CHECK",
                    "report_section": "company",
                },
            ],
            "total_signals": 1,
        }

        with patch(
            f"{_UL}.load_signals", return_value=mock_signals
        ), patch(
            f"{_UL}.load_taxonomy", return_value={}
        ), patch(
            f"{_UL}.load_backlog", return_value=[]
        ):
            result = runner.invoke(app, ["brain", "status"])

        assert result.exit_code == 0
        assert "Brain Status" in result.output

    def test_status_missing_db(self, tmp_path: Path) -> None:
        """Status command works even without DuckDB (YAML is primary)."""
        mock_signals = {
            "signals": [],
            "total_signals": 0,
        }
        missing = tmp_path / "nope.duckdb"

        with patch(
            "do_uw.cli._ensure_brain_db",
        ), patch(
            f"{_UL}.load_signals", return_value=mock_signals
        ), patch(
            f"{_UL}.load_taxonomy", return_value={}
        ), patch(
            f"{_UL}.load_backlog", return_value=[]
        ), patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=missing,
        ):
            result = runner.invoke(app, ["brain", "status"])

        # Status now reads from YAML, so it works even without DuckDB
        assert result.exit_code == 0
        assert "Brain Status" in result.output


# ---------------------------------------------------------------------------
# Tests: brain gaps
# ---------------------------------------------------------------------------


class TestBrainGaps:
    """Test the brain gaps CLI command."""

    def test_gaps_default(self) -> None:
        """Gaps command produces output with default filters."""
        mock_signals = {
            "signals": [
                {
                    "id": "TEST.check_1",
                    "name": "Test",
                    "execution_mode": "AUTO",
                    "required_data": ["SEC_10K"],
                    "data_locations": {},
                    "content_type": "EVALUATIVE_CHECK",
                    "depth": 2,
                },
            ]
        }

        with patch(
            f"{_UL}.load_signals", return_value=mock_signals
        ):
            result = runner.invoke(app, ["brain", "gaps"])

        assert result.exit_code == 0
        assert "Pipeline Gap Report" in result.output

    def test_gaps_severity_filter(self) -> None:
        """Gaps command with --severity CRITICAL filters output."""
        mock_signals = {"signals": []}

        with patch(
            f"{_UL}.load_signals", return_value=mock_signals
        ):
            result = runner.invoke(
                app, ["brain", "gaps", "--severity", "CRITICAL"]
            )

        assert result.exit_code == 0
        assert "Pipeline Gap Report" in result.output


# ---------------------------------------------------------------------------
# Tests: brain effectiveness
# ---------------------------------------------------------------------------


class TestBrainEffectiveness:
    """Test the brain effectiveness CLI command."""

    def test_effectiveness_empty(self, tmp_path: Path) -> None:
        """Effectiveness with empty DB shows report."""
        db_path = tmp_path / "brain.duckdb"
        _create_file_brain_db(db_path)

        with patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=db_path,
        ):
            result = runner.invoke(app, ["brain", "effectiveness"])

        assert result.exit_code == 0
        assert "Check Effectiveness Report" in result.output

    def test_effectiveness_missing_db(self, tmp_path: Path) -> None:
        """Effectiveness without DB exits with error."""
        missing = tmp_path / "nope.duckdb"
        with patch(
            "do_uw.cli._ensure_brain_db",
        ), patch(
            "do_uw.brain.brain_schema.get_brain_db_path",
            return_value=missing,
        ):
            result = runner.invoke(app, ["brain", "effectiveness"])

        assert result.exit_code == 1
        assert "not found" in result.output


# ---------------------------------------------------------------------------
# Tests: brain changelog
# ---------------------------------------------------------------------------


class TestBrainChangelog:
    """Test the brain changelog CLI command."""

    def test_changelog_empty(self) -> None:
        """Changelog with no entries shows message."""
        mock_writer = MagicMock()
        mock_writer.get_changelog.return_value = []

        with patch(
            "do_uw.brain.brain_writer.BrainWriter", return_value=mock_writer
        ):
            result = runner.invoke(app, ["brain", "changelog"])

        assert result.exit_code == 0
        assert "No changelog entries" in result.output

    def test_changelog_with_data(self) -> None:
        """Changelog with entries shows table."""
        mock_writer = MagicMock()
        mock_writer.get_changelog.return_value = [
            {
                "changelog_id": 1,
                "signal_id": "TEST.check_1",
                "old_version": None,
                "new_version": 1,
                "change_type": "CREATED",
                "change_description": "Initial creation",
                "changed_by": "test",
                "changed_at": "2026-01-01T00:00:00",
            },
        ]

        with patch(
            "do_uw.brain.brain_writer.BrainWriter", return_value=mock_writer
        ):
            result = runner.invoke(app, ["brain", "changelog", "--limit", "5"])

        assert result.exit_code == 0
        assert "Brain Changelog" in result.output
        assert "TEST.check_1" in result.output

    def test_changelog_filter_check(self) -> None:
        """Changelog with --check filter passes to writer."""
        mock_writer = MagicMock()
        mock_writer.get_changelog.return_value = []

        with patch(
            "do_uw.brain.brain_writer.BrainWriter", return_value=mock_writer
        ):
            result = runner.invoke(
                app, ["brain", "changelog", "--check", "TEST.check_1"]
            )

        assert result.exit_code == 0
        mock_writer.get_changelog.assert_called_once_with(
            signal_id="TEST.check_1", limit=50
        )


# ---------------------------------------------------------------------------
# Tests: brain backlog
# ---------------------------------------------------------------------------


class TestBrainBacklog:
    """Test the brain backlog CLI command."""

    def test_backlog_empty(self) -> None:
        """Backlog with no items shows message."""
        with patch(
            f"{_UL}.load_backlog", return_value=[]
        ):
            result = runner.invoke(app, ["brain", "backlog"])

        assert result.exit_code == 0
        assert "No open backlog items" in result.output

    def test_backlog_with_items(self) -> None:
        """Backlog with items shows table."""
        mock_items = [
            {
                "backlog_id": "BL-001",
                "title": "Add insider trading check",
                "description": "Need this check",
                "rationale": "Risk gap",
                "risk_questions": ["RQ-2.1"],
                "hazards": [],
                "priority": "HIGH",
                "gap_reference": None,
                "estimated_effort": "M",
                "status": "OPEN",
                "data_available": False,
            },
        ]

        with patch(
            f"{_UL}.load_backlog", return_value=mock_items
        ):
            result = runner.invoke(app, ["brain", "backlog"])

        assert result.exit_code == 0
        assert "Brain Backlog" in result.output
        assert "BL-001" in result.output


# ---------------------------------------------------------------------------
# Tests: brain export-docs
# ---------------------------------------------------------------------------


class TestBrainExportDocs:
    """Test the brain export-docs CLI command."""

    def test_export_docs_stdout(self) -> None:
        """Export docs to stdout produces Markdown."""
        mock_signals = {
            "signals": [
                {
                    "id": "TEST.COMPANY.check_1",
                    "name": "Test Check",
                    "content_type": "EVALUATIVE_CHECK",
                    "report_section": "company",
                    "risk_questions": [],
                    "threshold": {
                        "type": "tiered",
                        "red": "bad value",
                        "yellow": "warning value",
                        "clear": "good value",
                    },
                },
            ],
            "total_signals": 1,
        }

        with patch(
            f"{_UL}.load_signals", return_value=mock_signals
        ):
            result = runner.invoke(app, ["brain", "export-docs"])

        assert result.exit_code == 0
        assert "Brain Check Definitions" in result.output
        assert "TEST.COMPANY.check_1" in result.output

    def test_export_docs_to_file(self, tmp_path: Path) -> None:
        """Export docs to file creates Markdown file."""
        output_file = tmp_path / "export.md"
        mock_signals = {
            "signals": [
                {
                    "id": "TEST.FIN.check_2",
                    "name": "Financial Check",
                    "content_type": "EVALUATIVE_CHECK",
                    "report_section": "financial",
                    "risk_questions": ["RQ-3.1"],
                    "threshold": {
                        "type": "tiered",
                        "red": "bad",
                        "yellow": "",
                        "clear": "good",
                    },
                },
            ],
            "total_signals": 1,
        }

        with patch(
            f"{_UL}.load_signals", return_value=mock_signals
        ):
            result = runner.invoke(
                app, ["brain", "export-docs", "--output", str(output_file)]
            )

        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Brain Check Definitions" in content
        assert "TEST.FIN.check_2" in content

    def test_export_docs_empty(self) -> None:
        """Export docs with no checks shows message."""
        mock_signals = {"signals": [], "total_signals": 0}

        with patch(
            f"{_UL}.load_signals", return_value=mock_signals
        ):
            result = runner.invoke(app, ["brain", "export-docs"])

        assert result.exit_code == 0
        assert "No active checks" in result.output


# ---------------------------------------------------------------------------
# Tests: brain backtest
# ---------------------------------------------------------------------------


class TestBrainBacktest:
    """Test the brain backtest CLI command."""

    def test_backtest_missing_file(self, tmp_path: Path) -> None:
        """Backtest with non-existent file exits with error."""
        missing = tmp_path / "nope.json"
        result = runner.invoke(
            app, ["brain", "backtest", str(missing)]
        )

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_backtest_with_mock(self, tmp_path: Path) -> None:
        """Backtest delegates to run_backtest and displays result."""
        from do_uw.knowledge.backtest import BacktestResult

        state_file = tmp_path / "state.json"
        state_file.write_text("{}")  # Placeholder

        mock_result = BacktestResult(
            ticker="AAPL",
            state_path=str(state_file),
            state_date="2026-01-15",
            checks_executed=381,
            triggered=45,
            clear=200,
            skipped=100,
            info=36,
        )

        with patch(
            "do_uw.knowledge.backtest.run_backtest", return_value=mock_result
        ):
            result = runner.invoke(
                app,
                ["brain", "backtest", str(state_file), "--no-record"],
            )

        assert result.exit_code == 0
        assert "Backtest Result: AAPL" in result.output
        assert "381" in result.output
        assert "45" in result.output


# ---------------------------------------------------------------------------
# Tests: brain --help
# ---------------------------------------------------------------------------


class TestBrainHelp:
    """Test the brain help output."""

    def test_brain_help_shows_all_commands(self) -> None:
        """brain --help lists all 7 sub-commands."""
        result = runner.invoke(app, ["brain", "--help"])

        assert result.exit_code == 0
        for cmd in [
            "status",
            "gaps",
            "effectiveness",
            "changelog",
            "backlog",
            "export-docs",
            "backtest",
        ]:
            assert cmd in result.output, f"Command '{cmd}' not found in help output"
