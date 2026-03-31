"""Unit tests for NLP signal detection engine.

Tests readability change, tone shift, risk factor evolution,
whistleblower detection, and graceful degradation when prior year
filing is unavailable.
"""

from __future__ import annotations

from do_uw.stages.analyze.nlp_signals import (
    analyze_nlp_signals,
    compute_readability_change,
    detect_tone_shift,
    detect_whistleblower_language,
    track_risk_factor_evolution,
)

# -- Sample texts for testing -------------------------------------------------

# Simple readable text (low Fog Index)
_SIMPLE_TEXT = (
    "The company reported strong results. Revenue grew by ten percent. "
    "Costs were stable. Margins improved significantly this quarter. "
    "We expect growth to continue. The outlook is positive. "
    "Our products gained market share. Customer satisfaction remained high. "
) * 20  # Repeat to ensure enough text for textstat

# Complex text (higher Fog Index)
_COMPLEX_TEXT = (
    "Notwithstanding the aforementioned macroeconomic uncertainties "
    "and the concomitant geopolitical destabilization precipitating "
    "unprecedented volatility in international capital markets, the "
    "corporation's diversified portfolio of intellectual property assets "
    "and vertically integrated supply chain infrastructure contributed "
    "to a circumscribed amelioration of the anticipated deterioration "
    "in consolidated operating performance metrics. "
) * 20  # Repeat for reliable metrics


# -- Readability tests --------------------------------------------------------

def test_readability_increasing_fog():
    """Fog Index increase should be detected as INCREASING_COMPLEXITY."""
    result = compute_readability_change(_COMPLEX_TEXT, _SIMPLE_TEXT)
    assert result["classification"] == "INCREASING_COMPLEXITY"
    assert result["current_fog"] is not None
    assert result["prior_fog"] is not None
    assert result["fog_change"] > 0
    assert "increased" in result["evidence"].lower() or "complexity" in result["evidence"].lower()


def test_readability_stable():
    """Same text for both years should be STABLE."""
    result = compute_readability_change(_SIMPLE_TEXT, _SIMPLE_TEXT)
    assert result["classification"] == "STABLE"
    assert result["fog_change"] is not None
    assert abs(result["fog_change"]) < 2.0


def test_readability_no_prior():
    """Prior year unavailable should return CURRENT_ONLY."""
    result = compute_readability_change(_SIMPLE_TEXT, None)
    assert result["classification"] == "CURRENT_ONLY"
    assert result["current_fog"] is not None
    assert result["prior_fog"] is None
    assert result["fog_change"] is None
    assert "prior year unavailable" in result["evidence"].lower()


def test_readability_insufficient_data():
    """Very short text should return INSUFFICIENT_DATA."""
    result = compute_readability_change("Short.", None)
    assert result["classification"] == "INSUFFICIENT_DATA"


# -- Tone shift tests ---------------------------------------------------------

# Text heavy on negative keywords
_NEGATIVE_MDA = (
    "The company faces significant risk and uncertainty. Revenue decline "
    "continued. Litigation costs increased. Investigation ongoing. "
    "Impairment charges recognized. Restructuring plan announced. "
    "Adverse market conditions persist. Loss from operations widened. "
) * 15

# Text heavy on positive keywords
_POSITIVE_MDA = (
    "The company achieved record growth and strong performance. "
    "Improvement in margins exceeded expectations. Innovation drove "
    "opportunity for expansion. Robust momentum continued. "
    "Favorable market conditions supported outperformance. "
    "Achievement of strategic milestones accelerated growth. "
) * 15


def test_tone_shift_more_negative():
    """Shift from positive to negative should be MORE_NEGATIVE."""
    result = detect_tone_shift(_NEGATIVE_MDA, _POSITIVE_MDA)
    assert result["classification"] == "MORE_NEGATIVE"
    assert result["current_negative_ratio"] > result["prior_negative_ratio"]
    assert result["shift"] > 0


def test_tone_shift_stable():
    """Same text should be STABLE."""
    result = detect_tone_shift(_NEGATIVE_MDA, _NEGATIVE_MDA)
    assert result["classification"] == "STABLE"
    assert result["shift"] is not None
    assert abs(result["shift"]) < 0.05


def test_tone_no_prior():
    """Prior year unavailable should return CURRENT_ONLY."""
    result = detect_tone_shift(_NEGATIVE_MDA, None)
    assert result["classification"] == "CURRENT_ONLY"
    assert result["current_negative_ratio"] is not None
    assert result["prior_negative_ratio"] is None


# -- Risk factor evolution tests ----------------------------------------------

def test_risk_factor_evolution_new_factors():
    """New risk factors should be identified."""
    current = [
        "We face risks from cybersecurity threats",
        "Regulatory changes may impact operations",
        "NEW: AI regulation may affect our products",
        "Market competition is intense",
    ]
    prior = [
        "We face risks from cybersecurity threats",
        "Regulatory changes may impact operations",
        "Market competition is intense",
    ]
    result = track_risk_factor_evolution(current, prior)
    assert result["current_count"] == 4
    assert result["prior_count"] == 3
    assert result["net_change"] == 1
    assert len(result["new_factors"]) == 1
    assert "AI regulation" in result["new_factors"][0]
    assert len(result["removed_factors"]) == 0


def test_risk_factor_fuzzy_matching():
    """Similar risk factors should not be counted as new (fuzzy match)."""
    current = [
        "We face risks from cybersecurity threats to our information technology systems",
        "Regulatory changes may impact our operations and financial results",
    ]
    prior = [
        "We face risks from cybersecurity threats to our information technology systems",
        "Regulatory changes may impact our operations and financial results",
    ]
    result = track_risk_factor_evolution(current, prior)
    assert len(result["new_factors"]) == 0
    assert len(result["removed_factors"]) == 0
    assert result["net_change"] == 0


def test_risk_factor_no_prior():
    """Prior year unavailable should report current state only."""
    current = ["Risk A", "Risk B", "Risk C"]
    result = track_risk_factor_evolution(current, None)
    assert result["current_count"] == 3
    assert result["prior_count"] is None
    assert result["net_change"] is None
    assert "prior year unavailable" in result["evidence"].lower()


# -- Whistleblower detection --------------------------------------------------

def test_whistleblower_detection():
    """Whistleblower and qui tam language should be detected."""
    text = (
        "The company is subject to a whistleblower complaint filed under "
        "the False Claims Act. A qui tam action was brought by a relator "
        "alleging improper billing practices."
    )
    result = detect_whistleblower_language(text)
    assert result["detected"] is True
    assert "whistleblower" in result["matches"]
    assert "qui tam" in result["matches"]
    assert "false claims act" in result["matches"]
    assert "relator" in result["matches"]


def test_whistleblower_negative():
    """Normal text without whistleblower language should not trigger."""
    text = (
        "The company reported strong quarterly results with revenue growth "
        "of 15 percent year over year. Operating margins expanded to 25 percent. "
        "Management reaffirmed full year guidance."
    )
    result = detect_whistleblower_language(text)
    assert result["detected"] is False
    assert len(result["matches"]) == 0


# -- Full orchestrator test ---------------------------------------------------

def test_all_signals_no_prior_year():
    """Graceful degradation when prior year unavailable."""
    result = analyze_nlp_signals(
        extracted=None,
        prior_year_text=None,
        state=None,
    )
    assert "readability" in result
    assert "tone_shift" in result
    assert "risk_factors" in result
    assert "whistleblower" in result
    assert "summary" in result
    assert result["summary"]["prior_year_available"] is False

    # All signals should be in degraded mode (INSUFFICIENT_DATA or CURRENT_ONLY)
    readability = result["readability"]
    assert readability["classification"] in ("INSUFFICIENT_DATA", "CURRENT_ONLY")

    tone = result["tone_shift"]
    assert tone["classification"] in ("INSUFFICIENT_DATA", "CURRENT_ONLY")
