"""Phase E: Brain-driven gap search for SKIPPED checks.

After all structured ACQUIRE completes, checks with gap_bucket fields in brain
YAML that lack data_strategy routing receive targeted web searches.
Non-L1 checks only. Budget capped at min(budget_remaining, GAP_SEARCH_MAX).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml  # PyYAML — already in project

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.acquire.clients.web_search import WEB_SEARCH_TTL, WebSearchClient

logger = logging.getLogger(__name__)

GAP_SEARCH_MAX = 15  # Maximum gap searches per run (draws from shared 50-budget)

_BRAIN_CHECKS_DIR = Path(__file__).parent.parent.parent / "brain" / "signals"

# Gap bucket priority order for ranking (lower index = higher priority)
_GAP_BUCKET_ORDER = ["routing-gap", "aspirational", "intentionally-unmapped"]


def _load_gap_eligible_checks() -> list[dict[str, Any]]:
    """Load non-L1 checks with gap_bucket from brain YAML files.

    Walks brain/signals/**/*.yaml and returns checks that have:
    1. A gap_bucket field (was set in Plan 01)
    2. acquisition_tier that is NOT "L1" (hard code-level gate)

    Returns:
        List of check dicts with id, name, acquisition_tier, gap_bucket,
        gap_keywords, and tier fields.
    """
    eligible: list[dict[str, Any]] = []

    for yaml_path in sorted(_BRAIN_CHECKS_DIR.glob("**/*.yaml")):
        try:
            with yaml_path.open("r", encoding="utf-8") as fh:
                entries = yaml.safe_load(fh)
        except Exception as exc:
            logger.warning("Failed to load brain YAML %s: %s", yaml_path, exc)
            continue

        if not isinstance(entries, list):
            continue

        for entry in entries:
            if not isinstance(entry, dict):
                continue

            signal_id = entry.get("id")
            if not signal_id:
                continue

            # Must have gap_bucket (set in Plan 01)
            if "gap_bucket" not in entry:
                continue

            # Hard L1 gate — ineligible regardless of gap_bucket
            tier = entry.get("acquisition_tier", "")
            if tier == "L1":
                continue

            eligible.append({
                "id": signal_id,
                "name": entry.get("name", signal_id),
                "acquisition_tier": tier,
                "gap_bucket": entry.get("gap_bucket", ""),
                "gap_keywords": entry.get("gap_keywords", []),
                "tier": entry.get("tier", 99),
                "required_data": entry.get("required_data", []),
            })

    return eligible


def _rank_by_severity(
    checks: list[dict[str, Any]], max_count: int
) -> list[dict[str, Any]]:
    """Sort checks by priority (tier asc, then gap_bucket order).

    Args:
        checks: List of eligible check dicts.
        max_count: Maximum number of checks to return.

    Returns:
        Sorted, capped list of checks.
    """
    def sort_key(check: dict[str, Any]) -> tuple[int, int]:
        tier = int(check.get("tier", 99))
        bucket = check.get("gap_bucket", "")
        bucket_rank = (
            _GAP_BUCKET_ORDER.index(bucket)
            if bucket in _GAP_BUCKET_ORDER
            else len(_GAP_BUCKET_ORDER)
        )
        return (tier, bucket_rank)

    return sorted(checks, key=sort_key)[:max_count]


def _extract_domain(url: str) -> str:
    """Extract domain from URL, stripping www. prefix.

    Args:
        url: Full URL string.

    Returns:
        Domain string, or empty string on parse failure.
    """
    try:
        netloc = urlparse(url).netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _evaluate_evidence(
    results: list[dict[str, str]], keywords: list[str]
) -> tuple[bool, str]:
    """Apply evidence quality gate: check if any keyword appears in results.

    Args:
        results: List of search result dicts with title/snippet/url.
        keywords: List of keywords to look for (case-insensitive).

    Returns:
        (matched, domain) where matched=True if keyword found,
        domain is the netloc of the first matching result's URL.
        Returns (False, "") if keywords empty or results empty.
    """
    if not keywords or not results:
        return False, ""

    lower_keywords = [kw.lower() for kw in keywords]

    for result in results:
        # Check all text fields
        text_parts = [
            result.get("snippet", ""),
            result.get("description", ""),
            result.get("title", ""),
        ]
        combined = " ".join(part.lower() for part in text_parts if part)

        for keyword in lower_keywords:
            if keyword in combined:
                domain = _extract_domain(result.get("url", ""))
                return True, domain

    return False, ""


def run_gap_search(
    state: AnalysisState,
    acquired: AcquiredData,
    web_search: WebSearchClient,
    cache: AnalysisCache | None,
) -> None:
    """Execute Phase E: targeted web searches for non-L1 SKIPPED checks.

    Reads eligible signals from brain YAML, generates company-specific queries,
    executes them within budget, applies evidence quality gate, stores results.

    Args:
        state: Analysis state with ticker and company identity.
        acquired: AcquiredData to write brain_targeted_search results into.
        web_search: Shared WebSearchClient (budget already reflects A-D usage).
        cache: Optional cache for result storage and retrieval.
    """
    available = min(web_search.budget_remaining, GAP_SEARCH_MAX)
    if available <= 0:
        logger.info(
            "Phase E: No budget available for gap search "
            "(budget_remaining=%d, max=%d)",
            web_search.budget_remaining,
            GAP_SEARCH_MAX,
        )
        return

    # Load and rank eligible checks
    eligible = _load_gap_eligible_checks()
    if not eligible:
        logger.info("Phase E: No gap-eligible checks found in brain YAML")
        return

    ranked = _rank_by_severity(eligible, max_count=len(eligible))
    company_name = _get_company_name(state)
    ticker = state.ticker

    # Lazy import to avoid circular imports and module-load failures
    from do_uw.stages.acquire.gap_query_generator import (
        generate_gap_queries_batch,
    )

    # Batch query generation for efficiency
    queries = generate_gap_queries_batch(ranked[:available], company_name, ticker)

    searched = 0
    cached_hits = 0

    for check in ranked:
        if searched >= available:
            break

        signal_id = check["id"]
        keywords = check.get("gap_keywords", [])

        # Skip checks with empty keywords — unevaluable, not CLEAR
        if not keywords:
            logger.debug(
                "Phase E: Skipping check %s — empty gap_keywords "
                "(unevaluable, not marked CLEAR)",
                signal_id,
            )
            continue

        # Check cache first
        cache_key = f"gap_search:{ticker}:{signal_id}"
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None and isinstance(cached, dict):
                acquired.brain_targeted_search[signal_id] = cached
                cached_hits += 1
                logger.debug(
                    "Phase E: Cache hit for check %s (not counted against budget)",
                    signal_id,
                )
                continue

        # Generate query (use batch-generated or fall back to per-check)
        query = queries.get(signal_id)
        if not query:
            from do_uw.stages.acquire.gap_query_generator import generate_gap_query
            query = generate_gap_query(check, company_name, ticker)

        # Execute search (increments web_search._searches_used)
        results = web_search.search(query, cache=cache)
        searched += 1

        if not results:
            logger.debug(
                "Phase E: No results for check %s (not stored)", signal_id
            )
            continue

        # Apply evidence quality gate
        keywords_matched, domain = _evaluate_evidence(results, keywords)
        suggested_status = "TRIGGERED" if keywords_matched else "CLEAR"

        gap_result: dict[str, Any] = {
            "query": query,
            "results_count": len(results),
            "keywords_matched": keywords_matched,
            "suggested_status": suggested_status,
            "domain": domain,
            "confidence": "LOW",
        }

        acquired.brain_targeted_search[signal_id] = gap_result

        # Cache the result for future runs
        if cache is not None:
            cache.set(
                cache_key,
                gap_result,
                source="gap_search",
                ttl=WEB_SEARCH_TTL,
            )

        logger.debug(
            "Phase E: check=%s query=%r results=%d matched=%s status=%s",
            signal_id,
            query[:60],
            len(results),
            keywords_matched,
            suggested_status,
        )

    unsearched = max(0, len(eligible) - searched - cached_hits)
    logger.info(
        "Gap search: %d/%d budget used, %d eligible checks unsearched",
        searched,
        available,
        unsearched,
    )


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name from state, falling back to ticker."""
    if (
        state.company is not None
        and state.company.identity.legal_name is not None
    ):
        return state.company.identity.legal_name.value
    return state.ticker


# ---------------------------------------------------------------------------
# Exa semantic search — second-pass blind spot discovery
# ---------------------------------------------------------------------------

# Maximum Exa queries per run (independent of web search budget)
EXA_QUERY_CAP = 5

# D&O-relevant semantic query templates
_EXA_QUERY_TEMPLATES: list[tuple[str, str]] = [
    (
        "accounting_fraud",
        "{company} accounting irregularities fraud investigation",
    ),
    (
        "executive_misconduct",
        "{company} executive misconduct insider trading",
    ),
    (
        "regulatory_enforcement",
        "{company} regulatory enforcement action penalty",
    ),
    (
        "shareholder_litigation",
        "{company} shareholder derivative lawsuit settlement",
    ),
]


def run_exa_semantic_search(
    company_name: str,
    ticker: str,
) -> dict[str, list[dict[str, Any]]]:
    """Run Exa semantic search as second-pass blind spot discovery.

    Uses D&O-relevant query templates to find risks that keyword search
    may miss. Exa's neural search is better at contextual matching.

    Independent of the web search budget — capped at EXA_QUERY_CAP (5).
    Only runs if EXA_API_KEY is set; returns empty dict otherwise.

    Args:
        company_name: Full company name for query templates.
        ticker: Stock ticker (for logging context).

    Returns:
        Dict keyed by query category (e.g., "accounting_fraud") with
        lists of Exa result dicts as values.
    """
    from do_uw.stages.acquire.clients.exa_client import ExaClient

    client = ExaClient()
    if not client.is_available:
        logger.info(
            "Exa semantic search skipped (no API key) for %s (%s)",
            company_name,
            ticker,
        )
        return {}

    results: dict[str, list[dict[str, Any]]] = {}
    queries_run = 0

    for category, template in _EXA_QUERY_TEMPLATES:
        if queries_run >= EXA_QUERY_CAP:
            logger.debug(
                "Exa query cap reached (%d/%d), stopping",
                queries_run,
                EXA_QUERY_CAP,
            )
            break

        query = template.replace("{company}", company_name)
        category_results = client.search_semantic(query, num_results=5)
        results[category] = category_results
        queries_run += 1

        logger.debug(
            "Exa semantic '%s': %d results for %s",
            category,
            len(category_results),
            ticker,
        )

    logger.info(
        "Exa semantic search: %d queries, %d total results for %s (%s)",
        queries_run,
        sum(len(v) for v in results.values()),
        company_name,
        ticker,
    )
    return results
