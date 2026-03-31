# Pitfalls Research: v1.2 System Intelligence

**Domain:** Adding pipeline diagnostics, automated QA, underwriter feedback loops, signal lifecycle management, knowledge ingestion, and CI guardrails to an existing 400-check D&O underwriting analysis system
**Researched:** 2026-02-26
**Confidence:** HIGH (based on direct codebase audit of existing pipeline.py, knowledge/, brain/, stages/ + v1.0/v1.1 precedent failures + web research on false positive trust erosion, cross-cutting concern anti-patterns, feedback loop failures)

---

## Critical Pitfalls

Mistakes that break the working pipeline, corrupt the brain, erode underwriter trust in system output, or require multi-phase rework. These are the ones that justify v1.2 being its own milestone rather than a quick addition.

---

### Pitfall C1: Pipeline Integrity Audit That Breaks Working Checks

**What goes wrong:**
The pipeline integrity audit discovers "issues" in checks that are actually working correctly and produces recommendations to "fix" them. Acting on those recommendations silently changes check behavior -- flipping TRIGGERED checks to CLEAR or vice versa. The audit was meant to improve coverage but instead causes regressions in the 341 checks (400 minus 59 SKIPPED) that currently work.

Concrete scenario: The audit flags `FIN.LIQ.position` because its `data_strategy.field_key: current_ratio` lacks a formal declaration in a new "data contract" schema introduced by the audit system. A developer adds the declaration but maps it to `current_ratio_ttm` (trailing twelve months) instead of `current_ratio` (most recent quarter). The check now evaluates different data. AAPL's current_ratio is 0.87 (TRIGGERED) but current_ratio_ttm is 1.02 (CLEAR). The regression test catches a status flip only if it asserts exact status, not just "not SKIPPED."

**Why it happens:**
Pipeline integrity audits treat all non-conformance equally. When the audit reports "check X has issue Y," the natural response is to fix it. But "fix" implies something is broken. Many audit findings are documentation gaps (the check works, but the metadata is incomplete) or style inconsistencies (the check uses a legacy routing pattern that still functions). The audit conflates "not conforming to the new standard" with "not working."

The existing system has three routing paths that all produce correct results: `data_strategy.field_key` (Phase 31 declarative), `FIELD_FOR_CHECK` (legacy mapping), and Phase 26+ dedicated mappers. An audit that demands all checks use `field_key` forces migration of working legacy routes.

**Consequences:**
- Regression in production-validated check results for AAPL/RPM/TSLA
- Loss of the v1.0/v1.1 regression baselines that took 48 phases to establish
- Underwriter sees different findings on re-analysis of previously reviewed companies
- Team spends time debugging "audit fixes" rather than building new features

**Prevention:**
1. The integrity audit MUST be read-only in its first phase. It reports findings but makes zero changes. Output is a diagnostic report, not a migration script.
2. Establish a "green zone" principle: any check that produces correct results on all three regression tickers (AAPL, RPM, TSLA) is green regardless of which routing path it uses. Green checks are excluded from "fix needed" lists.
3. Audit findings must be severity-classified: BREAKING (check cannot evaluate at all), DEGRADED (check evaluates but with suboptimal data), DOCUMENTATION (check works but metadata is incomplete). Only BREAKING findings justify code changes.
4. Run the full regression suite BEFORE and AFTER any audit-driven change. Compare `{check_id: status}` dictionaries. Any status change must be explicitly justified.

**Warning signs:**
- Audit report lists more than 50 "issues" on first run (likely treating documentation gaps as functional issues)
- TRIGGERED or CLEAR count changes after implementing audit recommendations
- Developers referring to working checks as "non-compliant"
- Pull requests titled "fix audit findings" that modify routing logic for checks that were already passing

**Detection:**
- Regression test: `{check_id: status}` snapshot diff before/after audit changes
- CI check: `test_regression_stability.py` that asserts exact status counts per ticker

**Phase to address:** Phase 1 of v1.2. The audit must be built as a diagnostic tool ONLY. Remediation is a separate phase after audit report is reviewed.

---

### Pitfall C2: Automated QA That Produces False Positives and Erodes Trust

**What goes wrong:**
The automated QA system flags check results as "incorrect" when they are actually correct-but-surprising. Example: The QA system compares `FIN.LIQ.position` result to a "expected range" heuristic and flags AAPL's current_ratio of 0.87 as "suspiciously low for a $3T company." The QA alert reaches the underwriter or is displayed in the diagnostic dashboard. The underwriter investigates, finds the data is correct (Apple really does have a <1.0 current ratio), and starts ignoring QA alerts. After 3-4 false alerts, legitimate QA findings are also ignored.

This is the "analyst who cried wolf" problem documented extensively in security operations: organizations face an average of 960+ alerts daily, with 53% being false positives. Teams grow desensitized and start ignoring alerts wholesale, meaning real issues slip through.

**Why it happens:**
Automated QA for a domain-specific analysis system is fundamentally different from automated QA for software. Software QA has ground truth (expected output matches actual output). Analysis QA does not -- the system is discovering new information, and "surprising" results are often the most valuable ones. A QA system trained on "typical" results will flag every atypical finding as suspicious.

The existing system already handles this well for individual check evaluation (thresholds are domain-calibrated). But QA layered on top of check results introduces a second opinion system that doesn't have the same calibration.

**Consequences:**
- Alert fatigue: underwriter and developer both stop reading QA reports
- False positives in QA undermine confidence in the entire system, not just the QA layer
- Time spent investigating false QA alerts instead of improving actual analysis
- If QA false positives are not clearly distinguished from analysis false positives, underwriter may question the underlying check results themselves

**Prevention:**
1. Automated QA should validate DATA PROVENANCE, not DATA CORRECTNESS. Good QA questions: "Does this check have a source citation?" "Is the source date within 12 months?" "Is the confidence level appropriate for the source type?" Bad QA questions: "Is this value within expected range?" "Does this seem right?"
2. QA findings must have precision targets: no QA rule should be deployed if it has >5% false positive rate on the three regression tickers.
3. Start with structural QA only (missing fields, broken references, orphaned checks) before attempting semantic QA (questionable values). Structural QA has near-zero false positive rates.
4. Every QA rule must be backtested against existing AAPL/RPM/TSLA outputs before deployment. If it flags something on these tickers, the flag must be manually verified as correct before the rule goes live.
5. The QA report should distinguish DEFINITE (data is provably wrong -- e.g., check references a field that doesn't exist) from SUSPICIOUS (data is unusual -- informational only, no action required).

**Warning signs:**
- QA report has more than 10 flags on a clean company like AAPL
- Developer or underwriter says "I don't look at the QA report anymore"
- QA findings appear in the underwriter-facing worksheet output (they should be internal-only)
- QA rules reference hardcoded "expected values" rather than structural checks

**Detection:**
- Track QA precision: `true_positives / (true_positives + false_positives)` per QA rule
- If precision drops below 90%, disable the rule until recalibrated

**Phase to address:** Automated QA phase. Start with structural-only QA rules. Semantic QA rules require backtesting infrastructure and must be introduced one at a time with precision tracking.

---

### Pitfall C3: Feedback System That Collects Data But Never Closes the Loop

**What goes wrong:**
The `do-uw feedback <TICKER>` CLI is built, feedback is recorded in `brain_feedback` table (already exists -- see `feedback.py`), summary dashboards show pending feedback counts, but no mechanism exists to translate feedback into brain YAML changes. The feedback accumulates indefinitely. After 50+ entries with zero brain modifications, the underwriter stops providing feedback because they see no impact.

The existing `feedback.py` already has this partially: `record_feedback()` stores entries, `get_feedback_summary()` shows counts, and `_auto_propose_check()` creates INCUBATING proposals from MISSING_COVERAGE feedback. But the proposals themselves pile up in `brain_proposals` with status='PENDING' and no review workflow. The loop is 90% built but the critical last 10% (applying changes to brain YAML) is missing.

**Why it happens:**
Feedback collection is engineering work (build CLI, store data, show counts). Feedback application is domain work (interpret feedback, decide on threshold adjustments, test the change). Engineering work gets prioritized because it's measurable ("we built the feedback CLI!"). Domain work gets deferred because it's subjective ("should we adjust this threshold based on one underwriter's opinion?").

Additionally, the existing `brain_proposals` table has columns for `backtest_results` and `reviewed_by`, but no code path populates them. The infrastructure assumes a human review step that was never built.

**Consequences:**
- Underwriter engagement drops after initial enthusiasm
- Feedback table grows indefinitely with PENDING status
- Brain never improves from real-world usage
- The "learning loop" feature is technically complete but functionally dead
- Storage costs for unused data

**Prevention:**
1. Define the complete loop BEFORE building the CLI: feedback entry -> proposal generation -> backtest -> human review -> brain YAML change -> regression validation -> mark feedback as APPLIED.
2. Set a "feedback freshness" SLA: every PENDING feedback entry must be triaged within N analysis runs (not calendar days -- feedback is only relevant when the system is being used).
3. Build the simplest possible application path: THRESHOLD feedback generates a proposed threshold change, displays the old vs new value and the check results that would change, and asks for confirmation. One command: `do-uw brain apply-feedback <feedback_id>`.
4. The `mark_feedback_applied()` function already exists. Wire it to the end of the application path so the dashboard shows progress.
5. Build reporting: "10 feedback items received, 7 applied, 2 deferred, 1 rejected." The ratio matters more than the absolute count.

**Warning signs:**
- `brain_feedback` table has >20 PENDING entries
- `brain_proposals` table has >10 PENDING entries with no reviewed_by
- Feedback CLI is shipped but `do-uw brain apply-feedback` is not
- Underwriter provides feedback for the first 2-3 tickers then stops
- Dashboard shows "pending_accuracy: 15" but no applied count

**Detection:**
- Query: `SELECT status, COUNT(*) FROM brain_feedback GROUP BY status` -- if PENDING >> APPLIED, the loop is broken
- Track feedback-to-application latency: date between record_feedback and mark_feedback_applied

**Phase to address:** The feedback phase must include BOTH collection AND application. Do not ship feedback CLI without the apply workflow. The `mark_feedback_applied()` function is already implemented; it needs a CLI entry point and a brain YAML writer that executes the proposed change.

---

### Pitfall C4: Knowledge Ingestion That Pollutes the Brain with Noise

**What goes wrong:**
The `ingest_document()` function (already in `ingestion.py`) accepts external documents and creates INCUBATING checks. The LLM extraction (`ingestion_llm.py`) generates proposals from any document that mentions D&O-relevant keywords. When ingestion is connected to automatic sources (news feeds, regulatory updates, case law databases), the volume of INCUBATING checks overwhelms the review queue. After ingesting 200+ documents, the `brain_proposals` table has 500+ PENDING proposals. Nobody reviews them. New legitimate proposals are buried in noise.

The existing `_RELEVANCE_THRESHOLD = 5` in `discovery.py` and the `_DO_KEYWORDS` list are calibrated for blind spot discovery (find anything potentially relevant). For ongoing knowledge ingestion, this threshold is far too permissive.

**Why it happens:**
Knowledge ingestion has an asymmetric error cost: missing a relevant signal feels catastrophic ("we didn't know about this regulatory change!"), while ingesting noise feels harmless ("we'll just review it later"). This asymmetry drives developers to lower quality thresholds, capture everything, and defer filtering. But "review later" never happens at scale, and the noise-to-signal ratio degrades the entire proposal queue.

The existing `_extract_numbered_items()` function in `ingestion.py` turns every numbered list item (>10 chars) into a check_idea. A single industry analysis document with 50 numbered observations generates 50 INCUBATING checks, most of which are not D&O-relevant.

**Consequences:**
- Proposal queue becomes unusable (500+ PENDING proposals)
- Legitimate proposals (from underwriter feedback or genuine market events) are buried
- Brain YAML grows with INCUBATING checks that never activate
- DuckDB brain.duckdb bloats with unused records
- The ingestion feature is technically working but practically harmful

**Prevention:**
1. Ingestion must have a DAILY ingest budget: maximum 5 new proposals per day from automated sources. Manual ingestion via CLI is unlimited.
2. Require DUPLICATE detection before insertion: check if a semantically similar proposal already exists in brain_proposals. The `_derive_check_id()` function produces IDs from keywords but doesn't check for existing similar checks.
3. Auto-REJECT proposals that overlap with existing ACTIVE checks by >80% keyword similarity.
4. Every ingested proposal must include a `confidence_score` (from LLM extraction) and a `relevance_score` (from keyword matching). Only proposals above both thresholds enter the queue.
5. Implement proposal TTL: PENDING proposals not reviewed within 30 days are auto-archived (not deleted -- moved to EXPIRED status). This keeps the active queue manageable.
6. The `_extract_numbered_items()` function should be rate-limited: maximum 5 items per document, prioritized by position (earlier items in a document are usually more important).

**Warning signs:**
- `brain_proposals` table has >50 PENDING entries
- More than 20 proposals created in a single ingestion session
- Proposal titles contain generic phrases like "monitor changes" or "track developments"
- No proposals have been reviewed in 2+ weeks despite new submissions
- `brain_checks` table has >50 INCUBATING checks with no path to DEVELOPING

**Detection:**
- Query: `SELECT COUNT(*) FROM brain_proposals WHERE status = 'PENDING' AND created_at < current_timestamp - INTERVAL 30 DAYS` -- stale proposals indicate a broken review process
- Monitor proposal creation rate vs review rate

**Phase to address:** Knowledge ingestion phase. Implement quality gates and budget limits BEFORE connecting automated sources. Manual-only ingestion first, then automated with strict thresholds.

---

### Pitfall C5: Breaking the 7-Stage Pipeline Architecture with Cross-Cutting Diagnostics

**What goes wrong:**
Diagnostics, QA, and feedback features are "horizontal" concerns that touch every stage. The natural implementation is to add hooks into each stage: ACQUIRE logs data completeness metrics, EXTRACT logs extraction success rates, ANALYZE logs check evaluation statistics, SCORE logs scoring distributions, RENDER logs display completeness. These hooks turn every stage into a diagnostic emitter, coupling the diagnostic system to every stage's internal implementation.

Concrete example: A diagnostics collector is added to `AnalyzeStage` that queries `brain.duckdb` for check metadata during check evaluation to compare actual vs expected field routing. This query adds 200ms per check (400 checks x 200ms = 80 seconds). The pipeline, which runs in 10-20 minutes, now takes 12-22 minutes. Worse: the DuckDB query in ANALYZE stage creates a dependency on brain.duckdb that didn't exist before (ANALYZE previously operated only on in-memory state).

**Why it happens:**
Cross-cutting concerns are inherently hard to implement without violating stage boundaries. The pipeline's strength is its linear, sequential, boundary-respecting architecture (`pipeline.py` runs stages in order with validation gates between them). Diagnostics want to observe everything, which requires reaching into every stage's internals.

The existing `StageCallbacks` protocol in `pipeline.py` is the right pattern (stage-external observation) but it only reports stage-level events (start, complete, skip, fail). Adding check-level or field-level diagnostics requires either extending StageCallbacks beyond recognition or injecting diagnostic code inside stages.

**Consequences:**
- Stage boundaries blur: diagnostics code in ANALYZE imports from ACQUIRE
- Pipeline slows down from diagnostic overhead
- New dependencies (brain.duckdb in ANALYZE) violate the stage contract
- Testing stages in isolation becomes impossible because they depend on diagnostic infrastructure
- The "MCP boundary" rule (MCP tools only in ACQUIRE) is violated if diagnostics fetch additional data

**Prevention:**
1. Diagnostics MUST be a POST-PIPELINE phase, not a cross-cutting concern. After all 7 stages complete, a diagnostics pass reads the final `AnalysisState` and `brain.duckdb` to produce metrics. This adds an 8th logical step (not a stage -- it doesn't modify state) that runs after RENDER.
2. If per-stage metrics are needed, extend `StageCallbacks` with a `on_stage_metrics(stage_name: str, metrics: dict[str, Any])` callback. Each stage emits summary metrics (not detailed per-check data) through the callback. The diagnostic collector is outside the stage, not inside it.
3. Never import from `stages/acquire/` in `stages/analyze/` or vice versa for diagnostic purposes. If data needs to cross stage boundaries, it goes through `AnalysisState`.
4. Set a performance budget: diagnostics overhead must be <5% of total pipeline runtime. Measure before and after adding any diagnostic code.

**Warning signs:**
- New imports from `stages/acquire/` appearing in `stages/analyze/` files
- `brain.duckdb` queries appearing in files outside `brain/` or `knowledge/`
- Pipeline runtime increasing by >10% after diagnostic features are added
- A new "diagnostics" stage inserted between existing stages (violates PIPELINE_STAGES=7)
- `AnalysisState` growing new fields that only diagnostics consume

**Detection:**
- Import analysis: `grep -r "from do_uw.stages.acquire" src/do_uw/stages/analyze/` should return zero results
- Performance benchmark: `time do-uw analyze AAPL` before and after diagnostic code
- State size: `state.json` file size should not grow more than 10% from diagnostic metadata

**Phase to address:** Diagnostics phase. Design as post-pipeline pass or StageCallbacks extension. Never as in-stage hooks. Review the `StageCallbacks` protocol in `pipeline.py` as the starting point.

---

## Moderate Pitfalls

Mistakes that degrade the system's usefulness, create maintenance burden, or produce incorrect metrics without causing outright failures.

---

### Pitfall M1: Signal Lifecycle Management That Adds Bureaucracy Without Value

**What goes wrong:**
The existing `lifecycle.py` has a clean 4-state machine: INCUBATING -> DEVELOPING -> ACTIVE -> DEPRECATED. The v1.2 scope adds "signal epistemology" with a formal lifecycle of `emerging -> established -> deprecated` driven by market intelligence, run performance data, and underwriter feedback. If implemented as a second, parallel lifecycle (check lifecycle + signal lifecycle), every check now has TWO status fields that must be kept in sync. A check can be ACTIVE (lifecycle) but "emerging" (signal epistemology), creating confusion about whether it should be trusted.

Adding more states to the lifecycle (e.g., EMERGING, ESTABLISHED, CANDIDATE, REVIEW, SUNSET) increases transition complexity combinatorially. With 4 states, there are 12 possible transitions (some invalid). With 7 states, there are 42. Each transition needs validation, history recording, and test coverage.

**Why it happens:**
Signal lifecycle sounds valuable in theory: checks that are new and unvalidated should be treated differently from checks with years of performance data. But the existing system already handles this implicitly: INCUBATING checks don't execute in the pipeline (`execution_mode != "AUTO"`), DEVELOPING checks are being built, and ACTIVE checks run. The signal epistemology adds a second dimension of maturity that overlaps with the existing lifecycle.

**Consequences:**
- Two competing status systems for each check (lifecycle state vs signal maturity)
- Transition validation becomes error-prone (is it valid to go ACTIVE + emerging -> ACTIVE + deprecated?)
- Developer confusion about which status to check
- Brain YAML files get more fields that rarely change and provide marginal value
- The `transition_check()` function needs to be aware of signal maturity, creating coupling

**Prevention:**
1. Do NOT create a second lifecycle. Instead, add a single `maturity` field to the existing lifecycle that is orthogonal to status: `maturity: emerging | established | legacy`. This field is informational, not gating -- it does not affect whether a check executes.
2. The maturity field should be auto-computed from run data (how many tickers has this check evaluated? what is its fire rate stability?) rather than manually managed. No state machine, no transitions -- just a calculated property.
3. If signal epistemology truly needs state transitions, implement it as CHECK METADATA (a field on the check YAML) managed by a CLI command, NOT as a parallel lifecycle with its own state machine.
4. Deprecation is the one lifecycle event that IS signal epistemology. Use the existing DEPRECATED status + `deprecation_note` field (already added in v1.1) rather than creating a new mechanism.

**Warning signs:**
- Brain YAML checks gaining a `signal_status` field alongside the existing `lifecycle_state`
- New state machine code that duplicates `lifecycle.py` transition logic
- Developers asking "is this check active or just established?"
- More than 5 signal lifecycle states being proposed

**Detection:**
- Count lifecycle-related fields per check: should be exactly 1 status field
- Check for parallel state machine implementations in knowledge/ directory

**Phase to address:** Signal lifecycle phase. Implement as a computed property on check metadata, not a parallel state machine.

---

### Pitfall M2: CI Guardrails That Are Too Strict and Block Legitimate Brain Changes

**What goes wrong:**
A CI check is added: "every new check YAML must have a `data_strategy.field_key`." This sounds reasonable (ensures new checks are routable). But it blocks legitimate additions of qualitative/manual checks that intentionally lack field routing. An underwriter proposes a new check via feedback ("Does the CEO have prior criminal history?"), the auto-proposal creates an INCUBATING check, and the CI blocks the PR because the check has no `field_key`. The developer either (a) adds a bogus `field_key` to pass CI, or (b) decides it's not worth the hassle and drops the check.

This is the "reduced utility vs safety" tradeoff documented in guardrails literature: overly strict guardrails block harmless-but-nonconforming content, leading to workarounds that are worse than the original problem.

**Why it happens:**
CI guardrails are binary: pass or fail. The brain has three types of checks that need different guardrail profiles: (a) auto-evaluated checks that NEED field routing, (b) qualitative checks that intentionally lack field routing, and (c) INCUBATING checks that are incomplete by design. A single guardrail rule cannot accommodate all three types.

**Consequences:**
- Legitimate brain additions blocked by over-strict CI
- Developers add bogus metadata to pass CI (worse than no CI)
- INCUBATING checks cannot be merged until they're fully developed (defeats purpose of incubation)
- CI becomes something to work around rather than work with
- Brain evolution slows to a crawl

**Prevention:**
1. CI guardrails must be STATUS-AWARE: ACTIVE checks get strict validation (must have field_key, threshold, required_data). INCUBATING checks get minimal validation (must have id, name). DEVELOPING checks get intermediate validation.
2. Use WARNING level for non-critical issues instead of ERROR. CI fails on ERROR only; warnings are logged and reported but don't block merge.
3. Every CI guardrail rule must be documented with: what it checks, why it matters, how to legitimately bypass it (e.g., `# ci-skip: intentionally-manual` comment in YAML).
4. Implement guardrail PROFILES: `ci_profile: strict` for ACTIVE checks, `ci_profile: relaxed` for INCUBATING checks. Profiles are defined in config, not hardcoded.
5. Run guardrails against the CURRENT brain before deploying them. If they would fail on >5 existing ACTIVE checks, the guardrail is too strict.

**Warning signs:**
- CI blocks PRs that add INCUBATING checks
- Developers adding placeholder values like `field_key: "TODO"` to pass CI
- CI pass rate drops below 90% on legitimate brain changes
- Comments in PRs: "adding this to satisfy CI" or "CI workaround"

**Detection:**
- Track CI failure reasons: if >30% of failures are "missing field on INCUBATING check," the guardrail is too strict
- Audit YAML for placeholder values: `grep -r "TODO\|FIXME\|placeholder" src/do_uw/brain/checks/`

**Phase to address:** CI guardrails phase. Build status-aware guardrails from day one. Test against existing brain before deploying.

---

### Pitfall M3: CI Guardrails That Are Too Loose and Miss Real Issues

**What goes wrong:**
The opposite of M2: CI guardrails are so permissive that real issues slip through. A new ACTIVE check is added without a threshold definition, so it can never TRIGGER. Or a check's `required_data` references a source that doesn't exist in `ACQUIRED_SOURCES` (the gap detector already catches this, but the CI doesn't run the gap detector). The check enters the brain, runs in production, and silently SKIPs on every ticker.

**Why it happens:**
After encountering M2 (too strict), the natural response is to loosen guardrails. Or guardrails are written only for the happy path: "check has an id and a name" passes, even if the check is missing every field that matters for execution.

The existing `BrainCheckEntry` Pydantic model validates structure at load time but not semantic correctness. A check with `required_data: [SEC_FORM13F]` will load successfully (valid YAML, valid string list) but will always SKIP because `SEC_FORM13F` is not in `ACQUIRED_SOURCES`.

**Consequences:**
- New checks that look correct but never produce results
- SKIPPED count creeps up without anyone noticing
- Regression baselines slowly drift as new always-SKIPPED checks dilute the denominator
- Brain YAML grows with dead-on-arrival checks

**Prevention:**
1. CI must run the gap detector (`detect_gaps()`) on any PR that modifies brain YAML. New ACTIVE checks with CRITICAL gaps (source not acquired) fail CI.
2. For ACTIVE checks: require threshold definition (red + clear at minimum), require at least one factor assignment, require required_data to be a subset of ACQUIRED_SOURCES.
3. For field_key: if specified, verify the key exists in the extraction manifest (the `field_key_collector.py` already maps known keys).
4. Run a "new check smoke test": add the check to a minimal test that loads the brain, runs the check engine with mock data, and verifies the check produces a non-SKIPPED result. If a new ACTIVE check would always SKIP, CI fails.

**Warning signs:**
- SKIPPED count increasing over time (track per release)
- New checks merged without tests
- Gap detector finding CRITICAL issues that CI didn't catch
- Checks with `required_data: []` (no data requirements = will always evaluate to CLEAR, which is meaningless)

**Detection:**
- Track: `count(SKIPPED) / count(total_auto_checks)` per regression ticker per release. Should be stable or decreasing.
- CI check: `detect_gaps(new_or_modified_checks)` must return zero CRITICAL gaps

**Phase to address:** CI guardrails phase. Implement in parallel with M2 -- the strict/loose balance must be designed together.

---

### Pitfall M4: Over-Engineering Diagnostics When Simple Metrics Suffice

**What goes wrong:**
A full diagnostic dashboard is built with real-time pipeline health monitoring, per-check evaluation timelines, data routing sankey diagrams, and historical trend charts. The dashboard requires a web server, a time-series database, a frontend framework, and ongoing maintenance. It takes 2-3 phases to build. Meanwhile, the actual diagnostic questions are simple: "How many checks are SKIPPED?" "What data sources failed?" "Which checks changed status since last run?" These questions can be answered by a CLI command that queries the existing `state.json` and `brain.duckdb`.

**Why it happens:**
Diagnostics are fun to build. They're visual, they feel productive, and they have clear acceptance criteria ("the dashboard shows X"). But the USER of diagnostics (developer or underwriter) needs answers to specific questions, not a monitoring system. The existing system already has most diagnostic data in `state.json` (check results, stage timing) and `brain.duckdb` (check metadata, run history). Extracting that data into reports is a 1-phase effort; building a dashboard is a 3-phase effort with ongoing maintenance.

**Consequences:**
- 2-3 phases spent on dashboard infrastructure instead of brain improvements
- New dependencies (web framework, time-series DB) increase maintenance burden
- Dashboard requires its own CI, testing, and deployment pipeline
- Simple questions still require navigating a complex UI instead of running a CLI command
- The dashboard becomes stale when nobody maintains the frontend

**Prevention:**
1. Start with CLI-only diagnostics: `do-uw diagnostics <TICKER>` that prints a structured report to stdout. This can be built in 1-2 plans, uses existing data, and is immediately useful.
2. Diagnostic questions should be enumerated BEFORE any code is written: "What are the top 10 questions a developer/underwriter asks about system health?" Build answers to exactly those questions.
3. Use the existing `brain.duckdb` query interface for all metrics. No new database.
4. If visualization is needed, generate static HTML reports (like the existing worksheet) rather than building a live dashboard. The system already has an HTML generation pipeline.
5. A dashboard is justified ONLY if diagnostics are accessed >5x per day by >1 user. For a CLI tool used by a single underwriter, CLI output is the correct interface.

**Warning signs:**
- Architecture discussions about "which charting library to use"
- New dependencies on Flask/FastAPI/Streamlit appearing in `pyproject.toml`
- Diagnostic features taking more than 2 phases
- Developer building the dashboard but never looking at it in practice

**Detection:**
- Count new dependencies added for diagnostics: should be zero
- Measure time from "diagnostic question asked" to "answer received": CLI should be <5 seconds

**Phase to address:** Diagnostics phase. CLI-first, static reports second, live dashboard never (for this project's scale).

---

### Pitfall M5: Feedback Signals Not Connected to Actual Brain YAML Changes

**What goes wrong:**
The feedback system writes to `brain_feedback` (DuckDB), the proposals system writes to `brain_proposals` (DuckDB), the learning system writes to knowledge store (SQLite), but the brain YAML files (`src/do_uw/brain/checks/**/*.yaml`) are never modified by any of these systems. The brain YAML is the actual contract that drives the pipeline. Feedback and proposals that don't result in YAML changes have zero impact on analysis results.

The existing codebase has THREE stores: brain.duckdb (brain metadata + feedback + proposals), SQLite knowledge store (learning + notes + check definitions), and brain YAML files (actual check definitions). Only the YAML files affect pipeline behavior. The other stores are observability infrastructure.

**Why it happens:**
YAML modification is scary. Automated changes to the brain YAML risk corrupting the 400-check knowledge base that took 48 phases to build. The safe approach is to store feedback and proposals in databases and defer YAML modification to manual review. But "manual review" at scale means "never happens."

The `BrainWriter` class exists and can modify brain.duckdb, but there's no equivalent that safely modifies the YAML source files. The `brain build` command reads YAML and populates DuckDB, but there's no `brain apply` that reads DuckDB proposals and modifies YAML.

**Consequences:**
- Three data stores with no synchronization mechanism
- Feedback → DuckDB → nothing
- Proposals → DuckDB → nothing
- Learning → SQLite → nothing
- The brain YAML stays static despite all the intelligence infrastructure
- 90% of the feedback/learning/proposal code is infrastructure without impact

**Prevention:**
1. Build a `brain apply-proposal <proposal_id>` command that: reads the proposal from DuckDB, generates a YAML diff, shows the diff to the user, applies on confirmation, runs `brain build` to sync DuckDB, runs regression tests to verify no regressions.
2. For threshold adjustments: generate the exact YAML edit (old value -> new value) and apply it directly to the source YAML file using a YAML-aware editor (ruamel.yaml or equivalent) that preserves comments and formatting.
3. Make the YAML the single source of truth and the databases as caches. Changes flow: YAML -> `brain build` -> DuckDB. Never: DuckDB -> YAML (except through the explicit `apply-proposal` command).
4. The learning system's check effectiveness data should inform which proposals to prioritize (checks with low fire rate across many tickers might need threshold adjustment), but it should NOT auto-modify YAML.

**Warning signs:**
- `brain_feedback` has >20 entries but no YAML diffs in git history
- `brain_proposals` has >10 entries but no YAML files modified
- Developer manually editing YAML based on DuckDB data instead of using a workflow tool
- Three stores diverging: DuckDB says a check is DEPRECATED but YAML still has it as ACTIVE

**Detection:**
- Git log: `git log --stat src/do_uw/brain/checks/` -- if no changes for >2 weeks while feedback is being recorded, the loop is broken
- Query: `SELECT COUNT(*) FROM brain_proposals WHERE status = 'APPLIED'` -- should be >0 after feedback system is live

**Phase to address:** Must be addressed as part of the feedback phase. The `apply-proposal` workflow is the critical last mile that makes feedback actually work.

---

### Pitfall M6: Rendering Completeness Audit That Adds Display for Irrelevant Checks

**What goes wrong:**
The rendering completeness goal ("facets and display units populated end-to-end, no gaps") is interpreted as "every check must appear in the worksheet." This includes checks that CLEAR (no finding), checks that SKIP (no data), and checks that are irrelevant for the specific company. The worksheet balloons from a focused risk assessment to a 50-page data dump that buries red flags in noise.

The existing `display_when: has_data` field on check YAML (see `FIN.LIQ.position` example) already handles this correctly for individual checks. But a completeness audit that measures "% of checks displayed" incentivizes showing everything rather than showing what matters.

**Consequences:**
- Worksheet becomes unusable due to length
- Underwriter loses confidence in the system's ability to prioritize
- Critical red flags buried on page 30 of a 50-page document
- HTML render time increases proportionally with displayed checks

**Prevention:**
1. Rendering completeness should measure "% of TRIGGERED checks with complete display metadata" not "% of all checks displayed."
2. The metric that matters is: "Can every TRIGGERED finding be fully understood from the worksheet alone?" Not: "Does every check have a display representation?"
3. CLEAR and SKIPPED checks should be summarized (count per category) not displayed individually.
4. The existing `display_when` field is the correct mechanism. Do not override it with a blanket "show everything" policy.

**Warning signs:**
- Worksheet page count increasing after rendering completeness work
- New sections showing "Checks that passed" or "No findings" lists
- Display completeness metrics counting CLEAR/SKIPPED checks in the denominator

**Detection:**
- Track worksheet page count per ticker per release: should be stable or decreasing
- Count TRIGGERED checks vs total displayed sections: ratio should be high (>0.7)

**Phase to address:** Rendering completeness phase. Define the metric correctly before measuring.

---

## Minor Pitfalls

Issues that create maintenance annoyance or minor inconsistencies without significant impact.

---

### Pitfall m1: Diagnostic Metrics Not Versioned with Brain Changes

**What goes wrong:**
Diagnostic metrics (SKIPPED count, TRIGGERED count, coverage %) are tracked over time but not associated with the brain version (which checks existed, which were ACTIVE). When a batch of new checks is added, all metrics shift but there's no annotation explaining why. Looking at a trend chart: "SKIPPED count jumped from 59 to 75 on Feb 28" -- is this a regression or did 16 new checks get added?

**Prevention:** Tag every diagnostic snapshot with the brain version (count of ACTIVE checks, hash of brain YAML, or explicit version number). Track metrics as ratios (SKIPPED/total, not absolute SKIPPED count).

---

### Pitfall m2: Feedback CLI That Doesn't Reference Specific Check Results

**What goes wrong:**
`do-uw feedback AAPL` opens a generic prompt: "Enter your feedback." The underwriter types "the insider trading section seems wrong." This is recorded but unactionable because it doesn't reference a specific check_id, a specific value, or a specific finding.

**Prevention:** The feedback CLI must present the check results for the most recent analysis of that ticker and allow the underwriter to select specific checks. `do-uw feedback AAPL --check FIN.LIQ.position --direction TOO_STRICT --note "Apple's low current ratio is normal for tech"`.

---

### Pitfall m3: CI Running Full Brain Validation on Every Commit

**What goes wrong:**
CI loads all 400 brain YAML checks, runs gap detection, validates all fields, and runs regression tests on every commit. This takes 5+ minutes and runs on changes that don't touch brain YAML (e.g., a CSS fix in the render templates). Developer velocity drops.

**Prevention:** CI guardrails should be PATH-SCOPED: brain validation runs only when `src/do_uw/brain/checks/**/*.yaml` or `src/do_uw/brain/brain_check_schema.py` changes. General CI (linting, type checking, unit tests) runs on all changes. Brain-specific CI runs only on brain changes.

---

### Pitfall m4: Multiple Diagnostic Outputs With Different Definitions

**What goes wrong:**
The pipeline integrity audit reports "coverage: 85%." The diagnostics dashboard reports "coverage: 91%." The QA report reports "coverage: 78%." Each uses a different denominator: total checks, auto-evaluable checks, or checks with field routing. The underwriter asks "what's our coverage?" and gets three different answers.

**Prevention:** Define each metric ONCE in a shared module (`src/do_uw/diagnostics/metrics.py`). All consumers import from this module. Include the denominator in the metric name: `coverage_of_auto_checks`, `coverage_of_routed_checks`.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems specific to v1.2 features.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store diagnostics in AnalysisState | No new storage mechanism needed | State JSON bloats; diagnostics persist across pipeline resumes | Never -- diagnostics are ephemeral, not pipeline state |
| Add diagnostic hooks inside stage.run() | Direct access to stage internals | Stages become untestable in isolation; runtime overhead | Never -- use StageCallbacks or post-pipeline pass |
| Use separate SQLite DB for feedback | Avoids brain.duckdb schema changes | Third database (DuckDB + SQLite + new SQLite); sync issues | Never -- feedback already lives in brain.duckdb |
| Auto-apply feedback without human review | Faster loop closure | One bad threshold change corrupts 400-check scoring | Never for ACTIVE checks; acceptable for INCUBATING |
| Build web dashboard for diagnostics | Pretty visualizations | New dependency stack; maintenance burden | Only if accessed >5x/day by >1 user (unlikely) |
| Skip backtesting proposals before applying | Faster application workflow | Untested brain changes cause regressions | Never for ACTIVE checks |
| Implement signal epistemology as full state machine | Clean formal model | Combinatorial complexity; second lifecycle to maintain | Never -- use computed maturity field |
| Run all CI guardrails on all checks equally | Simpler CI configuration | INCUBATING checks blocked from merging | Never -- use status-aware profiles |

---

## Integration Gotchas

Common mistakes when connecting v1.2 features to the existing system.

| Integration Point | Common Mistake | Correct Approach |
|-------------------|----------------|------------------|
| Pipeline + diagnostics | Add diagnostic code inside each stage's run() method | Use StageCallbacks or post-pipeline diagnostic pass |
| brain.duckdb + feedback | Create new DuckDB tables without running `brain build` migration | Add tables to the existing brain build workflow; schema version them |
| Feedback CLI + AnalysisState | Feedback CLI re-runs analysis to get current results | Read from saved `state.json` in output directory (already persisted after each run) |
| CI guardrails + BrainCheckEntry | CI validates raw YAML dict against custom rules | CI should validate against BrainCheckEntry Pydantic model (already exists and does structural validation) |
| Learning system + brain YAML | Learning data (fire rates, co-firing) stored in SQLite but brain YAML has no link | Add optional `performance_data` computed field to BrainCheckEntry that reads from learning store |
| Discovery + ingestion | Discovery proposals in brain_proposals, ingestion proposals in knowledge store | Unify: all proposals go through brain_proposals table with source_type distinguishing origin |
| Diagnostics + state.json | Diagnostics modify state to store metrics | Diagnostics write to a SEPARATE file (e.g., `diagnostics.json` alongside `state.json`) |
| Regression tests + new features | New features change TRIGGERED counts, breaking regression baselines | Update baselines AFTER verifying changes are correct, not before. Baselines are assertions, not targets |

---

## Performance Traps

Patterns that work during development but fail at scale or with frequent use.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Gap detector runs on every pipeline start | 2-3 second startup delay | Run gap detector on brain YAML change only; cache result in brain.duckdb | At 600+ checks |
| QA validation runs on all 400 checks per analysis | 10-30 second QA phase added to pipeline | Run QA on TRIGGERED checks only (much smaller set, ~20-80 per ticker) | Always -- unnecessary work |
| Feedback summary queries brain.duckdb on every CLI command | 1-2 second delay on every `do-uw feedback` invocation | Cache summary; invalidate on new feedback entry only | At 500+ feedback entries |
| Learning system loads all analysis outcomes for each effectiveness query | O(n) where n = total analysis runs | Add indexes on analysis_run notes; cache fire rates in dedicated table | At 100+ analysis runs |
| CI guardrails load entire brain for validation | 3-5 second CI overhead per commit | Only load and validate changed YAML files; diff-based validation | Always for non-brain commits |
| Ingestion LLM extraction on every document | LLM API cost accumulates | Rate-limit ingestion; cache extraction results per document hash | At 50+ documents/month |

---

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces specific to v1.2.

- [ ] **Pipeline integrity audit runs:** Audit produces a report -- verify the report is READ-ONLY and makes no changes to check routing or status
- [ ] **Automated QA deployed:** QA rules exist -- verify false positive rate is <5% on all 3 regression tickers BEFORE exposing to underwriter
- [ ] **Feedback CLI works:** `do-uw feedback <TICKER>` records entries -- verify `do-uw brain apply-proposal` also exists and can modify YAML
- [ ] **Feedback loop closed:** Feedback recorded + proposals created -- verify at least 1 proposal has been applied to brain YAML and mark_feedback_applied was called
- [ ] **Knowledge ingestion running:** Documents can be ingested -- verify proposal queue is not growing unbounded (check PENDING count)
- [ ] **CI guardrails active:** Guardrails run on brain changes -- verify they are status-aware (INCUBATING checks pass with minimal fields)
- [ ] **CI guardrails not blocking:** Guardrails catch real issues -- verify legitimate brain PRs pass CI (>95% pass rate on real changes)
- [ ] **Signal lifecycle implemented:** Maturity field exists -- verify it is a computed property, not a second state machine
- [ ] **Diagnostics useful:** Diagnostic output exists -- verify it answers "how many checks SKIPPED?" in <5 seconds via CLI
- [ ] **Diagnostics not invasive:** Diagnostics produce metrics -- verify no new imports from stages/acquire in stages/analyze
- [ ] **Rendering completeness measured:** Coverage metric exists -- verify denominator is TRIGGERED checks, not all 400 checks
- [ ] **Three stores in sync:** brain.duckdb, SQLite knowledge store, brain YAML -- verify `brain build` produces consistent state from YAML source of truth
- [ ] **Regression baselines stable:** AAPL/RPM/TSLA regression -- verify `{check_id: status}` counts unchanged after each v1.2 phase (or explicitly justified)

---

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Audit breaks working checks (C1) | LOW | Roll back to pre-audit git state; re-run regression to confirm restoration; re-design audit as read-only |
| QA false positives erode trust (C2) | HIGH | Disable all semantic QA rules; retain structural-only rules; rebuild trust with developer/underwriter over 2-3 sessions; reintroduce rules one at a time with precision tracking |
| Feedback never applied (C3) | MEDIUM | Build minimal `apply-proposal` CLI; process top 5 pending feedback items manually; show underwriter the applied changes to rebuild engagement |
| Ingestion noise (C4) | MEDIUM | Bulk-archive all PENDING proposals older than 30 days; tighten relevance threshold; add daily budget cap; start fresh with clean queue |
| Cross-cutting diagnostics break stages (C5) | HIGH | Extract all diagnostic code from stages into post-pipeline pass; remove new DuckDB dependencies from stages; verify stage isolation with import analysis; 2-3 day rework |
| Signal lifecycle bureaucracy (M1) | LOW | Remove second state machine; replace with computed maturity field; 0.5 day refactor |
| CI too strict (M2) | LOW | Add status-aware bypass for INCUBATING checks; 0.5 day fix |
| CI too loose (M3) | MEDIUM | Add gap detector to CI; retroactively validate all checks merged since CI deployment; 1 day fix + validation |
| Over-engineered diagnostics (M4) | HIGH | Cannot easily simplify a dashboard to CLI; must decide: maintain dashboard or replace with CLI. Replacing wastes the dashboard investment. |

---

## Pitfall-to-Phase Mapping

How v1.2 phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| C1: Audit breaks working checks | Pipeline integrity audit phase -- design as read-only diagnostic first | Regression baselines unchanged after audit phase |
| C2: QA false positives erode trust | Automated QA phase -- structural-only rules first; precision tracking | <5% false positive rate on regression tickers |
| C3: Feedback never applied | Feedback phase -- build apply workflow alongside collection | At least 1 proposal applied to YAML; feedback APPLIED count >0 |
| C4: Ingestion noise | Knowledge ingestion phase -- quality gates + budget BEFORE automated sources | brain_proposals PENDING count <50 at all times |
| C5: Cross-cutting diagnostics | Diagnostics phase -- post-pipeline pass, not in-stage hooks | Zero new cross-stage imports; <5% pipeline runtime overhead |
| M1: Signal lifecycle bureaucracy | Signal lifecycle phase -- computed maturity field, not second state machine | Exactly 1 status field per check in YAML |
| M2: CI too strict | CI guardrails phase -- status-aware profiles from day one | INCUBATING checks pass CI with minimal fields |
| M3: CI too loose | CI guardrails phase -- gap detector in CI pipeline | New ACTIVE checks with CRITICAL gaps fail CI |
| M4: Over-engineered diagnostics | Diagnostics phase -- CLI-first, enumerate questions before building | Zero new framework dependencies; answers in <5 seconds |
| M5: Feedback not reaching YAML | Feedback phase -- build `apply-proposal` command | Git log shows brain YAML changes from applied proposals |
| M6: Rendering completeness overreach | Rendering completeness phase -- measure TRIGGERED display, not total display | Worksheet page count stable or decreasing |

---

## Phase-Specific Risk Assessment

Which v1.2 feature areas carry the most implementation risk.

| Feature Area | Risk Level | Primary Pitfall | Mitigation Complexity |
|--------------|-----------|-----------------|----------------------|
| Pipeline integrity audit | HIGH | C1: breaking working checks | LOW (make read-only first) |
| Automated QA | HIGH | C2: false positives erode trust | MEDIUM (precision tracking needed) |
| Feedback loops | MEDIUM | C3: collection without application | MEDIUM (apply workflow needed) |
| Knowledge ingestion | MEDIUM | C4: noise pollution | LOW (budget + TTL) |
| CI guardrails | MEDIUM | M2/M3: too strict or too loose | MEDIUM (status-aware profiles) |
| Diagnostics | LOW | M4: over-engineering | LOW (CLI-first decision) |
| Signal lifecycle | LOW | M1: bureaucracy | LOW (computed field, not state machine) |
| Rendering completeness | LOW | M6: overreach | LOW (correct metric definition) |

---

## Sources

- Direct codebase audit: `src/do_uw/pipeline.py` (StageCallbacks protocol, 7-stage architecture, state persistence)
- Direct codebase audit: `src/do_uw/knowledge/feedback.py` (record_feedback, get_feedback_summary, mark_feedback_applied, _auto_propose_check)
- Direct codebase audit: `src/do_uw/knowledge/lifecycle.py` (CheckStatus 4-state machine, transition_check, VALID_TRANSITIONS)
- Direct codebase audit: `src/do_uw/knowledge/learning.py` (AnalysisOutcome, CheckEffectiveness, fire rate computation, redundant pair detection)
- Direct codebase audit: `src/do_uw/knowledge/ingestion.py` (DocumentType, extract_knowledge_items, _extract_numbered_items, llm_extraction_fn)
- Direct codebase audit: `src/do_uw/knowledge/discovery.py` (_RELEVANCE_THRESHOLD=5, _DO_KEYWORDS, process_blind_spot_discoveries)
- Direct codebase audit: `src/do_uw/knowledge/gap_detector.py` (detect_gaps, ACQUIRED_SOURCES, GapReport)
- Direct codebase audit: `src/do_uw/brain/checks/fin/balance.yaml` (data_strategy.field_key, display_when, threshold structure)
- v1.1 PITFALLS.md (predecessor research for v1.1 pitfalls -- field_key routing conflicts, false positive injection, MCP boundary violations)
- [Avoid These 8 Mistakes in Test Automation Strategy (2026)](https://www.spec-india.com/blog/mistakes-to-avoid-in-test-automation-strategy) -- maintenance burden, selecting wrong tests for automation
- [Why False Positives Are the Bane of Application Security Testing](https://www.ox.security/blog/why-false-positives-are-the-bane-of-application-security-testing/) -- alert fatigue, trust erosion, 53% false positive rates
- [The Analyst Who Cried Malware: Rethinking Alert Fatigue](https://cardinalops.com/blog/rethinking-false-positives-alert-fatigue/) -- desensitization from false positives
- [How to Decide on Engineering Guardrails (LeadDev)](https://leaddev.com/software-quality/how-decide-engineering-guardrails) -- strict vs loose guardrail tradeoffs
- [Cross-Cutting Concerns in Microservices (Baeldung)](https://www.baeldung.com/cs/microservices-cross-cutting-concerns) -- observability as cross-cutting concern, sidecar pattern
- [Anti-Patterns in Knowledge Management (ResearchGate)](https://www.researchgate.net/publication/282452378_Anti-patterns_in_knowledge_management) -- knowledge system failure patterns
- [Data Quality Issues and Challenges (IBM)](https://www.ibm.com/think/insights/data-quality-issues) -- data decay, ingestion quality degradation

---
*Pitfalls research for: v1.2 System Intelligence features added to existing D&O underwriting pipeline*
*Researched: 2026-02-26*
