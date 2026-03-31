"""Tier classification and claim probability for D&O underwriting.

Maps quality scores to underwriting tiers (WIN through NO_TOUCH)
using tier boundaries from scoring.json. Computes claim probability
bands from tier probability ranges.
"""

from __future__ import annotations

import re
from typing import Any

from do_uw.models.company import CompanyProfile
from do_uw.models.scoring import (
    ClaimProbability,
    ProbabilityBand,
    Tier,
    TierClassification,
)

# -----------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------


def classify_tier(
    quality_score: float,
    tier_config: list[dict[str, Any]],
) -> TierClassification:
    """Classify quality score into an underwriting tier.

    Args:
        quality_score: Final quality score after CRF ceilings.
        tier_config: Tier definitions from scoring.json["tiers"].

    Returns:
        TierClassification with all fields populated.
    """
    for tier_entry in tier_config:
        min_score = int(tier_entry.get("min_score", 0))
        max_score = int(tier_entry.get("max_score", 100))
        if min_score <= quality_score <= max_score:
            tier_name = str(tier_entry.get("tier", "NO_TOUCH"))
            return TierClassification(
                tier=Tier(tier_name),
                score_range_low=min_score,
                score_range_high=max_score,
                probability_range=str(
                    tier_entry.get("probability_range", "")
                ),
                pricing_multiplier=str(
                    tier_entry.get("pricing_multiplier", "")
                ),
                action=str(tier_entry.get("action", "")),
            )

    # Fallback to NO_TOUCH if no range matches
    return TierClassification(
        tier=Tier.NO_TOUCH,
        score_range_low=0,
        score_range_high=10,
        probability_range=">20%",
        pricing_multiplier="N/A",
        action="Decline",
    )


def apply_industry_ceiling(
    tier: TierClassification,
    state: Any,
    tier_config: list[dict[str, Any]],
) -> TierClassification:
    """Apply industry-specific tier ceilings.

    Pre-revenue biotech companies cannot score above WATCH regardless
    of quantitative score — clinical-stage companies with no revenue
    have fundamentally different risk profiles that the generic scoring
    model doesn't capture.

    Args:
        tier: Current tier classification.
        state: AnalysisState (typed as Any to avoid circular import).
        tier_config: Tier definitions from scoring.json.

    Returns:
        Adjusted TierClassification, or original if no ceiling applies.
    """
    # Check if biotech playbook active
    playbook = getattr(state, "active_playbook_id", "") or ""
    if "BIOTECH" not in playbook.upper():
        return tier

    # Check if pre-revenue
    has_revenue = False
    if hasattr(state, "extracted") and state.extracted:
        fin = state.extracted.financials
        if fin:
            annual = getattr(fin, "annual_financials", None)
            if annual:
                ann_val = annual.value if hasattr(annual, "value") else annual
                if isinstance(ann_val, dict):
                    rev = ann_val.get("revenue")
                    if rev and isinstance(rev, dict):
                        rev_val = rev.get("value", 0)
                        if rev_val and float(rev_val or 0) > 10_000_000:
                            has_revenue = True
                    elif rev and isinstance(rev, (int, float)) and rev > 10_000_000:
                        has_revenue = True

    if has_revenue:
        return tier  # Revenue-stage biotech — no ceiling

    # Pre-revenue biotech: ceiling at WATCH
    _TIER_ORDER = {"WIN": 0, "WRITE": 1, "WATCH": 2, "WALK": 3, "NO_TOUCH": 4}
    current_rank = _TIER_ORDER.get(tier.tier.value, 4)
    ceiling_rank = _TIER_ORDER.get("WATCH", 2)

    if current_rank < ceiling_rank:
        # Score is above ceiling — downgrade to WATCH
        for entry in tier_config:
            if entry.get("tier") == "WATCH":
                return TierClassification(
                    tier=Tier.WATCH,
                    score_range_low=int(entry.get("min_score", 31)),
                    score_range_high=int(entry.get("max_score", 50)),
                    probability_range=str(entry.get("probability_range", "8.3-11.9%")),
                    pricing_multiplier=str(entry.get("pricing_multiplier", "1.5-2x")),
                    action="Pre-revenue biotech ceiling — "
                           + str(entry.get("action", "Write carefully")),
                )
        # Fallback WATCH if config entry not found
        return TierClassification(
            tier=Tier.WATCH,
            score_range_low=31,
            score_range_high=50,
            probability_range="8.3-11.9%",
            pricing_multiplier="1.5-2x + attachment",
            action="Pre-revenue biotech ceiling — write carefully, senior review required",
        )

    return tier


def compute_claim_probability(
    tier: TierClassification,
    company: CompanyProfile | None,
    sectors_config: dict[str, Any],
) -> ClaimProbability:
    """Compute claim probability from tier classification.

    Args:
        tier: Assigned tier with probability_range string.
        company: Company profile for sector lookup.
        sectors_config: Sector config for base rates.

    Returns:
        ClaimProbability with band, range values, and narrative.
    """
    range_str = tier.probability_range
    band = probability_range_to_band(range_str)
    low_pct, high_pct = _parse_probability_range(range_str)

    # Look up industry base rate
    base_rate = _get_industry_base_rate(company, sectors_config)

    # Build adjustment narrative
    narrative = _build_adjustment_narrative(
        tier.tier, band, base_rate, low_pct, high_pct
    )

    return ClaimProbability(
        band=band,
        range_low_pct=low_pct,
        range_high_pct=high_pct,
        industry_base_rate_pct=base_rate,
        adjustment_narrative=narrative,
        needs_calibration=True,
    )


# -----------------------------------------------------------------------
# Probability band helpers
# -----------------------------------------------------------------------


def probability_range_to_band(range_str: str) -> ProbabilityBand:
    """Map probability range string to ProbabilityBand enum.

    Examples:
        "<2%"    -> LOW
        "2-5%"   -> MODERATE
        "5-10%"  -> ELEVATED
        "10-15%" -> HIGH
        ">20%"   -> VERY_HIGH
    """
    clean = range_str.strip()
    if clean.startswith("<"):
        return ProbabilityBand.LOW
    if clean.startswith(">"):
        return ProbabilityBand.VERY_HIGH

    # Parse "X-Y%" format (supports decimals like "5.1-7.3%")
    match = re.match(r"(\d+\.?\d*)-(\d+\.?\d*)%?", clean)
    if match:
        low = float(match.group(1))
        if low < 5:
            return ProbabilityBand.MODERATE
        if low < 10:
            return ProbabilityBand.ELEVATED
        if low < 15:
            return ProbabilityBand.HIGH
        return ProbabilityBand.VERY_HIGH

    return ProbabilityBand.MODERATE


def _parse_probability_range(range_str: str) -> tuple[float, float]:
    """Parse probability range string into (low, high) percentages.

    Examples:
        "<2%"     -> (0.0, 2.0)
        "2-5%"    -> (2.0, 5.0)
        "5-10%"   -> (5.0, 10.0)
        "10-15%"  -> (10.0, 15.0)
        "15-20%"  -> (15.0, 20.0)
        ">20%"    -> (20.0, 25.0)
    """
    clean = range_str.strip().rstrip("%")

    # Handle "<X%"
    lt_match = re.match(r"<\s*(\d+\.?\d*)", clean)
    if lt_match:
        return 0.0, float(lt_match.group(1))

    # Handle ">X%"
    gt_match = re.match(r">\s*(\d+\.?\d*)", clean)
    if gt_match:
        low = float(gt_match.group(1))
        return low, min(low + 5.0, 25.0)

    # Handle "X-Y%"
    range_match = re.match(r"(\d+\.?\d*)\s*-\s*(\d+\.?\d*)", clean)
    if range_match:
        return float(range_match.group(1)), float(range_match.group(2))

    return 0.0, 5.0


# -----------------------------------------------------------------------
# Industry base rate and narrative
# -----------------------------------------------------------------------


def _get_industry_base_rate(
    company: CompanyProfile | None,
    sectors_config: dict[str, Any],
) -> float:
    """Look up industry base claim rate from sectors config.

    Default base rate is 4.0% (roughly 1 in 25 public companies
    per year face a securities class action).
    """
    default_rate = 4.0

    if company is None:
        return default_rate

    sector_code = "DEFAULT"
    if company.identity.sector is not None:
        sector_code = company.identity.sector.value

    # Check for sector-specific claim rate in sectors config
    claim_rates = sectors_config.get("claim_base_rates", {})
    if sector_code in claim_rates:
        return float(claim_rates[sector_code])
    if "DEFAULT" in claim_rates:
        return float(claim_rates["DEFAULT"])

    return default_rate


def _build_adjustment_narrative(
    tier: Tier,
    band: ProbabilityBand,
    base_rate: float,
    low_pct: float,
    high_pct: float,
) -> str:
    """Build narrative explaining probability adjustments."""
    parts: list[str] = [
        f"Industry base rate: {base_rate:.1f}%.",
    ]

    if band == ProbabilityBand.LOW:
        parts.append(
            f"Tier {tier.value} ({low_pct:.0f}-{high_pct:.0f}%): "
            "Below base rate. Strong risk profile reduces claim "
            "probability below industry average."
        )
    elif band == ProbabilityBand.MODERATE:
        parts.append(
            f"Tier {tier.value} ({low_pct:.0f}-{high_pct:.0f}%): "
            "Near base rate. Risk profile consistent with industry "
            "average claim frequency."
        )
    elif band == ProbabilityBand.ELEVATED:
        parts.append(
            f"Tier {tier.value} ({low_pct:.0f}-{high_pct:.0f}%): "
            "Above base rate. Multiple risk factors elevate claim "
            "probability above industry average."
        )
    elif band == ProbabilityBand.HIGH:
        parts.append(
            f"Tier {tier.value} ({low_pct:.0f}-{high_pct:.0f}%): "
            "Significantly above base rate. Concentration of risk "
            "factors suggests elevated claim likelihood."
        )
    elif band == ProbabilityBand.VERY_HIGH:
        parts.append(
            f"Tier {tier.value} ({low_pct:.0f}-{high_pct:.0f}%): "
            "Substantially above base rate. Critical risk factors "
            "and/or red flags indicate high claim probability."
        )

    parts.append(
        "NEEDS CALIBRATION: Probability estimates are indicative "
        "and require actuarial validation per SECT7-11."
    )
    return " ".join(parts)
