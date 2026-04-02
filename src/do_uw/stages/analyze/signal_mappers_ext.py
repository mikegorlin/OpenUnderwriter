"""Extended data mapper helpers for signal_mappers.py.

Split from signal_mappers.py to stay under 500-line limit.
Contains text signal helpers used by BIZ.* checks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from do_uw.models.state import ExtractedData


def _truncate_context(ctx: str, limit: int = 300) -> str:
    """Truncate context at word boundary, adding ellipsis only if truncated."""
    if len(ctx) <= limit:
        return ctx
    # Find last space within limit
    truncated = ctx[:limit]
    last_space = truncated.rfind(" ")
    if last_space > limit * 0.8:  # If space found in reasonable position
        truncated = ctx[:last_space]
    return truncated + "…"


def _text_signal_value(extracted: ExtractedData, signal_name: str) -> str | None:
    """Get display value from a text signal, or None if signal wasn't extracted.

    Returns a value for BOTH present and absent signals -- "not mentioned"
    is valid evaluation data (means the 10-K doesn't discuss this topic).
    Returns None only if the signal wasn't extracted at all.
    """
    sig = extracted.text_signals.get(signal_name)
    if not isinstance(sig, dict):
        return None
    if not sig.get("present"):
        return "Not mentioned in 10-K filing"
    count = sig.get("mention_count", 0)
    ctx = sig.get("context", "")
    if ctx:
        truncated = _truncate_context(ctx)
        return f"{count} mention(s): {truncated}"
    return f"{count} mention(s) in 10-K"


def _text_signal_count(extracted: ExtractedData, signal_name: str) -> int | None:
    """Get mention count from a text signal as a number.

    Returns 0 for signals that are present but not mentioned.
    Returns the mention_count for present signals.
    Returns None if the signal wasn't extracted at all.
    Used by EVALUATIVE_CHECK checks that need numeric comparison.
    """
    sig = extracted.text_signals.get(signal_name)
    if not isinstance(sig, dict):
        return None
    if not sig.get("present"):
        return 0
    return sig.get("mention_count", 0)


# Field name -> text signal name mapping for BIZ.* checks
BIZ_TEXT_SIG_FIELDS: dict[str, str] = {
    "barriers_to_entry": "barriers_to_entry",
    "competitive_moat": "competitive_moat",
    "industry_headwinds": "industry_headwinds",
    "technology_dependency": "technology_dependency",
    "regulatory_dependency": "regulatory_dependency",
    "capital_dependency": "capital_dependency",
    "macro_sensitivity": "macro_sensitivity",
    "distribution_channels": "distribution_channels",
    "contract_terms": "contract_terms",
    "cost_structure_analysis": "cost_structure_analysis",
    "operating_leverage": "cost_structure_analysis",
    "model_regulatory_dependency": "model_regulatory_dependency",
    "capital_intensity_ratio": "capital_dependency",
    "ai_risk_exposure": "ai_risk_exposure",
    "cybersecurity_posture": "cybersecurity_posture",
    "cyber_business_risk": "cyber_business_risk",
}


def compute_guidance_fields(
    earnings_guidance: Any,
    safe_sourced_fn: Any,
) -> dict[str, Any]:
    """Compute guidance-related fields from EarningsGuidanceAnalysis.

    Shared by both _map_financial_fields (FIN.GUIDE) and _map_market_fields
    (STOCK.* checks) to avoid code duplication across mappers.

    Args:
        earnings_guidance: EarningsGuidanceAnalysis model instance.
        safe_sourced_fn: The _safe_sourced unwrapper function.

    Returns:
        Dict of guidance field names to computed values.
    """
    eg = earnings_guidance
    result: dict[str, Any] = {}

    # Gate guidance-specific fields on whether company provides forward guidance.
    # FIN.GUIDE.current, track_record, philosophy are only meaningful for guiding companies.
    # FIN.GUIDE.earnings_reaction and analyst_consensus remain active for ALL companies.
    if not getattr(eg, "provides_forward_guidance", False):
        result["guidance_provided"] = "No"
        result["guidance_philosophy"] = "N/A"
        result["beat_rate"] = None  # Not company guidance -- don't evaluate
        # Preserve analyst beat/miss data under separate key for display
        result["analyst_beat_rate"] = safe_sourced_fn(eg.beat_rate)
    else:
        result["beat_rate"] = safe_sourced_fn(eg.beat_rate)
        result["guidance_provided"] = (
            "Yes" if eg.quarters else ("Withdrawn" if eg.guidance_withdrawals > 0 else None)
        )
        result["guidance_philosophy"] = eg.philosophy if eg.philosophy else None

    # Post-earnings drift: average stock reaction across recent quarters.
    # Always computed -- D&O relevant regardless of guidance status.
    reactions = [
        safe_sourced_fn(q.stock_reaction_pct)
        for q in eg.quarters
        if safe_sourced_fn(q.stock_reaction_pct) is not None
    ]
    result["post_earnings_drift"] = (
        round(sum(reactions) / len(reactions), 2) if reactions else None
    )

    # Consensus divergence: difference between guidance and actuals.
    # Always computed -- measures analyst estimate accuracy.
    divergences: list[float] = []
    for q in eg.quarters:
        g_hi = safe_sourced_fn(q.consensus_eps_high)
        g_lo = safe_sourced_fn(q.consensus_eps_low)
        actual = safe_sourced_fn(q.actual_eps)
        if g_hi is not None and g_lo is not None and actual is not None:
            midpoint = (g_hi + g_lo) / 2
            if midpoint != 0:
                divergences.append(round((actual - midpoint) / abs(midpoint) * 100, 2))
    result["consensus_divergence"] = (
        round(sum(divergences) / len(divergences), 2) if divergences else None
    )

    return result


# ---------------------------------------------------------------------------
# Boilerplate / false-positive SCA filters
# ---------------------------------------------------------------------------

# Patterns that indicate boilerplate 10-K language, not actual SCAs
_BOILERPLATE_PATTERNS = (
    "NORMAL COURSE OF BUSINESS",
    "GENERAL LITIGATION AND CLAIMS",
    "ROUTINE LITIGATION",
    "ORDINARY COURSE",
    "SUBJECT TO VARIOUS LEGAL PROCEEDINGS",
    "FROM TIME TO TIME",
    "PARTY TO LEGAL MATTERS",
    "LEGAL MATTERS ARISING",
    "INVOLVED IN LITIGATION",
    "SUBJECT TO CLAIMS",
    "LEGAL PROCEEDINGS AND CLAIMS",
    "INVOLVED IN CERTAIN LEGAL",
    "SUBJECT TO VARIOUS LEGAL",
    "PARTY TO CERTAIN LEGAL",
)


def _is_boilerplate_litigation(case_name_upper: str) -> bool:
    """True if case name matches boilerplate 10-K language patterns."""
    return any(pat in case_name_upper for pat in _BOILERPLATE_PATTERNS)


__all__ = [
    "BIZ_TEXT_SIG_FIELDS",
    "_is_boilerplate_litigation",
    "_text_signal_count",
    "_text_signal_value",
    "compute_guidance_fields",
]
