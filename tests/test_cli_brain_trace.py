"""CLI integration tests for brain trace-chain command.

Tests the `do-uw brain trace-chain` CLI command which presents
chain validation results via Rich terminal output and JSON export.

Phase 77 Plan 02.
"""

from __future__ import annotations

import json

from typer.testing import CliRunner

from do_uw.cli import app

runner = CliRunner()


def test_trace_chain_full_table() -> None:
    """Invoke with no args -- shows summary stats and signal table."""
    result = runner.invoke(app, ["brain", "trace-chain"])
    assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
    assert "Total" in result.output
    assert "Complete" in result.output
    assert "Broken" in result.output


def test_trace_chain_single_signal() -> None:
    """Invoke with a known signal ID -- shows vertical chain detail."""
    result = runner.invoke(app, ["brain", "trace-chain", "FIN.PROFIT.revenue"])
    assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
    assert "FIN.PROFIT.revenue" in result.output
    # Should show all 4 chain link types
    assert "ACQUIRE" in result.output
    assert "EXTRACT" in result.output
    assert "ANALYZE" in result.output
    assert "RENDER" in result.output


def test_trace_chain_unknown_signal() -> None:
    """Invoke with nonexistent signal -- prints error and exits 1."""
    result = runner.invoke(app, ["brain", "trace-chain", "NONEXISTENT.SIGNAL.xyz"])
    assert result.exit_code == 1
    # Should contain an error message about not found
    assert "not found" in result.output.lower() or "unknown" in result.output.lower()


def test_trace_chain_json_export(tmp_path: object) -> None:
    """Invoke with --json flag -- writes valid JSON report."""
    import pathlib

    assert isinstance(tmp_path, pathlib.Path)
    json_path = tmp_path / "test_chain_report.json"
    result = runner.invoke(app, ["brain", "trace-chain", "--json", str(json_path)])
    assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
    assert json_path.exists(), "JSON file was not created"

    data = json.loads(json_path.read_text())
    assert "total_signals" in data
    assert "chain_complete" in data
    assert "chain_broken" in data
    assert "gap_summary" in data


def test_trace_chain_json_has_all_signals(tmp_path: object) -> None:
    """JSON results list length matches total_signals."""
    import pathlib

    assert isinstance(tmp_path, pathlib.Path)
    json_path = tmp_path / "test_chain_report2.json"
    result = runner.invoke(app, ["brain", "trace-chain", "--json", str(json_path)])
    assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"

    data = json.loads(json_path.read_text())
    assert len(data["results"]) == data["total_signals"]
