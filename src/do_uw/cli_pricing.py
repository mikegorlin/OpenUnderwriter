"""CLI sub-commands for market pricing intelligence.

Provides commands for quote management and market analytics:
- `do-uw pricing add-quote` -- add a new insurance quote
- `do-uw pricing list-quotes` -- list and filter stored quotes
- `do-uw pricing market-position` -- query market position statistics
- `do-uw pricing trends` -- view market trend analysis
- `do-uw pricing import-csv` -- bulk-import quotes/programs from CSV
- `do-uw pricing programs ...` -- program management sub-commands

Registered as a Typer sub-app in cli.py.
"""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from do_uw.cli_pricing_programs import pricing_programs_app

pricing_app = typer.Typer(
    name="pricing",
    help="Market pricing intelligence",
    no_args_is_help=True,
)
pricing_app.add_typer(pricing_programs_app)
console = Console()


def _parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD string to a UTC datetime."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        msg = f"Invalid date format: {date_str!r} (expected YYYY-MM-DD)"
        raise typer.BadParameter(msg) from exc


@pricing_app.command("add-quote")
def add_quote(
    ticker: str = typer.Argument(help="Stock ticker symbol"),
    premium: float = typer.Option(..., "--premium", "-p", help="Total premium (USD)"),
    limit: float = typer.Option(..., "--limit", "-l", help="Total limit (USD)"),
    effective: str = typer.Option(
        ..., "--effective", "-e", help="Policy effective date (YYYY-MM-DD)"
    ),
    cap_tier: str = typer.Option(
        ..., "--cap-tier", help="Market cap tier: MEGA, LARGE, MID, SMALL, MICRO"
    ),
    status: str = typer.Option("QUOTED", "--status", help="Quote status"),
    retention: float | None = typer.Option(None, "--retention", help="SIR/deductible"),
    source: str = typer.Option("manual", "--source", "-s", help="Data source"),
    company_name: str | None = typer.Option(None, "--company-name", help="Company name"),
) -> None:
    """Add a new insurance quote to the pricing store."""
    from do_uw.knowledge.pricing_store import PricingStore
    from do_uw.models.pricing import MarketCapTier, QuoteInput, QuoteStatus

    ticker = ticker.upper()
    effective_dt = _parse_date(effective)
    name = company_name if company_name else ticker

    try:
        status_enum = QuoteStatus(status.upper())
    except ValueError:
        valid = ", ".join(s.value for s in QuoteStatus)
        console.print(f"[red]Invalid status: {status}[/red]\n[dim]Valid: {valid}[/dim]")
        raise typer.Exit(code=1) from None

    try:
        tier_enum = MarketCapTier(cap_tier.upper())
    except ValueError:
        valid = ", ".join(t.value for t in MarketCapTier)
        console.print(f"[red]Invalid cap tier: {cap_tier}[/red]\n[dim]Valid: {valid}[/dim]")
        raise typer.Exit(code=1) from None

    quote_input = QuoteInput(
        ticker=ticker, company_name=name, effective_date=effective_dt,
        quote_date=datetime.now(UTC), status=status_enum, total_limit=limit,
        total_premium=premium, retention=retention, market_cap_tier=tier_enum,
        source=source,
    )
    store = PricingStore()
    quote_id = store.add_quote(quote_input)
    console.print(
        f"[green]Quote #{quote_id} added for {ticker}[/green] "
        f"(premium=${premium:,.0f}, limit=${limit:,.0f})"
    )


@pricing_app.command("list-quotes")
def list_quotes(
    ticker: str | None = typer.Option(None, "--ticker", "-t", help="Filter by ticker"),
    status: str | None = typer.Option(None, "--status", help="Filter by status"),
    limit: int = typer.Option(20, "--limit", "-n", help="Maximum quotes to display"),
) -> None:
    """List stored insurance quotes with optional filters."""
    from do_uw.knowledge.pricing_store import PricingStore

    store = PricingStore()
    quotes = store.list_quotes(ticker=ticker, status=status, limit=limit)
    if not quotes:
        console.print("[dim]No quotes found.[/dim]")
        return

    table = Table(title="Insurance Quotes")
    for col, w, j in [
        ("ID", 5, "right"), ("Ticker", 8, "left"), ("Effective", 12, "left"),
        ("Status", 12, "left"), ("Premium", 14, "right"), ("Limit", 14, "right"),
        ("ROL", 8, "right"), ("Tier", 10, "left"), ("Cap Tier", 8, "left"),
    ]:
        table.add_column(col, width=w, justify=cast(Any, j))

    for q in quotes:
        table.add_row(
            str(q.id), q.ticker, q.effective_date.strftime("%Y-%m-%d"),
            q.status, f"${q.total_premium:,.0f}", f"${q.total_limit:,.0f}",
            f"{q.program_rate_on_line:.4f}", q.tier or "-", q.market_cap_tier,
        )
    console.print(table)


_CONFIDENCE_COLORS = {"HIGH": "green", "MEDIUM": "yellow", "LOW": "red", "INSUFFICIENT": "dim"}


def _fmt_rol(value: float | None) -> str:
    """Format a rate-on-line value for display."""
    return "N/A" if value is None else f"{value:.4f}"


@pricing_app.command("market-position")
def market_position(
    cap_tier: str | None = typer.Option(None, "--cap-tier", help="Market cap tier filter"),
    sector: str | None = typer.Option(None, "--sector", help="Sector filter"),
    layer: str | None = typer.Option(None, "--layer", help="Layer position filter"),
    months: int = typer.Option(24, "--months", help="Lookback window in months"),
    score_min: float | None = typer.Option(None, "--score-min", help="Min quality score"),
    score_max: float | None = typer.Option(None, "--score-max", help="Max quality score"),
) -> None:
    """Query market position statistics for a segment."""
    from do_uw.knowledge.pricing_analytics import MarketPositionEngine
    from do_uw.knowledge.pricing_store import PricingStore

    store = PricingStore()
    engine = MarketPositionEngine(store)
    score_range: tuple[float, float] | None = None
    if score_min is not None and score_max is not None:
        score_range = (score_min, score_max)

    pos = engine.get_market_position(
        market_cap_tier=cap_tier, sector=sector, layer_position=layer,
        score_range=score_range, months_back=months,
    )
    color = _CONFIDENCE_COLORS.get(pos.confidence_level, "dim")

    if pos.confidence_level == "INSUFFICIENT":
        console.print(Panel(
            f"[{color}]INSUFFICIENT DATA[/{color}]\n"
            f"Only {pos.peer_count} data points found.\n"
            "[dim]Try broader filters or increase --months.[/dim]",
            title="Market Position",
        ))
        return

    r = _fmt_rol
    mag = f" ({pos.trend_magnitude_pct:+.1f}%)" if pos.trend_magnitude_pct is not None else ""
    lines = [
        f"Confidence: [{color}]{pos.confidence_level}[/{color}] ({pos.peer_count} quotes)",
        *([] if not pos.data_window else [f"Data Window: {pos.data_window}"]),
        "", f"Median ROL: {r(pos.median_rate_on_line)}",
        f"Mean ROL:   {r(pos.mean_rate_on_line)}",
        f"95% CI:     {r(pos.ci_low)} - {r(pos.ci_high)}",
        f"IQR:        {r(pos.percentile_25)} - {r(pos.percentile_75)}",
        f"Range:      {r(pos.min_rate)} - {r(pos.max_rate)}",
        "", f"Trend: {pos.trend_direction}{mag}",
    ]
    console.print(Panel("\n".join(lines), title="Market Position"))


def _trend_style(direction: str) -> str:
    """Return Rich style for a trend direction."""
    return {"HARDENING": "red", "SOFTENING": "blue"}.get(direction, "dim")


@pricing_app.command("trends")
def trends(
    cap_tier: str | None = typer.Option(None, "--cap-tier", help="Market cap tier filter"),
    sector: str | None = typer.Option(None, "--sector", help="Sector filter"),
    layer: str | None = typer.Option(None, "--layer", help="Layer position filter"),
    months: int = typer.Option(48, "--months", help="Lookback window in months"),
) -> None:
    """View market trend analysis by period."""
    from do_uw.knowledge.pricing_analytics import MarketPositionEngine
    from do_uw.knowledge.pricing_store import PricingStore

    store = PricingStore()
    engine = MarketPositionEngine(store)
    result = engine.get_trends(
        market_cap_tier=cap_tier, sector=sector,
        layer_position=layer, months_back=months,
    )
    if not result.points:
        console.print("[dim]No trend data found.[/dim]")
        return

    table = Table(title=f"Market Trends: {result.segment_label}")
    table.add_column("Period", width=10)
    table.add_column("Count", width=8, justify="right")
    table.add_column("Median ROL", width=12, justify="right")
    table.add_column("Mean ROL", width=12, justify="right")
    for point in result.points:
        table.add_row(
            point.period, str(point.count),
            f"{point.median_rate:.4f}", f"{point.mean_rate:.4f}",
        )
    console.print(table)

    style = _trend_style(result.overall_direction)
    mag = ""
    if result.overall_magnitude_pct is not None:
        mag = f" ({result.overall_magnitude_pct:+.1f}%)"
    console.print(
        f"\nOverall: [{style}]{result.overall_direction}{mag}[/{style}] "
        f"({result.total_quotes} total quotes)"
    )


# -- CSV import --

_CSV_REQUIRED = {"ticker"}
_DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y"]


def _parse_csv_date(value: str) -> datetime:
    """Parse a date string trying multiple formats."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    msg = f"Cannot parse date: {value!r} (expected YYYY-MM-DD or MM/DD/YYYY)"
    raise ValueError(msg)


def _opt_float(row: dict[str, str], key: str) -> float | None:
    """Extract optional float from a CSV row."""
    val = row.get(key, "").strip()
    return float(val) if val else None


def _opt_str(row: dict[str, str], key: str) -> str | None:
    """Extract optional string from a CSV row."""
    val = row.get(key, "").strip()
    return val or None


def _opt_int(row: dict[str, str], key: str) -> int | None:
    """Extract optional int from a CSV row."""
    val = row.get(key, "").strip()
    return int(val) if val else None


@pricing_app.command("import-csv")
def import_csv(
    filepath: Path = typer.Argument(help="Path to CSV file"),
    source: str = typer.Option("csv_import", "--source", "-s", help="Data source tag"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate without importing"),
) -> None:
    """Bulk-import quotes or programs from a CSV file.

    Rows with premium + limit + effective_date become Quotes.
    Partial rows become Programs with whatever data is available.
    """
    from do_uw.knowledge.pricing_store import PricingStore

    if not filepath.exists():
        console.print(f"[red]File not found: {filepath}[/red]")
        raise typer.Exit(code=1)

    with open(filepath, newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            console.print("[red]CSV file is empty or has no headers.[/red]")
            raise typer.Exit(code=1)

        missing = _CSV_REQUIRED - set(reader.fieldnames)
        if missing:
            console.print(f"[red]Missing required columns: {', '.join(sorted(missing))}[/red]")
            raise typer.Exit(code=1)

        quote_store = PricingStore() if not dry_run else None
        prog_store: object | None = None
        imported = 0
        programs_created = 0
        errors = 0

        for row_num, row in enumerate(reader, start=2):
            try:
                required_keys = ("premium", "limit", "effective_date")
                has_full = all(row.get(k, "").strip() for k in required_keys)
                if has_full:
                    _csv_import_quote(row, row_num, source, dry_run, quote_store)
                    imported += 1
                else:
                    if prog_store is None and not dry_run:
                        from do_uw.knowledge.pricing_store_programs import ProgramStore
                        prog_store = ProgramStore()
                    _csv_import_program(row, row_num, source, dry_run, prog_store)
                    programs_created += 1
            except (ValueError, KeyError) as exc:
                console.print(f"[red]Row {row_num}: {exc}[/red]")
                errors += 1

    action = "validated" if dry_run else "imported"
    parts: list[str] = []
    if imported:
        parts.append(f"[green]{imported} quotes {action}[/green]")
    if programs_created:
        parts.append(f"[green]{programs_created} programs {action}[/green]")
    parts.append(f"[red]{errors} errors[/red]")
    console.print("\n" + ", ".join(parts))


def _csv_import_quote(
    row: dict[str, str], row_num: int, source: str,
    dry_run: bool, store: object | None,
) -> None:
    """Import a CSV row as a full Quote."""
    from do_uw.models.pricing import MarketCapTier, QuoteInput, QuoteStatus

    eff_dt = _parse_csv_date(row["effective_date"])
    tier = MarketCapTier(row.get("market_cap_tier", "MID").strip().upper())
    s_str = row.get("status", "QUOTED").strip().upper()
    status = QuoteStatus(s_str) if s_str else QuoteStatus.QUOTED
    qi = QuoteInput(
        ticker=row["ticker"].strip().upper(),
        company_name=row.get("company_name", row["ticker"]).strip(),
        effective_date=eff_dt, quote_date=eff_dt, status=status,
        total_limit=float(row["limit"]), total_premium=float(row["premium"]),
        retention=_opt_float(row, "retention"), market_cap_tier=tier,
        sic_code=_opt_str(row, "sic_code"), sector=_opt_str(row, "sector"),
        quality_score=_opt_float(row, "quality_score"),
        tier=_opt_str(row, "tier"), source=source,
        notes_text=_opt_str(row, "notes"),
    )
    if dry_run:
        console.print(
            f"[dim]Row {row_num}: {qi.ticker} "
            f"${qi.total_premium:,.0f} / ${qi.total_limit:,.0f}[/dim]"
        )
    else:
        store.add_quote(qi)  # type: ignore[union-attr]


def _csv_import_program(
    row: dict[str, str], row_num: int, source: str,
    dry_run: bool, prog_store: object | None,
) -> None:
    """Import a CSV row as a Program + optional PolicyYear."""
    from do_uw.models.pricing import BrokerInput, PolicyYearInput, ProgramInput

    ticker = row["ticker"].strip().upper()
    if dry_run:
        console.print(f"[dim]Row {row_num}: {ticker} (program)[/dim]")
        return

    from do_uw.knowledge.pricing_store_programs import ProgramStore
    store: ProgramStore = prog_store  # type: ignore[assignment]

    brokerage = row.get("brokerage", "").strip()
    broker: BrokerInput | None = None
    if brokerage:
        broker = BrokerInput(
            brokerage_name=brokerage, producer_name=_opt_str(row, "broker_name")
        )
    prog_input = ProgramInput(
        ticker=ticker, company_name=row.get("company_name", ticker).strip(),
        anniversary_month=_opt_int(row, "anniversary_month"),
        anniversary_day=_opt_int(row, "anniversary_day"), broker=broker,
    )
    existing = store.get_program_by_ticker(ticker)
    program_id = existing.id if existing else store.add_program(prog_input)

    if row.get("effective_date", "").strip():
        eff_dt = _parse_csv_date(row["effective_date"])
        py_input = PolicyYearInput(
            policy_year=eff_dt.year, effective_date=eff_dt,
            total_premium=_opt_float(row, "premium"), total_limit=_opt_float(row, "limit"),
            retention=_opt_float(row, "retention"), source=source,
        )
        store.add_policy_year(program_id, py_input)
