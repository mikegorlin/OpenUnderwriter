# Coding Conventions

**Analysis Date:** 2026-02-25

## Naming Patterns

**Files:**
- `snake_case.py` throughout — e.g., `factor_scoring.py`, `check_engine.py`, `brain_migrate_yaml.py`
- Stage entry points named `__init__.py` (e.g., `stages/score/__init__.py`)
- CLI files prefixed `cli_` — e.g., `cli_brain.py`, `cli_pricing.py`, `cli_validate.py`
- Brain-subsystem files prefixed `brain_` — e.g., `brain_loader.py`, `brain_schema.py`
- Helper/utility suffix `_helpers.py` — e.g., `check_helpers.py`, `narrative_helpers.py`
- Client files prefixed by domain — e.g., `market_client.py`, `sec_client.py`, `litigation_client.py`
- Renderer section files named `sect{N}_{topic}.py` — e.g., `sect3_financial.py`, `sect7_peril_map.py`

**Functions:**
- `snake_case` for all functions
- Private helpers prefixed with `_` — e.g., `_get_sector_code()`, `_make_company()`, `_load_or_create_state()`
- Factory functions named `make_*` or `create_*` — e.g., `create_serper_search_fn()`
- Stage entry functions named `run()` on Stage classes
- Sourced-value constructors: `sourced_str()`, `sourced_int()`, `sourced_float()`, `sourced_dict()`

**Variables:**
- `snake_case` throughout
- Config dicts named `*_config` — e.g., `scoring_config`, `rf_config`, `sectors_config`
- Unused parameters explicitly assigned to `_` — `_ = (index, total)` (common in callbacks)
- Error message strings assigned to `msg` before raising

**Types:**
- `PascalCase` for all classes and Pydantic models
- `SCREAMING_SNAKE_CASE` for `StrEnum` members — e.g., `HIGH = "HIGH"`, `COMPLETED = "completed"`
- Type aliases defined as module-level constants — e.g., `JsonDict = dict[str, Any]`
- Stage constant lists in `SCREAMING_SNAKE_CASE` — `PIPELINE_STAGES`, `CHUNK_SIZE`

## Code Style

**Formatting:**
- Tool: `ruff` (configured in `ruff.toml` at project root)
- Line length: 99 characters
- Target: Python 3.12 (`target-version = "py312"`)

**Linting:**
- Rule sets: `E` (pycodestyle), `F` (pyflakes), `B` (bugbear), `I` (isort), `UP` (pyupgrade), `S` (bandit security), `C4` (comprehensions), `RUF` (ruff-specific)
- `S101` (assert) suppressed in `tests/**`
- `B008` (function call in arg defaults) suppressed in all CLI files — required by Typer

**Type checking:**
- Pyright strict mode (`typeCheckingMode = "strict"` in `pyproject.toml`)
- Pyright venv-aware: `venvPath = "."`, `venv = ".venv"`

## Import Organization

**Order (enforced by ruff isort):**
1. Standard library
2. Third-party packages
3. First-party `do_uw.*` (known-first-party = `["do_uw"]`)

**Pattern — all files start with:**
```python
from __future__ import annotations
```
This is on 365/385 source files — effectively universal.

**Deferred imports inside functions:**
Used for heavy dependencies (docx, dotenv, logging setup) to avoid import-time side effects:
```python
def _ensure_brain_db() -> None:
    import logging
    from do_uw.brain.brain_schema import connect_brain_db, get_brain_db_path
    ...
```

**TYPE_CHECKING guard:**
Used in 22 files to avoid circular imports at runtime:
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from do_uw.models.company import CompanyProfile
    from do_uw.models.state import ExtractedData
```

**Path aliases:** None — all imports use full `do_uw.*` paths.

## Error Handling

**Custom exception classes:**
Each subsystem defines its own domain-specific exception:
- `DataAcquisitionError` — raised in `src/do_uw/stages/acquire/fallback.py` when all tiers fail
- `PipelineError` — raised in `src/do_uw/pipeline.py` for pipeline-level failures

**Exception message pattern:**
```python
msg = f"Unknown stage: {stage}. Valid: {PIPELINE_STAGES}"
raise ValueError(msg)
```
Message assigned to `msg` variable first (ruff B027 compliance), then raised.

**Catch-and-continue in acquisition:**
Errors in fallback tiers are caught, logged, and next tier tried — never bubble up silently:
```python
except Exception as exc:
    error_msg = f"{tier.name}: {exc}"
    errors.append(error_msg)
    logger.warning("Tier %s failed: %s", tier.name, exc)
```

**Non-fatal warnings at CLI boundary:**
Failures in optional subsystems (brain DB auto-init) are caught and logged as warnings, not exceptions:
```python
except Exception as exc:
    logging.getLogger(__name__).warning(
        "Brain DB auto-init failed (non-fatal): %s", exc
    )
```

**Missing data returns empty, not None:**
Accessor functions like `get_filings()`, `get_market_data()` return `{}` rather than `None` when data is absent:
```python
def get_filings(state: AnalysisState) -> dict[str, Any]:
    if state.acquired_data is None:
        return {}
    return dict(state.acquired_data.filings)
```

## Logging

**Framework:** Python `logging` module (standard library)

**Pattern:** Module-level logger created at top of each file:
```python
logger = logging.getLogger(__name__)
```
Present in all 160 non-`__init__` source files that do substantive work.

**Log levels:**
- `logger.info()` — stage progress, chunk counts, cache hits
- `logger.warning()` — non-fatal fallbacks, missing data, tier failures
- `logger.debug()` — fine-grained navigation (CIK lookups, etc.)
- No `logger.error()` observed — errors either raise or warn

**No `print()` in library code** — only in CLI-facing `console.print()` via Rich.

## Comments

**Module docstrings:**
Every file has a module-level docstring. Format:
```python
"""Short one-line summary.

Longer explanation of purpose, design decisions, and scope.
"""
```

**Class docstrings:**
All public classes have docstrings. Multi-line for models, brief for simple helpers.

**Inline comments:**
Used sparingly for non-obvious logic — e.g., regex explanations, SEC data quirks, `# pyright: ignore[...]` suppression with reason.

**Deprecation marking:**
Deprecated fields use `json_schema_extra={"deprecated": True}` and doc string starting with `DEPRECATED:`:
```python
governance_clean: bool | None = Field(
    default=None,
    json_schema_extra={"deprecated": True},
    description="DEPRECATED: Use section_densities['governance'].level instead. ...",
)
```

**Sectional dividers in long files:**
```python
# -----------------------------------------------------------------------
# Model serialization tests
# -----------------------------------------------------------------------
```

## Data Integrity Pattern (Core Convention)

**Every data point uses `SourcedValue[T]`:**
```python
class SourcedValue[T](BaseModel):
    value: T
    source: str  # "10-K filing 2024-11-01, CIK 0000320193"
    confidence: Confidence  # HIGH | MEDIUM | LOW
    as_of: datetime
    retrieved_at: datetime
```

**Use factory functions from `src/do_uw/stages/extract/sourced.py`:**
```python
from do_uw.stages.extract.sourced import sourced_str, sourced_float, sourced_int

market_cap = sourced_float(3.2e12, "yfinance:info", Confidence.MEDIUM)
legal_name = sourced_str("Apple Inc.", "SEC:submissions:CIK320193", Confidence.HIGH)
```

**Never use raw values for extracted data** — always `SourcedValue`.

## Function Design

**Size:** Enforced at 500 lines per file (CLAUDE.md rule). Functions are typically 10-40 lines.

**Parameters:**
- Type hints required on all parameters (Pyright strict)
- Return type hints required on all functions
- Optional params with `| None` union type, not `Optional[T]`

**Return values:**
- Always explicitly typed
- Empty collections (`{}`, `[]`) instead of `None` for missing-data cases in accessors
- `None` for optional stage outputs on `AnalysisState`

## Module Design

**Exports:**
- `__init__.py` files expose the public API for each stage (e.g., `stages/score/__init__.py` exports `ScoreStage`)
- Private helpers in same file prefixed with `_`
- Re-exports for backward compatibility annotated with comment: `# Re-export for backward compat (tests import _get_sector_code)`

**Barrel files:** `__init__.py` used at every package boundary, always minimal.

**Pydantic models:**
- All models use `BaseModel` from `pydantic`
- `ConfigDict(frozen=False)` on mutable models
- `Field(description=...)` on every field — description required
- `default_factory=lambda: []` (not mutable defaults)

---

*Convention analysis: 2026-02-25*
