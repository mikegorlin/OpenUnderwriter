"""Tests for 2-year history acquisition in market_client.

Verifies that _collect_yfinance_data returns history_2y,
sector_history_2y, and spy_history_2y keys alongside existing
1y/5y keys.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_yfinance():
    """Mock yfinance module for testing _collect_yfinance_data."""
    with patch(
        "do_uw.stages.acquire.clients.market_client.yf",
        create=True,
    ) as mock_yf:
        # Create a mock ticker that returns valid data for all calls.
        mock_ticker = MagicMock()

        # info returns a dict with sector for ETF resolution.
        mock_ticker.info = {"sector": "Technology", "currentPrice": 100.0}

        # history returns a non-empty DataFrame mock.
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.reset_index.return_value = mock_df
        mock_df.columns = ["Date", "Close"]
        mock_df.to_dict.return_value = {
            "Date": ["2025-01-01", "2025-01-02"],
            "Close": [100.0, 101.0],
        }
        mock_df.__iter__ = MagicMock(return_value=iter(["Date", "Close"]))
        mock_df.__getitem__ = MagicMock(return_value=mock_df)
        mock_ticker.history.return_value = mock_df

        # Other attributes return empty/minimal data.
        mock_ticker.insider_transactions = MagicMock(empty=True)
        mock_ticker.institutional_holders = MagicMock(empty=True)
        mock_ticker.recommendations = MagicMock(empty=True)
        mock_ticker.news = []
        mock_ticker.income_stmt = MagicMock(empty=True)
        mock_ticker.quarterly_income_stmt = MagicMock(empty=True)
        mock_ticker.balance_sheet = MagicMock(empty=True)
        mock_ticker.quarterly_balance_sheet = MagicMock(empty=True)
        mock_ticker.cashflow = MagicMock(empty=True)
        mock_ticker.quarterly_cashflow = MagicMock(empty=True)
        mock_ticker.major_holders = MagicMock(empty=True)
        mock_ticker.mutualfund_holders = MagicMock(empty=True)
        mock_ticker.dividends = MagicMock(empty=True)
        mock_ticker.splits = MagicMock(empty=True)
        mock_ticker.calendar = {}
        mock_ticker.earnings_history = MagicMock(empty=True)
        mock_ticker.eps_trend = MagicMock(empty=True)
        mock_ticker.eps_revisions = MagicMock(empty=True)
        mock_ticker.growth_estimates = MagicMock(empty=True)
        mock_ticker.revenue_estimate = MagicMock(empty=True)
        mock_ticker.earnings_estimate = MagicMock(empty=True)
        mock_ticker.upgrades_downgrades = MagicMock(empty=True)

        mock_yf.Ticker.return_value = mock_ticker
        yield mock_yf, mock_ticker


@patch("do_uw.stages.acquire.clients.market_client._resolve_sector_etf")
def test_collect_yfinance_data_has_history_2y(mock_resolve, mock_yfinance):
    """_collect_yfinance_data result contains history_2y key."""
    mock_resolve.return_value = "XLK"
    mock_yf, _ = mock_yfinance

    with patch("do_uw.stages.acquire.clients.market_client.yf", mock_yf):
        from do_uw.stages.acquire.clients.market_client import (
            _collect_yfinance_data,
        )

        result = _collect_yfinance_data("AAPL")

    assert "history_2y" in result, "history_2y key missing from result"
    assert result["history_2y"], "history_2y should not be empty"


@patch("do_uw.stages.acquire.clients.market_client._resolve_sector_etf")
def test_collect_yfinance_data_has_sector_history_2y(mock_resolve, mock_yfinance):
    """_collect_yfinance_data result contains sector_history_2y key."""
    mock_resolve.return_value = "XLK"
    mock_yf, _ = mock_yfinance

    with patch("do_uw.stages.acquire.clients.market_client.yf", mock_yf):
        from do_uw.stages.acquire.clients.market_client import (
            _collect_yfinance_data,
        )

        result = _collect_yfinance_data("AAPL")

    assert "sector_history_2y" in result, "sector_history_2y key missing"


@patch("do_uw.stages.acquire.clients.market_client._resolve_sector_etf")
def test_collect_yfinance_data_has_spy_history_2y(mock_resolve, mock_yfinance):
    """_collect_yfinance_data result contains spy_history_2y key."""
    mock_resolve.return_value = "XLK"
    mock_yf, _ = mock_yfinance

    with patch("do_uw.stages.acquire.clients.market_client.yf", mock_yf):
        from do_uw.stages.acquire.clients.market_client import (
            _collect_yfinance_data,
        )

        result = _collect_yfinance_data("AAPL")

    assert "spy_history_2y" in result, "spy_history_2y key missing"
