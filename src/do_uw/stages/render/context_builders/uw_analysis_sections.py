"""UW Analysis extended sections — context builders for sections 2-6."""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.uw_analysis_infographics import fmt_large_number
from do_uw.stages.render.formatters import safe_float

logger = logging.getLogger(__name__)

_TIER_COLORS = {
    "WIN": "#16A34A",
    "PREFERRED": "#22C55E",
    "WRITE": "#2563EB",
    "WATCH": "#D97706",
    "WALK": "#DC2626",
    "NO_TOUCH": "#7F1D1D",
}


def _to_dict(obj: Any) -> dict[str, Any]:
    """Convert Pydantic model or dict to plain dict."""
    if isinstance(obj, dict):
        return obj
    return obj.model_dump() if hasattr(obj, "model_dump") else {}


def _sv(v: Any) -> Any:
    """Extract .value from SourcedValue dicts/lists or return raw.

    Handles:
    - dict with "value" key → returns the value
    - list of SourcedValue dicts → returns list of extracted values
    - anything else → returns unchanged
    """
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    if isinstance(v, list):
        extracted = []
        for item in v:
            if isinstance(item, dict) and "value" in item:
                extracted.append(item["value"])
            else:
                extracted.append(item)
        return extracted
    return v


def _format_allegations(case: dict[str, Any]) -> str:
    """Extract clean allegations text from a litigation case dict.

    Handles: plain string, SourcedValue string, list of SourcedValue strings.
    Never returns raw Python repr.
    """
    # Try summary first (plain string)
    summary = _sv(case.get("allegations_summary"))
    if isinstance(summary, str) and summary:
        return summary

    raw = case.get("allegations")
    if raw is None:
        return ""

    val = _sv(raw)

    # Single string
    if isinstance(val, str):
        return val

    # List of strings (from _sv extracting SourcedValue list)
    if isinstance(val, list):
        parts = []
        for item in val:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                # Nested SourcedValue or raw dict — extract value
                parts.append(str(item.get("value", "")))
            else:
                parts.append(str(item))
        return "; ".join(p for p in parts if p)

    return str(val) if val else ""


# Jargon strings to skip in evidence text
_EVIDENCE_JARGON = ("Signal-driven scoring", "coverage=", "rule_based")


def _first_meaningful_evidence(ev: list[Any]) -> str:
    """Return the first evidence string that isn't system jargon."""
    for item in ev:
        s = str(item)
        if any(j in s for j in _EVIDENCE_JARGON):
            continue
        if s.strip():
            return s
    return ""


def _structure_exec_narrative(raw: str) -> dict[str, Any]:
    """Parse a wall-of-text executive narrative into structured components.

    Returns dict with:
      thesis: str -- first sentence (the core recommendation)
      risk_points: list[str] -- key negative observations
      mitigants: list[str] -- positive/offsetting observations
      conditions: list[str] -- specific terms/conditions recommended
      recommendation: str -- closing recommendation sentence
    """
    import re

    if not raw:
        return {}

    # Strip markdown headers
    text = re.sub(r"^#+ .+\n?", "", raw, flags=re.MULTILINE).strip()
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # Strip bold markdown

    # Split on paragraph breaks first, then sentence boundaries
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # Re-join as sentences
    all_sentences: list[str] = []
    for para in paragraphs:
        sents = re.split(r"(?<=[^A-Z][.!?])\s+(?=[A-Z])", para)
        all_sentences.extend(s.strip() for s in sents if s.strip())

    sentences = all_sentences
    if not sentences:
        return {}

    # First sentence/paragraph is the thesis — look for the recommendation line
    thesis = sentences[0]
    thesis_end = 0
    # If first paragraph is just a recommendation label, use it alone
    for i, s in enumerate(sentences):
        if (
            s.startswith("Underwriting Recommendation:")
            or s.startswith("WRITE")
            or s.startswith("WATCH")
        ):
            thesis = s
            thesis_end = i
            break
        if i == 0 and len(s) < 100:
            thesis = s
            thesis_end = i
            break

    risk_points: list[str] = []
    mitigants: list[str] = []
    conditions: list[str] = []
    recommendation = ""

    risk_keywords = (
        "active securities",
        "litigation",
        "deduction",
        "consumed",
        "ceiling",
        "elevate",
        "risk",
        "exposure",
        "class action",
        "filing-driven",
        "historical pattern",
        "premium architecture",
        "upper quartile",
    )
    mitigant_keywords = (
        "positive",
        "zero active",
        "clean audit",
        "no material",
        "safe",
        "offsetting",
        "downward pressure",
        "absence of",
        "minimal",
        "disconnected from disclosure",
    )
    condition_keywords = (
        "Terms must",
        "must incorporate",
        "mandatory",
        "automatic",
        "sublimit",
        "notice protocol",
        "quarterly",
        "reporting",
    )

    for s in sentences[thesis_end + 1 :]:
        s_lower = s.lower()
        if any(k in s_lower for k in condition_keywords):
            # Extract numbered conditions from within the sentence
            cond_match = re.findall(r"\((\d+)\)\s*([^(]+?)(?=\(\d+\)|$)", s)
            if cond_match:
                for _num, cond_text in cond_match:
                    conditions.append(cond_text.strip().rstrip(",;. "))
            else:
                conditions.append(s)
        elif any(k in s_lower for k in mitigant_keywords):
            mitigants.append(s)
        elif "tier" in s_lower and ("reflect" in s_lower or "recommend" in s_lower):
            recommendation = s
        elif any(k in s_lower for k in risk_keywords):
            risk_points.append(s)
        else:
            # Default: put in risk or mitigants based on tone
            risk_points.append(s)

    return {
        "thesis": thesis,
        "risk_points": risk_points[:5],
        "mitigants": mitigants[:4],
        "conditions": conditions[:5],
        "recommendation": recommendation,
    }


def _add_underwriting_critical_negatives(
    negatives: list[dict[str, Any]], state: AnalysisState
) -> None:
    """Add real-world underwriting-critical findings to key negatives.

    Scoring factors miss things a 30-year underwriter would flag immediately:
    active SCAs, extreme stock drawdowns, dangerous leverage, CHRONIC filer
    status. This supplements factor-based negatives with hard findings.
    """
    from do_uw.stages.render.sca_counter import get_active_genuine_scas

    existing_names = {n["name"].lower() for n in negatives}

    # 1. Active SCAs — the single most important D&O risk signal
    active_scas = get_active_genuine_scas(state)
    if active_scas and "active sca" not in " ".join(existing_names):
        case = active_scas[0]
        if isinstance(case, dict):
            court = case.get("court", "")
            cp = f"Class period {case.get('class_period_start', '?')} to {case.get('class_period_end', '?')}"
            drop = case.get("stock_drop_pct")
            ev = f"Active SCA filed in {court}. {cp}."
            if drop:
                ev += f" Stock drop: {drop}%."
        else:
            ev = "Active securities class action pending — direct D&O liability exposure."
        negatives.append(
            {
                "name": "Active Securities Class Action",
                "factor_id": "SCA",
                "points": "10.0",
                "max": "10",
                "ratio": 1.0,
                "evidence": ev,
            }
        )

    # 2. Extreme stock drawdown (>25% in recent period)
    md = state.acquired_data.market_data if state.acquired_data else None
    if md and isinstance(md, dict):
        info = md.get("info", md.get("yfinance_info", {}))
        if isinstance(info, dict):
            h52 = safe_float(info.get("fiftyTwoWeekHigh", 0), 0)
            price = safe_float(info.get("currentPrice", info.get("regularMarketPrice", 0)), 0)
            if h52 > 0 and price > 0:
                drawdown = (h52 - price) / h52 * 100
                if drawdown >= 25 and "drawdown" not in " ".join(existing_names):
                    negatives.append(
                        {
                            "name": "Severe Stock Drawdown",
                            "factor_id": "DRAWDOWN",
                            "points": f"{min(drawdown / 10, 10):.1f}",
                            "max": "10",
                            "ratio": min(drawdown / 100, 1.0),
                            "evidence": (
                                f"{drawdown:.0f}% decline from 52-week high of ${h52:.2f} "
                                f"to ${price:.2f}. Drawdowns >25% are the primary trigger for "
                                f"Section 10(b) loss causation theories in SCA litigation."
                            ),
                        }
                    )

    # 3. Extreme leverage (D/E > 200%)
    if state.extracted and state.extracted.financials:
        fin = state.extracted.financials
        de = getattr(fin, "debt_to_equity", None)
        de_val = de.value if hasattr(de, "value") else de
        if (
            de_val is None
            and state.acquired_data
            and isinstance(state.acquired_data.market_data, dict)
        ):
            de_val = safe_float(
                state.acquired_data.market_data.get("info", {}).get("debtToEquity", 0), 0
            )
            if de_val and de_val > 10:  # yfinance uses percentage
                de_val = de_val / 100
        de_float = safe_float(de_val, 0)
        if de_float > 2.0 and "leverage" not in " ".join(existing_names):
            negatives.append(
                {
                    "name": "Extreme Leverage",
                    "factor_id": "LEVERAGE",
                    "points": f"{min(de_float, 10):.1f}",
                    "max": "10",
                    "ratio": min(de_float / 5, 1.0),
                    "evidence": (
                        f"Debt-to-equity ratio of {de_float * 100:.0f}%. "
                        f"Extreme leverage amplifies D&O exposure through going-concern "
                        f"risk, covenant breach potential, and balance sheet fragility."
                    ),
                }
            )

    # 4. CHRONIC/REPEAT SCA filer
    if state.acquired_data:
        lit_data = getattr(state.acquired_data, "litigation_data", None)
        cases: list[dict[str, Any]] = []
        if isinstance(lit_data, dict):
            cases = lit_data.get("supabase_cases", [])
        elif lit_data:
            cases = getattr(lit_data, "supabase_cases", []) or []
        if (
            len(cases) >= 3
            and "chronic" not in " ".join(existing_names)
            and "repeat" not in " ".join(existing_names)
        ):
            settled = [
                c
                for c in cases
                if isinstance(c, dict) and str(c.get("case_status", "")).upper() == "SETTLED"
            ]
            total_settled = sum(c.get("settlement_amount_m", 0) or 0 for c in settled)
            ev = f"CHRONIC SCA filer — {len(cases)} filings."
            if total_settled:
                ev += f" Total settlements: ${total_settled:.1f}M."
            negatives.append(
                {
                    "name": "Chronic SCA Filer",
                    "factor_id": "CHRONIC",
                    "points": f"{min(len(cases) * 2, 10):.1f}",
                    "max": "10",
                    "ratio": min(len(cases) / 5, 1.0),
                    "evidence": ev,
                }
            )


def build_exec_summary_context(state: AnalysisState) -> dict[str, Any]:
    """Build executive summary + recommendation context."""
    pcn = {}
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        n = state.analysis.pre_computed_narratives
        pcn = _to_dict(n)

    exec_summary_text = pcn.get("executive_summary", "") or ""
    scoring_narrative = pcn.get("scoring", "") or ""
    narrative_structured = _structure_exec_narrative(exec_summary_text)

    scoring = _get_scoring(state)
    tier_info = scoring.get("tier", {})
    tier_name = tier_info.get("tier", "?") if isinstance(tier_info, dict) else str(tier_info)
    action = tier_info.get("action", "") if isinstance(tier_info, dict) else ""
    prob = tier_info.get("probability_range", "") if isinstance(tier_info, dict) else ""

    # Claim probability details
    cp = scoring.get("claim_probability", {}) or {}
    band = cp.get("band", "") if isinstance(cp, dict) else ""
    range_low = cp.get("range_low_pct", "") if isinstance(cp, dict) else ""
    range_high = cp.get("range_high_pct", "") if isinstance(cp, dict) else ""

    # Factor scores for key positives/negatives — with real D&O evidence from signals
    factors = scoring.get("factor_scores", [])

    # Build signal evidence per factor AND track signal IDs for relabeling
    factor_evidence: dict[str, list[str]] = {}
    factor_signal_ids: dict[str, list[str]] = {}
    if state.analysis and hasattr(state.analysis, "signal_results"):
        sr = state.analysis.signal_results
        sigs = sr if isinstance(sr, dict) else (_to_dict(sr) if sr else {})
        for sid, sig in sigs.items():
            if not isinstance(sig, dict) or sig.get("status") != "TRIGGERED":
                continue
            sig_factors = sig.get("factors", [])
            if not sig_factors:
                continue
            do_ctx = sig.get("do_context", "")
            sig_name = sig.get("signal_name", "")
            # Extract the useful part of do_context (after the jargon prefix)
            if do_ctx:
                parts = do_ctx.strip().split(". ", 1)
                if len(parts) > 1 and (
                    "signals elevated" in parts[0] or "caution zone" in parts[0]
                ):
                    explanation = parts[1]
                else:
                    explanation = do_ctx
            elif sig_name:
                explanation = sig_name
            else:
                continue
            fid0 = sig_factors[0]
            factor_evidence.setdefault(fid0, []).append(explanation)
            factor_signal_ids.setdefault(fid0, []).append(sid)

    def _relabel_factor(fid: str, default_name: str) -> str:
        """Relabel a factor based on what signals actually triggered.

        When the triggered signals for a factor are about a different topic
        than the factor name (e.g., F4 'IPO/SPAC/M&A' but only insider
        trading signals triggered), use the signal topic instead.
        """
        sids = factor_signal_ids.get(fid, [])
        if not sids:
            return default_name

        # Map signal ID prefixes to human-readable topic labels
        prefix_topics = {
            "GOV.INSIDER": "Insider Trading",
            "STOCK.INSIDER": "Insider Trading",
            "EXEC.INSIDER": "Insider Trading",
            "GOV.EXEC": "Executive Risk Profile",
            "EXEC.TENURE": "Executive Tenure",
            "FIN.FORENSIC": "Financial Forensics",
            "FIN.ACCT": "Accounting Risk",
            "LIT.SCA": "Securities Litigation",
            "STOCK.PRICE": "Stock Performance",
            "STOCK.VALUATION": "Valuation Risk",
            "NLP.RISK": "Disclosure Risk",
            "BIZ.EVENT": "Corporate Events",
        }

        # Count topics across all triggered signals
        topic_counts: dict[str, int] = {}
        for sid in sids:
            # Try 2-part prefix first, then 1-part
            parts = sid.split(".")
            prefix2 = ".".join(parts[:2]) if len(parts) >= 2 else parts[0]
            topic = prefix_topics.get(prefix2, "")
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        if not topic_counts:
            return default_name

        # If dominant topic differs from factor name, relabel
        dominant_topic = max(topic_counts, key=lambda t: topic_counts[t])
        # Check if the factor name already matches the dominant topic
        name_lower = default_name.lower()
        topic_lower = dominant_topic.lower()
        # If factor name contains a keyword from the dominant topic, keep it
        topic_words = set(topic_lower.split())
        name_words = set(name_lower.replace("/", " ").split())
        if topic_words & name_words:
            return default_name
        return dominant_topic

    # Build positive reasons dynamically from the signal data and company context.
    # NO hardcoded descriptions — derive everything from actual state.
    def _build_positive_reason(fid: str, fname: str, state: AnalysisState) -> str:
        """Build a data-driven positive reason for a low-scoring factor."""
        # Count how many signals for this factor are CLEAR vs total
        sr = {}
        if state.analysis and hasattr(state.analysis, "signal_results"):
            sr = state.analysis.signal_results
            sr = sr if isinstance(sr, dict) else (_to_dict(sr) if sr else {})

        clear_count = 0
        total_count = 0
        for _sid, sig in sr.items():
            if not isinstance(sig, dict):
                continue
            sig_factors = sig.get("factors", [])
            if fid in sig_factors or fid.replace(".", "") in [
                sf.replace(".", "") for sf in sig_factors
            ]:
                total_count += 1
                if sig.get("status") in ("CLEAR", "NOT_TRIGGERED"):
                    clear_count += 1

        # Check company-specific context for overrides
        years_public = None
        if state.company and hasattr(state.company, "years_public"):
            yp = state.company.years_public
            years_public = safe_float(yp.value if hasattr(yp, "value") else yp, None)

        # F4: Recent IPO companies ALWAYS have Section 11 exposure
        if fid in ("F4", "F.4") and years_public is not None and years_public <= 5:
            return (
                f"IPO {years_public:.0f}yr ago — Section 11/12(a)(2) exposure window active. "
                f"Low scoring reflects limited IPO-related claims filed to date, not absence of exposure."
            )

        # General case: build human-readable reason
        if total_count > 0:
            pct = clear_count / total_count * 100
            if pct >= 90:
                return f"No material {fname.lower()} concerns identified in current filings"
            elif pct >= 70:
                return (
                    f"Limited {fname.lower()} exposure — most risk indicators within normal range"
                )
            else:
                return f"Below-average {fname.lower()} risk relative to scoring thresholds"
        return f"Low risk: minimal {fname.lower()} indicators detected"

    positives = []
    negatives = []
    for f in factors:
        pts = safe_float(f.get("points_deducted", 0), 0)
        mx = safe_float(f.get("max_points", 1), 1)
        ratio = pts / mx if mx > 0 else 0
        raw_name = f.get("factor_name", f.get("factor_id", ""))
        fid = f.get("factor_id", "")

        # Get real evidence from triggered signals — combine top 2 for richer context
        # Deduplicate by checking for sentence overlap before combining
        sig_ev = factor_evidence.get(fid, [])
        if len(sig_ev) >= 2:
            # Only combine if the second evidence doesn't share sentences with the first
            # Split into sentences and check overlap
            ev0_sentences = {s.strip() for s in sig_ev[0].split(". ") if len(s.strip()) > 20}
            ev1_sentences = {s.strip() for s in sig_ev[1].split(". ") if len(s.strip()) > 20}
            if ev0_sentences & ev1_sentences:
                # Overlapping sentences — keep only the first
                evidence_text = sig_ev[0]
            elif sig_ev[1][:50] == sig_ev[0][:50]:
                evidence_text = sig_ev[0]
            else:
                evidence_text = sig_ev[0] + " " + sig_ev[1]
        elif sig_ev:
            evidence_text = sig_ev[0]
        else:
            evidence_text = ""

        # Relabel factor name based on actual triggered signals
        display_name = _relabel_factor(fid, raw_name)

        entry = {
            "name": display_name,
            "factor_id": fid,
            "points": f"{pts:.1f}",
            "max": f"{mx:.0f}",
            "ratio": ratio,
            "evidence": evidence_text,
        }
        if ratio < 0.05:
            # For positives, build reason dynamically from signal data and company context
            entry["evidence"] = _build_positive_reason(fid, display_name, state)
            positives.append(entry)
        elif ratio >= 0.15:
            negatives.append(entry)

    # Supplement with real-world underwriting-critical findings not in scoring factors
    _add_underwriting_critical_negatives(negatives, state)

    negatives.sort(key=lambda x: x["ratio"], reverse=True)
    positives.sort(key=lambda x: x["ratio"])

    # Deduplicate by name — keep highest-ratio entry for negatives
    seen_neg_names: set[str] = set()
    deduped_negatives: list[dict[str, Any]] = []
    for neg in negatives:
        if neg["name"] not in seen_neg_names:
            seen_neg_names.add(neg["name"])
            deduped_negatives.append(neg)
    negatives = deduped_negatives

    # Red flags
    red_flags = scoring.get("red_flags", [])
    rf_items = []
    for rf in red_flags or []:
        if rf.get("triggered"):
            rf_items.append(
                {
                    "name": rf.get("flag_name", ""),
                    "evidence": rf.get("evidence", []),
                    "max_tier": rf.get("max_tier", ""),
                }
            )

    # Commentary
    commentary_factual, commentary_bullets = _get_commentary(state, "executive_summary")

    return {
        "exec_summary_text": exec_summary_text,
        "scoring_narrative": scoring_narrative,
        "narrative": exec_summary_text,
        "narrative_structured": narrative_structured,
        "commentary_factual": commentary_factual,
        "commentary_bullets": commentary_bullets,
        "tier_name": tier_name,
        "tier_color": _TIER_COLORS.get(tier_name, "#6B7280"),
        "tier_action": action,
        "probability_range": prob,
        "claim_band": band,
        "claim_range": f"{range_low}% - {range_high}%" if range_low else "",
        "key_negatives": negatives[:6],
        "key_positives": positives[:6],
        "red_flags": rf_items,
    }


def build_financial_context(state: AnalysisState) -> dict[str, Any]:
    """Build financial analysis section context."""
    info = _get_yfinance_info(state)

    rev = info.get("totalRevenue")
    ebitda_val = info.get("ebitda")
    ni = info.get("netIncomeToCommon")
    ocf = info.get("operatingCashflow")
    fcf = info.get("freeCashflow")
    cash = info.get("totalCash")
    debt = info.get("totalDebt")
    cr = info.get("currentRatio")
    gw = info.get("goodwill")
    ta = info.get("totalAssets")
    # Try extracting goodwill from XBRL balance sheet if yfinance doesn't have it
    if gw is None and state.extracted and state.extracted.financials:
        gw = _extract_goodwill_from_xbrl(state)
    # Fallback: Total Assets - Net Tangible Assets = total intangibles including goodwill
    if gw is None and ta:
        nta = info.get("netTangibleAssets")
        if nta is not None and ta > 0:
            gw = ta - nta
            if gw <= 0:
                gw = 0  # Will show as "Minimal"
    gw_pct = (gw / ta * 100) if gw and ta and ta > 0 else None
    gm = info.get("grossMargins")
    om = info.get("operatingMargins")
    nm = info.get("profitMargins")
    em = info.get("ebitdaMargins")

    # Forensic scores
    distress = {}
    if state.extracted and state.extracted.financials:
        d = state.extracted.financials.distress
        if d:
            distress = _to_dict(d)

    beneish = distress.get("beneish_m_score", {}) or {}
    altman = distress.get("altman_z_score", {}) or {}
    piotroski = distress.get("piotroski_f_score", {}) or {}
    ohlson = distress.get("ohlson_o_score", {}) or {}

    b_score = beneish.get("score")
    b_zone = beneish.get("zone", "")
    a_score = altman.get("score")
    a_zone = altman.get("zone", "")
    p_score = piotroski.get("score")
    p_zone = piotroski.get("zone", "")
    o_score = ohlson.get("score")
    o_zone = ohlson.get("zone", "")

    # Historical financials from XBRL
    periods = []
    rev_hist: list[dict[str, Any]] = []
    ni_hist: list[dict[str, Any]] = []
    if state.extracted and state.extracted.financials:
        stmts = state.extracted.financials.statements
        if stmts:
            sd = _to_dict(stmts)
            inc = sd.get("income_statement", {})
            periods = inc.get("periods", []) or []
            for item in inc.get("line_items", []) or []:
                label = (item.get("label", "") or "").lower()
                vals = item.get("values", {})
                if "revenue" in label or "net sales" in label:
                    for p in periods:
                        v = _sv(vals.get(p))
                        rev_hist.append({"period": p, "value": v})
                if "net income" in label and "comprehensive" not in label:
                    for p in periods:
                        v = _sv(vals.get(p))
                        ni_hist.append({"period": p, "value": v})

    def _zc(z: str) -> str:
        z = (z or "").lower()
        return (
            "#16A34A"
            if z in ("safe", "strong", "manipulation unlikely")
            else ("#D97706" if z in ("grey", "gray", "moderate", "warning") else "#DC2626")
        )

    def _distress_do_context(model: str, score: float | None, zone: str | None) -> str:
        """Generate correct D&O context for distress models using ACTUAL zone, not signal."""
        if score is None or not zone:
            return ""
        z = zone.lower()
        s = f"{score:.2f}"
        if model == "altman":
            if z in ("distress",):
                return (
                    f"Altman Z-Score of {s} is in the distress zone (below 1.81) — historically associated "
                    "with 2-3x higher D&O claim frequency and increased exposure to insolvency-related claims."
                )
            if z in ("grey", "gray"):
                return (
                    f"Altman Z-Score of {s} is in the grey zone (1.81-2.99) — moderate financial stress "
                    "that could amplify D&O claim severity if stock price declines coincide with negative disclosures."
                )
            return (
                f"Altman Z-Score of {s} is in the safe zone (above 2.99) — low bankruptcy probability, "
                "a protective factor for D&O risk."
            )
        if model == "beneish":
            if "manip" in z:
                return (
                    f"Beneish M-Score of {s} exceeds -2.22 threshold — elevated earnings manipulation probability. "
                    "Restatement risk is a primary driver of SCA filings."
                )
            return (
                f"Beneish M-Score of {s} is below -2.22 threshold — low earnings manipulation probability. "
                "Reduces restatement risk."
            )
        if model == "ohlson":
            if z in ("distress",):
                return (
                    f"Ohlson O-Score of {s} indicates elevated bankruptcy probability — "
                    "heightened exposure to insolvency-related D&O claims."
                )
            return (
                f"Ohlson O-Score of {s} indicates low bankruptcy probability — "
                "supportive of favorable D&O risk profile."
            )
        if model == "piotroski":
            if z in ("weak",):
                return (
                    f"Piotroski F-Score of {score:.0f}/9 indicates weak financial position — "
                    "deteriorating fundamentals increase D&O exposure."
                )
            if z in ("grey", "gray", "moderate"):
                return (
                    f"Piotroski F-Score of {score:.0f}/9 indicates moderate financial position — "
                    "mixed signals warrant monitoring."
                )
            return (
                f"Piotroski F-Score of {score:.0f}/9 indicates strong financial position — "
                "positive for D&O risk assessment."
            )
        return ""

    # 4.7.2 + 4.7.3 Tax jurisdiction + UTB (placeholder — needs --fresh with new XBRL concepts)
    tax_breakdown = {}
    utb_amount = None
    # These will be populated when XBRL tax concepts are extracted
    if state.extracted and state.extracted.financials:
        fin_data = _to_dict(state.extracted.financials)
        tax_data = fin_data.get("tax_jurisdiction", {})
        if isinstance(tax_data, dict) and tax_data:
            tax_breakdown = {
                "federal": tax_data.get("federal"),
                "state": tax_data.get("state"),
                "foreign": tax_data.get("foreign"),
            }
        utb_raw = fin_data.get("unrecognized_tax_benefits")
        if utb_raw:
            utb_amount = safe_float(_sv(utb_raw), None)

    # Growth & return metrics from yfinance
    rev_growth = info.get("revenueGrowth")
    earn_growth = info.get("earningsGrowth")
    earn_q_growth = info.get("earningsQuarterlyGrowth")
    roe = info.get("returnOnEquity")
    roa = info.get("returnOnAssets")
    qr = info.get("quickRatio")
    bv = info.get("bookValue")
    rps = info.get("revenuePerShare")

    # Narrative & commentary
    fin_narrative = ""
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        pcn = _to_dict(state.analysis.pre_computed_narratives)
        fin_narrative = pcn.get("financial", "") or ""
    commentary_factual, commentary_bullets = _get_commentary(state, "financial")

    # Section opener — data-driven D&O connection
    section_opener = _build_section_opener(
        "financial",
        state,
        {
            "revenue": fmt_large_number(rev),
            "net_income": fmt_large_number(ni),
            "rev_growth": f"{rev_growth * 100:+.1f}% YoY" if rev_growth is not None else "N/A",
            "beneish_zone": b_zone.title() if b_zone else "",
            "altman_zone": a_zone.title() if a_zone else "",
        },
    )

    # Revenue provenance — derive from XBRL statements when available
    revenue_source = "N/A"
    revenue_as_of = ""
    revenue_confidence = ""
    if state.extracted and state.extracted.financials:
        fin_stmts = state.extracted.financials.statements
        if fin_stmts:
            sd_prov = _to_dict(fin_stmts)
            inc_prov = sd_prov.get("income_statement", {})
            prov_periods = inc_prov.get("periods", []) or []
            for prov_item in inc_prov.get("line_items", []) or []:
                prov_label = (prov_item.get("label", "") or "").lower()
                if "revenue" in prov_label or "net sales" in prov_label:
                    prov_vals = prov_item.get("values", {})
                    # Use latest period that has a value
                    for pk in prov_periods:
                        if prov_vals.get(pk) is not None:
                            revenue_as_of = pk
                            revenue_source = "XBRL"
                            revenue_confidence = "HIGH"
                            break
                    break
    # Fallback: if revenue came from yfinance
    if revenue_source == "N/A" and rev is not None:
        revenue_source = "yfinance"
        revenue_confidence = "MEDIUM"

    return {
        "revenue": fmt_large_number(rev),
        "revenue_source": revenue_source,
        "revenue_as_of": revenue_as_of,
        "revenue_confidence": revenue_confidence,
        "ebitda": fmt_large_number(ebitda_val),
        "net_income": fmt_large_number(ni),
        "ocf": fmt_large_number(ocf),
        "fcf": fmt_large_number(fcf),
        "cash": fmt_large_number(cash),
        "debt": fmt_large_number(debt),
        "current_ratio": f"{cr:.2f}" if cr else "N/A",
        "goodwill_pct": f"{gw_pct:.1f}%"
        if gw_pct
        else ("Minimal" if gw is not None and gw == 0 else "N/A"),
        "gross_margin": f"{gm * 100:.1f}%" if gm else "N/A",
        "op_margin": f"{om * 100:.1f}%" if om else "N/A",
        "net_margin": f"{nm * 100:.1f}%" if nm else "N/A",
        "ebitda_margin": f"{em * 100:.1f}%" if em else "N/A",
        "revenue_growth": f"{rev_growth * 100:.1f}%" if rev_growth is not None else "N/A",
        "earnings_growth": f"{earn_growth * 100:.1f}%" if earn_growth is not None else "N/A",
        "earnings_quarterly_growth": f"{earn_q_growth * 100:.1f}%"
        if earn_q_growth is not None
        else "N/A",
        "return_on_equity": f"{roe * 100:.1f}%" if roe is not None else "N/A",
        "return_on_assets": f"{roa * 100:.1f}%" if roa is not None else "N/A",
        "quick_ratio": f"{qr:.2f}" if qr is not None else "N/A",
        "book_value": f"${bv:.2f}" if bv is not None else "N/A",
        "revenue_per_share": f"${rps:.2f}" if rps is not None else "N/A",
        "beneish_score": f"{b_score:.2f}" if b_score is not None else "N/A",
        "beneish_zone": b_zone.title() if b_zone else "N/A",
        "beneish_color": _zc(b_zone),
        "altman_score": f"{a_score:.2f}" if a_score is not None else "N/A",
        "altman_zone": a_zone.title() if a_zone else "N/A",
        "altman_color": _zc(a_zone),
        "piotroski_score": f"{p_score:.0f}" if p_score is not None else "N/A",
        "piotroski_zone": p_zone.title() if p_zone else "N/A",
        "piotroski_color": _zc(p_zone),
        "ohlson_score": f"{o_score:.2f}" if o_score is not None else "N/A",
        "ohlson_zone": o_zone.title() if o_zone else "N/A",
        "ohlson_color": _zc(o_zone),
        # Alias keys for distress_indicators.html.j2 template (uses z_/beneish_/o_ prefixes)
        "z_score": f"{a_score:.2f}" if a_score is not None else "N/A",
        "z_zone": a_zone if a_zone else "N/A",
        "z_do_context": _distress_do_context("altman", a_score, a_zone),
        "beneish_do_context": _distress_do_context("beneish", b_score, b_zone),
        "beneish_level": "TRIGGERED" if b_zone and "manipul" in b_zone.lower() else "CLEAR",
        "o_score": f"{o_score:.2f}" if o_score is not None else "N/A",
        "o_zone": o_zone if o_zone else "N/A",
        "o_do_context": _distress_do_context("ohlson", o_score, o_zone),
        "piotroski_do_context": _distress_do_context("piotroski", p_score, p_zone),
        "z_trajectory": [],
        "piotroski_components": [],
        "periods": periods,
        "rev_hist": rev_hist,
        "ni_hist": ni_hist,
        "tax_breakdown": tax_breakdown,
        "utb_amount": fmt_large_number(utb_amount) if utb_amount else "N/A",
        "audit_alerts": _build_audit_alerts(state),
        "debt_maturity": _build_debt_maturity(state),
        "narrative": fin_narrative,
        "section_opener": section_opener,
        "commentary_factual": commentary_factual,
        "commentary_bullets": commentary_bullets,
        # Quarterly trends
        "quarterly_balance": _build_quarterly_balance(state),
        "quarterly_cashflow": _build_quarterly_cashflow(state),
        # Annual income statement comparison
        "annual_income": _build_annual_income(state),
        # XBRL balance sheet highlights
        "xbrl_balance_highlights": _build_xbrl_balance_highlights(state),
        # Unified financial snapshot — key metrics from all 3 statements
        "unified_snapshot": _build_unified_financial_snapshot(state, info),
    }


def _build_unified_financial_snapshot(
    state: AnalysisState,
    info: dict[str, Any],
) -> dict[str, Any]:
    """Build unified financial snapshot: annual P&L + quarterly P&L + balance sheet.

    Returns a dict with 'annual', 'quarterly', and 'balance_sheet' sections,
    each containing rows of key metrics with periods and change columns.
    """
    result: dict[str, Any] = {"annual": [], "quarterly": [], "balance_sheet": []}

    # === ANNUAL: Key P&L from yfinance quarterly data (aggregate FY) or XBRL ===
    # Use XBRL income statement if available for annual data
    annual_rows: list[dict[str, Any]] = []
    if state.extracted and state.extracted.financials:
        stmts = state.extracted.financials.statements
        if stmts:
            sd = _to_dict(stmts)
            inc = sd.get("income_statement", {})
            periods = inc.get("periods", []) or []
            line_items = inc.get("line_items", []) or []

            # Extract key metrics from XBRL income statement
            metric_map = {
                "revenue": ["revenue", "net sales", "total revenue", "net revenue"],
                "cost_of_revenue": ["cost of revenue", "cost of goods sold", "cost of sales"],
                "gross_profit": ["gross profit"],
                "operating_income": ["operating income", "income from operations"],
                "net_income": ["net income"],
            }
            # Periods may be newest-first or newest-last; sort descending
            sorted_periods = sorted(periods, reverse=True)
            extracted: dict[str, dict[str, float | None]] = {}
            for item in line_items:
                label = (item.get("label", "") or "").lower()
                vals = item.get("values", {})
                for key, keywords in metric_map.items():
                    if key not in extracted and any(kw in label for kw in keywords):
                        row_vals: dict[str, float | None] = {}
                        for p in sorted_periods[:2]:  # Latest 2 fiscal years
                            raw_v = vals.get(p)
                            v = _sv(raw_v)
                            row_vals[p] = safe_float(v, None) if v is not None else None
                        extracted[key] = row_vals

            # Build annual rows with YoY change
            if sorted_periods and extracted:
                p_latest = sorted_periods[0] if sorted_periods else ""
                p_prior = sorted_periods[1] if len(sorted_periods) > 1 else ""

                for metric_key, display_label in [
                    ("revenue", "Revenue"),
                    ("gross_profit", "Gross Profit"),
                    ("operating_income", "Operating Income"),
                    ("net_income", "Net Income"),
                ]:
                    vals_dict = extracted.get(metric_key, {})
                    latest = vals_dict.get(p_latest)
                    prior = vals_dict.get(p_prior)
                    yoy = None
                    if latest is not None and prior is not None and prior != 0:
                        yoy = (latest - prior) / abs(prior) * 100

                    # Clean period labels: "FY2025" → "2025", "2025-09-27" → "2025"
                    def _fy_label(p: str) -> str:
                        return p.replace("FY", "")[:4] if p else ""

                    annual_rows.append(
                        {
                            "label": display_label,
                            "latest_period": _fy_label(p_latest),
                            "latest_value": fmt_large_number(latest),
                            "prior_period": _fy_label(p_prior),
                            "prior_value": fmt_large_number(prior),
                            "yoy_pct": f"{yoy:+.1f}%" if yoy is not None else "N/A",
                            "yoy_color": "#16A34A" if yoy is not None and yoy >= 0 else "#DC2626",
                        }
                    )

                # Add EPS from yfinance
                eps_ttm = info.get("trailingEps")
                eps_fwd = info.get("forwardEps")
                if eps_ttm is not None:
                    annual_rows.append(
                        {
                            "label": "EPS (TTM)",
                            "latest_period": "TTM",
                            "latest_value": f"${eps_ttm:.2f}",
                            "prior_period": "Fwd",
                            "prior_value": f"${eps_fwd:.2f}" if eps_fwd is not None else "N/A",
                            "yoy_pct": "",
                            "yoy_color": "#6B7280",
                        }
                    )

    result["annual"] = annual_rows

    # === QUARTERLY: Key P&L from yfinance_quarterly (5Q with QoQ) ===
    q_rows: list[dict[str, Any]] = []
    if state.extracted and state.extracted.financials:
        yq = state.extracted.financials.yfinance_quarterly or []
        yq_list = list(yq) if isinstance(yq, list) else []
        if yq_list:
            # Collect quarterly data for 5 most recent quarters
            q_data: list[dict[str, Any]] = []
            for q in yq_list[:5]:
                if isinstance(q, dict):
                    q_data.append(
                        {
                            "period": _format_quarter_label(q.get("period", "")),
                            "revenue": q.get("revenue"),
                            "gross_profit": q.get("gross_profit"),
                            "op_income": q.get("operating_income"),
                            "net_income": q.get("net_income"),
                            "eps": q.get("diluted_eps") or q.get("eps"),
                        }
                    )

            # Build row per metric across quarters
            for metric_key, display_label in [
                ("revenue", "Revenue"),
                ("gross_profit", "Gross Profit"),
                ("op_income", "Operating Income"),
                ("net_income", "Net Income"),
                ("eps", "EPS"),
            ]:
                row: dict[str, Any] = {"label": display_label, "quarters": []}
                for i, qd in enumerate(q_data):
                    val = qd.get(metric_key)
                    if metric_key == "eps":
                        formatted = f"${val:.2f}" if val is not None else "N/A"
                    else:
                        formatted = fmt_large_number(val)
                    # QoQ change (compare with next element = prior quarter)
                    qoq = None
                    if val is not None and i + 1 < len(q_data):
                        prior_val = q_data[i + 1].get(metric_key)
                        if prior_val is not None and prior_val != 0:
                            qoq = (val - prior_val) / abs(prior_val) * 100
                    row["quarters"].append(
                        {
                            "period": qd["period"],
                            "value": formatted,
                            "qoq_pct": f"{qoq:+.1f}%" if qoq is not None else "",
                            "qoq_color": "#16A34A" if qoq is not None and qoq >= 0 else "#DC2626",
                        }
                    )
                q_rows.append(row)

    result["quarterly"] = q_rows

    # === BALANCE SHEET: Key items (latest + YoY) ===
    bs_rows: list[dict[str, Any]] = []
    cash_val = info.get("totalCash")
    debt_val = info.get("totalDebt")
    ta_val = info.get("totalAssets")
    equity = info.get("totalStockholderEquity") or info.get("bookValue")
    net_debt = (debt_val - cash_val) if debt_val is not None and cash_val is not None else None

    for label, val in [
        ("Cash & Equivalents", cash_val),
        ("Total Debt", debt_val),
        ("Net Debt", net_debt),
        ("Total Assets", ta_val),
    ]:
        bs_rows.append(
            {
                "label": label,
                "value": fmt_large_number(val),
            }
        )

    result["balance_sheet"] = bs_rows

    return result


def _build_quarterly_balance(state: AnalysisState) -> list[dict[str, Any]]:
    """Build quarterly balance sheet trend table from acquired market data."""
    if not state.acquired_data or not state.acquired_data.market_data:
        return []
    md = state.acquired_data.market_data
    md_dict = _to_dict(md) if not isinstance(md, dict) else md
    qbs = md_dict.get("quarterly_balance_sheet", {})
    if not qbs or not isinstance(qbs, dict):
        return []
    periods = qbs.get("periods", []) or []
    items = qbs.get("line_items", {})
    if not periods or not isinstance(items, dict):
        return []

    # Key metrics to extract — label in data → display label
    key_metrics = [
        ("Total Assets", "Total Assets"),
        ("Total Liabilities Net Minority Interest", "Total Liabilities"),
        ("Stockholders Equity", "Stockholders Equity"),
        ("Total Debt", "Total Debt"),
        ("Net Debt", "Net Debt"),
        ("Cash And Cash Equivalents", "Cash"),
        ("Cash Cash Equivalents And Short Term Investments", "Cash & ST Investments"),
        ("Working Capital", "Working Capital"),
        ("Tangible Book Value", "Tangible Book Value"),
        ("Retained Earnings", "Retained Earnings"),
    ]

    result: list[dict[str, Any]] = []
    for data_label, display_label in key_metrics:
        vals = items.get(data_label)
        if not isinstance(vals, list) or not vals:
            continue
        row: dict[str, Any] = {"label": display_label, "cells": []}
        for i, p in enumerate(periods):
            v = vals[i] if i < len(vals) else None
            row["cells"].append(
                {
                    "period": _format_q_period(p),
                    "raw": v,
                    "display": fmt_large_number(v) if v is not None else "—",
                }
            )
        result.append(row)
    return result


def _build_quarterly_cashflow(state: AnalysisState) -> list[dict[str, Any]]:
    """Build quarterly cash flow trend table from acquired market data."""
    if not state.acquired_data or not state.acquired_data.market_data:
        return []
    md = state.acquired_data.market_data
    md_dict = _to_dict(md) if not isinstance(md, dict) else md
    qcf = md_dict.get("quarterly_cashflow", {})
    if not qcf or not isinstance(qcf, dict):
        return []
    periods = qcf.get("periods", []) or []
    items = qcf.get("line_items", {})
    if not periods or not isinstance(items, dict):
        return []

    key_metrics = [
        ("Operating Cash Flow", "Operating Cash Flow"),
        ("Free Cash Flow", "Free Cash Flow"),
        ("Capital Expenditure", "Capital Expenditure"),
        ("Net Income From Continuing Operations", "Net Income"),
        ("Depreciation And Amortization", "Depreciation & Amort."),
        ("Stock Based Compensation", "Stock-Based Comp"),
        ("Repurchase Of Capital Stock", "Share Buybacks"),
        ("Common Stock Dividend Paid", "Dividends Paid"),
        ("Financing Cash Flow", "Financing Cash Flow"),
        ("Investing Cash Flow", "Investing Cash Flow"),
    ]

    result: list[dict[str, Any]] = []
    for data_label, display_label in key_metrics:
        vals = items.get(data_label)
        if not isinstance(vals, list) or not vals:
            continue
        row: dict[str, Any] = {"label": display_label, "cells": []}
        for i, p in enumerate(periods):
            v = vals[i] if i < len(vals) else None
            row["cells"].append(
                {
                    "period": _format_q_period(p),
                    "raw": v,
                    "display": fmt_large_number(v) if v is not None else "—",
                }
            )
        result.append(row)
    return result


def _build_annual_income(state: AnalysisState) -> dict[str, Any] | None:
    """Build 3-year annual income statement comparison from XBRL data."""
    if not state.extracted or not state.extracted.financials:
        return None
    stmts = state.extracted.financials.statements
    if not stmts:
        return None
    sd = _to_dict(stmts)
    inc = sd.get("income_statement", {})
    periods = inc.get("periods", []) or []
    if not periods:
        return None

    # Key line items to show
    target_labels = [
        ("total revenue", "Revenue"),
        ("cost of revenue", "Cost of Revenue"),
        ("gross profit", "Gross Profit"),
        ("research and development", "R&D Expense"),
        ("selling, general and administrative", "SG&A Expense"),
        ("total operating expenses", "Total OpEx"),
        ("operating income", "Operating Income"),
        ("income tax expense", "Income Tax"),
        ("net income", "Net Income"),
        ("basic earnings per share", "EPS (Basic)"),
        ("diluted earnings per share", "EPS (Diluted)"),
        ("gross margin percentage", "Gross Margin %"),
        ("operating margin percentage", "Operating Margin %"),
        ("net margin percentage", "Net Margin %"),
        ("effective tax rate", "Effective Tax Rate"),
    ]

    rows: list[dict[str, Any]] = []
    for search_term, display_label in target_labels:
        for item in inc.get("line_items", []) or []:
            label_lower = (item.get("label", "") or "").lower()
            if search_term in label_lower:
                vals = item.get("values", {})
                row_vals: list[dict[str, Any]] = []
                prev_v: float | None = None
                for p in periods:
                    raw = vals.get(p)
                    v = _sv(raw) if isinstance(raw, dict) else raw
                    v_float = safe_float(v, None)
                    # Compute YoY change
                    yoy: str | None = None
                    if v_float is not None and prev_v is not None and prev_v != 0:
                        change_pct = (v_float - prev_v) / abs(prev_v) * 100
                        yoy = f"{change_pct:+.1f}%"
                    # Format display value
                    if "margin" in display_label.lower() or "tax rate" in display_label.lower():
                        display = f"{v_float:.1f}%" if v_float is not None else "—"
                    elif "eps" in display_label.lower():
                        display = f"${v_float:.2f}" if v_float is not None else "—"
                    else:
                        display = fmt_large_number(v_float) if v_float is not None else "—"
                    row_vals.append(
                        {
                            "period": p,
                            "display": display,
                            "yoy": yoy,
                            "yoy_color": _yoy_color(yoy, display_label),
                        }
                    )
                    prev_v = v_float
                rows.append({"label": display_label, "cells": row_vals})
                break

    if not rows:
        return None
    return {"periods": periods, "rows": rows}


def _build_xbrl_balance_highlights(state: AnalysisState) -> dict[str, Any] | None:
    """Build XBRL balance sheet key metrics with multi-year comparison."""
    if not state.extracted or not state.extracted.financials:
        return None
    stmts = state.extracted.financials.statements
    if not stmts:
        return None
    sd = _to_dict(stmts)
    bs = sd.get("balance_sheet", {})
    periods = bs.get("periods", []) or []
    if not periods:
        return None

    target_labels = [
        ("total assets", "Total Assets"),
        ("total liabilities", "Total Liabilities"),
        ("total stockholders", "Stockholders Equity"),
        ("cash and cash equivalents", "Cash & Equivalents"),
        ("total debt", "Total Debt"),
        ("long-term debt", "Long-Term Debt"),
        ("short-term debt", "Short-Term Debt"),
        ("accounts receivable", "Accounts Receivable"),
        ("inventory", "Inventory"),
        ("property, plant and equipment", "PP&E, net"),
        ("goodwill", "Goodwill"),
        ("retained earnings", "Retained Earnings"),
        ("total current assets", "Current Assets"),
        ("total current liabilities", "Current Liabilities"),
    ]

    rows: list[dict[str, Any]] = []
    for search_term, display_label in target_labels:
        for item in bs.get("line_items", []) or []:
            label_lower = (item.get("label", "") or "").lower()
            if search_term in label_lower:
                vals = item.get("values", {})
                row_vals: list[dict[str, Any]] = []
                prev_v: float | None = None
                for p in periods:
                    raw = vals.get(p)
                    v = _sv(raw) if isinstance(raw, dict) else raw
                    v_float = safe_float(v, None)
                    yoy: str | None = None
                    if v_float is not None and prev_v is not None and prev_v != 0:
                        change_pct = (v_float - prev_v) / abs(prev_v) * 100
                        yoy = f"{change_pct:+.1f}%"
                    row_vals.append(
                        {
                            "period": p,
                            "display": fmt_large_number(v_float) if v_float is not None else "—",
                            "yoy": yoy,
                            "yoy_color": _yoy_color(yoy, display_label),
                        }
                    )
                    prev_v = v_float
                rows.append({"label": display_label, "cells": row_vals})
                break

    if not rows:
        return None
    return {"periods": periods, "rows": rows}


def _format_q_period(date_str: str) -> str:
    """Convert '2025-12-31' to 'Q1 25' style label."""
    try:
        parts = date_str.split("-")
        year = parts[0][2:]  # '25'
        month = int(parts[1])
        # Calendar quarters: Jan-Mar=Q1, Apr-Jun=Q2, Jul-Sep=Q3, Oct-Dec=Q4
        q = (month - 1) // 3 + 1
        return f"Q{q} '{year}"
    except Exception:
        return date_str[:7] if len(date_str) >= 7 else date_str


def _yoy_color(yoy: str | None, label: str) -> str:
    """Return color for YoY change. Green for positive, red for negative (inverted for expenses/debt)."""
    if not yoy:
        return "#6B7280"
    # For cost/expense/debt/tax items, increase is bad (red)
    invert_labels = ("cost", "expense", "opex", "debt", "tax", "liabilities")
    is_inverted = any(term in label.lower() for term in invert_labels)
    is_positive = yoy.startswith("+")
    if is_inverted:
        return "#DC2626" if is_positive else "#16A34A"
    return "#16A34A" if is_positive else "#DC2626"


def _build_audit_alerts(state: AnalysisState) -> list[dict[str, str]]:
    """Extract audit disclosure alerts: restatements, auditor changes, MW, Q4 loading."""
    alerts: list[dict[str, str]] = []
    if not state.extracted or not state.extracted.financials:
        return alerts
    fin = _to_dict(state.extracted.financials)
    audit = fin.get("audit", {}) or {}
    # Restatement
    if audit.get("has_restatement"):
        alerts.append(
            {
                "type": "Restatement",
                "severity": "HIGH",
                "detail": audit.get("restatement_detail", "Restatement disclosed in filings"),
            }
        )
    # Auditor change
    if audit.get("auditor_change"):
        alerts.append(
            {
                "type": "Auditor Change",
                "severity": "HIGH",
                "detail": audit.get("auditor_change_detail", "Change in independent auditor"),
            }
        )
    # Material weakness
    if audit.get("material_weakness"):
        alerts.append(
            {
                "type": "Material Weakness",
                "severity": "HIGH",
                "detail": audit.get(
                    "material_weakness_detail", "Material weakness in ICFR disclosed"
                ),
            }
        )
    # Q4 revenue loading
    q4_pct = fin.get("q4_revenue_pct")
    if q4_pct and safe_float(q4_pct, 0) > 35:
        alerts.append(
            {
                "type": "Q4 Revenue Loading",
                "severity": "MEDIUM",
                "detail": f"Q4 = {q4_pct}% of annual revenue (>35% threshold)",
            }
        )
    return alerts


def _build_debt_maturity(state: AnalysisState) -> list[dict[str, Any]] | None:
    """Build debt maturity schedule bars from extracted data."""
    if not state.extracted or not state.extracted.financials:
        return None
    fin = _to_dict(state.extracted.financials)
    maturity = fin.get("debt_maturity", []) or []
    if not maturity:
        return None
    max_val = max(safe_float(m.get("amount", 0), 0) for m in maturity) or 1
    result = []
    for m in maturity[:8]:  # Max 8 years
        amt = safe_float(m.get("amount", 0), 0)
        result.append(
            {
                "year": m.get("year", ""),
                "amount": fmt_large_number(amt) if amt else "—",
                "bar_height": max(4, int(50 * amt / max_val)),
                "near_term": m.get("near_term", False),
            }
        )
    return result if result else None


def build_governance_context(state: AnalysisState) -> dict[str, Any]:
    """Build governance & leadership section context."""
    gov = {}
    if state.extracted and state.extracted.governance:
        gov = _to_dict(state.extracted.governance)

    board = gov.get("board", {}) or {}
    lead = gov.get("leadership", {}) or {}
    own = gov.get("ownership", {}) or {}
    comp = gov.get("comp_analysis", {}) or {}

    # Board
    board_size = _sv(board.get("size"))
    independence = _sv(board.get("independence_ratio"))
    avg_tenure = _sv(board.get("avg_tenure_years"))
    ceo_chair = _sv(board.get("ceo_chair_duality"))
    classified = _sv(board.get("classified_board"))
    gender_div = _sv(board.get("board_gender_diversity_pct"))
    meetings = _sv(board.get("board_meetings_held"))

    # ISS scores
    iss_overall = _sv(board.get("iss_overall_risk"))
    iss_board = _sv(board.get("iss_board_risk"))
    iss_comp = _sv(board.get("iss_compensation_risk"))
    iss_audit = _sv(board.get("iss_audit_risk"))
    iss_rights = _sv(board.get("iss_shareholder_rights_risk"))

    # Executives — merge DEF 14A extraction + yfinance officer data for richest detail
    execs_raw = lead.get("executives", []) or []
    # Build yfinance officer lookup by name fragment
    yf_officers = {}
    info = _get_yfinance_info(state)
    for o in info.get("companyOfficers", []) or []:
        if isinstance(o, dict) and o.get("name"):
            # Key by last name for fuzzy matching
            parts = o["name"].replace("Mr. ", "").replace("Ms. ", "").replace("Mrs. ", "").split()
            if parts:
                yf_officers[parts[-1].lower()] = o

    executives = []
    for e in execs_raw:
        name = _sv(e.get("name")) or ""
        title = _sv(e.get("title"))
        tenure = _sv(e.get("tenure_years"))
        total_comp = _sv(e.get("total_compensation"))
        age = None
        total_pay = None
        # Try matching to yfinance for age and comp
        name_parts = name.split()
        if name_parts:
            yf = yf_officers.get(name_parts[-1].lower(), {})
            age = yf.get("age")
            total_pay = yf.get("totalPay")
        executives.append(
            {
                "name": name or "N/A",
                "title": title or "N/A",
                "tenure": f"{tenure:.0f}yr" if tenure else "N/A",
                "age": age,
                "compensation": fmt_large_number(total_comp or total_pay)
                if (total_comp or total_pay)
                else "N/A",
            }
        )

    # Board forensics (directors)
    bf_raw = gov.get("board_forensics", []) or []
    directors = []
    for d in bf_raw:
        name = _sv(d.get("name"))
        tenure = _sv(d.get("tenure_years"))
        is_ind = _sv(d.get("is_independent"))
        role = _sv(d.get("committee_roles"))
        qual_tags = d.get("qualification_tags", []) or []
        age_raw = _sv(d.get("age"))
        age_val = int(age_raw) if age_raw else None
        # Extract other_boards — may be list of SourcedValue dicts or strings
        ob_raw = d.get("other_boards", []) or []
        other_boards: list[str] = []
        for ob in ob_raw:
            if isinstance(ob, dict) and "value" in ob:
                other_boards.append(str(ob["value"]))
            elif isinstance(ob, str):
                other_boards.append(ob)
        is_overboarded = bool(d.get("is_overboarded"))
        # Count total boards (this company + other boards)
        total_board_count = 1 + len(other_boards)
        directors.append(
            {
                "name": name or "N/A",
                "tenure": f"{tenure:.0f}yr" if tenure else "N/A",
                "independent": "Yes" if is_ind else ("No" if is_ind is False else "N/A"),
                "committees": (
                    role
                    if isinstance(role, str)
                    else (", ".join(role) if isinstance(role, list) else "N/A")
                ),
                "qualification_tags": qual_tags,
                "age": age_val,
                "other_boards": other_boards,
                "is_overboarded": is_overboarded,
                "total_board_count": total_board_count,
            }
        )

    # Board column-visibility flags — hide all-dash columns
    board_has_any_other_boards = any(bool(d.get("other_boards")) for d in directors)
    board_has_any_flags = any(d.get("is_overboarded") for d in directors)
    board_has_any_age = any(d.get("age") is not None for d in directors)

    # Ownership
    inst_pct = _sv(own.get("institutional_pct"))
    insider_pct = _sv(own.get("insider_pct"))
    top_holders = []
    for h in (own.get("top_holders", []) or [])[:5]:
        hv = _sv(h)
        if isinstance(hv, dict):
            top_holders.append(
                {
                    "name": hv.get("name", "N/A"),
                    "pct": f"{hv.get('pct_out', 0) * 100:.1f}%",
                    "shares": fmt_large_number(hv.get("shares")),
                }
            )

    # Compensation
    ceo_comp = _sv(comp.get("ceo_total_comp"))
    pay_ratio = _sv(comp.get("ceo_pay_ratio"))
    say_on_pay = _sv(comp.get("say_on_pay_pct"))
    has_clawback = _sv(comp.get("has_clawback"))

    # Departures
    departures = _sv(lead.get("departures_18mo"))

    # 5.5.3 Shareholder proposals
    shareholder_proposals = _sv(board.get("shareholder_proposal_count"))

    # 5.6.4 Clawback policy scope
    clawback_scope = _sv(comp.get("clawback_scope"))

    # 5.4.3 + 5.4.4 Ownership trajectories + exercise-sell events
    ownership_trajectory_count = 0
    exercise_sell_count = 0
    if state.extracted and state.extracted.market:
        ia = state.extracted.market.insider_analysis
        if ia:
            ia_dict = _to_dict(ia)
            ot = ia_dict.get("ownership_trajectories", {})
            ownership_trajectory_count = len(ot) if isinstance(ot, dict) else 0
            ese = ia_dict.get("exercise_sell_events", [])
            exercise_sell_count = len(ese) if isinstance(ese, list) else 0

    # ISS scores from yfinance info (fallback if not in governance YAML)
    yf_info = _get_yfinance_info(state)
    if iss_overall is None and yf_info.get("overallRisk") is not None:
        iss_overall = yf_info.get("overallRisk")
    if iss_board is None and yf_info.get("boardRisk") is not None:
        iss_board = yf_info.get("boardRisk")
    if iss_comp is None and yf_info.get("compensationRisk") is not None:
        iss_comp = yf_info.get("compensationRisk")
    if iss_audit is None and yf_info.get("auditRisk") is not None:
        iss_audit = yf_info.get("auditRisk")
    if iss_rights is None and yf_info.get("shareHolderRightsRisk") is not None:
        iss_rights = yf_info.get("shareHolderRightsRisk")

    # Governance summary from extracted data
    gov_summary_raw = _sv(gov.get("governance_summary"))
    governance_summary = ""
    if isinstance(gov_summary_raw, str):
        governance_summary = gov_summary_raw
    elif isinstance(gov_summary_raw, dict):
        governance_summary = gov_summary_raw.get("value", "") or ""

    # Governance score breakdown from extracted data
    gov_score_raw = gov.get("governance_score", {}) or {}
    total_score_raw = gov_score_raw.get("total_score")
    total_score_val = _sv(total_score_raw) if total_score_raw else None
    if isinstance(total_score_val, dict):
        total_score_val = total_score_val.get("value")
    gov_total_score = safe_float(total_score_val, None)
    gov_score_components = []
    component_labels = {
        "independence_score": "Independence",
        "ceo_chair_score": "CEO/Chair Separation",
        "refreshment_score": "Board Refreshment",
        "overboarding_score": "Overboarding",
        "committee_score": "Committee Quality",
        "say_on_pay_score": "Say-on-Pay",
        "tenure_score": "Tenure Balance",
    }
    for key, label in component_labels.items():
        val = safe_float(gov_score_raw.get(key), None)
        if val is not None:
            gov_score_components.append(
                {
                    "label": label,
                    "score": f"{val:.1f}",
                    "max": "10",
                    "pct": val / 10 * 100,
                    "color": "#16A34A" if val >= 7 else ("#D97706" if val >= 4 else "#DC2626"),
                }
            )

    # Narrative & commentary
    gov_narrative = ""
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        pcn_gov = _to_dict(state.analysis.pre_computed_narratives)
        gov_narrative = pcn_gov.get("governance", "") or ""
    commentary_factual, commentary_bullets = _get_commentary(state, "governance")

    # Section opener — data-driven governance context
    # Find chair name from directors
    chair_name = "N/A"
    for d in directors:
        if d.get("is_chair"):
            chair_name = d.get("name", "N/A")
            break
    # Find CEO tenure from executives
    ceo_tenure_years = "N/A"
    for ex in executives:
        title = (ex.get("title") or "").lower()
        if "ceo" in title or "chief executive" in title:
            t = ex.get("tenure")
            if t and t != "N/A":
                ceo_tenure_years = t
            break

    section_opener = _build_section_opener(
        "governance",
        state,
        {
            "board_size": str(board_size) if board_size else "N/A",
            "independence_ratio": f"{independence * 100:.0f}%" if independence else "N/A",
            "chair_name": chair_name,
            "ceo_tenure": ceo_tenure_years,
        },
    )

    return {
        "board_size": board_size or "N/A",
        "independence_ratio": f"{independence * 100:.0f}%" if independence else "N/A",
        "avg_board_tenure": f"{avg_tenure:.1f}yr" if avg_tenure else "N/A",
        "ceo_chair_duality": "Yes" if ceo_chair else ("No" if ceo_chair is False else "N/A"),
        "classified_board": "Yes" if classified else ("No" if classified is False else "N/A"),
        "gender_diversity": f"{gender_div:.0f}%" if gender_div else "N/A",
        "meetings_held": meetings or "N/A",
        "iss_overall": iss_overall,
        "iss_board": iss_board,
        "iss_comp": iss_comp,
        "iss_audit": iss_audit,
        "iss_rights": iss_rights,
        "governance_summary": governance_summary,
        "governance_total_score": f"{gov_total_score:.1f}"
        if gov_total_score is not None
        else None,
        "governance_score_components": gov_score_components,
        "executives": executives,
        "directors": directors,
        "board_has_any_other_boards": board_has_any_other_boards,
        "board_has_any_flags": board_has_any_flags,
        "board_has_any_age": board_has_any_age,
        "institutional_pct": f"{inst_pct:.1f}%" if inst_pct else "N/A",
        "insider_pct": f"{insider_pct:.1f}%" if insider_pct else "N/A",
        "top_holders": top_holders,
        "ceo_total_comp": fmt_large_number(ceo_comp) if ceo_comp else "N/A",
        "ceo_pay_ratio": f"{pay_ratio:.0f}:1" if pay_ratio else "N/A",
        "say_on_pay": f"{say_on_pay:.0f}%" if say_on_pay else "N/A",
        "has_clawback": "Yes" if has_clawback else ("No" if has_clawback is False else "N/A"),
        "departures_18mo": departures or 0,
        "shareholder_proposals": shareholder_proposals or 0,
        "clawback_scope": clawback_scope or "",
        "ownership_trajectory_count": ownership_trajectory_count,
        "exercise_sell_count": exercise_sell_count,
        "narrative": gov_narrative,
        "section_opener": section_opener,
        "commentary_factual": commentary_factual,
        "commentary_bullets": commentary_bullets,
        # CEO compensation breakdown
        "ceo_comp_breakdown": _build_ceo_comp_breakdown(comp),
        # Board forensic details (rich bios)
        "board_forensic_details": _build_board_forensic_details(bf_raw),
        # Board extra metrics
        "board_attendance": _sv(board.get("board_attendance_pct")),
        "below_75_attendance": _sv(board.get("directors_below_75_pct_attendance")),
        "poison_pill": _sv(board.get("poison_pill")),
        "supermajority_voting": _sv(board.get("supermajority_voting")),
        "blank_check_preferred": _sv(board.get("blank_check_preferred")),
        "forum_selection": _sv(board.get("forum_selection_clause")),
        "exclusive_forum": _sv(board.get("exclusive_forum_provision")),
        # Ownership detail
        "activist_risk": _sv(own.get("activist_risk_assessment")),
        "has_dual_class": _sv(own.get("has_dual_class")),
        # Leadership stability
        "stability_score": _sv(lead.get("stability_score")),
    }


def _build_ceo_comp_breakdown(comp: dict[str, Any]) -> dict[str, Any] | None:
    """Build CEO compensation breakdown from comp_analysis data."""
    total = safe_float(_sv(comp.get("ceo_total_comp")), None)
    if total is None:
        return None
    salary = safe_float(_sv(comp.get("ceo_salary")), 0)
    bonus = safe_float(_sv(comp.get("ceo_bonus")), 0)
    equity = safe_float(_sv(comp.get("ceo_equity")), 0)
    other = safe_float(_sv(comp.get("ceo_other")), 0)
    pay_ratio = safe_float(_sv(comp.get("ceo_pay_ratio")), None)
    say_on_pay = safe_float(_sv(comp.get("say_on_pay_pct")), None)
    has_clawback = _sv(comp.get("has_clawback"))
    clawback_scope = _sv(comp.get("clawback_scope"))

    # Build bar segments (as % of total)
    components = []
    for label, val, color in [
        ("Salary", salary, "#3B82F6"),
        ("Bonus/Incentive", bonus, "#10B981"),
        ("Equity", equity, "#8B5CF6"),
        ("Other", other, "#F59E0B"),
    ]:
        if val and total > 0:
            pct = val / total * 100
            components.append(
                {
                    "label": label,
                    "amount": fmt_large_number(val),
                    "pct": f"{pct:.1f}%",
                    "pct_raw": pct,
                    "color": color,
                }
            )

    return {
        "total": fmt_large_number(total),
        "components": components,
        "pay_ratio": f"{pay_ratio:.0f}:1" if pay_ratio else None,
        "say_on_pay": f"{say_on_pay:.0f}%" if say_on_pay else None,
        "has_clawback": "Yes" if has_clawback else ("No" if has_clawback is False else None),
        "clawback_scope": clawback_scope or None,
    }


def _build_board_forensic_details(bf_raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build rich board forensic detail list from board_forensics data."""
    details: list[dict[str, Any]] = []
    for d in bf_raw:
        name = _sv(d.get("name")) or "N/A"
        qualifications = _sv(d.get("qualifications")) or ""
        age = _sv(d.get("age"))
        tenure = _sv(d.get("tenure_years"))
        is_ind = _sv(d.get("is_independent"))
        committees = d.get("committees", []) or []
        other_boards_raw = d.get("other_boards", []) or []
        other_boards = [str(_sv(ob)) for ob in other_boards_raw if _sv(ob)]
        is_overboarded = d.get("is_overboarded", False)
        prior_lit = d.get("prior_litigation", []) or []
        interlocks = d.get("interlocks", []) or []
        relationship_flags = d.get("relationship_flags", []) or []
        true_independence = d.get("true_independence_concerns", []) or []
        qual_tags = d.get("qualification_tags", []) or []

        details.append(
            {
                "name": name,
                "qualifications": qualifications,
                "age": int(age) if age else None,
                "tenure": f"{tenure:.0f} years" if tenure else None,
                "independent": "Yes" if is_ind else ("No" if is_ind is False else "N/A"),
                "committees": committees,
                "other_boards": other_boards,
                "is_overboarded": is_overboarded,
                "prior_litigation": [_sv(pl) for pl in prior_lit] if prior_lit else [],
                "interlocks": interlocks,
                "relationship_flags": relationship_flags,
                "true_independence_concerns": true_independence,
                "qualification_tags": qual_tags,
            }
        )
    return details


def build_litigation_context(state: AnalysisState) -> dict[str, Any]:
    """Build legal & litigation section context."""
    lit = {}
    if state.extracted and state.extracted.litigation:
        lit = _to_dict(state.extracted.litigation)

    # SCAs — extract ALL available detail per manifest 6.1.1-6.1.13
    scas_raw = lit.get("securities_class_actions", []) or []
    scas = []
    for s in scas_raw:
        # Legal theories — list of SourcedValue strings
        theories_raw = _sv(s.get("legal_theories", []))
        theories = []
        if isinstance(theories_raw, list):
            for t in theories_raw:
                if isinstance(t, str):
                    theories.append(t)
                elif isinstance(t, dict) and "value" in t:
                    theories.append(t["value"])
        # Named defendants
        defendants_raw = _sv(s.get("named_defendants", []))
        defendants = []
        if isinstance(defendants_raw, list):
            for d in defendants_raw:
                if isinstance(d, str):
                    defendants.append(d)
                elif isinstance(d, dict) and "value" in d:
                    defendants.append(d["value"])
        # Format settlement amount as currency
        settle_raw = _sv(s.get("settlement_amount"))
        settlement_display = ""
        if settle_raw is not None:
            try:
                amt = float(settle_raw)
                if amt >= 1e9:
                    settlement_display = f"${amt / 1e9:.1f}B"
                elif amt >= 1e6:
                    settlement_display = f"${amt / 1e6:.1f}M"
                elif amt > 0:
                    settlement_display = f"${amt:,.0f}"
            except (ValueError, TypeError):
                pass

        scas.append(
            {
                "case_name": _sv(s.get("case_name")) or "N/A",
                "status": _sv(s.get("status")) or "N/A",
                "court": _sv(s.get("court")) or "N/A",
                "filing_date": _sv(s.get("filing_date")) or "N/A",
                "allegations": _format_allegations(s),
                "legal_theories": theories,
                "class_period_start": _sv(s.get("class_period_start")) or "",
                "class_period_end": _sv(s.get("class_period_end")) or "",
                "docket_number": _sv(s.get("docket_number")) or "",
                "named_defendants": defendants,
                "lead_counsel": _sv(s.get("lead_counsel")) or "",
                "procedural_posture": _sv(s.get("procedural_posture")) or "",
                "damages_claimed": _sv(s.get("damages_claimed")) or "",
                "settlement_amount": settlement_display,
                "case_duration": "",  # TODO: compute from filing_date + resolution_date
            }
        )

    # Derivative suits — filter ghost entries (no case name, date, or court)
    derivs = lit.get("derivative_suits", []) or []
    deriv_cases = []
    for d in derivs:
        case_name = _sv(d.get("case_name")) or ""
        filing_date = _sv(d.get("filing_date")) or ""
        court = _sv(d.get("court")) or ""
        # Skip ghost suits with no meaningful identifiers
        has_name = case_name not in ("", "N/A", "Unknown")
        has_date = filing_date not in ("", "N/A")
        has_court = court not in ("", "N/A")
        if not has_name and not has_date and not has_court:
            continue
        deriv_cases.append(
            {
                "case_name": case_name or "N/A",
                "status": _sv(d.get("status")) or "N/A",
                "filing_date": filing_date or "N/A",
            }
        )

    # Regulatory — may be SourcedValue dicts with nested value
    regs = lit.get("regulatory_proceedings", []) or []
    reg_cases = []
    for r in regs if isinstance(regs, list) else []:
        rv = _sv(r)  # unwrap SourcedValue
        if isinstance(rv, dict):
            name = rv.get("agency") or rv.get("agency_name") or "N/A"
            status = rv.get("status") or "N/A"
            desc = rv.get("description") or ""
            if name and name != "N/A":
                reg_cases.append({"agency": name, "status": status, "description": desc})
        elif isinstance(rv, str) and rv:
            reg_cases.append({"agency": rv, "status": "N/A", "description": ""})

    # SEC enforcement — may be dict or list
    sec_raw = lit.get("sec_enforcement", []) or []
    sec_cases = []
    if isinstance(sec_raw, dict):
        # Single enforcement dict — wrap as list for uniform handling
        sec_raw = [sec_raw] if sec_raw else []
    for s in sec_raw if isinstance(sec_raw, list) else []:
        if isinstance(s, str):
            sec_cases.append({"action_type": s, "status": "N/A", "description": ""})
        elif isinstance(s, dict):
            sec_cases.append(
                {
                    "action_type": _sv(s.get("action_type")) or "N/A",
                    "status": _sv(s.get("status")) or "N/A",
                    "description": _sv(s.get("description")) or "",
                }
            )

    # 6.3.3 Industry sweep detection
    sec_enf = lit.get("sec_enforcement", {})
    if isinstance(sec_enf, dict):
        sweep_raw = _sv(sec_enf.get("industry_sweep_detected"))
    else:
        sweep_raw = False
    industry_sweep = bool(sweep_raw) if sweep_raw is not None else False

    # Summary stats — may be SourcedValue dicts
    active_count_raw = lit.get("active_matter_count", 0)
    active_count = (
        _sv(active_count_raw) if isinstance(active_count_raw, dict) else active_count_raw
    )
    active_count = int(active_count) if active_count else 0
    hist_raw = lit.get("historical_matter_count", 0)
    historical_count = _sv(hist_raw) if isinstance(hist_raw, dict) else hist_raw
    historical_count = int(historical_count) if historical_count else 0
    total_reserve = _sv(lit.get("total_litigation_reserve"))
    summary = _sv(lit.get("litigation_summary")) or ""

    # Narrative & commentary
    lit_narrative = ""
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        pcn_lit = _to_dict(state.analysis.pre_computed_narratives)
        lit_narrative = pcn_lit.get("litigation", "") or ""
    commentary_factual, commentary_bullets = _get_commentary(state, "litigation")

    # SOL window count for opener
    sol_count = 0
    sol_map_raw = lit.get("sol_map")
    sol_windows: list[dict[str, Any]] = []
    if sol_map_raw:
        # sol_map may be a list of window dicts or a dict with "windows" key
        if isinstance(sol_map_raw, list):
            sol_items = sol_map_raw
        else:
            sol_map_d = _to_dict(sol_map_raw) if not isinstance(sol_map_raw, dict) else sol_map_raw
            sol_items = sol_map_d.get("windows", []) or []
        sol_count = len(sol_items)
        for sw in sol_items:
            claim = _sv(sw.get("claim_type")) or "Unknown"
            sol_yrs = safe_float(_sv(sw.get("sol_years")), 0)
            repose_yrs = safe_float(_sv(sw.get("repose_years")), 0)
            sol_open = bool(_sv(sw.get("sol_open")))
            repose_open = bool(_sv(sw.get("repose_open")))
            sol_expiry = _sv(sw.get("sol_expiry")) or ""
            repose_expiry = _sv(sw.get("repose_expiry")) or ""
            sol_windows.append(
                {
                    "claim_type": str(claim).replace("_", " "),
                    "sol_years": sol_yrs,
                    "repose_years": repose_yrs,
                    "sol_open": sol_open,
                    "repose_open": repose_open,
                    "sol_expiry": str(sol_expiry)[:10],
                    "repose_expiry": str(repose_expiry)[:10],
                }
            )
        # Sort by repose years descending for visual impact
        sol_windows.sort(key=lambda x: x["repose_years"], reverse=True)

    # Case status counts for status summary visualization
    all_cases = scas + deriv_cases + sec_cases + reg_cases
    status_active = sum(
        1 for c in all_cases if c.get("status", "").upper() in ("ACTIVE", "PENDING")
    )
    status_settled = sum(1 for c in all_cases if c.get("status", "").upper() == "SETTLED")
    status_dismissed = sum(1 for c in all_cases if c.get("status", "").upper() == "DISMISSED")
    status_appeal = sum(1 for c in all_cases if c.get("status", "").upper() == "APPEAL")
    status_other = (
        len(all_cases) - status_active - status_settled - status_dismissed - status_appeal
    )

    # Section opener — data-driven litigation context
    section_opener = _build_section_opener(
        "litigation",
        state,
        {
            "active_matter_count": active_count,
            "historical_matter_count": historical_count,
            "sol_window_count": sol_count,
        },
    )

    # Contingent liabilities — unwrap SourcedValues for template display
    cont_raw = lit.get("contingent_liabilities", []) or []
    contingent_items: list[dict[str, str]] = []
    for c in cont_raw if isinstance(cont_raw, list) else []:
        desc = _sv(c.get("description") if isinstance(c, dict) else c) or ""
        classification = (
            _sv(c.get("asc_450_classification") if isinstance(c, dict) else None) or ""
        )
        source_note = _sv(c.get("source_note") if isinstance(c, dict) else None) or ""
        contingent_items.append(
            {
                "description": str(desc),
                "classification": str(classification) if classification else "Reasonably Possible",
                "amount_range": "—",
                "source": str(source_note),
            }
        )

    return {
        "scas": scas,
        "derivative_suits": deriv_cases,
        "regulatory_proceedings": reg_cases,
        "sec_enforcement": sec_cases,
        "contingent_liabilities": contingent_items,
        "active_matter_count": active_count,
        "historical_matter_count": historical_count,
        "total_reserve": fmt_large_number(total_reserve) if total_reserve else "N/A",
        "litigation_summary": summary,
        "industry_sweep": industry_sweep,
        "narrative": lit_narrative,
        "section_opener": section_opener,
        "commentary_factual": commentary_factual,
        "commentary_bullets": commentary_bullets,
        "sol_windows": sol_windows,
        "status_active": status_active,
        "status_settled": status_settled,
        "status_dismissed": status_dismissed,
        "status_appeal": status_appeal,
        "status_other": status_other,
        "total_cases": len(all_cases),
    }


def build_scoring_context(state: AnalysisState) -> dict[str, Any]:
    """Build scoring & risk profile section context."""
    scoring = _get_scoring(state)
    factors = scoring.get("factor_scores", [])

    factor_rows = []
    for f in factors:
        fid = f.get("factor_id", "")
        name = f.get("factor_name", fid)
        pts = safe_float(f.get("points_deducted", 0), 0)
        mx = safe_float(f.get("max_points", 1), 1)
        pct = (pts / mx * 100) if mx > 0 else 0
        ev = f.get("evidence", [])
        evidence_text = _first_meaningful_evidence(ev)
        # Triggered signals count
        sigs = f.get("signal_contributions", [])
        triggered = sum(1 for s in sigs if s.get("status") == "TRIGGERED")
        total_sigs = len(sigs)

        # If no meaningful evidence, summarize from triggered signal names
        if not evidence_text and triggered > 0:
            triggered_names = [
                s.get("signal_id", "").split(".")[-1].replace("_", " ")
                for s in sigs
                if s.get("status") == "TRIGGERED"
            ][:4]
            if triggered_names:
                # Human-readable: list the risk areas found, not signal counts
                evidence_text = "Risk areas identified: " + ", ".join(triggered_names)
                if triggered > 4:
                    evidence_text += f" (+{triggered - 4} more)"

        factor_rows.append(
            {
                "factor_id": fid,
                "name": name,
                "points": f"{pts:.1f}",
                "max_points": f"{mx:.0f}",
                "pct": pct,
                "bar_color": "#DC2626" if pct >= 30 else ("#F59E0B" if pct >= 10 else "#16A34A"),
                "evidence": evidence_text,
                "triggered_signals": triggered,
                "total_signals": total_sigs,
            }
        )

    qs = safe_float(scoring.get("quality_score"), 0)
    trp = safe_float(scoring.get("total_risk_points"), 0)
    tier_info = scoring.get("tier", {})
    tier_name = tier_info.get("tier", "?") if isinstance(tier_info, dict) else "?"

    # Red flags
    red_flags = scoring.get("red_flags", []) or []
    rf_list = []
    for rf in red_flags:
        if rf.get("triggered"):
            rf_list.append(
                {
                    "name": rf.get("flag_name", ""),
                    "evidence": rf.get("evidence", []),
                    "max_tier": rf.get("max_tier", ""),
                    "ceiling": rf.get("ceiling_applied", ""),
                }
            )

    # Narrative & commentary
    score_narrative = ""
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        pcn_sc = _to_dict(state.analysis.pre_computed_narratives)
        score_narrative = pcn_sc.get("scoring", "") or ""
    commentary_factual, commentary_bullets = _get_commentary(state, "scoring")

    return {
        "factor_rows": factor_rows,
        "quality_score": f"{qs:.1f}",
        "total_risk_points": f"{trp:.1f}",
        "tier_name": tier_name,
        "tier_color": _TIER_COLORS.get(tier_name, "#6B7280"),
        "red_flags": rf_list,
        "narrative": score_narrative,
        "commentary_factual": commentary_factual,
        "commentary_bullets": commentary_bullets,
    }


def build_questions_context(state: AnalysisState) -> list[dict[str, Any]]:
    """Build management questions section context."""
    pcn = {}
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        n = state.analysis.pre_computed_narratives
        pcn = _to_dict(n)

    raw = pcn.get("meeting_prep_questions", []) or []
    questions = []
    for i, q in enumerate(raw):
        text = (
            q
            if isinstance(q, str)
            else (q.get("question", str(q)) if isinstance(q, dict) else str(q))
        )
        # Clean up quoted strings
        text = text.strip().strip('"').strip("'")
        # Infer topic from content
        topic = _infer_topic(text)
        questions.append(
            {
                "number": i + 1,
                "text": text,
                "topic": topic,
                "priority": "HIGH" if i < 4 else ("MEDIUM" if i < 8 else "STANDARD"),
            }
        )
    return questions


def _infer_topic(text: str) -> str:
    """Infer question topic from content keywords."""
    t = text.lower()
    for topic, kws in [
        ("Litigation", ("litigation", "class action", "sca", "lawsuit", "settlement")),
        ("Financial", ("revenue", "margin", "financial", "earnings", "ebitda")),
        ("Governance", ("governance", "board", "director", "compensation")),
        ("Market", ("stock", "share", "buyback", "insider")),
        ("Regulatory", ("regulatory", "sec", "compliance", "investigation")),
        ("Cyber/Privacy", ("cyber", "data", "privacy", "breach")),
    ]:
        if any(w in t for w in kws):
            return topic
    return "General"


def _get_commentary(state: AnalysisState, section_key: str) -> tuple[str, str]:
    """Extract dual-voice commentary for a section. Returns (factual, bullets)."""
    if not state.analysis or not hasattr(state.analysis, "pre_computed_commentary"):
        return ("", "")
    pcc = state.analysis.pre_computed_commentary
    if not pcc:
        return ("", "")
    pcc_dict = _to_dict(pcc) if not isinstance(pcc, dict) else pcc
    section = pcc_dict.get(section_key, {})
    if not section or not isinstance(section, dict):
        return ("", "")
    factual = section.get("what_was_said", "") or ""
    bullets = section.get("underwriting_commentary", "") or ""
    return (factual, bullets)


def _extract_goodwill_from_xbrl(state: AnalysisState) -> Any:
    """Extract Goodwill from XBRL balance sheet line items."""
    try:
        stmts = state.extracted.financials.statements  # type: ignore[union-attr]
        if not stmts:
            return None
        sd = _to_dict(stmts)
        bs = sd.get("balance_sheet", {})
        for item in bs.get("line_items", []) or []:
            label = (item.get("label", "") or "").lower()
            if label in ("goodwill", "goodwill and other intangible assets"):
                vals = item.get("values", {})
                # Return most recent period value
                periods = bs.get("periods", []) or []
                for p in periods:
                    v = _sv(vals.get(p))
                    if v is not None:
                        return safe_float(v, None)
    except Exception:
        pass
    return None


def _structure_company_narrative(raw: str) -> dict[str, Any]:
    """Parse a pre-computed company narrative into structured components.

    Returns dict with:
      overview: str -- what the company does (first 1-2 sentences)
      revenue_model: str -- how the money flows
      risk_profile: str -- D&O-specific risks and exposure
    """
    import re

    if not raw:
        return {}

    # Strip markdown headers and bold markers
    text = re.sub(r"^#+ .+\n?", "", raw, flags=re.MULTILINE).strip()

    # Split on sentence boundaries (avoid splitting on Inc., Corp., Ltd., etc.)
    sentences = re.split(r"(?<=[^A-Z][.!?])\s+(?=[A-Z])", text)
    if not sentences:
        return {}

    # Revenue/money flow keywords (primary)
    revenue_primary_kw = (
        "business model",
        "hardware business",
        "services revenue",
        "product sales",
        "recurring",
        "subscription",
        "earnings contribution",
        "margin compression",
        "capital allocation",
        "iphone-dependent",
        "revenue model",
    )
    # Revenue secondary (only if no risk keywords dominate)
    revenue_secondary_kw = (
        "revenue",
        "iphone",
        "segment",
        "margin",
    )
    # D&O risk keywords
    risk_kw = (
        "litigation",
        "regulatory",
        "enforcement",
        "d&o",
        "director",
        "fiduciary",
        "shareholder",
        "derivative",
        "sec enforcement",
        "doj",
        "settlement",
        "claims",
        "patent disputes",
        "antitrust",
        "employment litigation",
        "wage",
        "fines exceeding",
        "injunction",
    )

    overview_parts: list[str] = []
    revenue_parts: list[str] = []
    risk_parts: list[str] = []

    for s in sentences:
        s_lower = s.lower()
        # First sentence always goes to overview
        if not overview_parts:
            overview_parts.append(s)
            continue

        has_revenue_primary = any(k in s_lower for k in revenue_primary_kw)
        has_revenue_secondary = any(k in s_lower for k in revenue_secondary_kw)
        has_risk = any(k in s_lower for k in risk_kw)

        if has_revenue_primary:
            # Revenue primary keywords take priority — even if risk keywords present
            revenue_parts.append(s)
        elif has_risk:
            risk_parts.append(s)
        elif has_revenue_secondary:
            revenue_parts.append(s)
        elif len(" ".join(overview_parts)) < 300:
            overview_parts.append(s)
        else:
            risk_parts.append(s)

    return {
        "overview": " ".join(overview_parts).strip(),
        "revenue_model": " ".join(revenue_parts).strip(),
        "risk_profile": " ".join(risk_parts).strip(),
    }


def _build_section_opener(
    section: str,
    state: AnalysisState,
    context_data: dict[str, Any],
) -> str:
    """Build a data-driven analytical opener for a section.

    Returns 2-4 sentences: data summary + D&O risk interpretation.
    The D&O sentence connects section data to specific underwriting
    implications using company context (sector, size, scoring).
    """
    info = _get_yfinance_info(state)
    ticker = state.ticker or "?"

    if section == "stock_market":
        # Build from market data
        price = info.get("currentPrice") or info.get("previousClose")
        h52 = info.get("fiftyTwoWeekHigh")
        pe = info.get("trailingPE")
        sp = info.get("shortPercentOfFloat")
        num_analysts = info.get("numberOfAnalystOpinions")
        rec_key = info.get("recommendationKey", "").upper()

        parts: list[str] = []
        if price and h52:
            pct_from_high = (1 - price / h52) * 100
            parts.append(
                f"{ticker} trades at ${price:,.0f} "
                f"({pct_from_high:.0f}% below 52-week high of ${h52:,.0f})"
            )
        if pe:
            parts.append(f"with a trailing P/E of {pe:.1f}x")
        opener = " ".join(parts[:2]) + "." if parts else ""

        extras: list[str] = []
        if sp is not None:
            extras.append(
                f"Short interest is {'minimal' if sp < 0.03 else 'elevated'} at {sp * 100:.1f}%"
            )
        if num_analysts and rec_key:
            extras.append(
                f"The {rec_key} consensus from {num_analysts} analysts suggests {'strong' if rec_key == 'BUY' else 'mixed'} market confidence"
            )
        if extras:
            opener += " " + ". ".join(extras) + "."
        do_risk = _build_do_risk_sentence(section, state, context_data)
        if do_risk:
            opener += " " + do_risk
        return opener

    elif section == "financial":
        rev = context_data.get("revenue", "")
        ni = context_data.get("net_income", "")
        rev_growth = context_data.get("rev_growth", "")
        beneish_zone = context_data.get("beneish_zone", "")
        altman_zone = context_data.get("altman_zone", "")

        parts = []
        if rev and rev != "N/A":
            growth_str = f" ({rev_growth})" if rev_growth and rev_growth != "N/A" else ""
            parts.append(f"{ticker} generated {rev} revenue{growth_str}")
        if ni and ni != "N/A":
            parts.append(f"with {ni} net income")
        opener = " ".join(parts[:2]) + "." if parts else ""

        forensic_parts: list[str] = []
        if beneish_zone:
            forensic_parts.append(f"Beneish M-Score in {beneish_zone} zone")
        if altman_zone:
            forensic_parts.append(f"Altman Z-Score in {altman_zone} zone")
        if forensic_parts:
            opener += " Forensic analysis: " + ", ".join(forensic_parts) + "."
        do_risk = _build_do_risk_sentence(section, state, context_data)
        if do_risk:
            opener += " " + do_risk
        return opener

    elif section == "governance":
        board_size = context_data.get("board_size", "")
        independence = context_data.get("independence_ratio", "")
        ceo_tenure = context_data.get("ceo_tenure", "")

        parts: list[str] = []
        if board_size and board_size != "N/A":
            ind_str = (
                f" ({independence} independent)" if independence and independence != "N/A" else ""
            )
            parts.append(f"{ticker}'s board of {board_size} directors{ind_str}")
        opener = " ".join(parts) + "." if parts else ""

        if ceo_tenure and ceo_tenure != "N/A":
            # ceo_tenure may be "15yr" or "15" — normalize display
            tenure_str = str(ceo_tenure).replace("yr", "").strip()
            opener += f" CEO tenure of {tenure_str} years is a key personnel continuity factor."
        do_risk = _build_do_risk_sentence(section, state, context_data)
        if do_risk:
            opener += " " + do_risk
        return opener

    elif section == "litigation":
        active = context_data.get("active_matter_count", 0)
        historical = context_data.get("historical_matter_count", 0)
        sol_windows = context_data.get("sol_window_count", 0)

        parts = []
        if active > 0:
            parts.append(f"{ticker} faces {active} active legal matter{'s' if active > 1 else ''}")
        else:
            parts.append(f"{ticker} has no active securities class actions")
        if historical > 0:
            parts.append(
                f"{historical} historical matter{'s' if historical > 1 else ''} establish litigation precedent"
            )
        opener = ". ".join(parts) + "." if parts else ""

        if sol_windows and sol_windows > 0:
            opener += f" {sol_windows} statute of limitations windows remain open for potential new claims."
        do_risk = _build_do_risk_sentence(section, state, context_data)
        if do_risk:
            opener += " " + do_risk
        return opener

    return ""


def _build_do_risk_sentence(
    section: str,
    state: AnalysisState,
    context_data: dict[str, Any],
) -> str:
    """Generate a D&O risk interpretation sentence for a section opener.

    Connects section data to specific D&O underwriting implications,
    using company context (sector, size, scoring) to make it specific.
    """
    ticker = state.ticker or "?"
    sector = ""
    mcap_tier = ""
    if state.company and state.company.identity:
        sv = state.company.identity.sector
        if sv:
            sector = sv.value if hasattr(sv, "value") else str(sv)
    if state.company and state.company.market_cap:
        sv = state.company.market_cap
        mcap = sv.value if hasattr(sv, "value") else sv
        if mcap:
            try:
                m = float(mcap)
                if m >= 200e9:
                    mcap_tier = "mega-cap"
                elif m >= 10e9:
                    mcap_tier = "large-cap"
                elif m >= 2e9:
                    mcap_tier = "mid-cap"
                else:
                    mcap_tier = "small-cap"
            except (ValueError, TypeError):
                pass

    score = None
    tier = None
    if state.scoring:
        score = state.scoring.composite_score
        if state.scoring.tier:
            tier = state.scoring.tier.tier

    if section == "financial":
        if sector in ("TECH", "COMM") and mcap_tier in ("mega-cap", "large-cap"):
            return (
                f"For a {mcap_tier} {sector.lower()} company, standard financial distress "
                f"indicators carry reduced weight — asset-light models structurally "
                f"produce metrics that would concern a traditional industrial underwriter."
            )
        if sector == "BIOT":
            return (
                "For biotech companies, cash runway relative to the next clinical "
                "catalyst is the critical financial metric — traditional profitability "
                "measures are secondary."
            )
        return ""

    if section == "governance":
        if mcap_tier in ("mega-cap", "large-cap"):
            return (
                "Large-company governance benefits from institutional shareholder "
                "oversight and proxy advisor scrutiny, but Caremark duty-of-oversight "
                "claims remain the primary governance D&O exposure."
            )
        if mcap_tier in ("small-cap", "micro-cap"):
            return (
                "Small-company governance warrants heightened scrutiny — limited "
                "institutional oversight, concentrated insider ownership, and fewer "
                "independent directors increase entrenchment and Caremark claim risk."
            )
        return ""

    if section == "litigation":
        active = context_data.get("active_matter_count", 0)
        if active > 0:
            return (
                "Active litigation is the single strongest predictor of future D&O "
                "claims — prior SCA plaintiffs and counsel are familiar with the "
                "company's disclosure practices and management team."
            )
        sol_windows = context_data.get("sol_window_count", 0)
        if sol_windows and sol_windows > 3:
            return (
                f"With {sol_windows} open statute of limitations windows, the company "
                f"faces material backward-looking exposure even without active suits."
            )
        return ""

    if section == "stock_market":
        if score and score > 85:
            return (
                f"With a quality score of {score:.0f}, market metrics are consistent "
                f"with a favorable risk profile — but stock decline remains the "
                f"primary trigger mechanism for securities class actions."
            )
        if score and score < 60:
            return (
                f"The quality score of {score:.0f} combined with market indicators "
                f"suggests elevated loss causation exposure under Dura Pharmaceuticals."
            )
        return ""

    return ""


def _build_risk_profile_card(
    business_description: str,
    revenue_model_type: str,
    customer_concentration: list[dict[str, Any]],
    supplier_concentration: list[dict[str, Any]],
    geographic_footprint: list[dict[str, Any]],
    do_exposure_factors: list[dict[str, Any]],
    state: AnalysisState | None = None,
) -> dict[str, Any]:
    """Build a concise risk profile answering what/how/where/why."""
    # What does the company do? — first sentence of business description
    what = ""
    if business_description:
        import re

        # Split on sentence boundaries (avoid splitting on Inc., Corp., Ltd., etc.)
        sents = re.split(r"(?<=[^A-Z][.!?])\s+(?=[A-Z])", business_description)
        what = sents[0].rstrip(".") + "." if sents else business_description[:200]
        # Ensure reasonable length
        if len(what) > 300:
            what = what[:300].rsplit(" ", 1)[0] + "..."

    # How does the money flow? — revenue model type badge
    how = revenue_model_type or ""

    # Where is the concentration risk?
    concentration: list[str] = []
    for cc in (customer_concentration or [])[:2]:
        name = cc.get("customer", "")
        pct = cc.get("revenue_pct", "")
        if name:
            s = name[:80]
            if pct and str(pct) != "0" and str(pct) != "0.0":
                s += f" ({pct}%)"
            concentration.append(s)
    for sc in (supplier_concentration or [])[:2]:
        name = sc.get("supplier", "")
        if name:
            concentration.append(name[:80])
    # Geographic concentration
    non_us = [
        g for g in (geographic_footprint or []) if "america" not in g.get("region", "").lower()
    ]
    if len(non_us) >= 3:
        intl_pcts = [g.get("percentage", "") for g in non_us[:3]]
        concentration.append(
            f"International: {', '.join(g.get('region', '') for g in non_us[:3])}"
        )

    # D&O triggers
    triggers: list[str] = []
    for ef in (do_exposure_factors or [])[:4]:
        reason = ef.get("reason", "")
        factor = ef.get("factor", "")
        label = reason if reason else factor.replace("_", " ").title()
        if label:
            triggers.append(label)

    # Litigation target profile — why this company is a D&O target
    litigation_target: list[str] = []
    if state:
        info = _get_yfinance_info(state)
        mcap = info.get("marketCap")
        employees = info.get("fullTimeEmployees")
        # Market cap as damages pool
        if mcap and mcap > 100e9:
            from do_uw.stages.render.context_builders.uw_analysis_infographics import (
                fmt_large_number,
            )

            litigation_target.append(
                f"{fmt_large_number(mcap)} market cap = maximum plaintiff damages pool"
            )
        # Employee count as employment litigation surface
        if employees and employees > 10000:
            # Count jurisdictions from geographic footprint
            jur_count = len(geographic_footprint) if geographic_footprint else 0
            emp_str = f"{employees:,} employees"
            if jur_count > 1:
                emp_str += f" across {jur_count}+ jurisdictions"
            litigation_target.append(f"{emp_str} = broad employment litigation surface")
        # Stakeholder count (customers, developers, etc.) from business description
        if business_description:
            import re as _re

            # Look for large stakeholder numbers in the description
            stakeholder_matches = _re.findall(
                r"(\d+[\d,]*\s*(?:million|billion|M|B)?\+?\s*(?:developer|customer|user|subscriber|member|merchant|partner|seller|vendor)s?)",
                business_description,
                _re.IGNORECASE,
            )
            if stakeholder_matches:
                litigation_target.append(
                    f"{stakeholder_matches[0]} = large stakeholder count for class certification"
                )

    return {
        "what": what,
        "how": how,
        "concentration": concentration[:4],
        "triggers": triggers[:5],
        "litigation_target": litigation_target[:3],
    }


def build_company_context(state: AnalysisState) -> dict[str, Any]:
    """Build company operations section context (Section 2 items)."""
    comp = {}
    if state.company:
        comp = _to_dict(state.company)

    # 2.2.3 Revenue model type — short label for badge, full text as description
    rmt_raw = _sv(comp.get("revenue_model_type")) or ""
    rmt_full = rmt_raw  # Keep full text for split parsing
    if isinstance(rmt_raw, str) and " - " in rmt_raw:
        revenue_model_type = rmt_raw.split(" - ")[0].strip()  # "HYBRID" not full paragraph
    else:
        revenue_model_type = rmt_raw

    # Parse revenue model split from full description (e.g., "~74% of revenue" for products)
    revenue_model_split: list[dict[str, Any]] = []
    if isinstance(rmt_full, str):
        # Pattern: "product sales (... representing ~74% of revenue)"
        # Capture the 1-3 words immediately before the parenthesized block
        pct_matches = re.findall(
            r"(\w+(?:\s+\w+){0,2})\s*\([^)]*?~?(\d+)%\s+of\s+revenue\)",
            rmt_full,
            re.IGNORECASE,
        )
        for label, pct in pct_matches:
            clean_label = re.sub(
                r"^(?:of|and|a|the|mix|recurring)\s+", "", label.strip(), flags=re.IGNORECASE
            )
            if clean_label:
                # Shorten "Services Revenue" -> "Services", "Product Sales" -> "Products"
                short = clean_label.title()
                short = re.sub(r"\s+(Sales|Revenue|Income)$", "", short, flags=re.IGNORECASE)
                if not short:
                    short = clean_label.title()
                revenue_model_split.append({"label": short, "pct": int(pct)})
        # Fallback: just extract all percentages
        if not revenue_model_split and "%" in rmt_full:
            simple_pcts = re.findall(r"~?(\d+)%", rmt_full)
            if len(simple_pcts) == 2:
                revenue_model_split = [
                    {"label": "Products", "pct": int(simple_pcts[0])},
                    {"label": "Services", "pct": int(simple_pcts[1])},
                ]

    # 2.3.5 + 2.3.6 Segment lifecycle + margins
    seg_lifecycle_raw = comp.get("segment_lifecycle", []) or []
    seg_lifecycle = []
    for sl in seg_lifecycle_raw:
        v = _sv(sl)
        if isinstance(v, dict):
            rev_amt = v.get("revenue_amount") or v.get("revenue")
            seg_lifecycle.append(
                {
                    "name": v.get("name", "N/A"),
                    "stage": v.get("stage", "N/A"),
                    "growth_rate": v.get("growth_rate"),
                    "revenue_amount": rev_amt,
                }
            )

    seg_margins_raw = comp.get("segment_margins", []) or []
    seg_margins = []
    for sm in seg_margins_raw:
        v = _sv(sm)
        if isinstance(v, dict):
            margin_pct = safe_float(v.get("margin_pct"), None)
            prior = safe_float(v.get("prior_margin_pct"), None)
            change = safe_float(v.get("change_bps"), None)
            # Treat 0.0 prior as "not available" (LLM didn't extract prior year)
            if prior is not None and prior == 0.0:
                prior = None
                change = None  # Change is meaningless without real prior
            seg_margins.append(
                {
                    "name": v.get("name", "N/A"),
                    "margin_pct": f"{margin_pct:.1f}%" if margin_pct is not None else "N/A",
                    "prior_margin_pct": f"{prior:.1f}%" if prior is not None else "N/A",
                    "change_bps": f"{change:+.0f}bps" if change is not None else "N/A",
                }
            )

    # 2.5.4 Disruption risk
    dr_raw = _sv(comp.get("disruption_risk"))
    disruption_risk = {}
    if isinstance(dr_raw, dict):
        level = dr_raw.get("level", "")
        threats = dr_raw.get("threats", []) or []
        disruption_risk = {
            "level": level,
            "threats": threats if isinstance(threats, list) else [str(threats)],
            "color": "#DC2626"
            if level == "HIGH"
            else ("#D97706" if level == "MODERATE" else "#16A34A"),
        }

    # 2.8.1 Subsidiary structure
    sub_raw = _sv(comp.get("subsidiary_structure"))
    subsidiary_structure = {}
    if isinstance(sub_raw, dict):
        jur_raw = sub_raw.get("jurisdictions") or []
        # jurisdictions may be a list of dicts — extract count, not raw list
        if isinstance(jur_raw, list):
            jur_count = sub_raw.get("jurisdiction_count") or len(jur_raw)
            high_reg = sum(
                1
                for j in jur_raw
                if isinstance(j, dict) and j.get("regulatory_regime") == "HIGH_REG"
            )
            low_reg = sum(
                1
                for j in jur_raw
                if isinstance(j, dict) and j.get("regulatory_regime") == "LOW_REG"
            )
        else:
            jur_count = jur_raw
            high_reg = sub_raw.get("high_reg") or sub_raw.get("high_regulation_count", "N/A")
            low_reg = sub_raw.get("low_reg") or sub_raw.get("low_regulation_count", "N/A")
        subsidiary_structure = {
            "count": sub_raw.get("total_subsidiaries")
            or sub_raw.get("count")
            or sub_raw.get("total_count", "N/A"),
            "jurisdictions": jur_count,
            "high_reg": high_reg,
            "low_reg": low_reg,
        }

    # 2.8.2 Workforce distribution
    wf_raw = _sv(comp.get("workforce_distribution"))
    workforce = {}
    if isinstance(wf_raw, dict):
        total = wf_raw.get("total") or wf_raw.get("total_employees")
        domestic = wf_raw.get("domestic") or wf_raw.get("domestic_employees")
        intl = wf_raw.get("international") or wf_raw.get("international_employees")
        workforce = {
            "total": f"{int(total):,}" if total else "N/A",
            "domestic": f"{int(domestic):,}" if domestic else "N/A",
            "international": f"{int(intl):,}" if intl else "N/A",
        }

    # 2.8.3 Operational complexity
    oc_raw = _sv(comp.get("operational_complexity"))
    op_complexity = {}
    if isinstance(oc_raw, dict):
        op_complexity = {
            "has_vie": oc_raw.get("has_vie") or oc_raw.get("vie", False),
            "has_spe": oc_raw.get("has_spe") or oc_raw.get("spe", False),
            "has_dual_class": oc_raw.get("has_dual_class") or oc_raw.get("dual_class", False),
        }

    # 2.8.4 Operational resilience
    or_raw = _sv(comp.get("operational_resilience"))
    op_resilience = {}
    if isinstance(or_raw, dict):
        geo = or_raw.get("primary_geography") or or_raw.get("geographic_concentration", "N/A")
        sc_depth = or_raw.get("supply_chain_depth", "N/A")
        fac = or_raw.get("single_facility_risk")
        fac_label = "Single-facility" if fac else ("Distributed" if fac is False else "N/A")
        op_resilience = {
            "geographic_concentration": geo,
            "supply_chain_depth": sc_depth,
            "facility_risk": fac_label,
            "overall_assessment": or_raw.get("overall_assessment", "N/A"),
        }

    # 2.8.5 Key person risk — enrich from governance + yfinance when LLM data incomplete
    kp_raw = _sv(comp.get("key_person_risk"))
    key_person = {}
    if isinstance(kp_raw, dict):
        risk_score = safe_float(kp_raw.get("risk_score"), None)
        ceo_tenure = kp_raw.get("ceo_tenure_years") or kp_raw.get("ceo_tenure")
        is_founder_led = kp_raw.get("is_founder_led", False)
        has_succession = kp_raw.get("has_succession_plan")

        # Enrich from governance leadership data if CEO tenure not set
        if not ceo_tenure and state.extracted and state.extracted.governance:
            gov_lead = state.extracted.governance.leadership
            if gov_lead:
                gov_lead_d = _to_dict(gov_lead)
                for ex in gov_lead_d.get("executives", []) or []:
                    ex_title = _sv(ex.get("title")) or ""
                    if "chief executive" in ex_title.lower() or "ceo" in ex_title.lower():
                        t = _sv(ex.get("tenure_years"))
                        if t:
                            ceo_tenure = safe_float(t, None)
                        break

        # Enrich from yfinance companyOfficers if still missing
        if not ceo_tenure:
            yf_info = _get_yfinance_info(state)
            for o in yf_info.get("companyOfficers", []) or []:
                if isinstance(o, dict):
                    o_title = (o.get("title") or "").lower()
                    if "ceo" in o_title or "chief executive" in o_title:
                        age = o.get("age")
                        if age and not ceo_tenure:
                            # Use age as indicator; tenure not directly in yfinance
                            pass
                        break

        # Recompute risk score from actual data if raw was 0 and we have enrichments
        if risk_score == 0 and ceo_tenure:
            # Simple risk heuristic: longer tenure + no succession = higher concentration risk
            tenure_val = safe_float(ceo_tenure, 0) or 0
            if tenure_val >= 15:
                risk_score = 6  # High concentration
            elif tenure_val >= 10:
                risk_score = 4  # Moderate
            elif tenure_val >= 5:
                risk_score = 3
            else:
                risk_score = 2  # New CEO = transition risk

        key_person = {
            "is_founder_led": is_founder_led,
            "ceo_tenure": ceo_tenure,
            "has_succession_plan": has_succession,
            "risk_score": f"{risk_score:.0f}" if risk_score is not None else "N/A",
            "color": (
                "#DC2626"
                if risk_score and risk_score >= 7
                else "#D97706"
                if risk_score and risk_score >= 4
                else "#16A34A"
            ),
        }

    # 2.10.1 + 2.10.5 Event timeline — from company data or LLM extractions
    events_raw = comp.get("event_timeline", []) or []
    events = []
    for e in events_raw:
        v = _sv(e)
        if isinstance(v, dict):
            events.append(
                {
                    "date": v.get("date", ""),
                    "event": v.get("event") or v.get("description", ""),
                    "type": v.get("type") or v.get("category", ""),
                }
            )

    # Enrich timeline from 8-K LLM extractions — ALWAYS try to replace generic "8-K filing" text
    _enrich_from_llm = (
        not events  # No events at all
        or all("8-K filing" in e.get("event", "") for e in events)  # All generic
    )
    if _enrich_from_llm and state.acquired_data and state.acquired_data.llm_extractions:
        events = []  # Replace generic entries with rich ones
        llm = state.acquired_data.llm_extractions
        if isinstance(llm, dict):
            for key, val in sorted(llm.items()):
                if "8-K" not in key:
                    continue
                if not isinstance(val, dict):
                    continue
                edate = val.get("event_date") or ""
                etype = val.get("event_type") or ""
                desc = val.get("event_description") or ""
                dep = val.get("departing_officer") or ""
                dep_title = val.get("departing_officer_title") or ""
                succ = val.get("successor") or ""
                restruct = val.get("restructuring_description") or ""
                restruct_charge = val.get("restructuring_charge")
                agr_summary = val.get("agreement_summary") or ""
                agr_type_raw = val.get("agreement_type") or ""
                # Build useful description
                if not desc:
                    if dep:
                        desc = f"{dep}"
                        if dep_title:
                            desc += f" ({dep_title})"
                        desc += " departure"
                        if succ:
                            desc += f"; succeeded by {succ}"
                    elif restruct:
                        desc = restruct[:200]
                        if restruct_charge and isinstance(restruct_charge, (int, float)):
                            desc += f" (${restruct_charge / 1_000_000:.0f}M charge)"
                    elif agr_summary:
                        desc = (
                            f"{agr_type_raw}: {agr_summary[:150]}"
                            if agr_type_raw
                            else agr_summary[:200]
                        )
                    elif etype:
                        desc = etype
                # Determine event type
                items = val.get("items_covered") or []
                restructuring = val.get("restructuring_type") or ""
                agreement_type = val.get("agreement_type") or ""
                category = "8-K"
                if restructuring or any(i in ("2.05", "2.06") for i in items):
                    category = "Restructuring"
                elif "underwriting" in agreement_type.lower():
                    category = "Offering"
                elif any(i in ("5.02",) for i in items):
                    category = "Leadership"
                elif any(i in ("1.01", "1.02") for i in items):
                    category = "Agreement"
                elif any(i in ("2.02",) for i in items):
                    category = "Earnings"
                elif any(i in ("5.07",) for i in items):
                    category = "Shareholder"
                elif any(i in ("4.01", "4.02") for i in items):
                    category = "Audit"
                events.append(
                    {
                        "date": edate[:10] if edate else "",
                        "event": desc[:200] if desc else etype,
                        "type": category,
                    }
                )
            events.sort(key=lambda x: x["date"], reverse=True)

    # M&A from XBRL cash flow
    ma_amount = _extract_xbrl_ma(state)

    # 2.1.1 Business description
    bus_desc_raw = _sv(comp.get("business_description"))
    business_description = ""
    if isinstance(bus_desc_raw, str):
        business_description = bus_desc_raw
    elif isinstance(bus_desc_raw, dict):
        business_description = bus_desc_raw.get("value", "") or ""

    # 2.4.1 Customer concentration
    cust_conc_raw = comp.get("customer_concentration", []) or []
    customer_concentration = []
    for cc in cust_conc_raw:
        v = _sv(cc)
        if isinstance(v, dict):
            customer_concentration.append(
                {
                    "customer": v.get("customer", "N/A"),
                    "revenue_pct": v.get("revenue_pct"),
                }
            )
        elif isinstance(v, str) and v:
            customer_concentration.append({"customer": v, "revenue_pct": None})

    # 2.4.2 Geographic footprint
    geo_raw = comp.get("geographic_footprint", []) or []
    geographic_footprint = []
    # Compute total subsidiaries for percentage calculation
    total_subsidiaries = 0.0
    jurisdiction_data = []
    for gf in geo_raw:
        v = _sv(gf)
        if isinstance(v, dict):
            jurisdiction = v.get("jurisdiction", "N/A")
            subsidiary_count = safe_float(v.get("subsidiary_count", 0.0))
            tax_haven = v.get("tax_haven", "").lower() == "true"
            jurisdiction_data.append(
                {
                    "jurisdiction": jurisdiction,
                    "subsidiary_count": subsidiary_count,
                    "tax_haven": tax_haven,
                }
            )
            total_subsidiaries += subsidiary_count

    # Build geographic footprint with percentages
    for entry in jurisdiction_data:
        region = entry["jurisdiction"]
        count = entry["subsidiary_count"]
        tax_haven = entry["tax_haven"]

        # Create display string
        if count == 1.0:
            detail = "1 subsidiary"
        else:
            detail = f"{int(count) if count.is_integer() else count} subsidiaries"
        if tax_haven:
            detail += " (Tax Haven)"

        # Calculate percentage for bar width visualization
        pct_num = 0.0
        if total_subsidiaries > 0:
            pct_num = (count / total_subsidiaries) * 100.0
        pct_str = f"{pct_num:.1f}%" if total_subsidiaries > 0 else "N/A"

        geographic_footprint.append(
            {
                "region": region,
                "percentage": detail,  # Using detail as the display string
                "pct_num": pct_num,
            }
        )

    # 2.4.3 Supplier concentration
    sup_raw = comp.get("supplier_concentration", []) or []
    supplier_concentration = []
    for sc in sup_raw:
        v = _sv(sc)
        if isinstance(v, dict):
            supplier_concentration.append(
                {
                    "supplier": v.get("supplier", "N/A"),
                    "cost_pct": v.get("cost_pct"),
                }
            )
        elif isinstance(v, str) and v:
            supplier_concentration.append({"supplier": v, "cost_pct": None})

    # 2.6 D&O exposure factors
    doex_raw = comp.get("do_exposure_factors", []) or []
    do_exposure_factors = []
    for de in doex_raw:
        v = _sv(de)
        if isinstance(v, dict):
            do_exposure_factors.append(
                {
                    "factor": v.get("factor", ""),
                    "reason": v.get("reason", ""),
                }
            )

    # Filer category
    filer_raw = _sv(comp.get("filer_category"))
    filer_category = ""
    if isinstance(filer_raw, str):
        filer_category = filer_raw
    elif isinstance(filer_raw, dict):
        filer_category = filer_raw.get("value", "") or ""

    # State of incorporation — may be in company.identity
    state_of_inc = ""
    ident = comp.get("identity", {}) or {}
    soi_raw = _sv(ident.get("state_of_incorporation"))
    if isinstance(soi_raw, str):
        state_of_inc = soi_raw
    elif isinstance(soi_raw, dict):
        state_of_inc = soi_raw.get("value", "") or ""

    # M&A from XBRL cash flow
    ma_amount = _extract_xbrl_ma(state)

    # Exchange from yfinance info
    yf_info = _get_yfinance_info(state)
    exchange = yf_info.get("exchange", "") or ""

    # Years public
    years_public_raw = _sv(comp.get("years_public"))
    years_public = ""
    if years_public_raw is not None:
        if isinstance(years_public_raw, (int, float)):
            years_public = str(int(years_public_raw))
        elif isinstance(years_public_raw, str) and years_public_raw:
            years_public = years_public_raw

    # Risk classification
    risk_class_raw = _sv(comp.get("risk_classification"))
    risk_classification = ""
    if isinstance(risk_class_raw, str) and risk_class_raw:
        risk_classification = risk_class_raw
    elif isinstance(risk_class_raw, dict):
        risk_classification = risk_class_raw.get("value", "") or ""

    # Narrative & commentary
    comp_narrative = ""
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        pcn = _to_dict(state.analysis.pre_computed_narratives)
        comp_narrative = pcn.get("company", "") or ""
    commentary_factual, commentary_bullets = _get_commentary(state, "company")

    # Structured narrative — parse pre-computed company narrative into parts
    narrative_structured = _structure_company_narrative(comp_narrative)

    # Company Risk Profile card — answers "what/how/where/why" at a glance
    risk_profile = _build_risk_profile_card(
        business_description,
        revenue_model_type,
        customer_concentration,
        supplier_concentration,
        geographic_footprint,
        do_exposure_factors,
        state=state,
    )

    return {
        "business_description": business_description,
        "risk_profile": risk_profile,
        "narrative_structured": narrative_structured,
        "customer_concentration": customer_concentration,
        "geographic_footprint": geographic_footprint,
        "supplier_concentration": supplier_concentration,
        "do_exposure_factors": do_exposure_factors,
        "filer_category": filer_category,
        "state_of_incorporation": state_of_inc,
        "exchange": exchange,
        "years_public": years_public,
        "risk_classification": risk_classification,
        "revenue_model_type": revenue_model_type,
        "revenue_model_split": revenue_model_split,
        "seg_lifecycle": seg_lifecycle,
        "seg_margins": seg_margins,
        "disruption_risk": disruption_risk,
        "subsidiary_structure": subsidiary_structure,
        "workforce": workforce,
        "op_complexity": op_complexity,
        "op_resilience": op_resilience,
        "key_person": key_person,
        "events": events,
        "ma_amount": fmt_large_number(ma_amount) if ma_amount else "N/A",
        "narrative": comp_narrative,
        "commentary_factual": commentary_factual,
        "commentary_bullets": commentary_bullets,
    }


def build_ma_profile_context(state: AnalysisState) -> dict[str, Any]:
    """Build M&A Profile section context from company fields + signal results.

    Data sources:
    - state.company.goodwill_balance (SourcedValue[float]) — from LLM 10-K extraction
    - state.company.acquisitions_total_spend (SourcedValue[float]) — from LLM 10-K extraction
    - state.company.acquisitions (list[SourcedValue[str]]) — from LLM 10-K extraction
    - state.company.goodwill_change_description (SourcedValue[str]) — from LLM 10-K extraction
    - state.analysis.xbrl_forensics.ma_forensics — from XBRL-derived computation
    - state.analysis.signal_results[BIZ.MA.*] — from signal evaluation

    Returns dict with template-ready values; empty dict if no M&A data available.
    """
    if not state.company:
        return {}

    prof = state.company
    comp = _to_dict(prof)

    # --- LLM-extracted M&A data ---
    goodwill_raw = _sv(comp.get("goodwill_balance"))
    goodwill = safe_float(goodwill_raw, None)
    spend_raw = _sv(comp.get("acquisitions_total_spend"))
    spend = safe_float(spend_raw, None)
    acqs_raw = comp.get("acquisitions", []) or []
    acquisitions = [_sv(a) for a in acqs_raw if _sv(a)]
    gw_change = _sv(comp.get("goodwill_change_description")) or ""

    # --- XBRL forensic M&A data (fallback / enrichment) ---
    ma_forensics: dict[str, Any] = {}
    if state.analysis and state.analysis.xbrl_forensics:
        xf = state.analysis.xbrl_forensics
        if isinstance(xf, dict):
            ma_forensics = xf.get("ma_forensics", {}) or {}
        else:
            mf = getattr(xf, "ma_forensics", None)
            if mf is not None:
                ma_forensics = mf.model_dump() if hasattr(mf, "model_dump") else {}

    # LLM extracts in millions USD — convert to raw for display/ratios
    if goodwill is not None and goodwill < 100_000:
        goodwill = goodwill * 1_000_000
    if spend is not None and spend < 100_000:
        spend = spend * 1_000_000

    # Fall back to XBRL data when LLM extraction is empty
    if goodwill is None and ma_forensics:
        goodwill = safe_float(ma_forensics.get("goodwill_balance"), None)
    if spend is None and ma_forensics:
        spend = safe_float(ma_forensics.get("total_acquisition_spend"), None)

    goodwill_growth = (
        safe_float(ma_forensics.get("goodwill_growth_rate"), None) if ma_forensics else None
    )
    acq_to_rev = (
        safe_float(ma_forensics.get("acquisition_to_revenue"), None) if ma_forensics else None
    )
    acq_years = ma_forensics.get("acquisition_years", []) if ma_forensics else []
    is_serial = ma_forensics.get("is_serial_acquirer", False) if ma_forensics else False

    # --- Revenue for ratio calculation (from XBRL income statement line items) ---
    revenue: float | None = None
    if state.extracted and state.extracted.financials:
        stmts = state.extracted.financials.statements
        if stmts is not None:
            inc = getattr(stmts, "income_statement", None)
            if inc is not None:
                inc_d = _to_dict(inc)
                for li in inc_d.get("line_items", []):
                    if not isinstance(li, dict):
                        continue
                    label = (li.get("label") or "").lower()
                    if label in ("revenue", "total revenue", "net revenue", "revenues"):
                        vals = li.get("values", {})
                        if isinstance(vals, dict):
                            for period in sorted(vals.keys(), reverse=True):
                                pv = vals[period]
                                if isinstance(pv, dict):
                                    revenue = safe_float(pv.get("value"), None)
                                else:
                                    revenue = safe_float(pv, None)
                                if revenue is not None:
                                    break
                        break

    # --- Equity for goodwill ratio (from XBRL balance sheet line items) ---
    equity: float | None = None
    if state.extracted and state.extracted.financials:
        stmts = state.extracted.financials.statements
        if stmts is not None:
            bs = getattr(stmts, "balance_sheet", None)
            if bs is not None:
                bs_d = _to_dict(bs)
                for li in bs_d.get("line_items", []):
                    if not isinstance(li, dict):
                        continue
                    label = (li.get("label") or "").lower()
                    if "stockholders' equity" in label and "liabilities" not in label:
                        vals = li.get("values", {})
                        if isinstance(vals, dict):
                            # Get the most recent period value
                            for period in sorted(vals.keys(), reverse=True):
                                pv = vals[period]
                                if isinstance(pv, dict):
                                    equity = safe_float(pv.get("value"), None)
                                else:
                                    equity = safe_float(pv, None)
                                if equity is not None:
                                    break
                        break

    # --- Compute ratios ---
    goodwill_pct_equity: float | None = None
    if goodwill is not None and equity and equity > 0:
        goodwill_pct_equity = (goodwill / equity) * 100

    spend_pct_revenue: float | None = None
    if spend is not None and revenue and revenue > 0:
        spend_pct_revenue = (spend / revenue) * 100
    elif acq_to_rev is not None:
        spend_pct_revenue = acq_to_rev * 100

    # --- Signal results ---
    signal_statuses: dict[str, dict[str, Any]] = {}
    if state.analysis and state.analysis.signal_results:
        for sig_id, result in state.analysis.signal_results.items():
            if sig_id.startswith("BIZ.MA."):
                if isinstance(result, dict):
                    signal_statuses[sig_id] = result
                else:
                    signal_statuses[sig_id] = (
                        result.model_dump() if hasattr(result, "model_dump") else {}
                    )

    # --- Determine overall risk level ---
    if goodwill_pct_equity is not None and goodwill_pct_equity > 50:
        risk_level, risk_color = "HIGH", "#DC2626"
    elif (goodwill_pct_equity is not None and goodwill_pct_equity > 25) or is_serial:
        risk_level, risk_color = "MODERATE", "#D97706"
    elif goodwill is not None or spend is not None or acquisitions:
        risk_level, risk_color = "LOW", "#16A34A"
    else:
        risk_level, risk_color = "N/A", "#9CA3AF"

    # Gate: no data at all → return empty
    # ma_forensics with all-None values doesn't count as real data
    has_data = bool(
        goodwill is not None
        or spend is not None
        or acquisitions
        or gw_change
        or acq_years
        or is_serial
    )
    if not has_data:
        return {}

    return {
        "goodwill": fmt_large_number(goodwill) if goodwill is not None else "N/A",
        "goodwill_raw": goodwill,
        "goodwill_pct_equity": f"{goodwill_pct_equity:.1f}%"
        if goodwill_pct_equity is not None
        else "N/A",
        "spend": fmt_large_number(spend) if spend is not None else "N/A",
        "spend_pct_revenue": f"{spend_pct_revenue:.1f}%"
        if spend_pct_revenue is not None
        else "N/A",
        "acquisitions": acquisitions,
        "acquisition_count": len(acquisitions) or len(acq_years),
        "goodwill_change": gw_change if gw_change else "N/A",
        "goodwill_growth": f"{goodwill_growth:.1%}" if goodwill_growth is not None else "N/A",
        "is_serial_acquirer": is_serial,
        "risk_level": risk_level,
        "risk_color": risk_color,
        "signals": signal_statuses,
    }


def build_market_extended_context(state: AnalysisState) -> dict[str, Any]:
    """Build extended market context (quarterly earnings + insider transactions)."""
    # 3.5.3 Quarterly earnings detail — enhanced with margins, YoY%, EPS estimates
    quarterly: list[dict[str, Any]] = []

    # Build earnings history lookup (quarter end date → estimate/surprise data)
    eh_lookup: dict[str, dict[str, Any]] = {}
    if state.acquired_data and state.acquired_data.market_data:
        eh = state.acquired_data.market_data.get("earnings_history", {})
        if isinstance(eh, dict):
            quarters = eh.get("quarter", [])
            eps_actual = eh.get("epsActual", [])
            eps_estimate = eh.get("epsEstimate", [])
            eps_diff = eh.get("epsDifference", [])
            surprise_pct = eh.get("surprisePercent", [])
            for i, qdate in enumerate(quarters):
                if isinstance(qdate, str):
                    eh_lookup[qdate] = {
                        "eps_actual": eps_actual[i] if i < len(eps_actual) else None,
                        "eps_estimate": eps_estimate[i] if i < len(eps_estimate) else None,
                        "eps_diff": eps_diff[i] if i < len(eps_diff) else None,
                        "surprise_pct": surprise_pct[i] if i < len(surprise_pct) else None,
                    }

    if state.extracted and state.extracted.financials:
        yq = state.extracted.financials.yfinance_quarterly or []
        # Also get prior-year quarters for YoY calculation
        yq_all = list(yq) if isinstance(yq, list) else []
        rev_by_period: dict[str, float] = {}
        for q in yq_all:
            if isinstance(q, dict):
                period = q.get("period", "")
                rev_val = q.get("revenue")
                if period and rev_val is not None:
                    rev_by_period[period] = float(rev_val)

        for q in yq_all[:6]:
            if isinstance(q, dict):
                period = q.get("period", "")
                rev = q.get("revenue")
                ni = q.get("net_income")
                gp = q.get("gross_profit")
                op_inc = q.get("operating_income")
                eps = q.get("diluted_eps") or q.get("eps")

                # Compute margins
                gross_margin = f"{gp / rev * 100:.1f}%" if gp and rev and rev > 0 else "N/A"
                op_margin = f"{op_inc / rev * 100:.1f}%" if op_inc and rev and rev > 0 else "N/A"

                # YoY revenue change — find same quarter prior year
                yoy_pct = "N/A"
                if period and rev:
                    try:
                        yr = int(period[:4])
                        prior_key = f"{yr - 1}{period[4:]}"
                        prior_rev = rev_by_period.get(prior_key)
                        if prior_rev and prior_rev > 0:
                            yoy_val = (rev - prior_rev) / prior_rev * 100
                            yoy_pct = f"{yoy_val:+.1f}%"
                    except (ValueError, IndexError):
                        pass

                # EPS estimate and beat/miss from earnings_history
                eh_data = eh_lookup.get(period, {})
                eps_est = eh_data.get("eps_estimate")
                surprise = eh_data.get("surprise_pct")
                # Clamp surprise to ±100% — values beyond that are EPS
                # surprise on near-zero estimates, not meaningful percentages.
                if surprise is not None and abs(surprise) > 1.0:
                    surprise = None
                eps_est_str = f"${eps_est:.2f}" if eps_est is not None else "N/A"
                if eps is not None and eps_est is not None:
                    beat_miss = "BEAT" if eps > eps_est else ("MISS" if eps < eps_est else "MEET")
                    surprise_str = f"{surprise * 100:+.1f}%" if surprise is not None else ""
                else:
                    beat_miss = ""
                    surprise_str = ""

                quarterly.append(
                    {
                        "period": _format_quarter_label(period),
                        "revenue": fmt_large_number(rev),
                        "yoy_pct": yoy_pct,
                        "gross_margin": gross_margin,
                        "op_margin": op_margin,
                        "net_income": fmt_large_number(ni),
                        "eps": f"${eps:.2f}" if eps is not None else "N/A",
                        "eps_estimate": eps_est_str,
                        "beat_miss": beat_miss,
                        "surprise_pct": surprise_str,
                    }
                )

    # 3.7.2 + 5.4.2 Insider transaction table (scienter-focused)
    insider_txns: list[dict[str, Any]] = []
    insider_10b5_1_pct: float | None = None  # None = not determinable
    insider_cluster_count = 0
    insider_timing_count = 0
    insider_exercise_sell_count = 0
    insider_cluster_events: list[dict[str, Any]] = []
    insider_timing_suspects: list[dict[str, Any]] = []
    insider_exercise_sells: list[dict[str, Any]] = []
    insider_ownership_alerts: list[dict[str, Any]] = []

    # Build set of exercise-sell owner+date pairs for row highlighting
    _exercise_sell_keys: set[str] = set()

    if state.extracted and state.extracted.market:
        ia = state.extracted.market.insider_analysis
        if ia:
            ia_dict = _to_dict(ia)

            # 10b5-1 plan coverage percentage
            # Note: This is derived from Form 4 text parsing, which is unreliable.
            # Most Form 4 filings don't disclose 10b5-1 plan status.
            # 0% likely means "can't determine" not "no plans exist."
            # 10b5-1: Form 4 parsing is unreliable for plan detection.
            # 0% from Form 4 means "can't determine", not "no plans exist".
            # Only trust values > 0 from actual 10b5-1 plan mentions.
            raw_pct_sv = ia_dict.get("pct_10b5_1")
            raw_pct = _sv(raw_pct_sv)
            pct_val = safe_float(raw_pct, None)
            if pct_val is not None and pct_val > 0:
                insider_10b5_1_pct = pct_val
            # else: stays None (not determinable)

            # Cluster events
            clusters = ia_dict.get("cluster_events", []) or []
            insider_cluster_count = len(clusters)
            for ce in clusters:
                insider_cluster_events.append(
                    {
                        "start_date": ce.get("start_date", ""),
                        "end_date": ce.get("end_date", ""),
                        "insider_count": ce.get("insider_count", 0),
                        "insiders": ce.get("insiders", []),
                        "total_value": fmt_large_number(ce.get("total_value", 0)),
                    }
                )

            # Timing suspects
            suspects = ia_dict.get("timing_suspects", []) or []
            insider_timing_count = len(suspects)
            for ts_item in suspects:
                insider_timing_suspects.append(
                    {
                        "insider_name": ts_item.get("insider_name", ""),
                        "transaction_date": ts_item.get("transaction_date", ""),
                        "transaction_type": ts_item.get("transaction_type", ""),
                        "filing_date": ts_item.get("filing_date", ""),
                        "filing_item": ts_item.get("filing_item", ""),
                        "filing_sentiment": ts_item.get("filing_sentiment", ""),
                        "days_before_filing": ts_item.get("days_before_filing", 0),
                        "transaction_value": fmt_large_number(ts_item.get("transaction_value", 0)),
                        "severity": ts_item.get("severity", "AMBER"),
                    }
                )

            # Exercise-and-sell events
            ex_sells = ia_dict.get("exercise_sell_events", []) or []
            insider_exercise_sell_count = len(ex_sells)
            for es in ex_sells:
                _exercise_sell_keys.add(f"{es.get('owner', '')}|{es.get('date', '')}")
                insider_exercise_sells.append(
                    {
                        "owner": es.get("owner", ""),
                        "date": es.get("date", ""),
                        "exercised_shares": f"{int(es.get('exercised_shares', 0)):,}"
                        if es.get("exercised_shares")
                        else "0",
                        "sold_shares": f"{int(es.get('sold_shares', 0)):,}"
                        if es.get("sold_shares")
                        else "0",
                        "sold_value": fmt_large_number(es.get("sold_value", 0)),
                        "is_10b5_1": es.get("is_10b5_1", False),
                    }
                )

            # Ownership alerts
            alerts = ia_dict.get("ownership_alerts", []) or []
            for oa in alerts:
                insider_ownership_alerts.append(
                    {
                        "insider_name": oa.get("insider_name", ""),
                        "role": oa.get("role", ""),
                        "severity": oa.get("severity", "INFORMATIONAL"),
                        "personal_pct_sold": oa.get("personal_pct_sold", 0.0),
                        "shares_sold": f"{int(oa.get('shares_sold', 0)):,}"
                        if oa.get("shares_sold")
                        else "0",
                        "is_c_suite": oa.get("is_c_suite", False),
                    }
                )

            # Transactions with enriched fields (title, 10b5-1, exercise-sell flag)
            for t in (ia_dict.get("transactions", []) or [])[:20]:
                name = _sv(t.get("insider_name")) or "N/A"
                title = _sv(t.get("title")) or ""
                ttype = t.get("transaction_type", "")
                tdate = _sv(t.get("transaction_date")) or ""
                shares = _sv(t.get("shares"))
                value = _sv(t.get("total_value"))
                is_10b5_1_val = _sv(t.get("is_10b5_1"))
                is_officer = t.get("is_officer", False)
                is_director = t.get("is_director", False)
                shares_after = _sv(t.get("shares_owned_following"))

                # Determine role label
                role_label = title
                if not role_label:
                    if is_officer:
                        role_label = "Officer"
                    elif is_director:
                        role_label = "Director"

                # Check if this is an exercise-sell row
                date_str = tdate[:10] if tdate else ""
                is_exercise_sell = f"{name}|{date_str}" in _exercise_sell_keys

                # Compute % of holdings sold (if shares_after available)
                pct_holdings = ""
                if shares_after and shares and ttype in ("SELL", "SALE"):
                    shares_val = safe_float(shares, 0.0)
                    after_val = safe_float(shares_after, 0.0)
                    if after_val + shares_val > 0:
                        pct = (shares_val / (after_val + shares_val)) * 100
                        pct_holdings = f"{pct:.0f}%"

                insider_txns.append(
                    {
                        "date": date_str,
                        "name": name,
                        "role": role_label,
                        "type": ttype,
                        "shares": f"{int(shares):,}" if shares else "N/A",
                        "value": fmt_large_number(value) if value else "N/A",
                        "is_10b5_1": bool(is_10b5_1_val),
                        "is_exercise_sell": is_exercise_sell,
                        "pct_holdings": pct_holdings,
                        "is_c_suite": is_officer,
                    }
                )

    # Insider net direction summary
    insider_net_direction = ""
    insider_net_label = ""
    insider_sell_total = 0.0
    insider_buy_total = 0.0
    if state.extracted and state.extracted.market:
        ia = state.extracted.market.insider_analysis
        if ia:
            ia_dict = _to_dict(ia)
            nbs = _sv(ia_dict.get("net_buying_selling"))
            if isinstance(nbs, str):
                insider_net_direction = nbs  # e.g., "NET_SELLING"
            # Compute total sell/buy dollar amounts from transactions
            for t in ia_dict.get("transactions", []) or []:
                ttype = t.get("transaction_type", "")
                val = safe_float(_sv(t.get("total_value")), 0.0)
                if ttype in ("SELL", "SALE"):
                    insider_sell_total += val
                elif ttype in ("BUY", "PURCHASE"):
                    insider_buy_total += val
    if "SELL" in insider_net_direction.upper():
        insider_net_label = "NET SELLER"
    elif "BUY" in insider_net_direction.upper():
        insider_net_label = "NET BUYER"
    elif insider_sell_total > insider_buy_total:
        insider_net_label = "NET SELLER"
    elif insider_buy_total > insider_sell_total:
        insider_net_label = "NET BUYER"
    else:
        insider_net_label = "NEUTRAL"
    insider_net_amount = abs(insider_sell_total - insider_buy_total)

    # Scienter risk level — composite assessment
    scienter_factors: list[str] = []
    scienter_score = 0
    # 10b5-1: None means not determinable from Form 4 data — don't penalize
    if insider_10b5_1_pct is not None and insider_10b5_1_pct < 20:
        scienter_score += 2
        scienter_factors.append("no 10b5-1 safe harbor")
    elif insider_10b5_1_pct is not None and insider_10b5_1_pct < 50:
        scienter_score += 1
        scienter_factors.append("low 10b5-1 coverage")
    if insider_cluster_count > 0:
        scienter_score += 2
        scienter_factors.append(
            f"{insider_cluster_count} cluster selling event{'s' if insider_cluster_count > 1 else ''}"
        )
    if insider_timing_count > 0:
        scienter_score += 2
        scienter_factors.append(
            f"{insider_timing_count} suspiciously timed transaction{'s' if insider_timing_count > 1 else ''}"
        )
    if insider_exercise_sell_count > 0:
        scienter_score += 1
        scienter_factors.append(
            f"{insider_exercise_sell_count} exercise-and-sell pattern{'s' if insider_exercise_sell_count > 1 else ''}"
        )
    if insider_net_label == "NET SELLER":
        scienter_score += 1
        scienter_factors.append("net selling posture")
    # C-suite selling carries extra weight
    csuite_selling = any(
        t.get("is_c_suite") and t.get("type") in ("SELL", "SALE") for t in insider_txns
    )
    if csuite_selling:
        scienter_score += 1
        scienter_factors.append("C-suite selling")

    if scienter_score >= 5:
        insider_scienter_level = "HIGH"
    elif scienter_score >= 3:
        insider_scienter_level = "MEDIUM"
    else:
        insider_scienter_level = "LOW"

    # Narrative from pre-computed narratives
    market_narrative = ""
    if state.analysis and hasattr(state.analysis, "pre_computed_narratives"):
        pcn = _to_dict(state.analysis.pre_computed_narratives)
        market_narrative = pcn.get("stock_market", "") or pcn.get("market", "") or ""

    # Section opener — data-driven D&O connection
    section_opener = _build_section_opener("stock_market", state, {})

    # Market summary fields for section cards
    info: dict[str, Any] = {}
    if state.acquired_data and state.acquired_data.market_data:
        info = state.acquired_data.market_data.get("info", {}) or {}
    stock_price_val = info.get("currentPrice")
    high_52w_val = info.get("fiftyTwoWeekHigh")
    low_52w_val = info.get("fiftyTwoWeekLow")
    beta_val = info.get("beta")
    short_pct_val = info.get("shortPercentOfFloat")
    analyst_count_val = info.get("numberOfAnalystOpinions")
    analyst_rec_val = info.get("recommendationKey")

    stock_price_str = f"${stock_price_val:,.2f}" if stock_price_val else "N/A"
    high_52w_str = f"${high_52w_val:,.2f}" if high_52w_val else "N/A"
    low_52w_str = f"${low_52w_val:,.2f}" if low_52w_val else "N/A"
    beta_str = f"{beta_val:.2f}" if beta_val is not None else "N/A"
    short_pct_str = f"{short_pct_val * 100:.1f}%" if short_pct_val else "N/A"
    analyst_count_str = str(analyst_count_val) if analyst_count_val is not None else "N/A"
    analyst_rec_str = str(analyst_rec_val or "N/A").upper().replace("_", " ")

    # Drawdown from 52W high
    drawdown_str = "N/A"
    if high_52w_val and stock_price_val and high_52w_val > 0:
        dd = ((high_52w_val - stock_price_val) / high_52w_val) * 100
        drawdown_str = f"{dd:.1f}%"

    # Adverse events — composite score from EXTRACT stage
    adverse_score = "N/A"
    adverse_count = 0
    adverse_breakdown = ""
    if state.extracted and state.extracted.market:
        ae = getattr(state.extracted.market, "adverse_events", None)
        if ae:
            score_val = (
                ae.total_score.value if hasattr(ae.total_score, "value") else ae.total_score
            )
            if score_val is not None:
                adverse_score = f"{float(score_val):.1f}"
            adverse_count = ae.event_count or 0
            sb = ae.severity_breakdown or {}
            parts = [f"{v} {k.title()}" for k, v in sb.items() if v]
            adverse_breakdown = ", ".join(parts)

    return {
        "quarterly_earnings": quarterly,
        "insider_transactions": insider_txns,
        "insider_net_label": insider_net_label,
        "insider_net_amount": fmt_large_number(insider_net_amount) if insider_net_amount else "",
        "insider_sell_total": fmt_large_number(insider_sell_total) if insider_sell_total else "",
        "insider_buy_total": fmt_large_number(insider_buy_total) if insider_buy_total else "",
        "insider_10b5_1_pct": insider_10b5_1_pct,
        "insider_cluster_count": insider_cluster_count,
        "insider_cluster_events": insider_cluster_events,
        "insider_timing_count": insider_timing_count,
        "insider_timing_suspects": insider_timing_suspects,
        "insider_exercise_sell_count": insider_exercise_sell_count,
        "insider_exercise_sells": insider_exercise_sells,
        "insider_ownership_alerts": insider_ownership_alerts,
        "insider_scienter_level": insider_scienter_level,
        "insider_scienter_factors": scienter_factors,
        "narrative": market_narrative,
        "section_opener": section_opener,
        # Market summary card fields
        "stock_price": stock_price_str,
        "high_52w": high_52w_str,
        "low_52w": low_52w_str,
        "beta": beta_str,
        "short_pct": short_pct_str,
        "analyst_count": analyst_count_str,
        "analyst_rec": analyst_rec_str,
        "drawdown_from_high": drawdown_str,
        # Adverse events (previously uncollected but extracted)
        "adverse_score": adverse_score,
        "adverse_count": adverse_count,
        "adverse_breakdown": adverse_breakdown,
    }


def _format_quarter_label(period: str) -> str:
    """Convert 'YYYY-MM-DD' to 'Q1 YYYY' format."""
    if not period or len(period) < 7:
        return period or "N/A"
    try:
        month = int(period[5:7])
        year = period[:4]
        q = (month - 1) // 3 + 1
        return f"Q{q} {year}"
    except (ValueError, IndexError):
        return period


def _extract_xbrl_ma(state: AnalysisState) -> float | None:
    """Extract M&A / acquisitions amount from XBRL cash flow statement."""
    try:
        if not state.extracted or not state.extracted.financials:
            return None
        stmts = state.extracted.financials.statements
        if not stmts:
            return None
        sd = _to_dict(stmts)
        cf = sd.get("cash_flow_statement", {})
        for item in cf.get("line_items", []) or []:
            label = (item.get("label", "") or "").lower()
            if any(kw in label for kw in ("acqui", "business_comb", "merger")):
                vals = item.get("values", {})
                periods = cf.get("periods", []) or []
                for p in periods:
                    v = _sv(vals.get(p))
                    if v is not None:
                        return safe_float(v, None)
    except Exception:
        pass
    return None


def build_forensic_composites_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build forensic composite scores context from analysis.forensic_composites."""
    if not state.analysis:
        return None
    fc = _to_dict(state.analysis).get("forensic_composites")
    if not fc or not isinstance(fc, dict):
        return None

    def _zone_color(zone: str) -> str:
        z = (zone or "").upper()
        if z in ("HIGH_INTEGRITY", "SAFE", "STRONG"):
            return "#16A34A"
        if z in ("CONCERNING", "WARNING", "MODERATE"):
            return "#D97706"
        if z in ("DANGER", "CRITICAL", "HIGH_RISK"):
            return "#DC2626"
        return "#6B7280"

    def _build_composite(key: str, label: str) -> dict[str, Any] | None:
        raw = fc.get(key)
        if not raw or not isinstance(raw, dict):
            return None
        score = safe_float(raw.get("overall_score"), None)
        zone = raw.get("zone", "")
        # Gather sub-scores from the composite
        sub_scores: list[dict[str, Any]] = []
        for sk, sv_raw in raw.items():
            if sk in ("overall_score", "zone", "sub_scores"):
                continue
            if isinstance(sv_raw, dict) and "score" in sv_raw:
                sub_scores.append(
                    {
                        "name": sv_raw.get("name", sk).replace("_", " ").title(),
                        "score": f"{safe_float(sv_raw['score'], 0):.0f}",
                        "evidence": sv_raw.get("evidence", ""),
                    }
                )
        return {
            "label": label,
            "score": f"{score:.0f}" if score is not None else "N/A",
            "score_raw": score,
            "zone": zone.replace("_", " ").title(),
            "zone_color": _zone_color(zone),
            "sub_scores": sub_scores,
        }

    composites = []
    for key, label in [
        ("financial_integrity_score", "Financial Integrity"),
        ("revenue_quality_score", "Revenue Quality"),
        ("cash_flow_quality_score", "Cash Flow Quality"),
    ]:
        c = _build_composite(key, label)
        if c:
            composites.append(c)

    return {"composites": composites} if composites else None


def build_xbrl_forensics_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build XBRL forensics detail table from analysis.xbrl_forensics."""
    if not state.analysis:
        return None
    xf = _to_dict(state.analysis).get("xbrl_forensics")
    if not xf or not isinstance(xf, dict):
        return None

    def _zone_badge(zone: str) -> tuple[str, str]:
        z = (zone or "").lower()
        if z == "safe":
            return ("Safe", "#16A34A")
        if z == "warning":
            return ("Warning", "#D97706")
        if z == "danger":
            return ("Alert", "#DC2626")
        return ("N/A", "#6B7280")

    def _trend_arrow(trend: str | None) -> str:
        if not trend:
            return ""
        t = trend.lower()
        if t == "improving":
            return "&#9650;"  # up arrow
        if t in ("deteriorating", "worsening"):
            return "&#9660;"  # down arrow
        return "&#9654;"  # right arrow (stable)

    categories: list[dict[str, Any]] = []
    # Process each category
    category_labels = {
        "beneish": "Beneish M-Score Components",
        "revenue": "Revenue Forensics",
        "capital_allocation": "Capital Allocation",
        "debt_tax": "Debt & Tax",
        "earnings_quality": "Earnings Quality",
        "balance_sheet": "Balance Sheet Forensics",
        "ma_forensics": "M&A Forensics",
    }
    for cat_key, cat_label in category_labels.items():
        cat_data = xf.get(cat_key)
        if not cat_data or not isinstance(cat_data, dict):
            continue

        # Beneish has different structure (flat numeric fields)
        if cat_key == "beneish":
            composite = safe_float(cat_data.get("composite_score"), None)
            zone = cat_data.get("zone", "")
            badge_label, badge_color = _zone_badge(zone)
            metrics: list[dict[str, Any]] = []
            for mk in ("dsri", "gmi", "aqi", "sgi", "depi", "sgai", "tata", "lvgi"):
                mv = safe_float(cat_data.get(mk), None)
                if mv is not None:
                    metrics.append(
                        {
                            "name": mk.upper(),
                            "value": f"{mv:.4f}",
                            "zone_label": "",
                            "zone_color": "#6B7280",
                            "trend": "",
                        }
                    )
            categories.append(
                {
                    "label": cat_label,
                    "summary": f"Composite: {composite:.2f}" if composite is not None else "",
                    "summary_badge": badge_label,
                    "summary_color": badge_color,
                    "metrics": metrics,
                }
            )
            continue

        # Standard structure: each metric has value/zone/trend/confidence
        metrics = []
        for metric_key, metric_data in cat_data.items():
            if not isinstance(metric_data, dict):
                continue
            val = metric_data.get("value")
            zone = metric_data.get("zone", "")
            trend = metric_data.get("trend")
            confidence = metric_data.get("confidence", "")

            if zone == "insufficient_data":
                continue  # Skip metrics with no data

            badge_label, badge_color = _zone_badge(zone)
            # Format value
            if val is None:
                val_str = "N/A"
            elif isinstance(val, bool):
                val_str = "Yes" if val else "No"
            elif isinstance(val, float):
                if abs(val) >= 100:
                    val_str = f"{val:,.1f}"
                elif abs(val) >= 1:
                    val_str = f"{val:.2f}"
                else:
                    val_str = f"{val:.4f}"
            else:
                val_str = str(val)

            metrics.append(
                {
                    "name": metric_key.replace("_", " ").title(),
                    "value": val_str,
                    "zone_label": badge_label,
                    "zone_color": badge_color,
                    "trend": _trend_arrow(trend),
                    "confidence": confidence,
                }
            )

        if metrics:
            categories.append(
                {
                    "label": cat_label,
                    "summary": "",
                    "summary_badge": "",
                    "summary_color": "",
                    "metrics": metrics,
                }
            )

    return {"categories": categories} if categories else None


def build_nlp_signals_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build NLP signals dashboard from analysis.nlp_signals + signal_results."""
    if not state.analysis:
        return None
    analysis = _to_dict(state.analysis)
    nlp = analysis.get("nlp_signals")
    if not nlp or not isinstance(nlp, dict):
        return None

    # Risk factors
    rf = nlp.get("risk_factors", {}) or {}
    risk_factor_count = rf.get("current_count")
    new_factors = rf.get("new_factors", []) or []
    removed_factors = rf.get("removed_factors", []) or []

    # Whistleblower
    wb = nlp.get("whistleblower", {}) or {}
    whistle_detected = wb.get("detected", False)

    # Readability
    readability = nlp.get("readability", {}) or {}
    read_class = readability.get("classification", "")

    # Tone
    tone = nlp.get("tone_shift", {}) or {}
    tone_class = tone.get("classification", "")

    # NLP signal results from signal_results
    sr = analysis.get("signal_results", {}) or {}
    nlp_signals: list[dict[str, Any]] = []
    for key in sorted(sr.keys()):
        if not key.startswith("NLP."):
            continue
        sig = sr[key]
        if not isinstance(sig, dict):
            continue
        val = sig.get("value")
        evidence = sig.get("evidence", "")
        disposition = sig.get("disposition", "")
        # Determine badge
        if "TRIGGERED" in str(disposition).upper() or (
            "Boolean check: True" in str(evidence) and "regulatory" in key.lower()
        ):
            badge = "TRIGGERED"
            badge_color = "#DC2626"
        elif val is True or "True condition met" in str(evidence):
            badge = "TRIGGERED"
            badge_color = "#DC2626"
        elif str(val) == "present" or "Management display" in str(evidence):
            badge = "INFO"
            badge_color = "#6366F1"
        elif val is False or "False condition" in str(evidence):
            badge = "CLEAR"
            badge_color = "#16A34A"
        elif "pending" in str(evidence).lower() or val is None:
            badge = "PENDING"
            badge_color = "#9CA3AF"
        else:
            badge = "INFO"
            badge_color = "#6366F1"

        # Friendly name
        short_name = key.replace("NLP.", "").replace(".", " ").replace("_", " ").title()
        nlp_signals.append(
            {
                "key": key,
                "name": short_name,
                "value": str(val) if val is not None else "N/A",
                "badge": badge,
                "badge_color": badge_color,
                "evidence": str(evidence)[:200] if evidence else "",
            }
        )

    # Narrative coherence from extracted governance
    coherence = {}
    if state.extracted and state.extracted.governance:
        gov = _to_dict(state.extracted.governance)
        nc = gov.get("narrative_coherence", {}) or {}
        if nc:
            for ck in ("strategy_vs_results", "tone_vs_financials", "overall_assessment"):
                raw = nc.get(ck)
                val = _sv(raw) if raw else None
                if val:
                    coherence[ck.replace("_", " ").title()] = str(val)

    # Sentiment trend
    sentiment_trend = None
    if state.extracted and state.extracted.governance:
        gov = _to_dict(state.extracted.governance)
        sent = gov.get("sentiment", {}) or {}
        lm_neg = sent.get("lm_negative_trend")
        if lm_neg:
            if isinstance(lm_neg, list) and lm_neg:
                val = _sv(lm_neg[0])
                sentiment_trend = f"{safe_float(val, 0):.0f}" if val else None
            else:
                sentiment_trend = str(_sv(lm_neg))

    return {
        "risk_factor_count": risk_factor_count,
        "new_risk_factors": len(new_factors),
        "removed_risk_factors": len(removed_factors),
        "whistle_detected": whistle_detected,
        "readability_class": read_class or "N/A",
        "tone_class": tone_class or "N/A",
        "signals": nlp_signals,
        "coherence": coherence,
        "sentiment_trend": sentiment_trend,
    }


def build_settlement_prediction_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build settlement prediction context from analysis.settlement_prediction."""
    if not state.analysis:
        return None
    sp = _to_dict(state.analysis).get("settlement_prediction")
    if not sp or not isinstance(sp, dict):
        return None

    ddl = safe_float(sp.get("ddl_amount"), None)
    model = sp.get("model", "")

    # Case characteristics
    chars = sp.get("case_characteristics", {}) or {}
    char_badges: list[dict[str, Any]] = []
    char_labels = {
        "accounting_fraud": "Accounting Fraud",
        "restatement": "Restatement",
        "insider_selling": "Insider Selling",
        "institutional_lead_plaintiff": "Institutional Lead Plaintiff",
        "top_tier_counsel": "Top-Tier Counsel",
        "sec_investigation": "SEC Investigation",
        "class_period_over_1yr": "Class Period >1yr",
        "multiple_corrective_disclosures": "Multiple Disclosures",
        "going_concern": "Going Concern",
        "officer_termination": "Officer Termination",
    }
    for ck, cl in char_labels.items():
        cv = chars.get(ck)
        if cv is not None:
            char_badges.append(
                {
                    "label": cl,
                    "present": bool(cv),
                    "color": "#DC2626" if cv else "#16A34A",
                }
            )

    # Tower risk
    tower = sp.get("tower_risk", {}) or {}
    layers: list[dict[str, Any]] = []
    layer_order = [
        ("primary", "Primary"),
        ("low_excess", "Low Excess"),
        ("mid_excess", "Mid Excess"),
        ("high_excess", "High Excess"),
    ]
    for lk, ll in layer_order:
        ld = tower.get(lk, {}) or {}
        if not ld:
            continue
        share = safe_float(ld.get("expected_loss_share_pct"), None)
        loss = safe_float(ld.get("expected_loss_amount"), None)
        layers.append(
            {
                "name": ll,
                "share_pct": f"{share:.1f}%" if share is not None else "N/A",
                "share_raw": share or 0,
                "expected_loss": fmt_large_number(loss) if loss is not None else "N/A",
                "characterization": ld.get("risk_characterization", ""),
            }
        )

    return {
        "ddl_amount": fmt_large_number(ddl) if ddl is not None else "N/A",
        "ddl_raw": ddl,
        "model": model,
        "characteristics": char_badges,
        "tower_layers": layers,
    }


def build_peril_map_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build peril map context from analysis.peril_map."""
    if not state.analysis:
        return None
    pm = _to_dict(state.analysis).get("peril_map")
    if not pm or not isinstance(pm, dict):
        return None

    overall = pm.get("overall_peril_rating", "")

    def _peril_color(band: str) -> str:
        b = (band or "").upper()
        if b in ("VERY_LOW", "LOW"):
            return "#16A34A"
        if b in ("MODERATE",):
            return "#D97706"
        if b in ("ELEVATED",):
            return "#EA580C"
        if b in ("HIGH", "CRITICAL"):
            return "#DC2626"
        return "#6B7280"

    # Assessments table
    assessments = []
    for a in pm.get("assessments", []) or []:
        if not isinstance(a, dict):
            continue
        ptype = a.get("plaintiff_type", "")
        prob = a.get("probability_band", "")
        sev = a.get("severity_band", "")
        triggered = a.get("triggered_signal_count", 0)
        total = a.get("evaluated_signal_count", 0)
        findings = a.get("key_findings", []) or []
        assessments.append(
            {
                "plaintiff_type": ptype.replace("_", " ").title(),
                "probability": prob.replace("_", " ").title(),
                "prob_color": _peril_color(prob),
                "severity": sev.replace("_", " ").title(),
                "sev_color": _peril_color(sev),
                "signals": f"{triggered}/{total}",
                "findings": [str(f)[:150] for f in findings[:3]],
            }
        )

    # Bear cases
    bear_cases = []
    for bc in pm.get("bear_cases", []) or []:
        if not isinstance(bc, dict):
            continue
        bear_cases.append(
            {
                "theory": bc.get("theory", ""),
                "plaintiff_type": (bc.get("plaintiff_type", "") or "").replace("_", " ").title(),
                "summary": bc.get("committee_summary", ""),
                "evidence_count": len(bc.get("evidence_chain", []) or []),
            }
        )

    # Coverage gaps
    gaps = pm.get("coverage_gaps", []) or []
    gap_list = [str(g)[:120] for g in gaps[:10]]

    return {
        "overall_rating": overall.replace("_", " ").title(),
        "overall_color": _peril_color(overall),
        "assessments": assessments,
        "bear_cases": bear_cases,
        "coverage_gaps": gap_list,
    }


def build_executive_risk_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build executive risk context from analysis.executive_risk."""
    if not state.analysis:
        return None
    er = _to_dict(state.analysis).get("executive_risk")
    if not er or not isinstance(er, dict):
        return None

    weighted = safe_float(er.get("weighted_score"), None)
    highest = er.get("highest_risk_individual", "")
    findings = er.get("key_findings", []) or []

    individuals: list[dict[str, Any]] = []
    for ind in er.get("individual_scores", []) or []:
        if not isinstance(ind, dict):
            continue
        score = safe_float(ind.get("total_score"), 0)
        individuals.append(
            {
                "name": ind.get("person_name", "N/A"),
                "role": ind.get("role", ""),
                "score": f"{score:.1f}",
                "score_raw": score,
                "score_color": "#DC2626"
                if score >= 1.0
                else ("#D97706" if score > 0 else "#16A34A"),
                "findings": ind.get("findings", []) or [],
                "tenure_flag": score > 0 and ind.get("tenure_stability", 0) > 0,
            }
        )

    return {
        "weighted_score": f"{weighted:.2f}" if weighted is not None else "N/A",
        "weighted_raw": weighted or 0,
        "weighted_color": "#DC2626"
        if (weighted or 0) >= 1.0
        else ("#D97706" if (weighted or 0) > 0.2 else "#16A34A"),
        "highest_risk": highest or "None",
        "findings": [str(f) for f in findings[:5]],
        "individuals": individuals,
    }


def build_temporal_signals_context(state: AnalysisState) -> dict[str, Any] | None:
    """Build temporal signals context from analysis.temporal_signals."""
    if not state.analysis:
        return None
    ts = _to_dict(state.analysis).get("temporal_signals")
    if not ts or not isinstance(ts, dict):
        return None

    summary = ts.get("summary", "")
    signals_raw = ts.get("signals", []) or []

    def _class_color(cls: str) -> str:
        c = (cls or "").upper()
        if c == "STABLE":
            return "#16A34A"
        if c in ("IMPROVING",):
            return "#2563EB"
        if c in ("DETERIORATING", "ADVERSE"):
            return "#DC2626"
        return "#6B7280"

    signals: list[dict[str, Any]] = []
    for sig in signals_raw:
        if not isinstance(sig, dict):
            continue
        name = (sig.get("metric_name", "") or "").replace("_", " ").title()
        cls = sig.get("classification", "")
        change = safe_float(sig.get("total_change_pct"), None)
        periods = sig.get("periods", []) or []
        # Get most recent and prior values
        latest_val = None
        prior_val = None
        if periods:
            latest_val = safe_float(
                periods[0].get("value") if isinstance(periods[0], dict) else None, None
            )
            if len(periods) > 1:
                prior_val = safe_float(
                    periods[1].get("value") if isinstance(periods[1], dict) else None, None
                )
        signals.append(
            {
                "name": name,
                "classification": cls.replace("_", " ").title(),
                "class_color": _class_color(cls),
                "change_pct": f"{change:+.1f}%" if change is not None else "N/A",
                "latest_value": latest_val,
                "prior_value": prior_val,
                "evidence": sig.get("evidence", ""),
            }
        )

    return {
        "summary": summary,
        "signals": signals,
    }


def _get_scoring(state: AnalysisState) -> dict[str, Any]:
    return _to_dict(state.scoring) if state.scoring else {}


def _get_yfinance_info(state: AnalysisState) -> dict[str, Any]:
    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            return md.get("info", {})
        if hasattr(md, "info"):
            return getattr(md, "info", {}) or {}
    return {}
