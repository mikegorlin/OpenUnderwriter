"""Legacy migration modules — emergency rollback only.

These modules were the original JSON-to-DuckDB migration path.
They are preserved here for emergency rollback but must NOT be
called in normal operation. brain.duckdb is rebuilt from YAML via
`angry-dolphin brain build`.

Normal callers: brain_loader.py (initial population only),
cli_brain.py (brain build command), cli_brain_ext.py (legacy migrate command).
"""
