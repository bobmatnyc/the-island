#!/usr/bin/env python3
"""
Seed Article Ingestion Script
Scrapes tier-1 news sources and expands archive from 3 → 100+ articles.

Design Decision: Source-Focused Batch Processing
Rationale: Target high-quality tier-1 sources (Miami Herald, AP/Reuters, NPR)
with specific URL patterns and credibility scoring. Uses existing scraper
infrastructure but adds source-specific configuration and resume capability.

Trade-offs:
- Source Quality: Tier-1 focus (0.90-0.98 credibility) vs. quantity
- Performance: Sequential processing with retry logic vs. parallel complexity
- Reliability: Resume capability for interrupted runs

Performance:
- Processing time: ~3-5 seconds per article
- Throughput: ~15-20 articles per minute
- 100 articles: ~5-7 minutes with retries

Data Quality Standards:
- Minimum word count: 200 words
- Credibility score: 0.90-0.98 for tier-1 sources
- Entity detection: Must mention at least 1 known entity
- Link verification: 404 check with archive.org fallback

Usage:
    # Scrape specific source
    python ingest_seed_articles.py --source "miami-herald"

    # Scrape all sources
    python ingest_seed_articles.py --all

    # Limit number of articles
    python ingest_seed_articles.py --all --limit 100

    # Resume from previous run
    python ingest_seed_articles.py --resume
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import scraper infrastructure
from scrape_news_articles import ArticleData, NewsArticleScraper
from tqdm import tqdm


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# Tier-1 Source Configuration
TIER_1_SOURCES = {
    "miami-herald": {
        "name": "Miami Herald",
        "base_url": "https://www.miamiherald.com",
        "credibility": 0.98,  # Pulitzer finalist
        "credibility_factors": {"tier": "tier_1", "pulitzer": "finalist"},
        "priority": 1,
        "target_articles": 50,
        "notes": "Perversion of Justice series - Julie K. Brown investigative reporting",
    },
    "ap": {
        "name": "Associated Press",
        "base_url": "https://apnews.com",
        "credibility": 0.95,
        "credibility_factors": {"tier": "tier_1"},
        "priority": 2,
        "target_articles": 30,
        "notes": "AP wire coverage - neutral reporting",
    },
    "reuters": {
        "name": "Reuters",
        "base_url": "https://www.reuters.com",
        "credibility": 0.92,
        "credibility_factors": {"tier": "tier_1"},
        "priority": 2,
        "target_articles": 30,
        "notes": "Reuters wire coverage - breaking news",
    },
    "npr": {
        "name": "NPR",
        "base_url": "https://www.npr.org",
        "credibility": 0.95,
        "credibility_factors": {"tier": "tier_1"},
        "priority": 3,
        "target_articles": 20,
        "notes": "NPR comprehensive coverage - investigative reporting",
    },
}


class IngestionProgress:
    """
    Track ingestion progress for resume capability.

    Stores scraped URLs to avoid re-scraping on resume.
    """

    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.scraped_urls: set[str] = set()
        self.load()

    def load(self):
        """Load progress from file if exists."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file) as f:
                    data = json.load(f)
                    self.scraped_urls = set(data.get("scraped_urls", []))
                logger.info(f"Loaded progress: {len(self.scraped_urls)} URLs already scraped")
            except Exception as e:
                logger.warning(f"Could not load progress file: {e}")

    def save(self):
        """Save progress to file."""
        try:
            with open(self.progress_file, "w") as f:
                json.dump(
                    {
                        "scraped_urls": list(self.scraped_urls),
                        "last_updated": datetime.utcnow().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Could not save progress: {e}")

    def add_url(self, url: str):
        """Mark URL as scraped."""
        self.scraped_urls.add(url)

    def is_scraped(self, url: str) -> bool:
        """Check if URL already scraped."""
        return url in self.scraped_urls


class IngestionStats:
    """Track ingestion statistics."""

    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0
        self.skipped = 0
        self.quality_filtered = 0
        self.errors: list[dict] = []
        self.start_time = time.time()

    def add_success(self):
        self.success += 1

    def add_failure(self, url: str, publication: str, error: str):
        self.failed += 1
        self.errors.append({"url": url, "publication": publication, "error": error})

    def add_skip(self):
        self.skipped += 1

    def add_quality_filter(self):
        self.quality_filtered += 1

    def get_summary(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "skipped": self.skipped,
            "quality_filtered": self.quality_filtered,
            "success_rate": f"{(self.success / max(1, self.total)) * 100:.1f}%",
            "elapsed_time": f"{elapsed:.1f}s",
            "avg_time_per_article": f"{elapsed / max(1, self.total):.1f}s",
        }


class SeedArticleIngester:
    """
    Ingest seed articles from tier-1 sources.

    Features:
    - Source-specific configuration with credibility scoring
    - Progress tracking and resume capability
    - Data quality filtering (min 200 words, entity mentions)
    - Archive.org fallback for dead links
    - Retry logic for network errors
    - Append to existing news_articles_index.json

    Example:
        ingester = SeedArticleIngester(
            data_dir=Path("data"),
            entity_index_path=Path("data/md/entities/ENTITIES_INDEX.json")
        )

        results = ingester.ingest_source(
            source="miami-herald",
            limit=50
        )

        print(f"Success: {results['success']}/{results['total']}")
    """

    def __init__(self, data_dir: Path, entity_index_path: Path, skip_verification: bool = False):
        """
        Initialize seed article ingester.

        Args:
            data_dir: Root data directory (contains metadata/)
            entity_index_path: Path to ENTITIES_INDEX.json
            skip_verification: Skip link verification (faster, default: False)
        """
        self.data_dir = data_dir
        self.articles_index_path = data_dir / "metadata" / "news_articles_index.json"
        self.progress_file = data_dir / "metadata" / ".ingestion_progress.json"

        # Initialize scraper
        logger.info("Initializing scraper...")
        self.scraper = NewsArticleScraper(
            entity_index_path=entity_index_path,
            verify_links=not skip_verification,
            check_archive=True,  # Always check archive for seed articles
        )

        # Load progress tracker
        self.progress = IngestionProgress(self.progress_file)

        logger.info(f"Articles index: {self.articles_index_path}")
        logger.info(f"Link verification: {'disabled' if skip_verification else 'enabled'}")

    def load_existing_articles(self) -> dict:
        """
        Load existing news_articles_index.json.

        Returns:
            Dictionary with metadata and articles list

        Creates new index if file doesn't exist.
        """
        if not self.articles_index_path.exists():
            logger.warning(f"Articles index not found, creating new: {self.articles_index_path}")
            return {
                "metadata": {
                    "total_articles": 0,
                    "date_range": {"earliest": None, "latest": None},
                    "sources": {},
                    "last_updated": datetime.utcnow().isoformat(),
                    "version": "1.0.0",
                },
                "articles": [],
            }

        try:
            with open(self.articles_index_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load articles index: {e}")
            raise

    def save_articles(self, articles_data: dict):
        """
        Save articles to news_articles_index.json.

        Args:
            articles_data: Complete articles index structure

        Error Handling:
        - Creates backup before overwriting
        - Atomic write with temp file
        """
        # Create backup
        if self.articles_index_path.exists():
            backup_path = self.articles_index_path.with_suffix(".json.backup")
            try:
                with open(self.articles_index_path) as src:
                    with open(backup_path, "w") as dst:
                        dst.write(src.read())
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")

        # Atomic write
        temp_path = self.articles_index_path.with_suffix(".json.tmp")
        try:
            with open(temp_path, "w") as f:
                json.dump(articles_data, f, indent=2)

            temp_path.replace(self.articles_index_path)
            logger.info(f"Saved articles index: {self.articles_index_path}")

        except Exception as e:
            logger.error(f"Failed to save articles: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise

    def update_metadata(self, articles_data: dict):
        """
        Recalculate metadata statistics.

        Updates:
        - total_articles count
        - date_range (earliest, latest)
        - sources (article counts by publication)
        - last_updated timestamp

        Args:
            articles_data: Articles index structure to update in-place
        """
        articles = articles_data.get("articles", [])

        # Count articles by source
        sources = {}
        for article in articles:
            pub = article.get("publication", "Unknown")
            sources[pub] = sources.get(pub, 0) + 1

        # Find date range
        dates = [
            article.get("published_date") for article in articles if article.get("published_date")
        ]

        if dates:
            earliest = min(dates)
            latest = max(dates)
        else:
            earliest = latest = None

        # Update metadata
        articles_data["metadata"] = {
            "total_articles": len(articles),
            "date_range": {"earliest": earliest, "latest": latest},
            "sources": sources,
            "last_updated": datetime.utcnow().isoformat(),
            "version": "1.0.0",
        }

    def validate_article_quality(self, article: ArticleData) -> tuple[bool, str]:
        """
        Validate article meets quality standards.

        Quality Criteria:
        - Minimum 200 words
        - At least 1 entity mention
        - Title and content excerpt present
        - Extraction successful

        Args:
            article: Scraped article data

        Returns:
            (is_valid, reason) tuple
        """
        if not article.extraction_success:
            return False, "Extraction failed"

        if not article.title or len(article.title) < 10:
            return False, "Title too short or missing"

        if article.word_count < 200:
            return False, f"Word count too low ({article.word_count} < 200)"

        if not article.content_excerpt or len(article.content_excerpt) < 50:
            return False, "Content excerpt missing or too short"

        if len(article.entities_mentioned) == 0:
            return False, "No entities mentioned"

        return True, "Valid"

    def convert_to_index_format(self, article: ArticleData) -> dict:
        """
        Convert ArticleData to news_articles_index.json format.

        Matches existing article schema in index.

        Args:
            article: Scraped article data

        Returns:
            Dictionary in index format
        """
        return {
            "id": article.id,
            "title": article.title,
            "publication": article.publication,
            "author": article.author,
            "published_date": article.published_date,
            "url": article.url,
            "archive_url": article.archive_url,
            "content_excerpt": article.content_excerpt,
            "word_count": article.word_count,
            "entities_mentioned": article.entities_mentioned,
            "entity_mention_counts": article.entity_mention_counts,
            "related_timeline_events": [],
            "credibility_score": article.credibility_score,
            "credibility_factors": article.credibility_factors,
            "tags": [],  # Could extract from content
            "language": "en",
            "access_type": article.access_type,
            "scraped_at": article.scraped_at,
            "last_verified": article.last_verified,
            "archive_status": article.archive_status,
        }

    def read_seed_csv(self, source_filter: Optional[str] = None) -> list[dict]:
        """
        Read articles from news_articles_seed.csv.

        Args:
            source_filter: Filter by source key (e.g., "miami-herald")

        Returns:
            List of article dictionaries
        """
        seed_path = self.data_dir / "sources" / "news_articles_seed.csv"

        if not seed_path.exists():
            logger.error(f"Seed CSV not found: {seed_path}")
            return []

        import csv

        articles = []
        with open(seed_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Skip empty rows
                if not row.get("url") or not row.get("publication"):
                    continue

                # Apply source filter
                if source_filter:
                    source_config = TIER_1_SOURCES.get(source_filter)
                    if source_config and row["publication"] != source_config["name"]:
                        continue

                articles.append(row)

        logger.info(f"Loaded {len(articles)} articles from seed CSV")
        return articles

    def ingest_source(
        self, source: str, limit: Optional[int] = None, dry_run: bool = False
    ) -> dict:
        """
        Ingest articles from specific tier-1 source.

        Workflow:
        1. Load existing articles index
        2. Read articles from seed CSV for source
        3. For each article:
           a. Skip if already scraped (resume)
           b. Scrape content and metadata
           c. Validate quality (min 200 words, entities)
           d. Apply source credibility score
           e. Append to articles list
        4. Update metadata and save index
        5. Save progress for resume

        Args:
            source: Source key (e.g., "miami-herald")
            limit: Maximum articles to process (None = all)
            dry_run: Don't save to index (default: False)

        Returns:
            Dictionary with ingestion statistics

        Example:
            >>> results = ingester.ingest_source("miami-herald", limit=10)
            >>> print(f"Success rate: {results['success_rate']}")
        """
        if source not in TIER_1_SOURCES:
            logger.error(f"Unknown source: {source}")
            logger.error(f"Valid sources: {', '.join(TIER_1_SOURCES.keys())}")
            return {"error": "Invalid source"}

        source_config = TIER_1_SOURCES[source]
        stats = IngestionStats()

        logger.info("=" * 80)
        logger.info(f"Ingesting articles from: {source_config['name']}")
        logger.info(f"Credibility: {source_config['credibility']}")
        logger.info(f"Target: {source_config['target_articles']} articles")
        logger.info("=" * 80)

        # Load existing articles
        try:
            articles_data = self.load_existing_articles()
        except Exception as e:
            return {"error": f"Failed to load articles: {e}"}

        # Read seed CSV
        articles_to_scrape = self.read_seed_csv(source_filter=source)

        if not articles_to_scrape:
            logger.warning(f"No articles found for source: {source}")
            return {"error": "No articles in seed CSV"}

        # Apply limit
        if limit:
            articles_to_scrape = articles_to_scrape[:limit]
            logger.info(f"Limited to {limit} articles")

        stats.total = len(articles_to_scrape)

        if dry_run:
            logger.info("DRY RUN MODE - No changes will be saved")

        # Process articles
        for article_row in tqdm(articles_to_scrape, desc=f"Scraping {source}", unit="article"):
            url = article_row["url"]
            publication = article_row["publication"]
            published_date = article_row.get("published_date")
            title = article_row.get("title")

            # Skip if already scraped
            if self.progress.is_scraped(url):
                logger.info(f"Skipping already scraped: {url}")
                stats.add_skip()
                continue

            try:
                # Scrape article
                scraped: ArticleData = self.scraper.scrape_article(
                    url=url, publication=publication, published_date=published_date, title=title
                )

                # Validate quality
                is_valid, reason = self.validate_article_quality(scraped)

                if not is_valid:
                    logger.warning(f"Quality filter rejected: {url} - {reason}")
                    stats.add_quality_filter()
                    # Mark as scraped to avoid retrying
                    self.progress.add_url(url)
                    continue

                # Override credibility with source-specific score
                scraped.credibility_score = source_config["credibility"]
                scraped.credibility_factors = source_config["credibility_factors"]

                # Convert to index format
                article_dict = self.convert_to_index_format(scraped)

                # Add to articles list
                articles_data["articles"].append(article_dict)
                stats.add_success()

                # Mark as scraped
                self.progress.add_url(url)

                logger.info(
                    f"✓ Scraped: {scraped.title[:60]} "
                    f"({scraped.word_count} words, {len(scraped.entities_mentioned)} entities)"
                )

            except Exception as e:
                logger.error(f"Error scraping {url}: {e!s}")
                stats.add_failure(url=url, publication=publication, error=str(e))

            # Rate limiting
            time.sleep(1.0)

        # Update metadata
        if not dry_run:
            self.update_metadata(articles_data)

            # Save articles
            try:
                self.save_articles(articles_data)
                logger.info(f"Saved {stats.success} new articles to index")
            except Exception as e:
                logger.error(f"Failed to save articles: {e}")
                return {"error": f"Save failed: {e}"}

            # Save progress
            self.progress.save()

        # Print summary
        summary = stats.get_summary()
        logger.info("\n" + "=" * 80)
        logger.info("Ingestion Summary:")
        logger.info("=" * 80)
        logger.info(f"Source: {source_config['name']}")
        logger.info(f"Total: {summary['total']}")
        logger.info(f"Success: {summary['success']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Skipped (already scraped): {summary['skipped']}")
        logger.info(f"Quality filtered: {summary['quality_filtered']}")
        logger.info(f"Success rate: {summary['success_rate']}")
        logger.info(f"Elapsed time: {summary['elapsed_time']}")
        logger.info(f"Avg time per article: {summary['avg_time_per_article']}")
        logger.info("=" * 80)

        return summary

    def ingest_all_sources(
        self, limit_per_source: Optional[int] = None, dry_run: bool = False
    ) -> dict:
        """
        Ingest articles from all tier-1 sources.

        Processes sources in priority order (Miami Herald first).

        Args:
            limit_per_source: Max articles per source (None = all)
            dry_run: Don't save to index (default: False)

        Returns:
            Dictionary with combined statistics
        """
        # Sort sources by priority
        sorted_sources = sorted(TIER_1_SOURCES.items(), key=lambda x: x[1]["priority"])

        combined_stats = {
            "sources": {},
            "total_success": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "total_quality_filtered": 0,
        }

        for source_key, source_config in sorted_sources:
            logger.info("\n" + "=" * 80)
            logger.info(f"Processing source: {source_config['name']}")
            logger.info("=" * 80)

            results = self.ingest_source(source=source_key, limit=limit_per_source, dry_run=dry_run)

            if "error" not in results:
                combined_stats["sources"][source_key] = results
                combined_stats["total_success"] += results.get("success", 0)
                combined_stats["total_failed"] += results.get("failed", 0)
                combined_stats["total_skipped"] += results.get("skipped", 0)
                combined_stats["total_quality_filtered"] += results.get("quality_filtered", 0)

            # Pause between sources
            time.sleep(2.0)

        # Print combined summary
        logger.info("\n" + "=" * 80)
        logger.info("ALL SOURCES SUMMARY:")
        logger.info("=" * 80)
        logger.info(f"Total success: {combined_stats['total_success']}")
        logger.info(f"Total failed: {combined_stats['total_failed']}")
        logger.info(f"Total skipped: {combined_stats['total_skipped']}")
        logger.info(f"Total quality filtered: {combined_stats['total_quality_filtered']}")
        logger.info("=" * 80)

        return combined_stats


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest seed articles from tier-1 news sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape Miami Herald articles
  python ingest_seed_articles.py --source miami-herald

  # Scrape all tier-1 sources
  python ingest_seed_articles.py --all

  # Limit to 10 articles per source
  python ingest_seed_articles.py --all --limit 10

  # Dry run (no changes)
  python ingest_seed_articles.py --all --dry-run

  # Resume previous run
  python ingest_seed_articles.py --resume

Available Sources:
  - miami-herald: Miami Herald (Pulitzer finalist, credibility: 0.98)
  - ap: Associated Press (credibility: 0.95)
  - reuters: Reuters (credibility: 0.92)
  - npr: NPR (credibility: 0.95)
        """,
    )

    parser.add_argument(
        "--source", type=str, choices=list(TIER_1_SOURCES.keys()), help="Scrape specific source"
    )

    parser.add_argument("--all", action="store_true", help="Scrape all tier-1 sources")

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume previous ingestion (skips already-scraped URLs)",
    )

    parser.add_argument(
        "--limit", type=int, default=None, help="Maximum articles to process per source"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Don't save to index, just show what would be done"
    )

    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip link verification (faster but less robust)",
    )

    parser.add_argument(
        "--data-dir",
        type=str,
        default="../../data",
        help="Path to data directory (default: ../../data)",
    )

    parser.add_argument(
        "--entity-index",
        type=str,
        default="../../data/md/entities/ENTITIES_INDEX.json",
        help="Path to ENTITIES_INDEX.json",
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.source and not args.all and not args.resume:
        logger.error("Must specify --source, --all, or --resume")
        parser.print_help()
        sys.exit(1)

    # Validate paths
    data_dir = Path(args.data_dir)
    entity_index = Path(args.entity_index)

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)

    if not entity_index.exists():
        logger.error(f"Entity index not found: {entity_index}")
        sys.exit(1)

    # Initialize ingester
    try:
        ingester = SeedArticleIngester(
            data_dir=data_dir,
            entity_index_path=entity_index,
            skip_verification=args.skip_verification,
        )
    except Exception as e:
        logger.error(f"Failed to initialize ingester: {e!s}")
        sys.exit(1)

    # Run ingestion
    try:
        if args.all or args.resume:
            results = ingester.ingest_all_sources(limit_per_source=args.limit, dry_run=args.dry_run)

            # Exit code based on success
            if results["total_failed"] > results["total_success"]:
                logger.warning("More failures than successes")
                sys.exit(1)

        elif args.source:
            results = ingester.ingest_source(
                source=args.source, limit=args.limit, dry_run=args.dry_run
            )

            if "error" in results:
                sys.exit(1)

            # Exit code based on success rate
            if results["failed"] > results["success"]:
                logger.warning("More failures than successes")
                sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nIngestion interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Ingestion failed: {e!s}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
