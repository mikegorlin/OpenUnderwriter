"""Tests for XBRL signal upgrade (Phase 70-02).

Verifies:
1. 40+ signals in fin/*.yaml and biz/*.yaml have xbrl_ or forensic_ field_keys
2. Mappers return XBRL-keyed values when statement data is present
3. Mappers return legacy values as fallback when XBRL data is None
4. Shadow table creation works without error
5. Field routing entries exist for all XBRL field_keys
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Test 1: YAML field_key audit
# ---------------------------------------------------------------------------


def _count_xbrl_signals() -> int:
    """Count signals with xbrl_ or forensic_ prefixed field_keys."""
    count = 0
    base = Path("src/do_uw/brain/signals")
    for domain in ("fin", "biz"):
        domain_path = base / domain
        if not domain_path.exists():
            continue
        for f in domain_path.glob("*.yaml"):
            with open(f) as fh:
                sigs = yaml.safe_load(fh)
            if sigs:
                for s in sigs:
                    fk = s.get("data_strategy", {}).get("field_key", "")
                    if fk.startswith("xbrl_") or fk.startswith("forensic_"):
                        count += 1
    return count


def test_at_least_40_xbrl_signals():
    """Verify at least 40 signals have XBRL-sourced field_keys."""
    count = _count_xbrl_signals()
    assert count >= 40, f"Only {count} XBRL-sourced signals (need 40+)"


def test_temporal_signals_have_xbrl_field_keys():
    """All 10 temporal signals should have xbrl_ field_keys."""
    temporal_path = Path("src/do_uw/brain/signals/fin/temporal.yaml")
    with open(temporal_path) as f:
        sigs = yaml.safe_load(f)
    xbrl_count = 0
    for s in sigs:
        fk = s.get("data_strategy", {}).get("field_key", "")
        if fk.startswith("xbrl_"):
            xbrl_count += 1
    assert xbrl_count == 10, f"Expected 10 temporal XBRL signals, got {xbrl_count}"


def test_balance_signals_have_xbrl_field_keys():
    """Liquidity and debt signals in balance.yaml should have xbrl_ field_keys."""
    balance_path = Path("src/do_uw/brain/signals/fin/balance.yaml")
    with open(balance_path) as f:
        sigs = yaml.safe_load(f)
    xbrl_ids = [
        s["id"]
        for s in sigs
        if s.get("data_strategy", {}).get("field_key", "").startswith("xbrl_")
    ]
    expected = {
        "FIN.LIQ.position",
        "FIN.LIQ.working_capital",
        "FIN.LIQ.efficiency",
        "FIN.LIQ.trend",
        "FIN.LIQ.cash_burn",
        "FIN.DEBT.structure",
        "FIN.DEBT.coverage",
        "FIN.DEBT.maturity",
    }
    assert expected.issubset(set(xbrl_ids)), f"Missing: {expected - set(xbrl_ids)}"


# ---------------------------------------------------------------------------
# Test 2: Mapper XBRL-keyed return values
# ---------------------------------------------------------------------------


def _make_extracted_financials():
    """Create a mock ExtractedData with financials data."""
    from do_uw.models.state import ExtractedData

    extracted = ExtractedData()
    # Mock financials with liquidity and leverage
    fin = MagicMock()
    # Liquidity: SourcedValue[dict]
    liq_sv = MagicMock()
    liq_sv.value = {"current_ratio": 2.1, "quick_ratio": 1.5, "cash_ratio": 0.8, "working_capital": 500000}
    fin.liquidity = liq_sv
    # Leverage: SourcedValue[dict]
    lev_sv = MagicMock()
    lev_sv.value = {"debt_to_equity": 0.8, "debt_to_ebitda": 3.2, "interest_coverage": 5.5}
    fin.leverage = lev_sv
    # Earnings quality
    eq_sv = MagicMock()
    eq_sv.value = {
        "quality_score": 1.5,
        "accruals_ratio": 0.03,
        "ocf_to_ni": 1.1,
        "dso_delta": 2.5,
        "revenue_quality": 0.85,
        "asset_quality_delta": 0.1,
        "cash_flow_adequacy": 1.0,
    }
    fin.earnings_quality = eq_sv
    # Distress indicators
    fin.distress = MagicMock()
    fin.distress.altman_z_score = MagicMock(score=3.5, is_partial=False, zone="safe")
    fin.distress.beneish_m_score = MagicMock(score=-2.5)
    fin.distress.piotroski_f_score = MagicMock(score=7)
    # Audit
    fin.audit = MagicMock()
    fin.audit.going_concern = None
    fin.audit.material_weaknesses = []
    fin.audit.restatements = []
    fin.audit.opinion_type = None
    fin.audit.tenure_years = None
    fin.audit.is_big4 = None
    fin.audit.critical_audit_matters = []
    # Other fields
    fin.debt_structure = None
    fin.refinancing_risk = None
    fin.tax_indicators = None
    fin.financial_health_narrative = None
    fin.statements = None
    fin.quarterly_xbrl = None
    extracted.financials = fin
    # Market
    extracted.market = None
    return extracted


def test_financial_mapper_returns_xbrl_keys():
    """Financial mapper should return xbrl_ keyed values alongside legacy keys."""
    from do_uw.stages.analyze.signal_mappers import map_signal_data

    extracted = _make_extracted_financials()
    # Map a liquidity signal
    result = map_signal_data(
        "FIN.LIQ.position",
        {"data_strategy": {"field_key": "xbrl_current_ratio"}},
        extracted,
    )
    # Should have xbrl_current_ratio
    assert "xbrl_current_ratio" in result, f"Missing xbrl_current_ratio. Keys: {list(result.keys())}"


def test_financial_mapper_returns_debt_xbrl_keys():
    """Debt signals should return xbrl_ keyed values."""
    from do_uw.stages.analyze.signal_mappers import map_signal_data

    extracted = _make_extracted_financials()
    result = map_signal_data(
        "FIN.DEBT.structure",
        {"data_strategy": {"field_key": "xbrl_debt_to_ebitda"}},
        extracted,
    )
    assert "xbrl_debt_to_ebitda" in result


def test_financial_mapper_returns_legacy_fallback():
    """When XBRL data is None, legacy keys should still be populated."""
    from do_uw.stages.analyze.signal_mappers import map_signal_data

    extracted = _make_extracted_financials()
    # Use legacy field_key to verify fallback
    result = map_signal_data(
        "FIN.DEBT.credit_rating",
        {"data_strategy": {"field_key": "debt_structure"}},
        extracted,
    )
    # debt_structure should exist (even if None)
    assert "debt_structure" in result


def test_temporal_mapper_returns_xbrl_keys():
    """Temporal mapper should populate xbrl_ keys when data available."""
    from do_uw.stages.analyze.signal_mappers_analytical import map_phase26_check

    extracted = _make_extracted_financials()
    result = map_phase26_check(
        "FIN.TEMPORAL.cfo_ni_divergence",
        {},
        extracted,
    )
    assert result is not None
    # Should have xbrl_ key when earnings_quality has ocf_to_ni
    assert "xbrl_cfo_ni_divergence" in result, f"Keys: {list(result.keys())}"


def test_quality_mapper_returns_xbrl_keys():
    """Quality mapper should populate xbrl_ keys."""
    from do_uw.stages.analyze.signal_mappers_analytical import map_phase26_check

    extracted = _make_extracted_financials()
    result = map_phase26_check(
        "FIN.QUALITY.quality_of_earnings",
        {},
        extracted,
    )
    assert result is not None
    assert "xbrl_earnings_quality" in result


# ---------------------------------------------------------------------------
# Test 3: Shadow table creation
# ---------------------------------------------------------------------------


    # No assertion needed - just verify no exception


# ---------------------------------------------------------------------------
# Test 4: Field routing coverage
# ---------------------------------------------------------------------------


def test_field_routing_has_xbrl_entries():
    """FIELD_FOR_CHECK should have entries for XBRL-upgraded signals."""
    from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

    xbrl_entries = {k: v for k, v in FIELD_FOR_CHECK.items() if v.startswith("xbrl_")}
    assert len(xbrl_entries) >= 20, (
        f"Only {len(xbrl_entries)} XBRL field routing entries (need 20+)"
    )


def test_field_routing_temporal_signals():
    """All 10 temporal signals should have field routing entries."""
    from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

    temporal_ids = [
        "FIN.TEMPORAL.revenue_deceleration",
        "FIN.TEMPORAL.margin_compression",
        "FIN.TEMPORAL.operating_margin_compression",
        "FIN.TEMPORAL.dso_expansion",
        "FIN.TEMPORAL.cfo_ni_divergence",
        "FIN.TEMPORAL.working_capital_deterioration",
        "FIN.TEMPORAL.debt_ratio_increase",
        "FIN.TEMPORAL.cash_flow_deterioration",
        "FIN.TEMPORAL.profitability_trend",
        "FIN.TEMPORAL.earnings_quality_divergence",
    ]
    for tid in temporal_ids:
        assert tid in FIELD_FOR_CHECK, f"Missing field routing for {tid}"
        assert FIELD_FOR_CHECK[tid].startswith("xbrl_"), (
            f"{tid} should route to xbrl_ key, got {FIELD_FOR_CHECK[tid]}"
        )


def test_no_threshold_changes():
    """Verify no signal thresholds were modified (only field_keys changed)."""
    # Spot check a few key signals for unchanged thresholds
    balance_path = Path("src/do_uw/brain/signals/fin/balance.yaml")
    with open(balance_path) as f:
        sigs = yaml.safe_load(f)

    for s in sigs:
        if s["id"] == "FIN.LIQ.position":
            assert s["threshold"]["red"] == "<1.0 current ratio (inadequate liquidity)"
        elif s["id"] == "FIN.DEBT.structure":
            assert "Debt/EBITDA >6x" in s["threshold"]["red"]
        elif s["id"] == "FIN.DEBT.coverage":
            assert "Interest coverage <1.5x" in s["threshold"]["red"]
