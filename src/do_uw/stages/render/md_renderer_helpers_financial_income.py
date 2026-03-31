"""Financial income statement extraction -- SHIM.

Canonical implementation moved to context_builders/financials.py (Phase 58).
This file re-exports for backward compatibility.
"""

from do_uw.stages.render.context_builders.financials import (
    extract_financials,
    find_line_item_value,
)

__all__ = ["extract_financials", "find_line_item_value"]
