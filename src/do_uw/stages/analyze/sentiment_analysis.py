"""Sentiment analysis extraction using Loughran-McDonald dictionary.

Combines L-M dictionary analysis of 10-K MD&A text (SECT5-04/09) with
broader sentiment signals from web search and market data.

Uses pysentiment2 for L-M dictionary tokenization and scoring.
All outputs carry SourcedValue provenance per CLAUDE.md.

Narrative coherence assessment lives in narrative_coherence.py.

Usage:
    sentiment, report = extract_sentiment(state)
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import SentimentProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_texts,
    get_filings,
    get_market_data,
    sourced_float,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Expected fields for the sentiment extraction report.
SENTIMENT_EXPECTED: list[str] = [
    "management_tone_trajectory",
    "hedging_language_trend",
    "ceo_cfo_divergence",
    "qa_evasion_score",
    "lm_negative_trend",
    "glassdoor_rating",
    "news_sentiment",
    "social_media_sentiment",
    "employee_sentiment",
]


# ---------------------------------------------------------------------------
# L-M sentiment helpers
# ---------------------------------------------------------------------------


def analyze_lm_sentiment(
    text: str,
) -> dict[str, float]:
    """Run Loughran-McDonald dictionary analysis on text.

    Uses pysentiment2 LM dictionary for financial-domain sentiment.
    Returns polarity, subjectivity, positive, and negative scores.

    Public for reuse by narrative_coherence module.
    """
    if not text.strip():
        return {
            "positive": 0.0,
            "negative": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
        }

    try:
        import pysentiment2 as ps  # type: ignore[import-untyped]

        lm = ps.LM()
        tokens: list[str] = lm.tokenize(text)  # type: ignore[reportUnknownMemberType]
        score: dict[str, Any] = lm.get_score(tokens)  # type: ignore[reportUnknownMemberType]
        return {
            "positive": float(score.get("Positive", 0.0)),
            "negative": float(score.get("Negative", 0.0)),
            "polarity": float(score.get("Polarity", 0.0)),
            "subjectivity": float(score.get("Subjectivity", 0.0)),
        }
    except Exception:
        logger.warning("pysentiment2 L-M analysis failed", exc_info=True)
        return {
            "positive": 0.0,
            "negative": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
        }


def _compute_sentiment_trends(
    current_score: dict[str, float],
    filing_texts: dict[str, Any],
) -> dict[str, str | None]:
    """Compare current vs prior year MD&A sentiment for trajectory.

    CEO-CFO divergence and Q&A evasion are set to None (deferred --
    require earnings call transcripts not available in 10-K).

    Returns dict with trajectory, hedging_trend, ceo_cfo_divergence,
    qa_evasion.
    """
    result: dict[str, str | None] = {
        "trajectory": None,
        "hedging_trend": None,
        "ceo_cfo_divergence": None,
        "qa_evasion": None,
    }

    # Look for prior year MD&A text.
    prior_text = ""
    for key in ("10-K_item7_prior", "item7_prior", "10-K_prior_item7"):
        val = str(filing_texts.get(key, ""))
        if val.strip():
            prior_text = val
            break

    if not prior_text.strip():
        return result

    prior_score = analyze_lm_sentiment(prior_text)

    # Determine trajectory: compare negative word proportions.
    curr_neg = current_score.get("negative", 0.0)
    prior_neg = prior_score.get("negative", 0.0)
    delta = curr_neg - prior_neg

    if delta > 0.02:
        result["trajectory"] = "DETERIORATING"
    elif delta < -0.02:
        result["trajectory"] = "IMPROVING"
    else:
        result["trajectory"] = "STABLE"

    # Hedging trend: subjectivity increase -> more hedging.
    curr_subj = current_score.get("subjectivity", 0.0)
    prior_subj = prior_score.get("subjectivity", 0.0)
    subj_delta = curr_subj - prior_subj

    if subj_delta > 0.02:
        result["hedging_trend"] = "INCREASING"
    elif subj_delta < -0.02:
        result["hedging_trend"] = "DECLINING"
    else:
        result["hedging_trend"] = "STABLE"

    return result


# ---------------------------------------------------------------------------
# Broader sentiment helpers
# ---------------------------------------------------------------------------


def _extract_broader_signals(
    web_results: dict[str, Any],
    market_data: dict[str, Any],
) -> dict[str, SourcedValue[float] | SourcedValue[str] | None]:
    """Extract broader sentiment signals from web search and market data.

    All results are LOW confidence per DATA-14 (web-sourced, single source).
    """
    signals: dict[str, SourcedValue[float] | SourcedValue[str] | None] = {
        "glassdoor_rating": None,
        "news_sentiment": None,
        "social_media_sentiment": None,
        "employee_sentiment": None,
    }

    # Glassdoor rating from web search results.
    glassdoor_raw = web_results.get("glassdoor")
    if isinstance(glassdoor_raw, dict):
        glassdoor = cast(dict[str, Any], glassdoor_raw)
        rating = glassdoor.get("rating")
        if rating is not None:
            try:
                signals["glassdoor_rating"] = sourced_float(
                    float(rating),
                    "Glassdoor web search",
                    Confidence.LOW,
                )
            except (ValueError, TypeError):
                pass

        # Employee sentiment from Glassdoor.
        emp_sent = glassdoor.get("employee_sentiment")
        if isinstance(emp_sent, str) and emp_sent in (
            "POSITIVE",
            "NEUTRAL",
            "NEGATIVE",
        ):
            signals["employee_sentiment"] = sourced_str(
                emp_sent,
                "Glassdoor web search",
                Confidence.LOW,
            )

    # News sentiment from web search.
    news = web_results.get("news_sentiment")
    if isinstance(news, str) and news in ("POSITIVE", "NEUTRAL", "NEGATIVE"):
        signals["news_sentiment"] = sourced_str(
            news,
            "Brave Search news results",
            Confidence.LOW,
        )

    # Social media sentiment.
    social = web_results.get("social_media_sentiment")
    if isinstance(social, str) and social in (
        "POSITIVE",
        "NEUTRAL",
        "NEGATIVE",
    ):
        signals["social_media_sentiment"] = sourced_str(
            social,
            "Social media web search",
            Confidence.LOW,
        )

    return signals


def get_mda_text(state: AnalysisState) -> str:
    """Get MD&A text (Item 7) from state filing texts.

    Public helper shared by sentiment_analysis and narrative_coherence.
    """
    filings = get_filings(state)
    texts = get_filing_texts(filings)
    for key in ("10-K_item7", "item7"):
        val = str(texts.get(key, ""))
        if val.strip():
            return val
    return ""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def extract_sentiment(
    state: AnalysisState,
) -> tuple[SentimentProfile, ExtractionReport]:
    """Extract multi-source sentiment profile from filings and web data.

    Runs L-M dictionary analysis on 10-K MD&A text (Item 7) and
    extracts broader sentiment signals from web search results.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (SentimentProfile, ExtractionReport).
    """
    profile = SentimentProfile()
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "10-K MD&A (Item 7) + web search"

    # Get MD&A text for L-M analysis.
    mda_text = get_mda_text(state)
    filings = get_filings(state)
    texts = get_filing_texts(filings)

    if not mda_text.strip():
        warnings.append("No MD&A text available for L-M analysis")

    # Run L-M analysis on current MD&A.
    lm_score = analyze_lm_sentiment(mda_text)

    # Compute trends (current vs prior year).
    trends = _compute_sentiment_trends(lm_score, texts)

    if trends["trajectory"] is not None:
        profile.management_tone_trajectory = sourced_str(
            trends["trajectory"],
            "L-M dictionary: 10-K Item 7 current vs prior",
            Confidence.LOW,
        )
        found.append("management_tone_trajectory")

    if trends["hedging_trend"] is not None:
        profile.hedging_language_trend = sourced_str(
            trends["hedging_trend"],
            "L-M dictionary: 10-K Item 7 subjectivity trend",
            Confidence.LOW,
        )
        found.append("hedging_language_trend")

    # CEO-CFO divergence and Q&A evasion deferred (need transcripts).
    if trends["ceo_cfo_divergence"] is not None:
        profile.ceo_cfo_divergence = sourced_str(
            trends["ceo_cfo_divergence"],
            "Earnings call transcript analysis",
            Confidence.LOW,
        )
        found.append("ceo_cfo_divergence")

    if trends["qa_evasion"] is not None:
        profile.qa_evasion_score = sourced_float(
            0.0,
            "Earnings call transcript analysis",
            Confidence.LOW,
        )
        found.append("qa_evasion_score")

    # Store L-M negative trend for current period.
    neg_val = lm_score.get("negative", 0.0)
    if mda_text.strip():
        profile.lm_negative_trend.append(
            sourced_float(
                neg_val, "L-M dictionary: 10-K Item 7", Confidence.LOW
            )
        )
        found.append("lm_negative_trend")

    # Extract broader sentiment signals.
    web_results: dict[str, Any] = {}
    if state.acquired_data is not None:
        web_results = dict(state.acquired_data.web_search_results)
    market_data = get_market_data(state)

    broader = _extract_broader_signals(web_results, market_data)

    glassdoor_sv = broader.get("glassdoor_rating")
    if glassdoor_sv is not None:
        profile.glassdoor_rating = glassdoor_sv  # type: ignore[assignment]
        found.append("glassdoor_rating")

    news_sv = broader.get("news_sentiment")
    if news_sv is not None:
        profile.news_sentiment = news_sv  # type: ignore[assignment]
        found.append("news_sentiment")

    social_sv = broader.get("social_media_sentiment")
    if social_sv is not None:
        profile.social_media_sentiment = social_sv  # type: ignore[assignment]
        found.append("social_media_sentiment")

    emp_sv = broader.get("employee_sentiment")
    if emp_sv is not None:
        profile.employee_sentiment = emp_sv  # type: ignore[assignment]
        found.append("employee_sentiment")

    report = create_report(
        extractor_name="sentiment_analysis",
        expected=SENTIMENT_EXPECTED,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return profile, report
