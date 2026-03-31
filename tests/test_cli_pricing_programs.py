"""Tests for the pricing programs CLI sub-app commands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from do_uw.cli import app
from do_uw.knowledge.pricing_store_programs import ProgramStore
from do_uw.models.pricing import (
    BrokerInput,
    PolicyYearInput,
    ProgramInput,
)

runner = CliRunner()

# Patch at source module for lazy imports inside CLI command functions
_PROG_STORE_PATH = "do_uw.knowledge.pricing_store_programs.ProgramStore"
_PRICING_STORE_PATH = "do_uw.knowledge.pricing_store.PricingStore"


def _patched_store() -> ProgramStore:
    """Create an in-memory ProgramStore for testing."""
    return ProgramStore(db_path=None)


class TestAddProgramCommand:
    """Test the add-program CLI command."""

    def test_add_program_minimal(self) -> None:
        """add-program with just ticker succeeds."""
        store = _patched_store()
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app,
                ["pricing", "programs", "add-program", "AAPL"],
            )
        assert result.exit_code == 0
        assert "Program #1 created for AAPL" in result.output

    def test_add_program_with_broker(self) -> None:
        """add-program with brokerage creates broker link."""
        store = _patched_store()
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app,
                [
                    "pricing", "programs", "add-program", "MSFT",
                    "--brokerage", "Marsh",
                    "--broker-name", "John Doe",
                    "--company-name", "Microsoft Corp",
                    "--anniversary-month", "6",
                    "--anniversary-day", "15",
                ],
            )
        assert result.exit_code == 0
        assert "Program #1 created for MSFT" in result.output

        # Verify broker was created
        brokers = store.list_brokers()
        assert len(brokers) == 1
        assert brokers[0].brokerage_name == "Marsh"


class TestListProgramsCommand:
    """Test the list-programs CLI command."""

    def test_list_programs_empty(self) -> None:
        """list-programs with none shows message."""
        store = _patched_store()
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app, ["pricing", "programs", "list-programs"]
            )
        assert result.exit_code == 0
        assert "No programs found" in result.output

    def test_list_programs_with_data(self) -> None:
        """list-programs shows table after creating program."""
        store = _patched_store()
        store.add_program(ProgramInput(ticker="AAPL", company_name="Apple"))
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app, ["pricing", "programs", "list-programs"]
            )
        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "Apple" in result.output


class TestProgramHistoryCommand:
    """Test the program-history CLI command."""

    def test_program_history_empty(self) -> None:
        """program-history with no data shows message."""
        store = _patched_store()
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app,
                ["pricing", "programs", "program-history", "AAPL"],
            )
        assert result.exit_code == 0
        assert "No program history" in result.output

    def test_program_history_with_data(self) -> None:
        """program-history shows table with policy years."""
        store = _patched_store()
        prog_id = store.add_program(ProgramInput(ticker="AAPL"))
        store.add_policy_year(
            prog_id,
            PolicyYearInput(
                policy_year=2024,
                total_premium=100_000.0,
                total_limit=5_000_000.0,
                retention=500_000.0,
            ),
        )
        store.add_policy_year(
            prog_id,
            PolicyYearInput(
                policy_year=2025,
                total_premium=120_000.0,
                total_limit=5_000_000.0,
                retention=750_000.0,
            ),
        )
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app,
                ["pricing", "programs", "program-history", "AAPL"],
            )
        assert result.exit_code == 0
        assert "2024" in result.output
        assert "2025" in result.output
        # YoY changes should appear
        assert "Year-over-Year" in result.output


class TestAddPolicyYearCommand:
    """Test the add-policy-year CLI command."""

    def test_add_policy_year(self) -> None:
        """add-policy-year creates year on existing program."""
        store = _patched_store()
        store.add_program(ProgramInput(ticker="AAPL"))
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app,
                [
                    "pricing", "programs", "add-policy-year",
                    "AAPL", "2025",
                    "--premium", "100000",
                    "--limit", "5000000",
                ],
            )
        assert result.exit_code == 0
        assert "Policy year 2025 added to AAPL" in result.output

    def test_add_policy_year_creates_program(self) -> None:
        """add-policy-year auto-creates program if none exists."""
        store = _patched_store()
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app,
                [
                    "pricing", "programs", "add-policy-year",
                    "NEWCO", "2025",
                ],
            )
        assert result.exit_code == 0
        assert "Created new program for NEWCO" in result.output
        assert "Policy year 2025 added to NEWCO" in result.output


class TestBrokersCommand:
    """Test the brokers CLI command."""

    def test_brokers_empty(self) -> None:
        """brokers with none shows message."""
        store = _patched_store()
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app, ["pricing", "programs", "brokers"]
            )
        assert result.exit_code == 0
        assert "No brokers found" in result.output

    def test_brokers_with_data(self) -> None:
        """brokers shows table after adding broker."""
        store = _patched_store()
        store.add_broker(
            BrokerInput(
                brokerage_name="Marsh",
                producer_name="John Doe",
                email="john@marsh.com",
            )
        )
        with patch(_PROG_STORE_PATH, return_value=store):
            result = runner.invoke(
                app, ["pricing", "programs", "brokers"]
            )
        assert result.exit_code == 0
        assert "Marsh" in result.output
        assert "John Doe" in result.output


class TestIngestCommand:
    """Test the ingest CLI command."""

    def test_ingest_command(self, tmp_path: Path) -> None:
        """ingest passes filepath to ingest_document."""
        test_file = tmp_path / "tower.xlsx"
        test_file.write_text("test content")

        mock_ingest = MagicMock(
            return_value={"layers": 5, "completeness": "PARTIAL"}
        )
        store = _patched_store()
        with (
            patch(
                "do_uw.knowledge.pricing_ingestion.ingest_document",
                mock_ingest,
            ),
            patch(_PROG_STORE_PATH, return_value=store),
        ):
            result = runner.invoke(
                app,
                [
                    "pricing", "programs", "ingest",
                    str(test_file), "AAPL",
                    "--hint", "tower spreadsheet",
                ],
            )
        assert result.exit_code == 0
        assert "Ingested tower.xlsx for AAPL" in result.output

    def test_ingest_no_api_key(self, tmp_path: Path) -> None:
        """ingest shows helpful error on RuntimeError."""
        test_file = tmp_path / "tower.xlsx"
        test_file.write_text("test content")

        mock_ingest = MagicMock(side_effect=RuntimeError("No API key"))
        store = _patched_store()
        with (
            patch(
                "do_uw.knowledge.pricing_ingestion.ingest_document",
                mock_ingest,
            ),
            patch(_PROG_STORE_PATH, return_value=store),
        ):
            result = runner.invoke(
                app,
                [
                    "pricing", "programs", "ingest",
                    str(test_file), "AAPL",
                ],
            )
        assert result.exit_code == 1
        assert "Ingestion error" in result.output

    def test_ingest_file_not_found(self) -> None:
        """ingest with missing file shows error."""
        result = runner.invoke(
            app,
            [
                "pricing", "programs", "ingest",
                "/nonexistent/file.xlsx", "AAPL",
            ],
        )
        assert result.exit_code == 1
        assert "File not found" in result.output


class TestImportCsvPartial:
    """Test import-csv with partial and enhanced data."""

    def test_import_csv_partial(self, tmp_path: Path) -> None:
        """CSV with just ticker creates programs (not quotes)."""
        csv_file = tmp_path / "partial.csv"
        csv_file.write_text("ticker\nAAPL\nMSFT\n")

        from do_uw.knowledge.pricing_store import PricingStore
        quote_store = PricingStore(db_path=None)
        prog_store = _patched_store()
        with (
            patch(_PRICING_STORE_PATH, return_value=quote_store),
            patch(_PROG_STORE_PATH, return_value=prog_store),
        ):
            result = runner.invoke(
                app, ["pricing", "import-csv", str(csv_file)]
            )
        assert result.exit_code == 0
        assert "2 programs imported" in result.output

    def test_import_csv_enhanced(self, tmp_path: Path) -> None:
        """CSV with brokerage and anniversary fields."""
        csv_file = tmp_path / "enhanced.csv"
        csv_file.write_text(
            "ticker,effective_date,brokerage,broker_name,"
            "anniversary_month,anniversary_day\n"
            "AAPL,2025-06-15,Marsh,Jane Doe,6,15\n"
        )

        from do_uw.knowledge.pricing_store import PricingStore
        quote_store = PricingStore(db_path=None)
        prog_store = _patched_store()
        with (
            patch(_PRICING_STORE_PATH, return_value=quote_store),
            patch(_PROG_STORE_PATH, return_value=prog_store),
        ):
            result = runner.invoke(
                app, ["pricing", "import-csv", str(csv_file)]
            )
        assert result.exit_code == 0
        assert "1 programs imported" in result.output

    def test_import_csv_full_still_works(self, tmp_path: Path) -> None:
        """CSV with all fields still imports as quotes."""
        csv_file = tmp_path / "full.csv"
        csv_file.write_text(
            "ticker,premium,limit,effective_date,market_cap_tier\n"
            "AAPL,500000,10000000,2025-01-15,LARGE\n"
        )

        from do_uw.knowledge.pricing_store import PricingStore
        quote_store = PricingStore(db_path=None)
        with patch(_PRICING_STORE_PATH, return_value=quote_store):
            result = runner.invoke(
                app, ["pricing", "import-csv", str(csv_file)]
            )
        assert result.exit_code == 0
        assert "1 quotes imported" in result.output
