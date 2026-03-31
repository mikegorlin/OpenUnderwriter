"""Section-specific LLM prompt builders for D&O narrative generation.

Each section gets a tailored prompt that requires company-specific data
in every sentence (QUAL-04), dollar amounts/percentages/names (QUAL-01),
and formal research report voice (D-01 through D-05).

Split from narrative_generator.py for 500-line compliance.
"""

from __future__ import annotations

from collections.abc import Callable

# ---------------------------------------------------------------------------
# Common rules appended to every section prompt
# ---------------------------------------------------------------------------
COMMON_RULES = (
    "Rules (MANDATORY):\n"
    "- You are a 30-year D&O underwriting veteran writing for other experts. "
    "Skip the obvious. Don't explain what D&O insurance is or what an SCA is. "
    "Your reader knows. Go straight to what makes THIS company's risk profile "
    "unusual, dangerous, or interesting.\n"
    "- Every sentence MUST contain company-specific data: dollar amounts, "
    "percentages, dates, or names. If a sentence could apply to any "
    "company by changing the name, DELETE IT.\n"
    "- Focus on the 2-3 things that would change an underwriter's pricing. "
    "What's the story? What's the catch? What would you warn a colleague "
    "about over coffee?\n"
    "- NEVER reference scoring factors (F1-F10), signal IDs, check ratios, "
    "composite scores, deduction points, or any scoring engine terminology.\n"
    "- NEVER use 'AI Assessment', 'automated analysis', 'system detected', "
    "'brain', 'signal triggered', or any machine-facing language.\n"
    "- Voice: direct, authoritative, specific. Like a senior underwriter's "
    "handwritten margin notes — sharp observations, not textbook summaries.\n"
    "- 3-5 sentences. No hedging. No filler. No 'This section'.\n"
    "- BANNED phrases (DELETE any sentence containing these): "
    "'has experienced a notable', 'warrants further investigation', "
    "'demonstrates a commitment', 'going forward', 'moving forward', "
    "'remains to be seen', 'time will tell', 'creating acute liability', "
    "'endemic to', 'stemming from', 'with particular exposure', "
    "'concentrate decision-making complexity', 'subject to various', "
    "'arising in the ordinary course', 'party to legal matters', "
    "'may be involved in certain', 'from time to time', "
    "'is subject to claims', 'in the normal course of business', "
    "'various legal proceedings', 'could have a material adverse', "
    "'no assurance', 'there can be no guarantee', "
    "'the company believes', 'management believes that'. "
    "If you catch yourself writing like a law review article or a 10-K "
    "risk factor, stop and write like you're briefing your boss in 60 seconds.\n"
    "- Do NOT start with any label or prefix."
)


# ---------------------------------------------------------------------------
# Per-section prompt builders
# ---------------------------------------------------------------------------
def _financial_prompt(
    company_name: str, data_str: str, length: str,
) -> str:
    return (
        f"Write a D&O underwriting financial health narrative for "
        f"{company_name}.\n"
        f"Write {length}.\n"
        f"Data: {data_str}\n"
        f"REQUIRED content (use actual values from the data):\n"
        f"- Revenue and net income with $ amounts, YoY change %\n"
        f"- Altman Z-Score (value + zone), Beneish M-Score "
        f"(value + zone), Piotroski F-Score, Ohlson O-Score\n"
        f"- Key ratios: current ratio, debt-to-equity, interest coverage\n"
        f"- D&O relevance: connect financial health to specific litigation "
        f"theories (going-concern allegations, restatement exposure under "
        f"Section 10(b) + Section 11)\n"
        f"{COMMON_RULES}"
    )


def _market_prompt(
    company_name: str, data_str: str, length: str,
) -> str:
    return (
        f"Write a D&O underwriting market events narrative for "
        f"{company_name}.\n"
        f"Write {length}.\n"
        f"Data: {data_str}\n"
        f"REQUIRED content (use actual values from the data):\n"
        f"- Stock price: current, 52-week high/low, % decline\n"
        f"- Significant stock drops: count, worst single-day decline "
        f"with date and trigger\n"
        f"- Insider activity: net direction, selling volume, "
        f"cluster events\n"
        f"- Executive departures: names, dates, planned vs unplanned\n"
        f"- D&O relevance: stock-drop litigation threshold "
        f"(Dura Pharmaceuticals loss causation standard), insider "
        f"selling and scienter inference (Tellabs)\n"
        f"{COMMON_RULES}"
    )


def _governance_prompt(
    company_name: str, data_str: str, length: str,
) -> str:
    return (
        f"Write a D&O underwriting governance narrative for "
        f"{company_name}.\n"
        f"Write {length}.\n"
        f"Data: {data_str}\n"
        f"REQUIRED content (use actual values from the data):\n"
        f"- Board size, independence ratio (%), average tenure\n"
        f"- CEO name and tenure, CEO/Chair duality status\n"
        f"- Compensation: CEO total comp $, say-on-pay approval %\n"
        f"- Governance red flags: overboarded directors, "
        f"classified board, dual-class structure\n"
        f"- D&O relevance: Caremark duty of oversight exposure, "
        f"duty of candor in proxy disclosures, derivative action risk\n"
        f"{COMMON_RULES}"
    )


def _litigation_prompt(
    company_name: str, data_str: str, length: str,
) -> str:
    return (
        f"Write a D&O underwriting litigation narrative for "
        f"{company_name}.\n"
        f"Write {length}.\n"
        f"Data: {data_str}\n"
        f"REQUIRED content (use actual values from the data):\n"
        f"- Active SCA count and case names with class periods\n"
        f"- Lead counsel tier and name\n"
        f"- Settlement history with $ amounts\n"
        f"- SEC enforcement stage\n"
        f"- Sector SCA filing rate comparison (sector vs company rate)\n"
        f"- Claim probability estimate\n"
        f"- D&O relevance: SCA recurrence probability, settlement "
        f"benchmarking against peer companies, regulatory enforcement "
        f"timeline as corrective disclosure, defense cost exposure\n"
        f"IMPORTANT: SCA = Securities Class Action. Do NOT use other "
        f"expansions.\n"
        f"{COMMON_RULES}"
    )


def _scoring_prompt(
    company_name: str, data_str: str, length: str,
) -> str:
    return (
        f"Write a D&O underwriting scoring narrative for "
        f"{company_name}.\n"
        f"Write {length}.\n"
        f"Data: {data_str}\n"
        f"REQUIRED content (use actual values from the data):\n"
        f"- Quality score (X/100) and tier classification\n"
        f"- Top 3 risk drivers by area (e.g., litigation history, "
        f"financial distress, governance weakness) — describe the risk, "
        f"not the scoring mechanism\n"
        f"- Any critical red flags that constrain the risk assessment\n"
        f"- Overall risk characterization for underwriting decision\n"
        f"- Active composite risk patterns if any\n"
        f"{COMMON_RULES}"
    )


def _company_prompt(
    company_name: str, data_str: str, length: str,
) -> str:
    return (
        f"Write the 'Company Overview', 'Revenue Model', and 'D&O Risk "
        f"Profile' sections for {company_name}'s D&O underwriting worksheet.\n"
        f"Write {length} per section (9-15 sentences total, 3 sections).\n"
        f"Data: {data_str}\n\n"
        f"FORMAT: Use exactly these three headers on separate lines:\n"
        f"Company Overview\n"
        f"Revenue Model\n"
        f"D&O Risk Profile\n\n"
        f"COMPANY OVERVIEW: What does this company actually do? Be specific. "
        f"Not 'provides testing services' but 'certifies product safety for "
        f"80,000 manufacturers — if UL says a fire alarm works, retailers "
        f"stock it.' Include market cap, employees, years public.\n\n"
        f"REVENUE MODEL: How does money flow? What's sticky vs discretionary? "
        f"What would break the revenue engine? Use actual segment data "
        f"and dollar amounts.\n\n"
        f"D&O RISK PROFILE: This is the underwriter's bottom line. "
        f"What are the 2-3 things about this specific company that drive "
        f"D&O exposure? Not generic 'regulatory risk' — the specific "
        f"mechanism. Example: 'If UL certifies a non-compliant product, "
        f"the entire downstream chain sues — that's the Martucci theory.' "
        f"Connect to actual litigation, governance, geographic, or "
        f"structural vulnerabilities in the data. If the company has a "
        f"dual-class structure, an active lawsuit, China exposure, or "
        f"recent IPO — those ARE the D&O story, not generic commentary.\n\n"
        f"{COMMON_RULES}"
    )


# ---------------------------------------------------------------------------
# Registry and dispatcher
# ---------------------------------------------------------------------------
SECTION_PROMPT_BUILDERS: dict[
    str,
    Callable[[str, str, str], str],
] = {
    "financial": _financial_prompt,
    "market": _market_prompt,
    "governance": _governance_prompt,
    "litigation": _litigation_prompt,
    "scoring": _scoring_prompt,
    "company": _company_prompt,
}


def build_section_prompt(
    section_id: str,
    company_name: str,
    data_str: str,
    length: str,
) -> str:
    """Build a section-specific LLM prompt with full analytical context."""
    builder = SECTION_PROMPT_BUILDERS.get(section_id)
    if builder:
        return builder(company_name, data_str, length)
    # Fallback generic prompt for unknown sections
    return (
        f"Write a D&O underwriting narrative for the {section_id} "
        f"section of {company_name}.\n"
        f"Write {length}.\n"
        f"Data: {data_str}\n"
        f"{COMMON_RULES}"
    )
