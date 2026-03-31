"""Tests for acquisition clients, fallback chain, and gates.

All tests use unittest.mock.patch -- no real network calls.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.acquire.clients.litigation_client import LitigationClient
from do_uw.stages.acquire.clients.market_client import MarketDataClient
from do_uw.stages.acquire.clients.news_client import NewsClient
from do_uw.stages.acquire.clients.sec_client import SECFilingClient
from do_uw.stages.acquire.clients.web_search import WebSearchClient
from do_uw.stages.acquire.fallback import (
    DataAcquisitionError,
    FallbackChain,
    FallbackTier,
)
from do_uw.stages.acquire.gates import ACQUISITION_GATES, GateType, check_gates

NOW = datetime.now(tz=UTC)


def _sv(val: str) -> SourcedValue[str]:
    return SourcedValue(value=val, source="test", confidence=Confidence.HIGH, as_of=NOW)


def _make_state(
    ticker: str = "AAPL", cik: str = "320193", name: str = "Apple Inc.",
) -> AnalysisState:
    """Create a minimal AnalysisState with resolved company identity."""
    identity = CompanyIdentity(ticker=ticker, cik=_sv(cik), legal_name=_sv(name))
    return AnalysisState(ticker=ticker, company=CompanyProfile(identity=identity))


# Mock SEC submissions response shared across tests.
_SUBMISSIONS_RESP: dict[str, Any] = {
    "filings": {"recent": {
        "form": ["10-K", "10-Q", "10-Q", "DEF 14A", "8-K", "4"],
        "accessionNumber": ["a1", "a2", "a3", "a4", "a5", "a6"],
        "filingDate": ["2025-11-01", "2025-08-01", "2025-05-01",
                       "2025-03-01", "2025-01-15", "2025-01-10"],
        "primaryDocument": ["d1.htm", "d2.htm", "d3.htm", "d4.htm", "d5.htm", "d6.htm"],
    }}
}


def _make_mock_df() -> MagicMock:
    """Create a mock pandas DataFrame for yfinance tests."""
    df = MagicMock()
    df.empty = False
    df.reset_index.return_value = df
    df.columns = ["Date", "Close"]
    df.__getitem__ = MagicMock(return_value=df)
    df.to_dict.return_value = {"Date": ["2025-01-01"], "Close": [150.0]}
    return df


class TestFallbackChain:
    def test_first_tier_succeeds(self) -> None:
        chain = FallbackChain(source_name="t", tiers=[
            FallbackTier("t1", Confidence.HIGH, lambda: {"d": 1}),
            FallbackTier("t2", Confidence.MEDIUM, lambda: {"d": 2}),
        ])
        data, conf, name = chain.execute()
        assert data == {"d": 1} and conf == Confidence.HIGH and name == "t1"

    def test_first_fails_second_succeeds(self) -> None:
        chain = FallbackChain(source_name="t", tiers=[
            FallbackTier("t1", Confidence.HIGH, lambda: None),
            FallbackTier("t2", Confidence.MEDIUM, lambda: {"d": 2}),
            FallbackTier("t3", Confidence.LOW, lambda: {"d": 3}),
        ])
        data, conf, name = chain.execute()
        assert data == {"d": 2} and conf == Confidence.MEDIUM and name == "t2"

    def test_all_tiers_fail(self) -> None:
        def _raise() -> dict[str, Any] | None:
            raise ConnectionError("timeout")

        chain = FallbackChain(source_name="src", tiers=[
            FallbackTier("t1", Confidence.HIGH, _raise),
            FallbackTier("t2", Confidence.LOW, lambda: None),
        ])
        with pytest.raises(DataAcquisitionError) as exc:
            chain.execute()
        assert exc.value.source_name == "src"
        assert len(exc.value.errors) == 1

    def test_exception_tier_then_success(self) -> None:
        def _raise() -> dict[str, Any] | None:
            raise RuntimeError("API error")

        chain = FallbackChain(source_name="t", tiers=[
            FallbackTier("fail", Confidence.HIGH, _raise),
            FallbackTier("ok", Confidence.LOW, lambda: {"d": "fb"}),
        ])
        data, conf, name = chain.execute()
        assert data == {"d": "fb"} and conf == Confidence.LOW and name == "ok"


class TestAcquisitionGates:
    def test_gate_count(self) -> None:
        assert len(ACQUISITION_GATES) == 6
        assert sum(1 for g in ACQUISITION_GATES if g.gate_type == GateType.HARD) == 3
        assert sum(1 for g in ACQUISITION_GATES if g.gate_type == GateType.SOFT) == 3

    def test_all_gates_pass(self) -> None:
        data = AcquiredData(
            filings={"10-K": [{"f": 1}], "10-Q": [{"f": 2}], "DEF 14A": [{"f": 3}]},
            market_data={"info": {}}, litigation_data={"r": [1]},
            web_search_results={"n": [1]},
        )
        assert all(r.passed for r in check_gates(data))

    def test_missing_annual_hard_fail(self) -> None:
        data = AcquiredData(
            filings={"10-Q": [{"f": 1}], "DEF 14A": [{"f": 2}]},
            market_data={"info": {}},
        )
        annual = next(r for r in check_gates(data) if r.gate_name == "annual_report")
        assert not annual.passed and annual.gate_type == GateType.HARD

    def test_fpi_20f_passes_annual_gate(self) -> None:
        data = AcquiredData(
            filings={"20-F": [{"f": 1}], "6-K": [{"f": 2}], "DEF 14A": [{"f": 3}]},
            market_data={"info": {}},
        )
        results = {r.gate_name: r.passed for r in check_gates(data)}
        assert results["annual_report"] and results["quarterly_report"]

    def test_missing_litigation_soft_fail(self) -> None:
        data = AcquiredData(
            filings={"10-K": [{"f": 1}], "10-Q": [{"f": 2}], "DEF 14A": [{"f": 3}]},
            market_data={"info": {}}, litigation_data={}, web_search_results={"n": [1]},
        )
        lit = next(r for r in check_gates(data) if r.gate_name == "litigation")
        assert not lit.passed and lit.gate_type == GateType.SOFT

    def test_def14a_no_space_passes(self) -> None:
        data = AcquiredData(
            filings={"10-K": [{"f": 1}], "10-Q": [{"f": 2}], "DEF14A": [{"f": 3}]},
            market_data={"info": {}},
        )
        proxy = next(r for r in check_gates(data) if r.gate_name == "proxy_statement")
        assert proxy.passed


class TestSECFilingClient:
    @patch("do_uw.stages.acquire.clients.sec_client_filing.sec_get")
    def test_domestic_filing_types(self, mock_get: MagicMock) -> None:
        mock_get.return_value = _SUBMISSIONS_RESP
        result = SECFilingClient().acquire(_make_state())
        for ft in ("10-K", "10-Q", "DEF 14A", "8-K", "4"):
            assert ft in result

    @patch("do_uw.stages.acquire.clients.sec_client_filing.sec_get")
    def test_fpi_filing_types(self, mock_get: MagicMock) -> None:
        mock_get.return_value = {"filings": {"recent": {
            "form": ["20-F", "6-K", "6-K"],
            "accessionNumber": ["a1", "a2", "a3"],
            "filingDate": ["2025-06-01", "2025-04-01", "2025-02-01"],
            "primaryDocument": ["d1.htm", "d2.htm", "d3.htm"],
        }}}
        state = _make_state(ticker="TSM", cik="1046179", name="TSMC")
        state.company.identity.is_fpi = True  # type: ignore[union-attr]
        result = SECFilingClient().acquire(state)
        assert "20-F" in result and "6-K" in result
        assert "10-K" not in result and "10-Q" not in result

    @patch("do_uw.stages.acquire.clients.sec_client_filing.sec_get")
    def test_filing_metadata_structure(self, mock_get: MagicMock) -> None:
        mock_get.return_value = {"filings": {"recent": {
            "form": ["10-K"], "accessionNumber": ["0001193125-25-123456"],
            "filingDate": ["2025-11-01"], "primaryDocument": ["f.htm"],
        }}}
        filings = SECFilingClient().acquire(_make_state()).get("10-K", [])
        assert len(filings) == 1
        for key in ("accession_number", "filing_date", "form_type",
                     "primary_doc_url", "filing_url"):
            assert key in filings[0]


class TestMarketDataClient:
    @patch("yfinance.Ticker")
    def test_collects_all_data_categories(self, mock_cls: MagicMock) -> None:
        mt = MagicMock()
        mt.info = {"marketCap": 3_000_000_000_000, "sector": "Technology"}
        mt.news = [{"title": "Apple news"}]
        df = _make_mock_df()
        mt.history.return_value = df
        mt.insider_transactions = df
        mt.institutional_holders = df
        mt.recommendations = df
        mock_cls.return_value = mt

        result = MarketDataClient().acquire(_make_state())
        assert result["info"]["marketCap"] == 3_000_000_000_000
        for k in ("history_1y", "history_5y", "insider_transactions",
                   "institutional_holders", "recommendations", "news"):
            assert k in result

    @patch("yfinance.Ticker")
    def test_partial_data_on_failure(self, mock_cls: MagicMock) -> None:
        mt = MagicMock()
        mt.info = {"sector": "Technology"}
        mt.history.side_effect = ConnectionError("Yahoo API down")
        mt.insider_transactions = None
        mt.institutional_holders = None
        mt.recommendations = None
        mt.news = None
        mock_cls.return_value = mt

        result = MarketDataClient().acquire(_make_state())
        assert result["info"]["sector"] == "Technology"
        assert result["history_1y"] == {} and result["history_5y"] == {}


class TestLitigationClient:
    def test_web_search_first(self) -> None:
        calls: list[str] = []

        def _search(q: str) -> list[dict[str, str]]:
            calls.append(q)
            return [{"title": "R", "url": "http://x.com", "snippet": ""}]

        ws = WebSearchClient(search_fn=_search, search_budget=50)
        with patch("do_uw.stages.acquire.clients.litigation_client.sec_get") as mg:
            mg.return_value = {"hits": {"hits": []}}
            result = LitigationClient(web_search=ws).acquire(_make_state())

        assert len(calls) == 4
        assert any("securities class action" in q for q in calls)
        assert any("SEC investigation" in q for q in calls)
        assert all(r["confidence"] == Confidence.LOW for r in result["web_results"])

    def test_sec_references_tagged_high(self) -> None:
        with patch("do_uw.stages.acquire.clients.litigation_client.sec_get") as mg:
            mg.return_value = {"hits": {"hits": [{"_source": {
                "form_type": "10-K", "file_date": "2024-11-01",
                "file_url": "http://sec.gov/f", "display_names": ["Apple Inc."],
            }}]}}
            result = LitigationClient().acquire(_make_state())
        assert result["sec_references"][0]["confidence"] == Confidence.HIGH


class TestWebSearchClient:
    def test_budget_tracking(self) -> None:
        n = 0

        def _s(q: str) -> list[dict[str, str]]:
            nonlocal n
            n += 1
            return [{"title": str(n), "url": "http://x.com", "snippet": ""}]

        c = WebSearchClient(search_fn=_s, search_budget=3)
        c.search("q1")
        c.search("q2")
        c.search("q3")
        assert c.searches_used == 3 and c.budget_remaining == 0
        assert c.search("q4") == [] and n == 3

    def test_blind_spot_priority_order(self) -> None:
        qs: list[str] = []

        def _s(q: str) -> list[dict[str, str]]:
            qs.append(q)
            return [{"title": "R", "url": "http://x.com", "snippet": ""}]

        results = WebSearchClient(search_fn=_s, search_budget=50).blind_spot_sweep(
            "Apple Inc.", "AAPL"
        )
        assert all(k in results for k in (
            "litigation", "regulatory", "short_seller", "whistleblower",
        ))
        assert "lawsuit" in qs[0] and "SEC subpoena" in qs[1]

    def test_blind_spot_stops_on_budget(self) -> None:
        def _s(q: str) -> list[dict[str, str]]:
            return [{"title": "R", "url": "http://x.com", "snippet": ""}]

        results = WebSearchClient(search_fn=_s, search_budget=2).blind_spot_sweep(
            "Apple Inc.", "AAPL"
        )
        assert sum(1 for v in results.values() if v) == 2

    def test_default_search_returns_empty(self) -> None:
        assert WebSearchClient().search("test") == []


class TestNewsClient:
    def test_collects_web_and_yfinance_news(self) -> None:
        def _s(q: str) -> list[dict[str, str]]:
            return [{"title": "Web", "url": "http://x.com", "snippet": ""}]

        ws = WebSearchClient(search_fn=_s, search_budget=50)
        with patch("yfinance.Ticker") as mc:
            mt = MagicMock()
            mt.news = [{"title": "yf news", "link": "http://y.com"}]
            mc.return_value = mt
            result = NewsClient(web_search=ws).acquire(_make_state())
        assert len(result["web_news"]) >= 1
        assert result["yfinance_news"][0]["title"] == "yf news"
