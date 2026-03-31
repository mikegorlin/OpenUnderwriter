"""Brain risk framework: YAML-first knowledge definitions.

Framework YAML files are the source of truth for all risk taxonomy,
peril definitions, causal chains, and factor classifications.
DuckDB tables are rebuilt from these files via ``brain build``.

Files:
    risk_model.yaml    — Framework definition (layers, dimensions)
    perils.yaml        — 8 D&O perils with HAZ code groupings
    causal_chains.yaml — ~15-20 claim pathways from trigger to loss
    taxonomy.yaml      — Pillars, layers, factors with freq/sev tags
"""
