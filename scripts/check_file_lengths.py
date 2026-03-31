#!/usr/bin/env python3
"""Enforce ARCH-05: No source file over 500 lines.

Run: uv run python scripts/check_file_lengths.py
Exit code 0 = pass, 1 = violations found.
"""

import sys
from pathlib import Path

MAX_LINES = 500
WARN_LINES = 400
SRC_DIR = Path("src")
TESTS_DIR = Path("tests")


def check_file_lengths() -> int:
    """Check all Python source files for line count violations."""
    failures: list[tuple[Path, int]] = []
    warnings: list[tuple[Path, int]] = []

    for search_dir in [SRC_DIR, TESTS_DIR]:
        if not search_dir.exists():
            continue
        for py_file in search_dir.rglob("*.py"):
            line_count = sum(1 for _ in py_file.open(encoding="utf-8"))
            if line_count > MAX_LINES:
                failures.append((py_file, line_count))
            elif line_count > WARN_LINES:
                warnings.append((py_file, line_count))

    for path, count in sorted(warnings):
        print(f"  WARN: {path} has {count} lines (approaching {MAX_LINES} limit)")

    for path, count in sorted(failures):
        print(f"  FAIL: {path} has {count} lines (max {MAX_LINES})")

    if failures:
        print(f"\n{len(failures)} file(s) exceed {MAX_LINES} line limit.")
        return 1

    if warnings:
        print(f"\n{len(warnings)} file(s) approaching limit. All files within {MAX_LINES} lines.")
    else:
        print(f"All files within {MAX_LINES} line limit.")
    return 0


if __name__ == "__main__":
    sys.exit(check_file_lengths())
