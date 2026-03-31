# Phase 51: Feedback Loop - Context

**Gathered:** 2026-02-27
**Status:** Ready for planning

<domain>
## Phase Boundary

End-to-end underwriter feedback loop: `do-uw feedback <TICKER>` captures structured reactions to check results, `do-uw feedback process` batch-processes feedback into calibration proposals with impact projections, and `do-uw brain apply-proposal <id>` modifies brain YAML directly, rebuilds DuckDB, validates regression, and creates a git commit. The loop closes completely -- feedback reaches brain YAML, not just DuckDB.

Interactive walk-through mode (CALIB-02) is explicitly deferred to v1.3+. This phase covers list-based selection, not guided one-by-one.

</domain>

<decisions>
## Implementation Decisions

### Reaction data model
- Three-way reaction types: AGREE, DISAGREE, ADJUST_SEVERITY
- Severity adjustment granularity: Claude's discretion (target level vs directional nudge -- pick what calibration proposals can best consume)
- Rationale is REQUIRED for every reaction -- not optional
- Feedback is ticker-specific by default (`feedback <TICKER>`), with a `--general` flag for systemic observations not tied to one company

### Capture flow UX
- `feedback <TICKER>` shows all triggered checks for that ticker run, underwriter picks which to react to from the list
- Full check detail shown per check: description, data evaluated, threshold that triggered, severity level -- underwriter should not need to flip back to worksheet
- Both interactive CLI (default) and file-based workflows: `feedback export <TICKER>` generates a structured review file for bulk/offline editing, `feedback import <file>` reads it back
- Interactive mode uses terminal prompts for selection and reaction entry

### Proposal presentation
- `feedback process` outputs a table summary of all generated proposals (check ID, direction, confidence, impact)
- Drill-down available per proposal for full before/after analysis
- Impact projections show BOTH: check fire rate change (always) and score impact on past tickers (when 3+ historical runs exist)
- Proposals include confidence indicator based on feedback volume: LOW (1 entry), MEDIUM (2-3 entries), HIGH (4+ entries)
- No TTL or automatic expiry -- proposals persist until explicitly approved, rejected, or deleted by underwriter

### Apply safety
- `brain apply-proposal <id>` shows YAML diff and requires confirmation prompt before writing
- `--yes` flag skips confirmation for scripted usage
- One proposal applied at a time -- no batch mode. Each proposal gets its own validation and commit.
- Git commit messages are structured and auto-generated: e.g., `brain(calibrate): adjust GOV-012 severity HIGH->MEDIUM based on 4 feedback entries`
- No editor opened for commit message -- fully automated

### Claude's Discretion
- Feedback storage strategy (DuckDB table vs files vs hybrid)
- Severity adjustment granularity (target level vs directional nudge)
- Regression validation behavior (auto-rollback vs block-and-require-force)
- Proposal aggregation algorithm (how multiple feedback entries for same check combine)
- Interactive CLI prompt library/approach

</decisions>

<specifics>
## Specific Ideas

- Underwriter should see full check context during feedback capture -- they shouldn't need the worksheet open alongside the feedback CLI
- The three CLI commands map cleanly to the success criteria: `feedback <TICKER>` (capture), `feedback process` (proposals), `brain apply-proposal <id>` (apply)
- Commit messages should be machine-parseable for later audit of brain evolution

</specifics>

<deferred>
## Deferred Ideas

- CALIB-02: Interactive walk-through mode (guided one-by-one through all checks) -- explicitly v1.3+
- CALIB-01: Feedback-driven threshold calibration with backtest (auto-proposes threshold changes when 10+ entries agree) -- v1.3+
- Batch apply-proposal (multiple proposals in one atomic commit) -- could revisit if one-at-a-time proves too slow in practice

</deferred>

---

*Phase: 51-feedback-loop*
*Context gathered: 2026-02-27*
