"""
News Articles API Routes
Epstein Document Archive - News Article Management

Provides endpoints for news article ingestion, search, and statistics.
Integrates with ChromaDB for semantic search and entity linking.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi import Path as PathParam
from models.news_article import (
    AccessType,
    ArticleLanguage,
    NewsArticle,
    NewsArticleCreate,
)
from pydantic import BaseModel
from services.entity_service import EntityService
from services.news_search_service import NewsSemanticSearch
from services.news_service import NewsService


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"

NEWS_INDEX_PATH = METADATA_DIR / "news_articles_index.json"
ENTITY_DOC_INDEX_PATH = METADATA_DIR / "entity_document_index.json"
TIMELINE_PATH = METADATA_DIR / "timeline.json"

# Initialize router
router = APIRouter(prefix="/api/news", tags=["News Articles"])

# Initialize services (lazy loaded)
_news_service: Optional[NewsService] = None
_entity_service: Optional[EntityService] = None
_search_service: Optional[NewsSemanticSearch] = None


def get_news_service() -> NewsService:
    """Get news service instance (lazy loading)."""
    global _news_service

    if _news_service is None:
        _news_service = NewsService(NEWS_INDEX_PATH)

    return _news_service


def get_entity_service() -> EntityService:
    """Get entity service instance (lazy loading)."""
    global _entity_service

    if _entity_service is None:
        _entity_service = EntityService(DATA_DIR)

    return _entity_service


def get_search_service() -> NewsSemanticSearch:
    """Get semantic search service instance (lazy loading)."""
    global _search_service

    if _search_service is None:
        _search_service = NewsSemanticSearch()

    return _search_service


# Response models
class ArticleListResponse(BaseModel):
    """Response model for article list endpoints"""

    articles: list[NewsArticle]
    total: int
    limit: int
    offset: int


class SourcesResponse(BaseModel):
    """Response model for sources summary"""

    sources: list[dict]
    total_sources: int


class StatsResponse(BaseModel):
    """Response model for statistics"""

    total_articles: int
    total_sources: int
    date_range: dict
    articles_by_source: dict
    last_updated: Optional[str]


# API Endpoints


@router.get("/articles", response_model=ArticleListResponse)
async def list_articles(
    entity: Optional[str] = Query(None, description="Filter by entity name or ID"),
    publication: Optional[str] = Query(None, description="Filter by publication"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    language: Optional[ArticleLanguage] = Query(None, description="Filter by language"),
    access_type: Optional[AccessType] = Query(None, description="Filter by access type"),
    min_credibility: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Minimum credibility score"
    ),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    List news articles with optional filtering.

    Supports filtering by:
    - Entity name or ID (automatically resolves names to IDs, case-insensitive)
    - Publication (case-insensitive)
    - Date range (start_date and/or end_date)
    - Tags (comma-separated, OR logic)
    - Language
    - Access type (public, paywall, archived, removed)
    - Minimum credibility score

    Returns paginated results with total count.

    Examples:
        GET /api/news/articles?entity=Jeffrey Epstein&limit=10&offset=0
        GET /api/news/articles?entity=jeffrey_epstein&limit=10&offset=0
    """
    try:
        service = get_news_service()

        # Parse tags if provided
        tags_list = None
        if tags:
            tags_list = [t.strip() for t in tags.split(",")]

        # Resolve entity ID to name if needed
        # Supports both entity IDs (e.g., "jeffrey_epstein") and names (e.g., "Jeffrey Epstein")
        # News articles store entity names, so we need to search by name
        entity_query = entity
        if entity:
            import logging

            logger = logging.getLogger(__name__)
            entity_service = get_entity_service()
            # Try as entity ID first (e.g., "jeffrey_epstein")
            entity_obj = entity_service.get_entity_by_id(entity)
            if entity_obj:
                # Found by ID - get canonical name
                canonical_name = (
                    entity_obj.get("name") if isinstance(entity_obj, dict) else entity_obj.name
                )

                # Handle name format inconsistency:
                # Entity index uses "LastName, FirstName" format
                # News articles use "FirstName LastName" format
                if ", " in canonical_name:
                    # Convert "Epstein, Jeffrey" -> "Jeffrey Epstein"
                    parts = canonical_name.split(", ", 1)
                    entity_query = f"{parts[1]} {parts[0]}"
                    logger.info(
                        f"Resolved entity ID '{entity}' to name '{canonical_name}' -> '{entity_query}'"
                    )
                else:
                    entity_query = canonical_name
                    logger.info(f"Resolved entity ID '{entity}' to name '{entity_query}'")
            else:
                # Not found by ID - try as name
                # First try the name as-is
                entity_obj = entity_service.get_entity_by_name(entity)
                if not entity_obj and " " in entity and ", " not in entity:
                    # If not found and looks like "FirstName LastName" format,
                    # try converting to "LastName, FirstName" format for entity lookup
                    parts = entity.rsplit(" ", 1)  # Split on last space
                    if len(parts) == 2:
                        reversed_name = f"{parts[1]}, {parts[0]}"
                        entity_obj = entity_service.get_entity_by_name(reversed_name)
                        logger.info(f"Tried reversed format: '{reversed_name}'")

                if entity_obj:
                    # Found by name - use the entity name as-is (already in correct format)
                    # Don't convert format since entity param is already in news article format
                    entity_query = entity
                    logger.info(f"Found entity by name: using '{entity_query}'")
                else:
                    logger.info(f"Entity not found in index, using as-is: '{entity}'")
                # If still not found, use as-is (might be partial name for substring match)

        # Search with filters
        # Note: Additional filters (language, access_type, credibility) must be applied
        # BEFORE pagination to get accurate total count. The NewsService search_articles
        # method doesn't support these filters yet, so we apply them manually then re-paginate.

        # Fetch ALL matching articles (no pagination yet)
        all_articles, base_total = service.search_articles(
            entity=entity_query,
            publication=publication,
            start_date=start_date,
            end_date=end_date,
            tags=tags_list,
            limit=10000,  # High limit to get all results
            offset=0,
        )

        # Apply additional filters
        filtered_articles = all_articles

        if language:
            filtered_articles = [a for a in filtered_articles if a.language == language]

        if access_type:
            filtered_articles = [a for a in filtered_articles if a.access_type == access_type]

        if min_credibility is not None:
            filtered_articles = [
                a
                for a in filtered_articles
                if a.credibility_score is not None and a.credibility_score >= min_credibility
            ]

        # Get total AFTER all filters
        total = len(filtered_articles)

        # NOW apply pagination to filtered results
        articles = filtered_articles[offset : offset + limit]

        return ArticleListResponse(articles=articles, total=total, limit=limit, offset=offset)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article_id}", response_model=NewsArticle)
async def get_article(article_id: str = PathParam(..., description="Article ID (UUID)")):
    """
    Get single article by ID.

    Args:
        article_id: Article UUID

    Returns:
        Complete article with all metadata

    Raises:
        404: Article not found
    """
    try:
        service = get_news_service()
        article = service.get_article_by_id(article_id)

        if not article:
            raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")

        return article

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/articles", response_model=NewsArticle, status_code=201)
async def create_article(article_data: NewsArticleCreate):
    """
    Create a new article (for ingestion scripts).

    Validates article data, generates ID, updates metadata, and
    optionally links to entities and timeline events.

    Request Body:
        NewsArticleCreate with all required fields

    Returns:
        Created article with generated ID and timestamps

    Raises:
        400: Invalid article data
        500: Failed to save article

    Example:
        POST /api/news/articles
        {
            "title": "Epstein court documents unsealed",
            "publication": "New York Times",
            "published_date": "2024-01-01",
            "url": "https://nytimes.com/article",
            "content_excerpt": "New court documents reveal...",
            "entities_mentioned": ["Jeffrey Epstein", "Ghislaine Maxwell"],
            "tags": ["court documents", "unsealing"]
        }
    """
    try:
        service = get_news_service()

        # Create article
        article = service.add_article(article_data)

        # Link to entities (async in background would be better)
        if article.entities_mentioned:
            service.link_to_entities(article, ENTITY_DOC_INDEX_PATH)

        # Link to timeline events
        if article.related_timeline_events:
            service.link_to_timeline(article, TIMELINE_PATH)

        return article

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/semantic")
async def semantic_search(
    query: str = Query(..., min_length=2, description="Natural language search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    similarity_threshold: float = Query(
        0.3, ge=0.0, le=1.0, description="Minimum similarity score"
    ),
    publication: Optional[str] = Query(None, description="Filter by publication"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    min_credibility: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Minimum credibility score"
    ),
    entities: Optional[str] = Query(None, description="Filter by entities (comma-separated)"),
):
    """
    Semantic search across news articles using vector embeddings.

    Uses sentence transformers and ChromaDB to find articles semantically similar
    to the query, even if exact keywords don't match.

    Args:
        query: Natural language search query (e.g., "financial crimes and corruption")
        limit: Maximum results to return (default: 10, max: 50)
        similarity_threshold: Minimum similarity score 0.0-1.0 (default: 0.3)
        publication: Filter by publication name (optional)
        start_date: Filter articles from this date (YYYY-MM-DD, optional)
        end_date: Filter articles until this date (YYYY-MM-DD, optional)
        min_credibility: Minimum credibility score (0.0-1.0, optional)
        entities: Filter by entity mentions, comma-separated (optional)

    Returns:
        {
            "query": str,
            "results": [
                {
                    "article": {...},
                    "similarity_score": float,
                    "matched_excerpt": str
                }
            ],
            "total": int,
            "filters_applied": {...}
        }

    Examples:
        GET /api/news/search/semantic?query=financial fraud cases&limit=10
        GET /api/news/search/semantic?query=victim testimony&entities=Jeffrey Epstein&min_credibility=0.8
    """
    try:
        search_service = get_search_service()

        # Parse entities if provided
        entities_list = None
        if entities:
            entities_list = [e.strip() for e in entities.split(",")]

        # Perform semantic search
        results = search_service.semantic_search(
            query=query,
            limit=limit,
            similarity_threshold=similarity_threshold,
            publication=publication,
            start_date=start_date,
            end_date=end_date,
            min_credibility=min_credibility,
            entities=entities_list,
        )

        return {
            "query": query,
            "results": results,
            "total": len(results),
            "filters_applied": {
                "similarity_threshold": similarity_threshold,
                "publication": publication,
                "date_range": (
                    {"start": start_date, "end": end_date} if start_date or end_date else None
                ),
                "min_credibility": min_credibility,
                "entities": entities_list,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/similar/{article_id}")
async def find_similar_articles(
    article_id: str = PathParam(..., description="Reference article ID"),
    limit: int = Query(5, ge=1, le=20, description="Maximum similar articles"),
    similarity_threshold: float = Query(
        0.5, ge=0.0, le=1.0, description="Minimum similarity score"
    ),
):
    """
    Find articles similar to a given article.

    Uses the article's vector embedding to find semantically similar articles.
    Useful for "related articles" features.

    Args:
        article_id: ID of the reference article
        limit: Maximum similar articles to return (default: 5, max: 20)
        similarity_threshold: Minimum similarity score (default: 0.5)

    Returns:
        {
            "reference_article_id": str,
            "similar_articles": [
                {
                    "article": {...},
                    "similarity_score": float,
                    "matched_excerpt": str
                }
            ],
            "total": int
        }

    Example:
        GET /api/news/search/similar/1de6b30b-3c6e-49e3-935c-f2e848db1b76?limit=5
    """
    try:
        search_service = get_search_service()

        # Find similar articles
        similar = search_service.find_similar_articles(
            article_id=article_id, limit=limit, similarity_threshold=similarity_threshold
        )

        return {
            "reference_article_id": article_id,
            "similar_articles": similar,
            "total": len(similar),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/stats")
async def get_search_stats():
    """
    Get statistics about semantic search capabilities.

    Returns information about indexed articles, embedding model,
    and collection statistics.

    Returns:
        {
            "total_articles": int,
            "indexed_articles": int,
            "unindexed_articles": int,
            "embedding_model": str,
            "embedding_dimensions": int,
            ...
        }

    Example:
        GET /api/news/search/stats
    """
    try:
        search_service = get_search_service()
        stats = search_service.get_search_statistics()

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", response_model=SourcesResponse)
async def list_sources():
    """
    Get list of all news sources with statistics.

    Returns summary for each publication including:
    - Article count
    - Date range (earliest and latest articles)
    - Average credibility score

    Sorted by article count (descending).

    Example Response:
        {
            "sources": [
                {
                    "publication": "New York Times",
                    "article_count": 45,
                    "date_range": {"earliest": "2019-07-01", "latest": "2024-01-01"},
                    "average_credibility": 0.85
                }
            ],
            "total_sources": 12
        }
    """
    try:
        service = get_news_service()
        sources = service.get_sources_summary()

        return SourcesResponse(sources=sources, total_sources=len(sources))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """
    Get aggregate statistics about news articles.

    Returns:
        - Total article count
        - Total unique sources (publications)
        - Date range (earliest and latest articles)
        - Article count by source
        - Last update timestamp

    Example Response:
        {
            "total_articles": 156,
            "total_sources": 12,
            "date_range": {"earliest": "2019-07-01", "latest": "2024-01-01"},
            "articles_by_source": {
                "New York Times": 45,
                "Washington Post": 32,
                ...
            },
            "last_updated": "2025-11-20T19:33:00Z"
        }
    """
    try:
        service = get_news_service()
        stats = service.get_statistics()

        return StatsResponse(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
