"""Manifest audit classification engine.

Phase 147 Plan 01: Classifies all manifest groups into three tiers:
  - RENDERS: template produces non-empty HTML with current context
  - WIRED: template has data path but renders empty for this ticker
  - SUPPRESSED: no data path, or display_only with zero signals fired

Provides build_manifest_audit_context() for the render context audit trail (D-08).
"""

from __future__ import annotations

import logging
from enum import StrEnum
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound, Undefined

from do_uw.brain.brain_unified_loader import load_signals
from do_uw.brain.manifest_schema import (
    ManifestGroup,
    OutputManifest,
    collect_signals_by_group,
    load_manifest,
)

logger = logging.getLogger(__name__)

# Template base directory
_TEMPLATES_BASE = Path(__file__).resolve().parents[2] / "templates" / "html"


class ManifestClassification(StrEnum):
    """Three-tier classification for manifest groups (D-01)."""

    RENDERS = "renders"
    WIRED = "wired"
    SUPPRESSED = "suppressed"


def _has_data_path(group: ManifestGroup) -> bool:
    """Check if a group declares data dependencies (requires or display_only)."""
    return bool(group.requires) or group.display_only


def _try_render(
    env: Environment,
    template_path: str,
    context: dict[str, Any],
) -> str | None:
    """Render a template, returning stripped output or None on error."""
    try:
        tmpl = env.get_template(template_path)
        return tmpl.render(**context).strip()
    except TemplateNotFound:
        logger.debug("Template not found: %s", template_path)
        return None
    except Exception:
        logger.debug("Template render error: %s", template_path, exc_info=True)
        return None


def classify_manifest_groups(
    state: Any = None,
    context: dict[str, Any] | None = None,
    *,
    manifest: OutputManifest | None = None,
) -> dict[str, ManifestClassification]:
    """Classify all manifest groups into renders/wired/suppressed.

    Args:
        state: AnalysisState (unused currently, reserved for future gating).
        context: Template context dict from build_html_context().
        manifest: Optional pre-loaded manifest. Loaded if not provided.

    Returns:
        Dict mapping group_id to ManifestClassification.
    """
    _ = state  # Reserved
    ctx = context or {}
    mfst = manifest or load_manifest()

    # Build Jinja2 env matching production path
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_BASE)),
        autoescape=False,
        undefined=_SilentUndefined,
    )
    # Register common filters/globals that templates expect
    _register_template_helpers(env, ctx)

    # Signal-to-group mapping for display_only suppression (D-06)
    try:
        sigs = load_signals()
        signals_by_group = collect_signals_by_group(sigs["signals"])
    except Exception:
        signals_by_group = {}

    result: dict[str, ManifestClassification] = {}

    for section in mfst.sections:
        for group in section.groups:
            rendered = _try_render(env, group.template, ctx)

            if rendered is None:
                # Template not found or crashed — classify as suppressed
                result[group.id] = ManifestClassification.SUPPRESSED
            elif rendered:
                # Non-empty output
                result[group.id] = ManifestClassification.RENDERS
            elif _has_data_path(group):
                # Empty output but has data path — display_only check
                group_signals = signals_by_group.get(group.id, [])
                if group.display_only and not group_signals:
                    result[group.id] = ManifestClassification.SUPPRESSED
                else:
                    result[group.id] = ManifestClassification.WIRED
            else:
                result[group.id] = ManifestClassification.SUPPRESSED

    return result


def build_manifest_audit_context(
    state: Any = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build audit context dict for template rendering (D-08).

    Returns:
        Dict with manifest_audit key containing counts and per-group classifications.
    """
    classifications = classify_manifest_groups(state, context)

    renders = sum(1 for v in classifications.values() if v == ManifestClassification.RENDERS)
    wired = sum(1 for v in classifications.values() if v == ManifestClassification.WIRED)
    suppressed = sum(
        1 for v in classifications.values() if v == ManifestClassification.SUPPRESSED
    )

    return {
        "manifest_audit": {
            "total": len(classifications),
            "renders": renders,
            "wired": wired,
            "suppressed": suppressed,
            "groups": {gid: cls.value for gid, cls in classifications.items()},
        }
    }


class _SilentUndefined(Undefined):
    """Undefined subclass that silently returns empty for missing variables.

    Prevents template crashes during classification — we want to test
    what renders, not crash on missing context keys.
    """

    def __str__(self) -> str:
        return ""

    def __iter__(self) -> Any:
        return iter([])

    def __bool__(self) -> bool:
        return False

    def __getattr__(self, _: str) -> "_SilentUndefined":
        return _SilentUndefined()

    def __call__(self, *_: Any, **__: Any) -> "_SilentUndefined":
        return _SilentUndefined()


def _register_template_helpers(env: Environment, ctx: dict[str, Any]) -> None:
    """Register filters and globals that production templates expect."""
    # Common filters — no-ops for classification purposes
    for name in (
        "format_na", "format_number", "format_pct", "format_currency",
        "format_date", "risk_class", "nl2br", "e",
    ):
        if name not in env.filters:
            env.filters[name] = lambda v, *a, **kw: str(v) if v else ""

    # Macros used as globals (kv_table, etc.) — stub as no-ops
    env.globals["kv_table"] = lambda *a, **kw: ""
    env.globals["mini_card"] = lambda *a, **kw: ""
    env.globals["section_header"] = lambda *a, **kw: ""


__all__ = [
    "ManifestClassification",
    "build_manifest_audit_context",
    "classify_manifest_groups",
]
