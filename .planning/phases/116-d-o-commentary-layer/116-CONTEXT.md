# Phase 116: D&O Commentary Layer - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Add D&O risk intelligence commentary to every evaluative data table and scoring factor in the worksheet, driven by brain signal `do_context` templates. Generate LLM-powered section-opening analytical narratives. Migrate all remaining hardcoded D&O commentary from Python/Jinja2 to brain YAML. Author do_context for all 562 brain signals via LLM batch generation. Promote CI gate from WARN to FAIL on all D&O commentary locations.

</domain>

<decisions>
## Implementation Decisions

### D&O Column Coverage Strategy
- **Evaluative tables only** — Tables presenting risk-relevant data get D&O columns: forensic indicators, governance metrics, litigation cases, scoring factors, market events, risk flags. Raw financial statements (income/balance/cash flow), peer comparison raw data, filing history, and officer/director raw listings do NOT get D&O columns
- **Empty cell fallback** — If no signal do_context exists for a row, leave the D&O column blank. Signals get authored over time — empty cells are honest representation of coverage. No filler commentary
- **All 562 signals get do_context** — LLM batch generation produces TRIGGERED_RED, TRIGGERED_YELLOW, CLEAR templates for every signal in the brain. Human spot-checks a sample (~20-30 key signals). `brain health` validates template syntax. Massive but achievable in one plan wave

### LLM Batch do_context Generation
- **Process**: Read all 562 signal YAMLs → for each signal, LLM generates per-status D&O commentary templates based on signal name, threshold, factors, and D&O domain knowledge → write back to YAML files → run `brain health` validation → spot-check key signals
- **Quality bar**: Every template must contain company-specific placeholder variables ({value}, {score}, {zone}, etc.) and reference the specific D&O litigation theory or risk vector the signal maps to. No generic "elevated risk" language (QUAL-04)
- **Batch generation runs FIRST** (Wave 1) before migration and wiring

### Scoring Factor Commentary Format
- **Expandable per-factor detail** — Each factor (F.1-F.10) gets a collapsible section: header with score, expanded view with "What Was Found" (data + source citations from signal `evidence` + `details` dict) and "Underwriting Commentary" (D&O interpretation from signal `do_context`)
- **Data source**: SignalResult fields — `evidence` (text summary), `details` (structured data dict), `source` (citation), `do_context` (D&O interpretation). No new data collection needed
- **"Why TIER, not ADJACENT_TIER"** — Algorithmic from factor scores. Compare composite to tier boundaries, identify factors closest to flipping, generate counterfactual ("If F.1 had been non-zero, score would reach X → COMPETE tier"). All from signal results, no LLM

### Section Narrative Generation
- **LLM-generated in ANALYZE stage** — After all signals evaluated and scoring complete. Full analytical context passed to LLM: signal results, scoring factors, financial data, company specifics. Stored on `state.narratives.*`. Renderers consume pre-generated strings as-is
- **All 6 major sections get narratives**: Financial Health (enhance existing `financial_narrative()`), Market Events (new), Governance Posture (new), Litigation Context (new), Scoring/Tier (new — includes tier explanation), Company Profile (new)
- **QUAL-07 compliance**: Every narrative must be a company-specific analytical paragraph that tells the STORY of this company's risk profile, not a generic section description. Must include specific data points (dollar amounts, percentages, dates, names)

### Migration + CI Gate Tightening
- **Migrate ALL 5 Python functions + Jinja2 template** in Phase 116:
  - `sect3_audit.py`: `_add_audit_do_context()` → audit signal do_context
  - `sect4_market_events.py`: `_departure_do_context()` → market event signal do_context
  - `sect5_governance.py`: `_add_leadership_do_context()` → governance signal do_context
  - `sect6_litigation.py`: `_add_sca_do_context()` → litigation signal do_context
  - `sect7_scoring_detail.py`: `_add_pattern_do_context()` → scoring signal do_context
  - `distress_indicators.html.j2`: inline D&O conditionals → `{{ do_context_string }}`
- **Delete Python functions after migration** — same pattern as Phase 115. Golden snapshot tests verify parity
- **Promote CI gate WARN→FAIL** — After Phase 116, CI gate FAILs on ALL D&O evaluative language in context_builders/ and templates/. WARN list becomes empty. Clean slate

### Wave Ordering
1. LLM batch: generate do_context for all 562 signals
2. Migrate: replace 5 Python functions with signal do_context consumption
3. Wire: add D&O columns to evaluative tables
4. Narratives: generate section openers (LLM in ANALYZE)
5. Scoring: factor detail rendering + tier explanation
6. CI gate: promote WARN→FAIL, verify clean

### Claude's Discretion
- Exact LLM prompt design for batch do_context generation
- Which tables qualify as "evaluative" vs "raw data" (use the guidelines above)
- Exact collapsible section implementation for factor detail
- Narrative prompt engineering for section openers
- Order of signal YAML file processing for batch generation
- How to handle signals with no meaningful D&O relevance (some technical/infrastructure signals)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 115 Infrastructure (consume, don't rebuild)
- `src/do_uw/stages/analyze/do_context_engine.py` — Template evaluation engine (render_do_context, apply_do_context, _select_template)
- `src/do_uw/stages/analyze/signal_results.py` — SignalResult.do_context field
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` — SignalResultView.do_context, get_signal_do_context() accessor
- `src/do_uw/stages/render/context_builders/financials_evaluative.py` — Reference consumer pattern (safe_get_result → .do_context)

### Migration Targets (must read before migrating)
- `src/do_uw/stages/render/sections/sect3_audit.py` — `_add_audit_do_context()` hardcoded D&O
- `src/do_uw/stages/render/sections/sect4_market_events.py` — `_departure_do_context()` hardcoded D&O
- `src/do_uw/stages/render/sections/sect5_governance.py` — `_add_leadership_do_context()` hardcoded D&O
- `src/do_uw/stages/render/sections/sect6_litigation.py` — `_add_sca_do_context()` hardcoded D&O
- `src/do_uw/stages/render/sections/sect7_scoring_detail.py` — `_add_pattern_do_context()` + allegation mapping hardcoded D&O
- `src/do_uw/templates/html/sections/financial/distress_indicators.html.j2` — Inline Jinja2 D&O conditionals

### CI Gate
- `tests/brain/test_do_context_ci_gate.py` — WARN_PYTHON_FILES and WARN_TEMPLATE_FILES to promote to FAIL

### Brain Signal YAML (batch generation targets)
- `src/do_uw/brain/signals/` — All 36+ YAML files containing 562 signals
- `src/do_uw/brain/brain_signal_schema.py` — PresentationSpec.do_context schema

### Scoring Model
- `src/do_uw/models/scoring.py` — ScoringResult, tier boundaries, factor scores
- `src/do_uw/stages/render/sections/sect7_scoring_detail.py` — Current factor rendering

### Existing Narrative
- `src/do_uw/stages/render/md_narrative.py` — `financial_narrative()` existing pattern

### Requirements
- `.planning/REQUIREMENTS.md` — COMMENT-01 through COMMENT-06, SCORE-01, SCORE-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `do_context_engine.py` — Full template evaluation engine from Phase 115 (render_do_context, apply_do_context, _select_template with compound key fallback)
- `_signal_consumer.py` — SignalResultView with do_context field, get_signal_do_context() accessor
- `safe_get_result()` from `_signal_fallback.py` — Graceful signal result retrieval
- `financial_narrative()` in `md_narrative.py` — Existing section narrative pattern to extend
- `add_styled_table()` — Table rendering utility used across all sections (add D&O column to headers)

### Established Patterns
- Consumer: `safe_get_result(signal_results, "SIGNAL.ID").do_context` — Phase 115 established this
- Golden snapshot tests for migration parity — Phase 115 pattern in `test_do_context_golden.py`
- CI gate progressive enforcement — Phase 115 pattern with FAIL/WARN tiers
- Collapsible sections with chevrons — CIQ-style pattern from v3.0 (VIS-04)

### Integration Points
- `signal_engine.py` — do_context already rendered for all signals in ANALYZE
- `AnalysisState` — needs new `narratives` field for section opener storage
- Section renderers (sect3-7) — add D&O columns + consume narratives
- Scoring renderer — add per-factor detail expansion + tier explanation
- `brain health` CLI — already reports do_context coverage (enhance after batch)

</code_context>

<specifics>
## Specific Ideas

- The LLM batch generation should include the signal's `factors` and `peril_ids` in the prompt context so do_context templates reference the correct D&O litigation theories
- For the tier explanation, show both "what pushes it up" (top contributing factors) and "what would change it" (counterfactual — which factor change would flip the tier)
- Section narratives should reference the scoring tier and key signals by name, creating cross-references between sections
- The distress_indicators.html.j2 Jinja2 migration should replace `{% if zone == 'Distress' %}` conditionals with a simple `{{ do_context }}` variable pass-through

</specifics>

<deferred>
## Deferred Ideas

- Interactive `brain preview-do-context SIGNAL_ID` command — useful for authoring but not Phase 116 scope
- do_context coverage threshold in CI (e.g., "must be >90%") — Phase 120 integration gate
- Sector-specific do_context variants (same signal, different D&O context per industry) — future milestone

</deferred>

---

*Phase: 116-d-o-commentary-layer*
*Context gathered: 2026-03-19*
