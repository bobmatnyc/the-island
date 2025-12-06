#!/usr/bin/env python3
"""
Import Epstein news articles from November 25 - December 6, 2025.
Reads from docs/research/epstein-news-nov25-dec6-2025-urls.json and imports via batch ingestion.

Usage:
    python import_nov25_dec6_articles.py --dry-run  # Test without importing
    python import_nov25_dec6_articles.py            # Import all articles
    python import_nov25_dec6_articles.py --limit 5  # Test with 5 articles
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_articles_from_json(json_path: Path) -> list[dict]:
    """
    Load articles from research JSON file.

    Args:
        json_path: Path to epstein-news-nov25-dec6-2025-urls.json

    Returns:
        List of article dictionaries with url, publication, date, title
    """
    with open(json_path) as f:
        data = json.load(f)

    articles = []
    for article in data["articles"]:
        # Skip tier-3 reference articles for now
        if article["priority"] == "tier_3":
            logger.info(f"Skipping tier-3 reference: {article['title']}")
            continue

        # Handle articles with "undated" dates
        published_date = article["date"]
        if published_date == "undated" or published_date == "reference":
            logger.warning(f"Article missing date, will be extracted: {article['title'][:50]}")
            published_date = None

        articles.append({
            "url": article["url"],
            "publication": article["source"],
            "published_date": published_date,
            "title": article["title"],
            "priority": article["priority"],
            "category": article["category"],
            "significance": article["significance"]
        })

    return articles


def create_csv_for_batch_ingestion(articles: list[dict], output_path: Path):
    """
    Create CSV file for batch ingestion script.

    CSV Format: url,publication,published_date,title,notes
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'url', 'publication', 'published_date', 'title', 'notes'
        ])
        writer.writeheader()

        for article in articles:
            writer.writerow({
                'url': article['url'],
                'publication': article['publication'],
                'published_date': article.get('published_date', ''),
                'title': article['title'],
                'notes': f"{article['priority']} - {article['significance']}"
            })

    logger.info(f"Created CSV with {len(articles)} articles: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Import Epstein news articles from Nov 25 - Dec 6, 2025",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (test without importing)
  python import_nov25_dec6_articles.py --dry-run

  # Import first 5 articles
  python import_nov25_dec6_articles.py --limit 5

  # Import all articles
  python import_nov25_dec6_articles.py

  # Custom API URL
  python import_nov25_dec6_articles.py --api-url http://localhost:8000
        """
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum articles to import (for testing)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test without actually importing"
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="FastAPI server URL (default: http://localhost:8000)"
    )

    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip link verification (faster but less robust)"
    )

    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent.parent
    json_path = project_root / "docs/research/epstein-news-nov25-dec6-2025-urls.json"
    csv_path = project_root / "data/temp_import_nov25_dec6.csv"
    entity_index = project_root / "data/md/entities/ENTITIES_INDEX.json"

    # Validate paths
    if not json_path.exists():
        logger.error(f"JSON file not found: {json_path}")
        sys.exit(1)

    if not entity_index.exists():
        logger.error(f"Entity index not found: {entity_index}")
        sys.exit(1)

    # Load articles from JSON
    logger.info(f"Loading articles from: {json_path}")
    try:
        articles = load_articles_from_json(json_path)
        logger.info(f"Loaded {len(articles)} articles (excluding tier-3 references)")
    except Exception as e:
        logger.error(f"Failed to load articles: {e}")
        sys.exit(1)

    # Apply limit
    if args.limit:
        articles = articles[:args.limit]
        logger.info(f"Limited to {args.limit} articles")

    # Create CSV
    try:
        create_csv_for_batch_ingestion(articles, csv_path)
    except Exception as e:
        logger.error(f"Failed to create CSV: {e}")
        sys.exit(1)

    # Import using batch ingestion script
    logger.info("\n" + "=" * 80)
    logger.info("Starting batch ingestion...")
    logger.info("=" * 80)

    try:
        # Import ingest_news_batch module
        sys.path.insert(0, str(project_root / "scripts/ingestion"))
        from ingest_news_batch import NewsArticleIngester

        # Initialize ingester
        ingester = NewsArticleIngester(
            api_url=args.api_url,
            entity_index_path=entity_index,
            skip_verification=args.skip_verification
        )

        # Run ingestion
        results = ingester.ingest_from_csv(
            csv_path=csv_path,
            limit=None,  # Already limited above
            dry_run=args.dry_run
        )

        # Cleanup temp CSV
        if not args.dry_run and csv_path.exists():
            csv_path.unlink()
            logger.info(f"Cleaned up temporary CSV: {csv_path}")

        # Report results
        logger.info("\n" + "=" * 80)
        logger.info("Import Complete!")
        logger.info("=" * 80)
        logger.info(f"Total articles processed: {results['total']}")
        logger.info(f"Successfully imported: {results['success']}")
        logger.info(f"Failed: {results['failed']}")
        logger.info(f"Success rate: {results['success_rate']}")
        logger.info(f"Time elapsed: {results['elapsed_time']}")
        logger.info("=" * 80)

        # Exit code based on success rate
        success_rate = results['success'] / max(1, results['total'])
        if success_rate < 0.5:
            logger.warning("Success rate below 50% - check errors")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nImport interrupted by user")
        if csv_path.exists():
            csv_path.unlink()
        sys.exit(130)

    except Exception as e:
        logger.error(f"Import failed: {e}")
        if csv_path.exists():
            csv_path.unlink()
        sys.exit(1)


if __name__ == "__main__":
    main()
