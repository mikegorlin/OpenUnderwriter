"""Post-pipeline QA verification report.

Runs automatically after pipeline completes to verify output quality
before presenting results. Checks:
1. Output file sizes (non-trivial generation)
2. Data completeness per major section
3. Extraction gap coverage
4. Hazard evidence quality (no fake evidence)
5. Key field population rates

Report formatting and printing is in qa_report_generator.py (split
for 500-line compliance).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# QA Check result types
# ---------------------------------------------------------------------------


@dataclass
class QACheck:
    """Single QA check result."""

    category: str
    name: str
    status: str  # PASS, WARN, FAIL
    detail: str
    value: str = ""


@dataclass
class QAReport:
    """Aggregated QA verification report."""

    ticker: str
    checks: list[QACheck] = field(default_factory=list)
    pass_count: int = 0
    warn_count: int = 0
    fail_count: int = 0

    @property
    def grade(self) -> str:
        if self.fail_count > 0:
            return "FAIL"
        if self.warn_count > 2:
            return "WARN"
        return "PASS"


# ---------------------------------------------------------------------------
# Output file verification
# ---------------------------------------------------------------------------


def _check_output_files(output_dir: Path) -> list[QACheck]:
    """Verify output files exist and are non-trivial."""
    checks: list[QACheck] = []
    expected = {
        "HTML": ("_worksheet.html", 50_000),
        "PDF": ("_worksheet.pdf", 20_000),
        "Word": ("_worksheet.docx", 20_000),
        "Markdown": ("_worksheet.md", 10_000),
    }

    for label, (suffix, min_bytes) in expected.items():
        files = list(output_dir.glob(f"*{suffix}"))
        if not files:
            checks.append(QACheck(
                category="Output",
                name=f"{label} file",
                status="FAIL",
                detail=f"No {suffix} file found",
            ))
            continue
        f = files[0]
        size = f.stat().st_size
        size_str = _fmt_size(size)
        if size < min_bytes:
            checks.append(QACheck(
                category="Output",
                name=f"{label} file",
                status="WARN",
                detail=f"Small file ({size_str}), expected >{_fmt_size(min_bytes)}",
                value=size_str,
            ))
        else:
            checks.append(QACheck(
                category="Output",
                name=f"{label} file",
                status="PASS",
                detail=f"{f.name}",
                value=size_str,
            ))

    # Check for chart images
    chart_dir = output_dir / "charts"
    if chart_dir.exists():
        chart_count = len(list(chart_dir.glob("*.png")))
        checks.append(QACheck(
            category="Output",
            name="Charts",
            status="PASS" if chart_count >= 3 else "WARN",
            detail=f"{chart_count} chart images",
            value=str(chart_count),
        ))

    return checks


# ---------------------------------------------------------------------------
# Data completeness
# ---------------------------------------------------------------------------


def _signal_data_completeness(state: Any) -> list[QACheck]:
    """Verify key data sections are populated."""
    checks: list[QACheck] = []

    # Company identity
    company = getattr(state, "company", None)
    if company and getattr(company, "identity", None):
        name = _sv_val(company.identity, "legal_name")
        checks.append(QACheck(
            category="Data",
            name="Company identity",
            status="PASS" if name else "FAIL",
            detail=name or "Missing company name",
            value=name or "",
        ))
    else:
        checks.append(QACheck(
            category="Data", name="Company identity",
            status="FAIL", detail="No company data",
        ))

    # Scoring
    scoring = getattr(state, "scoring", None)
    if scoring:
        score = getattr(scoring, "composite_score", None)
        tier = getattr(scoring, "tier", None)
        tier_name = getattr(tier, "name", None) if tier else None
        if score is not None:
            checks.append(QACheck(
                category="Data", name="Composite score",
                status="PASS",
                detail=f"Score {score:.1f}, Tier: {tier_name or 'N/A'}",
                value=f"{score:.1f}",
            ))
        else:
            checks.append(QACheck(
                category="Data", name="Composite score",
                status="FAIL", detail="No scoring data",
            ))
    else:
        checks.append(QACheck(
            category="Data", name="Composite score",
            status="FAIL", detail="No scoring data",
        ))

    extracted = getattr(state, "extracted", None)
    if not extracted:
        checks.append(QACheck(
            category="Data", name="Extracted data",
            status="FAIL", detail="No extracted data at all",
        ))
        return checks

    # Governance
    gov = getattr(extracted, "governance", None)
    if gov:
        execs = getattr(getattr(gov, "leadership", None), "executives", []) or []
        board = getattr(gov, "board_forensics", []) or []
        exec_tenured = sum(1 for e in execs if getattr(e, "tenure_years", None) is not None)
        checks.append(QACheck(
            category="Data", name="Governance: executives",
            status="PASS" if len(execs) >= 2 else "WARN",
            detail=f"{len(execs)} executives ({exec_tenured} with tenure)",
            value=str(len(execs)),
        ))
        board_with_quals = sum(
            1 for b in board
            if getattr(b, "qualifications", None) is not None
        )
        checks.append(QACheck(
            category="Data", name="Governance: board",
            status="PASS" if len(board) >= 3 else "WARN",
            detail=f"{len(board)} directors ({board_with_quals} with qualifications)",
            value=str(len(board)),
        ))
    else:
        checks.append(QACheck(
            category="Data", name="Governance",
            status="WARN", detail="No governance data",
        ))

    # Financials
    fin = getattr(extracted, "financials", None)
    if fin:
        distress = getattr(fin, "distress", None)
        has_altman = (
            distress and getattr(distress, "altman_z_score", None) is not None
        )
        checks.append(QACheck(
            category="Data", name="Financial: distress",
            status="PASS" if has_altman else "WARN",
            detail="Altman Z present" if has_altman else "No distress indicators",
        ))
    else:
        checks.append(QACheck(
            category="Data", name="Financials",
            status="WARN", detail="No financial data",
        ))

    # Litigation
    lit = getattr(extracted, "litigation", None)
    if lit:
        active = getattr(lit, "active_cases", []) or []
        checks.append(QACheck(
            category="Data", name="Litigation",
            status="PASS",
            detail=f"{len(active)} active case(s)",
            value=str(len(active)),
        ))
    else:
        checks.append(QACheck(
            category="Data", name="Litigation",
            status="WARN", detail="No litigation data",
        ))

    # Market
    market = getattr(extracted, "market", None)
    if market:
        stock = getattr(market, "stock", None)
        checks.append(QACheck(
            category="Data", name="Market data",
            status="PASS" if stock else "WARN",
            detail="Stock data present" if stock else "No stock data",
        ))
        # Stock price must be populated and non-zero — $0.00 renders misleadingly
        stock_price = _extract_stock_price(stock)
        if stock_price is None or stock_price == 0:
            checks.append(QACheck(
                category="Data", name="Stock price",
                status="FAIL",
                detail="Stock price is None or $0.00 — yfinance lookup likely failed (bad ticker?)",
            ))
        else:
            checks.append(QACheck(
                category="Data", name="Stock price",
                status="PASS",
                detail=f"${stock_price:,.2f}",
                value=f"{stock_price:.2f}",
            ))
    else:
        checks.append(QACheck(
            category="Data", name="Market data",
            status="WARN", detail="No market data",
        ))

    return checks


# ---------------------------------------------------------------------------
# Extraction gap coverage
# ---------------------------------------------------------------------------


def _check_extraction_gaps(state: Any) -> list[QACheck]:
    """Check extraction manifest gap coverage."""
    checks: list[QACheck] = []
    meta = getattr(state, "pipeline_metadata", {}) or {}
    gaps = meta.get("extraction_gaps")
    if not gaps:
        checks.append(QACheck(
            category="Coverage", name="Extraction manifest",
            status="WARN", detail="No extraction gap data available",
        ))
        return checks

    total = gaps.get("total_requirements", 0)
    fulfilled = gaps.get("fulfilled", 0)
    coverage = gaps.get("coverage_pct", 0.0)
    gap_count = gaps.get("gap_count", 0)

    status = "PASS" if coverage >= 60 else "WARN" if coverage >= 30 else "FAIL"
    checks.append(QACheck(
        category="Coverage", name="Brain field coverage",
        status=status,
        detail=f"{fulfilled}/{total} fields extracted ({coverage:.0f}%), {gap_count} gaps",
        value=f"{coverage:.0f}%",
    ))

    # Gaps by source
    by_source = gaps.get("gaps_by_source", {})
    if by_source:
        top_gaps = sorted(by_source.items(), key=lambda x: x[1], reverse=True)[:3]
        gap_summary = ", ".join(f"{src}: {cnt}" for src, cnt in top_gaps)
        checks.append(QACheck(
            category="Coverage", name="Top gap sources",
            status="PASS",
            detail=gap_summary,
        ))

    return checks


# ---------------------------------------------------------------------------
# Hazard evidence quality
# ---------------------------------------------------------------------------


def _check_hazard_evidence(state: Any) -> list[QACheck]:
    """Verify hazard dimension scores have real evidence, not filler."""
    checks: list[QACheck] = []

    hazard = getattr(state, "hazard_profile", None)
    if not hazard:
        checks.append(QACheck(
            category="Evidence", name="Hazard scoring",
            status="WARN", detail="No hazard profile",
        ))
        return checks

    dim_scores = getattr(hazard, "dimension_scores", []) or []
    if not dim_scores:
        checks.append(QACheck(
            category="Evidence", name="Hazard scoring",
            status="WARN", detail="No dimension scores",
        ))
        return checks

    total_dims = len(dim_scores)
    with_data = 0
    with_evidence = 0
    fake_evidence = 0

    for ds in dim_scores:
        d = ds if isinstance(ds, dict) else ds.__dict__ if hasattr(ds, "__dict__") else {}
        if d.get("data_available", False):
            with_data += 1
        evidence = d.get("evidence", [])
        if evidence:
            with_evidence += 1
            for e in evidence:
                e_lower = str(e).lower()
                if "not available" in e_lower or "no data" in e_lower:
                    fake_evidence += 1
                    break

    status = "PASS" if fake_evidence == 0 else "WARN"
    checks.append(QACheck(
        category="Evidence", name="Hazard dimensions",
        status=status,
        detail=(
            f"{total_dims} dimensions: {with_data} with data, "
            f"{with_evidence} with evidence"
            + (f", {fake_evidence} with fake evidence" if fake_evidence else "")
        ),
        value=f"{with_data}/{total_dims}",
    ))

    return checks


# ---------------------------------------------------------------------------
# Check results quality
# ---------------------------------------------------------------------------


def _check_analysis_results(state: Any) -> list[QACheck]:
    """Verify check engine results are populated."""
    checks: list[QACheck] = []
    analysis = getattr(state, "analysis", None)
    if not analysis:
        checks.append(QACheck(
            category="Analysis", name="Check results",
            status="WARN", detail="No analysis data",
        ))
        return checks

    signal_results = getattr(analysis, "signal_results", {}) or {}
    total = len(signal_results)
    triggered = sum(
        1 for r in signal_results.values()
        if getattr(r, "status", None) == "TRIGGERED"
        or (isinstance(r, dict) and r.get("status") == "TRIGGERED")
    )
    skipped = sum(
        1 for r in signal_results.values()
        if getattr(r, "status", None) == "SKIPPED"
        or (isinstance(r, dict) and r.get("status") == "SKIPPED")
    )

    checks.append(QACheck(
        category="Analysis", name="Check engine",
        status="PASS" if total > 100 else "WARN",
        detail=f"{total} checks run: {triggered} triggered, {skipped} skipped",
        value=str(total),
    ))

    return checks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_qa_verification(
    state: Any,
    output_dir: Path,
) -> QAReport:
    """Run all QA checks and produce a report.

    Args:
        state: Completed AnalysisState after pipeline run.
        output_dir: Directory containing output files.

    Returns:
        QAReport with all check results.
    """
    ticker = getattr(state, "ticker", "UNKNOWN")
    report = QAReport(ticker=ticker)

    # Run all check categories
    all_checks: list[QACheck] = []
    all_checks.extend(_check_output_files(output_dir))
    all_checks.extend(_signal_data_completeness(state))
    all_checks.extend(_check_extraction_gaps(state))
    all_checks.extend(_check_hazard_evidence(state))
    all_checks.extend(_check_analysis_results(state))

    # HTML content quality checks (SCREAMING_SNAKE, N/A, truncation, raw evidence)
    try:
        from do_uw.validation.qa_content import check_html_content
        all_checks.extend(check_html_content(output_dir, state))
    except Exception:
        logger.warning("HTML content QA failed (non-fatal)", exc_info=True)

    report.checks = all_checks
    report.pass_count = sum(1 for c in all_checks if c.status == "PASS")
    report.warn_count = sum(1 for c in all_checks if c.status == "WARN")
    report.fail_count = sum(1 for c in all_checks if c.status == "FAIL")

    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_size(n: int) -> str:
    """Format byte count as human-readable string."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}MB"
    if n >= 1_000:
        return f"{n / 1_000:.0f}KB"
    return f"{n}B"


def _extract_stock_price(stock: Any) -> float | None:
    """Extract current stock price from stock data model."""
    if stock is None:
        return None
    cp = getattr(stock, "current_price", None)
    if cp is None:
        return None
    val = getattr(cp, "value", cp)  # SourcedValue wrapper
    if val is None:
        return None
    try:
        return float(val) if float(val) > 0 else 0.0
    except (ValueError, TypeError):
        return None


def _sv_val(obj: Any, attr: str) -> str | None:
    """Extract string value from a SourcedValue attribute."""
    sv = getattr(obj, attr, None)
    if sv is None:
        return None
    val = getattr(sv, "value", None)
    if val is None:
        return None
    return str(val) if val else None


__all__ = ["QACheck", "QAReport", "run_qa_verification"]
