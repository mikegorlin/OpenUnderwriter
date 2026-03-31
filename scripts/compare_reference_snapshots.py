"""Compare current output against reference snapshots.

Usage: uv run python scripts/compare_reference_snapshots.py [--baseline-dir .planning/baselines] [--tickers AAPL,RPM,V]

For each ticker:
1. Load saved reference snapshot
2. Generate current snapshot
3. Compare: added/removed context keys, changed section hashes
4. Report differences
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_TICKERS = ["AAPL", "RPM", "V"]
DEFAULT_BASELINE_DIR = ".planning/baselines"


def compare_snapshots(baseline: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Compare two snapshots and return differences."""
    diffs: dict[str, Any] = {"context_keys": {}, "section_hashes": {}, "summary": ""}

    # Context key comparison
    base_keys = set(baseline.get("context_keys", {}).keys())
    curr_keys = set(current.get("context_keys", {}).keys())
    added = curr_keys - base_keys
    removed = base_keys - curr_keys
    if added:
        diffs["context_keys"]["added"] = sorted(added)
    if removed:
        diffs["context_keys"]["removed"] = sorted(removed)

    # Section hash comparison
    base_hashes = baseline.get("section_hashes", {})
    curr_hashes = current.get("section_hashes", {})
    changed = []
    for section_id in sorted(set(base_hashes) | set(curr_hashes)):
        base_hash = base_hashes.get(section_id)
        curr_hash = curr_hashes.get(section_id)
        if base_hash != curr_hash:
            changed.append({
                "section": section_id,
                "baseline": base_hash or "MISSING",
                "current": curr_hash or "MISSING",
                "status": (
                    "CHANGED"
                    if base_hash and curr_hash
                    else ("ADDED" if curr_hash else "REMOVED")
                ),
            })
    diffs["section_hashes"]["changes"] = changed

    # Summary
    total_changes = len(added) + len(removed) + len(changed)
    diffs["summary"] = (
        f"{total_changes} differences: {len(added)} keys added, "
        f"{len(removed)} keys removed, {len(changed)} sections changed"
    )
    return diffs


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Compare reference snapshots")
    parser.add_argument("--baseline-dir", default=DEFAULT_BASELINE_DIR)
    parser.add_argument("--tickers", default=",".join(DEFAULT_TICKERS))
    args = parser.parse_args()
    tickers = [t.strip() for t in args.tickers.split(",")]
    baseline_dir = Path(args.baseline_dir)
    exit_code = 0
    for ticker in tickers:
        ref_path = baseline_dir / f"{ticker}_reference.json"
        if not ref_path.exists():
            print(f"{ticker}: No baseline found at {ref_path}", file=sys.stderr)
            continue
        baseline = json.loads(ref_path.read_text())
        from scripts.capture_reference_snapshots import (
            capture_context_snapshot,
            compute_section_hashes,
            load_state,
        )

        try:
            state = load_state(ticker)
            current = {
                "context_keys": capture_context_snapshot(state),
                "section_hashes": compute_section_hashes(ticker),
            }
            diffs = compare_snapshots(baseline, current)
            print(f"{ticker}: {diffs['summary']}")
            if diffs["section_hashes"].get("changes"):
                exit_code = 1
                for change in diffs["section_hashes"]["changes"]:
                    print(f"  {change['status']}: {change['section']}")
        except Exception as e:
            print(f"{ticker}: FAILED - {e}", file=sys.stderr)
            exit_code = 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
