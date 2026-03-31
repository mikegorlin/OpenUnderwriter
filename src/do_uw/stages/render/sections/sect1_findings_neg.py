"""Negative finding narrative sub-builders for executive summary.

Each function produces a list of sentences for one finding type,
backed by real data from the analysis state. Every sentence must
contain company-specific data -- dollar amounts, percentages, dates,
names. No boilerplate. No generic D&O primer text.

Phase 119.1-01: Rewrote all functions to use 3+ data points each.
               Deleted neg_generic -- replaced with neg_from_finding.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.executive_summary import KeyFinding
from do_uw.models.state import AnalysisState


def _fmt_mktcap(mc: float) -> str:
    """Format market cap in billions to compact display ($3.6T or $45.2B)."""
    if mc >= 1000:
        return f"${mc / 1000:.1f}T"
    return f"${mc:.1f}B"
from do_uw.stages.render.sections.sect1_findings_data import (
    beneish_m_score,
    ceo_tenure_years,
    credibility_score,
    ddl_estimate,
    employee_count,
    executive_departure_count,
    factor_score,
    going_concern,
    goodwill_ratio,
    guidance_miss_count,
    is_line_item,
    litigation_counts,
    jurisdiction_count,
    market_cap_billions,
    piotroski_score,
    revenue_trend,
    scoring_tier,
    short_interest_pct,
    stock_decline_pct,
    stock_decline_prices,
    subsidiary_count,
    triggered_signal_ids,
)
from do_uw.stages.render.sections.sect1_helpers import (
    safe_distress,
    safe_governance_field,
    safe_leverage_ratio,
    safe_short_interest,
)


# ---------------------------------------------------------------------------
# Stock decline severity calibration
# ---------------------------------------------------------------------------

def _stock_decline_descriptor(pct: float) -> str:
    """Return severity descriptor calibrated to actual decline magnitude."""
    if pct >= 70:
        return "catastrophic collapse"
    if pct >= 50:
        return "severe decline"
    if pct >= 30:
        return "substantial decline"
    if pct >= 15:
        return "significant decline"
    if pct >= 10:
        return f"{pct:.0f}% decline"
    return f"{pct:.0f}% dip"


def _ddl_context(ddl_b: float) -> str:
    """Contextualize DDL magnitude."""
    if ddl_b >= 10:
        return "among the largest potential DDL exposures in the market"
    if ddl_b >= 1:
        return "well above institutional lead plaintiff thresholds"
    return "sufficient to attract plaintiff attention"


# ---------------------------------------------------------------------------
# Negative finding narrative builders
# ---------------------------------------------------------------------------


def neg_prior_litigation(state: AnalysisState, name: str) -> list[str]:
    """Structural complexity and litigation history."""
    subs = subsidiary_count(state)
    jurs = jurisdiction_count(state)
    gw = goodwill_ratio(state)
    lit = litigation_counts(state)

    sentences: list[str] = []
    parts: list[str] = []
    if subs:
        base = f"{name} has {subs} subsidiaries"
        if jurs:
            base += f" across {jurs} jurisdictions"
        base += f", increasing multi-jurisdictional litigation exposure"
        parts.append(base)
    if gw is not None and gw > 10:
        parts.append(
            f"Goodwill at {gw:.1f}% of total assets reflects "
            "an acquisition-driven strategy where integration "
            "risk and impairment charges are common SCA triggers"
        )
    if parts:
        sentences.append(". ".join(parts) + ".")

    lit_parts: list[str] = []
    total_lit = 0
    if lit["derivative"] > 0:
        s = "s" if lit["derivative"] > 1 else ""
        lit_parts.append(f"{lit['derivative']} derivative suit{s}")
        total_lit += lit["derivative"]
    if lit["sca"] > 0:
        s = "s" if lit["sca"] > 1 else ""
        lit_parts.append(f"{lit['sca']} securities class action{s}")
        total_lit += lit["sca"]
    if lit["enforcement"] > 0:
        s = "s" if lit["enforcement"] > 1 else ""
        lit_parts.append(
            f"{lit['enforcement']} SEC enforcement matter{s}"
        )
        total_lit += lit["enforcement"]
    if lit_parts:
        sentences.append(
            f"The current docket includes {', '.join(lit_parts)}."
        )

    # Factor-specific closing instead of generic text
    if gw is not None and gw > 15:
        sentences.append(
            f"With goodwill at {gw:.1f}% of total assets and "
            f"{total_lit} active matter{'s' if total_lit != 1 else ''}, "
            f"{name}'s exposure profile combines impairment risk "
            "with demonstrated plaintiff interest in this issuer."
        )
    elif total_lit > 0:
        mc = market_cap_billions(state)
        mc_str = f" at {_fmt_mktcap(mc)} market cap" if mc else ""
        sentences.append(
            f"With {total_lit} pending matter{'s' if total_lit != 1 else ''}"
            f"{mc_str}, {name} has an active litigation profile "
            "that will factor into loss-pick and pricing."
        )
    return sentences or [
        f"{name} has prior litigation history contributing to "
        "D&O risk assessment."
    ]


def neg_enforcement(state: AnalysisState, name: str) -> list[str]:
    """SEC enforcement action."""
    lit = litigation_counts(state)
    sentences = [
        f"{name} is subject to an active SEC enforcement action.",
    ]
    if lit["sca"] > 0 or lit["derivative"] > 0:
        sentences.append(
            f"The enforcement action compounds existing litigation "
            f"({lit['sca']} SCA, {lit['derivative']} derivative "
            f"matters pending), creating multi-front D&O exposure "
            f"for {name}'s directors and officers."
        )
    mc = market_cap_billions(state)
    if mc:
        sentences.append(
            f"At {_fmt_mktcap(mc)} market cap, the enforcement action "
            "creates significant Side A exposure for individual "
            "directors and officers, as regulatory findings "
            "are routinely incorporated into follow-on private "
            "securities complaints to establish scienter."
        )
    return sentences


def neg_doj(name: str, origin: str) -> list[str]:
    """DOJ criminal investigation."""
    return [
        f"A federal DOJ investigation is pending against {name}"
        + (f": {origin}" if origin else "") + ".",
        "DOJ investigations create derivative liability risk and "
        "signal governance failures that plaintiffs' counsel will "
        "incorporate into any securities complaint, strengthening "
        "scienter allegations.",
        "Criminal proceedings also create Side A exposure for "
        "individual directors and officers.",
    ]


def neg_audit_issues(state: AnalysisState, name: str) -> list[str]:
    """Restatement or audit-related issues -- enriched with Beneish M-Score."""
    sentences: list[str] = [
        f"{name} has audit-related risk factors that warrant "
        "underwriting attention.",
    ]

    # Beneish M-Score value and component flags
    bm = beneish_m_score(state)
    if bm is not None:
        f3 = factor_score(state, "F3")
        triggered = triggered_signal_ids(f3) if f3 else []
        flag_names: list[str] = []
        for sid in triggered:
            sl = sid.lower()
            if "dsri" in sl:
                flag_names.append("DSRI")
            elif "sgai" in sl:
                flag_names.append("SGAI")
            elif "tata" in sl:
                flag_names.append("TATA")
            elif "gmi" in sl:
                flag_names.append("GMI")
            elif "aqi" in sl:
                flag_names.append("AQI")
            elif "depi" in sl:
                flag_names.append("DEPI")
            elif "sgai" in sl:
                flag_names.append("SGAI")
            elif "lvgi" in sl:
                flag_names.append("LVGI")
        n_flags = len(flag_names)
        flag_str = f" ({', '.join(flag_names)})" if flag_names else ""
        sentences.append(
            f"Beneish M-Score of {bm:.2f} with {n_flags}/8 component "
            f"flags triggered{flag_str}."
        )
    else:
        f3 = factor_score(state, "F3")
        if f3:
            pts = f3.get("points_deducted", 0)
            mx = f3.get("max_points", 12)
            triggered = triggered_signal_ids(f3)
            areas: list[str] = []
            for sid in triggered:
                sl = sid.lower()
                if "beneish" in sl or "earnings" in sl:
                    areas.append("earnings quality metrics")
                elif "rev_rec" in sl or "revenue" in sl:
                    areas.append("revenue recognition patterns")
                elif "internal_control" in sl:
                    areas.append("internal control indicators")
                elif "related_party" in sl:
                    areas.append("related-party transactions")
                elif "goodwill" in sl or "impairment" in sl:
                    areas.append("goodwill/intangible valuation")
            uniq = list(dict.fromkeys(areas))[:4]
            if uniq and pts > 0:
                sentences.append(
                    f"Risk signals flagged in {', '.join(uniq)} "
                    f"({pts:.0f}/{mx} points on the audit factor)."
                )

    gw = goodwill_ratio(state)
    if gw is not None and gw > 15:
        sentences.append(
            f"Goodwill represents {gw:.1f}% of total assets, "
            "requiring annual impairment testing under ASC 350. "
            "Impairment charges are a frequent SCA trigger."
        )

    # Factor-specific D&O closing tied to actual signals
    tier = scoring_tier(state)
    if bm is not None and bm > -1.78:
        sentences.append(
            f"At M-Score {bm:.2f} (above the -1.78 manipulation threshold), "
            f"financial disclosure reliability is questionable, "
            f"creating exposure to restatement-driven Section 10(b) claims."
        )
    elif tier and tier in ("WALK", "NO_TOUCH"):
        sentences.append(
            f"Combined with {name}'s {tier} tier classification, "
            "audit risk factors compound overall D&O exposure."
        )
    return sentences


def neg_guidance(state: AnalysisState, name: str) -> list[str]:
    """Earnings guidance misses -- enriched with credibility data."""
    cred = credibility_score(state)
    misses = guidance_miss_count(state)
    mc = market_cap_billions(state)

    sentences: list[str] = []

    # Data-specific opener instead of generic "concerning patterns"
    if misses is not None and cred is not None:
        sentences.append(
            f"{name} has missed earnings guidance in {misses} quarter"
            f"{'s' if misses != 1 else ''}, with management credibility "
            f"score at {cred:.0f}%."
        )
    elif misses is not None:
        sentences.append(
            f"{name} has missed earnings guidance in {misses} quarter"
            f"{'s' if misses != 1 else ''}."
        )
    elif cred is not None:
        sentences.append(
            f"{name}'s management credibility score stands at {cred:.0f}%, "
            "reflecting a pattern of guidance inaccuracy."
        )
    else:
        # Minimal fallback -- still uses factor data
        f5 = factor_score(state, "F5")
        pts = f5.get("points_deducted", 0) if f5 else 0
        sentences.append(
            f"{name}'s earnings guidance track record has triggered "
            f"{pts:.0f} risk points on the guidance factor."
        )

    # Credibility interpretation
    if cred is not None and cred < 50:
        sentences.append(
            f"This sub-50% credibility score means {name}'s forward "
            "statements carry diminished investor trust, making future "
            "misses more likely to trigger SCA filings."
        )

    # DDL context with actual numbers
    if mc:
        ddl = ddl_estimate(state)
        if ddl:
            sentences.append(
                f"At {_fmt_mktcap(mc)} market cap with an estimated DDL "
                f"of ${ddl:.1f}B, guidance misses generate large "
                "absolute loss figures that attract institutional "
                "lead plaintiffs."
            )
        else:
            sentences.append(
                f"At {_fmt_mktcap(mc)} market cap, guidance misses generate "
                "large absolute DDL figures, amplifying settlement "
                "severity."
            )
    return sentences


def neg_stock_risk(
    state: AnalysisState, name: str, raw: str,
) -> list[str]:
    """Stock volatility or stock price decline -- severity-calibrated."""
    sentences: list[str] = []
    decline = stock_decline_pct(state)
    prices = stock_decline_prices(state)
    si = short_interest_pct(state)
    ddl = ddl_estimate(state)

    if decline is not None and "Decline" in raw:
        descriptor = _stock_decline_descriptor(decline)
        if prices:
            high, low, days = prices
            sentences.append(
                f"{name}'s stock has undergone a {descriptor} of "
                f"{decline:.1f}% from ${high:.2f} to ${low:.2f} "
                f"over {days} trading days."
            )
        else:
            sentences.append(
                f"{name}'s stock has undergone a {descriptor} of "
                f"{decline:.1f}%."
            )

        # DDL sentence
        if ddl is not None:
            ctx = _ddl_context(ddl)
            sentences.append(
                f"This creates an estimated Disclosure Dollar Loss "
                f"(DDL) of ${ddl:.1f}B, {ctx}."
            )
    elif decline is not None:
        # Volatility with actual decline data
        descriptor = _stock_decline_descriptor(decline)
        sentences.append(
            f"{name}'s stock exhibits elevated volatility with a "
            f"{descriptor} of {decline:.1f}% from its 52-week high."
        )
        if ddl is not None:
            sentences.append(
                f"The estimated DDL of ${ddl:.1f}B amplifies "
                "settlement severity for any corrective disclosure event."
            )
    else:
        # No decline data -- use what we have
        mc = market_cap_billions(state)
        sentences.append(
            f"{name}'s stock exhibits elevated volatility."
        )
        if mc:
            sentences.append(
                f"At {_fmt_mktcap(mc)} market cap, even routine disclosures "
                "can produce outsized price movements, creating the "
                "corrective disclosure pattern plaintiffs need for "
                "loss causation."
            )

    # Short interest if elevated
    if si is not None and si > 5:
        sentences.append(
            f"Short interest at {si:.1f}% of float indicates "
            "institutional bearish positioning that often precedes "
            "or amplifies SCA filings."
        )

    return sentences


def neg_governance(state: AnalysisState, name: str) -> list[str]:
    """Governance concerns -- enriched with CEO tenure, departures, board metrics."""
    from do_uw.stages.render.sections.sect1_findings_data import (
        board_size,
        classified_board,
    )

    sentences: list[str] = []
    independence = safe_governance_field(state, "independence_ratio")
    classified = classified_board(state)
    bsz = board_size(state)
    tenure = ceo_tenure_years(state)
    departures = executive_departure_count(state)
    tier = scoring_tier(state)

    # Opening with specific governance metrics
    concerns: list[str] = []
    if independence is not None and independence < 0.67:
        concerns.append(
            f"board independence at only {independence * 100:.0f}%"
        )
    if classified:
        concerns.append("a classified board structure")
    if bsz and bsz < 7:
        concerns.append(f"a {bsz}-member board (below typical 7+ for public companies)")

    if concerns:
        sentences.append(
            f"{name} has governance concerns including "
            + " and ".join(concerns) + "."
        )
    else:
        parts: list[str] = []
        if bsz:
            parts.append(f"{bsz}-member board")
        if independence is not None:
            parts.append(f"{independence * 100:.0f}% independence")
        if parts:
            sentences.append(
                f"{name}'s governance ({', '.join(parts)}) "
                "has triggered risk signals in the scoring model."
            )
        else:
            f9 = factor_score(state, "F9")
            pts = f9.get("points_deducted", 0) if f9 else 0
            sentences.append(
                f"{name}'s governance factor scored "
                f"{pts:.0f} risk points."
            )

    # CEO tenure context
    if tenure is not None:
        if tenure < 3:
            sentences.append(
                f"Recent CEO transition (tenure {tenure:.0f} years) "
                "creates leadership uncertainty during a period "
                "when management credibility is unproven."
            )
        elif tenure > 10 and tier and tier in ("WALK", "WATCH", "NO_TOUCH"):
            sentences.append(
                f"Despite {tenure:.0f}-year CEO tenure, governance "
                "structure shows weaknesses that undermine the "
                "stability benefit of long leadership tenure."
            )

    # Departure context
    if departures and departures > 0:
        sentences.append(
            f"Recent C-suite departures ({departures} in past 18 months) "
            "strengthen the 'rats leaving a sinking ship' inference "
            "that plaintiffs use to establish scienter."
        )

    # Factor-specific signals
    f9 = factor_score(state, "F9")
    if f9:
        triggered = triggered_signal_ids(f9)
        issues: list[str] = []
        for sid in triggered:
            sl = sid.lower()
            if "compensation" in sl:
                issues.append("executive compensation structure")
            elif "related" in sl:
                issues.append("related-party oversight")
            elif "insider" in sl:
                issues.append("insider trading patterns")
        if issues:
            sentences.append(
                f"Specific signals: {', '.join(issues)}."
            )

    # Specific closing tied to actual metrics, not generic Caremark primer
    if independence is not None and independence < 0.5 and tier and tier in ("WALK", "NO_TOUCH"):
        sentences.append(
            f"At {independence * 100:.0f}% independence with a {tier} "
            "tier classification, Caremark oversight failure claims "
            f"become highly viable against {name}'s board."
        )

    return sentences


def neg_short_interest(
    state: AnalysisState, name: str,
) -> list[str]:
    """Elevated short interest -- with specific positioning context."""
    si = safe_short_interest(state)
    mc = market_cap_billions(state)
    base = f"{name} has elevated short interest"
    if si:
        base += f" at {si:.1f}% of float"
    sentences = [base + "."]

    # Specific context based on short interest level
    if si and si > 15:
        sentences.append(
            f"At {si:.1f}%, short positioning is extreme -- "
            "this level typically indicates institutional conviction "
            "that material negative disclosures are forthcoming."
        )
    elif si and si > 10:
        sentences.append(
            f"Short interest above 10% ({si:.1f}%) signals "
            "significant institutional bearish conviction and "
            "increases the probability of short-seller reports "
            "that can catalyze SCA filings."
        )
    elif si:
        sentences.append(
            f"At {si:.1f}%, short positioning is elevated relative "
            "to typical levels, indicating some institutional "
            "bearish sentiment."
        )

    if mc and si:
        short_val = mc * si / 100
        sentences.append(
            f"With {_fmt_mktcap(mc)} market cap, the short position "
            f"represents ~${short_val:.1f}B in notional value."
        )
    return sentences


def neg_distress(state: AnalysisState, name: str) -> list[str]:
    """Financial distress -- enriched with Piotroski, current ratio, interest coverage, revenue trend."""
    z = safe_distress(state, "altman_z_score")
    de = safe_leverage_ratio(state, "debt_to_equity")
    gc = going_concern(state)
    pio = piotroski_score(state)
    current = is_line_item(state, "current_ratio")
    if current is None:
        from do_uw.stages.render.sections.sect1_findings_data import bs_line_item
        current = bs_line_item(state, "current_ratio")
    interest_cov = is_line_item(state, "interest_coverage_ratio")
    rev = revenue_trend(state)

    # Opening with all available distress metrics
    parts: list[str] = []
    if z is not None:
        if z < 1.1:
            parts.append(f"Altman Z-Score of {z:.2f} (distress zone)")
        elif z < 2.6:
            parts.append(f"Altman Z-Score of {z:.2f} (gray zone)")
        else:
            parts.append(f"Altman Z-Score of {z:.2f}")
    if de is not None:
        parts.append(f"D/E of {de:.2f}")
    if current is not None:
        parts.append(f"current ratio of {current:.1f}x")
    if interest_cov is not None:
        parts.append(f"interest coverage of {interest_cov:.1f}x")

    base = f"{name} shows financial distress indicators"
    if parts:
        base += f" ({', '.join(parts)})"
    sentences = [base + "."]

    # Piotroski context
    if pio is not None and pio <= 3:
        sentences.append(
            f"Piotroski F-Score of {pio}/9 confirms fundamental "
            "weakness across profitability, leverage, and operating "
            "efficiency dimensions."
        )
    elif pio is not None:
        sentences.append(f"Piotroski F-Score is {pio}/9.")

    # Revenue trend
    if rev == "declining":
        sentences.append(
            "Revenue trend is declining, compounding the distress profile "
            "and raising concerns about management's ability to reverse "
            "deterioration."
        )

    # Going concern
    if gc:
        sentences.append(
            "A going-concern qualification triggers acute D&O "
            "exposure including creditor derivative suits and Zone "
            "of Insolvency fiduciary duty expansion."
        )
    else:
        # Specific claim theory tied to actual indicators instead of generic
        if z is not None and z < 1.1:
            sentences.append(
                f"An Altman Z of {z:.2f} places {name} in the "
                "distress zone (bankruptcy probability >80%), creating "
                "creditor-related D&O exposure as fiduciary duties "
                "shift toward creditor interests."
            )
        elif interest_cov is not None and interest_cov < 2:
            sentences.append(
                f"Interest coverage of {interest_cov:.1f}x indicates "
                f"{name} may face covenant pressure, shifting fiduciary "
                "duty analysis toward creditor interests."
            )

    return sentences


def neg_ipo_ma(state: AnalysisState, name: str) -> list[str]:
    """IPO, SPAC, or M&A related risk."""
    sentences = [f"{name} has transaction-related risk factors."]
    gw = goodwill_ratio(state)
    if gw is not None and gw > 10:
        sentences.append(
            f"Goodwill at {gw:.1f}% of total assets reflects "
            "acquisition activity. Failed acquisitions are among "
            "the most common SCA triggers."
        )
    mc = market_cap_billions(state)
    if mc:
        sentences.append(
            f"At {_fmt_mktcap(mc)} market cap, transaction claims carry "
            "both Section 10(b) exposure (misleading disclosures) "
            "and Section 14(a) exposure (deficient proxy statements)."
        )
    else:
        sentences.append(
            "Transaction claims carry both Section 10(b) exposure "
            "(misleading disclosures) and Section 14(a) exposure "
            "(deficient proxy statements)."
        )
    return sentences


def neg_from_finding(
    state: AnalysisState, name: str, finding: KeyFinding,
) -> list[str]:
    """Data-driven fallback for findings that don't match named patterns.

    Instead of generic boilerplate, extracts signal data from the
    finding's origin/narrative to build company-specific text.
    """
    raw = finding.evidence_narrative
    origin = finding.section_origin or ""
    mc = market_cap_billions(state)
    tier = scoring_tier(state)

    sentences: list[str] = []

    # Use the full evidence narrative — it now includes the specific
    # trigger (e.g., "Critical Red Flag: Active SCA — Tucker v. Apple Inc.")
    if raw:
        sentences.append(f"{raw}.")

    # If we can find factor data from the origin, add it
    if origin:
        for fid in ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10"]:
            if fid in origin:
                fs = factor_score(state, fid)
                if fs:
                    pts = fs.get("points_deducted", 0)
                    mx = fs.get("max_points", 0)
                    sentences.append(
                        f"This contributes {pts:.0f}/{mx} points "
                        f"on scoring factor {fid}."
                    )
                    break

    return sentences or [raw or f"{name}: risk factor identified."]
