#!/usr/bin/env python3
"""
ChromaDB Entity Indexing Script

Indexes all Epstein entities (persons, locations, organizations) into ChromaDB
for vector search and semantic retrieval.

Usage:
    python scripts/chromadb/index_entities.py [--reset] [--limit N]

Options:
    --reset: Delete existing collection and start fresh
    --limit N: Index only first N entities (for testing)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import (
    BATCH_SIZE,
    CHROMADB_DIR,
    DATA_DIR,
    EMBEDDING_MODEL,
    PROGRESS_INTERVAL,
    VERBOSE,
)

# Entity-specific configuration
ENTITY_COLLECTION_NAME = "epstein_entities"
ENTITIES_PERSONS_PATH = DATA_DIR / "transformed" / "entities_persons.json"
ENTITIES_LOCATIONS_PATH = DATA_DIR / "transformed" / "entities_locations.json"
ENTITIES_ORGANIZATIONS_PATH = DATA_DIR / "transformed" / "entities_organizations.json"
ENTITY_CLASSIFICATIONS_PATH = DATA_DIR / "transformed" / "entity_classifications_derived.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO if VERBOSE else logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class EntityIndexer:
    """Index entities into ChromaDB with rich metadata for semantic search."""

    def __init__(self, reset: bool = False):
        """Initialize ChromaDB client and collection.

        Args:
            reset: If True, delete existing collection and start fresh
        """
        self.reset = reset
        self.stats = {
            "total_entities": 0,
            "indexed": 0,
            "with_biography": 0,
            "with_classifications": 0,
            "by_type": {"person": 0, "location": 0, "organization": 0},
            "errors": 0,
        }

        # Initialize ChromaDB
        logger.info(f"Initializing ChromaDB at {CHROMADB_DIR}")
        CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(CHROMADB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        if reset:
            try:
                self.client.delete_collection(name=ENTITY_COLLECTION_NAME)
                logger.info(f"Deleted existing collection: {ENTITY_COLLECTION_NAME}")
            except Exception as e:
                # Collection doesn't exist - this is fine
                logger.debug(f"Collection does not exist yet: {e}")

        self.collection = self.client.get_or_create_collection(
            name=ENTITY_COLLECTION_NAME,
            metadata={
                "description": "Epstein entity archive with semantic embeddings",
                "embedding_model": EMBEDDING_MODEL,
            },
        )

        logger.info(f"Collection '{ENTITY_COLLECTION_NAME}' ready")
        logger.info(f"Using embedding model: {EMBEDDING_MODEL}")

    def load_data(self) -> Dict:
        """Load all entity data sources into memory.

        Returns:
            Dictionary with loaded data: entities (by type), classifications
        """
        logger.info("Loading entity data files...")

        # Load entities by type
        entities = {}

        with open(ENTITIES_PERSONS_PATH) as f:
            persons_data = json.load(f)
            entities.update(persons_data["entities"])
            logger.info(f"Loaded {len(persons_data['entities'])} persons")

        with open(ENTITIES_LOCATIONS_PATH) as f:
            locations_data = json.load(f)
            entities.update(locations_data["entities"])
            logger.info(f"Loaded {len(locations_data['entities'])} locations")

        with open(ENTITIES_ORGANIZATIONS_PATH) as f:
            orgs_data = json.load(f)
            entities.update(orgs_data["entities"])
            logger.info(f"Loaded {len(orgs_data['entities'])} organizations")

        # Load classifications
        with open(ENTITY_CLASSIFICATIONS_PATH) as f:
            classifications_data = json.load(f)
            classifications = classifications_data["entities"]
            logger.info(
                f"Loaded classifications for {len(classifications)} entities"
            )

        logger.info(f"Total entities loaded: {len(entities)}")

        return {
            "entities": entities,
            "classifications": classifications,
        }

    def build_entity_text(self, entity: Dict, classifications: List[Dict]) -> str:
        """Build rich text content for entity embedding.

        Strategy: Combine multiple fields to create semantic-rich text:
        1. Entity type and canonical name
        2. Aliases (for name variations)
        3. Biography (if available)
        4. Classification labels (for context)

        Args:
            entity: Entity data
            classifications: List of classification objects

        Returns:
            Rich text string for embedding
        """
        text_parts = []

        # Part 1: Type and name
        entity_type = entity.get("entity_type", "unknown")
        canonical_name = entity.get("canonical_name", "Unknown")
        text_parts.append(f"{canonical_name} ({entity_type})")

        # Part 2: Biography (truncate if very long)
        biography = entity.get("biography")
        if biography:
            # Truncate to first 500 chars for embedding efficiency
            bio_text = biography.strip()
            if len(bio_text) > 500:
                bio_text = bio_text[:500] + "..."
            text_parts.append(bio_text)

        # Part 3: Aliases
        aliases = entity.get("aliases", [])
        if aliases and len(aliases) > 1:  # More than just canonical name
            # Deduplicate and filter out canonical name
            unique_aliases = [a for a in aliases if a.lower() != canonical_name.lower()]
            if unique_aliases:
                text_parts.append(f"Also known as: {', '.join(unique_aliases[:5])}")

        # Part 4: Classifications
        if classifications:
            labels = [c.get("label", "") for c in classifications]
            labels = [l for l in labels if l]  # Filter empty
            if labels:
                text_parts.append(f"Classifications: {', '.join(labels)}")

        return ". ".join(text_parts)

    def prepare_metadata(self, entity: Dict, classifications: List[Dict]) -> Dict:
        """Prepare metadata for ChromaDB storage.

        Args:
            entity: Entity data
            classifications: List of classification objects

        Returns:
            Metadata dictionary with ChromaDB-compatible types
        """
        # Extract classification info
        classification_labels = []
        highest_confidence = 0.0
        for c in classifications:
            label = c.get("label", "")
            if label:
                classification_labels.append(label)
            confidence = c.get("confidence", 0.0)
            if isinstance(confidence, (int, float)) and confidence > highest_confidence:
                highest_confidence = confidence

        metadata = {
            "entity_type": entity.get("entity_type", "unknown"),
            "canonical_name": entity.get("canonical_name", "Unknown"),
            "normalized_name": entity.get("normalized_name", ""),
            "document_count": int(entity.get("document_count", 0)),
            "connection_count": int(entity.get("connection_count", 0)),
            "has_biography": bool(entity.get("biography")),
            "classifications": ",".join(classification_labels),
            "classification_confidence": float(highest_confidence),
            "alias_count": len(entity.get("aliases", [])),
        }

        # ChromaDB requires all metadata values to be str, int, float, or bool
        # Convert any None to empty string
        for key, value in metadata.items():
            if value is None:
                metadata[key] = ""

        return metadata

    def index_entities(self, limit: Optional[int] = None):
        """Index entities in batches.

        Args:
            limit: Maximum number of entities to index (for testing)
        """
        data = self.load_data()
        entities = data["entities"]
        classifications = data["classifications"]

        # Determine entities to index
        entity_ids = list(entities.keys())
        if limit:
            entity_ids = entity_ids[:limit]
            logger.info(f"Limiting to first {limit} entities")

        self.stats["total_entities"] = len(entity_ids)
        logger.info(f"Starting indexing of {len(entity_ids)} entities...")

        # Process in batches
        for i in tqdm(range(0, len(entity_ids), BATCH_SIZE), desc="Indexing batches"):
            batch_ids = entity_ids[i : i + BATCH_SIZE]
            batch_documents = []
            batch_metadatas = []
            batch_ids_clean = []

            for entity_id in batch_ids:
                try:
                    entity = entities[entity_id]
                    entity_type = entity.get("entity_type", "unknown")

                    # Get classifications for this entity
                    entity_classifications = classifications.get(entity_id, {}).get(
                        "classifications", []
                    )

                    # Build text content
                    text_content = self.build_entity_text(
                        entity, entity_classifications
                    )

                    # Prepare metadata
                    metadata = self.prepare_metadata(entity, entity_classifications)

                    batch_documents.append(text_content)
                    batch_metadatas.append(metadata)
                    batch_ids_clean.append(entity_id)

                    # Update stats
                    self.stats["by_type"][entity_type] = (
                        self.stats["by_type"].get(entity_type, 0) + 1
                    )
                    if entity.get("biography"):
                        self.stats["with_biography"] += 1
                    if entity_classifications:
                        self.stats["with_classifications"] += 1

                except Exception as e:
                    logger.error(f"Error preparing entity {entity_id}: {e}")
                    self.stats["errors"] += 1

            # Add batch to collection (upsert for safe re-indexing)
            if batch_documents:
                try:
                    self.collection.upsert(
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        ids=batch_ids_clean,
                    )
                    self.stats["indexed"] += len(batch_documents)

                    if (i // BATCH_SIZE) % (PROGRESS_INTERVAL // BATCH_SIZE) == 0:
                        logger.info(
                            f"Progress: {self.stats['indexed']}/{self.stats['total_entities']} "
                            f"({self.stats['indexed']/self.stats['total_entities']*100:.1f}%)"
                        )

                except Exception as e:
                    logger.error(f"Error adding batch {i}: {e}")
                    self.stats["errors"] += len(batch_documents)

        logger.info("Indexing complete!")

    def print_statistics(self):
        """Print indexing statistics."""
        print("\n" + "=" * 60)
        print("ENTITY INDEXING STATISTICS")
        print("=" * 60)
        print(f"Total entities processed: {self.stats['total_entities']}")
        print(f"Successfully indexed: {self.stats['indexed']}")
        print(f"  - Persons: {self.stats['by_type'].get('person', 0)}")
        print(f"  - Locations: {self.stats['by_type'].get('location', 0)}")
        print(f"  - Organizations: {self.stats['by_type'].get('organization', 0)}")
        print(f"  - With biography: {self.stats['with_biography']}")
        print(f"  - With classifications: {self.stats['with_classifications']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"\nCollection size: {self.collection.count()} entities")
        print(f"ChromaDB location: {CHROMADB_DIR}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Index Epstein entities into ChromaDB"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collection and start fresh",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of entities to index (for testing)",
    )

    args = parser.parse_args()

    try:
        indexer = EntityIndexer(reset=args.reset)
        indexer.index_entities(limit=args.limit)
        indexer.print_statistics()

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
