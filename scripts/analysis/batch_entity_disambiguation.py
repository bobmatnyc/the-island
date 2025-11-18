#!/usr/bin/env python3
"""
Batch Entity Disambiguation

Processes all entities from ENTITIES_INDEX.json and:
1. Identifies ambiguous names (single names, incomplete formats)
2. Uses Mistral to suggest full names
3. Presents suggestions to user for confirmation
4. Updates entity index with approved changes
5. Logs all changes with provenance

Design Decision: User Confirmation Required
- Rationale: Epstein case is sensitive; automated changes could introduce errors
- Trade-off: Slower processing, but maintains data integrity
- Alternative: Fully automated rejected due to risk of false positives

Usage:
    # Interactive mode (default)
    python3 batch_entity_disambiguation.py

    # Process only high-priority ambiguous names
    python3 batch_entity_disambiguation.py --priority high

    # Dry run (show suggestions without saving)
    python3 batch_entity_disambiguation.py --dry-run

    # Process specific entities
    python3 batch_entity_disambiguation.py --entities "Ghislaine" "Maxwell" "Nadia"
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
import argparse
import sys

from mistral_entity_disambiguator import MistralEntityDisambiguator, DisambiguationResult

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BatchDisambiguator:
    """
    Batch processing for entity disambiguation

    Performance:
    - Expected: 100-200 entities per hour (with user confirmation)
    - Each disambiguation: 2-5 seconds (model inference)
    - Bottleneck: Human confirmation, not model speed
    """

    def __init__(self, dry_run: bool = False):
        """
        Initialize batch disambiguator

        Args:
            dry_run: If True, show suggestions but don't save changes
        """
        self.dry_run = dry_run
        self.base_path = Path(__file__).parent.parent.parent
        self.entity_index_path = self.base_path / "data/md/entities/ENTITIES_INDEX.json"
        self.backup_path = self.base_path / "data/metadata/entity_index_backups"
        self.changelog_path = self.base_path / "data/metadata/disambiguation_changelog.json"

        # Create backup directory
        self.backup_path.mkdir(parents=True, exist_ok=True)

        # Load entity index
        self.entity_index = self._load_entity_index()

        # Initialize Mistral
        logger.info("Loading Mistral model...")
        self.disambiguator = MistralEntityDisambiguator()

        # Track changes
        self.changes = []

    def _load_entity_index(self) -> Dict:
        """Load entity index from JSON"""
        if not self.entity_index_path.exists():
            raise FileNotFoundError(f"Entity index not found: {self.entity_index_path}")

        with open(self.entity_index_path) as f:
            return json.load(f)

    def _backup_entity_index(self):
        """Create timestamped backup of entity index"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_path / f"ENTITIES_INDEX_{timestamp}.json"

        with open(backup_file, 'w') as f:
            json.dump(self.entity_index, f, indent=2)

        logger.info(f"Backup created: {backup_file}")

    def _save_entity_index(self):
        """Save updated entity index"""
        if self.dry_run:
            logger.info("DRY RUN: Would save entity index (not saving)")
            return

        # Create backup first
        self._backup_entity_index()

        # Save updated index
        with open(self.entity_index_path, 'w') as f:
            json.dump(self.entity_index, f, indent=2)

        logger.info(f"Entity index saved: {self.entity_index_path}")

    def _save_changelog(self):
        """Save changelog of all changes"""
        if self.dry_run:
            logger.info("DRY RUN: Would save changelog (not saving)")
            return

        # Load existing changelog if exists
        changelog = []
        if self.changelog_path.exists():
            with open(self.changelog_path) as f:
                changelog = json.load(f)

        # Add new changes
        changelog.extend(self.changes)

        # Save
        with open(self.changelog_path, 'w') as f:
            json.dump(changelog, f, indent=2)

        logger.info(f"Changelog saved: {len(self.changes)} changes logged")

    def identify_ambiguous_entities(self, priority: str = "all") -> List[Dict]:
        """
        Identify entities with ambiguous names

        Args:
            priority: "high" (single names with many flights),
                     "medium" (single names with few flights),
                     "all" (all ambiguous names)

        Returns:
            List of entities needing disambiguation
        """
        entities = self.entity_index.get('entities', [])
        ambiguous = []

        for entity in entities:
            name = entity.get('name', '')
            flights = entity.get('flights', 0)

            # Check if ambiguous
            is_ambiguous = False
            priority_level = "low"

            # Single name (no comma, no space)
            if ',' not in name and ' ' not in name:
                is_ambiguous = True
                priority_level = "high" if flights > 10 else "medium"

            # Generic placeholder (Female, Male)
            if 'Female' in name or 'Male' in name:
                is_ambiguous = True
                priority_level = "high"

            # Single word with high flight count
            if ' ' not in name and ',' not in name and flights > 5:
                is_ambiguous = True
                priority_level = "high"

            if is_ambiguous:
                entity_copy = entity.copy()
                entity_copy['priority'] = priority_level

                # Filter by requested priority
                if priority == "all" or priority_level == priority:
                    ambiguous.append(entity_copy)

        # Sort by priority and flight count
        priority_order = {"high": 0, "medium": 1, "low": 2}
        ambiguous.sort(key=lambda x: (priority_order[x['priority']], -x.get('flights', 0)))

        return ambiguous

    def process_entity(self, entity: Dict) -> bool:
        """
        Process single entity disambiguation

        Args:
            entity: Entity dictionary from index

        Returns:
            True if entity was updated, False otherwise
        """
        name = entity.get('name', '')
        flights = entity.get('flights', 0)
        sources = entity.get('sources', [])

        print("\n" + "=" * 80)
        print(f"Entity: {name}")
        print(f"Flights: {flights}")
        print(f"Sources: {sources}")
        print("=" * 80)

        # Build context
        context = f"Appeared in {flights} flights. Sources: {sources}"

        # Get disambiguation suggestion
        try:
            result = self.disambiguator.disambiguate_entity(name, context)
        except Exception as e:
            logger.error(f"Error disambiguating {name}: {e}")
            return False

        # Display suggestion
        print(f"\n📝 Suggestion:")
        print(f"   Original: {result.original_name}")
        print(f"   Suggested: {result.suggested_name}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Reasoning: {result.reasoning}")

        # Skip if same name
        if result.original_name == result.suggested_name:
            print("\n⏭️  Suggested name same as original - skipping")
            return False

        # Ask for confirmation
        response = input("\n✅ Accept this suggestion? (y/n/skip): ").strip().lower()

        if response == 'y':
            # Update entity
            old_name = entity['name']
            entity['name'] = result.suggested_name
            entity['normalized_name'] = result.suggested_name

            # Add to merged_from if not already there
            if 'merged_from' not in entity:
                entity['merged_from'] = []
            if old_name not in entity['merged_from'] and old_name != result.suggested_name:
                entity['merged_from'].append(old_name)

            # Log change
            change_record = {
                'timestamp': datetime.now().isoformat(),
                'original_name': result.original_name,
                'new_name': result.suggested_name,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'method': 'mistral_disambiguation',
                'approved_by': 'user'
            }
            self.changes.append(change_record)

            print(f"\n✅ Updated: {old_name} → {result.suggested_name}")
            return True

        elif response == 'skip':
            print("\n⏭️  Skipped")
            return False

        else:
            print("\n❌ Rejected")
            return False

    def process_batch(self, entities: List[Dict], max_count: int = None):
        """
        Process batch of entities

        Args:
            entities: List of entities to process
            max_count: Maximum number to process (None = all)
        """
        total = len(entities)
        processed = 0
        updated = 0

        print("\n" + "=" * 80)
        print(f"Batch Disambiguation: {total} entities")
        print("=" * 80)

        for i, entity in enumerate(entities):
            if max_count and processed >= max_count:
                break

            print(f"\n[{i+1}/{total}]")

            if self.process_entity(entity):
                updated += 1

            processed += 1

        print("\n" + "=" * 80)
        print(f"Summary:")
        print(f"  Processed: {processed}")
        print(f"  Updated: {updated}")
        print(f"  Skipped: {processed - updated}")
        print("=" * 80)

        # Save changes
        if updated > 0:
            print("\n💾 Saving changes...")
            self._save_entity_index()
            self._save_changelog()
            print("✅ Changes saved successfully")

    def process_specific_entities(self, entity_names: List[str]):
        """
        Process specific entities by name

        Args:
            entity_names: List of entity names to process
        """
        entities = self.entity_index.get('entities', [])

        # Find matching entities
        matches = []
        for name in entity_names:
            for entity in entities:
                if entity.get('name', '').lower() == name.lower():
                    matches.append(entity)
                    break

        if not matches:
            print(f"❌ No entities found matching: {entity_names}")
            return

        print(f"\n✅ Found {len(matches)} matching entities")
        self.process_batch(matches)


def main():
    parser = argparse.ArgumentParser(description="Batch entity disambiguation using Mistral")
    parser.add_argument('--priority', choices=['high', 'medium', 'all'], default='high',
                       help='Priority level of entities to process')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show suggestions without saving changes')
    parser.add_argument('--max-count', type=int, default=None,
                       help='Maximum number of entities to process')
    parser.add_argument('--entities', nargs='+',
                       help='Specific entity names to process')

    args = parser.parse_args()

    print("=" * 80)
    print("Batch Entity Disambiguation")
    print("=" * 80)

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE: Changes will NOT be saved")

    # Initialize
    batch = BatchDisambiguator(dry_run=args.dry_run)

    # Process specific entities or batch
    if args.entities:
        batch.process_specific_entities(args.entities)
    else:
        # Identify ambiguous entities
        ambiguous = batch.identify_ambiguous_entities(priority=args.priority)
        print(f"\n✅ Found {len(ambiguous)} ambiguous entities (priority: {args.priority})")

        if not ambiguous:
            print("\n🎉 No ambiguous entities found!")
            return

        # Show preview
        print("\nTop 10 ambiguous entities:")
        for i, entity in enumerate(ambiguous[:10]):
            print(f"  {i+1}. {entity['name']:20s} - {entity.get('flights', 0):3d} flights - {entity['priority']}")

        # Confirm
        response = input("\nProceed with batch disambiguation? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled")
            return

        # Process
        batch.process_batch(ambiguous, max_count=args.max_count)


if __name__ == "__main__":
    main()
