# Phase 26: Check Reorganization & Analytical Engine Enhancement - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Reorganize 359 existing checks into a multi-dimensional classification system (scored/displayed flags, plaintiff lens, signal type). Add new analytical checks for temporal change detection, financial forensics composites, executive forensics, and NLP signals — prioritized by data availability. Remove ~34 deprecated checks. The analytical engine shifts from section-based to knowledge-framework-based organization, with IES-aware check evaluation and double-counting prevention via combined contribution caps.

</domain>

<decisions>
## Implementation Decisions

### Check Classification Model
- Multi-tag approach: separate `scored` (boolean) and `displayed` (boolean) flags rather than a single category enum
- A check can be scored + displayed, scored + hidden, or display-only
- 91 orphaned checks (empty factor mappings) should be reviewed and assigned appropriate factor mappings where they carry real signal
- ~34 deprecated checks (COVID-specific, never-implementable, duplicates) should be removed entirely from checks.json — no archive, no DEPRECATED status

### Double-Counting Resolution
- Both hazard profile (structural) and checks (behavioral) can score the same domain
- Weight normalization via combined contribution cap: set a ceiling per domain for hazard + check combined. If hazard already scores 60% of the cap, the check can only add up to 40%
- Structural checks (BIZ.CLASS, BIZ.SIZE, GOV.RIGHTS) keep running and display results alongside hazard profile assessment — underwriter sees both angles
- Checks should be IES-aware: a deteriorating signal in a high-IES company is amplified vs. the same signal in a low-IES company. Checks reference IES context during evaluation, not just at final scoring.

### New Analytical Capabilities Scope
- Prioritize by data availability: only build new checks where data is already acquired or easily acquirable
- Executive forensics: build the scorer pipeline but only score dimensions where data already exists in state (insider trading, officer changes from 10-K). Defer SEC SALI/CourtListener data acquisition to later phases
- NLP signals: extend ACQUIRE to fetch prior-year 10-K alongside current filing. NLP checks compare current vs. prior year. Gracefully degrade if prior year unavailable
- Financial forensics composites (FIS, RQS, CFQS): always display as score gauges/indicators, with prominent callouts/alerts only when thresholds are breached
- Checks that need unavailable data sources get stubbed as FUTURE_RESEARCH rather than built with empty data paths

### checks.json Management
- File structure: Claude's discretion based on maintainability and existing patterns
- Migration: hybrid script + manual review. Script applies obvious classifications (BIZ.SIZE = not scored, LIT.SCA = scored + shareholders lens). Manual review for edge cases.
- Knowledge store sync: Claude's discretion on whether new fields need Alembic migration or remain JSON-only
- CheckResult model: new fields are optional with defaults for backward compatibility. Existing tests don't break.

### Claude's Discretion
- Whether to split checks.json by prefix, by category, or keep single file
- Whether new metadata fields mirror to knowledge store SQLAlchemy model
- Specific classification of each individual check (script handles obvious cases, Claude reviews edge cases)

</decisions>

<specifics>
## Specific Ideas

- IES amplification: "given high IES, this behavioral signal is more concerning" — checks should reference IES context
- Combined contribution caps per domain prevent score inflation when both hazard and check score same area
- "Display score + highlight issues" pattern for forensic composites — always visible as gauge, alerts only on threshold breach
- Prior-year 10-K acquisition enables year-over-year NLP comparison (tone shift, risk factor evolution, readability changes)

</specifics>

<deferred>
## Deferred Ideas

- SEC SALI and CourtListener data acquisition for executive forensics — future phase when data sources are integrated into ACQUIRE
- Earnings call transcript analysis — blocked by transcript acquisition (no free/cheap source)
- Glassdoor sentiment analysis — deferred to Phase 30+ per framework guidance
- Full DERIV.*, REG.*, EMERGING.* check categories if blocked by data availability — build what data supports, defer the rest

</deferred>

---

*Phase: 26-check-reorganization-analytical-engine*
*Context gathered: 2026-02-12*
