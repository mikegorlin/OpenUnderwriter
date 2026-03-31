"""Blind spot discovery web search orchestrator.

Provides WebSearchClient with pluggable search function, budget tracking,
and priority-ordered blind spot discovery searches. The actual search
function is injected at runtime by the ACQUIRE stage orchestrator
(Plan 02-03) which has access to MCP tools (Brave Search).

Default search_fn returns empty results with a warning log.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from do_uw.cache.sqlite_cache import AnalysisCache

logger = logging.getLogger(__name__)

# Default search budget per analysis run.
DEFAULT_SEARCH_BUDGET = 10

# Monthly limit for Brave Search free tier.
MONTHLY_SEARCH_LIMIT = 2000
MONTHLY_WARN_THRESHOLD = 0.8  # Warn at 80% usage.

# Blind spot search categories in priority order.
BLIND_SPOT_SEARCHES: list[tuple[str, str]] = [
    (
        "litigation",
        '"{company}" lawsuit investigation fraud',
    ),
    (
        "regulatory",
        '"{company}" SEC subpoena Wells notice',
    ),
    (
        "short_seller",
        '"{company}" short seller report Hindenburg Muddy Waters Citron',
    ),
    (
        "whistleblower",
        '"{company}" restatement whistleblower scandal',
    ),
    (
        "industry_regulatory",
        '"{company}" FDA warning CFPB OSHA',
    ),
]

# Cache TTL for web search results: 30 days.
WEB_SEARCH_TTL = 30 * 24 * 3600


def _default_search_fn(query: str) -> list[dict[str, str]]:
    """Default no-op search function.

    Returns empty results and logs a warning. The real search function
    is injected by the ACQUIRE stage orchestrator.
    """
    logger.warning("No search function configured. Query not executed: %s", query)
    return []


class WebSearchClient:
    """Web search orchestrator with budget tracking.

    Provides single-query search and multi-query blind spot discovery.
    Search function is pluggable -- defaults to no-op, real implementation
    injected by the orchestrator at runtime.
    """

    def __init__(
        self,
        search_fn: Callable[[str], list[dict[str, str]]] | None = None,
        search_budget: int = DEFAULT_SEARCH_BUDGET,
    ) -> None:
        """Initialize with optional search function and budget.

        Args:
            search_fn: Callable that takes a query string and returns
                list of result dicts with 'title', 'url', 'snippet' keys.
                Defaults to a no-op that returns empty results.
            search_budget: Maximum searches per analysis run.
        """
        self._search_fn = search_fn or _default_search_fn
        self._budget = search_budget
        self._searches_used = 0

    @property
    def is_search_configured(self) -> bool:
        """Whether a real search function was injected (vs no-op default)."""
        return self._search_fn is not _default_search_fn

    @property
    def budget_remaining(self) -> int:
        """Number of searches remaining in current analysis budget."""
        return max(0, self._budget - self._searches_used)

    @property
    def searches_used(self) -> int:
        """Number of searches performed in current analysis."""
        return self._searches_used

    def search(
        self,
        query: str,
        cache: AnalysisCache | None = None,
    ) -> list[dict[str, str]]:
        """Perform a single web search with budget tracking.

        Args:
            query: Search query string.
            cache: Optional cache for results and monthly tracking.

        Returns:
            List of result dicts, or empty list if budget exhausted.
        """
        if self._searches_used >= self._budget:
            logger.warning(
                "Search budget exhausted (%d/%d). Skipping: %s",
                self._searches_used,
                self._budget,
                query,
            )
            return []

        # Check cache for this query.
        cache_key = f"websearch:{_query_hash(query)}"
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None and isinstance(cached, list):
                logger.debug("Cache hit for web search: %s", query[:60])
                return cast(list[dict[str, str]], cached)

        # Execute search.
        self._searches_used += 1
        results = self._search_fn(query)

        # Warn at 80% of per-analysis budget.
        if self._searches_used >= int(self._budget * MONTHLY_WARN_THRESHOLD):
            logger.warning(
                "Search budget at %d%% (%d/%d)",
                int(self._searches_used / self._budget * 100),
                self._searches_used,
                self._budget,
            )

        # Track monthly usage.
        _track_monthly_usage(cache)

        # Cache results.
        if cache is not None and results:
            cache.set(
                cache_key,
                results,
                source="web_search",
                ttl=WEB_SEARCH_TTL,
            )

        return results

    def blind_spot_sweep(
        self,
        company_name: str,
        ticker: str,
        cache: AnalysisCache | None = None,
    ) -> dict[str, list[dict[str, str]]]:
        """Run priority-ordered blind spot discovery searches.

        Searches in priority order, stopping if budget is exhausted.
        Higher priority searches (litigation, regulatory) run first.

        Args:
            company_name: Full company name for search queries.
            ticker: Stock ticker for supplementary queries.
            cache: Optional cache for results.

        Returns:
            Dict keyed by search category with lists of result dicts.
        """
        results: dict[str, list[dict[str, str]]] = {}

        for category, template in BLIND_SPOT_SEARCHES:
            if self.budget_remaining <= 0:
                logger.info(
                    "Budget exhausted, skipping remaining blind spot "
                    "searches (stopped before '%s')",
                    category,
                )
                break

            query = template.replace("{company}", company_name)
            category_results = self.search(query, cache=cache)
            results[category] = category_results

            logger.info(
                "Blind spot '%s': %d results (budget: %d/%d remaining)",
                category,
                len(category_results),
                self.budget_remaining,
                self._budget,
            )

        return results


def _query_hash(query: str) -> str:
    """Create a short, cache-safe hash of a search query."""
    import hashlib

    return hashlib.sha256(query.encode()).hexdigest()[:16]


def _track_monthly_usage(cache: AnalysisCache | None) -> None:
    """Increment monthly search counter and warn if approaching limit."""
    if cache is None:
        return

    month_key = f"brave:count:{datetime.now(tz=UTC).strftime('%Y-%m')}"
    current = cache.get(month_key)
    count = (current if isinstance(current, int) else 0) + 1

    cache.set(
        month_key,
        count,
        source="budget_tracker",
        ttl=45 * 24 * 3600,  # Keep for 45 days.
    )

    if count >= int(MONTHLY_SEARCH_LIMIT * MONTHLY_WARN_THRESHOLD):
        logger.warning(
            "Monthly Brave Search usage at %d/%d (%.0f%%)",
            count,
            MONTHLY_SEARCH_LIMIT,
            count / MONTHLY_SEARCH_LIMIT * 100,
        )
