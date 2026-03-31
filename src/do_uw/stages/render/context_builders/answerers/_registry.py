"""Central answerer registry — avoids circular imports.

Domain modules import `register` from here (not __init__.py).
__init__.py imports domain modules AFTER defining exports.
"""

from __future__ import annotations

from typing import Any, Callable

from do_uw.models.state import AnalysisState

AnswererFunc = Callable[[dict[str, Any], AnalysisState, dict[str, Any]], dict[str, Any]]
ANSWERER_REGISTRY: dict[str, AnswererFunc] = {}


def register(*question_ids: str) -> Callable[[AnswererFunc], AnswererFunc]:
    """Decorator to register an answerer for one or more question IDs."""

    def wrapper(fn: AnswererFunc) -> AnswererFunc:
        for qid in question_ids:
            ANSWERER_REGISTRY[qid] = fn
        return fn

    return wrapper
