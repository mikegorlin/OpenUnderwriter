"""Serper.dev web search client for pipeline web search integration.

Provides a search function compatible with WebSearchClient's pluggable
search_fn interface. Returns list of dicts with 'title', 'url', 'snippet'.

Requires SERPER_API_KEY environment variable.

Enhanced with:
- Shared httpx.Client with connection pooling
- Retry logic with exponential backoff (max 3 retries)
- Circuit breaker pattern (fail fast after 5 consecutive failures)
- Separate connect/read timeouts (10s connect, 30s read)
- Health check method for API connectivity verification
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)

SERPER_BASE_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL = "https://google.serper.dev/news"

# Circuit breaker state
_failure_count = 0
_last_success_time = time.time()  # Initialize to current time
_CIRCUIT_BREAKER_THRESHOLD = 5  # Consecutive failures before opening circuit
_CIRCUIT_BREAKER_RESET_SECONDS = 60  # Reset circuit after 60 seconds of no failures

# Shared HTTP client for connection pooling
_client: httpx.Client | None = None
_client_lock = False  # Simple lock for thread safety (not needed for single-threaded pipeline)


def _get_client() -> httpx.Client:
    """Get or create shared httpx.Client with optimized timeouts."""
    global _client
    if _client is None:
        _client = httpx.Client(
            timeout=httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0),
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True,
        )
    return _client


def _check_circuit_breaker() -> bool:
    """Check if circuit breaker is open (too many recent failures).
    
    Returns:
        True if circuit is open (should fail fast), False if closed (allow request).
    """
    global _failure_count, _last_success_time
    
    # Reset failure count if last success was more than reset seconds ago
    current_time = time.time()
    if current_time - _last_success_time > _CIRCUIT_BREAKER_RESET_SECONDS:
        _failure_count = 0
    
    # Open circuit if threshold exceeded
    if _failure_count >= _CIRCUIT_BREAKER_THRESHOLD:
        logger.warning(
            "Circuit breaker open (failures: %d). Failing fast for Serper.dev API.",
            _failure_count
        )
        return True
    
    return False


def _record_success() -> None:
    """Record successful API call to reset circuit breaker."""
    global _failure_count, _last_success_time
    _failure_count = 0
    _last_success_time = time.time()


def _record_failure() -> None:
    """Record failed API call for circuit breaker."""
    global _failure_count
    _failure_count += 1


def create_serper_search_fn() -> tuple[
    # Callable[[str], list[dict[str, str]]] | None
    Any,
    str,
]:
    """Create a Serper.dev search function if API key is available.

    Returns:
        Tuple of (search_fn, status_message).
        search_fn is None if API key is not configured.
    """
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return None, "SERPER_API_KEY not set -- web search disabled"

    def search_fn(query: str) -> list[dict[str, str]]:
        return _serper_search_with_retry(query, api_key)

    return search_fn, "Serper.dev web search enabled (with retry & circuit breaker)"


def _serper_search_with_retry(
    query: str,
    api_key: str,
    num_results: int = 10,
    max_retries: int = 3,
) -> list[dict[str, str]]:
    """Execute web search with retry logic and circuit breaker.
    
    Args:
        query: Search query string.
        api_key: Serper.dev API key.
        num_results: Number of results to return.
        max_retries: Maximum number of retry attempts (including initial).
    
    Returns:
        List of result dicts with 'title', 'url', 'snippet' keys.
    """
    # Check circuit breaker before attempting
    if _check_circuit_breaker():
        return []
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "q": query,
        "num": num_results,
    }
    
    last_exception: Exception | None = None
    
    for attempt in range(max_retries):
        try:
            # Exponential backoff: 1s, 2s, 4s
            if attempt > 0:
                backoff = 2 ** (attempt - 1)
                logger.debug("Retry attempt %d after %d seconds", attempt, backoff)
                time.sleep(backoff)
            
            logger.debug("Serper search attempt %d: %s", attempt + 1, query[:100])
            client = _get_client()
            response = client.post(
                SERPER_BASE_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            # Success - reset circuit breaker
            _record_success()
            logger.debug("Serper search completed: %s", query[:100])
            
            return _parse_serper_results(data)
            
        except httpx.HTTPStatusError as exc:
            last_exception = exc
            status_code = exc.response.status_code
            logger.warning(
                "Serper.dev search failed (HTTP %d) on attempt %d: %s",
                status_code,
                attempt + 1,
                query[:80],
            )
            # Don't retry on client errors (4xx) except 429 (rate limit)
            if 400 <= status_code < 500 and status_code != 429:
                break
                
        except httpx.RequestError as exc:
            last_exception = exc
            logger.warning(
                "Serper.dev request error on attempt %d: %s",
                attempt + 1,
                exc,
            )
            # Retry on network errors
    
    # All retries failed
    _record_failure()
    logger.error(
        "Serper.dev search failed after %d attempts: %s",
        max_retries,
        query[:80],
    )
    return []


def _parse_serper_results(data: dict[str, Any]) -> list[dict[str, str]]:
    """Parse Serper.dev API response into list of result dicts."""
    results: list[dict[str, str]] = []
    
    # Parse organic results
    organic: list[Any] = data.get("organic", [])
    for raw_item in organic:
        if not isinstance(raw_item, dict):
            continue
        item = cast(dict[str, Any], raw_item)
        results.append({
            "title": str(item.get("title", "")),
            "url": str(item.get("link", "")),
            "snippet": str(item.get("snippet", "")),
        })
    
    # Also include news results if present
    news: list[Any] = data.get("news", [])
    for raw_item in news:
        if not isinstance(raw_item, dict):
            continue
        item = cast(dict[str, Any], raw_item)
        results.append({
            "title": str(item.get("title", "")),
            "url": str(item.get("link", "")),
            "snippet": str(item.get("snippet", "")),
        })
    
    logger.debug(
        "Serper.dev returned %d results for: %s",
        len(results),
        "query placeholder",  # Query not available in this function
    )
    return results


def health_check() -> tuple[bool, str]:
    """Check Serper.dev API connectivity.
    
    Returns:
        Tuple of (is_healthy, message).
    """
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    if not api_key:
        return False, "SERPER_API_KEY not set"
    
    # Simple test query that should return results
    test_query = "test"
    results = _serper_search_with_retry(test_query, api_key, num_results=1, max_retries=1)
    
    if results:
        return True, "Serper.dev API is responsive"
    else:
        return False, "Serper.dev API test query returned no results"


__all__ = ["create_serper_search_fn", "health_check"]
