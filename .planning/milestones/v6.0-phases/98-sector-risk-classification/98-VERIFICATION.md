---
phase: 98-sector-risk-classification
verified: 2026-03-10T16:30:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 98: Sector Risk Classification Verification Report

**Phase Goal:** Underwriters can see where this company sits in the D&O risk landscape for its sector -- all as brain signals with sector-relative evaluation
**Verified:** 2026-03-10T16:30:00Z
**Status:** PASSED
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Company's GICS sub-industry maps to a D&O hazard tier (Highest/High/Moderate/Lower) | VERIFIED | sector_hazard_tiers.yaml has 35+ sub-industries + 11 sector fallbacks; _compute_hazard_tier implements 3-level fallback; 5 passing tests |
| 2 | Company's sector has top 3 claim theories with provenance | VERIFIED | sector_claim_patterns.yaml covers 22 GICS industry groups with 3 theories each; provenance metadata from SCAC/Cornerstone/NERA; 3 passing tests |
| 3 | Company's sector has named regulators and regulatory intensity baseline | VERIFIED | sector_regulatory_overlay.yaml covers 22 groups with named regulators (EPA, FDA, etc.), intensity (High/Moderate/Low), and trends; distinct from ENVR-01 per metadata.note; 3 passing tests |
| 4 | Company's D&O risk dimensions can be compared against sector median benchmarks | VERIFIED | sector_peer_benchmarks.yaml covers all 11 GICS sectors with median/std_dev; _compute_peer_comparison flags outliers >1 std_dev; 4 passing tests |
| 5 | 4+ brain signals with acquisition, evaluation, and presentation blocks | VERIFIED | sector.yaml has 4 signals (SECT.hazard_tier, SECT.claim_patterns, SECT.regulatory_overlay, SECT.peer_comparison), all with schema_version: 3, acquisition/evaluation/presentation blocks |
| 6 | Hazard tier classifies as Highest/High/Moderate/Lower from filing rate reference data | VERIFIED | sector_hazard_tiers.yaml tier definitions match (>15/8-15/3-8/<3 per 1000); extraction returns tier string; test_gics_sub_industry_match confirms Biotechnology -> Highest |
| 7 | Claim patterns displays top 3 theories per sector | VERIFIED | 22 groups x 3 theories each; each theory has theory/frequency/legal_basis/description fields |
| 8 | Peer comparison evaluates company vs sector median with outlier thresholds | VERIFIED | _compute_peer_comparison uses abs(val - median)/std_dev > 1.0; test_outlier_detection confirms score=90 vs IT median=62 flagged; test_no_outliers confirms score=65 not flagged |
| 9 | All signals wired to output manifest and render through facet dispatch | VERIFIED | signal_mappers.py routes SECT.* prefix; output_manifest.yaml has sector_risk group; company_profile.py calls extract_sector_signals; company.py context builder formats; sector_risk.html.j2 renders |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/config/sector_hazard_tiers.yaml` | GICS sub-industry to hazard tier mapping | VERIFIED | 348 lines, 35+ sub-industries, 11 sector fallbacks, provenance from Cornerstone/NERA/SCAC |
| `src/do_uw/brain/config/sector_claim_patterns.yaml` | Top 3 claim theories per GICS group | VERIFIED | 430 lines, 22 industry groups, each with 3 theories including legal_basis and frequency |
| `src/do_uw/brain/config/sector_regulatory_overlay.yaml` | Named regulators per GICS group | VERIFIED | 187 lines, 22 groups with named regulators, intensity, and trends |
| `src/do_uw/brain/config/sector_peer_benchmarks.yaml` | Sector median D&O benchmarks | VERIFIED | 191 lines, all 11 GICS sectors with median/std_dev for 4 dimensions |
| `src/do_uw/brain/signals/biz/sector.yaml` | 4 SECT signal definitions v3 schema | VERIFIED | 343 lines, 4 signals, all with schema_version: 3, group: sector_risk |
| `src/do_uw/stages/extract/sector_classification.py` | Extraction module with extract_sector_signals | VERIFIED | 342 lines, exports extract_sector_signals, 4 _compute_* functions, 3-level GICS fallback |
| `tests/test_sector_signals.py` | Unit tests (min 80 lines) | VERIFIED | 243 lines, 18 tests across 5 test classes, all passing |
| `src/do_uw/stages/analyze/signal_mappers.py` | SECT.* prefix routing | VERIFIED | SECT prefix dispatches to _map_sector_fields at line 199 |
| `src/do_uw/brain/output_manifest.yaml` | sector_risk group in business_profile | VERIFIED | sector_risk group at lines 129-134, positioned after external_environment |
| `src/do_uw/stages/extract/company_profile.py` | extract_sector_signals call | VERIFIED | Lazy import + try/except at lines 131-139, stores to text_signals["sector_classification"] |
| `src/do_uw/stages/render/context_builders/company.py` | _build_sector_risk context builder | VERIFIED | Lines 351-430+, tier-to-color mapping, outlier level logic, wired into main build function |
| `src/do_uw/templates/html/sections/company/sector_risk.html.j2` | HTML template for 4 signals | VERIFIED | 85 lines, renders hazard tier badge, claim theories table, regulatory overlay, peer comparison with outlier flags |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| signal_mappers.py | sector_classification.py | lazy import in _map_sector_fields | WIRED | `from do_uw.stages.extract.sector_classification import extract_sector_signals` at line 798+ |
| company_profile.py | sector_classification.py | extract_sector_signals call | WIRED | Import + call at line 133, stores result in text_signals["sector_classification"] |
| context_builders/company.py | state.extracted.text_signals | reads sector_classification | WIRED | `state.extracted.text_signals.get("sector_classification", {})` at line 361 |
| sector_classification.py | sector_hazard_tiers.yaml | YAML lookup by GICS code | WIRED | `_get_hazard_tiers()` loads YAML, `_compute_hazard_tier` looks up by 8-digit then 2-digit code |
| sector_classification.py | state.company | GICS/SIC code access | WIRED | Reads gics_code and identity.sic_code with SourcedValue unwrapping |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| SECT-01 | 98-01, 98-02 | Sector hazard tier classification (Highest/High/Moderate/Lower) mapped from SIC with D&O filing rate data | SATISFIED | sector_hazard_tiers.yaml with filing rates per tier; SECT.hazard_tier signal with RED/YELLOW evaluation; extraction + rendering wired |
| SECT-02 | 98-01, 98-02 | Sector-specific claim patterns (top 3 claim theories per sector from SCAC/settlement data) | SATISFIED | sector_claim_patterns.yaml with 22 groups x 3 theories; SECT.claim_patterns signal with display_when: has_data; template renders mini-table |
| SECT-03 | 98-01, 98-02 | Sector regulatory intensity overlay (number + severity of active sector regulators) | SATISFIED | sector_regulatory_overlay.yaml with named regulators and intensity; SECT.regulatory_overlay signal with YELLOW threshold; template shows regulators + ENVR cross-reference |
| SECT-04 | 98-01, 98-02 | Sector peer risk comparison (company vs sector median across key D&O dimensions) | SATISFIED | sector_peer_benchmarks.yaml with 11 sectors x 4 dimensions; SECT.peer_comparison signal with RED (>=2 outliers) / YELLOW (>=1); template shows outlier badges |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None found | - | - | - | - |

No TODO, FIXME, PLACEHOLDER, or stub patterns detected in any phase 98 artifact.

### Human Verification Required

### 1. Visual Rendering of Sector Risk Section

**Test:** Run `underwrite V --fresh` or load an existing state.json and re-render HTML. Open worksheet and scroll to Business Profile > Sector Risk Classification.
**Expected:** Hazard tier badge shows color-coded pill (red for Highest, amber for High, blue for Moderate, green for Lower). Claim theories render as a clean mini-table with legal basis column. Regulatory overlay shows named regulators with intensity badge. Peer comparison shows dimension values with outlier flags where applicable.
**Why human:** Visual appearance, CSS class rendering, and layout density cannot be verified programmatically.

### 2. GICS Code Coverage for Common Tickers

**Test:** Run pipeline for tickers across different sectors (e.g., AAPL=IT, V=Financials, RPM=Materials, PFE=Healthcare) and check sector risk section populates correctly for each.
**Expected:** Each company gets sector-appropriate hazard tier, claim theories, regulators, and peer benchmarks.
**Why human:** Verifying that the GICS->sector mapping produces sensible results for real companies requires domain knowledge.

### Gaps Summary

No gaps found. All 9 observable truths verified. All 12 artifacts exist, are substantive (well beyond stub thresholds), and are fully wired. All 5 key links confirmed. All 4 requirements (SECT-01 through SECT-04) satisfied with implementation evidence. 18 tests passing. No anti-patterns detected. 7 commits documented and verified in git history.

---

_Verified: 2026-03-10T16:30:00Z_
_Verifier: Claude (gsd-verifier)_
