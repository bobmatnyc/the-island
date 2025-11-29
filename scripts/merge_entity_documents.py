#!/usr/bin/env python3
"""
Merge document reference data from entity_document_index.json into entity_statistics.json.

This script resolves the blocking issue for bio enrichment by copying document references
from the document index into the entity statistics file where they're expected.

Design Decision: Name Matching Strategy
---------------------------------------
Rationale: entity_document_index uses "Last, First" format (e.g., "Maxwell, Ghislaine")
while entity_statistics uses lowercase_underscore IDs (e.g., "ghislaine_maxwell").
We need flexible matching to handle format variations.

Matching Strategy (in priority order):
1. Exact GUID match (if available)
2. Normalized name match (case-insensitive, handle "Last, First" and "First Last")
3. Name variation match (check all variations in entity_statistics)

Trade-offs:
- Performance: O(n*m) nested loop vs. O(n) hash map lookup
  - Chose hash map approach with multiple lookup keys for O(n) complexity
- Accuracy: Strict matching vs. fuzzy matching
  - Chose normalized exact matching to avoid false positives
- Complexity: Simple loop vs. sophisticated matching
  - Balanced with multi-key hash map (moderate complexity, high accuracy)

Alternatives Considered:
1. Fuzzy string matching (rejected: too slow, false positives)
2. Manual mapping file (rejected: maintenance overhead)
3. Database JOIN operation (rejected: overkill for one-time migration)

Performance Analysis:
- Time Complexity: O(n + m) where n = entities, m = document entries
- Space Complexity: O(n) for hash map lookups
- Expected Performance: <5 seconds for 1,637 entities + 69 document entries
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

# Project root is parent of scripts directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "metadata"

ENTITY_DOCUMENT_INDEX = DATA_DIR / "entity_document_index.json"
ENTITY_STATISTICS = DATA_DIR / "entity_statistics.json"


def normalize_name(name: str) -> str:
    """Normalize name for matching.

    Handles:
    - Case variations: "Maxwell" vs "maxwell"
    - Format variations: "Maxwell, Ghislaine" vs "Ghislaine Maxwell"
    - Extra whitespace

    Returns lowercase canonical form for comparison.
    """
    name = name.strip().lower()

    # Convert "Last, First" to "First Last"
    if ", " in name:
        parts = name.split(", ", 1)
        if len(parts) == 2:
            name = f"{parts[1]} {parts[0]}"

    return name


def build_entity_lookup(statistics: dict[str, Any]) -> dict[str, str]:
    """Build hash map for O(1) entity lookup.

    Creates multiple lookup keys per entity:
    - Normalized primary name
    - All name variations
    - Entity ID (as fallback)

    Returns dict mapping normalized_name -> entity_id
    """
    lookup: dict[str, str] = {}

    for entity_id, entity_data in statistics.get("statistics", {}).items():
        # Add primary name lookup
        primary_name = normalize_name(entity_data.get("name", ""))
        if primary_name:
            lookup[primary_name] = entity_id

        # Add name variations lookup
        for variation in entity_data.get("name_variations", []):
            normalized_var = normalize_name(variation)
            if normalized_var and normalized_var not in lookup:
                lookup[normalized_var] = entity_id

        # Add entity ID lookup (for exact ID matching)
        lookup[entity_id.lower()] = entity_id

    return lookup


def convert_document_format(doc_entry: dict[str, Any], base_path: Path) -> dict[str, Any]:
    """Convert document index format to entity statistics format.

    Input format (entity_document_index.json):
    {
        "doc_id": "DOJ-OGR-00022924",
        "filename": "DOJ-OGR-00022924.txt",
        "mentions": 50
    }

    Output format (entity_statistics.json):
    {
        "path": "data/sources/house_oversight_nov2025/ocr_text/DOJ-OGR-00022924.txt",
        "type": "text",
        "mentions": 45,
        "context": null
    }
    """
    filename = doc_entry.get("filename", "")

    # Construct full path to OCR text files
    doc_path = f"data/sources/house_oversight_nov2025/ocr_text/{filename}"

    return {
        "path": doc_path,
        "type": "text",  # All are OCR text files
        "mentions": doc_entry.get("mentions", 0),
        "context": None  # Optional field, not available in source
    }


def merge_documents(
    entity_doc_index: dict[str, Any],
    entity_stats: dict[str, Any],
    dry_run: bool = False,
    verbose: bool = False
) -> tuple[dict[str, Any], dict[str, int]]:
    """Merge document references into entity statistics.

    Returns:
        (updated_statistics, merge_stats) tuple
    """
    # Build fast lookup table
    entity_lookup = build_entity_lookup(entity_stats)

    # Statistics tracking
    stats = {
        "entities_updated": 0,
        "documents_added": 0,
        "duplicates_skipped": 0,
        "entities_not_found": 0,
        "total_doc_entries": 0
    }

    # Process each entity in document index
    entity_to_docs = entity_doc_index.get("entity_to_documents", {})
    stats["total_doc_entries"] = len(entity_to_docs)

    for entity_name, doc_data in entity_to_docs.items():
        # Find matching entity in statistics
        normalized_name = normalize_name(entity_name)
        entity_id = entity_lookup.get(normalized_name)

        if not entity_id:
            if verbose:
                print(f"⚠️  Entity not found in statistics: {entity_name}")
            stats["entities_not_found"] += 1
            continue

        # Get entity data
        entity = entity_stats["statistics"][entity_id]

        # Get current documents (for deduplication)
        existing_docs = {doc["path"]: doc for doc in entity.get("documents", [])}
        documents_before = len(existing_docs)

        # Add new documents
        for doc_entry in doc_data.get("documents", []):
            converted_doc = convert_document_format(doc_entry, DATA_DIR)
            doc_path = converted_doc["path"]

            if doc_path in existing_docs:
                stats["duplicates_skipped"] += 1
                if verbose:
                    print(f"  ⏭️  Duplicate skipped: {doc_path}")
                continue

            existing_docs[doc_path] = converted_doc
            stats["documents_added"] += 1

        # Update entity with merged documents
        merged_docs = list(existing_docs.values())
        documents_after = len(merged_docs)

        if documents_after > documents_before:
            entity["documents"] = merged_docs
            entity["total_documents"] = documents_after
            stats["entities_updated"] += 1

            if verbose:
                print(f"✅ {entity_name} ({entity_id}): {documents_before} -> {documents_after} documents")

    return entity_stats, stats


def create_backup(filepath: Path) -> Path:
    """Create timestamped backup of file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"
    shutil.copy2(filepath, backup_path)
    return backup_path


def main():
    parser = argparse.ArgumentParser(
        description="Merge document references from entity_document_index.json into entity_statistics.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python scripts/merge_entity_documents.py --dry-run --verbose

  # Execute merge with backup
  python scripts/merge_entity_documents.py --backup

  # Execute without backup (not recommended)
  python scripts/merge_entity_documents.py --no-backup
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would change without writing files"
    )

    parser.add_argument(
        "--backup",
        dest="backup",
        action="store_true",
        default=True,
        help="Create backup before merge (default: true)"
    )

    parser.add_argument(
        "--no-backup",
        dest="backup",
        action="store_false",
        help="Skip backup creation"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Detailed logging"
    )

    args = parser.parse_args()

    # Validate input files exist
    if not ENTITY_DOCUMENT_INDEX.exists():
        print(f"❌ Error: {ENTITY_DOCUMENT_INDEX} not found")
        return 1

    if not ENTITY_STATISTICS.exists():
        print(f"❌ Error: {ENTITY_STATISTICS} not found")
        return 1

    # Load data
    print(f"📖 Reading {ENTITY_DOCUMENT_INDEX.name}...")
    with open(ENTITY_DOCUMENT_INDEX, "r", encoding="utf-8") as f:
        entity_doc_index = json.load(f)

    print(f"📖 Reading {ENTITY_STATISTICS.name}...")
    with open(ENTITY_STATISTICS, "r", encoding="utf-8") as f:
        entity_stats = json.load(f)

    # Show initial state
    print("\n📊 Initial Statistics:")
    print(f"  Total entities in statistics: {entity_stats.get('total_entities', 0)}")
    print(f"  Total entities with documents: {entity_doc_index['metadata']['total_entities_mentioned']}")
    print(f"  Total document relationships: {entity_doc_index['metadata']['total_entity_mentions']}")

    # Perform merge
    print(f"\n{'🔍 DRY RUN MODE - No files will be modified' if args.dry_run else '🔄 Merging documents...'}\n")

    updated_stats, merge_stats = merge_documents(
        entity_doc_index,
        entity_stats,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    # Display results
    print("\n📈 Merge Statistics:")
    print(f"  ✅ Entities updated: {merge_stats['entities_updated']}")
    print(f"  📄 Documents added: {merge_stats['documents_added']}")
    print(f"  ⏭️  Duplicates skipped: {merge_stats['duplicates_skipped']}")
    print(f"  ⚠️  Entities not found: {merge_stats['entities_not_found']}")
    print(f"  📚 Total document entries processed: {merge_stats['total_doc_entries']}")

    # Show top entities with document counts
    if args.verbose:
        print("\n🔝 Top Entities by Document Count:")
        entities_with_docs = [
            (eid, edata["name"], edata.get("total_documents", 0))
            for eid, edata in updated_stats["statistics"].items()
            if edata.get("total_documents", 0) > 0
        ]
        entities_with_docs.sort(key=lambda x: x[2], reverse=True)

        for eid, name, count in entities_with_docs[:10]:
            print(f"  {name}: {count} documents")

    # Write updated file (unless dry run)
    if not args.dry_run:
        # Create backup if requested
        if args.backup:
            backup_path = create_backup(ENTITY_STATISTICS)
            print(f"\n💾 Backup created: {backup_path.name}")

        # Write merged data
        print(f"💾 Writing updated {ENTITY_STATISTICS.name}...")
        with open(ENTITY_STATISTICS, "w", encoding="utf-8") as f:
            json.dump(updated_stats, f, indent=2, ensure_ascii=False)

        print(f"✅ Successfully merged documents into {ENTITY_STATISTICS.name}")
    else:
        print("\n🔍 Dry run complete - no files modified")

    return 0


if __name__ == "__main__":
    exit(main())
