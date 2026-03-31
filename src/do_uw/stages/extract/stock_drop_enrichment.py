"""Drop event enrichment from 8-K filings and web search results.

Enriches StockDropEvent instances with:
- 8-K content (item numbers, description, category) when a filing
  is found near the drop date
- Web search context when no 8-K is available
- Trigger category classification

Separated from stock_drops.py for 500-line compliance.
"""

from __future__ import annotations

import logging
import re
from typing import Any, cast

from do_uw.models.market_events import StockDropEvent
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Item number to D&O-relevant category mapping.
_ITEM_CATEGORY: dict[str, str] = {
    "1.01": "agreement",
    "2.01": "acquisition",
    "2.02": "earnings_miss",
    "2.05": "restructuring",
    "2.06": "material_impairment",
    "3.01": "delisting",
    "4.02": "restatement",
    "5.02": "management_departure",
    "8.01": "other_event",
}

# 8-K item patterns to search for in raw text.
_ITEM_PATTERN = re.compile(
    r"Item\s+(\d+\.\d+)", re.IGNORECASE
)

# Category keywords for web search result matching.
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "earnings_miss": ["earnings", "missed", "miss", "revenue shortfall", "below expectations", "profit warning"],
    "guidance_cut": ["guidance", "lowered", "cut guidance", "revised down", "outlook"],
    "litigation": ["lawsuit", "sued", "litigation", "class action", "settlement", "indictment"],
    "analyst_downgrade": ["downgrade", "downgraded", "price target cut", "sell rating"],
    "regulatory": ["fda", "sec investigation", "regulatory", "enforcement", "fine", "penalty", "recall"],
    "management_departure": ["ceo resign", "cfo depart", "executive leave", "fired", "terminated"],
    "restatement": ["restatement", "restated", "accounting error", "material weakness"],
    "acquisition": ["acquisition", "merger", "deal", "takeover", "buyout"],
    "market_wide": ["market sell-off", "broad market", "recession", "fed rate", "tariff"],
}


# ---------------------------------------------------------------------------
# 8-K enrichment
# ---------------------------------------------------------------------------


def enrich_drops_from_8k(
    drops: list[StockDropEvent],
    state: AnalysisState,
) -> list[StockDropEvent]:
    """Enrich drop events using 8-K filing documents.

    For each drop with an 8-K trigger (or one near an 8-K date),
    extracts item numbers and a description from the filing text.
    """
    filing_docs = _get_8k_documents(state)
    if not filing_docs:
        return drops

    for drop in drops:
        if not drop.date:
            continue

        drop_date = drop.date.value[:10]

        # Find 8-K filing(s) within ±3 days of the drop.
        matched_docs = _find_8k_near_date(filing_docs, drop_date)
        if not matched_docs:
            continue

        # Extract item numbers and build description from first match.
        doc = matched_docs[0]
        full_text = doc.get("full_text", "")
        filing_date = doc.get("filing_date", "")

        items = _extract_items_from_text(full_text)
        if items:
            drop.trigger_8k_items = items

        description = _build_8k_description(doc, items)
        if description:
            drop.trigger_description = description

        category = _categorize_from_8k(items, full_text)
        if category:
            drop.trigger_category = category

        # Ensure trigger_event is set.
        if not drop.trigger_event:
            from do_uw.models.common import Confidence
            from do_uw.stages.extract.sourced import sourced_str

            drop.trigger_event = sourced_str(
                "8-K_filing", "SEC EDGAR filing", Confidence.HIGH,
            )

        # Set URL if not already set.
        if not drop.trigger_source_url:
            accession = doc.get("accession", "")
            if accession:
                drop.trigger_source_url = (
                    f"https://www.sec.gov/cgi-bin/browse-edgar"
                    f"?action=getcompany&accession={accession}&type=8-K"
                )

        logger.info(
            "Drop %s enriched: items=%s category=%s desc=%.60s",
            drop_date, items, category, description,
        )

    return drops


def _get_8k_documents(state: AnalysisState) -> list[dict[str, Any]]:
    """Get 8-K filing documents from acquired data."""
    if state.acquired_data is None:
        return []
    docs = state.acquired_data.filing_documents.get("8-K", [])
    if not isinstance(docs, list):
        return []
    return cast(list[dict[str, Any]], docs)


def _find_8k_near_date(
    docs: list[dict[str, Any]], target_date: str,
) -> list[dict[str, Any]]:
    """Find 8-K documents filed within ±3 days of target date."""
    from datetime import datetime as dt

    try:
        target = dt.strptime(target_date[:10], "%Y-%m-%d")
    except (ValueError, IndexError):
        return []

    matched: list[dict[str, Any]] = []
    for doc in docs:
        filing_date = doc.get("filing_date", "")
        if not filing_date:
            continue
        try:
            fd = dt.strptime(filing_date[:10], "%Y-%m-%d")
            if abs((fd - target).days) <= 3:
                matched.append(doc)
        except (ValueError, IndexError):
            continue

    # Sort by closest to target date.
    matched.sort(
        key=lambda d: abs(
            (dt.strptime(d.get("filing_date", "")[:10], "%Y-%m-%d") - target).days
        ),
    )
    return matched


def _extract_items_from_text(text: str) -> list[str]:
    """Extract 8-K item numbers from filing text."""
    matches = _ITEM_PATTERN.findall(text)
    # Deduplicate while preserving order.
    seen: set[str] = set()
    items: list[str] = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            items.append(m)
    # Filter to known SEC 8-K items (1.01 - 9.01).
    return [i for i in items if _is_valid_8k_item(i)]


def _is_valid_8k_item(item: str) -> bool:
    """Check if an item number is a valid 8-K item."""
    try:
        major = int(item.split(".")[0])
        return 1 <= major <= 9
    except (ValueError, IndexError):
        return False


def _build_8k_description(doc: dict[str, Any], items: list[str]) -> str:
    """Build a one-line description from 8-K document content."""
    parts: list[str] = []

    # Use event_type if available from LLM extraction.
    event_type = doc.get("event_type")
    if event_type:
        parts.append(str(event_type))

    # Add item descriptions.
    item_names: dict[str, str] = {
        "1.01": "Material Agreement",
        "2.01": "Acquisition/Disposition",
        "2.02": "Financial Results",
        "2.05": "Restructuring/Exit",
        "2.06": "Material Impairment",
        "3.01": "Delisting Notice",
        "4.01": "Auditor Change",
        "4.02": "Financial Restatement",
        "5.02": "Executive Change",
        "5.03": "Bylaw Amendment",
        "7.01": "Regulation FD Disclosure",
        "8.01": "Other Events",
        "9.01": "Exhibits",
    }

    if not parts:
        named = [item_names.get(i, f"Item {i}") for i in items if i != "9.01"]
        if named:
            parts.append(", ".join(named))

    # Extract a snippet from the full text for context.
    full_text = doc.get("full_text", "")
    snippet = _extract_key_snippet(full_text, items)
    if snippet:
        parts.append(snippet)

    return " — ".join(parts) if parts else ""


def _extract_key_snippet(text: str, items: list[str]) -> str:
    """Extract a key snippet from 8-K text near the first item reference.

    Returns up to 120 chars of context after the item header.
    """
    if not text or not items:
        return ""

    # Find text after the first significant item (skip 9.01 exhibits).
    for item in items:
        if item == "9.01":
            continue
        pattern = re.compile(
            rf"Item\s+{re.escape(item)}[^\n]*\n(.*?)(?:Item\s+\d+\.\d+|\Z)",
            re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(text)
        if match:
            body = match.group(1).strip()
            # Clean up whitespace and take first meaningful sentence.
            body = re.sub(r"\s+", " ", body)
            # Skip boilerplate.
            for line in body.split(". "):
                line = line.strip()
                if len(line) > 30 and not _is_boilerplate(line):
                    return line[:120].rstrip() + ("..." if len(line) > 120 else "")
    return ""


def _is_boilerplate(text: str) -> bool:
    """Check if text is SEC boilerplate."""
    lower = text.lower()
    boilerplate = [
        "pursuant to the requirements",
        "this current report",
        "the registrant",
        "filed herewith",
        "incorporated by reference",
        "signature",
        "exhibit",
    ]
    return any(b in lower for b in boilerplate)


def _categorize_from_8k(items: list[str], text: str) -> str:
    """Determine trigger category from 8-K items and text."""
    # Priority order: most D&O-relevant items first.
    priority = ["4.02", "2.02", "5.02", "2.06", "2.05", "2.01", "1.01", "3.01", "8.01"]
    for item in priority:
        if item in items:
            return _ITEM_CATEGORY.get(item, "other_event")

    # Fallback: scan text for keywords.
    lower = text.lower()
    if "restatement" in lower or "non-reliance" in lower:
        return "restatement"
    if "guidance" in lower and ("lower" in lower or "reduc" in lower):
        return "guidance_cut"
    return "other_event"


# ---------------------------------------------------------------------------
# Web search enrichment
# ---------------------------------------------------------------------------


def enrich_drops_from_web(
    drops: list[StockDropEvent],
    state: AnalysisState,
) -> list[StockDropEvent]:
    """Enrich unexplained drops using already-acquired web search results.

    For drops that have no trigger after 8-K enrichment, searches the
    acquired web_search_results for matching context by date and company.
    """
    web_results = _get_web_search_results(state)
    if not web_results:
        return drops

    company_name = state.company.identity.legal_name.value if state.company and state.company.identity.legal_name else ""

    for drop in drops:
        # Skip already-explained drops.
        if drop.trigger_description:
            continue
        if not drop.date:
            continue

        drop_date = drop.date.value[:10]

        # Search web results for context near this drop date.
        matches = _search_web_results_for_drop(
            web_results, drop_date, company_name, state.ticker,
        )
        if matches:
            best = matches[0]
            drop.trigger_description = best.get("snippet", "")[:150]
            drop.trigger_source_url = drop.trigger_source_url or best.get("url", "")
            category = _categorize_from_text(best.get("snippet", ""))
            if category:
                drop.trigger_category = category

            logger.info(
                "Drop %s enriched from web: category=%s desc=%.60s",
                drop_date, category, drop.trigger_description,
            )

    return drops


def _get_web_search_results(state: AnalysisState) -> list[dict[str, Any]]:
    """Get web search results from acquired data."""
    if state.acquired_data is None:
        return []
    raw = state.acquired_data.web_search_results
    if isinstance(raw, list):
        return cast(list[dict[str, Any]], raw)
    if isinstance(raw, dict):
        # May be keyed by query.
        all_results: list[dict[str, Any]] = []
        for _key, val in raw.items():
            if isinstance(val, list):
                all_results.extend(cast(list[dict[str, Any]], val))
        return all_results
    return []


def _search_web_results_for_drop(
    results: list[dict[str, Any]],
    drop_date: str,
    company_name: str,
    ticker: str,
) -> list[dict[str, Any]]:
    """Find web search results relevant to a specific drop date.

    Matches results by:
    1. Date proximity (publication date within ±5 days)
    2. Content relevance (mentions stock, drop, decline, etc.)
    """
    from datetime import datetime as dt

    try:
        target = dt.strptime(drop_date[:10], "%Y-%m-%d")
    except (ValueError, IndexError):
        return []

    scored: list[tuple[float, dict[str, Any]]] = []
    drop_keywords = {"drop", "fell", "decline", "plunge", "crash", "tumble", "slide", "loss", "down"}

    for result in results:
        score = 0.0
        snippet = str(result.get("snippet", "") or result.get("description", "")).lower()
        title = str(result.get("title", "")).lower()
        pub_date = result.get("date", "") or result.get("published", "")

        # Date proximity.
        if pub_date:
            try:
                pub = dt.strptime(str(pub_date)[:10], "%Y-%m-%d")
                days_diff = abs((pub - target).days)
                if days_diff <= 5:
                    score += 10.0 - days_diff
                else:
                    continue  # Too far from drop date.
            except (ValueError, IndexError):
                pass

        # Content relevance.
        text = f"{title} {snippet}"
        if ticker.lower() in text or company_name.lower() in text:
            score += 5.0
        if any(kw in text for kw in drop_keywords):
            score += 3.0
        if "stock" in text:
            score += 2.0

        if score > 5.0:  # Minimum relevance threshold.
            scored.append((score, result))

    scored.sort(key=lambda x: -x[0])
    return [r for _, r in scored[:3]]


def _categorize_from_text(text: str) -> str:
    """Determine trigger category from descriptive text."""
    lower = text.lower()
    best_category = ""
    best_score = 0

    for category, keywords in _CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in lower)
        if score > best_score:
            best_score = score
            best_category = category

    return best_category or "unknown"


# ---------------------------------------------------------------------------
# Corrective disclosure reverse lookup (Phase 90)
# ---------------------------------------------------------------------------

# D&O-relevant 8-K items that qualify as corrective disclosures.
D_AND_O_RELEVANT_8K_ITEMS: set[str] = {"2.02", "4.02", "5.02", "2.06"}


def _find_8k_after_drop(
    docs: list[dict[str, Any]],
    drop_date: str,
    max_lag_days: int = 14,
) -> list[tuple[dict[str, Any], int]]:
    """Find 8-K filings with D&O-relevant items filed 1-14 days AFTER drop.

    Args:
        docs: List of 8-K filing documents with filing_date and items fields.
        drop_date: Drop date as YYYY-MM-DD string.
        max_lag_days: Maximum days after drop to search (default 14).

    Returns:
        List of (doc, lag_days) tuples sorted by lag ascending.
    """
    from datetime import datetime as dt

    try:
        target = dt.strptime(drop_date[:10], "%Y-%m-%d")
    except (ValueError, IndexError):
        return []

    matches: list[tuple[dict[str, Any], int]] = []
    for doc in docs:
        filing_date = doc.get("filing_date", "")
        if not filing_date:
            continue

        try:
            fd = dt.strptime(filing_date[:10], "%Y-%m-%d")
        except (ValueError, IndexError):
            continue

        lag = (fd - target).days
        if lag < 1 or lag > max_lag_days:
            continue

        # Check if doc has D&O-relevant items.
        doc_items = doc.get("items", [])
        if not isinstance(doc_items, list):
            doc_items = []

        has_relevant = any(item in D_AND_O_RELEVANT_8K_ITEMS for item in doc_items)
        if not has_relevant:
            continue

        matches.append((doc, lag))

    matches.sort(key=lambda x: x[1])
    return matches


def _search_web_for_disclosure(
    web_results: list[dict[str, Any]],
    company_name: str,
    drop_date: str,
    window_days: int = 14,
) -> dict[str, Any] | None:
    """Search existing web results for articles published 1-14 days after drop.

    Args:
        web_results: Already-acquired web search results.
        company_name: Company name for matching.
        drop_date: Drop date as YYYY-MM-DD.
        window_days: Maximum days after drop to search.

    Returns:
        Best matching web result dict, or None.
    """
    from datetime import datetime as dt

    try:
        target = dt.strptime(drop_date[:10], "%Y-%m-%d")
    except (ValueError, IndexError):
        return None

    best: dict[str, Any] | None = None
    best_lag = window_days + 1

    company_lower = company_name.lower()

    for result in web_results:
        pub_date = result.get("date", "") or result.get("published", "")
        if not pub_date:
            continue

        try:
            pub = dt.strptime(str(pub_date)[:10], "%Y-%m-%d")
        except (ValueError, IndexError):
            continue

        lag = (pub - target).days
        if lag < 1 or lag > window_days:
            continue

        # Must mention company name.
        title = str(result.get("title", "")).lower()
        snippet = str(result.get("snippet", "")).lower()
        text = f"{title} {snippet}"

        if company_lower not in text:
            continue

        if lag < best_lag:
            best_lag = lag
            best = result

    return best


def enrich_drops_with_reverse_lookup(
    drops: list[StockDropEvent],
    docs: list[dict[str, Any]],
    web_results: list[dict[str, Any]],
    company_name: str,
) -> list[StockDropEvent]:
    """Enrich unexplained drops with corrective disclosure reverse lookup.

    For each drop that has no trigger_event (unexplained):
    1. Try finding an 8-K filed 1-14 days after the drop.
    2. Else try finding a web article published 1-14 days after.

    Args:
        drops: List of StockDropEvent instances.
        docs: 8-K filing documents.
        web_results: Already-acquired web search results.
        company_name: Company name for web search matching.

    Returns:
        Modified drops list with corrective disclosure fields set.
    """
    for drop in drops:
        # Skip already-explained drops.
        if drop.trigger_event:
            continue
        if not drop.date:
            continue

        drop_date = drop.date.value[:10]

        # Try 8-K reverse lookup.
        matches = _find_8k_after_drop(docs, drop_date)
        if matches:
            doc, lag = matches[0]
            drop.corrective_disclosure_type = "8-K"
            drop.corrective_disclosure_lag_days = lag
            accession = doc.get("accession", "")
            if accession:
                drop.corrective_disclosure_url = (
                    f"https://www.sec.gov/cgi-bin/browse-edgar"
                    f"?action=getcompany&accession={accession}&type=8-K"
                )
            continue

        # Fallback: web search.
        web_match = _search_web_for_disclosure(web_results, company_name, drop_date)
        if web_match:
            from datetime import datetime as dt

            pub_date = web_match.get("date", "") or web_match.get("published", "")
            try:
                pub = dt.strptime(str(pub_date)[:10], "%Y-%m-%d")
                target = dt.strptime(drop_date, "%Y-%m-%d")
                lag = (pub - target).days
            except (ValueError, IndexError):
                lag = None

            drop.corrective_disclosure_type = "news"
            drop.corrective_disclosure_lag_days = lag
            drop.corrective_disclosure_url = web_match.get("url", "")

    return drops


# ---------------------------------------------------------------------------
# Mark unexplained drops
# ---------------------------------------------------------------------------


def mark_unexplained_drops(drops: list[StockDropEvent]) -> list[StockDropEvent]:
    """Set trigger_category='unknown' for drops with no explanation.

    Unexplained significant drops are themselves a D&O risk signal —
    they may indicate undisclosed material information.
    """
    for drop in drops:
        if drop.trigger_category:
            continue
        if drop.is_market_wide and not drop.is_company_specific:
            drop.trigger_category = "market_wide"
        else:
            drop.trigger_category = "unknown"

    return drops


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def enrich_all_drops(
    drops: list[StockDropEvent],
    state: AnalysisState,
) -> list[StockDropEvent]:
    """Full enrichment pipeline for drop events.

    1. Enrich from 8-K filing documents
    2. Enrich remaining from web search results
    3. Mark any still-unexplained drops
    """
    drops = enrich_drops_from_8k(drops, state)
    drops = enrich_drops_from_web(drops, state)
    drops = mark_unexplained_drops(drops)
    return drops


__all__ = [
    "D_AND_O_RELEVANT_8K_ITEMS",
    "enrich_all_drops",
    "enrich_drops_from_8k",
    "enrich_drops_from_web",
    "enrich_drops_with_reverse_lookup",
    "mark_unexplained_drops",
]
