"""Tests for Exa semantic search client.

Validates:
- Structured output format (title, url, snippet, score, source, confidence)
- Graceful degradation when API key missing
- HTTP error handling
- Query execution with mocked httpx responses
- create_exa_search_fn factory function
- Gap searcher integration (run_exa_semantic_search)
"""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest


# ---------------------------------------------------------------------------
# ExaClient unit tests
# ---------------------------------------------------------------------------


class TestExaClient:
    """Tests for ExaClient class."""

    def test_search_returns_structured_output(self) -> None:
        """Verify search results contain required fields."""
        from do_uw.stages.acquire.clients.exa_client import ExaClient

        mock_response_data = {
            "results": [
                {
                    "title": "Test Article",
                    "url": "https://example.com/article",
                    "publishedDate": "2025-12-01",
                    "text": "Company faces accounting irregularities investigation.",
                    "score": 0.95,
                },
                {
                    "title": "Another Article",
                    "url": "https://example.com/another",
                    "publishedDate": "2025-11-15",
                    "text": "Regulatory enforcement action against company.",
                    "score": 0.88,
                },
            ]
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        with (
            patch.dict(os.environ, {"EXA_API_KEY": "test-key-123"}),
            patch("httpx.Client") as mock_client_cls,
        ):
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = ExaClient()
            results = client.search_semantic("test query")

        assert len(results) == 2
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result
            assert "score" in result
            assert result["source"] == "Exa"
            assert result["confidence"] == "LOW"

        assert results[0]["title"] == "Test Article"
        assert results[0]["url"] == "https://example.com/article"

    def test_graceful_degradation_no_api_key(self) -> None:
        """Verify empty list returned when EXA_API_KEY is missing."""
        from do_uw.stages.acquire.clients.exa_client import ExaClient

        with patch.dict(os.environ, {}, clear=True):
            # Remove the key if it exists
            os.environ.pop("EXA_API_KEY", None)
            client = ExaClient()
            results = client.search_semantic("test query")

        assert results == []

    def test_graceful_degradation_empty_api_key(self) -> None:
        """Verify empty list returned when EXA_API_KEY is empty string."""
        from do_uw.stages.acquire.clients.exa_client import ExaClient

        with patch.dict(os.environ, {"EXA_API_KEY": "  "}):
            client = ExaClient()
            results = client.search_semantic("test query")

        assert results == []

    def test_http_error_returns_empty_list(self) -> None:
        """Verify empty list on HTTP errors (not exceptions)."""
        from do_uw.stages.acquire.clients.exa_client import ExaClient

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error",
            request=MagicMock(spec=httpx.Request),
            response=mock_response,
        )

        with (
            patch.dict(os.environ, {"EXA_API_KEY": "test-key-123"}),
            patch("httpx.Client") as mock_client_cls,
        ):
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = ExaClient()
            results = client.search_semantic("test query")

        assert results == []

    def test_network_error_returns_empty_list(self) -> None:
        """Verify empty list on network errors."""
        from do_uw.stages.acquire.clients.exa_client import ExaClient

        with (
            patch.dict(os.environ, {"EXA_API_KEY": "test-key-123"}),
            patch("httpx.Client") as mock_client_cls,
        ):
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.side_effect = httpx.RequestError(
                "Connection refused",
                request=MagicMock(spec=httpx.Request),
            )
            mock_client_cls.return_value = mock_client

            client = ExaClient()
            results = client.search_semantic("test query")

        assert results == []

    def test_num_results_parameter(self) -> None:
        """Verify num_results is passed to API call."""
        from do_uw.stages.acquire.clients.exa_client import ExaClient

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with (
            patch.dict(os.environ, {"EXA_API_KEY": "test-key-123"}),
            patch("httpx.Client") as mock_client_cls,
        ):
            mock_client = MagicMock()
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            mock_client.post.return_value = mock_response
            mock_client_cls.return_value = mock_client

            client = ExaClient()
            client.search_semantic("test query", num_results=3)

            # Verify the numResults parameter was sent to the API
            call_args = mock_client.post.call_args
            json_body = call_args.kwargs.get("json") or call_args[1].get("json")
            assert json_body["numResults"] == 3


# ---------------------------------------------------------------------------
# create_exa_search_fn factory tests
# ---------------------------------------------------------------------------


class TestCreateExaSearchFn:
    """Tests for module-level create_exa_search_fn factory."""

    def test_returns_none_when_no_key(self) -> None:
        """Verify (None, message) when EXA_API_KEY is not set."""
        from do_uw.stages.acquire.clients.exa_client import create_exa_search_fn

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("EXA_API_KEY", None)
            fn, msg = create_exa_search_fn()

        assert fn is None
        assert "EXA_API_KEY" in msg

    def test_returns_callable_when_key_set(self) -> None:
        """Verify (callable, message) when EXA_API_KEY is set."""
        from do_uw.stages.acquire.clients.exa_client import create_exa_search_fn

        with patch.dict(os.environ, {"EXA_API_KEY": "test-key-123"}):
            fn, msg = create_exa_search_fn()

        assert fn is not None
        assert callable(fn)
        assert "enabled" in msg.lower() or "Exa" in msg


# ---------------------------------------------------------------------------
# run_exa_semantic_search integration tests
# ---------------------------------------------------------------------------


class TestRunExaSemanticSearch:
    """Tests for gap_searcher.run_exa_semantic_search function."""

    def test_returns_results_keyed_by_category(self) -> None:
        """Verify results are keyed by query category."""
        from do_uw.stages.acquire.gap_searcher import run_exa_semantic_search

        mock_results = [
            {
                "title": "Test",
                "url": "https://example.com",
                "snippet": "Test snippet",
                "score": 0.9,
                "source": "Exa",
                "confidence": "LOW",
            }
        ]

        with patch(
            "do_uw.stages.acquire.clients.exa_client.ExaClient"
        ) as mock_exa_cls:
            mock_client = MagicMock()
            mock_client.is_available = True
            mock_client.search_semantic.return_value = mock_results
            mock_exa_cls.return_value = mock_client

            results = run_exa_semantic_search("Apple Inc.", "AAPL")

        assert isinstance(results, dict)
        assert len(results) > 0
        # Each value should be a list
        for key, val in results.items():
            assert isinstance(val, list)

    def test_respects_max_query_cap(self) -> None:
        """Verify hard cap of 5 queries maximum."""
        from do_uw.stages.acquire.gap_searcher import run_exa_semantic_search

        with patch(
            "do_uw.stages.acquire.clients.exa_client.ExaClient"
        ) as mock_exa_cls:
            mock_client = MagicMock()
            mock_client.is_available = True
            mock_client.search_semantic.return_value = []
            mock_exa_cls.return_value = mock_client

            run_exa_semantic_search("Apple Inc.", "AAPL")

            # Should not exceed 5 API calls
            assert mock_client.search_semantic.call_count <= 5

    def test_returns_empty_when_no_api_key(self) -> None:
        """Verify empty dict when Exa is unavailable."""
        from do_uw.stages.acquire.gap_searcher import run_exa_semantic_search

        with patch(
            "do_uw.stages.acquire.clients.exa_client.ExaClient"
        ) as mock_exa_cls:
            mock_client = MagicMock()
            # Simulate no API key: is_available returns False
            mock_client.is_available = False
            mock_exa_cls.return_value = mock_client

            results = run_exa_semantic_search("Apple Inc.", "AAPL")

        assert isinstance(results, dict)
        assert results == {}
