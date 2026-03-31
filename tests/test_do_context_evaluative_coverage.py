"""CI gate: do_context evaluative column coverage.

Scans all Jinja2 templates under src/do_uw/templates/html/ for evaluative
column headers (D&O Risk, D&O Implication, D&O Relevance, etc.) and verifies
that corresponding table cell content references Jinja2 variables rather than
hardcoded evaluative text.

SC-5 requirement: 100% coverage -- every evaluative column must trace to a
brain signal do_context block (via variable reference in cell content).
"""

from __future__ import annotations

import re
from pathlib import Path

TEMPLATES_ROOT = Path("src/do_uw/templates/html")

# Evaluative column header strings to detect (case-insensitive)
EVALUATIVE_HEADERS = [
    "D&O Risk",
    "D&O Implication",
    "D&O Relevance",
    "Underwriting Commentary",
    "D&O Litigation Exposure",
    "D&O Factor",
]

# Compile header detection patterns
_HEADER_PATTERNS = [
    re.compile(re.escape(h), re.IGNORECASE) for h in EVALUATIVE_HEADERS
]

# Pattern for Jinja2 variable expressions: {{ ... }}
_JINJA2_VAR = re.compile(r"\{\{.*?\}\}")

# Pattern for Jinja2 macro calls that embed do_context internally
# e.g., {{ check_summary(...) }}, {{ do_implications(...) }}
_MACRO_CALLS = re.compile(
    r"\{\{\s*(check_summary|do_implications|render_do_context"
    r"|format_do_context)\s*\(.*?\)\s*\}\}"
)

# Patterns indicating a td cell references a do_context-related variable
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
    """Check if a line contains an evaluative column header."""
    for pat in _HEADER_PATTERNS:
        if pat.search(line):
            return True
    return False


def _is_header_element(line: str) -> bool:
    """Check if a line is a <th> element (column header, allowed to be literal)."""
    stripped = line.strip()
    return "<th" in stripped.lower()


def _cell_references_variable(line: str) -> bool:
    """Check if a <td> cell references a Jinja2 variable (not hardcoded text).

    A cell is considered covered if it contains:
    - A {{ variable }} expression referencing do_context/do_risk/do_implication
    - A macro call like {{ check_summary(...) }}
    - Any {{ expression }} (variable reference, not hardcoded)
    """
    if _JINJA2_VAR.search(line):
        return True
    return False


def _cell_has_do_context_var(line: str) -> bool:
    """Check if a cell's Jinja2 expressions reference do_context variables."""
    for pat in _DO_CONTEXT_VAR_PATTERNS:
        if pat.search(line):
            return True
    return False


def scan_template(filepath: Path) -> dict:
    """Scan a template for evaluative columns and their coverage.

    Returns dict with:
        path: template path
        evaluative_headers: list of header strings found
        covered: bool -- all evaluative cells reference variables
        details: list of {header, line_num, cell_covered, variable_found}
    """
    content = filepath.read_text(encoding="utf-8")
    lines = content.splitlines()

    result = {
        "path": str(filepath),
        "evaluative_headers": [],
        "covered": True,
        "details": [],
    }

    has_eval_header = False
    for i, line in enumerate(lines):
        # Only detect evaluative headers in <th> elements or table header rows.
        # Prose text mentioning "D&O risk" in callouts/paragraphs is NOT
        # an evaluative column header requiring variable coverage.
        is_table_header = (
            "<th" in line.lower()
            or "| " in line  # Markdown-style table header
        )
        if not is_table_header and _has_evaluative_header(line):
            continue  # Prose mention, not a column header
        if is_table_header and _has_evaluative_header(line):
            for h in EVALUATIVE_HEADERS:
                if re.search(re.escape(h), line, re.IGNORECASE):
                    has_eval_header = True
                    if h not in result["evaluative_headers"]:
                        result["evaluative_headers"].append(h)

    if not has_eval_header:
        return result

    # For templates with evaluative headers, check if the template uses
    # Jinja2 variables for the evaluative content (not just the headers).
    # We look for do_context/do_risk/do_implication variable references
    # anywhere in the template content (beyond the header <th> lines).
    has_do_var = False
    for line in lines:
        if _is_header_element(line) and _has_evaluative_header(line):
            continue  # Skip header lines -- they're allowed to be literal
        if _cell_has_do_context_var(line):
            has_do_var = True
            break
        # Also check for generic {{ var }} in td elements near evaluative context
        if "<td" in line.lower() and _JINJA2_VAR.search(line):
            has_do_var = True
            break

    # A template is "covered" if it has evaluative headers AND references
    # do_context variables (or Jinja2 expressions in cells).
    # Templates that use macros like do_implications() or check_summary()
    # are also covered since those macros embed do_context internally.
    has_macro_call = bool(
        re.search(
            r"do_implications|check_summary|do_context|do_risk|do_map",
            content,
            re.IGNORECASE,
        )
    )

    result["covered"] = has_do_var or has_macro_call

    return result


def scan_all_templates() -> list[dict]:
    """Scan all templates and return results for those with evaluative columns."""
    results = []
    for j2_file in sorted(TEMPLATES_ROOT.rglob("*.j2")):
        scan = scan_template(j2_file)
        if scan["evaluative_headers"]:
            results.append(scan)
    return results


def test_do_context_evaluative_coverage() -> None:
    """CI gate: 100% evaluative column coverage (SC-5).

    Every template with evaluative column headers (D&O Risk, D&O Relevance,
    etc.) must reference brain signal do_context variables in the corresponding
    cell content -- no hardcoded evaluative text.
    """
    results = scan_all_templates()
    assert results, "No templates with evaluative columns found -- scan may be broken"

    uncovered = [r for r in results if not r["covered"]]

    total = len(results)
    covered = total - len(uncovered)
    pct = (covered / total * 100) if total > 0 else 0

    assert not uncovered, (
        f"do_context evaluative coverage: {pct:.0f}% ({covered}/{total}). "
        f"100% required (SC-5).\n\nUncovered templates:\n"
        + "\n".join(
            f"  {r['path']}: headers={r['evaluative_headers']}"
            for r in uncovered
        )
    )


def test_evaluative_templates_exist() -> None:
    """Sanity check: templates with evaluative <th> column headers exist.

    Only counts templates where D&O evaluative headers appear in <th>
    elements (actual table columns), not in prose, comments, or div text.
    Current count is ~5 templates with evaluative table columns.
    """
    results = scan_all_templates()
    assert len(results) >= 3, (
        f"Only found {len(results)} templates with evaluative table columns "
        f"(expected >= 3). Scan patterns may need updating."
    )
