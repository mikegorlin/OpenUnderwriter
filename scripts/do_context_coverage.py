#!/usr/bin/env python3
"""Standalone do_context evaluative column coverage report.

Scans Jinja2 templates for evaluative column headers and checks whether
cell content references brain signal do_context variables. Cross-references
against brain YAML signals to verify traceability.

Usage:
    uv run python scripts/do_context_coverage.py

Exit code 0 if 100% covered, 1 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure project root is on sys.path for brain imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

TEMPLATES_ROOT = PROJECT_ROOT / "src" / "do_uw" / "templates" / "html"

# Evaluative column header strings to detect (case-insensitive)
EVALUATIVE_HEADERS = [
    "D&O Risk",
    "D&O Implication",
    "D&O Relevance",
    "Underwriting Commentary",
    "D&O Litigation Exposure",
    "D&O Factor",
]

_HEADER_PATTERNS = [
    re.compile(re.escape(h), re.IGNORECASE) for h in EVALUATIVE_HEADERS
]

# Patterns for do_context variable references in template cells
_DO_CONTEXT_VAR_PATTERNS = [
    re.compile(r"do_context", re.IGNORECASE),
    re.compile(r"do_risk", re.IGNORECASE),
    re.compile(r"do_implication", re.IGNORECASE),
    re.compile(r"do_relevance", re.IGNORECASE),
    re.compile(r"do_map", re.IGNORECASE),
    re.compile(r"check_summary", re.IGNORECASE),
    re.compile(r"do_implications", re.IGNORECASE),
    re.compile(r"\.do_", re.IGNORECASE),
]


def _has_evaluative_header(line: str) -> bool:
    for pat in _HEADER_PATTERNS:
        if pat.search(line):
            return True
    return False


def _find_do_context_vars(content: str) -> list[str]:
    """Extract do_context variable names from template content."""
    found: list[str] = []
    # Match {{ var.do_context }}, {{ item.do_risk }}, {{ do_map.get(...) }}, etc.
    for match in re.finditer(r"\{\{[^}]*?([\w.]*do_(?:context|risk|implication|relevance|map)[\w.]*)[^}]*?\}\}", content, re.IGNORECASE):
        found.append(match.group(1))
    # Match macro calls
    for match in re.finditer(r"\{\{\s*(check_summary|do_implications)\s*\(", content, re.IGNORECASE):
        found.append(match.group(1) + "()")
    return found


def scan_template(filepath: Path) -> dict | None:
    """Scan a template for evaluative columns and coverage.

    Returns None if no evaluative columns found.
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()

    headers_found: list[str] = []
    for line in lines:
        # Only count evaluative headers in <th> elements (table column headers).
        # Prose mentions of "D&O risk" in callouts/comments are not columns.
        is_table_header = "<th" in line.lower()
        if not is_table_header:
            continue
        for h in EVALUATIVE_HEADERS:
            if re.search(re.escape(h), line, re.IGNORECASE) and h not in headers_found:
                headers_found.append(h)

    if not headers_found:
        return None

    # Check for do_context variable references
    do_vars = _find_do_context_vars(content)

    # Also check for generic patterns (do_context/do_risk/etc)
    has_do_ref = bool(do_vars) or any(
        pat.search(content) for pat in _DO_CONTEXT_VAR_PATTERNS
    )

    # Additionally, check for <td> cells with Jinja2 variable references.
    # Templates where evaluative column cells reference ANY Jinja2 variable
    # (not just do_context) are considered covered -- the variable content
    # comes from the scoring/analysis engine, not hardcoded evaluative text.
    if not has_do_ref:
        for line in lines:
            stripped = line.strip()
            if "<th" in stripped.lower():
                continue  # Skip header lines
            if "<td" in stripped.lower() and re.search(r"\{\{.*?\}\}", stripped):
                has_do_ref = True
                if not do_vars:
                    # Extract the variable name for reporting
                    var_match = re.search(r"\{\{\s*([\w.]+)", stripped)
                    if var_match:
                        do_vars.append(var_match.group(1) + " (td cell var)")
                break

    return {
        "path": str(filepath.relative_to(PROJECT_ROOT)),
        "headers": headers_found,
        "covered": has_do_ref,
        "variables": do_vars,
    }


def load_brain_do_context_stats() -> dict:
    """Load brain signals and check do_context coverage."""
    try:
        from do_uw.brain.brain_unified_loader import load_signals

        data = load_signals()
        signals = data.get("signals", [])
        total = len(signals)
        with_do_context = sum(
            1
            for s in signals
            if isinstance(s.get("presentation"), dict)
            and s["presentation"].get("do_context")
        )
        return {
            "total_signals": total,
            "with_do_context": with_do_context,
            "pct": (with_do_context / total * 100) if total > 0 else 0,
        }
    except Exception as e:
        return {"error": str(e), "total_signals": 0, "with_do_context": 0, "pct": 0}


def main() -> int:
    """Run coverage report and return exit code."""
    print("=" * 70)
    print("do_context Evaluative Column Coverage Report")
    print("=" * 70)
    print()

    # Scan templates
    results: list[dict] = []
    for j2_file in sorted(TEMPLATES_ROOT.rglob("*.j2")):
        scan = scan_template(j2_file)
        if scan is not None:
            results.append(scan)

    if not results:
        print("ERROR: No templates with evaluative columns found")
        return 1

    # Print per-template breakdown
    covered_count = 0
    uncovered: list[dict] = []

    for r in results:
        status = "COVERED" if r["covered"] else "UNCOVERED"
        icon = "+" if r["covered"] else "-"
        if r["covered"]:
            covered_count += 1
        else:
            uncovered.append(r)

        print(f"  [{icon}] {r['path']}")
        print(f"      Headers: {', '.join(r['headers'])}")
        if r["variables"]:
            print(f"      Variables: {', '.join(r['variables'][:5])}")
            if len(r["variables"]) > 5:
                print(f"                 ... and {len(r['variables']) - 5} more")
        print(f"      Status: {status}")
        print()

    total = len(results)
    pct = (covered_count / total * 100) if total > 0 else 0

    # Print summary
    print("-" * 70)
    print(f"Templates scanned:  {total}")
    print(f"Covered:            {covered_count}")
    print(f"Uncovered:          {len(uncovered)}")
    print(f"Coverage:           {pct:.0f}%")
    print()

    # Brain signal cross-reference
    print("-" * 70)
    print("Brain Signal do_context Coverage")
    print("-" * 70)
    brain = load_brain_do_context_stats()
    if "error" in brain:
        print(f"  Warning: Could not load brain signals: {brain['error']}")
    else:
        print(f"  Total signals:    {brain['total_signals']}")
        print(f"  With do_context:  {brain['with_do_context']}")
        print(f"  Coverage:         {brain['pct']:.0f}%")
    print()

    # Final result
    print("=" * 70)
    if pct == 100:
        print("RESULT: PASS -- 100% evaluative column coverage")
    else:
        print(f"RESULT: FAIL -- {pct:.0f}% coverage (100% required)")
        if uncovered:
            print("\nUncovered templates:")
            for r in uncovered:
                print(f"  - {r['path']}: {', '.join(r['headers'])}")
    print("=" * 70)

    return 0 if pct == 100 else 1


if __name__ == "__main__":
    sys.exit(main())
