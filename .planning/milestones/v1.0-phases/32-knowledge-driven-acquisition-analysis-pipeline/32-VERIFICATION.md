---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
verified: 2026-02-20T17:30:00Z
status: gaps_found
score: 4/6 must-haves verified
re_verification: false
gaps:
  - truth: "ACQUIRE stage reads check data_strategy declarations to determine what sources to fetch — if a check says it needs SEC_10K:item_9a_controls, ACQUIRE ensures that section is acquired and section-split"
    status: failed
    reason: "ACQUIRE stage has zero integration with brain.duckdb or data_strategy declarations. The gap_detector knows what sources are required, but the ACQUIRE orchestrator does not read from brain at runtime. Plans 04-05 deliver the foundation (data in brain.duckdb, gap detection tooling) but explicitly scoped ACQUIRE wiring to Phase 33/34."
    artifacts:
      - path: "src/do_uw/stages/acquire/orchestrator.py"
        issue: "No brain, BrainDBLoader, data_strategy, or required_data references — ACQUIRE is unchanged from pre-Phase 32"
    missing:
      - "ACQUIRE stage must read active checks from brain.duckdb and derive required sources/sections from data_strategy declarations"
      - "If a check's data_strategy specifies SEC_10K:item_9a_controls, the acquire orchestrator must ensure that section is fetched and section-split"

  - truth: "When extraction_hints exist for a check, EXTRACT stage uses them to guide parsing — which fields to look for, what patterns indicate presence, what 'no data' looks like"
    status: failed
    reason: "No extraction_hints field exists in any check definition (0 of 388 checks). EXTRACT stage has no brain integration. Not claimed as complete in any plan's requirements-completed field — SC-2 was explicitly deferred to Phase 33/34 by the scoping note in Plan 04."
    artifacts:
      - path: "src/do_uw/stages/extract/"
        issue: "No extraction_hints, brain, or BrainDBLoader references anywhere in the extract stage"
      - path: "src/do_uw/brain/checks.json"
        issue: "0 of 388 checks have extraction_hints field"
    missing:
      - "extraction_hints field must be added to check definitions in checks.json"
      - "EXTRACT stage must read extraction_hints from brain for each check and use them to guide field parsing"
      - "Define 'no data' sentinel behavior guided by hints"
human_verification:
  - test: "Run 'do-uw brain status' command"
    expected: "Rich table showing check counts by lifecycle, content_type, section; taxonomy counts; backlog count; brain.duckdb file size"
    why_human: "CLI output formatting and Rich table rendering cannot be verified programmatically"
  - test: "Run 'do-uw brain gaps' command"
    expected: "Rich-formatted gap report with severity colors — CRITICAL in red, WARNING in yellow, INFO in dim; summary showing 0 CRITICAL gaps, N WARNING and INFO gaps"
    why_human: "Rich table color/styling and exact display format requires visual inspection"
  - test: "Run 'do-uw brain export-docs' and pipe to a file"
    expected: "Readable Markdown with all 5 sections, check IDs, names, thresholds, risk questions, lifecycle states — organized by report section"
    why_human: "Markdown formatting and comprehensiveness requires human review"
  - test: "Run 'do-uw brain backtest output/AAPL/state.json --no-record'"
    expected: "BacktestResult showing 381 checks executed, breakdown of triggered/clear/skipped/info (should match the verified AAPL result: 6 triggered, 42 clear, 40 skipped, 293 info)"
    why_human: "Backtest determinism against real state file should be verified by a human run"
---

# Phase 32: Knowledge-Driven Acquisition & Analysis Pipeline Verification Report

**Phase Goal:** Flip the pipeline so knowledge declarations drive data acquisition and extraction. Checks declare what data they need, ACQUIRE fills those needs, EXTRACT is guided by extraction hints, ANALYZE evaluates based on check type. Adding a new check auto-surfaces every missing pipeline link. Plus backtesting infrastructure.

**Verified:** 2026-02-20
**Status:** GAPS FOUND
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC-1 | ACQUIRE stage reads check data_strategy declarations to determine what sources to fetch | FAILED | `src/do_uw/stages/acquire/orchestrator.py` has zero brain/data_strategy references. ACQUIRE is unchanged from pre-Phase 32. Plans 04-07 deliver the foundation (gap_detector, brain.duckdb) but explicitly scoped ACQUIRE wiring to Phase 33/34. |
| SC-2 | EXTRACT stage uses extraction_hints from checks to guide parsing | FAILED | 0 of 388 checks have `extraction_hints` field. EXTRACT stage has no brain integration. Explicitly deferred to Phase 33/34 by Plan 04's scoping note. Not claimed as complete in any `requirements-completed` field. |
| SC-3 | Adding a new check produces a gap report surfacing every missing pipeline link | VERIFIED | `src/do_uw/knowledge/gap_detector.py` implements 3-level gap analysis (source/field/mapper). `do-uw brain gaps` CLI command surfaces CRITICAL/WARNING/INFO gaps. 15 gap detector tests pass against real checks.json. |
| SC-4 | MANAGEMENT_DISPLAY checks verify data presence; EVALUATIVE_CHECKs apply thresholds; INFERENCE_PATTERNs defer to evaluate_check | PARTIAL | `evaluate_management_display()` in check_engine.py correctly returns INFO/SKIPPED for MANAGEMENT_DISPLAY checks. EVALUATIVE_CHECK path unchanged. INFERENCE_PATTERN delegates to `evaluate_check()` (same as EVALUATIVE_CHECK) — multi-signal detection with temporal/cross-reference logic is NOT implemented for INFERENCE_PATTERN. SC-4 text says "run multi-signal detection with temporal and cross-reference logic" for INFERENCE_PATTERN, which is not yet true. |
| SC-5 | Backtesting infrastructure for running checks against historical state files | VERIFIED | `src/do_uw/knowledge/backtest.py` implements BacktestRunner and BacktestComparison. Verified against real AAPL state.json: 381 checks executed, results recorded to brain_check_runs with is_backtest=TRUE. 11 backtest tests pass. |
| SC-6 | After N runs, system reports always-fire, never-fire, high-skip, no-predictive-value checks | VERIFIED | `src/do_uw/brain/brain_effectiveness.py` implements compute_effectiveness() and update_effectiveness_table(). `do-uw brain effectiveness` CLI command surfaces the report. 27 effectiveness tests pass. |

**Score:** 3.5/6 truths verified (SC-3, SC-5, SC-6 fully verified; SC-4 partially verified; SC-1, SC-2 failed)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/brain_schema.py` | DuckDB DDL for 7 tables + 3 views + indexes | VERIFIED | 231 lines; 7 tables (brain_checks, brain_taxonomy, brain_backlog, brain_changelog, brain_effectiveness, brain_industry, brain_check_runs) + 3 views + indexes |
| `src/do_uw/brain/brain_migrate.py` | Migration: checks.json -> brain_checks, taxonomy, backlog | VERIFIED | 367 lines; migrate_checks_to_brain() returns {"checks": 388, "taxonomy_questions": 45, "taxonomy_factors": 10, "taxonomy_hazards": 15, "taxonomy_sections": 5, "backlog": 7} |
| `src/do_uw/brain/brain_enrich.py` | Enrichment applier creating version 2 rows | VERIFIED | 376 lines; enrich_brain_checks() and remap_to_v6() both present and functional |
| `src/do_uw/brain/enrichment_data.py` | Mapping tables: PREFIX_TO_REPORT_SECTION, SUBDOMAIN_TO_RISK_QUESTIONS, etc. | VERIFIED | 661 lines (exceeds 500-line guideline — acceptable as data-only module); 0 old Q-ID references; all mappings use v6 X.Y format |
| `src/do_uw/brain/brain_loader.py` | BrainDBLoader with lifecycle filtering and enrichment overlay | VERIFIED | 389 lines; section_map uses v6 names (company, market, financial, governance, litigation); auto-migrates if brain.duckdb missing |
| `src/do_uw/brain/brain_effectiveness.py` | EffectivenessTracker with fire_rate/skip_rate from brain_check_runs | VERIFIED | 425 lines; compute_effectiveness(), update_effectiveness_table(), record_check_run(), record_check_runs_batch() all implemented |
| `src/do_uw/knowledge/compat_loader.py` | BackwardCompatLoader delegates to BrainDBLoader | VERIFIED | Delegates when brain.duckdb exists (_try_brain_db_loader() returns BrainDBLoader); load_checks() uses BrainDBLoader when available |
| `src/do_uw/stages/analyze/check_engine.py` | Content-type-aware dispatch: MANAGEMENT_DISPLAY -> INFO, EVALUATIVE_CHECK -> threshold | VERIFIED | evaluate_management_display() at line 275; dispatch at lines 109-115; INFERENCE_PATTERN gets same path as EVALUATIVE_CHECK (deferred) |
| `src/do_uw/knowledge/requirements.py` | AcquisitionManifest and build_manifest() from check declarations | VERIFIED | 103 lines; Pydantic model with required_sources, source_to_checks, checks_by_depth, checks_by_content_type |
| `src/do_uw/knowledge/gap_detector.py` | PipelineGapDetector with detect_gaps() at 3 severity levels | VERIFIED | 201 lines; ACQUIRED_SOURCES (10 sources), HANDLED_PREFIXES (8 prefixes), PHASE26_PREFIXES (6 patterns) |
| `src/do_uw/knowledge/backtest.py` | BacktestRunner: load state, execute checks, record to brain_check_runs | VERIFIED | 252 lines; run_backtest() calls execute_checks(); compare_backtests() for A/B analysis |
| `src/do_uw/cli_brain.py` | 7-command Brain CLI sub-app | VERIFIED | 633 lines (exceeds 500-line guideline — 7 commands in one file); registered in cli.py as `brain_app` |
| `.planning/phases/32-knowledge-driven-acquisition-analysis-pipeline/QUESTIONS-FINAL.md` | Finalized v6 question framework (user-approved) | VERIFIED | 648 lines; 231 questions, 5 sections, 45 subsections; 11 review decisions documented |
| `src/do_uw/brain/brain.duckdb` | Populated brain database (separate from .cache/analysis.duckdb) | VERIFIED | 3.0MB at src/do_uw/brain/brain.duckdb; .cache/ contains analysis.db (different file entirely) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `brain_migrate.py` | `brain/checks.json` | json.load reads checks.json, inserts into brain_checks | WIRED | `_get_checks_json_path()` returns Path(__file__).parent / "checks.json" |
| `brain_schema.py` | brain.duckdb | CREATE TABLE brain_checks DDL | WIRED | 7 tables + 3 views + indexes; `create_schema()` executes DDL |
| `enrichment_data.py` | QUESTIONS-FINAL.md | SUBDOMAIN_TO_RISK_QUESTIONS uses v6 X.Y subsection IDs | WIRED | 0 old Q-ID references; verified by grep; all mappings match X.Y format |
| `brain_enrich.py` | brain.duckdb brain_checks | remap_to_v6() creates version 3 rows | WIRED | remap_to_v6() at line 236; idempotent |
| `compat_loader.py` | `brain_loader.py` | _try_brain_db_loader() delegates when brain.duckdb exists | WIRED | BackwardCompatLoader.load_checks() at line 137-139 delegates to BrainDBLoader |
| `check_engine.py` | `evaluate_management_display` | content_type dispatch at line 109-115 | WIRED | `if content_type == "MANAGEMENT_DISPLAY": result = evaluate_management_display(check, data)` |
| `requirements.py` | `brain/checks.json` | build_manifest reads required_data and data_locations from checks | WIRED | Iterates checks, reads required_data list and data_locations dict |
| `gap_detector.py` | `requirements.py` | detect_gaps takes AcquisitionManifest | WIRED | `from do_uw.knowledge.requirements import AcquisitionManifest`; function signature takes manifest |
| `brain_effectiveness.py` | brain.duckdb brain_check_runs | compute_effectiveness queries brain_check_runs | WIRED | `SELECT check_id, status, COUNT(*) FROM brain_check_runs WHERE is_backtest = FALSE` |
| `cli_brain.py` | `requirements.py` / `gap_detector.py` | gaps command calls build_manifest() then detect_gaps() | WIRED | Lines 196-207; lazy imports inside command function body |
| `cli_brain.py` | `brain_effectiveness.py` | effectiveness command calls compute_effectiveness() | WIRED | Line 271; lazy import inside command function body |
| `backtest.py` | `check_engine.py` | run_backtest calls execute_checks() on historical state | WIRED | Line 117-126; loads AnalysisState from JSON, calls execute_checks() |
| `cli.py` | `cli_brain.py` | app.add_typer(brain_app) | WIRED | Lines 18, 44; `from do_uw.cli_brain import brain_app` + `app.add_typer(brain_app, name="brain")` |
| ACQUIRE stage | brain.duckdb | ACQUIRE reads data_strategy to drive acquisition | NOT WIRED | SC-1 gap: no brain references in src/do_uw/stages/acquire/ — deferred to Phase 33/34 |
| EXTRACT stage | brain.duckdb | EXTRACT uses extraction_hints to guide parsing | NOT WIRED | SC-2 gap: no extraction_hints in checks.json, no brain references in src/do_uw/stages/extract/ — deferred to Phase 33/34 |

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|----------------|-------------|--------|----------|
| SC-1 | 32-04, 32-05 | ACQUIRE reads check data_strategy to drive what sources to fetch | BLOCKED | ACQUIRE stage unchanged; gap_detector provides analysis of what SHOULD be acquired but doesn't wire ACQUIRE. Plans 04-05 claim SC-1 as "requirements-completed" but the scoping note in Plan 04 explicitly defers ACQUIRE wiring to Phase 33/34. |
| SC-2 | (not claimed in any requirements-completed) | EXTRACT uses extraction_hints from checks to guide parsing | BLOCKED | 0 checks have extraction_hints field; EXTRACT stage has no brain integration; correctly not claimed as complete in any plan's requirements-completed |
| SC-3 | 32-04, 32-06, 32-07 | Gap detection surfaces missing pipeline links when new check added | SATISFIED | gap_detector.py + brain gaps CLI; 3-level analysis (source/field/mapper); 15 gap tests pass |
| SC-4 | 32-05 | Different evaluation paths by content_type | PARTIALLY SATISFIED | MANAGEMENT_DISPLAY gets INFO-only evaluation (correct). EVALUATIVE_CHECK unchanged (correct). INFERENCE_PATTERN delegates to evaluate_check() — multi-signal temporal/cross-reference logic is not implemented (deferred). |
| SC-5 | 32-07 | Backtesting infrastructure for historical state replay | SATISFIED | backtest.py + brain backtest CLI; verified against real AAPL state.json; 11 tests pass |
| SC-6 | 32-06, 32-07 | Check effectiveness measurement after N runs | SATISFIED | brain_effectiveness.py + brain effectiveness CLI; always-fire/never-fire/high-skip classification with N-based confidence; 27 tests pass |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/do_uw/brain/brain_migrate.py` | 203 | `check["name"],  # question (placeholder)` | Info | question field uses check name as placeholder; Plan 02 was intended to enrich this but it remains as-is |
| `src/do_uw/brain/enrichment_data.py` | (whole file) | 661 lines — exceeds 500-line anti-context-rot limit | Warning | File is data-only (static mapping tables), acknowledged in 32-02-SUMMARY.md; no logic |
| `src/do_uw/cli_brain.py` | (whole file) | 633 lines — exceeds 500-line anti-context-rot limit | Warning | 7 CLI commands in one file; could be split if it grows further |

### Human Verification Required

#### 1. Brain CLI Status Display

**Test:** Run `do-uw brain status`
**Expected:** Rich table showing check counts (active vs total) by lifecycle_state, content_type, report_section; taxonomy entity counts (45 risk questions, 10 factors, 15 hazards, 5 sections); backlog open items count; brain.duckdb file path and size
**Why human:** Rich table formatting and completeness of display require visual inspection

#### 2. Brain Gaps Report Colors

**Test:** Run `do-uw brain gaps` and `do-uw brain gaps --severity CRITICAL`
**Expected:** Gap report with severity color coding (CRITICAL=red, WARNING=yellow, INFO=dim); summary showing 0 CRITICAL gaps; WARNING gaps for checks without field routing; INFO gaps for prefix coverage
**Why human:** Rich color styling cannot be verified programmatically

#### 3. Export-Docs Readability

**Test:** Run `do-uw brain export-docs > /tmp/brain_export.md` and review the output
**Expected:** Organized Markdown with all 5 sections (company/market/financial/governance/litigation); each section lists active checks with check_id, name, thresholds, risk_questions, lifecycle_state; readable without code access
**Why human:** Markdown formatting and comprehensiveness of coverage requires human review

#### 4. Backtest Against Real AAPL State

**Test:** Run `do-uw brain backtest output/AAPL/state.json --no-record`
**Expected:** BacktestResult showing 381 checks executed; specific counts should be deterministic (verified internally as 6 triggered, 42 clear, 40 skipped, 293 info)
**Why human:** Verifying determinism against real state file and confirming result counts match the summary's reported values

## Gaps Summary

Two success criteria are structurally unmet because the phase explicitly deferred them to Phase 33/34:

**SC-1 (ACQUIRE driven by knowledge):** The brain knowledge layer now declares what every check needs (data_strategy.field_key, required_data, data_locations fields in checks.json). The PipelineGapDetector can tell you which sources are and aren't acquired. But the ACQUIRE stage itself (`stages/acquire/orchestrator.py`) is not wired to read from brain.duckdb at runtime. It still fetches a fixed set of sources. Plan 04's scoping note acknowledges this explicitly: "The actual wiring of ACQUIRE (brain-reads-to-drive-acquisition, SC-1)... is Phase 33/34 scope." Despite this, Plans 04 and 05 both list `requirements-completed: [SC-1, ...]` in their summaries — this is a misleading claim. What was completed is the foundation layer, not the success criterion as stated in the ROADMAP.

**SC-2 (EXTRACT guided by hints):** No implementation exists. There are no `extraction_hints` fields in any check definition (0 of 388). The EXTRACT stage has no brain integration. This was correctly not claimed in any plan's `requirements-completed` field, though the 32-07 SUMMARY's narrative bullet incorrectly lists "SC-2: Extraction guided by hints (Plan 05)" as achieved.

**SC-4 (Different evaluation paths by type):** The MANAGEMENT_DISPLAY and EVALUATIVE_CHECK paths are correctly implemented. However, the ROADMAP criterion specifies INFERENCE_PATTERN should "run multi-signal detection with temporal and cross-reference logic" — instead, INFERENCE_PATTERN currently delegates to the same `evaluate_check()` path as EVALUATIVE_CHECK. This is documented as deferred in check_engine.py comments ("Pattern composition remains in SCORE stage") and was acknowledged in the plans.

**What was delivered successfully:** The brain DuckDB knowledge store (Plans 01-04) is the strongest deliverable — 388 checks with v6 taxonomy enrichment, versioned, queryable, with gap detection and effectiveness tracking infrastructure. The Brain CLI (Plan 07) and backtesting (Plan 07) are fully operational. SC-3, SC-5, SC-6 are genuinely achieved.

---

_Verified: 2026-02-20_
_Verifier: Claude (gsd-verifier)_
