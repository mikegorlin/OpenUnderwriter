---
phase: 110-new-signal-mechanisms-adversarial-critique
plan: 02
subsystem: scoring, rendering
tags: [adversarial-critique, devil-advocate, caveats, pydantic, yaml-rules, jinja2, llm-narrative]

# Dependency graph
requires:
  - phase: 110-01
    provides: "Mechanism evaluators, deep-dive triggers, 562 signals, ScoreStage Steps 16-17"
provides:
  - "Adversarial critique engine: 4 caveat types (false positive, false negative, contradiction, data completeness)"
  - "Caveat + AdversarialResult Pydantic models with LLM narrative support"
  - "30 YAML-defined adversarial rules in brain/framework/adversarial_rules.yaml"
  - "Devil's Advocate HTML section with 4 color-coded subsections"
  - "Inline caveat badge macro + caveat_index for signal-level annotation"
  - "ScoreStage Step 18 with graceful degradation"
  - "adversarial_context.py context builder for template rendering"
affects: [rendering, scoring, worksheet-quality]

# Tech tracking
tech-stack:
  added: []
  patterns: ["YAML-driven rule evaluation", "batched LLM narrative generation with template fallback", "caveat_index signal-keyed inline annotation"]

key-files:
  created:
    - src/do_uw/models/adversarial.py
    - src/do_uw/stages/score/adversarial_engine.py
    - src/do_uw/stages/score/_adversarial_runner.py
    - src/do_uw/brain/framework/adversarial_rules.yaml
    - src/do_uw/stages/render/context_builders/adversarial_context.py
    - src/do_uw/templates/html/sections/adversarial_critique.html.j2
    - src/do_uw/templates/html/macros/caveat_badge.html.j2
    - tests/stages/score/test_adversarial_engine.py
    - tests/stages/score/test_adversarial_runner.py
    - tests/stages/render/test_adversarial_context.py
  modified:
    - src/do_uw/models/scoring.py
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/stages/render/context_builders/__init__.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/brain/output_manifest.yaml
    - tests/stages/render/test_manifest_rendering.py

key-decisions:
  - "30 adversarial rules (8 FP, 8 FN, 6 contradiction, 6+1 completeness) covering key D&O risk patterns"
  - "LLM narrative stub returns empty (preserves template fallback) -- production LLM integration deferred"
  - "caveat_index keyed by target_signal_id enables inline badges in any section template"
  - "Caveats NEVER modify scores -- verified by dedicated immutability tests"
  - "Manifest section groups reference parent template (adversarial_critique.html.j2) per ManifestGroup schema requirement"

patterns-established:
  - "YAML rule catalog pattern: declarative rules evaluated by pure Python functions"
  - "LLM narrative enrichment pattern: rule-based detection -> template explanation -> optional LLM enrichment (max 8 caveats)"
  - "Inline caveat badge pattern: caveat_index dict -> render_signal_caveats macro in section templates"

requirements-completed: [MECH-05, MECH-06]

# Metrics
duration: 15min
completed: 2026-03-16
---

# Phase 110 Plan 02: Adversarial Critique Summary

**Rule-based adversarial engine with 30 YAML rules detecting false positives, blind spots, contradictions, and data gaps -- rendered as Devil's Advocate section + inline caveat badges, with LLM narrative enrichment and strict score immutability**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-16T17:59:56Z
- **Completed:** 2026-03-16T18:14:56Z
- **Tasks:** 2
- **Files modified:** 16 (10 created, 6 modified)

## Accomplishments
- Adversarial critique engine with 4 detection functions evaluating 30 YAML-defined rules
- Devil's Advocate HTML section with amber/blue/purple/gray color-coded caveat cards
- Inline caveat badge macro enabling signal-level annotation in any worksheet section
- ScoreStage Step 18 integration with graceful degradation (pipeline continues if critique fails)
- 48 new tests across engine (23), runner (11), and context builder (14) -- all passing
- Score immutability verified: quality_score, tier, severity, patterns never modified

## Task Commits

Each task was committed atomically:

1. **Task 1: Adversarial models + rule engine + LLM narrative + YAML rules + ScoreStage Step 18** - `a122c89` (feat)
2. **Task 2: Devil's Advocate section + inline caveat badges + context builder + manifest wiring** - `6201c9b` (feat)

## Files Created/Modified
- `src/do_uw/models/adversarial.py` - Caveat + AdversarialResult Pydantic models
- `src/do_uw/stages/score/adversarial_engine.py` - 4 pure check functions (FP, FN, contradiction, completeness)
- `src/do_uw/stages/score/_adversarial_runner.py` - Orchestrator + LLM narrative generation
- `src/do_uw/brain/framework/adversarial_rules.yaml` - 30 declarative rules across 4 types
- `src/do_uw/stages/render/context_builders/adversarial_context.py` - Template context builder + caveat_index
- `src/do_uw/templates/html/sections/adversarial_critique.html.j2` - Devil's Advocate section template
- `src/do_uw/templates/html/macros/caveat_badge.html.j2` - Reusable inline badge macro
- `src/do_uw/models/scoring.py` - Added adversarial_result field + TYPE_CHECKING + model_rebuild
- `src/do_uw/stages/score/__init__.py` - Step 18 integration with try/except
- `src/do_uw/stages/render/html_renderer.py` - Wired build_adversarial_context into context
- `src/do_uw/brain/output_manifest.yaml` - Added adversarial_critique section after scoring

## Decisions Made
- 30 adversarial rules designed around real D&O underwriting patterns (CEO comp justification, sector-normal leverage, lockup expiry blind spots, revenue/margin divergence contradictions, proxy data gaps)
- LLM narrative stub returns empty for now -- template fallback explanations are substantive enough for initial deployment; production LLM integration is straightforward when ready
- caveat_index architecture enables any section template to render inline badges without changes to the context builder
- Manifest groups share parent template rather than individual sub-templates (single Devil's Advocate section with subsections)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed manifest group schema validation**
- **Found during:** Task 2 (manifest wiring)
- **Issue:** ManifestGroup schema requires `template` field on all groups; initial manifest entry omitted it
- **Fix:** Added `template: sections/adversarial_critique.html.j2` to all 4 group entries
- **Files modified:** src/do_uw/brain/output_manifest.yaml
- **Verification:** Manifest schema validation test passes
- **Committed in:** 6201c9b (Task 2 commit)

**2. [Rule 1 - Bug] Updated manifest rendering test for 15 sections**
- **Found during:** Task 2 (verification)
- **Issue:** test_manifest_rendering.py hardcoded 14 section IDs; adding adversarial_critique made it 15
- **Fix:** Added "adversarial_critique" to _MANIFEST_SECTION_IDS list, updated count assertion to 15
- **Files modified:** tests/stages/render/test_manifest_rendering.py
- **Verification:** 724 render tests pass
- **Committed in:** 6201c9b (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both auto-fixes necessary for test correctness. No scope creep.

## Issues Encountered
- ScoringResult forward reference resolution: Tests creating ScoringResult directly must call _rebuild_scoring_models() first (pre-existing pattern, same as hae_result/severity_result/pattern_engine_result)
- Pre-existing test_5layer_narrative.py failure (AnalysisState model_rebuild not called) -- not caused by this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 110 complete: all 2 plans delivered (mechanism evaluators + adversarial critique)
- 562 signals + 48 mechanism signals + 10 deep-dive triggers + 30 adversarial rules
- 403 score tests + 724 render tests passing
- Ready for Phase 111 (company.py decomposition) or Phase 112 (render integration)

---
*Phase: 110-new-signal-mechanisms-adversarial-critique*
*Completed: 2026-03-16*
