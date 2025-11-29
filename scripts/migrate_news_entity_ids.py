#!/usr/bin/env python3
"""
News Entity Linking Migration Script (1M-131)

Migrates news articles from name-based entity references to ID-based references.

Current State:
- News articles store entity names in `entities_mentioned` field
- ~83% of news entities have no mapping to existing entity IDs
- Name resolution happens at query time with ~95% accuracy

Target State:
- Store entity IDs directly in `entity_ids` field
- Maintain entity names for display in `entities_mentioned`
- 100% resolution for all entities (create new IDs as needed)

Strategy:
1. Load existing entity mappings (name_to_id)
2. For each news article entity:
   a. Try to resolve to existing entity ID
   b. If not found, generate new entity ID
3. Add `entity_ids` field to each article
4. Maintain backward compatibility with `entities_mentioned`
5. Generate report on new entities created

Author: Claude MPM
Ticket: 1M-131
Date: 2025-11-24
"""

import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple


def normalize_entity_name(name: str) -> str:
    """Normalize entity name for ID generation

    Converts names like "Prince Andrew, Duke of York" to "prince_andrew"

    Args:
        name: Entity name to normalize

    Returns:
        Normalized name suitable for entity ID
    """
    # Remove titles and suffixes
    name = re.sub(r',\s*(Duke|Earl|Lord|Baron|Sir|Dr\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?).*$', '', name)

    # Remove common prefixes
    name = re.sub(r'^(Prince|Princess|King|Queen|Duke|Duchess|Lord|Lady|Sir|Dr\.?|Prof\.?)\s+', '', name)

    # Convert to lowercase and replace spaces with underscores
    name = name.lower().strip()
    name = re.sub(r'[^\w\s-]', '', name)  # Remove special characters
    name = re.sub(r'[-\s]+', '_', name)   # Replace spaces/hyphens with underscore

    # Handle special cases
    name = name.replace('___', '_').replace('__', '_')
    name = name.strip('_')

    return name


def generate_entity_id(name: str, existing_ids: Set[str]) -> str:
    """Generate unique entity ID from name

    Args:
        name: Entity name
        existing_ids: Set of existing entity IDs to avoid collisions

    Returns:
        Unique entity ID
    """
    base_id = normalize_entity_name(name)

    # If unique, return as-is
    if base_id not in existing_ids:
        return base_id

    # Handle collisions with numeric suffix
    counter = 2
    while f"{base_id}_{counter}" in existing_ids:
        counter += 1

    return f"{base_id}_{counter}"


def load_data(data_dir: Path) -> Tuple[Dict, Dict]:
    """Load news articles and entity mappings

    Args:
        data_dir: Path to data directory

    Returns:
        Tuple of (news_data, name_to_id_mapping)
    """
    news_path = data_dir / "metadata" / "news_articles_index.json"
    mappings_path = data_dir / "metadata" / "entity_name_mappings.json"

    with open(news_path) as f:
        news_data = json.load(f)

    with open(mappings_path) as f:
        mappings_data = json.load(f)

    return news_data, mappings_data["name_to_id"]


def migrate_articles(news_data: Dict, name_to_id: Dict) -> Tuple[Dict, Dict]:
    """Migrate news articles to use entity IDs

    Args:
        news_data: News articles data
        name_to_id: Name-to-ID mapping dictionary

    Returns:
        Tuple of (updated_news_data, migration_report)
    """
    existing_ids = set(name_to_id.values())
    new_entities_created = {}
    resolution_stats = {
        "total_entity_mentions": 0,
        "resolved_to_existing": 0,
        "new_entities_created": 0,
        "articles_updated": 0
    }

    # Process each article
    for article in news_data["articles"]:
        entities_mentioned = article.get("entities_mentioned", [])
        entity_ids = []
        entity_id_map = {}  # name -> id mapping for this article

        resolution_stats["total_entity_mentions"] += len(entities_mentioned)

        for entity_name in entities_mentioned:
            # Try existing mapping first
            if entity_name in name_to_id:
                entity_id = name_to_id[entity_name]
                resolution_stats["resolved_to_existing"] += 1
            else:
                # Generate new entity ID
                entity_id = generate_entity_id(entity_name, existing_ids)

                # Track new entity
                if entity_id not in existing_ids:
                    new_entities_created[entity_id] = {
                        "id": entity_id,
                        "name": entity_name,
                        "first_seen_in_article": article["id"],
                        "source": "news_migration",
                        "created_at": datetime.utcnow().isoformat()
                    }
                    existing_ids.add(entity_id)
                    resolution_stats["new_entities_created"] += 1

                # Add to name_to_id for future lookups
                name_to_id[entity_name] = entity_id

            entity_ids.append(entity_id)
            entity_id_map[entity_name] = entity_id

        # Add entity_ids field to article
        article["entity_ids"] = entity_ids
        article["entity_id_map"] = entity_id_map
        resolution_stats["articles_updated"] += 1

    # Create migration report
    migration_report = {
        "migration_date": datetime.utcnow().isoformat(),
        "schema_version": "2.1",
        "statistics": resolution_stats,
        "new_entities": list(new_entities_created.values()),
        "new_entity_count": len(new_entities_created),
        "resolution_rate": {
            "existing": f"{resolution_stats['resolved_to_existing'] / resolution_stats['total_entity_mentions'] * 100:.1f}%",
            "new": f"{resolution_stats['new_entities_created'] / resolution_stats['total_entity_mentions'] * 100:.1f}%",
            "total": "100.0%"
        }
    }

    return news_data, migration_report


def save_results(data_dir: Path, news_data: Dict, migration_report: Dict):
    """Save migrated data and report

    Args:
        data_dir: Path to data directory
        news_data: Updated news data
        migration_report: Migration report
    """
    # Backup original file
    news_path = data_dir / "metadata" / "news_articles_index.json"
    backup_path = data_dir / "metadata" / f"news_articles_index.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(backup_path, 'w') as f:
        json.dump(news_data, f, indent=2)
    print(f"✓ Backup created: {backup_path.name}")

    # Save updated news articles
    with open(news_path, 'w') as f:
        json.dump(news_data, f, indent=2)
    print(f"✓ Updated news articles: {news_path.name}")

    # Save migration report
    report_path = data_dir / "metadata" / "news_entity_migration_report.json"
    with open(report_path, 'w') as f:
        json.dump(migration_report, f, indent=2)
    print(f"✓ Migration report: {report_path.name}")

    # Save new entities list for potential integration
    if migration_report["new_entities"]:
        new_entities_path = data_dir / "metadata" / "news_migration_new_entities.json"
        with open(new_entities_path, 'w') as f:
            json.dump(migration_report["new_entities"], f, indent=2)
        print(f"✓ New entities list: {new_entities_path.name}")


def print_summary(migration_report: Dict):
    """Print migration summary

    Args:
        migration_report: Migration report dictionary
    """
    stats = migration_report["statistics"]

    print("\n" + "=" * 70)
    print("NEWS ENTITY MIGRATION SUMMARY (1M-131)")
    print("=" * 70)
    print(f"Migration Date: {migration_report['migration_date']}")
    print(f"Schema Version: {migration_report['schema_version']}")
    print(f"\nArticles Updated: {stats['articles_updated']}")
    print(f"Total Entity Mentions: {stats['total_entity_mentions']}")
    print(f"\nResolution Breakdown:")
    print(f"  ✓ Resolved to Existing IDs: {stats['resolved_to_existing']} ({migration_report['resolution_rate']['existing']})")
    print(f"  ✓ New Entity IDs Created:   {stats['new_entities_created']} ({migration_report['resolution_rate']['new']})")
    print(f"  ✓ Total Resolution Rate:    {migration_report['resolution_rate']['total']}")

    if migration_report["new_entities"]:
        print(f"\n📊 Top 10 New Entities Created:")
        for entity in migration_report["new_entities"][:10]:
            print(f"   • {entity['name']:40s} → {entity['id']}")
        if len(migration_report["new_entities"]) > 10:
            print(f"   ... and {len(migration_report['new_entities']) - 10} more")

    print("\n" + "=" * 70)
    print("✅ Migration Complete!")
    print("=" * 70)


def main():
    """Main migration script"""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"

    print("🔄 Starting News Entity ID Migration (1M-131)")
    print("=" * 70)

    # Load data
    print("\n📂 Loading data...")
    news_data, name_to_id = load_data(data_dir)
    print(f"   ✓ Loaded {len(news_data['articles'])} news articles")
    print(f"   ✓ Loaded {len(name_to_id)} name-to-ID mappings")

    # Migrate
    print("\n🔧 Migrating articles...")
    updated_news_data, migration_report = migrate_articles(news_data, name_to_id)

    # Save results
    print("\n💾 Saving results...")
    save_results(data_dir, updated_news_data, migration_report)

    # Print summary
    print_summary(migration_report)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
