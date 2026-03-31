"""Market data and table extraction -- SHIM.

Canonical implementation moved to context_builders/market.py (Phase 58).
This file re-exports for backward compatibility.
"""

from do_uw.stages.render.context_builders.market import (
    dim_display_name,
    extract_market,
)

__all__ = ["dim_display_name", "extract_market"]
