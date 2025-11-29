#!/usr/bin/env python3
"""
RAG Query Interface
Epstein Document Archive - RAG System

Command-line interface for querying the vector store using semantic search,
entity filtering, and knowledge graph integration.

Usage:
    python3 scripts/rag/query_rag.py --query "Who visited Little St. James in 1998?"
    python3 scripts/rag/query_rag.py --entity "Clinton" --limit 10
    python3 scripts/rag/query_rag.py --semantic "financial transactions"
    python3 scripts/rag/query_rag.py --entities "Clinton" "Epstein" --limit 5
"""

import argparse
import json
import sys
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


class RAGQueryEngine:
    def __init__(self):
        """Initialize the RAG query engine."""
        # Load ChromaDB
        print("Loading ChromaDB collection...")
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR), settings=Settings(anonymized_telemetry=False)
        )

        try:
            self.collection = self.client.get_collection(name=COLLECTION_NAME)
            print(f"✅ Collection loaded: {self.collection.count()} documents")
        except:
            print("❌ Error: Collection not found. Run build_vector_store.py first.")
            sys.exit(1)

        # Load embedding model
        print("Loading embedding model...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Model loaded")

        # Load entity-document index
        self.entity_doc_index = self._load_entity_doc_index()

        # Load entity network
        self.entity_network = self._load_entity_network()

    def _load_entity_doc_index(self) -> dict:
        """Load entity-document index."""
        if ENTITY_DOC_INDEX_PATH.exists():
            with open(ENTITY_DOC_INDEX_PATH) as f:
                data = json.load(f)
                print(
                    f"✅ Entity index loaded: {data.get('metadata', {}).get('total_entities_mentioned', 0)} entities"
                )
                return data
        return {"entity_to_documents": {}}

    def _load_entity_network(self) -> dict:
        """Load entity network."""
        if ENTITY_NETWORK_PATH.exists():
            with open(ENTITY_NETWORK_PATH) as f:
                data = json.load(f)
                print(
                    f"✅ Entity network loaded: {data.get('metadata', {}).get('total_nodes', 0)} nodes"
                )
                return data
        return {"nodes": [], "edges": []}

    def semantic_search(
        self, query: str, limit: int = 10, entity_filter: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Perform semantic search across all documents.

        Args:
            query: Search query
            limit: Maximum number of results
            entity_filter: Optional list of entities to filter by

        Returns:
            List of matching documents with metadata
        """
        print(f"\n🔍 Semantic search: '{query}'")

        # Generate query embedding
        query_embedding = self.model.encode([query])[0]

        # Perform vector search
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit * 2,  # Get extra results for filtering
        )

        # Format results
        documents = []
        for i in range(len(results["ids"][0])):
            doc = {
                "id": results["ids"][0][i],
                "distance": results["distances"][0][i],
                "similarity": 1 - results["distances"][0][i],  # Convert distance to similarity
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
            }

            # Apply entity filter if specified
            if entity_filter:
                entity_mentions = doc["metadata"].get("entity_mentions", [])
                if not any(entity in entity_mentions for entity in entity_filter):
                    continue

            documents.append(doc)

            if len(documents) >= limit:
                break

        return documents

    def entity_search(self, entity_name: str, limit: int = 20) -> list[dict]:
        """
        Find documents mentioning a specific entity.

        Args:
            entity_name: Entity to search for
            limit: Maximum number of results

        Returns:
            List of documents mentioning the entity
        """
        print(f"\n👤 Entity search: '{entity_name}'")

        # Get documents from entity index
        entity_to_docs = self.entity_doc_index.get("entity_to_documents", {})

        # Try exact match first
        if entity_name in entity_to_docs:
            entity_data = entity_to_docs[entity_name]
            documents = entity_data["documents"][:limit]

            print(f"✅ Found {len(documents)} documents (total: {entity_data['document_count']})")
            return documents

        # Try fuzzy match
        matching_entities = [e for e in entity_to_docs if entity_name.lower() in e.lower()]

        if matching_entities:
            print(f"📝 Found similar entities: {', '.join(matching_entities[:5])}")
            entity_data = entity_to_docs[matching_entities[0]]
            documents = entity_data["documents"][:limit]
            return documents

        print(f"❌ No documents found for entity: {entity_name}")
        return []

    def multi_entity_search(self, entities: list[str], limit: int = 10) -> list[dict]:
        """
        Find documents mentioning ALL specified entities.

        Args:
            entities: List of entities
            limit: Maximum number of results

        Returns:
            List of documents mentioning all entities
        """
        print(f"\n👥 Multi-entity search: {', '.join(entities)}")

        entity_to_docs = self.entity_doc_index.get("entity_to_documents", {})

        # Get document sets for each entity
        doc_sets = []
        for entity in entities:
            if entity in entity_to_docs:
                doc_ids = {doc["doc_id"] for doc in entity_to_docs[entity]["documents"]}
                doc_sets.append(doc_ids)
            else:
                print(f"⚠️  Entity not found: {entity}")
                return []

        # Find intersection of all document sets
        if not doc_sets:
            return []

        common_docs = set.intersection(*doc_sets)
        print(f"✅ Found {len(common_docs)} documents mentioning all entities")

        # Get document details
        results = []
        for doc_id in list(common_docs)[:limit]:
            # Retrieve from ChromaDB
            try:
                doc_result = self.collection.get(ids=[doc_id])
                if doc_result["ids"]:
                    results.append(
                        {
                            "id": doc_result["ids"][0],
                            "text": doc_result["documents"][0],
                            "metadata": doc_result["metadatas"][0],
                        }
                    )
            except:
                pass

        return results

    def find_connections(self, entity_name: str, max_connections: int = 20) -> list[dict]:
        """
        Find entities connected to the specified entity via flight logs.

        Args:
            entity_name: Entity to find connections for
            max_connections: Maximum number of connections to return

        Returns:
            List of connected entities with relationship details
        """
        print(f"\n🔗 Finding connections for: '{entity_name}'")

        edges = self.entity_network.get("edges", [])

        # Find all edges involving this entity
        connections = []
        for edge in edges:
            if edge["source"] == entity_name:
                connections.append(
                    {
                        "entity": edge["target"],
                        "weight": edge["weight"],
                        "relationship": edge.get("relationship", "co-occurrence"),
                    }
                )
            elif edge["target"] == entity_name:
                connections.append(
                    {
                        "entity": edge["source"],
                        "weight": edge["weight"],
                        "relationship": edge.get("relationship", "co-occurrence"),
                    }
                )

        # Sort by weight (number of co-occurrences)
        connections.sort(key=lambda x: x["weight"], reverse=True)

        print(f"✅ Found {len(connections)} connections")
        return connections[:max_connections]

    def similar_documents(self, doc_id: str, limit: int = 5) -> list[dict]:
        """
        Find documents similar to the specified document.

        Args:
            doc_id: Document ID to find similar documents for
            limit: Maximum number of results

        Returns:
            List of similar documents
        """
        print(f"\n📄 Finding similar documents to: {doc_id}")

        # Get the source document
        try:
            source_doc = self.collection.get(ids=[doc_id])
            if not source_doc["ids"]:
                print(f"❌ Document not found: {doc_id}")
                return []

            # Use the document text as query
            doc_text = source_doc["documents"][0]
            return self.semantic_search(doc_text, limit=limit + 1)[1:]  # Exclude self

        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def _highlight_text(self, text: str, query: str, context_chars: int = 300) -> str:
        """Extract relevant excerpt from text with query highlighted."""
        # Find query terms in text
        query_terms = query.lower().split()

        best_position = 0
        best_score = 0

        # Find position with most query terms
        for i in range(len(text) - context_chars):
            excerpt = text[i : i + context_chars].lower()
            score = sum(1 for term in query_terms if term in excerpt)
            if score > best_score:
                best_score = score
                best_position = i

        # Extract excerpt
        start = max(0, best_position)
        end = min(len(text), best_position + context_chars)
        excerpt = text[start:end]

        # Add ellipsis
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."

        return excerpt


def main():
    parser = argparse.ArgumentParser(description="Query the Epstein document RAG system")

    # Search modes
    parser.add_argument("--query", type=str, help="Semantic search query")
    parser.add_argument("--entity", type=str, help="Search for documents mentioning entity")
    parser.add_argument(
        "--entities", type=str, nargs="+", help="Search for documents mentioning ALL entities"
    )
    parser.add_argument(
        "--connections", type=str, help="Find entities connected to specified entity"
    )
    parser.add_argument("--similar", type=str, help="Find documents similar to specified doc_id")

    # Parameters
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of results")
    parser.add_argument("--show-text", action="store_true", help="Show document text excerpts")

    args = parser.parse_args()

    # Initialize query engine
    engine = RAGQueryEngine()

    # Execute query
    results = []

    if args.query:
        results = engine.semantic_search(args.query, limit=args.limit)
    elif args.entity:
        results = engine.entity_search(args.entity, limit=args.limit)
    elif args.entities:
        results = engine.multi_entity_search(args.entities, limit=args.limit)
    elif args.connections:
        connections = engine.find_connections(args.connections, max_connections=args.limit)
        print("\n" + "=" * 70)
        print(f"CONNECTIONS FOR: {args.connections}")
        print("=" * 70)
        for i, conn in enumerate(connections, 1):
            print(f"{i:2d}. {conn['entity']:40s} - {conn['weight']:3d} co-occurrences")
        return
    elif args.similar:
        results = engine.similar_documents(args.similar, limit=args.limit)
    else:
        parser.print_help()
        return

    # Display results
    print("\n" + "=" * 70)
    print(f"RESULTS ({len(results)} documents)")
    print("=" * 70)

    for i, doc in enumerate(results, 1):
        print(f"\n[{i}] Document: {doc['id']}")

        if "similarity" in doc:
            print(f"    Similarity: {doc['similarity']:.4f}")

        metadata = doc.get("metadata", {})
        if metadata.get("date_extracted"):
            print(f"    Date: {metadata['date_extracted']}")

        entity_mentions = metadata.get("entity_mentions", [])
        if entity_mentions:
            print(f"    Entities: {', '.join(entity_mentions[:5])}")
            if len(entity_mentions) > 5:
                print(f"              ... and {len(entity_mentions) - 5} more")

        if args.show_text:
            text = doc.get("text", "")
            excerpt = engine._highlight_text(text, args.query or "", context_chars=300)
            print(f"\n    {excerpt}\n")

    print("=" * 70)


if __name__ == "__main__":
    main()
