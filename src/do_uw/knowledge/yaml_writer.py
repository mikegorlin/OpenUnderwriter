"""Round-trip YAML modification for brain signal files.

Uses ruamel.yaml to preserve comments and formatting when modifying
signal definitions. This is the ONLY module that writes to brain YAML
files -- all calibration changes flow through here.

Functions:
    build_signal_yaml_index: Scan signals/**/*.yaml, return {signal_id: yaml_path}
    modify_signal_in_yaml: Modify a signal's fields in its YAML file
    revert_yaml_change: Restore a YAML file from git (undo failed apply)
"""

from __future__ import annotations

import difflib
import logging
import subprocess
from io import StringIO
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Default signals directory
_SIGNALS_DIR = Path(__file__).parent.parent / "brain" / "signals"

# Updated header comment for calibrated files
_CALIBRATED_HEADER = (
    "# Brain signal definitions -- source of truth for brain build\n"
)


def build_signal_yaml_index(
    signals_dir: Path | None = None,
) -> dict[str, Path]:
    """Build mapping from signal_id to its YAML file path.

    Scans all YAML files in signals/**/*.yaml, loading each with
    PyYAML (read-only, fast) to extract signal IDs.

    Args:
        signals_dir: Directory containing signal YAML files.
            Defaults to src/do_uw/brain/signals/.

    Returns:
        Dict mapping signal_id -> absolute Path to its YAML file.
    """
    import yaml as pyyaml

    if signals_dir is None:
        signals_dir = _SIGNALS_DIR

    index: dict[str, Path] = {}
    for yaml_path in sorted(signals_dir.glob("**/*.yaml")):
        try:
            data = pyyaml.safe_load(yaml_path.read_text(encoding="utf-8"))
            if data is None:
                continue

            # YAML files contain a list of signal dicts
            signals = data if isinstance(data, list) else data.get("signals", [])
            for signal in signals:
                if isinstance(signal, dict) and "id" in signal:
                    index[signal["id"]] = yaml_path.resolve()
        except Exception:
            logger.warning("Failed to parse %s for index", yaml_path)

    logger.info(
        "Built signal YAML index: %d signals across %d files",
        len(index),
        len(set(index.values())),
    )
    return index


def modify_signal_in_yaml(
    yaml_path: Path,
    signal_id: str,
    changes: dict[str, Any],
) -> str:
    """Modify a signal's fields in its YAML file, preserving comments.

    Uses ruamel.yaml for round-trip editing. Only modifies the specific
    signal entry identified by signal_id.

    Args:
        yaml_path: Path to the YAML file containing the signal.
        signal_id: The signal ID to modify.
        changes: Dict of field -> new_value. Special handling:
            - "threshold" key with dict value: merges into threshold subfields
            - "lifecycle_state" key: directly sets the field
            - Other keys: set directly on the signal dict

    Returns:
        Unified diff string showing the changes made.

    Raises:
        ValueError: If signal_id not found in the YAML file.
        FileNotFoundError: If yaml_path doesn't exist.
    """
    from ruamel.yaml import YAML

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 120  # Prevent unnecessary line wrapping

    # Read original for diff
    original = yaml_path.read_text(encoding="utf-8")

    # Load with comment preservation
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.load(f)

    # Find the signal
    signals = data if isinstance(data, list) else data.get("signals", [])
    target = None
    for signal in signals:
        if isinstance(signal, dict) and signal.get("id") == signal_id:
            target = signal
            break

    if target is None:
        raise ValueError(
            f"Signal {signal_id} not found in {yaml_path}. "
            f"Available IDs: {[s.get('id') for s in signals if isinstance(s, dict)][:5]}..."
        )

    # Apply changes
    for key, value in changes.items():
        # Skip internal meta keys (prefixed with _)
        if key.startswith("_"):
            continue

        if key == "threshold" and isinstance(value, dict):
            # Merge threshold sub-fields
            if "threshold" not in target:
                target["threshold"] = {}
            for tk, tv in value.items():
                if tk.startswith("_"):
                    continue
                target["threshold"][tk] = tv
        else:
            target[key] = value

    # Write to buffer for diff comparison
    buf = StringIO()
    yaml.dump(data, buf)
    modified = buf.getvalue()

    # Update header comment if it still says "DO NOT EDIT"
    if "DO NOT EDIT" in modified:
        # Find and replace the first comment line
        lines = modified.split("\n")
        for i, line in enumerate(lines):
            if "DO NOT EDIT" in line:
                lines[i] = _CALIBRATED_HEADER.rstrip()
                break
        modified = "\n".join(lines)

    # Generate unified diff
    diff = difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{yaml_path.name}",
        tofile=f"b/{yaml_path.name}",
    )
    diff_str = "".join(diff)

    # Write to file
    yaml_path.write_text(modified, encoding="utf-8")

    logger.info("Modified signal %s in %s", signal_id, yaml_path.name)
    return diff_str


def revert_yaml_change(yaml_path: Path) -> bool:
    """Revert a YAML file to its last committed state using git checkout.

    Used when brain build fails after YAML modification, to restore
    the file to a known-good state.

    Args:
        yaml_path: Path to the YAML file to revert.

    Returns:
        True if revert succeeded, False otherwise.
    """
    try:
        subprocess.run(
            ["git", "checkout", "--", str(yaml_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Reverted %s to last committed state", yaml_path.name)
        return True
    except FileNotFoundError:
        logger.warning("git not available, cannot revert %s", yaml_path.name)
        return False
    except subprocess.CalledProcessError as exc:
        logger.warning("Failed to revert %s: %s", yaml_path.name, exc.stderr)
        return False
