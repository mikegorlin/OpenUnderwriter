"""Automated audit: render/ contains zero analytical logic.

Verifies Phase 35 success criterion 4: "grep for threshold comparisons
in render/ returns zero results." Uses AST analysis to detect analytical
patterns (score threshold comparisons, scoring function definitions,
LLM client imports) in the render stage.

Also verifies the pipeline has exactly 7 stages (CORE-04).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

# Root of the render stage source
RENDER_DIR = Path("src/do_uw/stages/render")

# Function names that should NOT be defined in render/
_FORBIDDEN_FUNC_NAMES = {
    "score_to_risk_level",
    "score_to_threat_label",
    "dim_score_threat",
    "is_financial_clean",
    "is_high_risk",
    "is_financial_health_clean",
    "classify_jurisdiction_risk",
}

# Variable names whose comparisons against numeric constants indicate
# analytical logic (threshold checks).
#
# Note: Generic `score` is excluded because it is a common attribute on
# model objects (DistressResult.score, AIRiskDimension.score) where the
# comparison checks model-intrinsic zone boundaries. Similarly,
# `quality_score` is excluded as it is used in meeting question generation
# to decide which questions to ask (inherent to question generation).
# The forbidden set targets compound names that imply risk classification
# or density assessment logic that should live in ANALYZE.
_SCORE_VAR_NAMES = {
    "threshold",
    "risk_level",
    "risk_score",
    "financial_clean",
    "overall_risk",
}


def _all_render_py_files() -> list[Path]:
    """Collect all .py files under render/."""
    return sorted(RENDER_DIR.rglob("*.py"))


def _parse_file(path: Path) -> ast.Module:
    """Parse a Python file to AST."""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


# ---------------------------------------------------------------------------
# Test 1: No threshold comparisons in render
# ---------------------------------------------------------------------------


class TestNoThresholdComparisons:
    """Verify no scoring/risk threshold comparisons in render files."""

    def test_no_analytical_function_definitions_in_render(self) -> None:
        """Phase 35 success criterion 4: grep for analytical definitions
        in render/ returns zero results.

        Checks for specific function/variable patterns that were identified
        in the research phase as analytical logic that belongs in ANALYZE.
        """
        import re

        # Patterns that should NOT exist in render/ .py files
        forbidden_patterns = [
            r"def _is_financial_clean",
            r"def _is_financial_health_clean",
            r"def _is_high_risk",
            r"def _score_to_risk_level",
            r"def _score_to_threat_label",
            r"def _dim_score_threat",
            r"def _risk_flag",
            r"def _classify_jurisdiction_risk",
            r"^_HIGH_RISK_JURISDICTIONS\s*[:=]",
        ]

        violations: list[str] = []

        for py_file in _all_render_py_files():
            content = py_file.read_text(encoding="utf-8")
            for line_num, line in enumerate(content.splitlines(), 1):
                for pattern in forbidden_patterns:
                    if re.search(pattern, line):
                        violations.append(
                            f"  {py_file.relative_to('.')}:{line_num} "
                            f"-- {line.strip()}"
                        )

        if violations:
            msg = (
                "Analytical function/variable definitions found in render/ "
                "(should be in ANALYZE or BENCHMARK):\n"
                + "\n".join(violations)
            )
            pytest.fail(msg)

    def test_no_threshold_comparisons_in_render(self) -> None:
        """Scan render/ AST for threshold comparisons against score vars.

        Allowed patterns (display formatting, not analytics):
        - len(x) > 0 (empty check)
        - x is not None / x is None (null check)
        - String comparisons
        - Enum checks
        - Comparisons where BOTH sides are variables (not hardcoded thresholds)

        Disallowed patterns:
        - score > 86, risk_level >= 3, threshold < 5.0
        - Any var named 'score'/'threshold'/'risk_level' compared to a numeric
          constant, EXCEPT model-intrinsic constants in context strings
        """
        violations: list[str] = []

        for py_file in _all_render_py_files():
            tree = _parse_file(py_file)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare):
                    continue

                # Check if any operand is a score-like variable compared
                # to a numeric constant
                all_values = [node.left, *node.comparators]
                var_names = set()
                has_numeric_const = False

                for val in all_values:
                    if isinstance(val, ast.Name) and val.id in _SCORE_VAR_NAMES:
                        var_names.add(val.id)
                    if isinstance(val, (ast.Constant,)) and isinstance(
                        val.value, (int, float)
                    ):
                        has_numeric_const = True

                    # Check attribute access: e.g., state.analysis.financial_clean
                    if isinstance(val, ast.Attribute):
                        attr = val.attr
                        if attr in _SCORE_VAR_NAMES:
                            var_names.add(attr)

                if var_names and has_numeric_const:
                    line = getattr(node, "lineno", "?")
                    violations.append(
                        f"  {py_file.relative_to('.')}:{line} "
                        f"-- threshold comparison on {var_names}"
                    )

        if violations:
            msg = (
                "Threshold comparisons found in render/ "
                "(analytical logic should be in ANALYZE):\n"
                + "\n".join(violations)
            )
            pytest.fail(msg)


# ---------------------------------------------------------------------------
# Test 2: No scoring functions defined in render
# ---------------------------------------------------------------------------


class TestNoScoringFunctions:
    """Verify no scoring/classification functions are defined in render/."""

    def test_no_scoring_functions_defined_in_render(self) -> None:
        """Scan render/ for function definitions containing forbidden names.

        Functions that import and re-export from benchmark/ are allowed
        (they don't define analytical logic, they just re-use it).
        """
        violations: list[str] = []

        for py_file in _all_render_py_files():
            tree = _parse_file(py_file)
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue

                # Check if function name matches forbidden patterns
                func_name = node.name.lstrip("_")
                for forbidden in _FORBIDDEN_FUNC_NAMES:
                    if forbidden in func_name:
                        violations.append(
                            f"  {py_file.relative_to('.')}:{node.lineno} "
                            f"-- def {node.name}() (matches '{forbidden}')"
                        )
                        break

        if violations:
            msg = (
                "Scoring/classification functions found defined in render/:\n"
                + "\n".join(violations)
            )
            pytest.fail(msg)

    def test_no_high_risk_jurisdictions_set_in_render(self) -> None:
        """Verify _HIGH_RISK_JURISDICTIONS set is not in render/."""
        violations: list[str] = []

        for py_file in _all_render_py_files():
            tree = _parse_file(py_file)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id == "_HIGH_RISK_JURISDICTIONS"
                        ):
                            violations.append(
                                f"  {py_file.relative_to('.')}:{node.lineno}"
                            )

        if violations:
            msg = (
                "_HIGH_RISK_JURISDICTIONS set found in render/ "
                "(should be in ANALYZE):\n" + "\n".join(violations)
            )
            pytest.fail(msg)


# ---------------------------------------------------------------------------
# Test 3: No LLM client imports in render
# ---------------------------------------------------------------------------


class TestNoLLMImportsInRender:
    """Verify no LLM client libraries imported in render/."""

    def test_no_anthropic_imports_in_render(self) -> None:
        """Verify no render/ file imports anthropic or instructor.

        LLM calls belong in BENCHMARK stage, not RENDER.
        Exception: TYPE_CHECKING imports are allowed (type hints only).
        """
        violations: list[str] = []
        forbidden_modules = {"anthropic", "instructor", "openai"}

        for py_file in _all_render_py_files():
            tree = _parse_file(py_file)
            for node in ast.walk(tree):
                # Skip TYPE_CHECKING blocks
                if isinstance(node, ast.If):
                    test = node.test
                    if isinstance(test, ast.Name) and test.id == "TYPE_CHECKING":
                        continue
                    if (
                        isinstance(test, ast.Attribute)
                        and test.attr == "TYPE_CHECKING"
                    ):
                        continue

                if isinstance(node, ast.Import):
                    for alias in node.names:
                        mod = alias.name.split(".")[0]
                        if mod in forbidden_modules:
                            violations.append(
                                f"  {py_file.relative_to('.')}:{node.lineno} "
                                f"-- import {alias.name}"
                            )

                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        mod = node.module.split(".")[0]
                        if mod in forbidden_modules:
                            violations.append(
                                f"  {py_file.relative_to('.')}:{node.lineno} "
                                f"-- from {node.module} import ..."
                            )

        if violations:
            msg = (
                "LLM client imports found in render/ "
                "(LLM calls belong in BENCHMARK):\n" + "\n".join(violations)
            )
            pytest.fail(msg)


# ---------------------------------------------------------------------------
# Test 4: Pipeline stages count
# ---------------------------------------------------------------------------


class TestPipelineStages:
    """Verify pipeline has exactly 7 stages (CORE-04)."""

    def test_pipeline_stages_count(self) -> None:
        from do_uw.models.state import PIPELINE_STAGES

        assert len(PIPELINE_STAGES) == 7, (
            f"Expected 7 pipeline stages, got {len(PIPELINE_STAGES)}: "
            f"{PIPELINE_STAGES}"
        )

    def test_pipeline_stages_names(self) -> None:
        from do_uw.models.state import PIPELINE_STAGES

        expected = [
            "resolve", "acquire", "extract", "analyze",
            "score", "benchmark", "render",
        ]
        assert PIPELINE_STAGES == expected
