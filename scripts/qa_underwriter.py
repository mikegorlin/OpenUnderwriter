"""Underwriter-Perspective QA — Does this worksheet instill confidence?

Unlike qa_uw_analysis.py (technical correctness), this QA system asks:
"Would a 30-year underwriter trust this output?"

Checks for:
- Ghost data (empty case shells, placeholder counts with no detail)
- Extraction gaps masquerading as analysis ("Not extracted" shown to user)
- Boilerplate that reveals machine origin
- Wasted space (charts with 1 data point, empty tables)
- Missing explanations (data shown without WHY it matters)
- Confidence killers (all-dash columns, generic D&O commentary)

Usage:
  uv run python scripts/qa_underwriter.py output/ULS\ -\ UL\ Solutions/2026-03-25/ULS_worksheet.html
  uv run python scripts/qa_underwriter.py --state output/ULS\ -\ UL\ Solutions/2026-03-25/state.json

Exit code: 0 = pass, 1 = issues found
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────
# CATEGORY 1: GHOST DATA — Sections that LOOK populated but are empty
# ─────────────────────────────────────────────────────────────────────


def check_ghost_data(html: str) -> list[str]:
    """Detect sections that show counts/headers but have no actual content.

    Examples:
    - "Derivative Suits (2)" but no case names/dates/courts
    - "Active Matters" header with nothing under it
    - Tables with all N/A or all dashes in data columns
    """
    issues = []

    # Ghost derivative suits: header shows count but no actual case details
    deriv_match = re.search(r"Derivative Suits\s*\((\d+)\)", html)
    if deriv_match:
        count = int(deriv_match.group(1))
        if count > 0:
            # Check if any actual case names exist after this header
            deriv_pos = deriv_match.end()
            deriv_section = html[deriv_pos : deriv_pos + 3000]
            # Look for actual case names (should have "v." or "vs." or specific names)
            has_case_names = bool(re.search(r"\bv\.\s|vs\.\s|\bCase No\.", deriv_section))
            has_dates = bool(re.search(r"20\d{2}-\d{2}-\d{2}", deriv_section))
            if not has_case_names and not has_dates:
                issues.append(
                    f"GHOST DATA: 'Derivative Suits ({count})' shows count but no actual "
                    f"case names, filing dates, or court information — remove or populate"
                )

    # Ghost tables: tables where >80% of data cells are dashes or N/A
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL)
    for i, table in enumerate(tables):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", table, re.DOTALL)
        if len(cells) < 6:
            continue
        cell_texts = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
        dash_count = sum(1 for c in cell_texts if c in ("—", "-", "–", ""))
        na_count = sum(1 for c in cell_texts if c in ("N/A", "Not Available", "Not extracted", "None", "UNKNOWN"))
        empty_pct = (dash_count + na_count) / len(cell_texts) if cell_texts else 0
        if empty_pct > 0.7 and len(cell_texts) > 10:
            # Get nearby heading for context
            table_pos = html.find(table[:50])
            heading = ""
            if table_pos > 0:
                pre = html[max(0, table_pos - 500) : table_pos]
                hdg = re.findall(r"<h[2-5][^>]*>([^<]+)</h", pre)
                if hdg:
                    heading = hdg[-1]
            issues.append(
                f"GHOST TABLE near '{heading}': {dash_count + na_count}/{len(cell_texts)} "
                f"cells are dashes/N/A ({empty_pct:.0%}) — hide or populate"
            )

    return issues


# ─────────────────────────────────────────────────────────────────────
# CATEGORY 2: EXTRACTION GAPS SHOWN TO USER
# ─────────────────────────────────────────────────────────────────────


def check_extraction_gaps_visible(html: str) -> list[str]:
    """Flag 'Not extracted' labels visible to the underwriter.

    If we couldn't extract data, don't show the field at all.
    Showing 'Not extracted' tells the user the system failed.
    """
    issues = []
    not_extracted_count = html.count("Not extracted")
    if not_extracted_count > 0:
        # Find what provisions show "Not extracted"
        contexts = re.findall(r"([^<]{0,50})Not extracted", html)
        unique_contexts = set()
        for ctx in contexts:
            clean = re.sub(r"<[^>]+>", "", ctx).strip()
            if clean:
                unique_contexts.add(clean[-40:])
        issues.append(
            f"EXTRACTION GAP: 'Not extracted' shown {not_extracted_count} times to user — "
            f"either extract or hide. Contexts: {list(unique_contexts)[:5]}"
        )
    return issues


# ─────────────────────────────────────────────────────────────────────
# CATEGORY 3: CONFIDENCE KILLERS — Patterns that erode trust
# ─────────────────────────────────────────────────────────────────────


def check_confidence_killers(html: str) -> list[str]:
    """Detect patterns that make an underwriter lose confidence in the output."""
    issues = []

    # All-dash columns in data tables (like Board Forensics with all "—" in Other Boards/Flags)
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL)
    for table in tables:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, re.DOTALL)
        if len(rows) < 4:
            continue  # Skip small tables
        # Check each column for all-dash pattern
        header_row = rows[0] if rows else ""
        headers = re.findall(r"<th[^>]*>(.*?)</th>", header_row, re.DOTALL)
        headers_clean = [re.sub(r"<[^>]+>", "", h).strip() for h in headers]

        for col_idx, header in enumerate(headers_clean):
            if not header:
                continue
            col_vals = []
            col_has_visual = False
            for row in rows[1:]:  # Skip header
                cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
                if col_idx < len(cells):
                    raw_cell = cells[col_idx]
                    val = re.sub(r"<[^>]+>", "", raw_cell).strip()
                    col_vals.append(val)
                    # Detect visual-only content: SVGs, confidence dots, styled
                    # indicator spans, progress bar divs — these have no text
                    # but carry meaningful visual data
                    if re.search(
                        r"<svg|confidence-dot|percentile-fill|percentile-bar|"
                        r"border-radius:\s*\d+px|"
                        r"height:\s*\d+px.*overflow:\s*hidden|"
                        r"width:\s*[\d.]+%",
                        raw_cell,
                    ):
                        col_has_visual = True
            if col_has_visual:
                continue  # Visual columns (dots, bars, sparklines) are valid
            if len(col_vals) >= 3:
                dash_count = sum(1 for v in col_vals if v in ("—", "-", "–", ""))
                if dash_count == len(col_vals):
                    issues.append(
                        f"ALL-DASH COLUMN: '{header}' column has {len(col_vals)} rows, "
                        f"ALL showing dashes — remove column or populate data"
                    )

    # Generic boilerplate D&O commentary
    caution_zone = html.count("caution zone")
    if caution_zone > 0:
        issues.append(
            f"GENERIC COMMENTARY: 'caution zone' appears {caution_zone} times — "
            f"brain YAML templates need specific litigation theory context"
        )

    monitor_count = html.count("Monitor for deterioration")
    if monitor_count > 0:
        issues.append(
            f"BOILERPLATE: 'Monitor for deterioration' appears {monitor_count} times — "
            f"tells underwriter nothing about WHAT to monitor or WHY"
        )

    # "UNKNOWN" status shown to user
    unknown_count = len(re.findall(r">\s*UNKNOWN\s*<", html))
    if unknown_count > 0:
        issues.append(
            f"INTERNAL STATUS: 'UNKNOWN' shown {unknown_count} times — "
            f"resolve to actual status or hide"
        )

    # Hardcoded conclusions that aren't derived from data
    _HARDCODED_CONCLUSIONS = [
        ("No securities class action history", "May be wrong — check actual SCA data"),
        ("No IPO/SPAC transaction risk exposure", "Wrong for recent IPOs — Section 11/12 exposure"),
        ("No restatements", "Should come from data, not hardcoded"),
        ("No financial distress indicators", "Should come from Altman/Beneish, not hardcoded"),
        ("Sound governance structure", "Should come from governance score, not hardcoded"),
        ("Stable executive leadership", "Should come from departure data, not hardcoded"),
        ("Normal short interest", "Should come from actual short data, not hardcoded"),
        ("Controlled volatility within normal range", "Should come from beta/vol data, not hardcoded"),
        ("Consistent earnings delivery", "Should come from miss data, not hardcoded"),
        ("Stable stock performance", "Should come from drawdown data, not hardcoded"),
    ]
    for phrase, reason in _HARDCODED_CONCLUSIONS:
        if phrase in html:
            issues.append(
                f"HARDCODED CONCLUSION: '{phrase}' — {reason}. "
                f"Conclusions must be derived from data, never static."
            )

    return issues


# ─────────────────────────────────────────────────────────────────────
# CATEGORY 4: WASTED SPACE — Charts/sections that add no value
# ─────────────────────────────────────────────────────────────────────


def check_wasted_space(html: str) -> list[str]:
    """Detect charts and sections that waste space without adding value."""
    issues = []

    # Charts with very few data points (embedded as PNG/SVG)
    # Timeline charts are generated as matplotlib PNGs — check if tiny
    img_tags = re.findall(r'<img[^>]+src="data:image/png;base64,([^"]{100,})"', html)
    # We can't decode PNGs easily, but we can check for timeline-related context
    timeline_mentions = re.findall(
        r"Litigation\s*(?:&amp;|&)\s*Regulatory\s*Timeline", html
    )

    # Check if timeline section exists but has very few events
    for tm in timeline_mentions:
        tm_pos = html.find(tm)
        if tm_pos >= 0:
            # Look for event data near the chart
            section = html[tm_pos : tm_pos + 5000]
            event_dates = re.findall(r"20\d{2}-\d{2}-\d{2}", section)
            unique_dates = set(event_dates)
            if len(unique_dates) <= 2:
                issues.append(
                    f"WASTED SPACE: Litigation Timeline chart shows only "
                    f"{len(unique_dates)} unique event(s) — consider inline display "
                    f"instead of full chart"
                )

    # Empty sections with just a header and "No X identified"
    no_identified = re.findall(
        r"<h[2-5][^>]*>([^<]+)</h[2-5]>\s*(?:<[^>]+>\s*)*(?:<[ip][^>]*>)?\s*"
        r"(?:No\s+[\w-]+\s+(?:identified|found|available|detected))",
        html,
    )
    for heading in no_identified:
        clean = re.sub(r"<[^>]+>", "", heading).strip()
        issues.append(
            f"EMPTY SECTION: '{clean}' says 'No X identified' — "
            f"hide section entirely or explain what was searched"
        )

    # Theoretical Exposure Windows — only flag if shown WITHOUT actual windows
    if "Theoretical Exposure Windows" in html:
        tew_pos = html.find("Theoretical Exposure Windows")
        # Check if "Active Windows" section exists BEFORE the theoretical one
        has_active_windows = "Active Windows" in html[:tew_pos] if tew_pos > 0 else False
        if not has_active_windows:
            tew_section = html[tew_pos : tew_pos + 3000]
            open_count = tew_section.count(">Open<")
            if open_count >= 4:
                issues.append(
                    f"CONFUSING SECTION: 'Theoretical Exposure Windows' shows {open_count} "
                    f"claim types all as 'Open' with no actual events — needs plain-English "
                    f"explanation of what this means or should be hidden"
                )

    return issues


# ─────────────────────────────────────────────────────────────────────
# CATEGORY 5: MISSING EXPLANATIONS — Data shown without context
# ─────────────────────────────────────────────────────────────────────


def check_missing_explanations(html: str) -> list[str]:
    """Detect data displayed without explanation of WHY it matters for D&O."""
    issues = []

    # Governance checks with no meaningful D&O explanation
    gov_checks_pos = html.find("Governance Checks")
    if gov_checks_pos >= 0:
        gov_section = html[gov_checks_pos : gov_checks_pos + 5000]
        triggered = re.findall(r"TRIGGERED", gov_section)
        if triggered:
            # Check if D&O Risk column has generic text
            do_risk_texts = re.findall(
                r"D&amp;?O\s+Risk.*?<td[^>]*>(.*?)</td>", gov_section, re.DOTALL
            )
            for text in do_risk_texts:
                clean = re.sub(r"<[^>]+>", "", text).strip()
                if "caution zone" in clean.lower() or "monitor for" in clean.lower():
                    issues.append(
                        f"UNEXPLAINED CHECK: Triggered governance check has generic "
                        f"D&O text: '{clean[:80]}...' — should explain specific "
                        f"litigation theory (Caremark, proxy contest, etc.)"
                    )

    # Board members with no forensic detail
    board_pos = html.find("Board Member Forensic Profiles")
    if board_pos >= 0:
        board_section = html[board_pos : board_pos + 10000]
        members = re.findall(r"Independence &amp;? Forensic Detail", board_section)
        detail_texts = re.findall(
            r"Independence.*?Detail.*?<(?:div|td|span)[^>]*>(.*?)</(?:div|td|span)>",
            board_section,
            re.DOTALL,
        )
        empty_details = sum(
            1 for d in detail_texts
            if re.sub(r"<[^>]+>", "", d).strip() in ("", "—", "-")
        )
        if members and empty_details > len(members) * 0.5:
            issues.append(
                f"EMPTY FORENSICS: {empty_details}/{len(members)} board members have "
                f"no forensic detail — section promises forensic analysis but delivers "
                f"nothing. Either populate or remove the 'Forensic' label."
            )

    return issues


# ─────────────────────────────────────────────────────────────────────
# CATEGORY 6: CONTRADICTIONS — Data that conflicts with itself
# ─────────────────────────────────────────────────────────────────────


def check_contradictions(html: str) -> list[str]:
    """Detect internal contradictions in the worksheet."""
    issues = []

    # "No deal-related litigation" when there ARE deal events
    # But NOT a contradiction if the template already notes the M&A activity
    if "No deal-related litigation identified" in html:
        has_ma_note = "recent M&amp;A activity" in html or "recent M&A activity" in html
        if not has_ma_note:
            deal_events = []
            for term in ["divestiture", "divest", "acquisition", "acquir", "offering", "secondary"]:
                if term.lower() in html.lower():
                    deal_events.append(term)
            if len(deal_events) >= 2:
                issues.append(
                    f"CONTRADICTION: 'No deal-related litigation identified' but worksheet "
                    f"mentions deal activity ({', '.join(deal_events[:3])}). "
                    f"Should explain what was searched and why nothing was found."
                )

    # Score says WIN but red flags are present
    if re.search(r"\bWIN\b", html[:5000]):
        critical_flags = len(re.findall(r"TRIGGERED|HIGH.*?risk|critical|severe", html[:20000], re.I))
        if critical_flags > 5:
            issues.append(
                f"SCORE-FLAG TENSION: Score tier is WIN but {critical_flags} risk "
                f"indicators found — commentary should address this explicitly"
            )

    return issues


# ─────────────────────────────────────────────────────────────────────
# CATEGORY 7: STATE-LEVEL CHECKS (run against state.json)
# ─────────────────────────────────────────────────────────────────────


def check_state_quality(state_path: str) -> list[str]:
    """Deep checks against the pipeline state, not just rendered HTML."""
    issues = []

    try:
        with open(state_path) as f:
            state = json.load(f)
    except Exception as e:
        return [f"Cannot load state: {e}"]

    # Check derivative suits quality
    deriv = state.get("extracted", {}).get("litigation", {}).get("derivative_suits", [])
    for i, suit in enumerate(deriv):
        case_name = suit.get("case_name")
        filing_date = suit.get("filing_date")
        court = suit.get("court")
        if not case_name and not filing_date and not court:
            issues.append(
                f"GHOST DERIVATIVE SUIT #{i + 1}: No case name, no filing date, no court — "
                f"this is an empty data shell, not a real case. Remove it."
            )

    # Check board forensics completeness
    board = state.get("extracted", {}).get("governance", {}).get("board_forensics", [])
    if board:
        empty_other_boards = sum(
            1 for m in board
            if not m.get("other_boards") or all(
                not (ob.get("value") if isinstance(ob, dict) else ob)
                for ob in (m.get("other_boards") or [])
            )
        )
        if empty_other_boards == len(board) and len(board) > 3:
            issues.append(
                f"BOARD DATA GAP: {len(board)} directors but NONE have 'other_boards' "
                f"populated — LLM extraction likely failed to parse proxy statement "
                f"board seat disclosures"
            )

    # Check bylaws extraction
    board_gov = state.get("extracted", {}).get("governance", {}).get("board", {})
    if board_gov:
        bylaws_fields = [
            "exclusive_forum_provision", "forum_selection_clause",
            "supermajority_voting", "special_meeting_threshold",
            "written_consent_allowed",
        ]
        missing = []
        for field in bylaws_fields:
            val = board_gov.get(field)
            if val is None or (isinstance(val, dict) and val.get("value") is None):
                missing.append(field)
        if missing:
            issues.append(
                f"BYLAWS GAPS: {len(missing)}/{len(bylaws_fields)} charter provisions "
                f"not extracted: {missing}. Either enhance DEF 14A extraction or "
                f"hide these fields."
            )

    # Check litigation timeline events
    timeline = state.get("extracted", {}).get("litigation", {}).get("litigation_timeline_events", [])
    if len(timeline) <= 1:
        issues.append(
            f"SPARSE TIMELINE: Only {len(timeline)} litigation timeline event(s) — "
            f"chart will be mostly empty. Consider inline display instead of full chart."
        )

    return issues


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────


def load_html(path: str) -> str:
    """Load HTML file."""
    return Path(path).read_text()


def run_qa(html_path: str, state_path: str | None = None) -> bool:
    """Run all underwriter-perspective QA checks."""
    html = load_html(html_path)
    print(f"Underwriter QA: {len(html):,} chars from {Path(html_path).name}")
    print("=" * 70)

    all_issues: list[str] = []
    html_checks: list[tuple[str, Any]] = [
        ("Ghost Data (empty shells)", check_ghost_data),
        ("Extraction Gaps Visible", check_extraction_gaps_visible),
        ("Confidence Killers", check_confidence_killers),
        ("Wasted Space", check_wasted_space),
        ("Missing Explanations", check_missing_explanations),
        ("Internal Contradictions", check_contradictions),
    ]

    for name, fn in html_checks:
        try:
            issues = fn(html)
        except Exception as e:
            issues = [f"CHECK ERROR: {e}"]
        if issues:
            print(f"\n  FAIL: {name} ({len(issues)} issues)")
            for issue in issues:
                print(f"    - {issue}")
            all_issues.extend(issues)
        else:
            print(f"  PASS: {name}")

    # State-level checks
    if state_path:
        print()
        try:
            state_issues = check_state_quality(state_path)
        except Exception as e:
            state_issues = [f"STATE CHECK ERROR: {e}"]
        if state_issues:
            print(f"  FAIL: State Quality ({len(state_issues)} issues)")
            for issue in state_issues:
                print(f"    - {issue}")
            all_issues.extend(state_issues)
        else:
            print(f"  PASS: State Quality")

    print(f"\n{'=' * 70}")
    if all_issues:
        print(f"TOTAL: {len(all_issues)} underwriter-confidence issues found")
        # Categorize
        categories = {
            "GHOST": 0, "EXTRACTION": 0, "CONFIDENCE": 0,
            "WASTED": 0, "MISSING": 0, "CONTRADICTION": 0,
            "STATE": 0,
        }
        for issue in all_issues:
            for cat in categories:
                if cat in issue.upper():
                    categories[cat] += 1
                    break
        print("  By category:", {k: v for k, v in categories.items() if v > 0})
        return False
    else:
        print("ALL UNDERWRITER QA CHECKS PASSED")
        return True


# Typing import for older Python
from typing import Any  # noqa: E402


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/qa_underwriter.py <html_path> [--state <state.json>]")
        sys.exit(1)

    html_path = sys.argv[1]
    state_path = None
    if "--state" in sys.argv:
        idx = sys.argv.index("--state")
        if idx + 1 < len(sys.argv):
            state_path = sys.argv[idx + 1]
    else:
        # Auto-detect state.json in same directory
        html_dir = Path(html_path).parent
        candidate = html_dir / "state.json"
        if candidate.exists():
            state_path = str(candidate)

    ok = run_qa(html_path, state_path)
    sys.exit(0 if ok else 1)
