"""Narrative builder functions for underwriting thesis, risk, and claims.

Relocated from render/sections/sect1_helpers.py to benchmark/ to establish
proper stage boundaries: analytical narrative construction belongs in
benchmark/ (analytical), not render/ (presentation).

These functions transform thin data labels into rich, analyst-quality
narrative paragraphs. Each builder takes AnalysisState and returns
narrative text strings.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.executive_summary import InherentRiskBaseline
from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import format_currency

# ---------------------------------------------------------------------------
# Market cap decile for ~4,000 account D&O universe
# ---------------------------------------------------------------------------

# Approximate decile boundaries based on US public company distribution
# for a typical ~4,000 account D&O book (mid-to-large caps).
_DECILE_BOUNDARIES: list[tuple[float, str]] = [
    (100_000_000_000, "Decile 1 (largest ~400 accounts)"),
    (40_000_000_000, "Decile 2"),
    (20_000_000_000, "Decile 3"),
    (10_000_000_000, "Decile 4"),
    (5_000_000_000, "Decile 5"),
    (3_000_000_000, "Decile 6"),
    (1_500_000_000, "Decile 7"),
    (750_000_000, "Decile 8"),
    (300_000_000, "Decile 9"),
    (0, "Decile 10 (smallest accounts)"),
]


def market_cap_decile(market_cap: float | None) -> tuple[int, str]:
    """Return (decile_number, description) for a market cap value.

    Decile 1 = largest companies (~$100B+), Decile 10 = smallest.
    Based on approximate distribution of ~4,000 D&O accounts.
    """
    if market_cap is None or market_cap <= 0:
        return (0, "N/A")
    for idx, (threshold, desc) in enumerate(_DECILE_BOUNDARIES):
        if market_cap >= threshold:
            return (idx + 1, desc)
    return (10, "Decile 10 (smallest accounts)")


# ---------------------------------------------------------------------------
# Thesis narrative builder
# ---------------------------------------------------------------------------


def build_thesis_narrative(state: AnalysisState) -> str:
    """Build a rich 4-6 sentence underwriting thesis from state data."""
    parts: list[str] = []

    # Company identification
    name = "The company"
    mcap_str = ""
    tier_str = ""
    sector = ""
    if state.executive_summary and state.executive_summary.snapshot:
        snap = state.executive_summary.snapshot
        name = snap.company_name or name
        if snap.market_cap:
            mcap_str = format_currency(snap.market_cap.value, compact=True)
            decile, _ = market_cap_decile(snap.market_cap.value)
            mcap_str = f"{mcap_str} (Decile {decile} of 10)"
    if state.executive_summary and state.executive_summary.inherent_risk:
        risk = state.executive_summary.inherent_risk
        sector = risk.sector_name or ""
        tier_label = risk.market_cap_tier or ""
        if tier_label:
            tier_str = f"{tier_label.lower()}-cap"

    # Opening: who they are
    opening = name
    if mcap_str and sector:
        opening = (
            f"{name} is a {mcap_str} {tier_str} "
            f"{sector.lower()} company"
        )
    elif mcap_str:
        opening = f"{name} ({mcap_str})"

    # Scoring context
    quality = state.scoring.quality_score if state.scoring else None
    tier_name = (
        state.scoring.tier.tier.value
        if (state.scoring and state.scoring.tier)
        else None
    )
    action = (
        state.scoring.tier.action
        if (state.scoring and state.scoring.tier)
        else None
    )

    # Red flags
    triggered_flags: list[Any] = []
    if state.scoring and state.scoring.red_flags:
        triggered_flags = [
            rf for rf in state.scoring.red_flags if rf.triggered
        ]

    # Top factor drivers
    top_factors: list[Any] = []
    if state.scoring and state.scoring.factor_scores:
        scored: list[Any] = sorted(
            state.scoring.factor_scores,
            key=_factor_deduction,
            reverse=True,
        )
        for fs in scored:
            if fs.points_deducted > 0:
                top_factors.append(fs)

    # Financials for context
    z_score = safe_distress(state, "altman_z_score")
    de_ratio = safe_leverage_ratio(state, "debt_to_equity")

    # Build the narrative
    if triggered_flags and quality is not None:
        # Case: red flags dominate
        flag_names = [rf.flag_name for rf in triggered_flags[:2]]
        flags_text = " and ".join(flag_names)
        ceiling = min(
            (
                rf.ceiling_applied
                for rf in triggered_flags
                if rf.ceiling_applied
            ),
            default=None,
        )
        parts.append(
            f"{opening} that would normally present as a stronger "
            f"underwriting account were it not for critical red "
            f"flags: {flags_text}."
        )
        if ceiling is not None and tier_name:
            parts.append(
                f"These findings impose a hard quality score "
                f"ceiling of {ceiling}, placing the account in "
                f"{tier_name} tier ({quality:.0f}/100) regardless "
                f"of other favorable factors."
            )
    elif quality is not None and tier_name:
        parts.append(
            f"{opening} scoring {quality:.0f}/100 ({tier_name} tier)."
        )
    else:
        parts.append(f"{opening}.")

    # Financial strength or weakness context
    if (
        z_score
        and z_score > 2.99
        and de_ratio is not None
        and de_ratio < 1.0
    ):
        parts.append(
            f"The balance sheet is strong (D/E {de_ratio:.2f}, "
            f"Z-Score {z_score:.2f}), eliminating financial "
            f"distress as a D&O claim catalyst."
        )
    elif z_score and z_score < 1.81:
        parts.append(
            f"Financial distress indicators are concerning "
            f"(Z-Score {z_score:.2f}), elevating going-concern "
            f"and creditor-related D&O exposure."
        )

    # Top risk driver detail
    if top_factors:
        top: Any = top_factors[0]
        evidence_text: str = (
            top.evidence[0] if top.evidence else "unspecified"
        )
        parts.append(
            f"The primary risk driver is {top.factor_name}, "
            f"driving elevated risk in this area. {evidence_text}."
        )

    # Inherent risk and positioning
    if state.executive_summary and state.executive_summary.inherent_risk:
        risk = state.executive_summary.inherent_risk
        cp = state.scoring.claim_probability if state.scoring else None
        if cp:
            ratio = (
                risk.company_adjusted_rate_pct
                / risk.sector_base_rate_pct
                if risk.sector_base_rate_pct > 0
                else 1.0
            )
            parts.append(
                f"At a {cp.range_low_pct:.0f}-"
                f"{cp.range_high_pct:.0f}% claim probability "
                f"({risk.company_adjusted_rate_pct:.1f}% adjusted "
                f"rate, {ratio:.1f}x the {sector} sector baseline "
                f"of {risk.sector_base_rate_pct:.1f}%), this "
                f"account requires "
                + (_position_guidance(action) or "careful positioning")
                + "."
            )

    return " ".join(parts) if parts else "Analysis incomplete."


# ---------------------------------------------------------------------------
# Inherent risk narrative
# ---------------------------------------------------------------------------


def build_risk_narrative(
    risk: InherentRiskBaseline,
    state: AnalysisState,
) -> str:
    """Build a 2-3 sentence narrative explaining the risk baseline."""
    parts: list[str] = []

    tier_name = (
        state.scoring.tier.tier.value
        if (state.scoring and state.scoring.tier)
        else "this"
    )
    base = risk.sector_base_rate_pct
    adj = risk.company_adjusted_rate_pct
    multiplier = adj / base if base > 0 else 1.0

    parts.append(
        f"At a {adj:.1f}% adjusted claim rate, the company faces "
        f"{multiplier:.1f}x its sector baseline of {base:.1f}% "
        f"for {risk.sector_name} companies."
    )

    # Explain the decomposition
    parts.append(
        f"This rate reflects the {risk.market_cap_tier} cap "
        f"multiplier ({risk.market_cap_multiplier:.2f}x) combined "
        f"with the quality score multiplier "
        f"({risk.score_multiplier:.2f}x from {tier_name} tier "
        f"classification)."
    )

    # Scenario if score improves
    if risk.score_multiplier > 1.5:
        hypothetical = base * risk.market_cap_multiplier * 1.0
        parts.append(
            f"If the score improved to WRITE tier, the rate would "
            f"drop to approximately {hypothetical:.1f}%."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Claim probability narrative
# ---------------------------------------------------------------------------


def build_claim_narrative(state: AnalysisState) -> str:
    """Build claim probability context narrative."""
    cp = state.scoring.claim_probability if state.scoring else None
    if not cp:
        return ""
    risk = (
        state.executive_summary.inherent_risk
        if state.executive_summary
        else None
    )
    base_rate = risk.sector_base_rate_pct if risk else 3.0
    sector = risk.sector_name if risk else "the sector"
    multiplier = (
        (cp.range_low_pct + cp.range_high_pct) / 2 / base_rate
        if base_rate > 0
        else 1.0
    )
    tier_name = (
        state.scoring.tier.tier.value
        if (state.scoring and state.scoring.tier)
        else "this"
    )

    adj_narrative = (
        cp.adjustment_narrative if cp.adjustment_narrative else ""
    )
    return (
        f"The {cp.range_low_pct:.0f}-{cp.range_high_pct:.0f}% "
        f"probability band represents approximately "
        f"{multiplier:.0f}x the {sector} sector base rate of "
        f"{base_rate:.1f}%. Accounts in {tier_name} tier "
        f"historically produce claims at elevated frequency. "
        + adj_narrative
    )


# ---------------------------------------------------------------------------
# Internal data extraction helpers
# ---------------------------------------------------------------------------


def _factor_deduction(fs: Any) -> float:
    """Extract points_deducted for sorting (avoids lambda type issue)."""
    result: float = fs.points_deducted
    return result


def safe_distress(
    state: AnalysisState, model: str
) -> float | None:
    """Safely extract a distress model score."""
    ext: Any = state.extracted
    if ext is None:
        return None
    fin: Any = ext.financials
    if fin is None:
        return None
    di: Any = fin.distress
    if di is None:
        return None
    result: Any = getattr(di, model, None)
    if result is None:
        return None
    # DistressResult has .score
    score: Any = getattr(result, "score", None)
    if score is not None:
        return float(score)
    return None


def safe_leverage_ratio(
    state: AnalysisState, ratio_name: str
) -> float | None:
    """Safely extract a leverage ratio from extracted financials."""
    ext: Any = state.extracted
    if ext is None:
        return None
    fin: Any = ext.financials
    if fin is None:
        return None
    lev: Any = fin.leverage
    if lev is None:
        return None
    val_dict: dict[str, Any] = dict(lev.value) if lev.value else {}
    raw: Any = val_dict.get(ratio_name)
    if raw is not None:
        return float(raw)
    return None


def _position_guidance(action: str | None) -> str | None:
    """Convert tier action to positioning language."""
    if not action:
        return None
    a = action.lower()
    if "excess" in a or "high" in a:
        return "high-excess positioning with elevated attachment"
    if "decline" in a:
        return (
            "declination or exceptionally restrictive terms"
        )
    if "primary" in a or "aggressively" in a:
        return "primary or low-excess participation"
    if "market" in a:
        return "standard market positioning"
    return action


__all__ = [
    "build_claim_narrative",
    "build_risk_narrative",
    "build_thesis_narrative",
    "market_cap_decile",
    "safe_distress",
    "safe_leverage_ratio",
]
