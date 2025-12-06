#!/usr/bin/env python3
"""
ChromaDB Entity Query Script

Query entities in the Epstein archive using semantic search.

Usage:
    # Search for entities by description
    python scripts/chromadb/query_entities.py "financiers and business associates"

    # Filter by entity type
    python scripts/chromadb/query_entities.py "islands" --type location

    # Find entities with biographies
    python scripts/chromadb/query_entities.py "accusers" --has-biography

    # Adjust result count
    python scripts/chromadb/query_entities.py "lawyers" --limit 20
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import CHROMADB_DIR, EMBEDDING_MODEL

# Entity-specific configuration
ENTITY_COLLECTION_NAME = "epstein_entities"


class EntityQueryClient:
    """Query entities from ChromaDB using semantic search."""

    def __init__(self):
        """Initialize ChromaDB client and connect to entity collection."""
        self.client = chromadb.PersistentClient(
            path=str(CHROMADB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        try:
            self.collection = self.client.get_collection(name=ENTITY_COLLECTION_NAME)
            print(f"Connected to collection: {ENTITY_COLLECTION_NAME}")
            print(f"Total entities: {self.collection.count()}")
        except Exception as e:
            print(f"Error: Collection '{ENTITY_COLLECTION_NAME}' not found.")
            print(
                "Please run 'python scripts/chromadb/index_entities.py' first to create the collection."
            )
            sys.exit(1)

    def query(
        self,
        query_text: str,
        limit: int = 10,
        entity_type: Optional[str] = None,
        has_biography: Optional[bool] = None,
        min_document_count: Optional[int] = None,
        classification: Optional[str] = None,
    ) -> Dict:
        """Query entities using semantic search.

        Args:
            query_text: Natural language query
            limit: Maximum number of results
            entity_type: Filter by type (person, location, organization)
            has_biography: Filter for entities with biographies
            min_document_count: Minimum number of documents entity appears in
            classification: Filter by classification label (partial match)

        Returns:
            Query results dictionary
        """
        # Build where filter
        where_conditions = []
        if entity_type:
            where_conditions.append({"entity_type": entity_type})
        if has_biography is not None:
            where_conditions.append({"has_biography": has_biography})

        # ChromaDB requires $and for multiple conditions
        where_filter = None
        if len(where_conditions) == 1:
            where_filter = where_conditions[0]
        elif len(where_conditions) > 1:
            where_filter = {"$and": where_conditions}

        # Build where_document filter (for classification text search)
        where_document_filter = None
        if classification:
            where_document_filter = {"$contains": classification}

        # Perform query
        results = self.collection.query(
            query_texts=[query_text],
            n_results=limit,
            where=where_filter if where_filter else None,
            where_document=where_document_filter,
        )

        # Post-filter by document count if needed
        if min_document_count is not None:
            filtered_results = {
                "ids": [[]],
                "distances": [[]],
                "metadatas": [[]],
                "documents": [[]],
            }
            for i, metadata in enumerate(results["metadatas"][0]):
                if metadata.get("document_count", 0) >= min_document_count:
                    filtered_results["ids"][0].append(results["ids"][0][i])
                    filtered_results["distances"][0].append(results["distances"][0][i])
                    filtered_results["metadatas"][0].append(results["metadatas"][0][i])
                    filtered_results["documents"][0].append(results["documents"][0][i])
            results = filtered_results

        return results

    def print_results(self, results: Dict, show_full_text: bool = False):
        """Pretty-print query results.

        Args:
            results: Query results from ChromaDB
            show_full_text: If True, show full entity text, else truncate
        """
        if not results["ids"][0]:
            print("\nNo results found.")
            return

        print(f"\nFound {len(results['ids'][0])} results:")
        print("=" * 80)

        for i, entity_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            document = results["documents"][0][i]
            distance = results["distances"][0][i]

            # Calculate similarity score (1 - distance for L2 distance)
            similarity = max(0, 1 - distance)

            print(f"\n{i+1}. {metadata['canonical_name']} ({metadata['entity_type']})")
            print(f"   ID: {entity_id}")
            print(f"   Similarity: {similarity:.3f}")
            print(f"   Documents: {metadata['document_count']}")
            print(f"   Connections: {metadata['connection_count']}")

            if metadata.get("classifications"):
                print(f"   Classifications: {metadata['classifications']}")

            if metadata.get("has_biography"):
                print(f"   ✓ Has biography")

            # Show text (truncated or full)
            if show_full_text:
                print(f"\n   Text:\n   {document}")
            else:
                preview = document[:200] + "..." if len(document) > 200 else document
                print(f"   Preview: {preview}")

            print("-" * 80)

    def stats(self):
        """Print collection statistics."""
        # Get sample of metadata to analyze
        sample = self.collection.get(limit=1000)

        if not sample["metadatas"]:
            print("Collection is empty.")
            return

        # Count by type
        type_counts = {}
        bio_count = 0
        classified_count = 0
        total_docs = 0
        total_connections = 0

        for metadata in sample["metadatas"]:
            entity_type = metadata.get("entity_type", "unknown")
            type_counts[entity_type] = type_counts.get(entity_type, 0) + 1

            if metadata.get("has_biography"):
                bio_count += 1

            if metadata.get("classifications"):
                classified_count += 1

            total_docs += metadata.get("document_count", 0)
            total_connections += metadata.get("connection_count", 0)

        print("\n" + "=" * 60)
        print("ENTITY COLLECTION STATISTICS")
        print("=" * 60)
        print(f"Total entities: {self.collection.count()}")
        print(f"Sampled: {len(sample['metadatas'])}")
        print(f"\nBy type (in sample):")
        for entity_type, count in sorted(type_counts.items()):
            print(f"  - {entity_type}: {count}")
        print(f"\nWith biographies: {bio_count}")
        print(f"With classifications: {classified_count}")
        print(f"Total document mentions: {total_docs}")
        print(f"Total connections: {total_connections}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query Epstein entities using semantic search"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query (natural language)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results (default: 10)",
    )
    parser.add_argument(
        "--type",
        choices=["person", "location", "organization"],
        help="Filter by entity type",
    )
    parser.add_argument(
        "--has-biography",
        action="store_true",
        help="Only show entities with biographies",
    )
    parser.add_argument(
        "--min-documents",
        type=int,
        help="Minimum number of documents entity must appear in",
    )
    parser.add_argument(
        "--classification",
        help="Filter by classification label (partial match)",
    )
    parser.add_argument(
        "--full-text",
        action="store_true",
        help="Show full entity text (not truncated)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show collection statistics",
    )

    args = parser.parse_args()

    try:
        client = EntityQueryClient()

        if args.stats:
            client.stats()
            return 0

        if not args.query:
            parser.print_help()
            print("\nError: Please provide a query or use --stats")
            return 1

        print(f"\nQuery: {args.query}")
        if args.type:
            print(f"Filter: entity_type = {args.type}")
        if args.has_biography:
            print(f"Filter: has_biography = True")
        if args.min_documents:
            print(f"Filter: document_count >= {args.min_documents}")
        if args.classification:
            print(f"Filter: classification contains '{args.classification}'")

        results = client.query(
            query_text=args.query,
            limit=args.limit,
            entity_type=args.type,
            has_biography=args.has_biography if args.has_biography else None,
            min_document_count=args.min_documents,
            classification=args.classification,
        )

        client.print_results(results, show_full_text=args.full_text)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
