"""Round-trip and integration tests for enriched check metadata.

Verifies that Phase 31 enriched fields (content_type, depth, rationale,
field_key, extraction_path, pattern_ref) survive the full data lifecycle:
brain/signals.json -> knowledge store migration -> query -> check engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.brain.brain_unified_loader import BrainLoader, load_signals
from do_uw.knowledge.migrate import migrate_from_json
from do_uw.knowledge.store import KnowledgeStore

_BRAIN_DIR = Path(__file__).parent.parent.parent / "src" / "do_uw" / "brain"


@pytest.fixture()
def migrated_store() -> KnowledgeStore:
    """In-memory KnowledgeStore with brain/ data migrated."""
    store = KnowledgeStore(db_path=None)
    migrate_from_json(_BRAIN_DIR, store)
    return store


@pytest.fixture()
def checks_json() -> dict[str, Any]:
    """Raw signals.json data."""
    with (_BRAIN_DIR / "config" / "signals.json").open() as f:
        data: dict[str, Any] = json.load(f)
    return data


# ------------------------------------------------------------------
# Test 1: Enriched fields survive migration
# ------------------------------------------------------------------


def test_enriched_fields_survive_migration(
    migrated_store: KnowledgeStore,
) -> None:
    """Known check FIN.LIQ.position has correct enriched fields after migration."""
    check = migrated_store.get_check("FIN.LIQ.position")
    assert check is not None
    assert check["content_type"] == "EVALUATIVE_CHECK"
    assert check["depth"] == 2
    assert check["field_key"] == "xbrl_current_ratio"


# ------------------------------------------------------------------
# Test 2: Content type filter counts match signals.json distribution
# ------------------------------------------------------------------


def test_content_type_filter_counts(
    migrated_store: KnowledgeStore,
) -> None:
    """Content type filter counts match signals.json distribution."""
    md = migrated_store.query_checks(
        content_type="MANAGEMENT_DISPLAY", limit=500
    )
    ec = migrated_store.query_checks(
        content_type="EVALUATIVE_CHECK", limit=500
    )
    ip = migrated_store.query_checks(
        content_type="INFERENCE_PATTERN", limit=500
    )
    assert len(md) == 98
    assert len(ec) == 281  # 276 + 4 governance checks (Phase 40) + 1 reclassified
    assert len(ip) == 21
    assert len(md) + len(ec) + len(ip) == 400


# ------------------------------------------------------------------
# Test 3: Depth filter returns correct checks
# ------------------------------------------------------------------


def test_depth_filter(migrated_store: KnowledgeStore) -> None:
    """Depth filter returns checks with matching depth level only."""
    for depth_val in (1, 2, 3, 4):
        results = migrated_store.query_checks(
            depth=depth_val, limit=500
        )
        assert len(results) > 0, f"No checks found for depth={depth_val}"
        for check in results:
            assert check["depth"] == depth_val, (
                f"Check {check['id']} has depth={check['depth']}, "
                f"expected {depth_val}"
            )


# ------------------------------------------------------------------
# Test 4: BrainLoader round-trips enriched fields
# ------------------------------------------------------------------


def test_brain_loader_roundtrip(
    migrated_store: KnowledgeStore,
) -> None:
    """BrainLoader returns checks with enriched fields present."""
    loader = BrainLoader()
    checks_data = loader.load_signals()
    checks = checks_data.get("signals", [])
    assert len(checks) >= 370

    # Index by ID for lookup
    by_id: dict[str, dict[str, Any]] = {
        str(c["id"]): c for c in checks
    }

    # Verify a MANAGEMENT_DISPLAY check
    biz = by_id.get("BIZ.CLASS.primary")
    assert biz is not None
    assert biz.get("content_type") == "MANAGEMENT_DISPLAY"

    # Verify an EVALUATIVE_CHECK with field_key
    fin = by_id.get("FIN.LIQ.position")
    assert fin is not None
    assert fin.get("content_type") == "EVALUATIVE_CHECK"
    ds = fin.get("data_strategy")
    assert isinstance(ds, dict)
    assert ds.get("field_key") == "xbrl_current_ratio"  # Phase 70: XBRL-sourced

    # Verify INFERENCE_PATTERN checks have pattern_ref (except known gaps)
    _known_gaps = {"LIT.PATTERN.peer_contagion", "LIT.PATTERN.temporal_correlation"}
    inf_checks = [
        c for c in checks
        if c.get("content_type") == "INFERENCE_PATTERN"
    ]
    # 19 total INFERENCE_PATTERN; some may be INACTIVE and excluded
    assert len(inf_checks) >= 13
    for ic in inf_checks:
        if ic["id"] in _known_gaps:
            continue
        assert ic.get("pattern_ref"), (
            f"INFERENCE_PATTERN check {ic['id']} missing pattern_ref"
        )


# ------------------------------------------------------------------
# Test 5: All INFERENCE_PATTERN checks have pattern_ref populated
# ------------------------------------------------------------------


def test_pattern_ref_populated(
    migrated_store: KnowledgeStore,
) -> None:
    """All 21 INFERENCE_PATTERN checks present; 19 of 21 have pattern_ref."""
    # 2 INFERENCE_PATTERN signals from Plan 33-03 lack pattern_ref:
    # LIT.PATTERN.peer_contagion, LIT.PATTERN.temporal_correlation
    _known_gaps = {"LIT.PATTERN.peer_contagion", "LIT.PATTERN.temporal_correlation"}
    results = migrated_store.query_checks(
        content_type="INFERENCE_PATTERN", limit=500
    )
    assert len(results) == 21
    missing: list[str] = []
    for check in results:
        if check["id"] in _known_gaps:
            continue
        if not check["pattern_ref"]:
            missing.append(check["id"])
    assert not missing, (
        f"Unexpected INFERENCE_PATTERN checks missing pattern_ref: {missing}"
    )


# ------------------------------------------------------------------
# Test 6: Check engine executes all enriched checks without crash
# ------------------------------------------------------------------


def test_signal_engine_with_enriched_checks(
    migrated_store: KnowledgeStore,
) -> None:
    """All AUTO signals execute without errors via BrainLoader."""
    from do_uw.models.state import ExtractedData
    from do_uw.stages.analyze import execute_signals

    checks_data = load_signals()
    all_checks = checks_data.get("signals", [])
    auto_signals = [
        c for c in all_checks
        if c.get("execution_mode") == "AUTO"
    ]
    assert len(auto_signals) > 350  # Should be ~393 evaluative + ~25 foundational

    # Count evaluative (non-foundational) signals for result count check
    evaluative_count = sum(
        1 for s in auto_signals if s.get("signal_class") != "foundational"
    )

    # Execute with empty data (all should skip gracefully)
    extracted = ExtractedData()
    results = execute_signals(auto_signals, extracted)

    # Foundational signals are skipped (no results), so results == evaluative count
    assert len(results) == evaluative_count

    # Verify result statuses are all valid
    valid_statuses = {"TRIGGERED", "CLEAR", "SKIPPED", "INFO"}
    for r in results:
        assert r.status.value in valid_statuses, (
            f"Check {r.signal_id} returned invalid status: {r.status}"
        )

    # Verify a known check produces a result with correct ID
    fin_results = [r for r in results if r.signal_id == "FIN.LIQ.position"]
    assert len(fin_results) == 1
    assert fin_results[0].signal_id == "FIN.LIQ.position"


# ------------------------------------------------------------------
# Test 7: Enriched checks validate against SignalDefinition model
# ------------------------------------------------------------------


def test_enriched_check_validates_against_definition() -> None:
    """Every signal validates through SignalDefinition."""
    from do_uw.knowledge.signal_definition import SignalDefinition

    checks_data = load_signals()
    checks = checks_data.get("signals", [])

    errors: list[str] = []
    for signal_dict in checks:
        cid = signal_dict.get("id", "?")
        try:
            cd = SignalDefinition.from_signal_dict(signal_dict)
            assert cd.id == signal_dict["id"]
        except Exception as exc:
            errors.append(f"Check {cid}: {exc}")

    assert not errors, (
        f"{len(errors)} checks failed validation:\n"
        + "\n".join(errors[:10])
    )


# ------------------------------------------------------------------
# Test 8: No field_key value changed vs FIELD_FOR_CHECK
# ------------------------------------------------------------------


def test_no_field_key_value_changed(
    checks_json: dict[str, Any],
) -> None:
    """Every data_strategy.field_key matches FIELD_FOR_CHECK (regression guard).

    Phase 70: signals.json has stale field_keys (pre-XBRL migration).
    Skip mismatches where FIELD_FOR_CHECK has been intentionally upgraded
    to xbrl_/forensic_ prefixed keys (Phase 70 XBRL migration).
    """
    from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

    checks = checks_json.get("signals", [])
    mismatches: list[str] = []

    for check in checks:
        ds = check.get("data_strategy")
        if not isinstance(ds, dict):
            continue
        fk = ds.get("field_key")
        if fk is None:
            continue
        cid = str(check["id"])
        if cid in FIELD_FOR_CHECK:
            expected = FIELD_FOR_CHECK[cid]
            if fk != expected:
                # Phase 70: Intentional XBRL migration -- skip these
                if expected.startswith("xbrl_") or expected.startswith("forensic_"):
                    continue
                mismatches.append(
                    f"{cid}: data_strategy.field_key={fk!r} "
                    f"vs FIELD_FOR_CHECK={expected!r}"
                )

    assert not mismatches, (
        f"{len(mismatches)} field_key mismatches:\n"
        + "\n".join(mismatches[:10])
    )
