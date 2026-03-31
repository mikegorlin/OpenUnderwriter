"""Supabase SCA filings lookup — SUPPLEMENTARY litigation enrichment.

Queries the Pricing Database Supabase instance for historical SCA filings
matching the company ticker. Returns structured case data including
settlements, class periods, allegations, and outcomes.

IMPORTANT: This is NOT a definitive source. Results are MEDIUM confidence
and must be cross-validated against authoritative sources (SEC EDGAR,
court records, company filings). Supabase data comes from scraped/enriched
sources and may contain errors, stale data, or misattributed cases.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Supabase connection for the Pricing Database
_SUPABASE_URL = "https://jfqenpobwadlhuvseiax.supabase.co"
_TABLE = "sca_filings"


def query_sca_filings(
    ticker: str,
    company_name: str | None = None,
) -> list[dict[str, Any]]:
    """Query Supabase sca_filings for a company's litigation history.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        company_name: Optional company name for broader matching.

    Returns:
        List of case dicts with fields matching CaseDetail model.
        Empty list if Supabase is unavailable or no matches found.
    """
    api_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not api_key:
        logger.debug("No SUPABASE_KEY — skipping Supabase litigation lookup")
        return []

    try:
        import httpx
    except ImportError:
        logger.debug("httpx not available — skipping Supabase lookup")
        return []

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Query by ticker first, then by company name
    cases: list[dict[str, Any]] = []

    try:
        # Query 1: exact ticker match
        url = (
            f"{_SUPABASE_URL}/rest/v1/{_TABLE}"
            f"?ticker=eq.{ticker}"
            f"&select=company_name,ticker,filing_date,case_status,court,"
            f"settlement_amount_m,class_period_start,class_period_end,"
            f"stock_drop_pct,allegation_accounting,allegation_insider_trading,"
            f"allegation_earnings,allegation_merger,allegation_ipo_offering,"
            f"lead_counsel,outcome_type,case_summary,docket_number,"
            f"case_duration_months,district_court,claim_type,"
            f"has_derivative_action,has_erisa_claim,defense_costs_m,"
            f"market_cap_at_filing_m,business_scenario"
            f"&order=filing_date.desc"
            f"&limit=20"
        )

        resp = httpx.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                cases.extend(data)

        # Query 2: company name match (catches "Apple Computer, Inc." etc.)
        if company_name:
            # Clean company name for ILIKE matching
            clean_name = company_name.replace("'", "''").split(",")[0].split(" Inc")[0].strip()
            if clean_name and len(clean_name) > 3:
                url2 = (
                    f"{_SUPABASE_URL}/rest/v1/{_TABLE}"
                    f"?company_name=ilike.*{clean_name}*"
                    f"&select=company_name,ticker,filing_date,case_status,court,"
                    f"settlement_amount_m,class_period_start,class_period_end,"
                    f"stock_drop_pct,allegation_accounting,allegation_insider_trading,"
                    f"allegation_earnings,allegation_merger,allegation_ipo_offering,"
                    f"lead_counsel,outcome_type,case_summary,docket_number,"
                    f"case_duration_months,district_court,claim_type,"
                    f"has_derivative_action,has_erisa_claim,defense_costs_m,"
                    f"market_cap_at_filing_m,business_scenario"
                    f"&order=filing_date.desc"
                    f"&limit=20"
                )
                resp2 = httpx.get(url2, headers=headers, timeout=15)
                if resp2.status_code == 200:
                    data2 = resp2.json()
                    if isinstance(data2, list):
                        # Dedup by filing_date + company_name
                        existing = {
                            (c.get("filing_date"), c.get("company_name"))
                            for c in cases
                        }
                        for case in data2:
                            key = (case.get("filing_date"), case.get("company_name"))
                            if key not in existing:
                                cases.append(case)

        # Filter out non-matching companies (e.g., "Apple REIT" for AAPL)
        if cases:
            filtered = _filter_matching_company(cases, ticker, company_name)
            logger.info(
                "Supabase SCA lookup: %d cases for %s (%d before filtering)",
                len(filtered), ticker, len(cases),
            )
            return filtered

    except Exception as exc:
        logger.warning("Supabase SCA lookup failed (non-fatal): %s", exc)

    return []


def _filter_matching_company(
    cases: list[dict[str, Any]],
    ticker: str,
    company_name: str | None,
) -> list[dict[str, Any]]:
    """Filter out cases for different companies with similar names.

    E.g., "Apple REIT Nine" and "Apple South" are NOT Apple Inc.
    """
    if not company_name:
        return [c for c in cases if c.get("ticker") == ticker]

    # Extract core company name (first word or two)
    core = company_name.split(",")[0].split(" Inc")[0].split(" Corp")[0].strip()

    # Exclusion patterns: names that share a prefix but are different companies
    _EXCLUSIONS = ("REIT", "South", "Hospitality", "Foster", "Leisure", "Industries")

    filtered = []
    for case in cases:
        cn = case.get("company_name", "")
        # Even for ticker matches, validate company name to catch database errors
        # (e.g., "Apple South, Inc." mapped to AAPL in Supabase)
        if cn and company_name:
            if any(excl in cn for excl in _EXCLUSIONS):
                # Check if the exclusion word is NOT in the actual company name
                if not any(excl in company_name for excl in _EXCLUSIONS):
                    logger.debug("Filtered wrong-company case: %s (ticker=%s)", cn, ticker)
                    continue
        # Exact ticker match
        if case.get("ticker") == ticker:
            filtered.append(case)
            continue
        # Company name must start with core name
        if cn.lower().startswith(core.lower()):
            if any(excl in cn for excl in _EXCLUSIONS):
                continue
            filtered.append(case)

    return filtered


def query_peer_sca_filings(
    tickers: list[str],
) -> list["PeerSCARecord"]:
    """Batch-query Supabase for SCA filings across peer tickers.

    Uses Supabase ``in.`` filter to fetch filings for multiple tickers
    in a single HTTP request. Returns structured PeerSCARecord models.

    Args:
        tickers: List of peer ticker symbols (e.g., ["AAPL", "MSFT"]).

    Returns:
        List of PeerSCARecord models, ordered by filing_date desc.
        Empty list if no tickers, no API key, or query fails.
    """
    from do_uw.models.company_intelligence import PeerSCARecord

    if not tickers:
        return []

    api_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not api_key:
        logger.warning(
            "Supabase key not available — peer SCA contagion data will be empty"
        )
        return []

    try:
        import httpx
    except ImportError:
        logger.warning("httpx not available — skipping peer SCA batch query")
        return []

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # Build in. filter: ticker=in.(AAPL,MSFT,GOOG)
    ticker_list = ",".join(t.upper() for t in tickers)
    url = (
        f"{_SUPABASE_URL}/rest/v1/{_TABLE}"
        f"?ticker=in.({ticker_list})"
        f"&select=company_name,ticker,filing_date,case_status,"
        f"settlement_amount_m,allegation_accounting,"
        f"allegation_insider_trading,allegation_earnings,"
        f"allegation_merger,allegation_ipo_offering,"
        f"case_summary,docket_number"
        f"&order=filing_date.desc"
        f"&limit=50"
    )

    try:
        resp = httpx.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            logger.warning(
                "Supabase peer SCA batch query failed: HTTP %d", resp.status_code
            )
            return []

        data = resp.json()
        if not isinstance(data, list):
            return []

        records: list[PeerSCARecord] = []
        for row in data:
            allegation = _infer_allegation_type(row)
            records.append(
                PeerSCARecord(
                    ticker=row.get("ticker", ""),
                    company_name=row.get("company_name", ""),
                    case_caption=row.get("case_summary", ""),
                    filing_date=row.get("filing_date", ""),
                    status=row.get("case_status", ""),
                    settlement_amount_m=row.get("settlement_amount_m"),
                    allegation_type=allegation,
                )
            )

        logger.info(
            "Supabase peer SCA batch: %d filings for %d tickers",
            len(records),
            len(tickers),
        )
        return records

    except Exception as exc:
        logger.warning("Supabase peer SCA batch query failed (non-fatal): %s", exc)
        return []


def _infer_allegation_type(row: dict[str, Any]) -> str:
    """Infer primary allegation type from boolean columns."""
    if row.get("allegation_accounting"):
        return "accounting"
    if row.get("allegation_insider_trading"):
        return "insider_trading"
    if row.get("allegation_earnings"):
        return "earnings"
    if row.get("allegation_merger"):
        return "merger"
    if row.get("allegation_ipo_offering"):
        return "ipo_offering"
    return "other"


def query_risk_card(ticker: str) -> dict[str, Any]:
    """Call get_risk_card(ticker) Supabase RPC for a complete litigation risk profile.

    Returns a single JSON blob with: company_profile, filing_history,
    scenario_benchmarks, screening_questions, repeat_filer_detail,
    liberty_layers, and data_coverage_note.

    Returns empty dict if Supabase is unavailable or no data found.
    """
    api_key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not api_key:
        logger.debug("No SUPABASE_KEY — skipping risk card lookup")
        return {}

    try:
        import httpx
    except ImportError:
        logger.debug("httpx not available — skipping risk card lookup")
        return {}

    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.post(
            f"{_SUPABASE_URL}/rest/v1/rpc/get_risk_card",
            headers=headers,
            json={"p_ticker": ticker.upper()},
            timeout=15,
        )
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, dict) and data.get("ticker"):
                logger.info(
                    "Supabase risk card: %s — score=%s, filings=%d, scenarios=%d",
                    ticker,
                    data.get("company_profile", {}).get("composite_risk_score", "N/A"),
                    len(data.get("filing_history", [])),
                    len(data.get("scenario_benchmarks", [])),
                )
                return data
            logger.debug("Risk card returned no data for %s", ticker)
        else:
            logger.warning("Risk card RPC failed: HTTP %d", resp.status_code)
    except Exception as exc:
        logger.warning("Risk card RPC failed (non-fatal): %s", exc)

    return {}


__all__ = ["query_sca_filings", "query_peer_sca_filings", "query_risk_card"]
