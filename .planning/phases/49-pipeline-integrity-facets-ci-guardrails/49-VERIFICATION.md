---
phase: 49-pipeline-integrity-facets-ci-guardrails
verified: 2026-02-26T21:30:00Z
status: gaps_found
score: 8/9 must-haves verified
gaps:
  - truth: "HTML rendering is driven by facet definitions controlling section organization (not only hardcoded prefix mappings)"
    status: partial
    reason: "FACET-03 requirement states 'facets control section organization and signal grouping' but implementation uses hardcoded _PREFIX_DISPLAY dict for section assignment; facets added as parallel metadata only. Plan 04 explicitly deferred full migration 'per user decision' — the plan's must_have was satisfied ('references facet metadata') but the REQUIREMENTS.md wording ('facets control section organization') was not fully achieved."
    artifacts:
      - path: "src/do_uw/stages/render/html_signals.py"
        issue: "_PREFIX_DISPLAY still controls section assignment; _lookup_facet_metadata adds facet_id/facet_name as additive metadata but does not drive section grouping"
    missing:
      - "Either update FACET-03 requirement status to partial/deferred in REQUIREMENTS.md, or migrate _group_signals_by_section to use facet definitions as the primary section driver instead of _PREFIX_DISPLAY"
---

# Phase 49: Pipeline Integrity, Facets & CI Guardrails — Verification Report

**Phase Goal:** Pipeline integrity, facets, and CI guardrails — rename check->signal nomenclature, add facet metadata to all signals, fix SKIPPED DEF14A signals, build trace/render-audit CLI commands, write CI contract tests.
**Verified:** 2026-02-26T21:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | 'check' terminology does not appear in signal-related identifiers in src/ | VERIFIED | 37 nomenclature lint tests all pass; `grep -r "BrainCheckEntry\|CheckResult\|check_engine\|brain/checks/"` returns 0 matches in src/ |
| 2 | brain/signals/ directory exists with all 400 signal YAML entries (brain/checks/ removed) | VERIFIED | `ls src/do_uw/brain/signals/` shows 8 subdirs; `ls src/do_uw/brain/checks/` returns "does not exist" |
| 3 | BrainSignalEntry is the schema class name; SignalResult is the result class name | VERIFIED | Both classes confirmed in brain_signal_schema.py and signal_results.py; imports resolve cleanly |
| 4 | Every ACTIVE signal has a facet field and complete display spec | VERIFIED | Programmatic check: 400/400 signals have facet, 0 missing display |
| 5 | 8 facet definition files exist covering all signal domains; all facet signal IDs valid | VERIFIED | 9 files in brain/facets/ (8 domain + red_flags); 400/400 signals in exactly one facet, zero duplicates, zero unknown IDs |
| 6 | Population B DEF14A signals triaged — INACTIVE marked, viable signals wired through governance mapper | VERIFIED | 20 GOV signals INACTIVE in YAML; board_attendance, board_diversity, clawback_policy, poison_pill, supermajority, forum_selection all mapped in signal_mappers_sections.py |
| 7 | brain trace and brain render-audit CLI commands work | VERIFIED | `do-uw brain trace GOV.BOARD.independence --blueprint` shows 5-stage pipeline journey; invalid ID exits with error; `do-uw brain render-audit AAPL` shows per-facet coverage (e.g., 53/85 for Governance) |
| 8 | CI contract tests enforce brain contract | VERIFIED | 10/10 test_brain_contract.py tests pass; 37/37 test_signal_nomenclature.py tests pass |
| 9 | HTML rendering is driven by facet definitions controlling section organization | PARTIAL | Facets added as parallel metadata (facet_id, facet_name on each signal); section assignment still uses hardcoded _PREFIX_DISPLAY dict — facets do not control section organization as required by FACET-03 |

**Score:** 8/9 truths verified

---

### Required Artifacts (All Plans)

| Artifact | Provides | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/brain_signal_schema.py` | BrainSignalEntry, BrainSignalThreshold, DisplaySpec schemas | VERIFIED | 97 lines; BrainSignalEntry at line 97, facet field at line 150 |
| `src/do_uw/brain/brain_build_signals.py` | YAML-to-DuckDB build pipeline for signals | VERIFIED | Substantive; respects YAML lifecycle_state field |
| `src/do_uw/stages/analyze/signal_engine.py` | Signal evaluation dispatch | VERIFIED | Imports SignalResult from signal_results; evaluate_signal defined |
| `src/do_uw/stages/analyze/signal_results.py` | SignalResult and SignalStatus classes | VERIFIED | SignalStatus at line 33, SignalResult at line 121 |
| `src/do_uw/brain/signals/` | 400 signal YAML definitions (8 subdirs) | VERIFIED | biz, exec, fin, fwrd, gov, lit, nlp, stock |
| `src/do_uw/brain/facets/business_profile.yaml` | Facet definition for BIZ domain | VERIFIED | Exists with 43 signals |
| `src/do_uw/brain/facets/financial_health.yaml` | Facet definition for FIN domain | VERIFIED | Exists with 58 signals |
| `src/do_uw/brain/facets/governance.yaml` | Facet definition for GOV domain | VERIFIED | Rebuilt from 12 to 85 signals |
| `src/do_uw/brain/facets/litigation.yaml` | Facet definition for LIT domain | VERIFIED | Exists with 65 signals |
| `src/do_uw/brain/facets/market_activity.yaml` | Facet definition for STOCK domain | VERIFIED | Exists with 35 signals |
| `src/do_uw/brain/facets/executive_risk.yaml` | Facet definition for EXEC domain | VERIFIED | Exists with 20 signals |
| `src/do_uw/brain/facets/forward_looking.yaml` | Facet definition for FWRD domain | VERIFIED | Exists with 79 signals |
| `src/do_uw/brain/facets/filing_analysis.yaml` | Facet definition for NLP domain | VERIFIED | Exists with 15 signals |
| `src/do_uw/stages/analyze/signal_mappers_sections.py` | map_governance_fields() with DEF14A signal mappings | VERIFIED | board_attendance, board_diversity, clawback_policy, poison_pill, supermajority_required, forum_selection_clause all present |
| `src/do_uw/stages/analyze/signal_field_routing.py` | FIELD_FOR_SIGNAL with new DEF14A routing | VERIFIED | GOV.BOARD.diversity -> "board_diversity", GOV.BOARD.attendance -> "board_attendance" |
| `src/do_uw/brain/signals/gov/*.yaml` | GOV signals with INACTIVE lifecycle_state | VERIFIED | 20 INACTIVE signals confirmed across board.yaml, effect.yaml, insider.yaml, pay.yaml, rights.yaml |
| `src/do_uw/cli_brain_trace.py` | brain trace + render-audit commands | VERIFIED | 494 lines; trace at line 309, render-audit at line 387; both functional |
| `src/do_uw/cli_brain.py` | Import registration for cli_brain_trace | VERIFIED | Line 426: `import do_uw.cli_brain_trace as _cli_brain_trace` |
| `src/do_uw/stages/render/html_signals.py` | _PREFIX_TO_FACET + facet metadata in grouping | PARTIAL | _PREFIX_TO_FACET and _lookup_facet_metadata() present and wired; facet_id/facet_name added to signal dicts — BUT section assignment still prefix-driven, not facet-driven |
| `tests/brain/test_brain_contract.py` | CI brain contract tests (10 tests) | VERIFIED | All 10 tests pass: data routes, thresholds, v6_subsection_ids, scoring linkage, facet, display, facet integrity, SKIPPED threshold |
| `tests/brain/test_signal_nomenclature.py` | CI nomenclature lint guard (37 tests) | VERIFIED | All 37 tests pass: 17 forbidden patterns x 2 dirs + 3 existence checks |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/do_uw/cli.py` | `src/do_uw/brain/brain_build_signals.py` | `brain_signals` table check | VERIFIED | Line 67: `"SELECT COUNT(*) FROM brain_signals"` |
| `src/do_uw/stages/analyze/signal_engine.py` | `src/do_uw/stages/analyze/signal_results.py` | SignalResult import | VERIFIED | Line 29: `from do_uw.stages.analyze.signal_results import DataStatus, SignalResult, SignalStatus` |
| `src/do_uw/models/state.py` | `src/do_uw/stages/analyze/signal_results.py` | signal_results dict on AnalysisResults | VERIFIED | Line 194: `signal_results: dict[str, Any]` |
| `src/do_uw/brain/signals/**/*.yaml` | `src/do_uw/brain/facets/*.yaml` | facet field matches facet ID | VERIFIED | 400/400 signals have valid facet ID; cross-validation passes |
| `src/do_uw/brain/facets/*.yaml` | `src/do_uw/brain/signals/**/*.yaml` | signals list references real signal IDs | VERIFIED | test_facet_signal_ids_are_valid passes; zero unknown IDs |
| `src/do_uw/cli_brain_trace.py` | `src/do_uw/brain/signals/**/*.yaml` | YAML load for trace definition stage | VERIFIED | yaml.safe_load pattern present; blueprint mode confirmed working |
| `src/do_uw/cli_brain_trace.py` | `src/do_uw/brain/facets/*.yaml` | load_all_facets for render-audit | VERIFIED | render-audit AAPL shows per-facet declared vs rendered counts |
| `tests/brain/test_brain_contract.py` | `src/do_uw/brain/signals/**/*.yaml` | rglob("*.yaml") loads all signals | VERIFIED | _load_all_signals() at line 24; all 10 tests green |
| `tests/brain/test_signal_nomenclature.py` | `src/do_uw/` | grep for forbidden check patterns | VERIFIED | subprocess grep; all 37 tests green |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| NOM-01 | 49-01 | "check" renamed to "signal" throughout codebase | SATISFIED | 37 nomenclature lint tests green; 0 forbidden patterns in src/; brain/checks/ gone |
| INT-01 | 49-03 | SKIPPED gap closed — Population B DEF14A signals evaluate instead of SKIP | SATISFIED | 20 INACTIVE signals removed from SKIPPED count; anti-takeover fields wired; SKIPPED reduced from 68 to ~48 (12 remain correctly SKIPPED due to LLM extraction quality) |
| INT-02 | 49-04 | `do-uw brain trace` shows full data route | SATISFIED | Command works in both --blueprint and live modes; 5 stages shown; invalid ID exits with error |
| INT-03 | 49-04 | `do-uw brain render-audit` reports declared vs populated per facet | SATISFIED | AAPL: 325/400 = 81% coverage per facet; per-facet declared vs rendered counts shown |
| FACET-01 | 49-02 | Facet definitions exist for all signal domains | SATISFIED | 9 facet files (8 domain + red_flags) in brain/facets/ |
| FACET-02 | 49-02 | Every signal has facet field and complete display spec | SATISFIED | 400/400 signals have facet; 400/400 have display spec with value_format and source_type |
| FACET-03 | 49-04 | HTML rendering driven by facet definitions, not hardcoded prefix mappings | PARTIAL | Facets added as parallel metadata (facet_id/facet_name on each signal dict) but section assignment still controlled by hardcoded _PREFIX_DISPLAY — requirement says "facets control section organization" which is not the case |
| FACET-04 | 49-02 | All facet signal IDs correct — declared signals map to real signals | SATISFIED | test_facet_signal_ids_are_valid: 9 facet files, 400 signals, zero unknown IDs, zero duplicates |
| QA-03 | 49-05 | CI tests enforce brain contract | SATISFIED | 10 contract tests + 37 nomenclature tests; all pass green |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/do_uw/brain/brain_build_signals.py` | 1 | Docstring still says "from checks/**/*.yaml" | Info | Cosmetic only — no functional impact |
| `src/do_uw/stages/render/html_signals.py` | 1 | Docstring says "Check result processing utilities" (old name) | Info | Cosmetic only |
| `src/do_uw/stages/render/html_signals.py` | 24 | Comment says "Phase 49 will migrate rendering to Facet-driven" — Phase 49 is complete but migration was deferred | Warning | Misleading comment; migration was explicitly deferred by user decision but comment reads as future-tense plan |

No blockers found. The cosmetic issues are documentation drift, not functional problems.

---

### Human Verification Required

#### 1. Full Pipeline Run — SKIPPED Count Validation

**Test:** Run `do-uw analyze AAPL` end-to-end and check SKIPPED count in output summary.
**Expected:** SKIPPED count ~48 (down from 68 pre-Phase 49), 20 fewer due to INACTIVE exclusion.
**Why human:** Full pipeline run requires live data acquisition; CI tests use static YAML checks not live pipeline results.

#### 2. brain trace Live Mode

**Test:** After running `do-uw analyze AAPL`, run `do-uw brain trace GOV.BOARD.independence` (without --blueprint).
**Expected:** Shows actual extracted value, mapping result, evaluation status with TRIGGERED/CLEAR/SKIPPED marker, evidence.
**Why human:** Live mode reads state.json from an analysis run; no state.json for independence signal verified in automated testing.

#### 3. FACET-03 Scope Clarification

**Test:** Review `src/do_uw/stages/render/html_signals.py` lines 37-59 and the comment at line 24.
**Expected:** User decision — either (a) accept current implementation as sufficient for FACET-03, or (b) file a new requirement to fully migrate section grouping to facet-driven.
**Why human:** The plan explicitly deferred full migration "per user decision" — the user needs to decide if the current partial implementation satisfies their intent for FACET-03.

---

### Gaps Summary

One gap blocking full goal achievement:

**FACET-03 Partial Implementation:** The REQUIREMENTS.md text for FACET-03 says "facets control section organization and signal grouping" and is marked [x] Complete. However, the actual implementation in `html_signals.py` keeps `_PREFIX_DISPLAY` as the authoritative section organizer and adds facets only as parallel metadata (`facet_id`, `facet_name` on each signal dict). The Plan 04 context explicitly states this was a "user decision" to defer full migration. This creates a discrepancy between the requirement being marked Complete and the implementation not fully satisfying "facets control section organization."

The gap is small in functional impact (the metadata is there, accessible by templates) but material if the requirement language is taken literally. The deferred-items.md does not mention this as a deferred item — it only covers test failures and LLM extraction quality.

**Recommended resolution:** Either (a) update REQUIREMENTS.md to note FACET-03 is partially satisfied (metadata added, section control deferred to v1.3+), or (b) add an entry to deferred-items.md explicitly flagging the full section-control migration as deferred.

---

## Summary: What Was Verified

Phase 49 delivered substantial, real work across all 5 plans:

- **NOM-01 (Plan 01):** Complete big-bang rename across 268 files; brain/checks/ gone; all signal_*.py files present; CI nomenclature lint guard enforces this going forward.
- **INT-01 (Plan 03):** 20 GOV signals marked INACTIVE; 6 anti-takeover DEF14A fields wired through governance mapper; SKIPPED count reduced.
- **INT-02 + INT-03 (Plan 04):** brain trace (blueprint + live) and brain render-audit working; both commands handle error cases.
- **FACET-01 + FACET-02 + FACET-04 (Plan 02):** 9 facet files; 400/400 signals have facet + display metadata; bidirectional integrity validated.
- **FACET-03 (Plan 04):** Partial — facet metadata added as parallel classification, but section organization not migrated to facet-driven.
- **QA-03 (Plan 05):** 10 + 37 = 47 CI tests all green; brain contract locked down.

All CI tests pass. Imports clean. Brain build succeeds with 400 signals.

---

_Verified: 2026-02-26T21:30:00Z_
_Verifier: Claude (gsd-verifier)_
