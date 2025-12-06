#!/usr/bin/env python3
"""
ChromaDB Query Script

Simple script to query the indexed documents and test the system.

Usage:
    python scripts/chromadb/query_documents.py "search query" [--limit 10]
"""

import argparse
import json
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import CHROMADB_DIR, COLLECTION_NAME


def query_collection(query: str, n_results: int = 10, filter_dict: dict = None):
    """Query the ChromaDB collection.

    Args:
        query: Search query text
        n_results: Number of results to return
        filter_dict: Optional metadata filter (e.g., {"classification": "court_record"})
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
        print("Please run index_documents.py first.")
        return

    print(f"Collection: {COLLECTION_NAME}")
    print(f"Total documents: {collection.count()}")
    print(f"\nQuery: {query}")
    if filter_dict:
        print(f"Filter: {json.dumps(filter_dict, indent=2)}")
    print(f"Returning top {n_results} results")
    print("=" * 60)

    # Query the collection
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=filter_dict,
        include=["documents", "metadatas", "distances"],
    )

    # Display results
    if not results["ids"][0]:
        print("No results found.")
        return

    for i, doc_id in enumerate(results["ids"][0]):
        distance = results["distances"][0][i]
        metadata = results["metadatas"][0][i]
        document = results["documents"][0][i]

        print(f"\n{i+1}. Document ID: {doc_id}")
        print(f"   Distance: {distance:.4f}")
        print(f"   Filename: {metadata.get('filename', 'N/A')}")
        print(f"   Classification: {metadata.get('classification', 'N/A')}")
        print(f"   Source: {metadata.get('source', 'N/A')}")
        print(f"   Entities: {metadata.get('entity_count', 0)}")
        print(f"   Has real content: {metadata.get('has_real_content', False)}")
        print(f"   Confidence: {metadata.get('confidence', 0.0):.2f}")

        # Show document preview (first 200 chars)
        preview = document[:200] + "..." if len(document) > 200 else document
        print(f"   Preview: {preview}")

    print("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query ChromaDB document collection")
    parser.add_argument("query", type=str, help="Search query text")
    parser.add_argument(
        "--limit", type=int, default=10, help="Number of results to return"
    )
    parser.add_argument(
        "--classification",
        type=str,
        help="Filter by classification (e.g., 'court_record')",
    )
    parser.add_argument(
        "--source", type=str, help="Filter by source (e.g., 'fbi_vault')"
    )

    args = parser.parse_args()

    # Build filter dictionary
    filter_dict = {}
    if args.classification:
        filter_dict["classification"] = args.classification
    if args.source:
        filter_dict["source"] = args.source

    query_collection(args.query, n_results=args.limit, filter_dict=filter_dict or None)


if __name__ == "__main__":
    main()
