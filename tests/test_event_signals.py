"""Tests for BIZ.EVENT corporate event brain signals (Phase 95).

Covers:
- YAML structure validation (5 signals, required blocks)
- Data mapper logic for each signal (positive and negative cases)
- Manifest registration
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import yaml

from do_uw.stages.analyze.signal_mappers_events import map_event_fields


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_extracted(
    *,
    restatements: list[Any] | None = None,
    material_weaknesses: list[Any] | None = None,
    offerings_3yr: list[Any] | None = None,
    active_section_11_windows: int = 0,
) -> MagicMock:
    """Build a minimal ExtractedData mock for event signal tests."""
    extracted = MagicMock()

    # Financials / audit
    audit = MagicMock()
    audit.restatements = restatements or []
    audit.material_weaknesses = material_weaknesses or []
    extracted.financials.audit = audit

    # Market / capital markets
    cm = MagicMock()
    cm.offerings_3yr = offerings_3yr or []
    cm.active_section_11_windows = active_section_11_windows
    extracted.market.capital_markets = cm

    return extracted


def _make_company(
    business_changes: list[Any] | None = None,
) -> MagicMock:
    """Build a minimal CompanyProfile mock."""
    company = MagicMock()
    if business_changes is None:
        company.business_changes = []
    else:
        company.business_changes = business_changes
    return company


def _make_analysis(
    *,
    is_serial_acquirer: bool = False,
    goodwill_to_assets: float | None = None,
    goodwill_growth_rate: float | None = None,
) -> MagicMock:
    """Build a minimal analysis mock with xbrl_forensics."""
    analysis = MagicMock()

    ma_forensics: dict[str, Any] = {
        "is_serial_acquirer": is_serial_acquirer,
        "goodwill_growth_rate": goodwill_growth_rate,
        "acquisition_to_revenue": None,
    }

    gw_metric: dict[str, Any] = {
        "value": goodwill_to_assets,
        "zone": "safe" if goodwill_to_assets is None else (
            "danger" if goodwill_to_assets > 0.40 else "warning"
        ),
    }

    analysis.xbrl_forensics = {
        "ma_forensics": ma_forensics,
        "balance_sheet": {
            "goodwill_to_assets": gw_metric,
        },
    }
    return analysis


def _sv(value: Any) -> MagicMock:
    """Create a mock SourcedValue."""
    sv = MagicMock()
    sv.value = value
    return sv


# ---------------------------------------------------------------------------
# Test 1: YAML structure
# ---------------------------------------------------------------------------


class TestEventSignalYAML:
    """Verify all 5 signals load from YAML with required fields."""

    @pytest.fixture(scope="class")
    def signals(self) -> list[dict[str, Any]]:
        path = Path("src/do_uw/brain/signals/biz/events.yaml")
        return yaml.safe_load(path.read_text())

    def test_event_signal_yaml_structure(self, signals: list[dict[str, Any]]) -> None:
        assert len(signals) == 5, f"Expected 5 signals, got {len(signals)}"

        expected_ids = {
            "BIZ.EVENT.ma_history",
            "BIZ.EVENT.ipo_exposure",
            "BIZ.EVENT.restatements",
            "BIZ.EVENT.capital_changes",
            "BIZ.EVENT.business_changes",
        }
        actual_ids = {s["id"] for s in signals}
        assert actual_ids == expected_ids

        for s in signals:
            assert "acquisition" in s, f'{s["id"]} missing acquisition block'
            assert "evaluation" in s, f'{s["id"]} missing evaluation block'
            assert "presentation" in s, f'{s["id"]} missing presentation block'
            assert s.get("schema_version") == 3, f'{s["id"]} missing schema_version 3'
            ds = s.get("data_strategy", {})
            assert "field_key" in ds, f'{s["id"]} missing data_strategy.field_key'


# ---------------------------------------------------------------------------
# Test 2-3: M&A history mapper
# ---------------------------------------------------------------------------


class TestMAHistoryMapper:
    """Test BIZ.EVENT.ma_history data mapping."""

    def test_ma_history_mapper_serial_acquirer(self) -> None:
        extracted = _make_extracted()
        analysis = _make_analysis(
            is_serial_acquirer=True,
            goodwill_to_assets=0.45,
            goodwill_growth_rate=0.30,
        )
        result = map_event_fields(
            "BIZ.EVENT.ma_history", extracted, analysis=analysis
        )
        # serial=2 + goodwill>40%=1 + growth>25%=1 = 4
        assert result.get("event_ma_risk_score", 0) >= 2

    def test_ma_history_mapper_no_activity(self) -> None:
        extracted = _make_extracted()
        # No analysis = no forensics data
        result = map_event_fields(
            "BIZ.EVENT.ma_history", extracted, analysis=None
        )
        assert result.get("event_ma_risk_score") == 0


# ---------------------------------------------------------------------------
# Test 4-5: IPO exposure mapper
# ---------------------------------------------------------------------------


class TestIPOExposureMapper:
    """Test BIZ.EVENT.ipo_exposure data mapping."""

    def test_ipo_exposure_active_window(self) -> None:
        extracted = _make_extracted(active_section_11_windows=2)
        result = map_event_fields(
            "BIZ.EVENT.ipo_exposure", extracted
        )
        assert result.get("event_ipo_exposure_score") == 2

    def test_ipo_exposure_no_window(self) -> None:
        extracted = _make_extracted(active_section_11_windows=0)
        result = map_event_fields(
            "BIZ.EVENT.ipo_exposure", extracted
        )
        assert result.get("event_ipo_exposure_score") == 0


# ---------------------------------------------------------------------------
# Test 6-7: Restatement mapper
# ---------------------------------------------------------------------------


class TestRestatementMapper:
    """Test BIZ.EVENT.restatements data mapping."""

    def test_restatement_fires_red(self) -> None:
        extracted = _make_extracted(restatements=["restatement_1"])
        result = map_event_fields(
            "BIZ.EVENT.restatements", extracted
        )
        assert result.get("event_restatement_severity") >= 2

    def test_restatement_clean(self) -> None:
        extracted = _make_extracted()
        result = map_event_fields(
            "BIZ.EVENT.restatements", extracted
        )
        assert result.get("event_restatement_severity") == 0


# ---------------------------------------------------------------------------
# Test 8: Capital changes mapper
# ---------------------------------------------------------------------------


class TestCapitalChangesMapper:
    """Test BIZ.EVENT.capital_changes data mapping."""

    def test_capital_changes_with_offerings(self) -> None:
        offerings = [MagicMock(), MagicMock(), MagicMock()]
        extracted = _make_extracted(offerings_3yr=offerings)
        result = map_event_fields(
            "BIZ.EVENT.capital_changes", extracted
        )
        assert result.get("event_capital_change_count") == 3


# ---------------------------------------------------------------------------
# Test 9: Business changes mapper
# ---------------------------------------------------------------------------


class TestBusinessChangesMapper:
    """Test BIZ.EVENT.business_changes data mapping."""

    def test_business_changes_filters_generic(self) -> None:
        changes = [
            _sv("8-K filed 2025-01-15"),
            _sv("8-K filed 2025-03-20"),
            _sv("8-K filed 2025-06-01"),
            _sv("Detected keyword: acquisition of XYZ Corp"),
            _sv("Major restructuring announced"),
        ]
        company = _make_company(business_changes=changes)
        extracted = _make_extracted()
        result = map_event_fields(
            "BIZ.EVENT.business_changes", extracted, company=company
        )
        # 3 generic entries filtered, 2 keyword matches remain
        assert result.get("event_business_change_count") == 2


# ---------------------------------------------------------------------------
# Test 10: Manifest registration
# ---------------------------------------------------------------------------


class TestManifestRegistration:
    """Test corporate_events group exists in output manifest."""

    def test_all_event_signals_in_manifest(self) -> None:
        manifest = yaml.safe_load(
            Path("src/do_uw/brain/output_manifest.yaml").read_text()
        )
        bp = [s for s in manifest["sections"] if s["id"] in ("business_profile", "company_operations")][0]
        group_ids = [g["id"] for g in bp["groups"]]
        assert "corporate_events" in group_ids
        # Verify it has proper render_as
        ce_group = [g for g in bp["groups"] if g["id"] == "corporate_events"][0]
        assert ce_group["render_as"] == "kv_table"
