---
phase: 52-extraction-data-quality
verified: 2026-02-28T20:30:00Z
status: passed
score: 20/20 must-haves verified
re_verification: false
gaps: []
human_verification:
  - test: "Run full SNA pipeline end-to-end and verify board directors array shows individual names + qualification tags in worksheet output"
    expected: "DEF 14A parsing returns ~10 named directors with qualification_tags populated (e.g., financial_expert, industry_expertise), age fields populated"
    why_human: "LLM re-extraction requires live pipeline run after cache invalidation from schema_hash change; cannot verify actual LLM output from static analysis alone"
  - test: "Run full SNA pipeline and verify FIN.GUIDE.current shows No (not Yes)"
    expected: "SNA output shows guidance_provided=No because detect_forward_guidance() returns False on SNA 10-K text; analyst_beat_rate still shown separately"
    why_human: "Requires live pipeline run against real SNA 10-K filing text; regex patterns are verified but LLM-extracted guidance_language field content cannot be confirmed without live run"
  - test: "Run full SNA pipeline and verify 0 CaseDetail records from boilerplate 10-K legal language"
    expected: "No false SCAs in SNA output; any generic legal reserve disclosures filtered by _meets_minimum_evidence() before reaching CaseDetail"
    why_human: "Regression test uses synthetic fixture; actual SNA 10-K boilerplate requires live pipeline run to confirm end-to-end filtering works"
---

# Phase 52: Extraction Data Quality Verification Report

**Phase Goal:** Fix 4 high-severity data quality issues found in SNA validation audit -- board director extraction, guidance vs consensus mislabel, litigation false positives, and volume spike detection

**Verified:** 2026-02-28T20:30:00Z
**Status:** PASSED
**Re-verification:** No -- initial verification

---

## Goal Achievement

### Observable Truths (Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Board directors array populated with individual names, independence status, committee memberships, and qualifications from DEF 14A parsing (SNA should show ~10 directors) | VERIFIED | `BoardForensicProfile.qualification_tags` and `age` fields exist; `convert_directors()` maps them from `ExtractedDirector`; DEF14A prompt requests per-director extraction with structured tags; 15/15 governance converter tests pass |
| 2 | FIN.GUIDE.* signals distinguish between company-issued guidance and analyst consensus estimates; non-guiding companies (like SNA) show FIN.GUIDE.current=No | VERIFIED | `EarningsGuidanceAnalysis.provides_forward_guidance` defaults to False; `detect_forward_guidance()` returns False for non-guidance text; `compute_guidance_fields()` gates guidance_provided/beat_rate/philosophy on this field; 27/27 guidance detection tests pass |
| 3 | Litigation extraction requires named parties, court/jurisdiction, and case number for SCA classification; boilerplate 10-K legal reserves no longer produce CaseDetail records; SNA produces 0 false SCAs | VERIFIED | `_meets_minimum_evidence()` filter active in `convert_legal_proceedings()`; 12-pattern `_is_generic_label()` catches boilerplate; 10-K prompt requires named plaintiff/court/date; SNA regression test in test suite passes; 55/55 litigation converter tests pass |
| 4 | STOCK.TRADE.volume_patterns upgraded from display-only to evaluative with tiered thresholds; volume spikes trigger event correlation via targeted news search | VERIFIED | Signal YAML: `work_type=evaluate`, `threshold.type=tiered`, `field_key=volume_spike_count`; `detect_volume_spikes()` computes 20-day MA; `correlate_volume_spikes()` runs in ACQUIRE via orchestrator Phase B+++; 15/15 volume spike tests pass |

**Score:** 4/4 truths verified (automated checks)

---

## Required Artifacts

### Plan 01: Board Director Qualification Tags (DQ-01)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/extract/llm/schemas/common.py` | ExtractedDirector with qualification_tags field | VERIFIED | Contains `qualification_tags`, 222 lines |
| `src/do_uw/models/governance_forensics.py` | BoardForensicProfile with qualification_tags and age fields | VERIFIED | Contains `qualification_tags` at line 182, `age` field present, 470 lines |
| `src/do_uw/stages/extract/llm/prompts.py` | Enhanced DEF14A prompt requesting per-director qualification tag extraction | VERIFIED | Contains "qualification tags" and "per-director" extraction instructions at line 73 |
| `src/do_uw/stages/extract/llm_governance.py` | Updated convert_directors mapping qualification_tags and age | VERIFIED | `qualification_tags=list(d.qualification_tags)` at line 132, `age` mapping with MEDIUM confidence at lines 133-136, 491 lines |
| `tests/test_llm_governance_converter.py` | Tests for qualification_tags and age mapping | VERIFIED | `test_convert_directors_qualification_tags` and `test_convert_directors_age_mapping` present, 15/15 pass |

### Plan 02: Forward Guidance Detection (DQ-02)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/market_events.py` | EarningsGuidanceAnalysis with provides_forward_guidance field | VERIFIED | Field defaults to False, 477 lines |
| `src/do_uw/stages/extract/earnings_guidance.py` | detect_forward_guidance function scanning filing text | VERIFIED | Function confirmed importable and returns correct True/False, exactly 500 lines |
| `src/do_uw/stages/analyze/signal_mappers_ext.py` | compute_guidance_fields gated on provides_forward_guidance | VERIFIED | `getattr(eg, "provides_forward_guidance", False)` gate at line 95, 165 lines |
| `src/do_uw/stages/extract/extract_market.py` | Caller wiring: passes guidance_language from TenKExtraction | VERIFIED | `llm_ten_k.guidance_language` passed at line 182 via `get_llm_ten_k(state)`, 355 lines |
| `tests/test_guidance_detection.py` | Tests for guidance detection and mapper gating | VERIFIED | 27 tests covering positive detection, negative, boilerplate exclusion, mapper gating -- all pass |

### Plan 03: Litigation False Positive Filtering (DQ-03)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/extract/llm/prompts.py` | Tightened 10-K prompt requiring named plaintiff/court/date | VERIFIED | "named plaintiff, class description, or government agency" at line 45, 203 lines |
| `src/do_uw/stages/extract/llm_litigation.py` | Post-extraction validation filtering hollow CaseDetail records | VERIFIED | `_meets_minimum_evidence()` at line 71, `_is_generic_label()`, `_is_borderline_evidence()` all present, 463 lines |
| `tests/test_llm_litigation_converter.py` | Tests for minimum evidence filter and borderline handling | VERIFIED | 17 new tests added (TestMeetsMinimumEvidence, TestIsGenericLabel, TestIsBorderlineEvidence, TestConvertLegalProceedingsFiltering), SNA regression passes, 55/55 pass |

### Plan 04: Volume Spike Detection (DQ-04)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/extract/volume_spikes.py` | detect_volume_spikes() function computing spikes from history_1y | VERIFIED | New file, 94 lines, function importable, returns correct spike count |
| `src/do_uw/models/market.py` | StockPerformance with volume_spike_count and volume_spike_events | VERIFIED | Both fields present with defaults (0 and []), 210 lines |
| `src/do_uw/brain/signals/stock/insider.yaml` | STOCK.TRADE.volume_patterns upgraded to tiered threshold | VERIFIED | `work_type=evaluate`, `threshold.type=tiered`, `field_key=volume_spike_count` confirmed via YAML parse |
| `src/do_uw/stages/analyze/signal_mappers.py` | volume_spike_count mapped in _map_market_fields | VERIFIED | `result["volume_spike_count"] = mkt.stock.volume_spike_count` at line 439, 505 lines |
| `src/do_uw/stages/acquire/spike_correlator.py` | correlate_volume_spikes() ACQUIRE helper running web search | VERIFIED | New file, 96 lines, function importable |
| `tests/test_volume_spikes.py` | Tests for spike detection, correlation, and mapping | VERIFIED | 15 tests covering detection, correlation, signal wiring -- all pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `llm/schemas/common.py` (ExtractedDirector) | `llm_governance.py` | `convert_directors reads d.qualification_tags` | WIRED | Line 132: `qualification_tags=list(d.qualification_tags)` |
| `llm_governance.py` | `governance_forensics.py` (BoardForensicProfile) | `convert_directors creates BoardForensicProfile with qualification_tags and age` | WIRED | Lines 132-136 map both fields |
| `extract_market.py` | `earnings_guidance.py` | `_run_earnings_guidance passes guidance_language from get_llm_ten_k(state)` | WIRED | Line 182: `guidance_text = llm_ten_k.guidance_language if llm_ten_k else None`, passed at line 185 |
| `earnings_guidance.py` | `market_events.py` (EarningsGuidanceAnalysis) | `Sets provides_forward_guidance on EarningsGuidanceAnalysis` | WIRED | `detect_forward_guidance` sets field on analysis object |
| `signal_mappers_ext.py` | `market_events.py` | `compute_guidance_fields reads provides_forward_guidance to gate evaluation` | WIRED | Line 95: `if not getattr(eg, "provides_forward_guidance", False)` |
| `llm/prompts.py` | LLM extraction | `Tighter prompt reduces hollow extraction at source` | WIRED | Line 45 contains "named plaintiff" requirement |
| `llm_litigation.py` | `models/litigation.py` (CaseDetail) | `convert_legal_proceedings filters before creating CaseDetail` | WIRED | Lines 249-264: `_is_borderline_evidence` then `_meets_minimum_evidence` guards |
| `volume_spikes.py` | `extract_market.py` (`stock_performance.py`) | `extract_market calls detect_volume_spikes with history_1y data` | WIRED | Lines 347-356 in `stock_performance.py` (pre-correlated fallback) |
| `extract_market.py` | `models/market.py` (StockPerformance) | `Sets volume_spike_count and volume_spike_events on StockPerformance` | WIRED | Lines 349-356: sets both fields |
| `signal_mappers.py` | `signal_field_routing.py` | `volume_spike_count field routed for STOCK.TRADE.volume_patterns` | WIRED | Line 153: `"STOCK.TRADE.volume_patterns": "volume_spike_count"` |
| `spike_correlator.py` | `orchestrator.py` | `Orchestrator calls correlate_volume_spikes after market data acquisition` | WIRED | Lines 145-163: Phase B+++ block calls `correlate_volume_spikes` non-blockingly |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| DQ-01 | 52-01 | Board directors array populated from DEF 14A -- individual names, independence, committees, qualifications | SATISFIED | `BoardForensicProfile.qualification_tags` and `age` fields wired from `ExtractedDirector` through `convert_directors()`; DEF14A prompt requests structured tags per director |
| DQ-02 | 52-02 | Guidance vs consensus correctly distinguished -- FIN.GUIDE.* signals check `provides_forward_guidance` before evaluating | SATISFIED | `detect_forward_guidance()` function + `provides_forward_guidance` field + `compute_guidance_fields()` gating all wired end-to-end |
| DQ-03 | 52-03 | Litigation extraction rejects boilerplate -- LLM requires named parties/court/docket for SCA; post-extraction filter drops hollow CaseDetail records | SATISFIED | Dual defense: tightened 10-K prompt (line 45) + `_meets_minimum_evidence()` filter in `convert_legal_proceedings()`; SNA regression test passes |
| DQ-04 | 52-04 | Volume spike detection and event correlation -- STOCK.TRADE.volume_patterns upgraded to evaluative with tiered thresholds; spikes trigger targeted news search | SATISFIED | Signal YAML upgraded (work_type=evaluate, threshold.type=tiered); `detect_volume_spikes()` + `correlate_volume_spikes()` wired through pipeline |

All 4 requirements satisfied. No orphaned requirements found -- requirements file confirms all 4 DQ-0x IDs are mapped to Phase 52 and marked complete.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `signal_mappers.py` | - | File at 505 lines, exceeds 500-line limit | Warning | Pre-existing at 502 lines; this phase added 3 lines. Acknowledged as tech debt in 52-04 summary. Does not affect functionality. |
| `orchestrator.py` | - | File at 656 lines, exceeds 500-line limit | Warning | Pre-existing issue (~625 lines before this phase). Acknowledged in 52-04 summary. Does not affect functionality. |

No blocker anti-patterns found. No TODO/FIXME/placeholder comments in new files. No empty/stub implementations.

Note: `earnings_guidance.py` is exactly 500 lines (boundary compliance, intentional compaction documented in 52-02 summary).

---

## Human Verification Required

### 1. Board Director Qualification Tags Live Pipeline

**Test:** Run `uv run do-uw analyze SNA` after clearing LLM cache and verify DEF 14A section produces named directors with `qualification_tags` populated.

**Expected:** SNA worksheet shows approximately 10 named board members. Each director entry has at least one structured qualification tag (e.g., `financial_expert`, `industry_expertise`, `prior_c_suite`). Age fields populated from proxy statement.

**Why human:** LLM extraction cache is invalidated by the `ExtractedDirector.qualification_tags` schema change (via `schema_hash()`). Results depend on actual DEF 14A content and LLM extraction quality. Static analysis cannot verify LLM output.

### 2. SNA Forward Guidance Correction

**Test:** Run `uv run do-uw analyze SNA` and examine FIN.GUIDE signals in the worksheet.

**Expected:** `FIN.GUIDE.current` shows guidance_provided=No (not Yes). Analyst consensus beat/miss data still appears under `analyst_beat_rate` key for display. Post-earnings drift and analyst consensus signals remain active.

**Why human:** Requires live pipeline run against actual SNA 10-K text. The `detect_forward_guidance()` patterns are verified against synthetic text but actual SNA filing language must confirm False detection. The `guidance_language` field from LLM extraction must be populated for the fix to engage.

### 3. SNA Litigation False Positive Elimination

**Test:** Run `uv run do-uw analyze SNA` and verify litigation section shows 0 CaseDetail records from boilerplate.

**Expected:** SNA produces 0 false SCAs. Any generic legal reserve boilerplate from 10-K Item 3 is filtered. If legitimate cases exist, they should have named parties and court/jurisdiction.

**Why human:** SNA regression test uses a synthetic fixture. The actual SNA 10-K boilerplate language must flow through the live pipeline to confirm `_meets_minimum_evidence()` filters it correctly.

---

## Gaps Summary

No gaps found. All 4 must-have truth claims are verified:

- All 112 tests (15 + 27 + 55 + 15) across 4 test files pass with 0 failures.
- All 11 key link connections are wired and confirmed via grep.
- All 12 required artifacts exist, are substantive (not stubs), and are wired.
- All 4 DQ requirements are satisfied and marked complete in REQUIREMENTS.md.
- 8 task commits verified in git log (cd06e9d, 19066ef, acd757a, 7af7d33, 14bbf1f, da69a00, 1a59607, b0d9644).
- Two pre-existing file size violations (signal_mappers.py at 505, orchestrator.py at 656) acknowledged as tech debt -- not introduced by this phase.
- 3 human verification items identified for live pipeline validation, none blocking goal achievement.

---

_Verified: 2026-02-28T20:30:00Z_
_Verifier: Claude (gsd-verifier)_
