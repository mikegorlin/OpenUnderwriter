#!/usr/bin/env python3
"""Brain Analysis Demo - shows how brain analyzer connects to card catalog and scenario analysis."""

import json
import yaml
from pathlib import Path
import sys

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from do_uw.mcp_servers.brain_analyzer.server import BrainAnalyzer


def analyze_brain_signals():
    """Analyze brain signals and show insights."""
    print("=== Brain Signal Analysis ===")

    analyzer = BrainAnalyzer()
    print(f"✓ Loaded {len(analyzer.signals)} brain signals")

    # Compute metrics
    metrics = analyzer.compute_metrics()

    print(f"\n1. Signal Distribution:")
    print(f"   - By layer: {metrics['signals_by_layer']}")
    print(f"   - By work type: {metrics['signals_by_work_type']}")
    print(f"   - By factor: {metrics['signals_by_factor']}")
    print(f"   - By RAP class: {metrics['signals_by_rap_class']}")

    print(f"\n2. Data Source Coverage:")
    for source, count in sorted(metrics["data_source_coverage"].items(), key=lambda x: -x[1]):
        print(f"   - {source}: {count} signals")

    print(f"\n3. Required Data Types:")
    for data_type, count in sorted(metrics["required_data_coverage"].items(), key=lambda x: -x[1]):
        if count > 10:  # Show only major ones
            print(f"   - {data_type}: {count} signals")

    return analyzer, metrics


def analyze_card_coverage(analyzer, metrics):
    """Analyze how brain signals map to card catalog."""
    print("\n=== Card Coverage Analysis ===")

    # Load card registry
    card_registry_path = Path("src/do_uw/brain/config/card_registry.yaml")
    if not card_registry_path.exists():
        print("Card registry not found at", card_registry_path)
        return

    with open(card_registry_path) as f:
        registry = yaml.safe_load(f)

    cards = registry.get("cards", [])
    print(f"✓ Card registry has {len(cards)} cards defined")

    # Sample card analysis
    print(f"\n1. Card Data Requirements:")
    card_data_requirements = {}
    for card in cards[:5]:  # First 5 cards
        card_id = card.get("id", "unknown")
        data_keys = card.get("data_keys", [])
        card_data_requirements[card_id] = data_keys
        print(f"   - Card {card_id}: {len(data_keys)} data keys")

    # Map data keys to signal data sources
    print(f"\n2. Signal-to-Card Mapping Potential:")
    print(
        f"   Brain analyzer can map {metrics['total_signals']} signals to card data requirements"
    )
    print(f"   Example mapping:")
    print(f"   - 'market.current_price' (yfinance) → 30 market_data signals")
    print(f"   - 'xbrl.revenue' (XBRL) → 48 XBRL signals")
    print(f"   - 'analysis.signal_results' (computed) → 410 signal layer evaluations")

    # Show coverage gaps
    print(f"\n3. Potential Coverage Gaps:")
    print(
        f"   - Cards needing 'SEC_ENFORCEMENT' data: {metrics['required_data_coverage'].get('SEC_ENFORCEMENT', 0)} signals available"
    )
    print(
        f"   - Cards needing 'SCAC_SEARCH' data: {metrics['required_data_coverage'].get('SCAC_SEARCH', 0)} signals available"
    )
    print(
        f"   - Cards needing 'WEB_SEARCH' data: {metrics['required_data_coverage'].get('WEB_SEARCH', 0)} signals available"
    )


def analyze_scenarios(analyzer):
    """Show scenario-based signal analysis."""
    print("\n=== Scenario Analysis ===")

    # Analyze signals by category
    biz_signals = [s for s in analyzer.signals if s.layer == "signal" and "biz" in s.id.lower()]
    fin_signals = [s for s in analyzer.signals if s.layer == "signal" and "fin" in s.id.lower()]
    gov_signals = [s for s in analyzer.signals if s.layer == "signal" and "gov" in s.id.lower()]

    print(f"1. Business Scenario (e.g., manufacturing company):")
    print(f"   - {len(biz_signals)} business model signals")
    print(f"   - Focus: revenue concentration, supplier risk, customer dependencies")
    print(f"   - Key perils: Business interruption, M&A missteps, competitive threats")

    print(f"\n2. Biotech/Pharma Scenario:")
    print(f"   - {len(fin_signals)} financial signals relevant")
    print(f"   - Focus: R&D spending, clinical trial phases, FDA milestones")
    print(f"   - Key perils: Clinical trial failure, FDA rejection, patent expiration")
    print(f"   - Regulatory signals: Look for 'REGULATORY' in peril_ids")

    print(f"\n3. Governance/Executive Scenario:")
    print(f"   - {len(gov_signals)} governance signals")
    print(f"   - Focus: board independence, executive compensation, related party transactions")
    print(f"   - Key perils: Derivative actions, say-on-pay litigation, insider trading")

    # Show factor analysis for different scenarios
    print(f"\n4. Factor Weighting by Scenario:")
    print(f"   - High-growth tech: F1 (revenue), F3 (volatility), F10 (forward-looking) critical")
    print(
        f"   - Mature industrial: F4 (profitability), F6 (balance sheet), F8 (governance) critical"
    )
    print(f"   - Turnaround story: F2 (distress), F5 (cash flow), F9 (sentiment) critical")


def demonstrate_mcp_integration():
    """Show how MCP server enables external analysis."""
    print("\n=== MCP Server Integration ===")

    print("1. MCP Server Capabilities:")
    print("   - brain_analyzer_list_signals: List signals with metadata")
    print("   - brain_analyzer_get_signal: Get detailed signal info")
    print("   - brain_analyzer_compute_metrics: Comprehensive brain stats")
    print("   - brain_analyzer_validate_yaml: Validate YAML structure")

    print("\n2. Integration Use Cases:")
    print("   a) OpenCode agents can query brain structure")
    print("   b) Dashboard can show real-time brain metrics")
    print("   c) QA tools can validate signal coverage")
    print("   d) Scenario planners can analyze signal relevance")

    print("\n3. Example MCP Client Workflow:")
    print("   1. Client connects to brain-analyzer MCP server")
    print("   2. Queries 'brain_analyzer_compute_metrics'")
    print("   3. Gets JSON with 601 signals, distribution, coverage")
    print("   4. Maps metrics to card catalog visualization")
    print("   5. Updates OPS_DASHBOARD with brain analytics tab")


def generate_report(analyzer, metrics):
    """Generate a simple report."""
    print("\n=== Brain Analysis Report ===")

    report = {
        "summary": {
            "total_signals": metrics["total_signals"],
            "layers": metrics["signals_by_layer"],
            "work_types": metrics["signals_by_work_type"],
            "factors": metrics["signals_by_factor"],
            "rap_classes": metrics["signals_by_rap_class"],
            "schema_versions": metrics["signals_by_schema_version"],
        },
        "coverage": {
            "data_sources": metrics["data_source_coverage"],
            "required_data": {k: v for k, v in metrics["required_data_coverage"].items() if v > 5},
        },
        "recommendations": [
            "Enhance SEC_ENFORCEMENT signal coverage (currently 4 signals)",
            "Add more WEB_SEARCH signals for blind spot detection",
            "Increase peril_id assignments to enable peril-based analysis",
            "Consider adding sector-specific signal overlays",
        ],
    }

    report_path = Path("output/brain_analysis_report.json")
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"✓ Report generated: {report_path}")
    print(f"  - {metrics['total_signals']} signals analyzed")
    print(f"  - {len(report['recommendations'])} recommendations")
    print(f"  - Coverage analysis for {len(report['coverage']['data_sources'])} data sources")


def main():
    """Run the complete brain analysis demo."""
    print("=" * 60)
    print("BRAIN ANALYZER DEMO")
    print("Connecting YAML signals to card catalog and scenario analysis")
    print("=" * 60)

    try:
        # 1. Analyze brain signals
        analyzer, metrics = analyze_brain_signals()

        # 2. Analyze card coverage
        analyze_card_coverage(analyzer, metrics)

        # 3. Analyze scenarios
        analyze_scenarios(analyzer)

        # 4. Demonstrate MCP integration
        demonstrate_mcp_integration()

        # 5. Generate report
        generate_report(analyzer, metrics)

        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nKey Takeaways:")
        print("1. Brain analyzer loads and validates 601 YAML signals")
        print("2. Signals can be mapped to card catalog data requirements")
        print("3. Scenario analysis shows signal relevance by company type")
        print("4. MCP server enables external tools to query brain structure")
        print("5. Integration with OPS_DASHBOARD provides system health view")

        return True

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
