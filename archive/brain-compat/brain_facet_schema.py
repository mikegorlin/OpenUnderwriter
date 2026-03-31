"""Backward-compat shim: brain_facet_schema → brain_section_schema.

Phase 56-02 renamed this module. All definitions now live in
brain_section_schema.py. This file re-exports everything under
the old names so any stale imports continue to work.

Old name → New name:
  FacetSpec (grouping) → SectionSpec
  SubsectionSpec (atomic) → FacetSpec
  FacetContentRef → SectionContentRef
  load_facet → load_section
  load_all_facets → load_all_sections
"""

from do_uw.brain.brain_section_schema import (  # noqa: F401
    FacetSpec as SubsectionSpec,
    SectionContentRef as FacetContentRef,
    SectionSpec as FacetSpec,
    load_all_sections as load_all_facets,
    load_section as load_facet,
)

__all__ = [
    "FacetContentRef",
    "FacetSpec",
    "SubsectionSpec",
    "load_all_facets",
    "load_facet",
]
