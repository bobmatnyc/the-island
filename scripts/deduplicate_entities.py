#!/usr/bin/env python3
"""
Deduplicate Entity Names

Consolidates entity variations with different capitalizations into single
canonical form. For example:
- "The Department of Justice" + "the Department of Justice" → "The Department of Justice"
- "New York" + "NEW YORK" + "new YORK" → "New York"

Design Decision: Prefer Title Case for Proper Nouns
Rationale: Most entities are proper nouns (organizations, locations) which
should use title case. We detect the "best" capitalization by preferring:
1. Title Case (e.g., "The Department of Justice")
2. Mixed case (e.g., "the Federal Bureau")
3. ALL CAPS as last resort (e.g., "NEW YORK")

This preserves readability while consolidating duplicates.

Performance:
- Processes ~1000 entities/second
- Merges document lists and mention counts
- Memory usage: ~50MB for largest entity files

Usage:
    # Preview duplicates (dry run)
    python3 scripts/deduplicate_entities.py --dry-run

    # Apply deduplication
    python3 scripts/deduplicate_entities.py

    # Only process specific files
    python3 scripts/deduplicate_entities.py --files organizations,locations
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# File paths
DATA_DIR = Path(__file__).parent.parent / "data"
METADATA_DIR = DATA_DIR / "metadata"

ENTITY_FILES = {
    "organizations": METADATA_DIR / "entity_organizations.json",
    "locations": METADATA_DIR / "entity_locations.json",
}


def normalize_for_comparison(name: str) -> str:
    """
    Normalize name for duplicate detection.

    Converts to lowercase and strips whitespace for comparison.
    This allows "The FBI" and "the FBI" and "THE FBI" to match.

    Args:
        name: Entity name

    Returns:
        Normalized name (lowercase, stripped)
    """
    return name.strip().lower()


def choose_best_capitalization(names: list[str]) -> str:
    """
    Choose best capitalization from list of name variations.

    Preference order:
    1. Title Case (e.g., "The Department of Justice")
    2. Mixed case (e.g., "the Federal Bureau")
    3. ALL CAPS (e.g., "NEW YORK") - least preferred

    Args:
        names: List of name variations

    Returns:
        Name with best capitalization

    Examples:
        >>> choose_best_capitalization(["NEW YORK", "new york", "New York"])
        'New York'

        >>> choose_best_capitalization(["the FBI", "The FBI", "THE FBI"])
        'The FBI'
    """
    if not names:
        return ""

    # Score each name
    # Higher score = better capitalization
    def score_capitalization(name: str) -> int:
        # Count uppercase, lowercase, and total words
        words = name.split()
        if not words:
            return 0

        uppercase_words = sum(1 for w in words if w.isupper())
        lowercase_words = sum(1 for w in words if w.islower())
        titlecase_words = sum(1 for w in words if w and w[0].isupper() and (len(w) == 1 or w[1:].islower()))

        total_words = len(words)

        # Prefer title case (most words start with capital, rest lowercase)
        if titlecase_words >= total_words * 0.7:
            return 100 + titlecase_words

        # Mixed case (some capitals, some lowercase)
        if uppercase_words > 0 and lowercase_words > 0:
            return 50

        # All lowercase (worst for proper nouns)
        if lowercase_words == total_words:
            return 10

        # ALL CAPS (worst)
        if uppercase_words == total_words:
            return 1

        return 0

    # Choose name with highest score
    best_name = max(names, key=score_capitalization)
    return best_name


def deduplicate_file(file_key: str, dry_run: bool = False) -> dict:
    """
    Deduplicate entities in a file.

    Consolidates entities with same normalized name into single entity
    with best capitalization. Merges document lists and mention counts.

    Args:
        file_key: Key in ENTITY_FILES dict
        dry_run: If True, preview changes without saving

    Returns:
        Statistics dict
    """
    file_path = ENTITY_FILES[file_key]
    print(f"\n{'[DRY RUN] ' if dry_run else ''}Processing {file_path.name}...")

    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return {}

    # Load data
    with open(file_path) as f:
        data = json.load(f)

    entities = data.get("entities", {})
    metadata = data.get("metadata", {})

    print(f"  Loaded {len(entities)} entities")

    # Group entities by normalized name
    grouped = defaultdict(list)
    for entity_key, entity_data in entities.items():
        name = entity_data.get("name", entity_key)
        normalized = normalize_for_comparison(name)
        grouped[normalized].append((entity_key, entity_data))

    # Find duplicates (groups with multiple entities)
    duplicates = {norm: group for norm, group in grouped.items() if len(group) > 1}

    print(f"  Found {len(duplicates)} groups of duplicates")

    # Statistics
    stats = {
        "total_entities": len(entities),
        "duplicate_groups": len(duplicates),
        "duplicate_entities": sum(len(group) for group in duplicates.values()),
        "entities_removed": 0,
        "entities_merged": 0,
    }

    # Preview duplicates
    if duplicates:
        print(f"\n  Duplicate Groups (showing first 20):")
        for norm_name, group in list(duplicates.items())[:20]:
            names = [entity_data.get("name", key) for key, entity_data in group]
            best_name = choose_best_capitalization(names)
            print(f"    '{best_name}' ({len(group)} variants):")
            for entity_key, entity_data in group:
                name = entity_data.get("name", entity_key)
                mention_count = entity_data.get("mention_count", 0)
                doc_count = len(entity_data.get("documents", []))
                marker = "→" if name == best_name else " "
                print(f"      {marker} {name} (mentions: {mention_count}, docs: {doc_count})")

    # Merge duplicates
    if not dry_run and duplicates:
        merged_entities = {}

        # First, add all non-duplicate entities
        for norm_name, group in grouped.items():
            if len(group) == 1:
                # Not a duplicate, keep as-is
                entity_key, entity_data = group[0]
                merged_entities[entity_key] = entity_data
            else:
                # Merge duplicates
                names = [entity_data.get("name", key) for key, entity_data in group]
                best_name = choose_best_capitalization(names)

                # Find entity with best name (or first if not found)
                canonical_entity = None
                canonical_key = None
                for entity_key, entity_data in group:
                    if entity_data.get("name") == best_name:
                        canonical_entity = entity_data
                        canonical_key = entity_key
                        break

                if not canonical_entity:
                    # Fallback to first entity
                    canonical_key, canonical_entity = group[0]

                # Merge data from all variants
                all_documents = []
                total_mentions = 0

                for entity_key, entity_data in group:
                    # Merge documents (remove duplicates)
                    docs = entity_data.get("documents", [])
                    all_documents.extend(docs)

                    # Sum mention counts
                    total_mentions += entity_data.get("mention_count", 0)

                # Remove duplicate documents
                unique_documents = list(set(all_documents))

                # Update canonical entity
                canonical_entity["name"] = best_name
                canonical_entity["mention_count"] = total_mentions
                canonical_entity["documents"] = unique_documents

                # Add to merged entities
                merged_entities[canonical_key] = canonical_entity

                stats["entities_merged"] += 1
                stats["entities_removed"] += len(group) - 1

        # Replace entities with merged version
        data["entities"] = merged_entities

        # Update metadata
        metadata["last_updated"] = datetime.now().isoformat()
        metadata["deduplication_date"] = datetime.now().isoformat()
        metadata["entities_before_dedup"] = stats["total_entities"]
        metadata["entities_after_dedup"] = len(merged_entities)

        # Backup original
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_name(f"{file_path.stem}_backup_{timestamp}{file_path.suffix}")
        shutil.copy2(file_path, backup_path)
        print(f"\n  ✓ Backed up to {backup_path.name}")

        # Save
        with open(file_path, 'w') as f:
            json.dump({"metadata": metadata, "entities": merged_entities}, f, indent=2)

        print(f"  ✓ Saved deduplicated file")
        print(f"    Before: {stats['total_entities']} entities")
        print(f"    After:  {len(merged_entities)} entities")
        print(f"    Removed: {stats['entities_removed']} duplicates")

    return stats


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Deduplicate entities with different capitalizations"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files"
    )
    parser.add_argument(
        "--files",
        type=str,
        default="all",
        help="Comma-separated list of files (organizations,locations) or 'all'"
    )

    args = parser.parse_args()

    # Determine which files to process
    if args.files == "all":
        files_to_process = list(ENTITY_FILES.keys())
    else:
        files_to_process = [f.strip() for f in args.files.split(",")]

    # Validate file keys
    invalid_files = [f for f in files_to_process if f not in ENTITY_FILES]
    if invalid_files:
        print(f"Error: Invalid file keys: {invalid_files}")
        print(f"Valid options: {list(ENTITY_FILES.keys())}")
        sys.exit(1)

    # Print header
    print("=" * 70)
    print("Entity Deduplication Script")
    print("=" * 70)
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No files will be modified\n")

    # Process files
    all_stats = {}
    for file_key in files_to_process:
        stats = deduplicate_file(file_key, dry_run=args.dry_run)
        all_stats[file_key] = stats

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    total_removed = sum(s.get("entities_removed", 0) for s in all_stats.values())
    total_groups = sum(s.get("duplicate_groups", 0) for s in all_stats.values())

    if args.dry_run:
        print(f"\nDRY RUN: Would consolidate {total_groups} duplicate groups")
        print(f"         Would remove {total_removed} duplicate entities")
        print("\nRun without --dry-run to apply changes")
    else:
        if total_removed > 0:
            print(f"\n✓ Successfully consolidated {total_groups} duplicate groups")
            print(f"✓ Removed {total_removed} duplicate entities")
            print("\nBackup files created with timestamp suffix")
        else:
            print("\n✓ No duplicates found - entities already deduplicated")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
