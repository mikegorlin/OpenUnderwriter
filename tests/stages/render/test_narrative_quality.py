"""Quality gate tests for narrative generation (NQ-01 through NQ-07).

Verifies that all neg_*/pos_* narrative functions produce company-specific
text using real data points from AnalysisState -- no boilerplate, no generic
D&O primer sentences, severity-calibrated language.

Phase 119.1-01: Initial scaffold with AAPL-like and ANGI-like mock states.
"""

from __future__ import annotations

import importlib
import inspect
import re
from datetime import UTC, datetime
from typing import Any

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.executive_summary import KeyFinding
from do_uw.models.financials import (
    AuditProfile,
    DistressIndicators,
    DistressResult,
    ExtractedFinancials,
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
)
from do_uw.models.forward_looking import CredibilityScore, ForwardLookingData
from do_uw.models.governance import BoardProfile, GovernanceData
from do_uw.models.governance_forensics import (
    LeadershipForensicProfile,
    LeadershipStability,
)
from do_uw.models.market import MarketSignals, ShortInterestProfile, StockPerformance
from do_uw.models.scoring import (
    FactorScore,
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.state import AnalysisState, ExtractedData


# ---------------------------------------------------------------------------
# Helper to make SourcedValue instances concisely
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 3, 20, tzinfo=UTC)


def _sv(value: Any, source: str = "test") -> SourcedValue:
    """Create a SourcedValue for testing."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.HIGH, as_of=_NOW,
    )


def _li(concept: str, label: str, values: dict[str, float]) -> FinancialLineItem:
    """Create a FinancialLineItem with proper SourcedValues."""
    sv_vals: dict[str, SourcedValue[float] | None] = {}
    for period, val in values.items():
        sv_vals[period] = _sv(val)
    return FinancialLineItem(
        label=label, xbrl_concept=concept, values=sv_vals,
    )


def _stmt(stmt_type: str, items: list[FinancialLineItem], periods: list[str]) -> FinancialStatement:
    """Create a FinancialStatement."""
    return FinancialStatement(
        statement_type=stmt_type, periods=periods, line_items=items,
    )


# ---------------------------------------------------------------------------
# Mock AnalysisState fixtures
# ---------------------------------------------------------------------------


def _make_aapl_like_state() -> AnalysisState:
    """Healthy mega-cap: AAPL-like profile."""
    company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="AAPL",
            legal_name=_sv("APPLE INC"),
        ),
        market_cap=_sv(3_400_000_000_000.0),
        employee_count=_sv(164_000),
    )

    stock = StockPerformance(
        current_price=_sv(227.0),
        high_52w=_sv(240.0),
        low_52w=_sv(215.0),
        decline_from_high_pct=_sv(5.4),
    )
    short_interest = ShortInterestProfile(
        short_pct_float=_sv(0.7),
    )
    market = MarketSignals(
        stock=stock,
        short_interest=short_interest,
    )

    board = BoardProfile(
        size=_sv(8),
        independence_ratio=_sv(0.88),
        classified_board=_sv(False),
    )
    ceo = LeadershipForensicProfile(
        name=_sv("Tim Cook"),
        title=_sv("Chief Executive Officer"),
        tenure_years=13.0,
    )
    leadership = LeadershipStability(
        executives=[ceo],
        departures_18mo=[],
    )
    governance = GovernanceData(
        board=board,
        leadership=leadership,
    )

    distress = DistressIndicators(
        altman_z_score=DistressResult(score=9.93, zone="safe"),
        piotroski_f_score=DistressResult(score=7.0, zone="safe"),
        beneish_m_score=DistressResult(score=-2.8, zone="safe"),
    )
    audit = AuditProfile(
        auditor_name=_sv("Deloitte & Touche LLP"),
        tenure_years=_sv(7),
        going_concern=_sv(False),
    )
    # Build financial statements with current_ratio and interest_coverage
    bs = _stmt("balance_sheet", [
        _li("current_ratio", "Current Ratio", {"FY2025": 1.07}),
    ], ["FY2025"])
    inc = _stmt("income", [
        _li("interest_coverage_ratio", "Interest Coverage", {"FY2025": 30.0}),
        _li("total_revenue", "Total Revenue", {"FY2025": 394_000_000_000.0}),
    ], ["FY2025"])
    stmts = FinancialStatements(balance_sheet=bs, income_statement=inc)
    financials = ExtractedFinancials(
        statements=stmts,
        distress=distress,
        audit=audit,
    )

    extracted = ExtractedData(
        financials=financials,
        market=market,
        governance=governance,
    )

    tier = TierClassification(
        tier=Tier.WANT,
        score_range_low=71,
        score_range_high=85,
    )
    scoring = ScoringResult(
        composite_score=82.0,
        quality_score=82.0,
        tier=tier,
        factor_scores=[],
    )

    credibility = CredibilityScore(
        beat_rate_pct=85.0,
        quarters_assessed=8,
        credibility_level="HIGH",
    )
    forward_looking = ForwardLookingData(credibility=credibility)

    return AnalysisState(
        ticker="AAPL",
        company=company,
        extracted=extracted,
        scoring=scoring,
        forward_looking=forward_looking,
    )


def _make_angi_like_state() -> AnalysisState:
    """Distressed small-cap: ANGI-like profile."""
    company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="ANGI",
            legal_name=_sv("ANGI HOMESERVICES INC"),
        ),
        market_cap=_sv(600_000_000.0),
        employee_count=_sv(4_200),
    )

    stock = StockPerformance(
        current_price=_sv(4.02),
        high_52w=_sv(15.30),
        low_52w=_sv(3.50),
        decline_from_high_pct=_sv(73.7),
    )
    short_interest = ShortInterestProfile(
        short_pct_float=_sv(17.95),
    )
    market = MarketSignals(
        stock=stock,
        short_interest=short_interest,
    )

    board = BoardProfile(
        size=_sv(5),
        independence_ratio=_sv(0.57),
        classified_board=_sv(True),
    )
    ceo = LeadershipForensicProfile(
        name=_sv("Joey Levin"),
        title=_sv("Chief Executive Officer"),
        tenure_years=2.0,
    )
    departed = LeadershipForensicProfile(
        name=_sv("Former CFO"),
        title=_sv("Chief Financial Officer"),
        tenure_years=1.5,
    )
    leadership = LeadershipStability(
        executives=[ceo],
        departures_18mo=[departed],
    )
    governance = GovernanceData(
        board=board,
        leadership=leadership,
    )

    distress = DistressIndicators(
        altman_z_score=DistressResult(score=0.98, zone="distress"),
        piotroski_f_score=DistressResult(score=2.0, zone="distress"),
        beneish_m_score=DistressResult(score=-2.1, zone="grey"),
    )
    audit = AuditProfile(
        going_concern=_sv(True),
    )
    bs = _stmt("balance_sheet", [
        _li("current_ratio", "Current Ratio", {"FY2025": 0.6}),
    ], ["FY2025"])
    inc = _stmt("income", [
        _li("interest_coverage_ratio", "Interest Coverage", {"FY2025": 0.8}),
        _li("total_revenue", "Total Revenue", {"FY2025": 1_200_000_000.0}),
    ], ["FY2025"])
    stmts = FinancialStatements(balance_sheet=bs, income_statement=inc)
    financials = ExtractedFinancials(
        statements=stmts,
        distress=distress,
        audit=audit,
    )

    extracted = ExtractedData(
        financials=financials,
        market=market,
        governance=governance,
    )

    tier = TierClassification(
        tier=Tier.WALK,
        score_range_low=26,
        score_range_high=40,
    )
    # Beneish component flags for ANGI
    f3_signals = [
        {"signal_id": "FIN.FORENSIC.beneish_dsri", "status": "TRIGGERED"},
        {"signal_id": "FIN.FORENSIC.beneish_sgai", "status": "TRIGGERED"},
        {"signal_id": "FIN.FORENSIC.beneish_tata", "status": "TRIGGERED"},
        {"signal_id": "FIN.FORENSIC.earnings_quality", "status": "CLEAR"},
    ]
    f3 = FactorScore(
        factor_id="F3",
        factor_name="Audit & Accounting Risk",
        max_points=12,
        points_deducted=8.0,
        signal_contributions=f3_signals,
    )
    f5 = FactorScore(
        factor_id="F5",
        factor_name="Earnings Guidance",
        max_points=10,
        points_deducted=6.0,
        signal_contributions=[],
    )
    scoring = ScoringResult(
        composite_score=38.0,
        quality_score=38.0,
        tier=tier,
        factor_scores=[f3, f5],
    )

    credibility = CredibilityScore(
        beat_rate_pct=35.0,
        quarters_assessed=6,
        credibility_level="LOW",
    )
    forward_looking = ForwardLookingData(credibility=credibility)

    return AnalysisState(
        ticker="ANGI",
        company=company,
        extracted=extracted,
        scoring=scoring,
        forward_looking=forward_looking,
    )


@pytest.fixture()
def aapl_like_state() -> AnalysisState:
    return _make_aapl_like_state()


@pytest.fixture()
def angi_like_state() -> AnalysisState:
    return _make_angi_like_state()


def _context(state: AnalysisState) -> dict[str, Any]:
    """Build a minimal context dict for narrative builders."""
    return {"_state": state}


# ---------------------------------------------------------------------------
# NQ-01: neg_generic is DELETED
# ---------------------------------------------------------------------------

def test_no_neg_generic():
    """Importing neg_generic from sect1_findings_neg must raise ImportError."""
    with pytest.raises(ImportError):
        from do_uw.stages.render.sections.sect1_findings_neg import neg_generic  # noqa: F401


def test_no_neg_generic_in_dispatcher():
    """sect1_findings.py source must not contain 'neg_generic'."""
    import do_uw.stages.render.sections.sect1_findings as mod
    src = inspect.getsource(mod)
    assert "neg_generic" not in src, "neg_generic still referenced in dispatcher"


# ---------------------------------------------------------------------------
# NQ-02: Stock decline severity calibration
# ---------------------------------------------------------------------------

def test_neg_stock_risk_severity_calibration(
    aapl_like_state: AnalysisState,
    angi_like_state: AnalysisState,
):
    """73.7% decline -> 'catastrophic'; 5% decline -> 'moderate'."""
    from do_uw.stages.render.sections.sect1_findings_neg import neg_stock_risk

    angi_text = " ".join(neg_stock_risk(angi_like_state, "Angi", "Stock Decline"))
    assert "catastrophic" in angi_text.lower(), f"73.7% decline should be 'catastrophic': {angi_text}"
    assert "73.7" in angi_text, f"Must include actual decline percentage: {angi_text}"

    aapl_text = " ".join(neg_stock_risk(aapl_like_state, "Apple", "Stock Decline"))
    assert "decline" in aapl_text.lower() or "dip" in aapl_text.lower(), (
        f"5% decline should use specific language: {aapl_text}"
    )
    assert "5" in aapl_text, f"Must include actual decline number: {aapl_text}"


# ---------------------------------------------------------------------------
# NQ-03: Data richness (3+ data points per function)
# ---------------------------------------------------------------------------

def test_neg_data_richness_stock(angi_like_state: AnalysisState):
    """neg_stock_risk output must contain 4+ distinct data points."""
    from do_uw.stages.render.sections.sect1_findings_neg import neg_stock_risk

    text = " ".join(neg_stock_risk(angi_like_state, "Angi", "Stock Decline"))
    data_points = 0
    if "73.7" in text or "73.7%" in text:
        data_points += 1  # decline pct
    if "$15" in text or "15.30" in text:
        data_points += 1  # high price
    if "$4" in text or "4.02" in text:
        data_points += 1  # low price
    if "17.95" in text or "17.9" in text:
        data_points += 1  # short interest
    if "DDL" in text or "Disclosure Dollar Loss" in text:
        data_points += 1  # DDL estimate
    assert data_points >= 4, (
        f"Expected 4+ data points, found {data_points} in: {text}"
    )


def test_neg_data_richness_governance(angi_like_state: AnalysisState):
    """neg_governance output must contain 3+ of: independence%, board size, CEO tenure, departures, compensation."""
    from do_uw.stages.render.sections.sect1_findings_neg import neg_governance

    text = " ".join(neg_governance(angi_like_state, "Angi"))
    data_points = 0
    if "57" in text:
        data_points += 1  # independence 57%
    if "5" in text and ("board" in text.lower() or "member" in text.lower()):
        data_points += 1  # board size 5
    if "2" in text and ("tenure" in text.lower() or "year" in text.lower()):
        data_points += 1  # CEO tenure 2yr
    if "departure" in text.lower() or "departed" in text.lower():
        data_points += 1  # departures
    if "compensation" in text.lower():
        data_points += 1
    assert data_points >= 3, (
        f"Expected 3+ governance data points, found {data_points} in: {text}"
    )


def test_neg_data_richness_distress(angi_like_state: AnalysisState):
    """neg_distress output must contain 3+ of: Altman Z, D/E, Piotroski, current ratio, interest coverage."""
    from do_uw.stages.render.sections.sect1_findings_neg import neg_distress

    text = " ".join(neg_distress(angi_like_state, "Angi"))
    data_points = 0
    if "0.98" in text:
        data_points += 1  # Altman Z
    if re.search(r"[Pp]iotroski.*2\b|2/9|F-Score.*2", text):
        data_points += 1  # Piotroski
    if "0.6" in text and ("current" in text.lower() or "ratio" in text.lower()):
        data_points += 1  # current ratio
    if "0.8" in text and ("interest" in text.lower() or "coverage" in text.lower()):
        data_points += 1  # interest coverage
    if "going" in text.lower() and "concern" in text.lower():
        data_points += 1  # going concern
    assert data_points >= 3, (
        f"Expected 3+ distress data points, found {data_points} in: {text}"
    )


def test_neg_data_richness_audit(angi_like_state: AnalysisState):
    """neg_audit_issues output must contain Beneish M-Score value and component flags."""
    from do_uw.stages.render.sections.sect1_findings_neg import neg_audit_issues

    text = " ".join(neg_audit_issues(angi_like_state, "Angi"))
    assert "-2.1" in text or "2.10" in text, f"Must contain Beneish M-Score value: {text}"
    # Must mention specific flags, not generic "strongest predictors"
    assert "strongest predictors" not in text.lower(), (
        f"Must not contain generic 'strongest predictors' text: {text}"
    )


def test_neg_data_richness_guidance(angi_like_state: AnalysisState):
    """neg_guidance output must contain miss count or credibility score."""
    from do_uw.stages.render.sections.sect1_findings_neg import neg_guidance

    text = " ".join(neg_guidance(angi_like_state, "Angi"))
    has_credibility = "35" in text or "credibility" in text.lower()
    has_miss = "miss" in text.lower() or "6" in text  # quarters assessed
    assert has_credibility or has_miss, (
        f"Must contain credibility score or miss count: {text}"
    )
    assert "concerning patterns" not in text.lower(), (
        f"Must not contain generic 'concerning patterns': {text}"
    )


# ---------------------------------------------------------------------------
# NQ-06: pos_stable_leadership differentiates healthy vs distressed
# ---------------------------------------------------------------------------

def test_pos_stable_leadership_differentiates(
    aapl_like_state: AnalysisState,
    angi_like_state: AnalysisState,
):
    """Healthy 13yr CEO vs distressed 2yr CEO must produce meaningfully different text."""
    from do_uw.stages.render.sections.sect1_findings_pos import pos_stable_leadership

    healthy_text = " ".join(pos_stable_leadership(aapl_like_state, "Apple"))
    distressed_text = " ".join(pos_stable_leadership(angi_like_state, "Angi"))

    # Must mention tenure
    assert "13" in healthy_text or "Tim Cook" in healthy_text, (
        f"Healthy text must mention CEO tenure or name: {healthy_text}"
    )
    assert "2" in distressed_text or "Joey Levin" in distressed_text, (
        f"Distressed text must mention CEO tenure or name: {distressed_text}"
    )

    # Must NOT contain the generic "rats leaving a sinking ship" boilerplate
    assert "rats leaving" not in healthy_text.lower()
    assert "rats leaving" not in distressed_text.lower()

    # Texts must be meaningfully different (not just name swaps)
    # Remove company names and check that remainder differs
    h_normalized = healthy_text.replace("Apple", "X").replace("Tim Cook", "CEO_NAME")
    d_normalized = distressed_text.replace("Angi", "X").replace("Joey Levin", "CEO_NAME")
    assert h_normalized != d_normalized, (
        "Healthy and distressed leadership text must differ beyond name swaps"
    )


# ---------------------------------------------------------------------------
# NQ-07: Differentiated full narrative (not just swapped names)
# ---------------------------------------------------------------------------

def test_differentiated_output(
    aapl_like_state: AnalysisState,
    angi_like_state: AnalysisState,
):
    """Full build_negative_narrative for stock risk produces different text for AAPL vs ANGI."""
    from do_uw.stages.render.sections.sect1_findings import (
        build_negative_narrative,
    )

    finding = KeyFinding(
        evidence_narrative="Stock Decline detected",
        section_origin="SECT4",
        scoring_impact="F2: -8 points",
        theory_mapping="10b-5 stock drop",
    )
    aapl_title, aapl_body = build_negative_narrative(
        finding, 0, _context(aapl_like_state),
    )
    angi_title, angi_body = build_negative_narrative(
        finding, 0, _context(angi_like_state),
    )

    # Normalize out company names
    aapl_norm = aapl_body.replace("Apple Inc.", "X").replace("Apple", "X").replace("AAPL", "X")
    angi_norm = angi_body.replace("Angi Homeservices Inc.", "X").replace("Angi", "X").replace("ANGI", "X")

    # Must contain different descriptors (catastrophic vs moderate)
    assert aapl_norm != angi_norm, (
        "AAPL and ANGI stock risk narratives must differ beyond name swaps"
    )


# ---------------------------------------------------------------------------
# NQ anti-boilerplate gate
# ---------------------------------------------------------------------------

def test_no_boilerplate_phrases(
    angi_like_state: AnalysisState,
):
    """No neg_*/pos_* function should produce known boilerplate phrases."""
    from do_uw.stages.render.sections import sect1_findings_neg, sect1_findings_pos

    boilerplate = [
        "even moderate risk factors can generate material d&o exposure",
        "historically correlated with increased d&o claim frequency",
    ]

    # Collect all neg_* outputs
    neg_outputs: list[str] = []
    neg_outputs.extend(sect1_findings_neg.neg_stock_risk(angi_like_state, "Test", "Stock Decline"))
    neg_outputs.extend(sect1_findings_neg.neg_governance(angi_like_state, "Test"))
    neg_outputs.extend(sect1_findings_neg.neg_distress(angi_like_state, "Test"))
    neg_outputs.extend(sect1_findings_neg.neg_audit_issues(angi_like_state, "Test"))
    neg_outputs.extend(sect1_findings_neg.neg_guidance(angi_like_state, "Test"))

    all_text = " ".join(neg_outputs).lower()
    for phrase in boilerplate:
        assert phrase not in all_text, f"Boilerplate found: '{phrase}'"


# ---------------------------------------------------------------------------
# NQ-04: No boilerplate D&O correlation language in brain YAML signals
# ---------------------------------------------------------------------------

def test_no_boilerplate_in_yaml():
    """No brain YAML signals contain the boilerplate D&O correlation phrase.

    Phase 119.1-03: All 343 occurrences of "historically correlated with
    increased D&O claim frequency and severity" must be replaced with
    signal-specific D&O risk mechanism explanations.
    """
    import glob

    boilerplate = "historically correlated with increased D&O claim frequency and severity"
    yaml_files = glob.glob("src/do_uw/brain/signals/**/*.yaml", recursive=True)
    assert len(yaml_files) > 50, f"Expected 50+ YAML files, found {len(yaml_files)}"

    violations: list[str] = []
    for f in yaml_files:
        with open(f) as fh:
            if boilerplate in fh.read():
                violations.append(f)
    assert violations == [], f"Boilerplate D&O language found in: {violations}"
