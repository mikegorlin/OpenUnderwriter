#!/usr/bin/env python3
"""
Design System Query Tool
Query card registry and design system YAML files for card catalog development.

Usage:
  python scripts/query_design_system.py list-cards --section 03
  python scripts/query_design_system.py card-info --id 15
  python scripts/query_design_system.py data-sources --card 15
  python scripts/query_design_system.py chart-styles --type L
  python scripts/query_design_system.py validate
  python scripts/query_design_system.py stats
"""

import argparse
import yaml
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Paths relative to project root
CARD_REGISTRY_PATH = Path("src/do_uw/brain/config/card_registry.yaml")
DESIGN_SYSTEM_PATH = Path("src/do_uw/brain/config/design_system.yaml")


class DesignSystemQuery:
    def __init__(self):
        self.card_registry = self._load_yaml(CARD_REGISTRY_PATH)
        self.design_system = self._load_yaml(DESIGN_SYSTEM_PATH)

    def _load_yaml(self, path: Path) -> Dict:
        """Load YAML file with error handling."""
        if not path.exists():
            print(f"Error: File not found: {path}", file=sys.stderr)
            sys.exit(1)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file {path}: {e}", file=sys.stderr)
            sys.exit(1)

    def list_cards(self, section: Optional[str] = None, active_only: bool = True) -> None:
        """List cards, optionally filtered by section and active status."""
        cards = self.card_registry.get("cards", [])

        if section:
            # Convert section number to string with leading zero if needed
            if len(section) == 1:
                section = f"0{section}"
            cards = [c for c in cards if c.get("section") == section]

        if active_only:
            cards = [c for c in cards if c.get("active", False)]

        print(f"\n{'ID':<4} {'Section':<8} {'Title':<40} {'Status':<12} {'Template':<20}")
        print("-" * 90)
        for card in cards:
            card_id = card.get("id", "N/A")
            section_num = card.get("section", "N/A")
            title = card.get("title", "N/A")[:38]
            status = card.get("status", "draft")
            template = card.get("template", "N/A")
            print(f"{card_id:<4} {section_num:<8} {title:<40} {status:<12} {template:<20}")

        print(
            f"\nTotal: {len(cards)} cards"
            + (f" in section {section}" if section else "")
            + (" (active only)" if active_only else "")
        )

    def card_info(self, card_id: str) -> None:
        """Show detailed information about a specific card."""
        cards = self.card_registry.get("cards", [])
        card = next((c for c in cards if c.get("id") == card_id), None)

        if not card:
            print(f"Error: Card '{card_id}' not found", file=sys.stderr)
            return

        print(f"\n{'=' * 60}")
        print(f"CARD DETAILS: {card.get('id')} - {card.get('title')}")
        print(f"{'=' * 60}")

        # Basic info
        print(f"Section:      {card.get('section')}")
        print(f"Status:       {card.get('status', 'draft')}")
        print(f"Active:       {card.get('active', False)}")
        print(f"Template:     {card.get('template', 'N/A')}")
        print(f"Description:  {card.get('description', 'N/A')}")

        # Data sources
        data_keys = card.get("data_keys", [])
        if data_keys:
            print(f"\nData Keys ({len(data_keys)}):")
            for key in data_keys:
                print(f"  - {key}")

        # Elements
        elements = card.get("elements", [])
        if elements:
            print(f"\nElements ({len(elements)}):")
            for elem in elements:
                elem_type = elem.get("type", "N/A")
                chart_ref = elem.get("chart_ref", "N/A")
                print(
                    f"  - {elem_type}" + (f" (chart: {chart_ref})" if chart_ref != "N/A" else "")
                )

        # Section color from design system
        section_num = card.get("section")
        if section_num:
            section_info = self._get_section_info(section_num)
            if section_info:
                print(f"\nSection Color: {section_info.get('color')}")
                print(f"Section Name:  {section_info.get('nav_label')}")

    def data_sources(self, card_id: Optional[str] = None) -> None:
        """Show data source information for a card or all cards."""
        if card_id:
            cards = self.card_registry.get("cards", [])
            card = next((c for c in cards if c.get("id") == card_id), None)
            if not card:
                print(f"Error: Card '{card_id}' not found", file=sys.stderr)
                return

            data_keys = card.get("data_keys", [])
            print(f"\nData sources for card {card_id} ({card.get('title')}):")
            if not data_keys:
                print("  No data keys defined")
                return

            # Get data pool
            data_pool = self.card_registry.get("data_pool", {})
            for key in data_keys:
                info = data_pool.get(key, {})
                source = info.get("source", "unknown")
                desc = info.get("desc", "No description")
                print(f"  - {key}: {source} ({desc})")
        else:
            # Show all data sources in data pool
            data_pool = self.card_registry.get("data_pool", {})
            print(f"\nAll data sources in pool ({len(data_pool)}):")

            # Group by source
            by_source = {}
            for key, info in data_pool.items():
                source = info.get("source", "unknown")
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(key)

            for source, keys in sorted(by_source.items()):
                print(f"\n{source} ({len(keys)}):")
                for key in sorted(keys):
                    info = data_pool[key]
                    desc = info.get("desc", "")
                    print(f"  - {key}: {desc}")

    def chart_styles(self, style_type: Optional[str] = None) -> None:
        """List chart styles from design system."""
        charts = self.design_system.get("charts", {})

        if style_type:
            # Filter by prefix
            charts = {k: v for k, v in charts.items() if k.startswith(style_type.upper())}

        if not charts:
            prefix_msg = f" with prefix '{style_type}'" if style_type else ""
            print(f"No chart styles found{prefix_msg}")
            return

        print(f"\nChart Styles ({len(charts)}):")
        for chart_id, chart_info in sorted(charts.items()):
            name = chart_info.get("name", "N/A")
            intent = chart_info.get("intent", "N/A")
            description = chart_info.get("description", "")[:60]
            print(f"{chart_id:<6} {name:<30} {intent:<15} {description}")

    def components(self) -> None:
        """List components from design system."""
        components = self.design_system.get("components", {})

        if not components:
            print("No components defined")
            return

        print(f"\nComponents ({len(components)}):")
        for comp_id, comp_info in sorted(components.items()):
            name = comp_info.get("name", "N/A")
            description = comp_info.get("description", "")[:60]
            print(f"{comp_id:<10} {name:<30} {description}")

    def validate(self) -> None:
        """Run validation checks on the design system."""
        print("Running design system validation...")

        cards = self.card_registry.get("cards", [])
        data_pool = self.card_registry.get("data_pool", {})
        sections = self.design_system.get("sections", {})

        issues = []

        # Check 1: Cards reference valid data keys
        for card in cards:
            card_id = card.get("id")
            data_keys = card.get("data_keys", [])
            for key in data_keys:
                if key not in data_pool:
                    issues.append(f"Card {card_id}: data key '{key}' not found in data pool")

        # Check 2: Cards have valid section numbers
        section_numbers = {info.get("number") for info in sections.values()}
        for card in cards:
            card_id = card.get("id")
            section = card.get("section")
            if section and section not in section_numbers:
                issues.append(f"Card {card_id}: section '{section}' not found in design system")

        # Check 3: Active cards have templates (if status is beyond draft)
        for card in cards:
            if card.get("active", False) and card.get("status") != "draft":
                if not card.get("template"):
                    issues.append(
                        f"Card {card.get('id')}: active card with status '{card.get('status')}' has no template"
                    )

        # Check 4: Chart references exist
        charts = self.design_system.get("charts", {})
        for card in cards:
            for elem in card.get("elements", []):
                chart_ref = elem.get("chart_ref")
                if chart_ref and chart_ref not in charts:
                    issues.append(
                        f"Card {card.get('id')}: chart reference '{chart_ref}' not found in design system"
                    )

        if issues:
            print(f"\nFound {len(issues)} issues:")
            for issue in issues:
                print(f"  ⚠️  {issue}")
        else:
            print("✓ No issues found")

    def stats(self) -> None:
        """Show statistics about the design system."""
        cards = self.card_registry.get("cards", [])
        data_pool = self.card_registry.get("data_pool", {})
        sections = self.design_system.get("sections", {})
        charts = self.design_system.get("charts", {})
        components = self.design_system.get("components", {})

        print("\n" + "=" * 60)
        print("DESIGN SYSTEM STATISTICS")
        print("=" * 60)

        # Card statistics
        active_cards = [c for c in cards if c.get("active", False)]
        by_status = {}
        by_section = {}
        for card in cards:
            status = card.get("status", "draft")
            by_status[status] = by_status.get(status, 0) + 1
            section = card.get("section", "unknown")
            by_section[section] = by_section.get(section, 0) + 1

        print(f"\n📊 CARDS")
        print(f"  Total: {len(cards)}")
        print(f"  Active: {len(active_cards)}")
        print(f"  By status:")
        for status, count in sorted(by_status.items()):
            print(f"    - {status}: {count}")

        print(f"\n📊 SECTIONS")
        print(f"  Total: {len(sections)}")
        for section_id, info in sections.items():
            color = info.get("color", "N/A")
            label = info.get("nav_label", "N/A")
            cards_in_section = by_section.get(info.get("number"), 0)
            print(f"    - {info.get('number')}: {label} ({color}) - {cards_in_section} cards")

        print(f"\n📊 DATA")
        print(f"  Data pool elements: {len(data_pool)}")
        by_source = {}
        for info in data_pool.values():
            source = info.get("source", "unknown")
            by_source[source] = by_source.get(source, 0) + 1
        for source, count in sorted(by_source.items()):
            print(f"    - {source}: {count}")

        print(f"\n📊 VISUAL ELEMENTS")
        print(f"  Chart styles: {len(charts)}")
        print(f"  Components: {len(components)}")

    def _get_section_info(self, section_num: str) -> Optional[Dict]:
        """Get section information by number."""
        sections = self.design_system.get("sections", {})
        for info in sections.values():
            if info.get("number") == section_num:
                return info
        return None


def main():
    parser = argparse.ArgumentParser(description="Query design system and card registry")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list-cards command
    list_parser = subparsers.add_parser("list-cards", help="List cards")
    list_parser.add_argument("--section", help="Filter by section number")
    list_parser.add_argument("--all", action="store_true", help="Include inactive cards")

    # card-info command
    info_parser = subparsers.add_parser("card-info", help="Show card details")
    info_parser.add_argument("--id", required=True, help="Card ID")

    # data-sources command
    ds_parser = subparsers.add_parser("data-sources", help="Show data sources")
    ds_parser.add_argument("--card", help="Card ID (optional, shows all if omitted)")

    # chart-styles command
    chart_parser = subparsers.add_parser("chart-styles", help="List chart styles")
    chart_parser.add_argument("--type", help="Filter by type prefix (L, F, etc.)")

    # components command
    subparsers.add_parser("components", help="List components")

    # validate command
    subparsers.add_parser("validate", help="Run validation checks")

    # stats command
    subparsers.add_parser("stats", help="Show statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    dsq = DesignSystemQuery()

    if args.command == "list-cards":
        dsq.list_cards(section=args.section, active_only=not args.all)
    elif args.command == "card-info":
        dsq.card_info(args.id)
    elif args.command == "data-sources":
        dsq.data_sources(args.card)
    elif args.command == "chart-styles":
        dsq.chart_styles(args.type)
    elif args.command == "components":
        dsq.components()
    elif args.command == "validate":
        dsq.validate()
    elif args.command == "stats":
        dsq.stats()


if __name__ == "__main__":
    main()
