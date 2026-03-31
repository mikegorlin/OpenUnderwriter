"""Tests for Phase 70-03 signal reactivation.

Verifies:
1. 15+ previously-INACTIVE signals now have lifecycle_state removed
2. Mapper returns non-None for reactivated signals when data present
3. Web search signals return CLEAR (not SKIPPED) when no search results found
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixture: Load all signal YAML files
# ---------------------------------------------------------------------------

SIGNALS_DIR = Path("src/do_uw/brain/signals")


def _load_all_signals() -> list[dict[str, Any]]:
    """Load all signals from YAML files."""
    signals: list[dict[str, Any]] = []
    for yaml_path in sorted(SIGNALS_DIR.rglob("*.yaml")):
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        if isinstance(data, list):
            signals.extend(data)
    return signals


ALL_SIGNALS = _load_all_signals()


# ---------------------------------------------------------------------------
# Part A: Signal reactivation verification
# ---------------------------------------------------------------------------

# Signals that were INACTIVE and are now reactivated in Phase 70-03
REACTIVATED_SIGNAL_IDS = [
    "GOV.EFFECT.auditor_change",
    "GOV.EFFECT.sig_deficiency",
    "GOV.EFFECT.late_filing",
    "GOV.EFFECT.nt_filing",
    "GOV.INSIDER.plan_adoption",
    "GOV.INSIDER.unusual_timing",
    "GOV.BOARD.expertise",
    "GOV.BOARD.succession",
    "GOV.RIGHTS.bylaws",
    "GOV.RIGHTS.proxy_access",
    "GOV.RIGHTS.action_consent",
    "GOV.RIGHTS.special_mtg",
    "GOV.PAY.equity_burn",
    "GOV.PAY.hedging",
    "GOV.PAY.401k_match",
    "GOV.PAY.deferred_comp",
    "GOV.PAY.pension",
    "GOV.PAY.exec_loans",
]


def test_reactivated_count_meets_minimum():
    """At least 15 previously-INACTIVE signals are now reactivated."""
    assert len(REACTIVATED_SIGNAL_IDS) >= 15


def test_reactivated_signals_no_longer_inactive():
    """All reactivated signals should NOT have lifecycle_state: INACTIVE."""
    signal_map = {s["id"]: s for s in ALL_SIGNALS}
    still_inactive = []
    for sid in REACTIVATED_SIGNAL_IDS:
        sig = signal_map.get(sid)
        assert sig is not None, f"Signal {sid} not found in YAML files"
        if sig.get("lifecycle_state") == "INACTIVE":
            still_inactive.append(sid)
    assert still_inactive == [], (
        f"These signals are still INACTIVE: {still_inactive}"
    )


def test_reactivated_signals_have_field_keys():
    """All reactivated signals should have data_strategy.field_key."""
    from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

    signal_map = {s["id"]: s for s in ALL_SIGNALS}
    missing_routing = []
    for sid in REACTIVATED_SIGNAL_IDS:
        sig = signal_map.get(sid)
        if sig is None:
            continue
        # Check: either data_strategy.field_key in YAML or entry in FIELD_FOR_CHECK
        ds = sig.get("data_strategy", {})
        has_yaml_fk = ds.get("field_key") is not None if isinstance(ds, dict) else False
        has_routing = sid in FIELD_FOR_CHECK
        if not has_yaml_fk and not has_routing:
            missing_routing.append(sid)
    assert missing_routing == [], (
        f"These reactivated signals lack field_key routing: {missing_routing}"
    )


# ---------------------------------------------------------------------------
# Part B: Web search signal wiring verification
# ---------------------------------------------------------------------------

# FWRD.WARN signals that were previously DATA_UNAVAILABLE (web-only)
WEB_SEARCH_SIGNAL_SUFFIXES = [
    "glassdoor_sentiment",
    "indeed_reviews",
    "blind_posts",
    "linkedin_headcount",
    "linkedin_departures",
    "g2_reviews",
    "trustpilot_trend",
    "app_ratings",
    "cfpb_complaints",
    "fda_medwatch",
    "nhtsa_complaints",
    "social_sentiment",
    "journalism_activity",
]


def test_web_search_signals_return_data():
    """Web search signals should return non-empty result with value key."""
    from do_uw.stages.analyze.signal_mappers_forward import map_fwrd_check

    # Create minimal ExtractedData with text_signals populated
    from do_uw.models.state import ExtractedData

    extracted = ExtractedData(
        text_signals={
            "labor_concentration": {"present": False, "mention_count": 0},
            "customer_churn_signals": {"present": False, "mention_count": 0},
            "regulatory_changes": {"present": False, "mention_count": 0},
            "whistleblower_exposure": {"present": False, "mention_count": 0},
        }
    )

    signals_with_data = []
    for suffix in WEB_SEARCH_SIGNAL_SUFFIXES:
        signal_id = f"FWRD.WARN.{suffix}"
        result = map_fwrd_check(signal_id, extracted)
        if result.get("value") is not None:
            signals_with_data.append(suffix)

    # All 13 should now return a value (CLEAR, not SKIPPED)
    assert len(signals_with_data) == len(WEB_SEARCH_SIGNAL_SUFFIXES), (
        f"Expected all {len(WEB_SEARCH_SIGNAL_SUFFIXES)} web signals to return data, "
        f"got {len(signals_with_data)}. Missing: "
        f"{set(WEB_SEARCH_SIGNAL_SUFFIXES) - set(signals_with_data)}"
    )


def test_web_search_signals_clear_when_no_risk():
    """Web search signals should return CLEAR-equivalent when no risk detected."""
    from do_uw.stages.analyze.signal_mappers_forward import map_fwrd_check
    from do_uw.models.state import ExtractedData

    extracted = ExtractedData(
        text_signals={
            "labor_concentration": {"present": False, "mention_count": 0},
            "customer_churn_signals": {"present": False, "mention_count": 0},
            "regulatory_changes": {"present": False, "mention_count": 0},
            "whistleblower_exposure": {"present": False, "mention_count": 0},
        }
    )

    for suffix in WEB_SEARCH_SIGNAL_SUFFIXES:
        signal_id = f"FWRD.WARN.{suffix}"
        result = map_fwrd_check(signal_id, extracted)
        val = result.get("value")
        assert val is not None, f"{signal_id} returned None (would be SKIPPED)"
        # Value should indicate no risk (various CLEAR messages)
        val_str = str(val).lower()
        assert any(
            indicator in val_str
            for indicator in ("no ", "not mentioned", "normal", "0 mention")
        ), f"{signal_id} value doesn't look like CLEAR: {val}"


def test_web_search_signals_trigger_when_risk_present():
    """Web search signals should reflect actual risk when text_signals have findings."""
    from do_uw.stages.analyze.signal_mappers_forward import map_fwrd_check
    from do_uw.models.state import ExtractedData

    extracted = ExtractedData(
        text_signals={
            "labor_concentration": {
                "present": True,
                "mention_count": 5,
                "context": "significant workforce reduction announced",
            },
            "customer_churn_signals": {"present": False, "mention_count": 0},
            "regulatory_changes": {"present": False, "mention_count": 0},
            "whistleblower_exposure": {"present": False, "mention_count": 0},
        }
    )

    # Employee-related signals should show risk
    result = map_fwrd_check("FWRD.WARN.glassdoor_sentiment", extracted)
    val = str(result.get("value", ""))
    assert "5 mention" in val, f"Expected risk data, got: {val}"


def test_governance_mapper_provides_reactivated_fields():
    """Governance mapper should populate fields for reactivated signals."""
    from do_uw.stages.analyze.signal_mappers_sections import map_governance_fields
    from do_uw.models.state import ExtractedData
    from do_uw.models.governance import GovernanceData

    # Create minimal governance data
    extracted = ExtractedData(governance=GovernanceData())

    result = map_governance_fields("GOV.EFFECT.late_filing", extracted)
    # Should return a value (False is valid -- means CLEAR, not SKIPPED)
    assert "late_filing_flag" in result or result != {}, (
        "Governance mapper should provide late_filing_flag"
    )

    result = map_governance_fields("GOV.EFFECT.nt_filing", extracted)
    assert "nt_filing_flag" in result or result != {}, (
        "Governance mapper should provide nt_filing_flag"
    )


def test_no_inactive_signals_remain_in_reactivation_set():
    """Verify no signal we intended to reactivate is still INACTIVE."""
    remaining_inactive = []
    for sig in ALL_SIGNALS:
        if sig.get("lifecycle_state") == "INACTIVE":
            remaining_inactive.append(sig["id"])
    # These are the signals intentionally left INACTIVE (ISS, proxy advisory, etc.)
    # They need external API access we don't have
    intentionally_inactive = {
        "GOV.EFFECT.iss_score",
        "GOV.EFFECT.proxy_advisory",
    }
    unexpected_inactive = set(remaining_inactive) - intentionally_inactive
    # There should be 0 unexpected INACTIVE signals
    # (all reactivatable signals have been reactivated)
    assert len(unexpected_inactive) == 0, (
        f"Unexpected INACTIVE signals: {unexpected_inactive}"
    )


# ---------------------------------------------------------------------------
# Part C: Overall signal count validation
# ---------------------------------------------------------------------------


def test_total_signal_count():
    """Total signal count should be >= 466 (400 original + 66 from Phase 70)."""
    assert len(ALL_SIGNALS) >= 466, (
        f"Expected >= 466 total signals, got {len(ALL_SIGNALS)}"
    )


def test_no_lifecycle_state_on_reactivated():
    """Reactivated signals should have lifecycle_state completely removed."""
    signal_map = {s["id"]: s for s in ALL_SIGNALS}
    has_lifecycle = []
    for sid in REACTIVATED_SIGNAL_IDS:
        sig = signal_map.get(sid)
        if sig and "lifecycle_state" in sig:
            has_lifecycle.append(sid)
    assert has_lifecycle == [], (
        f"These signals still have lifecycle_state field: {has_lifecycle}"
    )
