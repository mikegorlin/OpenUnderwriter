#!/usr/bin/env python3
"""Backtest audit tool: audit TRIGGERED and SKIPPED check results.

Loads a state.json, reruns all brain checks, and categorizes each result
into suspected false triggers, confirmed genuine triggers, routing failures,
and legitimately unavailable data.

Usage:
    uv run python scripts/backtest_audit.py output/AAPL/state.json
    uv run python scripts/backtest_audit.py output/TSLA/state.json
    uv run python scripts/backtest_audit.py output/AAPL/state.json --json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from do_uw.knowledge.backtest import run_backtest  # noqa: E402
from do_uw.stages.analyze.check_mappers import map_check_data  # noqa: E402

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Known false-trigger patterns and routing problems
# ---------------------------------------------------------------------------

# Check IDs where specific values are known false triggers
FALSE_TRIGGER_PATTERNS: dict[str, dict[str, Any]] = {
    # Employee count triggering as labor dependency
    "BIZ.DEPEND.labor": {
        "false_if": lambda val, src: src == "employee_count" or (
            isinstance(val, (int, float)) and val > 1000
        ),
        "reason": "Employee count mistakenly routed as labor risk flag count",
    },
    # Stock price triggering as PE ratio
    "STOCK.VALUATION.pe_ratio": {
        "false_if": lambda val, src: src == "current_price",
        "reason": "Stock price mistakenly routed as PE ratio",
    },
    # EXEC.PRIOR_LIT with hallucinated val=75.0
    "EXEC.PRIOR_LIT.any_officer": {
        "false_if": lambda val, src: isinstance(val, (int, float)) and val > 20,
        "reason": "Suspiciously high prior litigation count (likely hallucinated data)",
    },
    "EXEC.PRIOR_LIT.ceo_cfo": {
        "false_if": lambda val, src: isinstance(val, (int, float)) and val > 20,
        "reason": "Suspiciously high prior litigation count (likely hallucinated data)",
    },
}


def _classify_triggered(
    check_id: str,
    check_result: dict[str, Any],
    check_def: dict[str, Any],
) -> dict[str, Any]:
    """Classify a TRIGGERED result as genuine or suspected false.

    Returns a dict with classification details.
    """
    value = check_result.get("value")
    source = check_result.get("source", "")
    evidence = check_result.get("evidence", "")
    threshold = check_def.get("threshold", {})
    threshold_level = check_result.get("threshold_level", "")

    entry = {
        "check_id": check_id,
        "check_name": check_def.get("name", ""),
        "value": value,
        "source_field": source,
        "evidence": evidence,
        "threshold_red": threshold.get("red", ""),
        "threshold_yellow": threshold.get("yellow", ""),
        "threshold_level": threshold_level,
        "content_type": check_def.get("content_type", ""),
    }

    # Check against known false-trigger patterns
    pattern = FALSE_TRIGGER_PATTERNS.get(check_id)
    if pattern is not None:
        try:
            if pattern["false_if"](value, source):
                entry["classification"] = "FALSE_TRIGGER"
                entry["reason"] = pattern["reason"]
                return entry
        except Exception:
            pass

    entry["classification"] = "GENUINE"
    entry["reason"] = ""
    return entry


def _classify_skipped(
    check_id: str,
    check_result: dict[str, Any],
    check_def: dict[str, Any],
    mapped_data: dict[str, Any],
) -> dict[str, Any]:
    """Classify a SKIPPED result into routing failure or legitimate unavailable.

    A routing failure means: the data exists in the state but the mapper
    couldn't find it (bad field routing). Legitimate unavailable means:
    the data genuinely doesn't exist for this company.
    """
    data_status = check_result.get("data_status", "")
    data_reason = check_result.get("data_status_reason", "")
    evidence = check_result.get("evidence", "")

    entry = {
        "check_id": check_id,
        "check_name": check_def.get("name", ""),
        "data_status": data_status,
        "data_status_reason": data_reason,
        "evidence": evidence,
        "content_type": check_def.get("content_type", ""),
        "expected_source": check_def.get("data_strategy", {}).get("primary_source", ""),
        "field_key": check_def.get("data_strategy", {}).get("field_key", ""),
    }

    # NOT_APPLICABLE is a legitimate skip (sector filter)
    if data_status == "NOT_APPLICABLE":
        entry["classification"] = "NOT_APPLICABLE"
        entry["reason"] = "Check not applicable to company sector"
        return entry

    # Check if mapper returned empty dict (no fields mapped)
    if not mapped_data:
        entry["classification"] = "DATA_UNAVAILABLE"
        entry["reason"] = "No fields mapped for this check prefix"
        return entry

    # Check if all mapped values are None
    all_none = all(v is None for v in mapped_data.values())
    if all_none:
        entry["classification"] = "DATA_UNAVAILABLE"
        entry["reason"] = f"All mapped fields are None: {list(mapped_data.keys())}"
        return entry

    # Data exists but was filtered out by narrow_result -- routing failure
    has_data = any(v is not None for v in mapped_data.values())
    if has_data:
        non_none_keys = [k for k, v in mapped_data.items() if v is not None]
        entry["classification"] = "ROUTING_FAILURE"
        entry["reason"] = (
            f"Data exists in fields {non_none_keys} but check routes to "
            f"'{entry['field_key']}' which is not available"
        )
        return entry

    entry["classification"] = "DATA_UNAVAILABLE"
    entry["reason"] = "Data genuinely not available"
    return entry


def audit_backtest(
    state_path: Path,
) -> dict[str, Any]:
    """Run a full audit of check results against a state file.

    Returns a structured audit report with:
    - triggered_false: suspected false triggers
    - triggered_genuine: confirmed genuine triggers
    - skipped_routing_failure: checks that should have fired
    - skipped_unavailable: legitimately unavailable
    - skipped_not_applicable: sector filter skips
    - summary: counts and stats
    """
    from do_uw.models.state import AnalysisState

    # Load state
    with open(state_path, encoding="utf-8") as f:
        data = json.load(f)
    state = AnalysisState.model_validate(data)
    extracted = state.extracted
    company = state.company

    if extracted is None:
        return {"error": "No extracted data in state file"}

    # Load checks from JSON (same as backtest uses)
    checks_json_path = Path("src/do_uw/brain/checks.json")
    with open(checks_json_path, encoding="utf-8") as f:
        checks_data = json.load(f)
    checks = checks_data["checks"]

    # Build check lookup
    check_by_id: dict[str, dict[str, Any]] = {c["id"]: c for c in checks}

    # Execute all checks
    from do_uw.stages.analyze.check_engine import execute_checks

    results = execute_checks(checks, extracted, company)

    # Build results lookup
    results_by_id: dict[str, dict[str, Any]] = {}
    for r in results:
        results_by_id[r.check_id] = {
            "status": r.status.value,
            "value": r.value,
            "source": r.source,
            "evidence": r.evidence,
            "threshold_level": r.threshold_level,
            "data_status": str(r.data_status) if r.data_status else "",
            "data_status_reason": r.data_status_reason,
        }

    # Classify each result
    triggered_false: list[dict[str, Any]] = []
    triggered_genuine: list[dict[str, Any]] = []
    skipped_routing: list[dict[str, Any]] = []
    skipped_unavailable: list[dict[str, Any]] = []
    skipped_not_applicable: list[dict[str, Any]] = []
    clear_results: list[dict[str, Any]] = []
    info_results: list[dict[str, Any]] = []

    for check_id, result_data in results_by_id.items():
        check_def = check_by_id.get(check_id, {})
        status = result_data["status"]

        if status == "TRIGGERED":
            entry = _classify_triggered(check_id, result_data, check_def)
            if entry["classification"] == "FALSE_TRIGGER":
                triggered_false.append(entry)
            else:
                triggered_genuine.append(entry)

        elif status == "SKIPPED":
            # Get the pre-narrow mapped data to diagnose routing
            mapped = map_check_data(check_id, check_def, extracted, company)
            entry = _classify_skipped(check_id, result_data, check_def, mapped)
            if entry["classification"] == "ROUTING_FAILURE":
                skipped_routing.append(entry)
            elif entry["classification"] == "NOT_APPLICABLE":
                skipped_not_applicable.append(entry)
            else:
                skipped_unavailable.append(entry)

        elif status == "CLEAR":
            clear_results.append({
                "check_id": check_id,
                "check_name": check_def.get("name", ""),
                "value": result_data["value"],
                "source_field": result_data["source"],
            })

        elif status == "INFO":
            info_results.append({
                "check_id": check_id,
                "check_name": check_def.get("name", ""),
                "value": result_data["value"],
                "source_field": result_data["source"],
            })

    return {
        "ticker": state.ticker,
        "state_path": str(state_path),
        "total_checks": len(results),
        "triggered_false": triggered_false,
        "triggered_genuine": triggered_genuine,
        "skipped_routing_failure": skipped_routing,
        "skipped_unavailable": skipped_unavailable,
        "skipped_not_applicable": skipped_not_applicable,
        "clear": clear_results,
        "info": info_results,
        "summary": {
            "triggered_total": len(triggered_false) + len(triggered_genuine),
            "triggered_false_count": len(triggered_false),
            "triggered_genuine_count": len(triggered_genuine),
            "skipped_total": len(skipped_routing) + len(skipped_unavailable) + len(skipped_not_applicable),
            "skipped_routing_failure_count": len(skipped_routing),
            "skipped_unavailable_count": len(skipped_unavailable),
            "skipped_not_applicable_count": len(skipped_not_applicable),
            "clear_count": len(clear_results),
            "info_count": len(info_results),
        },
    }


def format_report(audit: dict[str, Any]) -> str:
    """Format the audit result as a human-readable report."""
    lines: list[str] = []
    summary = audit["summary"]

    lines.append(f"{'='*70}")
    lines.append(f"BACKTEST AUDIT REPORT: {audit['ticker']}")
    lines.append(f"State: {audit['state_path']}")
    lines.append(f"Total checks evaluated: {audit['total_checks']}")
    lines.append(f"{'='*70}")
    lines.append("")

    lines.append("SUMMARY")
    lines.append(f"  TRIGGERED: {summary['triggered_total']}")
    lines.append(f"    - Genuine:       {summary['triggered_genuine_count']}")
    lines.append(f"    - FALSE TRIGGER: {summary['triggered_false_count']}")
    lines.append(f"  CLEAR:   {summary['clear_count']}")
    lines.append(f"  SKIPPED: {summary['skipped_total']}")
    lines.append(f"    - Data unavailable:  {summary['skipped_unavailable_count']}")
    lines.append(f"    - ROUTING FAILURE:   {summary['skipped_routing_failure_count']}")
    lines.append(f"    - Not applicable:    {summary['skipped_not_applicable_count']}")
    lines.append(f"  INFO:    {summary['info_count']}")
    lines.append("")

    # FALSE TRIGGERS section
    if audit["triggered_false"]:
        lines.append(f"{'='*70}")
        lines.append("FALSE TRIGGERS (must fix)")
        lines.append(f"{'='*70}")
        for entry in sorted(audit["triggered_false"], key=lambda x: x["check_id"]):
            lines.append(f"\n  {entry['check_id']}: {entry['check_name']}")
            lines.append(f"    Value: {entry['value']}")
            lines.append(f"    Source field: {entry['source_field']}")
            lines.append(f"    Threshold level: {entry['threshold_level']}")
            lines.append(f"    Threshold red: {entry['threshold_red']}")
            lines.append(f"    Threshold yellow: {entry['threshold_yellow']}")
            lines.append(f"    REASON: {entry['reason']}")
        lines.append("")

    # ROUTING FAILURES section
    if audit["skipped_routing_failure"]:
        lines.append(f"{'='*70}")
        lines.append("ROUTING FAILURES (should have fired, but data couldn't be found)")
        lines.append(f"{'='*70}")
        for entry in sorted(audit["skipped_routing_failure"], key=lambda x: x["check_id"]):
            lines.append(f"\n  {entry['check_id']}: {entry['check_name']}")
            lines.append(f"    Expected source: {entry['expected_source']}")
            lines.append(f"    Expected field: {entry['field_key']}")
            lines.append(f"    REASON: {entry['reason']}")
        lines.append("")

    # GENUINE TRIGGERS section
    if audit["triggered_genuine"]:
        lines.append(f"{'='*70}")
        lines.append("GENUINE TRIGGERS (confirmed relevant)")
        lines.append(f"{'='*70}")
        for entry in sorted(audit["triggered_genuine"], key=lambda x: x["check_id"]):
            lines.append(f"\n  {entry['check_id']}: {entry['check_name']}")
            lines.append(f"    Value: {entry['value']}")
            lines.append(f"    Source field: {entry['source_field']}")
            lines.append(f"    Evidence: {entry['evidence'][:120]}")
        lines.append("")

    # SKIPPED - Data Unavailable
    if audit["skipped_unavailable"]:
        lines.append(f"{'='*70}")
        lines.append("SKIPPED - Data Unavailable (legitimate)")
        lines.append(f"{'='*70}")
        for entry in sorted(audit["skipped_unavailable"], key=lambda x: x["check_id"]):
            lines.append(f"  {entry['check_id']}: {entry['reason'][:100]}")
        lines.append("")

    # SKIPPED - Not Applicable
    if audit["skipped_not_applicable"]:
        lines.append(f"{'='*70}")
        lines.append("SKIPPED - Not Applicable (sector filter)")
        lines.append(f"{'='*70}")
        for entry in sorted(audit["skipped_not_applicable"], key=lambda x: x["check_id"]):
            lines.append(f"  {entry['check_id']}: {entry['check_name']}")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Backtest audit tool")
    parser.add_argument("state_path", type=Path, help="Path to state.json file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--save", action="store_true", default=True,
                       help="Save report to output/{ticker}/backtest_audit.txt")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)

    audit = audit_backtest(args.state_path)

    if args.json:
        print(json.dumps(audit, indent=2, default=str))
    else:
        report = format_report(audit)
        print(report)

        # Save to output dir
        if args.save:
            ticker = audit["ticker"]
            output_dir = Path("output") / ticker
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "backtest_audit.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\nReport saved to {output_path}")


if __name__ == "__main__":
    main()
