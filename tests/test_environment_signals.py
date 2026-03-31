"""Tests for ENVR.* environment assessment signal extraction.

Phase 97: Validates that extract_environment_signals computes 5 numeric
scores from existing state data (risk factors, geographic footprint,
litigation, LLM extraction).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.state import RiskFactorProfile


def _mock_state(
    risk_factors: list[RiskFactorProfile] | None = None,
    geographic_footprint: list | None = None,
    litigation_cases: list | None = None,
    regulatory_environment: str | None = None,
    interest_rate_risk: str | None = None,
    currency_risk: str | None = None,
    text_signals: dict | None = None,
) -> MagicMock:
    """Build a minimal mock AnalysisState for environment extraction."""
    state = MagicMock()
    state.extracted.risk_factors = risk_factors or []
    state.extracted.text_signals = text_signals or {}

    # Geographic footprint: list of SourcedValue[dict]
    if geographic_footprint is not None:
        sv_list = []
        for gf in geographic_footprint:
            sv = MagicMock()
            sv.value = gf
            sv_list.append(sv)
        state.company.geographic_footprint = sv_list
    else:
        state.company.geographic_footprint = []

    # Litigation
    if litigation_cases is not None:
        state.extracted.litigation.securities_class_actions = litigation_cases
    else:
        state.extracted.litigation = None

    # LLM extraction data (via acquired_data.llm_extractions)
    llm_data: dict = {}
    if any(v is not None for v in [regulatory_environment, interest_rate_risk, currency_risk]):
        llm_data["10-K:test"] = {
            "regulatory_environment": regulatory_environment,
            "interest_rate_risk": interest_rate_risk,
            "currency_risk": currency_risk,
        }
    state.acquired_data.llm_extractions = llm_data

    return state


class TestRegulatoryIntensity:
    """ENVR.regulatory_intensity: count distinct high-intensity regulators."""

    def test_regulatory_risk_factors_produce_positive_score(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            risk_factors=[
                RiskFactorProfile(title="FDA approval risk", category="REGULATORY", severity="HIGH"),
                RiskFactorProfile(title="EPA compliance", category="REGULATORY", severity="MEDIUM"),
            ],
        )
        result = extract_environment_signals(state)
        assert result["regulatory_intensity_score"] >= 1

    def test_llm_regulatory_environment_parsed(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            regulatory_environment="Subject to regulation by the SEC, FDA, and EPA.",
        )
        result = extract_environment_signals(state)
        assert result["regulatory_intensity_score"] >= 3

    def test_no_regulatory_returns_zero(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state()
        result = extract_environment_signals(state)
        assert result["regulatory_intensity_score"] == 0


class TestGeopolitical:
    """ENVR.geopolitical: geographic footprint vs sanctioned/high-risk countries."""

    def test_china_in_footprint(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            geographic_footprint=[
                {"jurisdiction": "China", "percentage": 10.0},
            ],
        )
        result = extract_environment_signals(state)
        assert result["geopolitical_risk_score"] >= 1

    def test_iran_sanctioned_country(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            geographic_footprint=[
                {"jurisdiction": "Iran", "percentage": 5.0},
            ],
        )
        result = extract_environment_signals(state)
        assert result["geopolitical_risk_score"] == 3

    def test_us_only_returns_zero(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            geographic_footprint=[
                {"jurisdiction": "United States", "percentage": 100.0},
            ],
        )
        result = extract_environment_signals(state)
        assert result["geopolitical_risk_score"] == 0

    def test_many_high_risk_countries(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            geographic_footprint=[
                {"jurisdiction": "China", "percentage": 20.0},
                {"jurisdiction": "Brazil", "percentage": 15.0},
                {"jurisdiction": "India", "percentage": 10.0},
                {"jurisdiction": "Turkey", "percentage": 5.0},
            ],
        )
        result = extract_environment_signals(state)
        assert result["geopolitical_risk_score"] >= 2


class TestCyberRisk:
    """ENVR.cyber_risk: CYBER risk factor severity and breach indicators."""

    def test_high_severity_cyber(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            risk_factors=[
                RiskFactorProfile(title="Cybersecurity breach risk", category="CYBER", severity="HIGH"),
            ],
        )
        result = extract_environment_signals(state)
        assert result["cyber_risk_score"] >= 2

    def test_low_severity_cyber(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            risk_factors=[
                RiskFactorProfile(title="Data protection compliance", category="CYBER", severity="LOW"),
            ],
        )
        result = extract_environment_signals(state)
        assert result["cyber_risk_score"] >= 1

    def test_breach_indicator_in_text_signals(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            text_signals={"cybersecurity_incident": "Data breach reported in 2024"},
        )
        result = extract_environment_signals(state)
        assert result["cyber_risk_score"] >= 3


class TestESGGap:
    """ENVR.esg_gap: ESG risk factors vs ESG litigation presence."""

    def test_esg_risk_factor_with_litigation(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        mock_case = MagicMock()
        mock_case.case_name = MagicMock()
        mock_case.case_name.value = "Environmental Class Action v. Company"
        state = _mock_state(
            risk_factors=[
                RiskFactorProfile(title="Climate risk", category="ESG", severity="HIGH"),
            ],
            litigation_cases=[mock_case],
        )
        result = extract_environment_signals(state)
        assert result["esg_gap_score"] >= 2

    def test_esg_risk_factor_no_litigation(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            risk_factors=[
                RiskFactorProfile(title="ESG disclosure requirements", category="ESG", severity="HIGH"),
            ],
        )
        result = extract_environment_signals(state)
        assert result["esg_gap_score"] >= 1

    def test_no_esg_returns_zero(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state()
        result = extract_environment_signals(state)
        assert result["esg_gap_score"] == 0


class TestMacroSensitivity:
    """ENVR.macro_sensitivity: count macro dimensions."""

    def test_interest_rate_and_currency(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            interest_rate_risk="Material exposure to interest rate fluctuations",
            currency_risk="Significant foreign currency translation risk",
        )
        result = extract_environment_signals(state)
        assert result["macro_sensitivity_score"] >= 2

    def test_financial_risk_factors_with_macro_terms(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state(
            risk_factors=[
                RiskFactorProfile(title="Inflation impact on raw materials", category="FINANCIAL", severity="HIGH"),
                RiskFactorProfile(title="Recession risk exposure", category="FINANCIAL", severity="MEDIUM"),
            ],
        )
        result = extract_environment_signals(state)
        assert result["macro_sensitivity_score"] >= 2

    def test_no_macro_returns_zero(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state()
        result = extract_environment_signals(state)
        assert result["macro_sensitivity_score"] == 0


class TestEmptyState:
    """Empty state returns all zero scores."""

    def test_all_scores_zero(self) -> None:
        from do_uw.stages.extract.environment_assessment import extract_environment_signals

        state = _mock_state()
        result = extract_environment_signals(state)
        assert result["regulatory_intensity_score"] == 0
        assert result["geopolitical_risk_score"] == 0
        assert result["esg_gap_score"] == 0
        assert result["cyber_risk_score"] == 0
        assert result["macro_sensitivity_score"] == 0


class TestSignalMapperRouting:
    """ENVR.* prefix routes to environment extraction results."""

    def test_envr_prefix_routes_to_environment(self) -> None:
        from do_uw.stages.analyze.signal_mappers import map_signal_data

        extracted = MagicMock()
        extracted.risk_factors = [
            RiskFactorProfile(title="FDA oversight", category="REGULATORY", severity="HIGH"),
        ]
        extracted.text_signals = {}
        extracted.litigation = None

        company = MagicMock()
        company.geographic_footprint = []

        # Mock acquired_data for LLM extraction access
        analysis = MagicMock()
        analysis.acquired_data = MagicMock()
        analysis.acquired_data.llm_extractions = {}

        # Build a mock state that extract_environment_signals can use
        # We patch the function to avoid deep state traversal
        with patch(
            "do_uw.stages.extract.environment_assessment.extract_environment_signals",
            return_value={
                "regulatory_intensity_score": 2,
                "geopolitical_risk_score": 0,
                "esg_gap_score": 0,
                "cyber_risk_score": 0,
                "macro_sensitivity_score": 0,
            },
        ):
            result = map_signal_data(
                "ENVR.regulatory_intensity",
                {"data_strategy": {"field_key": "regulatory_intensity_score"}},
                extracted,
                company,
                analysis,
            )
        assert result.get("regulatory_intensity_score") == 2
