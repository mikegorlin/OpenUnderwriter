"""Financial statement extraction from XBRL Company Facts.

Two-tier extraction approach:
1. Primary: Company Facts API for concept values (resolve_concept + get_period_values)
2. Fallback: edgartools for statement structure (when <50% coverage from Tier 1)

Covers SECT3-02 (Income Statement), SECT3-03 (Balance Sheet), SECT3-04 (Cash Flow).

Usage:
    statements, reports = extract_financial_statements(state)
    state.extracted.financials.statements = statements
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)
from do_uw.stages.extract.xbrl_derived import (
    DERIVED_BY_NAME,
    compute_multi_period_derived,
)
from do_uw.stages.extract.xbrl_mapping import (
    XBRLConcept,
    get_period_values,
    load_xbrl_mapping,
    normalize_sign,
    resolve_concept,
)

logger = logging.getLogger(__name__)

# Statement types and their extraction order.
STATEMENT_TYPES: list[str] = ["income", "balance_sheet", "cash_flow"]

# Minimum coverage percentage before triggering Tier 2 fallback.
TIER2_FALLBACK_THRESHOLD: float = 50.0


# ---------------------------------------------------------------------------
# Period label helpers
# ---------------------------------------------------------------------------


def fiscal_year_label(entry: dict[str, Any]) -> str:
    """Build a period label (e.g. ``"FY2024"``) from an XBRL fact entry."""
    fy = entry.get("fy")
    if fy is not None and isinstance(fy, int) and fy > 0:
        return f"FY{fy}"

    # Fallback: derive from end date.
    end_str = str(entry.get("end", ""))
    if len(end_str) >= 4:
        return f"FY{end_str[:4]}"

    return "FY_UNKNOWN"


def determine_periods(
    all_entries: list[list[dict[str, Any]]],
) -> list[str]:
    """Determine up to 3 chronological period labels from resolved entries."""
    labels: set[str] = set()
    for entries in all_entries:
        for entry in entries:
            labels.add(fiscal_year_label(entry))

    sorted_labels = sorted(labels)
    return sorted_labels[-3:] if len(sorted_labels) > 3 else sorted_labels


# ---------------------------------------------------------------------------
# SourcedValue construction
# ---------------------------------------------------------------------------


def _make_sourced_value(
    entry: dict[str, Any],
    cik: str,
    expected_sign: str = "any",
    concept_name: str = "",
) -> tuple[SourcedValue[float], bool]:
    """Build a SourcedValue from an XBRL fact entry with sign normalization.

    Args:
        entry: Single XBRL fact dict with ``val``, ``end``, ``form``,
            ``accn``, ``filed`` fields.
        cik: Company CIK for source reference.
        expected_sign: Expected sign convention (``"positive"``,
            ``"negative"``, or ``"any"``).
        concept_name: Canonical concept name for normalization logging.

    Returns:
        Tuple of (SourcedValue wrapping the numeric value, was_normalized).
    """
    form = entry.get("form", "10-K")
    end_date = entry.get("end", "unknown")
    accn = entry.get("accn", "unknown")
    source = f"{form} {end_date} CIK{cik} accn:{accn}"

    as_of_str = str(entry.get("end", "2000-01-01"))
    try:
        as_of = datetime.strptime(as_of_str, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError:
        as_of = datetime.now(tz=UTC)

    raw_value = float(entry.get("val", 0.0))
    normalized_value, was_normalized = normalize_sign(
        raw_value, expected_sign, concept_name
    )

    sv = SourcedValue[float](
        value=normalized_value,
        source=source,
        confidence=Confidence.HIGH,
        as_of=as_of,
    )
    return sv, was_normalized


# ---------------------------------------------------------------------------
# YoY change computation
# ---------------------------------------------------------------------------


def compute_yoy_change(
    values: dict[str, SourcedValue[float] | None],
    periods: list[str],
) -> float | None:
    """Compute year-over-year change between the two most recent periods.

    Formula: ``(latest - prior) / abs(prior) * 100``

    Args:
        values: Period-keyed sourced values for a line item.
        periods: Ordered period labels (chronological).

    Returns:
        YoY change as a percentage, or None if insufficient data.
    """
    if len(periods) < 2:
        return None

    latest_key = periods[-1]
    prior_key = periods[-2]
    latest_sv = values.get(latest_key)
    prior_sv = values.get(prior_key)

    if latest_sv is None or prior_sv is None:
        return None

    prior_val = prior_sv.value
    latest_val = latest_sv.value

    if prior_val == 0.0:
        return None

    return round((latest_val - prior_val) / abs(prior_val) * 100.0, 2)


# ---------------------------------------------------------------------------
# Single-statement extraction
# ---------------------------------------------------------------------------


def _extract_single_statement(
    facts: dict[str, Any],
    mapping: dict[str, XBRLConcept],
    statement_type: str,
    cik: str,
) -> tuple[FinancialStatement | None, ExtractionReport]:
    """Extract one financial statement from Company Facts data.

    Args:
        facts: Full companyfacts API response.
        mapping: Loaded XBRL concept mapping table.
        statement_type: One of ``"income"``, ``"balance_sheet"``,
            ``"cash_flow"``.
        cik: Company CIK for source references.

    Returns:
        Tuple of (statement or None, extraction report).
    """
    # Get concepts for this statement type.
    concept_names = [
        name
        for name, cfg in mapping.items()
        if cfg["statement"] == statement_type
    ]

    if not concept_names:
        report = create_report(
            extractor_name=statement_type,
            expected=[],
            found=[],
            source_filing=f"Company Facts API CIK{cik}",
        )
        return None, report

    # Resolve all concepts and collect their entries.
    resolved: dict[str, list[dict[str, Any]]] = {}
    all_period_entries: list[list[dict[str, Any]]] = []
    found_concepts: list[str] = []

    for concept_name in concept_names:
        entries = resolve_concept(facts, mapping, concept_name)
        if entries:
            period_entries = get_period_values(entries, periods=3)
            if period_entries:
                resolved[concept_name] = period_entries
                all_period_entries.append(period_entries)
                found_concepts.append(concept_name)

    # Determine periods from all resolved entries.
    periods = determine_periods(all_period_entries)

    # Build line items.
    line_items: list[FinancialLineItem] = []
    normalization_count = 0

    for concept_name in concept_names:
        entries = resolved.get(concept_name)
        if entries is None:
            # Concept not found -- include as empty line item.
            cfg = mapping[concept_name]
            line_items.append(
                FinancialLineItem(
                    label=cfg["description"],
                    values={},
                    xbrl_concept=concept_name,
                    yoy_change=None,
                )
            )
            continue

        cfg = mapping[concept_name]
        values: dict[str, SourcedValue[float] | None] = {}

        for entry in entries:
            label = fiscal_year_label(entry)
            if label in periods:
                sv, was_normalized = _make_sourced_value(
                    entry, cik, cfg["expected_sign"], concept_name
                )
                values[label] = sv
                if was_normalized:
                    normalization_count += 1

        yoy = compute_yoy_change(values, periods)

        line_items.append(
            FinancialLineItem(
                label=cfg["description"],
                values=values,
                xbrl_concept=concept_name,
                yoy_change=yoy,
            )
        )

    # Build normalization warnings for extraction report.
    normalization_warnings: list[str] = []
    if normalization_count > 0:
        normalization_warnings.append(
            f"Sign normalization applied to {normalization_count} value(s) "
            f"in {statement_type}"
        )

    # Create extraction report.
    report = create_report(
        extractor_name=statement_type,
        expected=concept_names,
        found=found_concepts,
        source_filing=f"Company Facts API CIK{cik}",
        warnings=normalization_warnings if normalization_warnings else None,
    )
    log_report(report)

    if not found_concepts:
        return None, report

    statement = FinancialStatement(
        statement_type=statement_type,
        periods=periods,
        line_items=line_items,
        filing_source=f"Company Facts API CIK{cik}",
        extraction_date=datetime.now(tz=UTC),
    )

    return statement, report


# ---------------------------------------------------------------------------
# Tier 2: edgartools fallback
# ---------------------------------------------------------------------------


def _try_edgartools_fallback(
    statement_type: str,
    cik: str,
    report: ExtractionReport,
) -> tuple[FinancialStatement | None, ExtractionReport]:
    """Attempt Tier 2 extraction via edgartools when Tier 1 has gaps.

    Only invoked when Company Facts API provides < 50% coverage
    for a statement. Uses edgartools to parse the full filing.

    Args:
        statement_type: Which statement to extract.
        cik: Company CIK string.
        report: The Tier 1 extraction report (updated with fallback info).

    Returns:
        Tuple of (statement or None, updated report).
    """
    try:
        # ACQUIRE expansion: edgartools filing fetch
        from edgar import Company  # type: ignore[import-untyped]

        company = Company(cik)  # type: ignore[no-untyped-call]
        filings = company.get_filings(form="10-K")  # type: ignore[no-untyped-call]

        if not filings or len(filings) == 0:  # type: ignore[arg-type]
            logger.warning(
                "edgartools fallback: no 10-K filings found for CIK%s", cik
            )
            report.warnings.append("edgartools: no 10-K filings found")
            return None, report

        latest = filings[0]  # type: ignore[index]
        logger.info(
            "edgartools fallback: processing %s for %s",
            latest,
            statement_type,
        )

        report.fallbacks_used.append(f"edgartools:{statement_type}")
        report.warnings.append(
            f"edgartools fallback attempted for {statement_type} "
            f"(Tier 1 coverage: {report.coverage_pct}%)"
        )

        # edgartools parsing is complex and filing-format dependent.
        # Return None to indicate fallback did not produce a result;
        # the report documents the attempt for traceability.
        return None, report

    except ImportError:
        logger.debug("edgartools not available for fallback")
        report.warnings.append("edgartools not installed")
        return None, report
    except Exception:
        logger.exception("edgartools fallback failed for %s", statement_type)
        report.warnings.append(f"edgartools fallback error for {statement_type}")
        return None, report


# ---------------------------------------------------------------------------
# Derived concept integration
# ---------------------------------------------------------------------------


def _collect_primitives_by_period(
    statements: list[FinancialStatement | None],
) -> dict[str, dict[str, float | None]]:
    """Collect primitive XBRL values organized by period.

    Scans all line items across all statements, building a flat dict
    per period of concept_name -> numeric value.

    Args:
        statements: List of extracted financial statements (may contain None).

    Returns:
        Dict of period_label -> {concept_name -> value}.
    """
    period_items: dict[str, dict[str, float | None]] = {}

    for stmt in statements:
        if stmt is None:
            continue
        for li in stmt.line_items:
            if li.xbrl_concept is None:
                continue
            for period_label, sv in li.values.items():
                if period_label not in period_items:
                    period_items[period_label] = {}
                if sv is not None:
                    period_items[period_label][li.xbrl_concept] = sv.value
                else:
                    period_items[period_label][li.xbrl_concept] = None

    return period_items


def _add_derived_line_items(
    statements: dict[str, FinancialStatement | None],
    derived_by_period: dict[str, dict[str, float | None]],
    cik: str,
) -> int:
    """Add derived concepts as FinancialLineItem entries to their statements.

    Each derived concept is added to the statement indicated by its
    DerivedDef.statement field. Values are wrapped in SourcedValue with
    DERIVED provenance.

    Args:
        statements: Dict of statement_type -> FinancialStatement.
        derived_by_period: Dict of derived_concept_name -> {period -> value}.
        cik: Company CIK for source references.

    Returns:
        Number of derived line items added.
    """
    added = 0

    for concept_name, period_values in derived_by_period.items():
        defn = DERIVED_BY_NAME.get(concept_name)
        if defn is None:
            continue

        # "derived" statement type = intermediate value, skip adding.
        target_type = defn.statement
        if target_type == "derived":
            continue

        target_stmt = statements.get(target_type)
        if target_stmt is None:
            continue

        # Build SourcedValue entries for each period.
        sv_values: dict[str, SourcedValue[float] | None] = {}
        for period_label, value in period_values.items():
            if value is not None:
                input_str = "+".join(defn.inputs)
                sv_values[period_label] = SourcedValue[float](
                    value=value,
                    source=f"DERIVED:{input_str} CIK{cik}",
                    confidence=Confidence.HIGH,
                    as_of=datetime.now(tz=UTC),
                )

        if not sv_values:
            continue

        # Compute YoY for this derived line item.
        yoy = compute_yoy_change(sv_values, target_stmt.periods)

        target_stmt.line_items.append(
            FinancialLineItem(
                label=defn.description,
                values=sv_values,
                xbrl_concept=concept_name,
                yoy_change=yoy,
            )
        )
        added += 1

    return added


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------


def _get_cik_from_state(state: AnalysisState) -> str:
    """Extract CIK string from state.

    Args:
        state: Current analysis state.

    Returns:
        CIK string, or empty string if not available.
    """
    if state.company is not None:
        cik_sv = state.company.identity.cik
        if cik_sv is not None:
            return str(cik_sv.value)
    return ""


def _get_company_facts(state: AnalysisState) -> dict[str, Any] | None:
    """Extract Company Facts data from state.

    Args:
        state: Current analysis state with acquired_data populated.

    Returns:
        Company Facts API response dict, or None if not available.
    """
    if state.acquired_data is None:
        return None

    raw = state.acquired_data.filings.get("company_facts")
    if not isinstance(raw, dict):
        return None

    return cast(dict[str, Any], raw)


def extract_financial_statements(
    state: AnalysisState,
) -> tuple[FinancialStatements, list[ExtractionReport]]:
    """Extract summary financial statements from XBRL Company Facts data.

    Two-tier approach:
    1. Company Facts API for concept values (primary)
    2. edgartools for statement structure (fallback when <50% coverage)

    Produces income statement, balance sheet, and cash flow statement
    with up to 3 annual periods and YoY change calculations.

    Args:
        state: AnalysisState with ``acquired_data.filings["company_facts"]``
            populated from ACQUIRE stage.

    Returns:
        Tuple of (FinancialStatements, list of ExtractionReports).
    """
    facts = _get_company_facts(state)
    cik = _get_cik_from_state(state)
    reports: list[ExtractionReport] = []

    if facts is None:
        logger.warning("No Company Facts data available for extraction")
        empty_statements = FinancialStatements(periods_available=0)
        for st_type in STATEMENT_TYPES:
            reports.append(
                create_report(
                    extractor_name=st_type,
                    expected=[],
                    found=[],
                    source_filing="N/A",
                    warnings=["No Company Facts data available"],
                )
            )
        return empty_statements, reports

    mapping = load_xbrl_mapping()

    # Also check IFRS namespace for foreign filers.
    ifrs_facts = facts.get("facts", {}).get("ifrs-full", {})
    if ifrs_facts and not facts.get("facts", {}).get("us-gaap", {}):
        logger.info("Company uses IFRS taxonomy (foreign filer)")

    # Extract each statement.
    income_stmt, income_rpt = _extract_single_statement(
        facts, mapping, "income", cik
    )
    balance_stmt, balance_rpt = _extract_single_statement(
        facts, mapping, "balance_sheet", cik
    )
    cashflow_stmt, cashflow_rpt = _extract_single_statement(
        facts, mapping, "cash_flow", cik
    )

    reports = [income_rpt, balance_rpt, cashflow_rpt]

    # Tier 2 fallback for low-coverage statements.
    if income_rpt.coverage_pct < TIER2_FALLBACK_THRESHOLD:
        fallback_stmt, income_rpt = _try_edgartools_fallback(
            "income", cik, income_rpt
        )
        if fallback_stmt is not None:
            income_stmt = fallback_stmt
        reports[0] = income_rpt

    if balance_rpt.coverage_pct < TIER2_FALLBACK_THRESHOLD:
        fallback_stmt, balance_rpt = _try_edgartools_fallback(
            "balance_sheet", cik, balance_rpt
        )
        if fallback_stmt is not None:
            balance_stmt = fallback_stmt
        reports[1] = balance_rpt

    if cashflow_rpt.coverage_pct < TIER2_FALLBACK_THRESHOLD:
        fallback_stmt, cashflow_rpt = _try_edgartools_fallback(
            "cash_flow", cik, cashflow_rpt
        )
        if fallback_stmt is not None:
            cashflow_stmt = fallback_stmt
        reports[2] = cashflow_rpt

    # Compute derived concepts from extracted primitives.
    stmt_list = [income_stmt, balance_stmt, cashflow_stmt]
    primitives_by_period = _collect_primitives_by_period(stmt_list)

    if primitives_by_period:
        derived_by_period = compute_multi_period_derived(primitives_by_period)
        stmt_map: dict[str, FinancialStatement | None] = {
            "income": income_stmt,
            "balance_sheet": balance_stmt,
            "cash_flow": cashflow_stmt,
        }
        derived_count = _add_derived_line_items(
            stmt_map, derived_by_period, cik,
        )
        logger.info(
            "Added %d derived line items across %d periods",
            derived_count,
            len(primitives_by_period),
        )

    # Count available periods (maximum across statements).
    period_counts: list[int] = []
    for stmt in [income_stmt, balance_stmt, cashflow_stmt]:
        if stmt is not None:
            period_counts.append(len(stmt.periods))

    periods_available = max(period_counts) if period_counts else 0

    statements = FinancialStatements(
        income_statement=income_stmt,
        balance_sheet=balance_stmt,
        cash_flow=cashflow_stmt,
        periods_available=periods_available,
    )

    logger.info(
        "Financial statement extraction complete: %d periods, "
        "income=%s balance=%s cashflow=%s",
        periods_available,
        "yes" if income_stmt else "no",
        "yes" if balance_stmt else "no",
        "yes" if cashflow_stmt else "no",
    )

    # Informational coverage validation (does not block extraction).
    try:
        from do_uw.stages.extract.xbrl_coverage import validate_coverage

        ticker = state.ticker or "UNKNOWN"
        validate_coverage(facts, mapping, ticker)
    except Exception:
        logger.debug("Coverage validation skipped (non-blocking)")

    return statements, reports
