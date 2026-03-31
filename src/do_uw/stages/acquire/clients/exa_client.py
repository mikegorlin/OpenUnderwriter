"""Exa semantic search client for blind spot discovery.

Provides neural/semantic search via the Exa API, complementing keyword-based
search (Brave/Serper) for D&O risk discovery. Semantic search excels at
finding contextually relevant results that keyword search misses, such as
"accounting irregularities at {company}" or "executive misconduct".

Requires EXA_API_KEY environment variable. Gracefully degrades to empty
results when key is missing (pipeline completes with existing search data).

Usage:
    client = ExaClient()
    results = client.search_semantic("Apple accounting fraud investigation")
    # Returns list of dicts with title, url, snippet, score, source, confidence

Factory function:
    fn, msg = create_exa_search_fn()
    # Returns (callable, status) matching serper_client pattern
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from typing import Any

import httpx

logger = logging.getLogger(__name__)

EXA_BASE_URL = "https://api.exa.ai/search"


class ExaClient:
    """Semantic search client using the Exa API.

    Reads EXA_API_KEY from environment. If missing, all searches return
    empty lists with a warning log (graceful degradation).
    """

    def __init__(self) -> None:
        """Initialize with API key from environment."""
        self._api_key = os.environ.get("EXA_API_KEY", "").strip()
        if not self._api_key:
            logger.warning(
                "EXA_API_KEY not set -- Exa semantic search disabled"
            )

    @property
    def is_available(self) -> bool:
        """Whether the Exa API key is configured."""
        return bool(self._api_key)

    def search_semantic(
        self,
        query: str,
        num_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Execute a semantic search via Exa API.

        Args:
            query: Natural language search query.
            num_results: Number of results to return (default 5).

        Returns:
            List of result dicts with keys: title, url, snippet, score,
            published_date, source ("Exa"), confidence ("LOW").
            Returns empty list on any failure or missing API key.
        """
        if not self._api_key:
            return []

        headers = {
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "numResults": num_results,
            "type": "neural",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    EXA_BASE_URL,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Exa search failed (HTTP %d): %s",
                exc.response.status_code,
                query[:80],
            )
            return []
        except httpx.RequestError as exc:
            logger.warning("Exa request error: %s", exc)
            return []
        except Exception as exc:
            logger.warning("Exa unexpected error: %s", exc)
            return []

        results: list[dict[str, Any]] = []
        raw_results: list[Any] = data.get("results", [])

        for item in raw_results:
            if not isinstance(item, dict):
                continue
            results.append({
                "title": str(item.get("title", "")),
                "url": str(item.get("url", "")),
                "snippet": str(item.get("text", "")),
                "score": float(item.get("score", 0.0)),
                "published_date": str(item.get("publishedDate", "")),
                "source": "Exa",
                "confidence": "LOW",
            })

        logger.debug(
            "Exa returned %d results for: %s",
            len(results),
            query[:60],
        )
        return results


def create_exa_search_fn() -> tuple[
    Callable[[str], list[dict[str, Any]]] | None,
    str,
]:
    """Create an Exa search function if API key is available.

    Matches the serper_client pattern: returns (search_fn, status_message).
    search_fn is None if API key is not configured.

    Returns:
        Tuple of (search_fn, status_message).
    """
    api_key = os.environ.get("EXA_API_KEY", "").strip()
    if not api_key:
        return None, "EXA_API_KEY not set -- Exa semantic search disabled"

    client = ExaClient()

    def search_fn(query: str) -> list[dict[str, Any]]:
        return client.search_semantic(query)

    return search_fn, "Exa semantic search enabled"


__all__ = ["ExaClient", "create_exa_search_fn"]
