#!/usr/bin/env python3
"""
Advanced Search API Routes
Epstein Document Archive - Unified Multi-Field Search with Fuzzy Matching

Provides comprehensive search across entities, flights, documents, and news articles
with advanced features like fuzzy matching, boolean operators, and faceted filtering.
"""

import json
import time
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Optional

import chromadb
from chromadb.config import Settings
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
ENTITY_INDEX_PATH = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
SEARCH_ANALYTICS_PATH = PROJECT_ROOT / "data/metadata/search_analytics.json"

COLLECTION_NAME = "epstein_documents"

# Initialize router
router = APIRouter(prefix="/api/search", tags=["Search"])

# Global instances (lazy loaded)
_chroma_client = None
_collection = None
_embedding_model = None
_entity_index = None
_search_analytics = None


def get_chroma_collection():
    """Get or create ChromaDB collection (lazy loading)."""
    global _chroma_client, _collection

    if _collection is None:
        _chroma_client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR), settings=Settings(anonymized_telemetry=False)
        )
        try:
            _collection = _chroma_client.get_collection(name=COLLECTION_NAME)
        except:
            raise HTTPException(
                status_code=503,
                detail="Vector store not initialized. Run build_vector_store.py first.",
            )

    return _collection


def get_embedding_model():
    """Get embedding model (lazy loading)."""
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    return _embedding_model


def get_entity_index():
    """Get entity index (lazy loading)."""
    global _entity_index

    if _entity_index is None:
        if ENTITY_INDEX_PATH.exists():
            with open(ENTITY_INDEX_PATH) as f:
                _entity_index = json.load(f)
        else:
            _entity_index = {"entities": []}

    return _entity_index


def load_search_analytics():
    """Get or initialize search analytics (lazy loading)."""
    global _search_analytics

    if _search_analytics is None:
        if SEARCH_ANALYTICS_PATH.exists():
            with open(SEARCH_ANALYTICS_PATH) as f:
                _search_analytics = json.load(f)
        else:
            _search_analytics = {
                "total_searches": 0,
                "popular_queries": {},
                "recent_searches": [],
                "last_updated": datetime.utcnow().isoformat(),
            }

    return _search_analytics


def save_search_analytics():
    """Save search analytics to disk."""
    global _search_analytics

    if _search_analytics:
        SEARCH_ANALYTICS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _search_analytics["last_updated"] = datetime.utcnow().isoformat()

        with open(SEARCH_ANALYTICS_PATH, "w") as f:
            json.dump(_search_analytics, f, indent=2)


def fuzzy_match(query: str, target: str, threshold: float = 0.6) -> float:
    """
    Calculate fuzzy similarity between query and target strings.

    Uses SequenceMatcher for Levenshtein-like distance calculation.

    Args:
        query: Search query string
        target: Target string to compare against
        threshold: Minimum similarity threshold (0.0-1.0)

    Returns:
        Similarity score (0.0-1.0), or 0.0 if below threshold
    """
    query_lower = query.lower()
    target_lower = target.lower()

    # Exact match
    if query_lower == target_lower:
        return 1.0

    # Substring match gets high score
    if query_lower in target_lower:
        return 0.9

    # Calculate sequence similarity
    similarity = SequenceMatcher(None, query_lower, target_lower).ratio()

    return similarity if similarity >= threshold else 0.0


def parse_boolean_query(query: str) -> dict[str, list[str]]:
    """
    Parse boolean operators from query string.

    Supports AND, OR, NOT operators:
    - "term1 AND term2" - both must be present
    - "term1 OR term2" - either must be present
    - "term1 NOT term2" - first present, second absent

    Args:
        query: Search query with optional boolean operators

    Returns:
        Dictionary with 'must', 'should', and 'must_not' term lists
    """
    result = {"must": [], "should": [], "must_not": []}  # AND terms  # OR terms  # NOT terms

    # Simple parsing (can be enhanced with proper query parser)
    terms = query.split()
    current_mode = "must"  # Default to AND behavior

    i = 0
    while i < len(terms):
        term = terms[i]

        if term.upper() == "AND":
            current_mode = "must"
        elif term.upper() == "OR":
            current_mode = "should"
        elif term.upper() == "NOT":
            if i + 1 < len(terms):
                result["must_not"].append(terms[i + 1].lower())
                i += 1
        else:
            result[current_mode].append(term.lower())

        i += 1

    return result


# Pydantic Models


class SearchFilters(BaseModel):
    """Filter options for advanced search."""

    doc_types: Optional[list[str]] = None
    sources: Optional[list[str]] = None
    entity_types: Optional[list[str]] = None
    date_start: Optional[str] = None
    date_end: Optional[str] = None
    min_similarity: Optional[float] = 0.5


class SearchResult(BaseModel):
    """Unified search result format."""

    id: str
    type: str  # entity, document, flight, news
    title: str
    description: str
    similarity: float
    metadata: dict[str, Any]
    highlights: Optional[list[str]] = None


class UnifiedSearchResponse(BaseModel):
    """Response for unified search."""

    query: str
    total_results: int
    search_time_ms: float
    results: list[SearchResult]
    facets: dict[str, dict[str, int]]
    suggestions: list[str]


class SearchSuggestion(BaseModel):
    """Search suggestion/autocomplete result."""

    text: str
    type: str
    score: float
    metadata: Optional[dict[str, Any]] = None


# API Endpoints


@router.get("/unified", response_model=UnifiedSearchResponse)
async def unified_search(
    query: str = Query(..., description="Search query with optional boolean operators"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    fields: Optional[str] = Query(
        "all",
        description="Comma-separated fields to search: all, entities, documents, flights, news",
    ),
    fuzzy: bool = Query(True, description="Enable fuzzy matching for typos"),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0, description="Minimum similarity score"),
    doc_type: Optional[str] = Query(None, description="Filter by document type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    date_start: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_end: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
):
    """
    Unified multi-field search across all data sources.

    Features:
    - Multi-field search (entities, documents, flights, news)
    - Fuzzy matching for typo tolerance
    - Boolean operators (AND, OR, NOT)
    - Date range filtering
    - Faceted results for filtering UI
    - Search suggestions

    Args:
        query: Search query (supports AND, OR, NOT operators)
        limit: Maximum results to return
        offset: Pagination offset
        fields: Which fields to search (all, entities, documents, flights, news)
        fuzzy: Enable fuzzy matching
        min_similarity: Minimum similarity threshold
        doc_type: Filter by document type
        source: Filter by source
        date_start: Start date for filtering
        date_end: End date for filtering

    Returns:
        Unified search results with facets and suggestions
    """
    start_time = time.time()

    try:
        # Track search analytics
        analytics = load_search_analytics()
        analytics["total_searches"] += 1
        analytics["popular_queries"][query] = analytics["popular_queries"].get(query, 0) + 1
        analytics["recent_searches"].insert(
            0, {"query": query, "timestamp": datetime.utcnow().isoformat(), "fields": fields}
        )
        analytics["recent_searches"] = analytics["recent_searches"][:100]  # Keep last 100
        save_search_analytics()

        # Parse boolean query
        boolean_terms = parse_boolean_query(query)

        # Determine which fields to search
        search_fields = fields.split(",") if fields != "all" else ["entities", "documents", "news"]

        all_results = []
        facets = {"types": {}, "sources": {}, "doc_types": {}, "entity_types": {}}

        # Search entities
        if "entities" in search_fields or "all" in search_fields:
            entity_results = await search_entities(query, boolean_terms, fuzzy, min_similarity)
            all_results.extend(entity_results)

            for result in entity_results:
                facets["types"]["entity"] = facets["types"].get("entity", 0) + 1

        # Search documents (via vector store)
        if "documents" in search_fields or "all" in search_fields:
            doc_results = await search_documents(
                query, boolean_terms, min_similarity, doc_type, source, date_start, date_end
            )
            all_results.extend(doc_results)

            for result in doc_results:
                facets["types"]["document"] = facets["types"].get("document", 0) + 1
                result_doc_type = result.metadata.get("doc_type", "unknown")
                facets["doc_types"][result_doc_type] = (
                    facets["doc_types"].get(result_doc_type, 0) + 1
                )
                result_source = result.metadata.get("source", "unknown")
                facets["sources"][result_source] = facets["sources"].get(result_source, 0) + 1

        # Search news articles
        if "news" in search_fields or "all" in search_fields:
            news_results = await search_news(
                query, boolean_terms, min_similarity, date_start, date_end
            )
            all_results.extend(news_results)

            for result in news_results:
                facets["types"]["news"] = facets["types"].get("news", 0) + 1

        # Sort by similarity
        all_results.sort(key=lambda x: x.similarity, reverse=True)

        # Apply pagination
        paginated_results = all_results[offset : offset + limit]

        # Generate suggestions based on query
        suggestions = generate_suggestions(query, analytics)

        search_time = (time.time() - start_time) * 1000

        return UnifiedSearchResponse(
            query=query,
            total_results=len(all_results),
            search_time_ms=search_time,
            results=paginated_results,
            facets=facets,
            suggestions=suggestions[:5],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def search_entities(
    query: str, boolean_terms: dict[str, list[str]], fuzzy: bool, min_similarity: float
) -> list[SearchResult]:
    """Search entities with fuzzy matching."""
    entity_index = get_entity_index()
    entities = entity_index.get("entities", [])

    results = []

    for entity in entities:
        name = entity.get("name", "")
        aliases = entity.get("aliases", [])
        biography = entity.get("biography", "")

        # Calculate similarity scores
        name_score = (
            fuzzy_match(query, name, 0.6)
            if fuzzy
            else (1.0 if query.lower() in name.lower() else 0.0)
        )

        # Check aliases
        alias_scores = (
            [fuzzy_match(query, alias, 0.6) for alias in aliases]
            if fuzzy
            else [1.0 if query.lower() in alias.lower() else 0.0 for alias in aliases]
        )
        max_alias_score = max(alias_scores) if alias_scores else 0.0

        # Check biography
        bio_score = 0.5 if query.lower() in biography.lower() else 0.0

        # Take best score
        best_score = max(name_score, max_alias_score, bio_score)

        if best_score >= min_similarity:
            results.append(
                SearchResult(
                    id=f"entity:{name}",
                    type="entity",
                    title=name,
                    description=biography[:200] + "..." if len(biography) > 200 else biography,
                    similarity=best_score,
                    metadata={
                        "aliases": aliases,
                        "categories": entity.get("categories", []),
                        "sources": entity.get("sources", []),
                    },
                    highlights=[name, *aliases[:3]],
                )
            )

    return results


async def search_documents(
    query: str,
    boolean_terms: dict[str, list[str]],
    min_similarity: float,
    doc_type: Optional[str],
    source: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
) -> list[SearchResult]:
    """Search documents via vector store."""
    collection = get_chroma_collection()
    model = get_embedding_model()

    # Generate query embedding
    query_embedding = model.encode([query])[0]

    # Build where filter
    where_filter = {}
    if doc_type:
        where_filter["doc_type"] = doc_type
    if source:
        where_filter["source"] = source

    # Search
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=50,
        where=where_filter if where_filter else None,
    )

    search_results = []

    for i in range(len(results["ids"][0])):
        doc_id = results["ids"][0][i]
        distance = results["distances"][0][i]
        similarity = 1 - distance
        text = results["documents"][0][i]
        metadata = results["metadatas"][0][i]

        if similarity >= min_similarity:
            # Create excerpt with context
            excerpt = text[:300] + "..." if len(text) > 300 else text

            search_results.append(
                SearchResult(
                    id=doc_id,
                    type="document",
                    title=metadata.get("filename", "Unknown Document"),
                    description=excerpt,
                    similarity=float(similarity),
                    metadata=metadata,
                    highlights=None,
                )
            )

    return search_results


async def search_news(
    query: str,
    boolean_terms: dict[str, list[str]],
    min_similarity: float,
    date_start: Optional[str],
    date_end: Optional[str],
) -> list[SearchResult]:
    """Search news articles."""
    collection = get_chroma_collection()
    model = get_embedding_model()

    # Generate query embedding
    query_embedding = model.encode([query])[0]

    # Build where filter for news articles
    where_filter = {"doc_type": "news_article"}

    # Search
    results = collection.query(
        query_embeddings=[query_embedding.tolist()], n_results=30, where=where_filter
    )

    search_results = []

    for i in range(len(results["ids"][0])):
        doc_id = results["ids"][0][i]
        distance = results["distances"][0][i]
        similarity = 1 - distance
        text = results["documents"][0][i]
        metadata = results["metadatas"][0][i]

        if similarity >= min_similarity:
            excerpt = text[:300] + "..." if len(text) > 300 else text

            search_results.append(
                SearchResult(
                    id=doc_id,
                    type="news",
                    title=metadata.get("title", "News Article"),
                    description=excerpt,
                    similarity=float(similarity),
                    metadata=metadata,
                    highlights=None,
                )
            )

    return search_results


def generate_suggestions(query: str, analytics: dict) -> list[str]:
    """
    Generate search suggestions based on query and analytics.

    Returns related queries that might be helpful.
    """
    suggestions = []

    # Get popular queries that are similar
    popular = analytics.get("popular_queries", {})
    query_lower = query.lower()

    for pop_query, _count in sorted(popular.items(), key=lambda x: x[1], reverse=True)[:20]:
        if pop_query != query and query_lower in pop_query.lower():
            suggestions.append(pop_query)

    # Add entity name suggestions
    entity_index = get_entity_index()
    entities = entity_index.get("entities", [])

    for entity in entities[:100]:  # Check top 100 entities
        name = entity.get("name", "")
        if query_lower in name.lower() and name not in suggestions:
            suggestions.append(name)

    return suggestions[:10]


@router.get("/suggestions", response_model=list[SearchSuggestion])
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Partial search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum suggestions"),
):
    """
    Get autocomplete suggestions for search query.

    Provides real-time suggestions based on:
    - Entity names and aliases
    - Popular search queries
    - Document titles

    Args:
        query: Partial search query (minimum 2 characters)
        limit: Maximum number of suggestions

    Returns:
        List of search suggestions with type and score
    """
    try:
        suggestions = []
        query_lower = query.lower()

        # Search entities
        entity_index = get_entity_index()
        entities = entity_index.get("entities", [])

        for entity in entities:
            name = entity.get("name", "")
            aliases = entity.get("aliases", [])

            # Check name
            if query_lower in name.lower():
                score = fuzzy_match(query, name, 0.5)
                if score > 0:
                    suggestions.append(
                        SearchSuggestion(
                            text=name,
                            type="entity",
                            score=score,
                            metadata={"categories": entity.get("categories", [])},
                        )
                    )

            # Check aliases
            for alias in aliases:
                if query_lower in alias.lower():
                    score = fuzzy_match(query, alias, 0.5)
                    if score > 0:
                        suggestions.append(
                            SearchSuggestion(
                                text=f"{alias} ({name})",
                                type="entity_alias",
                                score=score,
                                metadata={"canonical_name": name},
                            )
                        )

        # Get popular queries
        analytics = load_search_analytics()
        popular = analytics.get("popular_queries", {})

        for pop_query, count in popular.items():
            if query_lower in pop_query.lower():
                score = fuzzy_match(query, pop_query, 0.5)
                if score > 0:
                    suggestions.append(
                        SearchSuggestion(
                            text=pop_query,
                            type="popular_query",
                            score=score * 0.8,  # Slightly lower priority
                            metadata={"search_count": count},
                        )
                    )

        # Sort by score and limit
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:limit]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_search_analytics():
    """
    Get search analytics data.

    Returns:
    - Total number of searches
    - Popular search queries
    - Recent search history
    - Search trends

    Returns:
        Search analytics statistics
    """
    try:
        analytics = load_search_analytics()

        # Calculate top queries
        popular = analytics.get("popular_queries", {})
        top_queries = sorted(
            [{"query": q, "count": c} for q, c in popular.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:20]

        # Get recent searches (last 50)
        recent = analytics.get("recent_searches", [])[:50]

        return {
            "total_searches": analytics.get("total_searches", 0),
            "top_queries": top_queries,
            "recent_searches": recent,
            "last_updated": analytics.get("last_updated"),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/analytics/history")
async def clear_search_history():
    """
    Clear search history and analytics.

    Useful for privacy or testing purposes.
    Keeps popular queries but removes recent searches.

    Returns:
        Confirmation message
    """
    try:
        global _search_analytics

        analytics = load_search_analytics()
        analytics["recent_searches"] = []
        analytics["last_updated"] = datetime.utcnow().isoformat()

        save_search_analytics()

        return {"status": "success", "message": "Search history cleared"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
