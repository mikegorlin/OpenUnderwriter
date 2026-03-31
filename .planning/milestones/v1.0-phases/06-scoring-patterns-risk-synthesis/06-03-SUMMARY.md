---
phase: 06-scoring-patterns-risk-synthesis
plan: 03
subsystem: scoring
tags: [pattern-detection, allegation-mapping, risk-classification, composite-patterns, trigger-evaluation]

# Dependency graph
requires:
  - phase: 01-project-setup
    provides: patterns.json brain config, ConfigLoader
  - phase: 06-scoring-patterns-risk-synthesis
    plan: 02
    provides: FactorScore, PatternMatch, RedFlagResult models, scoring engine

provides:
  - detect_all_patterns() evaluating 19 composite patterns from patterns.json
  - map_allegations() mapping findings to 5 D&O allegation theories
  - classify_risk_type() classifying into 7 risk archetypes
  - is_regulated_industry() helper for SIC code ranges

affects:
  - phase: 06-scoring-patterns-risk-synthesis
    plan: 04
    impact: Pattern detection and allegation mapping feed into scoring calibration
  - phase: 07
    impact: Pattern results and risk classification feed into BENCHMARK stage

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Trigger condition evaluation with 8 operators (gt/lt/gte/lte/eq/ne/in/not_in)"
    - "Compound any_of triggers for multi-condition patterns"
    - "Severity computation: BASELINE/ELEVATED/HIGH/SEVERE from modifier points"
    - "Score impact capping: min(base + severity_points, max)"
    - "Theory-to-factor mapping for allegation exposure evaluation"
    - "Rule-based risk archetype classification with priority ordering"

# File tracking
key-files:
  created:
    - src/do_uw/stages/score/pattern_detection.py (324 lines)
    - src/do_uw/stages/score/pattern_fields.py (480 lines)
    - src/do_uw/stages/score/allegation_mapping.py (407 lines)
  modified:
    - src/do_uw/brain/patterns.json (added 2 patterns, updated counts)
    - tests/test_pattern_detection.py (64 tests)
    - tests/config/test_loader.py (updated pattern count 17->19)

# Decisions
decisions:
  - id: "06-03-01"
    decision: "Split pattern_detection.py into detection engine (324L) + field mapping (480L) for 500-line compliance"
    rationale: "Original file was 870 lines; field mapping is independent logic"
  - id: "06-03-02"
    decision: "Majority (>50%) trigger threshold for pattern detection"
    rationale: "Balanced between false positives (any single trigger) and false negatives (all triggers required)"
  - id: "06-03-03"
    decision: "Theory-to-factor mapping: A=[F1,F3,F5], B=[F2,F5], C=[F7,F8], D=[F9,F10], E=[F4]"
    rationale: "Maps directly to D&O allegation theory definitions from SECT7-05"
  - id: "06-03-04"
    decision: "Risk type classification priority: DISTRESSED > BINARY_EVENT > GROWTH_DARLING > GUIDANCE_DEPENDENT > REGULATORY_SENSITIVE > TRANSFORMATION > STABLE_MATURE"
    rationale: "Most severe/urgent archetypes take priority; multiple can trigger with secondary overlay"
  - id: "06-03-05"
    decision: "Renamed _check_regulatory_sensitive to _check_regulatory for line length"
    rationale: "Function name was causing line overflow; renamed for 500-line compliance"
  - id: "06-03-06"
    decision: "needs_calibration=True always for both allegation mapping and risk classification per SECT7-11"
    rationale: "All scoring outputs flagged for calibration review until validated against historical data"

# Metrics
metrics:
  duration: "12m 00s"
  completed: "2026-02-08"
---

# Phase 6 Plan 3: Pattern Detection & Allegation Mapping Summary

19-pattern composite detection engine with 5-theory allegation mapping and 7-archetype risk type classification, all rule-based

## What Was Built

### Task 1: Pattern Detection Engine (19 patterns)
- **pattern_detection.py** (324 lines): Core detection engine evaluating trigger conditions from patterns.json. Handles simple field/operator/value triggers and compound "any_of" sub-conditions. Computes severity from modifier points (BASELINE/ELEVATED/HIGH/SEVERE) and score impacts capped at configured maximums.
- **pattern_fields.py** (480 lines): Maps ~50 pattern field names to actual ExtractedData model paths. Covers stock, market, financial, governance, litigation, business, and forward-looking data domains. Returns None for unmapped/unavailable fields.
- **patterns.json updates**: Added AI_WASHING_RISK (business category, A+C theories) and EARNINGS_QUALITY_DETERIORATION (financial category, A theory). Updated total_patterns 17->19, category counts.

### Task 2: Allegation Mapping & Risk Type Classification
- **allegation_mapping.py** (407 lines): Two public APIs:
  - `map_allegations()`: Maps factor scores, patterns, and red flags to 5 allegation theories (A-E) with exposure levels. Theory A (Disclosure) maps to F1/F3/F5; Theory B (Guidance) to F2/F5; Theory C (Product/Ops) to F7/F8; Theory D (Governance) to F9/F10; Theory E (M&A) to F4. Detected patterns boost theories to HIGH exposure.
  - `classify_risk_type()`: Rule-based classification into 7 archetypes with priority ordering. DISTRESSED (going concern, Altman Z, F8>=6), BINARY_EVENT (Section 11 windows, Wells Notice), GROWTH_DARLING (>20% growth, <5yr public), GUIDANCE_DEPENDENT (F5>0, issues guidance), REGULATORY_SENSITIVE (regulated SIC, enforcement), TRANSFORMATION (new CEO <12mo, M&A), STABLE_MATURE (default).

## Test Coverage
- 64 tests in test_pattern_detection.py (42 pattern detection + 22 allegation/risk type)
- Full suite: 898 tests passing (up from 834)
- 0 pyright errors (strict mode)
- 0 ruff violations

## Decisions Made

1. Split pattern_detection.py into two files (detection engine + field mapping) for 500-line compliance
2. Majority (>50%) trigger threshold balances false positives vs false negatives
3. Theory-to-factor mapping follows SECT7-05 definitions directly
4. Risk type priority ordering puts most severe archetypes first with secondary overlay
5. needs_calibration=True always per SECT7-11

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] ConfigLoader test assertions updated for 19 patterns**
- **Found during:** Task 1 (but surfaced in Task 2 verification)
- **Issue:** tests/config/test_loader.py expected total_patterns=17 and patterns list length=17
- **Fix:** Updated both assertions to 19
- **Files modified:** tests/config/test_loader.py
- **Commit:** 0d99702

**2. [Rule 3 - Blocking] Unused `Any` import in allegation_mapping.py**
- **Found during:** Task 2 pyright check
- **Issue:** `from typing import Any` was imported but not used after code compaction
- **Fix:** Removed unused import
- **Files modified:** src/do_uw/stages/score/allegation_mapping.py
- **Commit:** 0d99702

**3. [Rule 1 - Bug] File over 500-line limit**
- **Found during:** Task 2 verification
- **Issue:** allegation_mapping.py was 570 lines on first draft
- **Fix:** Compacted docstrings, consolidated helpers, reduced blank lines to 407 lines
- **Files modified:** src/do_uw/stages/score/allegation_mapping.py
- **Commit:** 0d99702

## Next Phase Readiness

Phase 6 Plan 4 (scoring calibration) can proceed. Pattern detection, allegation mapping, and risk type classification are all operational and tested. The ScoreStage orchestrator in `__init__.py` will need to integrate these new modules (detect_all_patterns, map_allegations, classify_risk_type) into the scoring pipeline.
