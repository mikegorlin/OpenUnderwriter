"""Tests for CourtListener federal case search client.

Verifies:
- Successful API response parsing into structured results
- Source and confidence fields present on all results
- Graceful degradation on network error / timeout
- Cache hit/miss behavior
- Litigation type classification attempt
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.common import Confidence
from do_uw.stages.acquire.clients.courtlistener_client import CourtListenerClient


# --- Fixtures ---


@pytest.fixture()
def client() -> CourtListenerClient:
    """Create a CourtListenerClient instance."""
    return CourtListenerClient()


@pytest.fixture()
def tmp_cache(tmp_path: Path) -> AnalysisCache:
    """Create a temporary cache for testing."""
    return AnalysisCache(db_path=tmp_path / "test.db")


def _mock_cl_response() -> dict[str, Any]:
    """Build a mock CourtListener API response."""
    return {
        "count": 2,
        "results": [
            {
                "caseName": "Smith v. Acme Corp",
                "dateFiled": "2024-06-15",
                "court": "District Court, S.D. New York",
                "docketNumber": "1:24-cv-01234",
                "suitNature": "Employment",
            },
            {
                "caseName": "EPA v. Acme Corp",
                "dateFiled": "2023-01-10",
                "court": "District Court, D. New Jersey",
                "docketNumber": "2:23-cv-05678",
                "suitNature": "Environmental",
            },
        ],
    }


# --- Tests: Successful response parsing ---


class TestCourtListenerSuccess:
    """Tests for successful API response parsing."""

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_search_cases_returns_structured_results(
        self, mock_httpx: MagicMock, client: CourtListenerClient
    ) -> None:
        """search_cases returns list of dicts with expected fields."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _mock_cl_response()
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance

        result = client.search_cases("Acme Corp", "ACME")

        assert "cases" in result
        assert len(result["cases"]) == 2
        assert result["cases"][0]["case_name"] == "Smith v. Acme Corp"
        assert result["cases"][0]["date_filed"] == "2024-06-15"
        assert result["cases"][0]["court"] == "District Court, S.D. New York"
        assert result["cases"][0]["docket_number"] == "1:24-cv-01234"

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_source_and_confidence_on_all_results(
        self, mock_httpx: MagicMock, client: CourtListenerClient
    ) -> None:
        """Every case result has source='CourtListener' and confidence=LOW."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _mock_cl_response()
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance

        result = client.search_cases("Acme Corp", "ACME")

        for case in result["cases"]:
            assert case["source"] == "CourtListener"
            assert case["confidence"] == Confidence.LOW

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_litigation_type_classification(
        self, mock_httpx: MagicMock, client: CourtListenerClient
    ) -> None:
        """Results include litigation_type classification."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _mock_cl_response()
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance

        result = client.search_cases("Acme Corp", "ACME")

        assert result["cases"][0]["litigation_type"] == "employment"
        assert result["cases"][1]["litigation_type"] == "environmental"


# --- Tests: Graceful degradation ---


class TestCourtListenerGracefulDegradation:
    """Tests for graceful failure handling."""

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_network_error_returns_empty(
        self, mock_httpx: MagicMock, client: CourtListenerClient
    ) -> None:
        """Network error returns empty dict (graceful degradation)."""
        import httpx

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.side_effect = httpx.ConnectError("Connection refused")
        mock_httpx.Client.return_value = mock_client_instance
        mock_httpx.ConnectError = httpx.ConnectError

        result = client.search_cases("Acme Corp", "ACME")

        assert result == {}

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_timeout_returns_empty(
        self, mock_httpx: MagicMock, client: CourtListenerClient
    ) -> None:
        """Timeout returns empty dict (graceful degradation)."""
        import httpx

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.side_effect = httpx.TimeoutException("Timed out")
        mock_httpx.Client.return_value = mock_client_instance
        mock_httpx.TimeoutException = httpx.TimeoutException

        result = client.search_cases("Acme Corp", "ACME")

        assert result == {}

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_empty_api_response_returns_empty_cases(
        self, mock_httpx: MagicMock, client: CourtListenerClient
    ) -> None:
        """Empty API response returns dict with empty cases list."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"count": 0, "results": []}
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance

        result = client.search_cases("Acme Corp", "ACME")

        assert result.get("cases", []) == []


# --- Tests: Cache behavior ---


class TestCourtListenerCache:
    """Tests for cache hit/miss behavior."""

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_cache_miss_calls_api(
        self,
        mock_httpx: MagicMock,
        client: CourtListenerClient,
        tmp_cache: AnalysisCache,
    ) -> None:
        """On cache miss, API is called and result is cached."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = _mock_cl_response()
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__enter__ = MagicMock(return_value=mock_client_instance)
        mock_client_instance.__exit__ = MagicMock(return_value=False)
        mock_client_instance.get.return_value = mock_response
        mock_httpx.Client.return_value = mock_client_instance

        result = client.search_cases("Acme Corp", "ACME", cache=tmp_cache)

        assert "cases" in result
        assert len(result["cases"]) == 2
        # Verify API was called
        mock_client_instance.get.assert_called_once()

    @patch("do_uw.stages.acquire.clients.courtlistener_client.httpx")
    def test_cache_hit_skips_api(
        self,
        mock_httpx: MagicMock,
        client: CourtListenerClient,
        tmp_cache: AnalysisCache,
    ) -> None:
        """On cache hit, API is NOT called."""
        # Pre-populate cache
        cached_data = {"cases": [{"case_name": "Cached Case"}]}
        tmp_cache.set("courtlistener:ACME", cached_data, source="courtlistener")

        result = client.search_cases("Acme Corp", "ACME", cache=tmp_cache)

        assert result == cached_data
        # httpx should never have been used
        mock_httpx.Client.assert_not_called()
