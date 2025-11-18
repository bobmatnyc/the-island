#!/usr/bin/env python3
"""
Entity Name Formatting Validator

Validates entity names across the Epstein Archive database for:
- Trailing commas
- Leading/trailing spaces
- Multiple consecutive spaces
- Unusual ending characters
- Duplicate entities
- Multiple Jeffrey Epstein entities

Usage:
    python scripts/validation/validate_entity_names.py
    python scripts/validation/validate_entity_names.py --json  # JSON output
"""

import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime
from typing import Dict, List, Tuple, Set


class EntityNameValidator:
    """Validates entity name formatting across database files."""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.entities_file = self.base_path / "data/md/entities/ENTITIES_INDEX.json"
        self.flights_file = self.base_path / "data/md/entities/flight_logs_by_flight.json"

        self.issues = {
            'trailing_commas': [],
            'leading_trailing_spaces': [],
            'multiple_spaces': [],
            'unusual_endings': [],
            'duplicate_names': [],
            'jeffrey_epstein_variants': []
        }

    def load_data(self) -> Tuple[List[Dict], List[Dict]]:
        """Load entities and flight data."""
        with open(self.entities_file) as f:
            entities_data = json.load(f)

        with open(self.flights_file) as f:
            flights_data = json.load(f)

        return entities_data['entities'], flights_data['flights']

    def validate_entities(self, entities: List[Dict]) -> None:
        """Run all validation checks on entities."""
        # Check trailing commas
        for e in entities:
            name = e.get('name', '')
            if name.endswith(','):
                self.issues['trailing_commas'].append({
                    'name': name,
                    'type': e.get('type', 'unknown')
                })

        # Check leading/trailing spaces
        for e in entities:
            name = e.get('name', '')
            if name != name.strip():
                self.issues['leading_trailing_spaces'].append({
                    'name': name,
                    'trimmed': name.strip()
                })

        # Check multiple spaces
        for e in entities:
            name = e.get('name', '')
            if '  ' in name:
                self.issues['multiple_spaces'].append({
                    'name': name,
                    'cleaned': ' '.join(name.split())
                })

        # Check unusual endings
        valid_endings = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0-9.)"\'')
        for e in entities:
            name = e.get('name', '')
            if name and name[-1] not in valid_endings:
                self.issues['unusual_endings'].append({
                    'name': name,
                    'ending_char': name[-1],
                    'ascii_code': ord(name[-1])
                })

        # Check duplicates (case-insensitive)
        names_lower = [e.get('name', '').lower() for e in entities]
        duplicates = [(name, count) for name, count in Counter(names_lower).items() if count > 1]
        if duplicates:
            self.issues['duplicate_names'] = [
                {'name': name, 'count': count} for name, count in duplicates
            ]

        # Check Jeffrey Epstein variants
        jeffrey_entities = [
            e for e in entities
            if 'jeffrey' in e.get('name', '').lower() and 'epstein' in e.get('name', '').lower()
        ]
        # Store all Jeffrey entities for reporting (even if just 1)
        self.issues['jeffrey_epstein_variants'] = [
            {
                'name': e['name'],
                'normalized': e.get('normalized_name', 'N/A'),
                'flights': e.get('flights', 0),
                'sources': e.get('sources', [])
            }
            for e in jeffrey_entities
        ]

    def validate_flight_passengers(self, flights: List[Dict]) -> Dict[str, Set[str]]:
        """Validate passenger names in flight logs."""
        flight_issues = {
            'trailing_comma': set(),
            'leading_trailing_space': set(),
            'unusual_chars': set()
        }

        valid_endings = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0-9.)"\'')

        for flight in flights:
            for passenger in flight.get('passengers', []):
                if passenger.endswith(','):
                    flight_issues['trailing_comma'].add(passenger)

                if passenger != passenger.strip():
                    flight_issues['leading_trailing_space'].add(passenger)

                if passenger and passenger[-1] not in valid_endings:
                    flight_issues['unusual_chars'].add(passenger)

        return {k: list(v) for k, v in flight_issues.items()}

    def has_issues(self) -> bool:
        """Check if any issues were found."""
        return any(self.issues.values())

    def print_report(self, entities_count: int, flights_count: int,
                    flight_issues: Dict, passengers_count: int) -> None:
        """Print human-readable validation report."""
        print("=" * 80)
        print("ENTITY NAME FORMATTING VALIDATION REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Entities validation
        print("ENTITIES DATABASE")
        print("-" * 40)
        print(f"Total entities: {entities_count}\n")

        checks = [
            ("Trailing Commas", self.issues['trailing_commas']),
            ("Leading/Trailing Spaces", self.issues['leading_trailing_spaces']),
            ("Multiple Spaces", self.issues['multiple_spaces']),
            ("Unusual Endings", self.issues['unusual_endings']),
            ("Duplicate Names", self.issues['duplicate_names']),
        ]

        for check_name, issues in checks:
            if issues:
                print(f"❌ {check_name}: {len(issues)} issues")
                for issue in issues[:5]:
                    print(f"   - {issue}")
            else:
                print(f"✅ {check_name}: No issues")

        # Jeffrey Epstein check
        print()
        if len(self.issues['jeffrey_epstein_variants']) == 0:
            print("⚠️  Jeffrey Epstein: No entity found")
        elif len(self.issues['jeffrey_epstein_variants']) == 1:
            e = self.issues['jeffrey_epstein_variants'][0]
            print(f"✅ Jeffrey Epstein: Single entity")
            print(f"   - Name: \"{e['name']}\"")
            print(f"   - Normalized: \"{e['normalized']}\"")
            print(f"   - Flights: {e['flights']}")
        else:
            print(f"❌ Jeffrey Epstein: {len(self.issues['jeffrey_epstein_variants'])} variants")
            for e in self.issues['jeffrey_epstein_variants']:
                print(f"   - \"{e['name']}\" ({e['flights']} flights)")

        # Flight logs validation
        print("\n" + "=" * 80)
        print("FLIGHT LOGS")
        print("-" * 40)
        print(f"Total flights: {flights_count}")
        print(f"Unique passengers: {passengers_count}\n")

        flight_checks = [
            ("Trailing Commas", flight_issues['trailing_comma']),
            ("Leading/Trailing Spaces", flight_issues['leading_trailing_space']),
            ("Unusual Characters", flight_issues['unusual_chars']),
        ]

        for check_name, issues in flight_checks:
            if issues:
                print(f"❌ {check_name}: {len(issues)} issues")
                for issue in issues[:5]:
                    print(f"   - \"{issue}\"")
            else:
                print(f"✅ {check_name}: No issues")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        total_entity_issues = sum(len(v) for k, v in self.issues.items()
                                 if k != 'jeffrey_epstein_variants')
        total_entity_issues += max(0, len(self.issues['jeffrey_epstein_variants']) - 1)

        total_flight_issues = sum(len(v) for v in flight_issues.values())

        if total_entity_issues == 0 and total_flight_issues == 0:
            print("✅ ALL CHECKS PASSED - No formatting issues found!")
        else:
            print(f"❌ ISSUES FOUND:")
            print(f"   - Entity database: {total_entity_issues} issues")
            print(f"   - Flight logs: {total_flight_issues} issues")

    def get_json_report(self, entities_count: int, flights_count: int,
                       flight_issues: Dict, passengers_count: int) -> Dict:
        """Generate JSON format report."""
        total_entity_issues = sum(len(v) for k, v in self.issues.items()
                                 if k != 'jeffrey_epstein_variants')
        total_entity_issues += max(0, len(self.issues['jeffrey_epstein_variants']) - 1)

        total_flight_issues = sum(len(v) for v in flight_issues.values())

        return {
            'generated': datetime.now().isoformat(),
            'status': 'passed' if (total_entity_issues == 0 and total_flight_issues == 0) else 'failed',
            'entities': {
                'total': entities_count,
                'issues': self.issues,
                'total_issues': total_entity_issues
            },
            'flights': {
                'total': flights_count,
                'passengers': passengers_count,
                'issues': flight_issues,
                'total_issues': total_flight_issues
            },
            'summary': {
                'total_issues': total_entity_issues + total_flight_issues,
                'entities_passed': total_entity_issues == 0,
                'flights_passed': total_flight_issues == 0
            }
        }


def main():
    """Main validation entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate entity name formatting')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--base-path', default='.', help='Base path to project')
    args = parser.parse_args()

    try:
        validator = EntityNameValidator(args.base_path)
        entities, flights = validator.load_data()

        # Run validations
        validator.validate_entities(entities)
        flight_issues = validator.validate_flight_passengers(flights)

        # Get unique passenger count
        all_passengers = set()
        for flight in flights:
            all_passengers.update(flight.get('passengers', []))

        # Output report
        if args.json:
            report = validator.get_json_report(
                len(entities), len(flights), flight_issues, len(all_passengers)
            )
            print(json.dumps(report, indent=2))
        else:
            validator.print_report(
                len(entities), len(flights), flight_issues, len(all_passengers)
            )

        # Exit code based on validation result
        sys.exit(1 if validator.has_issues() else 0)

    except FileNotFoundError as e:
        print(f"❌ Error: Required file not found - {e}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in data file - {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
