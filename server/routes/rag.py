#!/usr/bin/env python3
"""
RAG API Routes
Epstein Document Archive - Vector Search & RAG Endpoints

Provides semantic search, entity-based retrieval, and knowledge graph integration.
"""

import json
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import chromadb
from chromadb.config import Settings
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
            path=str(VECTOR_STORE_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        try:
            _collection = _chroma_client.get_collection(name=COLLECTION_NAME)
        except:
            raise HTTPException(
                status_code=503,
                detail="Vector store not initialized. Run build_vector_store.py first."
            )

    return _collection


def get_embedding_model():
    """Get embedding model (lazy loading)."""
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    return _embedding_model


def get_entity_doc_index():
    """Get entity-document index (lazy loading)."""
    global _entity_doc_index

    if _entity_doc_index is None:
        if ENTITY_DOC_INDEX_PATH.exists():
            with open(ENTITY_DOC_INDEX_PATH, 'r') as f:
                _entity_doc_index = json.load(f)
        else:
            _entity_doc_index = {"entity_to_documents": {}}

    return _entity_doc_index


def get_entity_network():
    """Get entity network (lazy loading)."""
    global _entity_network

    if _entity_network is None:
        if ENTITY_NETWORK_PATH.exists():
            with open(ENTITY_NETWORK_PATH, 'r') as f:
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
    results: List[SearchResult]
    total_results: int
    search_time_ms: float


class EntitySearchResponse(BaseModel):
    entity: str
    documents: List[EntityDocumentResult]
    total_documents: int
    total_mentions: int


class ConnectionsResponse(BaseModel):
    entity: str
    connections: List[EntityConnection]
    total_connections: int


# API Endpoints

@router.get("/search", response_model=SearchResponse)
async def semantic_search(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=100, description="Maximum results"),
    entity_filter: Optional[str] = Query(None, description="Filter by entity name")
):
    """
    Perform semantic search across all documents.

    Returns documents ranked by similarity to the query.
    Optionally filter by entity mentions.
    """
    import time
    start_time = time.time()

    try:
        # Get collection and model
        collection = get_chroma_collection()
        model = get_embedding_model()

        # Generate query embedding
        query_embedding = model.encode([query])[0]

        # Search
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 2  # Get extra for filtering
        )

        # Format results
        formatted_results = []
        for i in range(len(results['ids'][0])):
            doc_id = results['ids'][0][i]
            distance = results['distances'][0][i]
            similarity = 1 - distance
            text = results['documents'][0][i]
            metadata = results['metadatas'][0][i]

            # Apply entity filter
            if entity_filter:
                entity_mentions = metadata.get('entity_mentions', [])
                if entity_filter not in entity_mentions:
                    continue

            # Create excerpt (first 300 chars)
            excerpt = text[:300] + "..." if len(text) > 300 else text

            formatted_results.append(SearchResult(
                id=doc_id,
                similarity=float(similarity),
                text_excerpt=excerpt,
                metadata=metadata
            ))

            if len(formatted_results) >= limit:
                break

        search_time = (time.time() - start_time) * 1000

        return SearchResponse(
            query=query,
            results=formatted_results,
            total_results=len(formatted_results),
            search_time_ms=search_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entity/{entity_name}", response_model=EntitySearchResponse)
async def get_entity_documents(
    entity_name: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum results")
):
    """
    Get documents mentioning a specific entity.

    Returns documents ranked by number of entity mentions.
    """
    try:
        entity_index = get_entity_doc_index()
        entity_to_docs = entity_index.get('entity_to_documents', {})

        # Try exact match first
        if entity_name in entity_to_docs:
            entity_data = entity_to_docs[entity_name]
        else:
            # Try fuzzy match
            matching = [
                e for e in entity_to_docs.keys()
                if entity_name.lower() in e.lower()
            ]

            if not matching:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entity not found: {entity_name}"
                )

            entity_data = entity_to_docs[matching[0]]

        # Format documents
        documents = [
            EntityDocumentResult(
                doc_id=doc['doc_id'],
                filename=doc['filename'],
                mentions=doc['mentions']
            )
            for doc in entity_data['documents'][:limit]
        ]

        return EntitySearchResponse(
            entity=entity_name,
            documents=documents,
            total_documents=entity_data['document_count'],
            total_mentions=entity_data['mention_count']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/similar/{doc_id}")
async def get_similar_documents(
    doc_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum results")
):
    """
    Find documents similar to the specified document.

    Uses the document's content as the query for semantic search.
    """
    try:
        collection = get_chroma_collection()

        # Get source document
        source_doc = collection.get(ids=[doc_id])

        if not source_doc['ids']:
            raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")

        # Use document text as query
        doc_text = source_doc['documents'][0]
        model = get_embedding_model()

        # Generate embedding
        query_embedding = model.encode([doc_text])[0]

        # Search for similar documents
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit + 1  # +1 to exclude self
        )

        # Format results (exclude source document)
        formatted_results = []
        for i in range(len(results['ids'][0])):
            result_id = results['ids'][0][i]

            # Skip source document
            if result_id == doc_id:
                continue

            distance = results['distances'][0][i]
            similarity = 1 - distance
            text = results['documents'][0][i]
            metadata = results['metadatas'][0][i]

            excerpt = text[:300] + "..." if len(text) > 300 else text

            formatted_results.append(SearchResult(
                id=result_id,
                similarity=float(similarity),
                text_excerpt=excerpt,
                metadata=metadata
            ))

            if len(formatted_results) >= limit:
                break

        return {
            "source_doc_id": doc_id,
            "similar_documents": formatted_results,
            "total_results": len(formatted_results)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/connections/{entity_name}", response_model=ConnectionsResponse)
async def get_entity_connections(
    entity_name: str,
    limit: int = Query(20, ge=1, le=100, description="Maximum connections")
):
    """
    Find entities connected to the specified entity via flight logs.

    Returns entities ranked by number of co-occurrences (flights together).
    """
    try:
        network = get_entity_network()
        edges = network.get('edges', [])

        # Find all edges involving this entity
        connections = []
        for edge in edges:
            if edge['source'] == entity_name:
                connections.append(EntityConnection(
                    entity=edge['target'],
                    weight=edge['weight'],
                    relationship=edge.get('relationship', 'co-occurrence')
                ))
            elif edge['target'] == entity_name:
                connections.append(EntityConnection(
                    entity=edge['source'],
                    weight=edge['weight'],
                    relationship=edge.get('relationship', 'co-occurrence')
                ))

        # Sort by weight
        connections.sort(key=lambda x: x.weight, reverse=True)

        return ConnectionsResponse(
            entity=entity_name,
            connections=connections[:limit],
            total_connections=len(connections)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-entity")
async def multi_entity_search(
    entities: str = Query(..., description="Comma-separated entity names"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results")
):
    """
    Find documents mentioning ALL specified entities.

    Entities should be comma-separated: "Clinton,Epstein,Maxwell"
    """
    try:
        entity_list = [e.strip() for e in entities.split(',')]

        if len(entity_list) < 2:
            raise HTTPException(
                status_code=400,
                detail="Provide at least 2 entities separated by commas"
            )

        entity_index = get_entity_doc_index()
        entity_to_docs = entity_index.get('entity_to_documents', {})

        # Get document sets for each entity
        doc_sets = []
        for entity in entity_list:
            if entity in entity_to_docs:
                doc_ids = {doc['doc_id'] for doc in entity_to_docs[entity]['documents']}
                doc_sets.append(doc_ids)
            else:
                raise HTTPException(
                    status_code=404,
                    detail=f"Entity not found: {entity}"
                )

        # Find intersection
        common_docs = set.intersection(*doc_sets)

        # Get document details from ChromaDB
        collection = get_chroma_collection()
        results = []

        for doc_id in list(common_docs)[:limit]:
            doc_result = collection.get(ids=[doc_id])
            if doc_result['ids']:
                text = doc_result['documents'][0]
                metadata = doc_result['metadatas'][0]
                excerpt = text[:300] + "..." if len(text) > 300 else text

                results.append({
                    "id": doc_id,
                    "text_excerpt": excerpt,
                    "metadata": metadata
                })

        return {
            "entities": entity_list,
            "documents": results,
            "total_results": len(common_docs)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics."""
    try:
        collection = get_chroma_collection()
        entity_index = get_entity_doc_index()
        network = get_entity_network()

        return {
            "total_documents": collection.count(),
            "total_entities": len(entity_index.get('entity_to_documents', {})),
            "total_entity_mentions": entity_index.get('metadata', {}).get('total_entity_mentions', 0),
            "network_nodes": network.get('metadata', {}).get('total_nodes', 0),
            "network_edges": network.get('metadata', {}).get('total_edges', 0),
            "vector_store_path": str(VECTOR_STORE_DIR),
            "collection_name": COLLECTION_NAME
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
