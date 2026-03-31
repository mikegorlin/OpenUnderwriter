# Milestones

## v12.0 Output Quality & Architectural Integrity (Shipped: 2026-03-28)

**Phases completed:** 7 phases, 14 plans, 23 tasks

**Key accomplishments:**

- Frozen MetricValue/CanonicalMetrics registry with 22 metrics, XBRL-first source priority, and full provenance tracking (source, confidence, as_of) validated against real AAPL state
- Canonical metrics computed once in build_html_context and consumed by 5 highest-duplication builders (key_stats, beta_report, company_profile, scorecard, exec_summary) with full backward compatibility
- 5 Pydantic context models (250+ typed fields) with validation wrapper and real-state tests against AAPL, RPM, and ULS
- All 5 builder calls in build_template_context() wrapped with _validate_context for typed validation with fallback
- YAML-driven validation engine that annotates TRIGGERED signals with false-positive context (IPO lifecycle, distress safe zone, negation language, departed executives) without ever changing signal status
- Post-extraction litigation classifier with 4 public functions covering legal theory classification, cross-list deduplication, year disambiguation, missing field flagging, and boilerplate separation
- Context builder enriched with legal theory labels, coverage side badges, source references, data quality flags, and separated unclassified reserves from classifier output
- HTML and Markdown litigation templates now render all 4 classifier-derived keys: legal theories, coverage side badges, data quality warnings, and unclassified reserves
- Post-render OutputSanitizer with 4-category HTML cleanup (markdown, Python serial, jargon, debug) and substitution logging for upstream fix evidence
- OutputSanitizer integrated into render_html_pdf as post-render safety net, sanitizing both browser and PDF HTML before write with log output
- ConsistencyChecker detects fact contradictions across HTML sections; SectionCompletenessGate suppresses >50% N/A sections with banners pre-render
- Real-state integration tests for 5 context builders plus template-vs-schema CI gate catching drift without MagicMock
- Litigation filing dates render as orange dash-dot vertical lines with abbreviated case names on both 1Y and 5Y stock charts

---

## v8.0 Intelligence Dossier (Shipped: 2026-03-21)

**Phases completed:** 7 phases, 33 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---

## v6.0 Company Profile Completeness (Shipped: 2026-03-14)

**Phases completed:** 9 phases (93-101), 14 plans
**Lines of code:** 149,564 Python source
**Git commits:** 74 over 5 days (2026-03-09 → 2026-03-14)
**Requirements:** 37/37 v6.0 requirements satisfied

**Delivered:** Complete company profile coverage across every dimension D&O underwriters evaluate beyond governance/litigation/financials — business model complexity, operational footprint, corporate events, structural opacity, external environment, and sector risk classification — all expressed as brain signals with evaluation thresholds and manifest-driven rendering, closing the worksheet's institutional depth gap.

**Key accomplishments:**

1. Business model extraction: 6 BMOD brain signals (revenue model type, concentration risk, key person dependency, lifecycle stage, disruption exposure, margin profile) via LLM extraction from 10-K with red/amber/green evaluation thresholds
2. Operational footprint: subsidiary structure from Exhibit 21 with regulatory regime classification, workforce distribution (domestic/international/union), operational resilience indicators — unified into BIZ.OPS.complexity_score (0-20 composite scale)
3. Corporate event risk: 5 BIZ.EVENT signals (M&A history with serial-acquirer detection, IPO/offering Section 11/12 windows, restatement timeline, capital structure changes, business pivots) wired from XBRL forensics
4. Structural complexity: disclosure opacity (risk factor count, FLS density), non-GAAP usage, related party density, off-balance-sheet exposure, holding structure depth — all scored via text signal scanning
5. External environment: regulatory intensity across jurisdictions, geopolitical/sanctions exposure, ESG commitment-vs-performance gap, cyber risk profile, macro sensitivity — 5 ENVR signals
6. Sector risk classification: D&O hazard tier (Highest/High/Moderate/Lower) from SCAC/NERA filing rate data, sector-specific claim patterns, regulatory overlay, peer risk comparison with outlier detection — static reference data with SIC-to-GICS fallback
7. CI contract tests enforcing signal portability (all v3 signals have acquisition+evaluation+presentation), manifest coverage (no orphan groups), and template purity (zero hardcoded thresholds in Jinja2)

**Tech Debt (accepted):**

- 3 HTML stub templates for operational data never expanded (Word/PDF renders, HTML shows nothing)
- context_builders/company.py at 1080 lines (exceeds 500-line limit, needs split)
- RENDER-03 complexity dashboard in Executive Summary skipped per user direction
- Nyquist VALIDATION.md missing for Phases 93-97 (pre-verification-step phases)

---

## v5.1 Stock Analysis Engine + Display Centralization (Shipped: 2026-03-09)

**Phases completed:** 6 phases, 13 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---

## v3.1 XBRL-First Data Integrity (Shipped: 2026-03-07)

**Phases completed:** 9 phases (67-75), 26 plans
**Lines of code:** 135,193 Python source
**Git commits:** 123 over 2 days (2026-03-05 -> 2026-03-07)
**Requirements:** 62/62 v3.1 requirements satisfied

**Delivered:** Comprehensive XBRL-first data integrity layer that eliminates LLM hallucination from all quantitative data -- 113+ XBRL concepts, 8-quarter extraction with trend analysis, forensic financial analysis (balance sheet, revenue quality, capital allocation, debt/tax, Beneish decomposition), SEC Frames API peer benchmarking with true percentile ranking, enhanced Form 4 insider trading, and closed-loop signal learning. LLM shifted to pure analyst role (qualitative/narrative only).

**Key accomplishments:**

1. XBRL concept expansion from 50 to 113+ concepts with sign normalization, derived computation (24 formulas), and coverage validation across all SEC filers
2. 8-quarter XBRL extraction with YTD disambiguation, fiscal period alignment, QoQ/YoY trend computation with acceleration detection, and XBRL/LLM reconciliation (1% divergence threshold)
3. Forensic financial analysis: 4 modules (balance sheet, capital allocation, debt/tax, revenue quality) plus Beneish 8-component decomposition and M&A serial acquirer detection -- all from XBRL, zero LLM
4. 66 new brain signals wired to XBRL data: 25 foundational (Tier 1 manifest), 29 forensic evaluative, 12 opportunity; 18 INACTIVE signals reactivated; shadow evaluation for regression safety
5. SEC Frames API peer benchmarking: true percentile ranking across all SEC filers with SIC-code sector filtering, replacing ratio-to-baseline proxy
6. Form 4 enhancement: ownership concentration tracking, gift/estate filtering, amendment deduplication, exercise-sell pattern detection, filing timing analysis
7. System integrity: Tier 1 data manifest with full traceability, template-facet validation CI, semantic content QA, post-pipeline learning loop with auto-calibration proposals

**Tech Debt (accepted):**

- 3 files over 500 lines (financial_models.py 578, market_events.py 597, financials.py 626) -- pre-existing or declarative Pydantic
- Nyquist VALIDATION.md missing for Phases 67-74
- v3.0 REQUIREMENTS.md traceability table not updated (archived as-is)
- MagicMock junk files from test patches without return_value
- test_enriched_roundtrip.py failing (V2 schema drift in ~16 signals)

---

## v1.0 MVP (Shipped: 2026-02-25)

**Phases completed:** 46 phases (1–45 incl. 10.1), 231 plans, ~400 tasks
**Lines of code:** 114,627 Python source + 78,165 tests (192,792 total)
**Git commits:** 965 over 19 days (2026-02-06 → 2026-02-25)
**Requirements:** 119/119 v1 requirements satisfied

**Delivered:** A complete 7-stage D&O underwriting pipeline that ingests any US public company ticker and produces an institutionally-credible HTML/Word/PDF worksheet surfacing every red flag and risk signal in public data, scored against 400 brain checks, benchmarked against industry peers, with actuarial pricing and meeting prep companion.

**Key accomplishments:**

1. Complete 7-stage pipeline (RESOLVE→ACQUIRE→EXTRACT→ANALYZE→SCORE→BENCHMARK→RENDER) with single AnalysisState Pydantic model as the only source of truth; 398 Python source files, no file over 500 lines
2. LLM extraction engine (Claude API + instructor) for all SEC filing types (10-K, 10-Q, 8-K, DEF 14A, Form 4, 20-F, 6-K) with schema versioning, caching, and anti-hallucination guardrails
3. Unified YAML brain knowledge model — 400 self-describing checks, 8-peril risk framework, 16 causal chains, all Pydantic-validated at load time with DuckDB as query cache rebuilt from YAML
4. HTML worksheet matching S&P Capital IQ institutional presentation quality — two-column layout, sticky TOC, peril-organized scoring, company favicon, institutionally credible per human review
5. 10-factor scoring engine with 11 CRF gates, 17 composite patterns, 8-peril framework, bear case generator, and settlement prediction with DDL scenarios and tower positioning recommendations
6. Actuarial pricing model with ILF-based excess layer pricing, market intelligence database, and model-vs-market divergence alerts
7. Multi-ticker validation (AAPL, TSLA, RPM, TEST) calibrated against Cornerstone/NERA/Stanford SCAC industry data; 366+ tests with pyright strict mode throughout

**Tech Debt (accepted):**

- ARCH-02: peer_group.py uses yfinance at EXTRACT stage (accepted exception — live peer enrichment at ACQUIRE boundary impractical)
- Phase 24: 5 of 7 plans unexecuted (pre-existing partial phase, requirements covered by other phases)
- Phase 36: Pricing Model Calibration never executed (requirements satisfied by Phase 10/10.1/12/27)
- test_render_coverage.py at 89.1% vs 90% threshold (pre-existing since Phase 38-07)
- 4 TODO(45) stubs in knowledge management CLI (non-pipeline)

---

## v1.1 Brain-Driven Acquisition & Data Coverage (Shipped: 2026-02-26)

**Phases completed:** 3 phases (46–48), 12 plans
**Files changed:** 696 files, +12,989 / -3,869 lines
**Git commits:** 58 commits over 1 day (2026-02-25 → 2026-02-26)
**Requirements:** 14/14 v1.1 requirements satisfied (GAP-01–06, MAP-01–03, QA-01–05)

**Delivered:** Brain-driven acquisition feedback loop that closes the gap between the 400-check brain corpus and the acquire stage — SKIPPED checks now get targeted web search fallback, all structured routing gaps are fixed, DEF 14A extraction expanded, and the QA audit output is accurate and trustworthy.

**Key accomplishments:**

1. Brain-driven gap search pipeline: classifies 68 SKIPPED checks by bucket, runs targeted web searches (budget-capped at 15/run) for eligible L2/L3 checks, re-evaluates with confidence=LOW and evidence quality gate preventing false triggers
2. Check data mapping completeness: audited and fixed all routing gaps in FIELD_FOR_CHECK, corrected 10 brain YAML gap_bucket labels, added data_strategy.field_key for governance checks
3. DEF 14A extraction expansion: 5 new BoardProfile fields (gender/racial diversity, meeting count, attendance %, directors below 75% attendance) validated on AAPL/RPM/TSLA
4. threshold_context on CheckResult: every TRIGGERED finding now carries human-readable threshold criterion from brain YAML (e.g., "red: Prior SEC enforcement action within 5 years")
5. Output quality hardening: QA audit source column shows actual filing references, value column displays evaluated data correctly (bool coercion fix), red flags display threshold criteria
6. Regression validated: SKIPPED count dropped from 68 to 59, TRIGGERED count held at 24 on AAPL (no false triggers), output approved on human review

**Tech Debt (accepted):**

- 3 orphaned mapper fields (board_diversity, board_racial_diversity, directors_below_75_pct_attendance) — forward-compatibility stubs for GOV.BOARD.diversity (L1/INVESTIGATION)
- GOV.BOARD.diversity has stale field_key: board_size (check is L1/INVESTIGATION, never evaluates)
- SUMMARY 46-03 missing requirements-completed frontmatter for GAP-02/03/04 (requirements confirmed satisfied via VERIFICATION.md)

---

## v1.2 System Intelligence (Shipped: 2026-02-28)

**Phases completed:** 6 phases (49–52.1), 18 plans
**Git commits:** ~80 commits over 2 days (2026-02-26 → 2026-02-28)
**Requirements:** 18/18 v1.2 requirements satisfied (NOM-01, INT-01–03, FACET-01–04, QA-01–05, FEED-01, DQ-01–04)

**Delivered:** The brain YAML is now the single contract driving the entire pipeline — every signal fully self-describing, every data route verified, every result displayed — with automated QA, underwriter feedback loops, and signal lifecycle management so the brain evolves and optimizes itself.

**Key accomplishments:**

1. Pipeline integrity: "check" renamed to "signal" system-wide; every brain signal has facet, display spec, traceable data route via `brain trace`; rendering completeness auditable via `brain render-audit`
2. Facet-driven section rendering: HTML section grouping driven by facet definitions (not hardcoded _PREFIX_DISPLAY); facets are authoritative for layout
3. Automated QA: post-run health summary, `brain health` unified dashboard, `brain delta` cross-run comparison, `brain audit` staleness/coverage/threshold analysis
4. CI guardrails: `test_brain_contract.py` fails build if any ACTIVE signal lacks data route, threshold, v6_subsection_ids, or factor/peril mapping
5. Feedback loop: underwriter reactions captured via `feedback` CLI, batch-processed into calibration proposals, applied to brain YAML with `apply-proposal` + git commit
6. Data quality: board directors extracted from DEF 14A with qualifications, guidance vs consensus distinguished, litigation boilerplate filtered, volume spike detection with event correlation

**Tech Debt (accepted):**

- signal_mappers.py at 505 lines (tech debt from Phase 52-04, defer split)
- 12 GOV signals SKIPPED due to LLM extraction quality on DEF 14A (correct wiring, data not populated)
- 20 GOV signals INACTIVE (no viable extraction path — preserved for audit trail)

---
