# Phase 34: Living Knowledge & Continuous Learning - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

The knowledge system becomes a living analytical framework that can ingest new information, accept underwriter feedback, propose new checks, backtest proposals, and apply calibration changes — all with human approval gates. The system gets smarter with every company analyzed and every external input ingested, without auto-changing anything.

</domain>

<decisions>
## Implementation Decisions

### Ingestion Scope
- **Dual entry points**: CLI command (`do-uw ingest <file-or-url>`) for manual ingestion + automatic discovery during ACQUIRE stage pipeline runs
- **Document types at launch**: News articles/URLs, claims/settlement reports, short seller reports, regulatory actions, and other arbitrary documents
- **Document scope**: Company-specific, industry-wide, or cross-cutting (e.g., new SEC rules affecting all companies)
- **Ingestion output**: Impact report first (what checks affected, gaps found, proposed changes), then user approves which changes to apply. Never silent knowledge updates.
- **LLM extraction**: System uses LLM to parse ingested documents and extract: what company, what happened, what's the D&O implication

### Learning Feedback Loop
- **Entry point**: CLI annotations — `do-uw feedback AAPL --check LIT.REG.sec_investigation --note 'false positive, this was resolved'`
- **Feedback types**: Check accuracy (right/wrong), threshold tuning (too sensitive/too loose), missing coverage ('you missed X')
- **Timing by type**: 'Check was wrong' = immediate flag (next run reflects it). Threshold changes = accumulate for batch review via `do-uw calibrate`
- **Missing coverage flow**: Log the gap AND auto-propose an INCUBATING check definition with suggested threshold, data source, field routing. Check stays INCUBATING until human approves.
- **Reviewer tracking**: Named reviewers — `do-uw feedback --reviewer 'john.smith'` tracks who provided what feedback
- **Run context**: Feedback can optionally reference a specific analysis run ID for traceability, but doesn't have to
- **Visibility**: CLI summary command (`do-uw feedback summary`) showing pending proposals, threshold drift, coverage gaps + worksheet 'Calibration Notes' section in next analysis run
- **Summary excludes**: Accuracy stats (not requested — focus on actionable items: proposals, drift, gaps)

### Check Lifecycle
- **Promotion path**: Backtest against cached state files first (show 'would have TRIGGERED for SMCI, CLEAR for AAPL'), then human approves
- **Backtesting**: Default to cached state files (fast, free). `do-uw backtest --live` for full re-run when higher confidence needed
- **Deactivation**: Soft deactivate — check moves to INACTIVE status, still in checks.json, skipped during execution, can be reactivated
- **Provenance**: Full tracking — created_from (ingested doc/feedback/pattern), created_by (system/reviewer), created_at, rationale, backtest_results
- **Lifecycle states**: INCUBATING → ACTIVE → INACTIVE (with possible reactivation)

### Calibration Guardrails
- **Autonomy**: Nothing auto-changes. All calibration changes require explicit human approval via CLI. System proposes, human disposes.
- **Audit trail**: Git-based — every calibration change is a git commit with structured message. Full history via git log, diff shows exactly what changed.
- **Rollback**: Git revert. Since changes are git commits, rollback = git revert. Simple, already built into the tool.
- **Preview before apply**: Diff + impact — show both what's changing (like git diff) AND what the downstream effect would be on cached runs (which checks would flip, which companies affected). User sees full picture before committing.

### Claude's Discretion
- LLM model choice for document parsing (likely claude-haiku-4-5 for cost efficiency, matching existing extraction)
- Database schema for feedback/proposals (extend brain DuckDB vs knowledge SQLite vs new store)
- Exact CLI subcommand structure beyond the decided entry points
- Impact simulation implementation (full re-eval vs selective check re-run)
- How automatic discovery during ACQUIRE integrates with existing web search flow

</decisions>

<specifics>
## Specific Ideas

- Feedback should feel like annotating a document — quick, low friction, not a form to fill out
- The `do-uw calibrate apply` flow should feel like `git add` + `git commit` — review what's staged, then commit
- Backtest results should be a clear table: company | check | current result | proposed result | changed?
- The system should never surprise an underwriter — if behavior changed since last run, say why in the worksheet

</specifics>

<deferred>
## Deferred Ideas

- Outcome tracking ('this company had a claim 6 months later') — valuable for calibration but requires external data input over time. Consider for a future enhancement.
- Per-check accuracy statistics — useful once enough feedback accumulates. Not needed at launch.
- Auto-promotion with criteria — explicitly rejected for now (human approval only), but could revisit if feedback volume grows.

</deferred>

---

*Phase: 34-living-knowledge-continuous-learning*
*Context gathered: 2026-02-21*
