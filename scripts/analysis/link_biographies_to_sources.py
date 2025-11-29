#!/usr/bin/env python3
"""
Link Entity Biographies to Source Documents

This script adds document references to entity biographies by linking them to:
1. Flight log entries (from flight_logs_by_flight.json)
2. Black book entries (from black_book.md)
3. Court documents (if available)

The goal is to provide verifiable source material for each biography.

Usage:
    python3 scripts/analysis/link_biographies_to_sources.py [--dry-run] [--backup]

Examples:
    # Dry run (show what would be changed)
    python3 scripts/analysis/link_biographies_to_sources.py --dry-run

    # Full run with backup
    python3 scripts/analysis/link_biographies_to_sources.py --backup
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from collections import defaultdict

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
BIOGRAPHIES_PATH = PROJECT_ROOT / "data" / "metadata" / "entity_biographies.json"
FLIGHT_LOGS_PATH = PROJECT_ROOT / "data" / "md" / "entities" / "flight_logs_by_flight.json"
BLACK_BOOK_PATH = PROJECT_ROOT / "data" / "md" / "entities" / "black_book.md"
ENTITIES_INDEX_PATH = PROJECT_ROOT / "data" / "md" / "entities" / "ENTITIES_INDEX.json"


def load_biographies() -> Dict:
    """Load entity biographies"""
    print("📖 Loading entity biographies...")
    with open(BIOGRAPHIES_PATH) as f:
        return json.load(f)


def load_flight_logs() -> Dict:
    """Load flight log data"""
    print("✈️  Loading flight logs...")
    try:
        with open(FLIGHT_LOGS_PATH) as f:
            return json.load(f)
    except FileNotFoundError:
        print("⚠️  Flight logs file not found")
        return {"flights": []}


def load_entities_index() -> Dict:
    """Load entities index (has entity IDs and display names)"""
    print("📋 Loading entities index...")
    try:
        with open(ENTITIES_INDEX_PATH) as f:
            data = json.load(f)
            # Handle both list and dict formats
            if isinstance(data, list):
                return {"entities": {}}
            return data
    except FileNotFoundError:
        print("⚠️  Entities index not found")
        return {"entities": {}}


def parse_black_book() -> Set[str]:
    """Parse black book markdown to extract entity names"""
    print("📕 Parsing black book...")
    entities = set()

    try:
        with open(BLACK_BOOK_PATH) as f:
            content = f.read()

        # Extract names from markdown lists
        # Format: "- **Name**: Additional info"
        pattern = r'-\s+\*\*([^*]+)\*\*'
        matches = re.findall(pattern, content)
        entities.update(name.strip() for name in matches)

        print(f"   Found {len(entities)} entities in black book")
    except FileNotFoundError:
        print("⚠️  Black book file not found")

    return entities


def normalize_name(name: str) -> str:
    """Normalize entity name for matching"""
    # Convert to lowercase, remove special chars, extra spaces
    name = name.lower()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name.strip())
    return name


def find_flight_appearances(entity_id: str, display_name: str, flight_logs: Dict) -> List[Dict]:
    """Find all flight log entries mentioning this entity"""
    appearances = []

    # Normalize variations of the name
    name_variations = {
        normalize_name(display_name),
        normalize_name(display_name.replace(',', '')),
        entity_id
    }

    for flight in flight_logs.get('flights', []):
        passengers = flight.get('passengers', [])

        # Check if any passenger matches this entity
        for passenger in passengers:
            passenger_norm = normalize_name(passenger)
            if passenger_norm in name_variations:
                appearances.append({
                    'flight_id': flight.get('flight_number', 'Unknown'),
                    'date': flight.get('date', 'Unknown'),
                    'from': flight.get('from', 'Unknown'),
                    'to': flight.get('to', 'Unknown'),
                    'passenger_name': passenger
                })

    return appearances


def check_black_book(display_name: str, black_book_entities: Set[str]) -> bool:
    """Check if entity appears in black book"""
    # Try exact match and variations
    variations = [
        display_name,
        display_name.replace(',', ''),
        ' '.join(reversed(display_name.split(', ')))  # "Last, First" -> "First Last"
    ]

    for variation in variations:
        if variation in black_book_entities:
            return True

    return False


def add_source_links(biographies: Dict, flight_logs: Dict, black_book_entities: Set[str], dry_run: bool = False) -> Dict:
    """Add source document links to biographies"""
    print("\n🔗 Linking biographies to source documents...")

    stats = {
        'total_processed': 0,
        'with_flights': 0,
        'with_black_book': 0,
        'with_both': 0,
        'total_flight_appearances': 0
    }

    for entity_id, bio_data in biographies.get('entities', {}).items():
        stats['total_processed'] += 1
        display_name = bio_data.get('display_name', entity_id)

        # Initialize sources if not exists
        if 'document_sources' not in bio_data:
            bio_data['document_sources'] = {}

        # Find flight appearances
        flight_appearances = find_flight_appearances(entity_id, display_name, flight_logs)
        if flight_appearances:
            stats['with_flights'] += 1
            stats['total_flight_appearances'] += len(flight_appearances)
            bio_data['document_sources']['flight_logs'] = {
                'count': len(flight_appearances),
                'entries': flight_appearances[:10]  # Limit to first 10 for brevity
            }
            print(f"  ✈️  {display_name}: {len(flight_appearances)} flights")

        # Check black book
        in_black_book = check_black_book(display_name, black_book_entities)
        if in_black_book:
            stats['with_black_book'] += 1
            bio_data['document_sources']['black_book'] = {
                'present': True,
                'note': 'Listed in Jeffrey Epstein\'s contact book'
            }
            print(f"  📕 {display_name}: In black book")

        # Count both sources
        if flight_appearances and in_black_book:
            stats['with_both'] += 1

    return stats


def create_backup(path: Path):
    """Create timestamped backup of file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = path.parent / f"{path.stem}.backup_{timestamp}{path.suffix}"

    import shutil
    shutil.copy(path, backup_path)
    print(f"💾 Backup created: {backup_path}")


def save_biographies(biographies: Dict, dry_run: bool = False, backup: bool = False):
    """Save updated biographies"""
    if dry_run:
        print("\n[DRY RUN] Would save updated biographies")
        return

    if backup:
        create_backup(BIOGRAPHIES_PATH)

    # Update metadata
    if 'metadata' not in biographies:
        biographies['metadata'] = {}

    biographies['metadata']['last_updated'] = datetime.now().isoformat()
    biographies['metadata']['source_linking_date'] = datetime.now().isoformat()

    with open(BIOGRAPHIES_PATH, 'w') as f:
        json.dump(biographies, f, indent=2)

    print(f"\n✅ Biographies updated: {BIOGRAPHIES_PATH}")


def print_summary(stats: Dict):
    """Print summary statistics"""
    print("\n" + "="*70)
    print("DOCUMENT LINKING SUMMARY")
    print("="*70)
    print(f"Total biographies processed: {stats['total_processed']}")
    print(f"With flight log references: {stats['with_flights']}")
    print(f"With black book references: {stats['with_black_book']}")
    print(f"With both sources: {stats['with_both']}")
    print(f"Total flight appearances: {stats['total_flight_appearances']}")
    print("="*70)


def main():
    parser = argparse.ArgumentParser(description='Link biographies to source documents')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without modifying files')
    parser.add_argument('--backup', action='store_true', help='Create backup before modifying')
    args = parser.parse_args()

    print("="*70)
    print("BIOGRAPHY DOCUMENT LINKING")
    print("="*70)

    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")

    # Load data
    biographies = load_biographies()
    flight_logs = load_flight_logs()
    black_book_entities = parse_black_book()

    # Add links
    stats = add_source_links(biographies, flight_logs, black_book_entities, args.dry_run)

    # Save results
    save_biographies(biographies, args.dry_run, args.backup)

    # Print summary
    print_summary(stats)

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes")
    else:
        print("\n✅ Document linking complete!")


if __name__ == '__main__':
    main()
