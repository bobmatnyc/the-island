"""
News Article Ingestion Package
Comprehensive scraper for Epstein case news coverage.

Modules:
- link_verifier: Verify URL availability and retrieve archive.org snapshots
- content_extractor: Extract article content and metadata
- entity_extractor: Extract entity mentions from text
- credibility_scorer: Calculate source credibility scores
- scrape_news_articles: Main scraper combining all modules
- ingest_news_batch: Batch ingestion from CSV

Usage:
    # Single article scraping
    from scrape_news_articles import scrape_single_article

    article = scrape_single_article(
        url="https://example.com/article",
        publication="Example News"
    )

    # Batch ingestion
    from ingest_news_batch import NewsArticleIngester

    ingester = NewsArticleIngester(
        api_url="http://localhost:8000",
        entity_index_path="data/md/entities/ENTITIES_INDEX.json"
    )

    results = ingester.ingest_from_csv("articles.csv")
"""

from .content_extractor import ArticleContent, ContentExtractor, extract_single_article
from .credibility_scorer import CredibilityScore, CredibilityScorer, score_article
from .entity_extractor import EntityExtractor, extract_entities_from_text
from .ingest_news_batch import BatchIngestionStats, NewsArticleIngester
from .link_verifier import LinkStatus, LinkVerifier, verify_single_url
from .scrape_news_articles import ArticleData, NewsArticleScraper, scrape_single_article


__all__ = [
    "ArticleContent",
    "ArticleData",
    "BatchIngestionStats",
    # Content extraction
    "ContentExtractor",
    "CredibilityScore",
    # Credibility scoring
    "CredibilityScorer",
    # Entity extraction
    "EntityExtractor",
    "LinkStatus",
    # Link verification
    "LinkVerifier",
    # Batch ingestion
    "NewsArticleIngester",
    # Main scraper
    "NewsArticleScraper",
    "extract_entities_from_text",
    "extract_single_article",
    "score_article",
    "scrape_single_article",
    "verify_single_url",
]

__version__ = "1.0.0"
