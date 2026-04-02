"""Acquisition inventory checker for incremental pipeline runs.

Inspects state.acquired_data to determine which data sources already
have sufficient data and can be skipped on re-runs.

Per CLAUDE.md memory: "Incremental acquisition (NON-NEGOTIABLE): Pipeline
must reuse existing data -- never re-run expensive LLM extractions or
API calls for data that hasn't changed."
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from do_uw.models.state import AcquiredData


@dataclass
class AcquisitionInventory:
    """Tracks which data sources need fetching vs already acquired."""

    needs_sec_filings: bool = True
    needs_market_data: bool = True
    needs_litigation: bool = True
    needs_news: bool = True
    needs_blind_spot: bool = True
    needs_courtlistener: bool = True
    needs_patents: bool = True
    needs_logo: bool = True
    needs_frames: bool = True
    needs_regulatory_data: bool = True
    needs_reference_data: bool = True
    skip_reasons: dict[str, str] = field(default_factory=dict)


def check_inventory(acquired: AcquiredData | None) -> AcquisitionInventory:
    """Check existing acquired data and return inventory of what's needed.

    Each source has a completeness heuristic:
    - SEC filings: at least 2 docs across 2+ form types
    - Market data: has history_1y or stock_info
    - Litigation: non-empty litigation_data
    - News: non-empty web_search_results
    - Blind spot: non-empty blind_spot_results
    - Patents: non-empty patent_data
    - Logo: non-empty company_logo_b64

    Args:
        acquired: Existing AcquiredData from a prior run, or None.

    Returns:
        AcquisitionInventory indicating which sources still need fetching.
    """
    inv = AcquisitionInventory()
    if acquired is None:
        return inv

    # SEC filings: complete if filing_documents has at least 2 form types
    # with docs (ensures we have both 10-K and DEF 14A at minimum).
    if acquired.filing_documents:
        doc_count = sum(len(docs) for docs in acquired.filing_documents.values())
        form_types = len(acquired.filing_documents)
        if doc_count >= 2 and form_types >= 2:
            inv.needs_sec_filings = False
            inv.skip_reasons["sec_filings"] = (
                f"Already have {doc_count} docs across {form_types} form types"
            )

    # Market data: complete if has history_1y or stock_info.
    if acquired.market_data:
        has_key_data = "history_1y" in acquired.market_data or "stock_info" in acquired.market_data
        if has_key_data:
            inv.needs_market_data = False
            inv.skip_reasons["market_data"] = (
                f"Already have {len(acquired.market_data)} market data keys"
            )

    # Litigation: complete if litigation_data is non-empty.
    if acquired.litigation_data:
        inv.needs_litigation = False
        inv.skip_reasons["litigation"] = (
            f"Already have litigation data with {len(acquired.litigation_data)} keys"
        )

    # News/web search: complete if web_search_results is non-empty.
    if acquired.web_search_results:
        inv.needs_news = False
        inv.skip_reasons["news"] = "Already have web search results"

    # Blind spot: complete if blind_spot_results is non-empty.
    if acquired.blind_spot_results:
        inv.needs_blind_spot = False
        inv.skip_reasons["blind_spot"] = "Already have blind spot results"

    # CourtListener: complete if courtlistener data exists in litigation.
    if acquired.litigation_data and acquired.litigation_data.get("courtlistener"):
        inv.needs_courtlistener = False
        inv.skip_reasons["courtlistener"] = "Already have CourtListener data"

    # Patents: complete if patent_data is non-empty.
    if acquired.patent_data:
        inv.needs_patents = False
        inv.skip_reasons["patents"] = "Already have patent data"

    # Logo: complete if company_logo_b64 is non-empty.
    if acquired.company_logo_b64:
        inv.needs_logo = False
        inv.skip_reasons["logo"] = "Already have company logo"

    # Frames: complete if filings has frames key.
    if acquired.filings and acquired.filings.get("frames"):
        inv.needs_frames = False
        inv.skip_reasons["frames"] = "Already have SEC Frames data"

    # Regulatory data: complete if regulatory_data exists and has content.
    if acquired.regulatory_data:
        inv.needs_regulatory_data = False
        inv.skip_reasons["regulatory_data"] = "Already have regulatory data"

    # Reference data: complete if reference_data exists and has content.
    if acquired.reference_data:
        inv.needs_reference_data = False
        inv.skip_reasons["reference_data"] = "Already have reference data"

    return inv
