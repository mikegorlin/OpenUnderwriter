"""Dossier enrichment helper functions.

Revenue card row enrichment, concentration dimension helpers, and
text extraction utilities used by the main dossier_enrichment module.

Phase 118-03: Revenue Model & Company Intelligence Dossier
"""

from __future__ import annotations

import re

from do_uw.models.dossier import RevenueModelCardRow
from do_uw.models.scoring import ScoringResult


# -----------------------------------------------------------------------
# Revenue Card Row Enrichment Helpers
# -----------------------------------------------------------------------
def enrich_revenue_quality(
    row: RevenueModelCardRow, value_lower: str, tier: str, ticker: str,
) -> None:
    """Enrich Revenue Quality row."""
    if "tier 3" in value_lower or "project" in value_lower or "one-time" in value_lower:
        row.risk_level = "HIGH"
        row.do_risk = (
            f"One-time/project revenue creates earnings volatility for {ticker} "
            f"-- a primary SCA trigger per F.5. Non-recurring revenue "
            f"is difficult to forecast, increasing guidance miss risk."
        )
    elif "tier 2" in value_lower or "mixed" in value_lower:
        row.risk_level = "MEDIUM"
        row.do_risk = (
            f"Mixed revenue model for {ticker} ({row.value}) creates moderate "
            f"earnings visibility risk. Transition periods between models "
            f"are common SCA triggers."
        )
    else:
        # Tier 1 or recurring/subscription
        row.risk_level = "LOW"
        row.do_risk = (
            f"Recurring revenue model for {ticker} provides strong earnings "
            f"visibility, reducing guidance miss risk."
        )


def enrich_concentration_card(
    row: RevenueModelCardRow, value_lower: str, ticker: str,
) -> None:
    """Enrich Concentration Risk card row."""
    pct = extract_percentage(row.value)
    if pct is not None and pct > 30:
        row.risk_level = "HIGH"
        row.do_risk = (
            f"High concentration ({row.value}) for {ticker} creates material "
            f"disclosure risk under Item 303 if key relationship deteriorates."
        )
    elif pct is not None and pct > 15:
        row.risk_level = "MEDIUM"
        row.do_risk = (
            f"Moderate concentration ({row.value}) for {ticker} requires "
            f"ongoing disclosure monitoring."
        )
    else:
        row.risk_level = "LOW"
        row.do_risk = (
            f"Diversified customer base for {ticker} minimizes "
            f"single-customer disclosure risk."
        )


def enrich_revrec_card(
    row: RevenueModelCardRow, value_lower: str, ticker: str,
) -> None:
    """Enrich Rev-Rec Complexity card row."""
    if "high" in value_lower or "complex" in value_lower:
        row.risk_level = "HIGH"
        row.do_risk = (
            f"Complex revenue recognition for {ticker} is a top-3 SCA "
            f"allegation category. Rev-rec judgment areas invite "
            f"plaintiff scrutiny."
        )
    elif "medium" in value_lower or "moderate" in value_lower:
        row.risk_level = "MEDIUM"
        row.do_risk = (
            f"Moderate rev-rec complexity for {ticker} requires consistent "
            f"application of ASC 606 judgment areas."
        )
    else:
        row.risk_level = "LOW"
        row.do_risk = (
            f"Standard revenue recognition for {ticker} with minimal "
            f"judgment areas."
        )


def enrich_generic_card(
    row: RevenueModelCardRow,
    scoring: ScoringResult | None,
    tier: str,
    ticker: str,
) -> None:
    """Enrich a generic revenue card row without specific handler."""
    if scoring is not None and scoring.quality_score < 50:
        row.risk_level = "MEDIUM"
        row.do_risk = (
            f"{row.attribute} for {ticker} ({row.value}) warrants "
            f"monitoring given {tier} tier classification."
        )
    else:
        row.risk_level = "LOW"
        row.do_risk = (
            f"{row.attribute}: {row.value}. No elevated exposure identified."
        )


# -----------------------------------------------------------------------
# Concentration Dimension Implication Map
# -----------------------------------------------------------------------
CONCENTRATION_IMPLICATION_MAP: dict[str, str] = {
    "customer": (
        "Loss of top customer = material misstatement if not "
        "disclosed per Item 303"
    ),
    "geographic": (
        "Geographic concentration exposes company to regional "
        "regulatory/economic shocks -- disclosure obligation "
        "under MD&A"
    ),
    "product": (
        "Product concentration risk: obsolescence or quality "
        "issue creates outsized revenue impact requiring "
        "immediate disclosure"
    ),
    "channel": (
        "Channel concentration creates dependency risk -- "
        "platform/distributor changes may require Item 1A "
        "risk factor update"
    ),
    "payer": (
        "Payer concentration increases collection risk and "
        "potential revenue timing disputes under ASC 606"
    ),
}


# -----------------------------------------------------------------------
# Text Extraction Utilities
# -----------------------------------------------------------------------
def extract_percentage(text: str) -> float | None:
    """Extract the first percentage value from text.

    Handles: "40%", "Top 1 = 40%", "= 5%", etc.
    """
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if match:
        return float(match.group(1))
    return None


def extract_number(text: str) -> float | None:
    """Extract a number from text like '85%', '3.2x', '$100M'."""
    match = re.search(r"(-?\d+(?:\.\d+)?)", text)
    if match:
        return float(match.group(1))
    return None


def extract_dollar_amount(text: str) -> float | None:
    """Extract dollar amount in millions from text like '$31M', '$145M'."""
    match = re.search(r"\$(\d+(?:\.\d+)?)\s*[MmBb]?", text)
    if match:
        val = float(match.group(1))
        if "b" in text.lower():
            val *= 1000  # Convert B to M
        return val
    return None
