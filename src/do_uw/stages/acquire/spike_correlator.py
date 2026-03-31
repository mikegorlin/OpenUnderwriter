"""Volume spike event correlation via web search.

Runs in ACQUIRE stage (per CLAUDE.md MCP boundary). Takes pre-computed
spike events from detect_volume_spikes() and searches for catalysts
(earnings announcements, lawsuits filed, analyst downgrades, etc.)
that explain each volume spike.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Max spikes to search for (budget protection).
MAX_SPIKE_SEARCHES = 5


def correlate_volume_spikes(
    spike_events: list[dict[str, Any]],
    company_name: str,
    ticker: str,
    search_fn: Callable[[str], list[dict[str, str]]],
    max_searches: int = MAX_SPIKE_SEARCHES,
) -> list[dict[str, Any]]:
    """Enrich volume spike events with catalyst context from web search.

    Args:
        spike_events: List of spike dicts from detect_volume_spikes().
        company_name: Company name for search queries.
        ticker: Stock ticker for search queries.
        search_fn: Pluggable web search function (injected from orchestrator).
        max_searches: Max number of spikes to search (budget protection).

    Returns:
        The same spike_events list with 'catalyst' field added to each.
        Spikes not searched (beyond max_searches) get catalyst=None.
    """
    if not spike_events:
        return spike_events

    # Sort by volume_multiple descending -- search the biggest spikes first.
    ranked = sorted(
        enumerate(spike_events),
        key=lambda x: x[1].get("volume_multiple", 0),
        reverse=True,
    )

    searched = 0
    for idx, spike in ranked:
        if searched >= max_searches:
            spike_events[idx].setdefault("catalyst", None)
            continue

        date_str = spike.get("date", "")
        query = f'"{company_name}" OR "{ticker}" {date_str} stock'
        try:
            results = search_fn(query)
            catalyst = _extract_catalyst(results)
            spike_events[idx]["catalyst"] = catalyst
            if catalyst:
                logger.info(
                    "VOL CORRELATE: %s spike catalyst: %s",
                    date_str,
                    catalyst[:80],
                )
        except Exception:
            logger.warning(
                "VOL CORRELATE: Search failed for spike %s",
                date_str,
                exc_info=True,
            )
            spike_events[idx]["catalyst"] = None
        searched += 1

    return spike_events


def _extract_catalyst(
    results: list[dict[str, str]],
) -> str | None:
    """Extract the most relevant catalyst headline from search results.

    Returns the title/snippet of the first result, or None if empty.
    Search results are already relevance-ranked by Brave Search.
    """
    if not results:
        return None
    for r in results:
        title = r.get("title", "").strip()
        snippet = r.get("description", r.get("snippet", "")).strip()
        if title:
            return f"{title}: {snippet}" if snippet else title
    return None
