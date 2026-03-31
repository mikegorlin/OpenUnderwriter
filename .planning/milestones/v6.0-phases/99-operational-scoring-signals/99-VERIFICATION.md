---
phase: 99-operational-scoring-signals
verified: 2026-03-10T17:15:00Z
status: passed
score: 4/4 must-haves verified
re_verification: false
---

# Phase 99: Operational Scoring & Signals Verification Report

**Phase Goal:** Operational complexity has a unified composite score aggregating all operational signals, and existing indicators are wired into the brain framework
**Verified:** 2026-03-10T17:15:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | BIZ.OPS.* signals evaluate through the V2 signal engine (not SKIPPED) | VERIFIED | `_map_ops_fields` routes BIZ.OPS.* prefix (signal_mappers.py:183) before generic BIZ.* fallback; field routing entries for all 4 signals (signal_field_routing.py:122-125) |
| 2 | Operational complexity composite score aggregates subsidiary, workforce, segment, and VIE/dual-class indicators | VERIFIED | `_map_ops_fields` computes 7-dimension score (signal_mappers.py:843-863): jurisdiction(max 5) + high_reg(max 3) + segments(max 3) + intl_pct(max 3) + VIE(2) + dual_class(2) + union(2) = max 20 |
| 3 | Composite signal fires at defined thresholds (>15 RED, >8 YELLOW) | VERIFIED | operations.yaml thresholds at lines 378-381; context builder maps >=15 HIGH/red, >=8 MODERATE/amber (company.py:580-588); 6 tests cover all threshold levels |
| 4 | All signals wired to output manifest and render through facet dispatch | VERIFIED | `_build_operational_complexity` wired into `extract_company()` (company.py:797); template at `operational_complexity.html.j2` renders composite badge, KV table, and indicator badges (69 lines, not a stub) |

**Score:** 4/4 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/signals/biz/operations.yaml` | BIZ.OPS.complexity_score composite signal | VERIFIED | 4 signals (3 existing + 1 composite), 412 lines, full v3 schema with evaluation thresholds and presentation blocks |
| `src/do_uw/stages/analyze/signal_mappers.py` | BIZ.OPS.* signal mapper routing | VERIFIED | `_map_ops_fields` function at line 746, routed at line 183-184 before generic BIZ.* |
| `src/do_uw/stages/analyze/signal_field_routing.py` | BIZ.OPS field routing entries | VERIFIED | 4 entries at lines 122-125 mapping to jurisdiction_count, international_pct, geographic_concentration_score, ops_complexity_score |
| `src/do_uw/stages/render/context_builders/company.py` | _build_operational_complexity context builder | VERIFIED | Function at line 501, wired into extract_company at line 797, returns (ops_dict, has_data) with 13 context keys |
| `src/do_uw/templates/html/sections/company/operational_complexity.html.j2` | Operational complexity dashboard template | VERIFIED | 69 lines, composite score badge with color coding, KV table with 7 data rows, indicator badges section |
| `src/do_uw/brain/field_registry.yaml` | ops_complexity_score COMPUTED entry | VERIFIED | Entry at line 155 with function compute_ops_complexity_score and 3 args |
| `src/do_uw/brain/field_registry_functions.py` | compute_ops_complexity_score function | VERIFIED | Function at line 466, registered in COMPUTED_FUNCTIONS dict at line 541 |
| `tests/test_ops_signals.py` | Test suite | VERIFIED | 16 tests across 4 classes: YAML validation, composite computation, context builder, field routing -- all pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| signal_mappers.py | operational_extraction.py | `_map_ops_fields` state proxy pattern | WIRED | Lazy imports 3 extraction functions (line 759-763), builds _StateProxy, calls all 3 extractors |
| context_builders/company.py | operational_complexity.html.j2 | context dict via Jinja2 | WIRED | `_build_operational_complexity` returns dict with keys matching template variables; `extract_company` passes as `operational_complexity_signals` (line 835) |
| signal_mappers.py dispatch | _map_ops_fields | `prefix2 == "BIZ.OPS"` check | WIRED | Routing at line 183 before generic `prefix == "BIZ"` at line 185 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| OPS-01 | 99-01-PLAN | Operational complexity indicators rendered (VIEs, dual-class, special structures) wired to brain signals with presentation blocks | SATISFIED | 4 indicator badges in template (VIE/SPE, Dual-Class, Holding Depth, OBS Exposure); context builder reads from text_signals and governance data |
| OPS-05 | 99-01-PLAN | Unified operational complexity score computed (subsidiaries x jurisdictions x segments x workforce) as composite brain signal | SATISFIED | BIZ.OPS.complexity_score signal with 7-dimension weighted formula (0-20 scale); both signal mapper and context builder compute it |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | No TODO, FIXME, PLACEHOLDER, or stub patterns found in any modified files |

### Human Verification Required

### 1. Operational Complexity Rendering

**Test:** Run pipeline for a complex company (e.g., RPM with many subsidiaries) and inspect the operational complexity section in HTML output
**Expected:** Composite score badge shows with correct color, KV table populated with real data, indicator badges show present/absent correctly
**Why human:** Visual layout quality, data accuracy against known company facts

### 2. Threshold Calibration

**Test:** Compare composite scores across 2-3 tickers of varying complexity
**Expected:** Scores differentiate meaningfully (e.g., multinational conglomerate > small domestic company)
**Why human:** Score reasonableness requires domain judgment

---

_Verified: 2026-03-10T17:15:00Z_
_Verifier: Claude (gsd-verifier)_
