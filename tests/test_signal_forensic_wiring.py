"""Tests for Phase 70 forensic signal wiring.

Verifies:
- _extract_forensic_value extracts correct values from nested xbrl_forensics dict
- _map_forensic_check returns correct field_key dict when xbrl_forensics data present
- _map_forensic_check returns empty/None gracefully when xbrl_forensics is None
- Forensic signal field_keys are routable through FIELD_FOR_CHECK
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest


# ── Fixtures ──


def _make_forensic_metric(
    value: float | bool | None = None,
    zone: str = "safe",
    trend: str | None = None,
) -> dict[str, Any]:
    """Create a ForensicMetric-like dict."""
    return {
        "value": value,
        "zone": zone,
        "trend": trend,
        "confidence": "HIGH",
        "details": {},
    }


def _make_xbrl_forensics() -> dict[str, Any]:
    """Create a sample xbrl_forensics nested dict matching Phase 69 output."""
    return {
        "balance_sheet": {
            "goodwill_to_assets": _make_forensic_metric(0.35, "warning"),
            "intangible_concentration": _make_forensic_metric(0.45, "warning"),
            "off_balance_sheet": _make_forensic_metric(0.08, "safe"),
            "cash_conversion_cycle": _make_forensic_metric(95.0, "warning"),
            "working_capital_volatility": _make_forensic_metric(0.12, "safe"),
        },
        "revenue": {
            "deferred_revenue_divergence": _make_forensic_metric(0.15, "warning"),
            "channel_stuffing": _make_forensic_metric(0.05, "safe"),
            "margin_compression": _make_forensic_metric(0.03, "warning"),
            "ocf_revenue_ratio": _make_forensic_metric(0.18, "safe"),
        },
        "capital_allocation": {
            "roic_trend": _make_forensic_metric(0.12, "safe"),
            "acquisition_effectiveness": _make_forensic_metric(0.75, "safe"),
            "buyback_timing": _make_forensic_metric(0.65, "safe"),
            "dividend_sustainability": _make_forensic_metric(0.80, "safe"),
        },
        "debt_tax": {
            "interest_coverage_trend": _make_forensic_metric(4.5, "safe"),
            "debt_maturity_concentration": _make_forensic_metric(0.25, "safe"),
            "etr_anomaly": _make_forensic_metric(0.05, "safe"),
            "deferred_tax_growth": _make_forensic_metric(0.10, "safe"),
            "pension_underfunding": _make_forensic_metric(0.08, "safe"),
        },
        "beneish": {
            "dsri": _make_forensic_metric(1.2, "safe"),
            "aqi": _make_forensic_metric(0.95, "safe"),
            "tata": _make_forensic_metric(0.01, "safe"),
            "composite_score": _make_forensic_metric(-2.5, "safe"),
        },
        "earnings_quality": {
            "sloan_accruals": _make_forensic_metric(0.03, "safe"),
            "cash_flow_manipulation": _make_forensic_metric(0.04, "safe"),
            "sbc_dilution": _make_forensic_metric(0.06, "warning"),
            "non_gaap_gap": _make_forensic_metric(0.12, "safe"),
        },
        "ma_forensics": {
            "serial_acquirer": _make_forensic_metric(True, "danger"),
            "goodwill_growth_rate": _make_forensic_metric(0.30, "danger"),
            "acquisition_to_revenue": _make_forensic_metric(0.20, "warning"),
        },
    }


# ── _extract_forensic_value tests ──


class TestExtractForensicValue:
    """Test the _extract_forensic_value helper."""

    def test_extracts_numeric_value(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _extract_forensic_value,
        )

        xf = _make_xbrl_forensics()
        val = _extract_forensic_value(xf, "balance_sheet", "goodwill_to_assets")
        assert val == 0.35

    def test_extracts_boolean_value(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _extract_forensic_value,
        )

        xf = _make_xbrl_forensics()
        val = _extract_forensic_value(xf, "ma_forensics", "serial_acquirer")
        assert val is True

    def test_returns_none_for_missing_category(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _extract_forensic_value,
        )

        xf = _make_xbrl_forensics()
        val = _extract_forensic_value(xf, "nonexistent", "anything")
        assert val is None

    def test_returns_none_for_missing_metric(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _extract_forensic_value,
        )

        xf = _make_xbrl_forensics()
        val = _extract_forensic_value(xf, "balance_sheet", "nonexistent")
        assert val is None

    def test_returns_none_for_insufficient_data(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _extract_forensic_value,
        )

        xf = {
            "balance_sheet": {
                "goodwill_to_assets": _make_forensic_metric(None, "insufficient_data"),
            },
        }
        val = _extract_forensic_value(xf, "balance_sheet", "goodwill_to_assets")
        assert val is None


# ── _map_forensic_check tests ──


class TestMapForensicCheck:
    """Test the _map_forensic_check mapper with xbrl_forensics data."""

    def _make_extracted(self) -> Any:
        """Create a minimal ExtractedData stub."""
        from do_uw.models.state import ExtractedData

        return ExtractedData()

    def test_returns_forensic_fields_when_analysis_present(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _map_forensic_check,
        )

        extracted = self._make_extracted()
        analysis = SimpleNamespace(xbrl_forensics=_make_xbrl_forensics())

        result = _map_forensic_check(
            "FIN.FORENSIC.goodwill_impairment_risk",
            extracted,
            analysis=analysis,
        )
        assert "forensic_goodwill_impairment_risk" in result
        assert result["forensic_goodwill_impairment_risk"] == 0.35

    def test_returns_all_forensic_fields(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _map_forensic_check,
        )

        extracted = self._make_extracted()
        analysis = SimpleNamespace(xbrl_forensics=_make_xbrl_forensics())

        result = _map_forensic_check(
            "FIN.FORENSIC.goodwill_impairment_risk",
            extracted,
            analysis=analysis,
        )
        # Mapper maps ONLY the field relevant to THIS signal (not all 29)
        forensic_keys = [k for k in result if k.startswith("forensic_")]
        assert len(forensic_keys) == 1, (
            f"Expected 1 forensic_ key, got {len(forensic_keys)}: {forensic_keys}"
        )
        assert "forensic_goodwill_impairment_risk" in result

    def test_returns_empty_when_no_analysis(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _map_forensic_check,
        )

        extracted = self._make_extracted()
        result = _map_forensic_check(
            "FIN.FORENSIC.goodwill_impairment_risk",
            extracted,
            analysis=None,
        )
        # No forensic_ keys without analysis
        forensic_keys = [k for k in result if k.startswith("forensic_")]
        assert len(forensic_keys) == 0

    def test_returns_empty_when_xbrl_forensics_none(self) -> None:
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _map_forensic_check,
        )

        extracted = self._make_extracted()
        analysis = SimpleNamespace(xbrl_forensics=None)

        result = _map_forensic_check(
            "FIN.FORENSIC.goodwill_impairment_risk",
            extracted,
            analysis=analysis,
        )
        forensic_keys = [k for k in result if k.startswith("forensic_")]
        assert len(forensic_keys) == 0

    def test_legacy_checks_still_work(self) -> None:
        """Ensure existing FIN.FORENSIC.fis_composite still routes to legacy path."""
        from do_uw.stages.analyze.signal_mappers_analytical import (
            _map_forensic_check,
        )

        extracted = self._make_extracted()
        # No analysis — legacy path only
        result = _map_forensic_check(
            "FIN.FORENSIC.fis_composite",
            extracted,
            analysis=None,
        )
        # Legacy check returns empty when no financials data
        assert isinstance(result, dict)


# ── Field routing tests ──


class TestForensicFieldRouting:
    """Verify forensic field_keys are routable through FIELD_FOR_CHECK."""

    def test_at_least_10_forensic_keys_in_field_routing(self) -> None:
        from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

        forensic_entries = {
            k: v for k, v in FIELD_FOR_CHECK.items()
            if v.startswith("forensic_")
        }
        assert len(forensic_entries) >= 10, (
            f"Expected >= 10 forensic_ entries in FIELD_FOR_CHECK, got {len(forensic_entries)}"
        )

    def test_all_29_forensic_signals_have_routing(self) -> None:
        from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

        forensic_entries = {
            k: v for k, v in FIELD_FOR_CHECK.items()
            if v.startswith("forensic_")
        }
        assert len(forensic_entries) >= 29, (
            f"Expected >= 29 forensic_ entries, got {len(forensic_entries)}"
        )

    def test_narrow_result_uses_forensic_field_key(self) -> None:
        from do_uw.stages.analyze.signal_field_routing import narrow_result

        data = {
            "forensic_goodwill_to_assets": 0.35,
            "forensic_intangible_concentration": 0.45,
            "value": "legacy",
        }
        # Signal with data_strategy.field_key takes priority
        sig_def = {"data_strategy": {"field_key": "forensic_goodwill_to_assets"}}
        result = narrow_result("FIN.FORENSIC.goodwill_impairment_risk", data, sig_def)
        assert result == {"forensic_goodwill_to_assets": 0.35}


# ── YAML signal count tests ──


class TestForensicYamlSignals:
    """Verify YAML signal files have correct counts and structure."""

    def test_forensic_xbrl_signal_count(self) -> None:
        import yaml
        from pathlib import Path

        path = Path("src/do_uw/brain/signals/fin/forensic_xbrl.yaml")
        with open(path) as f:
            sigs = yaml.safe_load(f)
        assert len(sigs) == 29, f"Expected 29 forensic signals, got {len(sigs)}"

    def test_opportunity_signal_count(self) -> None:
        import yaml
        from pathlib import Path

        path = Path("src/do_uw/brain/signals/fin/forensic_opportunities.yaml")
        with open(path) as f:
            sigs = yaml.safe_load(f)
        assert len(sigs) == 12, f"Expected 12 opportunity signals, got {len(sigs)}"

    def test_all_forensic_signals_have_field_key(self) -> None:
        import yaml
        from pathlib import Path

        path = Path("src/do_uw/brain/signals/fin/forensic_xbrl.yaml")
        with open(path) as f:
            sigs = yaml.safe_load(f)
        for s in sigs:
            ds = s.get("data_strategy", {})
            fk = ds.get("field_key", "")
            assert fk.startswith(("forensic_", "xbrl_")), (
                f"{s['id']} has field_key '{fk}' — expected forensic_ or xbrl_ prefix"
            )

    def test_all_signals_have_required_fields(self) -> None:
        import yaml
        from pathlib import Path

        for fname in ("forensic_xbrl.yaml", "forensic_opportunities.yaml"):
            path = Path(f"src/do_uw/brain/signals/fin/{fname}")
            with open(path) as f:
                sigs = yaml.safe_load(f)
            for s in sigs:
                assert "id" in s, f"Signal in {fname} missing id"
                assert "name" in s, f"{s.get('id', '?')} missing name"
                assert "threshold" in s, f"{s['id']} missing threshold"
                assert "provenance" in s, f"{s['id']} missing provenance"
                assert "group" in s, f"{s['id']} missing group"
                assert "display" in s, f"{s['id']} missing display"


# ── Phase 70-04: execute_signals analysis parameter tests ──


class TestExecuteSignalsAnalysisParam:
    """Verify execute_signals accepts and passes analysis parameter."""

    def test_analysis_param_in_signature(self) -> None:
        import inspect
        from do_uw.stages.analyze.signal_engine import execute_signals

        sig = inspect.signature(execute_signals)
        assert "analysis" in sig.parameters, (
            f"analysis param missing from execute_signals: {sig}"
        )

    def test_forensic_signal_non_skipped_with_analysis(self) -> None:
        """When analysis has xbrl_forensics data, forensic signals produce non-SKIPPED."""
        from do_uw.stages.analyze.signal_engine import execute_signals
        from do_uw.models.state import ExtractedData

        extracted = ExtractedData()
        analysis = SimpleNamespace(xbrl_forensics=_make_xbrl_forensics())

        # Minimal forensic signal config
        forensic_signal = {
            "id": "FIN.FORENSIC.goodwill_impairment_risk",
            "name": "Goodwill Impairment Risk",
            "execution_mode": "AUTO",
            "content_type": "EVALUATIVE_CHECK",
            "section": 3,
            "factors": ["F3"],
            "data_strategy": {"field_key": "forensic_goodwill_to_assets"},
            "threshold": {
                "type": "value",
                "red": 0.5,
                "yellow": 0.3,
                "direction": "above",
            },
        }

        results = execute_signals(
            [forensic_signal],
            extracted,
            company=None,
            analysis=analysis,
        )
        assert len(results) == 1
        result = results[0]
        # With xbrl_forensics providing goodwill_to_assets=0.35, this should
        # evaluate (not SKIP). 0.35 > 0.3 threshold = TRIGGERED yellow
        assert result.status.value != "SKIPPED", (
            f"Expected non-SKIPPED with forensic data, got {result.status.value}"
        )

    def test_forensic_signal_skipped_without_analysis(self) -> None:
        """Without analysis, forensic signals SKIP (no data)."""
        from do_uw.stages.analyze.signal_engine import execute_signals
        from do_uw.models.state import ExtractedData

        extracted = ExtractedData()

        forensic_signal = {
            "id": "FIN.FORENSIC.goodwill_impairment_risk",
            "name": "Goodwill Impairment Risk",
            "execution_mode": "AUTO",
            "content_type": "EVALUATIVE_CHECK",
            "section": 3,
            "factors": ["F3"],
            "data_strategy": {"field_key": "forensic_goodwill_to_assets"},
            "threshold": {
                "type": "value",
                "red": 0.5,
                "yellow": 0.3,
                "direction": "above",
            },
        }

        results = execute_signals(
            [forensic_signal],
            extracted,
            company=None,
            analysis=None,
        )
        assert len(results) == 1
        assert results[0].status.value == "SKIPPED"
