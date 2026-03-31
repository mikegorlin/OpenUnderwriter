"""Dual-voice commentary generation engine for D&O underwriting worksheet.

Generates per-section dual-voice commentary (What Was Said + Underwriting
Commentary) via DeepSeek. Pre-computed in BENCHMARK stage and stored
on state.analysis.pre_computed_commentary so RENDER is purely formatting.

Reuses existing infrastructure:
- extract_section_data() for base data
- get_signals_by_prefix() for signal aggregation
- derive_section_confidence() for confidence badge
- validate_narrative_amounts() for hallucination detection

Phase 130 Plan 01 deliverable.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

from do_uw.models.density import PreComputedCommentary, SectionCommentary
from do_uw.models.state import AnalysisState
from do_uw.stages.benchmark.commentary_prompts import (
    SECTION_PREFIX_MAP,
    build_commentary_prompt,
)
from do_uw.stages.benchmark.narrative_data import extract_section_data
from do_uw.stages.benchmark.narrative_generator import (
    _extract_known_values,
    validate_narrative_amounts,
)

logger = logging.getLogger(__name__)

# Default LLM model for commentary. Override via DO_UW_LLM_MODEL env var.
# DeepSeek-V3.2 for synthesis quality
_DEFAULT_LLM_MODEL = os.environ.get("DO_UW_LLM_MODEL", "deepseek-chat")

# Max tokens per section commentary (enough for both voices)
_MAX_COMMENTARY_TOKENS = 1200

# 8 sections that get dual-voice commentary
_COMMENTARY_SECTIONS = (
    "executive_brief",
    "financial",
    "market",
    "governance",
    "litigation",
    "scoring",
    "company",
    "meeting_prep",
)

# ---------------------------------------------------------------------------
# In-memory per-run cache (not persisted across runs)
# ---------------------------------------------------------------------------
_commentary_cache: dict[str, SectionCommentary] = {}


def clear_cache() -> None:
    """Clear the in-memory commentary cache (useful for testing)."""
    _commentary_cache.clear()


def _cache_key(section_id: str, data: dict[str, Any]) -> str:
    """Deterministic cache key from section data."""
    raw = json.dumps(
        {"section": section_id, "data": data},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Client creation (lazy import, same pattern as narrative_generator.py)
# ---------------------------------------------------------------------------
def _get_client() -> Any | None:
    """Create an OpenAI client with lazy import for DeepSeek.

    Returns None if openai is not installed.
    """
    try:
        import openai  # type: ignore[import-untyped]
        import os

        # Skip LLM commentary if DO_UW_SKIP_NARRATIVES is set
        if os.environ.get("DO_UW_SKIP_NARRATIVES", "").lower() in ("true", "1", "yes"):
            logger.info("Skipping LLM commentary per DO_UW_SKIP_NARRATIVES")
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
# Context extraction
# ---------------------------------------------------------------------------
def extract_commentary_context(
    state: AnalysisState,
    section_id: str,
) -> dict[str, Any]:
    """Extract enriched context for commentary generation.

    Includes everything from extract_section_data() PLUS:
    - Signal results with do_context strings
    - Scoring factor details
    - Section confidence
    """
    from do_uw.stages.render.context_builders._bull_bear import (
        derive_section_confidence,
    )
    from do_uw.stages.render.context_builders._signal_consumer import (
        get_signals_by_prefix,
    )

    # Base data from existing extraction
    data = extract_section_data(state, section_id)

    # Enrich with signal results and do_context
    if state.analysis and state.analysis.signal_results:
        sr = state.analysis.signal_results
        prefixes = SECTION_PREFIX_MAP.get(section_id, [])
        triggered: list[dict[str, Any]] = []
        do_contexts: list[str] = []
        for prefix in prefixes:
            signals = get_signals_by_prefix(sr, prefix)
            for sig in signals:
                if sig.status == "TRIGGERED":
                    triggered.append(
                        {
                            "id": sig.signal_id,
                            "value": sig.value,
                            "evidence": sig.evidence[:500] if sig.evidence else "",
                            "do_context": sig.do_context[:600] if sig.do_context else "",
                            "factors": list(sig.factors),
                        }
                    )
                if sig.do_context:
                    do_contexts.append(sig.do_context[:400])
        data["triggered_signals"] = triggered[:20]
        data["do_context_refs"] = do_contexts[:12]

    # Section confidence
    data["section_confidence"] = derive_section_confidence(state, section_id)

    return data


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------
def _parse_commentary_response(response_text: str) -> tuple[str, str]:
    """Parse LLM response into (what_was_said, underwriting_commentary).

    Splits on 'WHAT WAS SAID:' and 'UNDERWRITING COMMENTARY:' markers.
    Graceful fallback: if markers not found, first half goes to
    what_was_said, second half to underwriting_commentary.
    """
    text = response_text.strip()

    # Try splitting on markers
    what_marker = "WHAT WAS SAID:"
    uc_marker = "UNDERWRITING COMMENTARY:"

    what_idx = text.upper().find(what_marker.upper())
    uc_idx = text.upper().find(uc_marker.upper())

    if what_idx >= 0 and uc_idx > what_idx:
        what_text = text[what_idx + len(what_marker) : uc_idx].strip()
        uc_text = text[uc_idx + len(uc_marker) :].strip()
        return what_text, uc_text

    # Fallback: split roughly in half at a sentence boundary
    mid = len(text) // 2
    # Find nearest period after midpoint
    period_idx = text.find(".", mid)
    if period_idx > 0 and period_idx < len(text) - 1:
        return text[: period_idx + 1].strip(), text[period_idx + 1 :].strip()

    # Last resort: first half / second half
    return text[:mid].strip(), text[mid:].strip()


# ---------------------------------------------------------------------------
# Per-section commentary generation
# ---------------------------------------------------------------------------
def generate_section_commentary(
    state: AnalysisState,
    section_id: str,
    client: Any | None = None,
) -> SectionCommentary:
    """Generate dual-voice commentary for a single section.

    Extracts enriched context, builds prompt, calls DeepSeek,
    parses response, and runs cross-validation.

    Returns SectionCommentary with confidence and hallucination warnings.
    """
    context = extract_commentary_context(state, section_id)

    # Check in-memory cache
    key = _cache_key(section_id, context)
    if key in _commentary_cache:
        return _commentary_cache[key]

    openai_client = client or _get_client()
    if openai_client is None:
        # Graceful fallback: return empty commentary
        return SectionCommentary()

    # Extract company grounding info
    company_name = state.ticker
    ticker = state.ticker
    sector = ""
    if state.company:
        if state.company.identity.legal_name:
            company_name = state.company.identity.legal_name.value
        if state.company.identity.sector:
            sector = str(state.company.identity.sector.value)

    # Extract scoring factors if available
    scoring_factors: dict[str, Any] | None = None
    if state.scoring and state.scoring.factor_scores:
        scoring_factors = {
            f.factor_id: {
                "name": f.factor_name,
                "deducted": f.points_deducted,
                "max": f.max_points,
            }
            for f in state.scoring.factor_scores
            if f.points_deducted > 0
        }

    confidence = context.get("section_confidence", "MEDIUM")

    prompt = build_commentary_prompt(
        section_id=section_id,
        section_data={
            k: v
            for k, v in context.items()
            if k not in ("triggered_signals", "do_context_refs", "section_confidence")
        },
        triggered_signals=context.get("triggered_signals", []),
        do_context_refs=context.get("do_context_refs", []),
        scoring_factors=scoring_factors,
        confidence=confidence,
        company_name=company_name,
        ticker=ticker,
        sector=sector,
    )

    response = openai_client.chat.completions.create(
        model=_DEFAULT_LLM_MODEL,
        max_tokens=_MAX_COMMENTARY_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    raw_text = response.choices[0].message.content

    what_was_said, underwriting_commentary = _parse_commentary_response(raw_text)

    # Cross-validate dollar amounts against known state values
    known = _extract_known_values(context)
    warnings: list[str] = []
    warnings.extend(validate_narrative_amounts(what_was_said, known))
    warnings.extend(validate_narrative_amounts(underwriting_commentary, known))
    for w in warnings:
        logger.warning("Section %s commentary: %s", section_id, w)

    commentary = SectionCommentary(
        what_was_said=what_was_said,
        underwriting_commentary=underwriting_commentary,
        confidence=confidence,
        hallucination_warnings=warnings,
    )

    _commentary_cache[key] = commentary
    return commentary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def generate_all_commentary(
    state: AnalysisState,
) -> PreComputedCommentary:
    """Generate dual-voice commentary for all 8 analytical sections.

    Main entry point called from BenchmarkStage._precompute_commentary.
    Falls back to empty SectionCommentary objects when LLM is unavailable.
    Partial failure on individual sections does not crash the batch.
    """
    commentary = PreComputedCommentary()
    client = _get_client()

    for section_id in _COMMENTARY_SECTIONS:
        try:
            sc = generate_section_commentary(state, section_id, client)
            setattr(commentary, section_id, sc)
        except Exception:
            logger.warning(
                "Commentary generation failed for section %s",
                section_id,
                exc_info=True,
            )
            # Set empty commentary on failure
            setattr(commentary, section_id, SectionCommentary())

    return commentary
