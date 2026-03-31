# do-uw Project Memory

## Project Status
- **v6.0 — Company Profile Completeness** — SHIPPED 2026-03-14, archived to milestones/
- **v7.0 — Signal-Render Integrity** — CONFIRMED as next milestone (user priority)
- **Test suite: 5,687 passing, 0 failures** (2026-03-14)
- **Next step:** `/gsd:new-milestone` to formally start v7.0

## Architecture Findings
- [project_v7_decision.md](project_v7_decision.md) — Pre-v7.0 audit: 7/9 context builders bypass signals entirely
- [feedback_signal_architecture.md](feedback_signal_architecture.md) — ~60% of rendered content bypasses signal engine

## Implementation References
- [project_phase69_fixes.md](project_phase69_fixes.md)

## MCP/Skills Installed (2026-03-13)
- [mcp_skills.md](mcp_skills.md)

## User Preferences
- [user_preferences.md](user_preferences.md)

## Pending Reviews
- [project_review_decision_framework.md](project_review_decision_framework.md) — Mike must review decision_framework.yaml before Phase 107

## Product Design Decisions
- [project_worksheet_as_decision_record.md](project_worksheet_as_decision_record.md) — Worksheet is the official decision document, multi-audience, screen/print divergent

## User Feedback
- [feedback_guidance.md](feedback_guidance.md) — EPS must be company guidance not analyst consensus
- [feedback_stock_drops.md](feedback_stock_drops.md) — Stock drops must explain WHY
- [feedback_signal_architecture.md](feedback_signal_architecture.md) — All new features must follow signal architecture
- [feedback_v7_fields_mandatory.md](feedback_v7_fields_mandatory.md) — v7.0 fields are REQUIRED not optional in schema
- [feedback_research_config.md](feedback_research_config.md) — Research toggle accidentally disabled in v5.x; verify config at session start
