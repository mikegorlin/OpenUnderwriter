# Phase 47 SKIPPED Check Re-Audit Report

**Generated:** 2026-02-25
**Source:** AAPL state.json (output/AAPL-2026-02-25/state.json)
**Total SKIPPED:** 68
**Supersedes:** Phase 46 bucket classification

---

## Summary

| Population | Count | Action |
|---|---|---|
| Intentionally unmapped — external APIs / post-analysis artifacts / proprietary | 20 | Leave SKIPPED, no routing |
| Intentionally unmapped — DEF 14A data awaiting Phase 47 extraction expansion | 34 | Fix via DEF 14A schema expansion (Plan 47-04) |
| Intentionally unmapped — field exists but routing gap in FIELD_FOR_CHECK | 12 | Fix via routing (Plans 47-02/47-03) |
| Routing gap (routing-gap bucket) | 2 | Fix via routing (Plans 47-02/47-03) |
| **Total** | **68** | |

---

## Population A: Truly Intentionally Unmapped (20 checks)

These checks are genuinely unmappable in Phase 47 due to data constraints. They should remain SKIPPED. Phase 47 routing work does NOT touch these.

### A1: Post-analysis artifacts — no field to route (2 checks)

These checks are computed from analysis outputs, not raw extracted data. They have no field_for_check candidate because their inputs don't exist until executive risk scoring runs. Adding routing would require a separate post-scoring pass.

| Check ID | Reason |
|---|---|
| `EXEC.CEO.risk_score` | Composite score derived by executive risk engine after analysis — not a raw extracted field |
| `EXEC.CFO.risk_score` | Composite score derived by executive risk engine after analysis — not a raw extracted field |

### A2: External API / proprietary data sources (13 checks)

These checks require live external API access (Glassdoor, LinkedIn, Blind, ISS, etc.) that is not part of the acquire pipeline. Data sources are either proprietary (ISS) or require authenticated API keys (Glassdoor, LinkedIn). Intentionally unmapped per Phase 46 classification.

| Check ID | Data Source Required | Reason |
|---|---|---|
| `FWRD.WARN.app_ratings` | App store APIs (Apple, Google) | External authenticated API, not SEC |
| `FWRD.WARN.blind_posts` | Blind.com API | External authenticated API, not SEC |
| `FWRD.WARN.cfpb_complaints` | CFPB Complaint Database | External API, sector-specific |
| `FWRD.WARN.fda_medwatch` | FDA MedWatch API | External API, sector-specific |
| `FWRD.WARN.g2_reviews` | G2.com API | External authenticated API, not SEC |
| `FWRD.WARN.glassdoor_sentiment` | Glassdoor API | External authenticated API, not SEC |
| `FWRD.WARN.indeed_reviews` | Indeed API | External authenticated API, not SEC |
| `FWRD.WARN.journalism_activity` | Media monitoring APIs | External paid service |
| `FWRD.WARN.linkedin_departures` | LinkedIn API | External authenticated API, not SEC |
| `FWRD.WARN.linkedin_headcount` | LinkedIn API | External authenticated API, not SEC |
| `FWRD.WARN.nhtsa_complaints` | NHTSA Database | External API, sector-specific (automotive) |
| `FWRD.WARN.social_sentiment` | Twitter/Reddit APIs | External authenticated APIs |
| `FWRD.WARN.trustpilot_trend` | Trustpilot API | External authenticated API, not SEC |
| `GOV.EFFECT.iss_score` | ISS Governance Solutions | Proprietary paid data — not publicly available |
| `GOV.EFFECT.proxy_advisory` | ISS/Glass Lewis advisories | Proprietary paid data — not publicly available |

### A3: LLM narrative comparison checks — out of Phase 47 scope (2 checks)

These checks require comparing text from two different documents (e.g., 10-K vs earnings call transcript) using an LLM. The compare_narratives() capability does not yet exist in the pipeline.

| Check ID | Reason |
|---|---|
| `FWRD.NARRATIVE.10k_vs_earnings` | Requires LLM comparison of 10-K MD&A vs earnings call transcript — capability not built |
| `FWRD.NARRATIVE.investor_vs_sec` | Requires LLM comparison of investor presentations vs SEC filings — capability not built |

### A4: NLP filing timing checks — no field_key in routing map (2 checks)

These checks require computing filing delay from SEC EDGAR filing date metadata, not from extracted data fields. The filing date is available but there is no ExtractedData field that contains it — it lives in the SEC EDGAR metadata layer outside the extraction schema.

| Check ID | Reason |
|---|---|
| `NLP.FILING.filing_timing_change` | Requires comparing YoY filing dates from SEC EDGAR metadata — no ExtractedData field exists |
| `NLP.FILING.late_filing` | Requires computing delay from SEC deadline vs actual filing date — no ExtractedData field exists |

---

## Population B: Fixable via DEF 14A Extraction Expansion (34 checks)

These checks have `required_data: [SEC_DEF14A]` and their field_keys map to data that would be available from a properly extracted DEF 14A proxy statement. They are currently intentionally-unmapped because the DEF14AExtraction schema does not yet extract these fields, and/or the FIELD_FOR_CHECK mapping does not exist.

**Fix path:** Plan 47-04 expands DEF14AExtraction schema + convert_board_profile() + FIELD_FOR_CHECK entries.

### B1: Board composition from DEF 14A (9 checks)

These map to board composition statistics that convert_board_profile() already partially computes. Once new DEF 14A extraction fields are added, these route via existing BoardProfile fields.

| Check ID | field_key | Current block |
|---|---|---|
| `GOV.BOARD.size` | board_size | No FIELD_FOR_CHECK entry |
| `GOV.BOARD.independence` | board_independence | No FIELD_FOR_CHECK entry |
| `GOV.BOARD.tenure` | avg_board_tenure | No FIELD_FOR_CHECK entry |
| `GOV.BOARD.overboarding` | overboarded_directors | No FIELD_FOR_CHECK entry |
| `GOV.BOARD.attendance` | board_attendance | DEF14AExtraction missing board_attendance_pct field |
| `GOV.BOARD.diversity` | board_size (proxy) | DEF14AExtraction missing board_gender_diversity_pct field |
| `GOV.BOARD.expertise` | board_expertise | DEF14AExtraction missing expertise/skills matrix field |
| `GOV.BOARD.meetings` | board_meeting_count | DEF14AExtraction missing board_meetings_held field |
| `GOV.BOARD.succession` | ceo_succession_plan | DEF14AExtraction missing succession_plan_disclosed field |

### B2: Executive profile from DEF 14A (4 checks)

Duplicate display checks that overlap with GOV.BOARD checks above — they show executive-level board stats rather than board-aggregate stats.

| Check ID | field_key | Current block |
|---|---|---|
| `EXEC.PROFILE.board_size` | (same as GOV.BOARD.size) | No FIELD_FOR_CHECK, no DEF 14A field |
| `EXEC.PROFILE.independent_ratio` | (same as GOV.BOARD.independence) | No FIELD_FOR_CHECK, no DEF 14A field |
| `EXEC.PROFILE.avg_tenure` | (same as GOV.BOARD.tenure) | No FIELD_FOR_CHECK, no DEF 14A field |
| `EXEC.PROFILE.overboarded_directors` | (same as GOV.BOARD.overboarding) | No FIELD_FOR_CHECK, no DEF 14A field |

### B3: Governance rights from DEF 14A (10 checks)

Anti-takeover provisions and shareholder rights provisions already exist in DEF14AExtraction schema (`classified_board`, `supermajority_voting`, `poison_pill`, `forum_selection_clause`, `exclusive_forum_provision`). However, FIELD_FOR_CHECK entries are missing for most.

| Check ID | field_key | Current block |
|---|---|---|
| `GOV.RIGHTS.classified` | classified_board | No FIELD_FOR_CHECK entry — field exists in DEF14AExtraction |
| `GOV.RIGHTS.supermajority` | supermajority_required | No FIELD_FOR_CHECK entry — field exists in DEF14AExtraction |
| `GOV.RIGHTS.forum_select` | forum_selection_clause | No FIELD_FOR_CHECK entry — field exists in DEF14AExtraction |
| `GOV.RIGHTS.takeover` | takeover_defenses | No FIELD_FOR_CHECK entry — blank_check_preferred exists in schema |
| `GOV.RIGHTS.proxy_access` | proxy_access_threshold | DEF14AExtraction missing proxy_access_threshold field |
| `GOV.RIGHTS.special_mtg` | special_meeting_threshold | DEF14AExtraction missing special_meeting_threshold field |
| `GOV.RIGHTS.action_consent` | action_by_consent | DEF14AExtraction missing action_by_consent field |
| `GOV.RIGHTS.bylaws` | bylaw_provisions | DEF14AExtraction missing bylaw_amendment_rights field |
| `LIT.DEFENSE.forum_selection` | forum_selection_clause | No FIELD_FOR_CHECK entry — forum_selection_clause exists in DEF14AExtraction |
| `GOV.EFFECT.sig_deficiency` | significant_deficiency_flag | Not in DEF14AExtraction; needed from 10-K item 9A |

### B4: Compensation from DEF 14A (7 checks)

Additional compensation details not currently extracted from DEF 14A.

| Check ID | field_key | Current block |
|---|---|---|
| `GOV.PAY.golden_para` | golden_parachute_value | DEF14AExtraction has golden_parachute_total — no FIELD_FOR_CHECK |
| `GOV.PAY.hedging` | hedging_policy | DEF14AExtraction missing hedging_policy field |
| `GOV.PAY.equity_burn` | equity_burn_rate | DEF14AExtraction missing equity_burn_rate field |
| `GOV.PAY.exec_loans` | executive_loans | DEF14AExtraction missing exec_loans field |
| `GOV.PAY.401k_match` | retirement_benefits | DEF14AExtraction missing retirement_benefit_detail field |
| `GOV.PAY.deferred_comp` | deferred_comp_detail | DEF14AExtraction missing deferred_comp_detail field |
| `GOV.PAY.pension` | pension_detail | DEF14AExtraction missing pension_detail field |

### B5: Governance effectiveness from DEF 14A / 10-K (4 checks)

| Check ID | field_key | Current block |
|---|---|---|
| `GOV.EFFECT.auditor_change` | auditor_change_flag | Field may exist in extraction — needs FIELD_FOR_CHECK mapping |
| `GOV.EFFECT.late_filing` | late_filing_flag | Requires NT filing detection — different from NLP.FILING.late_filing |
| `GOV.EFFECT.nt_filing` | nt_filing_flag | Requires NT 10-K/10-Q filing detection |
| `GOV.INSIDER.plan_adoption` | plan_adoption_timing | Requires Form 4 Rule 10b5-1 plan adoption detection |
| `GOV.INSIDER.unusual_timing` | insider_unusual_timing | Requires Form 4 timing analysis |

---

## Population C: Routing Gap — Field Exists, No FIELD_FOR_CHECK Entry (12 checks)

These checks have data available in `ExtractedData` but no routing entry in `FIELD_FOR_CHECK`. Fix path: add `field_for_check` to brain YAML + rebuild.

| Check ID | field_key | What's in ExtractedData |
|---|---|---|
| `BIZ.DEPEND.labor` | labor_risk_flag_count | 10-K labor dependency text extraction |
| `BIZ.STRUCT.vie_spe` | vie_spe_present | 10-K VIE/SPE disclosure extraction |
| `FIN.ACCT.auditor_attestation_fail` | auditor_attestation_fail | 10-K Item 9A ICFR attestation |
| `FIN.ACCT.auditor_disagreement` | auditor_disagreement | 8-K disagreement with accountant |
| `FIN.ACCT.restatement_auditor_link` | restatement_auditor_link | 8-K restatement disclosure |
| `FIN.QUALITY.deferred_revenue_trend` | (derived) | Deferred revenue YoY from XBRL |
| `FIN.QUALITY.q4_revenue_concentration` | (derived) | Q4 vs annual revenue from XBRL + 10-Q |
| `FWRD.DISC.sec_comment_letters` | (from SEC EDGAR) | SEC comment letter metadata |
| `LIT.REG.comment_letters` | comment_letter_count | SEC comment letter count |
| `LIT.SECTOR.regulatory_databases` | sector_regulatory_count | Regulatory database cross-check |
| `GOV.EFFECT.iss_score` | iss_governance_score | Proprietary — see Population A2 |
| `GOV.EFFECT.proxy_advisory` | proxy_advisory_concern | Proprietary — see Population A2 |

**Note:** `GOV.EFFECT.iss_score` and `GOV.EFFECT.proxy_advisory` appear here only because they have field_keys — they are already classified as Population A2 (proprietary). The other 10 checks are genuine routing gaps fixable in Plan 47-02/47-03.

---

## Population D: Routing-Gap Bucket (2 checks)

These 2 checks have `gap_bucket: routing-gap` explicitly set in brain YAML from Phase 46 triage.

| Check ID | field_key | gap_keywords | Fix |
|---|---|---|---|
| `FIN.ACCT.restatement_stock_window` | restatement_stock_window | restatement, stock drop, disclosure | Add FIELD_FOR_CHECK mapping |
| `LIT.PATTERN.peer_contagion` | peer_contagion_risk | peer lawsuit, contagion, class action | Add FIELD_FOR_CHECK mapping |

---

## Intentionally-Unmapped Decisions

The following checks are **explicitly marked as intentionally unmapped** and must NOT have routing added in Phase 47:

1. **`EXEC.CEO.risk_score` and `EXEC.CFO.risk_score`** — Post-analysis composite scores; no raw field to route
2. **13x `FWRD.WARN.*`** (glassdoor, indeed, blind, app_ratings, g2_reviews, cfpb_complaints, fda_medwatch, journalism_activity, linkedin_departures, linkedin_headcount, nhtsa_complaints, social_sentiment, trustpilot_trend) — External APIs not in scope
3. **`FWRD.NARRATIVE.10k_vs_earnings` and `FWRD.NARRATIVE.investor_vs_sec`** — LLM comparison capability not yet built
4. **`GOV.EFFECT.iss_score` and `GOV.EFFECT.proxy_advisory`** — ISS/Glass Lewis proprietary data
5. **`NLP.FILING.filing_timing_change` and `NLP.FILING.late_filing`** — No ExtractedData field for SEC filing date metadata

**Target SKIPPED floor after Phase 47:** ~20-22 checks (the 20 truly intentionally unmapped in Population A). The remaining 46-48 checks should move to CLEAR/TRIGGERED/INFO as routing and extraction are added.

---

*Report generated from AAPL state.json + brain YAML gap_bucket classification*
*Phase 46 gap search already resolved 0 of these (gap_search_summary shows routing-gap population same as pre-46)*
