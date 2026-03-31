"""CLI sub-commands for D&O program management.

Provides commands for program, policy year, broker, and document management:
- `do-uw pricing programs add-program` -- create a new D&O program
- `do-uw pricing programs list-programs` -- list programs with filters
- `do-uw pricing programs program-history` -- year-over-year program evolution
- `do-uw pricing programs add-policy-year` -- add a policy year to a program
- `do-uw pricing programs brokers` -- list broker contacts
- `do-uw pricing programs ingest` -- ingest a document into pricing database

Registered as a Typer sub-app via cli_pricing.py.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

pricing_programs_app = typer.Typer(
    name="programs",
    help="D&O program management",
    no_args_is_help=True,
)
console = Console()


@pricing_programs_app.command("add-program")
def add_program(
    ticker: str = typer.Argument(help="Stock ticker symbol"),
    company_name: str | None = typer.Option(
        None, "--company-name", help="Company name"
    ),
    anniversary_month: int | None = typer.Option(
        None, "--anniversary-month", help="Anniversary month (1-12)"
    ),
    anniversary_day: int | None = typer.Option(
        None, "--anniversary-day", help="Anniversary day (1-31)"
    ),
    brokerage: str | None = typer.Option(
        None, "--brokerage", help="Brokerage firm name"
    ),
    broker_name: str | None = typer.Option(
        None, "--broker-name", help="Individual broker/producer name"
    ),
    broker_email: str | None = typer.Option(
        None, "--broker-email", help="Broker email address"
    ),
    broker_phone: str | None = typer.Option(
        None, "--broker-phone", help="Broker phone number"
    ),
    notes: str | None = typer.Option(
        None, "--notes", help="Free-form notes"
    ),
) -> None:
    """Create a new D&O insurance program."""
    from do_uw.knowledge.pricing_store_programs import ProgramStore
    from do_uw.models.pricing import BrokerInput, ProgramInput

    ticker = ticker.upper()

    broker_input: BrokerInput | None = None
    if brokerage:
        broker_input = BrokerInput(
            brokerage_name=brokerage,
            producer_name=broker_name,
            email=broker_email,
            phone=broker_phone,
        )

    program_input = ProgramInput(
        ticker=ticker,
        company_name=company_name,
        anniversary_month=anniversary_month,
        anniversary_day=anniversary_day,
        broker=broker_input,
        notes_text=notes,
    )

    store = ProgramStore(db_path=None)
    program_id = store.add_program(program_input)
    console.print(
        f"[green]Program #{program_id} created for {ticker}[/green]"
    )


@pricing_programs_app.command("list-programs")
def list_programs(
    ticker: str | None = typer.Option(
        None, "--ticker", "-t", help="Filter by ticker"
    ),
    limit: int = typer.Option(
        20, "--limit", "-n", help="Maximum programs to display"
    ),
) -> None:
    """List D&O insurance programs."""
    from do_uw.knowledge.pricing_store_programs import ProgramStore

    store = ProgramStore()
    programs = store.list_programs(ticker=ticker, limit=limit)

    if not programs:
        console.print("[dim]No programs found.[/dim]")
        return

    table = Table(title="D&O Insurance Programs")
    table.add_column("ID", width=5, justify="right")
    table.add_column("Ticker", width=8)
    table.add_column("Company", width=20)
    table.add_column("Anniversary", width=12)
    table.add_column("Broker", width=15)
    table.add_column("Policy Years", width=12, justify="right")

    for p in programs:
        anniv = "-"
        if p.anniversary_month and p.anniversary_day:
            anniv = f"{p.anniversary_month:02d}/{p.anniversary_day:02d}"
        broker_str = p.broker.brokerage_name if p.broker else "-"
        py_count = str(len(p.policy_years))

        table.add_row(
            str(p.id),
            p.ticker,
            p.company_name or "-",
            anniv,
            broker_str,
            py_count,
        )

    console.print(table)


@pricing_programs_app.command("program-history")
def program_history(
    ticker: str = typer.Argument(help="Stock ticker symbol"),
) -> None:
    """Show year-over-year program evolution."""
    from do_uw.knowledge.pricing_analytics_trends import (
        compute_yoy_changes,
        detect_carrier_rotations,
    )
    from do_uw.knowledge.pricing_store_programs import ProgramStore

    ticker = ticker.upper()
    store = ProgramStore()
    history = store.get_program_history(ticker)

    if not history:
        console.print(
            f"[dim]No program history found for {ticker}.[/dim]"
        )
        return

    # Main history table
    table = Table(title=f"Program History: {ticker}")
    table.add_column("Year", width=6, justify="right")
    table.add_column("Effective", width=12)
    table.add_column("Status", width=10)
    table.add_column("Limit", width=14, justify="right")
    table.add_column("Premium", width=14, justify="right")
    table.add_column("ROL", width=8, justify="right")
    table.add_column("Retention", width=14, justify="right")
    table.add_column("Completeness", width=12)
    table.add_column("Layers", width=6, justify="right")

    for py in history:
        eff_str = (
            py.effective_date.strftime("%Y-%m-%d")
            if py.effective_date
            else "-"
        )
        limit_str = (
            f"${py.total_limit:,.0f}" if py.total_limit else "-"
        )
        prem_str = (
            f"${py.total_premium:,.0f}" if py.total_premium else "-"
        )
        rol_str = (
            f"{py.program_rate_on_line:.4f}"
            if py.program_rate_on_line
            else "-"
        )
        ret_str = (
            f"${py.retention:,.0f}" if py.retention else "-"
        )

        table.add_row(
            str(py.policy_year),
            eff_str,
            py.status,
            limit_str,
            prem_str,
            rol_str,
            ret_str,
            py.data_completeness,
            str(len(py.layers)),
        )

    console.print(table)

    # Convert to dicts for YoY analysis
    py_dicts = [
        {
            "policy_year": py.policy_year,
            "total_premium": py.total_premium,
            "total_limit": py.total_limit,
            "retention": py.retention,
            "program_rate_on_line": py.program_rate_on_line,
            "layers": [
                {"carrier_name": layer.carrier_name}
                for layer in py.layers
            ],
        }
        for py in history
    ]

    # YoY changes
    changes = compute_yoy_changes(py_dicts)
    if changes:
        console.print("\n[bold]Year-over-Year Changes[/bold]")
        for c in changes:
            parts: list[str] = []
            parts.append(
                f"  {c['from_year']} -> {c['to_year']}:"
            )
            if c["premium_change_pct"] is not None:
                parts.append(
                    f"  Premium: {c['premium_change_pct']:+.1f}%"
                )
            if c["limit_change_pct"] is not None:
                parts.append(
                    f"  Limit: {c['limit_change_pct']:+.1f}%"
                )
            if c["retention_change_pct"] is not None:
                parts.append(
                    f"  Retention: {c['retention_change_pct']:+.1f}%"
                )
            if c["rol_change_pct"] is not None:
                parts.append(
                    f"  ROL: {c['rol_change_pct']:+.1f}%"
                )
            console.print("\n".join(parts))

    # Carrier rotations
    rotations = detect_carrier_rotations(py_dicts)
    if rotations:
        console.print("\n[bold]Carrier Rotations[/bold]")
        for r in rotations:
            if r["carriers_in"]:
                console.print(
                    f"  {r['year']}: "
                    f"[green]+{', '.join(r['carriers_in'])}[/green]"
                )
            if r["carriers_out"]:
                console.print(
                    f"  {r['year']}: "
                    f"[red]-{', '.join(r['carriers_out'])}[/red]"
                )


@pricing_programs_app.command("add-policy-year")
def add_policy_year(
    ticker: str = typer.Argument(help="Stock ticker symbol"),
    year: int = typer.Argument(help="Policy year (e.g. 2025)"),
    premium: float | None = typer.Option(
        None, "--premium", help="Total program premium (USD)"
    ),
    limit: float | None = typer.Option(
        None, "--limit", help="Total program limit (USD)"
    ),
    retention: float | None = typer.Option(
        None, "--retention", help="SIR/deductible (USD)"
    ),
    status: str = typer.Option(
        "QUOTED", "--status", help="Quote status"
    ),
    effective: str | None = typer.Option(
        None, "--effective", help="Effective date (YYYY-MM-DD)"
    ),
) -> None:
    """Add a policy year to a D&O program."""
    from datetime import UTC, datetime

    from do_uw.knowledge.pricing_store_programs import ProgramStore
    from do_uw.models.pricing import (
        PolicyYearInput,
        ProgramInput,
        QuoteStatus,
    )

    ticker = ticker.upper()
    store = ProgramStore()

    # Find or create program
    program = store.get_program_by_ticker(ticker)
    if program is None:
        prog_input = ProgramInput(ticker=ticker)
        program_id = store.add_program(prog_input)
        console.print(
            f"[dim]Created new program for {ticker}[/dim]"
        )
    else:
        program_id = program.id

    effective_dt: datetime | None = None
    if effective:
        try:
            effective_dt = datetime.strptime(
                effective, "%Y-%m-%d"
            ).replace(tzinfo=UTC)
        except ValueError:
            console.print(
                f"[red]Invalid date: {effective} "
                f"(expected YYYY-MM-DD)[/red]"
            )
            raise typer.Exit(code=1) from None

    try:
        status_enum = QuoteStatus(status.upper())
    except ValueError:
        valid = ", ".join(s.value for s in QuoteStatus)
        console.print(
            f"[red]Invalid status: {status}[/red]\n"
            f"[dim]Valid: {valid}[/dim]"
        )
        raise typer.Exit(code=1) from None

    py_input = PolicyYearInput(
        policy_year=year,
        effective_date=effective_dt,
        total_premium=premium,
        total_limit=limit,
        retention=retention,
        status=status_enum,
    )

    store.add_policy_year(program_id, py_input)
    console.print(
        f"[green]Policy year {year} added to "
        f"{ticker} program[/green]"
    )


@pricing_programs_app.command("brokers")
def brokers(
    brokerage: str | None = typer.Option(
        None, "--brokerage", help="Filter by brokerage name"
    ),
) -> None:
    """List brokers in the pricing database."""
    from do_uw.knowledge.pricing_store_programs import ProgramStore

    store = ProgramStore()
    broker_list = store.list_brokers(brokerage_name=brokerage)

    if not broker_list:
        console.print("[dim]No brokers found.[/dim]")
        return

    table = Table(title="Brokers")
    table.add_column("ID", width=5, justify="right")
    table.add_column("Brokerage", width=20)
    table.add_column("Producer", width=20)
    table.add_column("Email", width=25)
    table.add_column("Phone", width=15)

    for b in broker_list:
        table.add_row(
            str(b.id),
            b.brokerage_name,
            b.producer_name or "-",
            b.email or "-",
            b.phone or "-",
        )

    console.print(table)


@pricing_programs_app.command("ingest")
def ingest(
    filepath: Path = typer.Argument(
        help="Path to document file"
    ),
    ticker: str = typer.Argument(help="Stock ticker symbol"),
    hint: str | None = typer.Option(
        None,
        "--hint",
        help="Document type hint (e.g. 'tower spreadsheet')",
    ),
) -> None:
    """Ingest a document into the pricing database."""
    ticker = ticker.upper()

    if not filepath.exists():
        console.print(
            f"[red]File not found: {filepath}[/red]"
        )
        raise typer.Exit(code=1)

    try:
        from do_uw.knowledge.pricing_ingestion import (
            ingest_document,
        )
    except ImportError:
        console.print(
            "[red]Pricing ingestion module not available.[/red]\n"
            "[dim]Install required dependencies or check "
            "pricing_ingestion.py exists.[/dim]"
        )
        raise typer.Exit(code=1) from None

    try:
        from do_uw.knowledge.pricing_store_programs import (
            ProgramStore,
        )

        store = ProgramStore()
        result = ingest_document(
            filepath=filepath,
            ticker=ticker,
            store=store,
            hint=hint,
        )
        console.print(
            f"[green]Ingested {filepath.name} for "
            f"{ticker}[/green]"
        )
        if result.get("layers"):
            console.print(
                f"  Layers extracted: {result['layers']}"
            )
        if result.get("completeness"):
            console.print(
                f"  Completeness: {result['completeness']}"
            )
    except RuntimeError as exc:
        console.print(f"[red]Ingestion error: {exc}[/red]")
        console.print(
            "[dim]Check API keys and file format.[/dim]"
        )
        raise typer.Exit(code=1) from None
