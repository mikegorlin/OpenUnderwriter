---
phase: 128-infrastructure-foundation
verified: 2026-03-22T23:15:00Z
status: gaps_found
score: 10/11 must-haves verified
gaps:
  - truth: "A reference snapshot script captures JSON context + HTML section hashes for AAPL, RPM, V"
    status: partial
    reason: "Capture and compare scripts exist and are importable, but no baseline JSON files have been written to .planning/baselines/. The directory contains only a .gitkeep. The SUMMARY explicitly defers this to 'after next full pipeline run'. The capability exists; the baselines do not."
    artifacts:
      - path: ".planning/baselines/"
        issue: "Empty — no *_reference.json files captured yet"
    missing:
      - "Run: uv run python scripts/capture_reference_snapshots.py after AAPL, RPM, V pipeline runs to populate baselines"
human_verification: []
---

# Phase 128: Infrastructure Foundation Verification Report

**Phase Goal:** The codebase is structurally ready for 10+ new sections — assembly module is split, golden baselines exist for regression detection, acquisition is incremental, raw filings are stored for hallucination detection, and the audit appendix is clean
**Verified:** 2026-03-22T23:15:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | html_context_assembly.py is no longer the real implementation — it is a thin re-export stub | ✓ VERIFIED | File is 8 lines, re-exports `build_html_context` and `_risk_class` from `assembly_registry.py` |
| 2 | Each new assembly module is under 500 lines | ✓ VERIFIED | assembly_registry.py=115, assembly_html_extras.py=186, assembly_signals.py=233, assembly_dossier.py=313 |
| 3 | build_html_context(state) is callable from the new registry location | ✓ VERIFIED | `from do_uw.stages.render.context_builders.assembly_registry import build_html_context` succeeds |
| 4 | Audit appendix has no duplicate signal entries across disposition audit and render audit tables | ✓ VERIFIED | `build_audit_context` accepts `render_audit` param and produces `audit_unified_summary` + `audit_dedup_savings` keys |
| 5 | Running the pipeline twice skips already-acquired data sources on the second run | ✓ VERIFIED | `orchestrator.py` calls `check_inventory(state.acquired_data)` at top of `run()`, copies complete sources, logs SKIP per source |
| 6 | Raw filing text (10-K, DEF 14A) appears as .txt files in output/TICKER/sources/filings/ after pipeline run | ✓ VERIFIED | `render/__init__.py` `_save_source_documents()` writes full_text to disk; `filing_fetcher.py` populates `full_text` in FilingDocument TypedDict |
| 7 | LLM-extracted revenue that differs from XBRL by >2x triggers a discrepancy warning | ✓ VERIFIED | `_HALLUCINATION_THRESHOLD_RATIO = 2.0` in reconciler; `reconcile_value()` produces `DiscrepancyWarning` with ratio, concept, period, resolution |
| 8 | Discrepancy warnings are persisted on state.extracted.financials.reconciliation_warnings and surface in the audit appendix | ✓ VERIFIED | `ExtractedFinancials.reconciliation_warnings` field exists; `extract/__init__.py` line 283 assigns from report; `assembly_signals.py` lines 168-171 call `build_reconciliation_audit_context` |
| 9 | A reference snapshot script captures JSON context + HTML section hashes for AAPL, RPM, V | ✓ VERIFIED (partial) | Scripts exist and import cleanly; `capture_snapshot()` and `compute_section_hashes()` implemented with SHA256 |
| 10 | Golden baselines actually exist in .planning/baselines/ for regression detection | ✗ FAILED | `.planning/baselines/` contains only `.gitkeep` — no `*_reference.json` files captured |
| 11 | A comparison script detects when section hashes change and reports which sections differ | ✓ VERIFIED | `compare_snapshots()` returns `context_keys` + `section_hashes` diffs; `sys.exit(1)` when changes detected |

**Score:** 10/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/html_context_assembly.py` | Thin re-export stub <20 lines | ✓ VERIFIED | 8 lines, re-exports only |
| `src/do_uw/stages/render/context_builders/assembly_registry.py` | Registry pattern + build_html_context | ✓ VERIFIED | 115 lines; `register_builder`, `_BUILDERS`, `build_html_context` all present |
| `src/do_uw/stages/render/context_builders/assembly_html_extras.py` | HTML-specific context builders | ✓ VERIFIED | 186 lines; `@register_builder` decorator at line 29 |
| `src/do_uw/stages/render/context_builders/assembly_signals.py` | Signal results, coverage, footnotes | ✓ VERIFIED | 233 lines; `@register_builder` at line 137; wires reconciliation audit |
| `src/do_uw/stages/render/context_builders/assembly_dossier.py` | Dossier context builders | ✓ VERIFIED | 313 lines; `@register_builder` at line 20 |
| `src/do_uw/stages/acquire/inventory.py` | AcquisitionInventory + check_inventory | ✓ VERIFIED | `class AcquisitionInventory` at line 21, `def check_inventory` at line 36 |
| `tests/acquire/test_incremental_acquisition.py` | Tests for skip logic | ✓ VERIFIED | 14 tests; all pass |
| `tests/acquire/test_raw_filing_storage.py` | Tests for filing text storage | ✓ VERIFIED | 7 tests covering write, manifest, source_link, warning; all pass |
| `src/do_uw/stages/extract/xbrl_llm_reconciler.py` | DiscrepancyWarning + >2x flagging | ✓ VERIFIED | `DiscrepancyWarning` dataclass at line 32; `_HALLUCINATION_THRESHOLD_RATIO = 2.0` at line 28 |
| `src/do_uw/models/financials.py` | `reconciliation_warnings` field on ExtractedFinancials | ✓ VERIFIED | Line 440: `reconciliation_warnings: list[dict[str, Any]] = Field(...)` |
| `src/do_uw/stages/render/context_builders/audit.py` | `build_reconciliation_audit_context` + `audit_unified_summary` | ✓ VERIFIED | Both functions present; `build_reconciliation_audit_context` exported in `__all__` |
| `scripts/capture_reference_snapshots.py` | Capture script with SHA256 section hashing | ✓ VERIFIED | `capture_snapshot`, `compute_section_hashes` present; `hashlib.sha256` used |
| `scripts/compare_reference_snapshots.py` | Compare script with exit code 1 on change | ✓ VERIFIED | `compare_snapshots` present; `sys.exit(exit_code)` with `exit_code=1` on diffs |
| `.planning/baselines/` | Directory with captured reference JSONs | ✗ MISSING | Directory exists but contains only `.gitkeep` — no baseline JSON files |
| `tests/extract/test_xbrl_cross_validation.py` | 8 tests for >2x discrepancy flagging | ✓ VERIFIED | 8 tests; all pass |
| `tests/test_reference_snapshots.py` | Tests for snapshot capture/comparison | ✓ VERIFIED | 7 tests; all pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `html_renderer.py` | `html_context_assembly.py` stub | `import build_html_context` at line 49 | ✓ WIRED | Import present; stub delegates to assembly_registry |
| `assembly_registry.py` | `assembly_html_extras.py`, `assembly_signals.py`, `assembly_dossier.py` | `register_builder` decorator + import-triggered registration | ✓ WIRED | Lines 108-113 of registry import domain modules; `_BUILDERS` list populated at module load |
| `orchestrator.py` | `inventory.py` | `check_inventory(state.acquired_data)` at line 115 | ✓ WIRED | Import at line 38; `check_inventory` called in `run()`; `_copy_complete_sources` and `_log_inventory` helpers confirmed |
| `sec_client.py` / `filing_fetcher.py` | `state.acquired_data.filing_documents` | `FilingDocument` TypedDict with `full_text` field | ✓ WIRED | `filing_fetcher.py` populates `full_text`; orchestrator promotes `filing_documents` to dedicated field on `AcquiredData` |
| `render/__init__.py` | `output/TICKER/sources/filings/` | `_save_source_documents` writes `full_text` to `.txt` files | ✓ WIRED | Lines 142-156 write text; line 178 writes `source_link.json` |
| `xbrl_llm_reconciler.py` | `state.extracted.financials.reconciliation_warnings` | `extract/__init__.py` assigns `[dataclasses.asdict(w) for w in report.discrepancy_warnings]` | ✓ WIRED | Line 283 of `extract/__init__.py` confirmed |
| `state.extracted.financials.reconciliation_warnings` | `audit.py` `build_reconciliation_audit_context` | `assembly_signals.py` calls `build_reconciliation_audit_context(recon_warnings)` at lines 168-171 | ✓ WIRED | Full chain confirmed: reconciler → state → assembly_signals → audit context |
| `scripts/capture_reference_snapshots.py` | `.planning/baselines/` | Writes `{TICKER}_reference.json` per ticker | ✗ NOT WIRED (no baselines captured) | Scripts exist and run correctly but no baseline files produced yet |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| INFRA-01 | 128-01 | Assembly modules split, each <500 lines | ✓ SATISFIED | 4 modules: 115/186/233/313 lines; stub is 8 lines |
| INFRA-02 | 128-03 | Golden baselines captured for AAPL enabling before/after comparison | ✗ BLOCKED | Scripts implemented; `.planning/baselines/` is empty — no baselines captured |
| INFRA-03 | 128-02 | Inventory-based incremental acquisition skips already-fetched sources | ✓ SATISFIED | `check_inventory()` wired in orchestrator; 14 tests pass |
| INFRA-04 | 128-02 | Raw filing text stored in output/TICKER/sources/ | ✓ SATISFIED | `_save_source_documents` writes full_text + source_link.json; 7 tests pass |
| INFRA-05 | 128-03 | LLM financial numbers cross-validated against XBRL, >2x flagged | ✓ SATISFIED | `DiscrepancyWarning` dataclass; `_HALLUCINATION_THRESHOLD_RATIO = 2.0`; state persistence; audit wiring; 8 tests pass |
| INFRA-06 | 128-01 | Audit appendix deduplicated, overlapping sections consolidated | ✓ SATISFIED | `build_audit_context` merges disposition + render audit into `audit_unified_summary` with `audit_dedup_savings` count; 6 dedup tests pass |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | — | — | — | No TODO/FIXME/placeholder patterns, no stub returns, no orphaned modules |

### Test Results (All Phase 128 Tests)

```
tests/render/test_assembly_registry.py    14 passed in 0.59s
tests/render/test_audit_dedup.py          (included above)
tests/acquire/test_incremental_acquisition.py   }
tests/acquire/test_raw_filing_storage.py        } 36 passed in 9.26s
tests/extract/test_xbrl_cross_validation.py     }
tests/test_reference_snapshots.py               }
```

Total: **50 tests pass** with no failures across all Phase 128 test modules.

### Gaps Summary

One gap blocks full goal achievement:

**INFRA-02 — Golden baselines not captured.** The REQUIREMENTS.md says "System captures golden baseline output for AAPL before any rendering changes." The capture script (`scripts/capture_reference_snapshots.py`) is fully implemented, importable, and tested. However, no baseline JSON files exist in `.planning/baselines/`. The SUMMARY acknowledges this: "run `uv run python scripts/capture_reference_snapshots.py` after next full pipeline run to establish baselines." Until baselines are captured, the regression detection goal of Phase 128 cannot be exercised — there is nothing to compare against. AAPL output exists at `output/AAPL/` so baselines could be captured immediately.

**Fix:** Run `uv run python scripts/capture_reference_snapshots.py --tickers AAPL,RPM,V` (or at minimum AAPL) to populate `.planning/baselines/AAPL_reference.json`. This completes INFRA-02.

---

_Verified: 2026-03-22T23:15:00Z_
_Verifier: Claude (gsd-verifier)_
