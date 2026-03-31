"""Tests for three-tier section density assessments.

Covers CLEAN, ELEVATED, CRITICAL scenarios for governance, litigation,
financial, and market sections, plus per-subsection overrides.
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.density import DensityLevel, SectionDensity
from do_uw.models.financials import (
    AuditProfile,
    DistressIndicators,
    DistressResult,
    DistressZone,
    ExtractedFinancials,
)
from do_uw.models.governance import BoardProfile, GovernanceData
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    LeadershipForensicProfile,
    LeadershipStability,
    OwnershipAnalysis,
)
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
    SECEnforcementPipeline,
)
from do_uw.models.market import MarketSignals, ShortInterestProfile
from do_uw.models.market_events import (
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    InsiderClusterEvent,
    InsiderTradingAnalysis,
    StockDropAnalysis,
    StockDropEvent,
)
from do_uw.models.state import (
    AnalysisResults,
    AnalysisState,
    ExtractedData,
)
from do_uw.stages.analyze.section_assessments import compute_section_assessments


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv(val: object, confidence: str = "HIGH") -> SourcedValue:  # type: ignore[type-arg]
    """Shorthand for creating SourcedValue."""
    return SourcedValue(
        value=val,
        source="test",
        confidence=Confidence(confidence),
        as_of=datetime.now(tz=UTC),
    )


def _clean_state() -> AnalysisState:
    """Build a fully clean state (all sections CLEAN)."""
    return AnalysisState(
        ticker="CLEAN",
        analysis=AnalysisResults(),
        extracted=ExtractedData(
            financials=ExtractedFinancials(
                distress=DistressIndicators(
                    altman_z_score=DistressResult(score=3.5, zone=DistressZone.SAFE),
                    beneish_m_score=DistressResult(score=-2.5, zone=DistressZone.SAFE),
                    ohlson_o_score=DistressResult(score=0.1, zone=DistressZone.SAFE),
                    piotroski_f_score=DistressResult(score=7.0, zone=DistressZone.SAFE),
                ),
                audit=AuditProfile(
                    auditor_name=_sv("Deloitte"),
                    going_concern=_sv(False),
                ),
            ),
            market=MarketSignals(
                short_interest=ShortInterestProfile(
                    short_pct_float=_sv(2.0),
                ),
            ),
            governance=GovernanceData(
                board=BoardProfile(
                    independence_ratio=_sv(0.85),
                    ceo_chair_duality=_sv(False),
                    overboarded_count=_sv(0),
                ),
                ownership=OwnershipAnalysis(),
                leadership=LeadershipStability(),
            ),
            litigation=LitigationLandscape(),
        ),
    )


# ---------------------------------------------------------------------------
# CLEAN scenario
# ---------------------------------------------------------------------------


class TestCleanScenario:
    """All sections should be CLEAN when no issues exist."""

    def test_all_sections_clean(self) -> None:
        state = _clean_state()
        compute_section_assessments(state)

        assert state.analysis is not None
        densities = state.analysis.section_densities

        assert densities["governance"].level == DensityLevel.CLEAN
        assert densities["litigation"].level == DensityLevel.CLEAN
        assert densities["financial"].level == DensityLevel.CLEAN
        assert densities["market"].level == DensityLevel.CLEAN

    def test_clean_governance_subsections(self) -> None:
        state = _clean_state()
        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.subsection_overrides["4.1_people_risk"] == DensityLevel.CLEAN
        assert gov.subsection_overrides["4.2_structural_governance"] == DensityLevel.CLEAN
        assert gov.subsection_overrides["4.3_transparency"] == DensityLevel.CLEAN
        assert gov.subsection_overrides["4.4_activist"] == DensityLevel.CLEAN


# ---------------------------------------------------------------------------
# ELEVATED governance (CEO/Chair duality but otherwise fine)
# ---------------------------------------------------------------------------


class TestElevatedGovernance:
    """Governance ELEVATED when CEO/Chair duality but no critical flags."""

    def test_ceo_chair_duality_elevated(self) -> None:
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None
        state.extracted.governance.board.ceo_chair_duality = _sv(True)

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.level == DensityLevel.ELEVATED
        assert "CEO/Chair duality" in gov.concerns

    def test_overboarded_directors_elevated(self) -> None:
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None
        state.extracted.governance.board.overboarded_count = _sv(2)

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.level == DensityLevel.ELEVATED
        assert gov.subsection_overrides["4.1_people_risk"] == DensityLevel.ELEVATED

    def test_low_independence_elevated(self) -> None:
        """Independence between 50-75% is ELEVATED, not CRITICAL."""
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None
        state.extracted.governance.board.independence_ratio = _sv(0.60)

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.level == DensityLevel.ELEVATED
        assert gov.subsection_overrides["4.2_structural_governance"] == DensityLevel.ELEVATED


# ---------------------------------------------------------------------------
# CRITICAL governance (executive prior litigation)
# ---------------------------------------------------------------------------


class TestCriticalGovernance:
    """Governance CRITICAL when executives have prior litigation."""

    def test_exec_prior_litigation_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None
        state.extracted.governance.leadership = LeadershipStability(
            executives=[
                LeadershipForensicProfile(
                    name=_sv("John Doe"),
                    title=_sv("CEO"),
                    prior_litigation=[_sv("Prior SCA at Acme Corp")],
                ),
            ],
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.level == DensityLevel.CRITICAL
        assert gov.subsection_overrides["4.1_people_risk"] == DensityLevel.CRITICAL
        assert any("prior litigation" in e for e in gov.critical_evidence)

    def test_very_low_independence_critical(self) -> None:
        """Independence below 50% is CRITICAL."""
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None
        state.extracted.governance.board.independence_ratio = _sv(0.40)

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.subsection_overrides["4.2_structural_governance"] == DensityLevel.CRITICAL

    def test_activist_presence_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None
        state.extracted.governance.ownership = OwnershipAnalysis(
            known_activists=[_sv("Carl Icahn")],
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.subsection_overrides["4.4_activist"] == DensityLevel.CRITICAL


# ---------------------------------------------------------------------------
# CRITICAL litigation (active SCA + enforcement action)
# ---------------------------------------------------------------------------


class TestCriticalLitigation:
    """Litigation CRITICAL with active cases and enforcement."""

    def test_active_sca_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.litigation = LitigationLandscape(
            securities_class_actions=[
                CaseDetail(
                    case_name=_sv("In re Test Corp"),
                    status=_sv("ACTIVE"),
                ),
            ],
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        lit = state.analysis.section_densities["litigation"]
        assert lit.level == DensityLevel.CRITICAL
        assert any("active" in e.lower() for e in lit.critical_evidence)

    def test_enforcement_action_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.litigation = LitigationLandscape(
            sec_enforcement=SECEnforcementPipeline(
                highest_confirmed_stage=_sv("ENFORCEMENT_ACTION"),
                actions=[_sv({"type": "cease_desist", "date": "2025-01-01"})],
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        lit = state.analysis.section_densities["litigation"]
        assert lit.level == DensityLevel.CRITICAL

    def test_resolved_sca_elevated(self) -> None:
        """Resolved SCAs are ELEVATED, not CRITICAL."""
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.litigation = LitigationLandscape(
            securities_class_actions=[
                CaseDetail(
                    case_name=_sv("In re Old Corp"),
                    status=_sv("SETTLED"),
                ),
            ],
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        lit = state.analysis.section_densities["litigation"]
        assert lit.level == DensityLevel.ELEVATED
        assert any("resolved" in c.lower() for c in lit.concerns)

    def test_no_litigation_clean(self) -> None:
        """Empty litigation data is CLEAN."""
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.litigation = LitigationLandscape()

        compute_section_assessments(state)

        assert state.analysis is not None
        lit = state.analysis.section_densities["litigation"]
        assert lit.level == DensityLevel.CLEAN


# ---------------------------------------------------------------------------
# CRITICAL financial (distress zone + going concern)
# ---------------------------------------------------------------------------


class TestCriticalFinancial:
    """Financial CRITICAL with distress and going concern."""

    def test_distress_zone_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None and state.extracted.financials is not None
        state.extracted.financials.distress = DistressIndicators(
            altman_z_score=DistressResult(score=1.0, zone=DistressZone.DISTRESS),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        fin = state.analysis.section_densities["financial"]
        assert fin.level == DensityLevel.CRITICAL
        assert any("DISTRESS" in e for e in fin.critical_evidence)

    def test_going_concern_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None and state.extracted.financials is not None
        state.extracted.financials.audit = AuditProfile(
            going_concern=_sv(True),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        fin = state.analysis.section_densities["financial"]
        assert fin.level == DensityLevel.CRITICAL
        assert any("Going concern" in e for e in fin.critical_evidence)

    def test_grey_zone_elevated(self) -> None:
        """Grey zone distress model is ELEVATED, not CRITICAL."""
        state = _clean_state()
        assert state.extracted is not None and state.extracted.financials is not None
        state.extracted.financials.distress = DistressIndicators(
            altman_z_score=DistressResult(score=2.5, zone=DistressZone.GREY),
            beneish_m_score=DistressResult(score=-2.0, zone=DistressZone.SAFE),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        fin = state.analysis.section_densities["financial"]
        assert fin.level == DensityLevel.ELEVATED
        assert any("GREY" in c for c in fin.concerns)

    def test_material_weakness_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None and state.extracted.financials is not None
        state.extracted.financials.audit = AuditProfile(
            material_weaknesses=[_sv("IT general controls")],
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        fin = state.analysis.section_densities["financial"]
        assert fin.level == DensityLevel.CRITICAL


# ---------------------------------------------------------------------------
# Market density scenarios
# ---------------------------------------------------------------------------


class TestMarketDensity:
    """Market density scenarios."""

    def test_severe_drop_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.market = MarketSignals(
            stock_drops=StockDropAnalysis(
                single_day_drops=[
                    StockDropEvent(drop_pct=_sv(-15.0)),
                ],
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        mkt = state.analysis.section_densities["market"]
        assert mkt.level == DensityLevel.CRITICAL

    def test_high_short_interest_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.market = MarketSignals(
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(12.0),
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        mkt = state.analysis.section_densities["market"]
        assert mkt.level == DensityLevel.CRITICAL

    def test_moderate_short_interest_elevated(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.market = MarketSignals(
            short_interest=ShortInterestProfile(
                short_pct_float=_sv(7.0),
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        mkt = state.analysis.section_densities["market"]
        assert mkt.level == DensityLevel.ELEVATED
        assert any("7.0%" in c for c in mkt.concerns)

    def test_moderate_drops_elevated(self) -> None:
        """Drops 5-10% are ELEVATED, not CRITICAL."""
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.market = MarketSignals(
            stock_drops=StockDropAnalysis(
                single_day_drops=[
                    StockDropEvent(drop_pct=_sv(-7.5)),
                ],
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        mkt = state.analysis.section_densities["market"]
        assert mkt.level == DensityLevel.ELEVATED

    def test_big_earnings_miss_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.market = MarketSignals(
            earnings_guidance=EarningsGuidanceAnalysis(
                quarters=[
                    EarningsQuarterRecord(
                        quarter="Q1 2025",
                        result="MISS",
                        miss_magnitude_pct=_sv(-15.0),
                    ),
                ],
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        mkt = state.analysis.section_densities["market"]
        assert mkt.level == DensityLevel.CRITICAL

    def test_insider_cluster_elevated(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.market = MarketSignals(
            insider_analysis=InsiderTradingAnalysis(
                cluster_events=[
                    InsiderClusterEvent(insider_count=3),
                ],
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        mkt = state.analysis.section_densities["market"]
        assert mkt.level == DensityLevel.ELEVATED

    def test_many_insider_clusters_critical(self) -> None:
        state = _clean_state()
        assert state.extracted is not None
        state.extracted.market = MarketSignals(
            insider_analysis=InsiderTradingAnalysis(
                cluster_events=[
                    InsiderClusterEvent(insider_count=3),
                    InsiderClusterEvent(insider_count=4),
                    InsiderClusterEvent(insider_count=5),
                ],
            ),
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        mkt = state.analysis.section_densities["market"]
        assert mkt.level == DensityLevel.CRITICAL


# ---------------------------------------------------------------------------
# Per-subsection overrides
# ---------------------------------------------------------------------------


class TestSubsectionOverrides:
    """Governance subsection overrides work independently."""

    def test_mixed_subsection_overrides(self) -> None:
        """People CRITICAL but structural CLEAN -> overall CRITICAL."""
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None

        # People risk: executive with prior litigation
        state.extracted.governance.leadership = LeadershipStability(
            executives=[
                LeadershipForensicProfile(
                    name=_sv("Jane Smith"),
                    title=_sv("CFO"),
                    prior_litigation=[_sv("Prior fraud case")],
                ),
            ],
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.subsection_overrides["4.1_people_risk"] == DensityLevel.CRITICAL
        assert gov.subsection_overrides["4.2_structural_governance"] == DensityLevel.CLEAN
        assert gov.level == DensityLevel.CRITICAL

    def test_only_transparency_elevated(self) -> None:
        """Only transparency issues, rest CLEAN -> overall ELEVATED."""
        state = _clean_state()
        assert state.extracted is not None and state.extracted.governance is not None

        # Add restatements via audit
        assert state.extracted.financials is not None
        state.extracted.financials.audit = AuditProfile(
            restatements=[_sv({"type": "Revenue recognition", "impact": "Material"})],
        )

        compute_section_assessments(state)

        assert state.analysis is not None
        gov = state.analysis.section_densities["governance"]
        assert gov.subsection_overrides["4.3_transparency"] == DensityLevel.CRITICAL
        assert gov.subsection_overrides["4.1_people_risk"] == DensityLevel.CLEAN
        assert gov.level == DensityLevel.CRITICAL


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_no_analysis_noop(self) -> None:
        state = AnalysisState(ticker="NOOP")
        compute_section_assessments(state)
        assert state.analysis is None

    def test_no_extracted_data(self) -> None:
        state = AnalysisState(ticker="EMPTY", analysis=AnalysisResults())
        compute_section_assessments(state)

        assert state.analysis is not None
        # Governance and financial default to ELEVATED (unknown risk)
        assert state.analysis.section_densities["governance"].level == DensityLevel.ELEVATED
        assert state.analysis.section_densities["financial"].level == DensityLevel.ELEVATED
        # Litigation with no data = CLEAN (no evidence of issues)
        assert state.analysis.section_densities["litigation"].level == DensityLevel.CLEAN
        # Market without data = ELEVATED (unknown)
        assert state.analysis.section_densities["market"].level == DensityLevel.ELEVATED

    def test_section_density_model_defaults(self) -> None:
        """SectionDensity defaults are sane."""
        sd = SectionDensity()
        assert sd.level == DensityLevel.CLEAN
        assert sd.subsection_overrides == {}
        assert sd.concerns == []
        assert sd.critical_evidence == []
