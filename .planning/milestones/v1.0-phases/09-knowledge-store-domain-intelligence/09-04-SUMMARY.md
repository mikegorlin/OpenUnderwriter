---
phase: 09-knowledge-store-domain-intelligence
plan: 04
subsystem: learning-narrative
tags: [knowledge-store, learning, effectiveness, co-firing, narrative, risk-stories, cli]

# Dependency graph
requires:
  - phase: 09-knowledge-store-domain-intelligence
    plan: 02
    provides: KnowledgeStore query API, add_note, search_notes, get_check
provides:
  - Learning infrastructure: record_analysis_run, get_check_effectiveness, find_redundant_pairs, get_learning_summary
  - Narrative composition: compose_narrative with 7 pre-defined risk story templates
  - Narrative suggestions: suggest_new_narrative from co-firing cluster analysis
  - Knowledge CLI sub-app: do-uw knowledge narratives/learning-summary commands
affects: [09-05 (ingestion pipeline), 09-06 (integration), Phase 10+ (RENDER narrative embedding)]

# Tech tracking
tech-stack:
  added: []
  patterns: [note-based analysis tracking, Jaccard similarity for redundancy, greedy clustering for narrative suggestion, Typer sub-app pattern]

key-files:
  created:
    - src/do_uw/knowledge/learning.py
    - src/do_uw/knowledge/narrative.py
    - src/do_uw/cli_knowledge.py
    - tests/knowledge/test_learning.py
    - tests/knowledge/test_narrative.py
  modified:
    - src/do_uw/knowledge/store.py
    - src/do_uw/knowledge/__init__.py
    - src/do_uw/cli.py

key-decisions:
  - "Analysis runs stored as notes with 'analysis_run' tag (no new tables required)"
  - "query_notes_by_tag added to KnowledgeStore for public tag-based note queries (avoids _session private access)"
  - "Jaccard similarity for redundancy detection (intersection/union of fire sets, not just co-occurrence count)"
  - "Greedy cluster expansion for narrative suggestions (highest-degree-first with half-cluster connectivity threshold)"
  - "CLI sub-app in cli_knowledge.py registered via Typer add_typer (keeps cli.py under 230 lines)"
  - "Regex fullmatch for check pattern matching (supports both exact IDs and wildcards in templates)"

patterns-established:
  - "Note-based tracking: analysis outcomes stored as JSON notes, queried by tag"
  - "Typer sub-app: knowledge_app in cli_knowledge.py, registered in cli.py"
  - "Narrative template pattern: check_patterns + activation threshold + severity ordering"

# Metrics
duration: 8min
completed: 2026-02-09
---

# Phase 9 Plan 4: Learning Infrastructure and Narrative Composition Summary

**Check effectiveness tracking with fire rate/co-firing/redundancy analysis, plus 7-template narrative composition grouping checks into underwriter-friendly risk stories with CLI output**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-09T06:27:45Z
- **Completed:** 2026-02-09T06:35:32Z
- **Tasks:** 2
- **Files created:** 5
- **Files modified:** 3

## Accomplishments
- Learning infrastructure tracks analysis outcomes as JSON notes, computes check fire rates and co-firing partner rates, detects redundant pairs via Jaccard similarity, and generates aggregate learning summaries
- 7 narrative templates (restatement risk, event-driven claim, governance failure, regulatory exposure, financial distress, insider trading pattern, acquisition risk) that activate when >= 2 component checks fire
- Narrative suggestions from co-firing data using greedy cluster expansion to identify potential new risk stories
- Knowledge CLI sub-app with `do-uw knowledge narratives <ticker>` (compose risk stories) and `do-uw knowledge learning-summary` (aggregate metrics) commands
- 42 new tests (22 learning + 20 narrative), all passing alongside 1276 existing tests (1318 total)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create learning infrastructure for check effectiveness tracking** - `4ce9aa7` (feat)
2. **Task 2: Create narrative composition and knowledge CLI sub-app** - `f789ed3` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/learning.py` (340 lines) - AnalysisOutcome, CheckEffectiveness, record_analysis_run, get_check_effectiveness, find_redundant_pairs, get_learning_summary
- `src/do_uw/knowledge/narrative.py` (455 lines) - NarrativeStory, NARRATIVE_TEMPLATES (7), compose_narrative, get_available_narratives, suggest_new_narrative
- `src/do_uw/cli_knowledge.py` (170 lines) - Typer sub-app with narratives and learning-summary commands
- `src/do_uw/knowledge/store.py` (431 lines) - Added query_notes_by_tag method
- `src/do_uw/knowledge/__init__.py` (87 lines) - Updated exports with learning and narrative public API
- `src/do_uw/cli.py` (226 lines) - Registered knowledge sub-app
- `tests/knowledge/test_learning.py` - 22 tests for effectiveness tracking
- `tests/knowledge/test_narrative.py` - 20 tests for narrative composition

## Decisions Made
- **Note-based tracking**: Analysis runs stored as notes tagged 'analysis_run' rather than adding new SQLAlchemy tables. Avoids schema migration while providing full learning capability.
- **query_notes_by_tag public method**: Added to KnowledgeStore to avoid direct _session() access from learning.py (pyright strict reportPrivateUsage compliance).
- **Jaccard similarity**: Redundancy detection uses intersection/union rather than simple co-occurrence count, giving a more meaningful "always co-fire" metric.
- **Regex fullmatch patterns**: Narrative templates use regex patterns allowing both exact check ID matching and future wildcard support.
- **CLI sub-app**: Created cli_knowledge.py as a Typer sub-app rather than adding commands to cli.py (which is at 226 lines and would grow too large with knowledge commands).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pyright strict violations in learning.py**
- **Found during:** Task 1 (pyright check)
- **Issue:** Unused imports (field, UTC) and reportPrivateUsage on store._session() access
- **Fix:** Removed unused imports; added query_notes_by_tag public method to KnowledgeStore instead of accessing _session directly
- **Files modified:** src/do_uw/knowledge/learning.py, src/do_uw/knowledge/store.py
- **Committed in:** 4ce9aa7

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor refactor to use public API instead of private session access. Improved encapsulation.

## Issues Encountered
None beyond the auto-fixed item above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Learning infrastructure fully operational for recording and analyzing check effectiveness
- Narrative composition ready for pipeline integration (compose_narrative callable from any stage)
- CLI commands provide immediate utility for viewing learning data and risk narratives
- Full RENDER integration (embedding narratives into Word document) deferred to Phase 10+
- No blockers for subsequent plans (09-05, 09-06)

---
*Phase: 09-knowledge-store-domain-intelligence*
*Completed: 2026-02-09*
