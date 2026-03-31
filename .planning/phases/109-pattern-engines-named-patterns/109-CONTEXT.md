# Phase 109: Pattern Engines + Named Patterns - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement four pattern detection engines (Conjunction Scan, Peer Outlier, Migration Drift, Precedent Match) that find compound risk patterns invisible to individual signal evaluation. Seed a case library with 20 canonical D&O cases. Define 6 named archetypes in YAML. Build an engine firing panel visualization. Design blueprints are `pattern_engine_design.yaml`, `case_library_design.yaml`, and `named_archetypes_design.yaml` from Phase 106.

</domain>

<decisions>
## Implementation Decisions

### Data Availability & Cold Start
- **Conjunction Scan: seed + enrich model.** Ship with a curated seed correlation table derived from D&O domain knowledge (known cross-domain co-fire patterns like insider selling + margin compression + guidance miss). Conjunction Scan uses seed data immediately on day one. `brain_correlations` from actual pipeline runs gradually supplement/override seeds as run history builds.
- **Peer Outlier: reuse existing SEC Frames data.** No new ACQUIRE step. Peer Outlier works with whatever SEC Frames data the pipeline already pulls for benchmarking (Phase 75). If existing pull covers the needed metrics for 10+ peers, that's sufficient. Engine is limited to already-acquired metrics.
- **Migration Drift: AnalysisState XBRL only.** Operates on the 8 quarters of XBRL data already extracted in the current pipeline run (stored on AnalysisState). No cross-run history needed. Works on first run. XBRL is the authoritative source.
- **Missing data: NOT_FIRED with note.** When an engine can't run due to missing data (no XBRL, no peers), it shows NOT_FIRED (gray card) with a small note like "Insufficient data." No distinct DATA_UNAVAILABLE visual state.

### Case Library Seeding
- **Storage: YAML file(s) in `brain/framework/`.** Case library as YAML alongside other design artifacts. Human-readable, version-controlled, Pydantic-validated via the existing `PatternDefinition`-adjacent schema from `brain_schema.py`. Loaded at runtime like signals.
- **Signal profile depth: deep reconstruction (50-100 signals per case)** for the 5-6 landmark HIGH-confidence cases (Enron, WorldCom, Theranos, Wirecard, FTX, Valeant). Key-facts level (10-20 signals) for the remaining 14 MEDIUM-confidence cases. Use known public record to reconstruct broader signal profiles for landmarks.
- **Auto-expansion from pipeline: yes.** When the pipeline detects an active SCAC filing for the analyzed company, automatically create a case entry with the current signal profile and outcome=ongoing. Case library grows organically with every analyzed company that has active litigation.
- **Auto-added profiles flagged as POST_FILING.** Auto-added cases get `signal_profile_confidence: LOW` and a note: "Profile captured post-filing, not at time of filing." Precedent Match can weight these differently from curated seed cases.

### Engine Firing Thresholds
- **Ship design doc defaults, tune later.** Use the researched thresholds from `pattern_engine_design.yaml`:
  - Conjunction Scan: confidence > 0.5, minimum 3 signals, co_fire_rate > 0.15
  - Peer Outlier: multi-dimensional z > 2.0, single-metric z > 3.0, minimum 3 outlier metrics
  - Migration Drift: slope < -0.05/quarter, minimum 4 quarters, 2+ RAP categories
  - Precedent Match: notable > 0.30, strong > 0.50, very strong > 0.70
- All thresholds in config YAML, not hardcoded. Calibrate after running on 30+ tickers.
- **Archetype recommendation_floor: raises tier, never lowers.** If H/A/E scoring says STANDARD but Accounting Time Bomb fires with floor=ELEVATED, tier is raised to ELEVATED. Pattern match never makes things look better. Consistent with CRF veto logic.
- **No aggregate pattern score.** Each engine stands alone with its own confidence. No composite "pattern score" from weighted averaging. The tier floor from named archetypes is the only composite effect.
- **Precedent Match: show all matches including dismissals.** Dismissed cases appear in results but with 0.5x outcome severity weight. Both settlement and dismissal outcomes are informative for the UW.

### Firing Panel Display
- **Always show all 10 items** (4 engines + 6 archetypes). Gray cards show NOT_FIRED. Absence of a pattern is informative. UW sees all 10 were checked. Consistent with "show your work" philosophy.
- **Placement: after scoring, before P x S.** Reading order: Tier badge -> H/A/E composites -> Firing panel -> P x S chart -> Detailed sections. Patterns contextualize the scoring before severity.
- **Card detail: compact face + expandable drill-down.** Card face shows: name, MATCH/NOT_FIRED badge, match count (e.g., "7/19"), confidence bar, recommendation floor badge. Click to expand: matched signal IDs with current status, plus historical case references.
- **Precedent Match: top 3 matches with similarity + outcome.** Show: case name, similarity score, outcome (settlement amount or dismissed), 1-line key fact. E.g., "Valeant 2015 (0.52) -- $1.2B settlement -- channel stuffing via Philidor."

### Claude's Discretion
- Code organization within stages/score/ (new files, module structure)
- Exact Pydantic model structure for engine results and case library entries
- Seed correlation table contents and format
- Signal profile reconstruction depth judgment per case
- How to integrate engine results into the ScoreStage pipeline
- Chart rendering details for the firing panel (card layout, colors, spacing)
- YAML schema for case library entries (extending or mirroring PatternDefinition)

</decisions>

<specifics>
## Specific Ideas

- Seed + enrich model for Conjunction Scan mirrors how the brain learning loop works -- start with domain knowledge, improve from data
- Deep reconstruction for landmark cases means reading through SCAC complaints and SEC filings to map ~50-100 signals, not just the 10-15 obvious ones
- Auto-add from pipeline means the case library grows with every run that encounters an active filing -- over time this becomes a valuable proprietary dataset
- POST_FILING flag on auto-added cases preserves honesty about signal profile timing -- these are "what the company looks like now" not "what it looked like before trouble"
- Archetype tier floor = CRF veto logic -- both are non-compensatory overrides that raise severity, never reduce it

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brain/brain_correlation.py` (463 lines): Full co-occurrence mining engine with `mine_cooccurrences()`, `brain_correlations` table, `CorrelatedPair` Pydantic model. Conjunction Scan can reuse this infrastructure directly.
- `brain/brain_schema.py`: `PatternDefinition` Pydantic schema already defined with id, name, required_signals, minimum_matches, recommendation_floor, rap_dimensions, historical_cases, epistemology fields.
- `stages/score/scoring_lens.py`: `ScoringLens` Protocol and `ScoringLensResult` model -- pattern for pluggable engine interface.
- `stages/render/context_builders/_signal_consumer.py` (193 lines): SignalResultView with rap_class, rap_subcategory -- primary data source for all engines.
- `stages/render/context_builders/_signal_fallback.py` (105 lines): Graceful degradation pattern for missing signals.
- `brain/framework/pattern_engine_design.yaml`: Complete algorithm specification for all 4 engines.
- `brain/framework/case_library_design.yaml`: Case schema, 20 seed cases, similarity metrics, maintenance procedures.
- `brain/framework/named_archetypes_design.yaml`: 6 archetypes with real signal IDs, firing panel spec.
- `brain/framework/chart_styles.yaml` (Phase 105): Chart style registry for consistent rendering.

### Established Patterns
- ScoringLens Protocol: pluggable interface with `evaluate()` returning typed result. Mirror for PatternEngine protocol.
- Score stage orchestrator: `stages/score/__init__.py` runs steps sequentially. Pattern engines add as new step(s).
- Brain YAML as source of truth: all definitions in YAML, Pydantic-validated, loaded at runtime.
- Signal results dict[signal_id] -> SignalResultView extraction via consumer infrastructure.
- Graceful degradation: engine failure logged as warning, scoring continues. Same pattern for pattern engine failures.

### Integration Points
- `stages/score/__init__.py`: Add pattern engine step after severity computation (Step 16+)
- `state.scoring` or new `state.patterns`: Store engine results on AnalysisState
- `brain/framework/`: Case library YAML, seed correlations, archetype definitions
- `stages/render/context_builders/`: New pattern context builder for firing panel
- `templates/html/sections/`: New pattern section template with card grid
- `brain/framework/rap_signal_mapping.yaml`: Signal -> subcategory for cross-domain checks

</code_context>

<deferred>
## Deferred Ideas

- **Supabase migration for growing knowledge corpus** -- case library, correlations, calibration data, run history all point toward needing a persistent backend. Current DuckDB + YAML works for v7.0 but worth evaluating for v8.0+.
- Aggregate pattern score (weighted composite across engines) -- decided against for v7.0, individual engines stand alone.
- Interactive calibration session for pattern thresholds (like Phase 107 scoring calibration) -- future milestone.
- Bow-Tie engine and Control System engine (ADV-03, ADV-04) -- deferred to v8.0+.
- Case library versioning and immutability (designed but not critical for v7.0 seed).

</deferred>

---

*Phase: 109-pattern-engines-named-patterns*
*Context gathered: 2026-03-16*
