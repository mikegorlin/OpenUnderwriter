"""Generate a rich sample D&O underwriting worksheet for visual review.

Creates a comprehensive test fixture exercising all 7 sections + meeting
prep appendix with realistic data, then renders to Word/Markdown/PDF.

Usage: python scripts/generate_sample_doc.py
Output: output/SAMPLE/SAMPLE_worksheet.docx (+ .md, .pdf)
"""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.executive_summary import (
    CompanySnapshot,
    ExecutiveSummary,
    InherentRiskBaseline,
    KeyFinding,
    KeyFindings,
    UnderwritingThesis,
)
from do_uw.models.financials import (
    AuditProfile,
    DistressIndicators,
    DistressResult,
    DistressZone,
    ExtractedFinancials,
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
    PeerCompany,
    PeerGroup,
)
from do_uw.models.governance import (
    BoardProfile,
    CompensationFlags,
    GovernanceData,
)
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    LeadershipForensicProfile,
    LeadershipStability,
    NarrativeCoherence,
    OwnershipAnalysis,
    SentimentProfile,
)
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
    SECEnforcementPipeline,
)
from do_uw.models.litigation_details import LitigationTimelineEvent
from do_uw.models.market import MarketSignals
from do_uw.models.market_events import (
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    InsiderClusterEvent,
    InsiderTradingAnalysis,
    StockDropAnalysis,
    StockDropEvent,
)
from do_uw.models.market import ShortInterestProfile
from do_uw.models.scoring import (
    FactorScore,
    PatternMatch,
    RedFlagResult,
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.scoring_output import (
    AllegationMapping,
    AllegationTheory,
    ClaimProbability,
    FlaggedItem,
    FlagSeverity,
    LayerAssessment,
    ProbabilityBand,
    RedFlagSummary,
    RiskType,
    RiskTypeClassification,
    SeverityScenario,
    SeverityScenarios,
    TheoryExposure,
    TowerPosition,
    TowerRecommendation,
)
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.render.design_system import (
    DesignSystem,
    configure_matplotlib_defaults,
)
from do_uw.stages.render.word_renderer import render_word_document

_NOW = datetime(2025, 6, 15, tzinfo=UTC)


def _sv(value: Any, source: str = "SEC 10-K, 2024-12-31") -> SourcedValue[Any]:
    """Create a test SourcedValue with realistic source info."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=Confidence.HIGH,
        as_of=_NOW,
    )


def _sv_med(
    value: Any, source: str = "yfinance API"
) -> SourcedValue[Any]:
    """Create a MEDIUM confidence SourcedValue."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=Confidence.MEDIUM,
        as_of=_NOW,
    )


def _sv_low(
    value: Any, source: str = "Brave Search"
) -> SourcedValue[Any]:
    """Create a LOW confidence SourcedValue."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=Confidence.LOW,
        as_of=_NOW,
    )


def _build_company() -> CompanyProfile:
    """Build a realistic company profile (modeled loosely on a tech company)."""
    identity = CompanyIdentity(
        ticker="ACME",
        legal_name=_sv("Acme Technology Holdings Inc."),
        cik=_sv("0001567890"),
        sic_code=_sv("7372"),
        sic_description=_sv("Prepackaged Software"),
        naics_code=_sv("511210"),
        exchange=_sv("NASDAQ"),
        sector=_sv("TECH"),
        state_of_incorporation=_sv("DE"),
        fiscal_year_end=_sv("12-31"),
        entity_type=_sv("operating"),
    )
    return CompanyProfile(
        identity=identity,
        business_description=_sv(
            "Acme Technology Holdings Inc. is a leading provider of cloud-based "
            "enterprise resource planning (ERP) software and digital transformation "
            "services. The company serves over 15,000 customers globally across "
            "financial services, healthcare, and manufacturing verticals. Founded "
            "in 2008, Acme has grown through organic development and strategic "
            "acquisitions, including the $2.1B purchase of DataSync Corp in 2023."
        ),
        market_cap=_sv_med(8_500_000_000.0),
        employee_count=_sv(12500),
        filer_category=_sv("large accelerated"),
        years_public=_sv(11),
        revenue_segments=[
            _sv(
                {"name": "Cloud Subscriptions", "revenue": 1_800_000_000.0, "percentage": 54.5},
                source="SEC 10-K Item 1, 2024-12-31",
            ),
            _sv(
                {"name": "Professional Services", "revenue": 950_000_000.0, "percentage": 28.8},
                source="SEC 10-K Item 1, 2024-12-31",
            ),
            _sv(
                {"name": "License & Maintenance", "revenue": 550_000_000.0, "percentage": 16.7},
                source="SEC 10-K Item 1, 2024-12-31",
            ),
        ],
        geographic_footprint=[
            _sv({"region": "North America", "revenue": 2_310_000_000.0, "percentage": 70.0}),
            _sv({"region": "Europe", "revenue": 660_000_000.0, "percentage": 20.0}),
            _sv({"region": "Asia-Pacific", "revenue": 330_000_000.0, "percentage": 10.0}),
        ],
        subsidiary_count=_sv(47),
        section_summary=_sv_low(
            "Acme Technology is a large-cap cloud ERP company undergoing rapid "
            "growth via the $2.1B DataSync acquisition. International operations "
            "across 47 subsidiaries in 22 countries increase jurisdictional "
            "complexity. The company's guidance-dependent growth model and "
            "aggressive acquisition strategy create elevated D&O exposure."
        ),
        do_exposure_factors=[
            _sv({"factor": "Market Cap", "level": "HIGH", "rationale": "Large cap ($8.5B) attracts plaintiff firms and institutional investors"}),
            _sv({"factor": "Industry", "level": "HIGH", "rationale": "Technology sector has highest SCA filing rate at 5.8%"}),
            _sv({"factor": "International Ops", "level": "ELEVATED", "rationale": "47 subsidiaries across 22 countries; FCPA/UK Bribery Act exposure"}),
            _sv({"factor": "M&A Activity", "level": "HIGH", "rationale": "Recent $2.1B acquisition; integration risk and goodwill impairment"}),
            _sv({"factor": "Growth Model", "level": "ELEVATED", "rationale": "Guidance-dependent; consecutive miss risk from aggressive targets"}),
        ],
    )


def _build_financials() -> ExtractedFinancials:
    """Build realistic financial data with distress and audit info."""
    income = FinancialStatement(
        statement_type="income",
        periods=["FY2024", "FY2023", "FY2022"],
        line_items=[
            FinancialLineItem(
                label="Total Revenue",
                values={
                    "FY2024": _sv(3_300_000_000.0),
                    "FY2023": _sv(2_800_000_000.0),
                    "FY2022": _sv(2_350_000_000.0),
                },
                yoy_change=17.9,
            ),
            FinancialLineItem(
                label="Cost of Revenue",
                values={
                    "FY2024": _sv(1_485_000_000.0),
                    "FY2023": _sv(1_204_000_000.0),
                    "FY2022": _sv(987_500_000.0),
                },
                yoy_change=23.3,
            ),
            FinancialLineItem(
                label="Gross Profit",
                values={
                    "FY2024": _sv(1_815_000_000.0),
                    "FY2023": _sv(1_596_000_000.0),
                    "FY2022": _sv(1_362_500_000.0),
                },
                yoy_change=13.7,
            ),
            FinancialLineItem(
                label="Operating Income",
                values={
                    "FY2024": _sv(330_000_000.0),
                    "FY2023": _sv(420_000_000.0),
                    "FY2022": _sv(376_000_000.0),
                },
                yoy_change=-21.4,
            ),
            FinancialLineItem(
                label="Net Income",
                values={
                    "FY2024": _sv(165_000_000.0),
                    "FY2023": _sv(308_000_000.0),
                    "FY2022": _sv(282_000_000.0),
                },
                yoy_change=-46.4,
            ),
            FinancialLineItem(
                label="EPS (Diluted)",
                values={
                    "FY2024": _sv(1.32),
                    "FY2023": _sv(2.46),
                    "FY2022": _sv(2.26),
                },
                yoy_change=-46.3,
            ),
        ],
    )
    balance = FinancialStatement(
        statement_type="balance_sheet",
        periods=["FY2024", "FY2023"],
        line_items=[
            FinancialLineItem(
                label="Total Assets",
                values={
                    "FY2024": _sv(14_200_000_000.0),
                    "FY2023": _sv(10_500_000_000.0),
                },
                yoy_change=35.2,
            ),
            FinancialLineItem(
                label="Total Liabilities",
                values={
                    "FY2024": _sv(8_900_000_000.0),
                    "FY2023": _sv(5_800_000_000.0),
                },
                yoy_change=53.4,
            ),
            FinancialLineItem(
                label="Total Equity",
                values={
                    "FY2024": _sv(5_300_000_000.0),
                    "FY2023": _sv(4_700_000_000.0),
                },
                yoy_change=12.8,
            ),
            FinancialLineItem(
                label="Goodwill",
                values={
                    "FY2024": _sv(4_100_000_000.0),
                    "FY2023": _sv(2_200_000_000.0),
                },
                yoy_change=86.4,
            ),
        ],
    )
    distress = DistressIndicators(
        altman_z_score=DistressResult(
            score=2.35,
            zone=DistressZone.GREY,
            model_variant="original",
            trajectory=[
                {"period": "Q1", "score": 2.8},
                {"period": "Q2", "score": 2.6},
                {"period": "Q3", "score": 2.5},
                {"period": "Q4", "score": 2.35},
            ],
        ),
        beneish_m_score=DistressResult(
            score=-1.78,
            zone=DistressZone.GREY,
            model_variant="8-variable",
        ),
        ohlson_o_score=DistressResult(
            score=0.42,
            zone=DistressZone.SAFE,
            model_variant="standard",
        ),
        piotroski_f_score=DistressResult(
            score=5.0,
            zone=DistressZone.GREY,
            model_variant="standard",
        ),
    )
    audit = AuditProfile(
        auditor_name=_sv("Ernst & Young LLP"),
        is_big4=_sv(True),
        tenure_years=_sv(8),
        opinion_type=_sv("unqualified"),
        going_concern=_sv(False),
        material_weaknesses=[
            _sv("Ineffective internal controls over revenue recognition related to the DataSync acquisition integration"),
        ],
        restatements=[],
        critical_audit_matters=[
            _sv("Revenue recognition for multi-element cloud arrangements"),
            _sv("Goodwill impairment assessment for DataSync reporting unit"),
        ],
    )
    peer_group = PeerGroup(
        target_ticker="ACME",
        peers=[
            PeerCompany(ticker="CRM", name="Salesforce Inc.", market_cap=250_000_000_000.0, revenue=34_000_000_000.0, peer_score=72.0),
            PeerCompany(ticker="WDAY", name="Workday Inc.", market_cap=65_000_000_000.0, revenue=7_200_000_000.0, peer_score=85.0),
            PeerCompany(ticker="INTU", name="Intuit Inc.", market_cap=160_000_000_000.0, revenue=16_000_000_000.0, peer_score=78.0),
            PeerCompany(ticker="NOW", name="ServiceNow Inc.", market_cap=155_000_000_000.0, revenue=9_400_000_000.0, peer_score=82.0),
            PeerCompany(ticker="VEEV", name="Veeva Systems Inc.", market_cap=33_000_000_000.0, revenue=2_300_000_000.0, peer_score=90.0),
        ],
        construction_method="SIC 7372 + market cap tier match + yfinance enrichment",
    )
    return ExtractedFinancials(
        statements=FinancialStatements(
            income_statement=income,
            balance_sheet=balance,
            periods_available=3,
        ),
        distress=distress,
        audit=audit,
        peer_group=peer_group,
        leverage=_sv({
            "debt_to_equity": 1.68,
            "debt_to_ebitda": 4.2,
            "interest_coverage": 3.8,
        }),
        debt_structure=_sv({
            "total_debt": 6_200_000_000.0,
            "long_term_debt": 5_800_000_000.0,
            "short_term_debt": 400_000_000.0,
        }),
        refinancing_risk=_sv({
            "risk_level": "ELEVATED",
            "next_maturity_date": "2026-09-15",
            "amount_maturing": 1_500_000_000.0,
        }),
        financial_health_narrative=_sv_low(
            "Acme's financial health shows a mixed picture. Revenue growth of 17.9% "
            "is strong but largely acquisition-driven, with organic growth estimated "
            "at ~8%. Operating margins compressed from 15.0% to 10.0% due to DataSync "
            "integration costs. The $4.1B goodwill balance (29% of assets) represents "
            "significant impairment risk. Leverage has increased to 1.68x D/E from the "
            "acquisition financing, with $1.5B maturing in September 2026. Altman Z-Score "
            "has declined to the grey zone at 2.35, warranting close monitoring."
        ),
    )


def _build_market() -> MarketSignals:
    """Build realistic market signals data."""
    from do_uw.models.market import (
        InsiderTradingProfile,
        StockPerformance,
    )

    stock = StockPerformance(
        current_price=_sv_med(68.50),
        high_52w=_sv_med(112.30),
        low_52w=_sv_med(55.20),
        decline_from_high_pct=_sv_med(39.0),
        returns_1y=_sv_med(-28.5),
        volatility_90d=_sv_med(42.3),
    )
    drops = StockDropAnalysis(
        single_day_drops=[
            StockDropEvent(
                date=_sv_med("2025-01-15"),
                drop_pct=_sv_med(-15.2),
                drop_type="SINGLE_DAY",
                trigger_event=_sv_low("Q4 earnings miss; guidance withdrawn"),
                period_days=1,
            ),
            StockDropEvent(
                date=_sv_med("2024-11-08"),
                drop_pct=_sv_med(-9.8),
                drop_type="SINGLE_DAY",
                trigger_event=_sv_low("Short seller report by Citron Research"),
                period_days=1,
            ),
            StockDropEvent(
                date=_sv_med("2024-08-22"),
                drop_pct=_sv_med(-8.3),
                drop_type="SINGLE_DAY",
                trigger_event=_sv_low("SEC comment letter disclosure in 10-Q"),
                period_days=1,
            ),
        ],
        multi_day_drops=[
            StockDropEvent(
                date=_sv_med("2025-01-15"),
                drop_pct=_sv_med(-22.5),
                drop_type="MULTI_DAY",
                trigger_event=_sv_low("Post-earnings sell-off + analyst downgrades"),
                period_days=5,
            ),
        ],
    )
    insider_basic = InsiderTradingProfile(
        net_buying_selling=_sv_med("NET_SELLING"),
        total_sold_value=_sv_med(45_000_000.0),
        total_bought_value=_sv_med(2_000_000.0),
    )
    insider_analysis = InsiderTradingAnalysis(
        net_buying_selling=_sv_med("NET_SELLING"),
        pct_10b5_1=_sv_med(35.0),
        cluster_events=[
            InsiderClusterEvent(
                start_date="2024-12-18",
                end_date="2024-12-22",
                insider_count=4,
                insiders=["CEO", "CFO", "CTO", "VP Sales"],
                total_value=12_000_000.0,
            ),
            InsiderClusterEvent(
                start_date="2025-01-08",
                end_date="2025-01-12",
                insider_count=3,
                insiders=["CEO", "CFO", "GC"],
                total_value=8_500_000.0,
            ),
        ],
    )
    short_interest = ShortInterestProfile(
        short_pct_float=_sv_med(14.2),
        days_to_cover=_sv_med(6.8),
        trend_6m=_sv_med("INCREASING"),
        vs_sector_ratio=_sv_med(2.1),
        short_seller_reports=[
            _sv_low({"firm": "Citron Research", "date": "2024-11-08", "summary": "Alleged revenue recognition issues at DataSync"}),
        ],
    )
    earnings = EarningsGuidanceAnalysis(
        beat_rate=_sv_med(50.0),
        consecutive_miss_count=3,
        guidance_withdrawals=1,
        philosophy="AGGRESSIVE",
        quarters=[
            EarningsQuarterRecord(quarter="Q4 2024", result="MISS", miss_magnitude_pct=_sv_med(-8.5), stock_reaction_pct=_sv_med(-15.2)),
            EarningsQuarterRecord(quarter="Q3 2024", result="MISS", miss_magnitude_pct=_sv_med(-3.2), stock_reaction_pct=_sv_med(-8.3)),
            EarningsQuarterRecord(quarter="Q2 2024", result="MISS", miss_magnitude_pct=_sv_med(-1.1), stock_reaction_pct=_sv_med(-4.1)),
            EarningsQuarterRecord(quarter="Q1 2024", result="BEAT", miss_magnitude_pct=_sv_med(2.3), stock_reaction_pct=_sv_med(5.8)),
            EarningsQuarterRecord(quarter="Q4 2023", result="BEAT", miss_magnitude_pct=_sv_med(4.1), stock_reaction_pct=_sv_med(7.2)),
            EarningsQuarterRecord(quarter="Q3 2023", result="BEAT", miss_magnitude_pct=_sv_med(1.5), stock_reaction_pct=_sv_med(3.1)),
        ],
    )
    return MarketSignals(
        stock=stock,
        stock_drops=drops,
        insider_trading=insider_basic,
        insider_analysis=insider_analysis,
        short_interest=short_interest,
        earnings_guidance=earnings,
    )


def _build_governance() -> GovernanceData:
    """Build realistic governance data."""
    board = BoardProfile(
        size=_sv(11),
        independence_ratio=_sv(0.73),
        avg_tenure_years=_sv(5.2),
        ceo_chair_duality=_sv(True),
        overboarded_count=_sv(2),
        classified_board=_sv(False),
    )
    comp_flags = CompensationFlags(
        say_on_pay_support_pct=_sv(65.0, source="DEF 14A, 2024-04-15"),
        ceo_pay_ratio=_sv(280.0, source="DEF 14A, 2024-04-15"),
    )
    leadership = LeadershipStability(
        executives=[
            LeadershipForensicProfile(
                name=_sv("Robert Chen"),
                title=_sv("CEO & Chairman"),
                tenure_years=6.5,
                departure_type="ACTIVE",
                prior_litigation=[
                    _sv("Named defendant in securities class action at prior company (2018)"),
                ],
                shade_factors=[
                    _sv("CEO/Chairman duality reduces board oversight"),
                    _sv("Prior litigation exposure at former employer"),
                ],
            ),
            LeadershipForensicProfile(
                name=_sv("Sarah Kim"),
                title=_sv("CFO"),
                tenure_years=1.2,
                departure_type="ACTIVE",
                prior_litigation=[],
                shade_factors=[
                    _sv("Relatively new CFO (1.2 years) during critical integration period"),
                ],
            ),
            LeadershipForensicProfile(
                name=_sv("Michael Torres"),
                title=_sv("CTO"),
                tenure_years=4.0,
                departure_type="ACTIVE",
                prior_litigation=[],
                shade_factors=[],
            ),
            LeadershipForensicProfile(
                name=_sv("James Wright"),
                title=_sv("Former CFO"),
                tenure_years=5.0,
                departure_type="VOLUNTARY",
                prior_litigation=[],
                shade_factors=[
                    _sv("Departure during acquisition integration raises timing questions"),
                ],
            ),
        ],
        stability_score=_sv_low(58.0),
    )
    board_forensics = [
        BoardForensicProfile(
            name=_sv("Robert Chen"),
            tenure_years=_sv(6.5),
            is_independent=_sv(False),
            committees=["Executive"],
            is_overboarded=False,
        ),
        BoardForensicProfile(
            name=_sv("Patricia Adams"),
            tenure_years=_sv(8.0),
            is_independent=_sv(True),
            committees=["Audit", "Compensation"],
            is_overboarded=False,
        ),
        BoardForensicProfile(
            name=_sv("David Park"),
            tenure_years=_sv(3.0),
            is_independent=_sv(True),
            committees=["Audit"],
            is_overboarded=True,
        ),
    ]
    comp_analysis = CompensationAnalysis(
        ceo_total_comp=_sv(18_500_000.0, source="DEF 14A, 2024-04-15"),
        ceo_pay_ratio=_sv(280.0, source="DEF 14A, 2024-04-15"),
        say_on_pay_pct=_sv(65.0, source="DEF 14A, 2024-04-15"),
        has_clawback=_sv(True),
        ceo_pay_vs_peer_median=_sv(1.45),
    )
    ownership = OwnershipAnalysis(
        institutional_pct=_sv_med(72.0),
        insider_pct=_sv_med(8.0),
        known_activists=[_sv_low("ValueAct Capital (3.2% stake acquired Q3 2024)")],
    )
    sentiment = SentimentProfile(
        management_tone_trajectory=_sv_low("DETERIORATING"),
        hedging_language_trend=_sv_low("INCREASING"),
        ceo_cfo_divergence=_sv_low("MODERATE divergence on guidance outlook"),
        qa_evasion_score=_sv_low(0.35),
    )
    coherence = NarrativeCoherence(
        overall_assessment=_sv_low("MIXED"),
        coherence_flags=[
            _sv_low("Management guidance unchanged despite 3 consecutive misses"),
            _sv_low("Integration 'on track' messaging contradicts margin compression"),
        ],
    )
    return GovernanceData(
        board=board,
        compensation=comp_flags,
        leadership=leadership,
        board_forensics=board_forensics,
        comp_analysis=comp_analysis,
        ownership=ownership,
        sentiment=sentiment,
        narrative_coherence=coherence,
        governance_summary=_sv_low(
            "Governance structure shows moderate risk. CEO/Chairman duality reduces board "
            "independence. Say-on-pay support at 65% is below the 70% concern threshold. "
            "The recent CFO transition during a critical acquisition integration period "
            "raises leadership stability questions. ValueAct Capital's 3.2% activist "
            "position adds proxy contest risk. Positive: Big 4 auditor, clawback policy "
            "in place, majority independent board."
        ),
    )


def _build_litigation() -> LitigationLandscape:
    """Build realistic litigation data."""
    scas = [
        CaseDetail(
            case_name=_sv("In re Acme Technology Holdings Securities Litigation"),
            case_number=_sv("1:25-cv-01234"),
            court=_sv("S.D.N.Y."),
            filing_date=_sv(date(2025, 2, 10)),
            class_period_start=_sv(date(2024, 3, 1)),
            class_period_end=_sv(date(2025, 1, 15)),
            allegations=[_sv("Section 10(b)"), _sv("Rule 10b-5")],
            status=_sv("ACTIVE"),
            lead_counsel=_sv("Bernstein Litowitz Berger & Grossmann"),
            lead_counsel_tier=_sv(1),
        ),
        CaseDetail(
            case_name=_sv("Smith v. Acme Technology Holdings, Inc."),
            case_number=_sv("3:22-cv-05678"),
            court=_sv("N.D. Cal."),
            filing_date=_sv(date(2022, 8, 15)),
            allegations=[_sv("Section 10(b)"), _sv("Section 20(a)")],
            status=_sv("SETTLED"),
            settlement_amount=_sv(28_000_000.0),
            lead_counsel=_sv("Robbins Geller Rudman & Dowd"),
            lead_counsel_tier=_sv(1),
        ),
    ]
    enforcement = SECEnforcementPipeline(
        highest_confirmed_stage=_sv("COMMENT_LETTER"),
        comment_letter_count=_sv(3),
        comment_letter_topics=[
            _sv("Revenue recognition timing"),
            _sv("Non-GAAP metrics presentation"),
            _sv("Goodwill impairment testing methodology"),
        ],
        enforcement_narrative=_sv_low(
            "Three SEC comment letters received in 2024 focused on revenue recognition "
            "and goodwill impairment. No formal investigation indicated, but topic pattern "
            "aligns with SEC enforcement focus areas for technology acquisitions."
        ),
    )
    timeline_events = [
        LitigationTimelineEvent(
            event_date=date(2024, 8, 22),
            event_type=_sv_low("REGULATORY"),
            description=_sv_low("SEC comment letter on revenue recognition"),
            severity=_sv_low("MODERATE"),
        ),
        LitigationTimelineEvent(
            event_date=date(2024, 11, 8),
            event_type=_sv_low("MARKET"),
            description=_sv_low("Citron Research short seller report published"),
            severity=_sv_low("HIGH"),
        ),
        LitigationTimelineEvent(
            event_date=date(2025, 1, 15),
            event_type=_sv_low("FINANCIAL"),
            description=_sv_low("Q4 earnings miss; guidance withdrawn"),
            severity=_sv_low("HIGH"),
        ),
        LitigationTimelineEvent(
            event_date=date(2025, 2, 10),
            event_type=_sv_low("LITIGATION"),
            description=_sv_low("Securities class action filed (S.D.N.Y.)"),
            severity=_sv_low("CRITICAL"),
        ),
    ]
    return LitigationLandscape(
        securities_class_actions=scas,
        sec_enforcement=enforcement,
        litigation_timeline_events=timeline_events,
        active_matter_count=_sv(1),
        historical_matter_count=_sv(1),
        litigation_summary=_sv_low(
            "Acme faces a newly-filed securities class action alleging violations of "
            "Section 10(b) related to Q4 2024 earnings miss and guidance withdrawal. "
            "The class period spans March 2024 through January 2025. Lead counsel is "
            "Bernstein Litowitz (Tier 1). A prior SCA settled for $28M in 2023. Three "
            "SEC comment letters on revenue recognition were received in 2024. The "
            "Citron Research short seller report in November 2024 preceded the stock "
            "decline that triggered the new lawsuit."
        ),
    )


def _build_scoring() -> ScoringResult:
    """Build comprehensive scoring result with all SECT7 outputs."""
    factor_scores = [
        FactorScore(factor_id="F1", factor_name="Prior Litigation", max_points=15, points_deducted=12.0,
                     evidence=["Active SCA filed Feb 2025", "Prior $28M settlement"], rules_triggered=["F1-001", "F1-003"]),
        FactorScore(factor_id="F2", factor_name="Stock Decline", max_points=15, points_deducted=11.0,
                     evidence=["39% decline from 52-week high", "3 single-day drops >8%"], rules_triggered=["F2-001", "F2-002"]),
        FactorScore(factor_id="F3", factor_name="Accounting Risk", max_points=12, points_deducted=8.5,
                     evidence=["Material weakness in rev rec", "Beneish M-Score grey zone"], rules_triggered=["F3-001"]),
        FactorScore(factor_id="F4", factor_name="M&A Activity", max_points=8, points_deducted=6.0,
                     evidence=["$2.1B DataSync acquisition", "Goodwill at 29% of assets"], rules_triggered=["F4-001"]),
        FactorScore(factor_id="F5", factor_name="Regulatory Exposure", max_points=10, points_deducted=3.5,
                     evidence=["3 SEC comment letters", "Revenue recognition focus"], rules_triggered=["F5-002"]),
        FactorScore(factor_id="F6", factor_name="Financial Distress", max_points=10, points_deducted=5.0,
                     evidence=["Altman Z grey zone 2.35", "Leverage 1.68x D/E"], rules_triggered=["F6-001"]),
        FactorScore(factor_id="F7", factor_name="Volatility", max_points=8, points_deducted=5.5,
                     evidence=["90-day vol 42.3%", "Beta elevated"], rules_triggered=["F7-001"]),
        FactorScore(factor_id="F8", factor_name="Short Interest", max_points=7, points_deducted=5.0,
                     evidence=["Short interest 14.2%", "Short seller report published"], rules_triggered=["F8-001", "F8-002"]),
        FactorScore(factor_id="F9", factor_name="Governance", max_points=8, points_deducted=4.5,
                     evidence=["CEO/Chair duality", "Say-on-pay 65%", "Activist position"], rules_triggered=["F9-001", "F9-003"]),
        FactorScore(factor_id="F10", factor_name="Officer Stability", max_points=7, points_deducted=3.5,
                     evidence=["CFO transition during integration", "CEO prior litigation"], rules_triggered=["F10-001"]),
    ]
    red_flags = [
        RedFlagResult(
            flag_id="CRF-1", flag_name="Active Securities Litigation",
            triggered=True, ceiling_applied=50, max_tier="WATCH",
            evidence=["Active SCA in S.D.N.Y. with Tier 1 counsel"],
        ),
        RedFlagResult(
            flag_id="CRF-4", flag_name="Material Weakness",
            triggered=True, ceiling_applied=60, max_tier="WRITE",
            evidence=["Material weakness in revenue recognition controls"],
        ),
        RedFlagResult(
            flag_id="CRF-2", flag_name="SEC Investigation",
            triggered=False,
        ),
    ]
    patterns = [
        PatternMatch(
            pattern_id="PATTERN.GUIDANCE.COLLAPSE",
            pattern_name="Guidance Collapse",
            detected=True,
            severity="HIGH",
            triggers_matched=["3 consecutive misses", "Guidance withdrawal", "Stock drop >15%"],
            score_impact={"F2": 3.0, "F7": 2.0},
        ),
        PatternMatch(
            pattern_id="PATTERN.INSIDER.INFORMED_TRADING",
            pattern_name="Informed Trading Signal",
            detected=True,
            severity="ELEVATED",
            triggers_matched=["Net selling >$40M", "Cluster events pre-drop"],
            score_impact={"F2": 1.5},
        ),
    ]
    risk_type = RiskTypeClassification(
        primary=RiskType.GUIDANCE_DEPENDENT,
        secondary=RiskType.TRANSFORMATION,
        evidence=[
            "3 consecutive earnings misses",
            "Guidance withdrawal post-Q4",
            "$2.1B acquisition integration ongoing",
        ],
    )
    allegation = AllegationMapping(
        theories=[
            TheoryExposure(theory=AllegationTheory.A_DISCLOSURE, exposure_level="HIGH",
                          findings=["Material weakness disclosure delay", "Goodwill impairment risk not disclosed"],
                          factor_sources=["F1", "F3", "F5"]),
            TheoryExposure(theory=AllegationTheory.B_GUIDANCE, exposure_level="HIGH",
                          findings=["3 consecutive misses while maintaining guidance", "Aggressive growth targets"],
                          factor_sources=["F2", "F5"]),
            TheoryExposure(theory=AllegationTheory.C_PRODUCT_OPS, exposure_level="MODERATE",
                          findings=["Integration execution risk"], factor_sources=["F7", "F8"]),
            TheoryExposure(theory=AllegationTheory.D_GOVERNANCE, exposure_level="MODERATE",
                          findings=["CEO/Chair duality", "Low say-on-pay"], factor_sources=["F9", "F10"]),
            TheoryExposure(theory=AllegationTheory.E_MA, exposure_level="HIGH",
                          findings=["$2.1B DataSync acquisition at premium", "Goodwill 29% of assets"],
                          factor_sources=["F4"]),
        ],
        primary_exposure=AllegationTheory.A_DISCLOSURE,
        concentration_analysis=(
            "Risk is concentrated in Theories A (Disclosure) and B (Guidance), "
            "consistent with the GUIDANCE_DEPENDENT risk profile. The recent "
            "acquisition adds significant Theory E (M&A) exposure."
        ),
    )
    claim_prob = ClaimProbability(
        band=ProbabilityBand.HIGH,
        range_low_pct=12.0,
        range_high_pct=18.0,
        industry_base_rate_pct=5.8,
        adjustment_narrative=(
            "Base rate of 5.8% (Tech sector) adjusted upward for: active SCA (+4%), "
            "material weakness (+1.5%), short seller report (+0.7%). Partially offset "
            "by Big 4 auditor and clawback policy."
        ),
    )
    severity = SeverityScenarios(
        market_cap=8_500_000_000.0,
        scenarios=[
            SeverityScenario(percentile=25, label="Favorable", settlement_estimate=8_000_000.0,
                            defense_cost_estimate=3_200_000.0, total_exposure=11_200_000.0),
            SeverityScenario(percentile=50, label="Median", settlement_estimate=22_000_000.0,
                            defense_cost_estimate=5_500_000.0, total_exposure=27_500_000.0),
            SeverityScenario(percentile=75, label="Adverse", settlement_estimate=55_000_000.0,
                            defense_cost_estimate=11_000_000.0, total_exposure=66_000_000.0),
            SeverityScenario(percentile=95, label="Catastrophic", settlement_estimate=140_000_000.0,
                            defense_cost_estimate=28_000_000.0, total_exposure=168_000_000.0),
        ],
    )
    tower = TowerRecommendation(
        recommended_position=TowerPosition.MID_EXCESS,
        minimum_attachment="$15M xs $15M",
        side_a_assessment="Side A exposure elevated due to active SCA naming individual officers",
        layers=[
            LayerAssessment(position=TowerPosition.PRIMARY, risk_assessment="Highest exposure; active SCA in early stages", premium_guidance="Rate increase 15-25%"),
            LayerAssessment(position=TowerPosition.LOW_EXCESS, risk_assessment="Moderate exposure; settlement likely within $25M", premium_guidance="Rate adequate +5-10%"),
            LayerAssessment(position=TowerPosition.MID_EXCESS, risk_assessment="Recommended entry; attachment above likely settlement median", premium_guidance="Rate adequate"),
            LayerAssessment(position=TowerPosition.HIGH_EXCESS, risk_assessment="Low attachment probability; monitoring required", premium_guidance="Rate adequate -5%"),
        ],
    )
    red_flag_summary = RedFlagSummary(
        items=[
            FlaggedItem(description="Active securities class action with Tier 1 counsel", source="Stanford SCAC",
                       severity=FlagSeverity.CRITICAL, scoring_impact="Ceiling: 50", trajectory="NEW"),
            FlaggedItem(description="Material weakness in revenue recognition controls", source="SEC 10-K, Item 9A",
                       severity=FlagSeverity.HIGH, scoring_impact="F3: +5 pts", trajectory="NEW"),
            FlaggedItem(description="Short interest at 14.2% with active short seller report", source="yfinance + Brave Search",
                       severity=FlagSeverity.HIGH, scoring_impact="F8: +5 pts", trajectory="WORSENING"),
            FlaggedItem(description="CEO/Chairman duality with prior litigation history", source="DEF 14A + web search",
                       severity=FlagSeverity.MODERATE, scoring_impact="F9: +2 pts", trajectory="STABLE"),
            FlaggedItem(description="Say-on-pay support below 70% threshold", source="DEF 14A, 2024-04-15",
                       severity=FlagSeverity.MODERATE, scoring_impact="F9: +1 pt", trajectory="STABLE"),
        ],
        critical_count=1,
        high_count=2,
        moderate_count=2,
        low_count=0,
    )
    total_risk = sum(f.points_deducted for f in factor_scores)
    composite = 100.0 - total_risk
    quality = min(composite, 50.0)  # CRF-1 ceiling at 50
    return ScoringResult(
        composite_score=composite,
        quality_score=quality,
        total_risk_points=total_risk,
        factor_scores=factor_scores,
        red_flags=red_flags,
        tier=TierClassification(
            tier=Tier.WATCH,
            score_range_low=26,
            score_range_high=50,
            action="Monitor closely; consider declining primary. Mid-excess may be acceptable.",
        ),
        patterns_detected=patterns,
        risk_type=risk_type,
        allegation_mapping=allegation,
        claim_probability=claim_prob,
        severity_scenarios=severity,
        tower_recommendation=tower,
        red_flag_summary=red_flag_summary,
        calibration_notes=[
            "Allegation theory mapping requires expert validation",
            "Severity scenarios based on historical averages; adjust for jurisdiction",
            "Inherent risk baseline uses sector-level data; company-specific adjustment needed",
        ],
        binding_ceiling_id="CRF-1",
    )


def _build_executive_summary() -> ExecutiveSummary:
    """Build executive summary with all sub-components."""
    snapshot = CompanySnapshot(
        ticker="ACME",
        company_name="Acme Technology Holdings Inc.",
        market_cap=_sv_med(8_500_000_000.0),
        revenue=_sv(3_300_000_000.0),
        employee_count=_sv(12500),
        industry="Prepackaged Software",
        sic_code="7372",
        exchange="NASDAQ",
    )
    inherent_risk = InherentRiskBaseline(
        sector_base_rate_pct=5.8,
        market_cap_multiplier=1.35,
        market_cap_adjusted_rate_pct=7.83,
        score_multiplier=1.8,
        company_adjusted_rate_pct=14.1,
        severity_range_25th=8.0,
        severity_range_50th=22.0,
        severity_range_75th=55.0,
        severity_range_95th=140.0,
        sector_name="Technology",
        market_cap_tier="LARGE",
        methodology_note="NEEDS CALIBRATION -- multiplicative model: base * cap * score",
    )
    key_findings = KeyFindings(
        negatives=[
            KeyFinding(
                evidence_narrative="Active securities class action filed February 2025 with Tier 1 lead counsel (Bernstein Litowitz). Prior SCA settled for $28M.",
                section_origin="SECT6",
                scoring_impact="F1: +12 points; CRF-1 ceiling 50",
                theory_mapping="Theory A: Disclosure + Theory B: Guidance",
                ranking_score=0.95,
            ),
            KeyFinding(
                evidence_narrative="Stock declined 39% from 52-week high with 3 single-day drops exceeding 8%. Post-earnings drop of 15.2% on guidance withdrawal.",
                section_origin="SECT4",
                scoring_impact="F2: +11 points",
                theory_mapping="Theory A: Disclosure",
                ranking_score=0.90,
            ),
            KeyFinding(
                evidence_narrative="Material weakness in revenue recognition controls related to DataSync acquisition integration. 3 SEC comment letters on revenue recognition.",
                section_origin="SECT3",
                scoring_impact="F3: +8.5 points; CRF-4 ceiling 60",
                theory_mapping="Theory A: Disclosure",
                ranking_score=0.85,
            ),
            KeyFinding(
                evidence_narrative="$2.1B DataSync acquisition with goodwill at 29% of total assets ($4.1B). Significant impairment risk if integration targets missed.",
                section_origin="SECT3",
                scoring_impact="F4: +6 points",
                theory_mapping="Theory E: M&A",
                ranking_score=0.80,
            ),
            KeyFinding(
                evidence_narrative="Short interest at 14.2% of float with active Citron Research short seller report. Days to cover: 6.8.",
                section_origin="SECT4",
                scoring_impact="F8: +5 points",
                theory_mapping="Theory A: Disclosure",
                ranking_score=0.75,
            ),
        ],
        positives=[
            KeyFinding(
                evidence_narrative="Big 4 auditor (Ernst & Young) with 8-year tenure provides strong audit oversight.",
                section_origin="SECT3",
                scoring_impact="Mitigates F3 by -2 points",
                theory_mapping="Defense: Audit Quality",
                ranking_score=0.70,
            ),
            KeyFinding(
                evidence_narrative="Revenue growth of 17.9% YoY demonstrates strong underlying business momentum despite margin pressure.",
                section_origin="SECT3",
                scoring_impact="Mitigates F6 by -1 point",
                theory_mapping="Defense: Business Viability",
                ranking_score=0.60,
            ),
            KeyFinding(
                evidence_narrative="Clawback policy in place per Dodd-Frank compliance. 73% board independence ratio.",
                section_origin="SECT5",
                scoring_impact="Mitigates F9 by -1 point",
                theory_mapping="Defense: Governance Structure",
                ranking_score=0.55,
            ),
        ],
    )
    thesis = UnderwritingThesis(
        narrative=(
            "Acme Technology presents a WATCH-tier risk profile driven by an active securities "
            "class action with Tier 1 counsel, material weakness in revenue recognition controls, "
            "and a 39% stock decline from highs. The GUIDANCE_DEPENDENT risk type is confirmed by "
            "3 consecutive earnings misses culminating in guidance withdrawal. The $2.1B DataSync "
            "acquisition adds integration risk and goodwill impairment exposure. Quality score of "
            "35.5/100 is capped at 50 by CRF-1 (active litigation). Recommend mid-excess position "
            "at minimum; primary and low-excess carry elevated exposure."
        ),
        risk_type_label="GUIDANCE_DEPENDENT / TRANSFORMATION",
        top_factor_summary="F1 (12.0), F2 (11.0), F3 (8.5) -- Prior Litigation, Stock Decline, Accounting Risk",
    )
    return ExecutiveSummary(
        snapshot=snapshot,
        inherent_risk=inherent_risk,
        key_findings=key_findings,
        thesis=thesis,
    )


def _build_acquired_data() -> AcquiredData:
    """Build acquired data with price history for stock charts."""
    import random

    random.seed(42)  # Reproducible

    # Generate 1Y daily prices (declining trajectory)
    prices_1y: list[dict[str, Any]] = []
    base_price = 112.0
    for i in range(252):
        day = datetime(2024, 6, 15, tzinfo=UTC)
        from datetime import timedelta

        d = day + timedelta(days=i)
        # General decline with noise
        trend = -0.15 * (i / 252)  # -15% trend
        noise = random.gauss(0, 0.02)
        # Add specific events
        event_shock = 0.0
        if 105 <= i <= 106:  # ~Nov 2024 short seller report
            event_shock = -0.08
        if 150 <= i <= 155:  # ~Jan 2025 earnings miss
            event_shock = -0.12
        factor = 1.0 + trend + noise + event_shock
        price = base_price * max(factor, 0.4)
        prices_1y.append({"date": d.strftime("%Y-%m-%d"), "close": round(price, 2)})

    # ETF prices (moderate growth)
    etf_1y: list[dict[str, Any]] = []
    etf_base = 200.0
    for i in range(252):
        day = datetime(2024, 6, 15, tzinfo=UTC)
        from datetime import timedelta

        d = day + timedelta(days=i)
        trend = 0.12 * (i / 252)  # +12% trend
        noise = random.gauss(0, 0.008)
        price = etf_base * (1.0 + trend + noise)
        etf_1y.append({"date": d.strftime("%Y-%m-%d"), "close": round(price, 2)})

    return AcquiredData(
        market_data={
            "price_history": {
                "1Y": prices_1y,
                "5Y": prices_1y,  # Reuse for 5Y (simplified)
            },
            "sector_etf": "XLK",
            "etf_history": {
                "1Y": etf_1y,
                "5Y": etf_1y,
            },
        },
    )


def build_sample_state() -> AnalysisState:
    """Build a comprehensive sample AnalysisState for document generation."""
    state = AnalysisState(
        ticker="ACME",
        company=_build_company(),
        acquired_data=_build_acquired_data(),
        extracted=ExtractedData(
            financials=_build_financials(),
            market=_build_market(),
            governance=_build_governance(),
            litigation=_build_litigation(),
        ),
        scoring=_build_scoring(),
        executive_summary=_build_executive_summary(),
    )
    # Mark all stages completed
    for stage_name in ["resolve", "acquire", "extract", "analyze", "score", "benchmark"]:
        state.mark_stage_running(stage_name)
        state.mark_stage_completed(stage_name)
    return state


def main() -> None:
    """Generate the sample Word document."""
    configure_matplotlib_defaults()
    ds = DesignSystem()
    state = build_sample_state()

    output_dir = Path(__file__).resolve().parent.parent / "output" / "SAMPLE"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "SAMPLE_worksheet.docx"

    print(f"Generating sample document for {state.ticker}...")
    result = render_word_document(state, output_path, ds)
    print(f"Word document saved: {result}")
    print(f"  Size: {result.stat().st_size:,} bytes")

    # Also generate Markdown
    try:
        from do_uw.stages.render.md_renderer import render_markdown

        md_path = output_dir / "SAMPLE_worksheet.md"
        render_markdown(state, md_path, ds)
        print(f"Markdown saved: {md_path}")
    except Exception as e:
        print(f"Markdown generation failed (non-fatal): {e}")

    # Also generate PDF
    try:
        from do_uw.stages.render.pdf_renderer import render_pdf

        pdf_path = output_dir / "SAMPLE_worksheet.pdf"
        render_pdf(state, pdf_path, ds)
        print(f"PDF saved: {pdf_path}")
    except Exception as e:
        print(f"PDF generation failed (non-fatal): {e}")

    print("\nDone. Open SAMPLE_worksheet.docx in Word to review.")


if __name__ == "__main__":
    main()
