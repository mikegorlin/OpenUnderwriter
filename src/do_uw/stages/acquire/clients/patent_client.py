"""USPTO AI patent data client -- acquires raw patent records in ACQUIRE stage.

Queries the USPTO Patent Application Information Retrieval API for AI/ML-related
patents filed by the company. Returns raw result dicts for later parsing in
EXTRACT stage.

Per CLAUDE.md: all data acquisition must live in stages/acquire/.
"""

from __future__ import annotations

import logging
import time
from typing import Any, cast

import httpx

logger = logging.getLogger(__name__)

_USPTO_API_URL = "https://developer.uspto.gov/ibd-api/v1/patent/application"
_REQUEST_TIMEOUT = 10.0
_RATE_LIMIT_DELAY = 0.5
_MAX_ROWS = 50


def fetch_ai_patents(company_name: str) -> list[dict[str, Any]]:
    """Fetch AI/ML patent records for a company from the USPTO API.

    Args:
        company_name: Legal name of the company.

    Returns:
        List of raw patent result dicts, or empty list on any failure.
    """
    if not company_name:
        return []
    try:
        time.sleep(_RATE_LIMIT_DELAY)
        return _query_uspto(company_name)
    except Exception:
        logger.warning(
            "ACQUIRE: USPTO patent fetch failed for %s",
            company_name,
            exc_info=True,
        )
        return []


def _query_uspto(company_name: str) -> list[dict[str, Any]]:
    """Issue the HTTP request to USPTO and return raw results."""
    search_text = (
        f"{company_name} AND (artificial intelligence OR machine learning)"
    )
    params = {
        "searchText": search_text,
        "rows": str(_MAX_ROWS),
    }
    response = httpx.get(
        _USPTO_API_URL,
        params=params,
        timeout=_REQUEST_TIMEOUT,
    )
    response.raise_for_status()

    data: Any = response.json()
    if isinstance(data, dict):
        data_dict = cast(dict[str, Any], data)
        raw: Any = data_dict.get("results", data_dict.get("docs", []))
        if isinstance(raw, list):
            return cast(list[dict[str, Any]], raw)
    return []
