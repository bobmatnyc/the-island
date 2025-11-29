#!/usr/bin/env python3
"""
Extract Non-Human Entities from Documents

This script extracts organizations and locations mentioned in the Epstein archive
documents, distinct from the contact book person entities.

Strategy:
1. Use spaCy NER to identify ORG and GPE (location) entities in documents
2. Use LLM to classify and generate biographies for extracted entities
3. Create separate entity_organizations.json and entity_locations.json files
4. These will be merged with person entities for unified entity system

Features:
- Extract from all document text files
- Frequency-based filtering (entities mentioned multiple times)
- LLM-based biography generation with document context
- Deduplication and normalization

Usage:
    python scripts/analysis/extract_nonhuman_entities.py [--entity-type {org,location,all}] [--min-mentions 5] [--dry-run]

Requirements:
    - spaCy with en_core_web_lg model
    - OPENROUTER_API_KEY for biography generation
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple

# Load environment variables
env_file = Path(__file__).parent.parent.parent / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'server'))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    logger.error("spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_lg")
    SPACY_AVAILABLE = False

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    logger.warning("tqdm not available. Install with: pip install tqdm")
    TQDM_AVAILABLE = False
    def tqdm(iterable, **kwargs):
        return iterable


class NonHumanEntityExtractor:
    """Extract organizations and locations from Epstein archive documents."""

    def __init__(
        self,
        data_dir: Path,
        entity_type: str = 'all',
        min_mentions: int = 5,
        dry_run: bool = False
    ):
        """Initialize extractor.

        Args:
            data_dir: Path to data directory containing documents
            entity_type: 'org', 'location', or 'all'
            min_mentions: Minimum number of mentions required
            dry_run: If True, don't write results to disk
        """
        self.data_dir = data_dir
        self.entity_type = entity_type
        self.min_mentions = min_mentions
        self.dry_run = dry_run

        # Entity tracking
        self.organizations: Dict[str, Dict[str, Any]] = {}
        self.locations: Dict[str, Dict[str, Any]] = {}
        self.entity_mentions: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # entity -> [(doc_path, context)]

        # Statistics
        self.stats = {
            'documents_processed': 0,
            'organizations_found': 0,
            'locations_found': 0,
            'organizations_filtered': 0,
            'locations_filtered': 0
        }

        # Load spaCy model
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_lg")
                logger.info("Loaded spaCy en_core_web_lg model")
            except OSError:
                logger.error("spaCy model en_core_web_lg not found. Download with: python -m spacy download en_core_web_lg")
                sys.exit(1)
        else:
            sys.exit(1)

    def find_document_files(self) -> List[Path]:
        """Find all text document files in the archive.

        Returns:
            List of paths to text files
        """
        doc_dirs = [
            self.data_dir / 'sources' / 'house_oversight_nov2025' / 'ocr_text',
            self.data_dir / 'sources' / 'black_book' / 'text',
            self.data_dir / 'sources' / 'flight_logs' / 'text',
        ]

        doc_files = []
        for doc_dir in doc_dirs:
            if doc_dir.exists():
                doc_files.extend(doc_dir.glob('**/*.txt'))

        logger.info(f"Found {len(doc_files)} document files")
        return doc_files

    def extract_entities_from_text(self, text: str, doc_path: str) -> Tuple[Set[str], Set[str]]:
        """Extract organizations and locations from text using spaCy NER.

        Args:
            text: Document text content
            doc_path: Path to document (for tracking)

        Returns:
            Tuple of (organizations, locations) sets
        """
        # Process text with spaCy
        doc = self.nlp(text[:100000])  # Limit to first 100k chars for performance

        organizations = set()
        locations = set()

        for ent in doc.ents:
            # Skip very short entities
            if len(ent.text) < 3:
                continue

            # Extract organizations
            if ent.label_ == 'ORG' and (self.entity_type in ['org', 'all']):
                # Normalize entity name
                org_name = self.normalize_entity_name(ent.text)
                if self.is_valid_organization(org_name):
                    organizations.add(org_name)
                    # Store context
                    context = self.extract_context(text, ent.start_char, ent.end_char)
                    self.entity_mentions[f"org:{org_name}"].append((doc_path, context))

            # Extract locations (GPE = Geo-Political Entity, LOC = Location)
            if ent.label_ in ['GPE', 'LOC'] and (self.entity_type in ['location', 'all']):
                loc_name = self.normalize_entity_name(ent.text)
                if self.is_valid_location(loc_name):
                    locations.add(loc_name)
                    # Store context
                    context = self.extract_context(text, ent.start_char, ent.end_char)
                    self.entity_mentions[f"loc:{loc_name}"].append((doc_path, context))

        return organizations, locations

    def normalize_entity_name(self, name: str) -> str:
        """Normalize entity name for consistency.

        Args:
            name: Raw entity name

        Returns:
            Normalized name
        """
        # Remove extra whitespace
        name = ' '.join(name.split())

        # Remove common suffixes for deduplication
        # (We'll keep the full name for display, but use normalized for matching)
        return name.strip()

    def is_valid_organization(self, name: str) -> bool:
        """Check if organization name is valid and should be kept.

        Args:
            name: Organization name

        Returns:
            True if valid
        """
        # Skip single words (often misclassified)
        if ' ' not in name and len(name) < 10:
            return False

        # Skip common false positives
        false_positives = {'the', 'a', 'an', 'and', 'or', 'but'}
        if name.lower() in false_positives:
            return False

        # Must have some letters
        if not any(c.isalpha() for c in name):
            return False

        return True

    def is_valid_location(self, name: str) -> bool:
        """Check if location name is valid and should be kept.

        Args:
            name: Location name

        Returns:
            True if valid
        """
        # Skip very short names
        if len(name) < 3:
            return False

        # Skip common false positives
        false_positives = {'the', 'a', 'an', 'and', 'or', 'but', 'us', 'mr', 'ms', 'dr'}
        if name.lower() in false_positives:
            return False

        return True

    def extract_context(self, text: str, start: int, end: int, window: int = 200) -> str:
        """Extract context around an entity mention.

        Args:
            text: Full text
            start: Start position of entity
            end: End position of entity
            window: Characters to include on each side

        Returns:
            Context string
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        context = text[context_start:context_end]

        # Clean up
        context = ' '.join(context.split())
        return context

    def process_documents(self, doc_files: List[Path]) -> None:
        """Process all documents to extract entities.

        Args:
            doc_files: List of document file paths
        """
        logger.info(f"Processing {len(doc_files)} documents...")

        # Progress bar
        if TQDM_AVAILABLE:
            progress = tqdm(doc_files, desc="Extracting entities", unit="doc")
        else:
            progress = doc_files

        for doc_path in progress:
            try:
                # Read document
                with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()

                # Extract entities
                orgs, locs = self.extract_entities_from_text(text, str(doc_path))

                # Update statistics
                self.stats['documents_processed'] += 1
                self.stats['organizations_found'] += len(orgs)
                self.stats['locations_found'] += len(locs)

            except Exception as e:
                logger.error(f"Error processing {doc_path}: {e}")
                continue

    def filter_by_mentions(self) -> None:
        """Filter entities by minimum mention count."""
        logger.info(f"Filtering entities with < {self.min_mentions} mentions...")

        # Count mentions for each entity
        org_counts = Counter()
        loc_counts = Counter()

        for entity_key, mentions in self.entity_mentions.items():
            entity_type, entity_name = entity_key.split(':', 1)
            mention_count = len(mentions)

            if mention_count >= self.min_mentions:
                if entity_type == 'org':
                    org_counts[entity_name] = mention_count
                    self.organizations[entity_name] = {
                        'name': entity_name,
                        'entity_type': 'organization',
                        'mention_count': mention_count,
                        'documents': [doc for doc, _ in mentions],
                        'contexts': [ctx for _, ctx in mentions[:5]]  # Keep first 5 contexts
                    }
                elif entity_type == 'loc':
                    loc_counts[entity_name] = mention_count
                    self.locations[entity_name] = {
                        'name': entity_name,
                        'entity_type': 'location',
                        'mention_count': mention_count,
                        'documents': [doc for doc, _ in mentions],
                        'contexts': [ctx for _, ctx in mentions[:5]]
                    }

        self.stats['organizations_filtered'] = len(self.organizations)
        self.stats['locations_filtered'] = len(self.locations)

        logger.info(f"Organizations after filtering: {len(self.organizations)}")
        logger.info(f"Locations after filtering: {len(self.locations)}")

    def generate_biographies(self) -> None:
        """Generate LLM-based biographies for extracted entities.

        This will use the EntityService's LLM integration to generate
        biographical summaries based on document contexts.
        """
        logger.info("Biography generation will be implemented in next phase")
        logger.info("For now, creating placeholder biographies from contexts")

        # For organizations
        for org_name, org_data in self.organizations.items():
            # Create simple biography from contexts
            contexts = org_data['contexts']
            if contexts:
                bio = f"{org_name} is mentioned {org_data['mention_count']} times in the Epstein archive documents. "
                bio += f"Context: {contexts[0][:500]}..."
            else:
                bio = f"{org_name} appears in the Epstein archive documents."

            org_data['biography'] = bio

        # For locations
        for loc_name, loc_data in self.locations.items():
            contexts = loc_data['contexts']
            if contexts:
                bio = f"{loc_name} is mentioned {loc_data['mention_count']} times in the Epstein archive documents. "
                bio += f"Context: {contexts[0][:500]}..."
            else:
                bio = f"{loc_name} appears in the Epstein archive documents."

            loc_data['biography'] = bio

    def save_results(self) -> None:
        """Save extracted entities to JSON files."""
        if self.dry_run:
            logger.info("DRY RUN: Would save results to disk")
            return

        output_dir = self.data_dir / 'metadata'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save organizations
        if self.entity_type in ['org', 'all'] and self.organizations:
            org_file = output_dir / 'entity_organizations.json'
            org_data = {
                'metadata': {
                    'extraction_date': datetime.now().isoformat(),
                    'total_organizations': len(self.organizations),
                    'min_mentions': self.min_mentions
                },
                'entities': self.organizations
            }

            with open(org_file, 'w', encoding='utf-8') as f:
                json.dump(org_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self.organizations)} organizations to {org_file}")

        # Save locations
        if self.entity_type in ['location', 'all'] and self.locations:
            loc_file = output_dir / 'entity_locations.json'
            loc_data = {
                'metadata': {
                    'extraction_date': datetime.now().isoformat(),
                    'total_locations': len(self.locations),
                    'min_mentions': self.min_mentions
                },
                'entities': self.locations
            }

            with open(loc_file, 'w', encoding='utf-8') as f:
                json.dump(loc_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self.locations)} locations to {loc_file}")

    def print_statistics(self) -> None:
        """Print extraction statistics."""
        print("\n" + "="*60)
        print("ENTITY EXTRACTION STATISTICS")
        print("="*60)
        print(f"Documents processed: {self.stats['documents_processed']}")
        print(f"\nEntities found (before filtering):")
        print(f"  Organizations: {self.stats['organizations_found']}")
        print(f"  Locations: {self.stats['locations_found']}")
        print(f"\nEntities kept (>= {self.min_mentions} mentions):")
        print(f"  Organizations: {self.stats['organizations_filtered']}")
        print(f"  Locations: {self.stats['locations_filtered']}")
        print("="*60 + "\n")

        # Show top entities
        if self.organizations:
            print("Top 10 Organizations by mentions:")
            sorted_orgs = sorted(
                self.organizations.items(),
                key=lambda x: x[1]['mention_count'],
                reverse=True
            )[:10]
            for org_name, org_data in sorted_orgs:
                print(f"  {org_name}: {org_data['mention_count']} mentions")

        if self.locations:
            print("\nTop 10 Locations by mentions:")
            sorted_locs = sorted(
                self.locations.items(),
                key=lambda x: x[1]['mention_count'],
                reverse=True
            )[:10]
            for loc_name, loc_data in sorted_locs:
                print(f"  {loc_name}: {loc_data['mention_count']} mentions")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract non-human entities (organizations, locations) from documents"
    )
    parser.add_argument(
        '--entity-type',
        choices=['org', 'location', 'all'],
        default='all',
        help="Type of entities to extract"
    )
    parser.add_argument(
        '--min-mentions',
        type=int,
        default=5,
        help="Minimum number of mentions required (default: 5)"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't write results to disk"
    )
    parser.add_argument(
        '--data-dir',
        type=Path,
        default=Path(__file__).parent.parent.parent / 'data',
        help="Path to data directory (default: data/)"
    )

    args = parser.parse_args()

    # Validate data directory
    if not args.data_dir.exists():
        logger.error(f"Data directory not found: {args.data_dir}")
        sys.exit(1)

    # Initialize extractor
    extractor = NonHumanEntityExtractor(
        data_dir=args.data_dir,
        entity_type=args.entity_type,
        min_mentions=args.min_mentions,
        dry_run=args.dry_run
    )

    # Find documents
    doc_files = extractor.find_document_files()
    if not doc_files:
        logger.error("No document files found")
        sys.exit(1)

    # Process documents
    extractor.process_documents(doc_files)

    # Filter by mentions
    extractor.filter_by_mentions()

    # Generate biographies
    extractor.generate_biographies()

    # Save results
    extractor.save_results()

    # Print statistics
    extractor.print_statistics()

    logger.info("Extraction complete!")


if __name__ == '__main__':
    main()
