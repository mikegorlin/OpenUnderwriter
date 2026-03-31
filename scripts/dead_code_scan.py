#!/usr/bin/env python3
"""Reusable dead code detection tool using vulture.

Scans src/do_uw/ for unused code (functions, imports, variables, classes).
Uses a project-specific whitelist to suppress known false positives
from Pydantic, Typer, pytest, and other frameworks.

Usage:
    uv run python scripts/dead_code_scan.py              # Report only
    uv run python scripts/dead_code_scan.py --fix-imports # Also auto-fix unused imports via ruff
    uv run python scripts/dead_code_scan.py --min-confidence 80  # Higher confidence threshold

Exit codes:
    0 = No dead code found (or only whitelisted items)
    1 = Dead code detected
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SRC_DIR = Path("src/do_uw")
WHITELIST = Path("scripts/vulture_whitelist.py")
DEFAULT_MIN_CONFIDENCE = 60


def run_vulture(min_confidence: int = DEFAULT_MIN_CONFIDENCE) -> str:
    """Run vulture on src/do_uw/ with whitelist and return raw output."""
    cmd = [
        sys.executable, "-m", "vulture",
        str(SRC_DIR),
        str(WHITELIST),
        f"--min-confidence={min_confidence}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def categorize_findings(raw_output: str) -> dict[str, list[str]]:
    """Parse vulture output into categories."""
    categories: dict[str, list[str]] = {
        "unused_import": [],
        "unused_function": [],
        "unused_variable": [],
        "unused_class": [],
        "unused_attribute": [],
        "unused_property": [],
        "other": [],
    }

    for line in raw_output.strip().splitlines():
        if not line.strip():
            continue

        lower = line.lower()
        if "unused import" in lower:
            categories["unused_import"].append(line)
        elif "unused function" in lower:
            categories["unused_function"].append(line)
        elif "unused variable" in lower:
            categories["unused_variable"].append(line)
        elif "unused class" in lower:
            categories["unused_class"].append(line)
        elif "unused attribute" in lower:
            categories["unused_attribute"].append(line)
        elif "unused property" in lower:
            categories["unused_property"].append(line)
        else:
            categories["other"].append(line)

    return categories


def print_report(categories: dict[str, list[str]]) -> int:
    """Print categorized report and return total finding count."""
    total = sum(len(items) for items in categories.values())

    print("=" * 70)
    print("DEAD CODE SCAN REPORT")
    print("=" * 70)
    print(f"Source directory: {SRC_DIR}")
    print(f"Whitelist: {WHITELIST}")
    print()

    if total == 0:
        print("No dead code detected. All clean!")
        print("=" * 70)
        return 0

    category_labels = {
        "unused_import": "Unused Imports",
        "unused_function": "Unused Functions",
        "unused_variable": "Unused Variables",
        "unused_class": "Unused Classes",
        "unused_attribute": "Unused Attributes",
        "unused_property": "Unused Properties",
        "other": "Other",
    }

    # Summary table
    print("SUMMARY:")
    for key, label in category_labels.items():
        count = len(categories[key])
        if count > 0:
            print(f"  {label}: {count}")
    print(f"  TOTAL: {total}")
    print()

    # Detail sections
    for key, label in category_labels.items():
        items = categories[key]
        if not items:
            continue

        print(f"--- {label} ({len(items)}) ---")
        for item in sorted(items):
            print(f"  {item}")
        print()

    print("=" * 70)
    print(f"Total findings: {total}")
    print()
    print("To fix unused imports automatically:")
    print("  uv run ruff check --fix --select F401 src/do_uw/")
    print()
    print("To add false positives to the whitelist:")
    print("  Edit scripts/vulture_whitelist.py")
    print("=" * 70)

    return total


def fix_unused_imports() -> None:
    """Run ruff to auto-fix unused imports."""
    print("\nRunning ruff to fix unused imports...")
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--fix", "--select", "F401",
         str(SRC_DIR)],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        print(result.stdout)
    if result.returncode == 0:
        print("Unused imports fixed successfully.")
    else:
        print(f"ruff returned exit code {result.returncode}")
        if result.stderr:
            print(result.stderr)


def main() -> int:
    """Run dead code scan and return exit code."""
    parser = argparse.ArgumentParser(
        description="Scan for dead code in src/do_uw/ using vulture",
    )
    parser.add_argument(
        "--fix-imports",
        action="store_true",
        help="Auto-fix unused imports using ruff",
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=DEFAULT_MIN_CONFIDENCE,
        help=f"Minimum confidence threshold (default: {DEFAULT_MIN_CONFIDENCE})",
    )
    args = parser.parse_args()

    if not SRC_DIR.exists():
        print(f"ERROR: Source directory not found: {SRC_DIR}", file=sys.stderr)
        return 1

    if not WHITELIST.exists():
        print(f"WARNING: Whitelist not found: {WHITELIST}", file=sys.stderr)

    # Run vulture
    raw_output = run_vulture(min_confidence=args.min_confidence)

    # Categorize and report
    categories = categorize_findings(raw_output)
    total = print_report(categories)

    # Optionally fix imports
    if args.fix_imports and categories["unused_import"]:
        fix_unused_imports()
        # Re-scan after fixing
        print("\nRe-scanning after import fixes...")
        raw_output = run_vulture(min_confidence=args.min_confidence)
        categories = categorize_findings(raw_output)
        total = print_report(categories)

    return 1 if total > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
