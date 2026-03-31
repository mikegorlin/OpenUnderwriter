# D&O FRAMEWORK AUDIT & IMPROVEMENT REPORT
## Based on Review of 35+ Conversations (Dec 2025 – Feb 2026)
## February 8, 2026

---

## EXECUTIVE SUMMARY

After reviewing all project conversations, I've identified **14 recurring issues** across three categories: execution failures, framework gaps, and project file hygiene. The single biggest operational problem is **context window exhaustion** — analyses frequently hit the max limit mid-generation. Below is the full diagnostic with specific fixes mapped to project instruction changes.

---

## ISSUE CATEGORY 1: EXECUTION FAILURES (What Breaks During Analyses)

### 🔴 ISSUE 1: Context Window Exhaustion (CRITICAL — #1 Problem)

**Frequency**: 6+ conversations required continuation or died mid-output
- Discord: 3 separate chats to complete
- Eikon: 3 separate chats to complete  
- MSA: 2 chats (state file wasn't saved, had to redo)
- Kaiser: TBD placeholders because ran out of room

**Root Causes**:
| Token Consumer | Est. Cost | Notes |
|---------------|-----------|-------|
| Docx script generation | ~15,000 tokens | 300+ lines of inline JavaScript |
| NEG-001 sweep (8 searches) | ~8,000 tokens | Each search returns ~1K |
| Full industry module load | ~5,000 per file | Some modules are 40-50K |
| SEC filing fetch attempts | ~10,000+ tokens | Full 10-K/S-1 text dumps |
| Repeating data in output | ~3,000 tokens | Data shown in chat AND document |

**Proposed Fix for Project Instructions**:
1. Add **OUT-001**: Default output is markdown (not docx). Word doc on explicit request only. This was discussed in the Jan 16 session and a v1.3 markdown template was drafted but NEVER uploaded to project files.
2. Add **OUT-002**: State file save mandatory after Phase 4 (QS complete). Currently the instructions say "save state if conversation is lengthy" — too vague. Should be: "After Quick Screen completion, save state to `/mnt/user-data/outputs/[TICKER]_state.md`"
3. Add **OUT-003**: Targeted module loads. Instead of `view /mnt/project/biotech_module.md` (loads 34K), use `view [file] [1, 100]` to load just the exec summary and scoring tables.
4. Add **EX-011**: After each web search, extract key facts and discard raw text rather than keeping full search results in context.

---

### 🔴 ISSUE 2: SEC EDGAR Timeout / Stanford SCAC Failures

**Frequency**: Eikon S-1 failed 3x; Stanford SCAC unreliable across multiple analyses

**Proposed Fix**:
Add to Core Rules:
- **FETCH-001**: If SEC EDGAR direct fetch fails twice, fall back to web search for filing summary data (e.g., "Company S-1 IPO filing use of proceeds pipeline"). Do NOT retry the same failing URL.
- **FETCH-002**: If Stanford SCAC search fails, use "[Company] securities class action lawsuit" broad web search as alternative. Stanford is undergoing restructuring.

---

### 🟡 ISSUE 3: State File Not Saved (MSA Case)

**What happened**: MSA analysis completed in chat 1, but state was never saved. Chat 2 had to start from scratch.

**Fix**: Make state saves proactive, not reactive. See OUT-002 above.

---

### 🟡 ISSUE 4: TBD Placeholders in Output (Kaiser Case)

**What happened**: Kaiser analysis delivered with multiple TBD fields. Mike was frustrated: "why are they there????"

**Fix**: Already addressed in Core Rule 9 ("mark as 🟣 UNKNOWN"), but needs reinforcement:
- Add **OUT-004**: NO TBD placeholders in final output. If data unavailable after research, mark 🟣 UNKNOWN with search documentation. Never punt — fill gaps with actual research or explicitly state what was searched and not found.

---

## ISSUE CATEGORY 2: FRAMEWORK GAPS (What the Framework Misses)

### 🔴 ISSUE 5: Historical vs. Prospective Imbalance

**Source**: Primoris analysis — Lockton underwriter exposed that framework was 85% backward-looking

**Gaps identified**:
- Major growth catalysts not captured
- Policy/regulatory tailwind-headwind exposure
- Large project concentration (>15% revenue)
- Competitive landscape
- Capital allocation strategy

**Status**: QS-044 through QS-048 were drafted in Jan 16 session as patches but NEVER integrated into 01_QUICK_SCREEN_V4_7.md in project files.

**Fix**: These 5 checks need to be added to the Quick Screen. They exist as a patch file but were never uploaded.

---

### 🔴 ISSUE 6: F.5 Guidance vs. Analyst Consensus Confusion

**Source**: Primoris analysis — I conflated analyst consensus estimates with company-issued guidance

**The distinction**: "Did management guide investors accurately?" (F.5) vs. "Did analysts estimate accurately?" (different question entirely)

**Status**: F.5-000 prerequisite step was drafted but NEVER integrated into 10_SCORING.md.

**Fix**: Add prerequisite to F.5 scoring:
```
F.5-000: First establish — does the company provide quarterly guidance?
- If yes → Track company guidance vs. actual
- If no (annual only) → Track annual guidance evolution
- Separately: analyst consensus beat/miss is supplemental, NOT F.5 scored
```

---

### 🟡 ISSUE 7: Check Count Inflation in File Headers

**Source**: Jan 8 audit discovered file headers claim more checks than actually exist

| File | Header Claims | Actual Count | Delta |
|------|--------------|--------------|-------|
| 03_LITIGATION_REGULATORY | 37 | ~31 | -6 |
| 04_FINANCIAL_HEALTH | 112 | ~104 | -8 |
| 05_BUSINESS_MODEL | 74 | ~64 | -10 |

**Fix**: Correct headers in project files. The Project Instructions v4.7 also propagates these inflated numbers.

---

### 🟡 ISSUE 8: F.2 / STK Module Integration Incomplete

**Status**: `10_SCORING_F2_UPDATE.md` exists as a separate patch file but was never merged into `10_SCORING.md`. This means F.2 scoring still references the old methodology unless the analyst manually loads the patch.

**Fix**: Merge F.2 update into main scoring file and delete the standalone patch.

---

## ISSUE CATEGORY 3: PROJECT FILE HYGIENE

### 🟡 ISSUE 9: Orphaned / Superseded Files Still in Project

| File | Status | Action |
|------|--------|--------|
| `10_SCORING_F2_UPDATE.md` | Patch — never merged | Merge into 10_SCORING, then delete |
| `11_OUTPUT_TEMPLATE_V1_1.md` | Superseded by v1.2 | Delete (keep v1.2) |
| `RULE_RENUMBERING_MAP.md` | Legacy v4.6→v4.7 map | Delete (transition complete) |
| `PROJECT_ISSUES_INVENTORY.md` | Resolved issues from Jan 8 | Delete or archive |
| `REITs_Industry_Module_v2_1.docx` | Duplicates the .md version | Delete (corrupted per prior audit) |
| `ADT_DO_Analysis_v1_1_Final.docx` | Reference template | KEEP — formatting reference |

Removing 5 files would free up project knowledge capacity and reduce confusion.

---

### 🟡 ISSUE 10: Missing Patches Never Uploaded

These were created in conversations but never made it to project files:

| Item | Created In | Status |
|------|-----------|--------|
| QS-044 to QS-048 (prospective checks) | Jan 16 session | ❌ Not in project |
| F.5-000 prerequisite | Jan 16 session | ❌ Not in project |
| v1.3 Markdown output template | Jan 16 session | ❌ Not in project |
| OUT-001 to OUT-003 rules | Jan 16 session | ❌ Not in project |
| FETCH-001, FETCH-002 rules | Identified now | ❌ Not in project |

---

### 🟡 ISSUE 11: Encoding Corruption

**Source**: Jan 8 audit found 22 files with UTF-8 garbled characters (â€", â€™, etc.)

**Status**: Cleaned versions were generated but it's unclear if ALL files in project were replaced with clean versions. Some files may still have encoding artifacts.

---

## ISSUE CATEGORY 4: QUALITY / PROCESS LESSONS

### 🟡 ISSUE 12: Industry Module Structure Inconsistency

**Lesson from ORC/REIT**: First REIT module was too educational. Mike wants:
- Executive Summary with RED FLAGS / KEY STRENGTHS tables at top
- Action-oriented scoring adjustments and nuclear triggers
- Simple risk tiers that drive pricing decisions
- Management questions ranked by impact with upgrade/downgrade criteria

**Status**: This lesson was learned and applied to later modules, but the principle isn't codified in project instructions.

**Fix**: Add industry module quality standard to instructions:
```
Every industry module MUST include:
1. Executive Summary with RED FLAG and KEY STRENGTH tables
2. Sector-specific scoring adjustments (point values)
3. Nuclear triggers for the sector
4. Management questions ranked by underwriting impact
5. Upgrade/downgrade response criteria for each question
```

---

### 🟡 ISSUE 13: Integration Over Multiplication

**Lesson from Primoris**: When gaps are found, instinct is to add modules. Mike's correction: "integrate, don't multiply." Modify existing checks rather than creating new categories.

**Status**: Lesson captured in memory but not in project instructions.

**Fix**: Add to Core Rules:
- **MAINT-001**: When framework gaps are identified, first attempt to modify existing checks before creating new categories. Propose surgical modifications, not new modules.

---

### 🟡 ISSUE 14: Paycom Meeting Notes Structure

**Lesson**: When restructuring meeting notes, put "What Was Said" and "Underwriting Commentary" directly below each topic — not in separate sections. Flow matters for readability.

**Status**: One-off lesson, not a recurring issue. Already in memory.

---

## PROPOSED v4.8 UPDATE MANIFEST

### New Rules to Add

| Rule ID | Description | Add To |
|---------|-------------|--------|
| OUT-001 | Markdown is default output format | 00_PROJECT_INSTRUCTIONS |
| OUT-002 | Mandatory state save after QS completion | 00_PROJECT_INSTRUCTIONS |
| OUT-003 | Targeted module loads (first 100 lines) | 00_PROJECT_INSTRUCTIONS |
| OUT-004 | No TBD placeholders — 🟣 UNKNOWN with search docs | 00_PROJECT_INSTRUCTIONS |
| EX-011 | Extract key facts from searches, discard raw text | 00_PROJECT_INSTRUCTIONS |
| FETCH-001 | SEC EDGAR fallback after 2 failures | 00_PROJECT_INSTRUCTIONS |
| FETCH-002 | Stanford SCAC fallback to broad search | 00_PROJECT_INSTRUCTIONS |
| MAINT-001 | Integration over multiplication principle | 00_PROJECT_INSTRUCTIONS |
| QS-044 | Growth catalysts identification | 01_QUICK_SCREEN |
| QS-045 | Policy/regulatory tailwinds-headwinds | 01_QUICK_SCREEN |
| QS-046 | Large project concentration | 01_QUICK_SCREEN |
| QS-047 | Key competitors and market position | 01_QUICK_SCREEN |
| QS-048 | Capital allocation priorities | 01_QUICK_SCREEN |
| F.5-000 | Guidance type determination prerequisite | 10_SCORING |

### Files to Delete

| File | Reason |
|------|--------|
| `10_SCORING_F2_UPDATE.md` | Merge into 10_SCORING first |
| `11_OUTPUT_TEMPLATE_V1_1.md` | Superseded by v1.2 |
| `RULE_RENUMBERING_MAP.md` | Legacy transition complete |
| `PROJECT_ISSUES_INVENTORY.md` | Issues resolved |
| `REITs_Industry_Module_v2_1.docx` | Duplicate of .md version + corrupted |

### Files to Add

| File | Purpose |
|------|---------|
| `11_OUTPUT_TEMPLATE_V1_3_MD.md` | Markdown-native output template |

### Files to Update

| File | Changes |
|------|---------|
| `00_PROJECT_INSTRUCTIONS` | v4.7 → v4.8, add OUT/FETCH/MAINT rules, correct check counts |
| `01_QUICK_SCREEN` | Add QS-044 through QS-048 |
| `10_SCORING` | Merge F.2 update + add F.5-000 |
| `RULE_INDEX` | Add new rules, update totals |

---

## COMPLETED ANALYSES REGISTRY

| # | Company | Ticker | Sector | Score | Tier | Key Outcome |
|---|---------|--------|--------|-------|------|-------------|
| 1 | MSA Safety | MSA | INDU | ~25 | Below Avg | Led to VER-001/ZER-001 protocols |
| 2 | Generac Holdings | GNRC | INDU | ~15 | Low | Clean, prospective-only approach |
| 3 | Design Therapeutics | DSGN | BIOT | ~20 | Below Avg | Biotech module validated |
| 4 | Clear Street Group | Private | FINS | N/A | Conditional | Pre-IPO assessment |
| 5 | ADT Inc. | ADT | CDIS | ~28 | Below Avg | Established formatting template |
| 6 | CSX Corporation | CSX | CDIS/Rail | ~22 | Below Avg | Led to transport module |
| 7 | Orchid Island Capital | ORC | REIT | 49 | Elevated | Led to REIT module rewrite |
| 8 | Edison International | EIX | UTIL | 75 | EXTREME | Nuclear trigger (active litigation) |
| 9 | Discord Inc. | Private | TECH | 58 | HIGH | IPO Section 11 analysis |
| 10 | Eikon Therapeutics | EIKN | BIOT | 28 | Average | IPO biotech assessment |
| 11 | Silicon Labs | SLAB | TECH | ~30 | Average | Material weakness, no filed suit |
| 12 | TransDigm Group | TDG | INDU | 32 | Below Avg | Renewal, DOD scrutiny |
| 13 | Primoris Services | PRIM | INDU | 5 | Minimal | Exposed backward-looking gap |
| 14 | Kaiser Aluminum | KALU | INDU | 19 | Low | TBD lesson learned |
| 15 | NeuroPace | NPCE | HLTH | ~55 | High | Failed trial + securities investigations |
| 16 | Paycom Software | PAYC | TECH | N/A | CAUTION | Meeting notes + derivative gap |
| 17 | Liftoff Mobile | Private | TECH | N/A | Decline | Pre-IPO, 7.5x leverage |
| 18 | Jack in the Box | JACK | CDIS | 45 | Average | Franchise risk supplement |

---

## REGARDING "AGENT TEAMS"

The "agent teams" or "multiple agents" feature you've referenced in prior conversations (Kaiser, Discord, Liftoff) was the **extended search task** capability — where Claude launches parallel research threads to gather data simultaneously rather than sequentially.

**Current status**: This feature (`launch_extended_search_task`) is NOT currently available in my tool set for this conversation. The tools I have access to right now are: web_search, web_fetch, project_knowledge_search, conversation_search, Google Drive, Gmail, Google Calendar, Chrome browser automation, and file creation tools.

**What you can do**:
- If you're on Claude Max ($100 or $200/month), you may have access to **Deep Research** which performs comprehensive multi-source research with a written report
- The extended search/agent capability availability varies — it may need to be enabled in your account settings or may be rolling out gradually
- For D&O analyses specifically, the sequential approach works — the bottleneck is context window, not search parallelism

I'd recommend checking your Claude settings or contacting Anthropic support to confirm whether the extended search capability is available on your plan. If it becomes available, I can integrate it into the NEG-001 sweep (running all 8 searches simultaneously) which would be the highest-value use case.

---

## PRIORITY ACTION PLAN

### Immediate (Do Now)
1. ✅ Review this audit report
2. Delete 5 orphaned files from project
3. Upload v1.3 markdown template (I can generate it now)

### Short-Term (Next Session)
4. Generate updated 00_PROJECT_INSTRUCTIONS v4.8 incorporating all new rules
5. Generate updated 01_QUICK_SCREEN with QS-044 to QS-048
6. Generate updated 10_SCORING with merged F.2 + F.5-000
7. Generate updated RULE_INDEX

### Ongoing
8. After each analysis, update the completed analyses registry
9. Enforce markdown-first output to preserve context budget
10. State file saves after QS completion for every analysis

---

**END OF AUDIT REPORT**
