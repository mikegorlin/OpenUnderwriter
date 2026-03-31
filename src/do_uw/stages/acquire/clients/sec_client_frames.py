"""SEC EDGAR Frames API acquisition client.

Fetches cross-filer XBRL data from the SEC Frames API for peer
benchmarking. Each Frames call returns one value per reporting entity
for a given XBRL concept and calendar period (~5,000-10,000 filers).

Also builds an incremental CIK-to-SIC mapping from the SEC submissions
API for sector-relative percentile filtering.

Per CLAUDE.md: All data acquisition happens in ACQUIRE stage only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.stages.acquire.rate_limiter import sec_get

logger = logging.getLogger(__name__)

# SEC Frames API URL template.
SEC_FRAMES_URL = "https://data.sec.gov/api/xbrl/frames/us-gaap/{tag}/{unit}/{period}.json"

# SEC Submissions API URL template (for SIC lookup).
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"

# Cache TTLs in seconds.
FRAMES_TTL_COMPLETED = 180 * 24 * 3600  # 180 days for completed periods
FRAMES_TTL_CURRENT = 1 * 24 * 3600  # 1 day for current period
SIC_TTL = 90 * 24 * 3600  # 90 days for SIC mapping

# Maximum CIKs to fetch SIC codes for in a single run.
SIC_BATCH_LIMIT = 50


@dataclass(frozen=True)
class FramesMetricDef:
    """Definition of an XBRL metric to fetch from the Frames API.

    Attributes:
        metric_name: Internal name for the metric (e.g., "revenue").
        xbrl_tag: XBRL concept tag (e.g., "Revenues").
        unit: Unit of measure (default "USD").
        period_type: "duration" for income/cash flow, "instant" for balance sheet.
        higher_is_better: Whether higher values indicate better performance.
    """

    metric_name: str
    xbrl_tag: str
    unit: str = "USD"
    period_type: str = "duration"
    higher_is_better: bool = True


# Registry of all XBRL concepts to fetch for benchmarking.
# 8 direct metrics + 2 component-only metrics for derived ratios.
FRAMES_METRICS: list[FramesMetricDef] = [
    # Direct metrics (single concept = single Frames call)
    FramesMetricDef("revenue", "Revenues", "USD", "duration", True),
    FramesMetricDef("net_income", "NetIncomeLoss", "USD", "duration", True),
    FramesMetricDef("total_assets", "Assets", "USD", "instant", True),
    FramesMetricDef(
        "total_equity",
        "StockholdersEquity",
        "USD",
        "instant",
        True,
    ),
    FramesMetricDef(
        "total_liabilities",
        "Liabilities",
        "USD",
        "instant",
        False,
    ),
    FramesMetricDef(
        "operating_income",
        "OperatingIncomeLoss",
        "USD",
        "duration",
        True,
    ),
    FramesMetricDef(
        "cash_from_operations",
        "NetCashProvidedByOperatingActivities",
        "USD",
        "duration",
        True,
    ),
    FramesMetricDef(
        "rd_expense",
        "ResearchAndDevelopmentExpense",
        "USD",
        "duration",
        True,
    ),
    # Component-only metrics (needed for derived ratios in Plan 02)
    FramesMetricDef(
        "current_assets",
        "AssetsCurrent",
        "USD",
        "instant",
        True,
    ),
    FramesMetricDef(
        "current_liabilities",
        "LiabilitiesCurrent",
        "USD",
        "instant",
        False,
    ),
]


def _build_period_string(period_type: str, year: int) -> str:
    """Build Frames API period string.

    Duration concepts (revenue, income): CY{year}
    Instant concepts (assets, liabilities): CY{year}I

    Args:
        period_type: "duration" or "instant".
        year: Calendar year.

    Returns:
        Period string for the Frames API URL.
    """
    if period_type == "instant":
        return f"CY{year}I"
    return f"CY{year}"


def _determine_best_period(company_10k_year: int | None) -> int:
    """Determine the best calendar year for Frames queries.

    Uses the company's most recent 10-K fiscal year. Falls back to
    current_year - 1 when no 10-K year is available.

    Args:
        company_10k_year: Fiscal year of the company's most recent 10-K,
            or None if unknown.

    Returns:
        Calendar year to use for Frames API queries.
    """
    if company_10k_year is not None:
        return company_10k_year
    current_year = datetime.now(tz=UTC).year
    return current_year - 1


def _is_completed_period(year: int) -> bool:
    """Check if a calendar year period is completed (not current).

    A period is considered completed if the year is before the current
    calendar year. Current-year data may still be accumulating.

    Args:
        year: Calendar year to check.

    Returns:
        True if the period is completed.
    """
    current_year = datetime.now(tz=UTC).year
    return year < current_year


def acquire_frames(
    company_cik: int,
    company_10k_year: int | None,
    cache: AnalysisCache | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch cross-filer XBRL data from the SEC Frames API.

    For each metric in FRAMES_METRICS, fetches the Frames API response
    containing one value per reporting entity. Results are cached at
    system level (not per-company) since Frames data covers all filers.

    Args:
        company_cik: CIK of the target company (for logging).
        company_10k_year: Fiscal year of the company's most recent 10-K,
            or None to use current_year - 1.
        cache: Optional cache for storing/retrieving Frames responses.

    Returns:
        Dict keyed by metric_name, each value is a list of entity dicts
        with keys: accn, cik, entityName, loc, end, val.
    """
    year = _determine_best_period(company_10k_year)
    completed = _is_completed_period(year)
    ttl = FRAMES_TTL_COMPLETED if completed else FRAMES_TTL_CURRENT

    logger.info(
        "Acquiring Frames data for CIK %d, period year %d (completed=%s, TTL=%dd)",
        company_cik,
        year,
        completed,
        ttl // (24 * 3600),
    )

    result: dict[str, list[dict[str, Any]]] = {}

    for metric in FRAMES_METRICS:
        period = _build_period_string(metric.period_type, year)
        cache_key = f"sec:frames:{metric.xbrl_tag}:{metric.unit}:{period}"

        # Check cache first.
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(
                    "Cache hit for Frames %s/%s",
                    metric.xbrl_tag,
                    period,
                )
                result[metric.metric_name] = cached
                continue

        # Fetch from Frames API.
        url = SEC_FRAMES_URL.format(
            tag=metric.xbrl_tag,
            unit=metric.unit,
            period=period,
        )

        try:
            response = sec_get(url)
            data_list: list[dict[str, Any]] = response.get("data", [])
            result[metric.metric_name] = data_list

            logger.info(
                "Frames %s/%s: %d entities",
                metric.xbrl_tag,
                period,
                len(data_list),
            )

            # Cache the data list only (not full response -- memory
            # optimization per research pitfall 3).
            if cache is not None:
                cache.set(
                    cache_key,
                    data_list,
                    source="sec_edgar:frames_api",
                    ttl=ttl,
                )

        except Exception:
            logger.warning(
                "Frames API error for %s/%s (continuing with partial results)",
                metric.xbrl_tag,
                period,
                exc_info=True,
            )
            result[metric.metric_name] = []

    metrics_with_data = sum(1 for v in result.values() if v)
    logger.info(
        "Frames acquisition complete: %d/%d metrics with data",
        metrics_with_data,
        len(FRAMES_METRICS),
    )

    return result


def acquire_sic_mapping(
    ciks: set[int],
    cache: AnalysisCache | None = None,
) -> dict[int, str]:
    """Build CIK-to-SIC mapping from SEC submissions API.

    Fetches SIC codes incrementally: checks cache first, only fetches
    for uncached CIKs. Limits batch to SIC_BATCH_LIMIT per run to
    avoid excessive API calls on first run.

    Args:
        ciks: Set of CIK integers to look up.
        cache: Optional cache for storing/retrieving SIC codes.

    Returns:
        Dict mapping CIK (int) to SIC code (4-digit string).
    """
    result: dict[int, str] = {}
    uncached: list[int] = []

    # Check cache for each CIK.
    for cik in ciks:
        cache_key = f"sec:sic:{cik}"
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                result[cik] = str(cached)
                continue
        uncached.append(cik)

    if not uncached:
        logger.debug("SIC mapping: all %d CIKs cached", len(ciks))
        return result

    # Limit batch size.
    total_uncached = len(uncached)
    if total_uncached > SIC_BATCH_LIMIT:
        logger.info(
            "SIC mapping: %d uncached CIKs, limiting to %d this run (%d skipped)",
            total_uncached,
            SIC_BATCH_LIMIT,
            total_uncached - SIC_BATCH_LIMIT,
        )
        uncached = uncached[:SIC_BATCH_LIMIT]

    logger.info(
        "SIC mapping: fetching SIC codes for %d CIKs",
        len(uncached),
    )

    fetched = 0
    for cik in uncached:
        url = SEC_SUBMISSIONS_URL.format(cik=cik)
        try:
            response = sec_get(url)
            sic = response.get("sic", "")
            if sic:
                result[cik] = str(sic)
                fetched += 1

                # Cache the SIC code.
                if cache is not None:
                    cache.set(
                        f"sec:sic:{cik}",
                        sic,
                        source="sec_edgar:submissions_api",
                        ttl=SIC_TTL,
                    )
        except Exception:
            logger.warning(
                "SIC mapping: failed to fetch CIK %d (skipping)",
                cik,
                exc_info=True,
            )

    logger.info(
        "SIC mapping complete: %d/%d CIKs mapped (from cache: %d, from API: %d)",
        len(result),
        len(ciks),
        len(result) - fetched,
        fetched,
    )

    return result
