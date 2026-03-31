"""CI lint: ensure chart/market templates do not contain hardcoded thresholds.

Scans Jinja2 conditional expressions ({% if ... %}) for numeric literal
comparisons, which indicate thresholds have drifted back into templates
instead of being declared in signal YAML.

Allowed patterns:
- Comparisons to 0 (zero checks: == 0, > 0, != 0)
- Comparisons to 1 (boolean-like: > 1, >= 1)
- Format strings ('{:.1f}', '{:+.1f}')
- Non-conditional contexts (text content, CSS classes)
- Lines that reference 'thresholds.' (the approved pattern)
- figure_num comparisons
- Unit conversion (vol_90d * 100 if vol_90d < 1)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "src" / "do_uw" / "templates" / "html"

# Templates to scan for hardcoded thresholds
_TEMPLATES_TO_SCAN = [
    "sections/market/stock_charts.html.j2",
    "sections/market/stock_performance.html.j2",
]

# Regex to find Jinja2 conditional blocks
_CONDITIONAL_RE = re.compile(r"\{%[-\s]*(if|elif|set)\s+(.+?)[-\s]*%\}")

# Regex to find numeric comparisons in conditional expressions
# Matches: > 1.3, >= 25.0, < -20.0, == 10, != 5.5, * 1.3
_NUMERIC_COMPARISON_RE = re.compile(
    r"(?:[><=!]=?|[*])\s*-?(\d+\.?\d*)"
)

# Regex for flags.append / positives.append patterns (inline callout text)
_INLINE_APPEND_RE = re.compile(r"(flags|positives)\s*\.\s*append\s*\(")

# Allowed numeric values in conditionals (zero checks, boolean-like)
_ALLOWED_VALUES = {"0", "0.0", "1", "1.0", "-1", "-1.0", "100"}


def _scan_template_for_violations(template_path: Path) -> list[str]:
    """Scan a single template for hardcoded threshold violations.

    Returns list of violation strings with line number and match.
    """
    if not template_path.exists():
        return []  # Template doesn't exist yet -- skip

    violations: list[str] = []
    lines = template_path.read_text(encoding="utf-8").splitlines()

    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip non-conditional lines (pure HTML, text content, CSS)
        conditionals = _CONDITIONAL_RE.findall(stripped)
        if not conditionals:
            continue

        # Skip lines referencing thresholds.* (the approved pattern)
        if "thresholds." in stripped or "t_mdd." in stripped:
            continue

        # Check for inline append patterns (should not exist after refactor)
        if _INLINE_APPEND_RE.search(stripped):
            violations.append(
                f"  Line {line_num}: inline callout build detected: {stripped[:120]}"
            )
            continue

        # Check conditional expressions for numeric literals
        for _kw, expr in conditionals:
            # Skip format strings
            if "format(" in expr or "{:" in expr:
                continue
            # Skip figure_num comparisons
            if "figure_num" in expr:
                continue
            # Skip unit conversion pattern (vol_90d * 100 if vol_90d < 1)
            if "* 100" in expr and "< 1" in expr:
                continue

            matches = _NUMERIC_COMPARISON_RE.findall(expr)
            for val in matches:
                if val not in _ALLOWED_VALUES:
                    violations.append(
                        f"  Line {line_num}: numeric threshold '{val}' in: {expr.strip()[:100]}"
                    )

    return violations


@pytest.mark.parametrize(
    "template_rel_path",
    _TEMPLATES_TO_SCAN,
    ids=[Path(t).stem for t in _TEMPLATES_TO_SCAN],
)
def test_no_hardcoded_thresholds_in_template(template_rel_path: str) -> None:
    """Verify template has no hardcoded numeric thresholds in conditionals."""
    template_path = _TEMPLATE_DIR / template_rel_path
    if not template_path.exists():
        pytest.skip(f"Template not found: {template_rel_path}")

    violations = _scan_template_for_violations(template_path)
    assert violations == [], (
        f"Hardcoded thresholds found in {template_rel_path}:\n"
        + "\n".join(violations)
        + "\n\nThresholds must come from signal YAML via context['thresholds']. "
        "See Phase 91 DISP-01/DISP-04."
    )


def test_no_inline_flag_builders_in_stock_charts() -> None:
    """Verify stock_charts.html.j2 has no inline flags.append/positives.append."""
    template_path = _TEMPLATE_DIR / "sections/market/stock_charts.html.j2"
    if not template_path.exists():
        pytest.skip("stock_charts.html.j2 not found")

    content = template_path.read_text(encoding="utf-8")
    matches = _INLINE_APPEND_RE.findall(content)
    assert matches == [], (
        f"Found {len(matches)} inline callout builder(s) in stock_charts.html.j2. "
        "Callouts should be pre-built by evaluate_chart_callouts() in the context builder."
    )
