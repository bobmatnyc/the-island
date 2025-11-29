#!/usr/bin/env python3
"""
Merge November 2025 news articles into the main news articles index.

This script:
1. Loads existing news_articles_index.json
2. Loads new news_articles_november_2025.json
3. Deduplicates by URL
4. Updates metadata counts
5. Saves merged result back to news_articles_index.json
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

# File paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
EXISTING_INDEX = PROJECT_ROOT / "data/metadata/news_articles_index.json"
NEW_ARTICLES = PROJECT_ROOT / "data/metadata/news_articles_november_2025.json"
BACKUP_PATH = PROJECT_ROOT / "data/metadata/news_articles_index_backup_20251125.json"


def load_json(filepath: Path) -> Dict:
    """Load JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(filepath: Path, data: Dict) -> None:
    """Save JSON file with pretty formatting."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_uuid_id() -> str:
    """Generate UUID for article ID."""
    return str(uuid.uuid4())


def deduplicate_articles(articles: List[Dict]) -> tuple[List[Dict], int]:
    """
    Deduplicate articles by URL.

    Returns:
        Tuple of (deduplicated_articles, duplicate_count)
    """
    seen_urls: Set[str] = set()
    unique_articles: List[Dict] = []
    duplicates = 0

    for article in articles:
        url = article.get('url')
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)
        else:
            duplicates += 1
            print(f"⚠️  Duplicate URL found: {url}")

    return unique_articles, duplicates


def update_source_counts(articles: List[Dict]) -> Dict[str, int]:
    """Count articles by source/publication."""
    source_counts: Dict[str, int] = {}

    for article in articles:
        source = article.get('publication', 'Unknown')
        source_counts[source] = source_counts.get(source, 0) + 1

    return source_counts


def find_date_range(articles: List[Dict]) -> Dict[str, str]:
    """Find earliest and latest article dates."""
    dates = []

    for article in articles:
        pub_date = article.get('published_date')
        if pub_date:
            dates.append(pub_date)

    if not dates:
        return {"earliest": "unknown", "latest": "unknown"}

    dates.sort()
    return {
        "earliest": dates[0],
        "latest": dates[-1]
    }


def assign_uuid_ids(articles: List[Dict]) -> List[Dict]:
    """Assign UUID-based IDs to articles that have temporary IDs."""
    for article in articles:
        # Replace temporary IDs (nov2025-XXX) with UUID
        if article.get('id', '').startswith('nov2025-'):
            article['id'] = generate_uuid_id()

    return articles


def main():
    """Main merge process."""
    print("=" * 60)
    print("November 2025 News Articles Import")
    print("=" * 60)

    # Load existing index
    print("\n📂 Loading existing index...")
    existing_data = load_json(EXISTING_INDEX)
    existing_articles = existing_data.get('articles', [])
    print(f"   Found {len(existing_articles)} existing articles")

    # Load new articles
    print("\n📂 Loading new articles...")
    new_data = load_json(NEW_ARTICLES)
    new_articles = new_data.get('articles', [])
    print(f"   Found {len(new_articles)} new articles")

    # Assign UUID IDs to new articles
    print("\n🔑 Assigning UUID IDs to new articles...")
    new_articles = assign_uuid_ids(new_articles)

    # Create backup
    print(f"\n💾 Creating backup at {BACKUP_PATH.name}...")
    save_json(BACKUP_PATH, existing_data)

    # Merge articles
    print("\n🔀 Merging articles...")
    all_articles = existing_articles + new_articles
    print(f"   Total before deduplication: {len(all_articles)}")

    # Deduplicate
    print("\n🔍 Deduplicating by URL...")
    unique_articles, duplicate_count = deduplicate_articles(all_articles)
    print(f"   Removed {duplicate_count} duplicates")
    print(f"   Total after deduplication: {len(unique_articles)}")

    # Update metadata
    print("\n📊 Updating metadata...")
    updated_metadata = {
        "total_articles": len(unique_articles),
        "date_range": find_date_range(unique_articles),
        "sources": update_source_counts(unique_articles),
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "version": existing_data['metadata'].get('version', '1.0.0')
    }

    # Prepare final data structure
    final_data = {
        "metadata": updated_metadata,
        "articles": unique_articles
    }

    # Save merged index
    print(f"\n💾 Saving merged index to {EXISTING_INDEX.name}...")
    save_json(EXISTING_INDEX, final_data)

    # Print summary
    print("\n" + "=" * 60)
    print("✅ IMPORT COMPLETE")
    print("=" * 60)
    print(f"\nArticles added: {len(new_articles) - duplicate_count}")
    print(f"Duplicates skipped: {duplicate_count}")
    print(f"Total articles: {updated_metadata['total_articles']}")
    print(f"Date range: {updated_metadata['date_range']['earliest']} to {updated_metadata['date_range']['latest']}")
    print(f"\nBackup saved: {BACKUP_PATH}")
    print(f"Updated index: {EXISTING_INDEX}")

    # Print new sources breakdown
    print("\n📰 New articles by source:")
    new_sources = update_source_counts(new_articles)
    for source, count in sorted(new_sources.items(), key=lambda x: -x[1]):
        print(f"   {source}: {count}")

    print("\n✨ Import successful!\n")


if __name__ == "__main__":
    main()
