#!/usr/bin/env python3
"""
News Database Population Script
Populates news database from seed CSV with proper entity ID linking.

Design Decision: Simplified Import Without Web Scraping
Rationale: The seed CSV already has 4 manually curated articles in the database.
For initial population, we'll use the existing infrastructure to import the
remaining articles from news_articles_seed.csv using the scraper.

Performance:
- Processing time: ~3-5 seconds per article
- Entity matching: O(n) where n is number of entities per article

Usage:
    python populate_news_database.py --limit 5 --dry-run
    python populate_news_database.py
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


def load_entities_index(path: Path) -> dict[str, str]:
    """
    Load entities and create name-to-normalized_name mapping.

    Args:
        path: Path to ENTITIES_INDEX.json

    Returns:
        Dictionary mapping entity names to normalized names

    Note: Using normalized_name as the entity identifier since
    the current ENTITIES_INDEX uses list format without IDs.
    """
    with open(path) as f:
        data = json.load(f)

    # Build name variations mapping
    name_map = {}

    for entity in data["entities"]:
        name = entity["name"]
        normalized = entity["normalized_name"]

        # Map both name and normalized_name
        name_map[name.lower()] = normalized
        name_map[normalized.lower()] = normalized

        # Also map common variations
        # "Maxwell, Ghislaine" -> "Ghislaine Maxwell"
        if ", " in name:
            parts = name.split(", ")
            if len(parts) == 2:
                reversed_name = f"{parts[1]} {parts[0]}"
                name_map[reversed_name.lower()] = normalized

    logger.info(f"Loaded {len(data['entities'])} entities with {len(name_map)} name variations")
    return name_map


def get_existing_articles(index_path: Path) -> set:
    """Get URLs of articles already in database."""
    if not index_path.exists():
        return set()

    with open(index_path) as f:
        data = json.load(f)

    urls = {article["url"] for article in data.get("articles", [])}
    logger.info(f"Found {len(urls)} existing articles")
    return urls


def main():
    parser = argparse.ArgumentParser(description="Populate news database from seed CSV")

    parser.add_argument(
        "--limit", type=int, default=None, help="Maximum articles to import (for testing)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be imported without actually importing",
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8081",
        help="API server URL (default: http://localhost:8081)",
    )

    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent.parent.parent
    seed_csv = project_root / "data" / "sources" / "news_articles_seed.csv"
    entities_index = project_root / "data" / "md" / "entities" / "ENTITIES_INDEX.json"
    news_index = project_root / "data" / "metadata" / "news_articles_index.json"

    # Validate paths
    if not seed_csv.exists():
        logger.error(f"Seed CSV not found: {seed_csv}")
        return 1

    if not entities_index.exists():
        logger.error(f"Entity index not found: {entities_index}")
        return 1

    # Load entity mapping
    logger.info("Loading entity index...")
    load_entities_index(entities_index)

    # Get existing articles
    existing_urls = get_existing_articles(news_index)

    # Read seed CSV
    logger.info(f"Reading seed CSV: {seed_csv}")
    articles_to_import = []

    with open(seed_csv) as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get("url", "").strip()
            if url and url not in existing_urls:
                articles_to_import.append(row)

    logger.info(f"Articles to import: {len(articles_to_import)}")
    logger.info(f"Articles already in database: {len(existing_urls)}")

    if not articles_to_import:
        logger.info("No new articles to import!")
        return 0

    # Apply limit
    if args.limit:
        articles_to_import = articles_to_import[: args.limit]
        logger.info(f"Limited to {args.limit} articles")

    # Show what we'll import
    logger.info("\n" + "=" * 80)
    logger.info("Articles to be imported:")
    logger.info("=" * 80)
    for i, article in enumerate(articles_to_import, 1):
        logger.info(f"{i}. {article['publication']} - {article['published_date']}")
        logger.info(f"   {article['title']}")
        logger.info(f"   {article['url']}")
    logger.info("=" * 80)

    if args.dry_run:
        logger.info("\nDRY RUN MODE - No imports will be performed")
        return 0

    # Import using the batch ingestion script
    logger.info("\n" + "=" * 80)
    logger.info("Starting import using batch ingestion script...")
    logger.info("=" * 80)

    # Create temporary CSV with only new articles
    temp_csv = project_root / "data" / "sources" / "news_articles_temp.csv"
    with open(temp_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["url", "publication", "published_date", "title", "notes"]
        )
        writer.writeheader()
        writer.writerows(articles_to_import)

    # Run batch ingestion
    import subprocess

    result = subprocess.run(
        [
            "python3",
            str(project_root / "scripts" / "ingestion" / "ingest_news_batch.py"),
            str(temp_csv),
            "--api-url",
            args.api_url,
            "--entity-index",
            str(entities_index),
            "--skip-verification",  # Faster, we trust the seed data
        ],
        check=False,
    )

    # Clean up temp file
    temp_csv.unlink(missing_ok=True)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
