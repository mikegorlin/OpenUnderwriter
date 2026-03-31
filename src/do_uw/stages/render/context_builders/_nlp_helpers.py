"""NLP signal extraction helpers for the analysis context builder.

Extracted from analysis.py to keep it under 500 lines while surfacing
all SentimentProfile and NarrativeCoherence fields (SURF-03, SURF-08).
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState


# ---------------------------------------------------------------------------
# Trend arrow mapping
# ---------------------------------------------------------------------------

_UP_TRENDS = {"IMPROVING", "INCREASING"}
_DOWN_TRENDS = {"DETERIORATING", "DECLINING"}


def _trend_arrow(direction: str | None) -> dict[str, str]:
    """Return arrow character and CSS class for a trend direction."""
    if direction is None:
        return {"arrow": "trending_flat", "css": "trend-flat", "label": "N/A"}
    d = direction.upper()
    if d in _UP_TRENDS:
        return {"arrow": "trending_up", "css": "trend-up", "label": direction.title()}
    if d in _DOWN_TRENDS:
        return {"arrow": "trending_down", "css": "trend-down", "label": direction.title()}
    return {"arrow": "trending_flat", "css": "trend-flat", "label": direction.title()}


def _alignment_icon(status: str | None) -> dict[str, str]:
    """Return icon class for alignment status."""
    if status is None:
        return {"status": "N/A", "icon": "dash", "css": "text-gray-400"}
    s = status.upper()
    if s in ("ALIGNED", "COHERENT"):
        return {"status": status.title(), "icon": "check", "css": "alignment-check"}
    if s in ("DIVERGENT", "MISALIGNED", "SIGNIFICANT_GAPS"):
        return {"status": status.replace("_", " ").title(), "icon": "warning", "css": "alignment-warning"}
    if s == "MINOR_GAPS":
        return {"status": "Minor Gaps", "icon": "warning", "css": "alignment-warning"}
    return {"status": status.replace("_", " ").title(), "icon": "dash", "css": "text-gray-400"}


def _sv_val(sv: Any, fallback: Any = None) -> Any:
    """Extract .value from a SourcedValue or return fallback."""
    if sv is None:
        return fallback
    return sv.value if hasattr(sv, "value") else sv


def _sv_source(sv: Any) -> str:
    """Extract source string from a SourcedValue."""
    if sv is None:
        return ""
    return str(sv.source) if hasattr(sv, "source") and sv.source else ""


def _sv_confidence(sv: Any) -> str:
    """Extract confidence from a SourcedValue."""
    if sv is None:
        return ""
    return str(sv.confidence) if hasattr(sv, "confidence") and sv.confidence else ""


# ---------------------------------------------------------------------------
# Sentiment data extraction
# ---------------------------------------------------------------------------


def extract_sentiment_data(state: AnalysisState) -> dict[str, Any]:
    """Extract SentimentProfile fields into template-ready dict."""
    result: dict[str, Any] = {}
    sources: dict[str, str] = {}
    confidences: dict[str, str] = {}

    gov = getattr(state.extracted, "governance", None) if state.extracted else None
    sentiment = getattr(gov, "sentiment", None) if gov else None
    if sentiment is None:
        return result

    # Management tone with trend arrow
    tone_val = _sv_val(sentiment.management_tone_trajectory)
    result["management_tone"] = {
        "value": tone_val or "N/A",
        "trend": _trend_arrow(tone_val),
    }
    sources["management_tone"] = _sv_source(sentiment.management_tone_trajectory)
    confidences["management_tone"] = _sv_confidence(sentiment.management_tone_trajectory)

    # Hedging language with trend arrow
    hedge_val = _sv_val(sentiment.hedging_language_trend)
    result["hedging_language"] = {
        "value": hedge_val or "N/A",
        "trend": _trend_arrow(hedge_val),
    }
    sources["hedging_language"] = _sv_source(sentiment.hedging_language_trend)
    confidences["hedging_language"] = _sv_confidence(sentiment.hedging_language_trend)

    # CEO/CFO divergence
    div_val = _sv_val(sentiment.ceo_cfo_divergence)
    result["ceo_cfo_divergence"] = _alignment_icon(div_val)
    sources["ceo_cfo_divergence"] = _sv_source(sentiment.ceo_cfo_divergence)

    # Q&A evasion score
    qa_val = _sv_val(sentiment.qa_evasion_score)
    if qa_val is not None:
        pct = f"{qa_val * 100:.0f}%"
        severity = "High" if qa_val > 0.6 else "Moderate" if qa_val > 0.3 else "Low"
        result["qa_evasion"] = {"value": pct, "severity": severity, "raw": qa_val}
    else:
        result["qa_evasion"] = {"value": "N/A", "severity": "N/A", "raw": None}
    sources["qa_evasion"] = _sv_source(sentiment.qa_evasion_score)

    # Specificity trend
    spec_val = _sv_val(sentiment.specificity_trend)
    result["specificity_trend"] = {
        "value": spec_val or "N/A",
        "trend": _trend_arrow(spec_val),
    }
    sources["specificity_trend"] = _sv_source(sentiment.specificity_trend)

    # Multi-source sentiment
    result["glassdoor_rating"] = (
        f"{_sv_val(sentiment.glassdoor_rating):.1f}"
        if _sv_val(sentiment.glassdoor_rating) is not None
        else "N/A"
    )
    result["glassdoor_ceo_approval"] = (
        f"{_sv_val(sentiment.glassdoor_ceo_approval):.0f}%"
        if _sv_val(sentiment.glassdoor_ceo_approval) is not None
        else "N/A"
    )
    result["employee_sentiment"] = _sv_val(sentiment.employee_sentiment, "N/A")
    result["news_sentiment"] = _sv_val(sentiment.news_sentiment, "N/A")
    result["social_media_sentiment"] = _sv_val(sentiment.social_media_sentiment, "N/A")

    sources["glassdoor"] = _sv_source(sentiment.glassdoor_rating)
    sources["employee_sentiment"] = _sv_source(sentiment.employee_sentiment)
    sources["news_sentiment"] = _sv_source(sentiment.news_sentiment)
    sources["social_media_sentiment"] = _sv_source(sentiment.social_media_sentiment)

    result["_sources"] = sources
    result["_confidences"] = confidences
    return result


# ---------------------------------------------------------------------------
# L-M dictionary trends
# ---------------------------------------------------------------------------


def build_lm_trends(state: AnalysisState) -> dict[str, list[float]] | None:
    """Extract Loughran-McDonald dictionary trend data as value lists."""
    gov = getattr(state.extracted, "governance", None) if state.extracted else None
    sentiment = getattr(gov, "sentiment", None) if gov else None
    if sentiment is None:
        return None

    negative = [_sv_val(sv, 0.0) for sv in sentiment.lm_negative_trend]
    uncertainty = [_sv_val(sv, 0.0) for sv in sentiment.lm_uncertainty_trend]
    litigious = [_sv_val(sv, 0.0) for sv in sentiment.lm_litigious_trend]

    if not any([negative, uncertainty, litigious]):
        return None

    # Normalize to percentage of max for bar height rendering (0-100)
    def _normalize(vals: list[float]) -> list[float]:
        if not vals:
            return []
        mx = max(vals) if vals else 1.0
        if mx == 0:
            return [0.0] * len(vals)
        return [round(v / mx * 100, 1) for v in vals]

    return {
        "negative": _normalize(negative),
        "uncertainty": _normalize(uncertainty),
        "litigious": _normalize(litigious),
        "raw_negative": negative,
        "raw_uncertainty": uncertainty,
        "raw_litigious": litigious,
    }


# ---------------------------------------------------------------------------
# Narrative coherence
# ---------------------------------------------------------------------------


def extract_coherence_data(state: AnalysisState) -> dict[str, Any] | None:
    """Extract NarrativeCoherence fields into template-ready dict."""
    gov = getattr(state.extracted, "governance", None) if state.extracted else None
    coherence = getattr(gov, "narrative_coherence", None) if gov else None
    if coherence is None:
        return None

    sources: dict[str, str] = {}

    strategy = _alignment_icon(_sv_val(coherence.strategy_vs_results))
    sources["strategy_vs_results"] = _sv_source(coherence.strategy_vs_results)

    insider = _alignment_icon(_sv_val(coherence.insider_vs_confidence))
    sources["insider_vs_confidence"] = _sv_source(coherence.insider_vs_confidence)

    tone = _alignment_icon(_sv_val(coherence.tone_vs_financials))
    sources["tone_vs_financials"] = _sv_source(coherence.tone_vs_financials)

    employee = _alignment_icon(_sv_val(coherence.employee_vs_management))
    sources["employee_vs_management"] = _sv_source(coherence.employee_vs_management)

    overall = _alignment_icon(_sv_val(coherence.overall_assessment))
    sources["overall"] = _sv_source(coherence.overall_assessment)

    flags = [_sv_val(f, "") for f in coherence.coherence_flags]

    return {
        "strategy_alignment": strategy,
        "insider_alignment": insider,
        "tone_alignment": tone,
        "employee_alignment": employee,
        "overall": overall,
        "flags": [f for f in flags if f],
        "_sources": sources,
    }
