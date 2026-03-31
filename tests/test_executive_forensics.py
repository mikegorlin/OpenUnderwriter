"""Unit tests for executive forensics scoring pipeline.

Tests individual risk scoring, board aggregate computation,
name matching, and graceful degradation when data is unavailable.
"""

from __future__ import annotations

import pytest

from do_uw.models.executive_risk import BoardAggregateRisk, IndividualRiskScore
from do_uw.stages.analyze.executive_data import (
    _extract_role_from_title,
    _match_insider_to_executive,
)
from do_uw.stages.analyze.executive_forensics import (
    _apply_time_decay,
    compute_board_aggregate_risk,
    run_executive_forensics,
    score_individual_risk,
)


# -- Shared config fixture ---------------------------------------------------

@pytest.fixture()
def config():
    """Executive scoring config matching config/executive_scoring.json."""
    return {
        "role_weights": {
            "CEO": 3.0, "CFO": 2.5, "COO": 2.0, "GC": 2.0,
            "CAO": 2.0, "CTO": 1.5, "Director": 1.0, "Other": 1.0,
            "CLO": 2.0, "CRO": 1.5, "CISO": 1.5, "Chairman": 2.0,
            "Lead Independent Director": 1.5,
        },
        "dimension_max_scores": {
            "prior_litigation": 25,
            "regulatory_enforcement": 25,
            "prior_company_failures": 15,
            "insider_trading_patterns": 10,
            "negative_news": 10,
            "tenure_stability": 5,
        },
        "time_decay": {"half_life_years": 5, "minimum_weight": 0.1},
        "aggregate_thresholds": {"low": 20, "moderate": 35, "elevated": 50, "high": 70, "critical": 85},
    }


# -- Clean CEO (no red flags) ------------------------------------------------

def test_score_individual_ceo_clean(config):
    """CEO with no red flags should score near zero."""
    exec_data = {
        "name": "Jane Smith",
        "role": "CEO",
        "role_weight": 3.0,
        "prior_litigation": [],
        "prior_enforcement": [],
        "prior_restatements": [],
        "insider_trades": [],
        "bio_summary": "Jane Smith has 20 years of experience in technology leadership.",
        "years_tenure": 8.0,
        "officer_change_recent": False,
        "is_interim": False,
    }
    result = score_individual_risk(exec_data, config)
    assert isinstance(result, IndividualRiskScore)
    assert result.person_name == "Jane Smith"
    assert result.role == "CEO"
    assert result.role_weight == 3.0
    assert result.total_score == 0.0
    assert result.prior_litigation == 0.0
    assert result.regulatory_enforcement == 0.0
    assert result.insider_trading_patterns == 0.0
    assert result.tenure_stability == 0.0
    assert len(result.findings) == 0


# -- Risky CEO ---------------------------------------------------------------

def test_score_individual_ceo_risky(config):
    """CEO with prior litigation + insider selling should score high."""
    exec_data = {
        "name": "John Risk",
        "role": "CEO",
        "role_weight": 3.0,
        "prior_litigation": ["Named defendant in SCA at PriorCorp Inc."],
        "prior_enforcement": ["SEC enforcement action at FormerCo"],
        "prior_restatements": [],
        "insider_trades": [
            {"transaction_type": "SELL", "total_value": 2_000_000, "is_discretionary": True},
            {"transaction_type": "SELL", "total_value": 3_000_000, "is_discretionary": True},
            {"transaction_type": "SELL", "total_value": 1_500_000, "is_discretionary": False},
        ],
        "bio_summary": "Previously involved in securities class action settlement at OldCorp.",
        "years_tenure": 1.5,
        "officer_change_recent": False,
        "is_interim": False,
    }
    result = score_individual_risk(exec_data, config)
    assert result.total_score > 20.0  # Should have significant score
    assert result.prior_litigation > 0
    assert result.regulatory_enforcement > 0
    assert result.insider_trading_patterns > 0
    assert result.tenure_stability > 0  # Short tenure
    assert len(result.findings) > 0
    assert any("litigation" in f.lower() for f in result.findings)


# -- Insider trading dimension ------------------------------------------------

def test_insider_trading_dimension(config):
    """Net selling pattern should be detected and scored."""
    exec_data = {
        "name": "Selling Sam",
        "role": "CFO",
        "role_weight": 2.5,
        "prior_litigation": [],
        "prior_enforcement": [],
        "prior_restatements": [],
        "insider_trades": [
            {"transaction_type": "SELL", "total_value": 500_000, "is_discretionary": True},
            {"transaction_type": "SELL", "total_value": 300_000, "is_discretionary": True},
            {"transaction_type": "SELL", "total_value": 200_000, "is_discretionary": False},
            {"transaction_type": "BUY", "total_value": 50_000, "is_discretionary": False},
        ],
        "bio_summary": "",
        "years_tenure": 5.0,
        "officer_change_recent": False,
        "is_interim": False,
    }
    result = score_individual_risk(exec_data, config)
    assert result.insider_trading_patterns > 0
    assert any("net seller" in f.lower() or "discretionary" in f.lower() for f in result.findings)


# -- Tenure stability ---------------------------------------------------------

def test_tenure_stability_new_cfo(config):
    """CFO with < 2 years tenure should have higher stability score."""
    exec_data = {
        "name": "New CFO",
        "role": "CFO",
        "role_weight": 2.5,
        "prior_litigation": [],
        "prior_enforcement": [],
        "prior_restatements": [],
        "insider_trades": [],
        "bio_summary": "",
        "years_tenure": 0.8,
        "officer_change_recent": True,
        "is_interim": False,
    }
    result = score_individual_risk(exec_data, config)
    assert result.tenure_stability > 0
    assert any("tenure" in f.lower() or "appointment" in f.lower() for f in result.findings)


# -- Time decay ---------------------------------------------------------------

def test_time_decay_old_events():
    """10-year-old event should decay to ~25% of original score."""
    original = 10.0
    decayed = _apply_time_decay(original, years_ago=10.0, half_life=5.0, minimum_weight=0.1)
    # After 2 half-lives: 10 * 0.25 = 2.5
    assert abs(decayed - 2.5) < 0.01

    # After 0 years: no decay
    no_decay = _apply_time_decay(original, years_ago=0, half_life=5.0, minimum_weight=0.1)
    assert no_decay == 10.0


# -- Role weight CEO vs Director ---------------------------------------------

def test_role_weight_ceo_vs_director(config):
    """CEO should have 3x weight vs director at 1x."""
    ceo_data = {
        "name": "CEO Person",
        "role": "CEO",
        "role_weight": 3.0,
        "prior_litigation": ["Prior SCA"],
        "prior_enforcement": [],
        "prior_restatements": [],
        "insider_trades": [],
        "bio_summary": "",
        "years_tenure": 5.0,
        "officer_change_recent": False,
        "is_interim": False,
    }
    dir_data = {
        "name": "Director Person",
        "role": "Director",
        "role_weight": 1.0,
        "prior_litigation": ["Prior SCA"],
        "prior_enforcement": [],
        "prior_restatements": [],
        "insider_trades": [],
        "bio_summary": "",
        "years_tenure": 5.0,
        "officer_change_recent": False,
        "is_interim": False,
    }
    ceo_result = score_individual_risk(ceo_data, config)
    dir_result = score_individual_risk(dir_data, config)

    # Same raw score but different weights
    assert ceo_result.total_score == dir_result.total_score
    assert ceo_result.role_weight == 3.0
    assert dir_result.role_weight == 1.0


# -- Board aggregate weighted -------------------------------------------------

def test_board_aggregate_weighted(config):
    """Weighted average should correctly combine CEO(3x) and Director(1x)."""
    ceo_score = IndividualRiskScore(
        person_name="CEO", role="CEO", role_weight=3.0, total_score=30.0,
    )
    dir_score = IndividualRiskScore(
        person_name="Director", role="Director", role_weight=1.0, total_score=10.0,
    )
    aggregate = compute_board_aggregate_risk([ceo_score, dir_score], config)
    assert isinstance(aggregate, BoardAggregateRisk)
    # Expected: (30*3 + 10*1) / (3+1) = 100/4 = 25.0
    assert aggregate.weighted_score == 25.0
    assert aggregate.highest_risk_individual == "CEO"


# -- No executive data --------------------------------------------------------

def test_no_executive_data(config):
    """run_executive_forensics should return None when no data available."""
    from do_uw.models.state import AnalysisState

    state = AnalysisState(ticker="TEST")
    result = run_executive_forensics(state)
    assert result is None


# -- Name matching fuzzy ------------------------------------------------------

def test_name_matching_fuzzy():
    """'John A. Smith' should match 'John Smith' in insider trades."""
    trades = [
        {"insider_name": "John Smith", "transaction_type": "SELL", "total_value": 100_000},
        {"insider_name": "Jane Doe", "transaction_type": "SELL", "total_value": 50_000},
    ]

    # Exact first+last match (ignoring middle initial)
    matches = _match_insider_to_executive("John A. Smith", trades)
    assert len(matches) == 1
    assert matches[0]["insider_name"] == "John Smith"

    # Non-match
    matches = _match_insider_to_executive("Robert Johnson", trades)
    assert len(matches) == 0


# -- Role extraction ----------------------------------------------------------

def test_role_extraction():
    """Title-to-role mapping should handle common titles."""
    role_weights = {"CEO": 3.0, "CFO": 2.5, "COO": 2.0, "GC": 2.0, "CAO": 2.0, "CTO": 1.5, "Director": 1.0, "Other": 1.0}

    assert _extract_role_from_title("Chief Executive Officer", role_weights) == "CEO"
    assert _extract_role_from_title("Chief Financial Officer", role_weights) == "CFO"
    assert _extract_role_from_title("Chief Operating Officer", role_weights) == "COO"
    assert _extract_role_from_title("General Counsel", role_weights) == "GC"
    assert _extract_role_from_title("Director", role_weights) == "Director"
    assert _extract_role_from_title("VP of Sales", role_weights) == "Other"
    assert _extract_role_from_title("", role_weights) == "Other"


# -- Empty board aggregate ----------------------------------------------------

def test_board_aggregate_empty(config):
    """Empty individual scores should produce zero aggregate."""
    aggregate = compute_board_aggregate_risk([], config)
    assert aggregate.weighted_score == 0.0
    assert aggregate.highest_risk_individual == ""
    assert len(aggregate.key_findings) > 0  # Should note no data
