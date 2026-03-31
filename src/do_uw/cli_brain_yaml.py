"""Brain CLI commands for YAML schema validation and unlinked-check discovery.

Provides:
- ``do-uw brain validate`` -- validate all checks/**/*.yaml against unified schema
- ``do-uw brain unlinked`` -- list all checks with unlinked: true

Registered via import in cli_brain.py.
"""

from __future__ import annotations

import glob
from pathlib import Path

import typer

from do_uw.cli_brain import brain_app, console

# ---------------------------------------------------------------------------
# Required fields and valid enum values per the unified YAML schema
# (src/do_uw/brain/SCHEMA.md)
# ---------------------------------------------------------------------------

_REQUIRED_FIELDS = [
    "id",
    "name",
    "work_type",
    "layer",
    "acquisition_tier",
    "required_data",
    "worksheet_section",
    "display_when",
    "provenance",
]

_VALID_WORK_TYPES = {"extract", "evaluate", "infer"}
_VALID_LAYERS = {"hazard", "signal", "peril_confirming"}
_VALID_TIERS = {"L1", "L2", "L3", "L4"}

# Fields from the old schema that are now deprecated
_DEPRECATED_FIELDS = {"pillar", "category", "signal_type", "hazard_or_signal", "content_type"}


# ---------------------------------------------------------------------------
# brain validate
# ---------------------------------------------------------------------------


@brain_app.command("validate")
def brain_validate(
    checks_dir: Path = typer.Option(
        Path("src/do_uw/brain/signals"),
        "--checks-dir",
        help="Directory containing checks/**/*.yaml files",
    ),
) -> None:
    """Validate all checks YAML files against the unified schema."""
    import yaml

    errors: list[str] = []
    warnings: list[str] = []
    total = 0

    pattern = str(checks_dir / "**" / "*.yaml")
    yaml_files = sorted(glob.glob(pattern, recursive=True))

    if not yaml_files:
        console.print(f"[yellow]No YAML files found in {checks_dir}[/yellow]")
        raise typer.Exit(1)

    for yaml_file in yaml_files:
        data = yaml.safe_load(Path(yaml_file).read_text())
        checks = data if isinstance(data, list) else data.get("signals", [])

        for check in checks:
            total += 1
            cid = check.get("id", "UNKNOWN")
            short = Path(yaml_file).name

            # Validate required fields
            for field in _REQUIRED_FIELDS:
                if field not in check or check[field] is None:
                    errors.append(f"{short}: {cid}: missing required field '{field}'")

            # Validate enum values (only if present, to avoid double-reporting)
            wt = check.get("work_type")
            if wt is not None and wt not in _VALID_WORK_TYPES:
                errors.append(f"{short}: {cid}: invalid work_type '{wt}'")

            layer = check.get("layer")
            if layer is not None and layer not in _VALID_LAYERS:
                errors.append(f"{short}: {cid}: invalid layer '{layer}'")

            tier = check.get("acquisition_tier")
            if tier is not None and tier not in _VALID_TIERS:
                errors.append(f"{short}: {cid}: invalid acquisition_tier '{tier}'")

            # Warn on deprecated fields still present
            for dep in _DEPRECATED_FIELDS:
                if dep in check:
                    warnings.append(f"{short}: {cid}: deprecated field '{dep}' still present")

    # Print summary
    if errors:
        console.print(
            f"[bold red]VALIDATION FAILED:[/bold red] "
            f"{len(errors)} errors, {total} checks checked"
        )
        for e in errors[:20]:
            console.print(f"  [red]ERROR:[/red] {e}")
        if len(errors) > 20:
            console.print(f"  [dim]... and {len(errors) - 20} more errors[/dim]")
        raise typer.Exit(1)
    else:
        console.print(
            f"[bold green]VALIDATION PASSED:[/bold green] "
            f"{total} checks valid, {len(warnings)} warnings"
        )
        for w in warnings[:10]:
            console.print(f"  [yellow]WARN:[/yellow] {w}")
        if len(warnings) > 10:
            console.print(f"  [dim]... and {len(warnings) - 10} more warnings[/dim]")


# ---------------------------------------------------------------------------
# brain unlinked
# ---------------------------------------------------------------------------


@brain_app.command("unlinked")
def brain_unlinked(
    checks_dir: Path = typer.Option(
        Path("src/do_uw/brain/signals"),
        "--checks-dir",
        help="Directory containing checks/**/*.yaml files",
    ),
    domain: str | None = typer.Option(
        None,
        "--domain",
        help="Filter by domain prefix (e.g. GOV, FIN, BIZ)",
    ),
) -> None:
    """List all checks with unlinked: true (no causal chain assignment)."""
    import yaml

    unlinked_checks: list[dict] = []
    pattern = str(checks_dir / "**" / "*.yaml")
    yaml_files = sorted(glob.glob(pattern, recursive=True))

    if not yaml_files:
        console.print(f"[yellow]No YAML files found in {checks_dir}[/yellow]")
        raise typer.Exit(1)

    for yaml_file in yaml_files:
        data = yaml.safe_load(Path(yaml_file).read_text())
        checks = data if isinstance(data, list) else data.get("signals", [])
        for check in checks:
            if check.get("unlinked", False):
                signal_id = check.get("id", "")
                if domain is None or signal_id.startswith(domain):
                    unlinked_checks.append(check)

    filter_note = f" (domain={domain})" if domain else ""
    console.print(f"Unlinked checks: {len(unlinked_checks)}{filter_note}")
    for c in unlinked_checks:
        cid = c.get("id", "UNKNOWN")
        name = c.get("name", "")[:60]
        console.print(f"  {cid:<40s}  {name}")
