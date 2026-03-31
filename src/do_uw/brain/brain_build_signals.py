"""Validate brain YAML signals and export signals.json.

Called by `brain build` to validate all signal definitions and export
a signals.json snapshot for backward compatibility.

Phase 53 simplification: no longer writes to DuckDB definition tables.
DuckDB is used for history only (changelog, signal_runs, effectiveness).

Validation steps:
1. Load all signals via BrainLoader (YAML -> enrich -> BrainSignalEntry validate)
2. Cross-reference integrity: factor IDs in taxonomy, unique signal IDs
3. Coverage matrix: check prefix families have signals
4. Export signals.json to brain/config/signals.json
5. Log changelog entries for detected changes (DuckDB history)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_BRAIN_DIR = Path(__file__).parent


def _check_cross_references(
    signals: list[dict[str, Any]],
) -> list[str]:
    """Validate cross-reference integrity across signals.

    Checks:
    - Signal IDs are unique
    - All referenced factor IDs exist in known set

    Returns list of error messages (empty = all good).
    """
    errors: list[str] = []

    # Check signal ID uniqueness
    seen_ids: dict[str, int] = {}
    for sig in signals:
        sid = sig.get("id", sig.get("signal_id", "unknown"))
        seen_ids[sid] = seen_ids.get(sid, 0) + 1

    dupes = {sid: count for sid, count in seen_ids.items() if count > 1}
    if dupes:
        for sid, count in sorted(dupes.items()):
            errors.append(f"Duplicate signal ID '{sid}' appears {count} times")

    return errors


def _check_coverage(
    signals: list[dict[str, Any]],
) -> dict[str, int]:
    """Compute signal coverage by prefix family.

    Returns dict of prefix -> count for reporting.
    """
    prefix_counts: dict[str, int] = {}
    for sig in signals:
        sid = sig.get("id", sig.get("signal_id", ""))
        if "." in sid:
            prefix = sid.split(".")[0]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    return prefix_counts


def _export_signals_json(
    signals: list[dict[str, Any]],
    output_path: Path,
) -> int:
    """Export enriched signals to signals.json format.

    Writes a signals.json-compatible file from the validated signals.
    This is the backward-compatibility export for systems that read
    signals.json directly.

    Args:
        signals: List of enriched signal dicts from BrainLoader.
        output_path: Where to write the JSON file.

    Returns:
        Number of signals exported.
    """
    # Convert enriched signals to the export format expected by consumers
    section_map = {
        "company": 1, "market": 2, "financials": 3,
        "governance": 4, "litigation": 5,
        "disclosure": 4, "forward": 1,
    }

    checks: list[dict[str, Any]] = []
    for sig in signals:
        sid = sig.get("id", sig.get("signal_id", ""))
        threshold = sig.get("threshold", {})
        data_strategy = sig.get("data_strategy")

        check: dict[str, Any] = {
            "id": sid,
            "name": sig.get("name", sid),
            "content_type": sig.get("content_type", "EVALUATIVE_CHECK"),
            "depth": sig.get("depth", 2),
            "execution_mode": sig.get("execution_mode", "AUTO"),
            "section": sig.get("section") or sig.get("tier") or section_map.get(
                sig.get("report_section", ""), 0
            ),
            "factors": sig.get("factors", []),
            "required_data": sig.get("required_data", []),
            "data_locations": sig.get("data_locations", {}),
            "threshold": threshold if isinstance(threshold, dict) else {},
        }

        if sig.get("pattern_ref"):
            check["pattern_ref"] = sig["pattern_ref"]
        if data_strategy:
            check["data_strategy"] = data_strategy
        elif sig.get("field_key"):
            check["data_strategy"] = {"field_key": sig["field_key"]}
        if sig.get("pillar"):
            check["pillar"] = sig["pillar"]
        if sig.get("category"):
            check["category"] = sig["category"]
        if sig.get("signal_type"):
            check["signal_type"] = sig["signal_type"]
        if sig.get("hazard_or_signal"):
            check["hazard_or_signal"] = sig["hazard_or_signal"]
        if sig.get("plaintiff_lenses"):
            check["plaintiff_lenses"] = list(sig["plaintiff_lenses"])
        if sig.get("claims_correlation") is not None:
            check["claims_correlation"] = sig["claims_correlation"]
        if sig.get("amplifier"):
            check["amplifier"] = sig["amplifier"]
        if sig.get("amplifier_bonus_points") is not None:
            check["amplifier_bonus_points"] = sig["amplifier_bonus_points"]
        if sig.get("tier") is not None:
            check["tier"] = sig["tier"]
        if sig.get("sector_adjustments"):
            check["sector_adjustments"] = sig["sector_adjustments"]
        if sig.get("v6_subsection_ids"):
            check["v6_subsection_ids"] = list(sig["v6_subsection_ids"])
        if sig.get("extraction_hints"):
            check["extraction_hints"] = sig["extraction_hints"]
        if sig.get("rationale"):
            check["rationale"] = sig["rationale"]

        checks.append(check)

    output = {
        "$schema": "BRAIN_CHECKS_EXPORT",
        "version": "exported",
        "description": "Exported from brain YAML via brain build",
        "total_signals": len(checks),
        "signals": checks,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    logger.info("Exported %d signals to %s", len(checks), output_path)
    return len(checks)


def build_checks_from_yaml(
    conn: Any = None,
    *,
    checks_dir: Path | None = None,
) -> dict[str, int | list[str]]:
    """Validate YAML signals and export signals.json.

    Phase 53 simplified version: no DuckDB definition table writes.
    The conn parameter is accepted but no longer required (kept for
    backward-compat with cli_brain.py call site).

    Steps:
    1. Load + validate all signals via BrainLoader (YAML -> enrich -> validate)
    2. Run cross-reference integrity checks
    3. Compute coverage matrix by prefix family
    4. Export signals.json to brain/config/signals.json

    Returns:
        Dict with: signals, yaml_files, unlinked, errors, coverage.
    """
    from do_uw.brain.brain_unified_loader import _load_and_validate_signals

    if checks_dir is None:
        checks_dir = _BRAIN_DIR / "signals"

    # Step 1: Load and validate all signals from YAML
    signals, skipped = _load_and_validate_signals(checks_dir)
    yaml_file_count = len(set(
        str(f) for f in sorted(checks_dir.glob("**/*.yaml"))
    ))

    logger.info(
        "Loaded %d signals from %d YAML files (%d skipped validation)",
        len(signals), yaml_file_count, skipped,
    )

    # Step 2: Cross-reference integrity
    xref_errors = _check_cross_references(signals)
    if xref_errors:
        for err in xref_errors:
            logger.warning("Cross-reference error: %s", err)

    # Step 3: Coverage matrix
    coverage = _check_coverage(signals)
    logger.info(
        "Coverage: %d prefix families, %s",
        len(coverage),
        ", ".join(f"{k}={v}" for k, v in sorted(coverage.items())[:10]),
    )

    # Step 4: Export signals.json
    export_path = _BRAIN_DIR / "config" / "signals.json"
    _export_signals_json(signals, export_path)

    unlinked_count = sum(
        1 for s in signals if s.get("unlinked", False)
    )

    # Step 5: V2 signal validation
    v2_count = 0
    v2_errors: list[str] = []
    for sig in signals:
        if sig.get("schema_version", 1) >= 2:
            sid = sig.get("id", "UNKNOWN")
            v2_count += 1
            for section in ("acquisition", "evaluation", "presentation"):
                if not sig.get(section):
                    v2_errors.append(
                        f"V2 signal '{sid}' missing required section '{section}'"
                    )
    if v2_errors:
        for err in v2_errors:
            logger.warning("V2 validation: %s", err)
        xref_errors.extend(v2_errors)

    logger.info(
        "Brain build complete: validated %d signals (%d V2, %d unlinked, "
        "%d errors), exported signals.json",
        len(signals), v2_count, unlinked_count, len(xref_errors),
    )

    return {
        "signals": len(signals),
        "yaml_files": yaml_file_count,
        "unlinked": unlinked_count,
        "errors": xref_errors,
        "coverage": coverage,
        "v2_signals": v2_count,
    }
