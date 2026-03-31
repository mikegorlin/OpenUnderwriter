# Phase 111: Signal Wiring Closure - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Close all signal wiring gaps from the traceability audit. Every signal must have: working data source resolution, functional evaluator dispatch, render target (manifest group), and no orphans. Replace hardcoded mapper routing with YAML-driven field resolution. Zero aspirational-only declarations.

</domain>

<decisions>
## Implementation Decisions

### SKIPPED Signal Triage
- Triage each of the 64 SKIPPED signals individually: wire signals where data exists at a different state path (path mismatch fix), mark signals DEFERRED where data genuinely doesn't exist yet (needs future extraction work)
- For the 25 "mapper not configured" signals: add mapper/resolver routing if data exists somewhere in state, otherwise DEFERRED with documented rationale
- For the 39 "data not available" signals: close cheap path mismatches, defer signals requiring new LLM extraction or new API calls
- DEFERRED signals show in worksheet check panels with a "Data pending" badge — distinct from SKIPPED and CLEAR. Underwriter sees what the system WOULD check if data existed (transparency)
- Hard CI gate: SKIPPED rate must be <5% or CI fails. Enforced in Phase 115 as CI-04.

### Manifest Group Governance
- Ungoverned manifest groups displaying COMPUTED data (distress_indicators, ten_factor_scoring, tier_classification, etc.) marked `display_only: true` — these show outputs of scoring/analysis pipeline, inputs already governed by signals
- Ungoverned manifest groups displaying RAW EXTRACTED data (stock_performance, executive_compensation, board_composition, etc.) also marked `display_only: true` — signals evaluate risk FROM this data but don't govern the data display itself. Phase 113 builder rewrites will make signals annotate these displays.
- `display_only: true` field added directly in `output_manifest.yaml` on each ungoverned group — the manifest is already the rendering contract
- 48 Phase 110 mechanism signals (20 absence, 8 conjunction, 20 contextual) assigned to their parent domain manifest group based on primary domain. E.g., CONJ.ACCT_GOV maps to the group where its most actionable insight appears.

### Acquisition Field Wiring (CRITICAL — Brain Portability)
- **Replace ~3,000 lines of hardcoded mapper code** (`signal_mappers.py` + 5 `signal_mappers_*.py` files) with a YAML-driven generic field resolver
- The signal engine reads `acquisition.sources[].fields` declarations from YAML and resolves them directly against state — no prefix-based Python routing
- YAML acquisition block gets richer declarations to handle edge cases:
  - `path`: direct state traversal (e.g., `extracted.governance.board_composition.size`)
  - `computed_from`: for derived values like Beneish score that come from analysis stage (e.g., `analysis.xbrl_forensics.beneish.composite_score`)
  - `fallback_paths`: ordered list of alternate paths to try (e.g., try XBRL first, then LLM-extracted)
- Fix all 102 YAML field declarations to point at correct actual state paths — YAML stays as the authoritative spec, never delete aspirational fields
- **Hydration verification**: every signal that evaluated before the migration must still evaluate after. Side-by-side comparison of pre/post signal results on a test ticker.
- **QA gate**: run pipeline on at least one ticker pre and post migration, diff all signal results, zero regressions allowed

### Trend/Peer Evaluators
- Trend evaluator (`evaluate_trend`) compares current vs prior annual filing data — matches DISC.YOY naming convention
- Peer comparison evaluator: Claude's discretion on data source (SEC Frames percentiles vs MAD z-scores) based on what's actually available in the pipeline state
- Both evaluators produce standard signal result structure (CLEAR/TRIGGERED/SKIPPED) with comparison detail in evidence field (prior_value, current_value, delta, percentile)
- Trend and peer evaluators implemented as part of the YAML-driven resolver work — unified architecture change, not separate dispatch

### Claude's Discretion
- Specific peer comparison data source selection (SEC Frames percentiles vs MAD z-scores)
- Resolver architecture design (how generic resolver handles path traversal, computed fields, fallbacks)
- Individual signal-by-signal triage decisions for the 64 SKIPPED (wire vs DEFERRED)
- Assignment of 48 mechanism signals to specific manifest groups
- Categorization of 51 ungoverned manifest groups as display_only vs needing governance

</decisions>

<specifics>
## Specific Ideas

- "YAML should be telling others where to get the info" — the brain IS the spec, mappers should not exist as a separate routing layer
- "Wire what's missing, not delete it" — aspirational field declarations represent intended data flow and should be made real
- "Do not violate the brain portability principle" — signals must be fully self-contained, brain drives everything
- "Proper QA, hydration, verification" — the mapper replacement must be provably correct with zero regressions

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mechanism_evaluators.py` (509 lines): existing conjunction/absence/contextual evaluators — trend/peer evaluators extend this
- `_signal_consumer.py` + `_signal_fallback.py` (Phase 104): typed signal result extraction infrastructure
- SEC Frames percentile data at `analysis.benchmarks.frames_percentiles`: existing peer data
- XBRL 8-quarter data: existing multi-period data for trend comparison

### Established Patterns
- Mechanism dispatch in `signal_engine.py` lines 125-141: conjunction/absence/contextual dispatch pattern to follow for trend/peer
- Signal result structure: CLEAR/TRIGGERED/SKIPPED with evidence dict — uniform contract
- Phase 109 PeerOutlierEngine: MAD z-score approach already implemented for pattern detection

### Integration Points
- `signal_engine.py` (576 lines): dispatch loop needs YAML-driven field resolver replacing mapper calls
- `signal_mappers.py` + 5 extension files (~3,078 lines total): to be replaced by generic resolver
- `output_manifest.yaml`: needs `display_only: true` field on ungoverned groups
- `brain/signals/{absence,conjunction,contextual}/*.yaml` (48 files): need `group` field assignments
- All 562 signal YAML files: `acquisition.sources[].fields` paths need audit and correction

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 111-signal-wiring-closure*
*Context gathered: 2026-03-16*
