# D&O Liability Underwriting System

## What This Is

A complete Directors & Officers liability underwriting analysis system (Angry Dolphin Underwriting) that ingests a stock ticker and produces an exhaustive risk assessment worksheet. It pulls 100% publicly available data — SEC EDGAR filings (via LLM extraction), court records, governance data, financial metrics, news, and web sources — analyzes the company across every dimension that predicts D&O claims using a 400-check YAML brain framework, benchmarks against industry peers, surfaces red flags with peril-organized scoring, and outputs an HTML/Word/PDF document giving an underwriter the deepest possible insight into the risk. The HTML output matches institutional presentation quality (S&P Capital IQ layout density). Built as a CLI tool (`do-uw analyze <TICKER>`), outputs to `output/<TICKER>/`.

## Core Value

Surface every red flag and risk signal that exists in public data for any publicly traded company, benchmarked against industry peers, so an underwriter can make the most informed D&O decision possible.

## Requirements

### Validated

- ✓ 7-stage pipeline: RESOLVE→ACQUIRE→EXTRACT→ANALYZE→SCORE→BENCHMARK→RENDER — v1.0
- ✓ Single AnalysisState Pydantic model as only source of truth; no file over 500 lines — v1.0
- ✓ SEC EDGAR data pipeline (10-K, 10-Q, 8-K, DEF 14A, Form 4, CORRESP, S-1, NT) via edgartools + LLM extraction — v1.0
- ✓ Market data pipeline (yfinance: price history, volatility, short interest, analyst consensus) — v1.0
- ✓ Litigation data pipeline (Stanford SCAC, CourtListener, SEC enforcement, Item 3 extraction) — v1.0
- ✓ Governance data pipeline (board composition, insider trading, executive compensation, pay ratio) — v1.0
- ✓ Blind spot discovery (broad web search first-class at ACQUIRE start; company+risk-term sweeps) — v1.0
- ✓ Unified YAML brain: 400 self-describing checks, 8-peril framework, 16 causal chains, DuckDB query cache — v1.0
- ✓ 10-factor scoring engine, 11 CRF gates, 17 composite patterns, tier classification WIN→NO TOUCH — v1.0
- ✓ LLM extraction engine (Claude API + instructor) for all SEC filing types with schema versioning & caching — v1.0
- ✓ Actuarial pricing model: ILF-based, DDL scenarios, settlement prediction, tower positioning — v1.0
- ✓ Peer benchmarking: 7-metric registry, ratio-to-baseline percentile proxy, sector-relative context — v1.0
- ✓ HTML worksheet (primary output): two-column CapIQ layout, sticky TOC, peril scoring, company favicon — v1.0
- ✓ Word document output (python-docx), PDF (Playwright from HTML), Markdown (Jinja2) — v1.0
- ✓ Meeting prep companion: 231-question v6 framework across 5 sections, bear case generator — v1.0
- ✓ Multi-ticker validation (AAPL, TSLA, RPM, TEST) calibrated against NERA/Cornerstone/SCAC data — v1.0
- ✓ Knowledge store (SQLite ORM), live learning loop, calibration workflow — v1.0
- ✓ Market intelligence database for pricing comparisons, model-vs-market divergence alerts — v1.0
- ✓ AI Transformation Risk Factor section scoring AI exposure per sector — v1.0
- ✓ 119/119 v1 requirements satisfied — v1.0
- ✓ Brain-driven gap search: targeted web fallback for SKIPPED checks with evidence quality gate — v1.1
- ✓ Check data mapping completeness: all routing gaps fixed, DEF 14A expansion (board profile) — v1.1
- ✓ QA audit source/value column accuracy, threshold_context on TRIGGERED findings — v1.1
- ✓ 14/14 v1.1 requirements satisfied (GAP-01–06, MAP-01–03, QA-01–05) — v1.1
- ✓ Pipeline integrity: signal rename, facet metadata, traceable data routes, rendering completeness audit — v1.2
- ✓ Automated QA: post-run health summary, brain health dashboard, cross-run delta, brain audit — v1.2
- ✓ CI guardrails: test_brain_contract.py enforces data route, threshold, factor/peril mapping — v1.2
- ✓ Feedback loop: reaction capture, proposal generation, YAML write-back with git commit — v1.2
- ✓ Data quality: board director extraction, guidance vs consensus, litigation boilerplate filter, volume spikes — v1.2
- ✓ 18/18 v1.2 requirements satisfied (NOM-01, INT-01–03, FACET-01–04, QA-01–05, FEED-01, DQ-01–04) — v1.2
- ✓ Brain YAML direct runtime loading, Signal Contract V2, declarative mapping + evaluation — v2.0
- ✓ Facet-driven rendering (82 facets, 8 sections), DuckDB scoped to history only — v2.0
- ✓ Closed learning loop: statistical calibration, co-occurrence mining, signal lifecycle state machine — v2.0
- ✓ 28/28 v2.0 requirements satisfied (STORE-01–05, SCHEMA-01–06, MAP-01–04, EVAL-01–05, RENDER-01–04, LEARN-01–04) — v2.0
- ✓ Shared Context Layer: 22 extract_* functions in format-agnostic context_builders/, consumed by HTML + Word — v3.0
- ✓ HTML Visual Polish: CIQ-level density, paired-column KV, sticky headers, tabular-nums, collapsible sections — v3.0
- ✓ Word Adapter: 28 sections consuming shared context, ~6,000 lines of duplication eliminated — v3.0
- ✓ Surface Hidden Data: compensation, peer matrix, NLP dashboard, hazard cards, shade factors, source attribution — v3.0
- ✓ Facet Completion: all 12 brain sections with full facet definitions and templates — v3.0
- ✓ Static Charts: matplotlib stock/radar/ownership charts, SVG sparklines, CSS-only tabbed financials — v3.0
- ✓ PDF Enhancement: CSS running headers/footers, JS-based TOC with page numbers, details expansion — v3.0
- ✓ Narrative Depth: 5-layer architecture, bull/bear framing, confidence calibration, SCR framework — v3.0
- ✓ MCP Integration: CourtListener (federal litigation), FMP (financial ratios), Exa (semantic search) — v3.0
- ✓ QA: visual regression framework, performance budget tests, cross-ticker validation, 5,000+ tests — v3.0
- ✓ 58/58 v3.0 requirements satisfied — v3.0
- ✓ XBRL Foundation: 113+ concepts with sign normalization, derived computation, coverage validation — v3.1
- ✓ 8-quarter XBRL extraction with YTD disambiguation, QoQ/YoY trends, XBRL/LLM reconciliation — v3.1
- ✓ Forensic financial analysis: balance sheet, capital allocation, debt/tax, revenue quality, Beneish decomposition — v3.1
- ✓ 66 new brain signals (25 foundational + 29 forensic + 12 opportunity) wired to XBRL data — v3.1
- ✓ SEC Frames API peer benchmarking: true percentile ranking across all SEC filers — v3.1
- ✓ Form 4 enhancement: ownership concentration, deduplication, gift filtering, exercise-sell patterns — v3.1
- ✓ System integrity: Tier 1 manifest, template-facet validation, semantic QA, learning loop — v3.1
- ✓ 62/62 v3.1 requirements satisfied — v3.1
- ✓ 2-year daily lookback for stock analysis, 3-component return decomposition, peer-relative MDD ratio — v5.1 Phase 88
- ✓ DDL/MDL exposure quantification with 1.8% settlement estimate — v5.1 Phase 89
- ✓ Abnormal return event study with t-stat significance testing — v5.1 Phase 89
- ✓ EWMA volatility (lambda=0.94) with regime detection (LOW/NORMAL/ELEVATED/CRISIS) — v5.1 Phase 89
- ✓ Time-decay weighting on stock drops with per-drop return decomposition — v5.1 Phase 90
- ✓ Corrective disclosure reverse lookup for unexplained drops (8-K + news) — v5.1 Phase 90
- ✓ Chart evaluation thresholds and callout text declared in signal YAML, not Jinja2 templates — v5.1 Phase 91
- ✓ Chart type registry YAML with dynamic function resolution — v5.1 Phase 91
- ✓ CI contract: every extracted model field must have a render path or exclusion — v5.1 Phase 92
- ✓ Post-pipeline render audit with health check heuristics and cross-ticker QA — v5.1 Phase 92
- ✓ 17/17 v5.1 requirements satisfied (STOCK-01–09, DISP-01–04, REND-01–04) — v5.1
- ✓ Business model complexity: revenue type, concentration risk, key person, lifecycle, disruption, margins — 6 BMOD signals — v6.0
- ✓ Operational footprint: subsidiary structure, workforce distribution, resilience, composite complexity score — 4 OPS signals — v6.0
- ✓ Corporate event risk: M&A history, IPO/offering windows, restatements, capital changes, business pivots — 5 EVENT signals — v6.0
- ✓ External environment: regulatory intensity, geopolitical, ESG gap, cyber risk, macro sensitivity — 5 ENVR signals — v6.0
- ✓ Sector risk classification: hazard tier, claim patterns, regulatory overlay, peer comparison — 4 SECT signals — v6.0
- ✓ Structural complexity: disclosure opacity, non-GAAP usage, related parties, OBS exposure, holding structure — 5 STRUC signals — v6.0
- ✓ CI contract tests: signal portability gate, manifest coverage, template purity (zero hardcoded thresholds) — v6.0
- ✓ 37/37 v6.0 requirements satisfied (BMOD-01–06, OPS-01–05, EVENT-01–05, ENVR-01–05, SECT-01–04, STRUC-01–05, RENDER-01–07) — v6.0

- ✓ Canonical Metrics Registry: 22 metrics computed once with XBRL-first source priority, full provenance (source, confidence, as_of) — v12.0
- ✓ Typed Context Models: 5 Pydantic context models (250+ typed fields) with validation wrapper and real-state tests — v12.0
- ✓ Contextual Signal Validation: YAML-driven post-ANALYZE pass annotating false positives (IPO lifecycle, distress safe zone, negation, departed execs) — v12.0
- ✓ Litigation Classification: Legal theory classifier, cross-list dedup, year disambiguation, coverage side badges, missing field flagging — v12.0
- ✓ Output Sanitization: Post-render 4-category cleanup (markdown, Python serial, jargon, debug) with substitution logging — v12.0
- ✓ Quality Gates: Cross-section consistency checker, section completeness gate, real-state integration tests, template-schema CI gate — v12.0
- ✓ Stock Charts: 1Y/5Y with sector ETF overlay, litigation filing date annotations — v12.0

### Active

See REQUIREMENTS.md for v13.0 requirements.

## Current Milestone: v13.0 Worksheet Excellence

**Goal:** Transform the worksheet from data dump to decision document — resilient pipeline, clean naming, visual consistency, manifest wiring, question-driven underwriting, cross-ticker validation.

**Target features:**
- Pipeline & rendering resilience — no crashes on missing data, clear error reporting
- Rename beta_report → worksheet across all files, deduplicate cross-section facts
- Visual consistency — unified CSS stylesheet, print optimization
- Golden manifest wiring — all 27 templates render meaningful content or suppress
- Question-driven underwriting section — 50-80 YAML-driven questions auto-answered from pipeline data
- Cross-ticker validation — 4 company types with golden baselines

## Previous Milestone: v12.0 Output Quality & Architectural Integrity (SHIPPED 2026-03-28)

**Goal:** Eliminate the 5 root causes behind all CUO audit failures through architectural guarantees. 7 phases, 14 plans, 112 commits across 2 days.

## Previous Milestone: v10.0 Underwriting Intelligence (SHIPPED 2026-03-27)

**Goal:** Transform the worksheet from a data report into a senior-underwriter-quality intelligence dossier. Dual-voice pattern, Page-0 dashboard, 13 new analytical sections, Sonnet synthesis, section summary cards, 601 signals.

## Previous Milestone: v9.0 Worksheet Redesign (SHIPPED 2026-03-22)

**Goal:** Transform the worksheet from a 150K-line data dump into a McKinsey-quality infographic presentation that underwriters can read in 15 minutes. Maximum data density, minimal margins, professional visualization-forward design. 7 phases, scoring calibration, section reorder, market condensation, CSS density, inline SVGs, self-review module.

## Previous Milestone: v8.0 Intelligence Dossier (SHIPPED 2026-03-21)

**Goal:** Transform the worksheet from data display to D&O risk intelligence. Every data point gets "so what for D&O?" context through proper brain signal framework. 7 phases, 33 plans, 98 commits, 382 files (+53K lines) across 4 days. Known issues: scoring calibration, worksheet organization, narrative quality gaps.

## Previous Milestone: v7.0 Signal-Render Integrity: RAP Foundation (SHIPPED 2026-03-18)

**Goal:** Full-chain traceability (acquire→signal→score→render), H/A/E risk taxonomy, multiplicative scoring, severity model, pattern engines, adversarial critique, signal-driven scoring, manifest-governed rendering. 14 phases, 34 plans.

## Previous Milestone: v6.0 Company Profile Completeness (SHIPPED 2026-03-14)

**Goal:** Close the company profile gap — every dimension that D&O underwriters evaluate beyond governance/litigation/financials must be extracted, analyzed, and rendered. The worksheet's Business Profile section should match institutional underwriting depth across business model, operational complexity, corporate events, external environment, sector risk, and structural complexity.

## Previous Milestone: v5.1 Stock Analysis Engine + Display Centralization (SHIPPED 2026-03-09)

**Goal:** Complete quantitative stock analysis framework and centralize chart/display configuration into signal YAML with CI-enforced rendering completeness guarantees.

## Previous Milestone: v5.0 Signal Architecture v3 (PARTIALLY SHIPPED 2026-03-08)

**Goal:** Self-contained signals with thin manifest, dependency graph, section YAML elimination. Phases 82-84 completed (architecture). Phases 85-87 (sector-specific risk) deferred to future milestone.

## Previous Milestone: v4.0 Render Manifest & Output Integrity (SHIPPED 2026-03-08)

**Goal:** Guarantee consistent, auditable output by establishing a declared output manifest, enforcing end-to-end signal traceability (acquire→extract→analyze→render), and adding a completeness audit trail.

## Previous Milestone: v3.1 XBRL-First Data Integrity (SHIPPED 2026-03-07)

**Goal:** Eliminate LLM hallucination from all quantitative data. XBRL extraction engine with 113+ concepts, forensic analysis, SEC Frames API peer benchmarking, and closed-loop signal learning.

## Previous Milestone: v3.0 Professional-Grade Output (SHIPPED 2026-03-06)

**Goal:** Transform the D&O worksheet into an institutional-quality analytical briefing — CIQ-level density, professional narratives, interactive charts, and zero hidden data.

### Deferred (future milestones)

- **Industry-Specific Risk Analysis (CRITICAL)** — Every company is currently evaluated through 400 generic D&O signals regardless of industry. The system must probe sector-specific business model risk drivers — the dimensions that actually cause D&O claims in each industry. Requires: (1) industry risk taxonomy mapping SIC/industry to 5-10 key risk dimensions per sector, (2) sector-specific LLM extraction targets via brain_fields dynamic extraction, (3) sector-conditional brain signals that fire only for relevant industries, (4) sector-specific meeting prep questions, (5) true sector peer benchmarking (Visa vs Mastercard, not Visa vs JPM). Data is already acquired (10-K text, XBRL, litigation); gap is in extraction targeting and analytical framework. Examples: credit services needs interchange/MDL litigation, network volume concentration, client incentive trajectory, cross-border regulatory exposure; pharma needs FDA pipeline, patent cliffs, opioid litigation; banks need NIM, loan loss reserves, stress tests.
- Premium pricing calculator calibration against real quotes
- Phase 36: Pricing Model Calibration (market rate database backfill)
- Knowledge management CLI TODO stubs (4 stubs)
- test_render_coverage.py coverage gap (89.1% vs 90%)
- ARCH-02: peer_group.py yfinance EXTRACT-stage fix
- Web UI production deployment

### Out of Scope

- Real-time or sub-minute data freshness — thoroughness over speed
- Proprietary data feeds — system runs entirely on publicly available data
- Automated accept/decline decisions — system surfaces red flags, human makes the decision
- Private company analysis — public companies only (SEC filers)
- International-only companies — US-listed (including ADRs) only
- Mobile app — not needed

## Context

### Current State (v12.0)

- **Codebase:** ~500 Python source files, ~208K LOC; 5,000+ tests passing
- **Tech stack:** Python 3.12, uv, Pydantic v2, httpx, anthropic+instructor (LLM), python-docx, Jinja2, matplotlib, yfinance, edgartools, Playwright, SQLAlchemy 2.0, DuckDB, ruamel.yaml
- **Primary output:** HTML worksheet at `output/<TICKER>/<TICKER>_worksheet.html`
- **Pipeline:** `underwrite <TICKER>` — ~10-20 minutes for full analysis
- **Brain:** 601 YAML signals in `src/do_uw/brain/signals/` (36+ files), 179 XBRL concepts; DuckDB for run history only
- **Rendering:** 100+ HTML templates (12 per-section files), 90+ facets across 12 sections; Word (28+ sections via shared context_builders/); PDF via Playwright with TOC + running headers
- **Quality:** Canonical metrics registry (22 metrics), typed context models (5 Pydantic schemas, 250+ fields), contextual signal validation (YAML-driven), output sanitizer, consistency checker, completeness gate
- **Litigation:** Legal theory classifier, cross-source dedup, year disambiguation, coverage side tagging, missing field flagging
- **Stock charts:** 1Y/5Y with sector ETF overlay, litigation filing date annotations, earnings/drop markers
- **Data**: All public sources — SEC EDGAR + XBRL (primary), SEC Frames API (peer benchmarking), yfinance (market), Stanford SCAC/CourtListener (litigation), Brave Search + Exa (blind spots + gap fallback), FMP (financial ratios), Supabase (6,980 SCA filings)
- **XBRL:** 179 concepts, 8 quarters + 3 annual, sign normalization, derived formulas, coverage validation
- **Scoring:** 10-factor model, 11 CRF gates, 8-peril framework; context-aware sector/size thresholds
- **CI gates:** Signal portability, manifest coverage, template purity, template-schema cross-reference, real-state integration tests

### Predecessor: Underwriting-2.0

A previous version existed at `/Users/gorlin/Desktop/Underwriting-2.0/`. Problems avoided in this rebuild:
1. Monolithic 9,445-line generator → decomposed into modular renderers
2. 4 competing scoring definitions → one authoritative brain YAML
3. 7+ state files → single AnalysisState
4. Deprecated code left importable → zero dead code policy
5. Hardcoded thresholds → all in config JSON/YAML

### Domain Research (25 Years of D&O Data)

Key calibration numbers: 3.8% annual litigation rate (all listed), 6.1% for S&P 500, $14M median settlement (2024), 43-57% dismissal rate, ~3 year average time to settlement. Top loss drivers: financial restatements, stock price drops with corrective disclosures, earnings guidance misses (43% of 2024 filings). Market: $10.8B DWP (2024), 49% loss ratio.

## Constraints

- **Data**: 100% publicly available data only — no proprietary feeds, no paid databases
- **Platform**: Python 3.12+, CLI-first, runs on macOS
- **Architecture**: Modular Python package; no file over 500 lines; single source of truth for every concept
- **MCP limitation**: Background subagents cannot access MCP tools — all data acquisition in main context
- **SEC rate limits**: 10 req/sec max, proper User-Agent required
- **Output**: HTML is primary; Word/PDF/Markdown secondary

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Rewrite execution layer, preserve BRAIN/ knowledge | 43K lines of tangled code vs 1.5MB of clean domain knowledge | ✓ Good — clean architecture from day one |
| Python with uv package manager | Best ecosystem for data, SEC APIs, document generation | ✓ Good — uv sync is fast, lockfile works |
| CLI-first, no web UI in v1 | User works in Claude Code; UI adds complexity without value yet | ✓ Good — delivered faster, HTML output suffices |
| One source of truth for scoring model | Previous version had 4 conflicting definitions | ✓ Good — YAML brain is authoritative, DuckDB is cache |
| Modular template engine for documents | Previous 9,445-line monolith was unmaintainable | ✓ Good — per-section renderers under 500 lines each |
| All MCP data acquisition before agent spawning | Subagent MCP limitation is a hard platform constraint | ✓ Good — clean ACQUIRE/EXTRACT boundary |
| Peer-relative benchmarking for everything | Raw numbers without industry context are not actionable | ✓ Good — ratio-to-baseline proxy works well |
| HTML as primary output (not Word) | HTML is richer, reviewable in browser, CapIQ-quality layout possible | ✓ Good — human review confirmed institutional quality |
| Unified YAML brain (Phase 44) | Split brain (framework YAML + checks JSON + DuckDB) caused drift | ✓ Good — 400 checks in single YAML, Pydantic-validated |
| LLM extraction with instructor (Phases 18-20) | Regex extraction brittle on real SEC filing text variation | ✓ Good — structured output with schema versioning works |
| httpx over requests | Async support, modern API, better performance | ✓ Good — consistent throughout |
| SQLite for local data cache | Simple, no server needed, queryable, portable | ✓ Good — SQLAlchemy 2.0 + Mapped[] annotations work well |
| 7-stage linear pipeline | Clear stage boundaries, single flow, no branching | ✓ Good — PIPELINE_STAGES=7 constant throughout |
| ARCH-02 EXTRACT-stage HTTP accepted exception | peer_group.py yfinance enrichment impractical to move to ACQUIRE | ⚠️ Revisit — documented exception, not a bug |
| Deliverable shift: HTML as primary output | HTML supports richer layout than Word for this use case | ✓ Good — Word still generated, PDF via Playwright |
| Signal architecture constraint for v6.0 | All new data dimensions must be brain signals (no rendering outside signal framework) | ✓ Good — 29 new signals, 37 reqs, zero architectural shortcuts |
| State proxy pattern for signal mappers | Mapper functions need state data but can't import full state module | ✓ Good — reused across ENVR/SECT/BIZ.OPS consistently |
| Text signal counting for composite scores | Structural complexity metrics not available as LLM-extracted structured data | ✓ Good — keyword scanning effective for disclosure opacity |
| REFERENCE_DATA acquisition type | Sector risk data is static (SCAC/NERA studies), not per-company extraction | ✓ Good — claim patterns and regulatory overlay load from YAML tables |
| SIC-to-GICS 3-level fallback | Companies may lack GICS classification; need reliable sector mapping | ✓ Good — SIC→GICS→fallback covers all SEC filers |

| Brain-driven gap search for SKIPPED checks | Structured sources miss blind spots; web fallback catches them | ✓ Good — SKIPPED 68→59, zero false triggers |
| threshold_context on CheckResult | Underwriter needs to see why a check triggered, not just that it did | ✓ Good — human review confirmed |
| DEF 14A board profile expansion | Board diversity/attendance data exists in filings but wasn't extracted | ✓ Good — 5 new fields, validated on AAPL/RPM |
| Brain YAML direct runtime loading (v2.0) | DuckDB intermediary added latency and staleness for signal definitions | ✓ Good — 0.5s load, single source of truth |
| Signal Contract V2 additive schema (v2.0) | Old signals must keep working; new fields optional per signal | ✓ Good — 400 signals load unchanged, V2 fields add declarative paths |
| Facet-driven rendering (v2.0) | Hardcoded renderers can't scale to brain changes | ✓ Good — 82 facets across 8 sections, dispatch from YAML |
| HTML-First Canonical Output (v3.0) | HTML has 90+ templates, 82 facets, all interactive capability; Word reimplements 6K lines | ✓ Good — shared context eliminates duplication |
| XBRL-first quantitative data (v3.1) | LLM hallucination on financial numbers; XBRL is audited/official | ✓ Good — 113+ concepts, zero LLM for quantitative data |
| SEC Frames API peer benchmarking (v3.1) | Ratio-to-baseline proxy was imprecise; real cross-filer data available | ✓ Good — true percentile ranking across all SEC filers |
| Two-tier data acquisition model (v3.1) | Need explicit traceability for all data in the system | ✓ Good — Tier 1 manifest + signal-driven Tier 2 |
| Post-pipeline learning loop (v3.1) | Signals need to self-improve from run data | ✓ Good — auto-calibration proposals, fire-rate alerts |

---
*Last updated: 2026-03-28 after v13.0 milestone started — worksheet excellence: resilience, rename, visual consistency, manifest wiring, Q&A section, cross-ticker validation*
