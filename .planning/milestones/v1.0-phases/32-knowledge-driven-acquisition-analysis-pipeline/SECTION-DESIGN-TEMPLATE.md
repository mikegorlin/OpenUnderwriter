# Section Design Template

This template defines the process for redesigning each of the 7 brain sections. The COMPANY section is the pilot; all other sections follow the same pattern.

## Process Per Section

### Step 1: Define the Questions
What questions does an underwriter need answered by this section? Each question must have:
- **The question itself** (plain English)
- **Why we ask it** (D&O underwriting rationale)
- **What a good answer looks like** (what the underwriter should see)

Target: 8-12 questions per section.

### Step 2: Map Data Points to Each Question
For each question, identify:
- **Data points needed** (specific fields/values)
- **Data sources** (where they come from, with fallback chain)
- **Current status** (have it / partial / missing)

### Step 3: Define Actions Per Question
For each question, specify the three layers:
- **ACQUIRE:** What data do we pull in? From where? What's the fallback?
- **ANALYZE:** What evaluation runs? What thresholds? What's RED/YELLOW/CLEAR?
- **DISPLAY:** What does the underwriter see? Format, context, risk flags?

### Step 4: Map Current Checks
- Which existing checks answer each question?
- Which checks are orphans (don't answer any question)?
- Which questions have no checks (gaps)?

### Step 5: Consolidation & Gap Closure
- Merge redundant checks
- Retire orphan checks that don't serve any question
- Define new checks/extractions for gaps
- Prioritize: what must work for a useful worksheet vs nice-to-have

### Step 6: Implementation Plan
- What extraction logic needs to be built/fixed?
- What evaluation logic needs to be built/fixed?
- What rendering changes are needed?
- Estimated effort and dependencies

## Section Status Tracker

| Section | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 | Step 6 |
|---|---|---|---|---|---|---|
| COMPANY | DONE (7 areas, 31 Q) | DONE | DONE | PENDING | — | — |
| FINANCIAL | DONE (8 areas, 36 Q) | PENDING | — | — | — | — |
| GOVERNANCE | DONE (6 areas, 33 Q) | PENDING | — | — | — | — |
| LITIGATION | DONE (8 areas, 31 Q) | PENDING | — | — | — | — |
| MARKET | DONE (7 areas, 27 Q) | PENDING | — | — | — | — |
| DISCLOSURE | DONE (5 areas, 19 Q) | PENDING | — | — | — | — |
| FORWARD | DONE (5 areas, 25 Q) | PENDING | — | — | — | — |

**Design Documents:**
- `ALL-SECTIONS-QUESTIONS.md` — Step 1 for all 7 sections (46 areas, 202 questions)
- `COMPANY-SECTION-DESIGN.md` — Steps 1-3 complete (pilot section, full ACQUIRE/ANALYZE/DISPLAY)
- `SECTION-DESIGN-TEMPLATE.md` — This file: 6-step process per section
- `TAXONOMY-RECLASSIFICATION.md` — Reference: mechanical mapping of all 388 checks
