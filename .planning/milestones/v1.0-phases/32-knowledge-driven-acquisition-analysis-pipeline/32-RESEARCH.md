# Phase 32: Knowledge-Driven Acquisition & Analysis Pipeline - Research

**Researched:** 2026-02-15
**Domain:** Pipeline architecture inversion, knowledge-driven data acquisition, backtesting infrastructure
**Confidence:** HIGH

## Summary

Phase 32 inverts the pipeline's data flow so that knowledge declarations (check definitions) drive acquisition and extraction, instead of the current approach where ACQUIRE fetches a fixed set of data sources and ANALYZE tries to match checks to whatever was extracted. The enriched check metadata from Phase 31 (content_type, depth, data_strategy.field_key, required_data, data_locations) provides the foundation: each of the 388 checks already declares what data sources it needs, what filing sections contain the data, and what field to evaluate.

The current pipeline has three key architectural gaps that Phase 32 addresses. First, ACQUIRE fetches a hardcoded set of filing types (`DOMESTIC_FILING_TYPES`, `FPI_FILING_TYPES`) and data clients (SEC, market, litigation, news) regardless of what the check corpus actually needs. Adding a new check that requires a new data source (e.g., PCAOB inspection reports) means editing Python client code -- the check definition alone is insufficient. Second, EXTRACT runs a fixed sequence of 13+ extractor modules in a hardcoded order, with no awareness of which checks will consume the extracted data. Third, there is no automated way to detect gaps: "this check needs X, but the pipeline doesn't acquire/extract/evaluate X." Phase 32 closes all three gaps.

The backtesting infrastructure (success criteria 5-6) builds on existing foundations: the CheckRun table (Phase 30) already records per-check results from every pipeline run, and historical state files exist for AAPL and TSLA. The new work extends this to support running checks against cached state files and measuring check effectiveness over time.

**Primary recommendation:** Build a `RequirementsAnalyzer` that reads all check data_strategy declarations and produces an acquisition manifest. Wire the manifest into AcquisitionOrchestrator as a requirements-aware layer (without ripping out the existing client architecture). Build a `PipelineGapDetector` that compares check requirements to actual pipeline capabilities and reports every missing link. Add content-type-aware evaluation dispatch in the check engine. Build backtesting as a CLI command that loads historical state files and replays checks.

## Standard Stack

### Core (Already in Use -- No New Dependencies)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | RequirementsManifest, GapReport, BacktestResult models | Project standard per CLAUDE.md |
| SQLAlchemy 2.0 | 2.x | CheckRun queries for effectiveness metrics, backtest results | Already backing knowledge store |
| Typer | 0.x | CLI commands for gap report and backtest execution | Already the CLI framework |
| Rich | 13.x | Gap report and effectiveness metric display | Already used for CLI output |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x | Backtesting fixtures, gap detection tests | All testing |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| RequirementsAnalyzer reading checks.json directly | SQLAlchemy query on knowledge store | Direct JSON is simpler; store query is more reusable. Recommend store query since enriched fields are now persisted (Phase 31-04) |
| CLI-based backtesting | Scheduled backtesting runs | CLI is simpler, sufficient for current use case. Scheduled runs are premature |
| Gap detection as runtime warnings | Gap detection as static analysis tool | Static analysis (CLI command) is more useful -- runs at development time, not analysis time |

**Installation:** No new packages needed.

## Architecture Patterns

### Current Architecture (What Exists)

```
ACQUIRE (fixed clients)          EXTRACT (fixed extractors)       ANALYZE (check engine)
======================           ========================         =====================
SEC client  -> filings           company_profile                  load checks.json
Market client -> market_data     financial_statements             for check in checks:
Litigation client -> lit_data    distress_indicators                data = map_check_data()
News client -> web_search        debt_analysis                      result = evaluate_check()
                                 audit_risk
4 HARD gates, 2 SOFT gates       market extractors
                                 governance extractors
                                 litigation extractors
```

**Problems:**
1. ACQUIRE's client list is hardcoded -- no awareness of what checks need
2. EXTRACT's extractor sequence is hardcoded -- no awareness of check consumers
3. Adding a new check requiring new data requires editing 3+ Python files
4. No automated detection of "this check needs data we don't acquire"
5. No differentiated evaluation by content type (MANAGEMENT_DISPLAY evaluated same as EVALUATIVE_CHECK)

### Recommended Architecture

```
Phase 32 additions (layered on top, not replacing):

                   RequirementsAnalyzer
                   =====================
                   reads: checks.json (all 388, enriched)
                   produces: AcquisitionManifest
                     - required_sources: {SEC_10K, MARKET_PRICE, ...}
                     - required_sections: {SEC_10K: [item_9a_controls, ...]}
                     - source_to_checks: {SEC_10K: [check_ids...]}
                     |
                     v
ACQUIRE (requirements-aware)     EXTRACT (unchanged)              ANALYZE (type-aware)
========================         ==================               ====================
Manifest validates:              (future: extraction hints)        ContentType dispatch:
- all required sources covered                                      MD -> verify_presence()
- section-split for needed items                                    EC -> evaluate_threshold()
                                                                    IP -> detect_pattern()
                     |
                     v
              PipelineGapDetector
              ===================
              compares: manifest vs actual capabilities
              reports: missing sources, missing extractors,
                       missing field mappings, missing evaluators
                     |
                     v
              BacktestRunner
              ==============
              loads: historical state.json files
              replays: check execution against old state
              compares: check results over time
              reports: effectiveness metrics
```

### Pattern 1: Requirements Manifest from Check Declarations

**What:** A `RequirementsAnalyzer` reads all check definitions and produces a structured manifest of what the pipeline needs to acquire, extract, and evaluate.
**When to use:** At pipeline startup (before ACQUIRE) and as a standalone CLI tool for gap detection.

```python
class AcquisitionManifest(BaseModel):
    """What the pipeline needs based on check declarations."""

    required_sources: set[str]
    # e.g., {"SEC_10K", "SEC_DEF14A", "MARKET_PRICE", "SCAC_SEARCH", ...}

    required_sections: dict[str, set[str]]
    # e.g., {"SEC_10K": {"item_9a_controls", "item_1a_risk_factors", ...}}

    source_to_checks: dict[str, list[str]]
    # e.g., {"SEC_10K": ["FIN.LIQ.position", "FIN.LEV.total_debt", ...]}

    depth_distribution: dict[int, int]
    # e.g., {1: 20, 2: 270, 3: 54, 4: 44}


def build_acquisition_manifest(
    checks: list[dict[str, Any]],
) -> AcquisitionManifest:
    """Build manifest from enriched check definitions."""
    required_sources: set[str] = set()
    required_sections: dict[str, set[str]] = {}
    source_to_checks: dict[str, list[str]] = {}

    for check in checks:
        check_id = check["id"]
        for src in check.get("required_data", []):
            required_sources.add(src)
            source_to_checks.setdefault(src, []).append(check_id)

            # Section-level requirements from data_locations
            locs = check.get("data_locations", {}).get(src, [])
            if isinstance(locs, list):
                required_sections.setdefault(src, set()).update(locs)

    return AcquisitionManifest(
        required_sources=required_sources,
        required_sections=required_sections,
        source_to_checks=source_to_checks,
        depth_distribution=_count_depths(checks),
    )
```

### Pattern 2: Pipeline Gap Detection

**What:** A `PipelineGapDetector` compares check requirements to actual pipeline capabilities and produces a gap report.
**When to use:** Standalone CLI command (`do-uw knowledge gaps`), and optionally at pipeline startup.

```python
class PipelineGap(BaseModel):
    """A single gap in the pipeline for a check."""
    check_id: str
    check_name: str
    gap_type: str  # "SOURCE_NOT_ACQUIRED", "SECTION_NOT_SPLIT", "NO_EXTRACTOR", "NO_MAPPER", "NO_EVALUATOR"
    detail: str
    severity: str  # "CRITICAL" (check cannot run), "WARNING" (degraded), "INFO" (enhancement opportunity)


class GapReport(BaseModel):
    """Complete gap analysis for the pipeline."""
    total_checks: int
    fully_supported: int
    gaps: list[PipelineGap]
    by_type: dict[str, int]  # gap_type -> count
    by_severity: dict[str, int]  # severity -> count


# Pipeline capabilities registry (static analysis of what exists)
ACQUIRE_SOURCES: set[str] = {
    "SEC_10K", "SEC_10Q", "SEC_DEF14A", "SEC_8K", "SEC_FORM4",
    "SEC_13DG", "MARKET_PRICE", "MARKET_SHORT",
    "SCAC_SEARCH", "SEC_ENFORCEMENT",
}

EXTRACT_FIELDS: set[str] = {
    # Populated by introspecting ExtractedData model fields
    # or maintained as a registry
}
```

### Pattern 3: Content-Type-Aware Evaluation Dispatch

**What:** The check engine dispatches to different evaluation paths based on content_type.
**When to use:** In `execute_checks()` in check_engine.py, replacing the single evaluate_check() path.

```python
def evaluate_by_content_type(
    check: dict[str, Any],
    data: dict[str, Any],
) -> CheckResult:
    """Dispatch evaluation based on content_type."""
    content_type = check.get("content_type", "EVALUATIVE_CHECK")

    if content_type == "MANAGEMENT_DISPLAY":
        return evaluate_management_display(check, data)
    elif content_type == "INFERENCE_PATTERN":
        return evaluate_inference_pattern(check, data)
    else:  # EVALUATIVE_CHECK (default)
        return evaluate_check(check, data)  # existing logic


def evaluate_management_display(
    check: dict[str, Any],
    data: dict[str, Any],
) -> CheckResult:
    """MANAGEMENT_DISPLAY: verify data presence and format.

    No threshold evaluation. Reports INFO if data present,
    SKIPPED if data unavailable. These checks exist to ensure
    required display data is captured.
    """
    data_value, data_key = first_data_value(data)
    if data_value is None:
        return make_skipped(check, data)
    return CheckResult(
        check_id=check.get("id", "UNKNOWN"),
        check_name=check.get("name", ""),
        status=CheckStatus.INFO,
        value=coerce_value(data_value),
        evidence=f"Management display: {data_value}",
        source=data_key,
        factors=extract_factors(check),
        section=check.get("section", 0),
    )


def evaluate_inference_pattern(
    check: dict[str, Any],
    data: dict[str, Any],
) -> CheckResult:
    """INFERENCE_PATTERN: multi-signal detection with pattern_ref.

    Looks up pattern definition from patterns.json via pattern_ref,
    checks trigger conditions against multiple data points.
    Falls back to existing evaluate_check() if no pattern_ref.
    """
    pattern_ref = check.get("pattern_ref")
    if pattern_ref is None:
        return evaluate_check(check, data)  # fallback
    # Pattern evaluation logic here
    ...
```

### Pattern 4: Backtesting Infrastructure

**What:** A `BacktestRunner` loads historical state files and replays check execution to measure effectiveness.
**When to use:** CLI command (`do-uw knowledge backtest`), periodic calibration.

```python
class BacktestResult(BaseModel):
    """Result of running checks against a historical state file."""
    ticker: str
    state_date: str
    checks_executed: int
    checks_triggered: int
    checks_clear: int
    checks_skipped: int
    results: list[dict[str, Any]]


class EffectivenessReport(BaseModel):
    """Aggregated effectiveness metrics across N runs."""
    total_runs: int
    always_fire: list[str]    # checks that fire in every run (too sensitive?)
    never_fire: list[str]     # checks that never fire (miscalibrated?)
    high_skip: list[str]      # checks skipped >50% (data gap?)
    consistent: list[str]     # checks with stable fire rate (reliable signals)
```

### Anti-Patterns to Avoid

- **Replacing the ACQUIRE client architecture:** Phase 32 should LAYER requirements awareness on top of existing clients, not rewrite them. The RequirementsAnalyzer validates that existing clients cover the manifest; it does not become a new orchestrator.
- **Making EXTRACT check-aware at runtime:** The extraction hint system (success criteria 2) should be lightweight guidance (e.g., "prioritize extracting field X from section Y"), not a full rewrite of extractors to be check-driven. Extractors produce comprehensive data; checks select what they need.
- **Coupling gap detection to pipeline execution:** Gap detection should be a static analysis tool that can run independently, not something that halts the pipeline when gaps exist. Gaps are informational, not blocking.
- **Over-engineering backtesting:** Start with simple replay (load state, run checks, compare). Do NOT build a full time-series database, statistical framework, or ML-based effectiveness prediction. That is Phase 33 territory.
- **Breaking existing evaluation logic:** Content-type dispatch should be additive. EVALUATIVE_CHECK evaluation MUST remain identical to current behavior. MANAGEMENT_DISPLAY and INFERENCE_PATTERN get new paths, but the default path is unchanged.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Manifest generation | Manual source registry | Read from checks.json `required_data` + `data_locations` | 388 checks already declare their needs -- parse, don't duplicate |
| Pipeline capability registry | Hardcoded source list | Introspect from actual ACQUIRE clients + EXTRACT modules | Stays in sync with code |
| State file loading for backtest | Custom JSON parser | `Pipeline.load_state()` (already exists) | Handles deserialization, validation |
| Check statistics over time | Custom analytics | Extend `get_check_stats()` in store_bulk.py | Already has fire_rate/skip_rate computation |
| Gap report formatting | Custom text builder | Rich tables (already used in CLI) | Consistent with existing CLI output |

**Key insight:** Most of the data needed for Phase 32 already exists in the system. The 388 checks already declare `required_data` (10 distinct source types) and `data_locations` (150 source:section pairs). The ACQUIRE stage already fetches from these sources. The gap is that nothing connects the two -- no validation that ACQUIRE covers what checks need, and no automated detection when they diverge.

## Common Pitfalls

### Pitfall 1: Acquisition Manifest Scope Creep
**What goes wrong:** The manifest tries to control every aspect of acquisition (ordering, parallelism, caching, rate limiting) instead of just validating coverage.
**Why it happens:** The phrase "acquisition driven by knowledge" sounds like the manifest should replace the orchestrator.
**How to avoid:** The manifest is a VALIDATION layer, not a replacement. It answers: "Do our existing clients cover everything checks need?" and reports gaps. The orchestrator continues to run clients in its existing order.
**Warning signs:** Code that modifies AcquisitionOrchestrator's client list at runtime based on manifest.

### Pitfall 2: Breaking 1,800 Lines of Mapper Code
**What goes wrong:** Content-type dispatch in the check engine changes how data flows through the mapper chain, breaking the 5 mapper files (1,808 lines total).
**Why it happens:** MANAGEMENT_DISPLAY and INFERENCE_PATTERN need different evaluation, and the temptation is to change data mapping too.
**How to avoid:** Content-type dispatch happens AFTER data mapping, not before. All checks go through the same `map_check_data()` path. Only the evaluation step differs by content type.
**Warning signs:** Tests in check_mappers fail; check results change for EVALUATIVE_CHECK content type.

### Pitfall 3: Backtesting Assumes Deterministic Results
**What goes wrong:** Backtesting compares exact check results between runs, but some checks produce different results on different dates (market data, web search results).
**Why it happens:** State files contain point-in-time data. Re-running checks against the same state IS deterministic. But comparing results across different state files of the same company is NOT -- the data changed.
**How to avoid:** Backtesting replays against a FROZEN state file (deterministic). Cross-run comparison tracks trends, not exact matches. The effectiveness report uses fire_rate ranges, not binary pass/fail.
**Warning signs:** Flaky backtest results; "check X sometimes fires" treated as a bug instead of expected behavior.

### Pitfall 4: Gap Report Overwhelm
**What goes wrong:** Gap report has 200+ entries because many data_locations sections are not directly mapped to ACQUIRE capabilities (e.g., "SEC_10K:revenue_recognition_note" -- ACQUIRE fetches the 10-K but doesn't separately validate this section exists).
**Why it happens:** data_locations in checks are more granular than ACQUIRE's capabilities. ACQUIRE fetches whole filings; checks need specific sections. The gap between "filing acquired" and "section available" is EXTRACT's job (filing_sections.py), not ACQUIRE's.
**How to avoid:** Three levels of gap analysis: (1) SOURCE level: is the data source acquired? (2) SECTION level: is the filing section-split? (3) FIELD level: is the extracted field available? Level 1 is ACQUIRE's responsibility. Level 2 is EXTRACT's. Level 3 is mapper routing. Report each level separately.
**Warning signs:** Gap report mixes source-level and field-level gaps in one flat list.

### Pitfall 5: Extraction Hints Over-Engineering
**What goes wrong:** Extraction hints system becomes a full extraction DSL that competes with existing extractors.
**Why it happens:** Success criteria 2 says "EXTRACT stage uses [hints] to guide parsing." This sounds like hints should change extraction behavior.
**How to avoid:** Extraction hints are METADATA, not execution logic. They tell the gap detector "this check expects field X from section Y via pattern Z." They do NOT make the extractor do anything differently. The actual use case is: when adding a new check, the hint tells you what extractor needs to handle it. This is Phase 32's scope. Making extractors read hints and adjust behavior is Phase 33/34 territory.
**Warning signs:** Code that reads extraction_hints inside an extractor function.

### Pitfall 6: Effectiveness Metrics Without Enough Data
**What goes wrong:** Check effectiveness reports are generated with N=2 runs (AAPL, TSLA), producing meaningless statistics.
**Why it happens:** The system has only been run on a handful of tickers. Statistical significance requires more data.
**How to avoid:** The effectiveness framework should be built for future use. Start with simple counts (fire/clear/skip per check across runs). Report confidence based on N. Flag metrics as LOW confidence when N < 5. The infrastructure matters more than the initial results.
**Warning signs:** Presenting fire_rate from 2 runs as a reliable signal.

## Code Examples

### Example 1: RequirementsAnalyzer

```python
# src/do_uw/knowledge/requirements.py

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class AcquisitionManifest(BaseModel):
    """Structured requirements derived from check declarations."""
    required_sources: set[str] = Field(default_factory=set)
    required_sections: dict[str, set[str]] = Field(default_factory=dict)
    source_to_checks: dict[str, list[str]] = Field(default_factory=dict)
    checks_by_depth: dict[int, int] = Field(default_factory=dict)
    checks_by_content_type: dict[str, int] = Field(default_factory=dict)
    total_checks: int = 0


def build_manifest(checks: list[dict[str, Any]]) -> AcquisitionManifest:
    """Build acquisition manifest from enriched check definitions."""
    manifest = AcquisitionManifest(total_checks=len(checks))

    for check in checks:
        if check.get("execution_mode") != "AUTO":
            continue

        check_id = check["id"]
        depth = check.get("depth", 2)
        ct = check.get("content_type", "EVALUATIVE_CHECK")

        manifest.checks_by_depth[depth] = manifest.checks_by_depth.get(depth, 0) + 1
        manifest.checks_by_content_type[ct] = manifest.checks_by_content_type.get(ct, 0) + 1

        for src in check.get("required_data", []):
            manifest.required_sources.add(src)
            manifest.source_to_checks.setdefault(src, []).append(check_id)

            locs = check.get("data_locations", {}).get(src, [])
            if isinstance(locs, list):
                manifest.required_sections.setdefault(src, set()).update(locs)

    return manifest
```

### Example 2: PipelineGapDetector

```python
# src/do_uw/knowledge/gap_detector.py

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

from do_uw.knowledge.requirements import AcquisitionManifest


class PipelineGap(BaseModel):
    """A single gap in the pipeline coverage."""
    check_id: str
    check_name: str
    gap_type: str  # SOURCE_NOT_ACQUIRED, NO_FIELD_KEY, NO_EXTRACTOR_MAPPED
    detail: str
    severity: str  # CRITICAL, WARNING, INFO


class GapReport(BaseModel):
    """Complete gap analysis."""
    total_checks: int = 0
    fully_supported: int = 0
    gaps: list[PipelineGap] = Field(default_factory=list)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_severity: dict[str, int] = Field(default_factory=dict)


# Known pipeline capabilities (what ACQUIRE actually fetches)
ACQUIRED_SOURCES: set[str] = {
    "SEC_10K", "SEC_10Q", "SEC_DEF14A", "SEC_8K", "SEC_FORM4",
    "SEC_13DG", "MARKET_PRICE", "MARKET_SHORT",
    "SCAC_SEARCH", "SEC_ENFORCEMENT",
}

# Checks with data_strategy.field_key (Phase 31)
# Loaded dynamically from checks.json

def detect_gaps(
    checks: list[dict[str, Any]],
    manifest: AcquisitionManifest,
) -> GapReport:
    """Compare check requirements to pipeline capabilities."""
    report = GapReport(total_checks=len(checks))

    for check in checks:
        if check.get("execution_mode") != "AUTO":
            continue

        check_id = check["id"]
        check_gaps: list[PipelineGap] = []

        # Level 1: Source availability
        for src in check.get("required_data", []):
            if src not in ACQUIRED_SOURCES:
                check_gaps.append(PipelineGap(
                    check_id=check_id,
                    check_name=check.get("name", ""),
                    gap_type="SOURCE_NOT_ACQUIRED",
                    detail=f"Required source '{src}' not in ACQUIRE capabilities",
                    severity="CRITICAL",
                ))

        # Level 2: Field mapping
        ds = check.get("data_strategy", {})
        has_field_key = ds.get("field_key") is not None if isinstance(ds, dict) else False
        if not has_field_key:
            # Check if legacy FIELD_FOR_CHECK covers it
            from do_uw.stages.analyze.check_field_routing import FIELD_FOR_CHECK
            if check_id not in FIELD_FOR_CHECK:
                check_gaps.append(PipelineGap(
                    check_id=check_id,
                    check_name=check.get("name", ""),
                    gap_type="NO_FIELD_KEY",
                    detail="No field_key in data_strategy and no FIELD_FOR_CHECK entry",
                    severity="WARNING",
                ))

        if not check_gaps:
            report.fully_supported += 1
        report.gaps.extend(check_gaps)

    # Aggregate
    for gap in report.gaps:
        report.by_type[gap.gap_type] = report.by_type.get(gap.gap_type, 0) + 1
        report.by_severity[gap.severity] = report.by_severity.get(gap.severity, 0) + 1

    return report
```

### Example 3: BacktestRunner

```python
# src/do_uw/knowledge/backtest.py

from __future__ import annotations
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field

from do_uw.pipeline import Pipeline
from do_uw.stages.analyze.check_engine import execute_checks
from do_uw.knowledge.compat_loader import BackwardCompatLoader


class BacktestResult(BaseModel):
    """Result of replaying checks against a historical state."""
    ticker: str
    state_path: str
    state_date: str = ""
    checks_executed: int = 0
    triggered: int = 0
    clear: int = 0
    skipped: int = 0
    info: int = 0
    results_by_id: dict[str, str] = Field(default_factory=dict)


def run_backtest(state_path: Path) -> BacktestResult:
    """Load a historical state file and replay all checks."""
    state = Pipeline.load_state(state_path)

    loader = BackwardCompatLoader(playbook_id=state.active_playbook_id)
    brain = loader.load_all()
    checks = brain.checks.get("checks", [])

    results = execute_checks(checks, state.extracted, state.company)

    bt = BacktestResult(
        ticker=state.ticker,
        state_path=str(state_path),
        checks_executed=len(results),
    )
    for r in results:
        bt.results_by_id[r.check_id] = r.status.value
        if r.status.value == "TRIGGERED":
            bt.triggered += 1
        elif r.status.value == "CLEAR":
            bt.clear += 1
        elif r.status.value == "SKIPPED":
            bt.skipped += 1
        elif r.status.value == "INFO":
            bt.info += 1

    return bt
```

### Example 4: Check Effectiveness CLI

```python
# Extension to cli_knowledge.py

@knowledge_app.command()
def effectiveness(
    min_runs: int = typer.Option(3, help="Minimum runs to include"),
) -> None:
    """Show check effectiveness metrics across pipeline runs."""
    store = KnowledgeStore()
    stats = store.get_check_stats(min_runs=min_runs)

    always_fire = [s for s in stats if s["fire_rate"] == 1.0]
    never_fire = [s for s in stats if s["fire_rate"] == 0.0]
    high_skip = [s for s in stats if s["skip_rate"] > 0.5]

    console.print(f"\n[bold]Check Effectiveness Report[/bold]")
    console.print(f"Checks analyzed: {len(stats)} (min {min_runs} runs)")
    console.print(f"Always fire (too sensitive?): {len(always_fire)}")
    console.print(f"Never fire (miscalibrated?): {len(never_fire)}")
    console.print(f"High skip rate (data gaps?): {len(high_skip)}")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed client list in ACQUIRE | Still fixed client list | Phase 2 | Adding data sources requires Python code changes |
| Fixed extractor sequence | Still fixed sequence | Phase 3-5 | Adding extractors requires Python code changes |
| No content-type awareness in eval | Content types exist on checks (Phase 31), not used in eval yet | Phase 31 | All checks evaluated identically |
| No gap detection | Coverage gaps rendered in worksheet (Phase 31) | Phase 31 | Gaps visible in output but not at dev time |
| Check results discarded after run | CheckRun table persists results (Phase 30) | Phase 30 | Fire/skip rates queryable |
| No backtesting | Historical state files exist (AAPL, TSLA) | Phase 17+ | Data available but no replay framework |

## Current State Inventory (Quantified)

These numbers are critical for planning task scope:

| Metric | Count | Source |
|--------|-------|--------|
| Total checks | 388 | brain/checks.json |
| AUTO checks | 381 | execution_mode == "AUTO" |
| Checks with data_strategy.field_key | 247 | Phase 31 enrichment |
| Checks WITHOUT data_strategy (need prefix mappers) | 141 | EXEC:20, FIN:23, FWRD:83, NLP:15 |
| Unique required_data source types | 10 | SEC_10K, SEC_10Q, SEC_DEF14A, SEC_8K, SEC_FORM4, SEC_13DG, MARKET_PRICE, MARKET_SHORT, SCAC_SEARCH, SEC_ENFORCEMENT |
| Unique source:section pairs | 150 | data_locations across all checks |
| MANAGEMENT_DISPLAY checks | 64 | content_type |
| EVALUATIVE_CHECK checks | 305 | content_type |
| INFERENCE_PATTERN checks | 19 | content_type |
| Depth 1 (DISPLAY) | 20 | depth |
| Depth 2 (COMPUTE) | 270 | depth |
| Depth 3 (INFER) | 54 | depth |
| Depth 4 (HUNT) | 44 | depth |
| Mapper files | 5 | 1,808 lines total |
| FIELD_FOR_CHECK entries | 247 | check_field_routing.py |
| Historical state files | 3-5 | output/AAPL, output/TSLA, output/TSLA_post31 |
| Existing test files | 168 | tests/ directory |
| Current test count | ~1,796 | Phase 31 final count |

## Implementation Analysis: Success Criteria Mapping

### SC-1: Acquisition Driven by Knowledge
**What exists:** `required_data` on all 388 checks lists 10 source types. ACQUIRE has 4 clients (SEC, market, litigation, news) that collectively cover all 10 source types. `data_locations` lists 150 source:section pairs indicating what sections of each source are needed.
**What's needed:** A `RequirementsAnalyzer` that reads check definitions and produces a manifest. A validation step in ACQUIRE that confirms the manifest is satisfied. An ensure_section_split() step that validates section-splitting for sections checks declare they need.
**Complexity:** LOW-MEDIUM. The data is already declared; this is primarily a validation/reporting layer.

### SC-2: Extraction Guided by Check Hints
**What exists:** 247 checks have `data_strategy.field_key`. All 388 have `data_locations` with section-level detail. The `narrow_result()` function already uses `data_strategy.field_key` (Phase 31-03). No `extraction_hints` field exists on checks yet.
**What's needed:** An optional `extraction_hints` field on CheckDefinition (e.g., field patterns, expected value types, "no data" indicators). For Phase 32, this is primarily metadata that the gap detector uses -- NOT runtime extraction guidance. Making extractors actually USE hints is Phase 33/34.
**Complexity:** LOW. Adding the field is trivial. Populating it for all 388 checks requires scripted enrichment.

### SC-3: Pipeline Gap Detection
**What exists:** Nothing automated. Coverage gap rendering (Phase 31-03) shows which checks were SKIPPED in the output, but no development-time tool exists.
**What's needed:** A `PipelineGapDetector` that compares check requirements to pipeline capabilities across 3 levels: source, section, and field. A CLI command to run it. The result should be a machine-readable `GapReport` plus a Rich-formatted human display.
**Complexity:** MEDIUM. Requires introspecting pipeline capabilities (which sources ACQUIRE fetches, which fields EXTRACT produces, which mappers exist) and comparing to check declarations.

### SC-4: Different Evaluation Paths by Type
**What exists:** `content_type` is on all 388 checks (Phase 31). The check engine dispatches by threshold.type (tiered, boolean, percentage, etc.) but not by content_type. All checks go through `evaluate_check()` regardless of content type.
**What's needed:** Content-type-aware dispatch in `execute_checks()`. MANAGEMENT_DISPLAY checks get `evaluate_management_display()` (verify presence, report INFO). EVALUATIVE_CHECK checks get existing `evaluate_check()` (unchanged). INFERENCE_PATTERN checks get `evaluate_inference_pattern()` (multi-signal, pattern_ref lookup).
**Complexity:** MEDIUM. The dispatch is simple, but INFERENCE_PATTERN evaluation needs to integrate with patterns.json trigger conditions. Must not break existing EVALUATIVE_CHECK behavior.

### SC-5: Backtesting Infrastructure
**What exists:** Historical state files for AAPL and TSLA (4-7MB each). `Pipeline.load_state()` can deserialize them. `execute_checks()` can run against any ExtractedData. CheckRun table records results.
**What's needed:** A `BacktestRunner` that loads state files, runs current checks against them, stores results as CheckRun entries with a "backtest" flag. A CLI command (`do-uw knowledge backtest`). Comparison logic to diff check results across runs.
**Complexity:** LOW-MEDIUM. The components exist; this is primarily wiring and CLI.

### SC-6: Check Effectiveness Measurement
**What exists:** `get_check_stats()` computes fire_rate and skip_rate per check across all runs. `get_dead_checks()` finds never-fire checks. The `check-stats` and `dead-checks` CLI commands exist.
**What's needed:** An `EffectivenessReport` model that extends current stats with: always-fire detection (too sensitive), high-skip detection (data gaps), consistency metrics (standard deviation of fire rate across runs). A CLI command to display. Over time (after more runs), correlation with actual outcomes.
**Complexity:** LOW. Extends existing infrastructure.

## Open Questions

1. **Should RequirementsAnalyzer run at pipeline startup or only as CLI?**
   - What we know: Running at startup adds ~50ms but provides runtime validation that all required sources were acquired. Running as CLI-only is simpler but misses runtime gaps.
   - What's unclear: Is the runtime validation valuable given that ACQUIRE already has gate checks?
   - Recommendation: Both. Lightweight manifest validation at ACQUIRE completion (log warnings for gaps). Full gap analysis as CLI command. The runtime check is cheap enough.

2. **How should INFERENCE_PATTERN evaluation work with patterns.json?**
   - What we know: 19 checks have content_type=INFERENCE_PATTERN and pattern_ref. patterns.json has 19 patterns with trigger_conditions. The pattern detection engine in SCORE stage already evaluates patterns.
   - What's unclear: Should the ANALYZE check engine evaluate patterns inline, or should it defer to SCORE's pattern detection? Currently patterns are detected in SCORE after checks run.
   - Recommendation: ANALYZE's content-type dispatch for INFERENCE_PATTERN should NOT duplicate SCORE's pattern detection. Instead, ANALYZE should evaluate the individual signals that feed into patterns (which it already does), and INFERENCE_PATTERN checks should report their individual signal status. Pattern composition remains in SCORE. The content-type distinction for INFERENCE_PATTERN is primarily about the gap report and future extraction guidance, not a new evaluation path.

3. **How to handle the 141 checks without data_strategy?**
   - What we know: 141 checks (EXEC:20, FIN:23, FWRD:83, NLP:15) lack data_strategy because they use Phase 26+ mappers that return single-field dicts. These mappers bypass FIELD_FOR_CHECK entirely.
   - What's unclear: Should Phase 32 add data_strategy to these 141 checks, or treat them as "handled by dedicated mapper"?
   - Recommendation: The gap detector should recognize that checks handled by Phase 26+ dedicated mappers are NOT gaps -- they have a different (but valid) routing path. Add a `mapper_type` field or flag to distinguish "declarative field_key routing" from "dedicated mapper function" checks. No need to add data_strategy.field_key to the 141.

4. **Backtesting state file management**
   - What we know: State files are 4-7MB each. Currently stored in output/ directory per ticker.
   - What's unclear: Should backtest state files be archived separately? Should we version them by pipeline version?
   - Recommendation: Keep state files where they are. Add a `backtest_states/` directory convention for curated reference states. Version is implicit in the state file (created_at timestamp). Don't over-engineer state management for Phase 32.

5. **Extraction hints scope in Phase 32**
   - What we know: Success criteria 2 mentions extraction hints. Phase 31 added data_strategy but not extraction_hints.
   - What's unclear: How deep should extraction hints go? Regex patterns? LLM prompt fragments? Field types?
   - Recommendation: Phase 32 should add the `extraction_hints` field to CheckDefinition but populate it minimally (field_type, expected_format, null_indicators). The hints serve the gap detector ("does this check's extraction hint match an existing extractor?") not the extractors themselves. Making extractors hint-aware is Phase 33/34.

## Dependency Analysis

### Depends On (from Phase 31, all COMPLETE)
- [31-01] CheckDefinition Pydantic model with ContentType, DepthLevel, DataStrategy
- [31-02] All 388 checks enriched with content_type, depth, data_strategy.field_key
- [31-03] Declarative field_key resolution in narrow_result with 3-tier fallback
- [31-04] Migration persists enriched fields to Check ORM, query_checks supports content_type/depth filters

### Provides To (downstream phases)
- **Phase 33 (Living Knowledge)**: Gap detector identifies what new checks would need; backtest infrastructure validates new checks retroactively
- **Phase 34 (Display & Presentation Clarity)**: Content-type evaluation paths determine display treatment (MD=tables, EC=indicators, IP=narratives)
- **Phase 35 (Pricing Calibration)**: Effectiveness metrics inform scoring model calibration

## Sources

### Primary (HIGH confidence)
- `src/do_uw/pipeline.py` -- 306 lines, 7-stage sequential pipeline with resume support
- `src/do_uw/stages/acquire/__init__.py` -- AcquireStage with fixed client architecture
- `src/do_uw/stages/acquire/orchestrator.py` -- 348 lines, 4-phase acquisition flow (blind spot pre, structured, blind spot post, gates)
- `src/do_uw/stages/acquire/clients/sec_client.py` -- SEC filing client with hardcoded filing types
- `src/do_uw/stages/acquire/gates.py` -- 4 HARD + 2 SOFT acquisition gates
- `src/do_uw/stages/extract/__init__.py` -- ExtractStage with 13-phase fixed extractor sequence
- `src/do_uw/stages/analyze/__init__.py` -- AnalyzeStage with classification, hazard, check execution, analytical engines
- `src/do_uw/stages/analyze/check_engine.py` -- 308 lines, execute_checks() dispatcher
- `src/do_uw/stages/analyze/check_mappers.py` -- 488 lines, prefix-based data routing
- `src/do_uw/stages/analyze/check_field_routing.py` -- 346 lines, 247 check->field mappings with Phase 31 declarative resolution
- `src/do_uw/stages/analyze/check_evaluators.py` -- Threshold-type evaluation functions
- `src/do_uw/stages/analyze/check_results.py` -- CheckResult, CheckStatus, DataStatus models
- `src/do_uw/knowledge/check_definition.py` -- CheckDefinition, ContentType, DepthLevel, DataStrategy Pydantic models
- `src/do_uw/knowledge/models.py` -- Check ORM with Phase 31 enrichment columns
- `src/do_uw/knowledge/store.py` -- KnowledgeStore query API with content_type/depth filters
- `src/do_uw/knowledge/store_bulk.py` -- CheckRun recording, get_check_stats(), get_dead_checks()
- `src/do_uw/knowledge/compat_loader.py` -- BackwardCompatLoader bridge
- `src/do_uw/brain/checks.json` -- 388 enriched check definitions
- `src/do_uw/brain/patterns.json` -- 19 composite pattern definitions
- `output/AAPL/state.json`, `output/TSLA/state.json` -- Historical state files for backtesting

### Secondary (MEDIUM confidence)
- `src/do_uw/stages/analyze/check_mappers_phase26.py` -- 403 lines, Phase 26+ dedicated mappers
- `src/do_uw/stages/analyze/check_mappers_fwrd.py` -- 377 lines, FWRD check mappers
- `src/do_uw/stages/analyze/check_mappers_sections.py` -- 194 lines, governance/litigation section mappers
- `src/do_uw/stages/extract/filing_sections.py` -- Section parsing (item1, item1a, item3, item7, etc.)
- `.planning/phases/31-knowledge-model-redesign/31-RESEARCH.md` -- Phase 31 research (architecture context)
- `.planning/phases/31-knowledge-model-redesign/31-*-SUMMARY.md` -- Phase 31 plan summaries (delivered capabilities)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- No new dependencies, all tools already in project
- Requirements analyzer: HIGH -- Directly derived from existing check metadata (verified: all 388 checks have required_data, 150 source:section pairs)
- Gap detection: HIGH -- Static analysis of existing capabilities vs. declared requirements
- Content-type dispatch: HIGH -- ContentType enum exists (Phase 31), evaluation paths well-understood
- Backtesting: MEDIUM-HIGH -- Components exist (Pipeline.load_state, execute_checks, CheckRun) but integration is new
- Effectiveness metrics: MEDIUM -- Framework is straightforward; value depends on accumulating enough run data (N>5)
- Extraction hints: MEDIUM -- Scope is deliberately minimal for Phase 32; deeper integration is future work

**Research date:** 2026-02-15
**Valid until:** 2026-03-15 (stable domain -- no external dependency changes expected)
