"""Tests for Phase 33-04 Task 2: easy-win yfinance field extraction.

Validates that new model fields (volume, valuation ratios, analyst count,
GICS code) are populated correctly from yfinance info dict data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from do_uw.models.common import Confidence
from do_uw.models.market import StockPerformance
from do_uw.models.market_events import AnalystSentimentProfile
from do_uw.stages.extract.stock_performance import (
    _extract_float,
    _populate_easy_win_fields,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_info(**overrides: Any) -> dict[str, Any]:
    """Build a yfinance info dict with default values."""
    base: dict[str, Any] = {
        "currentPrice": 150.0,
        "averageDailyVolume10Day": 75_000_000,
        "averageVolume": 60_000_000,
        "trailingPE": 28.5,
        "forwardPE": 24.3,
        "enterpriseToEbitda": 19.7,
        "pegRatio": 1.45,
        "numberOfAnalystOpinions": 42,
        "recommendationMean": 2.1,
        "targetMeanPrice": 200.0,
        "targetHighPrice": 250.0,
        "targetLowPrice": 160.0,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# StockPerformance easy-win fields
# ---------------------------------------------------------------------------


class TestPopulateEasyWinFields:
    """Test _populate_easy_win_fields populates StockPerformance correctly."""

    def test_avg_daily_volume_from_10day(self) -> None:
        """Average volume uses 10-day value when available."""
        perf = StockPerformance()
        info = _make_info()
        _populate_easy_win_fields(perf, info)
        assert perf.avg_daily_volume is not None
        assert perf.avg_daily_volume.value == 75_000_000

    def test_avg_daily_volume_fallback_to_average(self) -> None:
        """Falls back to averageVolume when 10-day is missing."""
        perf = StockPerformance()
        info = _make_info(averageDailyVolume10Day=None)
        _populate_easy_win_fields(perf, info)
        assert perf.avg_daily_volume is not None
        assert perf.avg_daily_volume.value == 60_000_000

    def test_avg_daily_volume_zero_skipped(self) -> None:
        """Zero volume is not stored."""
        perf = StockPerformance()
        info = _make_info(averageDailyVolume10Day=0, averageVolume=0)
        _populate_easy_win_fields(perf, info)
        assert perf.avg_daily_volume is None

    def test_pe_ratio_populated(self) -> None:
        """Trailing P/E ratio is extracted and rounded."""
        perf = StockPerformance()
        _populate_easy_win_fields(perf, _make_info(trailingPE=28.567))
        assert perf.pe_ratio is not None
        assert perf.pe_ratio.value == 28.57

    def test_forward_pe_populated(self) -> None:
        """Forward P/E ratio is extracted."""
        perf = StockPerformance()
        _populate_easy_win_fields(perf, _make_info())
        assert perf.forward_pe is not None
        assert perf.forward_pe.value == 24.3

    def test_ev_ebitda_populated(self) -> None:
        """EV/EBITDA is extracted."""
        perf = StockPerformance()
        _populate_easy_win_fields(perf, _make_info())
        assert perf.ev_ebitda is not None
        assert perf.ev_ebitda.value == 19.7

    def test_peg_ratio_populated(self) -> None:
        """PEG ratio is extracted."""
        perf = StockPerformance()
        _populate_easy_win_fields(perf, _make_info())
        assert perf.peg_ratio is not None
        assert perf.peg_ratio.value == 1.45

    def test_nan_values_skipped(self) -> None:
        """NaN values from yfinance are treated as None."""
        perf = StockPerformance()
        info = _make_info(trailingPE=float("nan"), forwardPE=float("inf"))
        _populate_easy_win_fields(perf, info)
        assert perf.pe_ratio is None
        assert perf.forward_pe is None

    def test_none_values_skipped(self) -> None:
        """Missing keys produce None, not errors."""
        perf = StockPerformance()
        _populate_easy_win_fields(perf, {})
        assert perf.avg_daily_volume is None
        assert perf.pe_ratio is None
        assert perf.forward_pe is None
        assert perf.ev_ebitda is None
        assert perf.peg_ratio is None

    def test_all_fields_have_medium_confidence(self) -> None:
        """All populated fields use MEDIUM confidence."""
        perf = StockPerformance()
        _populate_easy_win_fields(perf, _make_info())
        for field_name in [
            "avg_daily_volume", "pe_ratio", "forward_pe",
            "ev_ebitda", "peg_ratio",
        ]:
            val = getattr(perf, field_name)
            assert val is not None, f"{field_name} should be populated"
            assert val.confidence == Confidence.MEDIUM, (
                f"{field_name} confidence should be MEDIUM"
            )


# ---------------------------------------------------------------------------
# Analyst count population
# ---------------------------------------------------------------------------


class TestAnalystCountPopulation:
    """Test that analyst_count is populated during sentiment extraction."""

    def test_analyst_count_from_extract(self) -> None:
        """extract_analyst_sentiment populates both coverage_count and analyst_count."""
        from do_uw.stages.extract.earnings_guidance import (
            extract_analyst_sentiment,
        )
        from do_uw.models.state import AcquiredData, AnalysisState

        # Build minimal state with market data containing info dict.
        state = AnalysisState(ticker="TEST")
        state.acquired_data = AcquiredData(
            market_data={"info": _make_info()},
        )
        profile, report = extract_analyst_sentiment(state)
        assert profile.coverage_count is not None
        assert profile.coverage_count.value == 42
        assert profile.analyst_count is not None
        assert profile.analyst_count.value == 42

    def test_analyst_count_none_when_missing(self) -> None:
        """analyst_count is None when numberOfAnalystOpinions is absent."""
        from do_uw.stages.extract.earnings_guidance import (
            extract_analyst_sentiment,
        )
        from do_uw.models.state import AcquiredData, AnalysisState

        state = AnalysisState(ticker="TEST")
        state.acquired_data = AcquiredData(
            market_data={"info": {}},
        )
        profile, _ = extract_analyst_sentiment(state)
        assert profile.analyst_count is None


# ---------------------------------------------------------------------------
# GICS code resolution
# ---------------------------------------------------------------------------


class TestGicsCodeResolution:
    """Test GICS code resolution from SIC mapping."""

    def test_gics_from_sic_mapping(self) -> None:
        """GICS code resolved from SIC->GICS mapping config."""
        from do_uw.stages.extract.company_profile_items import _resolve_gics_code
        from do_uw.stages.extract.sourced import sourced_str
        from do_uw.models.company import CompanyIdentity, CompanyProfile

        identity = CompanyIdentity(
            ticker="AAPL",
            sic_code=sourced_str("3571", "SEC EDGAR", Confidence.HIGH),
        )
        profile = CompanyProfile(identity=identity)
        result = _resolve_gics_code(profile, {})
        assert result is not None
        assert result.value == "45202030"
        assert "SIC" in result.source

    def test_gics_none_when_sic_missing(self) -> None:
        """Returns None when no SIC code available."""
        from do_uw.stages.extract.company_profile_items import _resolve_gics_code
        from do_uw.models.company import CompanyIdentity, CompanyProfile

        identity = CompanyIdentity(ticker="TEST")
        profile = CompanyProfile(identity=identity)
        result = _resolve_gics_code(profile, {})
        assert result is None

    def test_gics_none_when_sic_not_in_mapping(self) -> None:
        """Returns None when SIC code has no GICS mapping."""
        from do_uw.stages.extract.company_profile_items import _resolve_gics_code
        from do_uw.stages.extract.sourced import sourced_str
        from do_uw.models.company import CompanyIdentity, CompanyProfile

        identity = CompanyIdentity(
            ticker="TEST",
            sic_code=sourced_str("9999", "SEC EDGAR", Confidence.HIGH),
        )
        profile = CompanyProfile(identity=identity)
        result = _resolve_gics_code(profile, {})
        assert result is None

    def test_gics_mapping_file_exists(self) -> None:
        """The SIC->GICS mapping config file must exist."""
        mapping_path = Path("src/do_uw/brain/config/sic_gics_mapping.json")
        assert mapping_path.exists(), "sic_gics_mapping.json must exist"

    def test_gics_mapping_has_common_sics(self) -> None:
        """Mapping contains commonly used SIC codes."""
        mapping_path = Path("src/do_uw/brain/config/sic_gics_mapping.json")
        data = json.loads(mapping_path.read_text())
        mappings = data["mappings"]
        # AAPL SIC (3571), MSFT (7372), NVDA (3674), JPM (6021), JNJ (2834)
        for sic in ["3571", "7372", "3674", "6021", "2834"]:
            assert sic in mappings, f"Missing SIC {sic} in mapping"


# ---------------------------------------------------------------------------
# Model field existence
# ---------------------------------------------------------------------------


class TestModelFieldsExist:
    """Verify new model fields exist with correct types."""

    def test_stock_performance_volume_field(self) -> None:
        """StockPerformance has avg_daily_volume field."""
        perf = StockPerformance()
        assert hasattr(perf, "avg_daily_volume")
        assert perf.avg_daily_volume is None

    def test_stock_performance_valuation_fields(self) -> None:
        """StockPerformance has all valuation ratio fields."""
        perf = StockPerformance()
        for field in ["pe_ratio", "forward_pe", "ev_ebitda", "peg_ratio"]:
            assert hasattr(perf, field), f"Missing field: {field}"
            assert getattr(perf, field) is None

    def test_analyst_count_field(self) -> None:
        """AnalystSentimentProfile has analyst_count field."""
        profile = AnalystSentimentProfile()
        assert hasattr(profile, "analyst_count")
        assert profile.analyst_count is None

    def test_gics_code_field(self) -> None:
        """CompanyProfile has gics_code field."""
        from do_uw.models.company import CompanyIdentity, CompanyProfile

        identity = CompanyIdentity(ticker="TEST")
        profile = CompanyProfile(identity=identity)
        assert hasattr(profile, "gics_code")
        assert profile.gics_code is None
