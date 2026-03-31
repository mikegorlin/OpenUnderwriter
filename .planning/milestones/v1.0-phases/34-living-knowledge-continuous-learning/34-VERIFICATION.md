---
phase: 34-living-knowledge-continuous-learning
verified: 2026-02-20T00:00:00Z
status: human_needed
score: 7/9 success criteria verified
re_verification: false
human_verification:
  - test: "Ingest a real document and verify pattern extraction against PATTERNS.md"
    expected: "The LLM prompt identifies whether the event matches known composite patterns from brain/PATTERNS.md (e.g. SPAC settlement chains, restatement cascades). The response cites specific pattern IDs."
    why_human: "SC3 (Pattern Extraction) requires structured comparison to 17 known patterns. The LLM prompt asks about check categories but does not reference PATTERNS.md or produce structured pattern-match output. Cannot verify programmatically whether the LLM identifies named patterns vs just summarizing the event."
  - test: "Run `do-uw calibrate preview` and verify compounding improvement over baseline"
    expected: "The calibration preview shows accumulated threshold improvements based on prior runs (brain_effectiveness data), not just manually-submitted proposals."
    why_human: "SC6 (Baseline Self-Calibration) includes 'update based on accumulated results' — the architecture supports human-submitted THRESHOLD_CHANGE proposals but does not automatically mine brain_effectiveness or brain_check_runs to propose threshold adjustments. Whether this satisfies SC6 depends on the user's interpretation of 'accumulated results'."
---

# Phase 34: Living Knowledge & Continuous Learning — Verification Report

**Phase Goal:** The knowledge system becomes a living analytical framework that can ingest new information and evolve. When a new article, claim, regulatory action, or industry report arrives, the system can: evaluate whether existing checks cover it, identify knowledge gaps, extract new patterns, propose new checks or threshold adjustments, and validate retroactively against the portfolio. The system gets meaningfully smarter with every company analyzed and every external input ingested.

**Verified:** 2026-02-20
**Status:** human_needed
**Re-verification:** No — initial verification
**All 77 tests pass. Automated checks pass on 7/9 success criteria. 2 items need human verification.**

---

## Goal Achievement

### Observable Truths (Success Criteria from ROADMAP.md)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | External document ingestion | VERIFIED | `ingestion_llm.py` (extract_document_intelligence, fetch_url_content), `cli_ingest.py` (file/url commands), 19 tests pass |
| SC2 | Knowledge gap identification | VERIFIED | `gap_analysis` field in DocumentIngestionResult; LLM system prompt explicitly asks "what risks does this reveal that might not be covered?"; reflected in impact report |
| SC3 | Pattern extraction | ? UNCERTAIN | LLM prompt asks for check categories and new checks but does NOT reference PATTERNS.md or produce structured pattern comparison. No `patterns_identified` field in DocumentIngestionResult. Needs human to verify whether LLM output qualifies. |
| SC4 | Check proposal generation | VERIFIED | Proposals enter brain_proposals table with INCUBATING status via `store_proposals()`; `_proposal_has_sufficient_detail()` gates INCUBATING check creation; 4 tests cover this path |
| SC5 | Retroactive validation | VERIFIED | `preview_calibration()` in calibrate.py calls `execute_checks()` directly against cached state files (output/*/state.json), computing current vs proposed results diff; 15 tests including `test_preview_with_proposals` |
| SC6 | Baseline self-calibration | ? UNCERTAIN | THRESHOLD_CHANGE proposals can be submitted and applied with git audit trail. However no automated analysis mines brain_effectiveness/brain_check_runs to propose threshold adjustments — calibration drift detection is manual. Whether SC6 requires automated drift detection or human-submitted proposals is a judgment call. |
| SC7 | Underwriter feedback integration | VERIFIED | `feedback.py` (record_feedback, get_feedback_summary, auto-proposal), `cli_feedback.py` (add/summary/list), MISSING_COVERAGE auto-generates INCUBATING proposals; 11 tests pass |
| SC8 | Compounding intelligence | VERIFIED (architecture) | Discovery hook in orchestrator fires on every run, feeds proposals to brain; calibration promotes approved proposals to ACTIVE; brain_effectiveness tracks check run history; the mechanism for compounding is in place. Empirical verification requires 50+ runs. |
| SC9 | Pricing model distinction preserved | VERIFIED (no violation) | Phase 34 adds ingestion/feedback/calibration to the check/knowledge layer only. No changes touch scoring computation, pricing model, or actuarial data. Separation preserved by inaction. |

**Score:** 7/9 criteria verified with confidence, 2 need human judgment

---

## Required Artifacts

### Plan 01 — Brain Schema & Data Models

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/brain_schema.py` | brain_feedback + brain_proposals tables DDL, updated active view | VERIFIED | Tables at lines 203-234, view excludes RETIRED/INCUBATING/INACTIVE at line 246-248 |
| `src/do_uw/knowledge/ingestion_models.py` | ProposedCheck, DocumentIngestionResult, IngestionImpactReport | VERIFIED | All 3 models present, substantive fields, Pydantic v2 |
| `src/do_uw/knowledge/feedback_models.py` | FeedbackEntry, ProposalRecord, FeedbackSummary | VERIFIED | All 3 models with Literal types for enums |
| `tests/knowledge/test_brain_feedback_schema.py` | 13 tests for schema/lifecycle/models | VERIFIED | 13 tests pass (TestSchemaCreation, TestIncubatingLifecycle, TestIngestionModels, TestFeedbackModels) |

### Plan 02 — LLM Document Ingestion

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/knowledge/ingestion_llm.py` | extract_document_intelligence, fetch_url_content, generate_impact_report, store_proposals | VERIFIED | 4 public functions, lazy anthropic/instructor import, 269 lines |
| `src/do_uw/cli_ingest.py` | `do-uw ingest file` and `do-uw ingest url` commands | VERIFIED | ingest_app with file/url sub-commands, Rich display, --apply flag |
| `tests/knowledge/test_ingestion_llm.py` | Tests for LLM extraction, URL fetch, CLI | VERIFIED | 19 tests pass (mocked Anthropic calls) |

### Plan 03 — Underwriter Feedback System

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/knowledge/feedback.py` | record_feedback, get_feedback_summary, get_feedback_for_check, mark_feedback_applied | VERIFIED | All 4 public functions + _auto_propose_check, 425 lines |
| `src/do_uw/cli_feedback.py` | feedback_app with add/summary/list commands | VERIFIED | 3 subcommands (add, summary, list), 310 lines |
| `tests/knowledge/test_feedback.py` | 11 tests for feedback module and CLI | VERIFIED | 11 tests pass |

### Plan 04 — Calibration Workflow

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/knowledge/calibrate.py` | preview_calibration, apply_calibration, git audit, impact simulation | VERIFIED | CalibrationPreview + ApplyResult models, execute_checks called directly, git commit at lines 535+, 500 lines |
| `src/do_uw/cli_calibrate.py` | preview, apply, show commands | VERIFIED | 3 new commands added to existing calibrate_app |
| `tests/knowledge/test_calibrate.py` | 15 tests including git mock, claims correlation | VERIFIED | 15 tests pass |

### Plan 05 — Automatic Discovery & Calibration Notes

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/knowledge/discovery.py` | process_blind_spot_discoveries, get_discovery_summary, keyword scoring | VERIFIED | 20 D&O keywords, relevance threshold=5, non-blocking, 260 lines |
| `src/do_uw/stages/render/md_renderer_helpers_calibration.py` | render_calibration_notes | VERIFIED | Function present, queries brain DuckDB, lazy import, graceful fail, 223 lines |
| `src/do_uw/stages/render/sections/sect_calibration.py` | Word renderer for calibration notes | VERIFIED | File exists (4229 bytes) |
| `tests/knowledge/test_discovery_integration.py` | 19 tests for discovery, calibration notes | VERIFIED | 19 tests pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cli_ingest.py` | `ingestion_llm.py` | `extract_document_intelligence` | WIRED | Lazy import in `ingest_file()` and `ingest_url()` at lines 122-126, 194-199 |
| `cli_ingest.py` | `brain_writer.py` | `insert_check` via `store_proposals()` | WIRED | `_apply_proposals()` instantiates BrainWriter and calls `store_proposals_fn()` |
| `cli.py` | `cli_ingest.py` | `app.add_typer(ingest_app)` | WIRED | Line 50: `app.add_typer(ingest_app, name="ingest")` |
| `cli.py` | `cli_feedback.py` | `app.add_typer(feedback_app)` | WIRED | Line 49: `app.add_typer(feedback_app, name="feedback")` |
| `cli_feedback.py` | `feedback.py` | `record_feedback` | WIRED | Lines 104, 122 in feedback_add command |
| `feedback.py` | `brain_schema.py` | INSERT into brain_feedback + brain_proposals | WIRED | Lines 53-68 (INSERT), 240-253 (_auto_propose_check) |
| `calibrate.py` | `check_engine.py` | `execute_checks` | WIRED | Line 382: lazy import + calls at lines 417, 422 |
| `calibrate.py` | `brain_writer.py` | `BrainWriter` for apply | WIRED | Line 195 import, lines 227/237/246 usage |
| `cli_calibrate.py` | `calibrate.py` | `preview_calibration`, `apply_calibration` | WIRED | Lines 236, 370 |
| `orchestrator.py` | `discovery.py` | `process_blind_spot_discoveries` | WIRED | Lines 467-472 in `_run_discovery_hook()`, called at line 153 |
| `discovery.py` | `ingestion_llm.py` | `extract_document_intelligence` | WIRED | Line 173 lazy import inside `_process_single_result()` |
| `md_renderer.py` | `md_renderer_helpers_calibration.py` | `render_calibration_notes` | WIRED | Line 143 import, line 146 call |
| `word_renderer.py` | `sect_calibration.py` | `render_calibration_section` | WIRED | Line 93 dynamic import registration |
| `brain_schema.py` | `brain_writer.py` | `create_schema` called on connect | WIRED | Plan 01 confirmed (brain_writer._get_conn creates schema) |
| `brain_loader.py` | `brain_schema.py` | brain_checks_active excludes INCUBATING | WIRED | View DDL line 246-248 confirmed programmatically |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ARCH-09 | 34-04 | Scoring weights/thresholds in JSON config, never hardcoded | EXTENDED | calibrate.py exports checks.json via BrainWriter.export_json after apply; threshold changes go through structured proposal → review → apply → JSON export cycle |
| ARCH-10 | 34-01, 34-02, 34-05 | Brain knowledge assets carried forward + evolved | EXTENDED | New ingestion pipeline adds to existing checks.json; INCUBATING lifecycle gates new checks; discovery hook continuously enriches |
| SECT7-06 | 34-03, 34-04 | Claims correlation scoring calibration | EXTENDED | THRESHOLD_CHANGE proposals can update check weights/thresholds; test_apply_claims_correlation_update in test_calibrate.py verifies end-to-end |
| SECT7-07 | 34-03, 34-04 | Claim probability output calibration | EXTENDED | Feedback system allows THRESHOLD feedback on probability bands; calibration applies updates with git audit |
| SECT7-11 | 34-01, 34-02, 34-03, 34-04 | Calibration methodology — all parameters in config | EXTENDED | Full calibration loop: feedback → proposal → review → apply → checks.json export → git commit; all calibration parameters auditable |

**Note on requirement status:** All five requirements were already marked Complete from earlier phases (Phases 1 and 6). Phase 34 extends them with a living calibration workflow rather than introducing them for the first time. No orphaned requirements found.

---

## Anti-Patterns Found

| File | Pattern | Severity | Assessment |
|------|---------|----------|------------|
| `calibrate.py:34,38,42,46` | `return []` | Info | Typed default factory closures for Pydantic — legitimate pattern |
| `calibrate.py:388` | `return [], 0` | Info | Error return from `_run_impact_simulation` on empty output dir — appropriate |
| `calibrate.py:613,631` | `return {}` / `return []` | Info | Error returns in `_compute_proposal_changes` and `_get_proposals_by_ids` — appropriate |
| `calibrate.py:633` | `placeholders` variable | Info | SQL parameterized query construction — not a placeholder stub |

No blockers. No stubs detected. All "placeholder" matches are legitimate SQL or Pydantic patterns.

---

## Detailed Truth Assessments

### SC3: Pattern Extraction — Uncertain

**What was built:** The LLM extraction prompt asks the model to identify check categories (BIZ., FIN., GOV., LIT., MKT., REG. prefixes) and propose new checks. The `DocumentIngestionResult` model captures `affected_checks` (existing check IDs) and `proposed_new_checks`.

**What SC3 requires:** "New information is analyzed for patterns — 'This $500M SPAC settlement followed: projections during roadshow → missed post-merger → stock drop → 10b-5 suit.' Is this a known pattern? A variant? Something new?"

**The gap:** There is no structured comparison against the 17 composite risk patterns in `brain/PATTERNS.md`. The LLM prompt does not reference PATTERNS.md. The `DocumentIngestionResult` model has no `patterns_identified` or `pattern_match` field. The model's `pattern_ref` field in brain_checks exists for check-level references but is not populated by the ingestion pipeline.

**Human test needed:** Ingest a document describing a known pattern event (e.g., a SPAC restatement lawsuit) and verify whether the LLM output correctly identifies the known pattern by name vs. just describing it generically.

### SC6: Baseline Self-Calibration — Uncertain

**What was built:** `apply_calibration()` applies THRESHOLD_CHANGE proposals (human-submitted via `do-uw feedback add --type THRESHOLD` or `do-uw ingest`) with git audit trail and exports checks.json. All calibration parameters remain in config files.

**What SC6 requires:** "Industry base rates, severity baselines, and scoring parameters update based on accumulated results with human approval gates. Calibration drift is tracked and auditable."

**The ambiguity:** "Accumulated results" could mean (a) accumulated human feedback driving proposal submissions — this is implemented, or (b) automated mining of `brain_check_runs` / `brain_effectiveness` to propose threshold changes when patterns emerge — this is NOT implemented. The `brain_effectiveness` table schema exists but nothing queries it to generate THRESHOLD_CHANGE proposals automatically. The `do-uw calibrate show` command shows git history of calibration commits, providing auditability.

**Human test needed:** Determine whether SC6's "accumulated results" means "human-mediated calibration from observed results" (implemented) or "automated drift detection from run history" (not implemented).

---

## Test Execution Results

All 77 phase 34 tests pass:
- `test_brain_feedback_schema.py`: 13/13 passed
- `test_ingestion_llm.py`: 19/19 passed
- `test_feedback.py`: 11/11 passed
- `test_calibrate.py`: 15/15 passed
- `test_discovery_integration.py`: 19/19 passed

Total: **77 passed in 1.65s**

---

## Summary

Phase 34 delivers a substantive living knowledge framework. The core loop is fully implemented:

1. External documents can be ingested via LLM (`do-uw ingest file/url`)
2. Knowledge gaps are identified and proposals generated (INCUBATING status)
3. Underwriter feedback feeds calibration signals (`do-uw feedback add`)
4. Calibration can preview impact and apply changes with git audit (`do-uw calibrate preview/apply`)
5. Every pipeline run automatically processes blind spot results for proposals (discovery hook in orchestrator)
6. Worksheets show calibration status transparently (Calibration Notes section)

Two success criteria require human judgment to definitively verify:
- **SC3 (Pattern Extraction):** The system extracts intelligence and proposes new checks, but structured matching against the 17 named composite patterns in PATTERNS.md is not confirmed
- **SC6 (Baseline Self-Calibration):** The calibration infrastructure is in place, but whether automated drift detection from run history is required vs human-mediated calibration is ambiguous

All automated checks pass. No stub implementations found. The compounding intelligence architecture (discovery → proposals → review → activation → better future checks) is correctly wired end-to-end.

---

_Verified: 2026-02-20_
_Verifier: Claude (gsd-verifier)_
