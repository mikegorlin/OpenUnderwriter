"""AI disclosure extractor -- parse AI keywords from Item 1A risk factors.

Scans SEC 10-K Item 1A text for AI-related keyword mentions, classifies
the sentiment as OPPORTUNITY, THREAT, BALANCED, or UNKNOWN, and extracts
contextual risk factor snippets.  Also computes YoY trend when prior-year
filings are available.

Part of the SECT8 AI Transformation Risk Factor extraction pipeline.
"""

from __future__ import annotations

import logging
import re

from do_uw.models.ai_risk import AIDisclosureData
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.filing_sections import SECTION_DEFS, extract_section
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AI keyword categories
# ---------------------------------------------------------------------------

CORE_AI_TERMS: list[str] = [
    "artificial intelligence",
    "machine learning",
    "generative AI",
    "large language model",
    "deep learning",
    "neural network",
    "AI model",
    "AI system",
    "AI technology",
    "AI-powered",
    "AI-driven",
    "AI-enabled",
]

BROADER_AUTOMATION_TERMS: list[str] = [
    "automation",
    "algorithmic",
    "natural language processing",
    "computer vision",
    "robotic process automation",
]

# Compiled patterns (word-boundary, case-insensitive)
_CORE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE) for kw in CORE_AI_TERMS
]
_BROADER_PATTERNS: list[re.Pattern[str]] = [
    re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
    for kw in BROADER_AUTOMATION_TERMS
]

# Sentiment proximity keywords
THREAT_KEYWORDS: list[str] = [
    "risk",
    "threat",
    "disrupt",
    "displace",
    "compete",
    "challenge",
    "vulnerable",
    "obsolete",
    "replace",
]
OPPORTUNITY_KEYWORDS: list[str] = [
    "opportunity",
    "leverage",
    "invest",
    "adopt",
    "enhance",
    "improve",
    "transform",
    "benefit",
    "advantage",
]

_THREAT_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in THREAT_KEYWORDS) + r")\b",
    re.IGNORECASE,
)
_OPPORTUNITY_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in OPPORTUNITY_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# SECTION_DEFS lookup for Item 1A
_ITEM_1A_DEF = next(
    (d for d in SECTION_DEFS if d[0] == "item1a"), None
)

# Context window size for risk factor extraction (characters)
_CONTEXT_WINDOW = 200
_MAX_RISK_FACTORS = 10


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_ai_disclosures(
    state: AnalysisState,
) -> tuple[AIDisclosureData, ExtractionReport]:
    """Extract AI disclosure data from 10-K Item 1A risk factors.

    Args:
        state: Pipeline state with acquired filing documents.

    Returns:
        Tuple of (AIDisclosureData, ExtractionReport).
    """
    expected_fields = ["mention_count", "sentiment", "risk_factors", "yoy_trend"]

    item1a_text = _get_item1a_text(state)
    if not item1a_text:
        logger.info("SECT8: No Item 1A text available for AI disclosure parsing")
        return (
            AIDisclosureData(),
            create_report(
                extractor_name="ai_disclosure",
                expected=expected_fields,
                found=[],
                source_filing="none",
                warnings=["No Item 1A text available"],
            ),
        )

    # Count AI mentions
    core_matches = _count_matches(item1a_text, _CORE_PATTERNS)
    broader_matches = _count_matches(item1a_text, _BROADER_PATTERNS)
    mention_count = core_matches + broader_matches

    # Sentiment classification
    threat_mentions, opportunity_mentions = _count_sentiment(item1a_text)
    sentiment = _classify_sentiment(
        threat_mentions, opportunity_mentions, mention_count
    )

    # Risk factor extraction
    risk_factors = _extract_risk_factors(item1a_text)

    # YoY trend
    yoy_trend = _compute_yoy_trend(state, mention_count)

    found_fields: list[str] = []
    if mention_count > 0:
        found_fields.append("mention_count")
    if sentiment != "UNKNOWN":
        found_fields.append("sentiment")
    if risk_factors:
        found_fields.append("risk_factors")
    if yoy_trend != "UNKNOWN":
        found_fields.append("yoy_trend")

    disclosure = AIDisclosureData(
        mention_count=mention_count,
        risk_factors=risk_factors,
        opportunity_mentions=opportunity_mentions,
        threat_mentions=threat_mentions,
        sentiment=sentiment,
        yoy_trend=yoy_trend,
    )

    report = create_report(
        extractor_name="ai_disclosure",
        expected=expected_fields,
        found=found_fields,
        source_filing="10-K Item 1A",
    )

    logger.info(
        "SECT8: AI disclosure extracted -- %d mentions, sentiment=%s",
        mention_count,
        sentiment,
    )
    return disclosure, report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_item1a_text(state: AnalysisState) -> str:
    """Extract Item 1A text from the most recent 10-K filing."""
    if state.acquired_data is None:
        return ""

    docs = state.acquired_data.filing_documents.get("10-K", [])
    if not docs:
        return ""

    # Sort by filing_date descending to get most recent
    sorted_docs = sorted(docs, key=lambda d: d.get("filing_date", ""), reverse=True)
    most_recent = sorted_docs[0]
    full_text = most_recent.get("full_text", "")
    if not full_text:
        return ""

    # Use filing_sections to isolate Item 1A
    if _ITEM_1A_DEF is None:
        return ""
    return extract_section(full_text, _ITEM_1A_DEF[1], _ITEM_1A_DEF[2])


def _get_prior_item1a_text(state: AnalysisState) -> str:
    """Extract Item 1A text from the second most recent 10-K filing."""
    if state.acquired_data is None:
        return ""

    docs = state.acquired_data.filing_documents.get("10-K", [])
    if len(docs) < 2:
        return ""

    sorted_docs = sorted(docs, key=lambda d: d.get("filing_date", ""), reverse=True)
    prior = sorted_docs[1]
    full_text = prior.get("full_text", "")
    if not full_text:
        return ""

    if _ITEM_1A_DEF is None:
        return ""
    return extract_section(full_text, _ITEM_1A_DEF[1], _ITEM_1A_DEF[2])


def _count_matches(text: str, patterns: list[re.Pattern[str]]) -> int:
    """Count total regex matches across all patterns."""
    total = 0
    for pat in patterns:
        total += len(pat.findall(text))
    return total


def _count_sentiment(text: str) -> tuple[int, int]:
    """Count threat and opportunity keywords in text."""
    threat_count = len(_THREAT_PATTERN.findall(text))
    opportunity_count = len(_OPPORTUNITY_PATTERN.findall(text))
    return threat_count, opportunity_count


def _classify_sentiment(
    threat: int, opportunity: int, total_mentions: int
) -> str:
    """Classify overall AI sentiment.

    Returns THREAT if threat > 2 * opportunity, OPPORTUNITY if
    opportunity > 2 * threat, BALANCED otherwise, UNKNOWN if
    total AI mentions < 3.
    """
    if total_mentions < 3:
        return "UNKNOWN"
    if threat > 2 * opportunity:
        return "THREAT"
    if opportunity > 2 * threat:
        return "OPPORTUNITY"
    return "BALANCED"


def _extract_risk_factors(text: str) -> list[str]:
    """Extract context windows around AI keyword matches.

    Returns up to _MAX_RISK_FACTORS deduplicated snippets.
    """
    all_patterns = _CORE_PATTERNS + _BROADER_PATTERNS
    spans: list[tuple[int, int]] = []

    for pat in all_patterns:
        for match in pat.finditer(text):
            start = max(0, match.start() - _CONTEXT_WINDOW // 2)
            end = min(len(text), match.end() + _CONTEXT_WINDOW // 2)
            spans.append((start, end))

    # Merge overlapping spans
    merged = _merge_spans(spans)

    # Build snippets
    factors: list[str] = []
    for start, end in merged[:_MAX_RISK_FACTORS]:
        snippet = text[start:end].strip()
        # Clean up whitespace
        snippet = re.sub(r"\s+", " ", snippet)
        if snippet:
            factors.append(snippet)

    return factors


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Merge overlapping character spans."""
    if not spans:
        return []
    sorted_spans = sorted(spans)
    merged: list[tuple[int, int]] = [sorted_spans[0]]
    for start, end in sorted_spans[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))
    return merged


def _compute_yoy_trend(state: AnalysisState, current_count: int) -> str:
    """Compare current vs prior year AI mention counts.

    INCREASING if current > prior * 1.2, DECREASING if current < prior * 0.8,
    STABLE otherwise. Returns UNKNOWN if no prior data.
    """
    prior_text = _get_prior_item1a_text(state)
    if not prior_text:
        return "UNKNOWN"

    prior_core = _count_matches(prior_text, _CORE_PATTERNS)
    prior_broader = _count_matches(prior_text, _BROADER_PATTERNS)
    prior_count = prior_core + prior_broader

    if prior_count == 0:
        return "INCREASING" if current_count > 0 else "STABLE"

    ratio = current_count / prior_count
    if ratio > 1.2:
        return "INCREASING"
    if ratio < 0.8:
        return "DECREASING"
    return "STABLE"
