"""Serper.dev web search client for pipeline web search integration.

Provides a search function compatible with WebSearchClient's pluggable
search_fn interface. Returns list of dicts with 'title', 'url', 'snippet'.

Requires SERPER_API_KEY environment variable.
"""

from __future__ import annotations

import logging
import os
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)

SERPER_BASE_URL = "https://google.serper.dev/search"
SERPER_NEWS_URL = "https://google.serper.dev/news"


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
        return _serper_search(query, api_key)

    return search_fn, "Serper.dev web search enabled"


def _serper_search(
    query: str,
    api_key: str,
    num_results: int = 10,
) -> list[dict[str, str]]:
    """Execute a web search via Serper.dev API.

    Args:
        query: Search query string.
        api_key: Serper.dev API key.
        num_results: Number of results to return.

    Returns:
        List of result dicts with 'title', 'url', 'snippet' keys.
    """
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload: dict[str, Any] = {
        "q": query,
        "num": num_results,
    }

    try:
        logger.debug("Serper search executing: %s", query[:100])
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                SERPER_BASE_URL,
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        logger.debug("Serper search completed: %s", query[:100])
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Serper.dev search failed (HTTP %d): %s",
            exc.response.status_code,
            query[:80],
        )
        return []
    except httpx.RequestError as exc:
        logger.warning("Serper.dev request error: %s", exc)
        return []

    results: list[dict[str, str]] = []

    # Parse organic results.
    organic: list[Any] = data.get("organic", [])
    for raw_item in organic:
        if not isinstance(raw_item, dict):
            continue
        item = cast(dict[str, Any], raw_item)
        results.append(
            {
                "title": str(item.get("title", "")),
                "url": str(item.get("link", "")),
                "snippet": str(item.get("snippet", "")),
            }
        )

    # Also include news results if present.
    news: list[Any] = data.get("news", [])
    for raw_item in news:
        if not isinstance(raw_item, dict):
            continue
        item = cast(dict[str, Any], raw_item)
        results.append(
            {
                "title": str(item.get("title", "")),
                "url": str(item.get("link", "")),
                "snippet": str(item.get("snippet", "")),
            }
        )

    logger.debug(
        "Serper.dev returned %d results for: %s",
        len(results),
        query[:60],
    )
    return results


__all__ = ["create_serper_search_fn"]
