"""Backward-compat shim: facet_renderer → section_renderer.

Phase 56-02 renamed this module. Use section_renderer.build_section_context() instead.
"""

from do_uw.stages.render.section_renderer import (  # noqa: F401
    build_section_context as build_facet_context,
)

__all__ = ["build_facet_context"]
