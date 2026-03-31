---
phase: 28-presentation-layer-context-through-comparison
plan: 03
subsystem: render
tags: [peer-context, density-gating, financial-health, market-trading, docx]

# Dependency graph
requires:
  - phase: 28-02
    provides: "format_metric_with_context, get_peer_context_line, get_benchmark_for_metric utilities"
  - phase: 28-01
    provides: "Split render section files under 500 lines"
provides:
  - "Peer context enrichment for Sections 1, 3, and 4 metrics"
  - "_is_financial_health_clean() density gating function"
  - "_is_market_clean() density gating function"
  - "Concise rendering for clean financial and market profiles"
  - "sect3_peers.py extracted peer group renderer"
affects: [28-04, 28-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Issue-driven density gating: _is_*_clean() functions gate between concise and full-detail rendering"
    - "Peer context inline: metrics display percentile rank from benchmark when available"
    - "File extraction for 500-line compliance: sect3_peers.py split from sect3_financial.py"

key-files:
  created:
    - src/do_uw/stages/render/sections/sect3_peers.py
  modified:
    - src/do_uw/stages/render/sections/sect1_executive_tables.py
    - src/do_uw/stages/render/sections/sect3_financial.py
    - src/do_uw/stages/render/sections/sect3_audit.py
    - src/do_uw/stages/render/sections/sect4_market.py
    - src/do_uw/stages/render/sections/sect4_market_events.py

key-decisions:
  - "Extracted _render_peer_group to sect3_peers.py rather than sect3_tables.py (sect3_tables already 461 lines)"
  - "Market clean check includes adverse_events.event_count > 0 as a catch-all for unflagged issues"
  - "Short interest clean threshold set at 5% (absolute) with benchmark override via percentile > 50"

patterns-established:
  - "_is_financial_health_clean() checks: all distress models safe, no audit red flags, leverage below median"
  - "_is_market_clean() checks: no severe drops, no cluster selling, low short interest, no big earnings misses, no adverse events"
  - "Concise rendering pattern: single DOBody paragraph with key metric + peer context sentence"

# Metrics
duration: 13min
completed: 2026-02-13
---

# Phase 28 Plan 03: Peer Context + Density Gating for Sections 1, 3, 4 Summary

**Peer percentile context for financial and market metrics across Sections 1/3/4, with issue-driven density gating that renders clean companies concisely and problematic companies with full forensic detail**

## Performance

- **Duration:** 13 min
- **Started:** 2026-02-13T13:27:53Z
- **Completed:** 2026-02-13T13:41:19Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Section 1 snapshot now shows market cap with peer percentile context (e.g., "72nd percentile vs. 15 peers")
- Section 3 distress panel renders concise "Financial Integrity: No concerns" summary for clean companies, full forensic tables for problematic ones
- Section 3 audit renders concise "Audit Risk: No concerns. [Auditor], [tenure] year tenure, [opinion]" for clean profiles
- Section 4 stock stats include volatility peer context, short interest includes peer context with concise one-liner for clean markets
- Section 4 insider trading renders concise "No unusual activity" summary for clean markets, full transaction tables for problematic ones
- Extracted sect3_peers.py (117 lines) from sect3_financial.py to maintain 500-line compliance

## Task Commits

Each task was committed atomically:

1. **Task 1: Add peer context to Section 1 and Section 3 + financial density gating** - `e43878d` (feat)
2. **Task 2: Add peer context to Section 4 + market density gating** - `37ade2e` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/sections/sect3_peers.py` - Extracted peer group comparison table rendering (117 lines)
- `src/do_uw/stages/render/sections/sect1_executive_tables.py` - Market cap peer percentile in snapshot table
- `src/do_uw/stages/render/sections/sect3_financial.py` - Cleaned imports, delegated peer group to sect3_peers.py (459 lines)
- `src/do_uw/stages/render/sections/sect3_audit.py` - Tightened D&O context strings for 500-line compliance (495 lines)
- `src/do_uw/stages/render/sections/sect4_market.py` - Added _is_market_clean(), peer context for volatility/short interest, concise short interest (486 lines)
- `src/do_uw/stages/render/sections/sect4_market_events.py` - Concise insider trading for clean markets, updated stock drops empty message (497 lines)

## Decisions Made
- Extracted peer group rendering to new sect3_peers.py rather than adding to sect3_tables.py (already at 461 lines, would exceed 500)
- Market clean check uses 5% absolute short interest threshold with benchmark percentile > 50 override
- Adverse events event_count > 0 included in market clean check as catch-all for any flagged issues
- EarningsResult.MISS with miss_magnitude > 10% in recent 4 quarters triggers non-clean market

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Extracted sect3_peers.py for 500-line compliance**
- **Found during:** Task 1 (Section 3 modifications)
- **Issue:** sect3_financial.py was at 566 lines, exceeding the non-negotiable 500-line limit from CLAUDE.md
- **Fix:** Extracted _render_peer_group() and _NON_US_SUFFIXES to new sect3_peers.py (117 lines), reducing sect3_financial.py to 459 lines
- **Files modified:** src/do_uw/stages/render/sections/sect3_financial.py, src/do_uw/stages/render/sections/sect3_peers.py
- **Verification:** All 2928 tests pass, file at 459 lines
- **Committed in:** e43878d

**2. [Rule 3 - Blocking] Tightened sect3_audit.py for 500-line compliance**
- **Found during:** Task 1 (Section 3 modifications)
- **Issue:** sect3_audit.py was at 545 lines, exceeding 500-line limit
- **Fix:** Consolidated separator comment blocks, removed `_ = run` suppression lines, tightened D&O context strings
- **Files modified:** src/do_uw/stages/render/sections/sect3_audit.py
- **Verification:** All tests pass, file at 495 lines
- **Committed in:** e43878d

**3. [Rule 3 - Blocking] Tightened sect4_market.py and sect4_market_events.py**
- **Found during:** Task 2 (Section 4 modifications)
- **Issue:** After adding _is_market_clean() and peer context, sect4_market.py hit 504 lines and sect4_market_events.py hit 527 lines
- **Fix:** Removed separator comment blocks and `_ = run` lines from both files
- **Files modified:** src/do_uw/stages/render/sections/sect4_market.py, src/do_uw/stages/render/sections/sect4_market_events.py
- **Verification:** All tests pass, files at 486 and 497 lines
- **Committed in:** 37ade2e

---

**Total deviations:** 3 auto-fixed (3 blocking -- 500-line compliance)
**Impact on plan:** All fixes were mechanical line-count compliance. No scope creep. One new file created (sect3_peers.py) following existing codebase pattern of splitting for 500-line compliance.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Sections 1, 3, and 4 fully enriched with peer context and density gating
- Plans 04 (Sections 5/6 governance/litigation) and 05 (Section 7 scoring) can proceed
- _is_market_clean() and _is_financial_health_clean() patterns established for reuse
- All 2928 tests pass with 0 regressions

## Self-Check: PASSED

- All 7 files exist on disk
- Both commit hashes (e43878d, 37ade2e) found in git log
- All files under 500 lines (max: 497 in sect4_market_events.py)
- sect3_peers.py created (117 lines)

---
*Phase: 28-presentation-layer-context-through-comparison*
*Completed: 2026-02-13*
