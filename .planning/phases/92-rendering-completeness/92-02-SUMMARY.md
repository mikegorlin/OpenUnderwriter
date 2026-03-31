---
phase: 92-rendering-completeness
plan: 02
subsystem: rendering
tags: [health-check, yaml-config, qa-validation, business-profile, beautifulsoup, severity-reporting]

# Dependency graph
requires:
  - phase: 92-rendering-completeness
    plan: 01
    provides: "RenderAuditReport, compute_render_audit, render_audit.html.j2 template, render_audit context builder"
provides:
  - "health_check.py: LLM marker detection, zero placeholder detection (with allowlist), empty percentage detection"
  - "config/health_check.yaml: configurable LLM markers, zero-valid fields, empty value patterns"
  - "HealthIssue and HealthCheckReport dataclasses integrated into RenderAuditReport"
  - "Health Warnings section in Data Audit appendix with severity badges"
  - "qa_compare.py extended with business profile validation (revenue, customer, supplier, geographic)"
  - "Severity-based reporting ([HIGH]/[MEDIUM]/[LOW]) in QA compare output"
affects: [pipeline-output-quality, qa-workflow, future-extraction-signals]

# Tech tracking
tech-stack:
  added: []
  patterns: ["YAML-driven health check config with allowlists", "BeautifulSoup DOM walking for LLM marker detection", "Severity-based QA reporting"]

key-files:
  created:
    - src/do_uw/stages/render/health_check.py
    - config/health_check.yaml
    - tests/test_health_check.py
    - tests/test_qa_compare.py
  modified:
    - src/do_uw/stages/render/render_audit.py
    - src/do_uw/stages/render/context_builders/render_audit.py
    - src/do_uw/templates/html/appendices/render_audit.html.j2
    - scripts/qa_compare.py

key-decisions:
  - "BeautifulSoup for LLM marker detection (DOM-aware text extraction vs regex)"
  - "Row-level label scanning for empty percentage detection (catches ROE/ROA labels in first cell)"
  - "text_signals as proxy for business profile presence (no dedicated business_profile model exists)"
  - "Severity tags in QA compare: [HIGH] for render audit gaps, [MEDIUM] for business profile gaps"

patterns-established:
  - "Health check heuristics: config-driven, warnings-only, never blocking pipeline"
  - "QA severity tagging: [HIGH]/[MEDIUM]/[LOW] prefix in issue strings for categorization"

requirements-completed: [REND-03, REND-04]

# Metrics
duration: 7min
completed: 2026-03-09
---

# Phase 92 Plan 02: Health Check Heuristics and QA Business Profile Validation Summary

**Config-driven health check heuristics detecting LLM text leaks, zero placeholders, and empty values, plus cross-ticker QA validation of business profile data with severity-based reporting**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-09T18:25:32Z
- **Completed:** 2026-03-09T18:32:44Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Health check engine scans rendered HTML for three categories of quality issues: raw LLM text markers (BeautifulSoup DOM-aware), zero placeholders with context-aware allowlist, and empty/N/A values in numeric contexts
- Config-driven via config/health_check.yaml -- LLM markers, zero-valid fields, and empty value patterns all configurable without code changes
- Health warnings integrated into RenderAuditReport and surfaced in Data Audit appendix with color-coded severity badges (HIGH=red, MEDIUM=amber, LOW=gray)
- qa_compare.py extended with business profile validation using text_signals as proxy, plus render_audit presence checks
- Severity-based reporting in QA output: [HIGH] for missing render audit, [MEDIUM] for missing business profile data

## Task Commits

Each task was committed atomically:

1. **Task 1: Health check heuristics module + config + audit integration**
   - `6d39fdd` (test: add failing tests for health check heuristics)
   - `34089d5` (feat: health check module, config, audit integration, template)
2. **Task 2: Cross-ticker QA business profile validation**
   - `4ed1c18` (test: add failing tests for QA compare business profile)
   - `9149b87` (feat: extend qa_compare with business profile validation)

_Note: TDD tasks have test and implementation commits._

## Files Created/Modified
- `src/do_uw/stages/render/health_check.py` - Health check engine: HealthIssue, HealthCheckReport, detect_llm_markers, detect_zero_placeholders, detect_empty_percentages, run_health_checks
- `config/health_check.yaml` - Configurable LLM markers (10 patterns), zero-valid allowlist (11 fields), empty value patterns (4 patterns)
- `tests/test_health_check.py` - 14 unit tests covering all heuristics, config loading, aggregation, and integration
- `tests/test_qa_compare.py` - 5 unit tests for business profile validation and severity reporting
- `src/do_uw/stages/render/render_audit.py` - Extended RenderAuditReport with health_issues field, compute_render_audit runs health checks
- `src/do_uw/stages/render/context_builders/render_audit.py` - Extended to expose audit_health_issues and audit_health_count
- `src/do_uw/templates/html/appendices/render_audit.html.j2` - Added Health Warnings table section with severity badges
- `scripts/qa_compare.py` - Extended OutputProfile with business profile fields, compare_profiles with severity reporting

## Decisions Made
- Used BeautifulSoup for LLM marker detection rather than pure regex -- DOM-aware text extraction avoids matching inside HTML attributes/tags
- Row-level label scanning added for empty percentage detection -- catches "ROE" in first cell even when column header is generic "Value"
- text_signals used as proxy for business profile presence (no dedicated business_profile model exists in AnalysisState) -- revenue_quality_warn/segment_consistency for revenue segments, customer_concentration for customer, distribution_channels for supplier, geopolitical_exposure/fx_exposure for geographic
- Severity in QA compare uses string prefix tags ([HIGH]/[MEDIUM]/[LOW]) for simple grep-ability and backward-compatible formatting

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Row-level label scanning for empty percentage detection**
- **Found during:** Task 1 (empty percentage test)
- **Issue:** Test for "Not Available" in ROE row failed because column header "Value" didn't match percentage pattern, and has_numeric_headers was False
- **Fix:** Added row-level text scanning to check if any cell in the row has a percentage-like label (ROE, margin, ratio, etc.)
- **Files modified:** src/do_uw/stages/render/health_check.py
- **Verification:** All 14 health check tests pass

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor detection logic refinement. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 92 rendering completeness is now fully implemented (Plans 01 + 02)
- Health checks will surface warnings automatically in future pipeline runs
- QA compare now validates business profile data and render audit presence
- All outputs need pipeline re-runs to populate render_audit in state.json (existing outputs predate Plan 01)

## Self-Check: PASSED

All 4 created files verified on disk. All 4 task commits verified in git log. All 4 modified files verified on disk.
