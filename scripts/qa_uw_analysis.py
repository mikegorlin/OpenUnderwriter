"""Automated QA for the uw analysis HTML output.

Catches raw data leaks, missing sections, broken templates, and visual issues
BEFORE showing output to the user. Run after every render.

Usage: uv run python scripts/qa_uw_analysis.py output/AAPL/2026-03-22/AAPL_worksheet.html
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def load_html(path: str) -> str:
    """Load and extract the uw-analysis section from the HTML file.

    Finds the matching </section> for the uw-analysis <section> by
    counting nested section open/close tags.
    """
    html = Path(path).read_text()
    start = html.find('id="uw-analysis"')
    if start < 0:
        print("ERROR: No uw-analysis section found in HTML")
        sys.exit(1)
    # Walk forward from the <section that contains id="uw-analysis",
    # counting nested <section> / </section> pairs to find the matching close.
    section_start = html.rfind("<section", 0, start)
    if section_start < 0:
        section_start = start
    depth = 0
    pos = section_start
    while pos < len(html):
        open_idx = html.find("<section", pos)
        close_idx = html.find("</section>", pos)
        if close_idx < 0:
            break
        if open_idx >= 0 and open_idx < close_idx:
            depth += 1
            pos = open_idx + 1
        else:
            depth -= 1
            if depth <= 0:
                return html[start : close_idx + len("</section>")]
            pos = close_idx + 1
    # Fallback: return from start to end
    return html[start:]


# ── CHECK 1: Raw Data Leaks ──────────────────────────────────────────

_LEAK_PATTERNS = [
    (r"\{'name':\s*'[^']+',\s*'count':", "Python dict literal (list of dicts)"),
    (r"\{'value':\s*'", "Raw SourcedValue dict"),
    (r"'regulatory_regime':", "Raw regulatory_regime field"),
    (r"<Confidence\.", "Python Confidence enum repr"),
    (r"SourcedValue\(", "Raw Pydantic SourcedValue repr"),
    (r"<class\s+'", "Python class repr"),
    (r"datetime\.datetime\(", "Raw datetime object"),
    (r"TzInfo\(", "Raw TzInfo repr"),
    (r"'source':\s*'[^']*',\s*'confidence':", "Raw SourcedValue metadata"),
    (r"\[{['\"]value['\"]:", "List of SourcedValue dicts"),
]


def check_raw_data_leaks(html: str) -> list[str]:
    """Detect Python objects rendered as strings in the HTML."""
    issues = []
    for pattern, desc in _LEAK_PATTERNS:
        matches = list(re.finditer(pattern, html))
        if matches:
            for m in matches[:2]:
                ctx = html[max(0, m.start() - 40) : m.end() + 60].replace("\n", " ")
                issues.append(f"RAW DATA LEAK [{desc}]: ...{ctx[:150]}...")
    return issues


# ── CHECK 2: Section Presence & Order ─────────────────────────────────

_EXPECTED_SECTIONS = [
    ("scorecard", "Decision Dashboard"),
    ("executive-brief", "Executive Summary"),
    ("company-operations", "The Company"),
    ("stock-market", "Stock & Market"),
    ("financial-health", "Financial Analysis"),
    ("governance", "People & Governance"),
    ("litigation", "Litigation & Regulatory"),
    ("sector-industry", "Sector & Industry"),
    ("scoring", "Scoring & Underwriting"),
    ("meeting-prep", "Meeting Preparation"),
    ("audit-trail", "Audit Trail"),
]


def check_section_presence(html: str) -> list[str]:
    """Verify all manifest sections exist and are in correct order."""
    issues = []
    last_pos = -1
    for section_id, label in _EXPECTED_SECTIONS:
        pos = html.find(f'id="{section_id}"')
        if pos < 0:
            issues.append(f"MISSING SECTION: {label} (id={section_id})")
        elif pos < last_pos:
            issues.append(f"WRONG ORDER: {label} appears before previous section")
        else:
            last_pos = pos
    return issues


# ── CHECK 3: Content Presence ─────────────────────────────────────────

_CONTENT_CHECKS = [
    ("Key Risk Findings", "key findings section"),
    ("Margin Profile", "financial margins"),
    ("Forensic", "distress scores"),
    ("Board of Directors", "board table"),
    ("Named Executive", "officer table"),
    ("Meeting Preparation", "questions section"),
    ("Quarterly Earnings", "earnings table"),
    ("Insider Transactions", "insider table"),
]


def check_content_presence(html: str) -> list[str]:
    """Verify key content strings appear in the rendered output."""
    issues = []
    for text, desc in _CONTENT_CHECKS:
        if text not in html:
            issues.append(f"MISSING CONTENT: '{text}' ({desc})")
    return issues


# ── CHECK 4: N/A Density ─────────────────────────────────────────────

def check_na_density(html: str) -> list[str]:
    """Flag sections with excessive N/A values (>50% of data cells)."""
    issues = []
    na_count = html.count(">N/A<")
    # Very rough heuristic — flag if way too many
    if na_count > 100:
        issues.append(f"HIGH N/A DENSITY: {na_count} occurrences of 'N/A' — check data pipeline")
    return issues


# ── CHECK 5: Visual Integrity ────────────────────────────────────────

def check_visual_integrity(html: str) -> list[str]:
    """Check for duplicate nav bars, broken SVGs, empty sections."""
    issues = []

    # Duplicate nav bars
    nav_count = html.count('id="beta-nav-bar"')
    if nav_count > 1:
        issues.append(f"DUPLICATE NAV BAR: {nav_count} instances found")
    elif nav_count == 0:
        issues.append("MISSING NAV BAR")

    # SVG charts present
    svg_count = html.count("<svg")
    if svg_count < 3:
        issues.append(f"LOW SVG COUNT: only {svg_count} SVGs — charts may be missing")

    # Empty section bodies (section header immediately followed by another section)
    empty = re.findall(
        r'id="([\w-]+)"[^>]*>.*?</div>\s*</div>\s*{#.*?MANIFEST SECTION', html, re.DOTALL
    )
    for eid in empty:
        issues.append(f"POSSIBLY EMPTY SECTION: {eid}")

    return issues


# ── CHECK 6: Template Variable Leaks ─────────────────────────────────

def check_template_leaks(html: str) -> list[str]:
    """Detect unresolved Jinja2 variables in the output."""
    issues = []
    jinja_leaks = re.findall(r"\{\{[^}]+\}\}", html)
    for leak in jinja_leaks[:5]:
        issues.append(f"UNRESOLVED TEMPLATE VAR: {leak[:80]}")
    return issues


# ── CHECK 7: Semantic Mismatch in Key Risk Findings ────────────────

# Factor names → keywords that evidence MUST contain at least one of
_FACTOR_EVIDENCE_KEYWORDS: dict[str, list[str]] = {
    "Litigation": ["litigation", "lawsuit", "case", "class action", "sca", "settlement", "filing"],
    "Stock Decline": ["stock", "price", "drop", "decline", "pe ", "valuation", "drawdown"],
    "Financial": ["restatement", "audit", "earnings", "forensic", "revenue", "accrual", "weakness"],
    "Insider": ["insider", "exercise", "plan", "10b5-1", "sell", "buy", "ipo", "offering", "spac"],
    "Guidance": ["guidance", "miss", "estimate", "analyst", "consensus", "forecast"],
    "Short Interest": ["short", "days to cover", "squeeze"],
    "Volatility": ["volatility", "beta", "drawdown", "whipsaw"],
    "Distress": ["distress", "bankruptcy", "altman", "going concern", "insolvency"],
    "Governance": ["governance", "board", "compensation", "ceo pay", "regulatory", "supply chain"],
    "Emerging": ["officer", "cfo", "tenure", "departure", "stability", "key person", "emerging"],
}


def check_semantic_mismatch(html: str) -> list[str]:
    """Flag Key Risk Findings where evidence doesn't match the factor name.

    For example, if F6 (Short Interest) shows "CEO Net Seller" as evidence,
    that's a semantic mismatch — the evidence belongs under a different factor.
    """
    issues = []
    # Find key risk findings: look for factor headline + evidence bullets
    findings_start = html.find("Key Risk Findings")
    if findings_start < 0:
        return []

    # Find the end of findings section (next major section header)
    findings_end = html.find("Executive Summary", findings_start)
    if findings_end < 0:
        findings_end = findings_start + 5000

    findings_html = html[findings_start:findings_end]

    # Extract factor name + evidence pairs
    # Pattern: factor headline followed by bullet evidence
    factor_blocks = re.findall(
        r'font-weight:700;color:#111827"?>([^<]+)</span>.*?'
        r'(?:evidence_bullets|margin:4px)',
        findings_html,
        re.DOTALL,
    )

    # Simpler approach: just check for known mismatches in the findings section
    # Look for evidence bullets and check if they mention concepts from wrong factors
    for factor_name, keywords in _FACTOR_EVIDENCE_KEYWORDS.items():
        # Find all evidence under this factor
        factor_pos = findings_html.find(factor_name)
        if factor_pos < 0:
            continue

        # Get next 500 chars of evidence
        evidence_block = findings_html[factor_pos:factor_pos + 800]

        # Extract bullet text
        bullets = re.findall(r'<span>([^<]+)</span>', evidence_block)
        for bullet in bullets:
            bullet_lower = bullet.lower()
            # Check if ANY factor keyword matches
            has_relevant = any(kw in bullet_lower for kw in keywords)
            if not has_relevant and len(bullet) > 20:
                # Check which factor this evidence SHOULD belong to
                for other_factor, other_kw in _FACTOR_EVIDENCE_KEYWORDS.items():
                    if other_factor == factor_name:
                        continue
                    if any(kw in bullet_lower for kw in other_kw):
                        issues.append(
                            f"SEMANTIC MISMATCH: '{factor_name}' shows evidence "
                            f"that matches '{other_factor}': {bullet[:80]}..."
                        )
                        break

    return issues


# ── CHECK 8: Truncation Errors ───────────────────────────────────────

def check_no_truncation(html: str) -> list[str]:
    """Ensure no analytical content was truncated with '...' via Jinja2 truncate filter."""
    issues = []
    # Find truncation patterns that shouldn't be there
    # (Allow natural ellipsis in prose, but flag programmatic truncation)
    trunc_count = html.count("| truncate(")
    if trunc_count > 0:
        issues.append(f"JINJA2 TRUNCATE: {trunc_count} usages of | truncate() filter")
    return issues


# ── CHECK 9: Monitor for Deterioration Boilerplate ──────────────────

def check_boilerplate_text(html: str) -> list[str]:
    """Flag generic boilerplate text that adds no analytical value."""
    issues = []
    monitor_count = html.count("Monitor for deterioration")
    if monitor_count > 0:
        issues.append(
            f"BOILERPLATE: 'Monitor for deterioration' appears {monitor_count} times — "
            f"generic brain YAML text leaking into output"
        )
    return issues


# ── CHECK 10: Section Content Quality ─────────────────────────────────

_SECTION_IDS = [
    "company-operations",
    "stock-market",
    "financial-health",
    "governance",
    "litigation",
    "scoring",
]

def check_section_content_quality(html: str) -> list[str]:
    """Check that each section has meaningful content (>1000 chars)."""
    issues = []
    for i, sid in enumerate(_SECTION_IDS):
        start = html.find(f'id="{sid}"')
        if start < 0:
            continue
        # Find approximate end (next section or end of document)
        end = len(html)
        for next_sid in _SECTION_IDS[i + 1:]:
            next_pos = html.find(f'id="{next_sid}"', start + 1)
            if next_pos > 0:
                end = next_pos
                break
        section_html = html[start:end]
        # Strip HTML tags for content length check
        content = re.sub(r"<[^>]+>", "", section_html)
        content = re.sub(r"\s+", " ", content).strip()
        if len(content) < 1000:
            issues.append(
                f"THIN SECTION: '{sid}' has only {len(content)} chars of text "
                f"content (minimum 1000 expected)"
            )
    return issues


# ── CHECK 11: Company Narrative Quality ──────────────────────────────

def check_company_narrative(html: str) -> list[str]:
    """Check that the company section contains company name and revenue."""
    issues = []
    co_start = html.find('id="company-operations"')
    if co_start < 0:
        return ["MISSING: Company operations section not found"]
    # Find next section
    co_end = html.find('id="stock-market"', co_start)
    if co_end < 0:
        co_end = co_start + 10000
    co_html = html[co_start:co_end]
    # Should contain revenue figure ($XXX or $X.XX)
    if not re.search(r"\$[\d,.]+\s*[BMTbmt]", co_html):
        issues.append(
            "COMPANY NARRATIVE: No dollar figure found in company section "
            "(expected revenue or market cap)"
        )
    # Should contain "Company Overview" or structured narrative heading
    if "Company Overview" not in co_html and "Company Risk Profile" not in co_html:
        issues.append(
            "COMPANY NARRATIVE: Missing 'Company Overview' or 'Company Risk Profile' "
            "heading in company section"
        )
    return issues


# ── CHECK 12: Extended Jargon ─────────────────────────────────────────

_EXTENDED_JARGON_RE = [
    (r"(?<=>)[^<]*\bthreshold:\s*", "Internal threshold reference in visible text"),
    (r"(?<=>)[^<]*\bhost risk\b", "Brain YAML risk classification jargon"),
    (r"(?<=>)[^<]*\bagent risk\b", "Brain YAML risk classification jargon"),
    (r"(?<=>)[^<]*F\.\d+ = \d+/\d+", "Factor code with score ratio in visible text"),
]


def check_extended_jargon(html: str) -> list[str]:
    """Check for extended jargon patterns in visible text (not attributes/base64)."""
    issues = []
    # Strip base64-encoded content and style/script tags to avoid false positives
    clean = re.sub(r'data:[^"]+', '', html)
    clean = re.sub(r'<style[^>]*>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<script[^>]*>.*?</script>', '', clean, flags=re.DOTALL)

    for pattern, desc in _EXTENDED_JARGON_RE:
        matches = list(re.finditer(pattern, clean))
        if matches:
            for m in matches[:2]:
                ctx = clean[max(0, m.start() - 30):m.end() + 40].replace("\n", " ")
                issues.append(f"JARGON [{desc}]: ...{ctx[:120]}...")
    return issues


# ── CHECK 13: Investigative Depth ────────────────────────────────────

def check_investigative_depth(html: str) -> list[str]:
    """Verify the worksheet contains investigative analysis, not just data display."""
    issues = []
    import re
    dollar_amounts = re.findall(r'\$[\d,.]+[BMK]', html)
    if len(dollar_amounts) < 20:
        issues.append(f"LOW DOLLAR SPECIFICITY: only {len(dollar_amounts)} formatted dollar amounts (need 20+)")
    named_individuals = len(re.findall(r'(?:CEO|CFO|COO|Chairman|Director|General Counsel)\b', html))
    if named_individuals < 5:
        issues.append(f"LOW INDIVIDUAL NAMING: only {named_individuals} officer/director title references (need 5+)")
    specific_dates = len(re.findall(r'20\d{2}-\d{2}-\d{2}', html))
    if specific_dates < 10:
        issues.append(f"LOW DATE SPECIFICITY: only {specific_dates} specific dates (need 10+)")
    do_terms = sum(html.count(t) for t in ['D&amp;O', 'D&O', 'securities class action', 'SCA', 'fiduciary', 'scienter', 'class period', 'Side A', 'settlement', 'DDL', 'statute of limitations', '10b-5', 'Section 11'])
    if do_terms < 15:
        issues.append(f"LOW D&O LANGUAGE: only {do_terms} D&O-specific term occurrences (need 15+)")
    source_citations = sum(html.count(t) for t in ['10-K Filing', '10-Q Filing', 'Proxy Statement', 'Form 4', '8-K Filing', 'Stanford SCA', 'Market Data', 'XBRL'])
    if source_citations < 10:
        issues.append(f"LOW SOURCE CITATIONS: only {source_citations} source references (need 10+)")
    return issues


def check_data_consistency(html: str) -> list[str]:
    """Check for internal data consistency within the worksheet."""
    issues = []
    import re
    scores = re.findall(r'(?:score|Score).*?(\d{2,3})\s*/\s*100', html[:50000])
    if scores:
        unique_scores = set(scores)
        if len(unique_scores) > 1:
            issues.append(f"SCORE INCONSISTENCY: multiple scores shown: {unique_scores}")
    return issues


# ── MAIN ─────────────────────────────────────────────────────────────

def run_qa(html_path: str) -> bool:
    """Run all QA checks. Returns True if all pass."""
    html = load_html(html_path)
    print(f"QA: Loaded {len(html):,} chars from uw-analysis section")
    print(f"{'=' * 60}")

    all_issues: list[str] = []
    checks = [
        ("Raw Data Leaks", check_raw_data_leaks),
        ("Section Presence & Order", check_section_presence),
        ("Content Presence", check_content_presence),
        ("N/A Density", check_na_density),
        ("Visual Integrity", check_visual_integrity),
        ("Template Variable Leaks", check_template_leaks),
        ("Truncation Errors", check_no_truncation),
        ("Semantic Mismatch", check_semantic_mismatch),
        ("Boilerplate Text", check_boilerplate_text),
        ("Section Content Quality", check_section_content_quality),
        ("Company Narrative", check_company_narrative),
        ("Extended Jargon", check_extended_jargon),
        ("Investigative Depth", check_investigative_depth),
        ("Data Consistency", check_data_consistency),
    ]

    # Tier 2 checks added after $nan and garbage table incidents.
    # These are defined later in the file but referenced here via forward lookup.
    _tier2 = [
        ("NaN/Infinity Values", "_check_nan_infinity"),
        ("Internal Code Leaks (Main Body)", "_check_internal_codes_main_body"),
        ("Duplicate Column Content", "_check_duplicate_columns"),
        ("Empty Value Cells", "_check_empty_value_cells"),
        ("Section Data Density", "_check_section_data_density"),
        ("Financial Value Bounds", "_check_financial_bounds"),
        ("Orphaned Units", "_check_orphaned_units"),
    ]
    for name, fn_name in _tier2:
        fn = globals().get(fn_name)
        if fn is not None:
            checks.append((name, fn))

    for name, fn in checks:
        issues = fn(html)
        if issues:
            print(f"\nFAIL: {name} ({len(issues)} issues)")
            for issue in issues:
                print(f"  - {issue}")
            all_issues.extend(issues)
        else:
            print(f"PASS: {name}")

    print(f"\n{'=' * 60}")
    if all_issues:
        print(f"TOTAL: {len(all_issues)} issues found")
        return False
    else:
        print("ALL CHECKS PASSED")
        return True




# ── CHECK 13: Investigative Depth ────────────────────────────────────

def check_investigative_depth(html: str) -> list[str]:
    """Verify the worksheet contains investigative analysis, not just data display.
    
    A good D&O worksheet should contain:
    - Specific dollar amounts tied to risk exposure
    - Named individuals (officers, directors) with roles
    - Specific dates (filing dates, earnings dates, court dates)
    - D&O implications explained (not just data shown)
    - Cross-references between sections (litigation → financial impact)
    """
    issues = []
    
    # Must contain specific dollar amounts (not just N/A or formatted numbers)
    import re
    dollar_amounts = re.findall(r'\$[\d,.]+[BMK]', html)
    if len(dollar_amounts) < 20:
        issues.append(f"LOW DOLLAR SPECIFICITY: only {len(dollar_amounts)} formatted dollar amounts (need 20+)")
    
    # Must contain named individuals
    # Check for common officer titles near names
    named_individuals = len(re.findall(r'(?:CEO|CFO|COO|Chairman|Director|General Counsel)\b', html))
    if named_individuals < 5:
        issues.append(f"LOW INDIVIDUAL NAMING: only {named_individuals} officer/director title references (need 5+)")
    
    # Must contain specific dates (YYYY-MM-DD or Month DD, YYYY)
    specific_dates = len(re.findall(r'20\d{2}-\d{2}-\d{2}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}', html))
    if specific_dates < 10:
        issues.append(f"LOW DATE SPECIFICITY: only {specific_dates} specific dates (need 10+)")
    
    # Must contain D&O-specific language
    do_terms = sum(html.count(t) for t in [
        'D&amp;O', 'D&O', 'securities class action', 'SCA', 'fiduciary',
        'scienter', 'class period', 'Side A', 'settlement', 'DDL',
        'statute of limitations', '10b-5', 'Section 11',
    ])
    if do_terms < 15:
        issues.append(f"LOW D&O LANGUAGE: only {do_terms} D&O-specific term occurrences (need 15+)")
    
    # Must contain source citations
    source_citations = sum(html.count(t) for t in [
        '10-K Filing', '10-Q Filing', 'Proxy Statement', 'Form 4',
        '8-K Filing', 'Stanford SCA', 'Market Data', 'XBRL',
    ])
    if source_citations < 10:
        issues.append(f"LOW SOURCE CITATIONS: only {source_citations} source references (need 10+)")
    
    return issues


# ── CHECK 14: Cross-Company Consistency ──────────────────────────────

def check_data_consistency(html: str) -> list[str]:
    """Check for internal data consistency within the worksheet."""
    issues = []
    import re
    
    # Revenue should appear consistently (same number in multiple places)
    revenue_matches = re.findall(r'\$(\d+\.?\d*)[BM].*?(?:revenue|Revenue)', html[:100000])
    if revenue_matches:
        unique_revs = set(revenue_matches[:5])
        if len(unique_revs) > 2:
            issues.append(f"REVENUE INCONSISTENCY: {len(unique_revs)} different revenue figures shown: {unique_revs}")
    
    # Score should be consistent
    scores = re.findall(r'(?:score|Score).*?(\d{2,3})\s*/\s*100', html[:50000])
    if scores:
        unique_scores = set(scores)
        if len(unique_scores) > 1:
            issues.append(f"SCORE INCONSISTENCY: multiple scores shown: {unique_scores}")
    
    return issues


# Register new checks
_EXTENDED_CHECKS = [
    ("Investigative Depth", check_investigative_depth),
    ("Data Consistency", check_data_consistency),
]

# Monkey-patch into run_qa if not already there
_original_run_qa = run_qa

# ---------------------------------------------------------------------------
# Tier 1+2 QA checks — catches $nan, garbage tables, empty data, jargon
# ---------------------------------------------------------------------------


def _check_nan_infinity(html: str) -> list[str]:
    """Check for NaN, Infinity, undefined in visible text."""
    issues: list[str] = []
    for pattern, desc in [
        (r">\s*\$?nan\b", "NaN value"),
        (r">\s*Infinity\b", "Infinity value"),
        (r"nan%", "nan percentage"),
    ]:
        matches = re.findall(pattern, html, re.IGNORECASE)
        if matches:
            issues.append(f"{desc}: {len(matches)} instances")
    return issues


def _check_internal_codes_main_body(html: str) -> list[str]:
    """Check for internal code patterns in main body (not audit appendix)."""
    issues: list[str] = []
    audit_start = html.find('id="qa-audit"')
    if audit_start < 0:
        audit_start = html.find('id="data-audit"')
    main_body = html[:audit_start] if audit_start > 0 else html

    for code in [
        "MANUAL_ONLY", "FALLBACK_ONLY", "SourcedValue", "field_key",
        "signal_id", "execution_mode", "data_strategy", "ExtractedData",
        "Management Display:", "EVALUATIVE_CHECK",
    ]:
        count = main_body.count(code)
        if count > 0:
            issues.append(f"Internal code '{code}' in main body: {count}")
    return issues


def _check_duplicate_columns(html: str) -> list[str]:
    """Check for tables where adjacent columns have identical content."""
    issues: list[str] = []
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
    dup_count = 0
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        if len(cells) >= 2:
            clean = [re.sub(r"<[^>]+>", "", c).strip() for c in cells]
            for i in range(len(clean) - 1):
                if clean[i] and clean[i + 1] and len(clean[i]) > 20 and clean[i] == clean[i + 1]:
                    dup_count += 1
    if dup_count > 0:
        issues.append(f"{dup_count} rows with identical adjacent columns (garbage table)")
    return issues


def _check_empty_value_cells(html: str) -> list[str]:
    """Check for labeled fields with missing values."""
    issues: list[str] = []
    empty = re.findall(r"<b[^>]*>[^<]+</b>\s*</(?:span|div|td)>", html)
    suspicious = [m for m in empty if any(
        kw in m.lower() for kw in ("revenue", "assets", "debt", "margin", "ratio", "score", "price")
    )]
    if len(suspicious) > 3:
        issues.append(f"{len(suspicious)} labeled fields with missing values")
    return issues


def _check_section_data_density(html: str) -> list[str]:
    """Check for sections that are mostly N/A."""
    issues: list[str] = []
    # Check tables with high N/A concentration
    tables = re.findall(r"<table[^>]*>(.*?)</table>", html, re.DOTALL)
    for i, table in enumerate(tables):
        na_count = table.count(">N/A<") + table.count(">Not mentioned<")
        cell_count = len(re.findall(r"<td", table))
        if cell_count > 5 and na_count > cell_count * 0.6:
            # Get context (nearest heading)
            issues.append(f"Table {i}: {na_count}/{cell_count} cells N/A (>60%)")
    return issues


def _check_financial_bounds(html: str) -> list[str]:
    """Check for financial values outside reasonable bounds."""
    issues: list[str] = []
    neg_rev = re.findall(r"revenue[^<]*-\$[\d,]+", html, re.IGNORECASE)
    if neg_rev:
        issues.append(f"Negative revenue: {neg_rev[0][:50]}")
    return issues


def _check_orphaned_units(html: str) -> list[str]:
    """Check for currency/percentage symbols without values."""
    issues: list[str] = []
    orphaned_dollar = re.findall(r">\s*\$\s*<", html)
    if orphaned_dollar:
        issues.append(f"{len(orphaned_dollar)} orphaned $ (no value)")
    return issues


def _enhanced_run_qa(html_path: str) -> bool:
    """Enhanced QA with investigative depth checks."""
    html = load_html(html_path)
    print(f"QA: Loaded {len(html):,} chars from uw-analysis section")
    print(f"{'=' * 60}")

    all_issues: list[str] = []
    checks = [
        ("Raw Data Leaks", check_raw_data_leaks),
        ("Section Presence & Order", check_section_presence),
        ("Content Presence", check_content_presence),
        ("N/A Density", check_na_density),
        ("Visual Integrity", check_visual_integrity),
        ("Template Variable Leaks", check_template_leaks),
        ("Truncation Errors", check_no_truncation),
        ("Semantic Mismatch", check_semantic_mismatch),
        ("Boilerplate Text", check_boilerplate_text),
        ("Section Content Quality", check_section_content_quality),
        ("Company Narrative", check_company_narrative),
        ("Extended Jargon", check_extended_jargon),
        ("Investigative Depth", check_investigative_depth),
        ("Data Consistency", check_data_consistency),
        ("NaN/Infinity Values", _check_nan_infinity),
        ("Internal Code Leaks (Main Body)", _check_internal_codes_main_body),
        ("Duplicate Column Content", _check_duplicate_columns),
        ("Empty Value Cells", _check_empty_value_cells),
        ("Section Data Density", _check_section_data_density),
        ("Financial Value Bounds", _check_financial_bounds),
        ("Orphaned Units", _check_orphaned_units),
    ]

    for name, fn in checks:
        try:
            issues = fn(html)
        except Exception as e:
            issues = [f"CHECK ERROR: {e}"]
        if issues:
            print(f"\nFAIL: {name} ({len(issues)} issues)")
            for issue in issues:
                print(f"  - {issue}")
            all_issues.extend(issues)
        else:
            print(f"PASS: {name}")

    print(f"\n{'=' * 60}")
    if all_issues:
        print(f"TOTAL: {len(all_issues)} issues found")
        return False
    else:
        print("ALL CHECKS PASSED")
        return True

run_qa = _enhanced_run_qa


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python scripts/qa_uw_analysis.py <path_to_html>")
        sys.exit(1)
    ok = run_qa(sys.argv[1])
    sys.exit(0 if ok else 1)
