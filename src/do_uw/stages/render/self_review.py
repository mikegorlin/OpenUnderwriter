"""Post-pipeline HTML self-review audit.

Reads rendered HTML output and produces a structured JSON report with
per-section quality scores. Catches issues that previously required
manual human review:

- REVIEW-01: Section count, N/A count, empty sections, boilerplate, consistency
- REVIEW-02: Per-section JSON scores (data_population, narrative_quality, visual_compliance)
- REVIEW-04: LLM refusals, HTML double-encoding, empty red flags, DDL discrepancies
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Boilerplate patterns (mirrored from formatters.py for self-review)
# ---------------------------------------------------------------------------

_BOILERPLATE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"has experienced a notable",
        r"the company has shown",
        r"demonstrates a commitment to",
        r"is positioned to",
        r"may impact future",
        r"faces potential challenges",
        r"has maintained a strong",
        r"continues to demonstrate",
        r"reflects the company's",
        r"underscores the importance",
        r"it is worth noting",
        r"it should be noted",
        r"given the current landscape",
        r"in the current environment",
        r"going forward(?![\w-])",
        r"moving forward",
        r"remains to be seen",
        r"time will tell",
        r"has shown a trend",
        r"the company has exhibited",
        r"warrants?\s+(?:further\s+)?underwriting\s+attention",
        r"warrants?\s+(?:further\s+)?investigation",
        r"historically correlated with",
        r"contributes? to the overall risk profile",
        r"moderate pullback",
        r"notable decline",
        r"elevated volatility",
        r"even moderate risk factors can generate",
        r"creates? structural complexity that elevates",
        r"at its scale.*even moderate",
        r"among the strongest predictors",
        r"attracts? institutional lead plaintiffs",
        r"has an active litigation profile",
        r"risk factors compound overall",
        r"can generate material D&O exposure",
    )
]

# LLM refusal patterns (REVIEW-04)
_LLM_REFUSAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"I (?:cannot|can't|am unable to) (?:write|generate|create|produce)",
        r"I'm not able to (?:write|generate|create|produce)",
        r"as an AI(?: language model)?",
        r"I don't have (?:access|the ability) to",
        r"I (?:cannot|can't) (?:provide|offer) (?:specific|actual)",
        r"please (?:consult|refer to|check with)",
        r"this (?:information|data) (?:is|was) not available",
        r"I (?:would|need to) (?:recommend|suggest) (?:consulting|checking)",
    )
]

# HTML double-encoding patterns (REVIEW-04)
_DOUBLE_ENCODING_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p)
    for p in (
        r"&amp;lt;",
        r"&amp;gt;",
        r"&amp;amp;",
        r"&amp;quot;",
        r"&lt;strong&gt;",
        r"&lt;em&gt;",
        r"&lt;/strong&gt;",
        r"&lt;/em&gt;",
        r"<strong><strong>",
        r"</strong></strong>",
        r"<em><em>",
        r"</em></em>",
    )
]


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SectionScore:
    """Quality score for a single HTML section."""

    section_id: str
    section_title: str
    data_population: float  # 0.0-1.0: % of expected fields populated
    narrative_quality: float  # 0.0 if boilerplate detected, 1.0 if clean
    visual_compliance: float  # 0.0-1.0: borderless tables, compact spacing
    line_count: int = 0
    na_count: int = 0
    boilerplate_matches: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


@dataclass
class ReviewFinding:
    """A specific quality issue found during review."""

    category: str  # "boilerplate", "refusal", "encoding", "red_flag", "ddl", "consistency"
    severity: str  # "error", "warning", "info"
    message: str
    location: str = ""  # section ID or element description


@dataclass
class SelfReviewReport:
    """Complete self-review audit report."""

    ticker: str
    html_file: str
    section_count: int = 0
    total_na_count: int = 0
    empty_section_count: int = 0
    boilerplate_count: int = 0
    section_scores: list[SectionScore] = field(default_factory=list)
    findings: list[ReviewFinding] = field(default_factory=list)
    overall_score: float = 0.0  # 0.0-1.0 aggregate

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dict."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @property
    def grade(self) -> str:
        """Human-readable grade."""
        if self.overall_score >= 0.9:
            return "A"
        if self.overall_score >= 0.8:
            return "B"
        if self.overall_score >= 0.7:
            return "C"
        if self.overall_score >= 0.5:
            return "D"
        return "F"

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "warning")


# ---------------------------------------------------------------------------
# HTML parsing helpers
# ---------------------------------------------------------------------------


def _parse_sections(html: str) -> list[dict[str, Any]]:
    """Extract sections from HTML by h2 tags.

    Returns list of dicts with keys: id, title, content, line_count.
    Uses regex to avoid hard dependency on BeautifulSoup for this module.
    """
    sections: list[dict[str, Any]] = []

    # Try BeautifulSoup first for better parsing
    try:
        from bs4 import BeautifulSoup, Tag

        soup = BeautifulSoup(html, "html.parser")

        # Remove script/style
        for tag in soup(["script", "style"]):
            tag.decompose()

        # Find all <section> elements or fall back to h2 splitting
        section_tags = soup.find_all("section")
        if section_tags:
            for sec in section_tags:
                if not isinstance(sec, Tag):
                    continue
                sid = sec.get("id", "")
                h2 = sec.find("h2")
                title = h2.get_text(strip=True) if h2 else str(sid)
                content = sec.get_text()
                inner_html = sec.decode_contents()
                line_count = len(inner_html.split("\n"))
                sections.append({
                    "id": str(sid),
                    "title": title,
                    "content": content,
                    "html": inner_html,
                    "line_count": line_count,
                })
        else:
            # Fall back to h2 splitting
            h2_tags = soup.find_all("h2")
            for h2 in h2_tags:
                title = h2.get_text(strip=True)
                # Collect content until next h2
                content_parts = []
                for sibling in h2.find_next_siblings():
                    if sibling.name == "h2":
                        break
                    content_parts.append(sibling.get_text())
                content = "\n".join(content_parts)
                sid = h2.get("id", title.lower().replace(" ", "-"))
                sections.append({
                    "id": str(sid),
                    "title": title,
                    "content": content,
                    "html": str(h2.find_next_sibling()),
                    "line_count": len(content.split("\n")),
                })

        return sections

    except ImportError:
        pass

    # Regex fallback (no BS4)
    h2_pattern = re.compile(r"<h2[^>]*>(.*?)</h2>", re.DOTALL)
    matches = list(h2_pattern.finditer(html))

    for i, m in enumerate(matches):
        title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(html)
        section_html = html[start:end]
        content = re.sub(r"<[^>]+>", " ", section_html)
        content = re.sub(r"\s+", " ", content).strip()
        sections.append({
            "id": title.lower().replace(" ", "-"),
            "title": title,
            "content": content,
            "html": section_html,
            "line_count": len(section_html.split("\n")),
        })

    return sections


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _count_na(text: str) -> int:
    """Count N/A occurrences in text."""
    return len(re.findall(r"\bN/A\b", text))


def _check_boilerplate(text: str) -> list[str]:
    """Find boilerplate phrases in text. Returns list of matched phrases."""
    matches: list[str] = []
    for rx in _BOILERPLATE_PATTERNS:
        for m in rx.finditer(text):
            matches.append(m.group())
    return matches


def _check_llm_refusals(html: str) -> list[ReviewFinding]:
    """REVIEW-04: Detect LLM refusal messages in output."""
    findings: list[ReviewFinding] = []
    for rx in _LLM_REFUSAL_PATTERNS:
        for m in rx.finditer(html):
            findings.append(ReviewFinding(
                category="refusal",
                severity="error",
                message=f"LLM refusal detected: '{m.group()}'",
                location=_extract_context(html, m.start()),
            ))
    return findings


def _check_double_encoding(html: str) -> list[ReviewFinding]:
    """REVIEW-04: Detect HTML double-encoding artifacts."""
    findings: list[ReviewFinding] = []
    for rx in _DOUBLE_ENCODING_PATTERNS:
        for m in rx.finditer(html):
            findings.append(ReviewFinding(
                category="encoding",
                severity="error",
                message=f"Double-encoding detected: '{m.group()}'",
                location=_extract_context(html, m.start()),
            ))
    return findings


def _check_empty_red_flags(state: Any | None) -> list[ReviewFinding]:
    """REVIEW-04: Check for empty red flag sections (triggered=false in state)."""
    findings: list[ReviewFinding] = []
    if state is None:
        return findings

    scoring = getattr(state, "scoring", None)
    if scoring is None:
        return findings

    red_flags = getattr(scoring, "red_flags", None) or []
    if not red_flags:
        # No red flags at all might be OK for low-risk companies
        return findings

    empty_flags = []
    for flag in red_flags:
        if isinstance(flag, dict):
            triggered = flag.get("triggered", False)
            name = flag.get("name", flag.get("factor", "unknown"))
        else:
            triggered = getattr(flag, "triggered", False)
            name = getattr(flag, "name", getattr(flag, "factor", "unknown"))

        if not triggered:
            empty_flags.append(str(name))

    if empty_flags:
        findings.append(ReviewFinding(
            category="red_flag",
            severity="warning",
            message=f"{len(empty_flags)} red flag(s) not triggered: {', '.join(empty_flags[:5])}",
        ))

    return findings


def _check_ddl_discrepancy(html: str, state: Any | None) -> list[ReviewFinding]:
    """REVIEW-04: Check DDL estimate consistency between narrative and scorecard."""
    findings: list[ReviewFinding] = []

    # Extract DDL values from HTML -- look for dollar amounts near DDL/dollar-loss keywords
    # Pattern 1: "$X DDL" or "$X dollar-loss"
    # Pattern 2: "DDL ... $X" or "dollar-loss ... $X" (within ~60 chars)
    ddl_patterns = [
        re.compile(r"\$([\d,.]+[BMKT]?)\s*(?:DDL|dollar[\s-]*loss)", re.IGNORECASE),
        re.compile(r"(?:DDL|dollar[\s-]*loss)[^$]{0,60}\$([\d,.]+[BMKT]?)", re.IGNORECASE),
    ]
    ddl_matches: list[str] = []
    for pat in ddl_patterns:
        for m in pat.finditer(html):
            ddl_matches.append("$" + m.group(1))

    if len(ddl_matches) < 2:
        return findings  # Not enough DDL references to compare

    # Normalize DDL values for comparison
    values: list[float] = []
    for ddl_str in ddl_matches:
        val = _parse_dollar_amount(ddl_str)
        if val is not None and val > 0:
            values.append(val)

    if len(values) < 2:
        return findings

    # Check for large discrepancies (> 3x difference)
    min_val = min(values)
    max_val = max(values)
    if min_val > 0 and max_val / min_val > 3.0:
        findings.append(ReviewFinding(
            category="ddl",
            severity="error",
            message=(
                f"DDL discrepancy: values range from "
                f"${min_val:,.0f} to ${max_val:,.0f} "
                f"({max_val / min_val:.1f}x difference)"
            ),
        ))

    # Sanity: DDL should never exceed market cap
    if state is not None:
        mc = getattr(state, "company", None)
        mc_val = None
        if mc is not None:
            mc_field = getattr(mc, "market_cap", None)
            if mc_field is not None:
                raw = getattr(mc_field, "value", mc_field)
                if isinstance(raw, (int, float)) and raw > 0:
                    mc_val = raw / 1e9  # to billions
        if mc_val is not None:
            for v in values:
                if v > mc_val:
                    findings.append(ReviewFinding(
                        category="ddl",
                        severity="error",
                        message=(
                            f"DDL ${v:,.1f}B exceeds market cap "
                            f"${mc_val:,.1f}B — impossible value"
                        ),
                    ))

    return findings


def _check_data_consistency(html: str) -> list[ReviewFinding]:
    """REVIEW-01: Check for same metric showing different values in different sections."""
    findings: list[ReviewFinding] = []

    # Check common metrics that should be consistent
    # Market cap
    mcap_pattern = re.compile(
        r"(?:market\s+cap(?:italization)?)[:\s]*\$?([\d,.]+)\s*([BMT])",
        re.IGNORECASE,
    )
    mcap_values = _extract_metric_values(mcap_pattern, html)
    if len(set(mcap_values)) > 1:
        findings.append(ReviewFinding(
            category="consistency",
            severity="warning",
            message=f"Market cap shown as multiple values: {mcap_values}",
        ))

    # Revenue
    rev_pattern = re.compile(
        r"(?:(?:total\s+)?revenue)[:\s]*\$?([\d,.]+)\s*([BMT])",
        re.IGNORECASE,
    )
    rev_values = _extract_metric_values(rev_pattern, html)
    if len(set(rev_values)) > 1:
        findings.append(ReviewFinding(
            category="consistency",
            severity="warning",
            message=f"Revenue shown as multiple values: {rev_values}",
        ))

    return findings


def _extract_metric_values(
    pattern: re.Pattern[str], html: str
) -> list[str]:
    """Extract normalized metric values from HTML for consistency check."""
    values: list[str] = []
    for m in pattern.finditer(html):
        raw_num = m.group(1).replace(",", "")
        suffix = m.group(2).upper()
        values.append(f"${raw_num}{suffix}")
    return values


def _parse_dollar_amount(s: str) -> float | None:
    """Parse a dollar string like '$513B' or '$66,000,000' to a float."""
    s = s.strip()
    # Remove non-numeric prefix
    m = re.search(r"\$([\d,.]+)\s*([BMKT])?", s, re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1).replace(",", "")
    try:
        val = float(raw)
    except ValueError:
        return None
    suffix = (m.group(2) or "").upper()
    multipliers = {"B": 1e9, "M": 1e6, "K": 1e3, "T": 1e12}
    val *= multipliers.get(suffix, 1.0)
    return val


def _extract_context(html: str, pos: int, chars: int = 60) -> str:
    """Extract surrounding text for location context."""
    start = max(0, pos - chars)
    end = min(len(html), pos + chars)
    snippet = html[start:end]
    # Strip tags for readability
    snippet = re.sub(r"<[^>]+>", "", snippet).strip()
    return snippet[:120]


def _check_visual_compliance(section_html: str) -> float:
    """Score visual compliance for a section (0.0-1.0).

    Checks for:
    - Borderless tables (no border attrs or border-style in inline styles)
    - Compact spacing (no excessive padding/margins)
    """
    score = 1.0

    # Check for old-style bordered tables
    if re.search(r'border=["\']?[1-9]', section_html):
        score -= 0.5
    if re.search(r"border-style:\s*solid", section_html, re.IGNORECASE):
        score -= 0.3
    if re.search(r'cellpadding=["\']?[5-9]', section_html):
        score -= 0.2

    return max(0.0, score)


# ---------------------------------------------------------------------------
# Main review function
# ---------------------------------------------------------------------------


def run_self_review(
    html_path: Path,
    state: Any | None = None,
) -> SelfReviewReport:
    """Run comprehensive self-review on rendered HTML output.

    Args:
        html_path: Path to the rendered HTML worksheet file.
        state: Optional AnalysisState for cross-referencing state data.

    Returns:
        SelfReviewReport with all findings and per-section scores.
    """
    html = html_path.read_text(encoding="utf-8")
    report = SelfReviewReport(
        ticker=_extract_ticker(html_path),
        html_file=str(html_path),
    )

    # Parse sections
    sections = _parse_sections(html)
    report.section_count = len(sections)

    # Score each section
    total_na = 0
    total_boilerplate = 0
    empty_count = 0

    for sec in sections:
        content = sec["content"]
        na_count = _count_na(content)
        total_na += na_count

        boilerplate_matches = _check_boilerplate(content)
        total_boilerplate += len(boilerplate_matches)

        line_count = sec["line_count"]
        is_empty = line_count < 10

        if is_empty:
            empty_count += 1

        # Calculate data_population: ratio of non-N/A content
        # Heuristic: count "N/A" vs total substantive tokens
        tokens = content.split()
        na_tokens = na_count
        substantive = max(len(tokens) - na_tokens, 0)
        data_pop = substantive / max(len(tokens), 1)

        # narrative_quality: 0 if boilerplate, 1 if clean
        narr_quality = 0.0 if boilerplate_matches else 1.0

        # visual_compliance
        vis_compliance = _check_visual_compliance(sec.get("html", ""))

        section_score = SectionScore(
            section_id=sec["id"],
            section_title=sec["title"],
            data_population=round(data_pop, 3),
            narrative_quality=narr_quality,
            visual_compliance=round(vis_compliance, 3),
            line_count=line_count,
            na_count=na_count,
            boilerplate_matches=boilerplate_matches,
            issues=[],
        )

        if is_empty:
            section_score.issues.append("Section has fewer than 10 lines of content")

        report.section_scores.append(section_score)

    report.total_na_count = total_na
    report.boilerplate_count = total_boilerplate
    report.empty_section_count = empty_count

    # Run specific checks (REVIEW-04)
    report.findings.extend(_check_llm_refusals(html))
    report.findings.extend(_check_double_encoding(html))
    report.findings.extend(_check_empty_red_flags(state))
    report.findings.extend(_check_ddl_discrepancy(html, state))
    report.findings.extend(_check_data_consistency(html))

    # Calculate overall score
    report.overall_score = _calculate_overall_score(report)

    return report


def _extract_ticker(html_path: Path) -> str:
    """Extract ticker from filename like 'AAPL_worksheet.html'."""
    name = html_path.stem
    parts = name.split("_")
    return parts[0] if parts else "UNKNOWN"


def _calculate_overall_score(report: SelfReviewReport) -> float:
    """Calculate aggregate quality score from section scores and findings."""
    if not report.section_scores:
        return 0.0

    # Average section scores
    avg_data = sum(s.data_population for s in report.section_scores) / len(report.section_scores)
    avg_narr = sum(s.narrative_quality for s in report.section_scores) / len(report.section_scores)
    avg_vis = sum(s.visual_compliance for s in report.section_scores) / len(report.section_scores)

    # Weighted average: data 40%, narrative 30%, visual 30%
    base_score = avg_data * 0.4 + avg_narr * 0.3 + avg_vis * 0.3

    # Penalties for findings
    error_penalty = report.error_count * 0.05
    warning_penalty = report.warning_count * 0.02

    # Penalty for empty sections
    if report.section_count > 0:
        empty_penalty = (report.empty_section_count / report.section_count) * 0.2
    else:
        empty_penalty = 0.2

    final = max(0.0, min(1.0, base_score - error_penalty - warning_penalty - empty_penalty))
    return round(final, 3)


# ---------------------------------------------------------------------------
# JSON report writer
# ---------------------------------------------------------------------------


def write_review_report(report: SelfReviewReport, output_dir: Path) -> Path:
    """Write self-review report as JSON file.

    Args:
        report: Completed review report.
        output_dir: Directory to write report into.

    Returns:
        Path to the written JSON file.
    """
    report_path = output_dir / f"{report.ticker}_review.json"
    report_path.write_text(report.to_json(), encoding="utf-8")
    logger.info("Self-review report written to %s", report_path)
    return report_path


# ---------------------------------------------------------------------------
# Console summary printer
# ---------------------------------------------------------------------------


def print_review_summary(report: SelfReviewReport) -> None:
    """Print human-readable review summary to console using Rich."""
    try:
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        # Fallback plain text
        _print_plain_summary(report)
        return

    console = Console()
    console.print()
    console.print(
        f"[bold]Self-Review: {report.ticker}[/bold]  "
        f"Grade: [bold]{report.grade}[/bold] ({report.overall_score:.0%})"
    )
    console.print()

    # Summary stats
    console.print(f"  Sections: {report.section_count}")
    console.print(f"  N/A count: {report.total_na_count}")
    console.print(f"  Empty sections: {report.empty_section_count}")
    console.print(f"  Boilerplate phrases: {report.boilerplate_count}")
    console.print(f"  Errors: {report.error_count}")
    console.print(f"  Warnings: {report.warning_count}")

    # Findings
    if report.findings:
        console.print()
        table = Table(title="Findings", show_header=True, header_style="bold")
        table.add_column("Severity", width=8)
        table.add_column("Category", width=12)
        table.add_column("Message")

        for f in report.findings:
            style = "red" if f.severity == "error" else "yellow" if f.severity == "warning" else "dim"
            table.add_row(
                f"[{style}]{f.severity.upper()}[/{style}]",
                f.category,
                f.message,
            )
        console.print(table)

    # Low-scoring sections
    low_sections = [
        s for s in report.section_scores
        if s.data_population < 0.5 or s.narrative_quality < 1.0 or s.visual_compliance < 0.8
    ]
    if low_sections:
        console.print()
        table = Table(title="Sections Needing Attention", show_header=True, header_style="bold")
        table.add_column("Section", min_width=20)
        table.add_column("Data", width=6, justify="right")
        table.add_column("Narr", width=6, justify="right")
        table.add_column("Vis", width=6, justify="right")
        table.add_column("Issues")

        for s in low_sections[:10]:
            issues_str = "; ".join(s.issues + s.boilerplate_matches)
            table.add_row(
                s.section_title[:30],
                f"{s.data_population:.0%}",
                f"{s.narrative_quality:.0%}",
                f"{s.visual_compliance:.0%}",
                issues_str[:60] if issues_str else "",
            )
        console.print(table)

    console.print()


def _print_plain_summary(report: SelfReviewReport) -> None:
    """Plain text fallback when Rich is not available."""
    print(f"\nSelf-Review: {report.ticker}  Grade: {report.grade} ({report.overall_score:.0%})")
    print(f"  Sections: {report.section_count}")
    print(f"  N/A count: {report.total_na_count}")
    print(f"  Empty sections: {report.empty_section_count}")
    print(f"  Boilerplate: {report.boilerplate_count}")
    print(f"  Errors: {report.error_count}, Warnings: {report.warning_count}")
    for f in report.findings:
        print(f"  [{f.severity.upper()}] {f.category}: {f.message}")
    print()


__all__ = [
    "SectionScore",
    "ReviewFinding",
    "SelfReviewReport",
    "run_self_review",
    "write_review_report",
    "print_review_summary",
]
