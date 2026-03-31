# Phase 148: Question-Driven Underwriting Section - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 148-question-driven-underwriting-section
**Areas discussed:** Answer quality bar, Supabase scenario Qs, Answerer coverage strategy, Visual presentation

---

## Answer Quality Bar

### Partial data handling

| Option | Description | Selected |
|--------|-------------|----------|
| Partial answer + flag | Answer with what's available, mark missing pieces as 'Needs Review' inline | ✓ |
| Full answer or nothing | Only show answer if ALL data_sources populated | |
| Tiered confidence | Show answer with HIGH/MEDIUM/LOW confidence badge | |

**User's choice:** Partial answer + flag
**Notes:** None

### LLM extraction for gaps

| Option | Description | Selected |
|--------|-------------|----------|
| No LLM in this phase | Stick to structured pipeline data only | |
| LLM for specific gaps | Use LLM for questions where data exists in filing text but isn't structurally extracted | ✓ |
| LLM for all NO_DATA | Any unanswered question gets LLM pass against filing text | |

**User's choice:** LLM for specific gaps
**Notes:** User confirmed all four gap types are priority: risk factors, M&A, customer concentration, regulatory/compliance

### Minimum answer rate

| Option | Description | Selected |
|--------|-------------|----------|
| Always render, show gaps | Section always appears regardless of answer rate | ✓ |
| 50% minimum | Only render if half the questions have answers | |
| 80% minimum | Only render when most questions are answered | |

**User's choice:** Always render, show gaps
**Notes:** None

### LLM gap priorities

| Option | Description | Selected |
|--------|-------------|----------|
| Risk factors (BIZ-06) | 10-K Item 1A risk factors | ✓ |
| M&A activity (BIZ-05) | Pending/recent transactions from 8-K and proxy | ✓ |
| Customer concentration | 10-K '10%+ customers' disclosure | ✓ |
| Regulatory/compliance risks (OPS-01+) | Industry-specific regulatory exposure | ✓ |

**User's choice:** All four selected
**Notes:** User said "all gaps are a priority"

---

## Supabase Scenario Questions

### Integration layout

| Option | Description | Selected |
|--------|-------------|----------|
| Inline by domain | SCA questions slot into matching domains with 'SCA Data' source badge | ✓ |
| Separate 9th domain | Dedicated 'Claims History' domain at end | |
| Conditional overlay | Highlighted callout boxes within relevant domains | |

**User's choice:** Inline by domain
**Notes:** None

### Scenario types

| Option | Description | Selected |
|--------|-------------|----------|
| Filing frequency & recidivism | Has this company been sued before? How many times? | ✓ |
| Settlement ranges & severity | What did similar companies settle for? | ✓ |
| Peer SCA comparison | How does SCA history compare to sector peers? | ✓ |
| Trigger pattern matching | Does current profile match known SCA trigger patterns? | ✓ |

**User's choice:** All four selected
**Notes:** None

---

## Answerer Coverage Strategy

### Prioritization

| Option | Description | Selected |
|--------|-------------|----------|
| By data availability | Start with questions where pipeline data exists | |
| By domain importance | Financial and Litigation first | |
| All domains in parallel | Build answerers across all 8 domains simultaneously | ✓ |

**User's choice:** All domains in parallel
**Notes:** None

### Engine architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current architecture | screening_answers generic + domain-specific fallbacks | |
| Dedicated per-question | Every question gets its own answerer function | ✓ |
| Template-driven answers | Fill answer_template variables from data lookup table | |

**User's choice:** Dedicated per-question
**Notes:** None

---

## Visual Presentation

### Verdict display

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current dots | 14px circles with +/-/=/? symbols | ✓ |
| Wider verdict badges | Word badges like 'UPGRADE' / 'DOWNGRADE' | |
| Color-coded left border | 3px left border in verdict color | |

**User's choice:** Keep current dots
**Notes:** None

### Domain roll-up

| Option | Description | Selected |
|--------|-------------|----------|
| Per-question only | No roll-up verdict | |
| Domain verdict badge | Each domain header shows net assessment | |
| Domain + overall | Both domain-level badges AND section-level overall verdict | ✓ |

**User's choice:** Domain + overall
**Notes:** Maximum signal density preferred

### Print readiness

| Option | Description | Selected |
|--------|-------------|----------|
| Looks fine for print | No changes needed | |
| Needs print optimization | Add @media print tweaks for bars, small text, dots | ✓ |
| You decide | Claude evaluates during implementation | |

**User's choice:** Needs print optimization
**Notes:** None

---

## Claude's Discretion

- LLM prompt design for filing text extraction
- Per-question answerer file organization
- Specific @media print CSS rules
- SCA question YAML schema details

## Deferred Ideas

None — discussion stayed within phase scope
