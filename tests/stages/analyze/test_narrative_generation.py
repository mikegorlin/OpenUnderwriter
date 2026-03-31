"""Tests for LLM narrative generation with full analytical context.

Verifies that generate_all_narratives() populates all 6 section
narratives, that LLM prompts include company-specific data, and
that narratives avoid generic boilerplate.

Phase 116-04 deliverable.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.density import DensityLevel, PreComputedNarratives


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_anthropic_response() -> MagicMock:
    """Create a mock Anthropic response object."""
    response = MagicMock()
    content_block = MagicMock()
    content_block.text = (
        "RPM International reported revenue of $7.3B with net income of "
        "$412M (F3 = 3/8 points deducted). The Altman Z-Score of 2.1 places "
        "the company in the grey zone, while the Beneish M-Score of -2.8 "
        "suggests low earnings manipulation risk. Current ratio of 1.4 and "
        "debt-to-equity of 1.2 indicate moderate leverage."
    )
    response.content = [content_block]
    return response


@pytest.fixture()
def mock_state() -> MagicMock:
    """Create a mock AnalysisState with realistic data for testing."""
    state = MagicMock()
    state.ticker = "RPM"

    # Company identity
    state.company.identity.legal_name.value = "RPM International Inc."
    state.company.identity.sector.value = "Industrials"
    state.company.identity.sic_code.value = "2851"
    state.company.market_cap.value = 14_500_000_000
    state.company.employee_count.value = 17200
    state.company.years_public = 47
    state.company.business_description.value = (
        "RPM International Inc. manufactures specialty coatings, sealants, "
        "and building materials."
    )
    state.company.filer_category.value = "Large Accelerated Filer"
    state.company.risk_classification.value = "MODERATE"
    state.company.do_exposure_factors = []
    state.company.revenue_segments = []
    state.company.geographic_footprint = []
    state.company.identity.is_fpi = False

    # Extracted financials
    state.extracted.financials.statements.income_statement.line_items = []
    state.extracted.financials.distress.altman_z_score.score = 2.1
    state.extracted.financials.distress.altman_z_score.zone = "GREY"
    state.extracted.financials.distress.ohlson_o_score.score = 0.3
    state.extracted.financials.distress.ohlson_o_score.zone = "SAFE"
    state.extracted.financials.distress.piotroski_f_score.score = 6
    state.extracted.financials.distress.piotroski_f_score.zone = "MODERATE"
    state.extracted.financials.distress.beneish_m_score.score = -2.8
    state.extracted.financials.distress.beneish_m_score.zone = "UNLIKELY_MANIPULATOR"
    state.extracted.financials.debt_structure = None
    state.extracted.financials.liquidity = None
    state.extracted.financials.leverage = None
    state.extracted.financials.earnings_quality = None
    state.extracted.financials.audit = None

    # Extracted market
    state.extracted.market.stock.current_price.value = 120.50
    state.extracted.market.stock.high_52w.value = 135.80
    state.extracted.market.stock.low_52w.value = 98.20
    state.extracted.market.stock.decline_from_high_pct.value = 11.3
    state.extracted.market.stock.sector_relative_performance = None
    state.extracted.market.short_interest.short_pct_float = None
    state.extracted.market.short_interest.trend_6m = None
    state.extracted.market.stock_drops.worst_single_day = None
    state.extracted.market.stock_drops.significant_drops = []
    state.extracted.market.insider_analysis.net_buying_selling = None
    state.extracted.market.insider_analysis.total_insider_selling = None
    state.extracted.market.insider_analysis.pct_10b5_1 = None
    state.extracted.market.insider_analysis.cluster_events = []
    state.extracted.market.analyst.consensus = None
    state.extracted.market.analyst.recent_downgrades = 0
    state.extracted.market.analyst.recent_upgrades = 0

    # Governance
    state.extracted.governance.board.independence_ratio.value = 0.82
    state.extracted.governance.board.ceo_chair_duality.value = False
    state.extracted.governance.board.size.value = 11
    state.extracted.governance.board.avg_tenure_years.value = 7.3
    state.extracted.governance.governance_score.total_score.value = 72
    state.extracted.governance.leadership.executives = []
    state.extracted.governance.board_forensics = []
    state.extracted.governance.comp_analysis.say_on_pay_pct.value = 94.2
    state.extracted.governance.comp_analysis.ceo_total_comp.value = 8_500_000
    state.extracted.governance.comp_analysis.comp_mix = {"equity": 65}
    state.extracted.governance.board.classified_board = None
    state.extracted.governance.board.dual_class_structure = None
    state.extracted.governance.board.overboarded_count = None
    state.extracted.governance.leadership.departures_18mo = []

    # Litigation
    state.extracted.litigation.securities_class_actions = []
    state.extracted.litigation.derivative_suits = []
    state.extracted.litigation.sec_enforcement.highest_confirmed_stage = None
    state.extracted.litigation.sol_map = []
    state.extracted.litigation.total_litigation_reserve = None
    state.extracted.litigation.defense = None
    state.extracted.litigation.industry_patterns = []
    state.extracted.litigation.settlement_history = []

    # Scoring
    factor_f3 = MagicMock()
    factor_f3.factor_id = "F3"
    factor_f3.factor_name = "Financial Health"
    factor_f3.points_deducted = 3.0
    factor_f3.max_points = 8
    factor_f3.evidence = ["Altman Z in grey zone", "Moderate leverage"]
    factor_f3.rules_triggered = []
    factor_f3.sub_components = {}
    factor_f3.signal_contributions = []

    state.scoring.quality_score = 78.5
    state.scoring.composite_score = 75.0
    state.scoring.tier.tier = "WRITE"
    state.scoring.tier.action = "Standard underwriting"
    state.scoring.tier.probability_range = "5-15%"
    state.scoring.claim_probability.band = "MODERATE"
    state.scoring.claim_probability.range_low_pct = 5.0
    state.scoring.claim_probability.range_high_pct = 15.0
    state.scoring.factor_scores = [factor_f3]
    state.scoring.red_flags = []
    state.scoring.binding_ceiling_id = None
    state.scoring.patterns_detected = []

    # Analysis
    state.analysis.section_densities = {}
    state.analysis.signal_results = {}

    # Benchmark
    state.benchmark.inherent_risk.sector_annual_rate_pct = 3.2
    state.benchmark.inherent_risk.company_adjusted_rate_pct = 4.1

    # Executive summary
    state.executive_summary = None

    return state


# ---------------------------------------------------------------------------
# Tests: Financial narrative contains company data
# ---------------------------------------------------------------------------
class TestFinancialNarrative:
    """Verify financial narrative prompt includes company-specific data."""

    def test_financial_narrative_contains_company_data(
        self, mock_state: MagicMock, mock_anthropic_response: MagicMock,
    ) -> None:
        """Financial narrative prompt includes distress scores and ratios."""
        from do_uw.stages.benchmark.narrative_data import extract_section_data

        data = extract_section_data(mock_state, "financial")
        assert data["altman_z"] == 2.1
        assert data["altman_zone"] == "GREY"
        assert data["beneish_m"] == -2.8
        assert data["f3_points_deducted"] == 3.0

    def test_financial_prompt_is_section_specific(self) -> None:
        """Financial prompt mentions revenue, distress models, F3."""
        from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

        prompt = build_section_prompt(
            "financial", "RPM International", "{}", "3-5 sentences",
        )
        assert "financial health" in prompt.lower()
        assert "Altman Z-Score" in prompt
        assert "Beneish M-Score" in prompt
        assert "F3" in prompt
        assert "Revenue" in prompt


# ---------------------------------------------------------------------------
# Tests: Governance narrative contains board data
# ---------------------------------------------------------------------------
class TestGovernanceNarrative:
    """Verify governance narrative prompt includes board data."""

    def test_governance_narrative_contains_board_data(
        self, mock_state: MagicMock,
    ) -> None:
        """Governance data includes board size, independence, compensation."""
        from do_uw.stages.benchmark.narrative_data import extract_section_data

        data = extract_section_data(mock_state, "governance")
        assert data["board_size"] == 11
        assert data["independence_ratio"] == 0.82
        assert data["say_on_pay_pct"] == 94.2
        assert data["ceo_total_comp"] == 8_500_000
        assert data["total_score"] == 72

    def test_governance_prompt_is_section_specific(self) -> None:
        """Governance prompt mentions board size, CEO, F6."""
        from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

        prompt = build_section_prompt(
            "governance", "RPM International", "{}", "3-5 sentences",
        )
        assert "Board size" in prompt
        assert "independence ratio" in prompt
        assert "CEO" in prompt
        assert "F6" in prompt


# ---------------------------------------------------------------------------
# Tests: Litigation narrative contains SCA data
# ---------------------------------------------------------------------------
class TestLitigationNarrative:
    """Verify litigation narrative prompt includes SCA and sector data."""

    def test_litigation_narrative_contains_sca_data(
        self, mock_state: MagicMock,
    ) -> None:
        """Litigation data includes SCA count, sector filing rate."""
        from do_uw.stages.benchmark.narrative_data import extract_section_data

        data = extract_section_data(mock_state, "litigation")
        assert data["active_sca_count"] == 0
        assert data["sector_filing_rate_pct"] == 3.2
        assert data["company_adjusted_rate_pct"] == 4.1

    def test_litigation_prompt_is_section_specific(self) -> None:
        """Litigation prompt mentions SCA, lead counsel, F1/F5/F9."""
        from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

        prompt = build_section_prompt(
            "litigation", "RPM International", "{}", "3-5 sentences",
        )
        assert "SCA" in prompt
        assert "Securities Class Action" in prompt
        assert "F1" in prompt
        assert "F5" in prompt
        assert "F9" in prompt


# ---------------------------------------------------------------------------
# Tests: Narrative not generic
# ---------------------------------------------------------------------------
class TestNarrativeNotGeneric:
    """Verify narratives avoid banned generic phrases."""

    def test_narrative_not_generic(self) -> None:
        """Prompts forbid generic phrases."""
        from do_uw.stages.benchmark.narrative_prompts import (
            COMMON_RULES,
            build_section_prompt,
        )

        # Common rules ban generic phrases
        assert "This section" in COMMON_RULES
        assert "No hedging" in COMMON_RULES

        # Each section prompt includes the rules
        for section in ("financial", "market", "governance",
                        "litigation", "scoring", "company"):
            prompt = build_section_prompt(
                section, "TestCo", "{}", "3-5 sentences",
            )
            assert "No hedging" in prompt
            assert "company-specific data" in prompt


# ---------------------------------------------------------------------------
# Tests: All narrative fields populated
# ---------------------------------------------------------------------------
class TestAllFieldsPopulated:
    """Verify all 6 PreComputedNarratives fields are non-None after generation."""

    def test_all_narrative_fields_populated(
        self, mock_state: MagicMock, mock_anthropic_response: MagicMock,
    ) -> None:
        """All 6 section narrative fields should be non-None with LLM available."""
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_anthropic_response

        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=mock_client,
        ):
            from do_uw.stages.benchmark.narrative_generator import (
                clear_cache,
                generate_all_narratives,
            )
            clear_cache()
            narratives = generate_all_narratives(mock_state)

        # All 6 section fields populated (plus ai_risk and executive)
        assert narratives.company is not None
        assert narratives.financial is not None
        assert narratives.market is not None
        assert narratives.governance is not None
        assert narratives.litigation is not None
        assert narratives.scoring is not None

    def test_fallback_when_llm_unavailable(
        self, mock_state: MagicMock,
    ) -> None:
        """When LLM is unavailable, fallback narratives are used."""
        with patch(
            "do_uw.stages.benchmark.narrative_generator._get_client",
            return_value=None,
        ):
            from do_uw.stages.benchmark.narrative_generator import (
                clear_cache,
                generate_all_narratives,
            )
            clear_cache()
            narratives = generate_all_narratives(mock_state)

        # Should not crash; fallback may return empty strings
        assert isinstance(narratives, PreComputedNarratives)


# ---------------------------------------------------------------------------
# Tests: Section-specific prompts reference the right data
# ---------------------------------------------------------------------------
class TestPromptDataContext:
    """Verify each section prompt builder requires the right analytical data."""

    def test_market_prompt_requires_stock_data(self) -> None:
        """Market prompt requires stock price, drops, insider activity."""
        from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

        prompt = build_section_prompt(
            "market", "TestCo", "{}", "3-5 sentences",
        )
        assert "Stock price" in prompt or "stock price" in prompt
        assert "F2" in prompt
        assert "F7" in prompt
        assert "insider" in prompt.lower()

    def test_scoring_prompt_requires_tier_data(self) -> None:
        """Scoring prompt requires quality score, tier, factor deductions."""
        from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

        prompt = build_section_prompt(
            "scoring", "TestCo", "{}", "3-5 sentences",
        )
        assert "Quality score" in prompt
        assert "tier" in prompt.lower()
        assert "red flag" in prompt.lower()

    def test_company_prompt_requires_profile_data(self) -> None:
        """Company prompt requires ticker, sector, market cap, employees."""
        from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

        prompt = build_section_prompt(
            "company", "TestCo", "{}", "3-5 sentences",
        )
        assert "ticker" in prompt.lower()
        assert "Market capitalization" in prompt
        assert "Employee count" in prompt
        assert "SIC" in prompt

    def test_unknown_section_uses_generic_prompt(self) -> None:
        """Unknown section ID falls back to generic prompt."""
        from do_uw.stages.benchmark.narrative_prompts import build_section_prompt

        prompt = build_section_prompt(
            "unknown_section", "TestCo", "{}", "3-5 sentences",
        )
        assert "unknown_section" in prompt
        assert "company-specific data" in prompt


# ---------------------------------------------------------------------------
# Tests: Data extraction completeness
# ---------------------------------------------------------------------------
class TestDataExtraction:
    """Verify data extractors pull rich analytical context."""

    def test_scoring_data_includes_all_factors(
        self, mock_state: MagicMock,
    ) -> None:
        """Scoring extractor includes quality score, tier, factor deductions."""
        from do_uw.stages.benchmark.narrative_data import extract_section_data

        data = extract_section_data(mock_state, "scoring")
        assert data["quality_score"] == 78.5
        assert data["tier"] == "WRITE"
        assert data["tier_action"] == "Standard underwriting"
        assert data["claim_band"] == "MODERATE"
        assert data["top_risk_factors"][0]["name"] == "Financial Health"

    def test_company_data_includes_profile(
        self, mock_state: MagicMock,
    ) -> None:
        """Company extractor includes name, ticker, sector, market cap."""
        from do_uw.stages.benchmark.narrative_data import extract_section_data

        data = extract_section_data(mock_state, "company")
        assert data["legal_name"] == "RPM International Inc."
        assert data["ticker"] == "RPM"
        assert data["sector"] == "Industrials"
        assert data["market_cap"] == 14_500_000_000
        assert data["employees"] == 17200
        assert data["years_public"] == 47

    def test_market_data_includes_stock_prices(
        self, mock_state: MagicMock,
    ) -> None:
        """Market extractor includes current price, 52w high/low."""
        from do_uw.stages.benchmark.narrative_data import extract_section_data

        data = extract_section_data(mock_state, "market")
        assert data["current_price"] == 120.50
        assert data["high_52w"] == 135.80
        assert data["decline_from_high_pct"] == 11.3
