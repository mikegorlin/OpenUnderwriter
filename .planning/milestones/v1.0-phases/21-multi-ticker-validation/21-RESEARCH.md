# Phase 21: Multi-Ticker Validation & Production Hardening - Research

**Researched:** 2026-02-11
**Domain:** Pipeline validation, batch processing, error resilience, ground truth expansion
**Confidence:** HIGH (codebase-verified, Anthropic docs confirmed)

## Summary

Phase 21 validates the LLM extraction pipeline across 20+ diverse companies and hardens it for production. The core challenge is not building new features but running the existing 7-stage pipeline (RESOLVE > ACQUIRE > EXTRACT > ANALYZE > SCORE > BENCHMARK > RENDER) at scale, finding every failure, fixing it, and proving 90% accuracy against ground truth.

The current system has 2,371 tests, 0 lint/type errors, and runs successfully on TSLA and AAPL with LLM extraction. The pipeline writes `state.json` after each stage, enabling resume-from-failure. The LLM extractor already returns `None` on any failure (never raises), enabling graceful regex fallback. Cost tracking exists via `CostTracker` with $2.00/company budget. The extraction cache (`ExtractionCache`) prevents re-extraction of the same filing.

The implementation areas are: (1) ticker selection and batch runner, (2) ground truth expansion to 8-10 companies, (3) retry/error hardening for API and SEC, (4) Batch API support as optional CLI flag, (5) cost reporting, (6) checkpoint/resume for multi-ticker runs.

**Primary recommendation:** Build a `validate` CLI command that runs the pipeline on 20+ tickers sequentially, checkpoints after each, produces a comprehensive pass/fail report, and fixes every failure encountered. The Batch API is a secondary optimization (CLI flag, not default path).

## Standard Stack

### Core (Already in project -- no new dependencies needed)

| Library | Version | Purpose | Status |
|---------|---------|---------|--------|
| anthropic | >=0.79.0 | Anthropic API client, Batch API | Already installed |
| instructor | >=1.14.0 | Structured LLM output via tool_use | Already installed |
| pydantic | >=2.10 | Extraction schemas, state model | Already installed |
| httpx | >=0.28 | SEC EDGAR HTTP client | Already installed |
| typer | >=0.15 | CLI framework | Already installed |
| rich | >=13.0 | CLI progress display | Already installed |
| sqlite3 | stdlib | Extraction cache, analysis cache | Already used |

### Supporting (Already in project)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | >=1.1.0 | Market data acquisition | ACQUIRE stage |
| edgartools | >=5.14.1 | SEC EDGAR MCP tool | ACQUIRE stage |

### No New Dependencies

Phase 21 requires zero new library installations. Everything needed is already in `pyproject.toml`. The Anthropic Python SDK (`anthropic >= 0.79.0`) already includes the Message Batches API (`client.messages.batches.create()`). The SDK also has built-in retry with exponential backoff for 429/5xx errors (default `max_retries=2`, configurable).

## Architecture Patterns

### Existing Pipeline Architecture (No Changes Needed to Core)

```
src/do_uw/
  cli.py               -- Add `validate` command here
  pipeline.py           -- Pipeline.run() already saves state after each stage
  stages/
    resolve/            -- SEC identity resolution
    acquire/            -- Data acquisition (SEC, stock, litigation)
      rate_limiter.py   -- Currently 10 req/sec; needs configurable rate
    extract/
      __init__.py       -- ExtractStage orchestrator + LLM pre-step
      llm/
        extractor.py    -- LLMExtractor with budget, cache, retry
        cost_tracker.py -- Per-company cost tracking
        cache.py        -- SQLite extraction cache
    analyze/            -- Check execution
    score/              -- 10-factor scoring
    benchmark/          -- Peer comparison
    render/             -- Word/PDF/Markdown output

tests/
  ground_truth/
    __init__.py         -- ALL_GROUND_TRUTH registry
    helpers.py          -- Shared validation utilities
    tsla.py             -- Existing: 13 categories
    aapl.py             -- Existing: 13 categories
    jpm.py              -- Existing: 6 categories (financial institution)
    # Phase 21 adds 5-7 more company files here
  test_ground_truth_validation.py  -- Identity, financials, distress tests
  test_ground_truth_coverage.py    -- Phase 20 coverage tests
```

### Pattern 1: Validation Runner (New)

**What:** A CLI command that runs the full pipeline on multiple tickers sequentially with checkpointing, error capture, and a summary report.
**When to use:** `angry-dolphin validate` for bulk validation runs.

Key design decisions:
- Each ticker gets its own `output/<TICKER>/` directory with `state.json` (existing pattern)
- Checkpoint file tracks which tickers are complete (JSON in `.cache/validation_checkpoint.json`)
- On restart, skip completed tickers (like pipeline stage resume, but at ticker level)
- Continue on failure: catch `PipelineError`, record it, move to next ticker
- Report at end: table showing pass/fail per ticker with reasons

```python
# Validation runner pseudocode
class ValidationRunner:
    def __init__(self, tickers: list[str], output_dir: Path):
        self.tickers = tickers
        self.checkpoint = self._load_checkpoint()

    def run(self) -> ValidationReport:
        for ticker in self.tickers:
            if ticker in self.checkpoint.completed:
                continue
            try:
                # Clear cache for fresh run
                self._clear_ticker_cache(ticker)
                # Run full pipeline
                pipeline = Pipeline(output_dir=output_dir / ticker)
                state = pipeline.run(AnalysisState(ticker=ticker))
                # Record success
                self.checkpoint.mark_completed(ticker, state)
            except PipelineError as exc:
                self.checkpoint.mark_failed(ticker, str(exc))
            self._save_checkpoint()
        return self._build_report()
```

### Pattern 2: Ground Truth Expansion

**What:** Add ground truth data files for 5-7 new companies (total 8-10), following the existing pattern in `tests/ground_truth/`.
**Structure:** Each company is a Python file with a `GROUND_TRUTH` dict containing 13 categories.

The existing ground truth categories (per TSLA/AAPL):
1. `identity` -- legal_name, cik, sic_code, sector, exchange
2. `financials` -- revenue_latest, net_income_latest, total_assets, total_debt, cash_and_equivalents
3. `market` -- market_cap_tier
4. `governance` -- board_size, ceo_name, cfo_name
5. `litigation` -- has_active_sca, sca_count_approximate
6. `distress` -- altman_z_zone
7. `item1_business` -- has_business_description, employee_count, is_dual_class, has_customer_concentration
8. `item7_mda` -- has_critical_accounting_estimates, has_guidance_language
9. `item8_footnotes` -- has_going_concern, has_restatements
10. `item9a_controls` -- has_material_weakness, auditor_name, auditor_opinion
11. `eight_k_events` -- has_event_timeline, event_count_min
12. `ownership` -- insider_ownership_pct_min, top_institutional_holder_contains
13. `risk_factors` -- total_risk_factors_min, has_ai_risk_factor, has_cyber_risk_factor

JPM is a special case (financial institution) with only 6 categories.

### Pattern 3: Batch API Integration (Optional Flag)

**What:** Support `--batch` flag on the CLI that collects all filing extraction requests and submits them as a single Anthropic Message Batch for 50% cost reduction.
**When to use:** Only for bulk validation runs where immediate response is not needed.

The Anthropic Batch API:
- 50% discount on all token usage (Haiku 4.5: $0.50/MTok input, $2.50/MTok output in batch vs $1.00/$5.00 standard)
- Limit: 100,000 requests or 256MB per batch
- Processing: most batches finish < 1 hour, max 24 hours
- Results available for 29 days
- Python SDK: `client.messages.batches.create(requests=[...])`
- Each request needs unique `custom_id` (use `form_type:accession`)
- Results streamed via `client.messages.batches.results(batch_id)`
- Result types: succeeded, errored, canceled, expired

**Critical caveat:** instructor library does NOT natively support batch API for structured extraction. The Batch API returns raw message responses, not instructor-validated Pydantic models. The batch path would need to:
1. Build batch requests manually (bypass instructor)
2. Submit via `anthropic.Anthropic().messages.batches.create()`
3. Poll for completion
4. Parse responses and validate against Pydantic schemas manually
5. Cache results in the same ExtractionCache format

This is significantly more complex than the standard path. Recommendation: implement as separate utility, not integrated into the main LLMExtractor.

### Pattern 4: Configurable Rate Limiting

**What:** Make SEC EDGAR rate limit configurable for bulk runs.
**Current state:** `rate_limiter.py` uses module-level `_SEC_MAX_RPS = 10` with `_SEC_INTERVAL = 0.1s`.
**Change needed:** Allow rate to be reduced to 5 req/sec for validation runs (conservative for 20+ companies back-to-back). This could be a module-level setter or environment variable.

### Pattern 5: Retry with Exponential Backoff for Anthropic API

**What:** The Anthropic SDK already provides built-in retry (default 2x with short exponential backoff for 429/5xx). For Phase 21, increase to 3x and add fallback to regex.
**Current state:** LLMExtractor catches all exceptions and returns `None` (line 199-205 in extractor.py). The SDK's built-in retry handles transient failures. No additional retry code is needed at the application level -- the SDK already does this.
**Enhancement:** Configure the Anthropic client with `max_retries=3` when constructing the instructor client, and ensure the error log includes the specific exception type for debugging bulk runs.

### Anti-Patterns to Avoid

- **Running tickers in parallel:** The pipeline is synchronous with shared SEC rate limiter. Running in parallel would complicate rate limiting, caching, and error tracking. Run sequentially.
- **Modifying LLMExtractor for batch support:** The batch API returns raw messages, not instructor-validated Pydantic models. Don't try to shoehorn batch into the existing extractor. Build it as a separate utility.
- **Hardcoding ticker lists:** Put the validation ticker set in a config file or Python constant, not scattered through CLI code.
- **Skipping cache clear:** The CONTEXT.md says "all runs are fresh." Must clear both `AnalysisCache` entries and `ExtractionCache` entries for each ticker before running. But keep the extraction cache across runs for cost efficiency on re-runs after fixes.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API retry/backoff | Custom retry loops | Anthropic SDK built-in retry (`max_retries=3`) | SDK handles 429, 5xx, connection errors with proper backoff |
| Batch API polling | Custom polling loop | `time.sleep(60)` poll loop from Anthropic docs | Simple pattern, batch typically finishes < 1 hour |
| Ground truth comparison | Custom assertion framework | Existing `helpers.py` (assert_financial_close, record, print_accuracy_report) | Pattern is proven, handles tolerances, prints reports |
| Progress display | Custom progress bars | Rich library (already used in CLI) | Consistent with existing pipeline display |
| State persistence | Custom serialization | Pipeline._save_state() (already exists) | JSON serialization per stage completion |
| Cost tracking | New cost system | CostTracker + ExtractionCache.get_stats() | Already tracks per-extraction and per-company costs |

**Key insight:** The hardest part of Phase 21 is not infrastructure -- it's running the pipeline 20+ times, reading every failure, and fixing every extraction/converter/scoring bug encountered. The infrastructure (pipeline, caching, cost tracking, ground truth framework) is already built and proven on TSLA/AAPL.

## Common Pitfalls

### Pitfall 1: SEC EDGAR Rate Limiting Under Bulk Load
**What goes wrong:** Running 20+ tickers back-to-back generates hundreds of SEC API calls. At 10 req/sec, a burst of 200 requests takes 20 seconds. If SEC starts throttling or returning 403, the whole pipeline stalls.
**Why it happens:** SEC EDGAR allows 10 req/sec but may be stricter during peak hours or for sustained loads. The current rate limiter is per-request, not aware of sustained throughput.
**How to avoid:** Reduce to 5 req/sec for bulk validation (CONTEXT.md decision). Add retry with longer backoff (5x retry, starting at 2s) for SEC 403/429 responses.
**Warning signs:** HTTPStatusError(403) from sec_get(), repeated "rate limited" in logs.

### Pitfall 2: LLM Budget Exhaustion Mid-Pipeline
**What goes wrong:** The $2.00/company budget could be reached before all filings are extracted if a company has particularly large or numerous filings.
**Why it happens:** Some companies have very large 10-K filings (200k+ chars after stripping) or many 8-K filings. Token estimation is rough (len/4).
**How to avoid:** Log remaining budget after each extraction. If budget is 80%+ consumed, log a warning. The existing fallback to regex (when budget exceeded) is correct behavior.
**Warning signs:** "Cost budget exceeded" log messages, many filings falling back to regex for a single company.

### Pitfall 3: Ground Truth Staleness
**What goes wrong:** Ground truth values are based on specific fiscal year filings. If the system acquires a newer filing (e.g., FY2026 instead of FY2025), the values won't match.
**Why it happens:** XBRL data updates when new filings are posted. The system always gets the latest.
**How to avoid:** Use relative tolerances (existing 10% pattern), use directional assertions (has_going_concern = False, has_active_sca = True) rather than exact values where possible. Document the expected filing period in ground truth comments.
**Warning signs:** Financial values off by >10% for well-known companies, period labels don't match expectations.

### Pitfall 4: FPI and Edge Case Companies Breaking Extraction
**What goes wrong:** Companies filing 20-F instead of 10-K, holding companies with unusual structures, pre-revenue biotech with no revenue, REITs with non-standard financials -- all may fail extractors that assume standard 10-K/corporate structure.
**Why it happens:** Many extractors have implicit assumptions (e.g., revenue > 0, balance sheet has standard items). FPI detection exists (`is_fpi` flag, 20-F -> TenKExtraction mapping) but may not cover all edge cases.
**How to avoid:** Include edge case companies in the validation set (CONTEXT.md specifies this). When an extractor fails for an edge case, fix it or add a graceful None return rather than letting it crash.
**Warning signs:** PipelineError during EXTRACT stage for specific tickers, missing entire sections in state.json.

### Pitfall 5: Instructor/Anthropic Compatibility for Batch API
**What goes wrong:** Trying to use `instructor.from_provider()` with the Batch API. Instructor wraps the Anthropic client for structured output via tool_use mode. The Batch API returns raw message responses that instructor can't intercept.
**Why it happens:** Batch API is asynchronous -- you submit requests and poll for results later. Instructor expects synchronous request-response for schema validation.
**How to avoid:** Implement Batch API as a separate code path that manually constructs requests with tool_use parameters (matching what instructor generates), submits them via `anthropic.Anthropic().messages.batches.create()`, then validates responses against Pydantic schemas in post-processing.
**Warning signs:** Batch results not matching expected Pydantic schema, missing fields, validation errors.

### Pitfall 6: Checkpoint File Corruption
**What goes wrong:** If the process crashes between completing a ticker pipeline and saving the checkpoint, the same ticker gets re-run (wasting time and API calls).
**Why it happens:** Non-atomic write of checkpoint data.
**How to avoid:** Write checkpoint after EACH stage completes (leverage existing per-stage state.json saves). Use `state.json` existence + completed stages as the checkpoint signal, not a separate file. This leverages the existing resume-from-failure pattern.
**Warning signs:** Same ticker being re-extracted on restart, duplicate API costs.

## Code Examples

### Example 1: Validation CLI Command

```python
# In cli.py (or new cli_validate.py)
@app.command("validate")
def validate(
    output: Path = typer.Option(Path("output"), "--output", "-o"),
    tickers_file: Path = typer.Option(None, "--tickers-file"),
    conservative_rate: bool = typer.Option(True, "--conservative-rate"),
    fresh: bool = typer.Option(True, "--fresh", help="Clear cache before each ticker"),
) -> None:
    """Run validation across multiple tickers."""
    tickers = _load_ticker_list(tickers_file)
    if conservative_rate:
        _set_sec_rate_limit(5)  # 5 req/sec instead of 10

    results: dict[str, str] = {}
    for i, ticker in enumerate(tickers, 1):
        console.print(f"\n[bold]({i}/{len(tickers)}) {ticker}[/bold]")
        ticker_dir = output / ticker

        if fresh:
            _clear_ticker_output(ticker_dir)

        try:
            state = AnalysisState(ticker=ticker)
            pipeline = Pipeline(output_dir=ticker_dir)
            pipeline.run(state)
            results[ticker] = "PASS"
        except PipelineError as exc:
            results[ticker] = f"FAIL: {exc}"

    _print_validation_report(results)
```

### Example 2: Ground Truth File for New Company

```python
# tests/ground_truth/nvda.py (example)
"""Ground truth data for NVDA -- hand-verified from SEC filings."""
from __future__ import annotations
from typing import Any

GROUND_TRUTH: dict[str, dict[str, Any]] = {
    "identity": {
        "legal_name": "NVIDIA Corporation",
        "cik": "1045810",
        "sic_code": "3674",
        "sector": "TECH",
        "exchange": "Nasdaq",
    },
    "financials": {
        "revenue_latest": 130497000000.0,  # FY2025 (ending Jan 2025)
        "net_income_latest": 72880000000.0,
        "total_assets": 112198000000.0,
        "total_debt": 8462000000.0,
        "cash_and_equivalents": 8589000000.0,
        "period_label": "FY2025",
    },
    # ... 13 categories following the established pattern
}
```

### Example 3: Batch API Integration (Separate Utility)

```python
# Batch extraction utility (NOT integrated into LLMExtractor)
import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

def create_extraction_batch(
    filings: list[dict[str, str]],  # [{form_type, accession, text, prompt}]
    model: str = "claude-haiku-4-5",
) -> str:
    """Submit filings as a batch for 50% cost reduction."""
    client = anthropic.Anthropic()

    requests = []
    for filing in filings:
        custom_id = f"{filing['form_type']}:{filing['accession']}"
        requests.append(Request(
            custom_id=custom_id,
            params=MessageCreateParamsNonStreaming(
                model=model,
                max_tokens=16384,
                messages=[
                    {"role": "system", "content": filing["prompt"]},
                    {"role": "user", "content": filing["text"]},
                ],
                # Include tool_use for structured output (mimics instructor)
                tools=[...],  # Pydantic schema as tool definition
            ),
        ))

    batch = client.messages.batches.create(requests=requests)
    return batch.id  # Poll for results later
```

### Example 4: Cost Report Generation

```python
# From ExtractionCache.get_stats() -- already implemented
def generate_cost_report(output_dir: Path) -> dict[str, Any]:
    """Generate per-company and per-filing-type cost breakdown."""
    cache = ExtractionCache()
    stats = cache.get_stats()
    # stats already contains:
    # - total_entries, total_cost_usd
    # - total_input_tokens, total_output_tokens
    # - by_form_type: {form_type: {count, cost_usd}}

    # Enrich with per-company breakdown by scanning output dirs
    for ticker_dir in output_dir.iterdir():
        state_path = ticker_dir / "state.json"
        if state_path.exists():
            # Load state, get accession numbers, compute per-company cost
            ...
    return stats
```

### Example 5: Configurable Rate Limiter

```python
# Enhancement to rate_limiter.py
def set_max_rps(rps: int) -> None:
    """Set maximum requests per second for SEC EDGAR.

    Args:
        rps: Requests per second (1-10). Default 10.
    """
    global _SEC_MAX_RPS, _SEC_INTERVAL
    _SEC_MAX_RPS = max(1, min(10, rps))
    _SEC_INTERVAL = 1.0 / _SEC_MAX_RPS
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Regex extraction | LLM extraction (instructor + Haiku 4.5) | Phase 18-20 | Coverage went from ~55% to >90% |
| Single-ticker validation | Phase 15 archetype scoring tests | Phase 15 | 8 archetypes tested, but not full pipeline runs |
| No cost tracking | CostTracker + ExtractionCache stats | Phase 18 | Per-filing and per-company cost visibility |
| Fixed SEC rate (10/sec) | Configurable rate needed for bulk | Phase 21 | Prevents throttling on 20+ ticker runs |

**Deprecated/outdated:**
- instructor Batch CLI: Exists but uses file-based .jsonl workflow, not integrated with our LLMExtractor cache/cost tracking. Build custom batch integration instead.

## Ticker Selection (Claude's Discretion Area)

Based on the 10 industry playbook verticals and the CONTEXT.md requirements:

### Recommended Validation Ticker Set (24 tickers)

**Tech/SaaS (2+):** NVDA, CRM (SIC 3674, 7372 -- TECH_SAAS playbook)
**Biotech/Pharma (2+):** MRNA, AMGN (SIC 2836, 2836 -- BIOTECH_PHARMA playbook)
**Energy/Utilities (2+):** XOM, NEE (SIC 1311, 4911 -- ENERGY_UTILITIES playbook)
**Healthcare (2+):** UNH, HCA (SIC 6324, 8062 -- HEALTHCARE playbook; UNH may be FINS depending on SIC)
**CPG/Consumer (2+):** PG, KO (SIC 2840, 2086 -- CPG_CONSUMER playbook)
**Media/Entertainment (2+):** DIS, NFLX (SIC 4841, 7812 -- MEDIA_ENTERTAINMENT playbook)
**Industrials/Mfg (2+):** CAT, HON (SIC 3531, 3825 -- may need SIC verification)
**REITs (2+):** PLD, AMT (SIC 6512, 6512 -- REITS_REAL_ESTATE playbook)
**Transportation (2+):** UNP, FDX (SIC 4011, 4513 -- TRANSPORTATION_RAIL playbook)

**Known-outcome companies (3-5):**
- SMCI -- Accounting issues, delayed 10-K filing, auditor resignation (2024)
- RIDE (Lordstown Motors) -- SEC fraud charges, went bankrupt
- COIN -- SEC enforcement action, securities lawsuit
- LCID -- Securities class action over production numbers
- PLUG -- Restatement, material weakness

**Edge cases:**
- TSM -- Foreign private issuer (20-F), tests FPI handling
- BNTX -- Pre-revenue biotech (at time of COVID vaccine development), foreign issuer
- SPG -- REIT with non-standard financials

**Excluded:** Financial institutions (JPM, GS, BAC, etc.) per CONTEXT.md

Note: Exact tickers should be verified for SIC code -> playbook mapping accuracy before finalizing. Some companies may have changed SIC codes or may not map cleanly to a single playbook.

## Ground Truth Field Selection (Claude's Discretion Area)

For new companies, use the full 13-category structure from TSLA/AAPL. Critical fields to verify for every company:

**Must-have (accurate extraction is essential):**
- Identity: legal_name, cik, sic_code, sector, exchange
- Financials: revenue, net_income, total_assets (with 10% tolerance)
- Market: market_cap_tier
- Distress: altman_z_zone
- Controls: has_material_weakness, auditor_name

**Important (LLM extraction quality markers):**
- Governance: board_size, ceo_name
- Litigation: has_active_sca
- Item 1: has_business_description, employee_count
- Item 8: has_going_concern, has_restatements

**Nice-to-have (tests new Phase 20 extraction):**
- Risk factors: count, AI/cyber detection
- Ownership: insider_pct, top holder
- 8-K events: event count

For known-outcome companies (SMCI, RIDE, COIN, LCID, PLUG), the critical ground truth is:
- **Has material weakness (if applicable)**
- **Has active SCA (must be True)**
- **Has restatements (if applicable)**
- **Altman Z-Score zone (should show distress for bankrupt companies)**
- **Overall risk tier should be WALK or NO_TOUCH**

## Checkpoint Storage (Claude's Discretion Area)

**Recommendation:** Use `output/<TICKER>/state.json` existence as the checkpoint signal (no separate checkpoint file needed). The pipeline already saves state after each stage. To determine if a ticker is "complete," check if the RENDER stage has status COMPLETED in the state file.

For the validation report, write `output/validation_report.json` with:
```json
{
  "run_date": "2026-02-12T...",
  "tickers": ["NVDA", "CRM", ...],
  "results": {
    "NVDA": {"status": "PASS", "duration_seconds": 420, "cost_usd": 0.85},
    "CRM": {"status": "FAIL", "stage": "extract", "error": "..."},
    ...
  },
  "summary": {
    "total": 24, "passed": 22, "failed": 2,
    "total_cost_usd": 18.50,
    "avg_duration_seconds": 480
  }
}
```

## Cost Report Format (Claude's Discretion Area)

**Recommendation:** Both CLI output AND file.

CLI output (Rich table):
```
 # | Ticker | Status | Duration | Cost    | 10-K   | DEF14A | 8-K    | Other
---|--------|--------|----------|---------|--------|--------|--------|-------
 1 | NVDA   | PASS   | 7m 12s   | $0.85   | $0.42  | $0.18  | $0.12  | $0.13
 2 | CRM    | PASS   | 5m 30s   | $0.62   | $0.31  | $0.15  | $0.08  | $0.08
...
   | TOTAL  |        | 2h 15m   | $18.50  | $9.20  | $4.10  | $2.80  | $2.40
```

File: `output/cost_report.json` with detailed per-company, per-filing breakdowns.

## Retry Backoff Strategy (Claude's Discretion Area)

**Anthropic API:**
- Use SDK built-in retry: `Anthropic(max_retries=3)` (default is 2)
- SDK handles 429 with retry-after header, 5xx with exponential backoff
- On final failure, LLMExtractor already returns None -> regex fallback
- No additional application-level retry needed

**SEC EDGAR:**
- Current: 10 req/sec, no retry on HTTP errors
- Change to: 5 req/sec for bulk validation
- Add retry: 5 attempts with backoff schedule [2s, 4s, 8s, 16s, 32s]
- On 403 (rate limited): wait 10s then retry
- On 5xx (server error): standard exponential backoff
- On final failure: raise (pipeline will catch and mark stage failed)

**Implementation:**
```python
import time

def sec_get_with_retry(url: str, max_retries: int = 5) -> dict[str, Any]:
    """Rate-limited GET with retry for SEC EDGAR."""
    for attempt in range(max_retries):
        _rate_limit()
        try:
            client = _get_client()
            response = client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 403:
                wait = 10.0  # SEC rate limit cooldown
            elif exc.response.status_code >= 500:
                wait = 2.0 * (2 ** attempt)  # Exponential backoff
            else:
                raise  # 4xx other than 403 -- don't retry
            if attempt < max_retries - 1:
                logger.warning("SEC GET %s failed (%d), retrying in %.0fs",
                             url, exc.response.status_code, wait)
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Unreachable")  # Satisfy type checker
```

## Open Questions

1. **Instructor + Batch API integration complexity**
   - What we know: Instructor does NOT natively wrap batch API for structured extraction. The batch path requires manual tool_use construction, batch submission, polling, and post-hoc Pydantic validation.
   - What's unclear: Whether this complexity is worth the 50% cost savings for 20-24 tickers ($20-40 total).
   - Recommendation: Implement as a separate utility (not integrated into LLMExtractor). Test with a small batch first to validate the tool_use schema matches instructor's generated schema.

2. **Known-outcome company data availability**
   - What we know: SMCI had delayed 10-K filing and auditor issues in 2024. RIDE is bankrupt. COIN had SEC action.
   - What's unclear: Whether SEC EDGAR still has all filings for bankrupt/delisted companies (RIDE). Whether companies with delayed filings have all expected filing types.
   - Recommendation: Verify filing availability for each known-outcome ticker before committing to the validation set. Substitute if filings are missing.

3. **UNH SIC code classification**
   - What we know: UnitedHealth Group has SIC 6324 (Hospital & Medical Service Plans) which falls in the 6000-6399 FINANCIAL_SERVICES range.
   - What's unclear: Whether a health insurer should be tested as "Healthcare" or "Financial Services."
   - Recommendation: Include both UNH (as FINS/HEALTHCARE edge case) and a pure healthcare provider like HCA (SIC 8062).

4. **90% accuracy threshold interpretation**
   - What we know: CONTEXT.md specifies 90% overall accuracy, adjusted down from roadmap's 95%.
   - What's unclear: Is this 90% of fields across ALL companies, or 90% per company? Is a "skip" counted in the denominator?
   - Recommendation: 90% of non-skipped fields across all companies combined. Skipped fields (data not available) excluded from denominator.

## Sources

### Primary (HIGH confidence)
- Codebase: `src/do_uw/pipeline.py` -- Pipeline architecture, state persistence
- Codebase: `src/do_uw/stages/extract/llm/extractor.py` -- LLMExtractor with budget, cache, retry
- Codebase: `src/do_uw/stages/extract/llm/cost_tracker.py` -- CostTracker at $2.00/company
- Codebase: `src/do_uw/stages/extract/llm/cache.py` -- ExtractionCache with per-form-type stats
- Codebase: `src/do_uw/stages/acquire/rate_limiter.py` -- SEC rate limiter (10 req/sec)
- Codebase: `tests/ground_truth/` -- Existing ground truth framework (TSLA, AAPL, JPM)
- Codebase: `src/do_uw/cli.py` -- CLI structure, pipeline config
- Codebase: `src/do_uw/knowledge/playbooks.py` -- 10 industry playbook verticals
- [Anthropic Batch Processing Docs](https://platform.claude.com/docs/en/docs/build-with-claude/batch-processing) -- Batch API pricing (50%), limits, Python SDK examples
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) -- Built-in retry, max_retries config, batch API support

### Secondary (MEDIUM confidence)
- [Instructor Library](https://python.useinstructor.com/) -- from_provider() pattern, tool_use mode
- [Instructor Batch CLI](https://python.useinstructor.com/cli/batch/) -- Batch CLI exists but limited programmatic API for Anthropic
- [Anthropic Rate Limit Guide](https://markaicode.com/anthropic-api-rate-limits-429-errors/) -- SDK retry behavior details

### Tertiary (LOW confidence)
- Ticker financial data (NVDA, SMCI, etc.) -- Exact values need hand-verification from actual filings before being committed as ground truth

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- All libraries already installed and proven in Phases 18-20
- Architecture: HIGH -- All patterns are extensions of existing codebase patterns
- Pitfalls: HIGH -- Based on actual codebase examination and Anthropic API documentation
- Ticker selection: MEDIUM -- SIC-to-playbook mappings verified programmatically, but individual company edge cases need runtime verification
- Batch API: MEDIUM -- Anthropic docs are clear, but instructor compatibility needs testing
- Ground truth values: LOW -- Financial values for new companies need hand-verification from SEC filings

**Research date:** 2026-02-11
**Valid until:** 2026-03-11 (30 days -- stable domain, no fast-moving dependencies)
