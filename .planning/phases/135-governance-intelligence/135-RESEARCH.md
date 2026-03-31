# Phase 135: Governance Intelligence - Research

**Researched:** 2026-03-27
**Domain:** Governance extraction, officer background investigation, shareholder rights, insider trading display
**Confidence:** HIGH

## Summary

Phase 135 adds investigative depth to the governance section: per-officer background investigation with serial defendant detection via Supabase SCA cross-referencing, structured shareholder rights inventory with anti-takeover assessment, and per-insider trading activity detail with 10b5-1 plan classification. All five requirements build on substantial existing infrastructure -- 11 extraction modules, 3 context builders, 14 governance templates, and rich Pydantic models.

The primary technical challenge is the officer prior-company extraction from DEF 14A biographical text (requires LLM structured output) followed by batch Supabase cross-referencing. The shareholder rights inventory is largely a display reorganization -- most data fields already exist in `BoardProfile` and `DEF14AExtraction`. The per-insider activity detail requires aggregation from existing `InsiderTransaction` records that already have 10b5-1 classification.

**Primary recommendation:** Follow Phase 134 pattern exactly -- new Pydantic models in a focused file, extraction module, context builder helper, template fragments, beta_report wiring. Keep governance.py context builder under 500 lines by routing new context building through a dedicated `_governance_intelligence.py` helper.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Per-officer display: prior companies (from bio text), SCA/SEC history at prior companies (Supabase + EDGAR), personal litigation (web search), suitability assessment (HIGH/MEDIUM/LOW data completeness indicator)
- D-02: Officer prior company extraction uses LLM extraction from DEF 14A bio text -- structured output: list of {company_name, role, years}
- D-03: Suitability assessment is data completeness indicator, not judgment on the person
- D-04: Cross-reference officer prior companies against Supabase SCA database; flag "serial defendant" when officer was at Company X during class period of an SCA against Company X
- D-05: Batch Supabase query (same pattern as Phase 134 `query_peer_sca_filings`)
- D-06: Display: officer name with red "Serial Defendant" badge, linked case references, one-liner D&O implication
- D-07: Extract shareholder rights from DEF 14A and governance data already in state; cover 8 provisions (board classification, poison pill, supermajority, proxy access, cumulative voting, written consent, special meeting, forum selection)
- D-08: Display as checklist table: Provision | Status | Details | Defense Strength | D&O Implication; green/red/gray color coding
- D-09: Anti-takeover defense strength assessment: aggregate 8 provisions into Strong/Moderate/Weak
- D-10: Reuse existing insider trading extraction (`insider_trading.py`, `insider_trading_analysis.py`) with 10b5-1 detection
- D-11: Per-insider table: Name | Position | Total Sales ($) | Total Sales (%O/S) | Tx Count | 10b5-1 Plan Status | Activity Period; sort by total sales descending
- D-12: 10b5-1 plan status from existing `_detect_10b5_1()` -- render as badge: "10b5-1" (green) or "Discretionary" (amber)

### Claude's Discretion
- Template layout within existing beta_report governance section
- LLM prompt design for officer bio extraction
- How to handle officers with no prior company data (show "No prior public company history found" vs omit)
- Sorting/grouping of rights inventory provisions

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GOV-01 | Per-officer background: prior companies, SCA/SEC history, personal litigation, suitability | LLM extraction from bio text + Supabase cross-ref + existing `search_prior_litigation()` |
| GOV-02 | Serial defendant detection: flag execs present at companies during prior SCAs | Supabase `sca_filings` has `class_period_start`/`class_period_end` + `company_name` for date-range overlap matching |
| GOV-03 | Shareholder rights inventory: 8 provisions | 6 of 8 fields exist in `BoardProfile`; cumulative voting missing entirely, needs new DEF14A field |
| GOV-04 | Anti-takeover defense strength assessment | Existing `_build_anti_takeover()` covers 5 of 8 provisions; extend with 3 more + aggregate score |
| GOV-05 | Per-insider activity detail with 10b5-1 classification | `InsiderTransaction` model has all needed fields; aggregate by `insider_name` from existing `transactions` list |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Python 3.12+, uv, Pyright strict** -- all new code must be fully typed
- **Pydantic v2** -- all data models use Pydantic v2
- **httpx** for HTTP (Supabase queries already use it)
- **No file over 500 lines** -- governance.py context builder is already at 513 lines; new code MUST go in a separate helper file
- **safe_float()** for all numeric values from state -- never bare `float()`
- **No bare `float()` in render code** -- use `safe_float()` from formatters
- **No truncation of analytical content** in templates
- **Self-verification before showing output** -- re-render and run QA checks
- **Data integrity** -- every data point needs source + confidence; never hallucinate financial data
- **Governance MUST ALWAYS show** -- prior lawsuits, character issues, qualifications (this phase delivers all three)
- **Brain portability** -- renderers are dumb consumers, zero business logic in templates
- **No hardcoded thresholds** -- put in config/
- **ADDITIVE only** -- never remove existing analytical capabilities

## Standard Stack

### Core
No new dependencies required. All features build on existing infrastructure.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.x (existing) | Data models for officer background, shareholder rights | Already the project standard |
| httpx | existing | Supabase batch queries for officer SCA history | Already used by supabase_litigation.py |
| jinja2 | existing | Template fragments for new governance sub-sections | Already the rendering engine |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| defusedxml | existing | Form 4 XML parsing (insider trading, already in use) | Already used |

### Alternatives Considered
None -- zero new dependencies needed per locked decision.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  models/
    governance_intelligence.py     # NEW: OfficerBackground, SerialDefendant, ShareholderRightsInventory, PerInsiderActivity models
  stages/
    extract/
      officer_background.py        # NEW: LLM bio extraction + Supabase cross-ref + serial defendant detection
    render/
      context_builders/
        _governance_intelligence.py # NEW: Context builder for GOV-01 through GOV-05
  templates/html/sections/governance/
    officer_backgrounds.html.j2    # NEW: Per-officer investigation cards
    shareholder_rights.html.j2     # NEW: 8-provision checklist table
    per_insider_activity.html.j2   # NEW: Per-insider detail table
```

### Pattern 1: Phase 134 Pattern (Canonical)
**What:** Models -> extraction module -> context builder helper -> template fragments -> beta_report wiring
**When to use:** Every new feature in this phase
**Example flow:**
1. Define Pydantic models in `models/governance_intelligence.py`
2. Extraction logic in `stages/extract/officer_background.py`
3. Context builder in `stages/render/context_builders/_governance_intelligence.py`
4. Template fragments in `templates/html/sections/governance/`
5. Wire into `beta_report.html.j2` governance section via `{% include %}`
6. Wire context builder into `extract_governance()` in `governance.py`

### Pattern 2: Supabase Batch Query (from Phase 134)
**What:** Collect all company names from officer bios, query Supabase in one batch, match results to officers
**When to use:** GOV-01/GOV-02 serial defendant detection
**Example:**
```python
# Collect all prior company names from all officers
prior_companies: list[str] = []
for officer in officers:
    for pc in officer.prior_companies:
        prior_companies.append(pc.company_name)

# Single batch query via Supabase company_name ilike
# Then match class_period_start/end against officer tenure dates
```

### Pattern 3: Per-Insider Aggregation (GOV-05)
**What:** Group existing `InsiderTransaction` list by `insider_name`, compute per-person totals
**When to use:** GOV-05 per-insider activity detail
**Example:**
```python
from collections import defaultdict
by_insider: dict[str, list[InsiderTransaction]] = defaultdict(list)
for tx in transactions:
    if tx.insider_name and tx.transaction_type == "SELL":
        by_insider[tx.insider_name.value].append(tx)
```

### Anti-Patterns to Avoid
- **Adding context builder logic to governance.py directly** -- it's already at 513 lines. Use a new `_governance_intelligence.py` helper
- **Making separate Supabase calls per officer** -- use batch query pattern from Phase 134
- **LLM extraction without structured output schema** -- define a Pydantic schema for officer bio extraction to ensure consistent parsing
- **Hardcoding provision definitions in templates** -- define in context builder, template just renders

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SCA database lookup | Custom scraper | Existing `supabase_litigation.py` batch query | Already handles auth, filtering, error recovery |
| Form 4 10b5-1 detection | Custom parser | Existing `_detect_10b5_1()` in `insider_trading.py` | Handles all 3 detection methods (XML flag, transaction-level, footnote text) |
| Prior litigation search | Custom name matcher | Existing `search_prior_litigation()` in `leadership_parsing.py` | Searches litigation_data, web_search, blind_spot results |
| Officer bio extraction | Regex parsing | LLM structured output with Pydantic schema | DEF 14A bio formats are too varied for regex (locked decision D-02) |
| Board forensic profile display | New from scratch | Extend existing `board_forensics.html.j2` pattern | Template structure and CSS already established |

**Key insight:** 80% of the data pipeline already exists. The gaps are (1) LLM extraction of prior company names from bios, (2) cross-referencing those names against Supabase, and (3) display aggregation for per-insider activity.

## Common Pitfalls

### Pitfall 1: Governance Context Builder File Size
**What goes wrong:** Adding new context building logic to `governance.py` (already 513 lines) pushes it over 500-line limit
**Why it happens:** Natural tendency to extend existing file
**How to avoid:** Create `_governance_intelligence.py` helper, import into `governance.py` with a single function call
**Warning signs:** governance.py exceeding 500 lines after changes

### Pitfall 2: Supabase Company Name Matching Ambiguity
**What goes wrong:** Officer bio says "Acme Corp" but Supabase has "Acme Corporation" or "ACME, Inc." -- no match found
**Why it happens:** Company names vary across sources; no standardized identifier for private companies
**How to avoid:** Use `ilike` fuzzy matching (already done in `query_sca_filings`), extract core name before matching, tolerate false negatives
**Warning signs:** Serial defendant count is zero for obviously problematic officers

### Pitfall 3: LLM Bio Extraction Hallucination
**What goes wrong:** LLM invents prior companies or misattributes roles from bio text
**Why it happens:** Bios are dense text; LLM may confuse "served on the board of Company X" with "was CEO of Company X"
**How to avoid:** Use structured Pydantic output schema with clear field descriptions; cross-validate against the source_passage; mark as MEDIUM confidence
**Warning signs:** Officers showing implausible number of prior companies (>10), companies that don't exist

### Pitfall 4: Date Overlap Logic for Serial Defendant
**What goes wrong:** Incorrect date comparison flags officer as serial defendant when their tenure didn't actually overlap with the class period
**Why it happens:** Bio text gives approximate years ("2015-2020") while SCA has specific dates ("2018-03-15 to 2019-11-30"); need fuzzy date matching
**How to avoid:** Convert bio years to date ranges (start of first year to end of last year); check for ANY overlap with SCA class period, not exact containment
**Warning signs:** False positives (officer left company years before the SCA) or false negatives (officer was there during class period but dates parsed wrong)

### Pitfall 5: Cumulative Voting Field Missing
**What goes wrong:** GOV-03 requires 8 provisions including cumulative voting, but no `cumulative_voting` field exists in `BoardProfile` or `DEF14AExtraction`
**Why it happens:** Was never part of the original extraction schema
**How to avoid:** Add `cumulative_voting` field to `BoardProfile` model and `DEF14AExtraction` schema; existing LLM extraction will populate it on next --fresh run
**Warning signs:** Cumulative voting always shows "N/A" in shareholder rights inventory

### Pitfall 6: shares_outstanding Not Available for %O/S Calculation
**What goes wrong:** GOV-05 requires Total Sales (%O/S) but shares outstanding may not be in accessible state location
**Why it happens:** shares_outstanding lives in XBRL financials, not directly on insider trading models
**How to avoid:** Pull from `state.extracted.financials.statements` or `state.company.shares_outstanding` with fallback to None; display "N/A" if unavailable
**Warning signs:** All %O/S values show N/A

## Code Examples

### Officer Background Model (governance_intelligence.py)
```python
from pydantic import BaseModel, Field
from do_uw.models.common import SourcedValue

class PriorCompany(BaseModel):
    """A prior company extracted from officer bio text."""
    company_name: str = ""
    role: str = ""
    years: str = ""  # e.g., "2015-2020"
    start_year: int | None = None
    end_year: int | None = None

class OfficerSCAExposure(BaseModel):
    """An SCA case at a prior company during officer's tenure."""
    company_name: str = ""
    case_caption: str = ""
    filing_date: str = ""
    class_period_start: str = ""
    class_period_end: str = ""
    officer_role_at_time: str = ""
    settlement_amount_m: float | None = None

class OfficerBackground(BaseModel):
    """Per-officer investigative background for GOV-01."""
    name: str = ""
    title: str = ""
    prior_companies: list[PriorCompany] = Field(default_factory=list)
    sca_exposures: list[OfficerSCAExposure] = Field(default_factory=list)
    is_serial_defendant: bool = False
    personal_litigation: list[str] = Field(default_factory=list)
    suitability: str = "LOW"  # HIGH/MEDIUM/LOW data completeness
    suitability_reason: str = ""
```

### Supabase Batch Query for Officer Prior Companies
```python
def query_officer_prior_sca(
    company_names: list[str],
) -> list[dict[str, Any]]:
    """Batch query Supabase for SCA filings at officer prior companies.

    Uses company_name ilike matching (same pattern as query_sca_filings).
    Returns raw case dicts with class_period_start/end for date overlap check.
    """
    # Build OR filter for multiple company names
    # Supabase supports: company_name=ilike.*CompanyA*
    # For batch: use or=(company_name.ilike.*CompanyA*,company_name.ilike.*CompanyB*)
```

### Per-Insider Aggregation Pattern
```python
def aggregate_per_insider(
    transactions: list[InsiderTransaction],
    shares_outstanding: float | None = None,
) -> list[dict[str, Any]]:
    """Aggregate transactions by insider for GOV-05 display."""
    by_insider: dict[str, list[InsiderTransaction]] = defaultdict(list)
    for tx in transactions:
        if tx.insider_name and tx.transaction_code not in COMPENSATION_CODES:
            by_insider[tx.insider_name.value].append(tx)

    result = []
    for name, txs in by_insider.items():
        sells = [t for t in txs if t.transaction_type == "SELL"]
        total_sold = sum(safe_float(t.total_value.value) for t in sells if t.total_value)
        has_10b5_1 = any(t.is_10b5_1 and t.is_10b5_1.value for t in sells)
        # ... build per-insider dict
    return sorted(result, key=lambda x: x["total_sold"], reverse=True)
```

### Shareholder Rights Inventory (8 Provisions)
```python
# 8 provisions mapped to existing BoardProfile fields:
RIGHTS_PROVISIONS = [
    # (field_name, display_label, exists_in_model, is_protective, d&o_implication_yes, d&o_implication_no)
    ("classified_board", "Board Classification", True, True,
     "Staggered terms limit hostile takeover but increase Revlon duty scrutiny",
     "Annual elections -- shareholders can replace full board"),
    ("poison_pill", "Poison Pill / Rights Plan", True, True,
     "Deters hostile bids but may entrench management",
     "No poison pill -- vulnerable to hostile acquisition"),
    ("supermajority_voting", "Supermajority Requirements", True, True,
     "Higher bar for charter/bylaw changes limits shareholder power",
     "Simple majority -- shareholders can effect changes more easily"),
    ("proxy_access_threshold", "Proxy Access", True, False,
     "Shareholders can nominate directors -- increases board accountability",
     "No proxy access -- board controls nomination process"),
    ("cumulative_voting", "Cumulative Voting", False, False,  # NEEDS NEW FIELD
     "Minority shareholders can concentrate votes -- increases board diversity risk",
     "No cumulative voting -- standard plurality/majority"),
    ("written_consent_allowed", "Written Consent", True, False,
     "Shareholders can act without meeting -- increases activist power",
     "No written consent -- actions require formal meeting"),
    ("special_meeting_threshold", "Special Meeting Rights", True, False,
     "Shareholders can call special meetings -- increases responsiveness",
     "No/high threshold -- limits shareholder ability to force votes"),
    ("forum_selection_clause", "Forum Selection", True, True,
     "Channels litigation to chosen forum -- predictable defense environment",
     "No forum selection -- litigation risk across multiple jurisdictions"),
]
```

## Existing Infrastructure Inventory

### Data Already Available (no extraction needed)
| Data | Location | Populated? | Notes |
|------|----------|------------|-------|
| Board forensic profiles | `state.extracted.governance.board_forensics` | Yes | Name, tenure, committees, other_boards, qualifications |
| Leadership forensic profiles | `state.extracted.governance.leadership.executives` | Yes | Name, title, bio_summary, prior_litigation, shade_factors |
| Insider transactions | `state.extracted.market.insider_trading.transactions` | Yes | Full Form 4 parse with 10b5-1 detection |
| Anti-takeover (5 of 8) | `state.extracted.governance.board` | Yes | classified_board, poison_pill, supermajority, dual_class, blank_check |
| Governance provisions (3 of 8) | `state.extracted.governance.board` | Yes | proxy_access_threshold, special_meeting_threshold, written_consent_allowed |
| Forum selection | `state.extracted.governance.board.forum_selection_clause` | Yes | String value with clause text |

### Data Gaps (extraction needed)
| Data | Required For | Approach |
|------|-------------|----------|
| Officer prior companies with roles+dates | GOV-01, GOV-02 | LLM extraction from DEF 14A bio text |
| SCA history at prior companies | GOV-01, GOV-02 | Supabase batch query by company_name |
| Cumulative voting | GOV-03 | New field in BoardProfile + DEF14AExtraction |
| Per-insider aggregation | GOV-05 | Compute from existing InsiderTransaction list |

### Existing Functions to Reuse
| Function | File | Purpose |
|----------|------|---------|
| `query_peer_sca_filings()` | `supabase_litigation.py` | Batch Supabase query pattern |
| `query_sca_filings()` | `supabase_litigation.py` | Company-name ilike matching |
| `search_prior_litigation()` | `leadership_parsing.py` | Name-based litigation search |
| `_detect_10b5_1()` | `insider_trading.py` | 10b5-1 plan detection |
| `compute_aggregates()` | `insider_trading.py` | Insider trading aggregation |
| `_build_anti_takeover()` | `_governance_helpers.py` | Anti-takeover provision display |
| `_build_executive_detail()` | `_governance_helpers.py` | Executive profile display |
| `extract_board_from_proxy()` | `board_parsing.py` | DEF 14A board extraction |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Aggregate insider selling only | Per-insider detail | This phase | Underwriter sees WHO is selling, not just totals |
| Name-based litigation search only | Supabase SCA cross-reference | This phase | Date-precise serial defendant detection |
| Anti-takeover as 5 provisions | Full 8-provision shareholder rights inventory | This phase | Complete governance defense picture |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/ -x -q --tb=short -k "governance_intel"` |
| Full suite command | `uv run pytest tests/ -x -q --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GOV-01 | Officer background extraction from bio text | unit | `uv run pytest tests/extract/test_officer_background.py -x` | No -- Wave 0 |
| GOV-01 | Suitability assessment logic (HIGH/MEDIUM/LOW) | unit | `uv run pytest tests/extract/test_officer_background.py::test_suitability -x` | No -- Wave 0 |
| GOV-02 | Serial defendant detection via Supabase cross-ref | unit | `uv run pytest tests/extract/test_officer_background.py::test_serial_defendant -x` | No -- Wave 0 |
| GOV-02 | Date overlap logic (officer tenure vs class period) | unit | `uv run pytest tests/extract/test_officer_background.py::test_date_overlap -x` | No -- Wave 0 |
| GOV-03 | Shareholder rights inventory (8 provisions) | unit | `uv run pytest tests/render/test_governance_intelligence_ctx.py::test_shareholder_rights -x` | No -- Wave 0 |
| GOV-04 | Anti-takeover defense strength (Strong/Moderate/Weak) | unit | `uv run pytest tests/render/test_governance_intelligence_ctx.py::test_defense_strength -x` | No -- Wave 0 |
| GOV-05 | Per-insider aggregation from transactions | unit | `uv run pytest tests/render/test_governance_intelligence_ctx.py::test_per_insider -x` | No -- Wave 0 |
| GOV-05 | 10b5-1 badge logic | unit | `uv run pytest tests/render/test_governance_intelligence_ctx.py::test_10b5_1_badge -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/extract/test_officer_background.py tests/render/test_governance_intelligence_ctx.py -x -q`
- **Per wave merge:** `uv run pytest tests/ -x -q --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/extract/test_officer_background.py` -- covers GOV-01, GOV-02
- [ ] `tests/render/test_governance_intelligence_ctx.py` -- covers GOV-03, GOV-04, GOV-05
- [ ] `tests/models/test_governance_intelligence.py` -- model validation

## Open Questions

1. **Supabase batch query by company_name (OR filter)**
   - What we know: `query_sca_filings` uses single `company_name=ilike.*X*`, `query_peer_sca_filings` uses `ticker=in.(A,B,C)` batch
   - What's unclear: Supabase REST API supports `or=(company_name.ilike.*A*,company_name.ilike.*B*)` but URL length limits may apply for many companies
   - Recommendation: Use `or=()` filter for batches <= 20 companies; split into multiple requests if more

2. **Officer tenure date precision from bio text**
   - What we know: Bios say things like "served as CFO from 2015 to 2019" or "joined the company in 2018"
   - What's unclear: LLM extraction will give approximate years, not exact dates; SCA class periods are exact
   - Recommendation: Convert years to full-year ranges (2015 = 2015-01-01 to 2015-12-31); accept some false positives over missed serial defendants

3. **Shares outstanding for %O/S calculation**
   - What we know: Available in XBRL (`shares_outstanding`) and potentially `state.company.shares_outstanding`
   - What's unclear: Which state path is most reliable
   - Recommendation: Try `state.extracted.financials.statements` XBRL first, fall back to `state.company.shares_outstanding`, then None

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `models/governance_forensics.py`, `models/governance.py` -- existing model structure
- Codebase inspection: `stages/extract/insider_trading.py` -- full Form 4 parsing + 10b5-1 detection
- Codebase inspection: `stages/acquire/clients/supabase_litigation.py` -- batch query patterns
- Codebase inspection: `stages/render/context_builders/governance.py` -- 513 lines, at file size limit
- Codebase inspection: `stages/extract/llm/schemas/def14a.py` -- DEF 14A extraction schema
- Codebase inspection: `stages/extract/llm/schemas/common.py` -- ExtractedDirector model

### Secondary (MEDIUM confidence)
- Codebase inspection: `stages/extract/board_governance.py` -- board extraction + director litigation search pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, all existing infrastructure
- Architecture: HIGH -- follows established Phase 134 pattern exactly
- Pitfalls: HIGH -- identified from actual codebase constraints (file size limits, missing fields, date matching complexity)

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable -- no external dependency changes expected)
