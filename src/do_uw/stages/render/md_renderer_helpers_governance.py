"""Governance extraction -- SHIM.

Canonical implementation moved to context_builders/governance.py (Phase 58).
This file re-exports for backward compatibility.
"""

from do_uw.stages.render.context_builders.governance import (
    extract_governance,
)

__all__ = ["extract_governance"]
