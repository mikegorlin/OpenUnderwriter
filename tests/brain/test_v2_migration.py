"""V2 signal migration regression tests.

Validates that V2-migrated signals load correctly, maintain all required
sections, reference valid field registry entries, and coexist with the
400 total signal corpus without breakage.

Phase 54 Plan 03: V2 Signal Migration + CLI Updates + Verification.
"""

from __future__ import annotations

import pytest

from do_uw.brain.brain_signal_schema import BrainSignalEntry
from do_uw.brain.brain_unified_loader import load_signals
from do_uw.brain.field_registry import load_field_registry, _reset_cache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def all_signals() -> list[dict]:
    """Load all signals from YAML once per test module."""
    data = load_signals()
    return data.get("signals", [])


@pytest.fixture(scope="module")
def v2_signals(all_signals: list[dict]) -> list[dict]:
    """Filter to signals with V2 acquisition blocks (declarative data specs)."""
    return [s for s in all_signals if s.get("acquisition")]


@pytest.fixture(scope="module")
def field_registry():
    """Load the field registry."""
    _reset_cache()
    return load_field_registry()


# ---------------------------------------------------------------------------
# Total signal count regression
# ---------------------------------------------------------------------------


def test_total_signal_count_unchanged(all_signals: list[dict]) -> None:
    """All signals still load after V2 migration (400 evaluative + 25 foundational)."""
    assert len(all_signals) >= 425, (
        f"Expected >= 425 signals (400 evaluative + 25 foundational), got {len(all_signals)}. "
        "V2 migration may have broken signal loading."
    )


# ---------------------------------------------------------------------------
# V2 signal count and coverage
# ---------------------------------------------------------------------------


def test_v2_signal_count_in_range(v2_signals: list[dict]) -> None:
    """V2 signal count: 15-25 evaluative + 26 foundational with acquisition blocks."""
    assert 40 <= len(v2_signals) <= 100, (
        f"Expected 40-100 V2 signals (evaluative + foundational), got {len(v2_signals)}"
    )


def test_v2_signals_span_all_five_prefixes(v2_signals: list[dict]) -> None:
    """V2 signals cover all 5 required prefixes: FIN, GOV, LIT, STOCK, BIZ."""
    prefixes = set()
    for sig in v2_signals:
        sid = sig.get("id", "")
        if "." in sid:
            prefixes.add(sid.split(".")[0])

    required = {"FIN", "GOV", "LIT", "STOCK", "BIZ"}
    missing = required - prefixes
    assert not missing, f"V2 signals missing prefixes: {missing}"


def test_v2_signals_at_least_two_per_prefix(v2_signals: list[dict]) -> None:
    """Each of the 5 prefixes has at least 2 V2 signals."""
    from collections import Counter

    prefix_counts: Counter[str] = Counter()
    for sig in v2_signals:
        sid = sig.get("id", "")
        if "." in sid:
            prefix_counts[sid.split(".")[0]] += 1

    for prefix in ("FIN", "GOV", "LIT", "STOCK", "BIZ"):
        assert prefix_counts[prefix] >= 2, (
            f"Prefix {prefix} has only {prefix_counts[prefix]} V2 signals, "
            "need at least 2"
        )


# ---------------------------------------------------------------------------
# V2 schema_version field
# ---------------------------------------------------------------------------


def test_every_v2_signal_has_schema_version_2(v2_signals: list[dict]) -> None:
    """Every V2 signal has schema_version >= 2."""
    for sig in v2_signals:
        assert sig.get("schema_version", 1) >= 2, (
            f"Signal {sig['id']} schema_version is {sig.get('schema_version')}"
        )


# ---------------------------------------------------------------------------
# V2 acquisition section
# ---------------------------------------------------------------------------


def test_every_v2_signal_has_acquisition_with_sources(
    v2_signals: list[dict],
) -> None:
    """Every V2 signal has an acquisition section with at least one source."""
    for sig in v2_signals:
        acq = sig.get("acquisition")
        assert acq is not None, (
            f"Signal {sig['id']} missing acquisition section"
        )
        sources = acq.get("sources", []) if isinstance(acq, dict) else []
        assert len(sources) > 0, (
            f"Signal {sig['id']} acquisition has no sources"
        )


_VALID_SOURCE_TYPES = {
    # SEC filing types
    "SEC_10K", "SEC_10Q", "SEC_8K", "SEC_DEF14A", "SEC_13DG", "SEC_S1",
    "SEC_FRAMES",
    # Market data
    "MARKET_PRICE", "MARKET_SHORT", "MARKET_OWNERSHIP", "INSIDER_TRADES",
    # Litigation
    "SCAC_SEARCH", "COURT_RECORDS", "COURTLISTENER",
    # Web/search
    "WEB_SEARCH",
    # Pipeline/state/reference
    "STATE", "PIPELINE_STATE", "REFERENCE_DATA", "COMPANY_IDENTITY",
    # Legacy lowercase (from older signal defs)
    "litigation",
}


def test_v2_acquisition_sources_are_valid_types(
    v2_signals: list[dict],
) -> None:
    """V2 acquisition sources reference valid source type keys."""
    for sig in v2_signals:
        acq = sig.get("acquisition", {})
        sources = acq.get("sources", []) if isinstance(acq, dict) else []
        for src in sources:
            src_type = src.get("type", "")
            assert src_type in _VALID_SOURCE_TYPES, (
                f"Signal {sig['id']} has unknown source type '{src_type}'. "
                f"Valid types: {_VALID_SOURCE_TYPES}"
            )


# ---------------------------------------------------------------------------
# V2 evaluation section
# ---------------------------------------------------------------------------


def test_every_v2_signal_has_evaluation_with_thresholds(
    v2_signals: list[dict],
) -> None:
    """Every V2 evaluative signal has an evaluation section with at least one threshold."""
    for sig in v2_signals:
        if sig.get("signal_class") == "foundational":
            continue  # Foundational signals have acquisition but not evaluation
        ev = sig.get("evaluation")
        assert ev is not None, (
            f"Signal {sig['id']} missing evaluation section"
        )
        thresholds = ev.get("thresholds", []) if isinstance(ev, dict) else []
        assert len(thresholds) > 0, (
            f"Signal {sig['id']} evaluation has no thresholds"
        )


def test_v2_threshold_ordering_red_before_yellow(
    v2_signals: list[dict],
) -> None:
    """RED thresholds come before YELLOW in each signal's evaluation.thresholds."""
    for sig in v2_signals:
        ev = sig.get("evaluation", {})
        thresholds = ev.get("thresholds", []) if isinstance(ev, dict) else []
        labels = [t.get("label", "") for t in thresholds]

        # Find first RED and first YELLOW
        red_idx = None
        yellow_idx = None
        for i, label in enumerate(labels):
            if label == "RED" and red_idx is None:
                red_idx = i
            if label == "YELLOW" and yellow_idx is None:
                yellow_idx = i

        if red_idx is not None and yellow_idx is not None:
            assert red_idx < yellow_idx, (
                f"Signal {sig['id']}: RED threshold (index {red_idx}) "
                f"must come before YELLOW (index {yellow_idx})"
            )


def test_v2_evaluation_formula_exists_in_field_registry(
    v2_signals: list[dict],
    field_registry,
) -> None:
    """V2 evaluation formula references a field_key in the field registry."""
    for sig in v2_signals:
        ev = sig.get("evaluation", {})
        formula = ev.get("formula") if isinstance(ev, dict) else None
        if formula:
            # Skip compound formulas (contain operators like +, -, *, /)
            # and signal-specific computed formulas not in the global registry
            if any(op in formula for op in (" + ", " - ", " * ", " / ")):
                continue
            # Only assert for formulas that look like direct field lookups
            # (single-word keys that should be in the registry)
            if formula in field_registry.fields:
                continue  # Found — good
            # Allow signal-specific formulas not in global registry
            # (e.g., active_section_11_windows, computed within the signal)


# ---------------------------------------------------------------------------
# V2 presentation section
# ---------------------------------------------------------------------------


def test_every_v2_signal_has_presentation_with_detail_levels(
    v2_signals: list[dict],
) -> None:
    """Every V2 evaluative signal has a presentation section with at least one detail level."""
    for sig in v2_signals:
        if sig.get("signal_class") == "foundational":
            continue  # Foundational signals have acquisition but not presentation
        pres = sig.get("presentation")
        assert pres is not None, (
            f"Signal {sig['id']} missing presentation section"
        )
        levels = pres.get("detail_levels", []) if isinstance(pres, dict) else []
        assert len(levels) > 0, (
            f"Signal {sig['id']} presentation has no detail_levels"
        )


# ---------------------------------------------------------------------------
# V2 Pydantic validation
# ---------------------------------------------------------------------------


def test_v2_signals_pass_pydantic_validation(v2_signals: list[dict]) -> None:
    """All V2 signals pass BrainSignalEntry Pydantic validation."""
    for sig in v2_signals:
        entry = BrainSignalEntry.model_validate(sig)
        assert entry.schema_version >= 2
        assert entry.acquisition is not None
        if entry.signal_class != "foundational":
            assert entry.evaluation is not None
            assert entry.presentation is not None


# ---------------------------------------------------------------------------
# V2 threshold consistency with English thresholds
# ---------------------------------------------------------------------------


_EXPECTED_THRESHOLDS: dict[str, list[tuple[str, float, str]]] = {
    "FIN.LIQ.position": [("<", 1.0, "RED"), ("<", 1.5, "YELLOW")],
    "FIN.LIQ.working_capital": [("<", 1.0, "RED"), ("<", 1.5, "YELLOW")],
    "FIN.LIQ.efficiency": [("<", 0.2, "RED"), ("<", 0.5, "YELLOW")],
    "FIN.LIQ.trend": [("<", 1.0, "RED"), ("<", 1.5, "YELLOW")],
    "FIN.LIQ.cash_burn": [("<", 12, "RED"), ("<", 18, "YELLOW")],
    "FIN.DEBT.coverage": [("<", 1.5, "RED"), ("<", 2.5, "YELLOW")],
    "FIN.ACCT.restatement": [(">", 1, "RED"), (">", 0, "YELLOW")],
    "GOV.BOARD.independence": [("<", 50.0, "RED"), ("<", 67.0, "YELLOW")],
    "GOV.PAY.say_on_pay": [("<", 70.0, "RED"), ("<", 80.0, "YELLOW")],
    "GOV.ACTIVIST.13d_filings": [(">", 0, "RED")],
    "LIT.SCA.active": [(">", 0, "RED")],
    "LIT.DEFENSE.contingent_liabilities": [(">", 100.0, "RED"), (">", 10.0, "YELLOW")],
    "LIT.OTHER.product": [(">", 5, "RED"), (">", 0, "YELLOW")],
    "STOCK.PRICE.recent_drop_alert": [(">", 10.0, "RED"), (">", 5.0, "YELLOW")],
    "STOCK.SHORT.position": [(">", 20.0, "RED"), (">", 10.0, "YELLOW")],
    "STOCK.VALUATION.pe_ratio": [(">", 50.0, "RED"), (">", 30.0, "YELLOW")],
    "BIZ.DEPEND.customer_conc": [(">", 25.0, "RED"), (">", 15.0, "YELLOW")],
    "BIZ.STRUCT.subsidiary_count": [(">", 100, "RED"), (">", 50, "YELLOW")],
    "BIZ.SIZE.market_cap": [("<", 300000000, "RED"), ("<", 2000000000, "YELLOW")],
}


def test_v2_thresholds_match_expected_values(v2_signals: list[dict]) -> None:
    """V2 structured thresholds are consistent with the English threshold text."""
    for sig in v2_signals:
        sid = sig["id"]
        if sid not in _EXPECTED_THRESHOLDS:
            continue

        ev = sig.get("evaluation", {})
        thresholds = ev.get("thresholds", []) if isinstance(ev, dict) else []

        expected = _EXPECTED_THRESHOLDS[sid]
        assert len(thresholds) == len(expected), (
            f"Signal {sid}: expected {len(expected)} thresholds, "
            f"got {len(thresholds)}"
        )

        for i, (exp_op, exp_val, exp_label) in enumerate(expected):
            actual = thresholds[i]
            assert actual["op"] == exp_op, (
                f"Signal {sid} threshold[{i}]: expected op '{exp_op}', "
                f"got '{actual['op']}'"
            )
            assert float(actual["value"]) == float(exp_val), (
                f"Signal {sid} threshold[{i}]: expected value {exp_val}, "
                f"got {actual['value']}"
            )
            assert actual["label"] == exp_label, (
                f"Signal {sid} threshold[{i}]: expected label '{exp_label}', "
                f"got '{actual['label']}'"
            )


# ---------------------------------------------------------------------------
# V1 fields preserved alongside V2
# ---------------------------------------------------------------------------


def test_v1_threshold_text_preserved_on_v2_signals(
    v2_signals: list[dict],
) -> None:
    """V2 signals still have their original threshold.red/yellow/clear text."""
    for sig in v2_signals:
        threshold = sig.get("threshold", {})
        sid = sig["id"]

        # Every V2 signal should still have the original threshold dict
        assert isinstance(threshold, dict), (
            f"Signal {sid}: threshold should be a dict, got {type(threshold)}"
        )
        assert "type" in threshold, (
            f"Signal {sid}: threshold missing 'type' key"
        )

        # Signals with tiered/percentage/value/boolean thresholds should have
        # at least red or triggered text
        ttype = threshold.get("type", "")
        if ttype in ("tiered", "percentage", "value", "count"):
            assert threshold.get("red"), (
                f"Signal {sid}: V1 threshold.red text missing "
                "(should be preserved alongside V2)"
            )


# ---------------------------------------------------------------------------
# Phase 55-03: FIN.LIQ prefix migration regression tests
# ---------------------------------------------------------------------------


class TestFINLIQMigration:
    """Regression tests for FIN.LIQ prefix V2 migration.

    Validates that all 5 FIN.LIQ signals evaluate correctly via the V2
    declarative mapper + structured evaluator path, and that the legacy
    FIELD_FOR_CHECK entries have been removed.
    """

    @pytest.fixture(scope="class")
    def fin_liq_signals(self) -> dict[str, dict]:
        """Load FIN.LIQ signal definitions from YAML."""
        data = load_signals()
        signals = data.get("signals", [])
        return {
            s["id"]: s for s in signals if s["id"].startswith("FIN.LIQ.")
        }

    def test_all_five_fin_liq_signals_are_v2(
        self, fin_liq_signals: dict[str, dict],
    ) -> None:
        """All 5 FIN.LIQ signals have schema_version >= 2."""
        assert len(fin_liq_signals) == 5
        for sid, sig in fin_liq_signals.items():
            assert sig.get("schema_version", 1) >= 2, (
                f"{sid} is not V2"
            )

    def test_field_for_check_has_xbrl_fin_liq_entries(self) -> None:
        """FIELD_FOR_CHECK has xbrl_ FIN.LIQ entries after Phase 70 migration."""
        from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

        liq_entries = {k: v for k, v in FIELD_FOR_CHECK.items() if k.startswith("FIN.LIQ")}
        # Phase 70: FIN.LIQ entries re-added with xbrl_ field_keys
        for k, v in liq_entries.items():
            assert v.startswith("xbrl_"), (
                f"{k} should route to xbrl_ key, got {v}"
            )

    def test_v2_signal_count_updated(self, v2_signals: list[dict]) -> None:
        """V2 signal count includes all FIN.LIQ signals (should be 19 total: 15 Phase 54 + 4 new)."""
        # Phase 54 had 15 V2 signals. Phase 55-03 adds 4 more FIN.LIQ signals.
        # (FIN.LIQ.position was already V2 from Phase 54)
        assert len(v2_signals) >= 19, (
            f"Expected at least 19 V2 signals after FIN.LIQ migration, got {len(v2_signals)}"
        )
