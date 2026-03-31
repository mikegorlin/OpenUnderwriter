"""Vulture whitelist for known false positives.

Vulture reports these as unused, but they are used by frameworks
(Pydantic, Typer, pytest) or exported via __all__.

This file is NOT executed -- vulture reads it to suppress false positives.
"""

# ---------------------------------------------------------------------------
# Pydantic model config and validators (used by serialization framework)
# ---------------------------------------------------------------------------
model_config  # noqa: F821
model_validator  # noqa: F821
field_validator  # noqa: F821
model_post_init  # noqa: F821

# ---------------------------------------------------------------------------
# Typer CLI callback functions (invoked by framework, not called directly)
# ---------------------------------------------------------------------------
# These are decorated with @app.command() or @app.callback() and called
# by the Typer framework, not by user code.
status  # noqa: F821
gaps  # noqa: F821
effectiveness  # noqa: F821
changelog  # noqa: F821
backlog  # noqa: F821
export_docs  # noqa: F821
backtest  # noqa: F821
analyze  # noqa: F821
preview  # noqa: F821
apply  # noqa: F821
rollback  # noqa: F821
enrich  # noqa: F821
show  # noqa: F821
serve  # noqa: F821
feedback_summary  # noqa: F821
feedback_list  # noqa: F821
feedback_add  # noqa: F821
ingest_file  # noqa: F821
ingest_url  # noqa: F821
learning_summary  # noqa: F821
migrate  # noqa: F821
ingest  # noqa: F821
dead_checks  # noqa: F821
drift  # noqa: F821
deprecation_log  # noqa: F821
review  # noqa: F821
promote  # noqa: F821
traceability_audit  # noqa: F821
import_csv  # noqa: F821
program_history  # noqa: F821
cost_report  # noqa: F821

# ---------------------------------------------------------------------------
# Alembic migration functions (invoked by alembic framework)
# ---------------------------------------------------------------------------
upgrade  # noqa: F821
downgrade  # noqa: F821

# ---------------------------------------------------------------------------
# Typer app callback (invoked by Typer framework)
# ---------------------------------------------------------------------------
_app_init  # noqa: F821

# ---------------------------------------------------------------------------
# pytest fixtures (invoked by test framework)
# ---------------------------------------------------------------------------
# pytest fixtures are collected by name and injected into test functions.
tmp_path  # noqa: F821
monkeypatch  # noqa: F821

# ---------------------------------------------------------------------------
# Stage protocol methods (called by pipeline orchestrator)
# ---------------------------------------------------------------------------
run  # noqa: F821
name  # noqa: F821

# ---------------------------------------------------------------------------
# __all__ exports (re-exports for public API)
# ---------------------------------------------------------------------------
__all__  # noqa: F821

# ---------------------------------------------------------------------------
# Pydantic model fields (used by serialization, not referenced in code)
# ---------------------------------------------------------------------------
# Many Pydantic model fields appear "unused" because they're set via
# model_validate() or from JSON, not via direct attribute access.
# We whitelist common patterns rather than every field.
