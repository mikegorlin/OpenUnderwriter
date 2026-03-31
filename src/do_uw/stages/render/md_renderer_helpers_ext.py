"""Litigation extraction -- SHIM.

Canonical implementation moved to context_builders/litigation.py (Phase 58).
Governance re-export preserved for backward compatibility.
"""

from do_uw.stages.render.context_builders.governance import (
    extract_governance,
)
from do_uw.stages.render.context_builders.litigation import (
    extract_litigation,
)

__all__ = ["extract_governance", "extract_litigation"]
