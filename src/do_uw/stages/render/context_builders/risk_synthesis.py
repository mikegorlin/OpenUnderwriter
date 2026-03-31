"""LLM-powered risk synthesis for underwriter-quality output.

Takes all extracted/analyzed data and produces integrated narrative that
reads like a 30-year D&O underwriter wrote it. Two tiers:

1. Section-level critical review — each major section gets an LLM pass
   that interprets the data through an underwriting lens
2. Master risk synthesis — weaves all section insights into a coherent
   risk narrative for Key Risk Findings and UW Framework

Uses the same OpenAI/DeepSeek client pattern as narrative_generator.py.
Cached per state hash so re-renders don't re-call LLM.

Phase 148+ deliverable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")
_synthesis_cache: dict[str, Any] = {}


def _get_client() -> Any | None:
    """Get OpenAI/DeepSeek client, or None if unavailable."""
    try:
        import openai
        import os

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY not set")
            return None
        return openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
    except Exception:
        return None


def _cache_key(prefix: str, data: str) -> str:
    """Generate a cache key from prefix and data hash."""
    h = hashlib.md5(data.encode(), usedforsecurity=False).hexdigest()[:12]
    return f"{prefix}:{h}"


# ---------------------------------------------------------------------------
# Data collection — build the underwriting brief
# ---------------------------------------------------------------------------


def _build_underwriting_brief(state: AnalysisState) -> dict[str, Any]:
    """Collect all critical data points into a structured brief for LLM.

    This is the single data package that the LLM uses to write the
    risk narrative. Everything an underwriter needs to know.
    """
    from do_uw.stages.render.sca_counter import get_active_genuine_scas
    from do_uw.stages.render.formatters import safe_float

    brief: dict[str, Any] = {
        "ticker": state.ticker or "UNKNOWN",
        "company_name": "",
    }

    # Company identity
    if state.company and state.company.identity:
        id_ = state.company.identity
        brief["company_name"] = getattr(getattr(id_, "legal_name", None), "value", "") or ""

    # Market data
    md = state.acquired_data.market_data if state.acquired_data else None
    if md and isinstance(md, dict):
        info = md.get("info", md.get("yfinance_info", {}))
        if isinstance(info, dict):
            mcap = safe_float(info.get("marketCap", 0), 0)
            price = safe_float(info.get("currentPrice", info.get("regularMarketPrice", 0)), 0)
            h52 = safe_float(info.get("fiftyTwoWeekHigh", 0), 0)
            l52 = safe_float(info.get("fiftyTwoWeekLow", 0), 0)
            shares = safe_float(info.get("sharesOutstanding", 0), 0)
            short_pct = safe_float(info.get("shortPercentOfFloat", 0), 0)
            revenue = safe_float(info.get("totalRevenue", 0), 0)
            debt = safe_float(info.get("totalDebt", 0), 0)
            cash = safe_float(info.get("totalCash", 0), 0)
            employees = info.get("fullTimeEmployees", 0)

            drawdown = (h52 - price) / h52 * 100 if h52 > 0 and price > 0 else 0

            brief["market"] = {
                "market_cap": mcap,
                "price": price,
                "52w_high": h52,
                "52w_low": l52,
                "drawdown_pct": round(drawdown, 1),
                "shares_outstanding": shares,
                "short_pct_float": round(short_pct * 100, 1)
                if short_pct < 1
                else round(short_pct, 1),
                "revenue": revenue,
                "total_debt": debt,
                "cash": cash,
                "employees": employees,
            }

        # Insider transactions
        ins = md.get("insider_transactions", {})
        if isinstance(ins, dict) and ins.get("Text"):
            texts = ins.get("Text", [])
            names = ins.get("Insider", [])
            values = ins.get("Value", [])
            sales = []
            for i in range(min(len(texts), len(names))):
                txt = texts[i] if i < len(texts) else ""
                if txt and "sale" in str(txt).lower():
                    val = values[i] if i < len(values) else 0
                    if isinstance(val, (int, float)) and val > 0:
                        sales.append(
                            {
                                "name": str(names[i]),
                                "value": val,
                            }
                        )
            sales.sort(key=lambda s: s["value"], reverse=True)
            total_sold = sum(s["value"] for s in sales)
            brief["insider_sales"] = {
                "total_value": total_sold,
                "transaction_count": len(sales),
                "top_sellers": sales[:5],
            }

    # Litigation
    active_scas = get_active_genuine_scas(state)
    sca_list = []
    for sca in active_scas:
        if isinstance(sca, dict):
            sca_list.append(
                {
                    "filing_date": sca.get("filing_date", ""),
                    "court": sca.get("court", ""),
                    "class_period_start": sca.get("class_period_start", ""),
                    "class_period_end": sca.get("class_period_end", ""),
                    "stock_drop_pct": sca.get("stock_drop_pct"),
                    "allegations": [
                        k.replace("allegation_", "").replace("_", " ")
                        for k in sca
                        if k.startswith("allegation_") and sca[k]
                    ],
                }
            )
    brief["active_scas"] = sca_list

    # Historical litigation
    lit_cases: list[dict[str, Any]] = []
    if state.acquired_data:
        lit_data = getattr(state.acquired_data, "litigation_data", None)
        if isinstance(lit_data, dict):
            lit_cases = lit_data.get("supabase_cases", [])
        elif lit_data:
            lit_cases = getattr(lit_data, "supabase_cases", []) or []
    brief["historical_sca_count"] = len(lit_cases)
    settled = [
        c
        for c in lit_cases
        if isinstance(c, dict) and str(c.get("case_status", "")).upper() == "SETTLED"
    ]
    brief["total_settlements_m"] = sum(c.get("settlement_amount_m", 0) or 0 for c in settled)

    # Scoring
    if state.scoring:
        s = state.scoring
        brief["scoring"] = {
            "composite_score": getattr(s, "composite_score", None),
            "tier": getattr(getattr(s, "tier", None), "name", None),
        }
        # Factor scores
        factors = getattr(s, "factor_scores", None)
        if factors and isinstance(factors, list):
            factor_list = []
            for f in factors:
                fd = (
                    f
                    if isinstance(f, dict)
                    else (f.model_dump() if hasattr(f, "model_dump") else {})
                )
                factor_list.append(
                    {
                        "name": fd.get("name", ""),
                        "score": fd.get("score", 0),
                        "max_score": fd.get("max_score", 0),
                    }
                )
            brief["scoring"]["factors"] = sorted(
                factor_list, key=lambda x: x.get("score", 0), reverse=True
            )[:5]

    # Risk factors from 10-K
    if state.extracted and state.extracted.risk_factors:
        rfs = state.extracted.risk_factors
        high_rfs = []
        for rf in rfs:
            rd = (
                rf
                if isinstance(rf, dict)
                else (rf.model_dump() if hasattr(rf, "model_dump") else {})
            )
            if rd.get("do_relevance") == "HIGH":
                high_rfs.append(
                    {
                        "title": rd.get("title", "")[:80],
                        "category": rd.get("category", ""),
                        "is_new": rd.get("is_new_this_year", False),
                    }
                )
        brief["high_do_risk_factors"] = high_rfs[:10]

    # Financial highlights
    if state.extracted and state.extracted.financials:
        fin = state.extracted.financials
        distress = getattr(fin, "distress", None)
        if distress:
            brief["financial_distress"] = {
                "altman_z": getattr(distress, "altman_z_score", None),
                "altman_zone": getattr(distress, "altman_zone", None),
                "beneish_m": getattr(distress, "beneish_m_score", None),
                "beneish_signal": getattr(distress, "beneish_signal", None),
            }

    # Governance
    if state.extracted and state.extracted.governance:
        gov = state.extracted.governance
        leadership = getattr(gov, "leadership", None)
        if leadership:
            execs = getattr(leadership, "executives", []) or []
            brief["governance"] = {
                "executive_count": len(execs),
                "board_size": len(getattr(gov, "board_forensics", []) or []),
            }

    return brief


# ---------------------------------------------------------------------------
# LLM synthesis calls
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a senior D&O liability underwriter with 30 years of experience
reviewing publicly traded companies. You write concise, data-driven risk assessments
that other underwriters rely on to make binding decisions.

RULES:
- Every sentence must contain specific data (dollar amounts, percentages, dates, names)
- Never use boilerplate or generic D&O language
- Cross-reference findings against each other (insider sales during class period = scienter)
- Focus on GO-FORWARD exposure, not backward-looking history
- Write in the voice of a senior underwriter briefing their team
- No bullet points — flowing analytical prose
- Connect the dots between findings that individually look routine but together tell a story"""


def synthesize_key_findings(state: AnalysisState) -> list[dict[str, Any]] | None:
    """Generate LLM-synthesized key risk findings.

    Returns a list of finding dicts compatible with the key_findings template,
    or None if LLM is unavailable (falls back to f-string findings).
    """
    brief = _build_underwriting_brief(state)
    brief_json = json.dumps(brief, default=str)

    cache_key = _cache_key("key_findings", brief_json)
    if cache_key in _synthesis_cache:
        return _synthesis_cache[cache_key]

    client = _get_client()
    if client is None:
        logger.warning("Anthropic client unavailable — skipping LLM synthesis")
        return None

    ticker = brief.get("ticker", "UNKNOWN")
    company = brief.get("company_name", ticker)

    prompt = f"""Analyze this D&O underwriting data for {company} ({ticker}) and write
exactly 5 key risk findings. Each finding should be 2-3 sentences of integrated
analytical prose — not formatted data points, but the kind of narrative a senior
underwriter would dictate after reviewing the full file.

CRITICAL: These 5 findings must tell a coherent STORY:
- Finding 1: The most urgent current exposure (active litigation + what makes it dangerous)
- Finding 2: The market/financial context that amplifies the litigation risk
- Finding 3: The governance/insider pattern that creates scienter exposure
- Finding 4: The biggest GO-FORWARD strategic risk (what triggers the NEXT claim)
- Finding 5: The second biggest go-forward risk or the structural weakness

Cross-reference between findings. If there's an active SCA AND insider selling AND
a stock crash, weave them together — that's a scienter narrative, not three separate facts.

DATA:
{brief_json[:12000]}

Return EXACTLY 5 findings as a JSON array. Each finding object must have:
- "headline": short title (5-8 words)
- "severity": "red" or "yellow"
- "narrative": 2-3 sentence analytical paragraph (the prose an underwriter writes)
- "badge_label": 1-2 word badge (e.g., "ACTIVE CLAIM", "BALANCE SHEET", "GOVERNANCE")

Return ONLY the JSON array, no other text."""

    try:
        response = client.chat.completions.create(
            model=_DEFAULT_MODEL,
            max_tokens=2000,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()

        # Parse JSON from response (handle markdown code blocks)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        findings_data = json.loads(raw)
        if not isinstance(findings_data, list) or len(findings_data) < 3:
            logger.warning("LLM returned invalid findings structure")
            return None

        # Convert to template-compatible format
        results: list[dict[str, Any]] = []
        for f in findings_data[:5]:
            narrative = f.get("narrative", "")
            results.append(
                {
                    "id": f"synth_{len(results)}",
                    "headline": f.get("headline", "Risk Finding"),
                    "severity": f.get("severity", "red"),
                    "is_risk_factor": True,
                    "headline_tags": "",
                    "badge_value": f.get("badge_label", "RISK"),
                    "evidence_bullets": [narrative] if narrative else [],
                }
            )

        _synthesis_cache[cache_key] = results
        logger.info("LLM synthesized %d key findings for %s", len(results), ticker)
        return results

    except Exception:
        logger.warning("LLM key findings synthesis failed", exc_info=True)
        return None


def synthesize_section_review(
    section_id: str,
    section_data: dict[str, Any],
    state: AnalysisState,
) -> str | None:
    """Generate LLM critical review for a single section.

    Returns a 2-4 sentence underwriter insight paragraph, or None if
    LLM is unavailable.
    """
    data_json = json.dumps(section_data, default=str)[:6000]
    cache_key = _cache_key(f"section_{section_id}", data_json)
    if cache_key in _synthesis_cache:
        return _synthesis_cache[cache_key]

    client = _get_client()
    if client is None:
        return None

    ticker = state.ticker or "UNKNOWN"

    prompt = f"""Review this {section_id} data for {ticker} through a D&O underwriting lens.
Write 2-3 sentences of critical analysis — what does this data MEAN for the D&O risk?
What would you flag to your underwriting team? What's the go-forward exposure?

Focus on what's UNUSUAL, CONCERNING, or NOTABLE — not what's normal.
If everything looks clean, say so in one sentence and explain why.

DATA:
{data_json}

Return ONLY the analytical paragraph, no headers or formatting."""

    try:
        response = client.chat.completions.create(
            model=_DEFAULT_MODEL,
            max_tokens=400,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content.strip()
        _synthesis_cache[cache_key] = text
        return text

    except Exception:
        logger.warning("LLM section review failed for %s", section_id, exc_info=True)
        return None


def synthesize_uw_framework(
    state: AnalysisState,
    key_findings: list[dict[str, Any]] | None = None,
) -> str | None:
    """Generate LLM-synthesized underwriting framework recommendation.

    Takes the full data picture and key findings to produce a coherent
    underwriting posture recommendation — the kind of summary a chief
    underwriter writes before the risk committee meeting.
    """
    brief = _build_underwriting_brief(state)

    # Include key findings narratives if available
    if key_findings:
        brief["key_findings_narratives"] = [
            {
                "headline": f.get("headline", ""),
                "narrative": " ".join(f.get("evidence_bullets", [])),
            }
            for f in key_findings[:5]
        ]

    brief_json = json.dumps(brief, default=str)
    cache_key = _cache_key("uw_framework", brief_json)
    if cache_key in _synthesis_cache:
        return _synthesis_cache[cache_key]

    client = _get_client()
    if client is None:
        return None

    ticker = brief.get("ticker", "UNKNOWN")
    company = brief.get("company_name", ticker)

    prompt = f"""Write the underwriting framework recommendation for {company} ({ticker}).
This goes in the "Suggested Underwriting Posture" section that the lead underwriter
reads before deciding whether to quote, and at what terms.

Structure (flowing prose, not bullets):
1. OVERALL POSTURE — one sentence: bind/quote with conditions/decline/refer
2. KEY CONCERN — the single biggest risk driver (1-2 sentences)
3. PRICING IMPLICATION — what this risk profile means for rate/retention/capacity
4. CONDITIONS — specific conditions or exclusions to consider
5. MONITORING — what to watch going forward

DATA:
{brief_json[:10000]}

Return ONLY the analytical prose, no headers or formatting. 4-6 sentences total."""

    try:
        response = client.chat.completions.create(
            model=_DEFAULT_MODEL,
            max_tokens=600,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        text = response.choices[0].message.content.strip()
        _synthesis_cache[cache_key] = text
        return text

    except Exception:
        logger.warning("LLM UW framework synthesis failed", exc_info=True)
        return None


def synthesize_company_profile(state: AnalysisState) -> dict[str, str] | None:
    """Generate LLM-synthesized company profile for the Company section.

    Produces 4 focused analytical paragraphs that replace the data dump:
    1. Business overview — what the company does and how it makes money,
       framed for D&O relevance
    2. Risk landscape — the key risk factors, what's new this year,
       what the go-forward exposure looks like
    3. Concentration & structural risk — revenue/customer/geographic
       concentration, regulatory exposure, key person risk
    4. D&O underwriting implications — what this company profile means
       for the D&O program specifically

    Returns dict with keys: overview, risk_landscape, structural_risk,
    do_implications — or None if LLM unavailable.
    """
    brief = _build_underwriting_brief(state)

    # Add company-specific data
    ext = state.extracted
    if ext:
        # Risk factors
        rfs = ext.risk_factors or []
        rf_summary = []
        for rf in rfs[:15]:
            rd = (
                rf
                if isinstance(rf, dict)
                else (rf.model_dump() if hasattr(rf, "model_dump") else {})
            )
            if rd.get("do_relevance") in ("HIGH", "MEDIUM"):
                rf_summary.append(
                    {
                        "title": rd.get("title", "")[:80],
                        "category": rd.get("category", ""),
                        "severity": rd.get("severity", ""),
                        "is_new": rd.get("is_new_this_year", False),
                        "do_relevance": rd.get("do_relevance", ""),
                    }
                )
        brief["risk_factors"] = rf_summary

        # Governance highlights
        gov = ext.governance
        if gov:
            leadership = getattr(gov, "leadership", None)
            if leadership:
                execs = getattr(leadership, "executives", []) or []
                for e in execs:
                    title_sv = getattr(e, "title", None)
                    title_str = getattr(title_sv, "value", title_sv) if title_sv else ""
                    if title_str and "ceo" in str(title_str).lower():
                        name_sv = getattr(e, "name", None)
                        brief["ceo_name"] = str(getattr(name_sv, "value", name_sv) or "")
                        brief["ceo_tenure"] = getattr(e, "tenure_years", None)
                        break

    brief_json = json.dumps(brief, default=str)
    cache_key = _cache_key("company_profile", brief_json)
    if cache_key in _synthesis_cache:
        return _synthesis_cache[cache_key]

    client = _get_client()
    if client is None:
        return None

    ticker = brief.get("ticker", "UNKNOWN")
    company = brief.get("company_name", ticker)

    prompt = f"""Write a D&O underwriting company profile for {company} ({ticker}).

You are briefing a senior underwriter who needs to decide whether to quote this risk.
They have 2 minutes to read the company section before moving to financials and litigation.

Write EXACTLY 4 paragraphs in a JSON object:

1. "overview" — What the company does, how it makes money, its market position.
   Frame for D&O relevance: what about this business model creates or mitigates
   securities litigation risk? Mention revenue, market cap, employee count, sector.
   2-3 sentences.

2. "risk_landscape" — The top 3-4 risk factors from the 10-K that matter for D&O.
   Not all 22 — just the ones that could trigger a claim. If any are NEW this year,
   flag that. What's the dominant exposure vector? 2-3 sentences.

3. "structural_risk" — Concentration risk (customer, geographic, product), regulatory
   exposure (FCPA, DMA, antitrust), key person dependency, corporate complexity.
   What structural features of this company amplify D&O exposure? 2-3 sentences.

4. "do_implications" — The synthesis. Given everything above, what does this company
   profile mean for the D&O program? Is this a company where claims come from
   earnings misses, regulatory actions, M&A, or operational failures? What should
   the underwriter watch for in the next 12 months? 2-3 sentences.

DATA:
{brief_json[:10000]}

Return ONLY the JSON object with keys: overview, risk_landscape, structural_risk, do_implications.
Each value is a string paragraph. No markdown formatting."""

    try:
        response = client.chat.completions.create(
            model=_DEFAULT_MODEL,
            max_tokens=1200,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        result = json.loads(raw)
        if not isinstance(result, dict):
            return None

        _synthesis_cache[cache_key] = result
        logger.info("LLM synthesized company profile for %s", ticker)
        return result

    except Exception:
        logger.warning("LLM company profile synthesis failed", exc_info=True)
        return None


__all__ = [
    "synthesize_company_profile",
    "synthesize_key_findings",
    "synthesize_section_review",
    "synthesize_uw_framework",
]
