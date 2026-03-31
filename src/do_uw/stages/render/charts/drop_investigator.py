"""Drop catalyst investigator — web search per significant drop.

What a 30-year underwriter would actually do to explain a stock drop:

1. Check the date — what happened that week?
2. Search news — what was reported?
3. Check earnings — was there a miss? Guidance cut?
4. Check analyst actions — downgrades, target cuts?
5. Check competitor news — material announcements?
6. Check SEC filings — 8-K, S-3, 424B around that date?
7. Check insider trades — selling around that date?
8. Cross-reference — if beat earnings but dropped, WHY?

This module runs a targeted web search per drop cluster, then uses
DeepSeek to extract the actual cause from search results.

Called from build_drop_legend_data() after clustering, before rendering.
Replaces the template-based _context_aware_explanation garbage.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def investigate_drops(
    legend_data: list[dict[str, Any]],
    ticker: str,
    company_name: str = "",
    min_drop_pct: float = -5.0,
    max_searches: int = 12,
) -> list[dict[str, Any]]:
    """Investigate unexplained drops via web search + LLM extraction.

    Only investigates drops that:
    - Have drop_pct_raw <= min_drop_pct (significant enough)
    - Don't already have a real catalyst (earnings data, 8-K items)

    Args:
        legend_data: Drop legend dicts from build_drop_legend_data.
        ticker: Stock ticker for search queries.
        company_name: Company name for search queries.
        min_drop_pct: Only investigate drops worse than this.
        max_searches: Max web searches to run (budget control).

    Returns:
        Same legend_data with trigger fields updated for investigated drops.
    """
    api_key = os.environ.get("SERPER_API_KEY", "").strip()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()

    if not api_key:
        logger.debug("SERPER_API_KEY not set — drop investigation skipped")
        return legend_data

    if not deepseek_key:
        logger.debug("DEEPSEEK_API_KEY not set — drop investigation skipped")
        return legend_data

    # Identify drops needing investigation
    needs_investigation: list[int] = []
    for i, d in enumerate(legend_data):
        if d["drop_pct_raw"] > min_drop_pct:
            continue  # Too small
        if _has_real_catalyst(d):
            continue  # Already explained
        needs_investigation.append(i)

    if not needs_investigation:
        logger.debug("All drops already have real catalysts")
        return legend_data

    # Budget: investigate most severe first
    needs_investigation.sort(key=lambda i: legend_data[i]["drop_pct_raw"])
    needs_investigation = needs_investigation[:max_searches]

    logger.info(
        "Investigating %d/%d drops for %s via web search",
        len(needs_investigation),
        len(legend_data),
        ticker,
    )

    # Run searches and extract catalysts
    short_name = company_name or ticker
    for idx in needs_investigation:
        drop = legend_data[idx]
        try:
            catalyst = _investigate_single_drop(
                drop,
                ticker,
                short_name,
                api_key,
                deepseek_key,
            )
            if catalyst:
                legend_data[idx]["trigger"] = catalyst
                legend_data[idx]["investigated"] = True
        except Exception:
            logger.debug("Investigation failed for drop #%d", drop["number"], exc_info=True)

    return legend_data


def _has_real_catalyst(drop: dict[str, Any]) -> bool:
    """Check if a drop already has a real, data-backed catalyst.

    Earnings beat + big drop is NOT a real catalyst — we know they
    beat earnings but NOT why the stock still dropped. Needs investigation.
    """
    trigger = drop.get("trigger", "")
    cat = drop.get("category", "unknown")
    pct = drop.get("drop_pct_raw", 0)

    # Earnings beat + significant drop = NOT explained (needs investigation)
    if "Earnings beat" in trigger and pct <= -10:
        return False  # "Beat but dropped 37%" needs the real reason

    # Earnings miss IS a real catalyst
    if "Earnings miss" in trigger:
        return True

    # These categories mean we have actual data
    if cat in ("guidance_cut", "restatement", "management_departure", "litigation", "regulatory"):
        return True

    # 8-K data — we know the filing type but not the impact
    # Only count as "real" for small drops; big drops need investigation
    if trigger.startswith("8-K:") and pct > -20:
        return True

    return False


def _investigate_single_drop(
    drop: dict[str, Any],
    ticker: str,
    company_name: str,
    serper_key: str,
    deepseek_key: str,
) -> str | None:
    """Search + extract catalyst for a single drop."""
    import httpx

    date_str = drop["date"]
    pct = drop["drop_pct_raw"]

    # Parse date for search — use first date of cluster
    if " – " in date_str:
        search_date = date_str.split(" – ")[0].strip()
    else:
        search_date = date_str.strip()

    # Format date for search: "May 2024" from "2024-05-10"
    try:
        dt = datetime.fromisoformat(search_date[:10])
        month_year = dt.strftime("%B %Y")
        short_date = dt.strftime("%b %d, %Y")
    except (ValueError, TypeError):
        month_year = search_date
        short_date = search_date

    # Build search queries — multiple angles like an underwriter would
    queries = [
        f'"{ticker}" stock drop {month_year}',
        f'"{company_name}" stock decline {month_year}',
    ]

    # Collect search results
    all_results: list[dict[str, str]] = []
    headers = {
        "X-API-KEY": serper_key,
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=15.0) as client:
        for query in queries:
            try:
                resp = client.post(
                    "https://google.serper.dev/search",
                    headers=headers,
                    json={"q": query, "num": 5},
                )
                resp.raise_for_status()
                data = resp.json()

                for item in data.get("organic", []):
                    if isinstance(item, dict):
                        all_results.append(
                            {
                                "title": str(item.get("title", "")),
                                "snippet": str(item.get("snippet", "")),
                            }
                        )
                for item in data.get("news", []):
                    if isinstance(item, dict):
                        all_results.append(
                            {
                                "title": str(item.get("title", "")),
                                "snippet": str(item.get("snippet", "")),
                            }
                        )
            except Exception:
                logger.debug("Search failed for: %s", query[:60], exc_info=True)

    if not all_results:
        return None

    # Deduplicate by title
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for r in all_results:
        key = r["title"][:50]
        if key not in seen:
            seen.add(key)
            unique.append(r)

    # Feed to DeepSeek for extraction
    return _extract_catalyst(
        unique[:10],
        ticker,
        company_name,
        short_date,
        pct,
        deepseek_key,
    )


def _extract_catalyst(
    results: list[dict[str, str]],
    ticker: str,
    company_name: str,
    date: str,
    drop_pct: float,
    api_key: str,
) -> str | None:
    """Use DeepSeek to extract the actual catalyst from search results."""
    import openai

    results_text = "\n".join(f"- {r['title']}: {r['snippet']}" for r in results)

    prompt = f"""What caused {company_name} ({ticker}) to drop {drop_pct:+.1f}% around {date}?

{results_text}

Reply with ONLY the cause in under 80 characters. No preamble. No "Based on..." No caveats.
Name specific events, drugs, analysts, amounts. If uncertain, state the most likely cause as fact.
Examples: "FDA delayed VK2735 Phase 3 readout" | "JPM downgrade, PT cut to $45" | "Profit-taking after 40% run-up"
"""

    model = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")

    try:
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        response = client.chat.completions.create(
            model=model,
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content or ""
        text = text.strip()
        # Clean up — remove quotes, periods at end
        text = text.strip("\"'").rstrip(".")
        # Reject verbose LLM garbage
        garbage_starts = (
            "Based on",
            "I cannot",
            "I don't have",
            "The search results",
            "Unfortunately",
            "There is no",
            "No specific",
        )
        if any(text.startswith(g) for g in garbage_starts):
            return None
        if len(text) > 120:
            text = text[:117] + "..."
        return text if text else None
    except Exception:
        logger.debug("LLM extraction failed for %s %s", ticker, date, exc_info=True)
        return None


__all__ = ["investigate_drops"]
