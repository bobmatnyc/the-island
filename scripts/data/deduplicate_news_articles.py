#!/usr/bin/env python3
"""
Remove duplicate news articles from the database.

Strategy:
1. Group articles by (title, url, published_date)
2. Keep first occurrence, delete duplicates
3. Log all deletions for audit trail
4. Create backup before modification

Design Decision: Simple deduplication based on (title, url, date) tuple
Rationale: These three fields uniquely identify a news article. Articles with
the same title, URL, and publication date are duplicates from re-imports.

Trade-offs:
- Performance: O(n) single pass with dict lookup
- Accuracy: 100% for exact duplicates, won't catch near-duplicates
- Safety: Creates backup before any modifications

Error Handling:
- FileNotFoundError: Exit with clear error if news file missing
- JSONDecodeError: Exit if file is corrupted
- IOError: Exit if backup/write fails
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def load_news_data(news_file: Path) -> dict:
    """Load news articles from JSON file."""
    try:
        with open(news_file) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: News file not found: {news_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in news file: {e}")
        sys.exit(1)


def find_duplicates(articles: list) -> tuple[list, list]:
    """
    Find duplicate articles based on (title, url, published_date).

    Returns:
        tuple: (unique_articles, duplicate_articles)

    Complexity:
        Time: O(n) - single pass through articles
        Space: O(n) - dictionary to track seen articles
    """
    seen = {}
    duplicates = []
    unique_articles = []

    for article in articles:
        # Create unique key from article identifiers
        key = (
            article.get("title"),
            article.get("url"),
            article.get("published_date")
        )

        if key in seen:
            duplicates.append(article)
        else:
            seen[key] = article
            unique_articles.append(article)

    return unique_articles, duplicates


def create_backup(news_file: Path) -> Path:
    """Create timestamped backup of original file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = news_file.parent / f"{news_file.stem}_backup_{timestamp}{news_file.suffix}"

    try:
        with open(news_file) as f:
            content = f.read()
        with open(backup_file, 'w') as f:
            f.write(content)
        return backup_file
    except IOError as e:
        print(f"ERROR: Failed to create backup: {e}")
        sys.exit(1)


def save_news_data(news_file: Path, data: dict):
    """Save deduplicated news data to file."""
    try:
        with open(news_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"ERROR: Failed to write news file: {e}")
        sys.exit(1)


def log_duplicate_details(duplicates: list):
    """Log details of removed duplicates for audit trail."""
    print("\n=== DUPLICATE DETAILS ===")

    # Group duplicates by title for readability
    by_title = defaultdict(list)
    for dup in duplicates:
        title = dup.get("title", "Unknown Title")[:60]  # Truncate long titles
        by_title[title].append(dup)

    for title, dups in sorted(by_title.items()):
        print(f"\n'{title}...'")
        print(f"  Found {len(dups)} duplicate(s)")
        for dup in dups:
            print(f"  - URL: {dup.get('url', 'N/A')}")
            print(f"    Date: {dup.get('published_date', 'N/A')}")
            entities = dup.get("entities", [])
            if entities:
                print(f"    Entities: {', '.join(entities[:3])}{'...' if len(entities) > 3 else ''}")


def validate_deduplication(original_count: int, unique_count: int, duplicate_count: int):
    """Validate that deduplication math is correct."""
    if original_count != unique_count + duplicate_count:
        print("\nWARNING: Article count mismatch!")
        print(f"Original: {original_count}")
        print(f"Unique: {unique_count}")
        print(f"Duplicates: {duplicate_count}")
        print(f"Sum: {unique_count + duplicate_count}")
        return False
    return True


def recalculate_metadata(articles: list) -> dict:
    """
    Recalculate metadata from deduplicated articles.

    Returns:
        dict: Updated metadata with correct totals and date ranges

    Complexity: O(n) - single pass through articles
    """
    sources = defaultdict(int)
    all_dates = []

    for article in articles:
        # Count by publication source
        pub = article.get("publication")
        if pub:
            sources[pub] += 1

        # Collect dates for range calculation
        pub_date = article.get("published_date")
        if pub_date:
            all_dates.append(pub_date)

    # Calculate date range
    date_range = {}
    if all_dates:
        sorted_dates = sorted(all_dates)
        date_range = {
            "earliest": sorted_dates[0],
            "latest": sorted_dates[-1]
        }

    return {
        "total_articles": len(articles),
        "date_range": date_range,
        "sources": dict(sources),
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }


def main():
    """Main deduplication workflow."""
    print("=== News Article Deduplication ===\n")

    # Load news data
    news_file = Path("data/metadata/news_articles_index.json")
    print(f"Loading news data from: {news_file}")
    data = load_news_data(news_file)

    articles = data.get("articles", [])
    original_count = len(articles)
    print(f"Original article count: {original_count}")

    # Find duplicates
    print("\nAnalyzing for duplicates...")
    unique_articles, duplicates = find_duplicates(articles)

    duplicate_count = len(duplicates)
    unique_count = len(unique_articles)

    print(f"Found {duplicate_count} duplicate entries")
    print(f"Unique articles: {unique_count}")

    # Validate counts
    if not validate_deduplication(original_count, unique_count, duplicate_count):
        print("\nAborting due to validation error.")
        sys.exit(1)

    if duplicate_count == 0:
        print("\nNo duplicates found. Database is clean.")
        return

    # Log duplicate details
    log_duplicate_details(duplicates)

    # Create backup
    print("\n=== CREATING BACKUP ===")
    backup_file = create_backup(news_file)
    print(f"Backup created: {backup_file}")

    # Recalculate metadata
    print("\n=== RECALCULATING METADATA ===")
    new_metadata = recalculate_metadata(unique_articles)
    print(f"Updated metadata:")
    print(f"  - Total articles: {new_metadata['total_articles']}")
    print(f"  - Total sources: {len(new_metadata['sources'])}")
    print(f"  - Date range: {new_metadata['date_range'].get('earliest')} to {new_metadata['date_range'].get('latest')}")

    # Save deduplicated data
    print("\n=== SAVING DEDUPLICATED DATA ===")
    data["articles"] = unique_articles
    data["metadata"] = new_metadata
    save_news_data(news_file, data)
    print(f"Saved {unique_count} unique articles to: {news_file}")

    # Summary
    print("\n=== DEDUPLICATION COMPLETE ===")
    print(f"✅ Original articles: {original_count}")
    print(f"✅ Duplicates removed: {duplicate_count}")
    print(f"✅ Unique articles: {unique_count}")
    print(f"✅ Backup saved: {backup_file}")
    print(f"✅ Reduction: {duplicate_count / original_count * 100:.1f}%")

    print("\nNext steps:")
    print("1. Restart backend: cd /Users/masa/Projects/epstein && ./scripts/operations/restart-backend.sh")
    print("2. Verify count: curl -s http://localhost:8081/api/news/stats | python3 -m json.tool")
    print("3. Check UI: Open http://localhost:3000/news")


if __name__ == "__main__":
    main()
