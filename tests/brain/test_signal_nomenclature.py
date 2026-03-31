"""CI lint guard: ensure 'check' terminology is not used in signal contexts.

After the Phase 49 rename (check -> signal), this test prevents drift back
to the old terminology. It greps for specific signal-related patterns that
should have been renamed, with an allowlist for legitimate uses of "check"
in non-signal contexts.
"""

import subprocess
from pathlib import Path

import pytest

# Use __file__ for robust path resolution regardless of CWD
_PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = _PROJECT_ROOT / "src" / "do_uw"
TESTS_DIR = _PROJECT_ROOT / "tests"

# Signal-specific patterns that must NOT appear in source code
# Each tuple: (forbidden_term, correct_replacement)
FORBIDDEN_PATTERNS = [
    ("BrainCheckEntry", "BrainSignalEntry"),
    ("BrainCheckThreshold", "BrainSignalThreshold"),
    ("BrainCheckProvenance", "BrainSignalProvenance"),
    ("CheckResult", "SignalResult"),
    ("CheckStatus", "SignalStatus"),
    ("check_engine", "signal_engine"),
    ("check_evaluators", "signal_evaluators"),
    ("check_field_routing", "signal_field_routing"),
    ("check_helpers", "signal_helpers"),
    ("check_mappers", "signal_mappers"),
    ("check_results", "signal_results"),
    ("html_checks", "html_signals"),
    ("brain_check_schema", "brain_signal_schema"),
    ("brain_build_checks", "brain_build_signals"),
    ("brain/checks/", "brain/signals/"),
    ("brain_checks", "brain_signals"),
    ("cli_knowledge_checks", "cli_knowledge_signals"),
]

# Files/patterns excluded from the grep (these legitimately reference the old terms)
ALLOWLIST_FILES = [
    "test_signal_nomenclature.py",  # This test file itself
    "SUMMARY.md",  # Historical plan summaries may reference old terms
    "RESEARCH.md",  # Research documents reference old terms
    "CONTEXT.md",  # Context documents reference old terms
    "PLAN.md",  # Plan documents reference old terms
    "ROADMAP.md",
    "STATE.md",
    "RETROSPECTIVE.md",
    "__pycache__",
    ".pyc",
    "brain.duckdb",
    ".git/",
    "cli_brain_trace.py",  # Backward-compat fallback for reading old state files
    "health_summary.py",  # Backward-compat fallback for reading old state files
    "cli_feedback.py",  # Backward-compat fallback for reading old state files
]


def _grep_for_pattern(pattern: str, search_dir: Path) -> list[str]:
    """Grep for a pattern in Python files, returning violations."""
    result = subprocess.run(
        ["grep", "-rn", pattern, str(search_dir), "--include=*.py"],
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return []

    violations = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        # Skip allowlisted files
        if any(allowed in line for allowed in ALLOWLIST_FILES):
            continue
        violations.append(line)
    return violations


class TestNoCheckTerminology:
    """Verify 'check' is not used in signal-related identifiers."""

    @pytest.mark.parametrize("old_term,new_term", FORBIDDEN_PATTERNS)
    def test_no_forbidden_pattern_in_src(
        self, old_term: str, new_term: str
    ) -> None:
        violations = _grep_for_pattern(old_term, SRC_DIR)
        assert not violations, (
            f"Found '{old_term}' (should be '{new_term}') in src/:\n"
            + "\n".join(violations[:10])
        )

    @pytest.mark.parametrize("old_term,new_term", FORBIDDEN_PATTERNS)
    def test_no_forbidden_pattern_in_tests(
        self, old_term: str, new_term: str
    ) -> None:
        violations = _grep_for_pattern(old_term, TESTS_DIR)
        assert not violations, (
            f"Found '{old_term}' (should be '{new_term}') in tests/:\n"
            + "\n".join(violations[:10])
        )

    def test_no_check_directory_exists(self) -> None:
        """The brain/checks/ directory should not exist (renamed to signals/)."""
        checks_dir = SRC_DIR / "brain" / "checks"
        assert not checks_dir.exists(), (
            "brain/checks/ directory still exists (should be brain/signals/)"
        )

    def test_no_checks_json_exists(self) -> None:
        """checks.json should not exist (renamed to signals.json)."""
        checks_json = SRC_DIR / "brain" / "checks.json"
        assert not checks_json.exists(), (
            "checks.json still exists (should be signals.json)"
        )

    def test_no_check_prefixed_files_in_analyze(self) -> None:
        """No check_*.py files should exist in stages/analyze/."""
        analyze_dir = SRC_DIR / "stages" / "analyze"
        check_files = list(analyze_dir.glob("check_*.py"))
        assert not check_files, (
            f"check_*.py files still exist in analyze/: "
            f"{[f.name for f in check_files]}"
        )
