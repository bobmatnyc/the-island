#!/usr/bin/env python3
"""
Batch Entity Type Classification Script

Classifies all entities in entity_biographies.json using the existing 3-tier
LLM classification system:
- Tier 1: LLM (OpenRouter/Claude Haiku) - Primary method
- Tier 2: NLP (spaCy NER) - Fallback
- Tier 3: Keyword matching - Last resort

Usage:
    python scripts/analysis/classify_entity_types.py [--dry-run]

Requirements:
    - OPENROUTER_API_KEY environment variable for LLM classification
    - ENABLE_LLM_CLASSIFICATION=true (default)
    - ENABLE_NLP_CLASSIFICATION=true (default)

Output:
    - Creates backup: entity_biographies_backup_{timestamp}.json
    - Updates original file with entity_type field
    - Prints classification statistics

Cost Estimate:
    - ~$0.02 for all 1,637 entities using Claude Haiku
    - Processing time: 30-60 seconds
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Load environment variables from .env.local if it exists
env_file = Path(__file__).parent.parent.parent / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Force enable LLM classification for batch processing
# This overrides the .env.local setting to use the 3-tier system
os.environ['ENABLE_LLM_CLASSIFICATION'] = 'true'
os.environ.setdefault('ENABLE_NLP_CLASSIFICATION', 'true')

# Add project root and server directory to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'server'))

# Import the existing entity service
from services.entity_service import EntityService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import tqdm for progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    logger.warning("tqdm not available, progress bar disabled. Install with: pip install tqdm")
    TQDM_AVAILABLE = False
    # Fallback: tqdm that just iterates
    def tqdm(iterable, **kwargs):
        return iterable


class EntityTypeClassifier:
    """Batch classifier for entity types using existing EntityService."""

    def __init__(self, data_path: Path, dry_run: bool = False):
        """Initialize classifier.

        Args:
            data_path: Path to entity_biographies.json
            dry_run: If True, don't write changes to disk
        """
        self.data_path = data_path
        self.dry_run = dry_run

        # Initialize EntityService with data directory (parent of metadata)
        data_dir = data_path.parent.parent  # Go up from metadata/entity_biographies.json to data/
        self.entity_service = EntityService(data_dir)

        # Statistics tracking
        self.stats = {
            'total': 0,
            'processed': 0,
            'skipped_already_classified': 0,
            'by_type': {
                'person': 0,
                'organization': 0,
                'location': 0
            },
            'by_method': {
                'llm': 0,
                'nlp': 0,
                'keyword': 0
            }
        }

    def load_entities(self) -> Dict[str, Any]:
        """Load entity biographies JSON file.

        Returns:
            Dictionary with metadata and entities
        """
        logger.info(f"Loading entities from {self.data_path}")
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Loaded {len(data.get('entities', {}))} entities")
        return data

    def create_backup(self, data: Dict[str, Any]) -> Path:
        """Create timestamped backup of original file.

        Args:
            data: Original data to back up

        Returns:
            Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.data_path.parent / f"entity_biographies_backup_{timestamp}.json"

        logger.info(f"Creating backup: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return backup_path

    def classify_single_entity(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        show_progress: bool = True
    ) -> Optional[str]:
        """Classify a single entity using EntityService.

        Args:
            entity_id: Entity identifier
            entity_data: Entity metadata (name, bio, etc.)
            show_progress: Whether to log progress for debugging

        Returns:
            Entity type ('person', 'organization', 'location') or None if error
        """
        try:
            # Build context for LLM classification
            context = {}
            if 'summary' in entity_data:
                context['bio'] = entity_data['summary']

            entity_name = entity_data.get('name', entity_id)

            if show_progress and self.stats['processed'] % 100 == 0:
                logger.info(f"Processing entity {self.stats['processed'] + 1}/{self.stats['total']}: {entity_name}")

            # Use the existing detect_entity_type method
            entity_type = self.entity_service.detect_entity_type(
                entity_name=entity_name,
                context=context if context else None
            )

            return entity_type

        except Exception as e:
            logger.error(f"Failed to classify '{entity_id}' ({entity_data.get('name', entity_id)}): {e}")
            return None

    def detect_classification_method(self) -> str:
        """Detect which classification method will be used.

        Returns:
            'llm', 'nlp', or 'keyword'
        """
        # Check if LLM is enabled
        enable_llm = os.getenv("ENABLE_LLM_CLASSIFICATION", "true").lower() == "true"
        api_key = os.environ.get("OPENROUTER_API_KEY")

        if enable_llm and api_key:
            return 'llm'

        # Check if NLP is enabled
        enable_nlp = os.getenv("ENABLE_NLP_CLASSIFICATION", "true").lower() == "true"
        if enable_nlp:
            return 'nlp'

        return 'keyword'

    def classify_all(self, data: Dict[str, Any], force: bool = False) -> Dict[str, Any]:
        """Classify all entities in the dataset.

        Args:
            data: Full entity biographies data
            force: If True, reclassify even if entity_type already exists

        Returns:
            Updated data with entity_type fields
        """
        entities = data.get('entities', {})
        self.stats['total'] = len(entities)

        logger.info(f"Starting classification of {self.stats['total']} entities")
        logger.info(f"Feature flags: LLM={os.getenv('ENABLE_LLM_CLASSIFICATION', 'true')}, "
                   f"NLP={os.getenv('ENABLE_NLP_CLASSIFICATION', 'true')}")

        # Create progress bar
        entity_items = list(entities.items())
        if TQDM_AVAILABLE:
            progress = tqdm(entity_items, desc="Classifying entities", unit="entity")
        else:
            progress = entity_items
            logger.info("Processing entities (no progress bar)...")

        for entity_id, entity_data in progress:
            # Skip if already classified and not forcing
            if not force and 'entity_type' in entity_data:
                self.stats['skipped_already_classified'] += 1
                continue

            # Classify the entity
            entity_type = self.classify_single_entity(entity_id, entity_data)

            if entity_type:
                # Update entity data
                entity_data['entity_type'] = entity_type

                # Update statistics
                self.stats['processed'] += 1
                self.stats['by_type'][entity_type] = self.stats['by_type'].get(entity_type, 0) + 1

                # Track method (simple heuristic based on detection)
                method = self.detect_classification_method()
                self.stats['by_method'][method] = self.stats['by_method'].get(method, 0) + 1

                if TQDM_AVAILABLE:
                    progress.set_postfix({
                        'type': entity_type,
                        'person': self.stats['by_type']['person'],
                        'org': self.stats['by_type']['organization'],
                        'loc': self.stats['by_type']['location']
                    })

        return data

    def save_results(self, data: Dict[str, Any]) -> None:
        """Save classified entities to file.

        Args:
            data: Updated entity data
        """
        if self.dry_run:
            logger.info("DRY RUN: Would save results to disk")
            return

        logger.info(f"Saving results to {self.data_path}")

        # Update metadata
        if 'metadata' not in data:
            data['metadata'] = {}

        data['metadata']['last_classification'] = datetime.now().isoformat()
        data['metadata']['classification_stats'] = {
            'total_classified': self.stats['processed'],
            'by_type': self.stats['by_type'],
            'by_method': self.stats['by_method']
        }

        # Write to file with proper formatting
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info("Results saved successfully")

    def print_statistics(self, start_time: datetime, end_time: datetime) -> None:
        """Print classification statistics.

        Args:
            start_time: Processing start time
            end_time: Processing end time
        """
        duration = (end_time - start_time).total_seconds()

        print("\n" + "="*60)
        print("CLASSIFICATION STATISTICS")
        print("="*60)
        print(f"Total entities: {self.stats['total']}")
        print(f"Newly classified: {self.stats['processed']}")
        print(f"Already classified (skipped): {self.stats['skipped_already_classified']}")
        print(f"Processing time: {duration:.2f} seconds")

        print("\n" + "-"*60)
        print("CLASSIFICATION BY TYPE:")
        print("-"*60)
        total_classified = sum(self.stats['by_type'].values())
        for entity_type, count in sorted(self.stats['by_type'].items()):
            percentage = (count / total_classified * 100) if total_classified > 0 else 0
            print(f"  {entity_type.capitalize():15s}: {count:4d} ({percentage:5.1f}%)")

        print("\n" + "-"*60)
        print("CLASSIFICATION BY METHOD:")
        print("-"*60)
        for method, count in sorted(self.stats['by_method'].items()):
            percentage = (count / self.stats['processed'] * 100) if self.stats['processed'] > 0 else 0
            print(f"  {method.upper():15s}: {count:4d} ({percentage:5.1f}%)")

        print("\n" + "="*60)

        # Cost estimate (if using LLM)
        if self.stats['by_method'].get('llm', 0) > 0:
            # Claude Haiku pricing: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
            # Estimate: ~100 input tokens/entity, ~5 output tokens/entity
            llm_count = self.stats['by_method']['llm']
            estimated_input_tokens = llm_count * 100
            estimated_output_tokens = llm_count * 5
            estimated_cost = (estimated_input_tokens * 0.25 / 1_000_000 +
                            estimated_output_tokens * 1.25 / 1_000_000)
            print(f"Estimated LLM cost: ${estimated_cost:.4f}")
            print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Batch classify entity types using 3-tier LLM system"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Don't write changes to disk"
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help="Reclassify entities that already have entity_type"
    )
    parser.add_argument(
        '--data-path',
        type=Path,
        default=Path(__file__).parent.parent.parent / "data/metadata/entity_biographies.json",
        help="Path to entity_biographies.json (default: data/metadata/entity_biographies.json)"
    )

    args = parser.parse_args()

    # Validate data path
    if not args.data_path.exists():
        logger.error(f"Data file not found: {args.data_path}")
        sys.exit(1)

    # Check for OPENROUTER_API_KEY
    if not os.environ.get("OPENROUTER_API_KEY"):
        logger.warning("OPENROUTER_API_KEY not set - will fall back to NLP/keyword classification")

    # Initialize classifier
    classifier = EntityTypeClassifier(args.data_path, dry_run=args.dry_run)

    # Load entities
    data = classifier.load_entities()

    # Create backup (unless dry run)
    if not args.dry_run:
        backup_path = classifier.create_backup(data)
        logger.info(f"Backup created: {backup_path}")

    # Classify all entities
    start_time = datetime.now()
    updated_data = classifier.classify_all(data, force=args.force)
    end_time = datetime.now()

    # Save results
    classifier.save_results(updated_data)

    # Print statistics
    classifier.print_statistics(start_time, end_time)

    logger.info("Classification complete!")


if __name__ == '__main__':
    main()
