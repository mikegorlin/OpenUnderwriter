"""Analysis extraction -- SHIM.

Canonical implementation moved to context_builders/analysis.py (Phase 58).
This file re-exports for backward compatibility.
"""

from do_uw.stages.render.context_builders.analysis import (
    _score_to_exposure,
    extract_classification,
    extract_executive_risk,
    extract_forensic_composites,
    extract_hazard_profile,
    extract_nlp_signals,
    extract_peril_map,
    extract_risk_factors,
    extract_temporal_signals,
)

__all__ = [
    "extract_classification",
    "extract_executive_risk",
    "extract_forensic_composites",
    "extract_hazard_profile",
    "extract_nlp_signals",
    "extract_peril_map",
    "extract_risk_factors",
    "extract_temporal_signals",
]
