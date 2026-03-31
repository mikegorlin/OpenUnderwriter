"""Short interest extraction from yfinance and web search data.

Extracts short interest metrics, computes trends, compares against
peer group, and identifies short seller reports. Covers SECT4-05
for D&O underwriting.

Data sources:
1. yfinance info dict (short_pct_float, days_to_cover)
2. Web search results (short seller reports)
3. Peer market data (sector comparison)

Usage:
    profile, report = extract_short_interest(state)
    state.extracted.market.short_interest = profile
"""

from __future__ import annotations

import logging
import re
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market import ShortInterestProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_info_dict,
    get_market_data,
    now,
    sourced_float,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Expected fields for the extraction report.
EXPECTED_FIELDS: list[str] = [
    "short_pct_float",
    "days_to_cover",
    "trend_6m",
    "vs_sector_ratio",
    "short_seller_reports",
]

# Known activist short sellers to search for.
KNOWN_SHORT_SELLERS: list[str] = [
    "Hindenburg",
    "Muddy Waters",
    "Citron",
    "Spruce Point",
    "Kerrisdale",
    "Iceberg",
    "Grizzly",
    "Blue Orca",
    "Gotham City",
    "Bonitas",
]


# ---------------------------------------------------------------------------
# Short interest data extraction
# ---------------------------------------------------------------------------


def extract_current_short_interest(
    info: dict[str, Any],
) -> dict[str, Any]:
    """Extract current short interest metrics from yfinance info dict.

    Retrieves short_pct_float, days_to_cover, and computes a basic
    6-month trend indicator based on available data.

    Args:
        info: yfinance info dictionary.

    Returns:
        Dict with short_pct_float, days_to_cover, trend_6m values.
    """
    result: dict[str, Any] = {}

    # Short percent of float.
    short_pct = info.get("shortPercentOfFloat")
    if short_pct is None:
        # Try alternate key.
        short_pct = info.get("shortRatio")
        if short_pct is not None:
            # shortRatio is days-to-cover, not percent.
            result["days_to_cover"] = float(short_pct)
            short_pct = None

    if short_pct is not None:
        # yfinance returns as decimal (0.05 = 5%).
        pct_val = float(short_pct) * 100.0
        result["short_pct_float"] = pct_val

    # Days to cover.
    if "days_to_cover" not in result:
        dtc = info.get("shortRatio")
        if dtc is not None:
            result["days_to_cover"] = float(dtc)

    # Trend estimation from prior short interest data.
    # yfinance info has sharesShort and sharesShortPriorMonth.
    shares_short = info.get("sharesShort")
    shares_prior = info.get("sharesShortPriorMonth")
    if shares_short is not None and shares_prior is not None:
        try:
            current = float(shares_short)
            prior = float(shares_prior)
            if prior > 0:
                change_pct = ((current - prior) / prior) * 100.0
                if change_pct > 10.0:
                    result["trend_6m"] = "RISING"
                elif change_pct < -10.0:
                    result["trend_6m"] = "DECLINING"
                else:
                    result["trend_6m"] = "STABLE"
            else:
                result["trend_6m"] = "STABLE"
        except (ValueError, TypeError):
            pass

    return result


# ---------------------------------------------------------------------------
# Peer comparison
# ---------------------------------------------------------------------------


def compare_vs_peers(
    company_si: float | None,
    peer_data: list[dict[str, Any]],
) -> float | None:
    """Compare company short interest against peers.

    Computes ratio of company's short interest to peer average.
    Ratio > 1.0 means company is shorted more than peers.

    Args:
        company_si: Company's short percent of float.
        peer_data: List of peer info dicts with shortPercentOfFloat.

    Returns:
        Ratio of company SI to peer average, or None if insufficient data.
    """
    if company_si is None or company_si <= 0:
        return None

    peer_si_values: list[float] = []
    for peer in peer_data:
        si = peer.get("shortPercentOfFloat")
        if si is not None:
            try:
                val = float(si) * 100.0
                if val > 0:
                    peer_si_values.append(val)
            except (ValueError, TypeError):
                continue

    if not peer_si_values:
        return None

    avg_peer_si = sum(peer_si_values) / len(peer_si_values)
    if avg_peer_si <= 0:
        return None

    return round(company_si / avg_peer_si, 2)


# ---------------------------------------------------------------------------
# Short seller report detection
# ---------------------------------------------------------------------------


def identify_short_seller_reports(
    web_results: dict[str, Any],
    company_name: str,
) -> list[dict[str, str]]:
    """Identify short seller reports from web search results.

    Searches for mentions of known activist short sellers in
    web search results related to the company.

    Args:
        web_results: Web search results dict.
        company_name: Company name for contextual matching.

    Returns:
        List of dicts with source, date, allegations for each report.
    """
    reports: list[dict[str, str]] = []

    if not web_results or not company_name:
        return reports

    # Collect all text from web search results.
    search_texts = _collect_search_texts(web_results)

    if not search_texts:
        return reports

    company_lower = company_name.lower()

    for text, url in search_texts:
        text_lower = text.lower()
        # Must mention the company.
        if company_lower not in text_lower:
            continue

        for seller in KNOWN_SHORT_SELLERS:
            if seller.lower() in text_lower:
                # Extract date if available.
                date_match = re.search(
                    r"(\d{4}-\d{2}-\d{2}|\w+ \d{1,2},? \d{4})", text
                )
                date_str = date_match.group(1) if date_match else "unknown"

                # Extract brief allegation context.
                allegation = _extract_allegation_context(
                    text, seller, company_name
                )

                reports.append({
                    "source": seller,
                    "date": date_str,
                    "allegations": allegation,
                    "url": url,
                })
                break  # One seller per result.

    return reports


def _collect_search_texts(
    web_results: dict[str, Any],
) -> list[tuple[str, str]]:
    """Collect text + URL pairs from various web result formats.

    Handles different structures: list of results dicts, nested
    search result formats, and flat text.

    Args:
        web_results: Raw web search results dict.

    Returns:
        List of (text, url) tuples.
    """
    texts: list[tuple[str, str]] = []

    for _key, value in web_results.items():
        if isinstance(value, list):
            typed_list = cast(list[Any], value)
            for item in typed_list:
                if isinstance(item, dict):
                    item_dict = cast(dict[str, Any], item)
                    title = str(item_dict.get("title", ""))
                    desc = str(item_dict.get("description", ""))
                    snippet = str(item_dict.get("snippet", ""))
                    url = str(item_dict.get("url", ""))
                    combined = f"{title} {desc} {snippet}"
                    if combined.strip():
                        texts.append((combined, url))
                elif isinstance(item, str):
                    texts.append((item, ""))
        elif isinstance(value, str):
            texts.append((value, ""))

    return texts


def _extract_allegation_context(
    text: str, seller: str, company: str
) -> str:
    """Extract brief context around the short seller mention.

    Finds the sentence containing the seller name and returns
    a trimmed excerpt.

    Args:
        text: Full text containing the mention.
        seller: Short seller name.
        company: Company name for context.

    Returns:
        Trimmed allegation context string (max 300 chars).
    """
    sentences = re.split(r"[.!?]+", text)
    seller_lower = seller.lower()

    for sentence in sentences:
        if seller_lower in sentence.lower():
            cleaned = sentence.strip()
            if len(cleaned) > 300:
                cleaned = cleaned[:297] + "..."
            return cleaned

    return f"{seller} report on {company}"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_short_interest(
    state: AnalysisState,
) -> tuple[ShortInterestProfile, ExtractionReport]:
    """Extract short interest profile from yfinance and web search data.

    Populates ShortInterestProfile with current SI metrics, trend,
    peer comparison, and any identified short seller reports.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (ShortInterestProfile, ExtractionReport).
    """
    profile = ShortInterestProfile()
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "yfinance info + web search"

    # 1. Extract current short interest from yfinance info.
    info = get_info_dict(state)
    si_data = extract_current_short_interest(info)

    if "short_pct_float" in si_data:
        profile.short_pct_float = sourced_float(
            si_data["short_pct_float"],
            "yfinance shortPercentOfFloat",
            Confidence.MEDIUM,
        )
        found.append("short_pct_float")

    if "days_to_cover" in si_data:
        profile.days_to_cover = sourced_float(
            si_data["days_to_cover"],
            "yfinance shortRatio",
            Confidence.MEDIUM,
        )
        found.append("days_to_cover")

    if "trend_6m" in si_data:
        profile.trend_6m = sourced_str(
            si_data["trend_6m"],
            "yfinance sharesShort vs sharesShortPriorMonth",
            Confidence.MEDIUM,
        )
        found.append("trend_6m")

    # 1b. Absolute short share counts from yfinance info.
    from do_uw.stages.extract.sourced import sourced_int

    shares_short_raw = info.get("sharesShort")
    if shares_short_raw is not None:
        try:
            profile.shares_short = sourced_int(
                int(float(shares_short_raw)),
                "yfinance sharesShort",
                Confidence.MEDIUM,
            )
        except (ValueError, TypeError):
            pass

    shares_prior_raw = info.get("sharesShortPriorMonth")
    if shares_prior_raw is not None:
        try:
            profile.shares_short_prior = sourced_int(
                int(float(shares_prior_raw)),
                "yfinance sharesShortPriorMonth",
                Confidence.MEDIUM,
            )
        except (ValueError, TypeError):
            pass

    short_pct_out = info.get("sharesPercentSharesOut")
    if short_pct_out is not None:
        try:
            profile.short_pct_shares_out = sourced_float(
                round(float(short_pct_out) * 100.0, 2),
                "yfinance sharesPercentSharesOut",
                Confidence.MEDIUM,
            )
        except (ValueError, TypeError):
            pass

    # 2. Peer comparison.
    peer_si = _get_peer_short_interest(state)
    company_si = si_data.get("short_pct_float")
    ratio = compare_vs_peers(company_si, peer_si)
    if ratio is not None:
        profile.vs_sector_ratio = sourced_float(
            ratio,
            "yfinance peer shortPercentOfFloat comparison",
            Confidence.LOW,
        )
        found.append("vs_sector_ratio")

    # 3. Short seller report detection.
    company_name = _get_company_name(state)
    web_results = _get_web_results(state)
    seller_reports = identify_short_seller_reports(web_results, company_name)
    if seller_reports:
        for rpt in seller_reports:
            profile.short_seller_reports.append(
                SourcedValue[dict[str, str]](
                    value=rpt,
                    source=f"web search: {rpt.get('source', 'unknown')}",
                    confidence=Confidence.LOW,
                    as_of=now(),
                )
            )
        found.append("short_seller_reports")
        warnings.append(
            f"Short seller reports detected: {len(seller_reports)}"
        )
    else:
        # No reports found is still a valid extraction result.
        found.append("short_seller_reports")

    if not found:
        warnings.append("No short interest data available")

    report = create_report(
        extractor_name="short_interest",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return profile, report


# ---------------------------------------------------------------------------
# State accessor helpers
# ---------------------------------------------------------------------------


def _get_peer_short_interest(
    state: AnalysisState,
) -> list[dict[str, Any]]:
    """Get peer short interest data from acquired market data.

    Looks for peer_data in market_data, which contains yfinance
    info dicts for peer companies.

    Args:
        state: AnalysisState with acquired_data.

    Returns:
        List of peer info dicts.
    """
    market = get_market_data(state)
    peer_raw = market.get("peer_data")
    if peer_raw is not None and isinstance(peer_raw, list):
        return cast(list[dict[str, Any]], peer_raw)
    return []


def _get_company_name(state: AnalysisState) -> str:
    """Get company name from state."""
    if state.company and state.company.identity.legal_name:
        return state.company.identity.legal_name.value
    return state.ticker


def _get_web_results(state: AnalysisState) -> dict[str, Any]:
    """Get web search results from acquired data."""
    if state.acquired_data is None:
        return {}
    return dict(state.acquired_data.web_search_results)
