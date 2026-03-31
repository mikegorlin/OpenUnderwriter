"""Tests for hazard dimension scoring (47 dimensions across 7 categories).

Covers representative dimensions from every category, proxy/missing data
handling, data mapping, and the score_all_dimensions dispatcher.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import ExtractedData, RiskFactorProfile
from do_uw.stages.analyze.layers.hazard.data_mapping import map_dimension_data
from do_uw.stages.analyze.layers.hazard.dimension_h1_business import score_h1_dimension
from do_uw.stages.analyze.layers.hazard.dimension_h2_people import score_h2_dimension
from do_uw.stages.analyze.layers.hazard.dimension_h3_financial import score_h3_dimension
from do_uw.stages.analyze.layers.hazard.dimension_h4_governance import score_h4_dimension
from do_uw.stages.analyze.layers.hazard.dimension_h5_maturity import score_h5_dimension
from do_uw.stages.analyze.layers.hazard.dimension_h6_environment import score_h6_dimension
from do_uw.stages.analyze.layers.hazard.dimension_h7_emerging import score_h7_dimension
from do_uw.stages.analyze.layers.hazard.dimension_scoring import (
    score_all_dimensions,
    score_single_dimension,
)


# ---------------------------------------------------------------------------
# Fixtures: mock company + extracted data
# ---------------------------------------------------------------------------


def _mock_company(
    sector: str = "TECH",
    sic_code: str = "7372",
    years_public: int = 5,
    exchange: str = "NASDAQ",
    is_fpi: bool = False,
    state: str = "DE",
) -> CompanyProfile:
    """Build a minimal CompanyProfile for testing."""
    identity = CompanyIdentity(ticker="TEST")
    # Use MagicMock for SourcedValue fields
    identity.sector = MagicMock(value=sector)
    identity.sic_code = MagicMock(value=sic_code)
    identity.exchange = MagicMock(value=exchange)
    identity.state_of_incorporation = MagicMock(value=state)
    identity.is_fpi = is_fpi

    co = CompanyProfile(identity=identity)
    co.years_public = MagicMock(value=years_public)
    return co


def _mock_extracted(
    risk_factors: list[RiskFactorProfile] | None = None,
) -> ExtractedData:
    """Build a minimal ExtractedData for testing."""
    ext = ExtractedData()
    if risk_factors:
        ext.risk_factors = risk_factors
    return ext


def _dim_cfg(max_score: float = 5.0, **kwargs: Any) -> dict[str, Any]:
    """Build a minimal dimension config dict."""
    cfg: dict[str, Any] = {"max_score": max_score, "name": "Test", "weight": 1.0}
    cfg.update(kwargs)
    return cfg


# ---------------------------------------------------------------------------
# H1: Business & Operating Model tests
# ---------------------------------------------------------------------------


class TestH1IndustrySector:
    """H1-01: Industry sector risk tier scoring."""

    @pytest.mark.parametrize(
        "sector,expected_min,expected_max",
        [
            ("TECH", 6.0, 8.0),
            ("BIOT", 8.0, 10.0),
            ("UTIL", 1.0, 2.0),
        ],
    )
    def test_sector_risk_tiers(
        self, sector: str, expected_min: float, expected_max: float
    ) -> None:
        data = {"sector": sector, "sic_code": "1234", "_data_tier": "primary"}
        raw, sources, evidence = score_h1_dimension("H1-01", _dim_cfg(10), data)
        assert expected_min <= raw <= expected_max
        assert evidence

    def test_unknown_sector_gets_moderate(self) -> None:
        data = {"sector": "UNKNOWN_SECTOR", "_data_tier": "primary"}
        raw, _, evidence = score_h1_dimension("H1-01", _dim_cfg(10), data)
        assert 3.0 <= raw <= 5.0  # Moderate default


class TestH1Growth:
    """H1-09: Speed of growth scoring."""

    @pytest.mark.parametrize(
        "yoy,expected_min,expected_max",
        [
            (5.0, 0.0, 1.5),    # LOW
            (25.0, 2.0, 3.5),   # MODERATE
            (50.0, 4.0, 5.0),   # VERY HIGH
        ],
    )
    def test_growth_tiers(
        self, yoy: float, expected_min: float, expected_max: float
    ) -> None:
        data = {"yoy_growth": yoy, "revenue_current": 1e9, "_data_tier": "primary"}
        raw, sources, evidence = score_h1_dimension("H1-09", _dim_cfg(5), data)
        assert expected_min <= raw <= expected_max

    def test_negative_growth_has_risk(self) -> None:
        data = {"yoy_growth": -15.0, "_data_tier": "primary"}
        raw, _, evidence = score_h1_dimension("H1-09", _dim_cfg(5), data)
        assert raw > 0  # Negative growth still has restructuring risk


# ---------------------------------------------------------------------------
# H2: People & Management tests
# ---------------------------------------------------------------------------


class TestH2ManagementExperience:
    """H2-01: Management experience scoring."""

    def test_experienced_ceo(self) -> None:
        data = {
            "executives": [
                {"title": "CEO", "tenure_years": 12.0, "bio": "Veteran executive"},
                {"title": "CFO", "tenure_years": 8.0, "bio": "Experienced CFO"},
            ],
            "avg_tenure": 10.0,
            "_data_tier": "primary",
        }
        raw, sources, evidence = score_h2_dimension("H2-01", _dim_cfg(5), data)
        assert raw <= 3.0  # Experienced team = lower risk

    def test_first_time_ceo(self) -> None:
        data = {
            "executives": [
                {
                    "title": "Chief Executive Officer",
                    "tenure_years": 1.0,
                    "bio": "First time leading a public company",
                },
            ],
            "avg_tenure": 1.0,
            "_data_tier": "primary",
        }
        raw, _, evidence = score_h2_dimension("H2-01", _dim_cfg(5), data)
        assert raw >= 3.0  # First-time + short tenure = high risk
        assert any("first" in e.lower() for e in evidence)


# ---------------------------------------------------------------------------
# H3: Financial Structure tests
# ---------------------------------------------------------------------------


class TestH3Leverage:
    """H3-01: Leverage scoring."""

    def test_low_leverage(self) -> None:
        data = {"debt_to_equity": 0.3, "_data_tier": "primary"}
        raw, _, evidence = score_h3_dimension("H3-01", _dim_cfg(5), data)
        assert raw <= 1.5

    def test_high_leverage(self) -> None:
        data = {"debt_to_equity": 4.0, "_data_tier": "primary"}
        raw, _, evidence = score_h3_dimension("H3-01", _dim_cfg(5), data)
        assert raw >= 2.5
        assert any("HIGH" in e for e in evidence)

    def test_negative_equity(self) -> None:
        data = {"debt_to_equity": -2.0, "_data_tier": "primary"}
        raw, _, evidence = score_h3_dimension("H3-01", _dim_cfg(5), data)
        assert raw >= 3.0  # Negative equity = very high risk


# ---------------------------------------------------------------------------
# H4: Governance Structure tests
# ---------------------------------------------------------------------------


class TestH4CEOChair:
    """H4-01: CEO/Chair combined scoring."""

    def test_combined_true(self) -> None:
        data = {"ceo_chair_combined": True, "_data_tier": "primary"}
        raw, _, evidence = score_h4_dimension("H4-01", _dim_cfg(2), data)
        assert raw == 2.0
        assert any("combined" in e.lower() for e in evidence)

    def test_combined_false(self) -> None:
        data = {"ceo_chair_combined": False, "_data_tier": "primary"}
        raw, _, evidence = score_h4_dimension("H4-01", _dim_cfg(2), data)
        assert raw == 0.0


# ---------------------------------------------------------------------------
# H5: Public Company Maturity tests
# ---------------------------------------------------------------------------


class TestH5IPORecency:
    """H5-01: IPO recency scoring."""

    @pytest.mark.parametrize(
        "years,expected_min,expected_max",
        [
            (1, 4.0, 5.0),    # Within 3-year cliff
            (4, 2.0, 3.0),    # Transitioning
            (10, 0.0, 1.5),   # Seasoned
        ],
    )
    def test_ipo_age_tiers(
        self, years: int, expected_min: float, expected_max: float
    ) -> None:
        data = {"years_public": years, "_data_tier": "primary"}
        raw, _, evidence = score_h5_dimension("H5-01", _dim_cfg(5), data)
        assert expected_min <= raw <= expected_max


# ---------------------------------------------------------------------------
# H6: External Environment tests
# ---------------------------------------------------------------------------


class TestH6RegulatorySpotlight:
    """H6-02: Industry regulatory spotlight scoring."""

    def test_biot_high_spotlight(self) -> None:
        data = {"sector": "BIOT", "sic_code": "2836", "_data_tier": "primary"}
        raw, _, evidence = score_h6_dimension("H6-02", _dim_cfg(3), data)
        assert raw >= 1.5

    def test_util_lower_spotlight(self) -> None:
        data = {"sector": "UTIL", "_data_tier": "primary"}
        raw, _, evidence = score_h6_dimension("H6-02", _dim_cfg(3), data)
        assert raw <= 1.5


# ---------------------------------------------------------------------------
# H7: Emerging / Modern Hazards tests
# ---------------------------------------------------------------------------


class TestH7AI:
    """H7-01: AI adoption/governance scoring."""

    def test_high_ai_score(self) -> None:
        data = {
            "ai_score": 75.0,
            "disclosure_data": {"mention_count": 30, "sentiment": "THREAT"},
            "_data_tier": "primary",
        }
        raw, _, evidence = score_h7_dimension("H7-01", _dim_cfg(3), data)
        assert raw >= 2.0
        assert any("HIGH" in e for e in evidence)

    def test_low_ai_score(self) -> None:
        data = {
            "ai_score": 20.0,
            "disclosure_data": {"mention_count": 2, "sentiment": "BALANCED"},
            "_data_tier": "primary",
        }
        raw, _, evidence = score_h7_dimension("H7-01", _dim_cfg(3), data)
        assert raw <= 1.5


# ---------------------------------------------------------------------------
# Missing data handling tests
# ---------------------------------------------------------------------------


class TestMissingData:
    """Test that empty data -> neutral score with data_available=False."""

    def test_empty_data_returns_neutral(self) -> None:
        result = score_single_dimension(
            "H1-01",
            {"name": "Test", "max_score": 10, "weight": 1.0},
            {},
        )
        assert result["data_available"] is False
        assert result["data_tier"] == "unavailable"
        assert result["normalized_score"] == 35.0  # Default neutral (MODERATE)
        assert any("no data" in e.lower() or "baseline" in e.lower() for e in result["evidence"])

    def test_empty_data_all_categories(self) -> None:
        """Every category should handle empty data gracefully."""
        for dim_id in ["H1-01", "H2-01", "H3-01", "H4-01", "H5-01", "H6-01", "H7-01"]:
            result = score_single_dimension(
                dim_id,
                {"name": "Test", "max_score": 5, "weight": 1.0},
                {},
            )
            assert result["data_available"] is False
            assert 0 <= result["normalized_score"] <= 100


# ---------------------------------------------------------------------------
# Proxy data handling tests
# ---------------------------------------------------------------------------


class TestProxyData:
    """Test that proxy data -> data_available=True with proxy evidence."""

    def test_proxy_tier_marked_in_evidence(self) -> None:
        data = {
            "keyword_hits": ["CYBER: Data breach risk"],
            "_data_tier": "proxy",
        }
        result = score_single_dimension(
            "H7-02",
            {"name": "Cybersecurity", "max_score": 3, "weight": 1.0},
            data,
        )
        assert result["data_available"] is True
        assert result["data_tier"] == "proxy"
        assert any("proxy" in e.lower() for e in result["evidence"])

    def test_proxy_still_produces_valid_score(self) -> None:
        data = {
            "keyword_hits": ["ESG: Climate risk"],
            "sector": "ENGY",
            "_data_tier": "proxy",
        }
        result = score_single_dimension(
            "H7-03",
            {"name": "ESG", "max_score": 3, "weight": 1.0},
            data,
        )
        assert result["data_available"] is True
        assert 0 <= result["raw_score"] <= 3
        assert result["normalized_score"] > 0


# ---------------------------------------------------------------------------
# Data mapping tests
# ---------------------------------------------------------------------------


class TestDataMapping:
    """Test map_dimension_data() returns correct structure."""

    def test_known_dimension_returns_data_tier(self) -> None:
        co = _mock_company(sector="TECH")
        ext = _mock_extracted()
        result = map_dimension_data("H1-01", ext, co, {})
        assert "_data_tier" in result
        assert result["_data_tier"] == "primary"

    def test_unknown_dimension_returns_empty(self) -> None:
        co = _mock_company()
        ext = _mock_extracted()
        result = map_dimension_data("H99-99", ext, co, {})
        assert result == {}

    def test_h5_04_always_returns_data(self) -> None:
        """H5-04 FPI status always has data (boolean default)."""
        co = _mock_company(is_fpi=False)
        ext = _mock_extracted()
        result = map_dimension_data("H5-04", ext, co, {})
        assert result["_data_tier"] == "primary"
        assert result["is_fpi"] is False

    def test_proxy_from_risk_factors(self) -> None:
        """Dimension with risk factor proxy returns proxy tier."""
        rf = RiskFactorProfile(
            title="Platform dependency risk",
            category="TECHNOLOGY",
            source_passage="We depend on the Apple App Store platform for distribution",
        )
        co = _mock_company()
        ext = _mock_extracted(risk_factors=[rf])
        result = map_dimension_data("H1-12", ext, co, {})
        assert result.get("_data_tier") == "proxy"
        assert result.get("keyword_hits")


# ---------------------------------------------------------------------------
# score_all_dimensions integration test
# ---------------------------------------------------------------------------


class TestScoreAllDimensions:
    """Test score_all_dimensions() returns 47 dimension scores."""

    def test_returns_all_dimension_scores(self) -> None:
        """With full dimension config, returns one score per dimension."""
        co = _mock_company()
        ext = _mock_extracted()

        # Build config with all dimensions: H1=13, H2=8, H3=8, H4=8, H5=5, H6=7, H7=6 = 55
        dimensions: dict[str, dict[str, Any]] = {}
        h_counts = {"H1": 13, "H2": 8, "H3": 8, "H4": 8, "H5": 5, "H6": 7, "H7": 6}
        expected_total = sum(h_counts.values())  # 55
        for cat, count in h_counts.items():
            for i in range(1, count + 1):
                dim_id = f"{cat}-{i:02d}"
                dimensions[dim_id] = {
                    "name": f"Dimension {dim_id}",
                    "max_score": 5.0,
                    "weight": 1.0,
                }
        config = {"dimensions": dimensions}

        results = score_all_dimensions(ext, co, config)
        assert len(results) == expected_total

        # Every result should have required keys
        for r in results:
            assert "dimension_id" in r
            assert "raw_score" in r
            assert "normalized_score" in r
            assert "data_available" in r
            assert "evidence" in r
            assert 0 <= r["normalized_score"] <= 100

    def test_returns_empty_for_empty_config(self) -> None:
        co = _mock_company()
        ext = _mock_extracted()
        results = score_all_dimensions(ext, co, {"dimensions": {}})
        assert results == []

    def test_scores_ordered_by_dimension_id(self) -> None:
        co = _mock_company()
        ext = _mock_extracted()
        dimensions = {
            "H3-01": {"name": "Leverage", "max_score": 5, "weight": 1.0},
            "H1-01": {"name": "Industry", "max_score": 10, "weight": 1.0},
            "H2-01": {"name": "Experience", "max_score": 5, "weight": 1.0},
        }
        results = score_all_dimensions(ext, co, {"dimensions": dimensions})
        ids = [r["dimension_id"] for r in results]
        assert ids == sorted(ids)


# ---------------------------------------------------------------------------
# Normalization tests
# ---------------------------------------------------------------------------


class TestNormalization:
    """Test that scores are properly normalized to 0-100."""

    def test_max_score_normalizes_to_100(self) -> None:
        """A raw score at max should normalize to 100."""
        data = {"ceo_chair_combined": True, "_data_tier": "primary"}
        result = score_single_dimension(
            "H4-01",
            {"name": "CEO/Chair", "max_score": 2, "weight": 1.0},
            data,
        )
        assert result["raw_score"] == 2.0
        assert result["normalized_score"] == 100.0

    def test_zero_score_normalizes_to_zero(self) -> None:
        data = {"ceo_chair_combined": False, "_data_tier": "primary"}
        result = score_single_dimension(
            "H4-01",
            {"name": "CEO/Chair", "max_score": 2, "weight": 1.0},
            data,
        )
        assert result["raw_score"] == 0.0
        assert result["normalized_score"] == 0.0

    def test_score_clamped_to_max(self) -> None:
        """Even if scorer returns above max, it should be clamped."""
        # H3-01 with extreme leverage
        data = {"debt_to_equity": 10.0, "debt_to_ebitda": 20.0, "_data_tier": "primary"}
        result = score_single_dimension(
            "H3-01",
            {"name": "Leverage", "max_score": 5, "weight": 1.0},
            data,
        )
        assert result["raw_score"] <= 5.0
        assert result["normalized_score"] <= 100.0
