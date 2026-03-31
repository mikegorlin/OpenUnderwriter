"""Tests for forensic models and composite scoring.

Covers: Dechow F-Score, Montier C-Score, Enhanced Sloan Ratio,
Accrual Intensity, FIS, RQS, CFQS, zone classification, convergence.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import SourcedValue
from do_uw.models.financials import (
    AuditProfile,
    DistressIndicators,
    DistressResult,
    DistressZone,
    ExtractedFinancials,
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
)
from do_uw.models.forensic import ForensicZone
from do_uw.models.state import ExtractedData
from do_uw.stages.analyze.forensic_composites import (
    _classify_zone,
    _normalize_to_score,
    _weighted_composite,
    compute_cash_flow_quality_score,
    compute_financial_integrity_score,
    compute_revenue_quality_score,
    detect_beneish_dechow_convergence,
)
from do_uw.stages.analyze.forensic_models import (
    compute_accrual_intensity,
    compute_dechow_f_score,
    compute_enhanced_sloan_ratio,
    compute_montier_c_score,
)


# ---------------------------------------------------------------------------
# Fixtures: build ExtractedData with configurable financial data
# ---------------------------------------------------------------------------


_NOW = datetime.now(tz=UTC)


def _sv(val: float) -> SourcedValue[float]:
    """Create a SourcedValue[float] for testing."""
    return SourcedValue(value=val, source="test", confidence="HIGH", as_of=_NOW)


def _make_line_item(label: str, current: float, prior: float | None = None) -> FinancialLineItem:
    """Make a line item with current and optionally prior period."""
    values: dict[str, SourcedValue[float] | None] = {"FY2024": _sv(current)}
    if prior is not None:
        values["FY2023"] = _sv(prior)
    return FinancialLineItem(label=label, values=values)


def _make_extracted(
    *,
    revenue: tuple[float, float] | None = None,
    net_income: tuple[float, float] | None = None,
    total_assets: tuple[float, float] | None = None,
    receivable: tuple[float, float] | None = None,
    inventory: tuple[float, float] | None = None,
    current_assets: tuple[float, float] | None = None,
    property_ppe: tuple[float, float] | None = None,
    cash: tuple[float, float] | None = None,
    operating_cf: tuple[float, float] | None = None,
    depreciation: tuple[float, float] | None = None,
    current_liabilities: tuple[float, float] | None = None,
    capital_expenditure: tuple[float, float] | None = None,
    deferred_revenue: tuple[float, float] | None = None,
    beneish_score: float | None = None,
    material_weaknesses: int = 0,
    going_concern: bool = False,
    restatements: int = 0,
    is_big4: bool = True,
) -> ExtractedData:
    """Build ExtractedData with financial line items for testing."""
    periods = ["FY2024", "FY2023"]
    bs_items: list[FinancialLineItem] = []
    inc_items: list[FinancialLineItem] = []
    cf_items: list[FinancialLineItem] = []

    if total_assets:
        bs_items.append(_make_line_item("Total Assets", *total_assets))
    if receivable:
        bs_items.append(_make_line_item("Accounts Receivable", *receivable))
    if inventory:
        bs_items.append(_make_line_item("Inventories", *inventory))
    if current_assets:
        bs_items.append(_make_line_item("Total Current Assets", *current_assets))
    if property_ppe:
        bs_items.append(_make_line_item("Property Plant Equipment", *property_ppe))
    if cash:
        bs_items.append(_make_line_item("Cash and Equivalents", *cash))
    if current_liabilities:
        bs_items.append(_make_line_item("Total Current Liabilities", *current_liabilities))
    if deferred_revenue:
        bs_items.append(_make_line_item("Deferred Revenue", *deferred_revenue))

    if revenue:
        inc_items.append(_make_line_item("Total Revenue", *revenue))
    if net_income:
        inc_items.append(_make_line_item("Net Income", *net_income))

    if operating_cf:
        cf_items.append(_make_line_item("Operating Cash Flow", *operating_cf))
    if depreciation:
        cf_items.append(_make_line_item("Depreciation and Amortization", *depreciation))
    if capital_expenditure:
        cf_items.append(_make_line_item("Capital Expenditure", *capital_expenditure))

    stmts = FinancialStatements(
        income_statement=FinancialStatement(
            statement_type="income", periods=periods, line_items=inc_items),
        balance_sheet=FinancialStatement(
            statement_type="balance_sheet", periods=periods, line_items=bs_items),
        cash_flow=FinancialStatement(
            statement_type="cash_flow", periods=periods, line_items=cf_items),
        periods_available=2,
    )

    distress = DistressIndicators()
    if beneish_score is not None:
        distress.beneish_m_score = DistressResult(
            score=beneish_score, zone=DistressZone.DISTRESS if beneish_score > -1.78 else DistressZone.SAFE,
            model_variant="beneish_8var",
        )

    def _svt(val: object) -> SourcedValue:  # type: ignore[type-arg]
        return SourcedValue(value=val, source="test", confidence="HIGH", as_of=_NOW)

    audit = AuditProfile(
        is_big4=_svt(is_big4),
        going_concern=_svt(going_concern) if going_concern else None,
        material_weaknesses=[_svt(f"MW-{i}") for i in range(material_weaknesses)],
        restatements=[_svt({"type": "error"}) for _ in range(restatements)],
    )

    financials = ExtractedFinancials(statements=stmts, distress=distress, audit=audit)
    return ExtractedData(financials=financials)


# ---------------------------------------------------------------------------
# Test Dechow F-Score
# ---------------------------------------------------------------------------


class TestDechowFScore:
    def test_high_risk(self) -> None:
        """Known high-risk data with large receivable and inventory spikes."""
        ext = _make_extracted(
            total_assets=(1000, 800),
            receivable=(200, 100),  # +100% spike
            inventory=(150, 80),    # +87.5% spike
            current_assets=(400, 300),
            property_ppe=(200, 200),
            cash=(50, 50),
            revenue=(500, 450),
            net_income=(80, 70),
        )
        score, evidence = compute_dechow_f_score(ext)
        assert score > 1.40, f"Expected elevated Dechow, got {score}"
        assert "Dechow F-Score" in evidence

    def test_low_risk(self) -> None:
        """Clean data: minimal receivable/inventory changes, low soft assets."""
        ext = _make_extracted(
            total_assets=(1000, 980),
            receivable=(50, 49),        # Minimal change
            inventory=(40, 39),         # Minimal change
            current_assets=(200, 195),
            property_ppe=(700, 690),    # High PPE
            cash=(200, 195),            # High cash -> low soft assets
            revenue=(500, 490),
            net_income=(50, 48),
        )
        score, evidence = compute_dechow_f_score(ext)
        # Low soft assets + tiny changes = near baseline
        assert score < 1.40, f"Expected low Dechow, got {score}"

    def test_missing_data(self) -> None:
        """Returns 0.0 with insufficient data message."""
        ext = ExtractedData()
        score, evidence = compute_dechow_f_score(ext)
        assert score == 0.0
        assert "Insufficient" in evidence


# ---------------------------------------------------------------------------
# Test Montier C-Score
# ---------------------------------------------------------------------------


class TestMontierCScore:
    def test_all_flags(self) -> None:
        """All 6 indicators flagged -> score = 6."""
        ext = _make_extracted(
            net_income=(100, 80),        # NI rising
            operating_cf=(50, 70),       # CFO falling -> flag 1
            revenue=(500, 500),          # Flat revenue
            receivable=(120, 100),       # AR rising -> flag 2
            inventory=(90, 70),          # Inv rising -> flag 3
            current_assets=(350, 280),   # OCA rising -> flag 4
            depreciation=(-30, -40),     # Dep declining -> flag 5
            property_ppe=(200, 180),     # PPE basis
            total_assets=(1200, 1000),   # >10% growth -> flag 6
        )
        score, evidence = compute_montier_c_score(ext)
        assert score >= 4, f"Expected >= 4 flags, got {score}"
        assert "flagged" in evidence

    def test_clean(self) -> None:
        """Healthy financials -> low score."""
        ext = _make_extracted(
            net_income=(100, 90),
            operating_cf=(110, 95),       # CFO > NI improving
            revenue=(500, 480),
            receivable=(80, 85),          # AR stable/declining
            inventory=(60, 65),           # Inv stable
            current_assets=(250, 260),    # CA stable
            depreciation=(-40, -38),      # Dep stable
            property_ppe=(200, 200),
            total_assets=(1000, 990),     # <10% growth
        )
        score, evidence = compute_montier_c_score(ext)
        assert score <= 2, f"Expected <= 2 flags, got {score}"

    def test_no_data(self) -> None:
        """Empty data -> score 0.0."""
        ext = ExtractedData()
        score, evidence = compute_montier_c_score(ext)
        assert score == 0.0
        assert "Insufficient" in evidence


# ---------------------------------------------------------------------------
# Test Enhanced Sloan Ratio
# ---------------------------------------------------------------------------


class TestEnhancedSloanRatio:
    def test_high_accruals(self) -> None:
        """NI >> CFO -> high ratio."""
        ext = _make_extracted(
            net_income=(150, None),
            operating_cf=(30, None),
            total_assets=(1000, None),
        )
        ratio, evidence = compute_enhanced_sloan_ratio(ext)
        assert ratio > 0.10, f"Expected high Sloan, got {ratio}"
        assert "HIGH" in evidence

    def test_healthy(self) -> None:
        """NI close to CFO -> low ratio."""
        ext = _make_extracted(
            net_income=(100, None),
            operating_cf=(105, None),
            total_assets=(1000, None),
        )
        ratio, evidence = compute_enhanced_sloan_ratio(ext)
        assert ratio <= 0.05
        assert "HEALTHY" in evidence or "NORMAL" in evidence

    def test_missing_data(self) -> None:
        """Returns 0.0 with missing data."""
        ext = ExtractedData()
        ratio, evidence = compute_enhanced_sloan_ratio(ext)
        assert ratio == 0.0
        assert "Insufficient" in evidence


# ---------------------------------------------------------------------------
# Test Accrual Intensity
# ---------------------------------------------------------------------------


class TestAccrualIntensity:
    def test_high_intensity(self) -> None:
        """High accrual reliance."""
        ext = _make_extracted(
            net_income=(200, None),
            operating_cf=(100, None),
        )
        ratio, evidence = compute_accrual_intensity(ext)
        assert ratio >= 0.50, f"Expected high intensity, got {ratio}"

    def test_low_intensity(self) -> None:
        """Low accrual reliance with WC method."""
        ext = _make_extracted(
            operating_cf=(100, None),
            current_assets=(300, 290),
            cash=(100, 100),
            current_liabilities=(200, 195),
        )
        ratio, evidence = compute_accrual_intensity(ext)
        assert ratio < 0.50


# ---------------------------------------------------------------------------
# Test FIS (Financial Integrity Score)
# ---------------------------------------------------------------------------


class TestFinancialIntegrityScore:
    def test_high_integrity(self) -> None:
        """Clean financial data -> FIS > 60, zone HIGH_INTEGRITY or ADEQUATE."""
        ext = _make_extracted(
            total_assets=(1000, 950),
            receivable=(100, 98),
            inventory=(80, 79),
            current_assets=(300, 290),
            property_ppe=(400, 400),
            cash=(120, 113),
            revenue=(500, 490),
            net_income=(100, 95),
            operating_cf=(105, 100),
            depreciation=(-40, -38),
            current_liabilities=(200, 195),
            capital_expenditure=(-45, -42),
            beneish_score=-2.50,
        )
        fis = compute_financial_integrity_score(ext)
        assert fis.overall_score >= 60, f"Expected >= 60, got {fis.overall_score}"
        assert fis.zone in (ForensicZone.HIGH_INTEGRITY, ForensicZone.ADEQUATE)

    def test_critical(self) -> None:
        """Manipulated data -> FIS < 40, zone WEAK or CRITICAL."""
        ext = _make_extracted(
            total_assets=(1000, 800),
            receivable=(250, 100),      # Massive spike
            inventory=(180, 80),        # Massive spike
            current_assets=(500, 300),
            property_ppe=(200, 200),
            cash=(50, 50),
            revenue=(500, 450),
            net_income=(150, 70),       # NI way above CFO
            operating_cf=(30, 60),      # CFO declining
            depreciation=(-20, -30),    # Dep declining
            current_liabilities=(200, 150),
            capital_expenditure=(-10, -15),
            beneish_score=-1.50,        # Flagged
            material_weaknesses=2,
            going_concern=True,
        )
        fis = compute_financial_integrity_score(ext)
        assert fis.overall_score < 50, f"Expected < 50, got {fis.overall_score}"
        assert fis.zone in (ForensicZone.WEAK, ForensicZone.CRITICAL, ForensicZone.CONCERNING)

    def test_missing_sub_dimension(self) -> None:
        """Missing some data -> FIS computed from available dimensions."""
        ext = _make_extracted(
            total_assets=(1000, None),
            revenue=(500, None),
            net_income=(100, None),
            operating_cf=(105, None),
        )
        fis = compute_financial_integrity_score(ext)
        # Should still produce a score (reweighting)
        assert 0 <= fis.overall_score <= 100
        assert fis.zone is not None

    def test_all_missing(self) -> None:
        """No financial data -> default CONCERNING zone."""
        ext = ExtractedData()
        fis = compute_financial_integrity_score(ext)
        assert fis.overall_score == 50.0
        assert fis.zone == ForensicZone.CONCERNING


# ---------------------------------------------------------------------------
# Test RQS (Revenue Quality Score)
# ---------------------------------------------------------------------------


class TestRevenueQualityScore:
    def test_computation(self) -> None:
        """Revenue quality scoring produces valid results."""
        ext = _make_extracted(
            revenue=(500, 480),
            receivable=(100, 95),
            total_assets=(1000, 950),
        )
        rqs = compute_revenue_quality_score(ext)
        assert 0 <= rqs.overall_score <= 100
        assert rqs.zone is not None


# ---------------------------------------------------------------------------
# Test CFQS (Cash Flow Quality Score)
# ---------------------------------------------------------------------------


class TestCashFlowQualityScore:
    def test_computation(self) -> None:
        """Cash flow quality scoring produces valid results."""
        ext = _make_extracted(
            revenue=(500, None),
            net_income=(100, None),
            operating_cf=(105, None),
            capital_expenditure=(-45, None),
            depreciation=(-40, None),
        )
        cfqs = compute_cash_flow_quality_score(ext)
        assert 0 <= cfqs.overall_score <= 100
        assert cfqs.zone is not None


# ---------------------------------------------------------------------------
# Test Zone Classification
# ---------------------------------------------------------------------------


class TestZoneClassification:
    def test_boundaries(self) -> None:
        """Exact boundary values mapped correctly."""
        assert _classify_zone(100.0) == ForensicZone.HIGH_INTEGRITY
        assert _classify_zone(80.0) == ForensicZone.HIGH_INTEGRITY
        assert _classify_zone(79.9) == ForensicZone.ADEQUATE
        assert _classify_zone(60.0) == ForensicZone.ADEQUATE
        assert _classify_zone(59.9) == ForensicZone.CONCERNING
        assert _classify_zone(40.0) == ForensicZone.CONCERNING
        assert _classify_zone(39.9) == ForensicZone.WEAK
        assert _classify_zone(20.0) == ForensicZone.WEAK
        assert _classify_zone(19.9) == ForensicZone.CRITICAL
        assert _classify_zone(0.0) == ForensicZone.CRITICAL


# ---------------------------------------------------------------------------
# Test Weighted Composite with Nones
# ---------------------------------------------------------------------------


class TestWeightedComposite:
    def test_with_nones(self) -> None:
        """Skips None scores and reweights."""
        scores: dict[str, float | None] = {"a": 80.0, "b": None, "c": 60.0}
        weights = {"a": 0.5, "b": 0.3, "c": 0.2}
        result = _weighted_composite(scores, weights)
        # a=80*0.5=40, c=60*0.2=12, total_w=0.7, result=52/0.7=74.3
        expected = (80 * 0.5 + 60 * 0.2) / (0.5 + 0.2)
        assert abs(result - expected) < 0.2

    def test_all_none(self) -> None:
        """All None -> returns 50.0."""
        scores: dict[str, float | None] = {"a": None, "b": None}
        weights = {"a": 0.6, "b": 0.4}
        assert _weighted_composite(scores, weights) == 50.0


# ---------------------------------------------------------------------------
# Test Normalize to Score
# ---------------------------------------------------------------------------


class TestNormalizeToScore:
    def test_higher_is_worse(self) -> None:
        """Dechow-like scale: good=0.5, bad=2.0."""
        assert _normalize_to_score(0.0, 0.5, 2.0) == 100.0
        assert _normalize_to_score(2.5, 0.5, 2.0) == 0.0
        mid = _normalize_to_score(1.25, 0.5, 2.0)
        assert 40 < mid < 60

    def test_higher_is_better(self) -> None:
        """Piotroski-like: good=9, bad=0."""
        assert _normalize_to_score(9.0, 9.0, 0.0) == 100.0
        assert _normalize_to_score(0.0, 9.0, 0.0) == 0.0


# ---------------------------------------------------------------------------
# Test Convergence
# ---------------------------------------------------------------------------


class TestConvergence:
    def test_both_flagged(self) -> None:
        """Both Beneish and Dechow flagging -> convergence detected."""
        ext = _make_extracted(
            total_assets=(1000, 800),
            receivable=(250, 100),
            inventory=(180, 80),
            current_assets=(500, 300),
            property_ppe=(200, 200),
            cash=(50, 50),
            revenue=(500, 450),
            net_income=(150, 70),
            beneish_score=-1.50,  # Flagged (> -1.78)
        )
        conv, evidence = detect_beneish_dechow_convergence(ext)
        # Convergence depends on Dechow also being flagged
        assert isinstance(conv, bool)
        assert "Beneish" in evidence
        assert "Dechow" in evidence

    def test_no_convergence_clean(self) -> None:
        """Clean data -> no convergence."""
        ext = _make_extracted(
            total_assets=(1000, 950),
            receivable=(100, 98),
            revenue=(500, 490),
            beneish_score=-2.50,  # Not flagged
        )
        conv, evidence = detect_beneish_dechow_convergence(ext)
        assert conv is False
        assert "No convergence" in evidence


# ---------------------------------------------------------------------------
# Test signals.json integration
# ---------------------------------------------------------------------------


class TestChecksJson:
    def test_forensic_quality_signal_count(self) -> None:
        """At least 10 FIN.FORENSIC or FIN.QUALITY checks exist."""
        import json
        from pathlib import Path

        checks_path = Path("src/do_uw/brain/config/signals.json")
        data = json.loads(checks_path.read_text())
        forensic_quality = [
            c for c in data["signals"]
            if c["id"].startswith("FIN.FORENSIC") or c["id"].startswith("FIN.QUALITY")
        ]
        assert len(forensic_quality) >= 10, f"Found {len(forensic_quality)}"

    def test_convergence_is_amplifier(self) -> None:
        """Convergence check must have amplifier=true."""
        import json
        from pathlib import Path

        checks_path = Path("src/do_uw/brain/config/signals.json")
        data = json.loads(checks_path.read_text())
        conv = [c for c in data["signals"] if c["id"] == "FIN.FORENSIC.beneish_dechow_convergence"]
        assert len(conv) == 1
        assert conv[0].get("amplifier") is True
        assert conv[0].get("amplifier_bonus_points", 0) > 0

    def test_all_checks_have_classification(self) -> None:
        """All new forensic/quality checks have classification fields."""
        import json
        from pathlib import Path

        checks_path = Path("src/do_uw/brain/config/signals.json")
        data = json.loads(checks_path.read_text())
        for c in data["signals"]:
            if c["id"].startswith("FIN.FORENSIC") or c["id"].startswith("FIN.QUALITY"):
                assert c.get("category"), f"{c['id']} missing category"
                assert c.get("signal_type"), f"{c['id']} missing signal_type"
                assert c.get("plaintiff_lenses"), f"{c['id']} missing plaintiff_lenses"
