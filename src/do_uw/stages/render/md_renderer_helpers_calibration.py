"""Calibration notes -- SHIM.

Canonical implementation moved to context_builders/calibration.py (Phase 58).
This file re-exports for backward compatibility.
"""

from do_uw.stages.render.context_builders.calibration import (
    render_calibration_notes,
)

__all__ = ["render_calibration_notes"]
