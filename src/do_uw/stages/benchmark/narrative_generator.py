"""LLM-powered narrative generation for D&O underwriting worksheet.

Generates analyst-quality section narratives via Claude Sonnet, with
density-tiered length control and in-memory caching. Pre-computed in
BENCHMARK stage and stored on state.analysis.pre_computed_narratives
so RENDER is purely formatting.

Fallback: When openai/instructor are unavailable, falls back to
existing rule-based narratives from md_narrative.py and
md_narrative_sections.py. Fallback narratives are NOT labeled
"AI Assessment".

Section data extraction lives in narrative_data.py.
Section-specific prompts live in narrative_prompts.py.
Both split for 500-line compliance.

Phase 35 Plan 03 deliverable (enhanced Phase 116-04).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any

from do_uw.models.density import DensityLevel, PreComputedNarratives
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.narrative_data import (
    extract_findings,
    extract_section_data,
    extract_state_summary,
)
from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

logger = logging.getLogger(__name__)

# Default LLM model for narratives. Override via DO_UW_LLM_MODEL env var.
# DeepSeek for synthesis quality — matches extraction pipeline.
_DEFAULT_LLM_MODEL = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")

# Re-export for backward compat and test imports
_extract_section_data = extract_section_data

# ---------------------------------------------------------------------------
# In-memory per-run cache (not persisted across runs)
# ---------------------------------------------------------------------------
_narrative_cache: dict[str, str] = {}


def clear_cache() -> None:
    """Clear the in-memory narrative cache (useful for testing)."""
    _narrative_cache.clear()


def _cache_key(
    section_id: str,
    density: str,
    data: dict[str, Any],
) -> str:
    """Deterministic cache key from section data + density.

    Returns first 16 hex chars of SHA-256 for compact keys.
    """
    raw = json.dumps(
        {"section": section_id, "density": density, "data": data},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Density-tier configuration
# ---------------------------------------------------------------------------
_LENGTH_GUIDE: dict[str, str] = {
    "CLEAN": "4-6 sentences covering key metrics, their D&O relevance, and peer context",
    "ELEVATED": "6-8 sentences covering concerns, D&O exposure implications, and specific risk factors with evidence",
    "CRITICAL": (
        "8-12 sentences with forensic detail, cross-references to other "
        "sections, and specific underwriting implications"
    ),
}

_MAX_TOKENS: dict[str, int] = {
    "CLEAN": 600,
    "ELEVATED": 900,
    "CRITICAL": 1200,
}

_THESIS_LENGTH: dict[str, str] = {
    "CLEAN": "5-7 sentences synthesizing risk tier rationale and underwriting position",
    "ELEVATED": "8-10 sentences with risk tier rationale, key exposures, and mitigant analysis",
    "CRITICAL": "10-12 sentences with forensic synthesis and cross-section implications",
}

_QUESTION_COUNTS: dict[str, tuple[int, int]] = {
    "CLEAN": (3, 5),
    "ELEVATED": (5, 8),
    "CRITICAL": (8, 12),
}


# ---------------------------------------------------------------------------
# Post-generation cross-validation (anti-hallucination)
# ---------------------------------------------------------------------------
# FIX-01: The $383B hallucination originated from the LLM fabricating a revenue
# figure during narrative generation. The income statement line items in
# state.extracted.financials.statements contain XBRL-reconciled values (after
# Phase 128's xbrl_llm_reconciler), but the LLM may still hallucinate different
# numbers in its generated text. This validator catches such divergences.
_DOLLAR_PATTERN = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(T|B|M|K|trillion|billion|million|thousand)?",
    re.IGNORECASE,
)

_MULTIPLIERS: dict[str, float] = {
    "t": 1e12,
    "trillion": 1e12,
    "b": 1e9,
    "billion": 1e9,
    "m": 1e6,
    "million": 1e6,
    "k": 1e3,
    "thousand": 1e3,
}


def _parse_dollar_amount(match: re.Match[str]) -> float | None:
    """Parse a dollar amount from a regex match into raw numeric value."""
    try:
        num_str = match.group(1).replace(",", "")
        value = float(num_str)
        suffix = (match.group(2) or "").lower()
        multiplier = _MULTIPLIERS.get(suffix, 1.0)
        return value * multiplier
    except (ValueError, TypeError):
        return None


def validate_narrative_amounts(
    narrative: str,
    known_values: dict[str, float],
    threshold_ratio: float = 2.0,
) -> list[str]:
    """Cross-validate dollar amounts in narrative text against known state values.

    Extracts all dollar amounts from the narrative and compares each against
    the closest matching known value. If any amount diverges by more than
    threshold_ratio (default 2x), a warning string is returned.

    Args:
        narrative: Generated narrative text to validate.
        known_values: Dict of field_name -> numeric value from state data.
        threshold_ratio: Maximum allowed ratio between narrative and known values.

    Returns:
        List of warning strings (empty if all amounts are reasonable).
    """
    if not known_values or not narrative:
        return []

    warnings: list[str] = []
    known_nums = [v for v in known_values.values() if v and v != 0]
    if not known_nums:
        return []

    for match in _DOLLAR_PATTERN.finditer(narrative):
        amount = _parse_dollar_amount(match)
        if amount is None or amount == 0:
            continue

        # Find closest known value
        closest = min(known_nums, key=lambda kv: abs(kv - amount))
        if closest == 0:
            continue

        ratio = max(amount / abs(closest), abs(closest) / amount)
        if ratio > threshold_ratio:
            warnings.append(
                f"NARRATIVE_HALLUCINATION_FLAG: '{match.group(0)}' "
                f"(parsed={amount:,.0f}) diverges {ratio:.1f}x from "
                f"closest known value {closest:,.0f}"
            )

    return warnings


# ---------------------------------------------------------------------------
# Critique-and-refine: enforce company-specific output
# ---------------------------------------------------------------------------
_CRITIQUE_PROMPT = (
    "You are a senior D&O underwriting editor reviewing a narrative draft.\n"
    "Company: {company_name}\n"
    "Available data: {data_str}\n\n"
    "DRAFT:\n{narrative}\n\n"
    "Review each sentence. For each, ask:\n"
    "1. Could this sentence appear in a report about a DIFFERENT company if "
    "you changed the company name? If YES, it is GENERIC — rewrite it using "
    "specific numbers from the data.\n"
    "2. Does this sentence contain at least one specific number (dollar "
    "amount, percentage, date, count)? If NO, add one from the data.\n"
    "3. Does this sentence explain WHY this matters for D&O liability? "
    "If NO, add the connection.\n\n"
    "Return ONLY the improved narrative text. Same length. No labels or "
    "commentary about your changes. Just the better version."
)


def _critique_and_refine(
    narrative: str,
    company_name: str,
    data_str: str,
    client: Any,
    max_tok: int,
) -> str:
    """Run one critique pass to enforce company specificity.

    Returns the refined narrative, or the original if critique fails.
    """
    try:
        critique_prompt = _CRITIQUE_PROMPT.format(
            company_name=company_name,
            data_str=data_str[:4000],
            narrative=narrative,
        )
        response = client.chat.completions.create(
            model=_DEFAULT_LLM_MODEL,
            max_tokens=max_tok,
            messages=[{"role": "user", "content": critique_prompt}],
        )
        refined = response.choices[0].message.content.strip()
        # Sanity check: refined should be roughly same length (±50%)
        if refined and 0.5 < len(refined) / max(len(narrative), 1) < 2.0:
            return refined
        logger.warning("Critique pass produced unexpected length, keeping original")
        return narrative
    except Exception:
        logger.warning("Critique pass failed, keeping original", exc_info=True)
        return narrative


# ---------------------------------------------------------------------------
# LLM narrative generation functions
# ---------------------------------------------------------------------------
def generate_section_narrative(
    section_id: str,
    section_data: dict[str, Any],
    density: DensityLevel,
    company_name: str,
    client: Any | None = None,
) -> str:
    """Generate an LLM narrative for a single section.

    Uses section-specific prompts that require company-specific data in
    every sentence (QUAL-04), dollar amounts/percentages/names (QUAL-01),
    and scoring factor references (QUAL-02).

    Args:
        section_id: Section identifier (company, financial, market, etc.)
        section_data: Serialized section-relevant data.
        density: DensityLevel controlling narrative length.
        company_name: Company name for prompt context.
        client: Optional pre-created OpenAI/DeepSeek client.

    Returns:
        Narrative text (company-specific analytical paragraph).
    """
    key = _cache_key(section_id, density.value, section_data)
    if key in _narrative_cache:
        return _narrative_cache[key]

    openai_client = client or _get_client()
    if openai_client is None:
        msg = "OpenAI/DeepSeek client not available"
        raise ImportError(msg)

    data_str = json.dumps(section_data, default=str)[:8000]
    length = _LENGTH_GUIDE.get(density.value, "3-4 sentences")
    max_tok = _MAX_TOKENS.get(density.value, 600)

    # Build section-specific prompt
    prompt = build_section_prompt(
        section_id,
        company_name,
        data_str,
        length,
    )

    response = openai_client.chat.completions.create(
        model=_DEFAULT_LLM_MODEL,
        max_tokens=max_tok,
        messages=[{"role": "user", "content": prompt}],
    )
    narrative = response.choices[0].message.content

    # Critique-and-refine: enforce company specificity
    narrative = _critique_and_refine(
        narrative,
        company_name,
        data_str,
        openai_client,
        max_tok,
    )

    _narrative_cache[key] = narrative
    return narrative


def generate_executive_thesis(
    state_summary: dict[str, Any],
    density: DensityLevel,
    company_name: str,
    client: Any | None = None,
) -> str:
    """Generate executive summary thesis narrative.

    Tiered: CLEAN 3-4 sentences, ELEVATED/CRITICAL 6-8 sentences.
    Synthesizes key findings, risk tier, claim probability.
    """
    key = _cache_key("executive_thesis", density.value, state_summary)
    if key in _narrative_cache:
        return _narrative_cache[key]

    openai_client = client or _get_client()
    if openai_client is None:
        msg = "OpenAI/DeepSeek client not available"
        raise ImportError(msg)

    data_str = json.dumps(state_summary, default=str)[:6000]
    length = _THESIS_LENGTH.get(density.value, "3-4 sentences")
    max_tok = _MAX_TOKENS.get(density.value, 600)

    prompt = (
        f"Write a D&O underwriting executive thesis for "
        f"{company_name}.\n"
        f"Write {length}.\n"
        f"Tone: Bloomberg analyst report -- factual, decisive.\n"
        f"Data: {data_str}\n"
        f"Rules:\n"
        f"- Synthesize key findings into a coherent risk assessment.\n"
        f"- State the underwriting tier and recommended action clearly.\n"
        f"- Cite specific risk drivers with numbers (claim probability, "
        f"score, deductions).\n"
        f"- Explain WHY this company merits the tier (not just WHAT "
        f"the tier is).\n"
        f"- Reference specific headwinds and mitigants with evidence.\n"
        f"- Include filing-based sources where relevant.\n"
        f"- No hedging. No generic boilerplate. No filler.\n"
        f"- NEVER use generic phrases like 'has experienced', 'warrants "
        f"further investigation', 'demonstrates a commitment', 'going "
        f"forward', 'remains to be seen'. Every sentence MUST contain a "
        f"specific dollar amount, percentage, date, or named entity.\n"
        f"- If you lack specific data for a claim, omit the sentence "
        f"entirely rather than using generic language."
    )

    response = openai_client.chat.completions.create(
        model=_DEFAULT_LLM_MODEL,
        max_tokens=max_tok,
        messages=[{"role": "user", "content": prompt}],
    )
    thesis = response.choices[0].message.content
    _narrative_cache[key] = thesis
    return thesis


def generate_meeting_prep_questions(
    findings: dict[str, Any],
    density: DensityLevel,
    company_name: str,
    client: Any | None = None,
) -> list[str]:
    """Generate meeting prep questions tied to specific findings.

    Returns 3-5 for CLEAN, 5-8 for ELEVATED, 8-12 for CRITICAL.
    """
    key = _cache_key("meeting_prep", density.value, findings)
    cached = _narrative_cache.get(key)
    if cached is not None:
        return json.loads(cached)

    openai_client = client or _get_client()
    if openai_client is None:
        msg = "OpenAI/DeepSeek client not available"
        raise ImportError(msg)

    data_str = json.dumps(findings, default=str)[:6000]
    min_q, max_q = _QUESTION_COUNTS.get(density.value, (3, 5))

    # Build sector-specific guidance if available
    sector_guidance = ""
    sic = findings.get("sic_description", "")
    if sic:
        sector_guidance = (
            f"\nThis company is in the '{sic}' industry. "
            f"At least 2-3 questions MUST be sector-specific — ask about "
            f"industry-unique D&O risks, regulatory exposure, product/service "
            f"liability, and sector-specific claim theories that a generalist "
            f"underwriter might miss.\n"
        )
    ipo_guidance = ""
    if findings.get("ipo_recent"):
        ipo_guidance = (
            f"\nThis company has been public for only {findings['ipo_recent']} year(s). "
            f"At least 1-2 questions MUST address IPO-specific risks: "
            f"Section 11 liability, lockup expiration, secondary offerings, "
            f"controlled company governance, and pre-IPO disclosure gaps.\n"
        )

    prompt = (
        f"Generate {min_q}-{max_q} specific meeting preparation "
        f"questions for a D&O liability insurance underwriter meeting "
        f"with {company_name} management.\n"
        f"Each question must reference a specific finding from the "
        f"analysis data below. Do NOT ask generic questions.\n"
        f"NEVER use generic phrases like 'going forward', 'warrants "
        f"further investigation', 'demonstrates a commitment'. Each "
        f"question MUST cite a specific number, date, name, or finding.\n"
        f"IMPORTANT terminology: SCA = Securities Class Action (lawsuit "
        f"filed by shareholders alleging securities fraud). SCAs are NOT "
        f"'Shared Control Agreements' or any other expansion. Use the "
        f"full term 'securities class action' in questions, not the "
        f"abbreviation.\n"
        f"Questions should use D&O insurance terminology correctly: "
        f"litigation reserves, settlement exposure, claim probability, "
        f"defense costs, Side A/B/C coverage.\n"
        f"{sector_guidance}"
        f"{ipo_guidance}"
        f"Data: {data_str}\n"
        f"Format: Return ONLY a JSON array of question strings. "
        f"No preamble, no explanation."
    )

    response = openai_client.chat.completions.create(
        model=_DEFAULT_LLM_MODEL,
        max_tokens=_MAX_TOKENS.get(density.value, 600),
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.choices[0].message.content.strip()

    # Parse JSON array from response
    try:
        questions = json.loads(raw)
        if isinstance(questions, list):
            result = [
                (q.get("question", str(q)) if isinstance(q, dict) else str(q))
                for q in questions[:max_q]
            ]
        else:
            result = [raw]
    except json.JSONDecodeError:
        # If not valid JSON, split by newlines and clean up
        result = [
            line.lstrip("0123456789.-) ").strip()
            for line in raw.split("\n")
            if line.strip() and len(line.strip()) > 10
        ][:max_q]

    _narrative_cache[key] = json.dumps(result)
    return result


# ---------------------------------------------------------------------------
# Fallback: rule-based narratives
# ---------------------------------------------------------------------------
def _fallback_narrative(
    section_id: str,
    state: AnalysisState,
) -> str | None:
    """Generate fallback narrative using existing rule-based generators.

    Returns None if no fallback is available. Fallback narratives are
    NOT labeled "AI Assessment" since they are rule-based.
    """
    try:
        if section_id == "company":
            from do_uw.stages.render.md_narrative_sections import (
                company_narrative,
            )

            return company_narrative(state) or None
        if section_id == "governance":
            from do_uw.stages.render.md_narrative_sections import (
                governance_narrative,
            )

            return governance_narrative(state) or None
        if section_id == "litigation":
            from do_uw.stages.render.md_narrative_sections import (
                litigation_narrative,
            )

            return litigation_narrative(state) or None
        if section_id == "scoring":
            from do_uw.stages.render.md_narrative_sections import (
                scoring_narrative,
            )

            return scoring_narrative(state) or None
        if section_id == "financial":
            from do_uw.stages.render.md_narrative import (
                financial_narrative,
            )

            return financial_narrative(state) or None
        if section_id == "market":
            from do_uw.stages.render.md_narrative import (
                market_narrative,
            )

            return market_narrative(state) or None
    except Exception:
        logger.debug(
            "Fallback narrative failed for %s",
            section_id,
            exc_info=True,
        )
    return None


# ---------------------------------------------------------------------------
# Client creation (lazy import)
# ---------------------------------------------------------------------------
def _get_client() -> Any | None:
    """Create an OpenAI client with lazy import for DeepSeek.

    Returns None if openai is not installed.
    Matches existing LLMExtractor lazy import pattern.
    """
    try:
        import openai  # type: ignore[import-untyped]
        import os

        # Skip LLM narratives if DO_UW_SKIP_NARRATIVES is set
        if os.environ.get("DO_UW_SKIP_NARRATIVES", "").lower() in ("true", "1", "yes"):
            logger.info("Skipping LLM narratives per DO_UW_SKIP_NARRATIVES")
            return None
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            logger.warning("DEEPSEEK_API_KEY not set")
            return None
        return openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            timeout=60.0,
            max_retries=2,
        )
    except ImportError:
        return None
    except Exception:
        logger.warning(
            "Failed to create OpenAI client for DeepSeek",
            exc_info=True,
        )
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
_SECTIONS = (
    "company",
    "financial",
    "market",
    "governance",
    "litigation",
    "scoring",
    "ai_risk",
)


def generate_all_narratives(
    state: AnalysisState,
) -> PreComputedNarratives:
    """Generate all section narratives for RENDER consumption.

    Main entry point called from BenchmarkStage._precompute_narratives.
    Falls back to rule-based narratives when LLM is unavailable.
    Partial failure on individual sections does not crash the batch.
    """
    narratives = PreComputedNarratives()
    company_name = state.ticker
    if state.company and state.company.identity.legal_name:
        company_name = state.company.identity.legal_name.value

    # Determine if LLM is available
    client = _get_client()
    using_llm = client is not None
    if not using_llm:
        logger.warning(
            "OpenAI/DeepSeek client unavailable; falling back to rule-based narratives for all sections",
        )

    # Determine overall density for executive thesis and meeting prep
    overall_density = _overall_density(state)

    # Generate per-section narratives in parallel
    import concurrent.futures

    section_results: dict[str, str | None] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(_SECTIONS)) as executor:
        future_to_section = {}
        for section_id in _SECTIONS:
            density = _section_density(state, section_id)
            future = executor.submit(
                _generate_one,
                section_id,
                density,
                company_name,
                state,
                client,
                using_llm,
            )
            future_to_section[future] = section_id
        for future in concurrent.futures.as_completed(future_to_section):
            section_id = future_to_section[future]
            try:
                narrative = future.result()
                section_results[section_id] = narrative or None
            except Exception as e:
                logger.warning(
                    "Section narrative failed for %s: %s",
                    section_id,
                    e,
                    exc_info=True,
                )
                section_results[section_id] = None
    # Assign results to narratives object
    for section_id in _SECTIONS:
        setattr(narratives, section_id, section_results.get(section_id))

    # Generate executive thesis and meeting prep questions in parallel
    if using_llm:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Submit executive thesis task
            future_exec = executor.submit(
                lambda: generate_executive_thesis(
                    extract_state_summary(state),
                    overall_density,
                    company_name,
                    client,
                )
            )
            # Submit meeting prep questions task
            future_meeting = executor.submit(
                lambda: generate_meeting_prep_questions(
                    extract_findings(state),
                    overall_density,
                    company_name,
                    client,
                )
            )
            # Wait for both
            try:
                narratives.executive_summary = future_exec.result()
            except Exception:
                logger.warning(
                    "Executive thesis generation failed",
                    exc_info=True,
                )
                narratives.executive_summary = None
            try:
                narratives.meeting_prep_questions = future_meeting.result()
            except Exception:
                logger.warning(
                    "Meeting prep question generation failed",
                    exc_info=True,
                )
                narratives.meeting_prep_questions = None
    else:
        narratives.executive_summary = None
        narratives.meeting_prep_questions = None

    return narratives


def _overall_density(state: AnalysisState) -> DensityLevel:
    """Compute worst-case density across all sections."""
    if not state.analysis or not state.analysis.section_densities:
        return DensityLevel.CLEAN
    levels = [d.level for d in state.analysis.section_densities.values()]
    if DensityLevel.CRITICAL in levels:
        return DensityLevel.CRITICAL
    if DensityLevel.ELEVATED in levels:
        return DensityLevel.ELEVATED
    return DensityLevel.CLEAN


def _section_density(
    state: AnalysisState,
    section_id: str,
) -> DensityLevel:
    """Get density for a specific section."""
    if state.analysis and state.analysis.section_densities:
        sd = state.analysis.section_densities.get(section_id)
        if sd is not None:
            return sd.level
    return DensityLevel.CLEAN


def _generate_one(
    section_id: str,
    density: DensityLevel,
    company_name: str,
    state: AnalysisState,
    client: Any | None,
    using_llm: bool,
) -> str:
    """Generate narrative for one section with fallback and cross-validation."""
    try:
        if using_llm:
            section_data = extract_section_data(state, section_id)
            narrative = generate_section_narrative(
                section_id,
                section_data,
                density,
                company_name,
                client,
            )
            # Cross-validate dollar amounts against known state values
            known = _extract_known_values(section_data)
            warnings = validate_narrative_amounts(narrative, known)
            for w in warnings:
                logger.warning(
                    "Section %s: %s",
                    section_id,
                    w,
                )
            return narrative
        return _fallback_narrative(section_id, state) or ""
    except Exception:
        logger.warning(
            "Section narrative failed for %s, trying fallback",
            section_id,
            exc_info=True,
        )
        return _fallback_narrative(section_id, state) or ""


def _extract_known_values(section_data: dict[str, Any]) -> dict[str, float]:
    """Extract numeric values from section data for cross-validation."""
    known: dict[str, float] = {}
    for key, val in section_data.items():
        if isinstance(val, (int, float)) and val != 0:
            known[key] = float(val)
    return known
