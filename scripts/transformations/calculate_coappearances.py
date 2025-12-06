#!/usr/bin/env python3
"""Calculate entity co-appearances across all documents.

This script:
1. Reads document-to-entities mapping
2. Calculates pairs of entities appearing in same documents
3. Tracks co-appearance frequency and document types
4. Outputs structured co-appearance data

Performance: Optimized for 31,111 documents using itertools.combinations.
"""

import json
from collections import defaultdict
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TRANSFORMED_DIR = DATA_DIR / "transformed"
METADATA_DIR = DATA_DIR / "metadata"


def load_json(filepath: Path) -> dict:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        raise


def load_entity_uuid_mappings() -> Dict[str, dict]:
    """Load entity UUID mappings for entity metadata.

    Returns:
        Dict mapping normalized names to entity metadata (uuid, type, etc.)
    """
    logger.info("Loading entity UUID mappings...")
    uuid_file = TRANSFORMED_DIR / "entity_uuid_mappings.json"

    if not uuid_file.exists():
        logger.warning(f"UUID mappings not found at {uuid_file}")
        return {}

    data = load_json(uuid_file)
    mappings = data.get("mappings", {})

    # Create reverse lookup: normalized_name -> entity metadata
    name_to_entity = {}
    for uuid, entity in mappings.items():
        normalized_name = entity.get("normalized_name", "")
        name_to_entity[normalized_name] = {
            "id": uuid,
            "name": entity.get("canonical_name", ""),
            "type": entity.get("entity_type", "unknown")
        }
        # Also index by canonical name (lowercased)
        canonical = entity.get("canonical_name", "").lower()
        if canonical and canonical != normalized_name:
            name_to_entity[canonical] = {
                "id": uuid,
                "name": entity.get("canonical_name", ""),
                "type": entity.get("entity_type", "unknown")
            }
        # Also index by aliases
        for alias in entity.get("aliases", []):
            alias_lower = alias.lower()
            if alias_lower not in name_to_entity:
                name_to_entity[alias_lower] = {
                    "id": uuid,
                    "name": entity.get("canonical_name", ""),
                    "type": entity.get("entity_type", "unknown")
                }

    logger.info(f"Loaded {len(name_to_entity)} entity name mappings")
    return name_to_entity


def get_entity_metadata(entity_name: str, uuid_mappings: Dict[str, dict]) -> dict:
    """Get entity metadata (UUID, type) for a given entity name.

    Args:
        entity_name: Entity name from document_to_entities (lowercase)
        uuid_mappings: Name to entity metadata mapping

    Returns:
        Dict with id, name, type
    """
    # Try direct lookup
    if entity_name in uuid_mappings:
        return uuid_mappings[entity_name]

    # Try normalized version (replace spaces with underscores)
    normalized = entity_name.replace(" ", "_")
    if normalized in uuid_mappings:
        return uuid_mappings[normalized]

    # Fallback: create synthetic ID from name
    # Use title case for name display
    display_name = entity_name.title()
    return {
        "id": f"unmapped_{entity_name.replace(' ', '_')}",
        "name": display_name,
        "type": "unknown"
    }


def calculate_coappearances(
    doc_to_entities: Dict[str, List[str]],
    uuid_mappings: Dict[str, dict],
    min_coappearances: int = 2
) -> List[dict]:
    """Calculate entity co-appearances across documents.

    Args:
        doc_to_entities: Mapping of document_id -> list of entity names
        uuid_mappings: Entity name to metadata mapping
        min_coappearances: Minimum co-appearances to include (default: 2)

    Returns:
        List of co-appearance dicts with entity pairs and stats
    """
    logger.info(f"Calculating co-appearances from {len(doc_to_entities)} documents...")

    # Track co-appearances: (entity_a_id, entity_b_id) -> {count, docs, doc_types}
    coappearances: Dict[Tuple[str, str], dict] = defaultdict(
        lambda: {
            "count": 0,
            "documents": [],
            "document_types": defaultdict(int)
        }
    )

    # Process each document
    processed = 0
    for doc_id, entities in doc_to_entities.items():
        processed += 1
        if processed % 5000 == 0:
            logger.info(f"Processed {processed}/{len(doc_to_entities)} documents...")

        # Skip documents with 0 or 1 entities (no pairs possible)
        if len(entities) < 2:
            continue

        # Get entity metadata for all entities in document
        entity_metadata = [
            get_entity_metadata(ent.lower(), uuid_mappings)
            for ent in entities
        ]

        # Generate all pairs using combinations (efficient)
        for entity_a, entity_b in combinations(entity_metadata, 2):
            # Ensure consistent ordering: entity_a.id < entity_b.id
            if entity_a["id"] > entity_b["id"]:
                entity_a, entity_b = entity_b, entity_a

            # Create pair key
            pair_key = (entity_a["id"], entity_b["id"])

            # Update co-appearance stats
            coappearances[pair_key]["count"] += 1
            coappearances[pair_key]["documents"].append(doc_id)

            # Track document type (infer from doc_id prefix)
            if doc_id.startswith("DOJ-OGR"):
                doc_type = "government_document"
            elif doc_id.startswith("EMAIL"):
                doc_type = "email"
            elif doc_id.startswith("COURT"):
                doc_type = "court_filing"
            else:
                doc_type = "unknown"

            coappearances[pair_key]["document_types"][doc_type] += 1

            # Store entity metadata (only once)
            if "entity_a" not in coappearances[pair_key]:
                coappearances[pair_key]["entity_a"] = entity_a
                coappearances[pair_key]["entity_b"] = entity_b

    logger.info(f"Found {len(coappearances)} total entity pairs")

    # Filter by minimum co-appearances and convert to list
    filtered_coappearances = []
    for pair_key, data in coappearances.items():
        if data["count"] >= min_coappearances:
            filtered_coappearances.append({
                "entity_a": data["entity_a"],
                "entity_b": data["entity_b"],
                "count": data["count"],
                "documents": data["documents"],
                "document_types": dict(data["document_types"])
            })

    logger.info(f"After filtering (>={min_coappearances}): {len(filtered_coappearances)} pairs")

    # Sort by count (descending)
    filtered_coappearances.sort(key=lambda x: x["count"], reverse=True)

    return filtered_coappearances


def main():
    """Main execution function."""
    logger.info("Starting entity co-appearance calculation...")

    # Load input data
    logger.info("Loading document-to-entities mapping...")
    doc_to_entities_file = TRANSFORMED_DIR / "document_to_entities.json"
    doc_data = load_json(doc_to_entities_file)
    doc_to_entities = doc_data.get("document_to_entities", {})

    # Load UUID mappings
    uuid_mappings = load_entity_uuid_mappings()

    # Calculate co-appearances
    coappearances = calculate_coappearances(doc_to_entities, uuid_mappings)

    # Count unique entities
    unique_entities: Set[str] = set()
    for pair in coappearances:
        unique_entities.add(pair["entity_a"]["id"])
        unique_entities.add(pair["entity_b"]["id"])

    # Build output data
    output_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_pairs": len(coappearances),
            "total_entities": len(unique_entities),
            "document_sources": len(doc_to_entities),
            "min_coappearances_threshold": 2
        },
        "coappearances": coappearances
    }

    # Write output
    output_file = TRANSFORMED_DIR / "entity_coappearances.json"
    logger.info(f"Writing output to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    logger.info(f"Total entity pairs: {len(coappearances)}")
    logger.info(f"Unique entities involved: {len(unique_entities)}")
    logger.info(f"Documents processed: {len(doc_to_entities)}")

    if coappearances:
        top_pair = coappearances[0]
        logger.info(f"\nTop co-appearance:")
        logger.info(f"  {top_pair['entity_a']['name']} <-> {top_pair['entity_b']['name']}")
        logger.info(f"  Count: {top_pair['count']} documents")

    logger.info(f"\nOutput: {output_file}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
