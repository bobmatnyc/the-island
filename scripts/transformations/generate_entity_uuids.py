#!/usr/bin/env python3
"""
Generate deterministic UUIDs for all entities.

This script creates:
1. UUID mappings file (entity_uuid_mappings.json)
2. Transformed entity files with UUIDs:
   - entities_persons.json
   - entities_locations.json
   - entities_organizations.json

UUIDs are deterministic (UUID5) based on normalized name + entity type,
ensuring same entity always gets same UUID across runs.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any
import re
from collections import defaultdict

# UUID namespace for Epstein entities (deterministic)
NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
METADATA_DIR = DATA_DIR / "metadata"
TRANSFORMED_DIR = DATA_DIR / "transformed"

SOURCE_FILES = {
    "person": METADATA_DIR / "entity_biographies.json",
    "location": METADATA_DIR / "entity_locations.json",
    "organization": METADATA_DIR / "entity_organizations.json"
}

OUTPUT_FILES = {
    "mappings": TRANSFORMED_DIR / "entity_uuid_mappings.json",
    "person": TRANSFORMED_DIR / "entities_persons.json",
    "location": TRANSFORMED_DIR / "entities_locations.json",
    "organization": TRANSFORMED_DIR / "entities_organizations.json"
}


def normalize_name(name: str) -> str:
    """
    Normalize entity name for deterministic UUID generation.

    Steps:
    1. Convert to lowercase
    2. Remove possessives ('s)
    3. Remove extra whitespace
    4. Remove punctuation (except hyphens in names)
    5. Strip leading/trailing whitespace

    Examples:
        "Maxwell, Ghislaine" -> "maxwell ghislaine"
        "Bill Clinton's" -> "bill clinton"
        "New York City" -> "new york city"
    """
    # Lowercase
    normalized = name.lower()

    # Remove possessives
    normalized = re.sub(r"'s\b", "", normalized)

    # Remove commas and most punctuation, keep hyphens
    normalized = re.sub(r"[,\.;:!?\"']", "", normalized)

    # Collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    # Strip whitespace
    normalized = normalized.strip()

    return normalized


def generate_uuid(name: str, entity_type: str) -> str:
    """
    Generate deterministic UUID5 based on name and type.

    Args:
        name: Entity name (will be normalized)
        entity_type: Entity type (person, location, organization)

    Returns:
        UUID string
    """
    normalized = normalize_name(name)
    # Include type to prevent collisions (e.g., "Clinton" person vs "Clinton" location)
    unique_string = f"{entity_type}:{normalized}"
    return str(uuid.uuid5(NAMESPACE, unique_string))


def detect_duplicates(entities: Dict[str, Dict]) -> Dict[str, List[str]]:
    """
    Detect potential duplicate entities based on normalized names.

    Returns:
        Dict mapping normalized_name -> list of original names
    """
    normalized_to_names = defaultdict(list)

    for name in entities.keys():
        normalized = normalize_name(name)
        normalized_to_names[normalized].append(name)

    # Filter to only actual duplicates (>1 name for same normalized form)
    duplicates = {
        norm: names for norm, names in normalized_to_names.items()
        if len(names) > 1
    }

    return duplicates


def extract_aliases(name: str, entity_data: Dict) -> List[str]:
    """
    Extract aliases for an entity.

    For now, just returns the original name.
    Future: Could parse display_name, summary for alternate names.
    """
    aliases = [name]

    # Add display_name if different
    if "display_name" in entity_data and entity_data["display_name"] != name:
        aliases.append(entity_data["display_name"])

    return list(set(aliases))  # Deduplicate


def transform_person_entity(name: str, data: Dict, entity_id: str) -> Dict:
    """Transform person entity to target schema with UUID."""
    return {
        "entity_id": entity_id,
        "entity_type": "person",
        "canonical_name": data.get("display_name", name),
        "normalized_name": normalize_name(name),
        "aliases": extract_aliases(name, data),
        "classifications": data.get("relationship_categories", []),
        "document_count": 0,  # TODO: Could count from connections
        "news_count": 0,
        "connection_count": data.get("connection_count", 0),
        "biography": data.get("summary"),
        "quality_score": data.get("quality_score"),
        "word_count": data.get("word_count"),
        "source_refs": [],
        "metadata": {
            "original_file": "entity_biographies.json",
            "transform_date": datetime.utcnow().isoformat(),
            "generated_by": data.get("generated_by"),
            "generated_at": data.get("generated_at")
        }
    }


def transform_location_entity(name: str, data: Dict, entity_id: str) -> Dict:
    """Transform location entity to target schema with UUID."""
    return {
        "entity_id": entity_id,
        "entity_type": "location",
        "canonical_name": name,
        "normalized_name": normalize_name(name),
        "aliases": [name],
        "classifications": [],
        "document_count": len(data.get("documents", [])),
        "news_count": 0,
        "connection_count": data.get("connection_count", 0),
        "biography": None,
        "mention_count": data.get("mention_count", 0),
        "source_refs": data.get("documents", []),
        "metadata": {
            "original_file": "entity_locations.json",
            "transform_date": datetime.utcnow().isoformat()
        }
    }


def transform_organization_entity(name: str, data: Dict, entity_id: str) -> Dict:
    """Transform organization entity to target schema with UUID."""
    return {
        "entity_id": entity_id,
        "entity_type": "organization",
        "canonical_name": name,
        "normalized_name": normalize_name(name),
        "aliases": [name],
        "classifications": [],
        "document_count": len(data.get("documents", [])),
        "news_count": 0,
        "connection_count": data.get("connection_count", 0),
        "biography": None,
        "mention_count": data.get("mention_count", 0),
        "source_refs": data.get("documents", []),
        "metadata": {
            "original_file": "entity_organizations.json",
            "transform_date": datetime.utcnow().isoformat()
        }
    }


def process_entities(
    entity_type: str,
    source_file: Path,
    transform_func
) -> Tuple[Dict, Dict, Dict]:
    """
    Process entities from source file.

    Returns:
        (mappings, transformed_entities, duplicates)
    """
    print(f"\n{'='*60}")
    print(f"Processing {entity_type} entities from {source_file.name}")
    print('='*60)

    with open(source_file, 'r') as f:
        data = json.load(f)

    entities = data.get("entities", {})
    print(f"Found {len(entities)} {entity_type} entities")

    # Detect duplicates
    duplicates = detect_duplicates(entities)
    if duplicates:
        print(f"⚠️  Found {len(duplicates)} potential duplicates")
        for norm, names in list(duplicates.items())[:5]:  # Show first 5
            print(f"  - '{norm}': {names}")

    # Generate UUIDs and transform entities
    mappings = {}
    transformed = {}

    for name, entity_data in entities.items():
        # Generate deterministic UUID
        entity_id = generate_uuid(name, entity_type)

        # Create mapping entry
        mappings[entity_id] = {
            "canonical_name": entity_data.get("display_name", name) if entity_type == "person" else name,
            "normalized_name": normalize_name(name),
            "entity_type": entity_type,
            "aliases": extract_aliases(name, entity_data),
            "source_files": [source_file.name]
        }

        # Transform entity
        transformed_entity = transform_func(name, entity_data, entity_id)
        transformed[entity_id] = transformed_entity

    print(f"✅ Generated {len(transformed)} UUIDs for {entity_type} entities")

    return mappings, transformed, duplicates


def main():
    """Main execution."""
    print("="*60)
    print("Entity UUID Generation System")
    print("="*60)
    print(f"Started at: {datetime.utcnow().isoformat()}")
    print(f"UUID Namespace: {NAMESPACE}")

    # Create output directory
    TRANSFORMED_DIR.mkdir(exist_ok=True)

    # Process all entity types
    all_mappings = {}
    all_duplicates = {}
    stats = {
        "total_entities": 0,
        "by_type": {},
        "duplicates_found": 0
    }

    # Process persons
    person_mappings, person_entities, person_dupes = process_entities(
        "person",
        SOURCE_FILES["person"],
        transform_person_entity
    )
    all_mappings.update(person_mappings)
    all_duplicates["person"] = person_dupes
    stats["by_type"]["person"] = len(person_entities)
    stats["total_entities"] += len(person_entities)

    # Process locations
    location_mappings, location_entities, location_dupes = process_entities(
        "location",
        SOURCE_FILES["location"],
        transform_location_entity
    )
    all_mappings.update(location_mappings)
    all_duplicates["location"] = location_dupes
    stats["by_type"]["location"] = len(location_entities)
    stats["total_entities"] += len(location_entities)

    # Process organizations
    org_mappings, org_entities, org_dupes = process_entities(
        "organization",
        SOURCE_FILES["organization"],
        transform_organization_entity
    )
    all_mappings.update(org_mappings)
    all_duplicates["organization"] = org_dupes
    stats["by_type"]["organization"] = len(org_entities)
    stats["total_entities"] += len(org_entities)

    # Count total duplicates
    stats["duplicates_found"] = sum(len(dupes) for dupes in all_duplicates.values())

    # Write mappings file
    print(f"\n{'='*60}")
    print("Writing output files...")
    print('='*60)

    mappings_output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "total_entities": stats["total_entities"],
            "namespace": str(NAMESPACE),
            "by_type": stats["by_type"],
            "duplicates_detected": stats["duplicates_found"]
        },
        "mappings": all_mappings
    }

    with open(OUTPUT_FILES["mappings"], 'w') as f:
        json.dump(mappings_output, f, indent=2)
    print(f"✅ Created {OUTPUT_FILES['mappings']}")

    # Write transformed entity files
    for entity_type in ["person", "location", "organization"]:
        if entity_type == "person":
            entities = person_entities
        elif entity_type == "location":
            entities = location_entities
        else:
            entities = org_entities

        output = {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "total_entities": len(entities),
                "entity_type": entity_type,
                "namespace": str(NAMESPACE)
            },
            "entities": entities
        }

        with open(OUTPUT_FILES[entity_type], 'w') as f:
            json.dump(output, f, indent=2)
        print(f"✅ Created {OUTPUT_FILES[entity_type]}")

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    print(f"Total entities processed: {stats['total_entities']}")
    print(f"  - Persons: {stats['by_type']['person']}")
    print(f"  - Locations: {stats['by_type']['location']}")
    print(f"  - Organizations: {stats['by_type']['organization']}")
    print(f"\nUUIDs generated: {stats['total_entities']}")
    print(f"Potential duplicates detected: {stats['duplicates_found']}")

    if stats['duplicates_found'] > 0:
        print(f"\n⚠️  Duplicate Summary by Type:")
        for entity_type, dupes in all_duplicates.items():
            if dupes:
                print(f"  {entity_type}: {len(dupes)} duplicate groups")

    print(f"\nFiles created:")
    for file_path in OUTPUT_FILES.values():
        size_mb = file_path.stat().st_size / 1024 / 1024
        print(f"  - {file_path.name} ({size_mb:.2f} MB)")

    print(f"\nCompleted at: {datetime.utcnow().isoformat()}")
    print("="*60)


if __name__ == "__main__":
    main()
