"""Backward-compat re-exports. Real implementation in context_builders/assembly_registry.py."""

from do_uw.stages.render.context_builders.assembly_registry import (
    _risk_class,
    build_html_context,
)

__all__ = ["_risk_class", "build_html_context"]
