"""Answerer registry for the underwriting question framework.

Central registry mapping question_id -> answerer function.
Each domain module self-registers via the @register decorator.
"""

from __future__ import annotations

from do_uw.stages.render.context_builders.answerers._registry import (
    ANSWERER_REGISTRY,
    register,
)

# Import domain modules to trigger registration.
# Each module uses @register("XXX-NN") to self-register its answerers.
from do_uw.stages.render.context_builders.answerers import (  # noqa: E402, F401
    company as _company,
    decision as _decision,
    financial as _financial,
    governance as _governance,
    litigation as _litigation,
    market as _market,
    operational as _operational,
    program as _program,
)

__all__ = ["ANSWERER_REGISTRY", "register"]
