# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v3.1 — XBRL-First Data Integrity

**Shipped:** 2026-03-07
**Phases:** 9 | **Plans:** 26

### What Was Built
- XBRL extraction engine: 113+ concepts, 8-quarter extraction, sign normalization, 24 derived formulas
- Forensic financial analysis: 4 modules (balance sheet, capital allocation, debt/tax, revenue quality) + Beneish decomposition + M&A forensics
- SEC Frames API peer benchmarking with true cross-filer percentile ranking
- 66 new brain signals wired to XBRL data with shadow evaluation for regression safety
- Form 4 insider trading enhancement: ownership concentration, deduplication, exercise-sell patterns
- System integrity: Tier 1 manifest, template-facet validation CI, semantic QA, post-pipeline learning loop

### What Worked
- Wave-based parallelization (7 waves across 9 phases) kept execution flowing efficiently
- Shadow evaluation pattern prevented signal regressions during mass signal rewiring
- Gap closure phases (70-04, 70-05, 74) caught pipeline wiring issues before milestone audit
- Forensic re-evaluation pass pattern (run signals twice) was safer than reordering analytical engines
- Two-tier data acquisition model provided clear traceability for all data in the system

### What Was Inefficient
- v3.0 REQUIREMENTS.md was never updated for v3.1 -- requirements lived only in ROADMAP.md phase descriptions, making traceability harder
- Nyquist VALIDATION.md was skipped for 8 of 9 phases -- validation was done but not formalized
- Pipeline wiring (Phase 74) revealed that modules built in earlier phases weren't actually called from the pipeline -- should verify integration earlier
- 3 files grew past 500-line limit during this milestone (declarative Pydantic models)

### Patterns Established
- `foundational` vs `evaluative` signal types in BrainSignalEntry -- foundational signals declare Tier 1 manifest, evaluative signals evaluate data
- `forensic_` field_key prefix convention for all xbrl_forensics-backed signals
- `xbrl_` prefix convention for XBRL-sourced field_keys with dual-source pattern (xbrl_ + narrative_key)
- DerivedDef registry pattern for computed financial metrics with safe arithmetic helpers
- 3-layer false SCA filter: prompt hardening + boilerplate list + case specificity gate
- Post-pipeline learning hook with lazy import to avoid import-time dependencies

### Key Lessons
1. Always verify new modules are wired into the pipeline, not just tested in isolation -- Phase 74 gap closure was entirely about missing `import` + function calls
2. Requirements should live in REQUIREMENTS.md from milestone start, not just ROADMAP.md -- traceability table is valuable for audit
3. Direction-aware coloring (HIGH_IS_GOOD vs HIGH_IS_BAD) is essential for financial metrics -- users expect green=good regardless of whether the number is high or low
4. Frame regex (CY####Q# / CY####Q#I) is more reliable than duration-based YTD discrimination for quarterly XBRL extraction

### Cost Observations
- Model mix: primarily Opus (quality profile)
- 123 commits over 2 days
- High throughput: ~60 commits/day with 26 plans

---

## Milestone: v6.0 — Company Profile Completeness

**Shipped:** 2026-03-14
**Phases:** 9 | **Plans:** 14

### What Was Built
- Business model extraction: 6 BMOD signals (revenue type, concentration, key person, lifecycle, disruption, margins) via LLM extraction from 10-K
- Operational footprint: subsidiary structure from Exhibit 21, workforce distribution, resilience indicators, unified BIZ.OPS.complexity_score (0-20 composite)
- Corporate event risk: 5 BIZ.EVENT signals (M&A, IPO/offering windows, restatements, capital changes, business pivots) from XBRL forensics
- Structural complexity: disclosure opacity, non-GAAP usage, related parties, OBS exposure, holding structure via text signal scanning
- External environment: 5 ENVR signals (regulatory intensity, geopolitical, ESG gap, cyber, macro sensitivity)
- Sector risk: hazard tier from SCAC/NERA data, claim patterns, regulatory overlay, peer comparison with SIC-to-GICS fallback
- CI contract tests: portability gate, manifest coverage, template purity (zero hardcoded thresholds)

### What Worked
- Independent extraction phases (93-97) enabled parallel execution — all 5 completed in a single session
- Signal architecture constraint (all data through brain YAML) kept the milestone architecturally clean — 37 requirements, zero architectural shortcuts
- State proxy pattern (established in Phase 97) reused successfully across ENVR/SECT/OPS phases — consistent mapper interface
- Milestone audit caught 3 integration bugs (template variable scope, invalid enum, stale assertion) before shipping — Phase 101 gap closure was efficient
- Text signal counting as numeric input to composite scores (Phase 96) was an effective pattern for keyword-based risk scoring

### What Was Inefficient
- Phases 93-97 ran without verification step (pre-dates execute-phase verification), requiring retroactive audit discovery of bugs in Phase 100/101
- 3 HTML stub templates in Phase 94 never expanded — operational data renders in Word/PDF but HTML shows nothing
- context_builders/company.py grew to 1080 lines during Phase 100 — should have been split proactively (v6 subsection renderers eventually split to sect2_company_v6.py but builder wasn't)
- RENDER-03 complexity dashboard was planned but skipped per user direction — requirement marked satisfied but feature not built

### Patterns Established
- `company.X_signals` template variable pattern for all v6 subsection Jinja2 templates (not top-level variables)
- `signal_class: foundational` for static reference data signals (SECT.claim_patterns, SECT.regulatory_overlay)
- REFERENCE_DATA acquisition type for signals backed by static YAML reference tables
- State proxy pattern for bridging mapper arguments to extraction functions (ENVR, SECT, BIZ.OPS)
- Additive composite scoring: BIZ.OPS 0-20 from 7 dimensions, M&A 0-4 from 4 indicators, key person 0-3 from 3 indicators
- HHI-based geographic concentration scoring (0-100) with special top-1/top-2 dominance handling

### Key Lessons
1. Milestone audit before shipping catches real integration bugs — EVENT/STRUC HTML rendering was silently broken despite Word/PDF working and tests passing
2. Template variable scope is a common Jinja2 bug — always pass data under `company.` dict, never as top-level context variables
3. Static reference data signals need their own signal_class — trying to use `reference` (doesn't exist) caused silent signal drops
4. Text signal counting is effective for structural complexity scoring but requires careful threshold calibration across tickers

### Cost Observations
- Model mix: primarily Opus (quality profile)
- 74 commits over 5 days
- Moderate throughput: ~15 commits/day with 14 plans (lower than v3.1's 60/day due to more complex extraction logic per plan)

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 | 46 | 231 | Foundation -- everything from scratch |
| v1.1 | 3 | 12 | Brain-driven gap search feedback loop |
| v1.2 | 6 | 18 | System intelligence + CI guardrails |
| v2.0 | 11 | 32 | Brain architecture overhaul (YAML-first) |
| v3.0 | 9 | 26 | Professional output + shared context |
| v3.1 | 9 | 26 | XBRL-first data integrity + forensics |
| v4.0 | 7 | 12 | Render manifest + output integrity |
| v5.0 | 3 | 10 | Signal architecture v3 (partial) |
| v5.1 | 6 | 13 | Stock analysis + display centralization |
| v6.0 | 9 | 14 | Company profile completeness |

### Top Lessons (Verified Across Milestones)

1. Single source of truth prevents drift -- v1.0 established AnalysisState, v2.0 unified brain YAML, v3.1 unified data traceability via Tier 1 manifest
2. Build the extraction/analysis modules THEN wire them to rendering -- consistently more efficient than trying to do both simultaneously
3. Shadow/parallel evaluation patterns prevent regressions when mass-modifying existing systems
