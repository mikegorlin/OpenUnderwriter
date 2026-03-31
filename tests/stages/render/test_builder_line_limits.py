"""BUILD-07 verification: all context builder files must be under 300 lines.

Wave 0 test scaffold. Files not yet rewritten are excluded; as plans
complete, EXCLUDED_FILES shrinks until all builders comply.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Directory containing all context builder modules
_BUILDERS_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "src"
    / "do_uw"
    / "stages"
    / "render"
    / "context_builders"
)

# Files not yet rewritten -- shrinks as plans 02-04 complete
EXCLUDED_FILES: set[str] = {
    "_bull_bear.py",
    "chart_thresholds.py",
    "ddl_context.py",
    "litigation.py",
    "scorecard_context.py",
}

MAX_LINES = 300


def _builder_files() -> list[Path]:
    """Collect all public builder .py files (exclude __init__ and _ prefixed helpers)."""
    files: list[Path] = []
    for p in sorted(_BUILDERS_DIR.glob("*.py")):
        name = p.name
        if name == "__init__.py":
            continue
        if name.startswith("_"):
            continue
        if name in EXCLUDED_FILES:
            continue
        files.append(p)
    return files


@pytest.mark.parametrize(
    "builder_file",
    _builder_files(),
    ids=lambda p: p.name,
)
def test_builder_under_line_limit(builder_file: Path) -> None:
    """Each context builder module must be under 300 lines."""
    line_count = len(builder_file.read_text().splitlines())
    assert line_count <= MAX_LINES, (
        f"{builder_file.name} has {line_count} lines (limit: {MAX_LINES})"
    )
