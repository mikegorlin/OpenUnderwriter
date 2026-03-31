"""Per-section commentary prompt builders for dual-voice generation.

Each section gets a tailored dual-voice prompt producing:
- WHAT WAS SAID: factual data summary (numbers only, no interpretation)
- UNDERWRITING COMMENTARY: D&O risk interpretation with SCA theory refs

Split from commentary_generator.py for 500-line compliance.
Phase 130 Plan 01 deliverable.
"""

from __future__ import annotations

import json
from typing import Any

# ---------------------------------------------------------------------------
# Commentary rules (appended to every section prompt)
# ---------------------------------------------------------------------------
COMMENTARY_RULES = (
    "You are writing DUAL-VOICE commentary for a D&O underwriting worksheet section.\n"
    "Return TWO clearly labeled sections:\n\n"
    "WHAT WAS SAID:\n"
    "[2-4 sentences. ONLY facts: dollar amounts, percentages, dates, names. "
    "No interpretation. No opinion. This is what the filings/data show.]\n\n"
    "UNDERWRITING COMMENTARY:\n"
    "[3-6 sentences. D&O risk interpretation. Reference specific SCA litigation "
    "theories by name. "
    "Explain WHY this matters for D&O claims.]\n\n"
    "SCA Litigation Theory Reference (use these by name):\n"
    "PLAINTIFF THEORIES:\n"
    "- Section 10(b)/Rule 10b-5: material misstatement + stock drop\n"
    "- Scienter (Tellabs v. Makor): insider selling, internal docs establish knowledge\n"
    "- Loss causation (Dura Pharmaceuticals v. Broudo): corrective disclosure + economic loss\n"
    "- Section 11 strict liability (Securities Act 1933): misstatement in registration\n"
    "- Forward guidance fraud (PSLRA safe harbor exception): guidance with knowledge of falsity\n"
    "- Going-concern allegations: Z-Score distress + failure to disclose\n"
    "- Broken business narrative: touted business model fails, stock drops\n"
    "- Caremark duty of oversight (Marchand v. Barnhill): board failed monitoring\n"
    "- Duty of candor: directors misled shareholders in proxy\n"
    "- Restatement exposure: Section 10(b) + Section 11 dual exposure\n"
    "DEFENSE THEORIES:\n"
    "- PSLRA safe harbor: forward-looking statement with meaningful cautionary language\n"
    "- Loss causation defense: decline attributable to market/sector\n"
    "- No scienter: no insider selling, no contradicting internal documents\n"
    "- Puffery defense (Omnicare v. Laborers): statements too vague to be actionable\n"
    "- Truth-on-the-market: risk already known to market\n"
    "- Clean audit trail: SOX 302/906, no material weakness\n"
    "- Beat-and-raise pattern: consistent delivery removes guidance fraud vector\n\n"
    "Rules:\n"
    "- Every sentence MUST contain company-specific data.\n"
    "- In WHAT WAS SAID: zero interpretation, zero opinion.\n"
    "- In UNDERWRITING COMMENTARY: every claim connects to a named SCA theory.\n"
    "- NEVER reference scoring factors (F1-F10), signal IDs, check ratios, "
    "composite scores, deduction points, or any scoring engine terminology.\n"
    "- No generic phrases. No hedging. No filler. No 10-K boilerplate.\n"
    "- BANNED phrases (DELETE any sentence containing these): "
    "'warrants further investigation', 'demonstrates a commitment', "
    "'going forward', 'remains to be seen', 'subject to various', "
    "'arising in the ordinary course', 'from time to time', "
    "'various legal proceedings', 'could have a material adverse', "
    "'the company believes', 'management believes that', "
    "'in the normal course of business', 'no assurance', "
    "'party to legal matters', 'may be involved in certain'.\n"
)

# ---------------------------------------------------------------------------
# Section-to-signal prefix mapping
# ---------------------------------------------------------------------------
SECTION_PREFIX_MAP: dict[str, list[str]] = {
    "financial": ["FIN."],
    "market": ["STOCK.", "FWRD."],
    "governance": ["GOV.", "EXEC."],
    "litigation": ["LIT."],
    "scoring": ["BIZ."],
    "company": ["BIZ."],
    "executive_brief": [
        "FIN.", "STOCK.", "GOV.", "LIT.", "BIZ.", "EXEC.", "FWRD.",
    ],
    "meeting_prep": ["FIN.", "STOCK.", "GOV.", "LIT.", "BIZ."],
}


# ---------------------------------------------------------------------------
# Section-specific synthesis guidance
# ---------------------------------------------------------------------------
SECTION_GUIDANCE: dict[str, str] = {
    "financial": (
        "SECTION FOCUS: Lead with revenue trend and profitability trajectory. "
        "State Altman Z-Score zone and Beneish M-Score zone explicitly — these "
        "are the two forensic indicators underwriters check first. "
        "Connect to specific litigation theories: going-concern (Z-Score distress), "
        "restatement exposure (M-Score manipulation zone), earnings quality "
        "(cash flow vs. accruals divergence). Cite actual dollar amounts for "
        "revenue, net income, debt, and cash."
    ),
    "market": (
        "SECTION FOCUS: Lead with the largest stock decline and its catalyst. "
        "State the Dollar-Day Loss (DDL) if available — this is the primary "
        "damages metric in SCA complaints. Cover insider selling patterns: "
        "net direction, total value, whether 10b5-1 plans cover the sales. "
        "Connect to Dura Pharmaceuticals loss causation and Tellabs scienter. "
        "Cite specific stock prices, dates, and percentage declines."
    ),
    "governance": (
        "SECTION FOCUS: Lead with board independence percentage and CEO/Chair "
        "duality status — these are the two governance metrics that most "
        "directly affect D&O exposure. Cover say-on-pay results, executive "
        "departures in last 18 months, and overboarding. Connect to Caremark "
        "duty of oversight, Marchand v. Barnhill monitoring failures, and "
        "duty of candor in proxy statements."
    ),
    "litigation": (
        "SECTION FOCUS: Lead with active case count and most significant "
        "pending matter. State class periods, lead counsel tier, and "
        "settlement history with dollar amounts. Distinguish between "
        "10b-5 (Exchange Act) and Section 11 (Securities Act) claims. "
        "Cover SEC enforcement pipeline stage if applicable. "
        "Note any industry-wide litigation sweep affecting this sector."
    ),
    "company": (
        "SECTION FOCUS: Lead with what this company does and how it makes "
        "money — revenue model type and concentration risk. Cover the "
        "specific D&O triggers for THIS business model (guidance dependency "
        "for growth companies, regulatory exposure for financial services, "
        "product liability for manufacturers). Cite revenue segments, "
        "customer concentration percentages, and geographic footprint."
    ),
    "scoring": (
        "SECTION FOCUS: Lead with the overall risk tier and quality score. "
        "Identify the top 2-3 factors driving the score — cite the specific "
        "deductions and what evidence supports them. Explain what tier "
        "placement means for pricing: claim probability range, expected "
        "severity band, recommended underwriting action."
    ),
    "executive_brief": (
        "SECTION FOCUS: This is the first thing the underwriter reads. "
        "Lead with a one-sentence risk verdict. Then the 2-3 most material "
        "findings with specific numbers. Then the recommended action. "
        "No background — the reader is a D&O expert who wants the punchline."
    ),
    "meeting_prep": (
        "SECTION FOCUS: Generate questions a senior underwriter would ask "
        "the broker or insured in a submission meeting. Each question should "
        "reference a specific finding from the analysis and probe for "
        "additional context the data couldn't provide."
    ),
}


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def build_commentary_prompt(
    section_id: str,
    section_data: dict[str, Any],
    triggered_signals: list[dict[str, Any]],
    do_context_refs: list[str],
    scoring_factors: dict[str, Any] | None,
    confidence: str,
    company_name: str = "",
    ticker: str = "",
    sector: str = "",
) -> str:
    """Build a dual-voice commentary prompt for a specific section.

    Includes full analytical context: section data, triggered signal
    results with do_context strings, scoring factor details, and
    COMMENTARY_RULES instruction.

    Args:
        section_id: Section identifier (financial, market, etc.)
        section_data: Serialized section-relevant data dict.
        triggered_signals: List of triggered signal dicts with id/value/evidence/do_context.
        do_context_refs: List of D&O context strings from brain YAML signals.
        scoring_factors: Scoring factor details dict (optional).
        confidence: Section confidence level (HIGH/MEDIUM/LOW).
        company_name: Company legal name for grounding.
        ticker: Stock ticker for grounding.
        sector: Company sector for grounding.

    Returns:
        Complete prompt string for the LLM.
    """
    parts: list[str] = []

    # Header with company grounding
    parts.append(
        f"Company: {company_name} ({ticker})"
        + (f", Sector: {sector}" if sector else "")
    )
    parts.append(f"Section: {section_id.upper()}")
    parts.append(f"Data confidence: {confidence}")

    # Section-specific synthesis guidance
    guidance = SECTION_GUIDANCE.get(section_id)
    if guidance:
        parts.append(f"\n{guidance}")
    parts.append("")

    # Section data (truncated for token budget)
    data_str = json.dumps(section_data, default=str)[:6000]
    parts.append(f"SECTION DATA:\n{data_str}")
    parts.append("")

    # Triggered signals with do_context
    if triggered_signals:
        parts.append("TRIGGERED SIGNALS:")
        for sig in triggered_signals[:20]:
            sig_line = f"- {sig.get('id', '?')}: value={sig.get('value', '?')}"
            if sig.get("evidence"):
                sig_line += f", evidence: {sig['evidence'][:500]}"
            if sig.get("factors"):
                sig_line += f", factors: {sig['factors']}"
            parts.append(sig_line)
            if sig.get("do_context"):
                parts.append(f"  D&O context: {sig['do_context'][:600]}")
        parts.append("")

    # D&O context references from brain YAML
    if do_context_refs:
        parts.append("D&O THEORY CONTEXT (from brain signals):")
        for ref in do_context_refs[:12]:
            parts.append(f"- {ref}")
        parts.append("")

    # Scoring factor details
    if scoring_factors:
        parts.append("SCORING FACTORS:")
        factors_str = json.dumps(scoring_factors, default=str)[:1000]
        parts.append(factors_str)
        parts.append("")

    # Commentary rules
    parts.append(COMMENTARY_RULES)

    return "\n".join(parts)
