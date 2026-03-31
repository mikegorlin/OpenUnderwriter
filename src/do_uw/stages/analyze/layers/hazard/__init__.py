"""Hazard profile engine: Layer 2 of the five-layer analysis architecture.

Evaluates 7 hazard categories containing 55 dimensions to produce an
Inherent Exposure Score (IES, 0-100). Each dimension scores a structural
hazard condition -- characteristics that create inherent D&O exposure
independent of whether anything has actually gone wrong yet.

Categories:
  H1: Business & Operating Model (13 dimensions)
  H2: People & Management (8 dimensions)
  H3: Financial Structure (8 dimensions)
  H4: Governance Structure (8 dimensions)
  H5: Public Company Maturity (5 dimensions)
  H6: External Environment (7 dimensions)
  H7: Emerging / Modern Hazards (6 dimensions)

Pipeline position: After EXTRACT, before ANALYZE.
"""

from do_uw.stages.analyze.layers.hazard.dimension_scoring import score_all_dimensions
from do_uw.stages.analyze.layers.hazard.hazard_engine import compute_hazard_profile
from do_uw.stages.analyze.layers.hazard.interaction_effects import (
    detect_dynamic_interactions,
    detect_named_interactions,
)

__all__ = [
    "compute_hazard_profile",
    "detect_dynamic_interactions",
    "detect_named_interactions",
    "score_all_dimensions",
]
