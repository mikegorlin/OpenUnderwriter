# Phase 51: Feedback Loop - Research

**Researched:** 2026-02-27
**Domain:** Underwriter feedback capture, calibration proposal generation, YAML write-back with git audit
**Confidence:** HIGH

## Summary

Phase 51 implements the end-to-end underwriter feedback loop: capture structured reactions to triggered signals, batch-process them into calibration proposals with impact projections, and apply proposals by modifying brain YAML files with automated git commits. The codebase already has ~70% of the infrastructure: DuckDB tables (`brain_feedback`, `brain_proposals`), feedback recording (`knowledge/feedback.py`), proposal preview and apply (`knowledge/calibrate.py`, `calibrate_impact.py`), and CLI stubs (`cli_feedback.py`, `cli_calibrate.py`). The existing code operates on DuckDB only and uses a flat `--note`/`--check`/`--type` CLI. Phase 51 replaces this with (1) a ticker-centric interactive feedback flow showing triggered check details, (2) three-way reaction types (AGREE/DISAGREE/ADJUST_SEVERITY), (3) batch proposal generation with aggregation and confidence, and (4) YAML write-back via `brain apply-proposal` that modifies the source YAML files, rebuilds DuckDB, validates, and commits.

The critical technical gap is the YAML write-back: the current `apply_calibration()` writes only to DuckDB and commits `brain.duckdb`. The success criteria require changes to reach brain YAML (`src/do_uw/brain/signals/**/*.yaml`), which is the source of truth for `brain build`. This requires a round-trip YAML library (ruamel.yaml) that preserves comments and formatting.

**Primary recommendation:** Use ruamel.yaml for YAML round-trip editing, Rich+Typer for interactive prompts (no new dependency), and extend the existing feedback/calibrate modules rather than building parallel systems.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Three-way reaction types: AGREE, DISAGREE, ADJUST_SEVERITY
- Rationale is REQUIRED for every reaction -- not optional
- Feedback is ticker-specific by default (`feedback <TICKER>`), with a `--general` flag for systemic observations not tied to one company
- `feedback <TICKER>` shows all triggered checks for that ticker run, underwriter picks which to react to from the list
- Full check detail shown per check: description, data evaluated, threshold that triggered, severity level -- underwriter should not need to flip back to worksheet
- Both interactive CLI (default) and file-based workflows: `feedback export <TICKER>` generates a structured review file for bulk/offline editing, `feedback import <file>` reads it back
- Interactive mode uses terminal prompts for selection and reaction entry
- `feedback process` outputs a table summary of all generated proposals (check ID, direction, confidence, impact)
- Drill-down available per proposal for full before/after analysis
- Impact projections show BOTH: check fire rate change (always) and score impact on past tickers (when 3+ historical runs exist)
- Proposals include confidence indicator based on feedback volume: LOW (1 entry), MEDIUM (2-3 entries), HIGH (4+ entries)
- No TTL or automatic expiry -- proposals persist until explicitly approved, rejected, or deleted by underwriter
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

### Deferred Ideas (OUT OF SCOPE)
- CALIB-02: Interactive walk-through mode (guided one-by-one through all checks) -- explicitly v1.3+
- CALIB-01: Feedback-driven threshold calibration with backtest (auto-proposes threshold changes when 10+ entries agree) -- v1.3+
- Batch apply-proposal (multiple proposals in one atomic commit) -- could revisit if one-at-a-time proves too slow in practice
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FEED-01 | Underwriter feedback loop works end-to-end -- feedback CLI captures reactions, auto-generates calibration proposals, `do-uw brain apply-proposal` writes changes to brain YAML with git commit | All three sub-systems researched: (1) feedback capture via interactive CLI extending existing `cli_feedback.py` + `knowledge/feedback.py`, (2) proposal generation via new aggregation logic over `brain_feedback` table, (3) YAML write-back via ruamel.yaml + `brain build` + git commit extending `calibrate_impact.py` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruamel.yaml | >=0.18 | Round-trip YAML editing preserving comments/formatting | Only Python YAML library that preserves comments on round-trip; PyYAML strips them |
| typer | >=0.15 (already dep) | CLI framework, `typer.prompt()` and `typer.confirm()` for interactive input | Already in use; provides sufficient interactive prompts without new deps |
| rich | >=13.0 (already dep) | Terminal UI: tables, panels, syntax highlighting for YAML diffs | Already in use throughout CLI |
| pydantic | >=2.10 (already dep) | Feedback reaction models, proposal models | Already the project's data model framework |
| duckdb | >=1.4.4 (already dep) | Feedback storage, proposal tracking, signal run history | Already the brain runtime store |
| pyyaml | >=6.0 (already dep) | Read-only YAML loading (existing `brain build` path) | Already used for all YAML reads; ruamel.yaml only needed for writes |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| subprocess (stdlib) | N/A | Git operations (add, commit, diff) | Apply-proposal git audit trail |
| difflib (stdlib) | N/A | Unified diff generation for YAML preview | Show before/after YAML changes |
| json (stdlib) | N/A | Export format for offline feedback files | `feedback export/import` workflow |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ruamel.yaml | PyYAML + regex | PyYAML strips comments; regex is fragile. ruamel.yaml is the standard for this exact use case |
| typer.prompt() | questionary/InquirerPy | Adds a new dependency; typer's prompts + Rich tables are sufficient for list selection and text input |
| DuckDB for feedback storage | JSON files | DuckDB already has the schema (`brain_feedback`, `brain_proposals`); files would duplicate storage and need sync |

**Installation:**
```bash
uv add ruamel.yaml
```

## Architecture Patterns

### Recommended File Structure
```
src/do_uw/
  cli_feedback.py         # MODIFY: replace flat --note with interactive ticker flow
  knowledge/
    feedback_models.py    # MODIFY: add ReactionEntry, ReactionType, SeverityLevel models
    feedback.py           # MODIFY: add reaction recording, aggregation, proposal generation
    feedback_export.py    # NEW: export/import for offline feedback files
    calibrate.py          # MODIFY: extend apply to write YAML, not just DuckDB
    calibrate_impact.py   # MODIFY: extend git_commit to handle YAML files
    yaml_writer.py        # NEW: ruamel.yaml round-trip YAML modification
  cli_brain.py            # MODIFY: register apply-proposal subcommand
```

### Pattern 1: Ticker-Centric Feedback Capture
**What:** Load state.json for a ticker, extract triggered signal results, display them with full context, let underwriter select and react.
**When to use:** `do-uw feedback <TICKER>` command.
**Key data path:**
1. Find `output/{TICKER}-*/state.json` (most recent)
2. Load `analysis.check_results` dict
3. Filter to TRIGGERED status only (RED/YELLOW threshold_level)
4. Display table with signal_id, signal_name, value, threshold, evidence
5. User selects signal(s) from list by number
6. For each selected: show full detail panel, prompt for reaction type + rationale
7. Store reaction in `brain_feedback` with new reaction columns

```python
# State.json stores check_results under analysis:
# state["analysis"]["check_results"]["GOV.BOARD.independence"] = {
#     "check_id": "GOV.BOARD.independence",
#     "check_name": "Board Independence",
#     "status": "TRIGGERED",
#     "value": 0.45,
#     "threshold_level": "red",
#     "evidence": "Value 0.45 is below red threshold 50%",
#     "factors": ["F10"],
#     ...
# }
```

### Pattern 2: Proposal Aggregation from Feedback
**What:** Group feedback entries by signal_id, determine consensus direction, compute confidence from volume.
**When to use:** `do-uw feedback process` command.
**Algorithm:**
1. Query all PENDING feedback from `brain_feedback` grouped by `signal_id`
2. For each signal with feedback: count reactions by type (AGREE/DISAGREE/ADJUST)
3. Compute confidence: LOW (1 entry), MEDIUM (2-3), HIGH (4+)
4. For DISAGREE majority: propose threshold_change or deactivation
5. For ADJUST_SEVERITY: propose threshold shift in indicated direction
6. For AGREE majority: no proposal needed (check is working correctly) -- but still track for calibration metrics
7. Insert proposal into `brain_proposals` with computed confidence, direction, impact estimate
8. Run fire-rate impact: query `brain_signal_runs` for historical fire rate, project new rate after threshold change

### Pattern 3: YAML Write-Back with Validation
**What:** Modify the source YAML file for a signal, rebuild DuckDB, validate, git commit.
**When to use:** `do-uw brain apply-proposal <id>` command.
**Critical path:**
1. Load proposal from `brain_proposals`
2. Locate YAML file: signal_id prefix -> domain dir (e.g., GOV.BOARD.x -> `signals/gov/board.yaml`)
3. Load YAML with ruamel.yaml (preserving comments)
4. Find the signal entry by `id` field
5. Modify threshold/severity/lifecycle fields per proposal
6. Write YAML back (comments preserved)
7. Show unified diff of changes, prompt for confirmation
8. Run `brain build` programmatically to rebuild DuckDB from YAML
9. Validate: compare signal count, verify modified signal exists in active view
10. Git add the modified YAML file(s), git commit with structured message

```python
# YAML write-back with ruamel.yaml (comment-preserving)
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

with open(yaml_path) as f:
    data = yaml.load(f)

# Find and modify the signal
for signal in data:
    if signal["id"] == signal_id:
        signal["threshold"]["red"] = new_red_threshold
        break

with open(yaml_path, "w") as f:
    yaml.dump(data, f)
```

### Pattern 4: Signal ID to YAML File Mapping
**What:** Deterministic mapping from signal_id to its YAML file path.
**When to use:** YAML write-back needs to know which file to edit.
**Mapping logic:**
```
Signal ID: GOV.BOARD.independence
Prefix: GOV
Sub-prefix: BOARD
YAML file: signals/gov/board.yaml

Signal ID: FIN.LIQ.current_ratio
Prefix: FIN
Sub-prefix: LIQ
YAML file: signals/fin/balance.yaml  (need lookup, not just prefix)
```
**Important:** The YAML file mapping is NOT 1:1 with sub-prefixes. For example, `FIN.LIQ.current_ratio` is in `fin/balance.yaml`, not `fin/liq.yaml`. The correct approach is to scan all YAML files at startup, build a `signal_id -> yaml_path` index, and use that for write-back. This is a O(N) scan of ~36 files with ~400 signals -- fast enough to do on every `apply-proposal` invocation.

### Anti-Patterns to Avoid
- **Writing to DuckDB only:** The success criteria explicitly require changes to reach brain YAML. DuckDB is a cache rebuilt from YAML -- writing only to DuckDB means changes are lost on next `brain build`.
- **Editing signals.json:** The project has migrated to YAML as source of truth. The `NOTE` comment in `calibrate.py` line 280-285 explicitly warns against exporting to signals.json.
- **Using PyYAML for writes:** PyYAML strips all comments. The YAML files have header comments (e.g., `# Generated by brain_migrate_yaml.py -- DO NOT EDIT`) that must be preserved or updated.
- **Batch applying proposals:** User decision locks this to one-at-a-time with individual git commits. Each proposal is its own atomic unit.
- **Modifying existing feedback types:** The existing ACCURACY/THRESHOLD/MISSING_COVERAGE types serve different purposes (ingestion, calibration). Phase 51's AGREE/DISAGREE/ADJUST_SEVERITY are new reaction types for the feedback loop, stored alongside but distinct from the existing types.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Comment-preserving YAML editing | Regex-based YAML modification | ruamel.yaml round-trip | YAML structure is complex; regex will break on multi-line values, quoted strings, flow sequences |
| Terminal prompts with list selection | Custom stdin/readline code | typer.prompt() + Rich Table + numbered selection | Typer already handles terminal I/O; Rich renders attractive tables. Simple number input is sufficient for list selection |
| Git operations | Custom git wrapper class | subprocess.run() calls (already pattern in calibrate_impact.py) | The existing git_commit_calibration() is the established pattern; extend it, don't replace |
| Feedback storage | File-based JSON per feedback entry | brain_feedback DuckDB table (already exists) | Schema, indexes, queries all exist. Adding reaction columns is an ALTER TABLE |
| Signal ID -> YAML path mapping | Hardcoded prefix->file dict | Runtime scan of signals/**/*.yaml building signal_id index | File organization may change; runtime scan is always correct |
| Unified diff for YAML preview | Manual line-by-line comparison | difflib.unified_diff() on file content before/after | stdlib, well-tested, produces standard unified diff format |

**Key insight:** The project already has 70% of the infrastructure for this phase. The critical gaps are (1) the interactive capture UX, (2) aggregation logic, and (3) the YAML write-back. Everything else exists and should be extended, not rebuilt.

## Common Pitfalls

### Pitfall 1: YAML Comment Preservation on Write
**What goes wrong:** Using PyYAML's `yaml.dump()` strips all comments from the file, losing the header comment and any inline annotations.
**Why it happens:** PyYAML's data model doesn't represent comments.
**How to avoid:** Use ruamel.yaml exclusively for write operations. Load with `YAML().load()`, modify in-place, dump with `YAML().dump()`. Never convert to dict and back.
**Warning signs:** Comments disappearing from YAML files after apply-proposal.

### Pitfall 2: DuckDB and YAML Desync
**What goes wrong:** Applying a proposal updates YAML but fails on `brain build`, leaving YAML and DuckDB out of sync.
**Why it happens:** YAML modification might produce invalid structure, or brain build might fail for unrelated reasons.
**How to avoid:** Run `brain build` immediately after YAML write. If build fails, revert the YAML change (restore from git) before committing. The validation step must happen BEFORE the git commit.
**Warning signs:** `brain build` errors after apply-proposal; signal counts differ pre/post.

### Pitfall 3: Concurrent Feedback on Same Signal
**What goes wrong:** Multiple feedback entries for the same signal_id produce conflicting proposals (e.g., one says raise threshold, another says lower it).
**Why it happens:** Feedback can accumulate over time from different tickers/reviewers.
**How to avoid:** The aggregation algorithm must handle conflicts. When feedback entries for the same signal_id disagree on direction, the proposal should flag the conflict rather than average. Present both sides to the underwriter in the proposal detail.
**Warning signs:** Proposals with mixed directions, silent majority-rules that suppresses minority opinion.

### Pitfall 4: Signal ID Not Found in YAML
**What goes wrong:** A proposal references a signal_id that doesn't exist in any YAML file (e.g., it was created directly in DuckDB via the old feedback path).
**Why it happens:** The existing MISSING_COVERAGE feedback auto-creates INCUBATING checks in DuckDB only (see `_auto_propose_check()` in `feedback.py`). These have no YAML representation.
**How to avoid:** For NEW_CHECK proposals, the apply step must CREATE a new YAML entry (append to the appropriate domain file). For THRESHOLD_CHANGE and DEACTIVATION, the signal MUST already exist in YAML -- reject the proposal with an error message if not found.
**Warning signs:** "Signal not found in YAML" errors during apply.

### Pitfall 5: File-Based Feedback Import Validation
**What goes wrong:** Underwriter edits the exported feedback file with invalid signal_ids, malformed reactions, or missing required fields.
**Why it happens:** Humans make typos; the export format needs guardrails.
**How to avoid:** Validate every field on import. Signal IDs must exist in brain_signals_active. Reaction types must be one of the three valid values. Rationale must be non-empty. Report all validation errors before ingesting any entries.
**Warning signs:** Silently accepting invalid feedback that produces garbage proposals.

### Pitfall 6: Existing Feedback Data Migration
**What goes wrong:** The existing `brain_feedback` table has rows with the old `feedback_type` values (ACCURACY/THRESHOLD/MISSING_COVERAGE). The new reaction types (AGREE/DISAGREE/ADJUST_SEVERITY) must coexist without breaking existing queries.
**Why it happens:** The feedback table already has data and queries in `get_feedback_summary()`.
**How to avoid:** Add new columns for reaction data rather than overloading `feedback_type`. Keep the existing types for backward compatibility. The new reaction columns can be nullable, with the Phase 51 code only using entries that have reaction data populated. The existing summary command continues to work unchanged.
**Warning signs:** Old feedback CLI commands breaking; summary counts changing.

## Code Examples

### Interactive Feedback Capture (Typer + Rich)
```python
# No new dependency needed -- use typer.prompt() + Rich tables
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# Display triggered signals as a numbered table
table = Table(title=f"Triggered Signals for {ticker}")
table.add_column("#", width=4, justify="right")
table.add_column("Signal ID", min_width=25)
table.add_column("Name", min_width=20)
table.add_column("Value", width=12)
table.add_column("Level", width=8)
table.add_column("Evidence", min_width=30)

for i, (sig_id, result) in enumerate(triggered_checks.items(), 1):
    table.add_row(
        str(i), sig_id, result["check_name"],
        str(result.get("value", "N/A")),
        result.get("threshold_level", ""),
        result.get("evidence", "")[:60],
    )
console.print(table)

# Prompt for selection (comma-separated numbers)
selection = typer.prompt("Select signal(s) to react to (e.g., 1,3,5 or 'all')")

# For each selected signal, show detail panel and prompt reaction
for sig_id in selected_signals:
    console.print(Panel(
        f"[bold]{result['check_name']}[/bold]\n"
        f"Signal: {sig_id}\n"
        f"Value: {result['value']}\n"
        f"Threshold: {result['threshold_level']}: {result.get('evidence', '')}\n"
        f"Factors: {', '.join(result.get('factors', []))}",
        title="Signal Detail",
    ))
    reaction = typer.prompt(
        "Reaction [A]gree / [D]isagree / [S]everity adjustment",
    )
    rationale = typer.prompt("Rationale (required)")
```

### YAML Write-Back with ruamel.yaml
```python
from ruamel.yaml import YAML
from pathlib import Path

def modify_signal_in_yaml(
    yaml_path: Path,
    signal_id: str,
    changes: dict[str, Any],
) -> str:
    """Modify a signal's fields in its YAML file, preserving comments.

    Returns unified diff string for preview.
    """
    yaml = YAML()
    yaml.preserve_quotes = True

    # Read original for diff
    original = yaml_path.read_text()

    # Load with comment preservation
    with open(yaml_path) as f:
        data = yaml.load(f)

    # Find the signal
    signals = data if isinstance(data, list) else data.get("signals", [])
    target = None
    for signal in signals:
        if signal["id"] == signal_id:
            target = signal
            break

    if target is None:
        raise ValueError(f"Signal {signal_id} not found in {yaml_path}")

    # Apply changes
    for key, value in changes.items():
        if key == "threshold" and isinstance(value, dict):
            # Merge threshold sub-fields
            if "threshold" not in target:
                target["threshold"] = {}
            for tk, tv in value.items():
                target["threshold"][tk] = tv
        else:
            target[key] = value

    # Write back
    from io import StringIO
    buf = StringIO()
    yaml.dump(data, buf)
    modified = buf.getvalue()

    # Generate diff
    import difflib
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{yaml_path.name}",
        tofile=f"b/{yaml_path.name}",
    )
    diff_str = "".join(diff)

    # Write to file
    yaml_path.write_text(modified)

    return diff_str
```

### Signal ID to YAML Path Index
```python
def build_signal_yaml_index(
    signals_dir: Path,
) -> dict[str, Path]:
    """Build mapping from signal_id to its YAML file path.

    Scans all YAML files once, returns {signal_id: yaml_path}.
    """
    import yaml as pyyaml  # Read-only, safe_load is fine

    index: dict[str, Path] = {}
    for yaml_path in sorted(signals_dir.glob("**/*.yaml")):
        data = pyyaml.safe_load(yaml_path.read_text())
        signals = data if isinstance(data, list) else data.get("signals", [])
        for signal in signals:
            if isinstance(signal, dict) and "id" in signal:
                index[signal["id"]] = yaml_path
    return index
```

### Proposal Aggregation Algorithm
```python
def aggregate_feedback_for_signal(
    entries: list[FeedbackReaction],
) -> ProposalRecord | None:
    """Aggregate multiple feedback entries for one signal into a proposal.

    Confidence: LOW (1 entry), MEDIUM (2-3), HIGH (4+)
    Direction: majority vote of DISAGREE/ADJUST entries
    Conflict: flagged when no clear majority (40-60 split)
    """
    if not entries:
        return None

    # Count by reaction type
    agree_count = sum(1 for e in entries if e.reaction == "AGREE")
    disagree_count = sum(1 for e in entries if e.reaction == "DISAGREE")
    adjust_count = sum(1 for e in entries if e.reaction == "ADJUST_SEVERITY")

    total = len(entries)
    confidence = "LOW" if total == 1 else ("MEDIUM" if total <= 3 else "HIGH")

    # AGREE majority: no change proposal needed
    if agree_count > (disagree_count + adjust_count):
        return None  # Check is working as expected

    # DISAGREE majority: propose threshold relaxation or deactivation
    if disagree_count >= adjust_count:
        # Aggregate rationales
        rationale = "; ".join(e.rationale for e in entries if e.reaction == "DISAGREE")
        return ProposalRecord(
            source_type="FEEDBACK",
            signal_id=entries[0].signal_id,
            proposal_type="THRESHOLD_CHANGE",
            proposed_changes={"threshold_red": None},  # Computed separately
            rationale=f"Disagree consensus ({disagree_count}/{total}): {rationale}",
        )

    # ADJUST_SEVERITY: propose specific severity change
    # ... aggregate severity adjustment directions
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| DuckDB-only calibration | YAML source of truth + DuckDB cache | Phase 49 (YAML migration) | Apply must write YAML, not just DuckDB |
| `feedback add --note` CLI | Interactive ticker-centric capture | Phase 51 (this phase) | CLI redesign for feedback subcommands |
| signals.json as check registry | signals/**/*.yaml files (36 files, ~400 signals) | Phase 49 | Write-back targets YAML, not JSON |
| Manual `brain build` after changes | Automated build-validate-commit pipeline | Phase 51 (this phase) | apply-proposal is atomic: YAML edit + build + validate + commit |

**Deprecated/outdated:**
- `signals.json`: Import/export format only. Never write to it for calibration. Comment in `calibrate.py` line 280 explicitly warns.
- `feedback add --type ACCURACY/THRESHOLD`: Still works for old-style feedback, but Phase 51 adds new reaction-based capture alongside.

## Discretion Recommendations

### Feedback Storage Strategy: DuckDB (extend existing)
**Recommendation:** Use the existing `brain_feedback` table with additional columns for reaction data.
**Rationale:** Schema, indexes, and queries already exist. Adding `reaction_type`, `severity_target`, and `reaction_rationale` columns via ALTER TABLE is non-breaking. The existing feedback_type column stays for backward compat.

### Severity Adjustment Granularity: Target Level
**Recommendation:** Use target severity level (e.g., "should be MEDIUM instead of HIGH") rather than directional nudge ("reduce severity").
**Rationale:** Target levels produce unambiguous proposals. Directional nudges require interpreting "how much" which is subjective and harder to aggregate. When multiple reviewers say "should be MEDIUM", aggregation is trivial (unanimous vs. conflicting). When they say "reduce", you don't know if they mean MEDIUM or LOW.

### Regression Validation Behavior: Block and Require Force
**Recommendation:** If `brain build` fails after YAML modification, revert the YAML change automatically and report the error. Do NOT auto-rollback silently. The proposal stays PENDING and the user must investigate.
**Rationale:** Auto-rollback hides problems. The user needs to know the proposal couldn't be applied and why. A `--force` flag is not needed because the solution is to fix the proposal, not force a broken change.

### Proposal Aggregation Algorithm: Majority with Conflict Flag
**Recommendation:** Simple majority determines proposal direction. When no direction has >60% agreement, flag the proposal as CONFLICTED and require manual resolution rather than auto-generating a split-vote proposal.
**Rationale:** Split-vote proposals would confuse the underwriter. Better to surface the conflict explicitly ("3 reviewers say too sensitive, 2 say accurate -- manual review needed") than to silently pick a side.

### Interactive CLI Prompt Library: Typer + Rich (no new dep)
**Recommendation:** Use `typer.prompt()` for text input, `typer.confirm()` for yes/no, and Rich Tables with numbered rows for list selection. The user types numbers (e.g., "1,3,5" or "all") to select from the list.
**Rationale:** Questionary/InquirerPy would add a new dependency for marginal UX improvement. The project's CLI is already built on Typer+Rich. Simple numbered selection is sufficient for the use case (selecting from 5-30 triggered signals).

## Open Questions

1. **YAML Header Comment Update**
   - What we know: YAML files currently have `# Generated by brain_migrate_yaml.py -- DO NOT EDIT` as header. After apply-proposal, this comment is misleading since the file HAS been edited.
   - What's unclear: Should the header be updated to reflect calibration edits? Or removed entirely since YAML is now the editable source of truth?
   - Recommendation: Update header to `# Brain signal definitions -- source of truth for brain build` on first calibration edit. This is a one-time cosmetic change per file.

2. **Feedback for Non-Triggered Signals**
   - What we know: The user decided `feedback <TICKER>` shows triggered checks. But an underwriter might want to flag a check that should have triggered but didn't (false negative).
   - What's unclear: Should the interactive mode also allow reacting to CLEAR signals?
   - Recommendation: Add a `--all` flag to show all evaluated signals (not just triggered). Default remains triggered-only per user decision. This is a small addition to the CLI.

3. **State.json Key Name: `check_results` vs `signal_results`**
   - What we know: The state model has `signal_results` as the Pydantic field name, but the serialized JSON uses `check_results` (backward compat from the check->signal rename). WWD state.json shows `analysis.check_results` with 393 entries.
   - What's unclear: Which key should the feedback capture code use?
   - Recommendation: Use `analysis.check_results` for reading state.json (it's what actually exists in serialized files). The Pydantic alias handles this.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: `src/do_uw/cli_feedback.py`, `src/do_uw/knowledge/feedback.py`, `src/do_uw/knowledge/feedback_models.py` -- existing feedback infrastructure
- Codebase analysis: `src/do_uw/knowledge/calibrate.py`, `src/do_uw/knowledge/calibrate_impact.py` -- existing calibration/apply infrastructure
- Codebase analysis: `src/do_uw/brain/brain_build_signals.py`, `src/do_uw/brain/brain_migrate.py` -- YAML->DuckDB build path
- Codebase analysis: `src/do_uw/brain/brain_writer.py` -- versioned DuckDB writes with changelog
- Codebase analysis: `src/do_uw/brain/brain_schema.py` -- `brain_feedback` and `brain_proposals` table DDL
- Codebase analysis: `src/do_uw/brain/signals/**/*.yaml` -- 36 YAML files, ~400 signals, source of truth
- Codebase analysis: `output/WWD-2026-02-23/state.json` -- `analysis.check_results` with 393 entries, 16 TRIGGERED
- Codebase analysis: `tests/knowledge/test_feedback.py`, `tests/knowledge/test_calibrate.py` -- existing test patterns
- [ruamel.yaml PyPI](https://pypi.org/project/ruamel.yaml/) -- round-trip YAML library with comment preservation
- [questionary PyPI](https://pypi.org/project/questionary/) -- interactive CLI prompt library (evaluated, not recommended)

### Secondary (MEDIUM confidence)
- [ruamel.yaml documentation](https://yaml.dev/doc/ruamel.yaml/detail/) -- round-trip editing API details
- [InquirerPy GitHub](https://github.com/kazhala/InquirerPy) -- alternative prompt library (evaluated, not recommended)

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries verified against existing project dependencies; ruamel.yaml is the only new dependency and is the undisputed standard for comment-preserving YAML editing
- Architecture: HIGH - Extends existing modules with clear data flow; YAML write-back path verified against actual file structure
- Pitfalls: HIGH - Derived from actual codebase analysis (e.g., the signals.json warning, DuckDB-only apply, YAML comment headers)

**Research date:** 2026-02-27
**Valid until:** 2026-03-30 (stable domain, no external API dependencies)
