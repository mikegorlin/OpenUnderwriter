"""Auto-answer engine for underwriting screening questions.

Maps screening questions (from Supabase risk card or internal framework)
to pipeline-extracted data, evaluates upgrade/downgrade criteria, and
produces pre-filled answers with evidence and verdicts.

Each answerer function takes the full render context and returns an
AnsweredQuestion dict with: answer, evidence, verdict (UPGRADE/DOWNGRADE/
NEUTRAL/NO_DATA), and confidence.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def answer_screening_questions(
    questions: list[dict[str, Any]],
    ctx: dict[str, Any],
) -> list[dict[str, Any]]:
    """Auto-answer screening questions from pipeline data.

    Args:
        questions: Screening questions from get_risk_card or internal framework.
            Each has: question_id, question, weight, category, scenario,
            data_source, why_it_matters, upgrade_criteria, downgrade_criteria.
        ctx: Full render context from build_html_context (has executive_summary,
            financials, market, governance, litigation, scoring, etc.).

    Returns:
        Enriched questions with added fields: answer, evidence, verdict,
        confidence, data_found.
    """
    answered: list[dict[str, Any]] = []
    for q in questions:
        qid = q.get("question_id", "")
        answerer = _ANSWERERS.get(qid)
        if answerer:
            result = answerer(q, ctx)
        else:
            # Generic fallback — try to match by category
            cat = q.get("category", "")
            fallback = _CATEGORY_FALLBACKS.get(cat)
            if fallback:
                result = fallback(q, ctx)
            else:
                result = _no_data(q)
        answered.append({**q, **result})
    return answered


# ── Helper extractors ──────────────────────────────────────────────


def _sv(val: Any) -> Any:
    """Extract .value from SourcedValue or return as-is."""
    return val.value if hasattr(val, "value") else val


def _yf_info(ctx: dict[str, Any]) -> dict[str, Any]:
    """Get yfinance info dict from context state."""
    state = ctx.get("_state")
    if not state:
        return {}
    mkt_data = getattr(state.acquired_data, "market_data", None) or {}
    return mkt_data.get("info", {})


def _fmt_pct(val: float | None) -> str:
    if val is None:
        return "N/A"
    return f"{val:.1f}%" if abs(val) < 100 else f"{val:,.0f}%"


def _fmt_currency(val: float | None, compact: bool = True) -> str:
    if val is None:
        return "N/A"
    if compact:
        if abs(val) >= 1e12:
            return f"${val/1e12:.1f}T"
        if abs(val) >= 1e9:
            return f"${val/1e9:.1f}B"
        if abs(val) >= 1e6:
            return f"${val/1e6:.1f}M"
    return f"${val:,.0f}"


def _no_data(q: dict[str, Any]) -> dict[str, Any]:
    return {
        "answer": "Insufficient pipeline data to auto-answer.",
        "evidence": [],
        "verdict": "NO_DATA",
        "confidence": "LOW",
        "data_found": False,
    }


# ── UNIV: Universal questions ──────────────────────────────────────


def _answer_univ_01(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """UNIV-01: Stock drops >15% in last 12 months."""
    mkt = ctx.get("market", {})
    yfi = _yf_info(ctx)

    current = mkt.get("current_price", "") or yfi.get("currentPrice", "")
    high_52w = yfi.get("fiftyTwoWeekHigh")
    low_52w = yfi.get("fiftyTwoWeekLow")

    # Check for significant drops from enhanced_drop_events
    drops = ctx.get("enhanced_drop_events", [])

    evidence = []
    if high_52w and low_52w:
        drawdown = ((high_52w - low_52w) / high_52w) * 100
        evidence.append(f"52-week range: ${low_52w:.2f} – ${high_52w:.2f} (max drawdown {drawdown:.1f}%)")

    if current:
        evidence.append(f"Current price: {current}")

    big_drops = [d for d in drops if isinstance(d, dict) and abs(float(d.get("pct_change", 0) or 0)) >= 15]
    if big_drops:
        for d in big_drops[:3]:
            evidence.append(f"Drop {d.get('date', '?')}: {d.get('pct_change', '?')}% — {d.get('description', '')}")

    # Max drawdown from context
    mdd_1y = ctx.get("max_drawdown_1y_val")
    if mdd_1y and isinstance(mdd_1y, (int, float)):
        evidence.append(f"Max drawdown (1Y): {mdd_1y:.1f}%")

    # Verdict
    if big_drops:
        verdict = "DOWNGRADE"
        answer = f"{len(big_drops)} single-day drop(s) exceeding 15% in the last 12 months."
    elif high_52w and low_52w:
        drawdown = ((high_52w - low_52w) / high_52w) * 100
        if drawdown > 30:
            verdict = "DOWNGRADE"
            answer = f"No single-day >15% drop identified, but 52-week drawdown of {drawdown:.1f}% exceeds 30%."
        elif drawdown < 15:
            verdict = "UPGRADE"
            answer = f"Low volatility — 52-week drawdown only {drawdown:.1f}%."
        else:
            verdict = "NEUTRAL"
            answer = f"Moderate volatility — 52-week drawdown of {drawdown:.1f}%."
    else:
        return _no_data(q)

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "HIGH", "data_found": True}


def _answer_univ_02(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """UNIV-02: Short interest as % of float."""
    mkt = ctx.get("market", {})
    yfi = _yf_info(ctx)

    si_pct = yfi.get("shortPercentOfFloat")
    si_ratio = yfi.get("shortRatio")

    if si_pct is None:
        # Try extracted market
        si_obj = mkt.get("short_interest")
        if isinstance(si_obj, dict):
            si_pct = si_obj.get("short_pct_float")

    if si_pct is None:
        return _no_data(q)

    # shortPercentOfFloat from yfinance is a decimal (0.0085 = 0.85%)
    if si_pct < 1:
        si_pct_display = si_pct * 100
    else:
        si_pct_display = si_pct

    evidence = [f"Short interest: {si_pct_display:.2f}% of float"]
    if si_ratio:
        evidence.append(f"Days to cover: {si_ratio:.1f}")

    if si_pct_display > 8:
        verdict = "DOWNGRADE"
        answer = f"Elevated short interest at {si_pct_display:.1f}% of float — above 8% threshold."
    elif si_pct_display < 3:
        verdict = "UPGRADE"
        answer = f"Low short interest at {si_pct_display:.2f}% of float."
    else:
        verdict = "NEUTRAL"
        answer = f"Moderate short interest at {si_pct_display:.1f}% of float."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "HIGH", "data_found": True}


def _answer_univ_03(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """UNIV-03: Repeat SCA target."""
    lit = ctx.get("litigation", {})
    rc_repeat = lit.get("risk_card_repeat_filer", {})
    rc_filings = lit.get("risk_card_filing_history", [])
    rc_score = lit.get("risk_card_score")

    if not rc_repeat and not rc_filings:
        # Fallback to pipeline litigation data
        cases = lit.get("cases", []) + lit.get("historical_cases", [])
        if cases:
            n = len(cases)
            settled = [c for c in cases if c.get("status", "").upper() == "SETTLED"]
            evidence = [f"{n} total SCA case(s) found in pipeline data", f"{len(settled)} settled"]
            if n >= 2:
                verdict = "DOWNGRADE"
                answer = f"Repeat filer — {n} SCA cases identified."
            elif n == 1 and settled:
                verdict = "NEUTRAL"
                answer = "Single prior SCA with settlement."
            elif n == 1:
                verdict = "NEUTRAL"
                answer = "Single prior SCA (dismissed or pending)."
            else:
                verdict = "UPGRADE"
                answer = "No prior SCA history."
            return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "MEDIUM", "data_found": True}
        return _no_data(q)

    evidence = []
    filer_cat = rc_repeat.get("filer_category", "NONE")
    settle_rate = rc_repeat.get("company_settlement_rate_pct")
    total_settle = rc_repeat.get("total_settlement_exposure_m")
    n_filings = len(rc_filings)

    evidence.append(f"Filer category: {filer_cat}")
    evidence.append(f"Total SCA filings: {n_filings}")
    if settle_rate is not None:
        evidence.append(f"Settlement rate: {settle_rate}%")
    if total_settle is not None:
        evidence.append(f"Total settlement exposure: ${total_settle}M")
    if rc_score is not None:
        evidence.append(f"Composite SCA risk score: {rc_score}/100")

    if filer_cat in ("CHRONIC", "REPEAT"):
        verdict = "DOWNGRADE"
        answer = f"{filer_cat} repeat filer — {n_filings} SCA filings, {settle_rate}% settlement rate, ${total_settle}M total exposure."
    elif filer_cat == "PRIOR" and n_filings >= 2:
        verdict = "DOWNGRADE"
        answer = f"Prior filer with {n_filings} SCA filings and ${total_settle}M total settlement exposure."
    elif filer_cat == "PRIOR":
        verdict = "NEUTRAL"
        answer = f"Single prior SCA filing. Settlement rate: {settle_rate}%."
    elif filer_cat in ("FIRST_TIME", "NONE"):
        verdict = "UPGRADE"
        answer = "No prior SCA history in database."
    else:
        verdict = "NEUTRAL"
        answer = f"Filer category: {filer_cat}."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "HIGH", "data_found": True}


def _answer_univ_04(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """UNIV-04: Market cap and settlement severity curve."""
    es = ctx.get("executive_summary", {})
    yfi = _yf_info(ctx)

    mc_raw = yfi.get("marketCap") or 0
    mc_display = es.get("market_cap", "")

    if not mc_raw:
        if mc_display and mc_display != "N/A":
            return {
                "answer": f"Market cap: {mc_display}. Specific severity curve positioning requires numeric value.",
                "evidence": [f"Market cap: {mc_display}"],
                "verdict": "NEUTRAL",
                "confidence": "MEDIUM",
                "data_found": True,
            }
        return _no_data(q)

    evidence = [f"Market cap: {_fmt_currency(mc_raw)}"]

    # Map to severity curve
    if mc_raw >= 50e9:
        verdict = "DOWNGRADE"
        answer = f"Market cap {_fmt_currency(mc_raw)} — mega-cap zone where P90 settlements regularly exceed $100M. Tower adequacy is critical."
    elif mc_raw >= 10e9:
        verdict = "DOWNGRADE"
        answer = f"Market cap {_fmt_currency(mc_raw)} — large-cap zone where settlements scale significantly with damages. P90 settlements can exceed $100M."
    elif mc_raw >= 2e9:
        verdict = "NEUTRAL"
        answer = f"Market cap {_fmt_currency(mc_raw)} — mid-cap range. Settlements typically $5-50M if case proceeds."
    elif mc_raw >= 500e6:
        verdict = "NEUTRAL"
        answer = f"Market cap {_fmt_currency(mc_raw)} — small-cap. Lower absolute exposure but higher volatility-driven drop risk."
    else:
        verdict = "UPGRADE"
        answer = f"Market cap {_fmt_currency(mc_raw)} — micro/nano-cap. Settlement severity typically <$10M."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "HIGH", "data_found": True}


# ── ACCT: Accounting fraud questions ───────────────────────────────


def _answer_acct_01(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """ACCT-01: Material weakness in internal controls."""
    fin = ctx.get("financials", {})
    state = ctx.get("_state")

    evidence = []

    # Check audit alerts from financial context
    audit_alerts = fin.get("audit_alerts") or fin.get("audit_disclosure_alerts") or []
    mw_context = fin.get("audit_mw_do_context", "")

    # Check signal results for material weakness signals
    scoring = ctx.get("scoring", {})
    triggered = ctx.get("triggered_checks", [])
    mw_signals = [t for t in triggered if isinstance(t, dict) and "material_weakness" in str(t.get("signal_id", "")).lower()]

    if mw_context:
        evidence.append(f"MW D&O context: {mw_context[:200]}")
    if audit_alerts:
        for alert in audit_alerts[:3]:
            if isinstance(alert, dict):
                evidence.append(f"Audit alert: {alert.get('description', str(alert))[:120]}")
            else:
                evidence.append(f"Audit alert: {str(alert)[:120]}")
    if mw_signals:
        for s in mw_signals[:2]:
            evidence.append(f"Signal triggered: {s.get('signal_id', '')} — {s.get('evidence', '')[:80]}")

    # Verdict
    has_mw = bool(mw_signals) or any("material weakness" in str(a).lower() for a in audit_alerts)
    if has_mw:
        verdict = "DOWNGRADE"
        answer = "Material weakness or significant deficiency identified in audit disclosures."
    elif audit_alerts:
        verdict = "NEUTRAL"
        answer = "Audit alerts present but no material weakness identified."
    elif mw_context:
        verdict = "NEUTRAL"
        answer = "Internal controls context available — no material weakness flagged."
    else:
        # No data either way — check if we have audit info at all
        auditor = fin.get("auditor_name")
        if auditor:
            evidence.append(f"Auditor: {auditor}")
            verdict = "UPGRADE"
            answer = "No material weakness or significant deficiency disclosed. Clean audit opinion."
        else:
            return _no_data(q)

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "MEDIUM", "data_found": True}


def _answer_acct_02(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """ACCT-02: Big 4 auditor, auditor changes."""
    fin = ctx.get("financials", {})
    yfi = _yf_info(ctx)
    state = ctx.get("_state")

    auditor = fin.get("auditor_name")
    tenure = fin.get("auditor_tenure")
    audit_risk = yfi.get("auditRisk")

    # Check for auditor change in acquired market data
    has_change = (getattr(state.acquired_data, "market_data", None) or {}).get("has_auditor_change") if state else None

    evidence = []

    big4 = {"Deloitte", "Ernst & Young", "EY", "KPMG", "PricewaterhouseCoopers", "PwC"}

    if auditor:
        evidence.append(f"Auditor: {auditor}")
        is_big4 = any(b4.lower() in str(auditor).lower() for b4 in big4)
        evidence.append(f"Big 4: {'Yes' if is_big4 else 'No'}")
    else:
        is_big4 = None

    if tenure:
        evidence.append(f"Tenure: {tenure}")
    if audit_risk is not None:
        evidence.append(f"Yahoo audit risk score: {audit_risk}/10")
    if has_change is not None:
        evidence.append(f"Recent auditor change: {'Yes' if has_change else 'No'}")

    if not auditor and audit_risk is None:
        return _no_data(q)

    if is_big4 is False or (has_change and str(has_change).lower() == "true"):
        verdict = "DOWNGRADE"
        parts = []
        if is_big4 is False:
            parts.append("non-Big 4 auditor")
        if has_change and str(has_change).lower() == "true":
            parts.append("recent auditor change")
        answer = f"Risk factors: {', '.join(parts)}."
    elif is_big4 and audit_risk is not None and audit_risk <= 3:
        verdict = "UPGRADE"
        answer = f"Big 4 auditor ({auditor}) with low audit risk score ({audit_risk}/10)."
    elif is_big4:
        verdict = "UPGRADE"
        answer = f"Big 4 auditor ({auditor})."
    else:
        verdict = "NEUTRAL"
        answer = f"Auditor: {auditor}. Audit risk: {audit_risk}/10." if audit_risk else f"Auditor: {auditor}."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "MEDIUM", "data_found": True}


def _answer_acct_03(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """ACCT-03: GAAP vs non-GAAP delta."""
    # This typically requires earnings release data which may be in LLM extraction
    fin = ctx.get("financials", {})
    triggered = ctx.get("triggered_checks", [])

    # Look for earnings quality signals
    eq_signals = [t for t in triggered if isinstance(t, dict) and any(
        k in str(t.get("signal_id", "")).lower()
        for k in ("gaap", "non_gaap", "earnings_quality", "earnings_manipulation")
    )]

    beneish = fin.get("beneish_score") or fin.get("beneish_level")
    beneish_ctx = fin.get("beneish_do_context", "")

    evidence = []
    if beneish:
        evidence.append(f"Beneish M-Score: {beneish}")
    if beneish_ctx:
        evidence.append(f"Beneish context: {beneish_ctx[:150]}")
    for s in eq_signals[:2]:
        evidence.append(f"Signal: {s.get('signal_id', '')} — {s.get('evidence', '')[:80]}")

    if not evidence:
        return _no_data(q)

    if eq_signals or (beneish and "manipulator" in str(beneish).lower()):
        verdict = "DOWNGRADE"
        answer = "Earnings quality concerns identified — potential GAAP/non-GAAP divergence risk."
    elif beneish and "safe" in str(beneish).lower():
        verdict = "UPGRADE"
        answer = f"Beneish M-Score indicates low manipulation risk ({beneish})."
    else:
        verdict = "NEUTRAL"
        answer = "Earnings quality metrics available but inconclusive."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "MEDIUM", "data_found": True}


def _answer_acct_04(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """ACCT-04: CFO tenure and changes."""
    gov = ctx.get("governance", {})
    exec_risk = ctx.get("executive_risk", {})

    # Look for CFO in officers or board members
    officers = gov.get("board_members", [])
    ceo_comp = gov.get("ceo_comp", {})

    evidence = []

    # Check for CFO-specific data in executive risk or governance
    if isinstance(exec_risk, dict):
        for key in exec_risk:
            if "cfo" in str(key).lower():
                evidence.append(f"CFO data: {str(exec_risk[key])[:120]}")

    # Check triggered signals for executive change
    triggered = ctx.get("triggered_checks", [])
    cfo_signals = [t for t in triggered if isinstance(t, dict) and "cfo" in str(t.get("signal_id", "")).lower()]
    exec_change_signals = [t for t in triggered if isinstance(t, dict) and "executive_change" in str(t.get("signal_id", "")).lower()]

    for s in cfo_signals + exec_change_signals:
        evidence.append(f"Signal: {s.get('signal_id', '')} — {s.get('evidence', '')[:80]}")

    if not evidence:
        return _no_data(q)

    if cfo_signals or exec_change_signals:
        verdict = "DOWNGRADE"
        answer = "CFO change or short tenure detected — review 8-K Item 5.02 for context."
    else:
        verdict = "NEUTRAL"
        answer = "Executive data present but CFO-specific tenure not extractable from current pipeline data."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "LOW", "data_found": True}


def _answer_acct_05(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """ACCT-05: Revenue recognition complexity."""
    yfi = _yf_info(ctx)

    sector = yfi.get("sector", "")
    industry = yfi.get("industry", "")
    rev_growth = yfi.get("revenueGrowth")

    evidence = []
    if sector:
        evidence.append(f"Sector: {sector}")
    if industry:
        evidence.append(f"Industry: {industry}")
    if rev_growth is not None:
        evidence.append(f"Revenue growth: {rev_growth*100:.1f}%")

    # High-complexity industries for rev rec
    complex_industries = {
        "software", "saas", "cloud", "construction", "defense", "aerospace",
        "consulting", "services", "telecom", "real estate",
    }
    is_complex = any(ci in industry.lower() for ci in complex_industries) if industry else False

    # Check triggered signals
    triggered = ctx.get("triggered_checks", [])
    rev_signals = [t for t in triggered if isinstance(t, dict) and any(
        k in str(t.get("signal_id", "")).lower()
        for k in ("revenue_recognition", "rev_rec", "asc_606", "deferred_revenue")
    )]
    for s in rev_signals[:2]:
        evidence.append(f"Signal: {s.get('signal_id', '')} — {s.get('evidence', '')[:80]}")

    if not evidence:
        return _no_data(q)

    if rev_signals:
        verdict = "DOWNGRADE"
        answer = "Revenue recognition complexity flags identified in signal analysis."
    elif is_complex:
        verdict = "NEUTRAL"
        answer = f"Industry ({industry}) typically involves complex revenue recognition — verify ASC 606 disclosures."
    else:
        verdict = "UPGRADE"
        answer = f"Industry ({industry or sector}) generally has straightforward revenue recognition."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "MEDIUM", "data_found": True}


# ── INSIDER: Insider trading questions ─────────────────────────────


def _answer_insider_01(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """INSIDER-01: Insider selling patterns."""
    state = ctx.get("_state")
    if not state:
        return _no_data(q)

    mkt_data = getattr(state.acquired_data, "market_data", None) or {}
    insider_txns = mkt_data.get("insider_transactions")
    insider_narrative = ctx.get("insider_narrative", "")

    evidence = []
    if insider_narrative:
        evidence.append(f"Insider narrative: {str(insider_narrative)[:200]}")

    if isinstance(insider_txns, dict):
        buys = insider_txns.get("buys", 0)
        sells = insider_txns.get("sells", 0)
        evidence.append(f"Insider transactions: {buys} buys, {sells} sells")
    elif isinstance(insider_txns, list):
        evidence.append(f"Insider transactions: {len(insider_txns)} records")

    # Check triggered signals
    triggered = ctx.get("triggered_checks", [])
    insider_signals = [t for t in triggered if isinstance(t, dict) and "insider" in str(t.get("signal_id", "")).lower()]
    for s in insider_signals[:3]:
        evidence.append(f"Signal: {s.get('signal_id', '')} — {s.get('evidence', '')[:80]}")

    if not evidence:
        return _no_data(q)

    if insider_signals:
        verdict = "DOWNGRADE"
        answer = "Insider trading signals triggered — review Form 4 pattern for pre-announcement selling."
    else:
        verdict = "NEUTRAL"
        answer = "Insider transaction data available — no anomalous patterns flagged by signals."

    return {"answer": answer, "evidence": evidence, "verdict": verdict, "confidence": "MEDIUM", "data_found": True}


def _answer_insider_02(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """INSIDER-02: 10b5-1 plan coverage and governance."""
    gov = ctx.get("governance", {})

    # Check for trading policy signals
    triggered = ctx.get("triggered_checks", [])
    policy_signals = [t for t in triggered if isinstance(t, dict) and any(
        k in str(t.get("signal_id", "")).lower()
        for k in ("10b5", "trading_policy", "insider_policy", "blackout")
    )]

    evidence = []
    for s in policy_signals[:2]:
        evidence.append(f"Signal: {s.get('signal_id', '')} — {s.get('evidence', '')[:80]}")

    if not evidence:
        return {
            "answer": "10b5-1 plan details require proxy statement review — not yet auto-extracted.",
            "evidence": ["Data source: proxy statement corporate governance guidelines"],
            "verdict": "NO_DATA",
            "confidence": "LOW",
            "data_found": False,
        }

    return {"answer": "Trading policy signals detected.", "evidence": evidence, "verdict": "NEUTRAL", "confidence": "LOW", "data_found": True}


# ── Category fallbacks ─────────────────────────────────────────────


def _fallback_financial(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Generic financial question fallback."""
    fin = ctx.get("financials", {})
    es = ctx.get("executive_summary", {})
    evidence = []
    if es.get("revenue"):
        evidence.append(f"Revenue: {es['revenue']}")
    if es.get("market_cap"):
        evidence.append(f"Market cap: {es['market_cap']}")

    state = ctx.get("_state")
    if state:
        yf_info = (getattr(state.acquired_data, "market_data", None) or {}).get("info", {})
        for k in ["currentRatio", "debtToEquity", "returnOnEquity", "revenueGrowth"]:
            v = yf_info.get(k)
            if v is not None:
                evidence.append(f"{k}: {v}")

    if evidence:
        return {
            "answer": f"Financial data available — requires manual assessment against question criteria.",
            "evidence": evidence,
            "verdict": "NEUTRAL",
            "confidence": "LOW",
            "data_found": True,
        }
    return _no_data(q)


def _fallback_governance(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Generic governance question fallback."""
    gov = ctx.get("governance", {})
    evidence = []
    bs = gov.get("board_size")
    if bs:
        evidence.append(f"Board size: {bs}")
    ind = gov.get("board_independence_pct") or gov.get("pct_independent")
    if ind:
        evidence.append(f"Independence: {ind}")
    ceo_dual = gov.get("ceo_duality")
    if ceo_dual is not None:
        evidence.append(f"CEO duality: {ceo_dual}")

    state = ctx.get("_state")
    if state:
        yf_info = (getattr(state.acquired_data, "market_data", None) or {}).get("info", {})
        for k in ["boardRisk", "overallRisk"]:
            v = yf_info.get(k)
            if v is not None:
                evidence.append(f"{k}: {v}/10")

    if evidence:
        return {
            "answer": "Governance data available — requires manual assessment.",
            "evidence": evidence,
            "verdict": "NEUTRAL",
            "confidence": "LOW",
            "data_found": True,
        }
    return _no_data(q)


def _fallback_market(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Generic market question fallback."""
    mkt = ctx.get("market", {})
    evidence = []
    cp = mkt.get("current_price")
    if cp:
        evidence.append(f"Price: {cp}")
    beta = mkt.get("beta")
    if beta:
        evidence.append(f"Beta: {beta}")
    if evidence:
        return {
            "answer": "Market data available — requires manual assessment.",
            "evidence": evidence,
            "verdict": "NEUTRAL",
            "confidence": "LOW",
            "data_found": True,
        }
    return _no_data(q)


def _fallback_operational(q: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Generic operational question fallback."""
    state = ctx.get("_state")
    if not state:
        return _no_data(q)
    yf_info = (getattr(state.acquired_data, "market_data", None) or {}).get("info", {})
    evidence = []
    for k in ["sector", "industry", "fullTimeEmployees"]:
        v = yf_info.get(k)
        if v is not None:
            evidence.append(f"{k}: {v}")
    if evidence:
        return {
            "answer": "Operational context available — requires domain-specific assessment.",
            "evidence": evidence,
            "verdict": "NEUTRAL",
            "confidence": "LOW",
            "data_found": True,
        }
    return _no_data(q)


# ── Registries ─────────────────────────────────────────────────────


_ANSWERERS: dict[str, Any] = {
    "UNIV-01": _answer_univ_01,
    "UNIV-02": _answer_univ_02,
    "UNIV-03": _answer_univ_03,
    "UNIV-04": _answer_univ_04,
    "ACCT-01": _answer_acct_01,
    "ACCT-02": _answer_acct_02,
    "ACCT-03": _answer_acct_03,
    "ACCT-04": _answer_acct_04,
    "ACCT-05": _answer_acct_05,
    "INSIDER-01": _answer_insider_01,
    "INSIDER-02": _answer_insider_02,
}

_CATEGORY_FALLBACKS: dict[str, Any] = {
    "financial": _fallback_financial,
    "governance": _fallback_governance,
    "market": _fallback_market,
    "operational": _fallback_operational,
}


__all__ = ["answer_screening_questions"]
