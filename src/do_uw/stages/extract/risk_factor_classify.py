"""Risk factor classification: STANDARD / NOVEL / ELEVATED.

Deterministic classification of Item 1A risk factors based on
year-over-year changes and severity. No LLM calls required.

Uses difflib.SequenceMatcher (same approach as ten_k_yoy.py) for
fuzzy title matching between current and prior year factors.

Public API:
    classify_risk_factors(factors, prior_factors) -> list[RiskFactorProfile]
"""

from __future__ import annotations

import logging
from difflib import SequenceMatcher

from do_uw.models.state import RiskFactorProfile

logger = logging.getLogger(__name__)

# Minimum similarity ratio for title matching (same threshold as ten_k_yoy.py).
_TITLE_MATCH_THRESHOLD = 0.6

# Severity ordering for escalation detection.
_SEVERITY_RANK: dict[str, int] = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

# Category -> D&O litigation implication mapping.
_CATEGORY_DO_IMPLICATIONS: dict[str, str] = {
    "LITIGATION": (
        "Direct SCA trigger — company acknowledges litigation risk "
        "that may create Section 10b-5 exposure"
    ),
    "REGULATORY": (
        "Regulatory action creates Section 10b-5 exposure if "
        "investigation or enforcement was concealed from investors"
    ),
    "FINANCIAL": (
        "Financial deterioration triggers revenue miss SCA theory "
        "if management guidance was misleading"
    ),
    "CYBER": (
        "Data breach creates CCPA/GDPR privacy SCA exposure "
        "when breach disclosure impacts stock price"
    ),
    "ESG": (
        "ESG compliance failure creates derivative suit exposure "
        "for board failure to oversee sustainability commitments"
    ),
    "AI": (
        "AI liability creates emerging SCA theory for algorithmic "
        "harm, bias, or EU AI Act non-compliance"
    ),
    "OPERATIONAL": (
        "Operational disruption creates Section 10b-5 exposure "
        "if management failed to disclose known risks"
    ),
    "OTHER": (
        "Risk factor may create D&O exposure depending on "
        "materiality and disclosure adequacy"
    ),
}


def classify_risk_factors(
    factors: list[RiskFactorProfile],
    prior_factors: list[RiskFactorProfile] | None = None,
) -> list[RiskFactorProfile]:
    """Classify risk factors as STANDARD, NOVEL, or ELEVATED.

    Classification logic (deterministic):
    - is_new_this_year=True => NOVEL
    - severity="HIGH" AND (escalated from prior OR no prior match) => ELEVATED
    - All others => STANDARD

    Also populates do_implication based on category mapping.

    Args:
        factors: Current year risk factors to classify.
        prior_factors: Prior year factors for comparison (optional).

    Returns:
        Same list with classification and do_implication fields populated.
    """
    if not factors:
        return factors

    # Build prior factor lookup for fuzzy matching.
    prior_map: dict[int, RiskFactorProfile] = {}
    if prior_factors:
        for i, pf in enumerate(prior_factors):
            prior_map[i] = pf

    result: list[RiskFactorProfile] = []
    for factor in factors:
        classification = _classify_single(factor, prior_factors or [])
        do_implication = _CATEGORY_DO_IMPLICATIONS.get(
            factor.category,
            _CATEGORY_DO_IMPLICATIONS["OTHER"],
        )

        # Create updated copy with classification fields.
        updated = factor.model_copy(
            update={
                "classification": classification,
                "do_implication": do_implication,
            }
        )
        result.append(updated)

    novel_count = sum(1 for f in result if f.classification == "NOVEL")
    elevated_count = sum(1 for f in result if f.classification == "ELEVATED")
    logger.info(
        "Classified %d risk factors: %d NOVEL, %d ELEVATED, %d STANDARD",
        len(result),
        novel_count,
        elevated_count,
        len(result) - novel_count - elevated_count,
    )

    return result


def _classify_single(
    factor: RiskFactorProfile,
    prior_factors: list[RiskFactorProfile],
) -> str:
    """Classify a single risk factor.

    Priority: NOVEL (new this year) > ELEVATED (high + escalated) > STANDARD.
    """
    # Rule 1: New factors are NOVEL.
    if factor.is_new_this_year:
        return "NOVEL"

    # Rule 2: HIGH severity with escalation from prior year -> ELEVATED.
    # Only check if prior_factors are available — without comparison data,
    # we can't determine escalation, so default to STANDARD (not ELEVATED).
    if factor.severity == "HIGH" and prior_factors:
        matched_prior = _find_matching_prior(factor.title, prior_factors)
        if matched_prior is None:
            # New HIGH severity factor not in prior year -> ELEVATED.
            return "ELEVATED"
        prior_rank = _SEVERITY_RANK.get(matched_prior.severity, 2)
        current_rank = _SEVERITY_RANK.get(factor.severity, 2)
        if current_rank > prior_rank:
            return "ELEVATED"

    # Rule 3: Everything else is STANDARD.
    # When no prior_factors available, all non-NOVEL factors are STANDARD
    # (we can't claim ELEVATED without evidence of escalation).
    return "STANDARD"


def _find_matching_prior(
    title: str,
    prior_factors: list[RiskFactorProfile],
) -> RiskFactorProfile | None:
    """Find the best-matching prior factor by title similarity.

    Returns None if no match exceeds the threshold.
    """
    best_match: RiskFactorProfile | None = None
    best_ratio = 0.0

    title_lower = title.lower()
    for pf in prior_factors:
        ratio = SequenceMatcher(None, title_lower, pf.title.lower()).ratio()
        if ratio > best_ratio and ratio >= _TITLE_MATCH_THRESHOLD:
            best_ratio = ratio
            best_match = pf

    return best_match


__all__ = ["classify_risk_factors"]
