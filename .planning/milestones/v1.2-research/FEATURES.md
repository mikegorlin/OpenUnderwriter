# Feature Landscape: System Intelligence

**Domain:** Knowledge-driven D&O underwriting analysis system -- pipeline integrity, automated QA, feedback loops, signal lifecycle management
**Researched:** 2026-02-26
**System context:** 400-check YAML brain, 7-stage pipeline (RESOLVE through RENDER), DuckDB cache, existing CLI (`do-uw analyze/brain/feedback/ingest/validate/dashboard/calibrate`)

---

## Table Stakes

Features the system must have to be considered "self-aware" and operationally trustworthy. Missing any of these means the brain YAML contract is aspirational rather than enforced.

| Feature | Why Expected | Complexity | Dependencies | User-Observable Behavior |
|---------|--------------|------------|--------------|--------------------------|
| **Pipeline integrity audit (close the SKIPPED gap)** | v1.1 Phase 47 classified all 68 SKIPPED checks into 4 populations. Phase 48 verification confirmed SKIPPED=68 still in live runs -- Population B (34 DEF14A checks) have extraction schema but LLM extraction does not populate values. The brain contract says "every check has a data route." 68 SKIPPED checks means 17% of the brain is dead weight. | Med | `pipeline_audit.py`, `gap_detector.py`, `FIELD_FOR_CHECK`, DEF14A extraction schema (exists from Phase 47), LLM extraction prompts | `do-uw analyze AAPL` produces SKIPPED < 40 (Population A intentionally-unmapped is 20; remaining 48 should evaluate). `do-uw brain gaps` shows zero CRITICAL gaps. |
| **End-to-end data route traceability** | When an underwriter asks "where did this number come from?", the system must answer in one command. Currently requires reading YAML `data_strategy`, then `check_field_routing.py`, then `check_mappers.py`, then extraction schemas -- 4 files across 3 directories. | Med | Brain YAML `data_strategy` + `data_locations` fields, `FIELD_FOR_CHECK` registry, `check_mappers*.py`, extraction schemas | `do-uw brain trace FIN.LIQ.position` prints: `SEC_10Q -> llm_financials.py (balance_sheet.current_ratio) -> FIELD_FOR_CHECK[FIN.LIQ.position] -> check_evaluators.py (tiered) -> QA audit row + management section`. One command, full chain. |
| **Post-run validation** | Every `do-uw analyze` run should end with a health check. Currently the pipeline silently completes even when anomalous (e.g., 0 TRIGGERED on a company with known SCA litigation, or 100% SKIPPED on a company with full SEC filings). v1.1 Phase 48 exposed that SKIPPED=68 was not caught until manual verification. | Med | `AnalysisState` model, `check_results`, `brain_check_runs` table, `test_regression_baseline.py` thresholds | After every `do-uw analyze` run, console prints: "Validation: 332/400 evaluated, 24 TRIGGERED, 68 SKIPPED (20 intentional). Anomalies: none." If TRIGGERED=0 on a company with litigation data: "WARNING: 0 TRIGGERED but litigation data present -- review LIT.* checks." |
| **Coverage metrics (unified health view)** | Existing CLI has 4 separate commands for overlapping health data: `brain status` (check counts, lifecycle), `brain effectiveness` (fire rates), `brain gaps` (gap detection), `knowledge learning-summary` (run stats). An operator needs ONE view to understand system health. | Med | `brain_effectiveness.py`, `pipeline_audit.py`, `brain_check_runs` table, `brain_checks_active` view, existing CLI commands | `do-uw brain health` prints a single dashboard: total active checks, coverage % (evaluated/total), fire rate distribution histogram, top-5 never-fire checks, top-5 always-fire checks, top-5 high-skip checks, data freshness (last run date per ticker), feedback queue depth. |
| **CI guardrails (brain contract tests)** | When someone adds a new check to brain YAML, CI must fail if the check lacks: a data route (field_key or FIELD_FOR_CHECK), a threshold definition, v6_subsection_ids, at least one factor or peril_id. Existing tests cover fragments: `test_enrichment_coverage.py` checks v6 subsection coverage, `test_zero_coverage_checks.py` checks specific Phase 33 checks, `test_brain_loader.py` validates schema. No unified contract test exists. | Low | Existing test infrastructure, `BrainCheckEntry` schema, `FIELD_FOR_CHECK`, `HANDLED_PREFIXES` | `pytest tests/brain/test_brain_contract.py` runs in CI. Fails with explicit message: "CHECK BIZ.NEW.check has no data route: missing field_key AND no FIELD_FOR_CHECK entry." New check addition requires satisfying the contract before tests pass. |
| **Rendering completeness audit** | Every non-SKIPPED check should appear in the HTML output somewhere. Facet YAML files declare signals (`governance.yaml` declares 12 GOV.* signals), but no automated verification confirms those signals actually render. Phase 48 verified facets exist but not that all declared signals are populated. | Med | `brain_facet_schema.py`, facet YAML files (`facets/governance.yaml`, `facets/red_flags.yaml`), `html_checks.py`, `_get_facets()`, `_group_checks_by_section()` | `do-uw brain render-audit` reports: "governance facet: 12 signals declared, 10 populated, 2 missing (GOV.BOARD.expertise, GOV.BOARD.ceo_succession_plan -- data not extracted). red_flags facet: 0 signals declared (dynamic), 24 TRIGGERED findings rendered." |

---

## Differentiators

Features that elevate the system from "working tool" to "self-improving knowledge system." Not expected in most underwriting tools, but high value for long-term accuracy and trust.

| Feature | Value Proposition | Complexity | Dependencies | User-Observable Behavior |
|---------|-------------------|------------|--------------|--------------------------|
| **Underwriter feedback loop (end-to-end)** | The CLI and storage exist (`do-uw feedback add`, `feedback.py`, `brain_feedback` table, `FeedbackEntry/ProposalRecord` models). What is missing: feedback does not automatically generate calibration proposals, and the proposal-to-apply pipeline has not been tested end-to-end. Closing this loop means the system learns from every human review. | Med | `cli_feedback.py` (add/summary/list), `feedback.py` (record/query), `calibrate.py` (preview/apply), `calibrate_impact.py` (impact sim), `BrainWriter` (versioned writes) | Full loop: `do-uw feedback add AAPL --check FIN.LIQ.position --type THRESHOLD --direction TOO_SENSITIVE --note "1.2 ratio is normal for tech"` -> system auto-generates proposal -> `do-uw calibrate preview` shows impact -> `do-uw calibrate apply 42` changes brain YAML with git commit. |
| **Signal lifecycle management** | Checks must evolve. New risks emerge (AI liability, crypto exposure, ESG litigation), old risks become irrelevant. The lifecycle state machine exists (`lifecycle.py`: INCUBATING -> DEVELOPING -> ACTIVE -> DEPRECATED) and `BrainWriter` supports versioned transitions. What is missing: no automated lifecycle review that analyzes fire rates, feedback volume, and market intelligence to PROPOSE transitions. Currently all transitions are manual. | High | `lifecycle.py` state machine, `brain_effectiveness.py` (fire rates, never-fire/always-fire detection), `brain_feedback` table, `brain_check_runs`, `BrainWriter` versioning, `brain_backlog` table | `do-uw brain lifecycle review` analyzes all ACTIVE checks and produces: "DEPRECATION CANDIDATES: 3 checks never fired across 12 runs (GOV.EFFECT.iss_score, GOV.EFFECT.proxy_advisory, EXEC.CEO.risk_score). PROMOTION CANDIDATES: 2 INCUBATING checks with evidence from ingestion (BIZ.AI.model_risk, LIT.REG.ai_governance). RECALIBRATION: 4 checks fire in 100% of runs (GOV.PAY.ceo_total_comp, GOV.PAY.say_on_pay, STOCK.PRICE.volatility_52w, STOCK.PRICE.beta) -- thresholds may be too loose." Human approves all transitions. |
| **Knowledge ingestion (document -> brain proposals)** | The D&O landscape changes: new SEC rules, landmark settlements, emerging claim theories. The ingestion pipeline exists (`ingestion.py`, `ingestion_llm.py`, `cli_ingest.py` with file/url commands, `DocumentType` enum, `discovery.py` for blind spot auto-analysis). What is missing: the LLM ingestion path (`ingestion_llm.py`) has not been tested against real documents, and the proposal output does not flow into the calibration review pipeline. | High | `ingestion.py` (regex-based), `ingestion_llm.py` (LLM-based), `ingestion_models.py` (DocumentIngestionResult, IngestionImpactReport), `cli_ingest.py` (file, url commands), `discovery.py` (blind spot scoring), `BrainWriter` | `do-uw ingest file "2025-sec-enforcement-trends.pdf"` -> LLM extracts D&O implications -> identifies affected checks + gaps -> generates INCUBATING check proposals -> `do-uw brain backlog` shows new items -> `do-uw calibrate preview` shows impact. |
| **Anomaly detection (cross-run)** | When AAPL suddenly triggers 15 checks that were clear last quarter, something changed. The system stores historical run data (`brain_check_runs` table) and can compute deltas. No existing command surfaces cross-run anomalies. | Med | `brain_check_runs` table (populated by pipeline after ANALYZE), `brain_effectiveness.py`, historical `AnalysisState` outputs | After `do-uw analyze AAPL`: "DELTA from last run (2026-01-15): 6 checks flipped CLEAR->TRIGGERED (FIN.REV.recognition, LIT.SCA.pending_action, ...). 2 checks flipped TRIGGERED->CLEAR. Net risk change: +4 triggered." Also available via `do-uw brain delta AAPL`. |
| **Feedback-driven threshold calibration** | When 3+ underwriters flag the same check as TOO_SENSITIVE or TOO_LOOSE, the system should aggregate this signal, propose a specific threshold change, backtest it against all stored runs, and show before/after impact. The `calibrate.py` preview and `backtest.py` exist but are not wired to feedback aggregation. | High | `feedback.py` (aggregation queries), `calibrate.py` (preview/apply), `calibrate_impact.py` (what-if simulation), `backtest.py` (historical re-evaluation), `BrainWriter` | `do-uw calibrate preview` shows: "CHECK FIN.LIQ.position: 3 TOO_SENSITIVE feedbacks. Current red: <1.0. Proposed red: <0.8. Backtest (12 runs): false positives -40%, true positives unchanged. Confidence: MEDIUM (small sample)." |
| **Brain health periodic audit** | Comprehensive audit beyond single-run validation: stale checks (provenance.last_validated > 6 months), coverage imbalance across perils (some perils have 80 checks, others have 5), threshold conflicts (overlapping checks with contradictory thresholds), orphaned checks (in DuckDB but not in YAML). | Med | Brain YAML `provenance` field, `brain_check_runs`, peril/factor taxonomy, `brain_checks` table versioning | `do-uw brain audit` prints: "STALENESS: 12 checks have provenance.last_validated=null (never validated). IMBALANCE: Peril P1 (Securities Fraud) has 45 checks; Peril P7 (Fiduciary Breach) has 8. CONFLICTS: FIN.LIQ.position and FIN.LIQ.working_capital both trigger at current_ratio < 1.0 (redundant). ORPHANS: 0 checks in DuckDB not in YAML." |
| **Market intelligence auto-proposals** | `discovery.py` scores blind spot search results for D&O relevance (keyword density scoring). Wire this so every pipeline run automatically surfaces emerging risks and creates INCUBATING proposals without human initiation. All proposals still require human approval. | Med | `discovery.py` (relevance scoring, `_DO_KEYWORDS`), `ingestion_llm.py` (LLM analysis), `BrainWriter`, `brain_proposals` table | After `do-uw analyze AAPL` blind spot search: "Discovery: 2 high-relevance items found. (1) 'Apple faces EU Digital Markets Act probe' (relevance: 8/10) -> proposed check: LIT.REG.eu_dma_probe. (2) 'Former VP sued for trade secret theft' (relevance: 6/10) -> proposed check: LIT.OTHER.executive_trade_secret. Proposals stored for review." |

---

## Anti-Features

Features to explicitly NOT build. These are tempting but would violate core principles, add complexity without value, or create maintenance burden.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Auto-apply brain changes without human approval** | The system proposes, the human disposes. `calibrate.py` docstring: "Nothing auto-changes. All calibration requires explicit human approval via CLI." Auto-applying threshold changes or promoting INCUBATING checks without review removes the underwriter from the loop and creates silent knowledge drift. | Keep the proposal -> review -> approve -> apply workflow. Every brain mutation requires explicit `do-uw calibrate apply <ID>`. |
| **Real-time pipeline monitoring (Prometheus/Grafana)** | The system runs on-demand (10-20 min per ticker). There is no production server, no persistent process, no SLA. Monitoring infrastructure for a CLI tool is massive overhead for zero value. | Post-run validation at the end of each pipeline execution. On-demand `do-uw brain health` for periodic audits. |
| **ML-based automatic threshold optimization** | With 3-4 tickers in the validation set and maybe 12 historical runs, there is catastrophically insufficient data to train ML models. ML would overfit to a tiny sample and produce unreliable thresholds. The D&O domain has 25 years of calibration data (NERA, Cornerstone) that the brain already encodes via expert-authored thresholds. | Use underwriter feedback + domain expertise for threshold calibration. Log all outcomes for future ML when sample reaches 50+ companies. Use `expected_fire_rate` field (already in brain schema) as a calibration reference. |
| **Web UI for brain CRUD operations** | A web UI for browsing/editing brain YAML adds a full web framework, authentication, state management, and a competing mutation surface alongside the CLI. The existing `dashboard serve` command provides read-only visualization via FastAPI. Adding write capability means maintaining two input paths. | CLI-only for brain mutations via `do-uw brain`, `do-uw feedback`, `do-uw calibrate`, `do-uw ingest`. Dashboard remains read-only. |
| **Automated check generation from bulk SEC filing analysis** | Generating checks by scanning hundreds of SEC filings with LLM would produce high-volume, low-quality checks. The brain's value is curation (400 expert-authored checks across 25 years of D&O claims data), not volume. | Use `do-uw ingest` for targeted document analysis that produces INCUBATING proposals for human review. Quality over quantity. |
| **Cross-company correlation engine** | Detecting "when company A triggers check X, company B in the same sector likely triggers check Y" requires a graph database, large historical dataset, and statistical validation infrastructure. Premature with < 10 companies analyzed. | Use existing peer benchmarking (7-metric registry, ratio-to-baseline) for sector-relative context. Log cross-run data for future analysis. |
| **Push notifications / alerting system** | Email alerts, Slack webhooks, or push notifications for brain health issues or pipeline failures. Adds external service dependencies and configuration complexity for what is currently a single-operator CLI tool. | Print warnings and anomalies to console during pipeline runs. `do-uw brain health` and `do-uw brain audit` for on-demand checks. |
| **Version control UI for brain YAML** | A visual diff/merge UI for brain check changes. Tempting when multiple people edit brain YAML, but currently there is one operator. Git already provides version control, and `BrainWriter` creates versioned rows with changelog entries. | Use git for version control. `BrainWriter` creates append-only version rows. `do-uw brain changelog` shows recent changes. |

---

## Feature Dependencies

```
Pipeline Integrity Audit -----> End-to-End Data Route Tracing
       |                                    |
       v                                    v
CI Guardrails (brain tests) <--- Rendering Completeness Audit
       |
       v
Coverage Metrics Dashboard ----> Brain Health Periodic Audit
       |                                    |
       v                                    v
Post-Run Validation ---------> Anomaly Detection (cross-run)
       |
       v
Underwriter Feedback CLI -----> Feedback-Driven Threshold Calibration
       |                                    |
       v                                    v
Knowledge Ingestion Pipeline -> Market Intelligence Auto-Proposals
       |
       v
Signal Lifecycle Management (capstone: depends on feedback data, fire rates, ingestion proposals)
```

### Dependency Explanation

1. **Pipeline Integrity must come first.** You cannot validate what you cannot trace. The audit identifies gaps (Population B DEF14A checks not populating); tracing explains them (extraction schema exists but LLM prompts do not extract the fields); CI prevents new gaps from being introduced.

2. **Coverage Metrics depends on clean pipeline integrity.** Metrics are meaningless if the underlying data routes are broken. "Coverage = 83%" is useless if the 17% gap is due to wiring bugs rather than genuine data absence.

3. **Post-Run Validation depends on coverage metrics** to establish baselines for "normal." You need to know the expected SKIPPED count, expected TRIGGERED range, and expected coverage % before you can flag anomalies.

4. **Feedback CLI depends on post-run validation.** Underwriters need to see validated, trusted output before they can provide meaningful feedback. If the output shows "---" for source and value (Phase 48's starting state), feedback is noise.

5. **Knowledge Ingestion depends on feedback infrastructure.** Ingested documents create proposals that flow through the same proposal -> review -> apply pipeline as feedback-driven proposals. The infrastructure must be proven with feedback before adding the ingestion path.

6. **Signal Lifecycle is the capstone.** It consumes fire rates (from brain_check_runs), feedback signals (from brain_feedback), and ingestion proposals (from brain_proposals) to recommend lifecycle transitions. All three data streams must be operational before lifecycle review produces useful results.

---

## MVP Recommendation

### Phase 1: Foundation (Pipeline Integrity + CI)

Build trust in the brain contract.

1. **Fix Population B DEF14A extraction** -- The extraction schema exists (Phase 47), but LLM prompts do not extract the 5 new board governance fields from actual proxy statements. Fix the LLM extraction so live runs populate these fields, reducing SKIPPED from 68 toward 34 (Population A remains intentionally-unmapped at 20).
2. **Write unified CI brain contract test** -- `test_brain_contract.py` that validates every ACTIVE check has: data route, threshold, v6_subsection_ids, peril/factor mapping. Run in CI. Prevents future regressions.
3. **Implement `do-uw brain trace <CHECK_ID>`** -- Single-command traceability for any check.

### Phase 2: Validation + Visibility

Catch problems automatically.

4. **Post-run validator** -- Runs after every `do-uw analyze`, prints health summary, flags anomalies (0 TRIGGERED with litigation data, SKIPPED count above threshold).
5. **Unified `do-uw brain health`** -- Compose existing status, effectiveness, gaps, and learning-summary into one dashboard command.
6. **Rendering completeness audit** -- Cross-reference facet declarations vs actual rendered signals.

### Phase 3: Feedback Loop

Close the human-in-the-loop cycle.

7. **Wire feedback end-to-end** -- Feedback -> proposal auto-generation -> calibrate preview -> apply. Test the full loop with real feedback entries.
8. **Anomaly detection (cross-run)** -- Compare current run to historical runs, surface CLEAR->TRIGGERED flips.

### Phase 4: Knowledge Evolution

Make the brain self-improving.

9. **Knowledge ingestion (real-world testing)** -- Test `do-uw ingest` against actual SEC enforcement releases, short seller reports, claims studies. Tune LLM prompts. Wire proposals into calibration review.
10. **Signal lifecycle review** -- `do-uw brain lifecycle review` analyzes all checks using accumulated data, proposes promotions/deprecations/recalibrations.
11. **Market intelligence auto-proposals** -- Wire `discovery.py` to auto-create proposals from blind spot search results.

### Defer to Future Milestones

- **Feedback-driven threshold calibration with backtest** -- Requires 10+ feedback entries per check. Build logging infrastructure now, defer automated proposal generation until data volume supports it.
- **Brain health periodic audit (staleness, imbalance, conflicts)** -- Useful but not urgent. The brain is freshly authored (v1.0 was 2026-02-25). Staleness becomes relevant 6+ months from now.

---

## Existing Infrastructure Inventory

What already exists vs what needs building for each feature.

| Feature | Already Built | Needs Building |
|---------|--------------|----------------|
| Pipeline integrity (close SKIPPED gap) | `pipeline_audit.py`, `gap_detector.py`, `FIELD_FOR_CHECK` (247 entries), DEF14A schema with 5 new fields, `BoardProfile` with SourcedValue fields, `convert_board_profile()` | Fix LLM extraction prompts to actually populate board governance fields from proxy statements. Validate SKIPPED reduction on AAPL/RPM live runs. |
| End-to-end traceability | `data_strategy` and `data_locations` in 400 YAML checks, `check_field_routing.py`, `check_mappers*.py` (5 mapper files), extraction schemas | `do-uw brain trace` CLI command that walks the chain: YAML -> extraction -> mapper -> evaluator -> renderer. |
| Post-run validation | `AnalysisState` with full pipeline state, `test_regression_baseline.py` with SKIPPED_FLOOR/TRIGGERED_CEILING, `brain_check_runs` recording | Validator module that runs after RENDER. Anomaly detection rules (0 TRIGGERED + litigation present, SKIPPED above threshold, score out of range). Console output format. |
| Coverage metrics dashboard | `brain status` (counts, lifecycle), `brain effectiveness` (fire rates), `brain gaps` (gap detection), `knowledge learning-summary` (run stats) -- all exist as separate CLI commands | Unified `do-uw brain health` command that composes all four. Fire rate distribution histogram. Data freshness tracking. |
| CI guardrails | `test_enrichment_coverage.py` (v6 subsection coverage), `test_zero_coverage_checks.py` (Phase 33 checks), `test_brain_loader.py` (schema validation), `test_brain_writer.py` (versioned writes) | Unified `test_brain_contract.py`: every ACTIVE check has data_route + threshold + v6_subsection + factor/peril. |
| Rendering completeness | `brain_facet_schema.py` (FacetSpec model), facet YAML files, `_get_facets()`, `_group_checks_by_section()` | `do-uw brain render-audit` cross-reference command. |
| Feedback loop (end-to-end) | `cli_feedback.py` (add/summary/list), `feedback.py` (record/query/mark_applied), `feedback_models.py` (FeedbackEntry/ProposalRecord/FeedbackSummary), `calibrate.py` (preview/apply), `calibrate_impact.py` (impact sim, git commit), `backtest.py` | Auto-proposal generation from THRESHOLD/ACCURACY feedback. End-to-end integration test. Real-world testing. |
| Signal lifecycle | `lifecycle.py` (state machine: INCUBATING/DEVELOPING/ACTIVE/DEPRECATED, valid transitions, transition_check()), `BrainWriter` (insert_check, promote_check, retire_check, versioned rows), `brain_checks_active` view (excludes INCUBATING/INACTIVE) | Lifecycle review command. Automated analysis of fire rates + feedback + age to generate transition proposals. |
| Knowledge ingestion | `ingestion.py` (regex-based ingestion for .txt/.md), `ingestion_llm.py` (LLM-based for any document type), `ingestion_models.py` (DocumentIngestionResult, ProposedNewCheck), `cli_ingest.py` (file/url commands with Rich display), `discovery.py` (blind spot relevance scoring) | Real-world testing against actual documents. LLM prompt tuning. Proposal -> calibration pipeline wiring. |
| Anomaly detection | `brain_check_runs` stores run_id, check_id, status, ticker, timestamp. `brain_effectiveness.py` computes fire_rate, skip_rate per check. | Cross-run delta computation. New `do-uw brain delta <TICKER>` command. Alert threshold configuration. |
| Threshold calibration | `calibrate.py` (CalibrationPreview model, preview pending proposals, apply with git), `calibrate_impact.py` (compute_changes, run_impact_simulation, git_commit_calibration), `backtest.py` (historical re-evaluation) | Feedback aggregation -> auto-proposal pipeline. Backtest integration with calibrate preview (show before/after on historical data). |
| Brain health audit | `brain status` (lifecycle counts, content type breakdown), `provenance` field in brain YAML (origin, last_validated, source_date), `brain_check_runs` | Staleness detector (provenance.last_validated age). Coverage balance analyzer (checks per peril/factor). Threshold conflict detector (overlapping checks). `do-uw brain audit` command. |
| Market intelligence auto-proposals | `discovery.py` (relevance scoring with `_DO_KEYWORDS`, `_RELEVANCE_THRESHOLD`), `ingestion_llm.py` (can analyze search results), `BrainWriter` (can create INCUBATING checks) | Wire discovery -> ingestion_llm -> BrainWriter pipeline end-to-end in post-acquisition hook. Auto-create INCUBATING proposals. |

---

## Sources

### Codebase (HIGH confidence -- direct inspection)

- `src/do_uw/brain/` -- brain_check_schema.py, brain_effectiveness.py, brain_schema.py (19 tables, 11 views), brain_writer.py, brain_facet_schema.py, facets/, checks/
- `src/do_uw/knowledge/` -- lifecycle.py, feedback.py, feedback_models.py, calibrate.py, calibrate_impact.py, backtest.py, ingestion.py, ingestion_llm.py, discovery.py, gap_detector.py
- `src/do_uw/stages/analyze/` -- pipeline_audit.py, gap_revaluator.py, check_field_routing.py, check_engine.py, check_evaluators.py
- `src/do_uw/cli_*.py` -- cli_feedback.py, cli_brain.py, cli_validate.py, cli_dashboard.py, cli_ingest.py, cli_knowledge.py, cli_calibrate.py
- `tests/brain/` -- test_brain_effectiveness.py, test_enrichment_coverage.py, test_zero_coverage_checks.py, test_brain_loader.py, test_brain_writer.py
- v1.1 verification: Phase 47 (PASSED 14/14), Phase 48 (3/4, SKIPPED=68 gap, TSLA not run)

### Domain Research (MEDIUM confidence -- web search, multiple sources agree)

- Data pipeline observability patterns: [Monte Carlo - Data Pipeline Monitoring](https://www.montecarlodata.com/blog-data-pipeline-monitoring/), [IBM - Data Observability Model](https://www.ibm.com/think/insights/a-data-observability-model-for-data-engineers), [Datafold - Pipeline Monitoring](https://www.datafold.com/blog/what-is-data-pipeline-monitoring)
- Rule engine lifecycle: [Decisions.com - Rules Engine Trends 2025](https://decisions.com/the-evolving-power-of-rules-engines-trends-to-watch-in-2025/), [RulesEngine.dev - Best Practices](https://rulesengine.dev/article/Best_Practices_for_Implementing_a_Business_Rules_Engine.html)
- Expert systems knowledge evolution: [ScienceDirect - Epistemology of Rule-Based Expert Systems](https://www.sciencedirect.com/science/article/abs/pii/0004370283900085)
- Insurance underwriting rule engines: [Higson - Underwriting Risk Management](https://www.higson.io/blog/underwriting-risk-management), [Deloitte - Future of Insurance Underwriting](https://www.deloitte.com/us/en/insights/industry/financial-services/future-of-insurance-underwriting.html)
- Insurance underwriting feedback loops: [Insurance Journal - Underwriting at an Inflection Point](https://www.insurancejournal.com/news/international/2026/02/05/856854.htm)
