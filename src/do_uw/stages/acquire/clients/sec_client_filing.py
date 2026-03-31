"""Filing fetch helpers for SEC EDGAR.

Split from sec_client.py (Phase 45, 500-line rule).

Contains the low-level functions that fetch and parse filing
lists from the SEC EDGAR submissions API and EFTS full-text
search endpoint.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from do_uw.stages.acquire.rate_limiter import sec_get

logger = logging.getLogger(__name__)


# Filing types by company type (duplicated constants for self-contained use).
FILING_LOOKBACK: dict[str, int] = {
    "10-K": 3,
    "10-K/A": 3,      # Amendment filings signal restatements
    "20-F": 3,
    "10-Q": 12,
    "10-Q/A": 12,     # Quarterly amendment filings
    "6-K": 12,
    "DEF 14A": 3,
    "8-K": 50,         # 3 years of events (~15-20/year for large filers)
    "4": 50,           # 3 years of insider trades
    "S-3": 5,
    "S-1": 3,
    "424B": 5,
    "SC 13D": 10,
    "SC 13G": 10,
}

# SEC EDGAR base URLs.
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_EFTS_URL = (
    "https://efts.sec.gov/LATEST/search-index"
    "?q={query}&forms={form}&dateRange=custom"
    "&startdt={start}&enddt={end}"
)

# Form type variant matching.
_FORM_TYPE_VARIANTS: dict[str, list[str]] = {
    "4": ["4", "4/A"],
    "10-K/A": ["10-K/A", "10-KSB/A"],
    "10-Q/A": ["10-Q/A", "10-QSB/A"],
    "S-3": ["S-3", "S-3ASR", "S-3/A", "S-3D"],
    "S-1": ["S-1", "S-1/A"],
    "424B": ["424B1", "424B2", "424B3", "424B4", "424B5"],
    "SC 13D": ["SC 13D", "SC 13D/A", "SC13D", "SC13D/A"],
    "SC 13G": [
        "SC 13G", "SC 13G/A", "SC13G", "SC13G/A",
        "SCHEDULE 13G", "SCHEDULE 13G/A",
    ],
}


def _form_type_matches(filed_form: str, target_type: str) -> bool:
    """Check if a filed form matches the target type, including variants."""
    if filed_form == target_type:
        return True
    variants = _FORM_TYPE_VARIANTS.get(target_type)
    if variants is not None:
        return filed_form in variants
    return False


def _fetch_from_submissions(
    padded_cik: str,
    form_type: str,
) -> dict[str, Any] | None:
    """Fetch filing list from SEC EDGAR submissions API.

    Args:
        padded_cik: 10-digit zero-padded CIK.
        form_type: SEC form type (e.g., '10-K', 'DEF 14A').

    Returns:
        Dict with 'filings' key containing list of filing metadata,
        or None if no filings found.
    """
    url = SEC_SUBMISSIONS_URL.format(cik=padded_cik)
    data = sec_get(url)

    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return None

    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    dates = recent.get("filingDate", [])
    primary_docs = recent.get("primaryDocument", [])

    lookback = FILING_LOOKBACK.get(form_type, 10)
    cutoff = _filing_cutoff_date(form_type)

    filings: list[dict[str, str]] = []
    for i, form in enumerate(forms):
        if not _form_type_matches(form, form_type):
            continue
        if i >= len(dates) or dates[i] < cutoff:
            continue
        if len(filings) >= lookback:
            break

        accession = accessions[i] if i < len(accessions) else ""
        acc_no_dashes = accession.replace("-", "")
        cik_raw = padded_cik.lstrip("0") or "0"
        primary_doc = primary_docs[i] if i < len(primary_docs) else ""

        # For Form 4, strip XSLT prefix to get raw XML URL.
        if form_type == "4" and primary_doc.startswith("xsl"):
            parts = primary_doc.split("/", 1)
            if len(parts) == 2:
                primary_doc = parts[1]

        filing_url = (
            f"https://www.sec.gov/Archives/edgar/data/"
            f"{cik_raw}/{acc_no_dashes}/{primary_doc}"
        )

        filings.append({
            "accession_number": accession,
            "filing_date": dates[i] if i < len(dates) else "",
            "form_type": form,
            "primary_doc_url": filing_url,
            "filing_url": (
                f"https://www.sec.gov/cgi-bin/browse-edgar"
                f"?action=getcompany&CIK={cik_raw}"
                f"&type={form_type}&dateb=&owner=include&count=10"
            ),
        })

    if not filings:
        return None

    return {"filings": filings}


def _fetch_from_efts(
    ticker: str,
    form_type: str,
    cik: str,
) -> dict[str, Any] | None:
    """Fetch filings via SEC EFTS full-text search as discovery fallback.

    Args:
        ticker: Company ticker symbol.
        form_type: SEC form type to search for.
        cik: Company CIK (unpadded).

    Returns:
        Dict with 'filings' key, or None if no results.
    """
    cutoff = _filing_cutoff_date(form_type)
    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")

    # Use the first variant for EFTS (e.g., S-3ASR for S-3 queries).
    efts_form = form_type
    variants = _FORM_TYPE_VARIANTS.get(form_type)
    if variants and len(variants) > 1:
        efts_form = variants[1] if variants[0] == form_type else variants[0]

    url = SEC_EFTS_URL.format(
        query=ticker,
        form=efts_form,
        start=cutoff,
        end=today,
    )

    try:
        data = sec_get(url)
    except Exception:
        logger.debug("EFTS search failed for %s %s", ticker, form_type)
        return None

    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        return None

    lookback = FILING_LOOKBACK.get(form_type, 10)
    filings: list[dict[str, str]] = []

    for hit in hits[:lookback]:
        source = hit.get("_source", {})
        accession = source.get("file_num", "")
        filing_date = source.get("file_date", "")
        filing_url = source.get("file_url", "")

        filings.append({
            "accession_number": accession,
            "filing_date": filing_date,
            "form_type": form_type,
            "primary_doc_url": filing_url,
            "filing_url": filing_url,
        })

    if not filings:
        return None

    return {"filings": filings}


def _filing_cutoff_date(form_type: str) -> str:
    """Calculate the cutoff date for filing lookback.

    Returns ISO date string for how far back to look for a given
    filing type.
    """
    now = datetime.now(tz=UTC)
    if form_type in {"10-K", "20-F", "DEF 14A", "S-3", "S-1", "424B"}:
        cutoff = now - timedelta(days=3 * 365)
    elif form_type in {"10-Q", "6-K"}:
        cutoff = now - timedelta(days=3 * 365)
    elif form_type in {"8-K", "SC 13D", "SC 13G"}:
        cutoff = now - timedelta(days=365)
    elif form_type == "4":
        cutoff = now - timedelta(days=180)
    else:
        cutoff = now - timedelta(days=365)
    return cutoff.strftime("%Y-%m-%d")
