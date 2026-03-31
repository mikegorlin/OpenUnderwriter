"""Tests for the pricing CLI sub-app commands."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from do_uw.cli import app
from do_uw.knowledge.pricing_store import PricingStore
from do_uw.models.pricing import MarketCapTier, QuoteInput, QuoteStatus

runner = CliRunner()


def _patched_store() -> PricingStore:
    """Create an in-memory PricingStore for testing."""
    return PricingStore(db_path=None)


def _add_test_quotes(store: PricingStore, count: int = 5) -> None:
    """Add test quotes with varied rates to a store."""
    for i in range(count):
        qi = QuoteInput(
            ticker=f"T{i}",
            company_name=f"Company {i}",
            effective_date=datetime(2025, 6, i + 1, tzinfo=UTC),
            quote_date=datetime(2025, 6, i + 1, tzinfo=UTC),
            status=QuoteStatus.QUOTED,
            total_limit=1_000_000,
            total_premium=50_000 + i * 10_000,
            market_cap_tier=MarketCapTier.LARGE,
            sector="TECH",
            source="test",
        )
        store.add_quote(qi)


class TestAddQuoteCommand:
    """Test the add-quote CLI command."""

    def test_add_quote_command(self) -> None:
        """Add a quote via CLI and verify success output."""
        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                [
                    "pricing",
                    "add-quote",
                    "AAPL",
                    "--premium",
                    "500000",
                    "--limit",
                    "10000000",
                    "--effective",
                    "2025-01-01",
                    "--cap-tier",
                    "MEGA",
                ],
            )

        assert result.exit_code == 0
        assert "Quote #1 added for AAPL" in result.output

    def test_add_quote_with_options(self) -> None:
        """Add a quote with all optional parameters."""
        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                [
                    "pricing",
                    "add-quote",
                    "MSFT",
                    "--premium",
                    "800000",
                    "--limit",
                    "20000000",
                    "--effective",
                    "2025-06-01",
                    "--cap-tier",
                    "LARGE",
                    "--status",
                    "BOUND",
                    "--retention",
                    "1000000",
                    "--source",
                    "broker_xyz",
                    "--company-name",
                    "Microsoft Corp",
                ],
            )

        assert result.exit_code == 0
        assert "Quote #1 added for MSFT" in result.output

    def test_add_quote_invalid_status(self) -> None:
        """Invalid status shows error and exits."""
        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                [
                    "pricing",
                    "add-quote",
                    "AAPL",
                    "--premium",
                    "500000",
                    "--limit",
                    "10000000",
                    "--effective",
                    "2025-01-01",
                    "--cap-tier",
                    "MEGA",
                    "--status",
                    "INVALID",
                ],
            )

        assert result.exit_code == 1
        assert "Invalid status" in result.output

    def test_add_quote_invalid_cap_tier(self) -> None:
        """Invalid cap tier shows error and exits."""
        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                [
                    "pricing",
                    "add-quote",
                    "AAPL",
                    "--premium",
                    "500000",
                    "--limit",
                    "10000000",
                    "--effective",
                    "2025-01-01",
                    "--cap-tier",
                    "XXXL",
                ],
            )

        assert result.exit_code == 1
        assert "Invalid cap tier" in result.output


class TestListQuotesCommand:
    """Test the list-quotes CLI command."""

    def test_list_quotes_empty(self) -> None:
        """List quotes when none exist shows graceful message."""
        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app, ["pricing", "list-quotes"]
            )

        assert result.exit_code == 0
        assert "No quotes found" in result.output

    def test_list_quotes_with_data(self) -> None:
        """List quotes after adding one shows table output."""
        store = _patched_store()

        qi = QuoteInput(
            ticker="AAPL",
            company_name="Apple Inc.",
            effective_date=datetime(2025, 1, 1, tzinfo=UTC),
            quote_date=datetime(2025, 1, 1, tzinfo=UTC),
            status=QuoteStatus.QUOTED,
            total_limit=10_000_000,
            total_premium=500_000,
            market_cap_tier=MarketCapTier.MEGA,
            source="test",
        )
        store.add_quote(qi)

        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app, ["pricing", "list-quotes"]
            )

        assert result.exit_code == 0
        assert "AAPL" in result.output
        assert "QUOTED" in result.output

    def test_list_quotes_filtered(self) -> None:
        """List quotes with ticker filter."""
        store = _patched_store()

        for ticker in ["AAPL", "MSFT"]:
            qi = QuoteInput(
                ticker=ticker,
                company_name=f"{ticker} Inc.",
                effective_date=datetime(2025, 1, 1, tzinfo=UTC),
                quote_date=datetime(2025, 1, 1, tzinfo=UTC),
                status=QuoteStatus.QUOTED,
                total_limit=10_000_000,
                total_premium=500_000,
                market_cap_tier=MarketCapTier.MEGA,
                source="test",
            )
            store.add_quote(qi)

        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                ["pricing", "list-quotes", "--ticker", "AAPL"],
            )

        assert result.exit_code == 0
        assert "AAPL" in result.output


class TestMarketPositionCommand:
    """Test the market-position CLI command."""

    def test_market_position_command(self) -> None:
        """market-position with data shows statistics."""
        store = _patched_store()
        _add_test_quotes(store, count=5)

        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                [
                    "pricing",
                    "market-position",
                    "--cap-tier",
                    "LARGE",
                    "--sector",
                    "TECH",
                ],
            )

        assert result.exit_code == 0
        assert "Market Position" in result.output
        assert "Median ROL" in result.output
        assert "95% CI" in result.output

    def test_market_position_insufficient(self) -> None:
        """market-position with no data shows INSUFFICIENT message."""
        store = _patched_store()

        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                ["pricing", "market-position"],
            )

        assert result.exit_code == 0
        assert "INSUFFICIENT" in result.output


class TestTrendsCommand:
    """Test the trends CLI command."""

    def test_trends_command(self) -> None:
        """trends with data shows period table."""
        store = _patched_store()

        # Add quotes across two half-years
        for i, month in enumerate([1, 3, 5, 7, 9, 11]):
            qi = QuoteInput(
                ticker=f"T{i}",
                company_name=f"Company {i}",
                effective_date=datetime(2025, month, 1, tzinfo=UTC),
                quote_date=datetime(2025, month, 1, tzinfo=UTC),
                status=QuoteStatus.QUOTED,
                total_limit=1_000_000,
                total_premium=50_000 + i * 5_000,
                market_cap_tier=MarketCapTier.LARGE,
                sector="TECH",
                source="test",
            )
            store.add_quote(qi)

        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                [
                    "pricing",
                    "trends",
                    "--cap-tier",
                    "LARGE",
                    "--sector",
                    "TECH",
                ],
            )

        assert result.exit_code == 0
        assert "Market Trends" in result.output
        assert "2025-H1" in result.output
        assert "2025-H2" in result.output

    def test_trends_no_data(self) -> None:
        """trends with no data shows message."""
        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app, ["pricing", "trends"]
            )

        assert result.exit_code == 0
        assert "No trend data" in result.output


class TestImportCsvCommand:
    """Test the import-csv CLI command."""

    def test_import_csv_command(self, tmp_path: Path) -> None:
        """CSV with valid rows imports successfully."""
        csv_file = tmp_path / "quotes.csv"
        csv_file.write_text(
            "ticker,premium,limit,effective_date,market_cap_tier\n"
            "AAPL,500000,10000000,2025-01-15,LARGE\n"
            "MSFT,800000,20000000,2025-03-01,MEGA\n"
            "GOOG,600000,15000000,2025-06-01,LARGE\n"
        )

        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                ["pricing", "import-csv", str(csv_file)],
            )

        assert result.exit_code == 0
        assert "3 quotes imported" in result.output
        assert "0 errors" in result.output

        # Verify quotes were actually stored
        quotes = store.list_quotes()
        assert len(quotes) == 3

    def test_import_csv_dry_run(self, tmp_path: Path) -> None:
        """--dry-run validates but does not persist."""
        csv_file = tmp_path / "quotes.csv"
        csv_file.write_text(
            "ticker,premium,limit,effective_date,market_cap_tier\n"
            "AAPL,500000,10000000,2025-01-15,LARGE\n"
        )

        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                [
                    "pricing",
                    "import-csv",
                    str(csv_file),
                    "--dry-run",
                ],
            )

        assert result.exit_code == 0
        assert "1 quotes validated" in result.output
        # No data persisted in dry run (store was never used)
        assert len(store.list_quotes()) == 0

    def test_import_csv_missing_ticker_column(self, tmp_path: Path) -> None:
        """CSV missing required ticker column shows error."""
        csv_file = tmp_path / "bad.csv"
        csv_file.write_text(
            "premium,limit\n"
            "500000,10000000\n"
        )

        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                ["pricing", "import-csv", str(csv_file)],
            )

        assert result.exit_code == 1
        assert "Missing required columns" in result.output

    def test_import_csv_date_formats(self, tmp_path: Path) -> None:
        """CSV handles both YYYY-MM-DD and MM/DD/YYYY dates."""
        csv_file = tmp_path / "dates.csv"
        csv_file.write_text(
            "ticker,premium,limit,effective_date,market_cap_tier\n"
            "AAPL,500000,10000000,2025-01-15,LARGE\n"
            "MSFT,500000,10000000,01/15/2025,LARGE\n"
        )

        store = _patched_store()
        with patch(
            "do_uw.knowledge.pricing_store.PricingStore", return_value=store
        ):
            result = runner.invoke(
                app,
                ["pricing", "import-csv", str(csv_file)],
            )

        assert result.exit_code == 0
        assert "2 quotes imported" in result.output
