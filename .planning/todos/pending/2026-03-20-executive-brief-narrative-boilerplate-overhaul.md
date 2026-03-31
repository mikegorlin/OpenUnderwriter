---
created: 2026-03-20T23:36:31.556Z
title: Executive Brief narrative boilerplate overhaul
area: render
files:
  - src/do_uw/stages/render/sections/sect1_findings_neg.py:350-371
  - src/do_uw/stages/render/sections/sect1_findings.py:87-92
  - src/do_uw/stages/render/context_builders/_market_display.py
  - src/do_uw/stages/render/sections/sect1_executive_tables.py
  - src/do_uw/templates/html/sections/governance/deep_context.html.j2
---

## Problem

14+ boilerplate/template patterns across the worksheet produce generic text that could apply to any company by swapping the name. Violates the NON-NEGOTIABLE rule: "Every sentence must contain company-specific data."

**Critical patterns found:**
1. `neg_generic()` in `sect1_findings_neg.py:350-371` — catch-all producing "faces risk from X. At its scale ($YB market cap, Z employees), even moderate risk factors can generate material D&O exposure." Used for Critical Red Flag findings.
2. "historically correlated with increased D&O claim frequency" — repeated 5+ times verbatim across Quick Screen, Executive Brief
3. "Audit-related issues are among the strongest predictors" — generic D&O primer, no company-specific connection
4. "Leadership stability reduces the 'rats leaving a sinking ship' narrative" — identical for 15yr CEO (AAPL) and 2yr CEO in distressed company (ANGI)
5. D&O Implications callouts use same text for opposite financial profiles (Altman 9.93 vs 0.98)
6. Governance narratives truncated for complex companies (ANGI text cuts off)
7. ANGI's 73.7% decline described as "elevated volatility" instead of catastrophic collapse
8. Short interest 17.95% not elevated to key finding for ANGI
9. Same WALK recommendation for opposite risk profiles without explaining differentiation

**Scope:** Executive Brief findings, Governance narrative, Financial Health D&O implications, Quick Screen explanations, Meeting Prep questions, D&O Risk columns in tables.

**Blocking:** Phase 120 visual review approval — cannot approve v8.0 milestone with this quality level.

## Solution

1. Replace `neg_generic()` with finding-specific generators that connect the trigger to the company's actual risk profile (DDL mechanics, specific litigation theories, sector-specific exposure)
2. Remove all "historically correlated" boilerplate — replace with company-specific claim frequency data or delete
3. Make governance narrative scale properly (don't truncate for complex companies)
4. D&O Implications must differ based on actual financial position (distressed vs healthy)
5. Key findings must use company-specific language — if ANGI has 73.7% decline, say "catastrophic 73.7% decline" not "elevated volatility"
6. Quick Screen explanations must reference specific 10-K disclosures, not generic risk categories

Likely needs a dedicated phase or multi-plan effort — too many files and patterns for a quick fix.
