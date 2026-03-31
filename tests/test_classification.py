"""Tests for the classification engine (Layer 1).

Tests cover:
- Market cap tier determination (all 5 tiers + None)
- IPO age multiplier (3-year cliff model)
- Sector rate lookup (known and unknown codes)
- End-to-end classify_company for realistic scenarios
- Severity band computation
- Edge cases (None market_cap, unknown sector, 0 years public)
- DDL exposure computation

All tests use the real classification.json config loaded via fixture.
"""

from __future__ import annotations

import pytest

from do_uw.models.classification import ClassificationResult, MarketCapTier
from do_uw.stages.analyze.layers.classify.classification_engine import (
    _compute_ddl_base,
    _determine_cap_tier,
    _get_sector_rate,
    _ipo_age_multiplier,
    classify_company,
    load_classification_config,
)
from do_uw.stages.analyze.layers.classify.severity_bands import compute_severity_band


@pytest.fixture()
def config() -> dict:
    """Load real classification.json config."""
    return load_classification_config()


@pytest.fixture()
def tiers_config(config: dict) -> list:
    """Extract market_cap_tiers from config."""
    return config["market_cap_tiers"]


@pytest.fixture()
def sector_rates(config: dict) -> dict:
    """Extract sector_rates from config."""
    return config["sector_rates"]


@pytest.fixture()
def ipo_config(config: dict) -> dict:
    """Extract ipo_age_decay from config."""
    return config["ipo_age_decay"]


# -----------------------------------------------------------------------
# _determine_cap_tier tests
# -----------------------------------------------------------------------


class TestDetermineCapTier:
    """Tests for market cap tier determination."""

    def test_mega_cap(self, tiers_config: list) -> None:
        tier, mult = _determine_cap_tier(500_000_000_000, tiers_config)
        assert tier == MarketCapTier.MEGA
        assert mult == 1.8

    def test_large_cap(self, tiers_config: list) -> None:
        tier, mult = _determine_cap_tier(50_000_000_000, tiers_config)
        assert tier == MarketCapTier.LARGE
        assert mult == 1.3

    def test_mid_cap(self, tiers_config: list) -> None:
        tier, mult = _determine_cap_tier(5_000_000_000, tiers_config)
        assert tier == MarketCapTier.MID
        assert mult == 1.0

    def test_small_cap(self, tiers_config: list) -> None:
        tier, mult = _determine_cap_tier(1_000_000_000, tiers_config)
        assert tier == MarketCapTier.SMALL
        assert mult == 0.7

    def test_micro_cap(self, tiers_config: list) -> None:
        tier, mult = _determine_cap_tier(100_000_000, tiers_config)
        assert tier == MarketCapTier.MICRO
        assert mult == 0.5

    def test_none_market_cap_defaults_mid(self, tiers_config: list) -> None:
        tier, mult = _determine_cap_tier(None, tiers_config)
        assert tier == MarketCapTier.MID
        assert mult == 1.0

    def test_boundary_mega(self, tiers_config: list) -> None:
        """Exactly $200B should be MEGA."""
        tier, _ = _determine_cap_tier(200_000_000_000, tiers_config)
        assert tier == MarketCapTier.MEGA

    def test_boundary_just_below_mega(self, tiers_config: list) -> None:
        """$199.9B should be LARGE."""
        tier, _ = _determine_cap_tier(199_999_999_999, tiers_config)
        assert tier == MarketCapTier.LARGE

    def test_boundary_micro_at_zero(self, tiers_config: list) -> None:
        """$0 market cap should still be MICRO."""
        tier, _ = _determine_cap_tier(0, tiers_config)
        assert tier == MarketCapTier.MICRO


# -----------------------------------------------------------------------
# _ipo_age_multiplier tests
# -----------------------------------------------------------------------


class TestIPOAgeMultiplier:
    """Tests for IPO age cliff model."""

    def test_year_0(self, ipo_config: dict) -> None:
        assert _ipo_age_multiplier(0, ipo_config) == 2.8

    def test_year_2(self, ipo_config: dict) -> None:
        assert _ipo_age_multiplier(2, ipo_config) == 2.8

    def test_year_3_is_cliff(self, ipo_config: dict) -> None:
        """Year 3 is still within cliff period (inclusive)."""
        assert _ipo_age_multiplier(3, ipo_config) == 2.8

    def test_year_4_transition(self, ipo_config: dict) -> None:
        """Year 4 transitions to transition multiplier."""
        assert _ipo_age_multiplier(4, ipo_config) == 1.5

    def test_year_5_transition(self, ipo_config: dict) -> None:
        """Year 5 is still in transition period (inclusive)."""
        assert _ipo_age_multiplier(5, ipo_config) == 1.5

    def test_year_6_seasoned(self, ipo_config: dict) -> None:
        """Year 6 reaches seasoned multiplier."""
        assert _ipo_age_multiplier(6, ipo_config) == 1.0

    def test_year_20_seasoned(self, ipo_config: dict) -> None:
        assert _ipo_age_multiplier(20, ipo_config) == 1.0

    def test_none_years_public(self, ipo_config: dict) -> None:
        """None = unknown, assume seasoned."""
        assert _ipo_age_multiplier(None, ipo_config) == 1.0


# -----------------------------------------------------------------------
# _get_sector_rate tests
# -----------------------------------------------------------------------


class TestGetSectorRate:
    """Tests for sector rate lookup."""

    def test_known_sector_tech(self, sector_rates: dict) -> None:
        rate, code = _get_sector_rate("TECH", sector_rates)
        assert rate == 5.0
        assert code == "TECH"

    def test_known_sector_biot(self, sector_rates: dict) -> None:
        rate, _ = _get_sector_rate("BIOT", sector_rates)
        assert rate == 7.0

    def test_known_sector_util(self, sector_rates: dict) -> None:
        rate, _ = _get_sector_rate("UTIL", sector_rates)
        assert rate == 1.5

    def test_unknown_sector_uses_default(self, sector_rates: dict) -> None:
        rate, code = _get_sector_rate("ZZZZ", sector_rates)
        assert rate == 3.5
        assert code == "DEFAULT"


# -----------------------------------------------------------------------
# Severity band tests
# -----------------------------------------------------------------------


class TestSeverityBands:
    """Tests for severity band computation."""

    def test_mega_cap_band(self, tiers_config: list) -> None:
        low, high = compute_severity_band(500_000_000_000, tiers_config)
        assert low == 150
        assert high == 500

    def test_large_cap_band(self, tiers_config: list) -> None:
        low, high = compute_severity_band(50_000_000_000, tiers_config)
        assert low == 40
        assert high == 150

    def test_mid_cap_band(self, tiers_config: list) -> None:
        low, high = compute_severity_band(5_000_000_000, tiers_config)
        assert low == 15
        assert high == 40

    def test_small_cap_band(self, tiers_config: list) -> None:
        low, high = compute_severity_band(1_000_000_000, tiers_config)
        assert low == 5
        assert high == 15

    def test_micro_cap_band(self, tiers_config: list) -> None:
        low, high = compute_severity_band(100_000_000, tiers_config)
        assert low == 2
        assert high == 5

    def test_none_cap_defaults_mid(self, tiers_config: list) -> None:
        low, high = compute_severity_band(None, tiers_config)
        assert low == 15.0
        assert high == 40.0


# -----------------------------------------------------------------------
# DDL base computation tests
# -----------------------------------------------------------------------


class TestDDLBase:
    """Tests for DDL exposure computation."""

    def test_standard_ddl(self) -> None:
        # $50B market cap, 15% drop = $7.5B = 7500M
        ddl = _compute_ddl_base(50_000_000_000, 15)
        assert ddl == 7500.0

    def test_none_market_cap(self) -> None:
        assert _compute_ddl_base(None, 15) == 0.0

    def test_zero_drop(self) -> None:
        assert _compute_ddl_base(50_000_000_000, 0) == 0.0


# -----------------------------------------------------------------------
# End-to-end classify_company tests
# -----------------------------------------------------------------------


class TestClassifyCompany:
    """Integration tests for classify_company."""

    def test_aapl_like_mega_tech_seasoned(self, config: dict) -> None:
        """AAPL-like: mega cap TECH, 40 years public."""
        result = classify_company(
            market_cap=3_000_000_000_000,  # $3T
            sector_code="TECH",
            years_public=40,
            config=config,
        )
        assert isinstance(result, ClassificationResult)
        assert result.market_cap_tier == MarketCapTier.MEGA
        assert result.ipo_multiplier == 1.0
        # TECH base=5.0 * MEGA mult=1.8 * seasoned=1.0 = 9.0%
        assert 5.0 <= result.base_filing_rate_pct <= 10.0
        assert result.severity_band_low_m == 150
        assert result.severity_band_high_m == 500

    def test_smci_like_mid_tech_seasoned(self, config: dict) -> None:
        """SMCI-like: mid cap TECH, 15 years public."""
        result = classify_company(
            market_cap=5_000_000_000,  # $5B
            sector_code="TECH",
            years_public=15,
            config=config,
        )
        assert result.market_cap_tier == MarketCapTier.MID
        assert result.ipo_multiplier == 1.0
        # TECH base=5.0 * MID mult=1.0 * seasoned=1.0 = 5.0%
        assert result.base_filing_rate_pct == 5.0

    def test_pre_ipo_biotech(self, config: dict) -> None:
        """Pre-IPO biotech: small cap BIOT, 1 year public."""
        result = classify_company(
            market_cap=800_000_000,  # $800M
            sector_code="BIOT",
            years_public=1,
            config=config,
        )
        assert result.market_cap_tier == MarketCapTier.SMALL
        assert result.ipo_multiplier == 2.8
        # BIOT base=7.0 * SMALL mult=0.7 * cliff=2.8 = 13.72%
        assert result.base_filing_rate_pct > 10.0

    def test_utility_company(self, config: dict) -> None:
        """Stable utility: large cap, 50 years public."""
        result = classify_company(
            market_cap=30_000_000_000,  # $30B
            sector_code="UTIL",
            years_public=50,
            config=config,
        )
        assert result.market_cap_tier == MarketCapTier.LARGE
        # UTIL base=1.5 * LARGE mult=1.3 * seasoned=1.0 = 1.95%
        assert result.base_filing_rate_pct < 3.0

    def test_none_market_cap(self, config: dict) -> None:
        """Unknown market cap defaults to MID tier."""
        result = classify_company(
            market_cap=None,
            sector_code="TECH",
            years_public=10,
            config=config,
        )
        assert result.market_cap_tier == MarketCapTier.MID
        assert result.cap_filing_multiplier == 1.0

    def test_unknown_sector(self, config: dict) -> None:
        """Unknown sector falls back to DEFAULT rate."""
        result = classify_company(
            market_cap=5_000_000_000,
            sector_code="UNKNOWN",
            years_public=10,
            config=config,
        )
        # DEFAULT rate = 3.5
        assert result.base_filing_rate_pct == 3.5

    def test_zero_years_public(self, config: dict) -> None:
        """Year 0 = IPO year, should get cliff multiplier."""
        result = classify_company(
            market_cap=5_000_000_000,
            sector_code="TECH",
            years_public=0,
            config=config,
        )
        assert result.ipo_multiplier == 2.8
        # TECH 5.0 * MID 1.0 * cliff 2.8 = 14.0
        assert result.base_filing_rate_pct == 14.0

    def test_filing_rate_capped_at_25(self, config: dict) -> None:
        """Filing rate should never exceed 25% sanity ceiling."""
        result = classify_company(
            market_cap=500_000_000_000,  # Mega
            sector_code="BIOT",  # Highest sector rate (7.0)
            years_public=0,  # Cliff multiplier (2.8)
            config=config,
        )
        # BIOT 7.0 * MEGA 1.8 * cliff 2.8 = 35.28 -> capped at 25
        assert result.base_filing_rate_pct == 25.0

    def test_methodology_field(self, config: dict) -> None:
        """Check methodology is set correctly."""
        result = classify_company(
            market_cap=5_000_000_000,
            sector_code="TECH",
            years_public=10,
            config=config,
        )
        assert result.methodology == "classification_v1"

    def test_ddl_exposure_populated(self, config: dict) -> None:
        """DDL exposure should be computed from market cap."""
        result = classify_company(
            market_cap=50_000_000_000,
            sector_code="TECH",
            years_public=10,
            config=config,
        )
        # $50B * 15% = $7.5B = 7500M
        assert result.ddl_exposure_base_m == 7500.0

    def test_config_loads_successfully(self) -> None:
        """Verify load_classification_config returns valid config."""
        config = load_classification_config()
        assert "market_cap_tiers" in config
        assert "sector_rates" in config
        assert "ipo_age_decay" in config
        assert len(config["market_cap_tiers"]) == 5
        assert len(config["sector_rates"]) == 12
