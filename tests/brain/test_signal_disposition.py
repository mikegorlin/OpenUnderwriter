"""Tests for signal disposition tagging (Phase 78 — AUDIT-01).

Every brain signal gets exactly one disposition after a pipeline run.
No signal is unaccounted for.
"""

from __future__ import annotations

import pytest

from do_uw.stages.analyze.signal_disposition import (
    DispositionTag,
    SkipReason,
    build_dispositions,
)


def _make_signal(
    signal_id: str,
    name: str = "Test Signal",
    execution_mode: str = "AUTO",
    lifecycle_state: str = "active",
    signal_class: str = "evaluative",
) -> dict:
    """Create a minimal brain signal dict."""
    return {
        "id": signal_id,
        "name": name,
        "execution_mode": execution_mode,
        "lifecycle_state": lifecycle_state,
        "signal_class": signal_class,
    }


def _make_result(
    signal_id: str,
    status: str = "CLEAR",
    data_status: str = "EVALUATED",
    data_status_reason: str = "",
    evidence: str = "",
) -> dict:
    """Create a minimal signal result dict (as stored on state)."""
    return {
        "signal_id": signal_id,
        "signal_name": "Test Signal",
        "status": status,
        "data_status": data_status,
        "data_status_reason": data_status_reason,
        "evidence": evidence,
    }


class TestDispositionTagging:
    """Test individual disposition derivation."""

    def test_triggered_signal(self):
        signals = [_make_signal("FIN.LIQ.test")]
        results = {"FIN.LIQ.test": _make_result("FIN.LIQ.test", status="TRIGGERED", evidence="ratio=0.5")}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.TRIGGERED
        assert disp.evidence == "ratio=0.5"

    def test_clear_signal(self):
        signals = [_make_signal("FIN.LIQ.test")]
        results = {"FIN.LIQ.test": _make_result("FIN.LIQ.test", status="CLEAR")}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.CLEAN

    def test_skipped_data_unavailable(self):
        signals = [_make_signal("FIN.LIQ.test")]
        results = {
            "FIN.LIQ.test": _make_result(
                "FIN.LIQ.test",
                status="SKIPPED",
                data_status="DATA_UNAVAILABLE",
                data_status_reason="No balance sheet data",
            )
        }
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.SKIPPED
        assert disp.skip_reason == SkipReason.DATA_UNAVAILABLE

    def test_skipped_not_applicable(self):
        signals = [_make_signal("FIN.LIQ.test")]
        results = {
            "FIN.LIQ.test": _make_result(
                "FIN.LIQ.test",
                status="SKIPPED",
                data_status="NOT_APPLICABLE",
                data_status_reason="Signal not relevant for financials",
            )
        }
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.SKIPPED
        assert disp.skip_reason == SkipReason.NOT_APPLICABLE

    def test_inactive_signal(self):
        signals = [_make_signal("FIN.OLD.test", lifecycle_state="inactive")]
        results = {}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.INACTIVE

    def test_inactive_overrides_evaluation(self):
        """An inactive signal stays INACTIVE even if it has a result."""
        signals = [_make_signal("FIN.OLD.test", lifecycle_state="inactive")]
        results = {"FIN.OLD.test": _make_result("FIN.OLD.test", status="TRIGGERED")}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.INACTIVE

    def test_non_auto_without_result(self):
        signals = [_make_signal("LIT.SCA.test", execution_mode="MANUAL")]
        results = {}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.SKIPPED
        assert disp.skip_reason == SkipReason.NOT_AUTO_EVALUATED

    def test_foundational_signal(self):
        signals = [_make_signal("BASE.SECTOR.test", signal_class="foundational")]
        results = {}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.SKIPPED
        assert disp.skip_reason == SkipReason.FOUNDATIONAL

    def test_info_maps_to_clean(self):
        signals = [_make_signal("FIN.LIQ.test")]
        results = {"FIN.LIQ.test": _make_result("FIN.LIQ.test", status="INFO")}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.CLEAN


class TestBuildDispositionsIntegration:
    """Test build_dispositions with mixed signal populations."""

    def test_five_signals_zero_unaccounted(self):
        signals = [
            _make_signal("FIN.LIQ.triggered"),
            _make_signal("FIN.LIQ.clear"),
            _make_signal("FIN.LIQ.skipped"),
            _make_signal("FIN.OLD.inactive", lifecycle_state="inactive"),
            _make_signal("LIT.SCA.manual", execution_mode="MANUAL"),
        ]
        results = {
            "FIN.LIQ.triggered": _make_result("FIN.LIQ.triggered", status="TRIGGERED"),
            "FIN.LIQ.clear": _make_result("FIN.LIQ.clear", status="CLEAR"),
            "FIN.LIQ.skipped": _make_result(
                "FIN.LIQ.skipped", status="SKIPPED", data_status="DATA_UNAVAILABLE"
            ),
        }
        summary = build_dispositions(signals, results)
        assert summary.total == 5
        assert len(summary.dispositions) == 5

    def test_summary_counts(self):
        signals = [
            _make_signal("A.triggered"),
            _make_signal("B.clear"),
            _make_signal("C.skipped"),
            _make_signal("D.inactive", lifecycle_state="inactive"),
            _make_signal("E.manual", execution_mode="MANUAL"),
        ]
        results = {
            "A.triggered": _make_result("A.triggered", status="TRIGGERED"),
            "B.clear": _make_result("B.clear", status="CLEAR"),
            "C.skipped": _make_result(
                "C.skipped", status="SKIPPED", data_status="DATA_UNAVAILABLE"
            ),
        }
        summary = build_dispositions(signals, results)
        assert summary.triggered_count == 1
        assert summary.clean_count == 1
        assert summary.skipped_count == 2  # C.skipped + E.manual
        assert summary.inactive_count == 1
        assert summary.total == 5

    def test_section_prefix_extraction(self):
        signals = [_make_signal("FIN.LIQ.test")]
        results = {"FIN.LIQ.test": _make_result("FIN.LIQ.test", status="CLEAR")}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.section_prefix == "FIN"

    def test_by_section_counts(self):
        signals = [
            _make_signal("FIN.LIQ.a"),
            _make_signal("FIN.LIQ.b"),
            _make_signal("GOV.BOARD.c"),
        ]
        results = {
            "FIN.LIQ.a": _make_result("FIN.LIQ.a", status="TRIGGERED"),
            "FIN.LIQ.b": _make_result("FIN.LIQ.b", status="CLEAR"),
            "GOV.BOARD.c": _make_result("GOV.BOARD.c", status="CLEAR"),
        }
        summary = build_dispositions(signals, results)
        assert summary.by_section["FIN"]["triggered"] == 1
        assert summary.by_section["FIN"]["clean"] == 1
        assert summary.by_section["GOV"]["clean"] == 1

    def test_extraction_gap_fallthrough(self):
        """An AUTO signal with no result and not foundational -> EXTRACTION_GAP."""
        signals = [_make_signal("FIN.LIQ.orphan")]
        results = {}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.SKIPPED
        assert disp.skip_reason == SkipReason.EXTRACTION_GAP

    def test_deprecated_maps_to_inactive(self):
        signals = [_make_signal("OLD.DEP.test", lifecycle_state="deprecated")]
        results = {}
        summary = build_dispositions(signals, results)
        disp = summary.dispositions[0]
        assert disp.disposition == DispositionTag.INACTIVE
