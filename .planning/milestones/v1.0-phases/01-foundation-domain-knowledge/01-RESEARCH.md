# Phase 1: Foundation & Domain Knowledge - Research

**Researched:** 2026-02-07
**Domain:** Python project scaffolding, Pydantic state models, CLI pipelines, configuration-driven domain knowledge
**Confidence:** HIGH (most findings verified against official docs and predecessor codebase)

## Summary

Phase 1 establishes the entire foundation for an 8-phase D&O underwriting system rebuild. The core deliverables are: (1) a working Python 3.12 package managed by uv with a Typer CLI entry point, (2) a comprehensive `AnalysisState` Pydantic v2 model covering all 7 pipeline stages, (3) JSON configuration files migrated from the predecessor's ~594KB of validated domain knowledge (359 checks, 10-factor scoring, 17 composite patterns, sector baselines), (4) a pipeline orchestrator skeleton, and (5) a SQLite cache layer.

The predecessor project at `/Users/gorlin/Desktop/Underwriting-2.0/` provides extensive lessons in what NOT to do: a 9,569-line `generate_referral.py` monolith, 4 competing scoring definitions spread across markdown and JSON, 7+ state representations with no single source of truth, and 43,425 total lines of Python across the `tools/` directory alone. The rebuild must enforce strict anti-context-rot discipline from day one.

**Primary recommendation:** Build the AnalysisState model FIRST (it is the single source of truth), then config loading, then CLI/pipeline skeleton, then cache. Every subsequent phase depends on getting the state model right.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | Required by ARCH-01; latest stable features (type parameter syntax, improved error messages) |
| uv | latest | Package manager, virtual envs | Required by ARCH-01; replaces pip/poetry/pipenv; 10-100x faster |
| Pydantic | v2 (>=2.10) | Data models, validation, serialization | Required by ARCH-03; Rust-based core, strict typing, JSON schema generation |
| Typer | >=0.15 | CLI framework | Required by CORE-03; built on Click, Rich integration, type hints for args |
| Rich | >=13.0 | Terminal output, progress display | Typer dependency; structured progress, tables, spinners for pipeline stages |
| httpx | >=0.28 | HTTP client | Required by CLAUDE.md; async support, modern API, replaces requests |
| ruff | >=0.9 | Linting + formatting | Required by CLAUDE.md; replaces flake8/black/isort in one tool |
| Pyright | >=1.1.390 | Static type checking | Required by CLAUDE.md; strict mode for type safety |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| aiosqlite | >=0.22 | Async SQLite access | Cache layer for SEC filings, market data, analysis results |
| pytest | >=8.0 | Testing | Test runner with async support |
| pytest-asyncio | >=0.25 | Async test support | Testing async cache and pipeline code |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| SQLite | DuckDB | CLAUDE.md mentions DuckDB, but REQUIREMENTS.md (ARCH-04), ROADMAP.md success criteria, and prior research all specify SQLite. SQLite is zero-config, simpler for key-value caching. DuckDB excels at analytical queries but adds complexity for a cache. **Use SQLite.** The DuckDB MCP server is available for ad-hoc analysis but not for the cache layer. |
| Typer | Click | Typer wraps Click with type hints and Rich integration. Strictly better for this use case. |
| aiosqlite | sqlite3 | aiosqlite adds async support; needed if pipeline is async. Start with sync sqlite3, add aiosqlite when async pipeline is needed in Phase 2. |
| Pydantic | dataclasses + marshmallow | Pydantic v2 is strictly specified in CLAUDE.md. No alternative needed. |

**Confidence:** HIGH -- all libraries specified in project constitution (CLAUDE.md) or prior research.

**Installation:**
```bash
uv init do-uw --python 3.12
cd do-uw
uv add pydantic typer rich httpx
uv add --dev ruff pyright pytest pytest-asyncio
```

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  __init__.py           # Package version
  cli.py                # Typer CLI entry point (<200 lines)
  pipeline.py           # Pipeline orchestrator (<300 lines)
  models/
    __init__.py          # Re-exports
    state.py             # AnalysisState root model (<500 lines)
    company.py           # CompanyProfile, CompanyIdentity
    financials.py        # FinancialStatements, DistressIndicators
    market.py            # StockData, InsiderTrading, ShortInterest
    governance.py        # GovernanceProfile, BoardComposition
    litigation.py        # LitigationLandscape, CaseDetails
    scoring.py           # ScoringResult, FactorScore, TierClassification
    common.py            # Shared types: SourcedValue, Confidence, DataSource
  stages/
    __init__.py          # StageResult protocol
    resolve/
      __init__.py
    acquire/
      __init__.py
    extract/
      __init__.py
    analyze/
      __init__.py
    score/
      __init__.py
    benchmark/
      __init__.py
    render/
      __init__.py
  config/
    __init__.py          # Config loader
    loader.py            # JSON config loading with validation
  brain/                 # Migrated knowledge assets (JSON files)
    checks.json          # 359 D&O-specific checks
    scoring.json         # 10-factor scoring weights + rules
    patterns.json        # 17 composite patterns
    sectors.json         # Sector baselines
    red_flags.json       # 11 critical red flags
  cache/
    __init__.py
    sqlite_cache.py      # SQLite cache implementation
tests/
  conftest.py
  models/
    test_state.py
  config/
    test_loader.py
  test_cli.py
  test_pipeline.py
```

### Pattern 1: SourcedValue -- Data Integrity by Design
**What:** Every data point in the system carries provenance metadata.
**When to use:** ALL data stored in AnalysisState.
**Why:** CLAUDE.md NON-NEGOTIABLE: "Every data point MUST have a `source` and `confidence` field."

```python
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Generic, TypeVar

T = TypeVar("T")

class Confidence(str, Enum):
    HIGH = "HIGH"      # Audited/official source (SEC filings, exchange data)
    MEDIUM = "MEDIUM"  # Unaudited/estimates (company press releases, analyst data)
    LOW = "LOW"        # Derived/web (news articles, web search, single source)

class SourcedValue(BaseModel, Generic[T]):
    """Every data point carries its provenance."""
    value: T
    source: str = Field(description="Specific filing type + date + URL/CIK reference")
    confidence: Confidence
    as_of: datetime = Field(description="When this data was valid")
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
```

**Confidence:** HIGH -- pattern directly implements CLAUDE.md data integrity requirement.

### Pattern 2: Stage Protocol with Input/Output Contracts
**What:** Each pipeline stage has typed input/output contracts.
**When to use:** All 7 pipeline stages.
**Why:** ARCH-02 requires "defined input/output contracts and validation gates."

```python
from enum import Enum
from pydantic import BaseModel
from typing import Protocol

class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class StageResult(BaseModel):
    stage: str
    status: StageStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

class Stage(Protocol):
    """Protocol for all pipeline stages."""
    name: str

    async def run(self, state: "AnalysisState") -> "AnalysisState":
        """Execute stage, returning modified state."""
        ...

    def validate_input(self, state: "AnalysisState") -> list[str]:
        """Return list of validation errors. Empty = valid."""
        ...
```

**Confidence:** HIGH -- follows standard pipeline pattern with Pydantic validation.

### Pattern 3: AnalysisState as Single Source of Truth
**What:** One root model that is THE state for the entire analysis.
**When to use:** Everywhere. This is the core architectural decision.
**Why:** CORE-05 requires "single AnalysisState Pydantic model serialized as JSON, enabling resume-from-failure."

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class AnalysisState(BaseModel):
    """THE single source of truth for the entire analysis.
    Serialized to JSON between stages. Enables resume-from-failure."""

    # Metadata
    version: str = "1.0.0"
    ticker: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Pipeline progress
    stages: dict[str, StageResult] = Field(default_factory=lambda: {
        stage: StageResult(stage=stage, status=StageStatus.PENDING)
        for stage in ["resolve", "acquire", "extract", "analyze", "score", "benchmark", "render"]
    })

    # Stage outputs (populated as stages complete)
    company: Optional[CompanyProfile] = None      # After RESOLVE
    acquired_data: Optional[AcquiredData] = None   # After ACQUIRE
    extracted: Optional[ExtractedData] = None      # After EXTRACT
    analysis: Optional[AnalysisResults] = None     # After ANALYZE
    scoring: Optional[ScoringResult] = None        # After SCORE
    benchmark: Optional[BenchmarkResult] = None    # After BENCHMARK
    # RENDER produces files, not state

    model_config = ConfigDict(
        json_schema_extra={"title": "D&O Underwriting Analysis State"},
    )
```

**Confidence:** HIGH -- directly implements CORE-05 and ARCH-03.

### Pattern 4: Config-Driven Domain Knowledge
**What:** All scoring weights, thresholds, patterns, checks, and sector baselines stored in JSON, loaded and validated by Pydantic.
**When to use:** All domain knowledge that could change.
**Why:** ARCH-09 requires "Scoring weights, thresholds, tier boundaries, pattern trigger conditions, and red flag ceiling values stored in JSON configuration files -- never hardcoded."

```python
from pydantic import BaseModel
from pathlib import Path
import json

class ConfigLoader:
    """Loads and validates all config files from brain/ directory."""

    def __init__(self, brain_dir: Path):
        self.brain_dir = brain_dir

    def load_checks(self) -> CheckRegistry:
        return CheckRegistry.model_validate_json(
            (self.brain_dir / "checks.json").read_text()
        )

    def load_scoring(self) -> ScoringConfig:
        return ScoringConfig.model_validate_json(
            (self.brain_dir / "scoring.json").read_text()
        )
    # ... etc for patterns, sectors, red_flags
```

**Confidence:** HIGH -- Pydantic v2's `model_validate_json()` handles validation + deserialization.

### Anti-Patterns to Avoid (from Predecessor)

- **Monolithic files:** Predecessor's `generate_referral.py` was 9,569 lines, `check_executor.py` was 4,115 lines. ARCH-05 caps at 500 lines per file.
- **Multiple state representations:** Predecessor had `analysis.json`, `pipeline_results.json`, `master_data_manifest.json`, `execution_state_*.json`, `check_tracker.json`, `scoring_result.json` -- at least 7 different state files. This system has ONE: `AnalysisState`.
- **Competing scoring definitions:** Predecessor had scoring rules in `SYSTEM/03_SCORING_ENGINE.md` (markdown), `config/scoring_weights.json` (JSON), `config/factor_thresholds.json` (JSON), `config/tier_boundaries.json` (JSON), and embedded in `tools/check_executor.py` (Python). This system has ONE: `brain/scoring.json`.
- **Hardcoded thresholds:** Predecessor mixed thresholds in Python code and config files. ALL thresholds go in JSON config.
- **Importing deprecated modules:** Predecessor had 14 try/except import blocks in `orchestrator.py` alone, each handling missing or deprecated modules. Clean dependency graph from day one.
- **Data acquisition mixed with analysis:** Predecessor's `build_analysis_json.py` (65KB) mixed data fetching with analysis. Strict separation: ACQUIRE stage fetches, EXTRACT+ stages analyze.

**Confidence:** HIGH -- observed directly in predecessor codebase.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI argument parsing | argparse wrapper | Typer | Type hints become args automatically; Rich integration |
| Progress display | Custom print statements | Rich Progress/Status | Multiple concurrent tasks, spinners, tables |
| JSON serialization | json.dumps with custom encoders | Pydantic model_dump_json() | Handles datetime, enums, nested models; schema generation |
| Config validation | Manual dict checking | Pydantic model_validate_json() | Type-safe, detailed error messages, schema docs |
| File line limit enforcement | Custom Python script | Simple shell script in CI | `find src -name "*.py" -exec awk 'END{if(NR>500){print FILENAME": "NR" lines"; exit 1}}' {} \;` |
| HTTP client | urllib3/requests wrapper | httpx | Already specified; async support built in |
| Cache schema migration | Custom DDL scripts | Simple version column + migration function | SQLite schema is simple (3-4 tables); no ORM needed |

**Key insight:** Ruff does NOT have a built-in rule for maximum file line count (no equivalent to pylint's C0302). This must be enforced with a custom CI check (see Common Pitfalls section).

## Common Pitfalls

### Pitfall 1: File Length Enforcement Gap
**What goes wrong:** ARCH-05 requires no source file over 500 lines "enforced via CI/linting check." Ruff has no such rule. Pyright has no such rule.
**Why it happens:** People assume "linter" means ruff handles it. Ruff handles line LENGTH (E501), not file LENGTH.
**How to avoid:** Create a standalone script that runs in CI. Options:
  1. Shell script: `find src -name "*.py" | while read f; do lines=$(wc -l < "$f"); if [ "$lines" -gt 500 ]; then echo "FAIL: $f has $lines lines (max 500)"; exit 1; fi; done`
  2. Python script in `scripts/check_file_lengths.py` -- more portable, can be called from `uv run`
  3. pre-commit hook (if pre-commit is in scope)
**Warning signs:** Any file approaching 400 lines should be split proactively.
**Confidence:** HIGH -- verified that ruff has no file-line-count rule via official ruff rules documentation.

### Pitfall 2: Over-Engineering the State Model
**What goes wrong:** Trying to define every field of AnalysisState upfront when later phases will reveal needs.
**Why it happens:** Phase 1 says "complete AnalysisState Pydantic model" covering all 7 stages.
**How to avoid:** Define the STRUCTURE (root model + per-stage typed sub-models) completely. Use `Optional[T] = None` for stage outputs. Define detailed fields for stage sub-models as placeholders that later phases flesh out. The model should serialize/deserialize empty but be typed for all expected data.
**Warning signs:** Spending more than 50% of time on model fields that Phase 1 can't test.
**Confidence:** HIGH -- standard pattern for incremental model development.

### Pitfall 3: SQLite vs DuckDB Confusion
**What goes wrong:** CLAUDE.md says "DuckDB at `.cache/analysis.duckdb`" but REQUIREMENTS.md (ARCH-04), ROADMAP.md success criteria #5, and all prior research say SQLite.
**Why it happens:** CLAUDE.md was likely written after the DuckDB MCP server was installed and the terminology leaked.
**How to avoid:** Use SQLite for the cache layer. The DuckDB MCP server is installed and available for ad-hoc analytical queries, but the application's own cache is SQLite as specified in ARCH-04 and the research docs.
**Warning signs:** If someone writes `import duckdb` in cache code, that's wrong.
**Confidence:** HIGH -- ARCH-04 explicitly says "SQLite local cache." ROADMAP says "SQLite cache database."

### Pitfall 4: Knowledge Migration as Simple File Copy
**What goes wrong:** Copying predecessor config files verbatim without restructuring.
**Why it happens:** The predecessor has 6 config files (`config/`) + 10+ BRAIN files with overlapping and inconsistent data.
**How to avoid:** The predecessor's knowledge is spread across:
  - `SYSTEM/BRAIN/checks.json` (198KB, 359 checks -- THE primary asset)
  - `SYSTEM/BRAIN/PATTERNS.md` (32KB, 17 patterns -- needs conversion to JSON)
  - `SYSTEM/BRAIN/SCORING/SCORING.md` (14KB, scoring model -- needs conversion to JSON)
  - `config/scoring_weights.json` (14KB, scoring rules -- KEEP, already JSON)
  - `config/critical_red_flags.json` (7KB, 11 red flags -- KEEP, already JSON)
  - `config/sector_baselines.json` (8KB, sector data -- KEEP, already JSON)
  - `config/factor_thresholds.json` (7KB, thresholds -- merge into scoring.json)
  - `config/tier_boundaries.json` (6KB, tier definitions -- merge into scoring.json)
  - `config/check_registry.json` (10KB, 20-check sample -- IGNORE, checks.json is authoritative)

  **Migration strategy:**
  1. `checks.json` -- copy as-is (already JSON, 359 checks, well-structured)
  2. `scoring.json` -- consolidate from `scoring_weights.json` + `factor_thresholds.json` + `tier_boundaries.json`
  3. `patterns.json` -- convert from `PATTERNS.md` to JSON (17 patterns with trigger conditions)
  4. `sectors.json` -- copy from `sector_baselines.json` (already JSON)
  5. `red_flags.json` -- copy from `critical_red_flags.json` (already JSON)
  6. DISCARD: `check_registry.json` (20-check sample, superseded by `checks.json`), all markdown duplicates

**Warning signs:** If migration plan has more than 5 output files, it's too many.
**Confidence:** HIGH -- verified by reading all predecessor config and BRAIN files.

### Pitfall 5: Overcomplicating the Pipeline Skeleton
**What goes wrong:** Implementing actual stage logic in Phase 1 instead of stubs.
**Why it happens:** Success criteria #1 says "invokes the pipeline and shows structured progress output."
**How to avoid:** Each stage is a stub that: (1) validates input, (2) logs "running stage X", (3) updates state.stages[x].status to COMPLETED, (4) returns state. No actual data acquisition, extraction, or analysis. Just the skeleton.
**Warning signs:** Any `import httpx` or MCP calls in Phase 1 stage code.
**Confidence:** HIGH -- success criteria explicitly says "stages listed, each marked pending."

### Pitfall 6: Typer + Rich Integration Overhead
**What goes wrong:** Over-investing in CLI UX before the pipeline works.
**Why it happens:** Rich has beautiful output options. It's tempting to build elaborate dashboards.
**How to avoid:** Phase 1 CLI needs exactly:
  - `do-uw analyze <TICKER>` command
  - A Rich Status/Progress display showing 7 stages (pending/running/done)
  - Error handling that prints a clean message, not a traceback
  - `--verbose` flag for debug output
  That's it. No dashboards, tables, or fancy formatting until Phase 8.
**Confidence:** HIGH -- derived from success criteria.

## Code Examples

### pyproject.toml Configuration
```toml
[project]
name = "do-uw"
version = "0.1.0"
description = "D&O Liability Underwriting Worksheet System"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.10",
    "typer>=0.15",
    "rich>=13.0",
    "httpx>=0.28",
]

[project.scripts]
do-uw = "do_uw.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
target-version = "py312"
line-length = 99
src = ["src"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "B",   # flake8-bugbear
    "I",   # isort
    "UP",  # pyupgrade
    "S",   # flake8-bandit (security)
    "C4",  # flake8-comprehensions
    "RUF", # ruff-specific rules
]

[tool.ruff.lint.isort]
known-first-party = ["do_uw"]

[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
venvPath = "."
venv = ".venv"
```

**Source:** Official uv docs (https://docs.astral.sh/uv/concepts/projects/config/), ruff docs (https://docs.astral.sh/ruff/settings/).
**Confidence:** HIGH -- verified against official documentation.

### Typer CLI with Rich Progress
```python
"""CLI entry point for do-uw."""
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="do-uw", help="D&O Liability Underwriting Worksheet")
console = Console()

STAGES = ["resolve", "acquire", "extract", "analyze", "score", "benchmark", "render"]

@app.command()
def analyze(
    ticker: str = typer.Argument(help="Stock ticker symbol (e.g., AAPL)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
):
    """Analyze a company for D&O underwriting."""
    ticker = ticker.upper()
    console.print(f"\n[bold]D&O Underwriting Analysis: {ticker}[/bold]\n")

    # Show pipeline stages
    table = Table(title="Pipeline Stages")
    table.add_column("Stage", style="cyan")
    table.add_column("Status", style="yellow")
    for stage in STAGES:
        table.add_row(stage.upper(), "pending")
    console.print(table)

    # In Phase 1, this just shows the stages and exits.
    # Later phases will actually run each stage.
```

**Source:** Typer docs (https://typer.tiangolo.com/tutorial/progressbar/), Rich docs.
**Confidence:** HIGH -- verified pattern from official Typer documentation.

### SQLite Cache Initialization
```python
"""SQLite cache for API responses and analysis results."""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DEFAULT_CACHE_DIR = Path.home() / ".do-uw" / "cache"

class AnalysisCache:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path or DEFAULT_CACHE_DIR / "cache.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    content_type TEXT DEFAULT 'json'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)
            # Initialize version if empty
            if not conn.execute("SELECT version FROM schema_version").fetchone():
                conn.execute("INSERT INTO schema_version (version) VALUES (1)")

    def get(self, key: str) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None
            value, expires_at = row
            if expires_at and datetime.fromisoformat(expires_at) < datetime.utcnow():
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                return None
            return value

    def set(self, key: str, value: str, source: str, ttl_hours: int = 24):
        expires_at = (datetime.utcnow() + timedelta(hours=ttl_hours)).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO cache (key, value, source, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (key, value, source, datetime.utcnow().isoformat(), expires_at),
            )
```

**Source:** Python sqlite3 stdlib docs, ARCH-04 requirements.
**Confidence:** HIGH -- standard SQLite cache pattern.

### File Length Check Script
```python
#!/usr/bin/env python3
"""Enforce ARCH-05: No source file over 500 lines."""
import sys
from pathlib import Path

MAX_LINES = 500
WARN_LINES = 400
SRC_DIR = Path("src")

def check_file_lengths() -> int:
    failures = []
    warnings = []
    for py_file in SRC_DIR.rglob("*.py"):
        line_count = sum(1 for _ in py_file.open())
        if line_count > MAX_LINES:
            failures.append((py_file, line_count))
        elif line_count > WARN_LINES:
            warnings.append((py_file, line_count))

    for path, count in warnings:
        print(f"  WARN: {path} has {count} lines (approaching {MAX_LINES} limit)")

    for path, count in failures:
        print(f"  FAIL: {path} has {count} lines (max {MAX_LINES})")

    if failures:
        print(f"\n{len(failures)} file(s) exceed {MAX_LINES} line limit.")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(check_file_lengths())
```

**Source:** Custom implementation required because ruff lacks file-length-count rule.
**Confidence:** HIGH -- addresses a verified gap in ruff's rule set.

## Predecessor Knowledge Asset Inventory

### Files to Migrate (Total: ~594 KB across BRAIN/ and config/)

| File | Size | Format | Content | Migration Action |
|------|------|--------|---------|------------------|
| `SYSTEM/BRAIN/checks.json` | 198 KB | JSON | 359 D&O checks with IDs, sections, pillars, thresholds, data sources, execution modes | Copy as `brain/checks.json` |
| `SYSTEM/BRAIN/BRAIN.md` | 117 KB | Markdown | Human-readable version of all 359 checks (authoritative documentation) | Reference only -- checks.json is machine-readable source |
| `SYSTEM/BRAIN/PATTERNS.md` | 33 KB | Markdown | 17 composite patterns: 6 stock, 3 business, 2 financial, 3 governance, 3 forward | Convert to `brain/patterns.json` |
| `SYSTEM/BRAIN/SCORING/SCORING.md` | 14 KB | Markdown | 10-factor scoring model, empirical foundation, tier definitions | Convert to `brain/scoring.json` (merge with config/*.json) |
| `config/scoring_weights.json` | 14 KB | JSON | 10 factors with weights, max points, detailed rules per factor | Merge into `brain/scoring.json` |
| `config/sector_baselines.json` | 8 KB | JSON | Sector-specific baselines: short interest, volatility, leverage, guidance miss rates, insider trading norms, ETFs, dismissal rates | Copy as `brain/sectors.json` |
| `config/critical_red_flags.json` | 7 KB | JSON | 11 critical red flags with ceiling scores, processing rules, binding decision protocols | Copy as `brain/red_flags.json` |
| `config/factor_thresholds.json` | 7 KB | JSON | Sub-factor threshold ranges (stock decline, short interest, volatility, distress, guidance, insider) | Merge into `brain/scoring.json` |
| `config/tier_boundaries.json` | 6 KB | JSON | 6 W-series tiers (WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH) with score ranges, tower positions, severity ranges | Merge into `brain/scoring.json` |

### Files to IGNORE
| File | Reason |
|------|--------|
| `config/check_registry.json` | 20-check sample only; `checks.json` is authoritative with all 359 |
| `SYSTEM/BRAIN/EXTENDING.md` | Documentation for extending the predecessor system; not applicable to new architecture |
| `SYSTEM/BRAIN/OPTIMIZATION_RESEARCH.md` | Performance tuning notes for predecessor; different architecture |
| `SYSTEM/BRAIN/learning_log.json` | Empty log (0 analyses recorded) |
| `SYSTEM/BRAIN/CHANGELOG.md` | Predecessor changelog |
| `SYSTEM/BRAIN/CHECKS/*.csv` | CSV versions of checks; `checks.json` is authoritative |
| `SYSTEM/BRAIN/RULES/*.md` | Execution rules for predecessor's architecture |

### checks.json Structure (KEY ASSET)
The 359 checks are organized as:
- **Section 1 (Business):** 58 checks
- **Section 2 (Stock/Market):** 35 checks
- **Section 3 (Financial):** 32 checks
- **Section 4 (Litigation):** 56 checks
- **Section 5 (Governance):** 90 checks
- **Section 6 (Forward-Looking):** 88 checks

Each check has: `id`, `name`, `section`, `pillar` (P1-P4), `factors` (scoring), `required_data`, `data_locations`, `threshold`, `execution_mode`, `claims_correlation`, `tier`.

Four pillars organize the analytical framework:
- **P1_WHAT_WRONG** -- What could go wrong with this company?
- **P2_WHO_BLAMED** -- Who would get blamed?
- **P3_HOW_BAD** -- How severe would the consequences be?
- **P4_WHAT_NEXT** -- What's the forward-looking risk?

### Scoring Model Summary
- 10 factors totaling 100 points (quality_score = 100 - risk_points)
- F.1 Prior Litigation (20 pts) >> F.2 Stock Decline (15) >> F.3 Restatement (12) >> F.4 IPO/SPAC (10), F.5 Guidance (10) >> F.6 Short Interest (8), F.7 Volatility (9), F.8 Distress (8) >> F.9 Governance (6) >> F.10 Officers (2)
- Insider trading is a MULTIPLIER on F.2, not standalone
- 11 critical red flags set CEILING on quality score (cannot score higher)
- 6 W-series tiers: WIN (86-100), WANT (71-85), WRITE (51-70), WATCH (31-50), WALK (11-30), NO_TOUCH (0-10)
- Sector-specific adjustments for short interest, volatility, leverage, guidance misses, insider trading

## State of the Art

| Old Approach (Predecessor) | Current Approach (New System) | Impact |
|---------------------------|-------------------------------|--------|
| markdown prose for checks | JSON with Pydantic validation | Machine-executable, type-safe |
| 7+ state files | Single AnalysisState model | No drift, resume-from-failure |
| 9,500-line monolith | 500-line file cap | Maintainable, reviewable |
| pip + requirements.txt | uv + pyproject.toml + uv.lock | Reproducible, fast, locked |
| No type checking | Pyright strict mode | Catches errors at dev time |
| Manual formatting | ruff format + lint | Consistent, automated |
| No caching | SQLite cache with TTL | Fewer API calls, faster re-runs |
| Prose-based scoring rules | JSON config with Pydantic models | Single source of truth, no drift |

## Open Questions

1. **DuckDB MCP server role**: The DuckDB MCP server is installed. Should it be used for ad-hoc queries against the SQLite cache, or should it be left unused? The cache itself should be SQLite per ARCH-04, but DuckDB can read SQLite files natively. **Recommendation:** Defer to Phase 2. For Phase 1, just implement SQLite cache.

2. **AnalysisState granularity**: How detailed should the sub-models be in Phase 1? The success criteria says "covering all 7 pipeline stages" but the actual fields won't be populated until Phases 2-7. **Recommendation:** Define the top-level structure with typed Optional sub-models. Each sub-model should have a few placeholder fields with docstrings explaining what later phases will add. This satisfies "serializes to JSON and deserializes" while keeping Phase 1 focused.

3. **checks.json format evolution**: The predecessor's checks.json is 198KB and well-structured. Should it be taken as-is or restructured for the new architecture? **Recommendation:** Copy as-is for Phase 1 (it already validates as JSON). Restructure if needed when Phase 6 (SCORE stage) implements actual check execution. The JSON is already machine-parseable.

4. **Async from day one?**: Should the pipeline skeleton be async or sync? **Recommendation:** Sync for Phase 1. The pipeline is sequential (stages run one at a time). Async only matters for Phase 2 when multiple data sources are fetched concurrently. Starting sync keeps Phase 1 simple.

5. **PATTERNS.md conversion to JSON**: The 17 composite patterns in PATTERNS.md contain trigger conditions expressed as pseudocode (e.g., `IF single_day_drop > 15% AND trigger_identified AND peer_avg_drop < 5% THEN EVENT_COLLAPSE = DETECTED`). How should these be represented in JSON? **Recommendation:** Use a structured JSON format with `trigger_conditions` as a list of objects with `field`, `operator`, `value`. The pseudocode becomes machine-readable. This conversion is Phase 1 work since ARCH-10 requires carrying forward the knowledge.

## Sources

### Primary (HIGH confidence)
- Predecessor codebase at `/Users/gorlin/Desktop/Underwriting-2.0/` -- all knowledge files read directly
- uv official docs: https://docs.astral.sh/uv/concepts/projects/config/
- Ruff official docs: https://docs.astral.sh/ruff/settings/, https://docs.astral.sh/ruff/rules/, https://docs.astral.sh/ruff/faq/
- Pydantic v2 official docs: https://docs.pydantic.dev/latest/concepts/unions/
- Typer official docs: https://typer.tiangolo.com/tutorial/progressbar/
- Pyright configuration: https://github.com/microsoft/pyright/blob/main/docs/configuration.md
- Project CLAUDE.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, research/STACK.md

### Secondary (MEDIUM confidence)
- WebSearch results for uv project setup patterns, verified against official docs
- WebSearch results for DuckDB vs SQLite, cross-referenced with project requirements
- Hishel library for httpx caching (https://pypi.org/project/hishel/)

### Tertiary (LOW confidence)
- WebSearch results for pre-commit file length enforcement patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries specified in project constitution or verified against official docs
- Architecture: HIGH -- patterns derived from project requirements + predecessor failure analysis
- Pitfalls: HIGH -- directly observed in predecessor codebase
- Knowledge migration: HIGH -- all files read and inventoried with exact sizes

**Research date:** 2026-02-07
**Valid until:** 2026-03-07 (stable domain; libraries unlikely to have breaking changes)

## RESEARCH COMPLETE

**Phase:** 1 - Foundation & Domain Knowledge
**Confidence:** HIGH

### Key Findings

1. The predecessor's ~594KB of domain knowledge is well-structured JSON and markdown; the primary asset is `checks.json` (198KB, 359 checks). Migration requires copying 3 JSON files as-is and converting 2 markdown files (PATTERNS.md, SCORING.md) to JSON format, plus consolidating 3 scoring-related JSON files into one.

2. Ruff does NOT have a file-line-count rule (no C0302 equivalent). The 500-line-per-file limit (ARCH-05) must be enforced with a custom CI script -- either a shell one-liner or a Python script.

3. The CLAUDE.md says "DuckDB" for cache but EVERY other document (REQUIREMENTS.md ARCH-04, ROADMAP.md success criteria, research/STACK.md) says SQLite. Use SQLite.

4. The AnalysisState model should define the STRUCTURE completely (root + typed sub-models) but use `Optional[T] = None` for stage outputs. This satisfies "serializes to JSON and deserializes" while deferring field detail to later phases.

5. The predecessor's biggest architectural failures were: monolithic files (9,569-line script), multiple competing state representations (7+), multiple scoring definitions (4+), and mixing data acquisition with analysis. The new architecture's anti-context-rot rules directly address each of these.

### File Created

`.planning/phases/01-foundation-domain-knowledge/01-RESEARCH.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | All libraries specified in project constitution; versions verified against official docs |
| Architecture | HIGH | Patterns derived from requirements + predecessor failure analysis; predecessor code inspected |
| Pitfalls | HIGH | Each pitfall observed directly in predecessor or verified against official tool docs |
| Knowledge Migration | HIGH | All predecessor files read with exact sizes, formats, and content inventoried |

### Open Questions

1. DuckDB MCP role -- defer to Phase 2
2. AnalysisState field granularity -- define structure, use Optional for details
3. checks.json restructuring -- copy as-is, restructure later if needed
4. Async vs sync -- start sync, add async in Phase 2
5. PATTERNS.md JSON conversion format -- structured trigger conditions

### Ready for Planning

Research complete. Planner can now create PLAN.md files for plans 01-01, 01-02, and 01-03.
