"""Tests for the 7-lens plaintiff assessment engine.

Validates assess_lens, build_peril_map, match_plaintiff_firms,
probability/severity band mapping, and coverage gap collection.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from do_uw.models.peril import (
    PerilMap,
    PerilProbabilityBand,
    PerilSeverityBand,
    PlaintiffAssessment,
    PlaintiffFirmMatch,
)
from do_uw.stages.analyze.signal_results import SignalStatus, DataStatus, PlaintiffLens
from do_uw.stages.score.peril_mapping import (
    _collect_coverage_gaps,
    _compute_overall_rating,
    _extract_key_findings,
    _full_model_probability,
    _full_model_severity,
    _match_firm_to_tier,
    _proportional_probability,
    _proportional_severity,
    assess_lens,
    build_peril_map,
    match_plaintiff_firms,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


def _make_check(
    signal_id: str = "TEST.check",
    status: str = SignalStatus.TRIGGERED,
    plaintiff_lenses: list[str] | None = None,
    category: str = "DECISION_DRIVING",
    evidence: str = "Test evidence",
    data_status: str = DataStatus.EVALUATED,
    data_status_reason: str = "",
    signal_name: str = "Test Check",
) -> dict[str, Any]:
    """Create a mock check result dict."""
    return {
        "signal_id": signal_id,
        "signal_name": signal_name,
        "status": status,
        "evidence": evidence,
        "plaintiff_lenses": plaintiff_lenses or [],
        "category": category,
        "data_status": data_status,
        "data_status_reason": data_status_reason,
    }


def _make_lens_defaults() -> dict[str, list[str]]:
    """Minimal lens defaults for testing."""
    return {
        "STOCK.PRICE": ["SHAREHOLDERS"],
        "STOCK.SHORT": ["SHAREHOLDERS"],
        "FIN.ACCT": ["SHAREHOLDERS", "REGULATORS"],
        "LIT.SCA": ["SHAREHOLDERS"],
        "LIT.REG": ["REGULATORS"],
        "GOV.PAY": ["SHAREHOLDERS"],
        "BIZ.UNI.cyber": ["CUSTOMERS", "REGULATORS"],
        "BIZ.UNI.labor": ["EMPLOYEES"],
    }


# -----------------------------------------------------------------------
# assess_lens tests
# -----------------------------------------------------------------------


class TestAssessLens:
    """Test per-lens assessment logic."""

    def test_shareholders_multiple_triggers_elevated(self) -> None:
        """SHAREHOLDERS with many triggered checks -> ELEVATED probability."""
        checks = [
            _make_check("STOCK.PRICE.decline_30d", plaintiff_lenses=["SHAREHOLDERS"]),
            _make_check("STOCK.PRICE.decline_90d", plaintiff_lenses=["SHAREHOLDERS"]),
            _make_check("FIN.ACCT.restatement", plaintiff_lenses=["SHAREHOLDERS", "REGULATORS"]),
            _make_check("STOCK.SHORT.high", plaintiff_lenses=["SHAREHOLDERS"]),
            _make_check("STOCK.INSIDER.cluster", plaintiff_lenses=["SHAREHOLDERS"]),
            _make_check("LIT.SCA.active", plaintiff_lenses=["SHAREHOLDERS"]),
            _make_check("FIN.GUIDE.miss", plaintiff_lenses=["SHAREHOLDERS"]),
            # Add some clear checks to have a total
            _make_check("GOV.PAY.clawback", status=SignalStatus.CLEAR, plaintiff_lenses=["SHAREHOLDERS"]),
            _make_check("BIZ.SIZE.market_cap", status=SignalStatus.CLEAR, plaintiff_lenses=["SHAREHOLDERS"]),
        ]
        # High claim probability for full model
        claim_prob = {"band": "HIGH", "range_high_pct": 15.0}

        assessment = assess_lens(
            lens=PlaintiffLens.SHAREHOLDERS,
            signal_results=checks,
            lens_defaults=_make_lens_defaults(),
            claim_probability=claim_prob,
            severity_scenarios=None,
            allegation_mapping=None,
        )

        assert assessment.plaintiff_type == "SHAREHOLDERS"
        assert assessment.modeling_depth == "FULL"
        assert assessment.triggered_signal_count == 7
        assert assessment.total_signal_count == 9
        # HIGH claim prob -> at least ELEVATED
        assert assessment.probability_band in ("ELEVATED", "HIGH")

    def test_employees_zero_triggers_very_low(self) -> None:
        """EMPLOYEES with 0 triggered checks -> VERY_LOW probability."""
        checks = [
            _make_check("BIZ.UNI.labor", status=SignalStatus.CLEAR, plaintiff_lenses=["EMPLOYEES"]),
            _make_check("BIZ.UNI.labor_2", status=SignalStatus.CLEAR, plaintiff_lenses=["EMPLOYEES"]),
        ]

        assessment = assess_lens(
            lens=PlaintiffLens.EMPLOYEES,
            signal_results=checks,
            lens_defaults=_make_lens_defaults(),
            claim_probability=None,
            severity_scenarios=None,
            allegation_mapping=None,
        )

        assert assessment.plaintiff_type == "EMPLOYEES"
        assert assessment.modeling_depth == "PROPORTIONAL"
        assert assessment.triggered_signal_count == 0
        assert assessment.probability_band == "VERY_LOW"
        assert assessment.severity_band == "NUISANCE"

    def test_proportional_vs_full_depth(self) -> None:
        """SHAREHOLDERS=FULL, CUSTOMERS=PROPORTIONAL."""
        checks = [
            _make_check("test1", plaintiff_lenses=["SHAREHOLDERS", "CUSTOMERS"]),
        ]

        sh = assess_lens(
            lens=PlaintiffLens.SHAREHOLDERS,
            signal_results=checks,
            lens_defaults={},
            claim_probability={"band": "MODERATE", "range_high_pct": 5.0},
            severity_scenarios=None,
            allegation_mapping=None,
        )
        cu = assess_lens(
            lens=PlaintiffLens.CUSTOMERS,
            signal_results=checks,
            lens_defaults={},
            claim_probability=None,
            severity_scenarios=None,
            allegation_mapping=None,
        )

        assert sh.modeling_depth == "FULL"
        assert cu.modeling_depth == "PROPORTIONAL"

    def test_lens_defaults_fallback(self) -> None:
        """When check has no plaintiff_lenses, falls back to config defaults."""
        checks = [
            _make_check("STOCK.PRICE.decline", plaintiff_lenses=[]),
            _make_check("LIT.REG.sec_action", plaintiff_lenses=[]),
        ]
        defaults = _make_lens_defaults()

        sh = assess_lens(
            lens=PlaintiffLens.SHAREHOLDERS,
            signal_results=checks,
            lens_defaults=defaults,
            claim_probability=None,
            severity_scenarios=None,
            allegation_mapping=None,
        )
        reg = assess_lens(
            lens=PlaintiffLens.REGULATORS,
            signal_results=checks,
            lens_defaults=defaults,
            claim_probability=None,
            severity_scenarios=None,
            allegation_mapping=None,
        )

        # STOCK.PRICE defaults to SHAREHOLDERS only
        assert sh.triggered_signal_count >= 1
        # LIT.REG defaults to REGULATORS
        assert reg.triggered_signal_count >= 1


# -----------------------------------------------------------------------
# Probability band tests
# -----------------------------------------------------------------------


class TestProbabilityBandMapping:
    """Test probability band mapping functions."""

    def test_proportional_zero_very_low(self) -> None:
        assert _proportional_probability(0) == "VERY_LOW"

    def test_proportional_one_low(self) -> None:
        assert _proportional_probability(1) == "LOW"

    def test_proportional_two_low(self) -> None:
        assert _proportional_probability(2) == "LOW"

    def test_proportional_three_moderate(self) -> None:
        assert _proportional_probability(3) == "MODERATE"

    def test_proportional_five_moderate(self) -> None:
        assert _proportional_probability(5) == "MODERATE"

    def test_proportional_six_elevated(self) -> None:
        assert _proportional_probability(6) == "ELEVATED"

    def test_full_model_high_claim_prob(self) -> None:
        """High claim probability -> HIGH band."""
        result = _full_model_probability(
            triggered_count=5,
            total_count=10,
            claim_probability={"band": "HIGH", "range_high_pct": 15.0},
        )
        assert result == "HIGH"

    def test_full_model_low_claim_prob_zero_triggers(self) -> None:
        """Low claim prob + zero triggers -> downgraded."""
        result = _full_model_probability(
            triggered_count=0,
            total_count=10,
            claim_probability={"band": "LOW", "range_high_pct": 2.0},
        )
        # LOW base should downgrade to VERY_LOW with 0 triggers
        assert result == "VERY_LOW"


# -----------------------------------------------------------------------
# Severity band tests
# -----------------------------------------------------------------------


class TestSeverityBandMapping:
    """Test severity band mapping functions."""

    def test_proportional_zero_nuisance(self) -> None:
        assert _proportional_severity(0) == "NUISANCE"

    def test_proportional_two_minor(self) -> None:
        assert _proportional_severity(2) == "MINOR"

    def test_proportional_four_moderate(self) -> None:
        assert _proportional_severity(4) == "MODERATE"

    def test_proportional_five_significant(self) -> None:
        assert _proportional_severity(5) == "SIGNIFICANT"

    def test_full_model_nuisance(self) -> None:
        """Median settlement < $5M -> NUISANCE."""
        result = _full_model_severity({
            "scenarios": [{"percentile": 50, "label": "median", "settlement_estimate": 2_000_000}],
        })
        assert result == "NUISANCE"

    def test_full_model_minor(self) -> None:
        """Median settlement $5M-$25M -> MINOR."""
        result = _full_model_severity({
            "scenarios": [{"percentile": 50, "label": "median", "settlement_estimate": 15_000_000}],
        })
        assert result == "MINOR"

    def test_full_model_moderate(self) -> None:
        """Median settlement $25M-$100M -> MODERATE."""
        result = _full_model_severity({
            "scenarios": [{"percentile": 50, "label": "median", "settlement_estimate": 50_000_000}],
        })
        assert result == "MODERATE"

    def test_full_model_significant(self) -> None:
        """Median settlement $100M-$500M -> SIGNIFICANT."""
        result = _full_model_severity({
            "scenarios": [{"percentile": 50, "label": "median", "settlement_estimate": 200_000_000}],
        })
        assert result == "SIGNIFICANT"

    def test_full_model_severe(self) -> None:
        """Median settlement > $500M -> SEVERE."""
        result = _full_model_severity({
            "scenarios": [{"percentile": 50, "label": "median", "settlement_estimate": 1_000_000_000}],
        })
        assert result == "SEVERE"

    def test_full_model_no_median_scenario(self) -> None:
        """No median scenario -> NUISANCE (default zero)."""
        result = _full_model_severity({
            "scenarios": [{"percentile": 25, "label": "favorable", "settlement_estimate": 50_000_000}],
        })
        assert result == "NUISANCE"


# -----------------------------------------------------------------------
# Plaintiff firm matching tests
# -----------------------------------------------------------------------


class TestPlaintiffFirmMatching:
    """Test plaintiff firm matching logic."""

    def test_tier_1_match_severity_2x(self) -> None:
        """Tier 1 firm match -> severity_multiplier 2.0."""
        firms_config = {
            "tiers": {
                "1": {
                    "label": "elite",
                    "severity_multiplier": 2.0,
                    "firms": ["Bernstein Litowitz Berger & Grossmann"],
                },
                "2": {"label": "major", "severity_multiplier": 1.5, "firms": []},
            },
        }
        match = _match_firm_to_tier(
            "Lead counsel: Bernstein Litowitz Berger & Grossmann LLP",
            firms_config,
        )
        assert match is not None
        assert match.tier == 1
        assert match.severity_multiplier == 2.0
        assert match.firm_name == "Bernstein Litowitz Berger & Grossmann"

    def test_tier_2_match(self) -> None:
        """Tier 2 firm match -> severity_multiplier 1.5."""
        firms_config = {
            "tiers": {
                "1": {"label": "elite", "severity_multiplier": 2.0, "firms": []},
                "2": {
                    "label": "major",
                    "severity_multiplier": 1.5,
                    "firms": ["Pomerantz"],
                },
            },
        }
        match = _match_firm_to_tier("Pomerantz LLP", firms_config)
        assert match is not None
        assert match.tier == 2
        assert match.severity_multiplier == 1.5

    def test_no_match_returns_none(self) -> None:
        """Unknown firm -> None (no match)."""
        firms_config = {
            "tiers": {
                "1": {"label": "elite", "severity_multiplier": 2.0, "firms": ["Big Firm"]},
                "2": {"label": "major", "severity_multiplier": 1.5, "firms": ["Other Firm"]},
            },
        }
        match = _match_firm_to_tier("Unknown Regional Attorneys", firms_config)
        assert match is None

    def test_case_insensitive_matching(self) -> None:
        """Firm matching is case-insensitive."""
        firms_config = {
            "tiers": {
                "1": {
                    "label": "elite",
                    "severity_multiplier": 2.0,
                    "firms": ["Robbins Geller Rudman & Dowd"],
                },
                "2": {"label": "major", "severity_multiplier": 1.5, "firms": []},
            },
        }
        match = _match_firm_to_tier("ROBBINS GELLER RUDMAN & DOWD LLP", firms_config)
        assert match is not None
        assert match.tier == 1


# -----------------------------------------------------------------------
# build_peril_map integration test
# -----------------------------------------------------------------------


class TestBuildPerilMap:
    """Integration test for build_peril_map."""

    def test_produces_exactly_7_assessments(self) -> None:
        """build_peril_map always returns exactly 7 assessments."""
        from do_uw.models.state import AnalysisResults, AnalysisState

        state = AnalysisState(ticker="TEST")
        state.analysis = AnalysisResults(
            signal_results={
                "STOCK.PRICE.decline": {
                    "signal_id": "STOCK.PRICE.decline",
                    "signal_name": "Stock Price Decline",
                    "status": "TRIGGERED",
                    "evidence": "30-day decline >20%",
                    "plaintiff_lenses": ["SHAREHOLDERS"],
                    "category": "DECISION_DRIVING",
                    "data_status": "EVALUATED",
                },
                "LIT.REG.sec": {
                    "signal_id": "LIT.REG.sec",
                    "signal_name": "SEC Investigation",
                    "status": "TRIGGERED",
                    "evidence": "Wells notice issued",
                    "plaintiff_lenses": ["REGULATORS"],
                    "category": "DECISION_DRIVING",
                    "data_status": "EVALUATED",
                },
                "FIN.LIQ.missing": {
                    "signal_id": "FIN.LIQ.missing",
                    "signal_name": "Liquidity Data",
                    "status": "SKIPPED",
                    "evidence": "",
                    "plaintiff_lenses": ["CREDITORS", "SHAREHOLDERS"],
                    "category": "DECISION_DRIVING",
                    "data_status": "DATA_UNAVAILABLE",
                    "data_status_reason": "No financial data available",
                },
            },
        )

        peril_map = build_peril_map(state)

        assert len(peril_map.assessments) == 7
        lens_types = {a.plaintiff_type for a in peril_map.assessments}
        assert lens_types == {
            "SHAREHOLDERS", "REGULATORS", "CUSTOMERS",
            "COMPETITORS", "EMPLOYEES", "CREDITORS", "GOVERNMENT",
        }

    def test_overall_rating_is_max(self) -> None:
        """Overall peril rating is the max of individual lens bands."""
        assessments = [
            PlaintiffAssessment(
                plaintiff_type="SHAREHOLDERS",
                probability_band="ELEVATED",
                severity_band="MODERATE",
                modeling_depth="FULL",
            ),
            PlaintiffAssessment(
                plaintiff_type="REGULATORS",
                probability_band="LOW",
                severity_band="MINOR",
                modeling_depth="FULL",
            ),
            PlaintiffAssessment(
                plaintiff_type="CUSTOMERS",
                probability_band="VERY_LOW",
                severity_band="NUISANCE",
                modeling_depth="PROPORTIONAL",
            ),
            PlaintiffAssessment(
                plaintiff_type="COMPETITORS",
                probability_band="VERY_LOW",
                severity_band="NUISANCE",
                modeling_depth="PROPORTIONAL",
            ),
            PlaintiffAssessment(
                plaintiff_type="EMPLOYEES",
                probability_band="VERY_LOW",
                severity_band="NUISANCE",
                modeling_depth="PROPORTIONAL",
            ),
            PlaintiffAssessment(
                plaintiff_type="CREDITORS",
                probability_band="MODERATE",
                severity_band="MINOR",
                modeling_depth="PROPORTIONAL",
            ),
            PlaintiffAssessment(
                plaintiff_type="GOVERNMENT",
                probability_band="VERY_LOW",
                severity_band="NUISANCE",
                modeling_depth="PROPORTIONAL",
            ),
        ]

        overall = _compute_overall_rating(assessments)
        assert overall == "ELEVATED"

    def test_coverage_gaps_from_data_unavailable(self) -> None:
        """Coverage gaps populated from DATA_UNAVAILABLE checks."""
        checks = [
            _make_check(
                "FIN.LIQ.ratio",
                status=SignalStatus.SKIPPED,
                data_status=DataStatus.DATA_UNAVAILABLE,
                data_status_reason="No financial statements available",
            ),
            _make_check(
                "STOCK.PRICE.decline",
                status=SignalStatus.TRIGGERED,
                data_status=DataStatus.EVALUATED,
            ),
        ]
        gaps = _collect_coverage_gaps(checks)
        assert len(gaps) == 1
        assert "FIN.LIQ.ratio" in gaps[0]
        assert "No financial statements available" in gaps[0]

    def test_no_coverage_gaps_when_all_evaluated(self) -> None:
        """No coverage gaps when all checks are EVALUATED."""
        checks = [
            _make_check("STOCK.PRICE.decline", data_status=DataStatus.EVALUATED),
            _make_check("FIN.ACCT.quality", data_status=DataStatus.EVALUATED),
        ]
        gaps = _collect_coverage_gaps(checks)
        assert len(gaps) == 0


# -----------------------------------------------------------------------
# Key findings extraction tests
# -----------------------------------------------------------------------


class TestExtractKeyFindings:
    """Test key findings extraction from triggered checks."""

    def test_prioritizes_decision_driving(self) -> None:
        """DECISION_DRIVING checks appear before CONTEXT_DISPLAY."""
        checks = [
            _make_check(
                "ctx1", category="CONTEXT_DISPLAY",
                evidence="Context info", signal_name="Context Check",
            ),
            _make_check(
                "dec1", category="DECISION_DRIVING",
                evidence="Decision info", signal_name="Decision Check",
            ),
        ]
        findings = _extract_key_findings(checks, max_findings=5)
        assert len(findings) == 2
        assert "Decision Check" in findings[0]

    def test_max_findings_limit(self) -> None:
        """Respects max_findings limit."""
        checks = [_make_check(f"check_{i}", evidence=f"Finding {i}") for i in range(10)]
        findings = _extract_key_findings(checks, max_findings=3)
        assert len(findings) == 3
