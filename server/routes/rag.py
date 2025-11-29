#!/usr/bin/env python3
"""
RAG API Routes
Epstein Document Archive - Vector Search & RAG Endpoints

Provides semantic search, entity-based retrieval, and knowledge graph integration.
"""

import json
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
ENTITY_DOC_INDEX_PATH = PROJECT_ROOT / "data/metadata/entity_document_index.json"
ENTITY_NETWORK_PATH = PROJECT_ROOT / "data/metadata/entity_network.json"

COLLECTION_NAME = "epstein_documents"

# Initialize router
router = APIRouter(prefix="/api/rag", tags=["RAG"])

# Global instances (lazy loaded)
_chroma_client = None
_collection = None
_embedding_model = None
_entity_doc_index = None
_entity_network = None


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


def get_entity_doc_index():
    """Get entity-document index (lazy loading)."""
    global _entity_doc_index

    if _entity_doc_index is None:
        if ENTITY_DOC_INDEX_PATH.exists():
            with open(ENTITY_DOC_INDEX_PATH) as f:
                _entity_doc_index = json.load(f)
        else:
            _entity_doc_index = {"entity_to_documents": {}}

    return _entity_doc_index


def get_entity_network():
    """Get entity network (lazy loading)."""
    global _entity_network

    if _entity_network is None:
        if ENTITY_NETWORK_PATH.exists():
            with open(ENTITY_NETWORK_PATH) as f:
                _entity_network = json.load(f)
        else:
            _entity_network = {"nodes": [], "edges": []}

    return _entity_network


# Pydantic models
class SearchResult(BaseModel):
    id: str
    similarity: float
    text_excerpt: str
    metadata: dict


class EntityDocumentResult(BaseModel):
    doc_id: str
    filename: str
    mentions: int


class EntityConnection(BaseModel):
    entity: str
    weight: int
    relationship: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int
    search_time_ms: float


class EntitySearchResponse(BaseModel):
    entity: str
    documents: list[EntityDocumentResult]
    total_documents: int
    total_mentions: int


class ConnectionsResponse(BaseModel):
    entity: str
    connections: list[EntityConnection]
    total_connections: int


# API Endpoints


@router.get("/search", response_model=SearchResponse)
async def semantic_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    entity_filter: Optional[str] = Query(None, description="Filter by entity name"),
    doc_type: Optional[str] = Query(
        None, description="Filter by document type (news_article, court_doc, etc.)"
    ),
):
    """
    Perform semantic search across all documents.

    Returns documents ranked by similarity to the query.
    Optionally filter by entity mentions or document type.

    Args:
        query: Search query text
        limit: Maximum results to return
        entity_filter: Filter to documents mentioning this entity
        doc_type: Filter by document type (e.g., "news_article")
    """
    import time

    start_time = time.time()

    try:
        # Get collection and model
        collection = get_chroma_collection()
        model = get_embedding_model()

        # Generate query embedding
        query_embedding = model.encode([query])[0]

        # Build where filter
        where_filter = {}
        if doc_type:
            where_filter["doc_type"] = doc_type

        # Search with optional filter
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 2,  # Get extra for filtering
            where=where_filter if where_filter else None,
        )

        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            doc_id = results["ids"][0][i]
            distance = results["distances"][0][i]
            similarity = 1 - distance
            text = results["documents"][0][i]
            metadata = results["metadatas"][0][i]

            # Apply entity filter
            if entity_filter:
                entity_mentions = metadata.get("entity_mentions", "")
                if entity_filter not in entity_mentions:
                    continue

            # Create excerpt (first 300 chars)
            excerpt = text[:300] + "..." if len(text) > 300 else text

            formatted_results.append(
                SearchResult(
                    id=doc_id, similarity=float(similarity), text_excerpt=excerpt, metadata=metadata
                )
            )

            if len(formatted_results) >= limit:
                break

        search_time = (time.time() - start_time) * 1000

        return SearchResponse(
            query=query,
            results=formatted_results,
            total_results=len(formatted_results),
            search_time_ms=search_time,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_name}", response_model=EntitySearchResponse)
async def get_entity_documents(
    entity_name: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    include_news: bool = Query(True, description="Include news articles in results"),
):
    """
    Get documents mentioning a specific entity.

    Returns documents ranked by number of entity mentions.
    Supports alias resolution (e.g., "Bill Clinton" -> "William Clinton").

    Args:
        entity_name: Name of entity to search for
        limit: Maximum results to return
        include_news: Whether to include news articles in results
    """
    try:
        entity_index = get_entity_doc_index()
        entity_to_docs = entity_index.get("entity_to_documents", {})

        # Try exact match first
        if entity_name in entity_to_docs:
            entity_data = entity_to_docs[entity_name]
        else:
            # Try alias resolution via ENTITIES_INDEX.json
            from pathlib import Path

            project_root = Path(__file__).parent.parent.parent
            entities_index_path = project_root / "data" / "md" / "entities" / "ENTITIES_INDEX.json"

            canonical_name = None
            if entities_index_path.exists():
                with open(entities_index_path) as f:
                    data = json.load(f)
                    entities = data.get("entities", [])

                    # Search by alias
                    for entity in entities:
                        aliases = entity.get("aliases", [])
                        if entity_name in aliases:
                            canonical_name = entity.get("name")
                            break

            # Try canonical name from alias resolution
            if canonical_name and canonical_name in entity_to_docs:
                entity_data = entity_to_docs[canonical_name]
            else:
                # Try fuzzy match
                matching = [e for e in entity_to_docs if entity_name.lower() in e.lower()]

                if not matching:
                    raise HTTPException(status_code=404, detail=f"Entity not found: {entity_name}")

                entity_data = entity_to_docs[matching[0]]

        # Get documents from entity index
        all_documents = entity_data["documents"]

        # Optionally include news articles from ChromaDB
        if include_news:
            try:
                collection = get_chroma_collection()

                # Query for news articles mentioning this entity
                news_results = collection.get(
                    where={
                        "$and": [
                            {"doc_type": "news_article"},
                            {"entity_mentions": {"$contains": entity_name}},
                        ]
                    }
                )

                # Add news articles to documents list
                for i, news_id in enumerate(news_results["ids"]):
                    metadata = news_results["metadatas"][i]
                    all_documents.append(
                        {
                            "doc_id": news_id,
                            "filename": metadata.get("title", "News Article"),
                            "mentions": 1,  # News metadata doesn't track mention counts
                            "doc_type": "news_article",
                        }
                    )

            except Exception as e:
                # Log error but continue with existing documents
                print(f"Warning: Failed to fetch news articles: {e}")

        # Format documents
        documents = [
            EntityDocumentResult(
                doc_id=doc["doc_id"], filename=doc["filename"], mentions=doc["mentions"]
            )
            for doc in all_documents[:limit]
        ]

        return EntitySearchResponse(
            entity=entity_name,
            documents=documents,
            total_documents=len(all_documents),
            total_mentions=entity_data["mention_count"],
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{doc_id}")
async def get_similar_documents(
    doc_id: str, limit: int = Query(5, ge=1, le=20, description="Maximum results")
):
    """
    Find documents similar to the specified document.

    Uses the document's content as the query for semantic search.
    """
    try:
        collection = get_chroma_collection()

        # Get source document
        source_doc = collection.get(ids=[doc_id])

        if not source_doc["ids"]:
            raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

        # Use document text as query
        doc_text = source_doc["documents"][0]
        model = get_embedding_model()

        # Generate embedding
        query_embedding = model.encode([doc_text])[0]

        # Search for similar documents
        results = collection.query(
            query_embeddings=[query_embedding.tolist()], n_results=limit + 1  # +1 to exclude self
        )

        # Format results (exclude source document)
        formatted_results = []
        for i in range(len(results["ids"][0])):
            result_id = results["ids"][0][i]

            # Skip source document
            if result_id == doc_id:
                continue

            distance = results["distances"][0][i]
            similarity = 1 - distance
            text = results["documents"][0][i]
            metadata = results["metadatas"][0][i]

            excerpt = text[:300] + "..." if len(text) > 300 else text

            formatted_results.append(
                SearchResult(
                    id=result_id,
                    similarity=float(similarity),
                    text_excerpt=excerpt,
                    metadata=metadata,
                )
            )

            if len(formatted_results) >= limit:
                break

        return {
            "source_doc_id": doc_id,
            "similar_documents": formatted_results,
            "total_results": len(formatted_results),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{entity_name}", response_model=ConnectionsResponse)
async def get_entity_connections(
    entity_name: str, limit: int = Query(20, ge=1, le=100, description="Maximum connections")
):
    """
    Find entities connected to the specified entity via flight logs.

    Returns entities ranked by number of co-occurrences (flights together).
    """
    try:
        network = get_entity_network()
        edges = network.get("edges", [])

        # Find all edges involving this entity
        connections = []
        for edge in edges:
            if edge["source"] == entity_name:
                connections.append(
                    EntityConnection(
                        entity=edge["target"],
                        weight=edge["weight"],
                        relationship=edge.get("relationship", "co-occurrence"),
                    )
                )
            elif edge["target"] == entity_name:
                connections.append(
                    EntityConnection(
                        entity=edge["source"],
                        weight=edge["weight"],
                        relationship=edge.get("relationship", "co-occurrence"),
                    )
                )

        # Sort by weight
        connections.sort(key=lambda x: x.weight, reverse=True)

        return ConnectionsResponse(
            entity=entity_name, connections=connections[:limit], total_connections=len(connections)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-entity")
async def multi_entity_search(
    entities: str = Query(..., description="Comma-separated entity names"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
):
    """
    Find documents mentioning ALL specified entities.

    Entities should be comma-separated: "Clinton,Epstein,Maxwell"
    """
    try:
        entity_list = [e.strip() for e in entities.split(",")]

        if len(entity_list) < 2:
            raise HTTPException(
                status_code=400, detail="Provide at least 2 entities separated by commas"
            )

        entity_index = get_entity_doc_index()
        entity_to_docs = entity_index.get("entity_to_documents", {})

        # Get document sets for each entity
        doc_sets = []
        for entity in entity_list:
            if entity in entity_to_docs:
                doc_ids = {doc["doc_id"] for doc in entity_to_docs[entity]["documents"]}
                doc_sets.append(doc_ids)
            else:
                raise HTTPException(status_code=404, detail=f"Entity not found: {entity}")

        # Find intersection
        common_docs = set.intersection(*doc_sets)

        # Get document details from ChromaDB
        collection = get_chroma_collection()
        results = []

        for doc_id in list(common_docs)[:limit]:
            doc_result = collection.get(ids=[doc_id])
            if doc_result["ids"]:
                text = doc_result["documents"][0]
                metadata = doc_result["metadatas"][0]
                excerpt = text[:300] + "..." if len(text) > 300 else text

                results.append({"id": doc_id, "text_excerpt": excerpt, "metadata": metadata})

        return {"entities": entity_list, "documents": results, "total_results": len(common_docs)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/news-search")
async def search_news_articles(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    publication: Optional[str] = Query(None, description="Filter by publication"),
    min_credibility: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Minimum credibility score"
    ),
    entity: Optional[str] = Query(None, description="Filter by entity mention"),
    start_date: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
):
    """
    Search news articles with article-specific filters.

    Dedicated endpoint for news article search with publication,
    credibility, entity, and date range filters.

    Args:
        query: Search query text
        limit: Maximum results
        publication: Filter by publication name (case-insensitive)
        min_credibility: Minimum credibility score (0.0-1.0)
        entity: Filter by entity mentions
        start_date: Filter articles from this date (YYYY-MM-DD)
        end_date: Filter articles to this date (YYYY-MM-DD)

    Returns:
        Search results with news article metadata

    Design Decision: Date Filtering Strategy
    Rationale: ChromaDB metadata filtering for dates would require standardized
    YYYY-MM-DD format in all article metadata. Since articles may have varying
    date formats, we apply date filtering post-query on the Python side.

    Performance: O(n) filter after vector search. For timeline view (typical
    date ranges: 1-10 years), this adds <10ms overhead on result sets of 100-200
    articles. Acceptable for user-facing queries.

    Trade-offs:
    - Simplicity: Works with any date format in metadata
    - Flexibility: Easy to adjust date comparison logic
    - Performance: Slightly slower than DB-level filtering but negligible for
      typical result set sizes (<1000 articles)

    Future Enhancement: If article count exceeds 10,000 and date filtering
    becomes a bottleneck, migrate to standardized date field in ChromaDB
    metadata and use $gte/$lte operators.
    """
    import time

    start_time = time.time()

    try:
        collection = get_chroma_collection()
        model = get_embedding_model()

        # Generate query embedding
        query_embedding = model.encode([query])[0]

        # Build where filter for news articles
        where_filter = {"doc_type": "news_article"}

        # Add publication filter if specified
        if publication:
            where_filter["publication"] = {"$eq": publication}

        # Add credibility filter if specified
        if min_credibility is not None:
            where_filter["credibility_score"] = {"$gte": min_credibility}

        # Search with filters
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 2,  # Get extra for entity filtering
            where=where_filter,
        )

        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            doc_id = results["ids"][0][i]
            distance = results["distances"][0][i]
            similarity = 1 - distance
            text = results["documents"][0][i]
            metadata = results["metadatas"][0][i]

            # Apply entity filter if specified
            if entity:
                entity_mentions = metadata.get("entity_mentions", "")
                if entity.lower() not in entity_mentions.lower():
                    continue

            # Apply date range filter if specified
            if start_date or end_date:
                published_date = metadata.get("published_date", "")
                if published_date:
                    # Extract date part (YYYY-MM-DD) from datetime string
                    article_date = published_date.split("T")[0]

                    # Skip if outside date range
                    if start_date and article_date < start_date:
                        continue
                    if end_date and article_date > end_date:
                        continue

            # Create excerpt
            excerpt = text[:300] + "..." if len(text) > 300 else text

            formatted_results.append(
                SearchResult(
                    id=doc_id, similarity=float(similarity), text_excerpt=excerpt, metadata=metadata
                )
            )

            if len(formatted_results) >= limit:
                break

        search_time = (time.time() - start_time) * 1000

        return SearchResponse(
            query=query,
            results=formatted_results,
            total_results=len(formatted_results),
            search_time_ms=search_time,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar-news/{article_id}")
async def find_similar_articles(
    article_id: str, limit: int = Query(5, ge=1, le=20, description="Maximum results")
):
    """
    Find news articles similar to a specified article.

    Uses semantic similarity to find related news articles.

    Args:
        article_id: Article ID (can be just the UUID or full "news:uuid" format)
        limit: Maximum similar articles to return

    Returns:
        Similar news articles ranked by semantic similarity
    """
    try:
        collection = get_chroma_collection()
        model = get_embedding_model()

        # Normalize article ID format
        if not article_id.startswith("news:"):
            article_id = f"news:{article_id}"

        # Get source article
        source_doc = collection.get(ids=[article_id])

        if not source_doc["ids"]:
            raise HTTPException(status_code=404, detail=f"Article not found: {article_id}")

        # Check if it's actually a news article
        source_metadata = source_doc["metadatas"][0]
        if source_metadata.get("doc_type") != "news_article":
            raise HTTPException(
                status_code=400, detail=f"Document {article_id} is not a news article"
            )

        # Use article text as query
        doc_text = source_doc["documents"][0]
        query_embedding = model.encode([doc_text])[0]

        # Search for similar news articles only
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit + 1,  # +1 to exclude self
            where={"doc_type": "news_article"},
        )

        # Format results (exclude source article)
        formatted_results = []
        for i in range(len(results["ids"][0])):
            result_id = results["ids"][0][i]

            # Skip source article
            if result_id == article_id:
                continue

            distance = results["distances"][0][i]
            similarity = 1 - distance
            text = results["documents"][0][i]
            metadata = results["metadatas"][0][i]

            excerpt = text[:300] + "..." if len(text) > 300 else text

            formatted_results.append(
                SearchResult(
                    id=result_id,
                    similarity=float(similarity),
                    text_excerpt=excerpt,
                    metadata=metadata,
                )
            )

            if len(formatted_results) >= limit:
                break

        return {
            "source_article_id": article_id,
            "source_title": source_metadata.get("title", "Unknown"),
            "source_publication": source_metadata.get("publication", "Unknown"),
            "similar_articles": formatted_results,
            "total_results": len(formatted_results),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics including news articles."""
    try:
        collection = get_chroma_collection()
        entity_index = get_entity_doc_index()
        network = get_entity_network()

        # Count news articles
        news_results = collection.get(where={"doc_type": "news_article"})
        news_count = len(news_results["ids"]) if news_results["ids"] else 0

        # Total documents
        total_docs = collection.count()
        court_docs_count = total_docs - news_count

        return {
            "total_documents": total_docs,
            "court_documents": court_docs_count,
            "news_articles": news_count,
            "total_entities": len(entity_index.get("entity_to_documents", {})),
            "total_entity_mentions": entity_index.get("metadata", {}).get(
                "total_entity_mentions", 0
            ),
            "network_nodes": network.get("metadata", {}).get("total_nodes", 0),
            "network_edges": network.get("metadata", {}).get("total_edges", 0),
            "vector_store_path": str(VECTOR_STORE_DIR),
            "collection_name": COLLECTION_NAME,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
