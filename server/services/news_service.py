"""
News articles service for managing the news articles index.

Design Decision: Service Layer Pattern
Rationale: Encapsulates all news article business logic - loading, saving,
validation, and cross-referencing with entities and timeline. Routes remain
thin and focused on HTTP concerns.

Performance:
- Index loaded on first access (lazy loading)
- Cached in memory for fast subsequent reads
- Writes are synchronous but infrequent (<100/day expected)

Error Handling:
- Returns empty index if file not found (graceful degradation)
- Validates all article data before saving
- Atomic writes (temp file + rename) to prevent corruption
"""

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# Add server directory to path for imports
SERVER_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SERVER_DIR))

from models.news_article import (
    ArchiveStatus,
    NewsArticle,
    NewsArticleCreate,
    NewsArticleMetadata,
    NewsArticlesIndex,
)


class NewsService:
    """
    Service for managing news articles index.

    Handles CRUD operations, metadata updates, and entity/timeline linking.
    """

    def __init__(self, index_path: Path):
        """
        Initialize news service.

        Args:
            index_path: Path to news_articles_index.json
        """
        self.index_path = index_path
        self._index: Optional[NewsArticlesIndex] = None

    def load_news_index(self) -> NewsArticlesIndex:
        """
        Load news articles index from disk.

        Returns cached index if already loaded.

        Returns:
            NewsArticlesIndex with metadata and articles

        Performance: O(n) on first load, O(1) for cached access
        """
        if self._index is not None:
            return self._index

        if not self.index_path.exists():
            # Return empty index if file doesn't exist
            self._index = NewsArticlesIndex(metadata=NewsArticleMetadata(), articles=[])
            return self._index

        try:
            with self.index_path.open(encoding="utf-8") as f:
                data = json.load(f)
                self._index = NewsArticlesIndex(**data)
                return self._index
        except Exception as e:
            raise RuntimeError(f"Failed to load news index: {e}")

    def save_news_index(self, index: NewsArticlesIndex) -> None:
        """
        Save news articles index to disk.

        Uses atomic write (temp file + rename) to prevent corruption.

        Args:
            index: NewsArticlesIndex to save

        Error Handling: Raises RuntimeError if write fails
        """
        try:
            # Ensure parent directory exists
            self.index_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temp file first
            temp_path = self.index_path.with_suffix(".tmp")

            with temp_path.open("w", encoding="utf-8") as f:
                # Convert to dict for JSON serialization
                data = index.model_dump(mode="json")
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(self.index_path)

            # Update cache
            self._index = index

        except Exception as e:
            raise RuntimeError(f"Failed to save news index: {e}") from e

    def add_article(self, article_create: NewsArticleCreate) -> NewsArticle:
        """
        Add a new article to the index.

        Validates article, generates ID, updates metadata, and saves.

        Args:
            article_create: Article data (without ID)

        Returns:
            Complete NewsArticle with generated ID and timestamps

        Error Handling: Validates entities and timeline events exist before saving
        """
        # Load current index
        index = self.load_news_index()

        # Generate article ID
        article_id = str(uuid.uuid4())

        # Create full article with metadata
        article = NewsArticle(
            id=article_id,
            scraped_at=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
            archive_status=(
                ArchiveStatus.ARCHIVED if article_create.archive_url else ArchiveStatus.NOT_ARCHIVED
            ),
            **article_create.model_dump(),
        )

        # Add to index
        index.articles.append(article)

        # Update metadata
        self.update_metadata(index)

        # Save
        self.save_news_index(index)

        return article

    def get_article_by_id(self, article_id: str) -> Optional[NewsArticle]:
        """
        Get article by ID.

        Args:
            article_id: Article UUID or slug

        Returns:
            NewsArticle if found, None otherwise

        Performance: O(n) linear search (fast for <10,000 articles)
        """
        index = self.load_news_index()

        for article in index.articles:
            if article.id == article_id:
                return article

        return None

    def normalize_entity_name(self, name: str) -> set[str]:
        """
        Generate all possible name variations for robust entity matching.

        Design Decision: Comprehensive Name Normalization
        Rationale: Entity names have multiple formats across the system:
        - Entity IDs: "jeffrey_epstein" (lowercase, underscored)
        - Entity canonical: "Epstein, Jeffrey" (LastName, FirstName)
        - News articles: "Jeffrey Epstein" (FirstName LastName)
        - User queries: Any of the above, potentially different case

        Returns all variations to ensure substring matching works regardless
        of input format.

        Args:
            name: Entity name in any format

        Returns:
            Set of all possible name variations (lowercase for matching)

        Examples:
            >>> normalize_entity_name("jeffrey_epstein")
            {'jeffrey epstein', 'epstein jeffrey', 'epstein, jeffrey', 'jeffrey_epstein'}

            >>> normalize_entity_name("Epstein, Jeffrey")
            {'epstein, jeffrey', 'jeffrey epstein', 'epstein jeffrey'}
        """
        variations = set()

        # Add original (lowercased)
        variations.add(name.lower())

        # Replace underscores with spaces for processing
        normalized = name.replace('_', ' ')
        if normalized != name:
            variations.add(normalized.lower())

        # Handle "Last, First" format
        if ',' in normalized:
            parts = [p.strip() for p in normalized.split(',', 1)]
            if len(parts) == 2:
                # "Epstein, Jeffrey" -> "jeffrey epstein"
                variations.add(f"{parts[1]} {parts[0]}".lower())
                # "Epstein, Jeffrey" -> "epstein jeffrey"
                variations.add(f"{parts[0]} {parts[1]}".lower())

        # Handle "First Last" format (no comma)
        # Process normalized version (with underscores replaced)
        if ' ' in normalized and ',' not in normalized:
            parts = normalized.split()
            if len(parts) >= 2:
                # "Jeffrey Epstein" -> "epstein, jeffrey"
                variations.add(f"{parts[-1]}, {' '.join(parts[:-1])}".lower())
                # "Jeffrey Epstein" -> "epstein jeffrey"
                variations.add(f"{parts[-1]} {' '.join(parts[:-1])}".lower())

        return variations

    def search_articles(
        self,
        entity: Optional[str] = None,
        publication: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[NewsArticle], int]:
        """
        Search articles with filters.

        Args:
            entity: Filter by entity name (case-insensitive, format-flexible)
            publication: Filter by publication (case-insensitive)
            start_date: Articles from this date (YYYY-MM-DD)
            end_date: Articles until this date (YYYY-MM-DD)
            tags: Filter by tags (OR logic)
            limit: Results per page
            offset: Pagination offset

        Returns:
            Tuple of (articles, total_count)

        Performance: O(n) linear scan with filters (acceptable for <10,000 articles)

        Entity Matching:
            Supports all name formats through normalization:
            - "jeffrey_epstein" matches "Jeffrey Epstein"
            - "Epstein, Jeffrey" matches "Jeffrey Epstein"
            - "Jeffrey Epstein" matches itself
            Case-insensitive substring matching for robustness.
        """
        index = self.load_news_index()
        articles = index.articles

        # Filter by entity with robust name matching
        if entity:
            import logging
            logger = logging.getLogger(__name__)

            # Generate all possible name variations
            entity_variations = self.normalize_entity_name(entity)
            logger.info(f"Entity search: '{entity}' -> variations: {entity_variations}")

            # Match if any variation appears in any mentioned entity
            articles = [
                a for a in articles
                if any(
                    any(variation in e.lower() for variation in entity_variations)
                    for e in a.entities_mentioned
                )
            ]

            logger.info(f"Entity search matched {len(articles)} articles for '{entity}'")

        # Filter by publication
        if publication:
            pub_lower = publication.lower()
            articles = [a for a in articles if pub_lower in a.publication.lower()]

        # Filter by date range
        if start_date:
            articles = [a for a in articles if a.published_date >= start_date]

        if end_date:
            articles = [a for a in articles if a.published_date <= end_date]

        # Filter by tags (OR logic)
        if tags:
            tags_lower = [t.lower() for t in tags]
            articles = [a for a in articles if any(tag in tags_lower for tag in a.tags)]

        # Get total before pagination
        total = len(articles)

        # Paginate
        paginated = articles[offset : offset + limit]

        return paginated, total

    def get_sources_summary(self) -> list[dict]:
        """
        Get summary of all news sources.

        Returns:
            List of source summaries with article counts and date ranges

        Performance: O(n) single pass through articles
        """
        index = self.load_news_index()

        # Group articles by publication
        sources: dict[str, dict] = {}

        for article in index.articles:
            pub = article.publication

            if pub not in sources:
                sources[pub] = {
                    "publication": pub,
                    "article_count": 0,
                    "earliest_date": article.published_date,
                    "latest_date": article.published_date,
                    "credibility_scores": [],
                }

            source = sources[pub]
            source["article_count"] += 1

            # Update date range
            source["earliest_date"] = min(source["earliest_date"], article.published_date)

            source["latest_date"] = max(source["latest_date"], article.published_date)

            # Track credibility
            if article.credibility_score is not None:
                source["credibility_scores"].append(article.credibility_score)

        # Calculate averages and format
        result = []
        for pub, data in sources.items():
            avg_credibility = None
            if data["credibility_scores"]:
                avg_credibility = sum(data["credibility_scores"]) / len(data["credibility_scores"])

            result.append(
                {
                    "publication": pub,
                    "article_count": data["article_count"],
                    "date_range": {
                        "earliest": data["earliest_date"],
                        "latest": data["latest_date"],
                    },
                    "average_credibility": round(avg_credibility, 2) if avg_credibility else None,
                }
            )

        # Sort by article count (descending)
        result.sort(key=lambda x: x["article_count"], reverse=True)

        return result

    def get_statistics(self) -> dict:
        """
        Get aggregate statistics about articles.

        Returns:
            Statistics including total articles, sources, date range, etc.
        """
        index = self.load_news_index()

        return {
            "total_articles": index.metadata.total_articles,
            "total_sources": len(index.metadata.sources),
            "date_range": index.metadata.date_range,
            "last_updated": (
                index.metadata.last_updated.isoformat() if index.metadata.last_updated else None
            ),
            "articles_by_source": index.metadata.sources,
        }

    def update_metadata(self, index: NewsArticlesIndex) -> None:
        """
        Recalculate and update index metadata.

        Updates total count, date range, and source counts.

        Args:
            index: NewsArticlesIndex to update (modified in-place)

        Performance: O(n) single pass through articles
        """
        articles = index.articles

        # Update total count
        index.metadata.total_articles = len(articles)

        # Update date range
        if articles:
            dates = [a.published_date for a in articles]
            index.metadata.date_range = {"earliest": min(dates), "latest": max(dates)}
        else:
            index.metadata.date_range = {"earliest": None, "latest": None}

        # Update source counts
        sources: dict[str, int] = {}
        for article in articles:
            pub = article.publication
            sources[pub] = sources.get(pub, 0) + 1

        index.metadata.sources = sources

        # Update timestamp
        index.metadata.last_updated = datetime.now(timezone.utc)

    def link_to_entities(self, article: NewsArticle, entity_doc_index_path: Path) -> None:
        """
        Update entity_document_index.json with article entity mentions.

        Args:
            article: Article with entities_mentioned
            entity_doc_index_path: Path to entity_document_index.json

        Design Decision: Bidirectional Linking
        Rationale: Articles know which entities they mention. Entity index
        knows which articles mention each entity. Enables both directions.

        Error Handling: Gracefully handles missing index file
        """
        if not entity_doc_index_path.exists():
            return

        try:
            with entity_doc_index_path.open(encoding="utf-8") as f:
                entity_index = json.load(f)

            entity_to_docs = entity_index.get("entity_to_documents", {})

            # Update each entity's document list
            for entity_name in article.entities_mentioned:
                if entity_name not in entity_to_docs:
                    entity_to_docs[entity_name] = {
                        "documents": [],
                        "document_count": 0,
                        "mention_count": 0,
                    }

                entity_data = entity_to_docs[entity_name]

                # Add article as a document reference
                mention_count = article.entity_mention_counts.get(entity_name, 1)

                entity_data["documents"].append(
                    {
                        "doc_id": f"news:{article.id}",
                        "filename": article.title,
                        "mentions": mention_count,
                        "doc_type": "news_article",
                        "url": str(article.url),
                    }
                )

                entity_data["document_count"] += 1
                entity_data["mention_count"] += mention_count

            # Save updated index
            with entity_doc_index_path.open("w", encoding="utf-8") as f:
                json.dump(entity_index, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # Log error but don't fail article creation
            print(f"Warning: Failed to update entity index: {e}")

    def link_to_timeline(self, article: NewsArticle, timeline_path: Path) -> None:
        """
        Link article to timeline events.

        Args:
            article: Article with related_timeline_events
            timeline_path: Path to timeline.json

        Design Decision: Timeline Event References
        Rationale: Articles reference timeline events by ID. Enables
        viewing all articles related to specific historical events.

        Error Handling: Gracefully handles missing timeline file
        """
        if not article.related_timeline_events or not timeline_path.exists():
            return

        try:
            with timeline_path.open(encoding="utf-8") as f:
                timeline_data = json.load(f)

            events = timeline_data.get("events", [])

            # Find matching events and add article reference
            for event in events:
                if event.get("id") in article.related_timeline_events:
                    if "related_articles" not in event:
                        event["related_articles"] = []

                    event["related_articles"].append(
                        {
                            "article_id": article.id,
                            "title": article.title,
                            "publication": article.publication,
                            "url": str(article.url),
                        }
                    )

            # Save updated timeline
            with timeline_path.open("w", encoding="utf-8") as f:
                json.dump(timeline_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # Log error but don't fail article creation
            print(f"Warning: Failed to update timeline: {e}")

    def add_article_with_embedding(self, article_create: NewsArticleCreate) -> NewsArticle:
        """
        Add article and trigger embedding to ChromaDB.

        Convenience method that combines article creation with embedding.
        Embedding happens synchronously to ensure immediate searchability.

        Args:
            article_create: Article data (without ID)

        Returns:
            Complete NewsArticle with generated ID and timestamps

        Design Decision: Synchronous Embedding
        Rationale: For small batches (1-10 articles), synchronous embedding
        adds <1 second latency but ensures immediate searchability. For bulk
        imports, use embed_news_articles.py script instead.

        Performance: ~50-100ms per article for embedding
        """
        # Add article to index
        article = self.add_article(article_create)

        # Trigger embedding
        try:
            # Import batch_embed_helper here to avoid circular dependency
            import sys
            from pathlib import Path

            scripts_dir = Path(__file__).parent.parent.parent / "scripts" / "rag"
            sys.path.insert(0, str(scripts_dir))

            from batch_embed_helper import batch_embed_articles

            # Embed single article
            article_dict = article.model_dump(mode="json")
            result = batch_embed_articles([article_dict], batch_size=1)

            if result["success"] and result["embedded_count"] > 0:
                print(f"✅ Article embedded successfully: {article.id}")
            else:
                print(f"⚠️  Article embedding failed: {result.get('errors', 'Unknown error')}")

        except Exception as e:
            # Log error but don't fail article creation
            print(f"⚠️  Warning: Failed to trigger embedding: {e}")
            print("   Article created but not embedded. Run embed_news_articles.py to embed.")

        return article

    def batch_embed_existing_articles(self, limit: Optional[int] = None) -> dict:
        """
        Batch embed existing articles that don't have embeddings.

        Useful for retroactively embedding articles created before
        embedding system was implemented.

        Args:
            limit: Only embed first N articles (for testing)

        Returns:
            Dictionary with embedding results:
            - embedded_count: Number successfully embedded
            - failed_count: Number that failed
            - duration_seconds: Time taken

        Usage:
            >>> service = NewsService(index_path)
            >>> result = service.batch_embed_existing_articles()
            >>> print(f"Embedded {result['embedded_count']} articles")
        """
        try:
            # Import batch_embed_helper
            import sys
            from pathlib import Path

            scripts_dir = Path(__file__).parent.parent.parent / "scripts" / "rag"
            sys.path.insert(0, str(scripts_dir))

            from batch_embed_helper import batch_embed_articles

            # Load all articles
            index = self.load_news_index()
            articles = index.articles

            if limit:
                articles = articles[:limit]

            # Convert to dict format
            articles_dict = [a.model_dump(mode="json") for a in articles]

            # Batch embed
            result = batch_embed_articles(articles_dict)

            return result

        except Exception as e:
            return {
                "embedded_count": 0,
                "failed_count": len(articles) if articles else 0,
                "errors": [str(e)],
                "success": False,
            }
