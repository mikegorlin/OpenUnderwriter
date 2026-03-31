---
phase: 120-integration-visual-verification
plan: 03
subsystem: render, validation
tags: [qa-compare, visual-verification, cross-ticker, gold-standard, narrative-quality]

# Dependency graph
requires:
  - phase: 119.1-narrative-quality-overhaul
    provides: Company-specific narrative generators, signal-specific D&O commentary
  - phase: 120-01
    provides: CI gate for do_context coverage
  - phase: 120-02
    provides: Structural tests + performance budget
provides:
  - Cross-ticker QA comparison with v8.0 section awareness
  - Human-verified visual confirmation of output quality across 3 tickers
  - Fresh post-narrative-overhaul pipeline outputs for HNGE, AAPL, ANGI
affects: [v8.0-milestone-closure]

# Tech tracking
tech-stack:
  added: []
  patterns: [cross-ticker-v8-section-checks]

key-files:
  created: []
  modified:
    - scripts/qa_compare.py
    - src/do_uw/stages/render/context_builders/_narrative_generators.py

key-decisions:
  - "Scoring calibration flagged: AAPL and ANGI both WALK despite opposite risk profiles -- known issue for future milestone"
  - "PDF generation skipped (Playwright chromium not installed) -- not blocking for v8.0"

patterns-established:
  - "qa_compare.py v8.0 section inventory: intelligence-dossier, forward-looking, alternative-data, adversarial-critique"

requirements-completed: []

# Metrics
duration: 45min
completed: 2026-03-21
---

# Phase 120 Plan 03: Cross-Ticker QA + Visual Verification Summary

**Fresh pipeline runs on HNGE/AAPL/ANGI with post-narrative-overhaul code; human visual review confirmed narrative quality improvement across all 3 tickers**

## Performance

- **Duration:** ~45 min (pipeline runs + review)
- **Started:** 2026-03-21T03:54:57Z
- **Completed:** 2026-03-21T06:25:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- All 3 pipelines re-run with --fresh, producing HTML outputs reflecting Phase 119.1 narrative quality overhaul
- Human visual review approved: narrative quality confirmed as "better" with company-specific D&O commentary
- Two rendering bugs introduced by Phase 119.1 auto-fixed (KeyFinding slicing, SourcedValue join)
- Cross-ticker QA comparison updated with v8.0 section awareness (4 new section IDs)

## Pipeline Results

| Ticker | HTML | Word | Charts | QA Status | Time |
|--------|------|------|--------|-----------|------|
| HNGE | 7.5MB | 3.2MB | 14 | 15 pass, 3 warn, 5 fail | ~8 min |
| AAPL | 7.5MB | 3.1MB | 15 | 17 pass, 3 warn, 3 fail | ~16 min |
| ANGI | 9.2MB | 3.4MB | 14 | 17 pass, 3 warn, 3 fail | ~9 min |

QA failures: PDF missing (Playwright chromium not installed), brain field coverage low (known gap from SKIPPED signals). All other checks pass.

## Known Issue

**Scoring calibration flagged:** AAPL and ANGI both WALK despite opposite risk profiles. AAPL is a clean mega-cap; ANGI is a complex, declining company. The scoring system does not yet differentiate them adequately. This is a known issue for a future milestone.

## Task Commits

Each task was committed atomically:

1. **Task 1: Update qa_compare.py for v8.0 sections** - `a1b54267` (feat) -- completed in prior run
2. **Bug fix: KeyFinding object slicing** - `7958d891` (fix)
3. **Bug fix: SourcedValue in SCA case names** - `bbd9a04c` (fix)
4. **Task 2: Visual review checkpoint** - approved by human reviewer

**Plan metadata:** (this commit)

## Files Created/Modified
- `scripts/qa_compare.py` - Added v8.0 section IDs (intelligence-dossier, forward-looking, alternative-data, adversarial-critique) and feature checks
- `src/do_uw/stages/render/context_builders/_narrative_generators.py` - Fixed KeyFinding slicing bug and SourcedValue join bug

## Decisions Made
- Scoring calibration flagged as known issue for future milestone (AAPL and ANGI both WALK)
- PDF generation not blocking -- Playwright chromium binary missing from environment

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] KeyFinding object slicing in negative findings narrative generator**
- **Found during:** Pipeline re-run (HNGE)
- **Issue:** `_gen_negative_findings_implication` tried to slice `negs[0][:80]` but `negs` is `list[KeyFinding]`, not `list[str]`. Crash prevented HTML render.
- **Fix:** Extract `evidence_narrative` attribute before slicing
- **Files modified:** src/do_uw/stages/render/context_builders/_narrative_generators.py
- **Verification:** HNGE pipeline produces 7.5MB HTML after fix
- **Committed in:** 7958d891

**2. [Rule 1 - Bug] SourcedValue in SCA case names before string join**
- **Found during:** Pipeline re-run (AAPL)
- **Issue:** `case_name` field is `SourcedValue[str]`, not `str`. `", ".join(names)` fails with `TypeError: sequence item 0: expected str instance, SourcedValue[str] found`
- **Fix:** Unwrap via `_sv()` helper before joining
- **Files modified:** src/do_uw/stages/render/context_builders/_narrative_generators.py
- **Verification:** AAPL pipeline produces 7.5MB HTML after fix
- **Committed in:** bbd9a04c

---

**Total deviations:** 2 auto-fixed (2 bugs from Phase 119.1 narrative generators)
**Impact on plan:** Both bugs blocked HTML render. Fixes essential for pipeline completion. No scope creep.

## Issues Encountered
- `underwrite --fresh analyze TICKER` does not pass `--fresh` to the analyze subcommand -- must use `underwrite analyze --fresh TICKER` instead
- Stale `output/HNGE/` directory (without company name) caused pipeline to resume from cached state instead of running fresh -- removed manually
- Background pipeline process caused SQLite cache contention on retry -- waited for first process to complete

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 3 tickers have fresh v8.0 HTML output with narrative quality improvements
- Phase 120 plan 03 is the final plan -- Phase 120 is now complete
- v8.0 milestone ready for closure pending any follow-up from visual review findings

## Self-Check: PASSED

All files verified present. All commit hashes confirmed in git log.

---
*Phase: 120-integration-visual-verification*
*Completed: 2026-03-21*
