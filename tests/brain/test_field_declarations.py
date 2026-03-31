"""CI test: validate YAML field path declarations are syntactically valid.

Ensures that field paths declared in signal acquisition blocks use valid
dot-separated path segments that correspond to known state model field names.
Does NOT require a live state — validates path format only.

Phase 111-03: WIRE-05 enforcement.
"""

from __future__ import annotations

import re
from typing import Any

import pytest


# Known top-level state model paths (first segment of any dotted path)
VALID_TOP_LEVEL = {
    "extracted", "company", "analysis", "benchmark", "scoring",
    "acquired_data", "classification", "hazard_profile",
}

# Known second-level paths under each top-level
VALID_SECOND_LEVEL = {
    "extracted": {
        "financials", "market", "governance", "litigation",
        "ai_risk", "risk_factors", "text_signals", "ten_k_yoy",
    },
    "company": {
        "identity", "business_description", "market_cap", "employee_count",
        "filer_category", "years_public", "revenue_segments",
        "geographic_footprint", "subsidiary_count", "gics_code",
        "industry_classification", "business_model_description",
        "customer_concentration", "supplier_concentration",
        "operational_complexity", "financials", "key_person_risk",
        "revenue_model_type", "disruption_risk", "segment_lifecycle",
        "segment_margins", "risk_classification", "section_summary",
    },
    "analysis": {
        "checks_executed", "checks_passed", "checks_failed",
        "checks_skipped", "gap_search_summary", "signal_results",
        "patterns_detected", "temporal_signals", "forensic_composites",
        "executive_risk", "nlp_signals", "xbrl_forensics", "peril_map",
        "settlement_prediction", "section_densities",
        "pre_computed_narratives", "composite_results",
        "disposition_summary", "benchmarks",
    },
    "benchmark": {
        "peer_group_tickers", "peer_rankings", "peer_quality_scores",
        "sector_average_score", "relative_position", "metric_details",
        "frames_percentiles", "inherent_risk", "thesis_narrative",
        "risk_narrative", "risk_level", "claim_narrative",
    },
}


def _load_all_signals() -> list[dict[str, Any]]:
    """Load all brain signals from YAML files."""
    from do_uw.brain.brain_unified_loader import load_signals

    data = load_signals()
    return data.get("signals", [])


def _extract_field_paths(sig: dict[str, Any]) -> list[str]:
    """Extract all field paths declared in a signal's acquisition block."""
    paths: list[str] = []

    acquisition = sig.get("acquisition")
    if isinstance(acquisition, dict):
        sources = acquisition.get("sources")
        if isinstance(sources, list):
            for source in sources:
                if not isinstance(source, dict):
                    continue
                fields = source.get("fields")
                if not isinstance(fields, list):
                    continue
                for field_spec in fields:
                    if not isinstance(field_spec, dict):
                        continue
                    for key in ("path", "computed_from"):
                        p = field_spec.get(key)
                        if isinstance(p, str) and p:
                            paths.append(p)
                    fallbacks = field_spec.get("fallback_paths")
                    if isinstance(fallbacks, list):
                        for fb in fallbacks:
                            if isinstance(fb, str) and fb:
                                paths.append(fb)

    return paths


def test_yaml_field_paths_syntactically_valid() -> None:
    """Every declared field path must be dot-separated with valid segments."""
    signals = _load_all_signals()
    invalid: list[tuple[str, str, str]] = []

    for sig in signals:
        sig_id = sig.get("id", "UNKNOWN")
        paths = _extract_field_paths(sig)
        for path in paths:
            # Must be dot-separated
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", path):
                invalid.append((sig_id, path, "Invalid characters"))
                continue

            # First segment must be a known top-level
            segments = path.split(".")
            if segments[0] not in VALID_TOP_LEVEL:
                invalid.append((sig_id, path, f"Unknown top-level: {segments[0]}"))
                continue

            # Second segment should be known (if we have info)
            if len(segments) > 1 and segments[0] in VALID_SECOND_LEVEL:
                known = VALID_SECOND_LEVEL[segments[0]]
                if segments[1] not in known:
                    invalid.append((
                        sig_id, path,
                        f"Unknown second-level: {segments[0]}.{segments[1]}",
                    ))

    if invalid:
        msg_lines = [f"  {sid}: {p} ({reason})" for sid, p, reason in invalid[:20]]
        msg = "\n".join(msg_lines)
        if len(invalid) > 20:
            msg += f"\n  ... and {len(invalid) - 20} more"
        pytest.fail(
            f"{len(invalid)} signals have invalid field path declarations:\n{msg}"
        )


def test_field_path_not_empty_string() -> None:
    """No signal should declare an empty string as a field path."""
    signals = _load_all_signals()
    empty: list[str] = []

    for sig in signals:
        sig_id = sig.get("id", "UNKNOWN")
        acquisition = sig.get("acquisition")
        if not isinstance(acquisition, dict):
            continue
        sources = acquisition.get("sources")
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, dict):
                continue
            fields = source.get("fields")
            if not isinstance(fields, list):
                continue
            for field_spec in fields:
                if not isinstance(field_spec, dict):
                    continue
                for key in ("path", "computed_from"):
                    p = field_spec.get(key)
                    if p is not None and p == "":
                        empty.append(f"{sig_id}: empty {key}")

    if empty:
        pytest.fail(f"{len(empty)} signals have empty field paths: {empty[:10]}")
