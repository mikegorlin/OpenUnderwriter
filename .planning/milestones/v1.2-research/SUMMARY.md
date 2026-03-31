# Project Research Summary

**Project:** D&O Underwriting Worksheet System — v1.2 System Intelligence Additions
**Domain:** Pipeline diagnostics, automated QA, feedback loops, signal lifecycle, knowledge ingestion, CI guardrails
**Researched:** 2026-02-26
**Confidence:** HIGH — all four research domains derived from direct codebase audit of v1.0/v1.1

## Executive Summary

v1.2 is an operational intelligence milestone: the goal is to make a working 400-check D&O pipeline self-aware, self-validating, and self-improving. The central research finding is that most of the infrastructure for all six feature areas already exists in v1.0/v1.1 — what is missing is wiring, last-mile completion, and consolidation. This makes v1.2 fundamentally an integration milestone rather than a build-from-scratch effort. The recommended approach is to extend existing modules with thin wiring, add new files (never new runtime libraries), and resist the temptation to unify overlapping subsystems prematurely.

The central architectural insight across all six features is that they share a single control flow pattern: pipeline run produces data -> analytics detect signal -> system generates proposal -> human reviews and approves -> brain YAML is modified -> `brain build` resyncs DuckDB -> CI guardrails validate result. Building anything outside this pattern — auto-applying changes, storing mutations in DuckDB without corresponding YAML update, skipping human review — is the root cause of the project's predecessor failures. The brain YAML must remain the singular source of truth throughout v1.2. The sole new dependency is `pre-commit` (dev-only); all runtime features use the existing stack.

The primary risks are: (1) pipeline integrity work that accidentally modifies working checks — mitigated by making the audit strictly read-only in its first phase and requiring a `{check_id: status}` snapshot diff before any change; (2) automated QA that produces false positives and erodes underwriter trust — mitigated by structural-only QA rules with < 5% false positive rate before deployment; and (3) feedback infrastructure that collects data but never closes the loop to brain YAML changes — mitigated by building the `apply-proposal` workflow as a non-negotiable part of the feedback phase, not a follow-on.

## Key Findings

### Recommended Stack

The v1.2 stack requires exactly one new dependency: `pre-commit` (dev-only) for CI guardrails. Every runtime feature is implementable with the existing library stack. The codebase already contains DuckDB analytics (`brain_effectiveness.py`, `brain_schema.py`), Pydantic models for all feature domains, a Typer CLI framework, LLM extraction via instructor, and QA infrastructure in `validation/`. Adding new runtime libraries would violate CLAUDE.md's anti-context-rot rules and create unnecessary maintenance surface.

**Core technologies (roles in v1.2):**
- DuckDB (>=1.4.4): Extends brain analytics cache — pipeline run history, effectiveness metrics, feedback storage, new `brain_audit_results` and `brain_ingestion_log` tables
- Pydantic v2 (>=2.10): All new models — DiagnosticsReport, BrainAuditReport, FeedbackProcessReport, event types
- Typer (>=0.15): New subcommands — `brain health`, `brain audit`, `brain trace`, `brain lifecycle`, `feedback process`, `ingest event`
- Rich (>=13.0): Terminal dashboards for all diagnostic output — no web framework needed
- pre-commit (>=4.0, dev-only): Git hook framework for brain YAML validation at commit time

**Stack decision to watch:** The codebase has two overlapping data stores — `brain.duckdb` (DuckDB) and `knowledge.db` (SQLite via SQLAlchemy). Research recommends NOT attempting full convergence in v1.2. Instead, migrate only lifecycle tracking from SQLite to DuckDB (well-bounded), leave pricing/playbooks in SQLite, and defer complete unification to v1.3 once v1.2 validates DuckDB for all system intelligence workloads.

See `.planning/research/STACK.md` for full feature-by-feature analysis.

### Expected Features

**Must have (table stakes — system is not operationally trustworthy without these):**
- Pipeline integrity audit closing the SKIPPED gap — 68 SKIPPED checks (17% of brain) means the brain contract is aspirational; Population B DEF14A extraction schema exists but LLM prompts do not populate the 5 new board governance fields
- End-to-end data route traceability — `do-uw brain trace <CHECK_ID>` answers "where does this data come from?" in one command, replacing current 4-file/3-directory hunt
- Post-run validation — every `do-uw analyze` run must end with a health summary and anomaly flags (e.g., 0 TRIGGERED when litigation data is present)
- Unified coverage metrics dashboard — consolidate four separate CLI commands (`brain status`, `brain effectiveness`, `brain gaps`, `knowledge learning-summary`) into `do-uw brain health`
- CI guardrails — unified `test_brain_contract.py` that validates every ACTIVE check has data route, threshold, v6_subsection_ids, and factor/peril mapping
- Rendering completeness audit — cross-reference facet declarations vs. actual rendered signals; metric is TRIGGERED display %, not all-checks %

**Should have (differentiators — elevate to self-improving system):**
- Underwriter feedback loop end-to-end — feedback CLI + proposal auto-generation + `apply-proposal` workflow closing to brain YAML change
- Signal lifecycle management — automated lifecycle review proposing promotions/deprecations/recalibrations based on fire rates and feedback
- Knowledge ingestion real-world validation — test `do-uw ingest` against actual SEC enforcement releases; wire proposals into calibration review
- Anomaly detection (cross-run) — delta between current run and last run surfaced automatically after analysis
- Brain health periodic audit — staleness, coverage imbalance, threshold conflicts

**Defer to future milestones:**
- Feedback-driven threshold calibration with backtest — requires 10+ feedback entries per check; build logging infrastructure now, defer automated proposals until data volume justifies it
- Market intelligence auto-proposals wired to every pipeline run — build the manual proposal pipeline first; automation comes after the manual path is proven
- Full knowledge.db to brain.duckdb convergence — complex migration, out of scope for v1.2
- ML-based threshold optimization — catastrophically insufficient data (3-4 tickers, 12 historical runs); defer until 50+ companies analyzed

**Hard anti-features (do not build):**
- Auto-apply brain changes without human approval
- Real-time pipeline monitoring (Prometheus/Grafana) — this is a CLI tool, not a service
- Web UI for brain CRUD operations — dashboard stays read-only
- Cross-company correlation engine — premature with < 10 companies analyzed
- Scheduling libraries (APScheduler, Celery) — system cron or manual CLI invocation is correct

See `.planning/research/FEATURES.md` for full dependency graph and infrastructure inventory.

### Architecture Approach

All six v1.2 features follow the same structural pattern: new files in new packages, minimal wiring to existing CLI entry points (< 30 lines per existing file), no modifications to AnalysisState or the 7-stage pipeline data flow. The architecture research identified 8 existing files near the 500-line limit that cannot absorb new logic (`stages/analyze/__init__.py` at 429 lines, `brain_loader.py` at ~460, `knowledge/feedback.py` at ~426, `validation/qa_report.py` at ~461). All new logic goes into new files — approximately 3,585 lines across 19 new files total.

**Major components and responsibilities:**
1. `diagnostics/` (new package, ~735 lines) — read-only observer aggregating health score from DuckDB + gap_detector + pipeline_audit; produces DiagnosticsReport; never mutates state
2. `validation/brain_audit.py` + `validation/qa_checks_brain.py` (new, ~450 lines) — periodic brain consistency checks (orphaned references, schema drift, threshold completeness); separate from post-run QA
3. `knowledge/feedback_processor.py` + `knowledge/feedback_report.py` (new, ~500 lines) — batch processes PENDING feedback entries into brain_proposals; threshold auto-tuning; explicit trigger only, never automatic
4. `brain/signal_lifecycle.py` + `brain/signal_lifecycle_rules.py` (new, ~450 lines) — adds `lifecycle` field to brain YAML, data-driven auto-transition rules that produce proposals (never direct mutations)
5. `knowledge/event_ingestion.py` + `knowledge/event_store.py` + `knowledge/event_types.py` (new, ~550 lines) — structured market event ingestion, maps events to affected checks, stores in new `brain_events` DuckDB table
6. `tests/brain/test_brain_consistency.py` et al. (new, ~750 lines) — CI guardrail test suite, status-aware (ACTIVE checks get strict validation, INCUBATING checks get minimal validation)

**The universal control flow that must not be broken:**
```
pipeline run -> brain_check_runs (DuckDB)
                    |
diagnostics / effectiveness (read-only analytics)
                    |
brain_proposals (generated by feedback_processor / event_ingestion / lifecycle_rules)
                    |
human review (do-uw feedback report + apply)
                    |
brain YAML modified (via apply-proposal workflow)
                    |
brain build (YAML -> DuckDB resync)
                    |
CI guardrails (pytest tests/brain/)
```

See `.planning/research/ARCHITECTURE.md` for full component boundary map and DuckDB schema additions.

### Critical Pitfalls

1. **Pipeline integrity audit that breaks working checks (C1)** — The audit MUST be read-only in its first phase. Use a "green zone" principle: any check producing correct results on AAPL/RPM/TSLA regression tickers is green regardless of routing path. Only BREAKING findings justify code changes. Run `{check_id: status}` snapshot diff before and after any audit-driven change. Warning sign: TRIGGERED or CLEAR count changes after implementing audit recommendations.

2. **Automated QA false positives eroding underwriter trust (C2)** — Validate DATA PROVENANCE, not DATA CORRECTNESS. No QA rule deployed with > 5% false positive rate on regression tickers. Start structural-only (missing fields, broken references, orphaned checks). The "analyst who cried wolf" failure mode is well-documented: after 3-4 false alerts, all alerts are ignored and real issues slip through.

3. **Feedback system that collects data but never closes the loop (C3)** — The feedback infrastructure is 90% built but the critical last 10% (writing proposals back to brain YAML) is missing. The `apply-proposal` workflow is non-negotiable — do not ship feedback CLI without it. Warning sign: `brain_feedback` table has > 20 PENDING entries but no YAML diffs in git history.

4. **Cross-cutting diagnostics breaking the 7-stage pipeline (C5)** — Diagnostics MUST be a post-pipeline pass, not in-stage hooks. No new DuckDB queries inside stage modules. Performance budget: diagnostics overhead < 5% of total pipeline runtime. Warning sign: new imports from `stages/acquire/` appearing in `stages/analyze/` files.

5. **Knowledge ingestion polluting the brain with noise (C4)** — Daily ingest budget of maximum 5 new proposals from automated sources. Require duplicate detection before insertion. Implement proposal TTL (PENDING proposals not reviewed in 30 days auto-archived to EXPIRED). Manual CLI ingestion is unlimited; automated ingestion requires strict quality gates first.

6. **Signal lifecycle becoming dual-system bureaucracy (M1)** — Do NOT create a second lifecycle parallel to the existing `lifecycle.py` state machine. Add a single computed `maturity` field (informational, not gating) to the existing lifecycle. Auto-transitions always produce proposals, never direct YAML mutations.

See `.planning/research/PITFALLS.md` for full prevention strategies, warning signs, recovery costs, and phase-specific risk assessment.

## Implications for Roadmap

Based on combined research, the dependency graph points to a 4-phase structure. Phase 1 has zero external dependencies and provides the validation infrastructure that all subsequent phases require. Phase 2 adds active visibility and anomaly detection. Phase 3 closes the human feedback loop end-to-end. Phase 4 adds intelligence-driven evolution as the capstone.

### Phase 1: Foundation — Pipeline Integrity and CI Guardrails

**Rationale:** Pipeline integrity and CI guardrails have no upstream dependencies and provide the safety net for all subsequent work. The integrity audit must be strictly read-only to avoid regressions on 341 working checks. CI guardrails written in Phase 1 catch regressions from Phase 2+ modifications. Coverage metrics baselines established here make Phase 2 QA meaningful.

**Delivers:** SKIPPED gap diagnosis and partial resolution (Population B DEF14A extraction); `do-uw brain trace <CHECK_ID>` for single-command data route traceability; unified `test_brain_contract.py` CI suite (status-aware: ACTIVE strict, INCUBATING minimal); `do-uw brain health` dashboard compositing existing CLI commands; rendering completeness audit command.

**Addresses features:** Pipeline integrity audit, end-to-end traceability, coverage metrics dashboard, CI guardrails (all table stakes)

**Avoids pitfalls:** C1 (read-only audit, regression baseline before any changes), C5 (post-pipeline diagnostics only, no in-stage hooks), M2 (status-aware CI guardrails), M3 (gap detector in CI pipeline)

**Stack:** Pure DuckDB analytics + Pydantic + Rich CLI. Zero new runtime dependencies. One new dev dependency: `pre-commit`.

**Research flag:** Population B DEF14A fix requires empirical testing against real proxy statements to tune LLM prompts — SKIPPED reduction from 68 to target ~34 is an estimate until real DEF14A filings are tested.

### Phase 2: Automated QA and Anomaly Detection

**Rationale:** Post-run validation depends on Phase 1 coverage metrics to establish "normal" baselines — a QA rule needs to know the expected SKIPPED count before it can flag deviations. Anomaly detection depends on clean brain_check_runs data (Phase 1 fixes the SKIPPED gap so run history is meaningful). Brain health audit depends on stable Phase 1 baselines.

**Delivers:** Post-run validator running after every `do-uw analyze` with health summary and anomaly flags (0 TRIGGERED with litigation data present, SKIPPED above threshold); `do-uw brain audit` for periodic brain consistency checks; cross-run anomaly detection via `do-uw brain delta <TICKER>`; regression baseline management in `validation/baselines/`.

**Addresses features:** Post-run validation, anomaly detection, brain health periodic audit (table stakes + differentiators)

**Avoids pitfalls:** C2 (structural-only QA rules, < 5% false positive rate requirement, backtest against regression tickers before deployment), M4 (CLI-first, enumerate specific diagnostic questions before building, zero new framework dependencies), m4 (shared metrics module, not per-command definitions)

**Stack:** Extends `validation/qa_report.py` via thin wiring to new files (`validation/brain_audit.py`, `validation/qa_checks_brain.py`, `validation/regression.py`). DuckDB analytics for cross-run comparison.

**Research flag:** No external research needed — direct extension of established QACheck/QAReport pattern.

### Phase 3: Feedback Loop End-to-End

**Rationale:** Feedback collection already exists (80% built). This phase completes the critical last 20%: the `apply-proposal` workflow that modifies brain YAML. Feedback depends on trusted output (Phases 1 + 2 validate the output). Signal lifecycle (Phase 4) depends on feedback volume and fire rate data that Phase 3 starts accumulating. Do not ship this phase without at least one proposal applied to brain YAML and git history showing the change.

**Delivers:** `do-uw feedback process` (batch processes PENDING feedback into brain_proposals); `do-uw feedback report` (human-reviewable proposal list with before/after impact); `do-uw brain apply-proposal <id>` (modifies brain YAML, runs brain build, validates regression); interactive feedback mode that presents check results and captures reactions; end-to-end test with at least one proposal applied to brain YAML.

**Addresses features:** Underwriter feedback loop end-to-end, feedback-driven threshold calibration groundwork (differentiator)

**Avoids pitfalls:** C3 (apply workflow built alongside collection, never shipped without it), M5 (feedback must reach brain YAML, not just DuckDB proposals), m2 (feedback must reference specific check IDs not free-text)

**Stack:** `knowledge/feedback_processor.py` + `knowledge/feedback_report.py` (new). Thin wiring to `cli_feedback.py` (~30 lines). Reuses existing brain_proposals infrastructure.

**Research flag:** The `apply-proposal` YAML writer requires a spike — `BrainWriter` modifies DuckDB but no equivalent YAML modifier exists. Validate ruamel.yaml vs. regex-based approach before committing to an implementation plan; comment and formatting preservation is non-trivial.

### Phase 4: Knowledge Evolution

**Rationale:** Knowledge ingestion and signal lifecycle are the capstone features. Lifecycle review consumes fire rates (Phase 1), feedback signals (Phase 3), and ingestion proposals (Phase 4 itself) — all three data streams must be operational before lifecycle review produces useful results. Ingestion proposals flow through the apply-proposal pipeline (Phase 3 must exist). These are the highest-complexity features and should come last when the foundation is solid.

**Delivers:** `do-uw ingest` validated against real documents (SEC enforcement releases, claims studies) with tuned LLM prompts; `brain_events` DuckDB table for institutional memory; `do-uw brain lifecycle review` analyzing all checks using fire rate + feedback + age to propose promotions/deprecations/recalibrations; lifecycle tracking migrated from SQLite to DuckDB; `lifecycle.state` field added to brain YAML with computed maturity property.

**Addresses features:** Knowledge ingestion, signal lifecycle management (differentiators)

**Avoids pitfalls:** C4 (daily ingest budget of 5 proposals, duplicate detection, proposal TTL before automated sources), M1 (computed maturity field not parallel state machine), anti-pattern of premature knowledge.db/brain.duckdb convergence

**Stack:** `knowledge/event_ingestion.py`, `knowledge/event_store.py`, `knowledge/event_types.py`, `brain/signal_lifecycle.py`, `brain/signal_lifecycle_rules.py` (all new). Zero new runtime dependencies.

**Research flag:** LLM ingestion prompt quality is unknown until real documents are tested — quality gates and budget limits MUST be implemented before connecting automated sources.

### Phase Ordering Rationale

- CI guardrails and pipeline integrity come first because they protect all subsequent work: Phase 2+ adds ~140 lines of modifications to existing files; without CI those modifications have no regression safety net
- Coverage metrics must precede QA because QA needs baselines to define "normal" — a QA rule that fires on correct-but-surprising data is the false-positive failure mode (Pitfall C2)
- Feedback loop must precede knowledge ingestion because ingestion proposals must flow through a proven `apply-proposal` pipeline; building ingestion before the pipeline exists means proposals pile up unreviewed (Pitfall C4)
- Signal lifecycle is last because it consumes all three data streams (fire rates, feedback, ingestion proposals); any one missing makes lifecycle review noise rather than signal
- The ~3,585 estimated lines of new code across 19 new files are distributed roughly evenly — no single phase carries a disproportionate build burden

### Research Flags

Phases likely needing `/gsd:research-phase` or a pre-phase spike during planning:
- **Phase 1 (Population B DEF14A LLM fix):** Empirical — requires test runs against real DEF14A filings to tune prompts; SKIPPED reduction target is an estimate
- **Phase 3 (apply-proposal YAML writer):** Feasibility spike required — ruamel.yaml vs. regex-based approach; comment and formatting preservation is the key risk
- **Phase 4 (knowledge ingestion LLM tuning):** LLM prompt quality unknown until real SEC enforcement releases and claims studies are tested

Phases with standard patterns (skip research-phase):
- **Phase 1 (CI guardrails, brain health dashboard):** Extending existing pytest infrastructure and compositing existing CLI commands — established patterns throughout
- **Phase 2 (automated QA, regression baselines):** Direct extension of QACheck/QAReport pattern in `validation/qa_report.py`
- **Phase 3 (feedback processor, CLI enhancement):** 80% of infrastructure already built; remaining 20% follows same DuckDB proposal pattern as existing code
- **Phase 4 (signal lifecycle state machine):** State machine logic already exists in `lifecycle.py`; migration is well-bounded

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Derived from direct source code audit of all 33 runtime + 6 dev dependencies in pyproject.toml; zero ambiguity about runtime dependency needs |
| Features | HIGH | Based on Phase 47/48 verification results (SKIPPED=68 confirmed in live runs), direct inspection of what exists vs missing per feature in 21 source files |
| Architecture | HIGH | All claims verified against actual source files; file line counts measured; component boundaries confirmed; 3,585-line estimate grounded in per-file projections |
| Pitfalls | HIGH | Combination of v1.0/v1.1 predecessor failure analysis (CLAUDE.md), direct code audit identifying structural gaps, and domain research on false positive trust erosion |

**Overall confidence: HIGH**

### Gaps to Address

- **YAML writer for brain YAML modification:** The proposal-to-YAML-change step has no implementation yet. `BrainWriter` modifies DuckDB; the equivalent YAML modifier does not exist. Phase 3 planning should spike ruamel.yaml before committing to an implementation plan — comment and formatting preservation is non-trivial.

- **Population B DEF14A LLM prompt:** 34 checks in Population B (extraction schema exists, LLM prompts don't extract values) cannot be resolved without empirical testing against real proxy statements. SKIPPED reduction target (68 -> ~34) is an estimate; actual reduction depends on DEF14A document variability across companies.

- **Dual-store coexistence boundary in Phase 4:** `brain.duckdb` and `knowledge.db` currently dual-write check run data. The signal lifecycle migration (SQLite -> DuckDB) in Phase 4 touches this boundary. The migration scope needs to be bounded carefully to avoid scope creep into full store convergence (deferred to v1.3).

- **Feedback volume threshold for auto-tuning:** Feedback-driven threshold calibration requires 10+ feedback entries per check. With a 3-4 ticker validation set, this threshold may take many months to reach. Phase 3 should build the aggregation query infrastructure even though auto-proposal generation is deferred — the logging must start now.

## Sources

### Primary (HIGH confidence — direct source code inspection)

- `src/do_uw/brain/brain_schema.py` — 19 tables, 11 views, DuckDB schema; lifecycle_state, feedback, proposals, effectiveness, changelog tables all confirmed
- `src/do_uw/brain/brain_check_schema.py` — BrainCheckEntry Pydantic model (CI guardrail validation schema)
- `src/do_uw/brain/brain_effectiveness.py` — fire rate analytics, always-fire/never-fire/high-skip detection
- `src/do_uw/stages/analyze/pipeline_audit.py` — per-check data pipeline audit (HAS_DATA/NO_MAPPER/ALL_NONE)
- `src/do_uw/knowledge/lifecycle.py` — CheckStatus state machine (INCUBATING/DEVELOPING/ACTIVE/DEPRECATED) with SQLite backend
- `src/do_uw/knowledge/feedback.py` — feedback recording, auto-proposal, summary queries (DuckDB, 426 lines)
- `src/do_uw/knowledge/ingestion_llm.py` — LLM-powered document ingestion via instructor + anthropic
- `src/do_uw/cli_feedback.py`, `src/do_uw/cli_ingest.py`, `src/do_uw/cli_brain.py` — existing CLI confirming what is built vs missing
- `src/do_uw/validation/qa_report.py` — post-pipeline QA verification (5 check categories, 461 lines)
- `pyproject.toml` — 33 runtime + 6 dev dependencies
- v1.1 Phase 47 verification (PASSED 14/14), Phase 48 verification (3/4, SKIPPED=68 gap confirmed in live runs)

### Secondary (MEDIUM confidence — web research, multiple sources agree)

- [Monte Carlo - Data Pipeline Monitoring](https://www.montecarlodata.com/blog-data-pipeline-monitoring/) — data observability patterns
- [IBM - Data Observability Model](https://www.ibm.com/think/insights/a-data-observability-model-for-data-engineers) — pipeline health metrics design
- [pre-commit framework docs](https://pre-commit.com/) — CI hook implementation patterns
- [ruff-pre-commit](https://github.com/astral-sh/ruff-pre-commit) — ruff pre-commit integration
- [Deloitte - Future of Insurance Underwriting](https://www.deloitte.com/us/en/insights/industry/financial-services/future-of-insurance-underwriting.html) — feedback loop practices in underwriting systems
- [Insurance Journal - Underwriting at an Inflection Point](https://www.insurancejournal.com/news/international/2026/02/05/856854.htm) — industry context for underwriting intelligence

### Tertiary (informational only)

- [Decisions.com - Rules Engine Trends 2025](https://decisions.com/the-evolving-power-of-rules-engines-trends-to-watch-in-2025/) — signal lifecycle management patterns in rules engines
- Security operations alert fatigue research — cited in Pitfall C2 context (organizations face 960+ alerts/day with 53% false positive rates)

---
*Research completed: 2026-02-26*
*Ready for roadmap: yes*
