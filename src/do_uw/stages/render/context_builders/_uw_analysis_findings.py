"""Key Risk Findings builder for uw analysis — risk-factor-driven, not signal-driven.

PRIMARY source: 10-K Risk Factors with HIGH D&O relevance (company-specific disclosures).
SECONDARY source: Triggered signals not already covered by risk factors (quantitative).
"""
from __future__ import annotations

import re
from typing import Any

from do_uw.models.state import AnalysisState


def _build_critical_findings(state: AnalysisState) -> list[dict[str, Any]]:
    """Build findings for critical underwriting risks that brain signals miss.

    These are the things a 30-year underwriter flags FIRST — active SCAs,
    extreme stock drops, chronic filer status. Uses the same dict schema as
    rf_results/signal_results so the template renders them identically:
    - headline, severity, is_risk_factor, headline_tags
    - evidence_bullets (list of strings — template renders these as bullet points)
    - badge_value (shown in colored pill)

    Every bullet must read like a senior underwriter wrote it — specific numbers,
    cross-referenced findings, and what the combined picture means for D&O.
    """
    from do_uw.stages.render.sca_counter import get_active_genuine_scas
    from do_uw.stages.render.formatters import safe_float

    results: list[dict[str, Any]] = []
    ticker = state.ticker or "Company"
    mcap_str = ""
    mcap = 0.0
    shares_out = 0.0
    md = state.acquired_data.market_data if state.acquired_data else None
    if md and isinstance(md, dict):
        info = md.get("info", md.get("yfinance_info", {}))
        if isinstance(info, dict):
            mcap = safe_float(info.get("marketCap", 0), 0)
            shares_out = safe_float(info.get("sharesOutstanding", 0), 0)
            if mcap > 1e9:
                mcap_str = f"${mcap / 1e9:.1f}B"
            elif mcap > 1e6:
                mcap_str = f"${mcap / 1e6:.0f}M"
    else:
        info = {}

    # Pre-compute cross-reference data for narrative weaving
    active_scas = get_active_genuine_scas(state)
    insider_sales = _extract_insider_sales_summary(state)
    h52 = safe_float(info.get("fiftyTwoWeekHigh", 0), 0)
    price = safe_float(info.get("currentPrice", info.get("regularMarketPrice", 0)), 0)
    drawdown = (h52 - price) / h52 * 100 if h52 > 0 and price > 0 else 0

    # Supabase litigation history
    lit_cases: list[dict[str, Any]] = []
    if state.acquired_data:
        lit_data = getattr(state.acquired_data, "litigation_data", None)
        if isinstance(lit_data, dict):
            lit_cases = lit_data.get("supabase_cases", [])
        elif lit_data:
            lit_cases = getattr(lit_data, "supabase_cases", []) or []

    has_chronic = len(lit_cases) >= 3

    # 1. Active SCA — THE most critical D&O finding
    if active_scas:
        case = active_scas[0]
        bullets: list[str] = []
        if isinstance(case, dict):
            court = case.get("court", "Unknown court")
            cp_start = case.get("class_period_start", "")
            cp_end = case.get("class_period_end", "")
            drop = case.get("stock_drop_pct")
            filing_date = case.get("filing_date", "")
            allegation_types = []
            for atype in ("accounting", "insider_trading", "earnings", "merger", "ipo_offering"):
                if case.get(f"allegation_{atype}"):
                    allegation_types.append(atype.replace("_", " ").title())

            # Lead bullet: filing facts + defense cost exposure
            bullets.append(
                f"Securities class action filed {filing_date} in {court}. "
                f"This creates immediate defense cost exposure (typically $5-15M for "
                f"{'mega' if mcap > 50e9 else 'large' if mcap > 10e9 else 'mid'}-cap "
                f"companies) and potential settlement/judgment liability "
                f"that must be reserved against the program."
            )

            # Class period + stock movement within it
            if cp_start and cp_end:
                period_bullet = (
                    f"Class period: {cp_start} to {cp_end}. "
                    f"All stock price movement within this window is already subject "
                    f"to the pending claim."
                )
                if drawdown >= 20:
                    period_bullet += (
                        f" The {drawdown:.0f}% decline from the 52-week high "
                        f"provides plaintiffs with the loss causation element "
                        f"required under Dura Pharmaceuticals."
                    )
                bullets.append(period_bullet)

            # Insider sales during class period — scienter narrative
            if insider_sales["total_value"] > 0:
                bullets.append(
                    f"During this period, insiders sold {insider_sales['summary']}. "
                    f"Insider selling during the class period is the cornerstone of "
                    f"scienter allegations — plaintiffs argue executives knew of "
                    f"undisclosed problems and sold before the stock dropped."
                )

            # Stock drop + notional damages
            if drop:
                notional = (h52 - price) * shares_out if shares_out else 0
                notional_str = f"${notional / 1e9:.1f}B" if notional > 1e9 else f"${notional / 1e6:.0f}M" if notional > 1e6 else ""
                drop_bullet = (
                    f"Alleged stock drop of {drop}% forms the basis of "
                    f"loss causation."
                )
                if notional_str:
                    drop_bullet += (
                        f" Notional shareholder losses of {notional_str} "
                        f"virtually guarantee sustained plaintiff interest."
                    )
                bullets.append(drop_bullet)

            # Allegation theories + chronic filer cross-reference
            if allegation_types:
                theories = ", ".join(allegation_types)
                theory_bullet = f"Allegation theories: {theories}."
                if "Earnings" in theories:
                    theory_bullet += (
                        " Earnings-related claims carry the highest settlement "
                        "severity among SCA categories."
                    )
                if has_chronic:
                    theory_bullet += (
                        f" {ticker}'s history as a chronic filer ({len(lit_cases)} "
                        f"prior SCAs) means the plaintiffs' bar has institutional "
                        f"knowledge of how to litigate against this company."
                    )
                bullets.append(theory_bullet)
        else:
            bullets = [
                "Active securities class action creates immediate D&O program exposure — "
                "defense costs, settlement risk, and impaired program renewability."
            ]

        results.append({
            "id": "critical_active_sca",
            "headline": "Active Securities Class Action",
            "severity": "red",
            "is_risk_factor": True,
            "headline_tags": "",
            "badge_value": "ACTIVE CLAIM",
            "evidence_bullets": bullets,
        })

    # 2. Severe stock drawdown (>30%)
    if drawdown >= 30:
        # Estimate DDL-style damages: price decline * float * class period fraction
        # More conservative than raw (high-price) * shares — reflects tradeable float
        decline_per_share = h52 - price
        raw_notional = decline_per_share * shares_out if shares_out else 0
        # Cap at 2x market cap as sanity check (raw DDL can exceed mcap for large drops)
        capped_notional = min(raw_notional, mcap * 2) if mcap > 0 else raw_notional
        notional_str = f"${capped_notional / 1e9:.1f}B" if capped_notional > 1e9 else f"${capped_notional / 1e6:.0f}M" if capped_notional > 1e6 else ""
        bullets = [
            f"Stock declined {drawdown:.0f}% from 52-week high of ${h52:.2f} to "
            f"${price:.2f}. Drawdowns exceeding 25% are the primary statistical "
            f"trigger for Section 10(b) loss causation theories — plaintiffs' counsel "
            f"routinely monitors for drops of this magnitude as filing triggers.",
        ]
        if mcap_str:
            bullets.append(
                f"At {mcap_str} current market cap, a {drawdown:.0f}% decline from "
                f"52-week highs creates massive plaintiff incentive. Even with typical "
                f"certification rates and trading volume discounts, the damages pool "
                f"is large enough to attract every major plaintiffs' firm."
            )
        if active_scas:
            bullets.append(
                "The active SCA confirms this drawdown has already attracted "
                "litigation. The underwriting question is whether additional "
                "claims will follow — derivative suits, ERISA claims, or "
                "state-court actions that sit outside the federal class."
            )
        elif insider_sales["total_value"] > 0:
            bullets.append(
                f"Executive selling ({insider_sales['summary']}) during this "
                f"decline creates the appearance of informed selling that "
                f"plaintiffs' firms actively screen for as a filing catalyst."
            )
        results.append({
            "id": "critical_stock_drawdown",
            "headline": f"{drawdown:.0f}% Stock Decline from 52-Week High",
            "severity": "red",
            "is_risk_factor": True,
            "headline_tags": "",
            "badge_value": "MARKET DATA",
            "evidence_bullets": bullets,
        })

    # 3. Chronic SCA filer
    if has_chronic:
        settled = [c for c in lit_cases if isinstance(c, dict) and str(c.get("case_status", "")).upper() == "SETTLED"]
        total_settled = sum(c.get("settlement_amount_m", 0) or 0 for c in settled)
        dismissed = [c for c in lit_cases if isinstance(c, dict) and str(c.get("case_status", "")).upper() == "DISMISSED"]
        bullets = [
            f"{ticker} has been named defendant in {len(lit_cases)} securities class "
            f"actions — classifying it as a chronic filer. Chronic filers exhibit "
            f"persistent governance or disclosure patterns that attract repeat "
            f"litigation regardless of management changes or operational improvements.",
        ]
        if settled:
            case_word = "case" if len(settled) == 1 else "cases"
            settlement_bullet = (
                f"Settlement history: {len(settled)} {case_word} settled for "
                f"${total_settled:.1f}M total."
            )
            if active_scas:
                settlement_bullet += (
                    " Prior settlement amounts establish a pricing floor — "
                    "the market expects this company to settle, and the active "
                    "SCA confirms the pattern is continuing."
                )
            else:
                settlement_bullet += (
                    " Prior settlement amounts establish a pricing floor — "
                    "the market has already established what this company's "
                    "litigation exposure costs to resolve."
                )
            bullets.append(settlement_bullet)
        if dismissed:
            d_word = "case" if len(dismissed) == 1 else "cases"
            bullets.append(
                f"{len(dismissed)} {d_word} dismissed — but even dismissed SCAs "
                f"generate $3-8M in defense costs and signal ongoing plaintiff "
                f"attention to this company."
            )
        # Filing timeline
        dates = sorted([c.get("filing_date", "") for c in lit_cases if c.get("filing_date")])
        if len(dates) >= 2:
            bullets.append(
                f"Filing history spans {dates[0]} to {dates[-1]}. "
                f"Pricing must reflect the actuarial claim frequency, not just "
                f"the current clean/active status."
            )
        results.append({
            "id": "critical_chronic_filer",
            "headline": f"Chronic SCA Filer — {len(lit_cases)} Historical Filings",
            "severity": "red",
            "is_risk_factor": True,
            "headline_tags": "",
            "badge_value": "SCA DATABASE",
            "evidence_bullets": bullets,
        })

    return results


def _extract_insider_sales_summary(state: AnalysisState) -> dict[str, Any]:
    """Extract insider sales summary for cross-referencing in critical findings.

    Returns dict with:
    - total_value: total dollar value of insider sales
    - top_sellers: list of (name, value) tuples
    - summary: human-readable summary string
    """
    result: dict[str, Any] = {"total_value": 0, "top_sellers": [], "summary": ""}

    md = state.acquired_data.market_data if state.acquired_data else None
    if not md or not isinstance(md, dict):
        return result

    ins = md.get("insider_transactions", {})
    if not isinstance(ins, dict) or not ins.get("Text"):
        return result

    texts = ins.get("Text", [])
    names = ins.get("Insider", [])
    values = ins.get("Value", [])

    sales: list[tuple[str, float]] = []
    for i in range(min(len(texts), len(names))):
        txt = texts[i] if i < len(texts) else ""
        if not txt or "sale" not in str(txt).lower():
            continue
        val = values[i] if i < len(values) else None
        if val and isinstance(val, (int, float)) and val > 0:
            name_parts = str(names[i]).split()
            display = " ".join(w.capitalize() for w in name_parts) if name_parts else str(names[i])
            sales.append((display, float(val)))

    if not sales:
        return result

    sales.sort(key=lambda s: s[1], reverse=True)
    total = sum(v for _, v in sales)
    result["total_value"] = total
    result["top_sellers"] = sales[:3]

    # Build human-readable summary
    if total >= 1e9:
        total_str = f"${total / 1e9:.1f}B"
    elif total >= 1e6:
        total_str = f"${total / 1e6:.1f}M"
    else:
        total_str = f"${total:,.0f}"

    top_name = sales[0][0] if sales else ""
    top_val = sales[0][1] if sales else 0
    if top_val >= 1e6:
        top_str = f"${top_val / 1e6:.1f}M"
    else:
        top_str = f"${top_val:,.0f}"

    if len(sales) == 1:
        result["summary"] = f"{total_str} ({top_name}: {top_str})"
    else:
        result["summary"] = (
            f"{total_str} across {len(sales)} transactions "
            f"(led by {top_name} at {top_str})"
        )

    return result


def _fmt_signal_value(v: Any) -> str:
    """Format a signal value for human display."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "Yes" if v else "No"
    if isinstance(v, (int, float)):
        abs_v = abs(v)
        if abs_v >= 1e9:
            return f"${v / 1e9:.1f}B"
        if abs_v >= 1e6:
            return f"${v / 1e6:.1f}M"
        if abs_v > 100:
            return f"{v:,.0f}"
        if 0 < abs_v < 1:
            return f"{v:.2f}"
        return f"{v:.1f}" if isinstance(v, float) else str(v)
    return str(v)


def _clean_do_context(do_ctx: str) -> str:
    """Extract the useful D&O explanation from do_context, removing jargon prefix."""
    if not do_ctx:
        return ""
    text = do_ctx.strip()
    parts = text.split(". ", 1)
    if len(parts) > 1 and ("signals elevated" in parts[0] or "is in the caution zone" in parts[0]):
        second = parts[1].strip()
        if second.startswith("Monitor for deterioration"):
            match = re.match(r'^(.+?)\s+at\s+(.+?)\s*\((.+?)\)', parts[0])
            if match:
                sig_name, value, _threshold = match.groups()
                return f"{sig_name}: {value}"
            caution_idx = parts[0].find(" is in the caution zone")
            if caution_idx > 0:
                return parts[0][:caution_idx].strip()
            elevated_idx = parts[0].find(" signals elevated")
            if elevated_idx > 0:
                return parts[0][:elevated_idx].strip()
            return parts[0].strip()
        return second
    return text


def _source_label(source: str) -> str:
    """Convert trace_data_source to human-readable label."""
    labels = {
        "SEC_10K": "10-K Filing",
        "SEC_10Q": "10-Q Filing",
        "SEC_DEF14A": "Proxy Statement",
        "SEC_FORM4": "Form 4 (Insider)",
        "SEC_8K": "8-K Filing",
        "SEC_S1": "S-1 Registration",
        "SEC_S3": "S-3 Shelf",
        "SCAC_SEARCH": "Stanford SCA Database",
        "MARKET_PRICE": "Market Data",
    }
    if not source:
        return ""
    key = source.split(":")[0]
    return labels.get(key, key.replace("_", " ").title())


# Risk categories for grouping triggered signals by TOPIC
_RISK_CATEGORIES: list[tuple[str, str, list[str]]] = [
    ("litigation", "Litigation & Legal Exposure", [
        "litigation", "sca", "class action", "settlement", "sol ", "statute",
        "derivative", "allegation", "erisa", "historical suit", "existing securities",
    ]),
    ("insider", "Insider Activity & Executive Risk", [
        "ceo", "cfo", "insider", "exercise", "seller", "tenure", "plan adoption",
        "notable activity", "compensation", "ceo total", "officer",
    ]),
    ("financial", "Financial & Accounting Red Flags", [
        "channel", "liquidity", "working capital", "margin", "etr", "dividend",
        "cash flow", "restatement", "forensic", "accrual", "earnings quality",
        "tax rate", "off-balance",
    ]),
    ("market", "Market & Valuation Risk", [
        "pe ratio", "ev ebitda", "stock", "earnings reaction", "ipo", "offering",
        "short interest", "volatility", "beta", "decline", "drop",
    ]),
    ("operational", "Operational & Regulatory Risk", [
        "supply chain", "supplier", "government", "risk factor", "regulatory",
        "single-source", "macro", "concentration",
    ]),
]


def _categorize_signal(sig_name: str) -> str:
    """Assign a signal to a risk category based on its name."""
    name_lower = sig_name.lower()
    for cat_id, _label, keywords in _RISK_CATEGORIES:
        if any(kw in name_lower for kw in keywords):
            return cat_id
    return "other"


def _is_absence_evidence(value: Any, explanation: str) -> bool:
    """Return True if signal represents ABSENCE of a risk, not its presence."""
    val_str = str(value).lower() if value is not None else ""
    expl_lower = explanation.lower()
    absence_phrases = (
        "not mentioned", "not detected", "not present", "not found",
        "no evidence", "none identified", "none found", "no instances",
    )
    return any(phrase in val_str or phrase in expl_lower for phrase in absence_phrases)


def _is_system_note(explanation: str) -> bool:
    """Return True if explanation is a system/calibration note."""
    lower = explanation.lower()
    return any(phrase in lower for phrase in (
        "recommend calibration", "needs calibration",
        "industry-standard concentration", "signal-driven scoring",
        "coverage=", "base claim frequency",
    ))


def _dedup_bullets(bullets: list[str]) -> list[str]:
    """Remove duplicate or near-duplicate evidence bullets."""
    seen_prefixes: set[str] = set()
    unique: list[str] = []
    for bullet in bullets:
        plain = re.sub(r'<[^>]+>', '', bullet)
        prefix = plain[:60].lower().strip()
        if prefix in seen_prefixes:
            continue
        seen_prefixes.add(prefix)
        unique.append(bullet)
    return unique


def _collect_triggered_signals(state: AnalysisState) -> list[dict[str, Any]]:
    """Collect all triggered signals from state, cleaned and categorized."""
    all_triggered: list[dict[str, Any]] = []
    if not state or not hasattr(state, "analysis") or not state.analysis:
        return all_triggered

    sigs: dict[str, Any] = {}
    if hasattr(state.analysis, "signal_results"):
        sr = state.analysis.signal_results
        sigs = sr if isinstance(sr, dict) else (sr.model_dump() if hasattr(sr, "model_dump") else {})

    for _sid, sig in sigs.items():
        if not isinstance(sig, dict) or sig.get("status") != "TRIGGERED":
            continue
        sig_name = sig.get("signal_name", "")
        do_ctx = sig.get("do_context", "")
        source = sig.get("trace_data_source", sig.get("source", ""))
        category = sig.get("category", "")
        threshold_level = sig.get("threshold_level", "")
        sig_value = sig.get("value")

        explanation = _clean_do_context(do_ctx)
        explanation = re.sub(r'\s*\(threshold:[^)]*\)', '', explanation)

        if _is_absence_evidence(sig_value, explanation):
            continue
        if _is_system_note(explanation):
            continue

        if (not explanation
                or "Monitor for deterioration" in explanation
                or "this agent risk" in explanation
                or "this host risk" in explanation):
            if sig_name and sig_value is not None:
                formatted_val = _fmt_signal_value(sig_value)
                if formatted_val and "not mentioned" not in formatted_val.lower():
                    explanation = f"<b>{sig_name}</b>: {formatted_val}"
                else:
                    continue
            else:
                continue
        if explanation.startswith("triggered "):
            explanation = explanation[len("triggered "):]

        all_triggered.append({
            "name": sig_name,
            "name_lower": sig_name.lower(),
            "value": _fmt_signal_value(sig_value),
            "explanation": explanation,
            "source": _source_label(source),
            "category": _categorize_signal(sig_name),
            "is_decision_driving": category == "DECISION_DRIVING",
            "threshold_level": threshold_level or "yellow",
        })
    return all_triggered


# Keyword maps: risk factor category -> signal name keywords that confirm it
_RF_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "REGULATORY": [
        "regulatory", "government", "risk factor", "compliance", "enforcement",
        "antitrust", "dma", "statute", "sol ", "open statute",
    ],
    "LITIGATION": [
        "litigation", "sca", "class action", "settlement", "derivative",
        "allegation", "erisa", "existing securities", "active sca", "historical suit",
    ],
    "FINANCIAL": [
        "channel", "liquidity", "working capital", "margin", "etr", "dividend",
        "cash flow", "restatement", "forensic", "accrual", "earnings quality",
        "tax rate", "off-balance",
    ],
    "COMPETITIVE": [
        "concentration", "single-source", "supplier", "supply chain",
        "product concentration", "macro",
    ],
    "TECHNOLOGY": [
        "cyber", "data breach", "technology", "ip ", "patent",
    ],
    "GOVERNANCE": [
        "ceo", "cfo", "insider", "exercise", "seller", "tenure",
        "compensation", "officer", "board",
    ],
    "COMPLIANCE": [
        "sox", "fcpa", "internal control", "material weakness",
    ],
    "ESG": ["esg", "climate", "environmental", "social"],
    "CYBER": ["cyber", "data breach", "ransomware", "privacy"],
}


def _match_signals_to_risk_factor(
    rf_title: str,
    rf_category: str,
    all_signals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Find triggered signals that confirm or quantify a specific risk factor.

    Matching is deliberately strict to avoid showing irrelevant signals:
    - Category keyword match requires ALSO matching a title word (>4 chars)
    - Title-only match requires matching 2+ significant words (>5 chars)
    - Signal explanation text is also checked for title keywords
    """
    matches: list[dict[str, Any]] = []
    title_lower = rf_title.lower()

    cat_keywords = _RF_SIGNAL_KEYWORDS.get(rf_category, [])
    title_words_strict = [w for w in re.split(r'\W+', title_lower) if len(w) >= 5]
    title_words_broad = [w for w in re.split(r'\W+', title_lower) if len(w) >= 4]

    for sig in all_signals:
        name_lower = sig["name_lower"]
        expl_lower = sig.get("explanation", "").lower()

        # Strategy 1: Category keyword + title word overlap
        cat_match = any(kw in name_lower for kw in cat_keywords)
        title_broad = any(tw in name_lower or tw in expl_lower for tw in title_words_broad)
        if cat_match and title_broad:
            matches.append(sig)
            continue

        # Strategy 2: Strong title overlap (2+ strict words in signal name/explanation)
        strict_hits = sum(1 for tw in title_words_strict if tw in name_lower or tw in expl_lower)
        if strict_hits >= 2:
            matches.append(sig)

    return matches


def _sv(obj: Any, key: str) -> str:
    """Extract scalar value from a SourcedValue dict/object or plain field."""
    if obj is None:
        return ""
    val = obj.get(key) if isinstance(obj, dict) else getattr(obj, key, None)
    if val is None:
        return ""
    # Handle SourcedValue dict (from JSON)
    if isinstance(val, dict) and "value" in val:
        return str(val.get("value", ""))
    # Handle SourcedValue Pydantic object
    if hasattr(val, "value"):
        return str(val.value) if val.value is not None else ""
    return str(val)


def _fmt_dollars(amount: float | int) -> str:
    """Format a dollar amount for human display."""
    if amount >= 1e12:
        return f"${amount / 1e12:.1f}T"
    if amount >= 1e9:
        return f"${amount / 1e9:.1f}B"
    if amount >= 1e6:
        return f"${amount / 1e6:.1f}M"
    if amount >= 1e3:
        return f"${amount / 1e3:.0f}K"
    return f"${amount:,.0f}"


def _enrich_risk_factor_finding(
    finding: dict[str, Any],
    rf_category: str,
    state: AnalysisState,
    used_enrichments: set[str],
) -> None:
    """Add specific data points to a risk factor finding from state data.

    Pulls actual case names, dollar amounts, regulatory fines, and DDL
    exposure from extracted/acquired data to replace generic commentary.
    Tracks used_enrichments to avoid showing DDL on multiple findings.
    """
    title_lower = finding["headline"].lower()
    bullets = finding["evidence_bullets"]

    # --- Determine what enrichment this specific finding needs ---
    # "General legal" = umbrella finding about all litigation (gets case names + DDL)
    is_general_legal = rf_category == "LITIGATION" and any(
        kw in title_lower for kw in ("legal proceedings", "contingencies", "claims")
    )
    # "Primary litigation" = LITIGATION category but about a specific case/topic
    is_primary_litigation = rf_category == "LITIGATION" and not is_general_legal
    is_regulatory = rf_category == "REGULATORY" or any(
        kw in title_lower for kw in ("antitrust", "regulatory", "enforcement", "compliance", "dma")
    )
    is_financial = rf_category == "FINANCIAL" or any(
        kw in title_lower for kw in ("revenue", "tariff", "macroeconomic", "financial")
    )

    # --- Litigation enrichment ---
    if is_general_legal:
        # The umbrella "Legal proceedings" finding gets case names + DDL
        show_cases = "sca_cases" not in used_enrichments
        show_ddl = "ddl" not in used_enrichments
        _enrich_litigation(
            bullets, state,
            show_ddl=show_ddl,
            show_cases=show_cases,
        )
        if show_cases:
            used_enrichments.add("sca_cases")
        if show_ddl:
            used_enrichments.add("ddl")
    elif is_primary_litigation:
        # Specific litigation findings (e.g., "Epic Games") get DDL only, not case list
        show_ddl = "ddl" not in used_enrichments
        if show_ddl:
            _enrich_litigation(
                bullets, state,
                show_ddl=True,
                show_cases=False,
            )
            used_enrichments.add("ddl")

    # --- Regulatory enrichment ---
    if is_regulatory:
        _enrich_regulatory(bullets, state, title_lower)

    # --- Financial impact enrichment ---
    if is_financial:
        _enrich_financial_impact(bullets, state, title_lower, used_enrichments)


def _enrich_litigation(
    bullets: list[str],
    state: AnalysisState,
    *,
    show_ddl: bool = True,
    show_cases: bool = True,
) -> None:
    """Add specific case names, courts, and DDL to litigation-related findings."""
    if not state.extracted or not state.extracted.litigation:
        return
    lit = state.extracted.litigation

    # Active case names (only shown once to avoid repetition across findings)
    if show_cases:
        scas = lit.securities_class_actions or [] if hasattr(lit, "securities_class_actions") else []
        if isinstance(scas, list):
            active = [s for s in scas if _sv(s, "status") in ("ACTIVE", "PENDING")]
            for sca in active[:2]:
                name = _sv(sca, "case_name")
                court = _sv(sca, "court")
                if name and name != "<UNKNOWN>":
                    bullet = f'<b>{name}</b>'
                    if court and court != "<UNKNOWN>":
                        bullet += f' ({court})'
                    bullet += ' — <span style="color:#DC2626">ACTIVE</span>'
                    bullets.append(bullet)

    # DDL exposure (only shown once across all findings)
    if show_ddl and state.analysis:
        sp = state.analysis.settlement_prediction
        if sp and isinstance(sp, dict):
            ddl = sp.get("ddl_amount", 0)
            tower = sp.get("tower_risk", {})
            primary = tower.get("primary", {}) if isinstance(tower, dict) else {}
            expected_loss = primary.get("expected_loss_amount", 0) if isinstance(primary, dict) else 0
            if ddl and isinstance(ddl, (int, float)) and ddl > 0:
                bullet = f'Maximum DDL: <b>{_fmt_dollars(ddl)}</b>'
                if expected_loss and isinstance(expected_loss, (int, float)) and expected_loss > 0:
                    bullet += f' — primary layer expected loss: <b>{_fmt_dollars(expected_loss)}</b>'
                bullets.append(bullet)


def _enrich_regulatory(
    bullets: list[str], state: AnalysisState, title_lower: str,
) -> None:
    """Add specific regulatory agency actions, fine amounts, and proceedings."""
    if not state.extracted or not state.extracted.litigation:
        return
    lit = state.extracted.litigation
    reg_procs = lit.regulatory_proceedings if hasattr(lit, "regulatory_proceedings") else []
    if not isinstance(reg_procs, list):
        return

    for proc in reg_procs[:3]:
        val = proc.get("value", proc) if isinstance(proc, dict) else proc
        if not isinstance(val, dict):
            continue
        agency = val.get("agency", "")
        desc = val.get("description", "")
        if not agency or not desc:
            continue
        # Only add if relevant to this finding's topic
        if "antitrust" in title_lower and agency not in ("DOJ", "EC", "EU", "FTC"):
            continue
        bullets.append(
            f'<b>{agency}</b>: {desc}'
            f' <span style="color:#9CA3AF;font-size:7pt">(Regulatory)</span>'
        )


def _enrich_financial_impact(
    bullets: list[str],
    state: AnalysisState,
    title_lower: str,
    used_enrichments: set[str] | None = None,
) -> None:
    """Add revenue, market cap, and financial exposure data (once only)."""
    if used_enrichments and "financial_impact" in used_enrichments:
        return
    if used_enrichments is not None:
        used_enrichments.add("financial_impact")

    mkt_info: dict[str, Any] = {}
    if state.acquired_data and hasattr(state.acquired_data, "market_data"):
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            mkt_info = md.get("info", {})

    revenue = mkt_info.get("totalRevenue", 0) if isinstance(mkt_info, dict) else 0
    market_cap = mkt_info.get("marketCap", 0) if isinstance(mkt_info, dict) else 0

    if revenue and isinstance(revenue, (int, float)) and revenue > 0:
        bullets.append(
            f'Total revenue at risk: <b>{_fmt_dollars(revenue)}</b>'
            f' <span style="color:#9CA3AF;font-size:7pt">(Market Data)</span>'
        )
    if market_cap and isinstance(market_cap, (int, float)) and market_cap > 0:
        bullets.append(
            f'Current market cap: <b>{_fmt_dollars(market_cap)}</b>'
            f' <span style="color:#9CA3AF;font-size:7pt">(Market Data)</span>'
        )


def _build_signal_litigation_bullets(state: AnalysisState) -> list[str]:
    """Build specific litigation bullets from state data for signal-only findings."""
    bullets: list[str] = []
    if not state.extracted or not state.extracted.litigation:
        return bullets
    lit = state.extracted.litigation

    # Active SCAs with case names
    scas = lit.securities_class_actions or [] if hasattr(lit, "securities_class_actions") else []
    if isinstance(scas, list):
        active = [s for s in scas if _sv(s, "status") in ("ACTIVE", "PENDING")]
        settled = [s for s in scas if _sv(s, "status") == "SETTLED"]
        if active:
            for sca in active[:3]:
                name = _sv(sca, "case_name")
                court = _sv(sca, "court")
                if name and name != "<UNKNOWN>":
                    bullet = f'<b>{name}</b>'
                    if court and court != "<UNKNOWN>":
                        bullet += f' ({court})'
                    bullet += ' — <span style="color:#DC2626">ACTIVE</span>'
                    bullets.append(bullet)
        if settled:
            bullets.append(
                f'{len(settled)} prior securities action(s) settled — establishes litigation history'
            )

    # Derivative suits
    deriv = lit.derivative_suits if hasattr(lit, "derivative_suits") else []
    if isinstance(deriv, list) and deriv:
        bullets.append(f'<b>{len(deriv)}</b> derivative suit(s) filed — direct board/officer liability')

    # DDL
    if state.analysis:
        sp = state.analysis.settlement_prediction
        if sp and isinstance(sp, dict):
            ddl = sp.get("ddl_amount", 0)
            tower = sp.get("tower_risk", {})
            primary = tower.get("primary", {}) if isinstance(tower, dict) else {}
            expected_loss = primary.get("expected_loss_amount", 0) if isinstance(primary, dict) else 0
            if ddl and isinstance(ddl, (int, float)) and ddl > 0:
                bullet = f'Maximum DDL: <b>{_fmt_dollars(ddl)}</b>'
                if expected_loss and isinstance(expected_loss, (int, float)) and expected_loss > 0:
                    bullet += f' — primary layer expected loss: <b>{_fmt_dollars(expected_loss)}</b>'
                bullets.append(bullet)

    # SOL map
    sol_map = lit.sol_map if hasattr(lit, "sol_map") else None
    if sol_map and isinstance(sol_map, dict):
        open_windows = sum(
            1 for v in sol_map.values()
            if isinstance(v, dict) and v.get("value", {}).get("status") == "OPEN"
        )
        if open_windows:
            bullets.append(
                f'<b>{open_windows}</b> open statute-of-limitations window(s) — unexpired claim exposure'
            )

    return bullets


def _build_signal_insider_bullets(state: AnalysisState) -> list[str]:
    """Build specific insider activity bullets from state data."""
    bullets: list[str] = []

    # Get actual insider transaction data
    mkt_data = {}
    if state.acquired_data and hasattr(state.acquired_data, "market_data"):
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            mkt_data = md

    ins = mkt_data.get("insider_transactions", {})
    if isinstance(ins, dict) and ins.get("Text"):
        texts = ins.get("Text", [])
        names = ins.get("Insider", [])
        positions = ins.get("Position", [])
        values = ins.get("Value", [])
        dates = ins.get("Start Date", [])

        # Find actual sales with dollar values
        sales: list[dict[str, Any]] = []
        for i in range(min(len(texts), len(names))):
            txt = texts[i] if i < len(texts) else ""
            if not txt or "sale" not in str(txt).lower():
                continue
            val = values[i] if i < len(values) else None
            if val and isinstance(val, (int, float)) and val > 0:
                sales.append({
                    "name": names[i] if i < len(names) else "",
                    "position": positions[i] if i < len(positions) else "",
                    "text": txt,
                    "value": val,
                    "date": dates[i] if i < len(dates) else "",
                })

        # Show top sellers by value
        sales.sort(key=lambda s: s["value"], reverse=True)
        for sale in sales[:3]:
            name_parts = sale["name"].split()
            display_name = " ".join(w.capitalize() for w in name_parts) if name_parts else sale["name"]
            bullets.append(
                f'<b>{display_name}</b> ({sale["position"]}): '
                f'sold {_fmt_dollars(sale["value"])} on {sale["date"]}'
            )

        if sales:
            total_sold = sum(s["value"] for s in sales)
            bullets.append(
                f'Total insider sales: <b>{_fmt_dollars(total_sold)}</b> across {len(sales)} transactions'
            )

    # Executive risk findings
    if state.analysis and hasattr(state.analysis, "executive_risk"):
        exec_risk = state.analysis.executive_risk
        if isinstance(exec_risk, dict):
            kf = exec_risk.get("key_findings", [])
            for finding in kf[:2]:
                if isinstance(finding, str) and finding.strip():
                    bullets.append(finding)

    return bullets


def _build_risk_factor_findings(
    risk_factors: list[Any],
    all_signals: list[dict[str, Any]],
    state: AnalysisState | None = None,
) -> tuple[list[dict[str, Any]], set[str]]:
    """Build findings from 10-K risk factors with HIGH/MEDIUM D&O relevance."""
    results: list[dict[str, Any]] = []
    used_signal_names: set[str] = set()
    used_enrichments: set[str] = set()  # Track which enrichments have been shown

    for rf in risk_factors:
        if isinstance(rf, dict):
            title = rf.get("title", "")
            category = rf.get("category", "OTHER")
            severity = rf.get("severity", "MEDIUM")
            is_new = rf.get("is_new_this_year", False)
            do_relevance = rf.get("do_relevance", "MEDIUM")
            source_passage = rf.get("source_passage", "")
        else:
            title = getattr(rf, "title", "")
            category = getattr(rf, "category", "OTHER")
            severity = getattr(rf, "severity", "MEDIUM")
            is_new = getattr(rf, "is_new_this_year", False)
            do_relevance = getattr(rf, "do_relevance", "MEDIUM")
            source_passage = getattr(rf, "source_passage", "")

        if do_relevance not in ("HIGH", "MEDIUM"):
            continue

        confirming = _match_signals_to_risk_factor(title, category, all_signals)
        for sig in confirming:
            used_signal_names.add(sig["name"])

        evidence_bullets: list[str] = []

        # Primary: the actual 10-K disclosure — but ONLY if it contains
        # company-specific data (dollar amounts, dates, names), not generic
        # boilerplate that could apply to any company.
        _10K_BOILERPLATE = (
            "we are, and may in the future be",
            "subject to various",
            "arising in the ordinary course",
            "from time to time",
            "party to legal matters",
            "may be involved in certain",
            "could seriously harm our business",
            "could have a material adverse",
            "expensive and time-consuming",
            "litigation matters that are expensive",
            "if resolved adversely",
        )
        if source_passage:
            passage_lower = source_passage.lower()
            is_10k_boilerplate = any(bp in passage_lower for bp in _10K_BOILERPLATE)
            if not is_10k_boilerplate:
                passage = source_passage
                evidence_bullets.append(
                    f'<span style="color:#374151">{passage}</span>'
                    f' <span style="color:#9CA3AF;font-size:7pt">(10-K Filing)</span>'
                )

        # Secondary: confirming signal data — only quantitative, not boilerplate
        _SIGNAL_BOILERPLATE = (
            "plaintiffs allege", "may signal", "creates personal liability",
            "strongest predictor", "signal management has identified",
            "represent unexpired claim", "may subsequently", "premature de-risking",
            "litigation velocity", "signals elevated",
            "boolean check", "thresholds (red",
            "from d&o underwriting practice and claims experience",
            "from d&o claims experience",
            "mention(s):",
        )
        for sig in confirming[:3]:
            expl = sig["explanation"]
            plain = re.sub(r'<[^>]+>', '', expl)
            has_data = bool(re.search(r'\d', plain))
            is_boilerplate = any(phrase in plain.lower() for phrase in _SIGNAL_BOILERPLATE)
            if not has_data or is_boilerplate:
                continue
            # Truncate cleanly at word boundary if too long
            if len(plain) > 200:
                cut = plain[:197].rsplit(" ", 1)[0]
                plain = cut + "..."
                expl = plain
            bullet = expl
            if sig["source"]:
                bullet += f' <span style="color:#9CA3AF;font-size:7pt">({sig["source"]})</span>'
            evidence_bullets.append(bullet)

        # Enrichment: add specific data from state (case names, $ amounts, DDL)
        if state:
            _enrich_risk_factor_finding(
                {"headline": title, "evidence_bullets": evidence_bullets},
                category,
                state,
                used_enrichments,
            )

        evidence_bullets = _dedup_bullets(evidence_bullets)[:5]

        # Severity based on D&O relevance + risk factor severity
        if do_relevance == "HIGH" and severity == "HIGH":
            finding_severity = "red"
        elif do_relevance == "HIGH" or severity == "HIGH":
            finding_severity = "red" if confirming else "yellow"
        else:
            finding_severity = "yellow"

        # Build tags
        tags: list[str] = []
        if is_new:
            tags.append("NEW")
        if do_relevance == "HIGH":
            tags.append("HIGH D&O")

        tag_html = ""
        if tags:
            tag_parts = []
            for tag in tags:
                if tag == "NEW":
                    tag_parts.append(
                        '<span style="display:inline-block;padding:1px 5px;border-radius:3px;'
                        'font-size:7pt;font-weight:700;background:#7C3AED;color:white;'
                        'margin-left:4px;vertical-align:middle">NEW</span>'
                    )
                else:
                    tag_parts.append(
                        '<span style="display:inline-block;padding:1px 5px;border-radius:3px;'
                        'font-size:7pt;font-weight:700;background:#DC2626;color:white;'
                        'margin-left:4px;vertical-align:middle">HIGH D&O</span>'
                    )
            tag_html = "".join(tag_parts)

        results.append({
            "id": f"rf_{category.lower()}_{len(results)}",
            "name": title,
            "headline": title,
            "headline_tags": tag_html,
            "evidence_bullets": evidence_bullets,
            "signal_count": len(confirming),
            "points": severity,
            "max": do_relevance,
            "pct": 100 if finding_severity == "red" else 50,
            "severity": finding_severity,
            "badge_value": severity,
            "is_risk_factor": True,
        })

    return results, used_signal_names


def _build_signal_only_findings(
    all_signals: list[dict[str, Any]],
    exclude_names: set[str],
    state: AnalysisState | None = None,
) -> list[dict[str, Any]]:
    """Build fallback findings from triggered signals not covered by risk factors."""
    remaining_signals = [s for s in all_signals if s["name"] not in exclude_names]

    by_category: dict[str, list[dict[str, Any]]] = {}
    for sig in remaining_signals:
        by_category.setdefault(sig["category"], []).append(sig)

    results: list[dict[str, Any]] = []
    for cat_id, cat_label, _keywords in _RISK_CATEGORIES:
        cat_signals = by_category.get(cat_id, [])
        if not cat_signals:
            continue

        cat_signals.sort(key=lambda s: (
            0 if s["is_decision_driving"] else 1,
            0 if s["threshold_level"] == "red" else 1,
        ))

        # Try to build specific data-driven bullets from state FIRST
        evidence_bullets: list[str] = []
        if state:
            if cat_id == "litigation":
                evidence_bullets = _build_signal_litigation_bullets(state)
            elif cat_id == "insider":
                evidence_bullets = _build_signal_insider_bullets(state)

        # Fall back to signal explanations only if no specific data found
        if not evidence_bullets:
            _SIGNAL_JUNK = (
                "mention(s):", "boolean check", "thresholds (red",
                "from d&o underwriting practice", "from d&o claims experience",
                "signals elevated", "plaintiffs allege", "may signal",
                "strongest predictor", "creates personal liability",
                "litigation velocity", "represent unexpired claim",
            )
            # Negation phrases that mean the signal is a false positive
            _NEGATION_PHRASES = (
                "do not have any", "does not have any",
                "do not have holdings", "no holdings in",
                "not a party to", "no variable interest",
                "do not maintain any", "do not consolidate any",
            )
            for sig in cat_signals[:5]:
                expl = sig["explanation"]
                expl_lower = expl.lower()
                # Skip if signal evidence contains negation (false positive)
                if any(neg in expl_lower for neg in _NEGATION_PHRASES):
                    continue
                # Skip generic brain YAML boilerplate
                if any(junk in expl_lower for junk in _SIGNAL_JUNK):
                    continue
                # Truncate at sentence boundary, not mid-word
                plain = re.sub(r'<[^>]+>', '', expl)
                if len(plain) > 200:
                    cut = plain[:200].rsplit(". ", 1)[0]
                    if len(cut) < 50:
                        cut = plain[:200].rsplit(" ", 1)[0]
                    plain = cut + "..."
                    expl = plain
                bullet = expl
                if sig["source"]:
                    bullet += f' <span style="color:#9CA3AF;font-size:7pt">({sig["source"]})</span>'
                evidence_bullets.append(bullet)

        evidence_bullets = _dedup_bullets(evidence_bullets)[:5]

        # Note: signal count intentionally omitted — system jargon not shown to underwriters

        red_count = sum(1 for s in cat_signals if s["threshold_level"] == "red")
        severity = "red" if red_count >= 3 else "yellow" if red_count >= 1 else "green"

        results.append({
            "id": cat_id,
            "name": cat_label,
            "headline": cat_label,
            "headline_tags": "",
            "evidence_bullets": evidence_bullets,
            "signal_count": len(cat_signals),
            "points": str(red_count),
            "max": str(len(cat_signals)),
            "pct": red_count / len(cat_signals) * 100 if cat_signals else 0,
            "severity": severity,
            "badge_value": f"{len(cat_signals)}",
            "is_risk_factor": False,
        })

    return results


def findings(ctx: dict[str, Any], scoring: dict[str, Any], state: AnalysisState | None = None) -> None:
    """Build key risk findings from REAL company-specific risks.

    PRIMARY: 10-K Risk Factors with HIGH D&O relevance.
    SECONDARY: Triggered signals not covered by risk factors.
    """
    all_signals = _collect_triggered_signals(state)

    # Build from 10-K risk factors (PRIMARY)
    risk_factors: list[Any] = []
    if state and state.extracted:
        rfs = state.extracted.risk_factors
        if rfs:
            relevance_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            risk_factors = sorted(rfs, key=lambda rf: (
                relevance_order.get(
                    rf.get("do_relevance", "LOW") if isinstance(rf, dict)
                    else getattr(rf, "do_relevance", "LOW"), 3),
                not (rf.get("is_new_this_year", False) if isinstance(rf, dict)
                     else getattr(rf, "is_new_this_year", False)),
                severity_order.get(
                    rf.get("severity", "LOW") if isinstance(rf, dict)
                    else getattr(rf, "severity", "LOW"), 3),
            ))

    rf_results: list[dict[str, Any]] = []
    used_signal_names: set[str] = set()
    if risk_factors:
        rf_results, used_signal_names = _build_risk_factor_findings(risk_factors, all_signals, state)

    # Build signal-only findings for uncovered categories (SECONDARY)
    signal_results = _build_signal_only_findings(all_signals, used_signal_names, state)

    # --- Build final Key Risk Findings list ---
    # PRIMARY PATH: LLM synthesis — produces integrated underwriter narrative
    # FALLBACK PATH: f-string critical findings + secondary risk factors
    if state:
        try:
            from do_uw.stages.render.context_builders.risk_synthesis import (
                synthesize_key_findings,
            )
            synth = synthesize_key_findings(state)
            if synth and len(synth) >= 3:
                ctx["key_findings"] = synth
                ctx["red_count"] = sum(1 for f in synth if f["severity"] == "red")
                ctx["yellow_count"] = sum(1 for f in synth if f["severity"] == "yellow")
                return
        except Exception:
            logger.warning("LLM synthesis unavailable, using f-string fallback", exc_info=True)

    # FALLBACK: f-string critical findings
    critical_findings = _build_critical_findings(state)

    # Critical findings take the first N slots — guaranteed
    results: list[dict[str, Any]] = list(critical_findings)

    # Fill remaining slots (up to 5 total) from rf + signal results
    # STRATEGY: Critical findings already cover active SCAs, stock crash, chronic
    # filer, and insider sales (woven into SCA scienter narrative). The remaining
    # slots must answer: "What GO-FORWARD risks could trigger the NEXT claim?"
    # A 30-year underwriter doesn't rehash what's already in findings #1-3 —
    # they look at strategic exposures: financial leverage, revenue concentration,
    # regulatory overhang, M&A integration risk, governance gaps.
    remaining_slots = max(0, 5 - len(results))
    if remaining_slots > 0:
        secondary = rf_results + signal_results

        # Determine which categories are already covered by critical findings
        critical_ids = {r.get("id", "") for r in results}
        has_sca = "critical_active_sca" in critical_ids
        has_chronic = "critical_chronic_filer" in critical_ids

        # Filter out redundant findings — these are already in the critical section
        filtered: list[dict[str, Any]] = []
        for r in secondary:
            headline_lower = r.get("headline", "").lower()
            fid = r.get("id", "")

            # Skip insider findings when SCA finding already includes scienter narrative
            if has_sca and (
                "insider" in fid or "insider" in headline_lower
                or "executive risk" in headline_lower
            ):
                continue

            # Skip generic litigation findings when SCA/chronic already present
            if (has_sca or has_chronic) and (
                "class action" in headline_lower
                or ("litigation" in headline_lower and "privacy" not in headline_lower
                    and "regulatory" not in headline_lower)
            ):
                continue

            filtered.append(r)

        # Sort: go-forward strategic risks first, then severity
        # Underwriter priority: what could cause the NEXT claim?
        _GO_FORWARD_ORDER = {
            "financial": 0,     # Leverage, distress, restatement risk
            "operational": 1,   # Concentration, supply chain, key person
            "regulatory": 2,    # Government action, compliance, DMA
            "cyber": 3,         # Data breach, privacy (forward exposure)
            "market": 4,        # Valuation, guidance, analyst expectations
            "litigation": 5,    # Non-SCA litigation (already covered above)
            "insider": 6,       # Already in SCA narrative
        }

        def _strategic_key(f: dict[str, Any]) -> tuple[int, int, int]:
            sev = 0 if f["severity"] == "red" else 1
            fid = f.get("id", "")
            cat = fid.split("_")[1] if fid.startswith("rf_") and len(fid.split("_")) > 1 else fid
            # Bonus for risk factors with confirming signals (cross-validated)
            has_signals = 1 if len(f.get("evidence_bullets", [])) > 1 else 2
            return (has_signals, _GO_FORWARD_ORDER.get(cat, 5), sev)

        filtered.sort(key=_strategic_key)
        for r in filtered:
            if len(results) >= 5:
                break
            results.append(r)

    ctx["key_findings"] = results
    ctx["red_count"] = sum(1 for f in results if f["severity"] == "red")
    ctx["yellow_count"] = sum(1 for f in results if f["severity"] == "yellow")
