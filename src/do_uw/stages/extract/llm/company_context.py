"""Company context overlay for LLM extraction prompts.

Appends company-specific context (sector, size, business model) to
system prompts so the LLM can calibrate its extraction and assessment
relative to what's normal for this type of company.

This is the fix for false positives like Apple's current ratio < 1.0
triggering a liquidity warning — mega-cap tech companies intentionally
run negative working capital.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile

logger = logging.getLogger(__name__)


# Market cap tier breakpoints (USD)
_MCAP_TIERS: list[tuple[float, str]] = [
    (200e9, "mega-cap"),
    (10e9, "large-cap"),
    (2e9, "mid-cap"),
    (300e6, "small-cap"),
    (50e6, "micro-cap"),
    (0, "nano-cap"),
]

# SIC-based sector context for LLM guidance.
# Each entry: (SIC range start, SIC range end, sector label, model notes)
_SECTOR_CONTEXT: list[tuple[int, int, str, str]] = [
    (7370, 7379, "Technology/Software", (
        "Software/SaaS companies often have high deferred revenue, "
        "negative working capital by design, and intangible-heavy "
        "balance sheets. Current ratio < 1.0 may reflect subscription "
        "prepayments, not distress. Focus on cash flow generation, "
        "ARR/NRR trends, and revenue recognition practices."
    )),
    (3570, 3579, "Technology/Hardware", (
        "Computer hardware companies operate asset-light distribution "
        "models. Negative working capital is common (Apple, Dell) due to "
        "high inventory turnover and extended supplier payment terms. "
        "Assess cash conversion cycle and operating cash flow, not "
        "current ratio in isolation."
    )),
    (3674, 3674, "Semiconductors", (
        "Semiconductor companies are capital-intensive with cyclical "
        "revenue. Inventory levels fluctuate with demand cycles. "
        "Working capital needs are highly variable. Assess against "
        "semiconductor cycle position, not generic industrial norms."
    )),
    (6000, 6199, "Banking/Financial", (
        "Banks and financial institutions have fundamentally different "
        "balance sheet structures. Leverage ratios, Tier 1 capital, "
        "loan loss reserves, and NIM are the relevant metrics — not "
        "current ratio or working capital. Standard industrial "
        "financial health signals do not apply."
    )),
    (6200, 6399, "Financial Services/Insurance", (
        "Insurance and financial services companies hold regulatory "
        "reserves that distort standard metrics. Loss reserves, "
        "combined ratio, and investment income are the relevant metrics."
    )),
    (2830, 2836, "Pharmaceuticals/Biotech", (
        "Pharmaceutical and biotech companies may have no revenue "
        "(clinical-stage), massive R&D burn rates, and binary event "
        "risk (FDA approvals). Cash runway relative to next catalyst "
        "is the key metric. Traditional profitability signals don't "
        "apply to pre-revenue biotechs."
    )),
    (4910, 4941, "Utilities", (
        "Utilities operate with regulated returns and high leverage "
        "by design. Debt/EBITDA of 4-6x is normal (vs 2-3x for tech). "
        "Rate case outcomes and regulatory relationships are more "
        "relevant than leverage ratios."
    )),
    (5411, 5499, "Retail/Consumer", (
        "Retailers often have negative working capital from high "
        "inventory turnover and trade payables. Assess same-store "
        "sales, inventory days, and cash conversion cycle."
    )),
    (1311, 1389, "Oil & Gas", (
        "Energy companies have highly cyclical earnings tied to "
        "commodity prices. Reserve replacement, finding costs, and "
        "hedging programs are key metrics. Standard deviation thresholds "
        "must account for commodity price volatility."
    )),
]


def _get_mcap_tier(market_cap: float | None) -> str:
    """Classify market cap into tier label."""
    if market_cap is None:
        return "unknown"
    for threshold, label in _MCAP_TIERS:
        if market_cap >= threshold:
            return label
    return "nano-cap"


def _format_mcap(market_cap: float | None) -> str:
    """Format market cap as human-readable string."""
    if market_cap is None:
        return "unknown"
    if market_cap >= 1e12:
        return f"${market_cap / 1e12:.1f}T"
    if market_cap >= 1e9:
        return f"${market_cap / 1e9:.1f}B"
    if market_cap >= 1e6:
        return f"${market_cap / 1e6:.0f}M"
    return f"${market_cap:,.0f}"


def _get_sector_context(sic_code: str | None) -> tuple[str, str]:
    """Get sector label and model context from SIC code.

    Returns:
        Tuple of (sector_label, context_notes).
    """
    if not sic_code:
        return ("Unknown", "")
    try:
        sic_int = int(sic_code)
    except ValueError:
        return ("Unknown", "")

    for start, end, label, notes in _SECTOR_CONTEXT:
        if start <= sic_int <= end:
            return (label, notes)
    return ("General", "")


def _extract_company_fields(company: CompanyProfile) -> dict[str, Any]:
    """Safely extract relevant fields from CompanyProfile."""
    def _sv(val: Any) -> Any:
        if val is None:
            return None
        if hasattr(val, "value"):
            return val.value
        return val

    identity = company.identity
    return {
        "ticker": identity.ticker,
        "legal_name": _sv(identity.legal_name),
        "sic_code": _sv(identity.sic_code),
        "sic_description": _sv(identity.sic_description),
        "sector": _sv(identity.sector),
        "market_cap": _sv(company.market_cap),
        "filer_category": _sv(company.filer_category),
        "years_public": _sv(company.years_public),
        "employee_count": _sv(company.employee_count),
        "revenue_model_type": _sv(company.revenue_model_type),
    }


def build_company_context(company: CompanyProfile | None) -> str:
    """Build company context string to append to LLM extraction prompts.

    Provides the LLM with sector, size, and business model information
    so it can calibrate extraction and assessment. This prevents false
    positives from applying generic industrial norms to companies with
    fundamentally different financial structures.

    Args:
        company: CompanyProfile from state, or None if unavailable.

    Returns:
        Context string to append to system prompt. Empty if no useful
        context is available.
    """
    if company is None:
        return ""

    fields = _extract_company_fields(company)
    parts: list[str] = []

    # Company identity
    name = fields["legal_name"] or fields["ticker"]
    ticker = fields["ticker"]
    parts.append(f"COMPANY CONTEXT: {name} ({ticker})")

    # Sector + SIC context
    sector_label, sector_notes = _get_sector_context(fields["sic_code"])
    sic_desc = fields["sic_description"] or ""
    if sic_desc:
        parts.append(f"Industry: {sic_desc} (SIC: {fields['sic_code']})")
    if sector_label != "Unknown":
        parts.append(f"Sector: {sector_label}")

    # Market cap + tier
    mcap = fields["market_cap"]
    if mcap is not None:
        tier = _get_mcap_tier(mcap)
        parts.append(f"Market Cap: {_format_mcap(mcap)} ({tier})")

    # Filer category
    filer = fields["filer_category"]
    if filer:
        parts.append(f"SEC Filer Category: {filer}")

    # Years public
    yrs = fields["years_public"]
    if yrs is not None:
        if yrs <= 2:
            parts.append(f"Years Public: {yrs} (RECENT IPO — heightened Section 11 exposure)")
        else:
            parts.append(f"Years Public: {yrs}")

    # Employee count
    emp = fields["employee_count"]
    if emp is not None:
        parts.append(f"Employees: {emp:,}")

    # Revenue model
    rev_model = fields["revenue_model_type"]
    if rev_model:
        parts.append(f"Revenue Model: {rev_model}")

    # Sector-specific guidance
    if sector_notes:
        parts.append(f"\nSECTOR-SPECIFIC GUIDANCE:\n{sector_notes}")

    # Size-specific guidance
    if mcap is not None:
        tier = _get_mcap_tier(mcap)
        if tier == "mega-cap":
            parts.append(
                "\nSIZE CONTEXT: Mega-cap companies have deep capital "
                "market access, diversified revenue streams, and often "
                "intentionally optimize working capital. Standard small-company "
                "financial distress signals (current ratio, quick ratio) may "
                "not indicate actual risk. Focus on cash flow adequacy, "
                "covenant compliance, and credit rating trajectory."
            )
        elif tier in ("micro-cap", "nano-cap"):
            parts.append(
                "\nSIZE CONTEXT: Micro/nano-cap companies have limited "
                "capital market access, concentrated revenue, and higher "
                "financial fragility. Standard distress signals are MORE "
                "meaningful — treat liquidity and leverage warnings with "
                "elevated severity."
            )

    if len(parts) <= 1:
        return ""

    context = "\n".join(parts)
    logger.info(
        "Built company context overlay for %s (%s, %s)",
        ticker,
        sector_label,
        _get_mcap_tier(mcap) if mcap else "unknown",
    )
    return f"\n\n{context}\n"


__all__ = ["build_company_context"]
