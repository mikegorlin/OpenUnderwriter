"""CI contract test: every extracted model field has a render path (Phase 92 -- REND-01).

Statically validates that every field in ExtractedData, ScoringResult,
ClassificationResult, HazardProfile, and BenchmarkResult either:
  (a) Appears in a context builder (.py files in context_builders/)
  (b) Appears in a Jinja2 template (.j2 files in templates/html/)
  (c) Is listed in config/render_exclusions.yaml

Adding a new field to the model without a render path or exclusion entry
causes this test to fail.

This test uses static analysis (file content scanning) -- no pipeline run needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SRC_ROOT = Path(__file__).resolve().parent.parent / "src" / "do_uw"
_CONTEXT_BUILDERS_DIR = _SRC_ROOT / "stages" / "render" / "context_builders"
_TEMPLATES_DIR = _SRC_ROOT / "templates" / "html"
_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_all_file_contents(directory: Path, suffix: str) -> str:
    """Concatenate all file contents from a directory tree matching suffix."""
    parts: list[str] = []
    for file_path in directory.rglob(f"*{suffix}"):
        try:
            parts.append(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return "\n".join(parts)


def _get_exclusion_paths() -> set[str]:
    """Load exclusion paths from render_exclusions.yaml."""
    from do_uw.stages.render.coverage import load_render_exclusions

    return set(load_render_exclusions().keys())


def _enumerate_model_fields(
    model_cls: type[BaseModel],
    prefix: str = "",
    max_depth: int = 3,
) -> list[str]:
    """Recursively enumerate field names from a Pydantic model class.

    Returns dot-separated field paths. Only goes `max_depth` levels deep
    to avoid infinite recursion with self-referential models.

    For the CI test, we enumerate top-level and first-level nested field
    names -- the test checks that the field NAME (leaf) appears somewhere
    in context builders or templates.
    """
    if max_depth <= 0:
        return []

    fields: list[str] = []
    for field_name, field_info in model_cls.model_fields.items():
        path = f"{prefix}.{field_name}" if prefix else field_name
        fields.append(path)

        # Try to recurse into nested Pydantic models
        annotation = field_info.annotation
        # Handle Optional[X] -> X
        inner = _unwrap_optional(annotation)
        if inner is not None and isinstance(inner, type) and issubclass(inner, BaseModel):
            fields.extend(
                _enumerate_model_fields(inner, prefix=path, max_depth=max_depth - 1)
            )

    return fields


def _unwrap_optional(annotation: Any) -> type | None:
    """Unwrap Optional[X] or X | None to get X."""
    import typing

    origin = getattr(annotation, "__origin__", None)
    args = getattr(annotation, "__args__", None)

    # Handle Union types (X | None or Optional[X])
    if origin is typing.Union or str(origin) == "typing.Union":
        if args:
            non_none = [a for a in args if a is not type(None)]
            if len(non_none) == 1:
                return non_none[0]
    return None


def _is_field_excluded(field_path: str, exclusion_paths: set[str]) -> bool:
    """Check if a field path is covered by any exclusion prefix."""
    for excl in exclusion_paths:
        if field_path == excl or field_path.startswith(excl + "."):
            return True
    return False


def _field_name_in_text(field_name: str, text: str) -> bool:
    """Check if a field name appears in combined source text.

    Uses the leaf field name (last component of the dot path) for matching.
    """
    leaf = field_name.rsplit(".", 1)[-1]
    return leaf in text


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCIRenderPaths:
    """CI gate: every model field has a render path or exclusion."""

    @pytest.fixture(scope="class")
    def context_builder_text(self) -> str:
        """Concatenated text of all context builder .py files."""
        return _load_all_file_contents(_CONTEXT_BUILDERS_DIR, ".py")

    @pytest.fixture(scope="class")
    def template_text(self) -> str:
        """Concatenated text of all Jinja2 template .j2 files."""
        return _load_all_file_contents(_TEMPLATES_DIR, ".j2")

    @pytest.fixture(scope="class")
    def combined_text(self, context_builder_text: str, template_text: str) -> str:
        """Combined context builder + template text."""
        # Also include the main renderers which reference fields directly
        renderer_text = _load_all_file_contents(
            _SRC_ROOT / "stages" / "render", ".py"
        )
        return context_builder_text + "\n" + template_text + "\n" + renderer_text

    @pytest.fixture(scope="class")
    def exclusions(self) -> set[str]:
        """Exclusion paths from YAML config."""
        return _get_exclusion_paths()

    def test_extracted_data_fields_have_render_paths(
        self, combined_text: str, exclusions: set[str]
    ) -> None:
        """Every ExtractedData field has a render path or exclusion."""
        from do_uw.models.state import ExtractedData

        fields = _enumerate_model_fields(ExtractedData, prefix="extracted")
        missing: list[str] = []

        for field_path in fields:
            if _is_field_excluded(field_path, exclusions):
                continue
            if _field_name_in_text(field_path, combined_text):
                continue
            missing.append(field_path)

        assert not missing, (
            f"{len(missing)} ExtractedData field(s) have no render path and "
            f"are not in render_exclusions.yaml:\n"
            + "\n".join(f"  - {f}" for f in missing)
        )

    def test_scoring_fields_have_render_paths(
        self, combined_text: str, exclusions: set[str]
    ) -> None:
        """Every ScoringResult field has a render path or exclusion."""
        from do_uw.models.scoring import ScoringResult

        fields = _enumerate_model_fields(ScoringResult, prefix="scoring")
        missing: list[str] = []

        for field_path in fields:
            if _is_field_excluded(field_path, exclusions):
                continue
            if _field_name_in_text(field_path, combined_text):
                continue
            missing.append(field_path)

        assert not missing, (
            f"{len(missing)} ScoringResult field(s) have no render path:\n"
            + "\n".join(f"  - {f}" for f in missing)
        )

    def test_classification_fields_have_render_paths(
        self, combined_text: str, exclusions: set[str]
    ) -> None:
        """Every ClassificationResult field has a render path or exclusion."""
        from do_uw.models.classification import ClassificationResult

        fields = _enumerate_model_fields(ClassificationResult, prefix="classification")
        missing: list[str] = []

        for field_path in fields:
            if _is_field_excluded(field_path, exclusions):
                continue
            if _field_name_in_text(field_path, combined_text):
                continue
            missing.append(field_path)

        assert not missing, (
            f"{len(missing)} ClassificationResult field(s) have no render path:\n"
            + "\n".join(f"  - {f}" for f in missing)
        )

    def test_hazard_profile_fields_have_render_paths(
        self, combined_text: str, exclusions: set[str]
    ) -> None:
        """Every HazardProfile field has a render path or exclusion."""
        from do_uw.models.hazard_profile import HazardProfile

        fields = _enumerate_model_fields(HazardProfile, prefix="hazard_profile")
        missing: list[str] = []

        for field_path in fields:
            if _is_field_excluded(field_path, exclusions):
                continue
            if _field_name_in_text(field_path, combined_text):
                continue
            missing.append(field_path)

        assert not missing, (
            f"{len(missing)} HazardProfile field(s) have no render path:\n"
            + "\n".join(f"  - {f}" for f in missing)
        )

    def test_benchmark_fields_have_render_paths(
        self, combined_text: str, exclusions: set[str]
    ) -> None:
        """Every BenchmarkResult field has a render path or exclusion."""
        from do_uw.models.scoring import BenchmarkResult

        fields = _enumerate_model_fields(BenchmarkResult, prefix="benchmark")
        missing: list[str] = []

        for field_path in fields:
            if _is_field_excluded(field_path, exclusions):
                continue
            if _field_name_in_text(field_path, combined_text):
                continue
            missing.append(field_path)

        assert not missing, (
            f"{len(missing)} BenchmarkResult field(s) have no render path:\n"
            + "\n".join(f"  - {f}" for f in missing)
        )

    def test_synthetic_field_fails_without_exclusion(self) -> None:
        """Adding a field without a render path or exclusion would be caught.

        This meta-test verifies the detection logic works by checking that
        a synthetic field name NOT in any source file is flagged.
        """
        combined = "some text about financials and governance"
        exclusions: set[str] = set()

        # A completely synthetic field name that doesn't exist anywhere
        synthetic = "extracted.financials.zzz_nonexistent_audit_test_field_42"
        assert not _is_field_excluded(synthetic, exclusions)
        assert not _field_name_in_text(synthetic, combined)

    def test_exclusions_yaml_loads(self) -> None:
        """render_exclusions.yaml loads without errors."""
        exclusions = _get_exclusion_paths()
        assert len(exclusions) > 0
        assert "acquired_data" in exclusions
