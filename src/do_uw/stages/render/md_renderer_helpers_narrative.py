"""Company and executive summary extraction -- SHIM.

Canonical implementation moved to context_builders/company.py (Phase 58).
This file re-exports for backward compatibility.
"""

from do_uw.stages.render.context_builders.company import (
    extract_company,
    extract_exec_summary,
)

__all__ = ["extract_company", "extract_exec_summary"]
