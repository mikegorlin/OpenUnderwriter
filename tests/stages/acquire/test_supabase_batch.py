"""Tests for batch peer SCA query in supabase_litigation client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_empty_tickers_returns_empty() -> None:
    """query_peer_sca_filings([]) returns [] immediately."""
    from do_uw.stages.acquire.clients.supabase_litigation import (
        query_peer_sca_filings,
    )

    assert query_peer_sca_filings([]) == []


def test_missing_supabase_key_logs_warning() -> None:
    """Missing SUPABASE_KEY logs warning and returns []."""
    from do_uw.stages.acquire.clients.supabase_litigation import (
        query_peer_sca_filings,
    )

    with patch.dict("os.environ", {}, clear=True):
        result = query_peer_sca_filings(["AAPL", "MSFT"])
    assert result == []


def test_batch_query_url_uses_in_filter() -> None:
    """Batch query uses Supabase in. filter for multiple tickers."""
    from do_uw.stages.acquire.clients.supabase_litigation import (
        query_peer_sca_filings,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "company_name": "Apple Inc",
            "ticker": "AAPL",
            "filing_date": "2024-01-15",
            "case_status": "active",
            "settlement_amount_m": None,
            "allegation_accounting": True,
            "allegation_insider_trading": False,
            "allegation_earnings": False,
            "allegation_merger": False,
            "allegation_ipo_offering": False,
        },
    ]

    with (
        patch.dict("os.environ", {"SUPABASE_KEY": "test-key"}),
        patch("httpx.get", return_value=mock_response) as mock_get,
    ):
        result = query_peer_sca_filings(["AAPL", "MSFT"])

    # Verify the URL contains the in. filter
    call_url = mock_get.call_args[0][0]
    assert "ticker=in." in call_url
    assert "AAPL" in call_url
    assert "MSFT" in call_url

    # Returns PeerSCARecord instances
    assert len(result) >= 1
    assert result[0].ticker == "AAPL"


def test_batch_query_returns_peer_sca_records() -> None:
    """Results are PeerSCARecord model instances."""
    from do_uw.models.company_intelligence import PeerSCARecord
    from do_uw.stages.acquire.clients.supabase_litigation import (
        query_peer_sca_filings,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "company_name": "Microsoft Corp",
            "ticker": "MSFT",
            "filing_date": "2023-06-01",
            "case_status": "settled",
            "settlement_amount_m": 25.0,
            "allegation_accounting": False,
            "allegation_earnings": True,
        },
    ]

    with (
        patch.dict("os.environ", {"SUPABASE_KEY": "test-key"}),
        patch("httpx.get", return_value=mock_response),
    ):
        result = query_peer_sca_filings(["MSFT"])

    assert len(result) == 1
    assert isinstance(result[0], PeerSCARecord)
    assert result[0].ticker == "MSFT"
    assert result[0].settlement_amount_m == 25.0


def test_batch_query_single_http_request() -> None:
    """Batch query makes only one HTTP request regardless of ticker count."""
    from do_uw.stages.acquire.clients.supabase_litigation import (
        query_peer_sca_filings,
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = []

    with (
        patch.dict("os.environ", {"SUPABASE_KEY": "test-key"}),
        patch("httpx.get", return_value=mock_response) as mock_get,
    ):
        query_peer_sca_filings(["AAPL", "MSFT", "GOOG", "META", "AMZN"])

    assert mock_get.call_count == 1
