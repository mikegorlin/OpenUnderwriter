"""Diff signal results between pre- and post-migration snapshots.

Compares two signal result JSON snapshots and reports:
- REGRESSIONS: signals that were CLEAR/TRIGGERED and are now SKIPPED
- IMPROVEMENTS: signals that were SKIPPED and are now CLEAR/TRIGGERED
- DEFERRED: signals that moved to DEFERRED status (acceptable)
- UNCHANGED: signals with identical status

Exit code:
- 0: No regressions
- 1: Regressions found

Usage:
    uv run python scripts/diff_signal_results.py pre.json post.json

Phase 111-03: QA gate for signal resolver migration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_snapshot(path: str) -> dict[str, dict[str, str]]:
    """Load a signal result snapshot from JSON file."""
    with Path(path).open() as f:
        return json.load(f)


def diff_signals(
    pre: dict[str, dict[str, str]],
    post: dict[str, dict[str, str]],
) -> dict[str, list[str]]:
    """Compare pre and post signal snapshots.

    Returns dict with keys:
    - regressions: signals that were evaluating but now SKIPPED
    - improvements: signals that were SKIPPED but now evaluating
    - deferred: signals that moved to DEFERRED
    - status_changed: signals whose TRIGGERED/CLEAR status flipped
    - unchanged: signals with identical status
    - new_signals: signals in post but not in pre
    - removed_signals: signals in pre but not in post
    """
    result: dict[str, list[str]] = {
        "regressions": [],
        "improvements": [],
        "deferred": [],
        "status_changed": [],
        "unchanged": [],
        "new_signals": [],
        "removed_signals": [],
    }

    all_ids = set(pre.keys()) | set(post.keys())

    for sig_id in sorted(all_ids):
        pre_data = pre.get(sig_id)
        post_data = post.get(sig_id)

        if pre_data is None:
            result["new_signals"].append(sig_id)
            continue
        if post_data is None:
            result["removed_signals"].append(sig_id)
            continue

        pre_status = pre_data.get("status", "UNKNOWN")
        post_status = post_data.get("status", "UNKNOWN")
        post_data_status = post_data.get("data_status", "")

        # DEFERRED is acceptable (explicit classification)
        if post_data_status == "DEFERRED":
            result["deferred"].append(sig_id)
            continue

        # Was evaluating (CLEAR/TRIGGERED/INFO), now SKIPPED = REGRESSION
        if pre_status in ("CLEAR", "TRIGGERED", "INFO") and post_status == "SKIPPED":
            result["regressions"].append(sig_id)
            continue

        # Was SKIPPED, now evaluating = IMPROVEMENT
        if pre_status == "SKIPPED" and post_status in ("CLEAR", "TRIGGERED", "INFO"):
            result["improvements"].append(sig_id)
            continue

        # Status changed (CLEAR <-> TRIGGERED) — may need investigation
        if pre_status != post_status:
            result["status_changed"].append(sig_id)
            continue

        result["unchanged"].append(sig_id)

    return result


def print_report(diff: dict[str, list[str]], pre: dict, post: dict) -> None:
    """Print a human-readable diff report."""
    print("=" * 60)
    print("Signal Result Migration Diff Report")
    print("=" * 60)
    print()

    total = sum(len(v) for v in diff.values())
    print(f"Total signals compared: {total}")
    print(f"  Unchanged:      {len(diff['unchanged'])}")
    print(f"  Improvements:   {len(diff['improvements'])}")
    print(f"  Deferred:       {len(diff['deferred'])}")
    print(f"  Status changed: {len(diff['status_changed'])}")
    print(f"  New signals:    {len(diff['new_signals'])}")
    print(f"  Removed:        {len(diff['removed_signals'])}")
    print(f"  REGRESSIONS:    {len(diff['regressions'])}")
    print()

    if diff["regressions"]:
        print("!!! REGRESSIONS FOUND !!!")
        print("-" * 40)
        for sig_id in diff["regressions"]:
            pre_s = pre.get(sig_id, {}).get("status", "?")
            post_s = post.get(sig_id, {}).get("status", "?")
            print(f"  {sig_id}: {pre_s} -> {post_s}")
        print()

    if diff["improvements"]:
        print("Improvements (formerly SKIPPED, now evaluating):")
        for sig_id in diff["improvements"][:20]:
            post_s = post.get(sig_id, {}).get("status", "?")
            print(f"  {sig_id}: SKIPPED -> {post_s}")
        if len(diff["improvements"]) > 20:
            print(f"  ... and {len(diff['improvements']) - 20} more")
        print()

    if diff["deferred"]:
        print(f"Deferred to Data Pending: {len(diff['deferred'])} signals")
        print()

    if diff["status_changed"]:
        print("Status changes (investigate if unexpected):")
        for sig_id in diff["status_changed"][:10]:
            pre_s = pre.get(sig_id, {}).get("status", "?")
            post_s = post.get(sig_id, {}).get("status", "?")
            print(f"  {sig_id}: {pre_s} -> {post_s}")
        print()

    if diff["new_signals"]:
        print(f"New signals in post (not in pre): {len(diff['new_signals'])}")
        for sig_id in diff["new_signals"][:10]:
            print(f"  {sig_id}")
        print()


def main() -> None:
    """Run the diff and exit with appropriate code."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <pre.json> <post.json>")
        sys.exit(2)

    pre_path = sys.argv[1]
    post_path = sys.argv[2]

    if not Path(pre_path).exists():
        print(f"Pre-migration file not found: {pre_path}")
        sys.exit(2)
    if not Path(post_path).exists():
        print(f"Post-migration file not found: {post_path}")
        sys.exit(2)

    pre = load_snapshot(pre_path)
    post = load_snapshot(post_path)

    diff = diff_signals(pre, post)
    print_report(diff, pre, post)

    if diff["regressions"]:
        print(f"FAIL: {len(diff['regressions'])} regressions detected")
        sys.exit(1)
    else:
        print("PASS: Zero regressions")
        sys.exit(0)


if __name__ == "__main__":
    main()
