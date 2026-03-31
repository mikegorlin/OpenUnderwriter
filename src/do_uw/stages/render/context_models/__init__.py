"""Typed context models for the 5 highest-leakage context builders.

Each model defines the Pydantic schema for the dict returned by its
corresponding builder function. The _validate_context wrapper provides
safe validation with fallback to untyped dicts.
"""

from do_uw.stages.render.context_models.exec_summary import ExecSummaryContext
from do_uw.stages.render.context_models.financial import FinancialContext
from do_uw.stages.render.context_models.governance import GovernanceContext
from do_uw.stages.render.context_models.litigation import LitigationContext
from do_uw.stages.render.context_models.market import MarketContext
from do_uw.stages.render.context_models.validation import _validate_context

__all__ = [
    "ExecSummaryContext",
    "FinancialContext",
    "GovernanceContext",
    "LitigationContext",
    "MarketContext",
    "_validate_context",
]
