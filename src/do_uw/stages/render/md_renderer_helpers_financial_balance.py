"""Financial balance sheet helpers -- SHIM.

Canonical implementation moved to context_builders/financials_balance.py (Phase 58).
This file re-exports for backward compatibility. Private helpers only.
"""

from do_uw.stages.render.context_builders.financials_balance import (  # noqa: F401
    _build_statement_rows,
    _format_line_value,
)

__all__: list[str] = []
