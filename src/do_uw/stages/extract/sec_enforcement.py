"""SEC enforcement pipeline position mapping extractor.

Determines the company's position in the SEC enforcement pipeline
by searching 10-K Item 3, Item 1A, and EFTS data for enforcement
signal patterns. Uses highest-stage-wins logic across stages:
  NONE < COMMENT_LETTER < INFORMAL_INQUIRY < FORMAL_INVESTIGATION
  < WELLS_NOTICE < ENFORCEMENT_ACTION

Covers SECT6-04 for D&O underwriting.

Usage:
    pipeline, report = extract_sec_enforcement(state)
    state.extracted.litigation.sec_enforcement = pipeline
"""

from __future__ import annotations

import logging
import re
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import EnforcementStage, SECEnforcementPipeline
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.filing_sections import SECTION_DEFS, extract_section
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    now,
    sourced_int,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXPECTED_FIELDS: list[str] = [
    "highest_stage",
    "pipeline_signals",
    "comment_letter_count",
    "comment_letter_topics",
    "industry_sweep",
    "enforcement_narrative",
    "actions",
    "aaer_count",
]

# Enforcement stage ordering (index = severity rank).
STAGE_ORDER: list[EnforcementStage] = [
    EnforcementStage.NONE,
    EnforcementStage.COMMENT_LETTER,
    EnforcementStage.INFORMAL_INQUIRY,
    EnforcementStage.FORMAL_INVESTIGATION,
    EnforcementStage.WELLS_NOTICE,
    EnforcementStage.ENFORCEMENT_ACTION,
]

# Stage detection patterns ordered most severe to least.
STAGE_PATTERNS: list[tuple[EnforcementStage, re.Pattern[str]]] = [
    (
        EnforcementStage.ENFORCEMENT_ACTION,
        re.compile(
            r"enforcement\s+action|complaint\s+filed|civil\s+penalty"
            r"|consent\s+decree",
            re.IGNORECASE,
        ),
    ),
    (
        EnforcementStage.WELLS_NOTICE,
        re.compile(r"[Ww]ells\s+[Nn]otice", re.IGNORECASE),
    ),
    (
        EnforcementStage.FORMAL_INVESTIGATION,
        re.compile(
            r"formal\s+(?:order\s+of\s+)?investigation|HO-\d+",
            re.IGNORECASE,
        ),
    ),
    (
        EnforcementStage.INFORMAL_INQUIRY,
        re.compile(
            r"informal\s+(?:inquiry|investigation)"
            r"|(?:voluntary\s+)?information\s+request",
            re.IGNORECASE,
        ),
    ),
    (
        EnforcementStage.COMMENT_LETTER,
        re.compile(
            r"comment\s+letter|CORRESP|staff\s+comment",
            re.IGNORECASE,
        ),
    ),
]

# Industry sweep detection pattern template.
SWEEP_KEYWORDS = re.compile(
    r"SEC\s+(?:sweep|industry\s+sweep|enforcement\s+sweep"
    r"|coordinated\s+investigation)",
    re.IGNORECASE,
)

# 8-K enforcement-related keywords.
ENFORCEMENT_8K_KEYWORDS = re.compile(
    r"SEC\s+(?:enforcement|investigation|subpoena|Wells)"
    r"|enforcement\s+action|consent\s+order",
    re.IGNORECASE,
)

# Comment letter topic extraction patterns.
COMMENT_TOPIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("revenue_recognition", re.compile(
        r"revenue\s+recognition|ASC\s+606", re.IGNORECASE,
    )),
    ("goodwill_impairment", re.compile(
        r"goodwill|impairment|ASC\s+350", re.IGNORECASE,
    )),
    ("non_gaap_measures", re.compile(
        r"non-GAAP|non\s+GAAP|adjusted\s+(?:EBITDA|earnings)",
        re.IGNORECASE,
    )),
    ("segment_reporting", re.compile(
        r"segment\s+reporting|ASC\s+280|operating\s+segments",
        re.IGNORECASE,
    )),
    ("md_and_a", re.compile(
        r"MD&A|management.s\s+discussion", re.IGNORECASE,
    )),
    ("internal_controls", re.compile(
        r"internal\s+controls?|(?:SOX|Sarbanes)", re.IGNORECASE,
    )),
    ("related_party", re.compile(
        r"related\s+party|related-party", re.IGNORECASE,
    )),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def stage_rank(stage: EnforcementStage) -> int:
    """Return numeric rank of an enforcement stage (higher = more severe)."""
    try:
        return STAGE_ORDER.index(stage)
    except ValueError:
        return 0


def _get_section_text(
    full_text: str, section_name: str,
) -> str:
    """Extract a named section from filing text."""
    section_def = next(
        (d for d in SECTION_DEFS if d[0] == section_name), None,
    )
    if section_def is None:
        return ""
    return extract_section(full_text, section_def[1], section_def[2])


def _extract_context_sentence(
    text: str, match: re.Match[str], max_len: int = 500,
) -> str:
    """Extract surrounding sentence context for a regex match."""
    start = max(0, match.start() - 300)
    end = min(len(text), match.end() + 300)
    context = text[start:end].strip()
    return context[:max_len]


# Non-SEC agencies whose "formal investigation" should not count.
_NON_SEC_AGENCIES = re.compile(
    r"European\s+Commission|Department\s+of\s+Justice|DOJ\b|FTC\b"
    r"|Federal\s+Trade|CFPB|EPA\b|FDA\b|OSHA\b|NHTSA|State\s+Attorney"
    r"|Digital\s+Markets\s+Act|DMA\b|antitrust\s+lawsuit",
    re.IGNORECASE,
)

# Hypothetical/conditional language in risk factors that describes
# potential regulatory outcomes, NOT actual enforcement activity.
_HYPOTHETICAL_LANGUAGE = re.compile(
    r"could\s+(?:also\s+)?result\s+in"
    r"|may\s+(?:lead|result|be\s+subject)"
    r"|are\s+generally\s+increasing"
    r"|noncompliance\s+could"
    r"|if\s+(?:we|the\s+company)\s+(?:fail|do\s+not)"
    r"|there\s+can\s+be\s+no\s+assurance"
    r"|no\s+assurance\s+that"
    r"|we\s+cannot\s+predict"
    r"|subject\s+to\s+(?:various|significant|potential)\s+(?:risks?|penalties)"
    r"|from\s+time\s+to\s+time"
    r"|regulatory\s+authorities\s+(?:may|could|are\s+generally)",
    re.IGNORECASE,
)

# Positive SEC context required for serious stages.
_SEC_CONTEXT = re.compile(
    r"\bSEC\b|Securities\s+and\s+Exchange\s+Commission"
    r"|Division\s+of\s+Enforcement|AAER\b"
    r"|Commission\s+staff",
    re.IGNORECASE,
)


def _detect_stages(
    text: str, source: str,
) -> list[tuple[EnforcementStage, SourcedValue[str]]]:
    """Detect enforcement stages from text.

    Returns list of (stage, signal) tuples.
    Filters out hypothetical/boilerplate risk-factor language.
    For FORMAL_INVESTIGATION and above, requires SEC context nearby.
    """
    results: list[tuple[EnforcementStage, SourcedValue[str]]] = []
    for stage, pattern in STAGE_PATTERNS:
        match = pattern.search(text)
        if match:
            context = _extract_context_sentence(text, match)
            # Skip matches attributed to non-SEC agencies
            if _NON_SEC_AGENCIES.search(context):
                continue
            # Skip hypothetical/conditional risk-factor language
            if _HYPOTHETICAL_LANGUAGE.search(context):
                logger.debug(
                    "Skipping %s signal (hypothetical language): %.100s",
                    stage.value, context,
                )
                continue
            # For serious stages, additional validation
            if stage in (
                EnforcementStage.FORMAL_INVESTIGATION,
                EnforcementStage.WELLS_NOTICE,
                EnforcementStage.ENFORCEMENT_ACTION,
            ):
                wider_start = max(0, match.start() - 500)
                wider_end = min(len(text), match.end() + 500)
                wider = text[wider_start:wider_end]
                # Reject if non-SEC agency is mentioned nearby
                if _NON_SEC_AGENCIES.search(wider):
                    continue
                # Require positive SEC context nearby
                if not _SEC_CONTEXT.search(wider):
                    logger.debug(
                        "Skipping %s signal (no SEC context): %.100s",
                        stage.value, context,
                    )
                    continue
            signal = sourced_str(context, source, Confidence.MEDIUM)
            results.append((stage, signal))
    return results


def _get_comment_letter_count(state: AnalysisState) -> int | None:
    """Get CORRESP count from acquired filings data."""
    if state.acquired_data is None:
        return None
    filings = dict(state.acquired_data.filings)
    corresp = filings.get("CORRESP")
    if isinstance(corresp, list):
        return len(cast(list[Any], corresp))
    if isinstance(corresp, int):
        return corresp
    return None


def _detect_comment_topics(
    text: str, source: str,
) -> list[SourcedValue[str]]:
    """Detect comment letter topics from text."""
    topics: list[SourcedValue[str]] = []
    seen: set[str] = set()
    for topic_name, pattern in COMMENT_TOPIC_PATTERNS:
        if pattern.search(text) and topic_name not in seen:
            topics.append(sourced_str(topic_name, source, Confidence.LOW))
            seen.add(topic_name)
    return topics


def _detect_industry_sweep(
    state: AnalysisState,
) -> SourcedValue[bool] | None:
    """Check web search results for industry sweep indicators."""
    if state.acquired_data is None:
        return None

    # Check litigation web_results and blind spot results.
    sources_to_check: list[str] = []

    web_results = state.acquired_data.litigation_data.get("web_results")
    if isinstance(web_results, list):
        for r in cast(list[Any], web_results):
            sources_to_check.append(str(r))

    blind = state.acquired_data.blind_spot_results
    if blind:
        for _key, val in blind.items():
            if isinstance(val, str):
                sources_to_check.append(val)
            elif isinstance(val, list):
                for item in cast(list[Any], val):
                    sources_to_check.append(str(item))

    for text in sources_to_check:
        if SWEEP_KEYWORDS.search(text):
            return SourcedValue[bool](
                value=True, source="web search / blind spots",
                confidence=Confidence.LOW, as_of=now(),
            )

    return SourcedValue[bool](
        value=False, source="web search / blind spots",
        confidence=Confidence.LOW, as_of=now(),
    )


def _check_8k_enforcement(state: AnalysisState) -> list[SourcedValue[str]]:
    """Check 8-K filings for enforcement-related disclosures."""
    signals: list[SourcedValue[str]] = []
    full_text_8k = get_filing_document_text(state, "8-K")
    if not full_text_8k:
        return signals

    source = "8-K filings"
    for match in ENFORCEMENT_8K_KEYWORDS.finditer(full_text_8k):
        context = _extract_context_sentence(full_text_8k, match)
        signals.append(sourced_str(context, source, Confidence.MEDIUM))
        if len(signals) >= 5:  # Cap at 5 signals.
            break

    return signals


def _generate_narrative(
    highest_stage: EnforcementStage,
    signal_count: int,
    comment_count: int | None,
    sweep_detected: bool,
) -> str:
    """Generate enforcement narrative summary."""
    parts: list[str] = []

    if highest_stage == EnforcementStage.NONE:
        parts.append(
            "No SEC enforcement pipeline activity detected."
        )
    else:
        parts.append(
            f"Company is at {highest_stage.value} stage in the "
            f"SEC enforcement pipeline, with {signal_count} "
            "supporting signal(s) identified."
        )

    if comment_count is not None and comment_count > 0:
        parts.append(
            f"SEC has issued {comment_count} comment letter(s)."
        )

    if sweep_detected:
        parts.append(
            "Industry sweep activity detected among peers, "
            "suggesting elevated regulatory scrutiny."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_sec_enforcement(
    state: AnalysisState,
) -> tuple[SECEnforcementPipeline, ExtractionReport]:
    """Extract SEC enforcement pipeline position from filing text.

    Searches 10-K Item 3, Item 1A, 8-K, and EFTS data for
    enforcement signals. Determines highest confirmed stage
    using highest-stage-wins logic.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (SECEnforcementPipeline, ExtractionReport).
    """
    pipeline = SECEnforcementPipeline()
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "10-K Item 3 + Item 1A + 8-K + EFTS"

    # Get filing text.
    full_text = get_filing_document_text(state, "10-K")
    item3_text = _get_section_text(full_text, "item3") if full_text else ""
    item1a_text = _get_section_text(full_text, "item1a") if full_text else ""
    combined_text = f"{item3_text}\n{item1a_text}"

    # Detect enforcement stages from Item 3 + Item 1A.
    all_signals: list[tuple[EnforcementStage, SourcedValue[str]]] = []
    if item3_text:
        all_signals.extend(
            _detect_stages(item3_text, "10-K Item 3")
        )
    if item1a_text:
        all_signals.extend(
            _detect_stages(item1a_text, "10-K Item 1A")
        )

    # Cross-reference 8-K filings.
    # 8-K keywords (investigation, subpoena, Wells) indicate activity in
    # the enforcement pipeline but do NOT prove a completed enforcement
    # action.  Classify as FORMAL_INVESTIGATION — the highest-stage-wins
    # logic will still promote if a more severe signal is found elsewhere.
    signals_8k = _check_8k_enforcement(state)
    for signal in signals_8k:
        all_signals.append(
            (EnforcementStage.FORMAL_INVESTIGATION, signal)
        )

    # Determine highest confirmed stage.
    highest = EnforcementStage.NONE
    for detected_stage, signal in all_signals:
        pipeline.pipeline_signals.append(signal)
        if stage_rank(detected_stage) > stage_rank(highest):
            highest = detected_stage

    # Guard: ENFORCEMENT_ACTION requires actual structured enforcement
    # actions, not just text-pattern matches.  Without entries in the
    # actions list, text signals can only confirm up to WELLS_NOTICE
    # (the last pre-action stage).  This prevents false positives where
    # generic legal language ("consent decree", "enforcement action")
    # in filings triggers the most severe stage for companies with zero
    # actual SEC enforcement actions.
    if (
        highest == EnforcementStage.ENFORCEMENT_ACTION
        and not pipeline.actions
    ):
        highest = EnforcementStage.WELLS_NOTICE

    # Guard: WELLS_NOTICE requires actual "Wells Notice" text in at
    # least one signal.  If the stage was downgraded from
    # ENFORCEMENT_ACTION or elevated from a non-Wells pattern, cap at
    # FORMAL_INVESTIGATION unless the Wells Notice regex actually fired.
    _WELLS_RE = re.compile(r"[Ww]ells\s+[Nn]otice", re.IGNORECASE)
    if highest == EnforcementStage.WELLS_NOTICE and not any(
        _WELLS_RE.search(sig.value)
        for _stage, sig in all_signals
    ):
        highest = EnforcementStage.FORMAL_INVESTIGATION

    pipeline.highest_confirmed_stage = sourced_str(
        highest.value, source_filing, Confidence.MEDIUM,
    )
    # Backward-compat: also set pipeline_position.
    pipeline.pipeline_position = sourced_str(
        highest.value, source_filing, Confidence.MEDIUM,
    )
    found.append("highest_stage")
    if pipeline.pipeline_signals:
        found.append("pipeline_signals")

    # Comment letter count.
    comment_count = _get_comment_letter_count(state)
    if comment_count is not None:
        pipeline.comment_letter_count = sourced_int(
            comment_count, "EFTS/audit data", Confidence.MEDIUM,
        )
        found.append("comment_letter_count")

    # Comment letter topics.
    topics = _detect_comment_topics(combined_text, "10-K text")
    pipeline.comment_letter_topics = topics
    if topics:
        found.append("comment_letter_topics")

    # Industry sweep detection.
    sweep = _detect_industry_sweep(state)
    pipeline.industry_sweep_detected = sweep
    found.append("industry_sweep")

    sweep_detected = sweep.value if sweep else False

    # Enforcement narrative.
    narrative = _generate_narrative(
        highest, len(all_signals), comment_count, sweep_detected,
    )
    pipeline.enforcement_narrative = sourced_str(
        narrative, source_filing, Confidence.LOW,
    )
    found.append("enforcement_narrative")

    # Actions and AAER are typically populated from structured data
    # in later phases; mark as expected but not found here.
    if not full_text:
        warnings.append("No 10-K filing text available")

    report = create_report(
        extractor_name="sec_enforcement",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return pipeline, report
