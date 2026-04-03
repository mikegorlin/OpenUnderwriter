"""Brain Analyzer MCP Server.

Read-only analysis of brain YAML signals. Provides metrics, validation,
and coverage reporting without modifying the brain.

Environment variables:
    BRAIN_ROOT: Path to brain directory (default: src/do_uw/brain)
    BRAIN_ANALYZER_CACHE: Whether to cache loaded signals (default: true)
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Optional
import json

import yaml
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
from mcp.types import Tool, TextContent

# Import brain signal schema from the project
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from do_uw.brain.brain_signal_schema import BrainSignalEntry


class BrainAnalyzer:
    """Loads and analyzes brain YAML signals."""

    def __init__(self, brain_root: Optional[Path] = None):
        self.brain_root = brain_root or Path("src/do_uw/brain")
        self.signals: list[BrainSignalEntry] = []
        self._load_signals()

    def _load_signals(self) -> None:
        """Load all signal YAML files."""
        signals_dir = self.brain_root / "signals"
        if not signals_dir.exists():
            raise ValueError(f"Signals directory not found: {signals_dir}")

        signals = []
        for yaml_file in signals_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data is None:
                        continue
                    for item in data:
                        try:
                            signal = BrainSignalEntry.model_validate(item)
                            signals.append(signal)
                        except Exception as e:
                            print(
                                f"Warning: Skipping invalid signal in {yaml_file}: {e}",
                                file=sys.stderr,
                            )
            except Exception as e:
                print(f"Warning: Failed to read {yaml_file}: {e}", file=sys.stderr)

        self.signals = signals

    def get_signal_by_id(self, signal_id: str) -> Optional[BrainSignalEntry]:
        """Find a signal by its ID."""
        for signal in self.signals:
            if signal.id == signal_id:
                return signal
        return None

    def compute_metrics(self) -> dict[str, Any]:
        """Compute comprehensive metrics about loaded signals."""
        if not self.signals:
            return {"total_signals": 0}

        # Basic counts
        metrics = {
            "total_signals": len(self.signals),
            "signals_by_layer": {},
            "signals_by_work_type": {},
            "signals_by_factor": {},
            "signals_by_peril": {},
            "signals_by_rap_class": {},
            "signals_by_schema_version": {},
            "data_source_coverage": {},
            "required_data_coverage": {},
        }

        for signal in self.signals:
            # Layer
            metrics["signals_by_layer"][signal.layer or "unknown"] = (
                metrics["signals_by_layer"].get(signal.layer or "unknown", 0) + 1
            )

            # Work type
            metrics["signals_by_work_type"][signal.work_type] = (
                metrics["signals_by_work_type"].get(signal.work_type, 0) + 1
            )

            # Factors
            for factor in signal.factors:
                metrics["signals_by_factor"][factor] = (
                    metrics["signals_by_factor"].get(factor, 0) + 1
                )

            # Peril IDs
            for peril in signal.peril_ids:
                metrics["signals_by_peril"][peril] = metrics["signals_by_peril"].get(peril, 0) + 1

            # RAP class
            metrics["signals_by_rap_class"][signal.rap_class] = (
                metrics["signals_by_rap_class"].get(signal.rap_class, 0) + 1
            )

            # Schema version
            metrics["signals_by_schema_version"][signal.schema_version] = (
                metrics["signals_by_schema_version"].get(signal.schema_version, 0) + 1
            )

            # Data sources from provenance
            source = signal.provenance.data_source
            if source:
                metrics["data_source_coverage"][source] = (
                    metrics["data_source_coverage"].get(source, 0) + 1
                )

            # Required data types
            for req in signal.required_data:
                metrics["required_data_coverage"][req] = (
                    metrics["required_data_coverage"].get(req, 0) + 1
                )

        return metrics

    def list_signals(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """List signals with basic metadata."""
        result = []
        for signal in self.signals[offset : offset + limit]:
            result.append(
                {
                    "id": signal.id,
                    "name": signal.name,
                    "work_type": signal.work_type,
                    "layer": signal.layer,
                    "factors": signal.factors,
                    "rap_class": signal.rap_class,
                    "schema_version": signal.schema_version,
                }
            )
        return result

    def validate_yaml(self) -> dict[str, Any]:
        """Validate YAML structure and report errors."""
        # Re-load with validation
        signals_dir = self.brain_root / "signals"
        errors = []
        warnings = []

        for yaml_file in signals_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data is None:
                        warnings.append(f"Empty YAML file: {yaml_file}")
                        continue
                    if not isinstance(data, list):
                        errors.append(f"YAML root is not a list: {yaml_file}")
                        continue
                    for i, item in enumerate(data):
                        try:
                            BrainSignalEntry.model_validate(item)
                        except Exception as e:
                            errors.append(f"{yaml_file}: item {i}: {e}")
            except yaml.YAMLError as e:
                errors.append(f"YAML syntax error in {yaml_file}: {e}")
            except Exception as e:
                errors.append(f"Unexpected error reading {yaml_file}: {e}")

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": errors[:50],  # Limit output
            "warnings": warnings[:50],
        }

    def analyze_by_peril(self) -> dict[str, Any]:
        """Analyze signals by peril category."""
        peril_counts = {}
        for signal in self.signals:
            for peril_id in signal.peril_ids:
                peril_counts[peril_id] = peril_counts.get(peril_id, 0) + 1

        return {
            "total_signals": len(self.signals),
            "signals_with_peril": sum(1 for s in self.signals if s.peril_ids),
            "peril_counts": peril_counts,
            "peril_distribution": {
                peril: count / len(self.signals) for peril, count in peril_counts.items()
            },
        }

    def analyze_by_factor(self) -> dict[str, Any]:
        """Analyze signals by factor (F1-F10)."""
        factor_counts = {}
        for signal in self.signals:
            for factor in signal.factors:
                factor_counts[factor] = factor_counts.get(factor, 0) + 1

        return {
            "total_signals": len(self.signals),
            "signals_with_factors": sum(1 for s in self.signals if s.factors),
            "factor_counts": factor_counts,
            "factor_distribution": {
                factor: count / len(self.signals) for factor, count in factor_counts.items()
            },
        }

    def analyze_by_rap_class(self) -> dict[str, Any]:
        """Analyze signals by RAP class (host, agent, environment)."""
        rap_counts = {}
        for signal in self.signals:
            rap_class = signal.rap_class
            rap_counts[rap_class] = rap_counts.get(rap_class, 0) + 1

        return {
            "total_signals": len(self.signals),
            "rap_counts": rap_counts,
            "rap_distribution": {
                rap_class: count / len(self.signals) for rap_class, count in rap_counts.items()
            },
        }

    def analyze_coverage_by_data_source(self) -> dict[str, Any]:
        """Analyze data source coverage from required_data field."""
        data_source_counts = {}
        for signal in self.signals:
            for data_key in signal.required_data:
                # Extract source type from data key (e.g., "SEC_10K" from "SEC_10K.revenue")
                parts = data_key.split(".")
                if parts:
                    source = parts[0]
                    data_source_counts[source] = data_source_counts.get(source, 0) + 1

        return {
            "total_signals": len(self.signals),
            "signals_with_required_data": sum(1 for s in self.signals if s.required_data),
            "data_source_counts": data_source_counts,
            "coverage_gaps": [
                source
                for source, count in data_source_counts.items()
                if count < 10  # Arbitrary threshold for under-covered sources
            ],
        }

    def scenario_analysis(self, scenario_type: str = "biotech") -> dict[str, Any]:
        """Analyze signals relevant to a specific scenario.

        Args:
            scenario_type: One of "biotech", "ipo", "tech", "industrial", "financial"
        """
        # Placeholder logic - in reality would use sector_adjustments or other fields
        relevant_signals = []
        for signal in self.signals:
            # Check if signal has sector_adjustments for this scenario
            if signal.sector_adjustments and scenario_type in signal.sector_adjustments:
                relevant_signals.append(signal.id)
            # Also check if signal ID contains scenario keywords
            elif scenario_type.lower() in signal.id.lower():
                relevant_signals.append(signal.id)

        return {
            "scenario_type": scenario_type,
            "relevant_signals_count": len(relevant_signals),
            "relevant_signals": relevant_signals[:50],  # Limit output
            "coverage_percentage": len(relevant_signals) / len(self.signals)
            if self.signals
            else 0,
        }


async def main() -> None:
    """Run the MCP server over stdio."""
    # Create server instance
    server = Server("brain-analyzer")

    # Initialize brain analyzer
    brain_root = os.environ.get("BRAIN_ROOT")
    analyzer = BrainAnalyzer(Path(brain_root) if brain_root else None)

    # Define tools
    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return [
            Tool(
                name="brain_analyzer_list_signals",
                description="List brain signals with metadata",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of signals to return",
                            "default": 100,
                        },
                        "offset": {
                            "type": "number",
                            "description": "Offset for pagination",
                            "default": 0,
                        },
                    },
                },
            ),
            Tool(
                name="brain_analyzer_get_signal",
                description="Get detailed information about a specific signal",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "signal_id": {
                            "type": "string",
                            "description": "Signal ID (e.g., GOV.BOARD.independence)",
                        },
                    },
                    "required": ["signal_id"],
                },
            ),
            Tool(
                name="brain_analyzer_compute_metrics",
                description="Compute comprehensive metrics about brain signals",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="brain_analyzer_validate_yaml",
                description="Validate brain YAML files and report errors",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="brain_analyzer_analyze_by_factor",
                description="Analyze signals by factor (F1-F10)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="brain_analyzer_analyze_by_rap_class",
                description="Analyze signals by RAP class (host, agent, environment)",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="brain_analyzer_analyze_coverage_by_data_source",
                description="Analyze data source coverage from required_data field",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "brain_analyzer_list_signals":
            limit = arguments.get("limit", 100)
            offset = arguments.get("offset", 0)
            signals = analyzer.list_signals(limit=limit, offset=offset)
            return [
                TextContent(
                    type="text",
                    text=json.dumps(signals, indent=2, default=str),
                )
            ]

        elif name == "brain_analyzer_get_signal":
            signal_id = arguments["signal_id"]
            signal = analyzer.get_signal_by_id(signal_id)
            if signal is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({"error": f"Signal not found: {signal_id}"}, indent=2),
                    )
                ]
            # Convert to dict, handling Pydantic models
            signal_dict = signal.model_dump(mode="json")
            return [
                TextContent(
                    type="text",
                    text=json.dumps(signal_dict, indent=2, default=str),
                )
            ]

        elif name == "brain_analyzer_compute_metrics":
            metrics = analyzer.compute_metrics()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(metrics, indent=2, default=str),
                )
            ]

        elif name == "brain_analyzer_validate_yaml":
            validation = analyzer.validate_yaml()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(validation, indent=2, default=str),
                )
            ]

        elif name == "brain_analyzer_analyze_by_factor":
            analysis = analyzer.analyze_by_factor()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(analysis, indent=2, default=str),
                )
            ]

        elif name == "brain_analyzer_analyze_by_rap_class":
            analysis = analyzer.analyze_by_rap_class()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(analysis, indent=2, default=str),
                )
            ]

        elif name == "brain_analyzer_analyze_coverage_by_data_source":
            analysis = analyzer.analyze_coverage_by_data_source()
            return [
                TextContent(
                    type="text",
                    text=json.dumps(analysis, indent=2, default=str),
                )
            ]

        else:
            raise ValueError(f"Unknown tool: {name}")

    # Run server over stdio
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="brain-analyzer",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
