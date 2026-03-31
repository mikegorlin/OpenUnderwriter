"""Tests for inventory-based incremental acquisition.

Verifies that the ACQUIRE stage checks existing state.acquired_data
before dispatching clients, skipping sources that already have data.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.state import AcquiredData
from do_uw.stages.acquire.inventory import AcquisitionInventory, check_inventory


class TestCheckInventoryEmpty:
    """check_inventory with empty/None AcquiredData returns all needed."""

    def test_none_acquired_returns_all_needed(self) -> None:
        inv = check_inventory(None)
        assert inv.needs_sec_filings is True
        assert inv.needs_market_data is True
        assert inv.needs_litigation is True
        assert inv.needs_news is True
        assert inv.needs_blind_spot is True
        assert inv.needs_patents is True
        assert inv.needs_logo is True

    def test_empty_acquired_returns_all_needed(self) -> None:
        acquired = AcquiredData()
        inv = check_inventory(acquired)
        assert inv.needs_sec_filings is True
        assert inv.needs_market_data is True
        assert inv.needs_litigation is True
        assert inv.needs_news is True

    def test_skip_reasons_empty_for_new_state(self) -> None:
        inv = check_inventory(None)
        assert inv.skip_reasons == {}


class TestCheckInventoryPopulated:
    """check_inventory with populated data marks sources complete."""

    def test_sec_filings_complete(self) -> None:
        acquired = AcquiredData(
            filing_documents={
                "10-K": [{"accession": "a1", "full_text": "text"}],
                "DEF 14A": [{"accession": "a2", "full_text": "text"}],
            }
        )
        inv = check_inventory(acquired)
        assert inv.needs_sec_filings is False
        assert "sec_filings" in inv.skip_reasons

    def test_market_data_complete(self) -> None:
        acquired = AcquiredData(
            market_data={"history_1y": {"close": [100, 101]}}
        )
        inv = check_inventory(acquired)
        assert inv.needs_market_data is False
        assert "market_data" in inv.skip_reasons

    def test_litigation_complete(self) -> None:
        acquired = AcquiredData(
            litigation_data={"scac": [{"case": "test"}]}
        )
        inv = check_inventory(acquired)
        assert inv.needs_litigation is False
        assert "litigation" in inv.skip_reasons

    def test_news_complete(self) -> None:
        acquired = AcquiredData(
            web_search_results={"query1": [{"title": "News"}]}
        )
        inv = check_inventory(acquired)
        assert inv.needs_news is False
        assert "news" in inv.skip_reasons

    def test_blind_spot_complete(self) -> None:
        acquired = AcquiredData(
            blind_spot_results={"pre_structured": {"risk": []}}
        )
        inv = check_inventory(acquired)
        assert inv.needs_blind_spot is False

    def test_patents_complete(self) -> None:
        acquired = AcquiredData(
            patent_data=[{"title": "AI Patent"}]
        )
        inv = check_inventory(acquired)
        assert inv.needs_patents is False

    def test_logo_complete(self) -> None:
        acquired = AcquiredData(company_logo_b64="abc123base64")
        inv = check_inventory(acquired)
        assert inv.needs_logo is False


class TestCheckInventoryPartial:
    """check_inventory with partial data marks only complete sources."""

    def test_partial_filings_still_needed(self) -> None:
        """Single form type with 1 doc is not enough (need >= 2 types)."""
        acquired = AcquiredData(
            filing_documents={
                "10-K": [{"accession": "a1", "full_text": "text"}],
            }
        )
        inv = check_inventory(acquired)
        assert inv.needs_sec_filings is True

    def test_market_without_history_still_needed(self) -> None:
        """Market data without history_1y or stock_info still needed."""
        acquired = AcquiredData(
            market_data={"some_other_key": "value"}
        )
        inv = check_inventory(acquired)
        assert inv.needs_market_data is True

    def test_mixed_complete_and_incomplete(self) -> None:
        """Some sources complete, others not."""
        acquired = AcquiredData(
            market_data={"stock_info": {"ticker": "AAPL"}},
            litigation_data={"scac": [{"case": "test"}]},
            # No filings, no news
        )
        inv = check_inventory(acquired)
        assert inv.needs_sec_filings is True
        assert inv.needs_market_data is False
        assert inv.needs_litigation is False
        assert inv.needs_news is True


class TestOrchestratorUsesInventory:
    """Orchestrator.run() skips clients when inventory says complete."""

    @patch("do_uw.stages.acquire.orchestrator.check_inventory")
    @patch("do_uw.stages.acquire.orchestrator._run_discovery_hook")
    def test_skips_structured_when_all_complete(
        self, mock_discovery: MagicMock, mock_check: MagicMock
    ) -> None:
        """When inventory says all complete, orchestrator copies data."""
        from do_uw.stages.acquire.orchestrator import AcquisitionOrchestrator

        # Create mock inventory that says everything is complete
        inv = AcquisitionInventory(
            needs_sec_filings=False,
            needs_market_data=False,
            needs_litigation=False,
            needs_news=False,
            needs_blind_spot=False,
            needs_courtlistener=False,
            needs_patents=False,
            needs_logo=False,
            needs_frames=False,
        )
        mock_check.return_value = inv

        # Create state with existing acquired data
        existing_acquired = AcquiredData(
            filing_documents={"10-K": [{"accession": "a1", "full_text": "text"}]},
            market_data={"history_1y": {}},
            litigation_data={"scac": []},
            web_search_results={"q1": []},
            blind_spot_results={"pre": {}},
            patent_data=[{"title": "p"}],
            company_logo_b64="logo123",
        )

        state = MagicMock()
        state.ticker = "TEST"
        state.company = MagicMock()
        state.company.identity.legal_name.value = "Test Corp"
        state.company.identity.cik.value = "12345"
        state.acquired_data = existing_acquired

        orchestrator = AcquisitionOrchestrator()
        result = orchestrator.run(state)

        # Verify data was copied from existing state
        assert result.market_data == existing_acquired.market_data
        assert result.litigation_data == existing_acquired.litigation_data
        assert result.web_search_results == existing_acquired.web_search_results
