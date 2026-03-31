---
phase: 106-model-research
plan: 02
subsystem: brain-framework
tags: [pattern-engines, case-library, archetypes, conjunction-scan, peer-outlier, migration-drift, precedent-match, yaml-design]

requires:
  - phase: 102-rap-taxonomy
    provides: "H/A/E taxonomy with 20 subcategories, 514 signals, SCAC validation"
  - phase: 103-schema-foundation
    provides: "PatternDefinition Pydantic schema, brain_correlations table, epistemology"
provides:
  - "Four pattern engine algorithm specifications (Conjunction Scan, Peer Outlier, Migration Drift, Precedent Match)"
  - "Case library schema with similarity metrics, SCAC seed structure, 20 canonical cases"
  - "Six named D&O archetypes with real signal IDs, minimum matches, recommendation floors"
  - "Engine firing panel visualization specification"
affects: [109-pattern-engines, 110-conjunction-rules, 112-worksheet-render]

tech-stack:
  added: []
  patterns:
    - "Engine algorithm spec: steps, data requirements, complexity analysis, thresholds, output format"
    - "Case library fingerprint: binary signal vector with importance-weighted Jaccard similarity"
    - "Named archetype pattern: real signal IDs from brain/signals/ with minimum_matches and recommendation_floor"

key-files:
  created:
    - src/do_uw/brain/framework/pattern_engine_design.yaml
    - src/do_uw/brain/framework/case_library_design.yaml
    - src/do_uw/brain/framework/named_archetypes_design.yaml
  modified: []

key-decisions:
  - "Four independent pattern engines running in parallel with no inter-engine dependencies"
  - "Conjunction Scan uses brain_correlations table with cross-domain requirement (2+ of H/A/E)"
  - "Peer Outlier uses z-scores with MAD (robust to outliers) from SEC Frames peer data"
  - "Migration Drift requires gradual deterioration (no single-quarter jumps >2x slope)"
  - "Precedent Match uses weighted Jaccard with CRF=3x, elevated=2x importance weighting"
  - "Case library seeded with 20 canonical cases from Enron through Activision"
  - "AI Mirage archetype identifies 3 future signal gaps for Phase 110"
  - "Engine firing panel uses horizontal card grid with confidence-based color coding"

patterns-established:
  - "Signal fingerprint: binary vector {signal_id: 0|1} for company risk profile comparison"
  - "Archetype definition: real signal IDs, minimum_matches, recommendation_floor, historical_cases, epistemology"
  - "Future signal gap tracking: future_signal.* prefix for signals not yet in corpus"

requirements-completed: [PAT-01-design, PAT-02-design, PAT-03-design, PAT-04-design, PAT-05-design, PAT-06-design, PAT-07-design]

duration: 7min
completed: 2026-03-15
---

# Phase 106 Plan 02: Pattern Engines + Case Library + Archetypes Summary

**Four pattern detection engine algorithms (Conjunction, Peer Outlier, Migration Drift, Precedent Match) with 20-case library schema and 6 named D&O archetypes using real signal IDs from 514-signal corpus**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-15T04:44:14Z
- **Completed:** 2026-03-15T04:57:45Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments
- Four pattern engine specifications with complete algorithm steps, data requirements, complexity analysis, thresholds, and output formats
- Case library design with entry schema, weighted Jaccard similarity, SCAC seed structure, and 20 canonical D&O cases
- Six named archetypes (Desperate Growth Trap, Governance Vacuum, Post-SPAC Hangover, Accounting Time Bomb, Regulatory Reckoning, AI Mirage) with real signal IDs verified against brain/signals/ YAML files
- Engine firing panel visualization with horizontal card layout and confidence color coding

## Task Commits

1. **Task 1: Pattern engine algorithm design** - `d50c50b` (feat)
2. **Task 2: Case library + named archetypes** - `2762153` (feat)

## Files Created/Modified
- `src/do_uw/brain/framework/pattern_engine_design.yaml` - 596-line design: 4 engines, coordination, data requirements
- `src/do_uw/brain/framework/case_library_design.yaml` - 510-line design: schema, similarity, SCAC seed, 20 cases
- `src/do_uw/brain/framework/named_archetypes_design.yaml` - 450-line design: 6 archetypes, firing panel spec

## Decisions Made
- See key-decisions in frontmatter above

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All three design documents are complete implementation blueprints for Phase 109 (Pattern Engines + Named Patterns)
- Case library seed requires signal profile reconstruction for 20 canonical cases
- AI Mirage archetype has 3 identified future signal gaps for Phase 110
- Peer Outlier engine may require SEC Frames peer data acquisition addition
- Migration Drift engine requires multi-quarter XBRL data caching

---
*Phase: 106-model-research*
*Completed: 2026-03-15*
