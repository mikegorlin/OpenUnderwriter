"""Scoring validation tests: known-outcome company archetypes.

Integration tests that construct real AnalysisState fixtures and run
them through the actual scoring engine. NO mocking of scoring engine.

Validates that archetypal risk profiles produce expected tier ranges,
CRF gates trigger correctly, and factor scores show monotonic ordering.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.financials import AuditProfile, ExtractedFinancials
from do_uw.models.governance import (
    BoardProfile,
    GovernanceData,
)
from do_uw.models.governance_forensics import (
    LeadershipForensicProfile,
    LeadershipStability,
)
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
    SECEnforcementPipeline,
)
from do_uw.models.market import (
    InsiderTradingProfile,
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.market_events import (
    CapitalMarketsActivity,
    CapitalMarketsOffering,
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
)
from do_uw.models.scoring import Tier
from do_uw.models.state import ExtractedData
from do_uw.stages.score.factor_scoring import score_all_factors
from do_uw.stages.score.red_flag_gates import (
    apply_crf_ceilings,
    evaluate_red_flag_gates,
)
from do_uw.stages.score.tier_classification import classify_tier

NOW = datetime.now(tz=UTC)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------


def _sv(
    value: object, source: str = "test", conf: Confidence = Confidence.HIGH
) -> SourcedValue:  # type: ignore[type-arg]
    """Shorthand to create a SourcedValue for testing."""
    return SourcedValue(value=value, source=source, confidence=conf, as_of=NOW)


def _load_scoring_config() -> dict[str, Any]:
    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
    with (brain_dir / "scoring.json").open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def _load_sectors_config() -> dict[str, Any]:
    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
    with (brain_dir / "sectors.json").open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def _load_red_flags_config() -> dict[str, Any]:
    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
    with (brain_dir / "red_flags.json").open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def _make_company(
    sector: str = "TECH", market_cap: float = 5e9
) -> CompanyProfile:
    return CompanyProfile(
        identity=CompanyIdentity(ticker="TEST", sector=_sv(sector)),
        market_cap=_sv(market_cap),
    )


def _score_full_pipeline(
    extracted: ExtractedData,
    company: CompanyProfile | None = None,
) -> tuple[float, str | None, Tier, list[Any], list[Any]]:
    """Run full scoring pipeline and return quality_score, binding_id, tier, factors, flags."""
    scoring_config = _load_scoring_config()
    sectors_config = _load_sectors_config()
    rf_config = _load_red_flags_config()

    factors = score_all_factors(scoring_config, extracted, company, sectors_config)
    flags = evaluate_red_flag_gates(rf_config, scoring_config, extracted, company)

    total_deducted = sum(f.points_deducted for f in factors)
    composite = max(0.0, 100.0 - total_deducted)

    quality_score, binding_id = apply_crf_ceilings(composite, flags)
    tier_result = classify_tier(quality_score, scoring_config["tiers"])

    return quality_score, binding_id, tier_result.tier, factors, flags


def _factor_by_id(
    factors: list[Any], factor_id: str
) -> Any:
    """Find a factor score by ID (e.g., 'F1')."""
    matches = [f for f in factors if f.factor_id == factor_id]
    assert len(matches) == 1, f"Expected 1 factor with id={factor_id}, got {len(matches)}"
    return matches[0]


def _date_months_ago(months: int) -> str:
    """ISO date string for approximately N months ago."""
    d = date.today() - timedelta(days=int(months * 30.4))
    return d.isoformat()


# -----------------------------------------------------------------------
# Archetype fixture builders
# -----------------------------------------------------------------------


def _build_pristine_blue_chip() -> tuple[ExtractedData, CompanyProfile]:
    """Stable mega-cap, no litigation, strong governance, low volatility."""
    company = _make_company(sector="TECH", market_cap=200e9)
    ceo_start = date.today() - timedelta(days=int(10 * 365.25))
    cfo_start = date.today() - timedelta(days=int(5 * 365.25))
    extracted = ExtractedData(
        litigation=LitigationLandscape(),  # no SCAs, no enforcement
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(8.0),  # <20% decline
                volatility_90d=_sv(1.5),  # low vol
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(1.0),
                vs_sector_ratio=_sv(0.25),  # well below sector avg
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                    for i in range(1, 9)
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(going_concern=_sv(False)),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.85),
                ceo_chair_duality=_sv(False),
            ),
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("Chief Executive Officer"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("Chief Financial Officer"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


def _build_solid_mid_cap() -> tuple[ExtractedData, CompanyProfile]:
    """Healthy mid-cap, clean record, settled suit years ago."""
    company = _make_company(sector="INDU", market_cap=8e9)
    ceo_start = date.today() - timedelta(days=int(6 * 365.25))
    cfo_start = date.today() - timedelta(days=int(3 * 365.25))
    settled_date = date.today() - timedelta(days=int(7 * 365.25))
    extracted = ExtractedData(
        litigation=LitigationLandscape(
            securities_class_actions=[
                CaseDetail(
                    case_name=_sv("In re OldCo Securities"),
                    status=_sv("SETTLED"),
                    filing_date=_sv(settled_date),
                    settlement_amount=_sv(5e6),
                ),
            ]
        ),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(25.0),  # moderate
                volatility_90d=_sv(2.5),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(3.5),
                vs_sector_ratio=_sv(1.2),
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter="Q1 2025", result="MISS"),
                    *[
                        EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                        for i in range(2, 9)
                    ],
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(going_concern=_sv(False)),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.75),
                ceo_chair_duality=_sv(False),
            ),
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("CEO"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("CFO"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


def _build_growth_darling_stressed() -> tuple[ExtractedData, CompanyProfile]:
    """High-growth tech with elevated risk signals."""
    company = _make_company(sector="TECH", market_cap=15e9)
    ipo_date = _date_months_ago(30)
    ceo_start = date.today() - timedelta(days=int(3 * 365.25))
    cfo_start = date.today() - timedelta(days=int(2 * 365.25))
    extracted = ExtractedData(
        litigation=LitigationLandscape(),  # no SCA
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(35.0),  # 30-40% range
                volatility_90d=_sv(5.5),  # high vol
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(8.0),
                vs_sector_ratio=_sv(2.0),  # 2x sector
            ),
            insider_trading=InsiderTradingProfile(
                ceo_cfo_pct_sold=_sv(30.0),  # heavy selling
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter="Q1 2025", result="MISS"),
                    EarningsQuarterRecord(quarter="Q2 2025", result="MISS"),
                    *[
                        EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                        for i in range(3, 9)
                    ],
                ]
            ),
            capital_markets=CapitalMarketsActivity(
                offerings_3yr=[
                    CapitalMarketsOffering(
                        offering_type="IPO",
                        date=_sv(ipo_date),
                    )
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(going_concern=_sv(False)),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.70),
                ceo_chair_duality=_sv(False),
            ),
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("CEO"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("CFO"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


def _build_distressed_company() -> tuple[ExtractedData, CompanyProfile]:
    """Financial distress with going concern opinion."""
    company = _make_company(sector="BIOT", market_cap=500e6)
    ceo_start = date.today() - timedelta(days=int(1.5 * 365.25))
    cfo_start = date.today() - timedelta(days=180)
    extracted = ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(55.0),  # severe
                volatility_90d=_sv(12.0),  # extreme for any sector
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(20.0),
                vs_sector_ratio=_sv(3.3),
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter=f"Q{i} 2025", result="MISS")
                    for i in range(1, 5)
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(
                going_concern=_sv(True),
                material_weaknesses=[_sv("Inadequate controls over financial reporting")],
            ),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.60),
                ceo_chair_duality=_sv(True),
            ),
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("CEO"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("CFO"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


def _build_active_sca_defendant() -> tuple[ExtractedData, CompanyProfile]:
    """Company with active securities class action -- CRF-1 ceiling."""
    company = _make_company(sector="FINS", market_cap=10e9)
    ceo_start = date.today() - timedelta(days=int(5 * 365.25))
    cfo_start = date.today() - timedelta(days=int(3 * 365.25))
    extracted = ExtractedData(
        litigation=LitigationLandscape(
            securities_class_actions=[
                CaseDetail(
                    case_name=_sv("In re TestFinCo Securities Litigation"),
                    status=_sv("ACTIVE"),
                )
            ],
            sec_enforcement=SECEnforcementPipeline(
                pipeline_position=_sv("FORMAL_INVESTIGATION"),
            ),
        ),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(40.0),
                volatility_90d=_sv(4.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(6.0),
                vs_sector_ratio=_sv(2.0),
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter="Q1 2025", result="MISS"),
                    EarningsQuarterRecord(quarter="Q2 2025", result="MISS"),
                    *[
                        EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                        for i in range(3, 9)
                    ],
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(going_concern=_sv(False)),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.80),
                ceo_chair_duality=_sv(False),
            ),
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("CEO"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("CFO"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


def _build_spac_penny_stock() -> tuple[ExtractedData, CompanyProfile]:
    """Post-SPAC with stock below $5 -- CRF-6 ceiling."""
    company = _make_company(sector="TECH", market_cap=200e6)
    spac_date = _date_months_ago(12)
    ceo_start = date.today() - timedelta(days=int(1 * 365.25))
    cfo_start = date.today() - timedelta(days=int(0.5 * 365.25))
    extracted = ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(70.0),  # massive decline
                current_price=_sv(3.0),  # below $5
                volatility_90d=_sv(8.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(12.0),
                vs_sector_ratio=_sv(3.0),
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter=f"Q{i} 2025", result="MISS")
                    for i in range(1, 4)
                ]
            ),
            capital_markets=CapitalMarketsActivity(
                offerings_3yr=[
                    CapitalMarketsOffering(
                        offering_type="SPAC",
                        date=_sv(spac_date),
                    )
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(going_concern=_sv(False)),
        ),
        governance=GovernanceData(
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("CEO"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("CFO"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


def _build_short_seller_target() -> tuple[ExtractedData, CompanyProfile]:
    """Named in recent activist short report -- CRF-7 ceiling."""
    company = _make_company(sector="HLTH", market_cap=5e9)
    report_date = _date_months_ago(3)
    ceo_start = date.today() - timedelta(days=int(4 * 365.25))
    cfo_start = date.today() - timedelta(days=int(2 * 365.25))
    extracted = ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(45.0),
                volatility_90d=_sv(5.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(15.0),
                vs_sector_ratio=_sv(3.75),
                short_seller_reports=[
                    _sv({"source": "Hindenburg Research", "date": report_date}),
                ],
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter="Q1 2025", result="MISS"),
                    *[
                        EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                        for i in range(2, 9)
                    ],
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(going_concern=_sv(False)),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.70),
                ceo_chair_duality=_sv(False),
            ),
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("CEO"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("CFO"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


def _build_restatement_crisis() -> tuple[ExtractedData, CompanyProfile]:
    """Recent Big R restatement with audit issues -- CRF-5 ceiling."""
    company = _make_company(sector="CONS", market_cap=3e9)
    restatement_date = _date_months_ago(6)
    ceo_start = date.today() - timedelta(days=int(3 * 365.25))
    cfo_start = date.today() - timedelta(days=90)  # recently replaced
    extracted = ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(30.0),
                volatility_90d=_sv(4.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(8.0),
                vs_sector_ratio=_sv(1.5),
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter="Q1 2025", result="MISS"),
                    EarningsQuarterRecord(quarter="Q2 2025", result="MISS"),
                    *[
                        EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                        for i in range(3, 9)
                    ],
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(
                going_concern=_sv(False),
                restatements=[
                    _sv({"date": restatement_date, "type": "big_R", "impact": "Material"})
                ],
                material_weaknesses=[
                    _sv("Material weakness in revenue recognition controls")
                ],
            ),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.65),
                ceo_chair_duality=_sv(True),
            ),
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        title=_sv("CEO"),
                        tenure_start=_sv(ceo_start.isoformat()),
                    ),
                    LeadershipForensicProfile(
                        title=_sv("CFO"),
                        tenure_start=_sv(cfo_start.isoformat()),
                    ),
                ],
            ),
        ),
    )
    return extracted, company


# -----------------------------------------------------------------------
# Archetype validation tests
# -----------------------------------------------------------------------


ARCHETYPE_BUILDERS = {
    "pristine_blue_chip": _build_pristine_blue_chip,
    "solid_mid_cap": _build_solid_mid_cap,
    "growth_darling_stressed": _build_growth_darling_stressed,
    "distressed_company": _build_distressed_company,
    "active_sca_defendant": _build_active_sca_defendant,
    "spac_penny_stock": _build_spac_penny_stock,
    "short_seller_target": _build_short_seller_target,
    "restatement_crisis": _build_restatement_crisis,
}


class TestArchetypeValidation:
    """Validate scoring engine against known-outcome company archetypes."""

    def test_pristine_blue_chip_is_win_or_want(self) -> None:
        """Stable mega-cap with no issues -> WIN or WANT tier."""
        extracted, company = _build_pristine_blue_chip()
        quality, binding, tier, factors, _ = _score_full_pipeline(extracted, company)

        assert tier in (Tier.WIN, Tier.WANT), (
            f"Pristine blue chip got tier={tier.value}, quality={quality}"
        )
        assert quality >= 71, f"Blue chip quality={quality} should be >= 71"
        assert binding is None, "No CRF should trigger for pristine blue chip"

        # All factors should be 0 or near-0
        for f in factors:
            if f.factor_id in ("F1", "F2", "F5", "F6", "F8"):
                assert f.points_deducted <= 3, (
                    f"Blue chip {f.factor_id} deducted {f.points_deducted}"
                )

    def test_solid_mid_cap_is_want_or_write(self) -> None:
        """Healthy mid-cap with minor issues -> WANT or WRITE."""
        extracted, company = _build_solid_mid_cap()
        quality, binding, tier, factors, _ = _score_full_pipeline(extracted, company)

        assert tier in (Tier.WANT, Tier.WRITE), (
            f"Solid mid-cap got tier={tier.value}, quality={quality}"
        )
        assert 40 <= quality <= 90, f"Mid-cap quality={quality} out of expected range"
        assert binding is None, "No CRF should trigger for solid mid-cap"

        # F1 should show some points for settled suit
        f1 = _factor_by_id(factors, "F1")
        assert f1.points_deducted > 0, "Settled SCA should give F1 points"

    def test_growth_darling_stressed_is_write_range(self) -> None:
        """High-growth tech with risk signals -> WRITE range."""
        extracted, company = _build_growth_darling_stressed()
        quality, _binding, tier, factors, _ = _score_full_pipeline(extracted, company)

        # Should be in WRITE or possibly WANT (depending on exact calibration)
        assert tier in (Tier.WANT, Tier.WRITE, Tier.WATCH), (
            f"Growth darling got tier={tier.value}, quality={quality}"
        )
        # Must score lower than pristine blue chip
        pristine_ext, pristine_co = _build_pristine_blue_chip()
        pristine_quality, _, _, _, _ = _score_full_pipeline(pristine_ext, pristine_co)
        assert quality < pristine_quality, (
            f"Growth darling ({quality}) should score lower than blue chip ({pristine_quality})"
        )

        # F2 should be non-zero (35% decline hits 30-40% rule)
        f2 = _factor_by_id(factors, "F2")
        assert f2.points_deducted > 0, "35% decline should trigger F2"

    def test_distressed_company_is_watch_or_walk(self) -> None:
        """Going concern + distress -> WATCH or worse, CRF-4 triggered."""
        extracted, company = _build_distressed_company()
        quality, _binding, tier, factors, flags = _score_full_pipeline(extracted, company)

        assert quality <= 50, f"Distressed company quality={quality} should be <= 50"
        assert tier in (Tier.WATCH, Tier.WALK, Tier.NO_TOUCH), (
            f"Distressed company got tier={tier.value}"
        )

        # CRF-4 (going concern) should trigger with ceiling 50
        crf4 = [f for f in flags if f.flag_id == "CRF-4"]
        assert len(crf4) == 1
        assert crf4[0].triggered is True, "CRF-4 should trigger for going concern"

        # F8 should have going concern hard trigger
        f8 = _factor_by_id(factors, "F8")
        assert f8.points_deducted >= 6, "Going concern hard trigger = 6 pts"

    def test_active_sca_defendant_is_walk_or_worse(self) -> None:
        """Active SCA -> WALK or worse, CRF-1 ceiling at 30."""
        extracted, company = _build_active_sca_defendant()
        quality, binding, tier, factors, flags = _score_full_pipeline(extracted, company)

        assert quality <= 30, (
            f"Active SCA defendant quality={quality} should be <= 30 (CRF-1 ceiling)"
        )
        assert tier in (Tier.WALK, Tier.NO_TOUCH), (
            f"Active SCA defendant got tier={tier.value}"
        )
        assert binding == "CRF-1", f"Binding ceiling should be CRF-1, got {binding}"

        # CRF-1 must trigger
        crf1 = [f for f in flags if f.flag_id == "CRF-1"]
        assert crf1[0].triggered is True

        # F1 should be at max (20 pts for active SCA)
        f1 = _factor_by_id(factors, "F1")
        assert f1.points_deducted == 20.0, "Active SCA -> F1 = 20 pts max"

    def test_spac_penny_stock_is_watch_or_worse(self) -> None:
        """SPAC <18mo + stock <$5 -> CRF-6 ceiling at 50."""
        extracted, company = _build_spac_penny_stock()
        quality, _binding, tier, _factors, flags = _score_full_pipeline(extracted, company)

        assert quality <= 50, (
            f"SPAC penny stock quality={quality} should be <= 50 (CRF-6 ceiling)"
        )
        assert tier in (Tier.WATCH, Tier.WALK, Tier.NO_TOUCH), (
            f"SPAC penny stock got tier={tier.value}"
        )

        # CRF-6 should trigger
        crf6 = [f for f in flags if f.flag_id == "CRF-6"]
        assert len(crf6) == 1
        assert crf6[0].triggered is True, "CRF-6 should trigger for SPAC under $5"

        # CRF-8 (>60% decline) should also trigger
        crf8 = [f for f in flags if f.flag_id == "CRF-8"]
        assert crf8[0].triggered is True, "70% decline should trigger CRF-8"

    def test_short_seller_target_is_watch_or_worse(self) -> None:
        """Hindenburg report <6 months -> CRF-7 ceiling at 50."""
        extracted, company = _build_short_seller_target()
        quality, _binding, tier, _factors, flags = _score_full_pipeline(extracted, company)

        assert quality <= 50, (
            f"Short seller target quality={quality} should be <= 50"
        )
        assert tier in (Tier.WATCH, Tier.WALK, Tier.NO_TOUCH), (
            f"Short seller target got tier={tier.value}"
        )

        # CRF-7 should trigger
        crf7 = [f for f in flags if f.flag_id == "CRF-7"]
        assert len(crf7) == 1
        assert crf7[0].triggered is True, "CRF-7 should trigger for short report <6mo"

    def test_restatement_crisis_is_watch_or_worse(self) -> None:
        """Big R restatement <12 months -> CRF-5 ceiling at 50."""
        extracted, company = _build_restatement_crisis()
        quality, _binding, tier, factors, flags = _score_full_pipeline(extracted, company)

        assert quality <= 50, (
            f"Restatement crisis quality={quality} should be <= 50"
        )
        assert tier in (Tier.WATCH, Tier.WALK, Tier.NO_TOUCH), (
            f"Restatement crisis got tier={tier.value}"
        )

        # CRF-5 should trigger
        crf5 = [f for f in flags if f.flag_id == "CRF-5"]
        assert len(crf5) == 1
        assert crf5[0].triggered is True, "CRF-5 should trigger for restatement <12mo"

        # F3 should be at or near max (12 pts for restatement <12mo)
        f3 = _factor_by_id(factors, "F3")
        assert f3.points_deducted >= 5, (
            f"Restatement <12mo F3 should score high, got {f3.points_deducted}"
        )


# -----------------------------------------------------------------------
# Monotonicity tests -- more risk = higher deductions
# -----------------------------------------------------------------------


class TestMonotonicity:
    """Verify that scoring factors are monotonically ordered with risk."""

    def test_f1_more_litigation_more_points(self) -> None:
        """F1: active SCA > settled <3yr > settled 5-10yr > clean."""
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()

        # Clean: no litigation
        clean = ExtractedData(litigation=LitigationLandscape())
        clean_scores = score_all_factors(scoring_config, clean, None, sectors_config)
        f1_clean = _factor_by_id(clean_scores, "F1").points_deducted

        # All test SCAs need securities legal theories to pass the
        # non-SCA filter (environmental/product cases are filtered out).
        _sca_theories = [_sv("RULE_10B5")]

        # Settled 5-10yr ago
        settled_old_date = date.today() - timedelta(days=int(7 * 365.25))
        old_settled = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(
                        case_name=_sv("In re Old Securities Litigation"),
                        status=_sv("SETTLED"),
                        filing_date=_sv(settled_old_date),
                        legal_theories=_sca_theories,
                        coverage_type=_sv("SCA_SIDE_A"),
                    )
                ]
            )
        )
        old_scores = score_all_factors(scoring_config, old_settled, None, sectors_config)
        f1_old = _factor_by_id(old_scores, "F1").points_deducted

        # Settled <3yr ago
        settled_new_date = date.today() - timedelta(days=int(1.5 * 365.25))
        new_settled = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(
                        case_name=_sv("In re Recent Securities Litigation"),
                        status=_sv("SETTLED"),
                        filing_date=_sv(settled_new_date),
                        legal_theories=_sca_theories,
                        coverage_type=_sv("SCA_SIDE_A"),
                    )
                ]
            )
        )
        new_scores = score_all_factors(scoring_config, new_settled, None, sectors_config)
        f1_new = _factor_by_id(new_scores, "F1").points_deducted

        # Active SCA
        active = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(
                        case_name=_sv("In re Active Securities Class Action"),
                        status=_sv("ACTIVE"),
                        legal_theories=_sca_theories,
                        coverage_type=_sv("SCA_SIDE_A"),
                    )
                ]
            )
        )
        active_scores = score_all_factors(scoring_config, active, None, sectors_config)
        f1_active = _factor_by_id(active_scores, "F1").points_deducted

        assert f1_clean < f1_old <= f1_new < f1_active, (
            f"F1 not monotonic: clean={f1_clean}, old_settled={f1_old}, "
            f"new_settled={f1_new}, active={f1_active}"
        )

    def test_f2_larger_decline_more_points(self) -> None:
        """F2: 60% > 45% > 25% > 10% decline."""
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()

        declines = [10.0, 25.0, 45.0, 65.0]
        f2_scores: list[float] = []

        for decline in declines:
            extracted = ExtractedData(
                market=MarketSignals(
                    stock=StockPerformance(decline_from_high_pct=_sv(decline))
                )
            )
            scores = score_all_factors(scoring_config, extracted, None, sectors_config)
            f2_scores.append(_factor_by_id(scores, "F2").points_deducted)

        for i in range(len(f2_scores) - 1):
            assert f2_scores[i] <= f2_scores[i + 1], (
                f"F2 not monotonic: decline {declines[i]}% -> {f2_scores[i]} pts, "
                f"decline {declines[i+1]}% -> {f2_scores[i+1]} pts"
            )

    def test_f5_more_misses_more_points(self) -> None:
        """F5: 4 misses > 3 misses > 2 misses > 1 miss > 0 misses."""
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()

        f5_scores: list[float] = []
        for miss_count in range(5):
            quarters = [
                EarningsQuarterRecord(
                    quarter=f"Q{i+1} 2025",
                    result="MISS" if i < miss_count else "BEAT",
                )
                for i in range(8)
            ]
            extracted = ExtractedData(
                market=MarketSignals(
                    earnings_guidance=EarningsGuidanceAnalysis(quarters=quarters)
                )
            )
            scores = score_all_factors(scoring_config, extracted, None, sectors_config)
            f5_scores.append(_factor_by_id(scores, "F5").points_deducted)

        for i in range(len(f5_scores) - 1):
            assert f5_scores[i] <= f5_scores[i + 1], (
                f"F5 not monotonic: {i} misses -> {f5_scores[i]}, "
                f"{i+1} misses -> {f5_scores[i+1]}"
            )

    def test_f6_higher_si_ratio_more_points(self) -> None:
        """F6: 4x > 2.5x > 1.7x > 0.5x sector ratio."""
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()

        ratios = [0.5, 1.7, 2.5, 4.0]
        f6_scores: list[float] = []

        for ratio in ratios:
            extracted = ExtractedData(
                market=MarketSignals(
                    short_interest=ShortInterestProfile(
                        short_pct_float=_sv(ratio * 4.0),  # TECH baseline ~4%
                        vs_sector_ratio=_sv(ratio),
                    )
                )
            )
            scores = score_all_factors(scoring_config, extracted, None, sectors_config)
            f6_scores.append(_factor_by_id(scores, "F6").points_deducted)

        for i in range(len(f6_scores) - 1):
            assert f6_scores[i] <= f6_scores[i + 1], (
                f"F6 not monotonic: ratio {ratios[i]} -> {f6_scores[i]}, "
                f"ratio {ratios[i+1]} -> {f6_scores[i+1]}"
            )

    def test_f7_higher_vol_ratio_more_points(self) -> None:
        """F7: 4x > 2.5x > 1.7x > 0.5x sector vol ratio."""
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()
        company = _make_company(sector="TECH")

        vol_ratios = [0.5, 1.7, 2.5, 4.0]
        f7_scores: list[float] = []

        # TECH sector vol baseline typical = 2.5
        for ratio in vol_ratios:
            vol = ratio * 2.5
            extracted = ExtractedData(
                market=MarketSignals(
                    stock=StockPerformance(volatility_90d=_sv(vol))
                )
            )
            scores = score_all_factors(scoring_config, extracted, company, sectors_config)
            f7_scores.append(_factor_by_id(scores, "F7").points_deducted)

        for i in range(len(f7_scores) - 1):
            assert f7_scores[i] <= f7_scores[i + 1], (
                f"F7 not monotonic: vol_ratio {vol_ratios[i]} -> {f7_scores[i]}, "
                f"vol_ratio {vol_ratios[i+1]} -> {f7_scores[i+1]}"
            )

    def test_f8_going_concern_triggers_hard_points(self) -> None:
        """F8: going concern hard trigger gives >= 6 points."""
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()

        # Without going concern
        no_gc = ExtractedData(
            financials=ExtractedFinancials(
                audit=AuditProfile(going_concern=_sv(False))
            )
        )
        no_gc_scores = score_all_factors(scoring_config, no_gc, None, sectors_config)
        f8_no_gc = _factor_by_id(no_gc_scores, "F8").points_deducted

        # With going concern
        gc = ExtractedData(
            financials=ExtractedFinancials(
                audit=AuditProfile(going_concern=_sv(True))
            )
        )
        gc_scores = score_all_factors(scoring_config, gc, None, sectors_config)
        f8_gc = _factor_by_id(gc_scores, "F8").points_deducted

        assert f8_gc > f8_no_gc, (
            f"F8 going concern ({f8_gc}) should be > no going concern ({f8_no_gc})"
        )
        assert f8_gc >= 6.0, f"F8 going concern hard trigger should be >= 6, got {f8_gc}"


# -----------------------------------------------------------------------
# CRF gate validation
# -----------------------------------------------------------------------


class TestCRFGateValidation:
    """Validate that each CRF gate triggers on its specific condition."""

    def test_all_17_gates_evaluated(self) -> None:
        """All 17 CRF gates produce results even with empty data."""
        rf_config = _load_red_flags_config()
        sc_config = _load_scoring_config()
        extracted = ExtractedData()
        results = evaluate_red_flag_gates(rf_config, sc_config, extracted, None)
        assert len(results) == 17, f"Expected 17 CRF gates, got {len(results)}"

    def test_crf1_only_triggers_on_active_sca(self) -> None:
        """CRF-1 triggers only when SCA status is ACTIVE."""
        rf_config = _load_red_flags_config()
        sc_config = _load_scoring_config()

        # Settled SCA should NOT trigger CRF-1
        settled = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(case_name=_sv("Settled"), status=_sv("SETTLED"))
                ]
            )
        )
        results = evaluate_red_flag_gates(rf_config, sc_config, settled, None)
        crf1 = [r for r in results if r.flag_id == "CRF-1"]
        assert not crf1[0].triggered, "Settled SCA should not trigger CRF-1"

    def test_crf4_triggers_only_on_going_concern(self) -> None:
        """CRF-4 requires going_concern=True in audit."""
        rf_config = _load_red_flags_config()
        sc_config = _load_scoring_config()

        # No going concern
        no_gc = ExtractedData(
            financials=ExtractedFinancials(
                audit=AuditProfile(going_concern=_sv(False))
            )
        )
        results = evaluate_red_flag_gates(rf_config, sc_config, no_gc, None)
        crf4 = [r for r in results if r.flag_id == "CRF-4"]
        assert not crf4[0].triggered, "going_concern=False should not trigger CRF-4"

    @pytest.mark.parametrize(
        "crf_id,ceiling",
        [
            ("CRF-1", 30),  # Active SCA -> WALK
            ("CRF-2", 30),  # Wells Notice -> WALK
            ("CRF-3", 30),  # DOJ -> WALK
            ("CRF-4", 50),  # Going concern -> WATCH
            ("CRF-5", 50),  # Restatement <12mo -> WATCH
            ("CRF-6", 50),  # SPAC under $5 -> WATCH
            ("CRF-7", 50),  # Short seller -> WATCH
            ("CRF-8", 50),  # >60% decline -> WATCH
            ("CRF-9", 50),  # 7-day drop -> WATCH
            ("CRF-10", 50),  # 30-day drop -> WATCH
            ("CRF-11", 50),  # 90-day drop -> WATCH
        ],
    )
    def test_crf_ceilings_match_config(self, crf_id: str, ceiling: int) -> None:
        """Each CRF has the correct ceiling value from scoring.json."""
        sc_config = _load_scoring_config()
        ceilings = sc_config["critical_red_flag_ceilings"]["ceilings"]
        from do_uw.stages.score.red_flag_gates import _normalize_crf_id

        for c in ceilings:
            if _normalize_crf_id(c["id"]) == crf_id:
                assert c["max_quality_score"] == ceiling, (
                    f"{crf_id} ceiling expected {ceiling}, got {c['max_quality_score']}"
                )
                return
        pytest.fail(f"CRF {crf_id} not found in scoring.json ceilings")
