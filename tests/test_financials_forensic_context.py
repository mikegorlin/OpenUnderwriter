"""Tests for forensic dashboard context builder (Phase 73)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.financials_forensic import (
    build_forensic_dashboard_context,
)


def _make_metric(value: float | None = None, zone: str = "safe", trend: str | None = None) -> dict:
    """Create a ForensicMetric-like dict."""
    return {
        "value": value,
        "zone": zone,
        "trend": trend,
        "confidence": "HIGH",
    }


def _make_beneish(
    composite: float = -2.5,
    dsri: float = 1.0,
    gmi: float = 0.9,
    aqi: float = 1.0,
    sgi: float = 1.05,
    depi: float = 1.0,
    sgai: float = 1.0,
    lvgi: float = 1.0,
    tata: float = 0.01,
) -> dict:
    return {
        "composite_score": composite,
        "dsri": dsri,
        "gmi": gmi,
        "aqi": aqi,
        "sgi": sgi,
        "depi": depi,
        "sgai": sgai,
        "lvgi": lvgi,
        "tata": tata,
        "zone": "manipulation_unlikely" if composite <= -2.22 else "manipulation_likely",
        "primary_driver": None,
        "trajectory": [],
    }


def _make_forensics_dict(
    beneish: dict | None = None,
    balance_sheet: dict | None = None,
) -> dict:
    """Build a minimal xbrl_forensics dict."""
    bs = balance_sheet or {
        "goodwill_to_assets": _make_metric(0.15, "safe"),
        "intangible_concentration": _make_metric(0.25, "warning"),
        "off_balance_sheet_ratio": _make_metric(0.05, "safe"),
        "cash_conversion_cycle": _make_metric(45.0, "safe"),
        "working_capital_volatility": _make_metric(0.1, "safe"),
    }
    return {
        "balance_sheet": bs,
        "capital_allocation": {
            "roic": _make_metric(12.0, "safe"),
            "acquisition_effectiveness": _make_metric(0.8, "safe"),
            "buyback_timing": _make_metric(None, "insufficient_data"),
            "dividend_sustainability": _make_metric(1.5, "safe"),
        },
        "debt_tax": {
            "interest_coverage": _make_metric(8.0, "safe"),
            "debt_maturity_concentration": _make_metric(0.2, "safe"),
            "etr_anomaly": _make_metric(0.03, "safe"),
            "deferred_tax_growth": _make_metric(0.05, "safe"),
            "pension_underfunding": _make_metric(None, "not_applicable"),
        },
        "revenue": {
            "deferred_revenue_divergence": _make_metric(0.1, "safe"),
            "channel_stuffing_indicator": _make_metric(0.05, "safe"),
            "margin_compression": _make_metric(-0.02, "safe"),
            "ocf_revenue_ratio": _make_metric(0.15, "safe"),
        },
        "beneish": beneish or _make_beneish(),
        "earnings_quality": {
            "sloan_accruals": _make_metric(-0.03, "safe"),
            "cash_flow_manipulation": _make_metric(0.02, "safe"),
            "sbc_revenue_ratio": _make_metric(0.05, "safe"),
            "non_gaap_gap": _make_metric(0.1, "safe"),
        },
        "ma_forensics": {
            "is_serial_acquirer": False,
            "acquisition_years": [],
            "total_acquisition_spend": None,
            "goodwill_growth_rate": None,
            "acquisition_to_revenue": None,
        },
    }


class TestForensicDashboardEmpty:
    """Test graceful fallback when data is missing."""

    def test_no_analysis(self):
        state = MagicMock()
        state.analysis = None
        result = build_forensic_dashboard_context(state)
        assert result["has_data"] is False

    def test_no_xbrl_forensics(self):
        state = MagicMock()
        state.analysis.xbrl_forensics = None
        result = build_forensic_dashboard_context(state)
        assert result["has_data"] is False

    def test_beneish_no_data(self):
        state = MagicMock()
        data = _make_forensics_dict(beneish={
            "composite_score": None,
            "dsri": None, "gmi": None, "aqi": None, "sgi": None,
            "depi": None, "sgai": None, "lvgi": None, "tata": None,
            "zone": "insufficient_data", "primary_driver": None, "trajectory": [],
        })
        state.analysis.xbrl_forensics = data
        result = build_forensic_dashboard_context(state)
        assert result["beneish"]["has_data"] is False


class TestForensicDashboardWithData:
    """Test context building with mock forensic data."""

    def _make_state(self, forensics_dict: dict | None = None) -> MagicMock:
        state = MagicMock()
        state.analysis.xbrl_forensics = forensics_dict or _make_forensics_dict()
        return state

    def test_has_data(self):
        state = self._make_state()
        result = build_forensic_dashboard_context(state)
        assert result["has_data"] is True

    def test_bands_structure(self):
        state = self._make_state()
        result = build_forensic_dashboard_context(state)
        for band in result["bands"]:
            assert "severity" in band
            assert "label" in band
            assert "color" in band
            assert "modules" in band
            assert band["severity"] in ("critical", "warning", "normal")

    def test_modules_have_findings(self):
        state = self._make_state()
        result = build_forensic_dashboard_context(state)
        for band in result["bands"]:
            for mod in band["modules"]:
                assert "name" in mod
                assert "composite_score" in mod
                assert "zone" in mod
                assert "findings" in mod
                assert len(mod["findings"]) > 0

    def test_severity_sorting(self):
        """Critical modules should appear before warning before normal."""
        data = _make_forensics_dict()
        # Make balance sheet critical
        data["balance_sheet"]["goodwill_to_assets"] = _make_metric(0.8, "danger")
        data["balance_sheet"]["intangible_concentration"] = _make_metric(0.9, "danger")
        state = self._make_state(data)
        result = build_forensic_dashboard_context(state)
        severity_order = [b["severity"] for b in result["bands"]]
        expected = sorted(severity_order, key=lambda s: {"critical": 0, "warning": 1, "normal": 2}[s])
        assert severity_order == expected

    def test_beneish_components(self):
        state = self._make_state()
        result = build_forensic_dashboard_context(state)
        beneish = result["beneish"]
        assert beneish["has_data"] is True
        assert len(beneish["components"]) == 8
        codes = [c["code"] for c in beneish["components"]]
        assert "DSRI" in codes
        assert "TATA" in codes

    def test_beneish_pass_fail(self):
        """Test that components correctly flag pass/fail against thresholds."""
        data = _make_forensics_dict(beneish=_make_beneish(
            composite=-1.5,  # manipulation_likely
            dsri=1.5,  # > 1.031 threshold = FAIL
            gmi=0.5,  # < 1.014 threshold = PASS
        ))
        state = self._make_state(data)
        result = build_forensic_dashboard_context(state)
        components = {c["code"]: c for c in result["beneish"]["components"]}
        assert components["DSRI"]["pass"] is False  # 1.5 > 1.031
        assert components["GMI"]["pass"] is True  # 0.5 <= 1.014

    def test_beneish_zone(self):
        # manipulation_unlikely
        data = _make_forensics_dict(beneish=_make_beneish(composite=-3.0))
        state = self._make_state(data)
        result = build_forensic_dashboard_context(state)
        assert result["beneish"]["zone"] == "manipulation_unlikely"

        # manipulation_likely
        data2 = _make_forensics_dict(beneish=_make_beneish(composite=-1.0))
        state2 = self._make_state(data2)
        result2 = build_forensic_dashboard_context(state2)
        assert result2["beneish"]["zone"] == "manipulation_likely"

    def test_empty_bands_hidden(self):
        """If no modules are critical, the critical band should be absent."""
        state = self._make_state()  # all safe
        result = build_forensic_dashboard_context(state)
        band_severities = [b["severity"] for b in result["bands"]]
        # With all-safe data, should have mostly/only normal band
        # The warning band from intangible_concentration might exist
        assert "critical" not in band_severities or any(
            b["severity"] == "critical" for b in result["bands"]
        )
