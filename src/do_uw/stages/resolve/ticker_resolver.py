"""Ticker and company name resolution with fuzzy matching.

Maps stock tickers or company names to CIK numbers using SEC's
company_tickers.json with rapidfuzz for fuzzy matching.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date
from typing import Any, cast

from rapidfuzz import fuzz, process

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.stages.acquire.rate_limiter import sec_get

logger = logging.getLogger(__name__)

# SEC endpoint for all company tickers.
_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"

# Cache TTL: 30 days in seconds.
_TICKERS_CACHE_TTL = 30 * 24 * 60 * 60

# Fuzzy match thresholds.
_AUTO_MATCH_THRESHOLD = 90
_MIN_MATCH_THRESHOLD = 80


@dataclass(frozen=True)
class ResolvedTicker:
    """Result of ticker/company name resolution."""

    ticker: str
    cik: int
    company_name: str
    confidence: float  # 0-100 fuzzy match score; 100 for exact ticker match.
    all_tickers: list[str]


def _is_ticker_input(input_str: str) -> bool:
    """Detect if input looks like a ticker symbol."""
    stripped = input_str.strip()
    return (
        len(stripped) <= 5
        and stripped.isalpha()
        and stripped == stripped.upper()
    )


def _fetch_company_tickers(
    cache: AnalysisCache | None = None,
) -> list[dict[str, Any]]:
    """Fetch SEC company_tickers.json, using cache if available.

    Returns list of dicts with keys: cik_str, ticker, title.
    """
    cache_key = f"sec:tickers:company_tickers:{date.today().isoformat()}"

    if cache is not None:
        cached = cache.get(cache_key)
        if cached is not None:
            return cast(list[dict[str, Any]], cached)

    raw = sec_get(_COMPANY_TICKERS_URL)

    # SEC returns {"0": {"cik_str": ..., "ticker": ..., "title": ...}, ...}
    entries: list[dict[str, Any]] = list(raw.values())

    if cache is not None:
        cache.set(cache_key, entries, source="SEC EDGAR", ttl=_TICKERS_CACHE_TTL)

    return entries


def _group_by_cik(
    entries: list[dict[str, Any]],
) -> dict[int, list[dict[str, Any]]]:
    """Group company_tickers entries by CIK for parent entity resolution."""
    groups: dict[int, list[dict[str, Any]]] = {}
    for entry in entries:
        cik = int(entry["cik_str"])
        if cik not in groups:
            groups[cik] = []
        groups[cik].append(entry)
    return groups


def resolve_ticker(
    input_str: str,
    cache: AnalysisCache | None = None,
) -> ResolvedTicker:
    """Resolve a ticker symbol or company name to CIK and identity.

    If input is a ticker (uppercase, <= 5 chars, alpha): exact lookup.
    If input is a company name: fuzzy match against SEC company list.

    Args:
        input_str: Ticker symbol (e.g. "AAPL") or company name (e.g. "Apple").
        cache: Optional cache for SEC data.

    Returns:
        ResolvedTicker with CIK, company name, and confidence.

    Raises:
        ValueError: If no match is found.
    """
    stripped = input_str.strip()
    if not stripped:
        msg = "Input cannot be empty"
        raise ValueError(msg)

    entries = _fetch_company_tickers(cache)
    cik_groups = _group_by_cik(entries)

    if _is_ticker_input(stripped):
        return _resolve_by_ticker(stripped, entries, cik_groups)
    return _resolve_by_name(stripped, entries, cik_groups)


def _resolve_by_ticker(
    ticker: str,
    entries: list[dict[str, Any]],
    cik_groups: dict[int, list[dict[str, Any]]],
) -> ResolvedTicker:
    """Exact ticker lookup in SEC company list."""
    upper_ticker = ticker.upper()
    for entry in entries:
        if entry["ticker"].upper() == upper_ticker:
            cik = int(entry["cik_str"])
            all_tickers = _get_all_tickers(cik, cik_groups)
            logger.info(
                "Ticker %s resolved to CIK %d (%s)",
                ticker,
                cik,
                entry["title"],
            )
            return ResolvedTicker(
                ticker=upper_ticker,
                cik=cik,
                company_name=str(entry["title"]),
                confidence=100.0,
                all_tickers=all_tickers,
            )
    msg = f"Ticker '{ticker}' not found in SEC company list"
    raise ValueError(msg)


def _resolve_by_name(
    name: str,
    entries: list[dict[str, Any]],
    cik_groups: dict[int, list[dict[str, Any]]],
) -> ResolvedTicker:
    """Fuzzy match company name against SEC company list."""
    # Build name-to-entry lookup.
    name_to_entry: dict[str, dict[str, Any]] = {}
    for entry in entries:
        title = str(entry["title"])
        if title not in name_to_entry:
            name_to_entry[title] = entry

    # Normalize to lowercase for case-insensitive matching.
    # Without this, "HINGE HEALTH" matches "CARDINAL HEALTH INC" (85.5)
    # instead of "Hinge Health, Inc." (28.4) due to WRatio case sensitivity.
    lower_to_original: dict[str, str] = {}
    for title in name_to_entry:
        lower_to_original[title.lower()] = title

    results = process.extract(
        name.lower(),
        lower_to_original.keys(),
        scorer=fuzz.WRatio,
        limit=5,
        score_cutoff=_MIN_MATCH_THRESHOLD,
    )

    if not results:
        msg = f"No company match found for '{name}' (threshold: {_MIN_MATCH_THRESHOLD})"
        raise ValueError(msg)

    # Map back to original-case title for entry lookup.
    best_name = lower_to_original[results[0][0]]
    best_score = results[0][1]
    second_score = results[1][1] if len(results) > 1 else 0.0

    # Auto-proceed if best is strong and clearly better than runner-up.
    if best_score >= _AUTO_MATCH_THRESHOLD and second_score < _MIN_MATCH_THRESHOLD:
        entry = name_to_entry[best_name]
        cik = int(entry["cik_str"])
        all_tickers = _get_all_tickers(cik, cik_groups)
        logger.info(
            "Name '%s' matched to '%s' (score=%.1f, CIK=%d)",
            name,
            best_name,
            best_score,
            cik,
        )
        return ResolvedTicker(
            ticker=str(entry["ticker"]),
            cik=cik,
            company_name=str(best_name),
            confidence=float(best_score),
            all_tickers=all_tickers,
        )

    # If best is above threshold but ambiguous, use the best match.
    entry = name_to_entry[best_name]
    cik = int(entry["cik_str"])
    all_tickers = _get_all_tickers(cik, cik_groups)
    logger.info(
        "Name '%s' best match: '%s' (score=%.1f, CIK=%d)",
        name,
        best_name,
        best_score,
        cik,
    )
    return ResolvedTicker(
        ticker=str(entry["ticker"]),
        cik=cik,
        company_name=str(best_name),
        confidence=float(best_score),
        all_tickers=all_tickers,
    )


def _get_all_tickers(
    cik: int,
    cik_groups: dict[int, list[dict[str, Any]]],
) -> list[str]:
    """Get all tickers sharing the same CIK, sorted alphabetically."""
    group = cik_groups.get(cik, [])
    tickers = sorted({str(e["ticker"]).upper() for e in group})
    return tickers
