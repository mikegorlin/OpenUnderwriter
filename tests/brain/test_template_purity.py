"""CI contract test: template purity (no hardcoded thresholds).

Validates that Jinja2 templates in company/ sections contain zero
hardcoded thresholds or evaluation logic. Renderers must be dumb
consumers per the brain portability principle -- all evaluation
logic belongs in signal evaluation, not templates.

Phase 100-03: CI contract tests for brain portability.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# Template directories to scan
_TEMPLATES_BASE = Path(__file__).resolve().parents[2] / "src" / "do_uw" / "templates" / "html"
_COMPANY_DIR = _TEMPLATES_BASE / "sections" / "company"

# Directories/files to scan for purity
_SCAN_TARGETS: list[Path] = [
    _COMPANY_DIR,
]

# Additional individual files to scan (if they exist)
_EXTRA_FILES: list[Path] = [
    _TEMPLATES_BASE / "sections" / "executive" / "complexity_dashboard.html.j2",
]

# Patterns that indicate hardcoded evaluation logic in Jinja2 blocks.
# These match numeric comparisons inside {% ... %} blocks (conditionals).
#
# Matches things like: {% if score > 3 %}, {% if value >= 15 %}, {% if x < 0.5 %}
# Does NOT match: {% if count > 0 %} (presence check), CSS classes, loop counters
_FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "Numeric threshold in Jinja2 conditional",
        # Match {%...%} containing comparison with number > 0
        # Captures: > 1, >= 2, < 0.5, <= 10, == 42, != 7
        # Excludes: > 0, != 0, == 0, >= 0 (presence/absence checks)
        # Excludes: loop.index comparisons
        re.compile(
            r"\{%[^%]*?"  # Opening {% tag
            r"(?<!loop\.index\s)"  # Not preceded by loop.index
            r"(?<!loop\.index0\s)"  # Not preceded by loop.index0
            r"(?:>|<|>=|<=|==|!=)\s*"  # Comparison operator
            r"(?!0(?:\s|%|\}))"  # NOT followed by just 0 (presence check)
            r"([1-9]\d*(?:\.\d+)?|\d+\.\d*[1-9])"  # Positive numeric literal > 0
            r"[^%]*?%\}",  # Closing %} tag
            re.DOTALL,
        ),
    ),
    (
        "Python eval/exec in template",
        re.compile(r"\b(?:eval|exec)\s*\("),
    ),
]

# Known safe patterns to exclude from matches (false positives).
# These are patterns that look like thresholds but are actually safe.
_SAFE_PATTERNS: list[re.Pattern[str]] = [
    # Pagination/slicing: [:5], [:10], [:3]
    re.compile(r"\[:\d+\]"),
    # Range limits in loops: range(1, N)
    re.compile(r"range\s*\("),
    # Truncation with |truncate(N)
    re.compile(r"\|\s*truncate\s*\(\s*\d+"),
    # String multiplication or repeat
    re.compile(r"'\s*\*\s*\d+"),
    # Batch/chunk filters: |batch(N), |slice(N)
    re.compile(r"\|\s*(?:batch|slice|round|default)\s*\(\s*\d+"),
    # Length comparisons: |length > N (checking collection size is display logic)
    re.compile(r"\|\s*length\s*(?:>|<|>=|<=|==|!=)\s*\d+"),
    # CSS/formatting numbers in class names or style attributes
    re.compile(r'class\s*=\s*"[^"]*\d+'),
    # Modulo for alternating rows: loop.index % 2
    re.compile(r"loop\.index\d?\s*%\s*\d+"),
    # Colspan/rowspan
    re.compile(r"(?:colspan|rowspan)\s*=\s*[\"']\d+"),
]


def _collect_template_files() -> list[Path]:
    """Collect all .html.j2 files to scan."""
    files: list[Path] = []
    for target in _SCAN_TARGETS:
        if target.is_dir():
            files.extend(sorted(target.rglob("*.html.j2")))
        elif target.is_file():
            files.append(target)
    for extra in _EXTRA_FILES:
        if extra.exists():
            files.append(extra)
    return files


def _is_safe_match(line: str) -> bool:
    """Check if a matched line is actually a known safe pattern."""
    return any(pat.search(line) for pat in _SAFE_PATTERNS)


def _scan_file_for_violations(filepath: Path) -> list[str]:
    """Scan a template file for forbidden patterns.

    Returns list of violation descriptions.
    """
    content = filepath.read_text()
    lines = content.split("\n")
    violations: list[str] = []
    rel = filepath.relative_to(_TEMPLATES_BASE)

    for pattern_name, pattern in _FORBIDDEN_PATTERNS:
        for i, line in enumerate(lines, 1):
            matches = pattern.findall(line) if pattern.groups else pattern.finditer(line)
            if pattern.groups:
                # Pattern with capture groups returns strings
                if matches:
                    if not _is_safe_match(line):
                        violations.append(
                            f"  {rel}:{i}: {pattern_name} -- {line.strip()}"
                        )
            else:
                # Pattern without capture groups returns match objects
                match_list = list(matches)
                if match_list and not _is_safe_match(line):
                    violations.append(
                        f"  {rel}:{i}: {pattern_name} -- {line.strip()}"
                    )

    return violations


def test_company_templates_have_no_hardcoded_thresholds() -> None:
    """Company section templates must contain zero evaluation logic.

    The brain portability principle requires renderers to be dumb consumers.
    All threshold comparisons, scoring logic, and evaluation decisions belong
    in signal YAML evaluation blocks, not in Jinja2 templates.

    Allowed:
    - Presence checks (> 0, != 0, == 0)
    - Loop counters (loop.index)
    - CSS classes with numbers
    - Collection length checks (display pagination)
    - Filters with numeric args (truncate, batch, round)
    """
    files = _collect_template_files()
    assert len(files) > 0, (
        f"No template files found to scan. "
        f"Check paths: {[str(t) for t in _SCAN_TARGETS]}"
    )

    all_violations: list[str] = []
    for filepath in files:
        violations = _scan_file_for_violations(filepath)
        all_violations.extend(violations)

    assert not all_violations, (
        f"{len(all_violations)} hardcoded threshold(s) found in templates:\n"
        + "\n".join(all_violations)
        + "\n\nMove evaluation logic to signal YAML evaluation blocks."
    )


def test_template_files_found() -> None:
    """Verify that we are scanning a reasonable number of template files.

    As of v6.0 there are 19 company templates.
    """
    files = _collect_template_files()
    assert len(files) >= 10, (
        f"Expected at least 10 template files to scan, found {len(files)}. "
        "Template directory may have moved."
    )


@pytest.mark.parametrize(
    "template_file",
    _collect_template_files(),
    ids=[str(f.relative_to(_TEMPLATES_BASE)) for f in _collect_template_files()],
)
def test_individual_template_purity(template_file: Path) -> None:
    """Each template file must individually pass purity checks."""
    violations = _scan_file_for_violations(template_file)
    assert not violations, (
        f"Hardcoded threshold(s) in {template_file.relative_to(_TEMPLATES_BASE)}:\n"
        + "\n".join(violations)
    )
