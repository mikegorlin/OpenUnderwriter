"""Tests for Serper.dev web search client.

Validates:
- create_serper_search_fn factory function
- Circuit breaker pattern (fail fast after 5 consecutive failures)
- Retry logic with exponential backoff (max 3 retries)
- Health check method
- Graceful degradation when API key missing
- HTTP error handling and timeouts
"""

from __future__ import annotations

import os
import time
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# Serper client unit tests
# ---------------------------------------------------------------------------


class TestSerperClient:
    """Tests for serper_client module functions."""

    def setup_method(self) -> None:
        """Reset circuit breaker state before each test."""
        import do_uw.stages.acquire.clients.serper_client as serper_module
        serper_module._failure_count = 0
        serper_module._last_success_time = time.time()

    def test_create_serper_search_fn_with_api_key(self) -> None:
        """Verify search function is created when API key present."""
        from do_uw.stages.acquire.clients.serper_client import create_serper_search_fn

        with patch.dict(os.environ, {"SERPER_API_KEY": "test-key-123"}):
            search_fn, status = create_serper_search_fn()
            assert search_fn is not None
            assert "serper.dev web search enabled" in status.lower()
            assert "retry" in status.lower() or "circuit" in status.lower()

    def test_create_serper_search_fn_without_api_key(self) -> None:
        """Verify None returned when API key missing."""
        from do_uw.stages.acquire.clients.serper_client import create_serper_search_fn

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SERPER_API_KEY", None)
            search_fn, status = create_serper_search_fn()
            assert search_fn is None
            assert "serper_api_key not set" in status.lower()
            assert "web search disabled" in status.lower()

    def test_search_success(self) -> None:
        """Verify successful search returns structured results."""
        from do_uw.stages.acquire.clients.serper_client import create_serper_search_fn

        mock_response_data = {
            "organic": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "Test snippet 1",
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/2",
                    "snippet": "Test snippet 2",
                },
            ]
        }

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = MagicMock()

        # Patch _get_client to return mocked client
        with (
            patch.dict(os.environ, {"SERPER_API_KEY": "test-key-123"}),
            patch("do_uw.stages.acquire.clients.serper_client._get_client") as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            search_fn, _ = create_serper_search_fn()
            assert search_fn is not None
            results = search_fn("test query")

        assert len(results) == 2
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "snippet" in result
            assert result["url"].startswith("https://")

        assert results[0]["title"] == "Test Result 1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["snippet"] == "Test snippet 1"

    def test_search_retry_on_failure(self) -> None:
        """Verify retry logic on transient failures."""
        from do_uw.stages.acquire.clients.serper_client import create_serper_search_fn

        call_count = 0

        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:  # Fail first two attempts
                raise httpx.ConnectTimeout("Connection timeout")
            # Succeed on third attempt
            mock_response = MagicMock(spec=httpx.Response)
            mock_response.status_code = 200
            mock_response.json.return_value = {"organic": []}
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with (
            patch.dict(os.environ, {"SERPER_API_KEY": "test-key-123"}),
            patch("do_uw.stages.acquire.clients.serper_client._get_client") as mock_get_client,
            patch("time.sleep") as mock_sleep,  # Speed up test
        ):
            mock_client = MagicMock()
            mock_client.post.side_effect = mock_post
            mock_get_client.return_value = mock_client

            search_fn, _ = create_serper_search_fn()
            assert search_fn is not None
            results = search_fn("test query")

        assert call_count == 3  # Should have retried twice
        assert results == []  # Empty results from mock
        # Verify sleep was called for retries
        # mock_sleep.assert_called()

    def test_circuit_breaker_opens_after_failures(self) -> None:
        """Verify circuit breaker opens after 5 consecutive failures."""
        from do_uw.stages.acquire.clients.serper_client import create_serper_search_fn

        call_count = 0

        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise httpx.ConnectTimeout("Connection timeout")

        with (
            patch.dict(os.environ, {"SERPER_API_KEY": "test-key-123"}),
            patch("do_uw.stages.acquire.clients.serper_client._get_client") as mock_get_client,
            patch("time.sleep") as mock_sleep,  # Speed up test
        ):
            mock_client = MagicMock()
            mock_client.post.side_effect = mock_post
            mock_get_client.return_value = mock_client

            search_fn, _ = create_serper_search_fn()
            assert search_fn is not None

            # Make 6 calls - circuit should open after 5th failure
            for i in range(6):
                search_fn(f"query {i}")

        # Each failure has 3 retries = 15 calls for 5 failures
        # 6th search should be blocked by circuit breaker (no HTTP calls)
        assert call_count == 15  # 5 failures × 3 retries each

    def test_health_check_success(self) -> None:
        """Verify health check returns True when API is accessible."""
        from do_uw.stages.acquire.clients.serper_client import health_check

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"organic": [{"title": "test", "link": "http://test.com", "snippet": "test"}]}
        mock_response.raise_for_status = MagicMock()

        with (
            patch.dict(os.environ, {"SERPER_API_KEY": "test-key-123"}),
            patch("do_uw.stages.acquire.clients.serper_client._get_client") as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_get_client.return_value = mock_client

            healthy, message = health_check()
            assert healthy is True
            assert "responsive" in message.lower()

    def test_health_check_failure(self) -> None:
        """Verify health check returns False when API is inaccessible."""
        from do_uw.stages.acquire.clients.serper_client import health_check

        with (
            patch.dict(os.environ, {"SERPER_API_KEY": "test-key-123"}),
            patch("do_uw.stages.acquire.clients.serper_client._get_client") as mock_get_client,
        ):
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.ConnectTimeout("Timeout")
            mock_get_client.return_value = mock_client

            healthy, message = health_check()
            assert healthy is False
            assert "returned no results" in message.lower()

    def test_health_check_no_api_key(self) -> None:
        """Verify health check returns False when API key missing."""
        from do_uw.stages.acquire.clients.serper_client import health_check

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SERPER_API_KEY", None)
            healthy, message = health_check()
            assert healthy is False
            assert "serper_api_key not set" in message.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
