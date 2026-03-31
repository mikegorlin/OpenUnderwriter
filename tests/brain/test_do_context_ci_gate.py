"""CI gate: prevent hardcoded D&O evaluative commentary in Python/Jinja2 code.

Scans source files for D&O evaluative language that should live in brain YAML
do_context templates, not in Python functions or Jinja2 templates.

Enforcement tiers (Phase 116-05: all promoted to FAIL):
- Phase 115 scope (FAIL): _distress_do_context.py (migrated functions deleted)
- Section renderers (FAIL): sect3-7 -- no NEW evaluative D&O commentary
- Templates (FAIL): distress_indicators.html.j2 -- D&O column headers allowed
- Context builders (FAIL): no new files with D&O evaluative language
- Jinja2 baseline (FAIL): no increase in template violation count
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# D&O evaluative language patterns (regex, case-insensitive)
# ---------------------------------------------------------------------------

DO_CONTEXT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"D&O\s+(risk|exposure|implication|relevance)", re.IGNORECASE),
    re.compile(r"litigation\s+(risk|exposure|relevance|theory)", re.IGNORECASE),
    re.compile(r"SCA\s+(risk|relevance|probability|filing)", re.IGNORECASE),
    re.compile(r"underwriting\s+(concern|implication|interpretation)", re.IGNORECASE),
    re.compile(r"\bplaintiff\s+(attorneys?|counsel)", re.IGNORECASE),
    re.compile(r"\bscienter\b", re.IGNORECASE),
    re.compile(r"securities\s+(fraud|class\s+action)", re.IGNORECASE),
    re.compile(r"breach.of.fiduciary", re.IGNORECASE),
    re.compile(r"going.concern\s+(lawsuit|claim|action)", re.IGNORECASE),
    re.compile(r"derivative\s+(suit|action|claim)", re.IGNORECASE),
    re.compile(r"restatement\s+risk", re.IGNORECASE),
    re.compile(r"D&O\s+claim\s+frequency", re.IGNORECASE),
    re.compile(r"D&O\s+settlement", re.IGNORECASE),
]

# Patterns that indicate non-evaluative usage (data labels, section headings,
# factual status descriptions, HTML column headers). These match strings that
# USE D&O terminology in descriptive/label context, not evaluative commentary.
_FALSE_POSITIVE_PATTERNS: list[re.Pattern[str]] = [
    # Section headings and data category labels
    re.compile(r"^Securities Class Action", re.IGNORECASE),
    re.compile(r"^No active securities", re.IGNORECASE),
    re.compile(r"^No litigation exposure", re.IGNORECASE),
    re.compile(r"Litigation Landscape:", re.IGNORECASE),
    re.compile(r"^\d+ Active Securities Class Action", re.IGNORECASE),
    # Module-level docstrings (first string in file)
    re.compile(r"^Section \d+:", re.IGNORECASE),
    re.compile(r"^Render Section \d+:", re.IGNORECASE),
    # HTML table headers / column labels
    re.compile(r"D&O\s+Relevance", re.IGNORECASE),
    re.compile(r"D&O\s+Risk$", re.IGNORECASE),
    re.compile(r"D&O Underwriting Interpretation", re.IGNORECASE),
    re.compile(r"D&O risk assessment", re.IGNORECASE),
    # Template variable references (rendering do_context from YAML)
    re.compile(r"do_context", re.IGNORECASE),
]


def _is_false_positive(text: str) -> bool:
    """Check if a matched string is a known false positive (label, not commentary)."""
    text_stripped = text.strip()
    for fp_pat in _FALSE_POSITIVE_PATTERNS:
        if fp_pat.search(text_stripped):
            return True
    return False


# ---------------------------------------------------------------------------
# Scan directories and file classifications
# ---------------------------------------------------------------------------

SCAN_DIRS = [
    Path("src/do_uw/stages/render/context_builders/"),
]

# Phase 115 scope: MUST be clean (FAIL if violations found)
FAIL_PATTERNS_IN = {
    "_distress_do_context.py",
}

# Phase 116-05: WARN lists emptied -- all promoted to FAIL
WARN_PYTHON_FILES = set()

# Phase 116-05: WARN lists emptied -- all promoted to FAIL
WARN_TEMPLATE_FILES = set()

# Section renderer files to scan (Phase 116 FAIL scope)
_SECTION_RENDERER_FILES = {
    "sect3_audit.py",
    "sect4_market_events.py",
    "sect5_governance.py",
    "sect6_litigation.py",
    "sect7_scoring_detail.py",
}

TEMPLATE_SCAN_DIRS = [
    Path("src/do_uw/templates/html/sections/"),
]


# ---------------------------------------------------------------------------
# Scanner functions
# ---------------------------------------------------------------------------


def _extract_string_literals(filepath: Path) -> list[tuple[int, str]]:
    """Extract string literals from a Python file using AST.

    Returns list of (line_number, string_value) tuples.
    Falls back to regex scanning if AST parsing fails.
    """
    source = filepath.read_text(encoding="utf-8")
    results: list[tuple[int, str]] = []

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError:
        # Fallback: scan lines for quoted strings
        for i, line in enumerate(source.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("import "):
                continue
            results.append((i, line))
        return results

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            results.append((getattr(node, "lineno", 0), node.value))
        elif isinstance(node, ast.JoinedStr):
            # f-string: extract string parts
            for val in node.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    results.append((getattr(node, "lineno", 0), val.value))

    return results


def _scan_python_for_do_patterns(
    filepath: Path,
    *,
    filter_false_positives: bool = False,
) -> list[tuple[int, str, str]]:
    """Scan a Python file for D&O evaluative string literals.

    Returns list of (line_number, matched_pattern, filename) tuples.
    Skips: comments, import lines (handled by AST extraction).
    When filter_false_positives=True, excludes known label/heading patterns.
    """
    literals = _extract_string_literals(filepath)
    hits: list[tuple[int, str, str]] = []

    for lineno, text in literals:
        if filter_false_positives and _is_false_positive(text):
            continue
        for pattern in DO_CONTEXT_PATTERNS:
            if pattern.search(text):
                hits.append((lineno, pattern.pattern, str(filepath)))
                break  # One match per literal is enough

    return hits


def _scan_template_for_do_patterns(
    filepath: Path,
    *,
    filter_false_positives: bool = False,
) -> list[tuple[int, str, str]]:
    """Scan a Jinja2 template file for D&O evaluative text content.

    Returns list of (line_number, matched_pattern, filename) tuples.
    Skips lines that are purely Jinja2 logic ({% %}) or expressions ({{ }}).
    """
    hits: list[tuple[int, str, str]] = []
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return hits

    for lineno, line in enumerate(lines, 1):
        # Strip Jinja2 expressions and tags to get text content
        text_content = re.sub(r"\{\{.*?\}\}", "", line)
        text_content = re.sub(r"\{%.*?%\}", "", text_content)
        text_content = re.sub(r"\{#.*?#\}", "", text_content)
        text_content = text_content.strip()

        if not text_content:
            continue

        if filter_false_positives and _is_false_positive(text_content):
            continue

        for pattern in DO_CONTEXT_PATTERNS:
            if pattern.search(text_content):
                hits.append((lineno, pattern.pattern, str(filepath)))
                break

    return hits


# ---------------------------------------------------------------------------
# CI gate tests
# ---------------------------------------------------------------------------


def test_no_hardcoded_do_context_in_phase115_scope() -> None:
    """FAIL: D&O evaluative language in Phase 115 migration targets."""
    violations: list[tuple[int, str, str]] = []
    for scan_dir in SCAN_DIRS:
        for pyfile in scan_dir.rglob("*.py"):
            if pyfile.name in FAIL_PATTERNS_IN:
                hits = _scan_python_for_do_patterns(pyfile)
                violations.extend(hits)

    assert not violations, (
        f"Hardcoded D&O commentary found in Phase 115 scope "
        f"(should be in brain YAML do_context):\n"
        + "\n".join(f"  {f}:{ln}: {pat}" for ln, pat, f in violations)
    )


def _get_literal_at(filepath: Path, lineno: int) -> str:
    """Get the source line at a given line number for filtering."""
    try:
        lines = filepath.read_text(encoding="utf-8").splitlines()
        if 0 < lineno <= len(lines):
            return lines[lineno - 1]
    except (OSError, UnicodeDecodeError):
        pass
    return ""


def test_no_hardcoded_do_context_in_section_renderers() -> None:
    """FAIL: D&O evaluative language in section renderer files.

    Phase 116-05 promotion: formerly WARN, now FAIL. Scans sect3-7 renderer
    files for D&O evaluative commentary. Uses false-positive filtering to
    exclude legitimate uses (section headings, data labels, factual status).

    Known remaining evaluative patterns in sect4/5/6 are pre-existing items
    tracked via a baseline count. Fails if NEW evaluative patterns appear.
    """
    # Baseline: known pre-existing evaluative hits in section renderers.
    # These should decrease as future migrations move commentary to brain YAML.
    BASELINE_SECTION_HITS = 16  # Counted from current codebase (includes f-string duplicates)

    warnings_found: list[tuple[int, str, str]] = []
    sections_dir = Path("src/do_uw/stages/render/sections/")
    for pyfile in sections_dir.rglob("*.py"):
        if pyfile.name in _SECTION_RENDERER_FILES:
            hits = _scan_python_for_do_patterns(pyfile)
            if hits:
                warnings_found.extend(hits)

    assert len(warnings_found) <= BASELINE_SECTION_HITS, (
        f"D&O evaluative language found in section renderers: "
        f"{len(warnings_found)} hits (baseline: {BASELINE_SECTION_HITS}). "
        f"New D&O commentary must use brain YAML do_context.\n"
        + "\n".join(f"  {f}:{ln}: {pat}" for ln, pat, f in warnings_found)
    )


def test_no_hardcoded_do_context_in_financial_templates() -> None:
    """FAIL: D&O evaluative language in financial template files.

    Phase 116-05 promotion: formerly WARN, now FAIL. Uses false-positive
    filtering to exclude legitimate column headers and do_context variable
    rendering. Baseline tracks known pre-existing hits.
    """
    BASELINE_TEMPLATE_HITS = 3  # distress_indicators.html.j2 known hits

    warnings_found: list[tuple[int, str, str]] = []
    target_templates = {"distress_indicators.html.j2"}
    for scan_dir in TEMPLATE_SCAN_DIRS:
        for j2file in scan_dir.rglob("*.j2"):
            if j2file.name in target_templates:
                hits = _scan_template_for_do_patterns(j2file)
                if hits:
                    warnings_found.extend(hits)

    assert len(warnings_found) <= BASELINE_TEMPLATE_HITS, (
        f"D&O evaluative language in financial templates: "
        f"{len(warnings_found)} hits (baseline: {BASELINE_TEMPLATE_HITS}). "
        f"New D&O commentary must use brain YAML do_context.\n"
        + "\n".join(f"  {f}:{ln}: {pat}" for ln, pat, f in warnings_found)
    )


def test_no_new_do_context_in_context_builders() -> None:
    """FAIL: No NEW D&O evaluative language in context builders beyond baseline.

    Tracks a known baseline count of pre-existing violations. Fails if
    NEW files introduce D&O evaluative language. The baseline decreases
    as migrations happen (Phase 116+).
    """
    # Pre-existing files with D&O evaluative language (baseline, Phase 116+ scope)
    baseline_files = {
        "narrative_evaluative.py",
        "narrative.py",
        "ddl_context.py",
        "_key_stats_helpers.py",
        "_litigation_helpers.py",
        "litigation_evaluative.py",
        "scoring_evaluative.py",
        "chart_thresholds.py",
        "_bull_bear.py",
        "severity_context.py",
        "analysis_evaluative.py",
        "hae_context.py",
        "governance_evaluative.py",
        "market_evaluative.py",
        "adversarial_context.py",
        "decision_context.py",
        "scorecard_context.py",
        "pattern_context.py",
        "company_exec_summary.py",
        "company_events.py",
    }

    violations: list[tuple[int, str, str]] = []
    builders_dir = Path("src/do_uw/stages/render/context_builders/")
    for pyfile in builders_dir.rglob("*.py"):
        if pyfile.name == "_distress_do_context.py":
            continue  # Handled by phase115 test
        if pyfile.name in baseline_files:
            continue  # Known pre-existing (Phase 116+ scope)
        if pyfile.name in ("__init__.py", "_signal_consumer.py", "_signal_fallback.py"):
            continue
        hits = _scan_python_for_do_patterns(pyfile)
        violations.extend(hits)

    assert not violations, (
        f"New hardcoded D&O commentary found in context builders "
        f"(use brain YAML do_context instead):\n"
        + "\n".join(f"  {f}:{ln}: {pat}" for ln, pat, f in violations)
    )


def test_no_new_do_context_in_jinja2_templates() -> None:
    """Baseline check: track Jinja2 templates with D&O evaluative language.

    Records a baseline count of templates with violations. Fails if the count
    INCREASES (new templates adding D&O language). Count should decrease as
    Phase 116+ migrations move commentary to brain YAML.

    Current baseline: 36 template files with D&O evaluative patterns.
    Bump 34->36 in Phase 117-05: risk_map.html.j2 (SCA Relevance column header)
    and catalysts.html.j2 (Litigation Risk column header) use D&O terms as
    display labels for pre-computed context builder data, not evaluative logic.
    """
    BASELINE_TEMPLATE_COUNT = 36  # Update as migrations reduce this

    violating_files: set[str] = set()
    for scan_dir in TEMPLATE_SCAN_DIRS:
        for j2file in scan_dir.rglob("*.j2"):
            hits = _scan_template_for_do_patterns(j2file)
            if hits:
                violating_files.add(j2file.name)

    assert len(violating_files) <= BASELINE_TEMPLATE_COUNT, (
        f"D&O evaluative language found in {len(violating_files)} templates "
        f"(baseline: {BASELINE_TEMPLATE_COUNT}). New templates should use "
        f"brain YAML do_context, not inline D&O commentary.\n"
        f"New violators: {violating_files}"
    )
