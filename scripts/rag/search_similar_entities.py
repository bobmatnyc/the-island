#!/usr/bin/env python3
"""
Semantic Entity Similarity Search

Find entities similar to a given entity based on biography text similarity.
Uses ChromaDB vector store with entity biography embeddings.

Usage:
    python3 scripts/rag/search_similar_entities.py <entity_name> [--limit N]

Examples:
    python3 scripts/rag/search_similar_entities.py "jeffrey_epstein" --limit 10
    python3 scripts/rag/search_similar_entities.py "ghislaine_maxwell" --limit 5
"""

import argparse
import sys
from pathlib import Path
from typing import List, Dict, Tuple

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("Error: chromadb not installed. Run: pip3 install chromadb")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Error: sentence-transformers not installed. Run: pip3 install sentence-transformers")
    sys.exit(1)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store" / "chroma"

# ChromaDB configuration
COLLECTION_NAME = "epstein_documents"


class EntitySimilaritySearch:
    """Search for similar entities using vector embeddings."""

    def __init__(self):
        """Initialize the similarity search."""
        print(f"Connecting to ChromaDB at {VECTOR_STORE_DIR}")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR),
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )

        # Get collection
        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            print(f"✓ Connected to collection '{COLLECTION_NAME}'")
        except Exception as e:
            print(f"Error: Could not get collection '{COLLECTION_NAME}': {e}")
            sys.exit(1)

        # Initialize embedding model
        print("Loading sentence transformer model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✓ Model loaded\n")

    def find_similar_entities(
        self, entity_name: str, limit: int = 10
    ) -> List[Tuple[str, float, Dict]]:
        """Find entities similar to the given entity.

        Args:
            entity_name: Entity identifier (e.g., "jeffrey_epstein")
            limit: Maximum number of similar entities to return

        Returns:
            List of tuples (entity_name, similarity_score, metadata)
        """
        # First, get the target entity from ChromaDB
        doc_id = f"entity_bio_{entity_name}"

        try:
            target_entity = self.collection.get(
                ids=[doc_id],
                include=["embeddings", "metadatas", "documents"]
            )

            if not target_entity["ids"]:
                print(f"Error: Entity '{entity_name}' not found in vector store")
                print(f"Tried ID: {doc_id}")
                return []

            # Get the embedding for the target entity
            target_embedding = target_entity["embeddings"][0]
            target_metadata = target_entity["metadatas"][0]
            target_doc = target_entity["documents"][0]

            print(f"Target Entity: {target_metadata.get('display_name', entity_name)}")
            print(f"Primary Category: {target_metadata.get('primary_category', 'unknown')}")
            print(f"Quality Score: {target_metadata.get('quality_score', 0.0)}")
            print(f"\nBiography excerpt:")
            print(target_doc[:200] + "...\n")
            print("=" * 60)

        except Exception as e:
            print(f"Error retrieving entity '{entity_name}': {e}")
            return []

        # Query for similar entities
        try:
            results = self.collection.query(
                query_embeddings=[target_embedding],
                n_results=limit + 1,  # +1 because first result will be the entity itself
                where={"doc_type": "entity_biography"},
                include=["distances", "metadatas", "documents"]
            )

            if not results["ids"]:
                print("No similar entities found")
                return []

            # Parse results (skip first result if it's the entity itself)
            similar_entities = []
            for idx, (doc_id, distance, metadata, doc) in enumerate(zip(
                results["ids"][0],
                results["distances"][0],
                results["metadatas"][0],
                results["documents"][0]
            )):
                # Skip the entity itself
                if doc_id == f"entity_bio_{entity_name}":
                    continue

                # Convert distance to similarity score (0-1 range, higher is more similar)
                # ChromaDB uses L2 distance, smaller distance = more similar
                similarity_score = 1.0 / (1.0 + distance)

                entity_name_from_id = doc_id.replace("entity_bio_", "")
                similar_entities.append((entity_name_from_id, similarity_score, metadata, doc))

                if len(similar_entities) >= limit:
                    break

            return similar_entities

        except Exception as e:
            print(f"Error querying similar entities: {e}")
            import traceback
            traceback.print_exc()
            return []

    def print_results(self, similar_entities: List[Tuple[str, float, Dict, str]]):
        """Print search results in a readable format.

        Args:
            similar_entities: List of (entity_name, similarity_score, metadata, doc)
        """
        if not similar_entities:
            print("No similar entities found")
            return

        print(f"\nFound {len(similar_entities)} similar entities:\n")

        for idx, (entity_name, similarity, metadata, doc) in enumerate(similar_entities, 1):
            print(f"{idx}. {metadata.get('display_name', entity_name)}")
            print(f"   Similarity: {similarity:.4f}")
            print(f"   Category: {metadata.get('primary_category', 'unknown')}")
            print(f"   Quality: {metadata.get('quality_score', 0.0):.2f}")

            # Show biography excerpt
            excerpt = doc[:150].replace("\n", " ")
            print(f"   Bio: {excerpt}...")
            print()

    def cluster_by_category(self, entity_name: str, limit: int = 20):
        """Find similar entities and group by category.

        Args:
            entity_name: Entity identifier
            limit: Maximum number of similar entities to retrieve
        """
        similar_entities = self.find_similar_entities(entity_name, limit)

        if not similar_entities:
            return

        # Group by category
        by_category = {}
        for entity_name, similarity, metadata, doc in similar_entities:
            category = metadata.get("primary_category", "unknown")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((entity_name, similarity, metadata))

        # Print by category
        print("\nSimilar Entities Grouped by Category:")
        print("=" * 60)

        for category, entities in sorted(by_category.items()):
            print(f"\n{category.upper()} ({len(entities)} entities):")
            for entity_name, similarity, metadata in entities[:5]:  # Top 5 per category
                print(f"  • {metadata.get('display_name', entity_name)} (similarity: {similarity:.4f})")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Find entities similar to a given entity based on biography text"
    )
    parser.add_argument(
        "entity_name",
        help="Entity identifier (e.g., jeffrey_epstein, ghislaine_maxwell)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of similar entities to return (default: 10)",
    )
    parser.add_argument(
        "--cluster",
        action="store_true",
        help="Group results by relationship category",
    )

    args = parser.parse_args()

    # Create search instance
    search = EntitySimilaritySearch()

    # Execute search
    if args.cluster:
        search.cluster_by_category(args.entity_name, args.limit)
    else:
        similar_entities = search.find_similar_entities(args.entity_name, args.limit)
        search.print_results(similar_entities)


if __name__ == "__main__":
    main()
