"""Answerers for Domain 4: Stock & Market Risk (MKT-01 through MKT-07)."""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.answerers._registry import register
from do_uw.stages.render.context_builders.answerers._helpers import (
    fmt_currency,
    fmt_pct,
    no_data,
    partial_answer,
    safe_float_extract,
    triggered_signals,
    yf_info,
)


@register("MKT-01")
def _answer_mkt_01(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Has the stock had any drops >15% in the last 12 months?"""
    drops = ctx.get("enhanced_drop_events", [])
    yfi = yf_info(ctx)

    high_52w = safe_float_extract(yfi.get("fiftyTwoWeekHigh"))
    low_52w = safe_float_extract(yfi.get("fiftyTwoWeekLow"))

    evidence = []
    big_drops = [
        d for d in drops
        if isinstance(d, dict) and abs(safe_float_extract(d.get("pct_change", 0), 0) or 0) >= 15
    ]

    if high_52w and low_52w and high_52w > 0:
        drawdown = ((high_52w - low_52w) / high_52w) * 100
        evidence.append(f"52-week range: ${low_52w:.2f} - ${high_52w:.2f}")
        evidence.append(f"Max drawdown: {drawdown:.1f}%")

    for d in big_drops[:3]:
        evidence.append(f"Drop {d.get('date', '')}: {d.get('pct_change', '')}%")

    if not evidence:
        return no_data()

    if big_drops:
        verdict = "DOWNGRADE"
        answer = f"{len(big_drops)} stock drop(s) exceeding 15% in the last 12 months."
    elif high_52w and low_52w and high_52w > 0:
        drawdown = ((high_52w - low_52w) / high_52w) * 100
        if drawdown > 30:
            verdict = "DOWNGRADE"
            answer = f"52-week drawdown of {drawdown:.1f}% -- elevated volatility."
        elif drawdown < 15:
            verdict = "UPGRADE"
            answer = f"Low volatility -- 52-week drawdown only {drawdown:.1f}%."
        else:
            verdict = "NEUTRAL"
            answer = f"Moderate volatility -- {drawdown:.1f}% 52-week drawdown."
    else:
        verdict = "NEUTRAL"
        answer = "Stock data available but no significant drops identified."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("MKT-02")
def _answer_mkt_02(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Short interest and days-to-cover."""
    yfi = yf_info(ctx)

    si_pct = safe_float_extract(yfi.get("shortPercentOfFloat"))
    si_ratio = safe_float_extract(yfi.get("shortRatio"))

    if si_pct is None:
        return no_data()

    # yfinance returns decimal (0.0085 = 0.85%)
    si_display = si_pct * 100 if si_pct < 1 else si_pct

    evidence = [f"Short interest: {si_display:.2f}% of float"]
    if si_ratio is not None:
        evidence.append(f"Days to cover: {si_ratio:.1f}")

    if si_display > 8:
        verdict = "DOWNGRADE"
        answer = f"Elevated short interest at {si_display:.1f}% of float -- above 8% threshold."
    elif si_display < 3:
        verdict = "UPGRADE"
        answer = f"Low short interest at {si_display:.2f}% of float."
    else:
        verdict = "NEUTRAL"
        answer = f"Moderate short interest at {si_display:.1f}% of float."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("MKT-03")
def _answer_mkt_03(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """DDL exposure -- settlement severity curve position."""
    yfi = yf_info(ctx)
    mc_raw = safe_float_extract(yfi.get("marketCap"))
    settlement = ctx.get("settlement", {})

    if not mc_raw:
        return no_data()

    evidence = [f"Market cap: {fmt_currency(mc_raw)}"]

    # Settlement benchmarks from risk card
    if isinstance(settlement, dict):
        p50 = settlement.get("p50_settlement") or settlement.get("median_settlement")
        if p50:
            evidence.append(f"P50 settlement benchmark: {p50}")

    # Severity curve by market cap tier
    if mc_raw >= 50e9:
        tier_note = "mega-cap zone -- P90 settlements regularly exceed $100M"
        verdict = "DOWNGRADE"
    elif mc_raw >= 10e9:
        tier_note = "large-cap -- settlements scale significantly, P90 can exceed $100M"
        verdict = "DOWNGRADE"
    elif mc_raw >= 2e9:
        tier_note = "mid-cap -- settlements typically $5-50M"
        verdict = "NEUTRAL"
    elif mc_raw >= 500e6:
        tier_note = "small-cap -- lower absolute exposure, higher volatility risk"
        verdict = "NEUTRAL"
    else:
        tier_note = "micro/nano-cap -- settlement severity typically <$10M"
        verdict = "UPGRADE"

    answer = f"Market cap {fmt_currency(mc_raw)} -- {tier_note}."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("MKT-04")
def _answer_mkt_04(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Insider buying/selling patterns."""
    evidence = []

    mkt_data = {}
    if state.acquired_data:
        mkt_data = getattr(state.acquired_data, "market_data", None) or {}
    insider_txns = mkt_data.get("insider_transactions") if isinstance(mkt_data, dict) else None

    insider_signals = triggered_signals(ctx, prefix="insider")
    for s in insider_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    if isinstance(insider_txns, dict):
        buys = insider_txns.get("buys", 0)
        sells = insider_txns.get("sells", 0)
        evidence.append(f"Insider buys: {buys}, sells: {sells}")
    elif isinstance(insider_txns, list) and insider_txns:
        evidence.append(f"Insider transactions: {len(insider_txns)} records")

    if not evidence:
        return no_data()

    if insider_signals:
        verdict = "DOWNGRADE"
        answer = f"Insider trading signals triggered ({len(insider_signals)} signal(s)) -- review Form 4 pattern."
    else:
        verdict = "NEUTRAL"
        answer = "Insider transaction data available -- no anomalous patterns flagged."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("MKT-05")
def _answer_mkt_05(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Major institutional holders."""
    mkt_data = {}
    if state.acquired_data:
        mkt_data = getattr(state.acquired_data, "market_data", None) or {}
    inst_holders = mkt_data.get("institutional_holders") if isinstance(mkt_data, dict) else None

    evidence = []
    if isinstance(inst_holders, list) and inst_holders:
        for h in inst_holders[:5]:
            if isinstance(h, dict):
                name = h.get("Holder", h.get("holder", ""))
                pct = h.get("pctHeld", h.get("% Out", ""))
                if name:
                    evidence.append(f"{name}: {pct}")
        evidence.append(f"Total institutional holders reported: {len(inst_holders)}")

    yfi = yf_info(ctx)
    inst_pct = safe_float_extract(yfi.get("heldPercentInstitutions"))
    if inst_pct is not None:
        evidence.append(f"Institutional ownership: {inst_pct * 100:.1f}%")

    if not evidence:
        return no_data()

    verdict = "NEUTRAL"
    if inst_pct is not None:
        answer = f"Institutional ownership: {inst_pct * 100:.1f}%."
        if inst_holders and isinstance(inst_holders, list) and inst_holders:
            top = inst_holders[0]
            if isinstance(top, dict):
                answer += f" Top holder: {top.get('Holder', top.get('holder', 'N/A'))}."
    else:
        answer = f"{len(inst_holders)} institutional holders reported."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }


@register("MKT-06")
def _answer_mkt_06(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Stock price near 52-week highs or lows."""
    yfi = yf_info(ctx)

    high_52w = safe_float_extract(yfi.get("fiftyTwoWeekHigh"))
    low_52w = safe_float_extract(yfi.get("fiftyTwoWeekLow"))
    current = safe_float_extract(yfi.get("currentPrice") or yfi.get("regularMarketPrice"))

    if not (high_52w and low_52w and current):
        return no_data()

    evidence = [
        f"Current price: ${current:.2f}",
        f"52-week high: ${high_52w:.2f}",
        f"52-week low: ${low_52w:.2f}",
    ]

    range_width = high_52w - low_52w
    if range_width > 0:
        pct_of_range = ((current - low_52w) / range_width) * 100
        evidence.append(f"Position in range: {pct_of_range:.0f}%")
    else:
        pct_of_range = 50.0

    pct_from_high = ((high_52w - current) / high_52w) * 100 if high_52w > 0 else 0
    pct_from_low = ((current - low_52w) / low_52w) * 100 if low_52w > 0 else 0

    if pct_from_high <= 10:
        verdict = "UPGRADE"
        answer = f"Near 52-week high -- {pct_from_high:.1f}% below ${high_52w:.2f}. Strong stock performance."
    elif pct_from_low <= 10:
        verdict = "DOWNGRADE"
        answer = f"Near 52-week low -- only {pct_from_low:.1f}% above ${low_52w:.2f}. Potential damages class growing."
    else:
        verdict = "NEUTRAL"
        answer = f"Mid-range at ${current:.2f} ({pct_of_range:.0f}% of 52-week range)."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "HIGH",
        "data_found": True,
    }


@register("MKT-07")
def _answer_mkt_07(
    q: dict[str, Any], state: AnalysisState, ctx: dict[str, Any]
) -> dict[str, Any]:
    """Recent equity or debt issuances."""
    evidence = []

    offering_signals = [
        s for s in triggered_signals(ctx)
        if any(
            k in str(s.get("signal_id", "")).lower()
            for k in ("offering", "s-3", "424b", "shelf", "secondary")
        )
    ]

    for s in offering_signals[:3]:
        evidence.append(
            f"Signal: {s.get('signal_id', '')} -- {str(s.get('evidence', ''))[:100]}"
        )

    # Check extracted SEC filings for S-3/424B
    if state.extracted:
        sec_filings = getattr(state.extracted, "sec_filings", None)
        if isinstance(sec_filings, list):
            offering_filings = [
                f for f in sec_filings
                if isinstance(f, dict)
                and any(t in str(f.get("form_type", "")).upper() for t in ("S-3", "424B", "S-1"))
            ]
            if offering_filings:
                evidence.append(f"Offering filings found: {len(offering_filings)}")

    if not evidence:
        return {
            "answer": "No recent equity or debt offerings detected in pipeline data.",
            "evidence": ["No offering signals triggered"],
            "verdict": "UPGRADE",
            "confidence": "MEDIUM",
            "data_found": True,
        }

    verdict = "DOWNGRADE"
    answer = f"Recent offering activity detected ({len(offering_signals)} signal(s)) -- Section 11 exposure."

    return {
        "answer": answer,
        "evidence": evidence,
        "verdict": verdict,
        "confidence": "MEDIUM",
        "data_found": True,
    }
