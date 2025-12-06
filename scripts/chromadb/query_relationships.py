#!/usr/bin/env python3
"""
ChromaDB Relationship Query Script

Query entity relationships using semantic search.

Usage:
    python scripts/chromadb/query_relationships.py "search query" [--limit 10]

Examples:
    # Find relationships involving FBI
    python scripts/chromadb/query_relationships.py "FBI connections" --limit 5

    # Find flight log relationships
    python scripts/chromadb/query_relationships.py "flight logs" --source-type flight_logs

    # Find person-to-organization relationships
    python scripts/chromadb/query_relationships.py "Jeffrey Epstein organizations" --target-type organization

    # Find strong connections (high weight)
    python scripts/chromadb/query_relationships.py "Jeffrey Epstein" --min-weight 100
"""

import argparse
import json
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import CHROMADB_DIR

COLLECTION_NAME = "epstein_relationships"


def query_relationships(
    query: str,
    n_results: int = 10,
    entity_name: str = None,
    source_type: str = None,
    target_type: str = None,
    connection_type: str = None,
    min_weight: int = None,
):
    """Query the relationship collection.

    Args:
        query: Semantic search query
        n_results: Number of results to return
        entity_name: Filter by specific entity name (source or target)
        source_type: Filter by source entity type (person, organization, location, etc.)
        target_type: Filter by target entity type
        connection_type: Filter by connection type (documents, flight_logs)
        min_weight: Minimum relationship weight
    """
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=str(CHROMADB_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        collection = client.get_collection(name=COLLECTION_NAME)
    except ValueError:
        print(f"Error: Collection '{COLLECTION_NAME}' not found.")
        print("Please run index_relationships.py first.")
        return

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total relationships: {collection.count()}")
    print(f"\nQuery: {query}")
    print("=" * 60)

    # Build filter dictionary using ChromaDB's supported operators
    # Note: ChromaDB only supports: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin
    filter_dict = {}
    if source_type:
        filter_dict["source_type"] = source_type
    if target_type:
        filter_dict["target_type"] = target_type
    if min_weight:
        filter_dict["weight"] = {"$gte": min_weight}

    # Note: entity_name and connection_type filtering will be done post-query
    # since ChromaDB doesn't support $contains or $or with complex string matching

    if filter_dict:
        print(f"Filters: {json.dumps(filter_dict, indent=2)}")

    print(f"Returning top {n_results} results")
    print("=" * 60)

    # Query the collection (fetch more results for post-filtering)
    query_limit = n_results * 3 if (entity_name or connection_type) else n_results

    try:
        results = collection.query(
            query_texts=[query],
            n_results=query_limit,
            where=filter_dict if filter_dict else None,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        print(f"Query error: {e}")
        print("\nNote: ChromaDB's where clause only supports: $eq, $ne, $gt, $gte, $lt, $lte, $in, $nin")
        return

    # Display results
    if not results["ids"][0]:
        print("No results found.")
        return

    # Post-filter results for entity_name and connection_type
    filtered_results = []
    for i, edge_id in enumerate(results["ids"][0]):
        metadata = results["metadatas"][0][i]

        # Filter by entity_name (case-insensitive substring match)
        if entity_name:
            entity_lower = entity_name.lower()
            source_name = metadata.get('source_name', '').lower()
            target_name = metadata.get('target_name', '').lower()
            if entity_lower not in source_name and entity_lower not in target_name:
                continue

        # Filter by connection_type
        if connection_type:
            conn_types = metadata.get('connection_types', '')
            if connection_type not in conn_types:
                continue

        filtered_results.append(i)
        if len(filtered_results) >= n_results:
            break

    if not filtered_results:
        print("No results found after filtering.")
        return

    # Display filtered results
    for rank, i in enumerate(filtered_results, 1):
        edge_id = results["ids"][0][i]
        distance = results["distances"][0][i]
        metadata = results["metadatas"][0][i]
        document = results["documents"][0][i]

        print(f"\n{rank}. Relationship ID: {edge_id}")
        print(f"   Distance: {distance:.4f}")
        print(f"   Connection: {metadata.get('source_name')} ({metadata.get('source_type')}) ↔ "
              f"{metadata.get('target_name')} ({metadata.get('target_type')})")
        print(f"   Weight: {metadata.get('weight')}")
        print(f"   Documents: {metadata.get('document_count')}")
        print(f"   Flight Logs: {metadata.get('flight_log_count')}")
        print(f"   Connection Types: {metadata.get('connection_types')}")

        if metadata.get('primary_doc_type'):
            print(f"   Primary Document Type: {metadata.get('primary_doc_type')} "
                  f"({metadata.get('primary_doc_type_count')} docs)")

        print(f"   Description: {document}")

    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Query entity relationships in ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find FBI connections
  %(prog)s "FBI connections" --limit 5

  # Find flight log relationships
  %(prog)s "flight logs" --connection-type flight_logs

  # Find Jeffrey Epstein's organizational connections
  %(prog)s "organizations" --entity "Jeffrey Epstein" --target-type organization

  # Find strong connections (weight >= 100)
  %(prog)s "Jeffrey Epstein" --min-weight 100
        """,
    )
    parser.add_argument("query", type=str, help="Semantic search query")
    parser.add_argument(
        "--limit", type=int, default=10, help="Number of results to return"
    )
    parser.add_argument(
        "--entity",
        type=str,
        help="Filter by entity name (searches both source and target)",
    )
    parser.add_argument(
        "--source-type",
        type=str,
        help="Filter by source entity type (person, organization, location, etc.)",
    )
    parser.add_argument(
        "--target-type",
        type=str,
        help="Filter by target entity type",
    )
    parser.add_argument(
        "--connection-type",
        type=str,
        choices=["documents", "flight_logs"],
        help="Filter by connection type",
    )
    parser.add_argument(
        "--min-weight",
        type=int,
        help="Minimum relationship weight",
    )

    args = parser.parse_args()

    query_relationships(
        query=args.query,
        n_results=args.limit,
        entity_name=args.entity,
        source_type=args.source_type,
        target_type=args.target_type,
        connection_type=args.connection_type,
        min_weight=args.min_weight,
    )


if __name__ == "__main__":
    main()
