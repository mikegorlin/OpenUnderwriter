"""Tests for cost report generation and formatting.

Verifies report generation from output directories, Rich table
rendering, and JSON round-trip serialization.
"""

from __future__ import annotations

import json
from pathlib import Path

from do_uw.validation.cost_report import (
    CostReport,
    CostReportEntry,
    generate_cost_report,
    load_cost_report,
    print_cost_report,
    save_cost_report,
)


def test_generate_cost_report_empty(tmp_path: Path) -> None:
    """Empty output directory produces empty report."""
    report = generate_cost_report(tmp_path)
    assert report.entries == []
    assert report.grand_total_usd == 0.0
    assert report.by_filing_type_total == {}


def test_generate_cost_report_nonexistent(tmp_path: Path) -> None:
    """Non-existent output directory produces empty report."""
    missing = tmp_path / "does_not_exist"
    report = generate_cost_report(missing)
    assert report.entries == []


def test_generate_cost_report_skips_hidden_dirs(
    tmp_path: Path,
) -> None:
    """Hidden directories (like .validation_checkpoint.json dir) are skipped."""
    hidden = tmp_path / ".hidden"
    hidden.mkdir()
    (hidden / "state.json").write_text("{}", encoding="utf-8")

    report = generate_cost_report(tmp_path)
    assert report.entries == []


def test_generate_cost_report_skips_non_state(
    tmp_path: Path,
) -> None:
    """Ticker directories without state.json are skipped."""
    ticker_dir = tmp_path / "AAPL"
    ticker_dir.mkdir()
    # No state.json file

    report = generate_cost_report(tmp_path)
    assert report.entries == []


def test_print_cost_report_formatting(capsys: object) -> None:
    """Cost report table renders without errors."""
    report = CostReport(
        entries=[
            CostReportEntry(
                ticker="AAPL",
                total_cost_usd=0.1234,
                duration_seconds=45.3,
                by_filing_type={"10-K": 0.0800, "DEF 14A": 0.0434},
            ),
            CostReportEntry(
                ticker="MSFT",
                total_cost_usd=0.0987,
                duration_seconds=38.1,
                by_filing_type={"10-K": 0.0987},
            ),
        ],
        grand_total_usd=0.2221,
        by_filing_type_total={"10-K": 0.1787, "DEF 14A": 0.0434},
    )

    # Should not raise
    print_cost_report(report)


def test_save_cost_report_json(tmp_path: Path) -> None:
    """Cost report round-trips through JSON serialization."""
    report = CostReport(
        entries=[
            CostReportEntry(
                ticker="TSLA",
                total_cost_usd=0.5000,
                duration_seconds=60.0,
                by_filing_type={"10-K": 0.3000, "8-K": 0.2000},
            ),
        ],
        grand_total_usd=0.5000,
        by_filing_type_total={"10-K": 0.3000, "8-K": 0.2000},
    )

    path = tmp_path / "cost_report.json"
    save_cost_report(report, path)
    assert path.exists()

    # Verify JSON structure
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["grand_total_usd"] == 0.5
    assert len(data["entries"]) == 1
    assert data["entries"][0]["ticker"] == "TSLA"
    assert data["entries"][0]["by_filing_type"]["10-K"] == 0.3


def test_load_cost_report_round_trip(tmp_path: Path) -> None:
    """load_cost_report deserializes save_cost_report output."""
    original = CostReport(
        entries=[
            CostReportEntry(
                ticker="GOOG",
                total_cost_usd=0.2500,
                duration_seconds=30.0,
                by_filing_type={"10-K": 0.2500},
            ),
        ],
        grand_total_usd=0.2500,
        by_filing_type_total={"10-K": 0.2500},
    )

    path = tmp_path / "report.json"
    save_cost_report(original, path)
    loaded = load_cost_report(path)

    assert loaded.grand_total_usd == original.grand_total_usd
    assert len(loaded.entries) == len(original.entries)
    assert loaded.entries[0].ticker == "GOOG"
    assert loaded.entries[0].by_filing_type == {"10-K": 0.2500}


def test_load_cost_report_not_found(tmp_path: Path) -> None:
    """load_cost_report raises FileNotFoundError for missing file."""
    import pytest

    with pytest.raises(FileNotFoundError):
        load_cost_report(tmp_path / "missing.json")


def test_cost_report_entry_defaults() -> None:
    """CostReportEntry has sensible defaults."""
    entry = CostReportEntry(
        ticker="TEST",
        total_cost_usd=0.0,
        duration_seconds=0.0,
    )
    assert entry.by_filing_type == {}


def test_empty_report_print() -> None:
    """Empty report renders without errors."""
    report = CostReport()
    print_cost_report(report)
