#!/usr/bin/env python3
"""
Entity Similarity Service

Provides semantic similarity search for entities using ChromaDB vector store.
Enables discovery of related entities based on biography text similarity.
"""

import logging
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# CRITICAL: Disable ChromaDB telemetry BEFORE importing chromadb
# ChromaDB 1.3.5 has a bug where telemetry tries to access non-existent schema columns
# causing "no such column: collections.topic" error during initialization.
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "none"

try:
    import chromadb
except ImportError:
    chromadb = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


logger = logging.getLogger(__name__)


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store" / "chroma"
COLLECTION_NAME = "epstein_documents"


class EntitySimilarityService:
    """Service for finding similar entities using vector embeddings."""

    _instance = None

    def __new__(cls):
        """Singleton pattern to reuse ChromaDB connection and model."""
        if cls._instance is None:
            cls._instance = super(EntitySimilarityService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the similarity service."""
        if self._initialized:
            return

        # Check dependencies
        if chromadb is None:
            raise ImportError("chromadb not installed. Run: pip3 install chromadb")
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers not installed. Run: pip3 install sentence-transformers")

        logger.info(f"Initializing EntitySimilarityService with vector store at {VECTOR_STORE_DIR}")

        # Initialize ChromaDB (telemetry disabled at module level)
        try:
            logger.info("Creating ChromaDB client...")
            self.client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
            logger.info("ChromaDB client created successfully")

            logger.info(f"Getting collection '{COLLECTION_NAME}'...")
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            logger.info(f"✓ Connected to ChromaDB collection '{COLLECTION_NAME}'")
        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Initialize embedding model
        try:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("✓ Sentence transformer model loaded")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise

        self._initialized = True

    def find_similar_entities(
        self,
        entity_name: str,
        limit: int = 10,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """Find entities similar to the given entity.

        Args:
            entity_name: Entity identifier (e.g., "jeffrey_epstein")
            limit: Maximum number of similar entities to return
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            List of similar entity dictionaries with metadata

        Raises:
            ValueError: If entity not found in vector store
        """
        doc_id = f"entity_bio_{entity_name}"

        try:
            # Get target entity embedding
            target_entity = self.collection.get(
                ids=[doc_id],
                include=["embeddings", "metadatas", "documents"]
            )

            if not target_entity["ids"]:
                raise ValueError(f"Entity '{entity_name}' not found in vector store")

            target_embedding = target_entity["embeddings"][0]
            target_metadata = target_entity["metadatas"][0]

            # Query for similar entities
            results = self.collection.query(
                query_embeddings=[target_embedding],
                n_results=limit + 1,  # +1 because first result is the entity itself
                where={"doc_type": "entity_biography"},
                include=["distances", "metadatas", "documents"]
            )

            if not results["ids"]:
                return []

            # Parse results and calculate similarity scores
            similar_entities = []
            for idx, (result_id, distance, metadata, doc) in enumerate(zip(
                results["ids"][0],
                results["distances"][0],
                results["metadatas"][0],
                results["documents"][0]
            )):
                # Skip the entity itself
                if result_id == doc_id:
                    continue

                # Convert L2 distance to similarity score (0-1 range)
                similarity_score = 1.0 / (1.0 + distance)

                # Apply minimum similarity filter
                if similarity_score < min_similarity:
                    continue

                entity_id = result_id.replace("entity_bio_", "")

                similar_entities.append({
                    "entity_id": entity_id,
                    "display_name": metadata.get("display_name", entity_id),
                    "similarity_score": round(similarity_score, 4),
                    "primary_category": metadata.get("primary_category"),
                    "quality_score": metadata.get("quality_score", 0.0),
                    "word_count": metadata.get("word_count", 0),
                    "biography_excerpt": doc[:200] if doc else None
                })

                if len(similar_entities) >= limit:
                    break

            return similar_entities

        except Exception as e:
            logger.error(f"Error finding similar entities for '{entity_name}': {e}")
            raise

    def cluster_by_category(
        self,
        entity_name: str,
        limit: int = 20
    ) -> Dict[str, List[Dict]]:
        """Find similar entities and group by category.

        Args:
            entity_name: Entity identifier
            limit: Maximum number of similar entities to retrieve

        Returns:
            Dictionary mapping category names to lists of similar entities
        """
        similar_entities = self.find_similar_entities(entity_name, limit)

        # Group by primary category
        by_category = {}
        for entity in similar_entities:
            category = entity.get("primary_category", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(entity)

        return by_category

    def search_by_text(
        self,
        query_text: str,
        limit: int = 10,
        category_filter: Optional[str] = None
    ) -> List[Dict]:
        """Search entities by text query.

        Args:
            query_text: Free text search query
            limit: Maximum number of results
            category_filter: Optional category to filter results

        Returns:
            List of matching entities with similarity scores
        """
        try:
            # Generate embedding for query text
            query_embedding = self.model.encode(query_text).tolist()

            # Build where clause
            where_clause = {"doc_type": "entity_biography"}
            if category_filter:
                where_clause["primary_category"] = category_filter

            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_clause,
                include=["distances", "metadatas", "documents"]
            )

            if not results["ids"]:
                return []

            # Parse results
            matching_entities = []
            for result_id, distance, metadata, doc in zip(
                results["ids"][0],
                results["distances"][0],
                results["metadatas"][0],
                results["documents"][0]
            ):
                similarity_score = 1.0 / (1.0 + distance)
                entity_id = result_id.replace("entity_bio_", "")

                matching_entities.append({
                    "entity_id": entity_id,
                    "display_name": metadata.get("display_name", entity_id),
                    "similarity_score": round(similarity_score, 4),
                    "primary_category": metadata.get("primary_category"),
                    "quality_score": metadata.get("quality_score", 0.0),
                    "biography_excerpt": doc[:200] if doc else None
                })

            return matching_entities

        except Exception as e:
            logger.error(f"Error searching entities by text: {e}")
            raise


# Singleton instance getter
_service_instance = None

def get_entity_similarity_service() -> EntitySimilarityService:
    """Get or create the entity similarity service instance.

    Returns:
        EntitySimilarityService singleton instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = EntitySimilarityService()
    return _service_instance
