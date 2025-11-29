#!/usr/bin/env python3
"""
Entity Relationship Categorization Script

Categorizes all 1,637 entities by their relationship to Jeffrey Epstein based on:
- Source materials (flight logs, black book)
- Connection frequency
- Flight statistics
- Biography keywords (for entities with biographies)

Generates biography summaries for entities that have full biographies.

Output: Enhanced entity_biographies.json with relationship categories and summaries
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from datetime import datetime
from collections import Counter

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX_PATH = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
BIOGRAPHIES_PATH = PROJECT_ROOT / "data/metadata/entity_biographies.json"
ONTOLOGY_PATH = PROJECT_ROOT / "data/metadata/entity_relationship_ontology.json"
OUTPUT_PATH = PROJECT_ROOT / "data/metadata/entity_biographies.json"
BACKUP_PATH = PROJECT_ROOT / "data/metadata/entity_biographies_backup_{timestamp}.json"

class EntityCategorizer:
    """Categorizes entities based on relationship ontology"""

    @staticmethod
    def normalize_entity_id(name: str) -> str:
        """
        Convert entity name to normalized ID format (lowercase snake_case)

        Examples:
            'Abby King' -> 'abby_king'
            'Adam Dell' -> 'adam_dell'
            'ABOFF SHELLY' -> 'aboff_shelly'
        """
        return name.lower().replace(' ', '_').replace('-', '_')

    def __init__(self, ontology_path: Path, entities_index_path: Path):
        """Load ontology and entity index"""
        with open(ontology_path, 'r') as f:
            self.ontology = json.load(f)

        with open(entities_index_path, 'r') as f:
            entities_data = json.load(f)

        # Extract entities list from ENTITIES_INDEX
        # Structure: { "entities": [ {...}, {...}, ... ] }
        entities_list = entities_data.get('entities', [])

        # Convert to dictionary keyed by NORMALIZED entity ID
        # This ensures compatibility with entity_biographies.json format
        self.entities_index = {}
        for entity in entities_list:
            # Get the name from ENTITIES_INDEX (Title Case with spaces)
            entity_name = entity.get('normalized_name', entity.get('name', ''))
            if entity_name:
                # Convert to lowercase snake_case to match biography file format
                normalized_id = self.normalize_entity_id(entity_name)
                # Store both normalized ID and original name
                entity['normalized_id'] = normalized_id
                entity['original_name'] = entity_name
                self.entities_index[normalized_id] = entity

        print(f"Loaded {len(self.entities_index)} entities from ENTITIES_INDEX")

    def calculate_confidence(self, entity_data: Dict, category_def: Dict) -> float:
        """
        Calculate confidence score (0.0-1.0) for category assignment

        High confidence (>0.8): Multiple sources, meets all criteria
        Medium confidence (0.65-0.8): Meets some criteria
        Low confidence (<0.65): Minimal evidence
        """
        confidence = 0.5  # Base confidence

        sources = entity_data.get('sources', [])
        source_set = set(s.lower() for s in sources)

        # Check source requirements
        required_sources = category_def.get('sources', [])
        source_logic = category_def.get('source_logic', 'OR')  # Default to OR for backward compatibility

        if required_sources:
            matching_sources = sum(1 for req in required_sources
                                  if any(req.lower() in s for s in source_set))

            if source_logic == 'AND':
                # Require ALL sources to match (stricter for categories like associates)
                if matching_sources == len(required_sources):
                    confidence += 0.3  # Full bonus for meeting all requirements
                else:
                    # Heavily penalize if not all sources present
                    confidence -= 0.2
            else:
                # OR logic: any matching source provides partial credit
                if matching_sources > 0:
                    confidence += 0.2 * (matching_sources / len(required_sources))

        # Check connection thresholds
        connections = entity_data.get('connections', 0)
        if 'min_connections' in category_def and connections >= category_def['min_connections']:
            confidence += 0.2
        if 'max_connections' in category_def and connections <= category_def['max_connections']:
            confidence += 0.1

        # Check flight thresholds
        # Note: ENTITIES_INDEX uses 'flights' field, not 'trips'
        trips = entity_data.get('trips', entity_data.get('flights', 0))
        if 'flights_threshold' in category_def and trips >= category_def['flights_threshold']:
            confidence += 0.3

        # Check keywords in name/biography
        keywords = category_def.get('keywords', [])
        if keywords:
            name = entity_data.get('name', '').lower()
            biography = entity_data.get('biography') or ''
            if biography:
                biography = biography.lower()
            text = f"{name} {biography}"

            matching_keywords = sum(1 for kw in keywords if kw.lower() in text)
            if matching_keywords > 0:
                confidence += 0.2 * (matching_keywords / len(keywords))

        return min(confidence, 1.0)

    def categorize_entity(self, entity_id: str, entity_data: Dict) -> List[Dict]:
        """
        Categorize a single entity based on ontology rules

        Returns list of category assignments with confidence scores
        """
        categories = []

        # Get ontology categories sorted by priority
        primary_relationships = self.ontology.get('primary_relationships', {})
        sorted_categories = sorted(
            primary_relationships.items(),
            key=lambda x: x[1]['priority']
        )

        for cat_type, cat_def in sorted_categories:
            confidence = self.calculate_confidence(entity_data, cat_def)

            # Use stricter threshold for associates category to prevent over-assignment
            threshold = 0.65 if cat_type == 'associates' else 0.5

            if confidence > threshold:
                categories.append({
                    'type': cat_type,
                    'label': cat_def['label'],
                    'color': cat_def['color'],
                    'bg_color': cat_def['bg_color'],
                    'priority': cat_def['priority'],
                    'confidence': 'high' if confidence > 0.8 else 'medium' if confidence > 0.65 else 'low'
                })

        # If no categories assigned, mark as peripheral
        if not categories:
            peripheral_def = primary_relationships.get('peripheral', {})
            categories.append({
                'type': 'peripheral',
                'label': peripheral_def.get('label', 'Peripheral'),
                'color': peripheral_def.get('color', '#6B7280'),
                'bg_color': peripheral_def.get('bg_color', '#F3F4F6'),
                'priority': peripheral_def.get('priority', 9),
                'confidence': 'high'
            })

        return categories

    def determine_document_appearance(self, sources: List[str]) -> str:
        """Determine which document type(s) entity appears in"""
        source_set = set(s.lower() for s in sources)

        has_flight = any('flight' in s for s in source_set)
        has_black_book = any('black' in s or 'birthday' in s or 'book' in s for s in source_set)
        has_court = any('court' in s or 'unsealed' in s or 'deposition' in s for s in source_set)

        source_count = sum([has_flight, has_black_book, has_court])

        if source_count >= 2:
            return 'multiple_sources'
        elif has_flight:
            return 'flight_logs_only'
        elif has_black_book:
            return 'black_book_only'
        elif has_court:
            return 'court_docs_only'
        else:
            return 'unknown'

    def determine_connection_strength(self, connections: int) -> str:
        """Categorize connection strength based on count"""
        if connections >= 10:
            return 'high'
        elif connections >= 3:
            return 'medium'
        else:
            return 'low'

    def generate_biography_summary(self, full_biography: str) -> str:
        """
        Extract first 2-3 sentences from biography as summary

        Returns first 2-3 sentences (max 300 characters)
        """
        if not full_biography:
            return ""

        # Split into sentences
        sentences = re.split(r'[.!?]+\s+', full_biography.strip())

        # Take first 2-3 sentences
        summary_sentences = []
        char_count = 0
        max_chars = 300

        for sentence in sentences[:3]:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Add period if missing
            if not sentence.endswith('.'):
                sentence += '.'

            # Check if adding this sentence exceeds limit
            if char_count + len(sentence) > max_chars and summary_sentences:
                break

            summary_sentences.append(sentence)
            char_count += len(sentence) + 1  # +1 for space

        return ' '.join(summary_sentences)

    def process_all_entities(self, biographies_data: Dict) -> Dict:
        """
        Process all entities from ENTITIES_INDEX

        Merges with existing biography data where available
        """
        existing_entities = biographies_data.get('entities', {})
        updated_entities = {}

        stats = {
            'total_processed': 0,
            'with_biographies': 0,
            'without_biographies': 0,
            'categories_assigned': Counter(),
            'source_distribution': Counter()
        }

        for entity_id, entity_data in self.entities_index.items():
            # entity_id is now normalized (lowercase snake_case)
            # entity_data contains 'original_name' (Title Case) and 'normalized_id'
            stats['total_processed'] += 1

            # Check if entity has biography (using normalized ID)
            has_biography = entity_id in existing_entities
            if has_biography:
                stats['with_biographies'] += 1
                # Start with existing biography data
                updated_entity = existing_entities[entity_id].copy()
                # Ensure display_name uses the original Title Case name
                if 'display_name' not in updated_entity or not updated_entity['display_name']:
                    updated_entity['display_name'] = entity_data.get('original_name', entity_id)
                # Update source_material from ENTITIES_INDEX (critical for categorization)
                updated_entity['source_material'] = entity_data.get('sources', [])
            else:
                stats['without_biographies'] += 1
                # Create new entity entry
                updated_entity = {
                    'id': entity_id,  # Normalized ID (lowercase snake_case)
                    'display_name': entity_data.get('original_name', entity_id),  # Title Case name
                    'biography': None,
                    'source_material': entity_data.get('sources', [])
                }

            # Add entity index data to entity for categorization
            entity_data_with_bio = entity_data.copy()
            if has_biography:
                entity_data_with_bio['biography'] = updated_entity.get('biography', '')

            # Categorize entity
            categories = self.categorize_entity(entity_id, entity_data_with_bio)
            updated_entity['relationship_categories'] = categories

            # Track category statistics
            for cat in categories:
                stats['categories_assigned'][cat['type']] += 1

            # Generate biography summary if biography exists
            if updated_entity.get('biography'):
                summary = self.generate_biography_summary(updated_entity['biography'])
                updated_entity['biography_summary'] = summary
            else:
                updated_entity['biography_summary'] = None

            # Add secondary attributes
            sources = entity_data.get('sources', [])
            connections = entity_data.get('connections', 0)

            updated_entity['secondary_attributes'] = {
                'document_appearance': self.determine_document_appearance(sources),
                'connection_strength': self.determine_connection_strength(connections)
            }

            # Track source distribution
            stats['source_distribution'][updated_entity['secondary_attributes']['document_appearance']] += 1

            updated_entities[entity_id] = updated_entity

        return updated_entities, stats


def main():
    """Main execution"""
    print("Entity Relationship Categorization Script")
    print("=" * 60)

    # Load existing biographies
    print(f"\nLoading existing biographies from: {BIOGRAPHIES_PATH}")
    with open(BIOGRAPHIES_PATH, 'r') as f:
        biographies_data = json.load(f)

    print(f"Loaded {len(biographies_data.get('entities', {}))} existing biographies")

    # Initialize categorizer
    print(f"\nInitializing categorizer with ontology from: {ONTOLOGY_PATH}")
    categorizer = EntityCategorizer(ONTOLOGY_PATH, ENTITIES_INDEX_PATH)

    # Process all entities
    print("\nProcessing all entities...")
    updated_entities, stats = categorizer.process_all_entities(biographies_data)

    # Create backup of original file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = str(BACKUP_PATH).format(timestamp=timestamp)
    print(f"\nCreating backup: {backup_path}")
    with open(backup_path, 'w') as f:
        json.dump(biographies_data, f, indent=2)

    # Update metadata
    metadata = biographies_data.get('metadata', {})
    metadata['total_entities'] = stats['total_processed']
    metadata['entities_with_biographies'] = stats['with_biographies']
    metadata['entities_without_biographies'] = stats['without_biographies']
    metadata['categorization_date'] = datetime.now().isoformat()
    metadata['ontology_version'] = categorizer.ontology.get('version', '1.0.0')

    # Preserve existing metadata stats
    if 'average_quality_score' not in metadata and stats['with_biographies'] > 0:
        # Calculate from entities with quality_score
        quality_scores = [e.get('quality_score', 0) for e in updated_entities.values()
                         if e.get('quality_score')]
        if quality_scores:
            metadata['average_quality_score'] = sum(quality_scores) / len(quality_scores)

    # Build output structure
    output_data = {
        'metadata': metadata,
        'entities': updated_entities
    }

    # Write updated data
    print(f"\nWriting updated data to: {OUTPUT_PATH}")
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("CATEGORIZATION COMPLETE")
    print("=" * 60)
    print(f"\n📊 Processing Summary:")
    print(f"   Total Entities Processed: {stats['total_processed']}")
    print(f"   With Biographies: {stats['with_biographies']}")
    print(f"   Without Biographies: {stats['without_biographies']}")

    print(f"\n📋 Category Distribution:")
    for cat_type, count in stats['categories_assigned'].most_common():
        print(f"   {cat_type}: {count}")

    print(f"\n📄 Source Distribution:")
    for source_type, count in stats['source_distribution'].most_common():
        print(f"   {source_type}: {count}")

    print(f"\n✅ Output written to: {OUTPUT_PATH}")
    print(f"💾 Backup created at: {backup_path}")


if __name__ == '__main__':
    main()
