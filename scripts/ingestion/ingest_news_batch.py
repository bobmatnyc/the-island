#!/usr/bin/env python3
"""
Batch News Article Ingestion Script
Processes CSV of article URLs and ingests into archive database.

Design Decision: CSV-Based Batch Processing
Rationale: CSV format is simple, universal, and easy to create/edit. Allows
for manual curation of article lists before ingestion. Progress tracking and
error handling ensure resilience for large batches.

Trade-offs:
- Simplicity: CSV format vs. complex database source
- Performance: Sequential processing (3-5 sec/article) vs. parallel (complex)
- Error handling: Individual failures don't stop batch

Performance:
- Processing time: ~3-5 seconds per article average
  - Link verification: 1 second
  - Content extraction: 1-2 seconds
  - Entity extraction: 0.2 seconds
  - API POST: 0.5-1 second
- Throughput: ~15-20 articles per minute
- 100 articles: ~5-7 minutes

Usage:
    python ingest_news_batch.py input.csv --limit 100 --dry-run
    python ingest_news_batch.py articles.csv --api-url http://localhost:8000
    python ingest_news_batch.py seed.csv --skip-verification
"""

import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# Import scraper
from scrape_news_articles import ArticleData, NewsArticleScraper
from tqdm import tqdm


# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BatchIngestionStats:
    """Track ingestion statistics."""

    def __init__(self):
        self.total = 0
        self.success = 0
        self.failed = 0
        self.skipped = 0
        self.errors: list[dict] = []
        self.start_time = time.time()

    def add_success(self):
        self.success += 1

    def add_failure(self, url: str, publication: str, error: str):
        self.failed += 1
        self.errors.append({"url": url, "publication": publication, "error": error})

    def add_skip(self):
        self.skipped += 1

    def get_summary(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": f"{(self.success / max(1, self.total)) * 100:.1f}%",
            "elapsed_time": f"{elapsed:.1f}s",
            "avg_time_per_article": f"{elapsed / max(1, self.total):.1f}s",
        }


class NewsArticleIngester:
    """
    Batch article ingestion from CSV.

    CSV Format:
        url,publication,published_date,title,notes
        https://example.com/article,Example News,2024-01-15,Optional Title,Optional notes

    Required columns: url, publication
    Optional columns: published_date, title, notes

    Features:
    - Progress tracking with tqdm
    - Error logging to file
    - Dry-run mode (no API calls)
    - Limit processing for testing
    - Skip link verification (faster)

    Example:
        ingester = NewsArticleIngester(
            api_url="http://localhost:8000",
            entity_index_path="data/md/entities/ENTITIES_INDEX.json"
        )

        results = ingester.ingest_from_csv(
            csv_path="articles.csv",
            limit=100,
            dry_run=False
        )

        print(f"Success: {results['success']}/{results['total']}")
    """

    def __init__(
        self, api_url: str, entity_index_path: str | Path, skip_verification: bool = False
    ):
        """
        Initialize batch ingester.

        Args:
            api_url: FastAPI server URL (e.g., "http://localhost:8000")
            entity_index_path: Path to ENTITIES_INDEX.json
            skip_verification: Skip link verification (faster, default: False)
        """
        self.api_url = api_url.rstrip("/")
        self.skip_verification = skip_verification

        # Initialize scraper
        logger.info("Initializing scraper...")
        self.scraper = NewsArticleScraper(
            entity_index_path=entity_index_path, verify_links=not skip_verification
        )

        logger.info(f"API URL: {self.api_url}")
        logger.info(f"Link verification: {'disabled' if skip_verification else 'enabled'}")

    def _read_csv(self, csv_path: Path) -> list[dict]:
        """
        Read articles from CSV file.

        Args:
            csv_path: Path to CSV file

        Returns:
            List of article dictionaries

        Raises:
            FileNotFoundError: If CSV doesn't exist
            ValueError: If CSV missing required columns
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        articles = []

        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)

            # Validate required columns
            required = {"url", "publication"}
            if not required.issubset(reader.fieldnames or set()):
                raise ValueError(
                    f"CSV missing required columns. "
                    f"Required: {required}, Found: {reader.fieldnames}"
                )

            # Read rows
            for row in reader:
                # Skip empty rows
                if not row.get("url") or not row.get("publication"):
                    continue

                articles.append(row)

        logger.info(f"Loaded {len(articles)} articles from CSV")
        return articles

    def _post_to_api(self, article_data: dict) -> bool:
        """
        POST article to API endpoint.

        Args:
            article_data: Article data in API format

        Returns:
            True if successful, False otherwise

        Error Handling:
        - Network errors: Logged and return False
        - 4xx/5xx errors: Logged with response body
        - Timeout: 30 seconds max
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/news/articles",
                json=article_data,
                timeout=30,
                headers={"Content-Type": "application/json"},
            )

            response.raise_for_status()
            logger.info(f"Successfully posted article: {article_data['title'][:50]}")
            return True

        except requests.HTTPError as e:
            logger.error(
                f"HTTP error posting article: {e.response.status_code}\n"
                f"Response: {e.response.text[:500]}"
            )
            return False

        except requests.Timeout:
            logger.error("Timeout posting article (>30s)")
            return False

        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)[:200]}")
            return False

    def ingest_from_csv(
        self, csv_path: str | Path, limit: Optional[int] = None, dry_run: bool = False
    ) -> dict:
        """
        Ingest articles from CSV file.

        Workflow:
        1. Read articles from CSV
        2. For each article:
           a. Scrape content and metadata
           b. POST to API (unless dry_run)
           c. Track success/failure
        3. Write error log if failures
        4. Return statistics

        Args:
            csv_path: Path to CSV file
            limit: Maximum articles to process (None = all)
            dry_run: Don't POST to API, just scrape (default: False)

        Returns:
            Dictionary with ingestion statistics

        Example:
            >>> results = ingester.ingest_from_csv("articles.csv", limit=10)
            >>> print(f"Success rate: {results['success_rate']}")
        """
        csv_path = Path(csv_path)
        stats = BatchIngestionStats()

        # Read CSV
        try:
            articles = self._read_csv(csv_path)
        except Exception as e:
            logger.error(f"Failed to read CSV: {e!s}")
            return {"error": str(e)}

        # Apply limit
        if limit:
            articles = articles[:limit]
            logger.info(f"Limited to {limit} articles")

        stats.total = len(articles)

        if dry_run:
            logger.info("DRY RUN MODE - No API calls will be made")

        # Process articles
        for article in tqdm(articles, desc="Ingesting articles", unit="article"):
            url = article["url"]
            publication = article["publication"]
            published_date = article.get("published_date")
            title = article.get("title")

            try:
                # Scrape article
                scraped: ArticleData = self.scraper.scrape_article(
                    url=url, publication=publication, published_date=published_date, title=title
                )

                if not scraped.extraction_success:
                    stats.add_failure(
                        url=url,
                        publication=publication,
                        error=scraped.error_message or "Extraction failed",
                    )
                    continue

                # Convert to API format
                api_data = self.scraper.to_api_format(scraped)

                # POST to API (unless dry_run)
                if not dry_run:
                    success = self._post_to_api(api_data)

                    if success:
                        stats.add_success()
                    else:
                        stats.add_failure(url=url, publication=publication, error="API POST failed")
                else:
                    # Dry run - just count as success
                    stats.add_success()
                    logger.info(f"[DRY RUN] Would post: {scraped.title[:50]}")

            except Exception as e:
                logger.error(f"Error processing {url}: {e!s}")
                stats.add_failure(url=url, publication=publication, error=str(e))

            # Rate limiting (be nice to servers)
            time.sleep(0.5)

        # Write error log
        if stats.errors:
            error_log_path = csv_path.parent / f"{csv_path.stem}_errors.json"
            with open(error_log_path, "w") as f:
                json.dump(stats.errors, f, indent=2)
            logger.info(f"Error log written to: {error_log_path}")

        # Return summary
        summary = stats.get_summary()
        logger.info("\n" + "=" * 80)
        logger.info("Ingestion Summary:")
        logger.info("=" * 80)
        logger.info(f"Total: {summary['total']}")
        logger.info(f"Success: {summary['success']}")
        logger.info(f"Failed: {summary['failed']}")
        logger.info(f"Success rate: {summary['success_rate']}")
        logger.info(f"Elapsed time: {summary['elapsed_time']}")
        logger.info(f"Avg time per article: {summary['avg_time_per_article']}")
        logger.info("=" * 80)

        return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Batch ingest news articles from CSV",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (no API calls)
  python ingest_news_batch.py articles.csv --dry-run

  # Process first 10 articles
  python ingest_news_batch.py articles.csv --limit 10

  # Skip link verification (faster)
  python ingest_news_batch.py articles.csv --skip-verification

  # Custom API URL
  python ingest_news_batch.py articles.csv --api-url http://localhost:5000

CSV Format:
  url,publication,published_date,title,notes
  https://example.com/article,Example News,2024-01-15,Optional Title,Optional notes

Required columns: url, publication
Optional columns: published_date, title, notes
        """,
    )

    parser.add_argument("input_file", type=str, help="CSV file with articles to ingest")

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of articles to process (for testing)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Don't POST to API, just show what would be done"
    )

    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip link verification (faster but less robust)",
    )

    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="FastAPI server URL (default: http://localhost:8000)",
    )

    parser.add_argument(
        "--entity-index",
        type=str,
        default="../../data/md/entities/ENTITIES_INDEX.json",
        help="Path to ENTITIES_INDEX.json",
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # Validate entity index
    entity_index = Path(args.entity_index)
    if not entity_index.exists():
        logger.error(f"Entity index not found: {entity_index}")
        sys.exit(1)

    # Initialize ingester
    try:
        ingester = NewsArticleIngester(
            api_url=args.api_url,
            entity_index_path=entity_index,
            skip_verification=args.skip_verification,
        )
    except Exception as e:
        logger.error(f"Failed to initialize ingester: {e!s}")
        sys.exit(1)

    # Run ingestion
    try:
        results = ingester.ingest_from_csv(
            csv_path=input_path, limit=args.limit, dry_run=args.dry_run
        )

        # Exit code based on success rate
        if "error" in results:
            sys.exit(1)

        success_rate = results["success"] / max(1, results["total"])
        if success_rate < 0.5:
            logger.warning("Success rate below 50% - check errors")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("\nIngestion interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Ingestion failed: {e!s}")
        sys.exit(1)


if __name__ == "__main__":
    main()
