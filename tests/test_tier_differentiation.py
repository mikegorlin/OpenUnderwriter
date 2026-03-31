"""Cross-profile tier differentiation tests.

Validates the scoring engine produces sensible RELATIVE ordering across
company archetypes -- not just individual tier correctness, but coherent
risk ranking across the full spectrum.

Integration tests using real scoring engine with no mocking.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

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
)
from do_uw.models.market import (
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.market_events import (
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
# Helpers (duplicated -- test files are independent)
# -----------------------------------------------------------------------


def _sv(
    value: object, source: str = "test", conf: Confidence = Confidence.HIGH
) -> SourcedValue:  # type: ignore[type-arg]
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
    """Run full scoring pipeline: quality_score, binding_id, tier, factors, flags."""
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


def _date_months_ago(months: int) -> str:
    d = date.today() - timedelta(days=int(months * 30.4))
    return d.isoformat()


# -----------------------------------------------------------------------
# Archetype fixture builders (independent copies for this file)
# -----------------------------------------------------------------------


def _build_apple_like() -> tuple[ExtractedData, CompanyProfile]:
    """Pristine blue chip: mega-cap, zero issues, strong governance."""
    company = _make_company(sector="TECH", market_cap=200e9)
    ceo_start = date.today() - timedelta(days=int(10 * 365.25))
    cfo_start = date.today() - timedelta(days=int(5 * 365.25))
    return ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(8.0),
                volatility_90d=_sv(1.5),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(1.0),
                vs_sector_ratio=_sv(0.25),
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
    ), company


def _build_solid_company() -> tuple[ExtractedData, CompanyProfile]:
    """Solid mid-cap: minor settled litigation, 1 miss."""
    company = _make_company(sector="INDU", market_cap=8e9)
    ceo_start = date.today() - timedelta(days=int(6 * 365.25))
    cfo_start = date.today() - timedelta(days=int(3 * 365.25))
    settled_date = date.today() - timedelta(days=int(7 * 365.25))
    return ExtractedData(
        litigation=LitigationLandscape(
            securities_class_actions=[
                CaseDetail(
                    case_name=_sv("In re OldCo"),
                    status=_sv("SETTLED"),
                    filing_date=_sv(settled_date),
                )
            ]
        ),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(25.0),
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
    ), company


def _build_stressed_growth() -> tuple[ExtractedData, CompanyProfile]:
    """Stressed growth company: 35% decline, 2 misses, high SI."""
    company = _make_company(sector="TECH", market_cap=15e9)
    ceo_start = date.today() - timedelta(days=int(3 * 365.25))
    cfo_start = date.today() - timedelta(days=int(2 * 365.25))
    return ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(35.0),
                volatility_90d=_sv(5.5),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(8.0),
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
    ), company


def _build_boeing_like() -> tuple[ExtractedData, CompanyProfile]:
    """Boeing-like: active SCA + stock decline + governance issues."""
    company = _make_company(sector="INDU", market_cap=100e9)
    ceo_start = date.today() - timedelta(days=int(1 * 365.25))
    cfo_start = date.today() - timedelta(days=int(2 * 365.25))
    return ExtractedData(
        litigation=LitigationLandscape(
            securities_class_actions=[
                CaseDetail(
                    case_name=_sv("In re BoeingLike Corp"),
                    status=_sv("ACTIVE"),
                )
            ]
        ),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(50.0),
                volatility_90d=_sv(6.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(5.0),
                vs_sector_ratio=_sv(1.7),
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter=f"Q{i} 2025", result="MISS")
                    for i in range(1, 4)
                ] + [
                    EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                    for i in range(4, 9)
                ]
            ),
        ),
        financials=ExtractedFinancials(
            audit=AuditProfile(going_concern=_sv(False)),
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
    ), company


def _build_smci_like() -> tuple[ExtractedData, CompanyProfile]:
    """SMCI-like: restatement + short seller + accounting issues."""
    company = _make_company(sector="TECH", market_cap=10e9)
    restatement_date = _date_months_ago(6)
    report_date = _date_months_ago(4)
    ceo_start = date.today() - timedelta(days=int(5 * 365.25))
    cfo_start = date.today() - timedelta(days=60)
    return ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(55.0),
                volatility_90d=_sv(7.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(12.0),
                vs_sector_ratio=_sv(3.0),
                short_seller_reports=[
                    _sv({"source": "Hindenburg Research", "date": report_date}),
                ],
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
                    _sv("Revenue recognition controls"),
                    _sv("IT general controls"),
                ],
            ),
        ),
        governance=GovernanceData(
            board=BoardProfile(
                independence_ratio=_sv(0.55),
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
    ), company


def _build_lucid_like() -> tuple[ExtractedData, CompanyProfile]:
    """Lucid-like: SPAC penny stock with severe decline."""
    from do_uw.models.market_events import (
        CapitalMarketsActivity,
        CapitalMarketsOffering,
    )

    company = _make_company(sector="TECH", market_cap=200e6)
    spac_date = _date_months_ago(12)
    ceo_start = date.today() - timedelta(days=int(1 * 365.25))
    cfo_start = date.today() - timedelta(days=int(0.5 * 365.25))
    return ExtractedData(
        litigation=LitigationLandscape(),
        market=MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(70.0),
                current_price=_sv(3.0),
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
                    CapitalMarketsOffering(offering_type="SPAC", date=_sv(spac_date))
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
    ), company


# -----------------------------------------------------------------------
# 1. Risk Ordering Test
# -----------------------------------------------------------------------


class TestRiskOrdering:
    """Verify coherent quality score ordering across all archetypes."""

    def test_full_spectrum_ordering(self) -> None:
        """Archetypes form coherent risk bands with expected tier groupings."""
        results: dict[str, tuple[float, Tier]] = {}

        archetypes = [
            ("apple_like", _build_apple_like),
            ("solid_company", _build_solid_company),
            ("stressed_growth", _build_stressed_growth),
            ("boeing_like", _build_boeing_like),
            ("smci_like", _build_smci_like),
            ("lucid_like", _build_lucid_like),
        ]

        for name, builder in archetypes:
            extracted, company = builder()
            quality, _, tier, _, _ = _score_full_pipeline(extracted, company)
            results[name] = (quality, tier)

        # Band 1: pristine companies score highest (WIN/WANT)
        apple_q = results["apple_like"][0]
        assert apple_q >= 86, (
            f"apple_like quality={apple_q:.1f} should be >= 86 (WIN tier)"
        )

        # Band 2: solid and stressed are in WANT/WRITE range, both above 50
        solid_q = results["solid_company"][0]
        stressed_q = results["stressed_growth"][0]
        assert solid_q > 50 and stressed_q > 50, (
            f"solid ({solid_q:.1f}) and stressed ({stressed_q:.1f}) "
            f"should both be > 50 (above WATCH threshold)"
        )

        # Both should be below pristine
        assert apple_q > solid_q, (
            f"apple_like ({apple_q:.1f}) should score higher than "
            f"solid_company ({solid_q:.1f})"
        )
        assert apple_q > stressed_q, (
            f"apple_like ({apple_q:.1f}) should score higher than "
            f"stressed_growth ({stressed_q:.1f})"
        )

        # Band 3: CRF-triggered profiles are capped
        for name in ("boeing_like", "smci_like", "lucid_like"):
            quality = results[name][0]
            assert quality <= 50, (
                f"{name} quality={quality:.1f} should be <= 50 (CRF triggered)"
            )

        # boeing_like (CRF-1, ceiling 30) should be <= 30
        boeing_q = results["boeing_like"][0]
        assert boeing_q <= 30, (
            f"boeing_like quality={boeing_q:.1f} should be <= 30 (active SCA)"
        )

        # CRF-triggered profiles should be strictly below non-CRF profiles
        min_non_crf = min(apple_q, solid_q, stressed_q)
        max_crf = max(
            results["boeing_like"][0],
            results["smci_like"][0],
            results["lucid_like"][0],
        )
        assert min_non_crf > max_crf, (
            f"Non-CRF minimum ({min_non_crf:.1f}) should be > "
            f"CRF maximum ({max_crf:.1f})"
        )


# -----------------------------------------------------------------------
# 2. Sector Differentiation Test
# -----------------------------------------------------------------------


class TestSectorDifferentiation:
    """Same risk profile across sectors should produce different scores."""

    def _build_identical_profile(
        self, sector: str
    ) -> tuple[ExtractedData, CompanyProfile]:
        """Build an identical risk profile for a given sector."""
        company = _make_company(sector=sector, market_cap=10e9)
        ceo_start = date.today() - timedelta(days=int(5 * 365.25))
        cfo_start = date.today() - timedelta(days=int(3 * 365.25))
        return ExtractedData(
            litigation=LitigationLandscape(),
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(30.0),
                    volatility_90d=_sv(4.0),
                ),
                short_interest=ShortInterestProfile(
                    short_pct_float=_sv(8.0),
                    # No vs_sector_ratio -- let engine compute from baseline
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
                leverage=_sv({"debt_to_ebitda": 4.0}),
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
        ), company

    def test_sector_variation_meaningful(self) -> None:
        """Same profile across TECH, FINS, BIOT, UTIL shows score variation."""
        sectors = ["TECH", "FINS", "BIOT", "UTIL"]
        scores: dict[str, float] = {}

        for sector in sectors:
            extracted, company = self._build_identical_profile(sector)
            quality, _, _, _, _ = _score_full_pipeline(extracted, company)
            scores[sector] = quality

        # The range of scores should be meaningful (>= 3 points between extremes)
        max_score = max(scores.values())
        min_score = min(scores.values())
        spread = max_score - min_score

        assert spread >= 3.0, (
            f"Cross-sector spread is only {spread:.1f} points. "
            f"Scores: {scores}. Expected >= 3 points difference."
        )

    def test_biot_8pct_si_better_than_tech_8pct_si(self) -> None:
        """BIOT with 8% SI should score better than TECH with 8% SI.

        BIOT baseline SI is 6% (ratio = 1.33x), TECH baseline is 4% (ratio = 2x).
        So 8% SI is less alarming in BIOT than TECH.
        """
        extracted_biot, company_biot = self._build_identical_profile("BIOT")
        extracted_tech, company_tech = self._build_identical_profile("TECH")

        # Score both
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()

        factors_biot = score_all_factors(
            scoring_config, extracted_biot, company_biot, sectors_config
        )
        factors_tech = score_all_factors(
            scoring_config, extracted_tech, company_tech, sectors_config
        )

        f6_biot = next(f for f in factors_biot if f.factor_id == "F6")
        f6_tech = next(f for f in factors_tech if f.factor_id == "F6")

        # BIOT F6 should be <= TECH F6 (less alarming in biotech)
        assert f6_biot.points_deducted <= f6_tech.points_deducted, (
            f"BIOT F6={f6_biot.points_deducted} should be <= "
            f"TECH F6={f6_tech.points_deducted} "
            f"(8% SI is normal-ish in biotech, elevated in tech)"
        )


# -----------------------------------------------------------------------
# 3. Red Flag Dominance Test
# -----------------------------------------------------------------------


class TestRedFlagDominance:
    """CRF gates dominate factor scores: ceiling overrides composite."""

    def _build_pristine_with_one_flag(
        self, flag_type: str
    ) -> tuple[ExtractedData, CompanyProfile]:
        """Build pristine company + one specific red flag."""
        company = _make_company(sector="TECH", market_cap=50e9)
        ceo_start = date.today() - timedelta(days=int(10 * 365.25))
        cfo_start = date.today() - timedelta(days=int(5 * 365.25))
        base_extracted = ExtractedData(
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(8.0),
                    volatility_90d=_sv(1.5),
                ),
                short_interest=ShortInterestProfile(
                    short_pct_float=_sv(1.0),
                    vs_sector_ratio=_sv(0.25),
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

        # Add the specific red flag
        if flag_type == "active_sca":
            base_extracted.litigation = LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(case_name=_sv("In re Securities Class Action"), status=_sv("ACTIVE"), legal_theories=[_sv("RULE_10B5")], coverage_type=_sv("SCA_SIDE_A"))
                ]
            )
        elif flag_type == "going_concern":
            base_extracted.financials = ExtractedFinancials(
                audit=AuditProfile(going_concern=_sv(True))
            )
        elif flag_type == "restatement":
            restatement_date = _date_months_ago(6)
            base_extracted.financials = ExtractedFinancials(
                audit=AuditProfile(
                    going_concern=_sv(False),
                    restatements=[
                        _sv({"date": restatement_date, "type": "big_R"})
                    ],
                )
            )

        return base_extracted, company

    def test_crf1_dominates_pristine_factors(self) -> None:
        """Active SCA on pristine company -> ceiling 30, not factor score."""
        extracted, company = self._build_pristine_with_one_flag("active_sca")
        quality, binding, tier, _, _ = _score_full_pipeline(extracted, company)

        assert quality <= 30, (
            f"CRF-1 ceiling should cap at 30, got quality={quality}"
        )
        assert binding == "CRF-1"
        assert tier in (Tier.WALK, Tier.NO_TOUCH)

    def test_crf4_dominates_pristine_factors(self) -> None:
        """Going concern on pristine company -> ceiling 50."""
        extracted, company = self._build_pristine_with_one_flag("going_concern")
        quality, binding, tier, _, _ = _score_full_pipeline(extracted, company)

        assert quality <= 50, (
            f"CRF-4 ceiling should cap at 50, got quality={quality}"
        )
        assert binding == "CRF-4"
        assert tier in (Tier.WATCH, Tier.WALK, Tier.NO_TOUCH)

    def test_crf5_dominates_pristine_factors(self) -> None:
        """Restatement <12mo on pristine company -> ceiling 50."""
        extracted, company = self._build_pristine_with_one_flag("restatement")
        quality, binding, tier, _, _ = _score_full_pipeline(extracted, company)

        assert quality <= 50, (
            f"CRF-5 ceiling should cap at 50, got quality={quality}"
        )
        assert binding == "CRF-5"
        assert tier in (Tier.WATCH, Tier.WALK, Tier.NO_TOUCH)


# -----------------------------------------------------------------------
# 4. Cumulative Risk Test
# -----------------------------------------------------------------------


class TestCumulativeRisk:
    """Adding risk factors progressively lowers the score."""

    def test_progressive_degradation(self) -> None:
        """Start pristine, add risk factors, score decreases each step."""
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()
        company = _make_company(sector="TECH", market_cap=50e9)
        ceo_start = date.today() - timedelta(days=int(10 * 365.25))
        cfo_start = date.today() - timedelta(days=int(5 * 365.25))

        # Step 0: Pristine baseline
        step0 = ExtractedData(
            litigation=LitigationLandscape(),
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(5.0),
                    volatility_90d=_sv(1.5),
                ),
                short_interest=ShortInterestProfile(
                    short_pct_float=_sv(1.0),
                    vs_sector_ratio=_sv(0.25),
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
        factors0 = score_all_factors(scoring_config, step0, company, sectors_config)
        score0 = 100.0 - sum(f.points_deducted for f in factors0)

        # Step 1: Add 30% stock decline
        step1 = step0.model_copy(deep=True)
        step1.market = MarketSignals(
            stock=StockPerformance(
                decline_from_high_pct=_sv(30.0),
                volatility_90d=_sv(1.5),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(1.0),
                vs_sector_ratio=_sv(0.25),
            ),
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                    for i in range(1, 9)
                ]
            ),
        )
        factors1 = score_all_factors(scoring_config, step1, company, sectors_config)
        score1 = 100.0 - sum(f.points_deducted for f in factors1)

        # Step 2: Add 2 guidance misses
        step2 = step1.model_copy(deep=True)
        assert step2.market is not None
        step2.market.earnings_guidance = EarningsGuidanceAnalysis(
            quarters=[
                EarningsQuarterRecord(quarter="Q1 2025", result="MISS"),
                EarningsQuarterRecord(quarter="Q2 2025", result="MISS"),
                *[
                    EarningsQuarterRecord(quarter=f"Q{i} 2025", result="BEAT")
                    for i in range(3, 9)
                ],
            ]
        )
        factors2 = score_all_factors(scoring_config, step2, company, sectors_config)
        score2 = 100.0 - sum(f.points_deducted for f in factors2)

        # Step 3: Add elevated short interest
        step3 = step2.model_copy(deep=True)
        assert step3.market is not None
        step3.market.short_interest = ShortInterestProfile(
            short_pct_float=_sv(12.0),
            vs_sector_ratio=_sv(3.0),
        )
        factors3 = score_all_factors(scoring_config, step3, company, sectors_config)
        score3 = 100.0 - sum(f.points_deducted for f in factors3)

        # Step 4: Add material weakness
        step4 = step3.model_copy(deep=True)
        step4.financials = ExtractedFinancials(
            audit=AuditProfile(
                going_concern=_sv(False),
                material_weaknesses=[_sv("Control deficiency")],
            ),
        )
        factors4 = score_all_factors(scoring_config, step4, company, sectors_config)
        score4 = 100.0 - sum(f.points_deducted for f in factors4)

        # Verify strictly decreasing
        assert score0 > score1, (
            f"Step 0 ({score0:.1f}) should be > Step 1 ({score1:.1f}) [+30% decline]"
        )
        assert score1 > score2, (
            f"Step 1 ({score1:.1f}) should be > Step 2 ({score2:.1f}) [+2 misses]"
        )
        assert score2 > score3, (
            f"Step 2 ({score2:.1f}) should be > Step 3 ({score3:.1f}) [+high SI]"
        )
        assert score3 > score4, (
            f"Step 3 ({score3:.1f}) should be > Step 4 ({score4:.1f}) [+material weakness]"
        )


# -----------------------------------------------------------------------
# 5. Edge Case Tests
# -----------------------------------------------------------------------


class TestEdgeCases:
    """Boundary conditions and extreme values."""

    def test_zero_risk_profile_scores_100(self) -> None:
        """Minimal empty state -> 0 risk points -> quality = 100, tier = WIN."""
        extracted = ExtractedData()
        scoring_config = _load_scoring_config()
        sectors_config = _load_sectors_config()

        factors = score_all_factors(scoring_config, extracted, None, sectors_config)
        total_deducted = sum(f.points_deducted for f in factors)

        assert total_deducted == 0.0, (
            f"Zero-risk profile should deduct 0 points, got {total_deducted}"
        )

        quality = 100.0 - total_deducted
        tier = classify_tier(quality, scoring_config["tiers"])
        assert tier.tier == Tier.WIN, f"Quality 100 should be WIN, got {tier.tier}"

    def test_maximum_risk_scores_zero(self) -> None:
        """Every factor at max -> quality near 0, tier = NO_TOUCH."""
        company = _make_company(sector="TECH", market_cap=200e9)
        ceo_start = date.today() - timedelta(days=30)  # brand new CEO
        cfo_start = date.today() - timedelta(days=30)  # brand new CFO
        restatement_date = _date_months_ago(3)

        from do_uw.models.market_events import (
            CapitalMarketsActivity,
            CapitalMarketsOffering,
        )

        spac_date = _date_months_ago(6)
        extracted = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(case_name=_sv("In re Securities Class Action"), status=_sv("ACTIVE"), legal_theories=[_sv("RULE_10B5")], coverage_type=_sv("SCA_SIDE_A"))
                ]
            ),
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(75.0),
                    current_price=_sv(2.0),
                    volatility_90d=_sv(15.0),
                ),
                short_interest=ShortInterestProfile(
                    short_pct_float=_sv(25.0),
                    vs_sector_ratio=_sv(6.0),
                ),
                earnings_guidance=EarningsGuidanceAnalysis(
                    quarters=[
                        EarningsQuarterRecord(quarter=f"Q{i} 2025", result="MISS")
                        for i in range(1, 9)
                    ]
                ),
                capital_markets=CapitalMarketsActivity(
                    offerings_3yr=[
                        CapitalMarketsOffering(
                            offering_type="SPAC", date=_sv(spac_date)
                        )
                    ]
                ),
            ),
            financials=ExtractedFinancials(
                audit=AuditProfile(
                    going_concern=_sv(True),
                    restatements=[_sv({"date": restatement_date, "type": "big_R"})],
                    material_weaknesses=[_sv("MW1"), _sv("MW2")],
                ),
                leverage=_sv({"debt_to_ebitda": 10.0}),
            ),
            governance=GovernanceData(
                board=BoardProfile(
                    independence_ratio=_sv(0.40),
                    ceo_chair_duality=_sv(True),
                    dual_class_structure=_sv(True),
                ),
                leadership=LeadershipStability(
                    executives=[
                        LeadershipForensicProfile(
                            title=_sv("CEO"),
                            tenure_start=_sv(ceo_start.isoformat()),
                            is_interim=_sv(True),
                        ),
                        LeadershipForensicProfile(
                            title=_sv("CFO"),
                            tenure_start=_sv(cfo_start.isoformat()),
                            is_interim=_sv(True),
                        ),
                    ],
                ),
            ),
        )

        quality, _binding, tier, factors, _ = _score_full_pipeline(extracted, company)

        # CRF-1 (active SCA) should cap at 30
        assert quality <= 30, f"Max risk quality={quality} should be <= 30"
        assert tier in (Tier.WALK, Tier.NO_TOUCH), (
            f"Max risk should be WALK or NO_TOUCH, got {tier.value}"
        )

        # Many factor points should be deducted
        total_deducted = sum(f.points_deducted for f in factors)
        assert total_deducted >= 50, (
            f"Max risk should deduct >= 50 points, got {total_deducted}"
        )

    def test_boundary_score_86_is_win(self) -> None:
        """Score exactly 86 -> WIN tier (86-100 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(86.0, tiers)
        assert result.tier == Tier.WIN

    def test_boundary_score_85_is_want(self) -> None:
        """Score exactly 85 -> WANT tier (71-85 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(85.0, tiers)
        assert result.tier == Tier.WANT

    def test_boundary_score_71_is_want(self) -> None:
        """Score exactly 71 -> WANT tier (71-85 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(71.0, tiers)
        assert result.tier == Tier.WANT

    def test_boundary_score_70_is_write(self) -> None:
        """Score exactly 70 -> WRITE tier (51-70 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(70.0, tiers)
        assert result.tier == Tier.WRITE

    def test_boundary_score_51_is_write(self) -> None:
        """Score exactly 51 -> WRITE tier (51-70 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(51.0, tiers)
        assert result.tier == Tier.WRITE

    def test_boundary_score_50_is_watch(self) -> None:
        """Score exactly 50 -> WATCH tier (31-50 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(50.0, tiers)
        assert result.tier == Tier.WATCH

    def test_boundary_score_31_is_watch(self) -> None:
        """Score exactly 31 -> WATCH tier (31-50 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(31.0, tiers)
        assert result.tier == Tier.WATCH

    def test_boundary_score_30_is_walk(self) -> None:
        """Score exactly 30 -> WALK tier (11-30 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(30.0, tiers)
        assert result.tier == Tier.WALK

    def test_boundary_score_10_is_no_touch(self) -> None:
        """Score exactly 10 -> NO_TOUCH tier (0-10 range)."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(10.0, tiers)
        assert result.tier == Tier.NO_TOUCH

    def test_boundary_score_0_is_no_touch(self) -> None:
        """Score 0 -> NO_TOUCH tier."""
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(0.0, tiers)
        assert result.tier == Tier.NO_TOUCH
