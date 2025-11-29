#!/usr/bin/env python3
"""
Knowledge Graph + RAG Integration
Epstein Document Archive - Hybrid Search System

Combines vector similarity (ChromaDB), graph relationships (entity network),
and metadata filtering for advanced queries.

Usage:
    python3 scripts/rag/kg_rag_integration.py --query "financial transactions" --entity "Wexner"
    python3 scripts/rag/kg_rag_integration.py --connect "Clinton" "Epstein" --date-range "1995-2000"
    python3 scripts/rag/kg_rag_integration.py --path "Clinton" "Maxwell" --max-hops 2
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer


# Project paths
PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
VECTOR_STORE_DIR = PROJECT_ROOT / "data/vector_store/chroma"
ENTITY_DOC_INDEX_PATH = PROJECT_ROOT / "data/metadata/entity_document_index.json"
ENTITY_NETWORK_PATH = PROJECT_ROOT / "data/metadata/entity_network.json"

COLLECTION_NAME = "epstein_documents"


class KnowledgeGraphRAG:
    def __init__(self):
        """Initialize the hybrid KG + RAG system."""
        # Load ChromaDB
        print("Loading ChromaDB collection...")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR), settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_collection(name=COLLECTION_NAME)
        print(f"✅ Collection loaded: {self.collection.count()} documents")

        # Load embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded")

        # Load entity-document index
        with open(ENTITY_DOC_INDEX_PATH) as f:
            self.entity_doc_index = json.load(f)
            print("✅ Entity index loaded")

        # Load entity network
        with open(ENTITY_NETWORK_PATH) as f:
            self.entity_network = json.load(f)
            print("✅ Entity network loaded")

        # Build adjacency list for graph traversal
        self.adjacency_list = self._build_adjacency_list()

    def _build_adjacency_list(self) -> dict[str, list[tuple[str, int]]]:
        """Build adjacency list from entity network for graph traversal."""
        adj_list = defaultdict(list)

        for edge in self.entity_network.get("edges", []):
            source = edge["source"]
            target = edge["target"]
            weight = edge["weight"]

            adj_list[source].append((target, weight))
            adj_list[target].append((source, weight))

        return dict(adj_list)

    def find_path_between_entities(
        self, entity1: str, entity2: str, max_hops: int = 3
    ) -> Optional[list[str]]:
        """
        Find shortest path between two entities in the graph.

        Args:
            entity1: Starting entity
            entity2: Target entity
            max_hops: Maximum path length

        Returns:
            List of entities forming the path, or None if no path exists
        """
        if entity1 not in self.adjacency_list or entity2 not in self.adjacency_list:
            return None

        # BFS for shortest path
        queue = [(entity1, [entity1])]
        visited = {entity1}

        while queue:
            current, path = queue.pop(0)

            if len(path) - 1 >= max_hops:
                continue

            if current == entity2:
                return path

            for neighbor, _ in self.adjacency_list.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, [*path, neighbor]))

        return None

    def get_documents_connecting_entities(
        self, entities: list[str], semantic_query: Optional[str] = None, limit: int = 10
    ) -> list[dict]:
        """
        Find documents connecting multiple entities.

        Combines:
        - Entity co-occurrence (from entity-document index)
        - Semantic similarity (if query provided)
        - Graph relationships (entity network)

        Args:
            entities: List of entities to connect
            semantic_query: Optional semantic query for ranking
            limit: Maximum results

        Returns:
            List of documents ranked by relevance
        """
        print(f"\n🔗 Finding documents connecting: {', '.join(entities)}")

        entity_to_docs = self.entity_doc_index.get("entity_to_documents", {})

        # Get documents for each entity
        doc_sets = []
        for entity in entities:
            if entity in entity_to_docs:
                doc_ids = {doc["doc_id"] for doc in entity_to_docs[entity]["documents"]}
                doc_sets.append(doc_ids)
            else:
                print(f"⚠️  Entity not found: {entity}")
                return []

        # Find intersection (documents mentioning ALL entities)
        common_docs = set.intersection(*doc_sets)
        print(f"✅ Found {len(common_docs)} documents mentioning all entities")

        if not common_docs:
            return []

        # If semantic query provided, rank by similarity
        if semantic_query:
            return self._rank_by_semantic_similarity(list(common_docs), semantic_query, limit)

        # Otherwise, rank by total entity mentions
        return self._rank_by_entity_mentions(list(common_docs), entities, entity_to_docs, limit)

    def _rank_by_semantic_similarity(
        self, doc_ids: list[str], query: str, limit: int
    ) -> list[dict]:
        """Rank documents by semantic similarity to query."""
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]

        # Get documents from ChromaDB
        results = []
        for doc_id in doc_ids:
            doc = self.collection.get(ids=[doc_id])
            if doc["ids"]:
                # Calculate similarity
                doc_text = doc["documents"][0]
                doc_embedding = self.model.encode([doc_text])[0]

                # Cosine similarity
                similarity = float(
                    sum(a * b for a, b in zip(query_embedding, doc_embedding))
                    / (
                        sum(a**2 for a in query_embedding) ** 0.5
                        * sum(b**2 for b in doc_embedding) ** 0.5
                    )
                )

                results.append(
                    {
                        "id": doc_id,
                        "similarity": similarity,
                        "text": doc_text,
                        "metadata": doc["metadatas"][0],
                    }
                )

        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def _rank_by_entity_mentions(
        self, doc_ids: list[str], entities: list[str], entity_to_docs: dict, limit: int
    ) -> list[dict]:
        """Rank documents by total entity mention count."""
        doc_scores = defaultdict(int)

        # Calculate total mentions for each document
        for entity in entities:
            entity_data = entity_to_docs.get(entity, {})
            for doc in entity_data.get("documents", []):
                if doc["doc_id"] in doc_ids:
                    doc_scores[doc["doc_id"]] += doc["mentions"]

        # Get top documents
        top_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        # Retrieve from ChromaDB
        results = []
        for doc_id, score in top_docs:
            doc = self.collection.get(ids=[doc_id])
            if doc["ids"]:
                results.append(
                    {
                        "id": doc_id,
                        "mention_score": score,
                        "text": doc["documents"][0],
                        "metadata": doc["metadatas"][0],
                    }
                )

        return results

    def temporal_entity_query(
        self,
        entity: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """
        Find documents mentioning entity within a date range.

        Args:
            entity: Entity name
            start_date: Start date (YYYY-MM-DD or YYYY)
            end_date: End date (YYYY-MM-DD or YYYY)
            limit: Maximum results

        Returns:
            List of documents within date range
        """
        print(f"\n📅 Temporal query: {entity} ({start_date} to {end_date})")

        entity_to_docs = self.entity_doc_index.get("entity_to_documents", {})

        if entity not in entity_to_docs:
            print(f"❌ Entity not found: {entity}")
            return []

        entity_data = entity_to_docs[entity]
        results = []

        for doc_info in entity_data["documents"]:
            doc_id = doc_info["doc_id"]

            # Get document metadata
            doc = self.collection.get(ids=[doc_id])
            if not doc["ids"]:
                continue

            metadata = doc["metadatas"][0]
            doc_date = metadata.get("date_extracted")

            # Filter by date range
            if doc_date:
                if start_date and doc_date < start_date:
                    continue
                if end_date and doc_date > end_date:
                    continue

                results.append(
                    {
                        "id": doc_id,
                        "date": doc_date,
                        "mentions": doc_info["mentions"],
                        "text": doc["documents"][0],
                        "metadata": metadata,
                    }
                )

        # Sort by date
        results.sort(key=lambda x: x["date"] or "")
        print(f"✅ Found {len(results)} documents in date range")

        return results[:limit]

    def graph_enhanced_search(
        self,
        semantic_query: str,
        required_entities: Optional[list[str]] = None,
        connection_weight_threshold: int = 5,
        limit: int = 10,
    ) -> list[dict]:
        """
        Hybrid search combining semantic similarity and graph structure.

        Args:
            semantic_query: Text query for semantic search
            required_entities: Optional entities that must be mentioned
            connection_weight_threshold: Minimum connection weight for entity pairs
            limit: Maximum results

        Returns:
            Documents ranked by hybrid score (semantic + graph)
        """
        print(f"\n🧠 Graph-enhanced search: '{semantic_query}'")

        # Perform semantic search
        query_embedding = self.model.encode([semantic_query])[0]
        semantic_results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 3,  # Get extra for filtering
        )

        # Score documents
        scored_docs = []

        for i in range(len(semantic_results["ids"][0])):
            doc_id = semantic_results["ids"][0][i]
            distance = semantic_results["distances"][0][i]
            semantic_score = 1 - distance
            metadata = semantic_results["metadatas"][0][i]
            entity_mentions = metadata.get("entity_mentions", [])

            # Filter by required entities
            if required_entities:
                if not all(e in entity_mentions for e in required_entities):
                    continue

            # Calculate graph score (based on entity connections)
            graph_score = 0
            for i, entity1 in enumerate(entity_mentions):
                for entity2 in entity_mentions[i + 1 :]:
                    # Check if entities are connected in graph
                    for neighbor, weight in self.adjacency_list.get(entity1, []):
                        if neighbor == entity2 and weight >= connection_weight_threshold:
                            graph_score += weight

            # Hybrid score: 70% semantic, 30% graph
            hybrid_score = 0.7 * semantic_score + 0.3 * min(graph_score / 100, 1.0)

            scored_docs.append(
                {
                    "id": doc_id,
                    "semantic_score": float(semantic_score),
                    "graph_score": graph_score,
                    "hybrid_score": float(hybrid_score),
                    "text": semantic_results["documents"][0][i],
                    "metadata": metadata,
                }
            )

        # Sort by hybrid score
        scored_docs.sort(key=lambda x: x["hybrid_score"], reverse=True)

        print(f"✅ Found {len(scored_docs)} results")
        return scored_docs[:limit]


def main():
    parser = argparse.ArgumentParser(description="Knowledge Graph + RAG Integration")

    # Query modes
    parser.add_argument("--query", type=str, help="Semantic search query")
    parser.add_argument("--connect", type=str, nargs="+", help="Find documents connecting entities")
    parser.add_argument("--path", type=str, nargs=2, help="Find path between two entities")
    parser.add_argument("--temporal", type=str, help="Entity for temporal query")

    # Filters
    parser.add_argument("--entity", type=str, help="Filter by entity")
    parser.add_argument("--date-range", type=str, nargs=2, help="Date range: START END")
    parser.add_argument("--max-hops", type=int, default=3, help="Maximum hops for path finding")
    parser.add_argument("--weight-threshold", type=int, default=5, help="Minimum connection weight")

    # Parameters
    parser.add_argument("--limit", type=int, default=10, help="Maximum results")

    args = parser.parse_args()

    # Initialize system
    kg_rag = KnowledgeGraphRAG()

    # Execute query
    results = []

    if args.path:
        # Find path between entities
        entity1, entity2 = args.path
        path = kg_rag.find_path_between_entities(entity1, entity2, args.max_hops)

        print("\n" + "=" * 70)
        print(f"PATH: {entity1} → {entity2}")
        print("=" * 70)

        if path:
            print(" → ".join(path))
            print(f"\nPath length: {len(path) - 1} hops")
        else:
            print(f"No path found within {args.max_hops} hops")

        return

    if args.connect:
        # Connect multiple entities
        results = kg_rag.get_documents_connecting_entities(
            args.connect, semantic_query=args.query, limit=args.limit
        )

    elif args.temporal:
        # Temporal query
        start_date, end_date = None, None
        if args.date_range:
            start_date, end_date = args.date_range

        results = kg_rag.temporal_entity_query(args.temporal, start_date, end_date, args.limit)

    elif args.query:
        # Hybrid search
        required_entities = [args.entity] if args.entity else None
        results = kg_rag.graph_enhanced_search(
            args.query,
            required_entities=required_entities,
            connection_weight_threshold=args.weight_threshold,
            limit=args.limit,
        )

    else:
        parser.print_help()
        return

    # Display results
    print("\n" + "=" * 70)
    print(f"RESULTS ({len(results)} documents)")
    print("=" * 70)

    for i, doc in enumerate(results, 1):
        print(f"\n[{i}] Document: {doc['id']}")

        if "hybrid_score" in doc:
            print(f"    Hybrid Score: {doc['hybrid_score']:.4f}")
            print(f"    - Semantic: {doc['semantic_score']:.4f}")
            print(f"    - Graph: {doc['graph_score']}")
        elif "similarity" in doc:
            print(f"    Similarity: {doc['similarity']:.4f}")
        elif "mention_score" in doc:
            print(f"    Mention Score: {doc['mention_score']}")

        metadata = doc.get("metadata", {})
        if metadata.get("date_extracted"):
            print(f"    Date: {metadata['date_extracted']}")

        entity_mentions = metadata.get("entity_mentions", [])
        if entity_mentions:
            print(f"    Entities: {', '.join(entity_mentions[:5])}")

        # Show excerpt
        text = doc.get("text", "")
        excerpt = text[:300] + "..." if len(text) > 300 else text
        print(f"\n    {excerpt}\n")

    print("=" * 70)


if __name__ == "__main__":
    main()
