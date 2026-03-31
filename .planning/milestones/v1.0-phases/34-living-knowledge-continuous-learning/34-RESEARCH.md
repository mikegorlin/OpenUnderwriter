# Phase 34: Living Knowledge & Continuous Learning - Research

**Researched:** 2026-02-20
**Domain:** Knowledge management, feedback systems, CLI-driven calibration workflows, LLM document extraction
**Confidence:** HIGH (internal codebase research -- all findings verified against source code)

## Summary

Phase 34 transforms the knowledge system from a static check registry into a living analytical framework that ingests external documents, accepts underwriter feedback, proposes new checks, backtests proposals, and applies calibration changes -- all with human approval gates. The system gets smarter with every company analyzed and every external input ingested.

The codebase already has substantial infrastructure to build on: an existing ingestion module (`knowledge/ingestion.py`) with rule-based extraction, a brain DuckDB with versioned checks and changelog, a backtest engine (`knowledge/backtest.py`), check effectiveness tracking (`brain/brain_effectiveness.py`), a BrainWriter with insert/update/retire/promote operations, and an LLM extraction pipeline using instructor + Anthropic (claude-haiku-4-5). The primary work is: (1) replacing rule-based ingestion with LLM-powered extraction, (2) building the feedback CLI commands, (3) building the calibration workflow with git-based audit trail, (4) connecting automatic discovery during ACQUIRE to the ingestion pipeline, and (5) adding the INCUBATING lifecycle state to the brain check lifecycle.

**Primary recommendation:** Extend the existing `knowledge/ingestion.py` with LLM extraction (the TODO on line 212 says "Phase 13: Implement LLM-based extraction_fn for unstructured industry reports"), add new DuckDB tables for feedback and proposals, build CLI commands using the established Typer sub-app pattern, and wire impact simulation through the existing backtest infrastructure.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Ingestion Scope
- **Dual entry points**: CLI command (`do-uw ingest <file-or-url>`) for manual ingestion + automatic discovery during ACQUIRE stage pipeline runs
- **Document types at launch**: News articles/URLs, claims/settlement reports, short seller reports, regulatory actions, and other arbitrary documents
- **Document scope**: Company-specific, industry-wide, or cross-cutting (e.g., new SEC rules affecting all companies)
- **Ingestion output**: Impact report first (what checks affected, gaps found, proposed changes), then user approves which changes to apply. Never silent knowledge updates.
- **LLM extraction**: System uses LLM to parse ingested documents and extract: what company, what happened, what's the D&O implication

#### Learning Feedback Loop
- **Entry point**: CLI annotations -- `do-uw feedback AAPL --check LIT.REG.sec_investigation --note 'false positive, this was resolved'`
- **Feedback types**: Check accuracy (right/wrong), threshold tuning (too sensitive/too loose), missing coverage ('you missed X')
- **Timing by type**: 'Check was wrong' = immediate flag (next run reflects it). Threshold changes = accumulate for batch review via `do-uw calibrate`
- **Missing coverage flow**: Log the gap AND auto-propose an INCUBATING check definition with suggested threshold, data source, field routing. Check stays INCUBATING until human approves.
- **Reviewer tracking**: Named reviewers -- `do-uw feedback --reviewer 'john.smith'` tracks who provided what feedback
- **Run context**: Feedback can optionally reference a specific analysis run ID for traceability, but doesn't have to
- **Visibility**: CLI summary command (`do-uw feedback summary`) showing pending proposals, threshold drift, coverage gaps + worksheet 'Calibration Notes' section in next analysis run
- **Summary excludes**: Accuracy stats (not requested -- focus on actionable items: proposals, drift, gaps)

#### Check Lifecycle
- **Promotion path**: Backtest against cached state files first (show 'would have TRIGGERED for SMCI, CLEAR for AAPL'), then human approves
- **Backtesting**: Default to cached state files (fast, free). `do-uw backtest --live` for full re-run when higher confidence needed
- **Deactivation**: Soft deactivate -- check moves to INACTIVE status, still in checks.json, skipped during execution, can be reactivated
- **Provenance**: Full tracking -- created_from (ingested doc/feedback/pattern), created_by (system/reviewer), created_at, rationale, backtest_results
- **Lifecycle states**: INCUBATING -> ACTIVE -> INACTIVE (with possible reactivation)

#### Calibration Guardrails
- **Autonomy**: Nothing auto-changes. All calibration changes require explicit human approval via CLI. System proposes, human disposes.
- **Audit trail**: Git-based -- every calibration change is a git commit with structured message. Full history via git log, diff shows exactly what changed.
- **Rollback**: Git revert. Since changes are git commits, rollback = git revert. Simple, already built into the tool.
- **Preview before apply**: Diff + impact -- show both what's changing (like git diff) AND what the downstream effect would be on cached runs (which checks would flip, which companies affected). User sees full picture before committing.

### Claude's Discretion
- LLM model choice for document parsing (likely claude-haiku-4-5 for cost efficiency, matching existing extraction)
- Database schema for feedback/proposals (extend brain DuckDB vs knowledge SQLite vs new store)
- Exact CLI subcommand structure beyond the decided entry points
- Impact simulation implementation (full re-eval vs selective check re-run)
- How automatic discovery during ACQUIRE integrates with existing web search flow

### Deferred Ideas (OUT OF SCOPE)
- Outcome tracking ('this company had a claim 6 months later') -- valuable for calibration but requires external data input over time. Consider for a future enhancement.
- Per-check accuracy statistics -- useful once enough feedback accumulates. Not needed at launch.
- Auto-promotion with criteria -- explicitly rejected for now (human approval only), but could revisit if feedback volume grows.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ARCH-09 | Scoring weights, thresholds, tier boundaries stored in JSON config files -- never hardcoded | Calibration changes modify `brain/checks.json` thresholds and DuckDB rows; git commits track changes to JSON config files |
| ARCH-10 | Predecessor BRAIN/ knowledge assets carried forward -- checks.json, SCORING.md, PATTERNS.md, sector_baselines.json, critical_red_flags.json | Ingestion adds new checks to the existing brain asset store; lifecycle management ensures continuity |
| SECT7-06 | Claims Correlation Scoring -- calibration flagged | Feedback loop allows threshold tuning for claims correlation scoring factors; backtest validates changes |
| SECT7-07 | Claim Probability output -- includes comparison to industry base rate | Calibration can adjust base rate thresholds; sector baselines are updateable via the same workflow |
| SECT7-11 | NEEDS CALIBRATION -- system parameters require calibration against real-world cases | Primary requirement addressed: feedback loop + backtest + human-approved calibration flow |
</phase_requirements>

## Standard Stack

### Core (Already in Project)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `anthropic` | >=0.79.0 | LLM API for document parsing | Already used by LLMExtractor for SEC filing extraction |
| `instructor` | >=1.14.0 | Structured LLM output extraction with Pydantic | Already used for schema-validated extraction |
| `duckdb` | >=1.4.4 | Brain database with versioned checks, changelog, check_runs | Already the brain's primary store |
| `typer` | >=0.15 | CLI framework with sub-app composition | Already used for all CLI commands |
| `rich` | >=13.0 | Terminal tables, progress display, diff output | Already used for all CLI output |
| `pydantic` | >=2.10 | Data models, validation, serialization | Foundation of entire state model |
| `sqlalchemy` | >=2.0 | Knowledge store ORM (knowledge.db) | Already used for knowledge SQLite store |

### Supporting (May Need)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `httpx` | >=0.28 | URL content fetching for ingestion | Already in project; needed for `do-uw ingest <url>` |
| `subprocess` | stdlib | Git operations for audit trail | For `git add`, `git commit` in calibration apply |

### No New Dependencies Needed

Phase 34 does not require any new external libraries. All capabilities (LLM extraction, database, CLI, HTTP) are already available in the project dependencies.

## Architecture Patterns

### Recommended New File Structure

```
src/do_uw/
  cli_ingest.py           # NEW: `do-uw ingest` commands
  cli_feedback.py         # NEW: `do-uw feedback` commands
  knowledge/
    ingestion.py          # EXTEND: Add LLM extraction, URL support
    ingestion_llm.py      # NEW: LLM-powered document parser
    ingestion_models.py   # NEW: Pydantic models for ingestion results
    feedback.py           # NEW: Feedback recording and querying
    feedback_models.py    # NEW: Pydantic models for feedback
    proposals.py          # NEW: Check proposal generation and management
    calibrate.py          # NEW: Calibration impact simulation
  calibration/
    runner.py             # EXISTING: extend to support backtest proposals
  brain/
    brain_schema.py       # EXTEND: Add feedback + proposals tables
    brain_writer.py       # EXTEND: Add INCUBATING lifecycle support
```

### Pattern 1: LLM Document Extraction (Claude's Discretion: Model Choice)

**Recommendation:** Use claude-haiku-4-5 via the existing `LLMExtractor` pattern.

**What:** Extract structured D&O implications from arbitrary documents using the same instructor + Anthropic pattern used for SEC filing extraction.

**Why claude-haiku-4-5:** The existing `LLMExtractor` in `src/do_uw/stages/extract/llm/extractor.py` already uses claude-haiku-4-5 with instructor for structured extraction from SEC filings. Cost is approximately $0.10-0.20 per filing. For ingestion documents (typically much shorter than 10-K filings), cost will be even lower. Using the same model maintains consistency.

**Example schema:**
```python
# Source: Pattern from src/do_uw/stages/extract/llm/extractor.py
from pydantic import BaseModel, Field

class DocumentIngestionResult(BaseModel):
    """LLM-extracted structured output from an ingested document."""
    company_ticker: str | None = Field(None, description="Affected company ticker, if specific")
    industry_scope: str = Field("universal", description="universal, sector-specific, or company-specific")
    event_type: str = Field(description="LITIGATION, REGULATORY, SETTLEMENT, SHORT_SELLER, etc.")
    event_summary: str = Field(description="One-paragraph summary of the event")
    do_implications: list[str] = Field(description="D&O liability implications identified")
    affected_checks: list[str] = Field(description="Check IDs that this information relates to")
    proposed_new_checks: list[ProposedCheck] = Field(default_factory=list)
    gap_analysis: str = Field("", description="What existing checks miss about this event")
    confidence: str = Field("MEDIUM", description="HIGH, MEDIUM, LOW")
```

### Pattern 2: Feedback Storage (Claude's Discretion: Database Schema)

**Recommendation:** Extend brain DuckDB with new tables, NOT knowledge SQLite.

**Rationale:** The brain DuckDB (`brain.duckdb`) is the authority for check lifecycle, versioning, and run tracking. Feedback directly relates to checks and runs. Adding feedback tables to brain DuckDB maintains a single authority for check-related operations. The knowledge SQLite store (`knowledge.db`) is primarily for notes and FTS search, not operational check management.

**New DuckDB tables:**
```sql
-- Feedback entries from underwriters
CREATE TABLE IF NOT EXISTS brain_feedback (
    feedback_id INTEGER PRIMARY KEY DEFAULT nextval('feedback_seq'),
    ticker VARCHAR,                          -- NULL = cross-company
    check_id VARCHAR,                        -- NULL = general feedback
    run_id VARCHAR,                          -- Optional: link to specific run
    feedback_type VARCHAR NOT NULL,          -- ACCURACY, THRESHOLD, MISSING_COVERAGE
    direction VARCHAR,                       -- FALSE_POSITIVE, FALSE_NEGATIVE, TOO_SENSITIVE, TOO_LOOSE
    note TEXT NOT NULL,
    reviewer VARCHAR NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'PENDING',  -- PENDING, APPLIED, REJECTED
    applied_at TIMESTAMP,
    applied_change_id INTEGER,               -- Links to brain_changelog
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

-- Check proposals (from ingestion, feedback, or pattern detection)
CREATE TABLE IF NOT EXISTS brain_proposals (
    proposal_id INTEGER PRIMARY KEY DEFAULT nextval('proposal_seq'),
    source_type VARCHAR NOT NULL,            -- INGESTION, FEEDBACK, PATTERN
    source_ref VARCHAR,                      -- Document name, feedback_id, etc.
    check_id VARCHAR,                        -- NULL for new check proposals
    proposal_type VARCHAR NOT NULL,          -- NEW_CHECK, THRESHOLD_CHANGE, DEACTIVATION
    proposed_check JSON,                     -- Full check definition for NEW_CHECK
    proposed_changes JSON,                   -- {field: {old: X, new: Y}} for changes
    backtest_results JSON,                   -- Backtest outcome snapshot
    rationale TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'PENDING',  -- PENDING, APPROVED, REJECTED, APPLIED
    reviewed_by VARCHAR,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);
```

### Pattern 3: CLI Sub-App Composition (Verified Pattern)

**What:** Each new CLI domain gets its own `cli_*.py` file registered as a Typer sub-app in `cli.py`.

**Source:** Verified from `src/do_uw/cli.py` lines 44-49 -- existing pattern for brain_app, calibrate_app, dashboard_app, knowledge_app, pricing_app, validate_app.

```python
# In cli.py:
from do_uw.cli_ingest import ingest_app
from do_uw.cli_feedback import feedback_app
app.add_typer(ingest_app, name="ingest")
app.add_typer(feedback_app, name="feedback")
```

### Pattern 4: Impact Simulation (Claude's Discretion: Implementation)

**Recommendation:** Selective check re-run using existing backtest infrastructure, NOT full pipeline re-eval.

**Rationale:** The existing `run_backtest()` in `knowledge/backtest.py` already loads a historical state.json and re-runs all checks against it. For impact simulation:
1. Load cached state files from `output/{TICKER}/state.json`
2. Apply proposed changes to in-memory check definitions
3. Run `execute_checks()` with the modified definitions against existing ExtractedData
4. Compare results with the original run stored in `state.analysis.check_results`
5. Report which checks flipped (TRIGGERED->CLEAR, CLEAR->TRIGGERED, etc.)

This is fast (no API calls, no data acquisition) and leverages existing infrastructure. The `compare_backtests()` function already produces the right diff format.

### Pattern 5: Automatic Discovery Integration (Claude's Discretion)

**Recommendation:** Add a post-acquisition ingestion hook in ACQUIRE stage.

**What:** After blind spot web search results are collected, automatically feed relevant results through the ingestion pipeline to identify new risks and propose checks.

**How:** The `WebSearchClient` in `stages/acquire/clients/web_search.py` already collects blind spot results into `state.acquired_data.blind_spot_results`. Add a hook after blind spot collection that:
1. Filters results by D&O relevance score
2. Fetches full text for high-relevance URLs using httpx
3. Runs LLM extraction on the content
4. Stores proposals in `brain_proposals` table
5. Includes a "Discovery Findings" section in the impact report

This does NOT auto-change anything -- it just logs proposals for the next `do-uw feedback summary` review.

### Pattern 6: Git-Based Audit Trail for Calibration

**What:** When `do-uw calibrate apply` commits changes, it uses subprocess to create a git commit with a structured message.

**Implementation:**
```python
import subprocess

def _git_commit_calibration(
    files_changed: list[str],
    summary: str,
    details: str,
) -> str:
    """Create a git commit for calibration changes.

    Returns the commit hash.
    """
    for f in files_changed:
        subprocess.run(["git", "add", f], check=True)

    message = f"calibrate: {summary}\n\n{details}"
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True, text=True, check=True,
    )
    # Extract commit hash from output
    return result.stdout.strip()
```

The user explicitly chose git-based audit trail over a custom audit table, and git revert for rollback. This means:
- `checks.json` changes are committed to git
- `brain.duckdb` changes are also committed (binary diff, but git tracks it)
- `do-uw calibrate show` can shell out to `git log --oneline -- brain/checks.json` for history
- Rollback is `git revert <hash>` followed by brain re-sync

### Anti-Patterns to Avoid

- **Silent knowledge changes:** NEVER modify checks or thresholds without explicit user approval. Every change must go through the proposal -> review -> apply workflow.
- **Multiple state stores for feedback:** Keep ALL feedback/proposals in brain DuckDB, not split across SQLite and DuckDB.
- **Coupled ingestion and application:** Ingestion ONLY produces proposals and impact reports. Application is a separate explicit step.
- **Auto-promoting checks:** Even if backtest results look great, checks stay INCUBATING until a human approves them. The user explicitly rejected auto-promotion.
- **Modifying AnalysisState for feedback:** Feedback is about the knowledge system (checks, thresholds), NOT about the pipeline state. Don't add feedback fields to AnalysisState.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured LLM extraction from documents | Custom prompt + JSON parsing | `instructor` + `anthropic` via existing `LLMExtractor` pattern | Already handles retries, validation, caching, cost tracking |
| Check versioning and audit trail | Custom version tracking | Existing `BrainWriter.update_check()` with auto-versioning + `brain_changelog` | Already implements append-only versioning with changelog |
| Check backtesting against historical data | Custom replay engine | Existing `run_backtest()` + `compare_backtests()` | Already loads state files, runs checks, produces comparison diffs |
| Check effectiveness metrics | Custom statistics computation | Existing `brain_effectiveness.py` + `store_bulk.py` check stats | Already computes fire/skip/clear rates, always-fire/never-fire detection |
| CLI output formatting | Custom table formatting | Rich `Table` and `Console` (existing pattern in all cli_*.py) | Consistent with all existing CLI output |
| Git operations | Custom VCS wrapper | `subprocess.run(["git", ...])` | Simple, direct, no abstraction needed for 3-4 git operations |

**Key insight:** The codebase already has 80% of the plumbing needed. The existing BrainWriter, backtest engine, ingestion module, LLM extractor, and effectiveness tracking are purpose-built foundations that Phase 34 extends rather than replaces.

## Common Pitfalls

### Pitfall 1: Two Knowledge Stores Drift
**What goes wrong:** The knowledge SQLite store (`knowledge.db`) and brain DuckDB (`brain.duckdb`) get out of sync when feedback is stored in one but changes are applied in the other.
**Why it happens:** The codebase has two stores that coexist (acknowledged in `brain_effectiveness.py` lines 8-16: "Two systems coexist... These will converge in a future plan").
**How to avoid:** Store ALL Phase 34 feedback and proposals in brain DuckDB exclusively. Knowledge SQLite is for notes/FTS search only. Don't add new operational tables to knowledge.db.
**Warning signs:** If you find yourself needing to query both stores in a single workflow, you've split concerns incorrectly.

### Pitfall 2: Ingestion Changes Bypass Approval
**What goes wrong:** A well-intentioned shortcut lets ingestion directly create ACTIVE checks instead of INCUBATING ones.
**Why it happens:** The existing `_create_incubating_check()` in `ingestion.py` already creates checks with status="INCUBATING", but the new LLM-based flow might be tempted to fast-track well-defined proposals.
**How to avoid:** Enforce INCUBATING as the ONLY status for auto-created checks. Promotion requires explicit `do-uw calibrate apply` command.
**Warning signs:** Any code path that creates a check with status != "INCUBATING" outside of the calibrate apply workflow.

### Pitfall 3: Git Commits on Dirty Working Tree
**What goes wrong:** `do-uw calibrate apply` tries to git commit but the user has uncommitted changes to checks.json or brain.duckdb, causing merge conflicts or accidental inclusion of unrelated changes.
**Why it happens:** The user decided on git-based audit trail, but the working directory might not be clean.
**How to avoid:** Before `calibrate apply`, check `git status --porcelain` for modified tracked files in the brain/ directory. Warn and abort if dirty. Only stage and commit the specific files that `calibrate apply` modifies.
**Warning signs:** `git add -A` in calibration code (should be `git add brain/checks.json brain/brain.duckdb` specifically).

### Pitfall 4: Backtest Compares Wrong Baseline
**What goes wrong:** Impact simulation compares proposed check results against the CURRENT run, but the current run was done with CURRENT checks (not the proposed ones), so the diff is meaningless.
**Why it happens:** Confusion about what "baseline" means in backtest comparison.
**How to avoid:** The baseline is the EXISTING check results stored in `state.analysis.check_results`. The comparison target is a FRESH execution of the modified checks against the SAME `state.extracted` data. The diff shows what WOULD CHANGE if the proposal were applied.
**Warning signs:** If backtest shows zero changes for a proposal that clearly modifies a threshold, the comparison is wrong.

### Pitfall 5: Feedback Volume Overload
**What goes wrong:** Without filtering or summarization, `do-uw feedback summary` becomes an unreadable wall of text with hundreds of pending items.
**Why it happens:** As the system processes more companies and receives more feedback, pending items accumulate.
**How to avoid:** Group feedback by type (accuracy, threshold, missing coverage), show counts per group, and only expand details on request. Default summary shows: N pending accuracy flags, M threshold proposals, K coverage gaps. Details via `--verbose` or `--check <id>`.
**Warning signs:** Summary output exceeding 50 lines without filtering options.

### Pitfall 6: INCUBATING Checks Polluting Active Runs
**What goes wrong:** INCUBATING checks accidentally get loaded into the check engine and slow down or confuse the pipeline.
**Why it happens:** The `BrainDBLoader.load_checks()` uses `brain_checks_active` view which filters on `lifecycle_state != 'RETIRED'`. If INCUBATING is not excluded, these checks enter the pipeline.
**How to avoid:** Update the `brain_checks_active` view to ALSO exclude INCUBATING checks: `WHERE lifecycle_state NOT IN ('RETIRED', 'INCUBATING')`. INCUBATING checks are only visible via `do-uw brain status` and `do-uw feedback summary`.
**Warning signs:** Check count increasing unexpectedly after ingestion runs.

## Code Examples

### Existing Ingestion Hook Point (Line 212 TODO)
```python
# Source: src/do_uw/knowledge/ingestion.py lines 210-214
def extract_knowledge_items(
    text: str,
    doc_type: DocumentType,
    extraction_fn: Callable[[str, DocumentType], list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    # TODO(Phase 13): Implement LLM-based extraction_fn for unstructured industry reports
    if extraction_fn is not None:
        return extraction_fn(text, doc_type)
```
The `extraction_fn` parameter is the designated hook for LLM extraction. Phase 34 should implement a function with this signature that calls the LLM.

### Existing BrainWriter Lifecycle Operations
```python
# Source: src/do_uw/brain/brain_writer.py
writer = BrainWriter()

# Insert new INCUBATING check
writer.insert_check(
    check_id="ING.NEW.check_id",
    check_data={
        "name": "New check from ingestion",
        "content_type": "EVALUATIVE_CHECK",
        "lifecycle_state": "INCUBATING",  # NOT in brain_checks_active
        "threshold_type": "tiered",
        "threshold_red": "> 5",
        ...
    },
    reason="Auto-proposed from ingested short seller report",
    created_by="ingestion_pipeline",
)

# Promote to ACTIVE after human approval
writer.promote_check(
    check_id="ING.NEW.check_id",
    new_lifecycle="SCORING",  # Now appears in brain_checks_active
    reason="Approved by john.smith after backtest showed 3/12 tickers triggered",
    promoted_by="john.smith",
)

# Soft deactivate (INACTIVE -- skipped but not deleted)
writer.update_check(
    check_id="FIN.LIQ.obsolete_check",
    changes={"lifecycle_state": "INACTIVE"},
    reason="Threshold was too aggressive, deactivated pending recalibration",
    changed_by="calibration_pipeline",
)
```

### Existing Backtest Infrastructure
```python
# Source: src/do_uw/knowledge/backtest.py
from do_uw.knowledge.backtest import run_backtest, compare_backtests

# Run current checks against historical state
result_before = run_backtest(Path("output/AAPL/state.json"), record=False)

# ... apply proposed threshold change ...

result_after = run_backtest(Path("output/AAPL/state.json"), record=False)

# Compare what changed
comparison = compare_backtests(result_before, result_after)
for change in comparison.changed:
    print(f"{change['check_id']}: {change['old_status']} -> {change['new_status']}")
```

### Existing Check Run Recording
```python
# Source: src/do_uw/brain/brain_effectiveness.py
from do_uw.brain.brain_effectiveness import record_check_runs_batch

rows = [
    {
        "run_id": f"pipeline_{ticker}_{timestamp}",
        "check_id": "FIN.LIQ.position",
        "check_version": 1,
        "status": "TRIGGERED",
        "value": "0.85",
        "evidence": "Current ratio 0.85 below red threshold 1.0",
        "ticker": "SMCI",
    },
    # ... more check results ...
]
record_check_runs_batch(conn, rows)
```

### Existing CLI Sub-App Pattern
```python
# Source: Pattern from src/do_uw/cli_brain.py
import typer
from rich.console import Console
from rich.table import Table

feedback_app = typer.Typer(
    name="feedback",
    help="Underwriter feedback: record, review, summarize",
    no_args_is_help=True,
)
console = Console()

@feedback_app.command("add")
def add(
    ticker: str = typer.Argument(help="Ticker the feedback applies to"),
    check: str = typer.Option(None, "--check", "-c", help="Check ID"),
    note: str = typer.Option(..., "--note", "-n", help="Feedback text"),
    reviewer: str = typer.Option("anonymous", "--reviewer", "-r"),
    type: str = typer.Option("ACCURACY", "--type", "-t"),
    run_id: str = typer.Option(None, "--run-id"),
) -> None:
    """Record underwriter feedback on a check result."""
    ...

@feedback_app.command("summary")
def summary() -> None:
    """Show pending proposals, threshold drift, coverage gaps."""
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Rule-based ingestion only (regex patterns) | LLM extraction available via instructor+anthropic | Phase 22 (LLM extraction) | Phase 34 can use LLM for smart document parsing |
| Single checks.json as authority | brain.duckdb with versioned checks + checks.json fallback | Phase 32-33 (brain migration) | Check lifecycle management already supports insert/update/retire/promote |
| No backtest capability | `run_backtest()` + `compare_backtests()` available | Phase 33 | Impact simulation can reuse backtest infrastructure |
| No check run tracking | `brain_check_runs` table + `brain_effectiveness` metrics | Phase 30 | Fire rate and effectiveness data available for calibration |
| Static check definitions | BrainWriter with auto-versioning and changelog | Phase 32 | Full audit trail for check modifications already exists |

**Deprecated/outdated:**
- `knowledge.db` CheckRun table: Superseded by `brain_check_runs` in DuckDB for operational tracking. Keep knowledge.db for notes/FTS only.
- `config/check_classification.json`: Phase 26 classification is now embedded in check definitions, not a separate file.

## Open Questions

1. **INCUBATING lifecycle state mapping to brain_checks_active view**
   - What we know: The `brain_checks_active` view currently filters `WHERE lifecycle_state != 'RETIRED'`. The existing lifecycle states in brain_migrate.py are: INVESTIGATION, MONITORING, SCORING, RETIRED.
   - What's unclear: Should INCUBATING be a new state or map to INVESTIGATION? The user decided on INCUBATING -> ACTIVE -> INACTIVE as the lifecycle. This doesn't perfectly map to the existing INVESTIGATION -> MONITORING -> SCORING -> RETIRED lifecycle.
   - Recommendation: Add INCUBATING as a new lifecycle_state value. Update `brain_checks_active` view to exclude both RETIRED and INCUBATING: `WHERE lifecycle_state NOT IN ('RETIRED', 'INCUBATING')`. Map user's "ACTIVE" to the existing SCORING state (which means the check participates in evaluation). Map INACTIVE to a new state that the view also excludes. This preserves backward compatibility while adding the new lifecycle path.

2. **Feedback referencing run_id format**
   - What we know: Pipeline runs generate run_ids like `pipeline_AAPL_20260220_143022` (visible in brain_check_runs). The user wants optional run_id in feedback.
   - What's unclear: How does the user discover the run_id to reference? It's currently only visible in brain_check_runs, not surfaced in CLI output.
   - Recommendation: After each pipeline run, print the run_id to CLI output. Also store it in the output state.json metadata. For `do-uw feedback`, if no run_id specified, default to the most recent run for that ticker.

3. **Binary brain.duckdb in git audit trail**
   - What we know: User decided on git-based audit trail. checks.json diffs are readable. brain.duckdb is a binary file -- git tracks it but diffs are useless.
   - What's unclear: Is this acceptable? The user said "git log, diff shows exactly what changed." Binary DuckDB diffs won't show what changed.
   - Recommendation: After each calibration change, ALSO export the affected check(s) to a human-readable JSON sidecar file (`brain/calibration_log.jsonl` -- one JSON line per change with timestamp, check_id, old_threshold, new_threshold, reason, reviewer). This gives both git-trackable changes AND a readable audit trail. The BrainWriter changelog already has this data; the sidecar is just a convenience export.

4. **URL ingestion and content fetching**
   - What we know: User decided `do-uw ingest <file-or-url>`. The project has httpx for HTTP.
   - What's unclear: Should URL fetching use the existing `fetch` MCP tool or direct httpx? MCP tools are supposed to be ACQUIRE-stage only per CLAUDE.md.
   - Recommendation: Use direct httpx for CLI-driven ingestion (not a pipeline stage, so MCP boundary doesn't apply). Use `newspaper`-style extraction or simple HTML-to-text conversion for readability. Keep it simple -- httpx GET + basic HTML tag stripping. The LLM is resilient to messy text input.

## Sources

### Primary (HIGH confidence -- direct codebase examination)
- `src/do_uw/knowledge/ingestion.py` -- Existing ingestion module with TODO for LLM extraction (line 212)
- `src/do_uw/brain/brain_writer.py` -- BrainWriter with insert/update/retire/promote and auto-versioning
- `src/do_uw/brain/brain_schema.py` -- DuckDB schema with 7 tables + 3 views + indexes
- `src/do_uw/brain/brain_effectiveness.py` -- Check effectiveness tracking, fire rate computation
- `src/do_uw/brain/brain_loader.py` -- BrainDBLoader with lifecycle filtering and enrichment overlay
- `src/do_uw/knowledge/backtest.py` -- Backtest engine: run_backtest() + compare_backtests()
- `src/do_uw/knowledge/learning.py` -- Analysis outcome recording, effectiveness metrics, redundancy detection
- `src/do_uw/stages/extract/llm/extractor.py` -- LLMExtractor using instructor + anthropic claude-haiku-4-5
- `src/do_uw/knowledge/models.py` -- SQLAlchemy ORM models with Check, CheckHistory, CheckRun, Note
- `src/do_uw/stages/analyze/check_engine.py` -- Check execution engine with content-type dispatch
- `src/do_uw/stages/analyze/check_results.py` -- CheckResult model with traceability chain
- `src/do_uw/cli.py` -- CLI entry point with sub-app registration pattern
- `src/do_uw/cli_brain.py` -- Brain CLI commands (status, gaps, effectiveness, changelog, backlog, export-docs, backtest)
- `src/do_uw/cli_calibrate.py` -- Existing calibrate CLI (run, report, enrich -- enrich is stub)
- `src/do_uw/calibration/runner.py` -- CalibrationRunner with checkpointing, learning infrastructure recording
- `src/do_uw/calibration/config.py` -- 12 calibration tickers with expected tiers
- `src/do_uw/pipeline.py` -- Pipeline orchestrator with 7-stage execution
- `src/do_uw/models/state.py` -- AnalysisState, AcquiredData, ExtractedData, AnalysisResults
- `src/do_uw/knowledge/gap_detector.py` -- Gap detection for pipeline coverage

### Secondary (MEDIUM confidence -- inferred from existing patterns)
- CLI sub-app pattern inference from 9 existing cli_*.py files
- DuckDB schema extension pattern from brain_schema.py DDL style
- LLM extraction cost estimates from existing LLMExtractor usage ($0.10-0.20 per filing)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in pyproject.toml, no new dependencies
- Architecture: HIGH -- all patterns verified against existing codebase, extending proven infrastructure
- Pitfalls: HIGH -- identified from actual codebase state (two-store drift, view filtering, git operations)
- LLM extraction approach: HIGH -- existing LLMExtractor provides exact pattern to follow
- Database schema: MEDIUM -- new tables proposed but schema specifics may need adjustment during implementation

**Research date:** 2026-02-20
**Valid until:** 2026-03-20 (stable -- internal codebase, no external dependency changes expected)
