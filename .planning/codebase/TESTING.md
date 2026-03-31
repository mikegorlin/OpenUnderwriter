# Testing Patterns

**Analysis Date:** 2026-02-25

## Test Framework

**Runner:**
- pytest 9.0.2+
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`
- `testpaths = ["tests"]`, `pythonpath = ["src"]`

**Assertion Library:**
- pytest built-in `assert` (S101 suppressed in `tests/**` via `ruff.toml`)

**Async support:**
- `pytest-asyncio` 1.3.0+ installed but no async tests detected in current codebase (all tests are synchronous)

**Run Commands:**
```bash
uv run pytest                      # Run all tests
uv run pytest tests/test_pipeline.py  # Run specific file
uv run pytest -k "test_score"      # Run by keyword
uv run pytest --tb=short           # Short traceback format
```

No coverage configuration detected in `pyproject.toml` — no enforced coverage threshold.

## Test File Organization

**Location:** Tests live in a dedicated `tests/` root directory (NOT co-located with source).

**Structure mirrors `src/do_uw/`:**
```
tests/
├── conftest.py                        # Shared fixtures (project_root, fixtures_dir)
├── stages/
│   ├── acquire/                       # Tests for src/do_uw/stages/acquire/
│   ├── analyze/                       # Tests for src/do_uw/stages/analyze/
│   ├── benchmark/                     # Tests for src/do_uw/stages/benchmark/
│   ├── extract/                       # Tests for src/do_uw/stages/extract/
│   ├── render/                        # Tests for src/do_uw/stages/render/
│   └── score/                         # Tests for src/do_uw/stages/score/
├── brain/                             # Tests for src/do_uw/brain/
├── config/                            # Tests for src/do_uw/config/
├── knowledge/                         # Tests for src/do_uw/knowledge/
├── models/                            # Tests for src/do_uw/models/
├── render/                            # Render integration tests
├── ground_truth/                      # Hand-verified reference data
│   ├── helpers.py                     # Shared helpers (NOT a test file)
│   ├── aapl.py, coin.py, tsla.py ...  # Per-ticker ground truth constants
│   └── __init__.py                    # Exports ALL_GROUND_TRUTH dict
└── test_*.py                          # Top-level tests (pipeline, analyze, score, etc.)
```

**Naming:**
- All test files: `test_{module_name}.py`
- All test functions/methods: `test_{description_in_snake_case}`
- Stage-level tests sometimes in subdirs, sometimes at top level (both patterns exist)

## Test Structure

**Suite Organization (class-based, preferred):**
```python
class TestScoringModels:
    """Test that all new Pydantic models serialize/deserialize."""

    def test_risk_type_enum(self) -> None:
        assert RiskType.BINARY_EVENT == "BINARY_EVENT"

    def test_risk_type_classification(self) -> None:
        rtc = RiskTypeClassification(
            primary=RiskType.GROWTH_DARLING,
            secondary=RiskType.GUIDANCE_DEPENDENT,
            evidence=["High growth", "Frequent guidance"],
        )
        data = rtc.model_dump()
        assert data["primary"] == "GROWTH_DARLING"
        restored = RiskTypeClassification.model_validate(data)
        assert restored.primary == RiskType.GROWTH_DARLING
```

**Function-based tests (also common):**
```python
@pytest.mark.parametrize("ticker", TICKERS)
def test_identity_legal_name(ticker: str) -> None:
    """Verify extracted legal name matches ground truth."""
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    ...
```

**Patterns:**
- Module docstring on every test file explaining scope and design decisions
- `from __future__ import annotations` on all test files (same as source)
- Descriptive docstrings on every test method
- Type hints on all test functions (`-> None`)
- Build helpers at module level, not inline (e.g., `_make_company()`, `_sv()`, `_make_check()`)

## Mocking

**Framework:** `unittest.mock` — `patch` decorator and `MagicMock`

**Primary pattern — `@patch` decorator stacking:**
```python
@patch(
    "do_uw.stages.acquire.orchestrator.AcquisitionOrchestrator.run",
    side_effect=_mock_orchestrator_run,
)
@patch(
    "do_uw.stages.resolve.sec_identity.sec_get",
    side_effect=_mock_sec_get,
)
def test_pipeline_runs_all_stages(
    self,
    _mock_si: MagicMock,
    _mock_orch: MagicMock,
) -> None:
    ...
```

**Mock return value helpers:**
Factory functions at module level produce consistent mock data:
```python
def _mock_cache() -> MagicMock:
    """Create a mock AnalysisCache that always returns None (no cache)."""
    cache = MagicMock()
    cache.get.return_value = None
    return cache

def _mock_acquired_data() -> AcquiredData:
    """Create mock AcquiredData that passes all gates."""
    return AcquiredData(
        filings={"10-K": [{"f": 1}], ...},
        gate_results=[{"gate_name": "annual_report", "passed": True, ...}],
    )
```

**What to mock:**
- All network calls (SEC EDGAR, yfinance, web search) — patch at the lowest-level function
- Cache reads/writes — inject `MagicMock()` with `cache.get.return_value = None`
- Stage sub-orchestrators in pipeline integration tests
- `side_effect` used when mock needs to inspect args or return data based on URL pattern

**What NOT to mock:**
- Pydantic model creation/validation — always use real models
- Scoring engine logic against real `scoring.json` / `red_flags.json` config files
- DuckDB schema creation — tests use in-memory DuckDB (`:memory:`)
- Business logic being tested (the system under test)

## Fixtures and Factories

**Global conftest (`tests/conftest.py`):**
```python
@pytest.fixture()
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent

@pytest.fixture()
def fixtures_dir() -> Path:
    """Return the test fixtures directory."""
    return Path(__file__).parent / "fixtures"
```

**In-memory DuckDB fixture (pattern in `tests/brain/test_brain_schema.py`):**
```python
@pytest.fixture()
def conn(self) -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection with schema."""
    connection = connect_brain_db(":memory:")
    create_schema(connection)
    return connection
```

**Parametrized ticker fixture (pattern in `tests/test_pipeline_smoke.py`):**
```python
@pytest.fixture(params=TICKERS)
def ticker(request: pytest.FixtureRequest) -> str:
    return request.param  # type: ignore[no-any-return]

@pytest.fixture()
def output_dir(ticker: str) -> Path:
    """Find the most recent output directory for a ticker."""
    base = Path("output")
    date_dirs = sorted(base.glob(f"{ticker}-*"), reverse=True)
    if date_dirs:
        return date_dirs[0]
    return base / ticker
```

**Test data builders (`_sv()` shorthand in `tests/test_score_stage.py`):**
```python
NOW = datetime.now(tz=UTC)

def _sv(value: object, source: str = "test", conf: Confidence = Confidence.HIGH) -> SourcedValue:
    """Shorthand to create a SourcedValue for testing."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=conf,
        as_of=NOW,
    )
```

**Test data builder factories:**
```python
def _make_company(sector: str = "TECH", market_cap: float = 5e9) -> CompanyProfile:
    """Create a CompanyProfile with given sector and market cap."""
    return CompanyProfile(
        identity=CompanyIdentity(ticker="TEST", sector=_sv(sector)),
        market_cap=_sv(market_cap),
    )
```

**Location:** No `tests/fixtures/` directory with data files detected. Test data is built programmatically or loaded from real config files (e.g., `scoring.json`, `red_flags.json`).

## Ground Truth Testing

A unique test pattern: hand-verified reference data for 10 real companies used to validate extraction accuracy.

**Ground truth data files (`tests/ground_truth/`):**
```python
# tests/ground_truth/aapl.py
GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {"legal_name": "Apple Inc.", "cik": "320193", ...},
    "financials": {"revenue_latest": 416161000000.0, ...},
    "governance": {"board_size": 8, "ceo_name": "Tim Cook", ...},
    ...
}
```

**Ground truth test pattern:**
- Tests `pytest.skip()` if no state file for ticker (requires prior pipeline run)
- `pytest.mark.xfail()` for known extraction limitations
- `assert_financial_close()` with relative tolerance (default 5%) for numeric fields:
```python
def assert_financial_close(
    ticker: str, field_name: str, actual: float | None, expected: float,
    *, rel_tol: float = 0.05,
) -> None:
    ...
    is_close = abs(actual - expected) <= rel_tol * abs(expected)
    assert is_close, f"{field_name}: {actual:,.0f} vs expected {expected:,.0f} ..."
```
- Accuracy report printed to stdout via `print_accuracy_report()` helper

**Tickers covered:** AAPL, COIN, DIS, JPM, MRNA, NFLX, NVDA, PG, SMCI, TSLA, XOM

## Coverage

**Requirements:** None enforced — no `--cov` in pytest config, no minimum threshold.

**View coverage manually:**
```bash
uv run pytest --cov=do_uw --cov-report=term-missing
```

## Test Types

**Unit Tests (majority):**
- Scope: Individual functions, Pydantic model creation/serialization, pure logic
- Location: `tests/test_score_stage.py`, `tests/test_analyze_stage.py`, `tests/brain/`, etc.
- No external dependencies; all data built in-process

**Integration Tests:**
- Scope: Full stage execution with mocked external calls, model roundtrip, config loading
- Pattern: `TestScoreStageRun.test_score_stage_populates_state()` — runs real `ScoreStage.run()` with real config files and real Pydantic models
- Location: `tests/test_pipeline.py`, `tests/test_phase26_integration.py`, `tests/knowledge/test_integration.py`

**Smoke Tests (requires prior pipeline run):**
- Scope: Output file existence, format validity, content quality checks
- Location: `tests/test_pipeline_smoke.py`
- Always guard with `pytest.skip()` if output doesn't exist

**Ground Truth Validation Tests (requires prior pipeline run):**
- Scope: Extraction accuracy against hand-verified data
- Location: `tests/test_ground_truth_validation.py`, `tests/test_ground_truth_coverage.py`
- Parametrized across all 10+ tickers; skip gracefully if state missing

**E2E Tests:** Not used as a separate category — smoke tests serve this role.

## Common Patterns

**Skip when output files absent:**
```python
def test_state_file_exists(self, ticker: str, output_dir: Path) -> None:
    state_path = output_dir / "state.json"
    if not state_path.exists():
        pytest.skip(f"No state.json for {ticker} -- run pipeline first")
    assert state_path.stat().st_size > 1000
```

**Error testing:**
```python
def test_empty_ticker_fails_validation(self) -> None:
    """Pipeline raises PipelineError for empty ticker."""
    state = AnalysisState(ticker="")
    pipeline = Pipeline()
    with pytest.raises(PipelineError, match="Validation failed"):
        pipeline.run(state)
```

**Pydantic roundtrip testing (standard for every new model):**
```python
def test_risk_type_classification(self) -> None:
    rtc = RiskTypeClassification(
        primary=RiskType.GROWTH_DARLING,
        secondary=RiskType.GUIDANCE_DEPENDENT,
        evidence=["High growth", "Frequent guidance"],
    )
    data = rtc.model_dump()
    restored = RiskTypeClassification.model_validate(data)
    assert restored.primary == RiskType.GROWTH_DARLING
```

**Loading real config files in tests:**
```python
def _load_scoring_config() -> dict:
    """Load the real scoring.json for testing."""
    import json
    from pathlib import Path

    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain"
    with (brain_dir / "scoring.json").open() as f:
        return json.load(f)
```

**Custom marker:**
```python
# pyproject.toml:
# markers = ["output_validation: validates generated .docx output against ground truth"]

@pytest.mark.output_validation
def test_docx_content_matches_ground_truth(...): ...
```

**Parametrize across tickers:**
```python
TICKERS = list(ALL_GROUND_TRUTH.keys())

@pytest.mark.parametrize("ticker", TICKERS)
def test_identity_legal_name(ticker: str) -> None:
    state = load_state(ticker)
    if state is None:
        pytest.skip(f"No state.json found for {ticker}")
    ...
```

---

*Testing analysis: 2026-02-25*
