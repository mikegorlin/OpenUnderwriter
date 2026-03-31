"""Brain CLI commands for live learning: brain add and brain provenance.

Provides:
- ``do-uw brain add`` -- add a new check from an article/research source
- ``do-uw brain provenance`` -- show provenance chain for a specific check

Registered via import in cli_brain.py.
"""

from __future__ import annotations

import glob
import os
import subprocess
import tempfile
from datetime import date as date_type
from pathlib import Path

import typer
import yaml

from do_uw.cli_brain import brain_app, console

# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------

_VALID_DOMAINS = {"biz", "fin", "gov", "exec", "lit", "stock", "fwrd", "nlp"}


def _resolve_domain_file(domain: str, signal_id: str, checks_dir: Path) -> Path:
    """Map domain + signal_id to the target YAML file path.

    Args:
        domain: Domain prefix (biz|fin|gov|exec|lit|stock|fwrd|nlp).
        signal_id: The check ID being added (used to pick subdirectory).
        checks_dir: Root checks directory.

    Returns:
        Path to the target YAML file.
    """
    if domain == "gov":
        subprefix = signal_id.split(".")[1].lower() if "." in signal_id else "effect"
        submap = {
            "board": "board",
            "audit": "audit",
            "exec": "exec_comp",
            "activist": "activist",
            "pay": "pay",
            "rights": "rights",
            "insider": "insider",
        }
        subfile = submap.get(subprefix, "effect")
        return checks_dir / "gov" / f"{subfile}.yaml"
    elif domain == "fwrd":
        subprefix = signal_id.split(".")[1].lower() if "." in signal_id else "transform"
        submap = {
            "guid": "guidance",
            "forecast": "guidance",
            "spac": "spac",
            "merger": "spac",
            "ma": "ma",
            "acq": "ma",
        }
        subfile = submap.get(subprefix, "transform")
        return checks_dir / "fwrd" / f"{subfile}.yaml"
    elif domain == "biz":
        subprefix = signal_id.split(".")[1].lower() if "." in signal_id else "core"
        submap = {
            "model": "model",
            "dep": "dependencies",
            "depend": "dependencies",
            "comp": "competitive",
            "competitive": "competitive",
        }
        subfile = submap.get(subprefix, "core")
        return checks_dir / "biz" / f"{subfile}.yaml"
    elif domain == "fin":
        subprefix = signal_id.split(".")[1].lower() if "." in signal_id else "income"
        submap = {
            "income": "income",
            "balance": "balance",
            "cash": "balance",
            "forensic": "forensic",
            "accounting": "accounting",
            "temporal": "temporal",
        }
        subfile = submap.get(subprefix, "income")
        return checks_dir / "fin" / f"{subfile}.yaml"
    elif domain == "lit":
        subprefix = signal_id.split(".")[1].lower() if "." in signal_id else "other"
        submap = {
            "sca": "sca",
            "sec": "reg_sec",
            "reg": "reg_sec",
            "agency": "reg_agency",
            "defense": "defense",
            "history": "sca_history",
        }
        subfile = submap.get(subprefix, "other")
        return checks_dir / "lit" / f"{subfile}.yaml"
    elif domain == "stock":
        subprefix = signal_id.split(".")[1].lower() if "." in signal_id else "price"
        submap = {
            "price": "price",
            "short": "short",
            "insider": "insider",
            "ownership": "ownership",
            "pattern": "pattern",
        }
        subfile = submap.get(subprefix, "price")
        return checks_dir / "stock" / f"{subfile}.yaml"
    elif domain == "exec":
        return checks_dir / "exec" / "activity.yaml"
    else:
        # nlp and any other single-file domains
        return checks_dir / domain / f"{domain}.yaml"


# ---------------------------------------------------------------------------
# brain add
# ---------------------------------------------------------------------------


@brain_app.command("add")
def brain_add(
    domain: str = typer.Option(
        ...,
        "--domain",
        help="Domain prefix: biz|fin|gov|exec|lit|stock|fwrd|nlp",
    ),
    source: str = typer.Option(
        ...,
        "--source",
        help="URL or citation for the source article/report (REQUIRED)",
    ),
    date: str = typer.Option(
        ...,
        "--date",
        help="ISO date of source document YYYY-MM-DD (REQUIRED)",
    ),
    checks_dir: Path = typer.Option(
        Path("src/do_uw/brain/signals"),
        "--checks-dir",
        help="Root checks directory",
    ),
) -> None:
    """Add a new check from an article or research source.

    Opens an interactive YAML template in $EDITOR. Validates against the
    unified schema before saving. Runs brain build automatically after saving.

    Examples:

        uv run do-uw brain add --domain gov --source "https://example.com/study" --date "2023-11-15"

        uv run do-uw brain add --domain fin --source "Stanford SCAC Report 2023" --date "2023-11-01"
    """
    # Validate domain
    if domain not in _VALID_DOMAINS:
        typer.echo(f"ERROR: domain must be one of: {', '.join(sorted(_VALID_DOMAINS))}")
        raise typer.Exit(1)

    # Validate date format
    try:
        date_type.fromisoformat(date)
    except ValueError:
        typer.echo(f"ERROR: --date must be ISO format YYYY-MM-DD, got: {date}")
        raise typer.Exit(1)

    # YAML template pre-populated with provenance from --source and --date
    template = f"""# New check from: {source}
# Date: {date}
# Edit ALL fields below, then save and close the editor.
# Required: id, name, work_type, layer, acquisition_tier, required_data,
#           worksheet_section, display_when, provenance

id: {domain.upper()}.SUBTYPE.descriptive_name    # e.g. GOV.BOARD.insider_ratio
name: Descriptive check name
work_type: evaluate     # extract | evaluate | infer
layer: signal           # hazard | signal | peril_confirming
acquisition_tier: L2    # L1 (XBRL/filing) | L2 (filing text) | L3 (web/market) | L4 (derived)

# Risk position
factors: []             # e.g. [F9] — scoring factor IDs
peril_ids: []           # empty until causal chain linked
chain_roles: {{}}        # empty until causal chain linked
unlinked: true

# Data acquisition
required_data: []       # e.g. [SEC_PROXY, SEC_10K]
data_locations: {{}}

# Evaluation (for work_type: evaluate)
threshold:
  type: ratio
  red: ""
  yellow: ""
  clear: ""
execution_mode: AUTO
claims_correlation: 0.0
tier: 2
depth: 2

# Presentation
worksheet_section: governance   # company_profile|financial|governance|litigation|scoring|market|forward
display_when: has_data          # always|has_data|fired|critical_only
v6_subsection_ids: []
plaintiff_lenses: [SHAREHOLDERS]

# Provenance (auto-populated from --source and --date flags)
provenance:
  origin: brain_add
  confidence: low
  last_validated: null
  source_url: {source}
  source_date: {date}
  source_author: null
  added_by: null
"""

    # Write to temp file and open in $EDITOR
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(template)
        tmp_path = f.name

    editor = os.environ.get("EDITOR", "vi")
    typer.echo(f"Opening editor: {editor} {tmp_path}")
    try:
        subprocess.run([editor, tmp_path], check=True)
    except subprocess.CalledProcessError:
        typer.echo("ERROR: Editor exited with error. Aborting.")
        os.unlink(tmp_path)
        raise typer.Exit(1)
    except FileNotFoundError:
        typer.echo(f"ERROR: Editor '{editor}' not found. Set $EDITOR to a valid editor.")
        os.unlink(tmp_path)
        raise typer.Exit(1)

    # Read back the edited content
    try:
        raw_text = Path(tmp_path).read_text()
        signal_data = yaml.safe_load(raw_text)
    except yaml.YAMLError as e:
        typer.echo(f"ERROR: Invalid YAML after editing: {e}")
        typer.echo(f"[dim]Temp file preserved at: {tmp_path}[/dim]")
        raise typer.Exit(1)
    finally:
        # Clean up temp file only if YAML was parsed successfully
        if Path(tmp_path).exists() and "signal_data" in dir():
            os.unlink(tmp_path)

    if not isinstance(signal_data, dict):
        typer.echo("ERROR: YAML must be a single check object (dict), not a list.")
        raise typer.Exit(1)

    # Enforce required fields
    required_fields = [
        "id", "name", "work_type", "layer", "acquisition_tier",
        "required_data", "worksheet_section", "display_when",
    ]
    missing = [f for f in required_fields if not signal_data.get(f)]
    if missing:
        typer.echo(f"ERROR: Missing required fields: {missing}")
        raise typer.Exit(1)

    # Enforce provenance.source_url (required for brain_add origin)
    prov = signal_data.get("provenance", {})
    if not prov or not prov.get("source_url"):
        typer.echo("ERROR: provenance.source_url is required for brain add")
        raise typer.Exit(1)

    # Determine target file from domain + signal_id
    signal_id = signal_data["id"]
    target_file = _resolve_domain_file(domain, signal_id, checks_dir)
    target_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing checks in the target file
    existing: list[dict] = []
    if target_file.exists():
        existing_data = yaml.safe_load(target_file.read_text())
        if isinstance(existing_data, list):
            existing = existing_data
        elif isinstance(existing_data, dict) and "signals" in existing_data:
            existing = existing_data["signals"]

    # Check for duplicate ID
    if any(c.get("id") == signal_id for c in existing):
        typer.echo(f"ERROR: Check ID '{signal_id}' already exists in {target_file}")
        raise typer.Exit(1)

    # Append and write back
    existing.append(signal_data)
    target_file.write_text(
        yaml.dump(existing, default_flow_style=False, allow_unicode=True)
    )
    typer.echo(f"Added check '{signal_id}' to {target_file}")

    # Run brain build automatically
    typer.echo("Running brain build...")
    result = subprocess.run(
        ["uv", "run", "do-uw", "brain", "build"],
        capture_output=True,
        text=True,
    )
    if result.stdout:
        typer.echo(result.stdout.strip())
    if result.returncode != 0:
        typer.echo(f"WARNING: brain build failed:\n{result.stderr}")
    else:
        typer.echo("brain build complete — new check is active")


# ---------------------------------------------------------------------------
# brain provenance
# ---------------------------------------------------------------------------


@brain_app.command("provenance")
def brain_provenance(
    signal_id: str = typer.Argument(
        ...,
        help="Check ID to look up (e.g. GOV.BOARD.independence)",
    ),
    checks_dir: Path = typer.Option(
        Path("src/do_uw/brain/signals"),
        "--checks-dir",
        help="Root checks directory",
    ),
) -> None:
    """Show provenance chain for a specific check.

    Searches all checks/**/*.yaml files for the given check ID and displays
    its full provenance block, causal chain linkage, and peril assignments.

    Examples:

        uv run do-uw brain provenance GOV.BOARD.independence

        uv run do-uw brain provenance FIN.INCOME.revenue_concentration
    """
    found_check: dict | None = None
    found_file: str | None = None

    pattern = str(checks_dir / "**" / "*.yaml")
    for yaml_file in sorted(glob.glob(pattern, recursive=True)):
        try:
            data = yaml.safe_load(Path(yaml_file).read_text())
        except yaml.YAMLError:
            continue

        checks = data if isinstance(data, list) else data.get("signals", [])
        if not isinstance(checks, list):
            continue

        for check in checks:
            if check.get("id") == signal_id:
                found_check = check
                found_file = yaml_file
                break
        if found_check:
            break

    if not found_check or not found_file:
        typer.echo(f"Check '{signal_id}' not found in {checks_dir}/**/*.yaml")
        raise typer.Exit(1)

    prov = found_check.get("provenance") or {}

    console.print(f"\n[bold]Check:[/bold] {signal_id}")
    console.print(f"[bold]File:[/bold]  {found_file}")
    console.print(f"[bold]Name:[/bold]  {found_check.get('name', 'N/A')}")

    console.print("\n[bold]Provenance:[/bold]")
    console.print(f"  origin:          {prov.get('origin', 'unknown')}")
    console.print(f"  confidence:      {prov.get('confidence', 'unknown')}")
    console.print(f"  source_url:      {prov.get('source_url') or 'null'}")
    console.print(f"  source_date:     {prov.get('source_date') or 'null'}")
    console.print(f"  source_author:   {prov.get('source_author') or 'null'}")
    console.print(f"  last_validated:  {prov.get('last_validated') or 'null'}")
    console.print(f"  added_by:        {prov.get('added_by') or 'null'}")

    console.print("\n[bold]Risk position:[/bold]")
    console.print(f"  work_type:        {found_check.get('work_type', 'N/A')}")
    console.print(f"  layer:            {found_check.get('layer', 'N/A')}")
    console.print(f"  acquisition_tier: {found_check.get('acquisition_tier', 'N/A')}")
    console.print(f"  factors:          {found_check.get('factors') or []}")
    console.print(f"  peril_ids:        {found_check.get('peril_ids') or []}")
    console.print(f"  chain_roles:      {found_check.get('chain_roles') or {}}")
    console.print(f"  unlinked:         {found_check.get('unlinked', True)}")
