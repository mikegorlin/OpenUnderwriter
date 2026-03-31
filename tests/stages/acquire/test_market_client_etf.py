"""Tests for sector ETF resolution in market_client.py.

Verifies _resolve_sector_etf() correctly maps yfinance sector names
to primary sector ETF tickers via brain/sectors.json lookup.
"""

from __future__ import annotations

from do_uw.stages.acquire.clients.market_client import _resolve_sector_etf


class TestResolveSectorEtf:
    """Sector ETF resolution from yfinance sector names."""

    def test_resolve_sector_etf_technology(self) -> None:
        """Technology -> XLK via TECH code."""
        assert _resolve_sector_etf("Technology") == "XLK"

    def test_resolve_sector_etf_healthcare(self) -> None:
        """Healthcare -> XLV via HLTH code."""
        assert _resolve_sector_etf("Healthcare") == "XLV"

    def test_resolve_sector_etf_financial(self) -> None:
        """Financial Services -> XLF via FINS code."""
        assert _resolve_sector_etf("Financial Services") == "XLF"

    def test_resolve_sector_etf_industrials(self) -> None:
        """Industrials -> XLI via INDU code."""
        assert _resolve_sector_etf("Industrials") == "XLI"

    def test_resolve_sector_etf_energy(self) -> None:
        """Energy -> XLE via ENGY code."""
        assert _resolve_sector_etf("Energy") == "XLE"

    def test_resolve_sector_etf_consumer_cyclical(self) -> None:
        """Consumer Cyclical -> XLY via CONS code."""
        assert _resolve_sector_etf("Consumer Cyclical") == "XLY"

    def test_resolve_sector_etf_consumer_defensive(self) -> None:
        """Consumer Defensive -> XLP via STPL code."""
        assert _resolve_sector_etf("Consumer Defensive") == "XLP"

    def test_resolve_sector_etf_basic_materials(self) -> None:
        """Basic Materials -> XLB via MATL code."""
        assert _resolve_sector_etf("Basic Materials") == "XLB"

    def test_resolve_sector_etf_utilities(self) -> None:
        """Utilities -> XLU via UTIL code."""
        assert _resolve_sector_etf("Utilities") == "XLU"

    def test_resolve_sector_etf_real_estate(self) -> None:
        """Real Estate -> XLRE via REIT code."""
        assert _resolve_sector_etf("Real Estate") == "XLRE"

    def test_resolve_sector_etf_communication(self) -> None:
        """Communication Services -> XLC via COMM code."""
        assert _resolve_sector_etf("Communication Services") == "XLC"

    def test_resolve_sector_etf_unknown(self) -> None:
        """Unknown sector returns None."""
        assert _resolve_sector_etf("Underwater Basket Weaving") is None

    def test_resolve_sector_etf_empty(self) -> None:
        """Empty string returns None."""
        assert _resolve_sector_etf("") is None
