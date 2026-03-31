"""News and sentiment acquisition client.

Collects recent news from web search and yfinance. Web search provides
broader coverage; yfinance news provides structured article metadata.

Cache TTL: 30 days (news staleness threshold per user decisions).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.state import AnalysisState
from do_uw.stages.acquire.clients.web_search import WebSearchClient

logger = logging.getLogger(__name__)

# Cache TTL: 30 days for news data.
NEWS_TTL = 30 * 24 * 3600


class NewsClient:
    """News and sentiment data acquisition client.

    Collects news from web search and yfinance, tagged with source
    and confidence level.
    """

    def __init__(
        self,
        web_search: WebSearchClient | None = None,
    ) -> None:
        """Initialize with optional web search client.

        Args:
            web_search: WebSearchClient for web queries.
                Defaults to a new instance with default (no-op) search.
        """
        self._web_search = web_search or WebSearchClient()

    @property
    def name(self) -> str:
        """Client name for logging and identification."""
        return "news_sentiment"

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Acquire news data from web search and yfinance.

        Args:
            state: Analysis state with ticker and company identity.
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict with: web_news (list), yfinance_news (list).
        """
        ticker = state.ticker
        company_name = _get_company_name(state)
        cache_key = f"news:{ticker}:{datetime.now(tz=UTC).strftime('%Y-%m')}"

        # Check cache first.
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for news: %s", cache_key)
                return dict(cached)

        logger.info("Acquiring news for %s (%s)", ticker, company_name)

        # Web search for recent news.
        web_news = _search_web_news(
            self._web_search, company_name, state, cache
        )

        # yfinance news as secondary source.
        yfinance_news = _fetch_yfinance_news(ticker)

        result: dict[str, Any] = {
            "web_news": web_news,
            "yfinance_news": yfinance_news,
        }

        # Cache results.
        if cache is not None:
            cache.set(
                cache_key,
                result,
                source="news_client",
                ttl=NEWS_TTL,
            )

        return result


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name from state, falling back to ticker."""
    if (
        state.company is not None
        and state.company.identity.legal_name is not None
    ):
        return state.company.identity.legal_name.value
    return state.ticker


def _search_web_news(
    web_search: WebSearchClient,
    company_name: str,
    state: AnalysisState,
    cache: AnalysisCache | None,
) -> list[dict[str, str]]:
    """Run web searches for recent news about the company."""
    results: list[dict[str, str]] = []

    # Primary: company name + news.
    query = f'"{company_name}" news'
    results.extend(web_search.search(query, cache=cache))

    # Secondary: company + CEO name if known.
    ceo_name = _get_ceo_name(state)
    if ceo_name:
        query = f'"{company_name}" {ceo_name}'
        results.extend(web_search.search(query, cache=cache))

    logger.info("Web news search: %d results for %s", len(results), company_name)
    return results


def _get_ceo_name(state: AnalysisState) -> str | None:
    """Extract CEO name from state if available.

    This data may be populated by the RESOLVE stage or from
    market data. Returns None if not available.
    """
    # CEO name may come from yfinance info or SEC filings.
    # Not available until EXTRACT stage in many cases.
    return None


def _fetch_yfinance_news(ticker: str) -> list[dict[str, Any]]:
    """Fetch news articles from yfinance."""
    try:
        import yfinance as yf  # type: ignore[import-untyped]

        yf_ticker = yf.Ticker(ticker)
        raw_news: Any = getattr(yf_ticker, "news", None)
        if isinstance(raw_news, list):
            return cast(list[dict[str, Any]], raw_news)
        return []
    except Exception as exc:
        logger.warning("yfinance news fetch failed for %s: %s", ticker, exc)
        return []
