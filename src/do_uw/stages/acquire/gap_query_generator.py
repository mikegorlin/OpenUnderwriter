"""LLM-based query generation for gap searches.

Two-step: LLM generates an optimized company-specific query string.
Falls back to template if LLM unavailable or fails.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_gap_query(check: dict[str, Any], company_name: str, ticker: str) -> str:
    """Generate a company-specific search query for a gap check.

    Tries LLM generation first; falls back to template on any failure.

    Args:
        check: Check dict with id, name, gap_keywords, required_data, etc.
        company_name: Full company legal name.
        ticker: Stock ticker symbol.

    Returns:
        Search query string.
    """
    try:
        return _generate_via_llm(check, company_name, ticker)
    except Exception:
        return _generate_via_template(check, company_name, ticker)


def _generate_via_template(check: dict[str, Any], company_name: str, ticker: str) -> str:
    """Generate query using keyword template (no LLM required).

    Args:
        check: Check dict with gap_keywords and name fields.
        company_name: Full company legal name.
        ticker: Stock ticker symbol.

    Returns:
        Template-based search query string.
    """
    keywords = check.get("gap_keywords", [])
    if keywords:
        keyword_str = " ".join(str(kw) for kw in keywords[:3])
        return f'"{company_name}" ({ticker}) {keyword_str}'
    # Fallback: use check name when no keywords
    signal_name = check.get("name", check.get("id", ""))
    return f'"{company_name}" {ticker} {signal_name}'


def _generate_via_llm(check: dict[str, Any], company_name: str, ticker: str) -> str:
    """Generate an optimized query via DeepSeek (lazy import).

    Uses batch approach when multiple checks are passed but this function
    handles a single check. Returns empty string on any failure so caller
    can fall back to template.

    Args:
        check: Check dict with id, name, required_data, gap_keywords.
        company_name: Full company legal name.
        ticker: Stock ticker symbol.

    Returns:
        LLM-generated query string, or empty string on failure.
    """
    try:
        import openai  # Lazy import — don't fail at module load
        import os
    except ImportError:
        logger.debug("openai package not installed; using template fallback")
        return ""

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.debug("DEEPSEEK_API_KEY not set; using template fallback")
        return ""

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    model = "deepseek-chat"

    signal_id = check.get("id", "unknown")
    signal_name = check.get("name", signal_id)
    required_data = check.get("required_data", [])
    keywords = check.get("gap_keywords", [])

    prompt = (
        f"Generate a web search query to find evidence about {company_name} "
        f"({ticker}) related to: {signal_name}.\n"
        f"Data needed: {', '.join(str(r) for r in required_data)}.\n"
        f"Focus on: {', '.join(str(k) for k in keywords)}.\n"
        f"Return ONLY the search query string, maximum 12 words, "
        f"optimized for recent news, regulatory actions, public disclosures."
    )

    logger.debug("Gap query LLM call: model=%s check=%s", model, signal_id)

    response = client.chat.completions.create(
        model=model,
        max_tokens=50,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a financial research search query generator. "
                    "Output only the search query string, nothing else. "
                    "Focus on regulatory actions, enforcement, public disclosures."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    # Extract text from response
    if not response.choices:
        return ""

    text = response.choices[0].message.content.strip()

    # Take only the first line and validate length
    first_line = text.split("\n")[0].strip()
    if not first_line or len(first_line) > 100:
        logger.debug(
            "Gap query LLM returned unusable response (len=%d), using template fallback",
            len(first_line),
        )
        return ""

    return first_line


def generate_gap_queries(
    checks: list[dict[str, Any]], company_name: str, ticker: str
) -> dict[str, str]:
    """Generate search queries for multiple checks in batch.

    Uses LLM batch generation when possible, falls back to template
    for any failures.

    Args:
        checks: List of check dicts.
        company_name: Full company legal name.
        ticker: Stock ticker symbol.

    Returns:
        Dict mapping signal_id -> query string.
    """
    if not checks:
        return {}
    # Try LLM batch generation first
    try:
        return _batch_via_llm(checks, company_name, ticker)
    except Exception:
        # Fall back to template for all checks
        return {c["id"]: _generate_via_template(c, company_name, ticker) for c in checks}


def _batch_via_llm(checks: list[dict[str, Any]], company_name: str, ticker: str) -> dict[str, str]:
    """Batch LLM query generation for efficiency.

    Generates queries for all checks in one API call to reduce latency
    and cost. Parses numbered response lines.

    Returns:
        Dict mapping signal_id -> query string. Falls back to template
        for any check that couldn't be parsed.
    """
    try:
        import openai
        import os
    except ImportError:
        logger.debug("openai package not installed; skipping batch LLM")
        raise RuntimeError("openai not installed")

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.debug("DEEPSEEK_API_KEY not set; skipping batch LLM")
        raise RuntimeError("DEEPSEEK_API_KEY not set")

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    model = "deepseek-chat"

    # Build numbered list of checks
    lines = []
    for i, check in enumerate(checks, 1):
        signal_name = check.get("name", check.get("id", ""))
        keywords = check.get("gap_keywords", [])
        kw_str = ", ".join(str(k) for k in keywords[:3]) if keywords else ""
        lines.append(f"{i}. {signal_name}" + (f" [{kw_str}]" if kw_str else ""))

    checks_text = "\n".join(lines)
    prompt = (
        f"Generate a web search query for each item about "
        f"{company_name} ({ticker}):\n\n"
        f"{checks_text}\n\n"
        f"Return ONLY numbered responses (1. query, 2. query, etc.), "
        f"max 12 words each. Focus on regulatory actions, enforcement, "
        f"recent disclosures."
    )

    logger.debug("Gap query batch LLM call: model=%s checks=%d", model, len(checks))

    response = client.chat.completions.create(
        model=model,
        max_tokens=200,
        messages=[
            {
                "role": "system",
                "content": (
                    "You generate search queries. Output numbered responses only, "
                    "one per line (1. ..., 2. ...). No other text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
    )

    if not response.choices:
        raise ValueError("Empty LLM response")

    response_text = response.choices[0].message.content.strip()
    if not response_text:
        raise ValueError("Empty LLM response content")

    # Parse numbered responses
    result: dict[str, str] = {}
    for i, check in enumerate(checks, 1):
        signal_id = check["id"]
        # Match "N. query text"
        for response_line in response_text.split("\n"):
            stripped = response_line.strip()
            if stripped.startswith(f"{i}."):
                query = stripped[len(f"{i}.") :].strip()
                if query and len(query) <= 100:
                    result[signal_id] = query
                    break
        # Fallback to template if not found
        if signal_id not in result:
            result[signal_id] = _generate_via_template(check, company_name, ticker)

    return result
