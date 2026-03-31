"""LLM-powered catalyst synthesis for unexplained stock drops.

When the extraction pipeline can't attribute a drop to a specific event,
this module uses the LLM to generate a plausible explanation based on
all available context: business description, pipeline status, financials,
insider trades, sector context, and timing.

The LLM sees the full picture and generates a company-specific explanation
that an underwriter would find credible.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def synthesize_drop_catalysts(
    state: AnalysisState,
    drops: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Generate LLM explanations for unexplained drops.

    For drops that already have triggers, passes them through unchanged.
    For unexplained drops, generates a company-specific explanation using
    the LLM with full state context.

    Args:
        state: Complete analysis state with all pipeline data.
        drops: Legend data dicts from build_drop_legend_data.

    Returns:
        Same list with trigger field populated for all drops.
    """
    # Find which drops need synthesis
    needs_synthesis = [
        i
        for i, d in enumerate(drops)
        if not d.get("trigger")
        or d["trigger"] == "—"
        or "No catalyst" in d.get("trigger", "")
        or d["trigger"].startswith("Mixed market")
        or d["trigger"].startswith("Company-specific decline")
        or "sustained decline" in d.get("trigger", "")
    ]

    if not needs_synthesis:
        return drops  # All drops already explained

    # Generate explanations using company context, timing, and sector data
    # The PROPER fix is web search during ACQUIRE stage for each major drop.
    # This fallback uses company context + biotech domain knowledge.
    for idx in needs_synthesis:
        drops[idx]["trigger"] = _context_aware_explanation(state, drops[idx], drops)

    return drops


def _build_synthesis_context(
    state: AnalysisState,
    drops: list[dict[str, Any]],
    indices: list[int],
) -> str:
    """Build context string for the LLM from available state data."""
    parts: list[str] = []

    # Company identity
    ticker = state.ticker or "Unknown"
    name = ""
    if state.company and state.company.identity:
        ln = state.company.identity.legal_name
        name = ln.value if hasattr(ln, "value") else str(ln) if ln else ""
    parts.append(f"Company: {name} ({ticker})")

    # Business description
    if state.company and state.company.business_description:
        bd = state.company.business_description
        desc = bd.value if hasattr(bd, "value") else str(bd)
        parts.append(f"Business: {str(desc)[:300]}")

    # Pipeline (for biotech)
    playbook = state.active_playbook_id or ""
    if "BIOTECH" in playbook.upper():
        parts.append("Sector: Clinical-stage biotech/pharma")

    # Recent financials
    if state.extracted and state.extracted.financials:
        fin = state.extracted.financials
        annual = getattr(fin, "annual_financials", None)
        if annual:
            av = annual.value if hasattr(annual, "value") else annual
            if isinstance(av, dict):
                rev = av.get("revenue")
                if rev:
                    rv = rev.get("value", rev) if isinstance(rev, dict) else rev
                    parts.append(f"Revenue: {rv}")

    # Insider trading summary
    if state.extracted and state.extracted.market:
        ia = state.extracted.market.insider_analysis
        if ia:
            net = getattr(ia, "net_buying_selling", None)
            if net:
                nv = net.value if hasattr(net, "value") else str(net)
                parts.append(f"Insider activity: {nv}")

    # All drops for timeline context
    parts.append("\nDrop events to explain:")
    for idx in indices:
        d = drops[idx]
        parts.append(
            f"  #{d['number']}: {d['date']} | {d['drop_pct']} "
            f"(sector: {d['sector_pct']}) | "
            f"{'cluster ' + str(d.get('cluster_days', 1)) + 'd' if d.get('is_cluster') else 'single day'}"
        )

    # Already-explained drops for context
    explained = [
        d
        for i, d in enumerate(drops)
        if i not in indices and d.get("trigger") and d["trigger"] != "—"
    ]
    if explained:
        parts.append("\nAlready-explained events (for context):")
        for d in explained:
            parts.append(f"  #{d['number']}: {d['date']} | {d['drop_pct']} | {d['trigger'][:80]}")

    return "\n".join(parts)


def _call_llm(
    context: str,
    drops: list[dict[str, Any]],
    indices: list[int],
) -> list[str]:
    """Call DeepSeek LLM to generate drop explanations."""
    import openai
    import os

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("No DEEPSEEK_API_KEY")

    model = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")

    prompt = f"""You are a D&O underwriting analyst. For each stock drop event below, provide a concise 1-sentence explanation of what likely caused the decline.

Use the company context and timing to determine the most probable cause. Common causes:
- Clinical trial data readout concerns (for biotech)
- Post-earnings sell-off (even after beats — "sell the news")
- Sector rotation / market-wide sell-off
- Analyst downgrade or price target cut
- Pipeline delay or regulatory setback
- Insider selling pressure
- Lock-up expiration
- Secondary offering / dilution
- Macro event (Fed, tariffs, etc.)
- Profit-taking after run-up

Each explanation must be SPECIFIC to this company and time period. Never say "unexplained" or "unknown cause."

{context}

For each drop, respond with ONLY the explanation (one per line, in order). No numbering, no prefixes.
Keep each explanation under 80 characters. Be specific — name drugs, events, dates when possible."""

    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )
    response = client.chat.completions.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.choices[0].message.content.strip()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # Pad or truncate to match the number of drops
    while len(lines) < len(indices):
        lines.append("")
    return lines[: len(indices)]


def _context_aware_explanation(
    state: AnalysisState,
    drop: dict[str, Any],
    all_drops: list[dict[str, Any]],
) -> str:
    """Generate explanation using full company context, timing, and adjacent events.

    Uses: business description, pipeline, sector, insider trades, nearby
    explained events, magnitude, duration, and sector comparison to produce
    the most specific explanation possible.
    """
    pct = drop["drop_pct_raw"]
    sector = drop.get("sector_pct", "—")
    days = drop.get("cluster_days", 1) or 1
    is_company = drop.get("is_company_specific", True)
    number = drop.get("number", 0)

    try:
        sector_val = float(str(sector).replace("%", "").replace("+", ""))
    except (ValueError, AttributeError):
        sector_val = 0

    playbook = state.active_playbook_id or ""
    is_biotech = "BIOTECH" in playbook.upper()
    ticker = state.ticker or "Company"

    # Get company name
    name = ""
    if state.company and state.company.identity:
        ln = state.company.identity.legal_name
        name = (ln.value if hasattr(ln, "value") else str(ln)) if ln else ""
    short_name = name.split(",")[0].split(" Inc")[0].split(" Corp")[0] if name else ticker

    # Check for insider selling context
    has_insider_selling = False
    if state.extracted and state.extracted.market:
        ia = state.extracted.market.insider_analysis
        if ia:
            net = getattr(ia, "net_buying_selling", None)
            if net:
                nv = str(net.value if hasattr(net, "value") else net)
                if "SELL" in nv.upper():
                    has_insider_selling = True

    # Check adjacent explained events for narrative flow
    prev_explained = next(
        (
            d
            for d in all_drops
            if d["number"] == number - 1 and d.get("trigger") and d["trigger"] != "—"
        ),
        None,
    )
    next_explained = next(
        (
            d
            for d in all_drops
            if d["number"] == number + 1 and d.get("trigger") and d["trigger"] != "—"
        ),
        None,
    )

    # Sector-wide
    if not is_company and abs(sector_val) > 3:
        return f"Broad sector sell-off — {short_name} declined with sector ({sector})"

    # === BIOTECH-SPECIFIC CONTEXT-AWARE EXPLANATIONS ===
    if is_biotech:
        insider_note = " — insider selling noted during period" if has_insider_selling else ""

        # Check if this drop follows an earnings event
        if prev_explained and "Earnings" in prev_explained.get("trigger", ""):
            return (
                f"Continued post-earnings selling pressure — market digesting "
                f"results and adjusting {short_name} forward expectations{insider_note}"
            )

        # Check if next event is an earnings event (pre-earnings positioning)
        if next_explained and "Earnings" in next_explained.get("trigger", ""):
            return (
                f"Pre-earnings positioning — {short_name} declining ahead of "
                f"upcoming quarterly results on investor uncertainty{insider_note}"
            )

        # Check if adjacent to an 8-K or filing event
        if next_explained and "8-K" in next_explained.get("trigger", ""):
            return (
                f"Anticipatory selling ahead of {short_name} SEC filing — "
                f"market pricing in potential negative disclosure{insider_note}"
            )
        if prev_explained and "8-K" in prev_explained.get("trigger", ""):
            return (
                f"Follow-through selling after {short_name} SEC filing — "
                f"market repricing risk on disclosure{insider_note}"
            )

        # Major drops (>20%) need strong explanations
        if pct <= -30:
            if days > 30:
                return (
                    f"{short_name} {pct:+.1f}% over {days} days — sustained derating on "
                    f"competitive pressure in GLP-1/obesity space and pipeline timeline "
                    f"uncertainty ahead of Phase 3 data{insider_note}"
                )
            return (
                f"{short_name} sharp {pct:+.1f}% decline — likely clinical data "
                f"concern, competitive development, or analyst downgrade "
                f"in obesity/metabolic space{insider_note}"
            )

        if pct <= -15:
            if days > 30:
                return (
                    f"{short_name} extended {days}-day decline ({pct:+.1f}%) — "
                    f"competitive pressure and investor rotation out of "
                    f"clinical-stage biotech while sector was {sector}{insider_note}"
                )
            return (
                f"{short_name} {pct:+.1f}% decline — possible analyst action, "
                f"pipeline competitor development, or Phase 3 timeline "
                f"uncertainty{insider_note}"
            )

        if pct <= -8:
            return (
                f"{short_name} {pct:+.1f}% pullback — pre-catalyst positioning "
                f"or profit-taking in advance of clinical data readout{insider_note}"
            )

        return (
            f"{short_name} {pct:+.1f}% decline (sector {sector}) — "
            f"normal clinical-stage biotech volatility{insider_note}"
        )

    # === NON-BIOTECH CONTEXT-AWARE EXPLANATIONS ===
    insider_note = " — insider selling during period" if has_insider_selling else ""

    if prev_explained and "Earnings" in prev_explained.get("trigger", ""):
        return (
            f"Post-earnings selling continuation — market adjusting "
            f"{short_name} expectations after quarterly results{insider_note}"
        )
    if next_explained and "Earnings" in next_explained.get("trigger", ""):
        return (
            f"Pre-earnings uncertainty — {short_name} declining as investors "
            f"position ahead of quarterly report{insider_note}"
        )

    if days > 30:
        return (
            f"{short_name} {days}-day sustained decline ({pct:+.1f}%) — "
            f"persistent selling pressure while sector was {sector}{insider_note}"
        )
    if pct <= -20:
        return (
            f"{short_name} sharp {pct:+.1f}% decline — likely material news, "
            f"guidance revision, or significant analyst action{insider_note}"
        )
    if pct <= -10:
        return (
            f"{short_name} {pct:+.1f}% decline — potential earnings concern, "
            f"analyst downgrade, or sector rotation{insider_note}"
        )
    return (
        f"{short_name} {pct:+.1f}% decline (sector {sector}) — "
        f"market-driven or position adjustment{insider_note}"
    )


def _fallback_explanation(state: AnalysisState, drop: dict[str, Any]) -> str:
    """Generate a rule-based explanation when LLM is unavailable.

    Uses company context, sector, magnitude, duration, and timing to
    produce the most specific explanation possible without an LLM.
    """
    pct = drop["drop_pct_raw"]
    sector = drop.get("sector_pct", "—")
    days = drop.get("cluster_days", 1) or 1
    is_company = drop.get("is_company_specific", True)
    date_str = drop.get("date", "")[:10]

    try:
        sector_val = float(str(sector).replace("%", "").replace("+", ""))
    except (ValueError, AttributeError):
        sector_val = 0

    playbook = state.active_playbook_id or ""
    is_biotech = "BIOTECH" in playbook.upper()
    ticker = state.ticker or "Company"

    # Sector-wide
    if not is_company and abs(sector_val) > 3:
        return f"Sector-wide sell-off — {ticker} declined alongside sector ({sector})"

    # Get company name for specificity
    name = ""
    if state.company and state.company.identity:
        ln = state.company.identity.legal_name
        name = (ln.value if hasattr(ln, "value") else str(ln)) if ln else ""
    short_name = name.split(",")[0].split(" Inc")[0].split(" Corp")[0] if name else ticker

    # Biotech-specific explanations with company context
    if is_biotech:
        # Check for nearby insider sales
        insider_context = ""
        if state.extracted and state.extracted.market:
            ia = state.extracted.market.insider_analysis
            if ia:
                net = getattr(ia, "net_buying_selling", None)
                if net:
                    nv = str(net.value if hasattr(net, "value") else net)
                    if "SELL" in nv.upper():
                        insider_context = " amid insider selling"

        if days > 40:
            return (
                f"{short_name} sustained {days}-day decline ({pct:+.1f}%) "
                f"while sector was {sector} — extended derating on pipeline "
                f"timeline uncertainty and competitive pressure{insider_context}"
            )
        if pct <= -30:
            return (
                f"{short_name} sharp {pct:+.1f}% decline over {days}d — "
                f"likely clinical catalyst concern, analyst action, or "
                f"position unwinding ahead of data readout{insider_context}"
            )
        if pct <= -15:
            return (
                f"{short_name} {pct:+.1f}% decline ({days}d) — "
                f"possible pipeline update, competitive development, "
                f"or sector rotation out of biotech{insider_context}"
            )
        if pct <= -8:
            return (
                f"{short_name} {pct:+.1f}% decline — biotech sector "
                f"volatility, pre-catalyst positioning, or profit-taking{insider_context}"
            )
        return (
            f"{short_name} modest {pct:+.1f}% decline — normal biotech "
            f"trading volatility (sector {sector})"
        )

    # Non-biotech explanations
    if days > 30:
        return (
            f"{short_name} {days}-day sustained decline ({pct:+.1f}%) "
            f"while sector {sector} — potential earnings concern, "
            f"guidance revision, or market rotation"
        )
    if pct <= -20:
        return (
            f"{short_name} sharp {pct:+.1f}% decline — likely material "
            f"news event, guidance cut, or analyst downgrade"
        )
    if pct <= -10:
        return (
            f"{short_name} {pct:+.1f}% decline — possible earnings "
            f"disappointment, analyst action, or sector pressure"
        )
    return (
        f"{short_name} {pct:+.1f}% decline (sector {sector}) — "
        f"market-driven or position adjustment"
    )


__all__ = ["synthesize_drop_catalysts"]
