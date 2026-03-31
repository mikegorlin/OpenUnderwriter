"""Tests for filing_documents data flow from SEC client to state.

Verifies that:
1. Filing documents are promoted to acquired.filing_documents (dedicated field)
2. get_filing_documents(state) returns populated data from the primary field
3. Filing documents are NOT double-stored in filings dict
4. Backward compatibility: get_filing_documents fallback for legacy state
5. State serialization excludes company_facts and filing_texts from filings
6. In-memory state retains company_facts after serialization (extractors need it)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.pipeline import _restore_filings_blobs, _strip_filings_blobs
from do_uw.stages.acquire.orchestrator import (
    AcquisitionOrchestrator,
    _promote_filing_fields,
)
from do_uw.stages.extract.sourced import get_filing_documents

NOW = datetime.now(tz=UTC)


def _sv(val: str) -> SourcedValue[str]:
    return SourcedValue(
        value=val, source="test", confidence=Confidence.HIGH, as_of=NOW
    )


def _make_resolved_state(
    ticker: str = "AAPL",
    cik: str = "320193",
    name: str = "Apple Inc.",
) -> AnalysisState:
    """Create a state with resolve stage completed."""
    identity = CompanyIdentity(
        ticker=ticker, cik=_sv(cik), legal_name=_sv(name)
    )
    state = AnalysisState(
        ticker=ticker, company=CompanyProfile(identity=identity)
    )
    state.mark_stage_running("resolve")
    state.mark_stage_completed("resolve")
    return state


# Sample filing documents as returned by filing_fetcher.
_MOCK_FILING_DOCS: dict[str, list[dict[str, str]]] = {
    "10-K": [
        {
            "accession": "0001-23-456789",
            "filing_date": "2025-11-01",
            "form_type": "10-K",
            "full_text": "Annual report full text content here.",
        },
    ],
    "DEF 14A": [
        {
            "accession": "0001-23-456790",
            "filing_date": "2025-03-01",
            "form_type": "DEF 14A",
            "full_text": "Proxy statement full text content here.",
        },
    ],
    "8-K": [
        {
            "accession": "0001-23-456791",
            "filing_date": "2025-01-15",
            "form_type": "8-K",
            "full_text": "Current report full text content here.",
        },
    ],
}

# Sample SEC client result that includes filing_documents.
_MOCK_SEC_RESULT: dict[str, Any] = {
    "10-K": [{"accession_number": "a1", "filing_date": "2025-11-01"}],
    "10-Q": [{"accession_number": "a2", "filing_date": "2025-08-01"}],
    "DEF 14A": [{"accession_number": "a3", "filing_date": "2025-03-01"}],
    "8-K": [{"accession_number": "a4", "filing_date": "2025-01-15"}],
    "4": [{"accession_number": "a5", "filing_date": "2025-01-10"}],
    "company_facts": {"facts": {"us-gaap": {"Revenue": {}}}},
    "filing_documents": _MOCK_FILING_DOCS,
    "filing_texts": {"10-K": {"item_1": "Legacy text"}},
}


class TestPromoteFilingFields:
    """Test the _promote_filing_fields helper directly."""

    def test_filing_documents_moved_to_acquired(self) -> None:
        """Filing documents are popped from data and set on acquired."""
        data: dict[str, Any] = {
            "10-K": [{"accession_number": "a1"}],
            "filing_documents": {"10-K": [{"full_text": "content"}]},
        }
        acquired = AcquiredData()

        _promote_filing_fields(data, acquired)

        # Promoted to dedicated field.
        assert "10-K" in acquired.filing_documents
        assert acquired.filing_documents["10-K"][0]["full_text"] == "content"
        # Removed from filings dict.
        assert "filing_documents" not in data

    def test_filing_texts_removed(self) -> None:
        """Legacy filing_texts are removed from filings dict."""
        data: dict[str, Any] = {
            "10-K": [{"accession_number": "a1"}],
            "filing_texts": {"10-K": {"item_1": "Legacy"}},
        }
        acquired = AcquiredData()

        _promote_filing_fields(data, acquired)

        assert "filing_texts" not in data

    def test_no_filing_documents_noop(self) -> None:
        """When no filing_documents key, nothing happens."""
        data: dict[str, Any] = {
            "10-K": [{"accession_number": "a1"}],
        }
        acquired = AcquiredData()

        _promote_filing_fields(data, acquired)

        assert acquired.filing_documents == {}

    def test_empty_filing_documents_not_promoted(self) -> None:
        """Empty dict filing_documents is not promoted (falsy)."""
        data: dict[str, Any] = {
            "filing_documents": {},
        }
        acquired = AcquiredData()

        _promote_filing_fields(data, acquired)

        assert acquired.filing_documents == {}


class TestOrchestratorFilingDocuments:
    """Integration tests for filing_documents flow through orchestrator."""

    @patch("do_uw.stages.acquire.orchestrator.time")
    def test_filing_documents_reach_acquired_field(
        self, mock_time: MagicMock
    ) -> None:
        """SEC client result has filing_documents promoted to acquired."""
        mock_time.sleep = MagicMock()

        sec = MagicMock()
        sec.name = "sec_filings"
        sec.acquire.return_value = _MOCK_SEC_RESULT.copy()

        market = MagicMock()
        market.name = "market_data"
        market.acquire.return_value = {
            "info": {"marketCap": 3_000_000_000_000},
            "history_1y": {"Close": [150.0]},
        }

        orchestrator = AcquisitionOrchestrator(
            cache=None, search_budget=0
        )
        orchestrator._sec_client = sec
        orchestrator._market_client = market
        orchestrator._litigation_client = MagicMock(
            name="litigation",
            acquire=MagicMock(return_value={}),
        )
        orchestrator._news_client = MagicMock(
            name="news_sentiment",
            acquire=MagicMock(return_value={}),
        )

        state = _make_resolved_state()
        result = orchestrator.run(state)

        # Filing documents at dedicated field.
        assert "10-K" in result.filing_documents
        assert "DEF 14A" in result.filing_documents
        assert "8-K" in result.filing_documents

        # Filing documents NOT in filings dict (no double-store).
        assert "filing_documents" not in result.filings

        # Legacy filing_texts also removed.
        assert "filing_texts" not in result.filings

        # Company facts still in filings dict (extractors need it).
        assert "company_facts" in result.filings

    @patch("do_uw.stages.acquire.orchestrator.time")
    def test_get_filing_documents_returns_data(
        self, mock_time: MagicMock
    ) -> None:
        """get_filing_documents(state) returns the promoted data."""
        mock_time.sleep = MagicMock()

        sec = MagicMock()
        sec.name = "sec_filings"
        sec.acquire.return_value = _MOCK_SEC_RESULT.copy()

        market = MagicMock()
        market.name = "market_data"
        market.acquire.return_value = {
            "info": {"marketCap": 3_000_000_000_000},
            "history_1y": {"Close": [150.0]},
        }

        orchestrator = AcquisitionOrchestrator(
            cache=None, search_budget=0
        )
        orchestrator._sec_client = sec
        orchestrator._market_client = market
        orchestrator._litigation_client = MagicMock(
            name="litigation",
            acquire=MagicMock(return_value={}),
        )
        orchestrator._news_client = MagicMock(
            name="news_sentiment",
            acquire=MagicMock(return_value={}),
        )

        state = _make_resolved_state()
        acquired = orchestrator.run(state)
        state.acquired_data = acquired

        docs = get_filing_documents(state)
        assert "10-K" in docs
        assert docs["10-K"][0]["full_text"] == (
            "Annual report full text content here."
        )
        assert "DEF 14A" in docs


class TestGetFilingDocumentsFallback:
    """Test backward-compat fallback in get_filing_documents."""

    def test_primary_field_preferred(self) -> None:
        """When filing_documents on AcquiredData, uses that."""
        state = AnalysisState(ticker="AAPL")
        state.acquired_data = AcquiredData(
            filing_documents={
                "10-K": [{"full_text": "primary"}],
            },
            filings={
                "filing_documents": {
                    "10-K": [{"full_text": "fallback"}],
                },
            },
        )

        docs = get_filing_documents(state)
        assert docs["10-K"][0]["full_text"] == "primary"

    def test_fallback_to_filings_dict(self) -> None:
        """When filing_documents field empty, falls back to filings dict."""
        state = AnalysisState(ticker="AAPL")
        state.acquired_data = AcquiredData(
            filing_documents={},
            filings={
                "filing_documents": {
                    "DEF 14A": [{"full_text": "from filings"}],
                },
            },
        )

        docs = get_filing_documents(state)
        assert "DEF 14A" in docs
        assert docs["DEF 14A"][0]["full_text"] == "from filings"

    def test_no_data_returns_empty(self) -> None:
        """When no filing documents anywhere, returns empty dict."""
        state = AnalysisState(ticker="AAPL")
        state.acquired_data = AcquiredData()

        docs = get_filing_documents(state)
        assert docs == {}

    def test_no_acquired_data_returns_empty(self) -> None:
        """When acquired_data is None, returns empty dict."""
        state = AnalysisState(ticker="AAPL")

        docs = get_filing_documents(state)
        assert docs == {}


class TestStateSerialization:
    """Test that large blobs are stripped before state.json serialization."""

    def _make_state_with_blobs(self) -> AnalysisState:
        """Create state with company_facts and filing_texts in filings."""
        # Simulate a large company_facts blob (~100KB for test).
        large_facts: dict[str, Any] = {
            "facts": {
                "us-gaap": {
                    f"Concept{i}": {
                        "units": {"USD": [{"val": i * 1000}] * 10}
                    }
                    for i in range(200)
                }
            }
        }
        state = AnalysisState(ticker="TSLA")
        state.acquired_data = AcquiredData(
            filings={
                "10-K": [{"accession_number": "a1"}],
                "10-Q": [{"accession_number": "a2"}],
                "company_facts": large_facts,
                "filing_texts": {"10-K": {"item_1": "Legacy text" * 100}},
                "exhibit_21": {"subsidiaries": ["Sub A", "Sub B"]},
            },
            filing_documents={
                "10-K": [{"full_text": "Annual report text"}],
            },
        )
        return state

    def test_strip_removes_company_facts(self) -> None:
        """_strip_filings_blobs removes company_facts from filings."""
        state = self._make_state_with_blobs()

        stripped = _strip_filings_blobs(state)

        assert "company_facts" not in state.acquired_data.filings  # type: ignore[union-attr]
        assert "company_facts" in stripped

    def test_strip_removes_filing_texts(self) -> None:
        """_strip_filings_blobs removes filing_texts from filings."""
        state = self._make_state_with_blobs()

        stripped = _strip_filings_blobs(state)

        assert "filing_texts" not in state.acquired_data.filings  # type: ignore[union-attr]
        assert "filing_texts" in stripped

    def test_strip_removes_exhibit_21(self) -> None:
        """_strip_filings_blobs removes exhibit_21 from filings."""
        state = self._make_state_with_blobs()

        stripped = _strip_filings_blobs(state)

        assert "exhibit_21" not in state.acquired_data.filings  # type: ignore[union-attr]
        assert "exhibit_21" in stripped

    def test_restore_puts_blobs_back(self) -> None:
        """_restore_filings_blobs restores stripped data."""
        state = self._make_state_with_blobs()
        original_facts = state.acquired_data.filings["company_facts"]  # type: ignore[union-attr]

        stripped = _strip_filings_blobs(state)
        _restore_filings_blobs(state, stripped)

        assert state.acquired_data.filings["company_facts"] is original_facts  # type: ignore[union-attr]
        assert "filing_texts" in state.acquired_data.filings  # type: ignore[union-attr]
        assert "exhibit_21" in state.acquired_data.filings  # type: ignore[union-attr]

    def test_serialized_json_excludes_company_facts(self) -> None:
        """After strip, model_dump_json does not contain company_facts."""
        state = self._make_state_with_blobs()

        stripped = _strip_filings_blobs(state)
        json_str = state.model_dump_json()
        _restore_filings_blobs(state, stripped)

        parsed = json.loads(json_str)
        filings = parsed["acquired_data"]["filings"]
        assert "company_facts" not in filings
        assert "filing_texts" not in filings
        assert "exhibit_21" not in filings
        # Regular filing metadata still present.
        assert "10-K" in filings
        assert "10-Q" in filings

    def test_serialized_json_under_2mb(self) -> None:
        """Serialized state is under 2MB after stripping blobs."""
        state = self._make_state_with_blobs()

        stripped = _strip_filings_blobs(state)
        json_bytes = state.model_dump_json().encode("utf-8")
        _restore_filings_blobs(state, stripped)

        assert len(json_bytes) < 2_000_000, (
            f"State JSON is {len(json_bytes):,} bytes, expected < 2,000,000"
        )

    def test_in_memory_state_unmodified_after_save(self) -> None:
        """After strip+restore cycle, in-memory state has all data."""
        state = self._make_state_with_blobs()

        stripped = _strip_filings_blobs(state)
        _ = state.model_dump_json()
        _restore_filings_blobs(state, stripped)

        # company_facts still accessible in memory for extractors.
        assert "company_facts" in state.acquired_data.filings  # type: ignore[union-attr]
        facts = state.acquired_data.filings["company_facts"]  # type: ignore[union-attr]
        assert "facts" in facts
        assert "us-gaap" in facts["facts"]

    def test_strip_noop_when_no_acquired_data(self) -> None:
        """_strip_filings_blobs handles None acquired_data."""
        state = AnalysisState(ticker="AAPL")

        stripped = _strip_filings_blobs(state)

        assert stripped == {}

    def test_restore_noop_when_empty_stripped(self) -> None:
        """_restore_filings_blobs handles empty stripped dict."""
        state = AnalysisState(ticker="AAPL")
        state.acquired_data = AcquiredData()

        _restore_filings_blobs(state, {})
        # No error raised.
