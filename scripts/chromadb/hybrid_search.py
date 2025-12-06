#!/usr/bin/env python3
"""
ChromaDB Hybrid Search - Query across all collections

Unified search interface that queries documents, entities, and relationships
simultaneously and combines results intelligently.

Features:
- Parallel querying of all three collections
- Score normalization for consistent ranking
- Type filtering (document, entity, relationship)
- Faceted results for UI filtering
- Rich CLI output and JSON export

Usage:
    # Basic search across all collections
    python scripts/chromadb/hybrid_search.py "Jeffrey Epstein connections"

    # Filter by result type
    python scripts/chromadb/hybrid_search.py "flight logs" --type document,entity

    # JSON output for API integration
    python scripts/chromadb/hybrid_search.py "lawyers" --json

    # Adjust result limits
    python scripts/chromadb/hybrid_search.py "private islands" --limit 20

    # Per-collection limits
    python scripts/chromadb/hybrid_search.py "FBI" --doc-limit 5 --entity-limit 5 --rel-limit 5

Examples:
    # Find all evidence about a person
    python scripts/chromadb/hybrid_search.py "Ghislaine Maxwell" --limit 30

    # Focus on locations
    python scripts/chromadb/hybrid_search.py "New York" --type entity --entity-type location

    # Search for legal documents
    python scripts/chromadb/hybrid_search.py "depositions" --type document
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import chromadb
from chromadb.config import Settings

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import CHROMADB_DIR, COLLECTION_NAME, EMBEDDING_MODEL

# Collection names
DOCUMENT_COLLECTION = COLLECTION_NAME  # "epstein_documents"
ENTITY_COLLECTION = "epstein_entities"
RELATIONSHIP_COLLECTION = "epstein_relationships"


@dataclass
class SearchResult:
    """Unified search result from any collection."""

    type: str  # "document", "entity", or "relationship"
    id: str
    name: str  # Display name
    score: float  # Normalized 0-1 (1 = best match)
    preview: str  # Text snippet
    metadata: Dict

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "id": self.id,
            "name": self.name,
            "score": round(self.score, 4),
            "preview": self.preview,
            "metadata": self.metadata,
        }


class HybridSearchClient:
    """Query all ChromaDB collections and combine results."""

    def __init__(self, chromadb_path: Path = CHROMADB_DIR):
        """Initialize ChromaDB client and load collections.

        Args:
            chromadb_path: Path to ChromaDB persistent storage
        """
        self.client = chromadb.PersistentClient(
            path=str(chromadb_path),
            settings=Settings(anonymized_telemetry=False),
        )

        # Load collections
        self.collections = {}
        self._load_collection(DOCUMENT_COLLECTION, "document")
        self._load_collection(ENTITY_COLLECTION, "entity")
        self._load_collection(RELATIONSHIP_COLLECTION, "relationship")

        if not self.collections:
            raise RuntimeError("No collections found. Please index data first.")

    def _load_collection(self, name: str, result_type: str):
        """Load a collection if it exists.

        Args:
            name: Collection name
            result_type: Result type tag (document, entity, relationship)
        """
        try:
            collection = self.client.get_collection(name=name)
            self.collections[result_type] = collection
            print(f"✓ Loaded {name}: {collection.count()} items")
        except Exception as e:
            print(f"⚠ Collection '{name}' not found: {e}")

    def search(
        self,
        query: str,
        limit: int = 20,
        result_types: Optional[List[str]] = None,
        doc_limit: Optional[int] = None,
        entity_limit: Optional[int] = None,
        rel_limit: Optional[int] = None,
        entity_type: Optional[str] = None,
        document_classification: Optional[str] = None,
    ) -> Dict:
        """Execute hybrid search across all collections.

        Args:
            query: Search query text
            limit: Total result limit (distributed across collections)
            result_types: Filter by types (["document", "entity", "relationship"])
            doc_limit: Override limit for documents
            entity_limit: Override limit for entities
            rel_limit: Override limit for relationships
            entity_type: Filter entities by type (person, location, organization)
            document_classification: Filter documents by classification

        Returns:
            Dictionary with results, facets, and metadata
        """
        # Filter collections by result type
        active_collections = {}
        if result_types:
            for rtype in result_types:
                if rtype in self.collections:
                    active_collections[rtype] = self.collections[rtype]
        else:
            active_collections = self.collections

        if not active_collections:
            return self._empty_result(query)

        # Calculate per-collection limits
        per_collection_limit = limit // len(active_collections)
        collection_limits = {
            "document": doc_limit or per_collection_limit,
            "entity": entity_limit or per_collection_limit,
            "relationship": rel_limit or per_collection_limit,
        }

        # Query collections in parallel
        all_results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}

            if "document" in active_collections:
                where_filter = None
                if document_classification:
                    where_filter = {"classification": document_classification}
                futures[executor.submit(
                    self._query_documents,
                    query,
                    collection_limits["document"],
                    where_filter,
                )] = "document"

            if "entity" in active_collections:
                where_filter = None
                if entity_type:
                    where_filter = {"entity_type": entity_type}
                futures[executor.submit(
                    self._query_entities,
                    query,
                    collection_limits["entity"],
                    where_filter,
                )] = "entity"

            if "relationship" in active_collections:
                futures[executor.submit(
                    self._query_relationships,
                    query,
                    collection_limits["relationship"],
                )] = "relationship"

            # Collect results as they complete
            for future in as_completed(futures):
                result_type = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Error querying {result_type}: {e}", file=sys.stderr)

        # Sort by score (descending) and apply global limit
        all_results.sort(key=lambda r: r.score, reverse=True)
        top_results = all_results[:limit]

        # Generate facets
        facets = self._generate_facets(all_results)

        return {
            "query": query,
            "total_results": len(top_results),
            "results": [r.to_dict() for r in top_results],
            "facets": facets,
        }

    def _query_documents(
        self,
        query: str,
        limit: int,
        where_filter: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """Query document collection.

        Args:
            query: Search query
            limit: Result limit
            where_filter: Metadata filter

        Returns:
            List of SearchResult objects
        """
        collection = self.collections["document"]
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        for i, doc_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            document = results["documents"][0][i]
            distance = results["distances"][0][i]

            # Normalize score (ChromaDB uses L2 distance, lower is better)
            # Typical range: 0.0 (perfect) to 2.0 (very different)
            # Convert to 0-1 score where 1 is best
            score = max(0, 1 - (distance / 2.0))

            # Generate display name
            name = metadata.get("filename", doc_id)

            # Generate preview
            preview = document[:200] + "..." if len(document) > 200 else document

            search_results.append(
                SearchResult(
                    type="document",
                    id=doc_id,
                    name=name,
                    score=score,
                    preview=preview,
                    metadata=metadata,
                )
            )

        return search_results

    def _query_entities(
        self,
        query: str,
        limit: int,
        where_filter: Optional[Dict] = None,
    ) -> List[SearchResult]:
        """Query entity collection.

        Args:
            query: Search query
            limit: Result limit
            where_filter: Metadata filter

        Returns:
            List of SearchResult objects
        """
        collection = self.collections["entity"]
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        for i, entity_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            document = results["documents"][0][i]
            distance = results["distances"][0][i]

            # Normalize score
            score = max(0, 1 - (distance / 2.0))

            # Display name
            name = metadata.get("canonical_name", entity_id)
            entity_type = metadata.get("entity_type", "unknown")

            # Preview
            preview = document[:200] + "..." if len(document) > 200 else document

            search_results.append(
                SearchResult(
                    type="entity",
                    id=entity_id,
                    name=f"{name} ({entity_type})",
                    score=score,
                    preview=preview,
                    metadata=metadata,
                )
            )

        return search_results

    def _query_relationships(
        self,
        query: str,
        limit: int,
    ) -> List[SearchResult]:
        """Query relationship collection.

        Args:
            query: Search query
            limit: Result limit

        Returns:
            List of SearchResult objects
        """
        collection = self.collections["relationship"]
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        search_results = []
        for i, rel_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            document = results["documents"][0][i]
            distance = results["distances"][0][i]

            # Normalize score
            score = max(0, 1 - (distance / 2.0))

            # Display name (connection)
            source_name = metadata.get("source_name", "Unknown")
            target_name = metadata.get("target_name", "Unknown")
            name = f"{source_name} ↔ {target_name}"

            # Preview is the relationship description
            preview = document

            search_results.append(
                SearchResult(
                    type="relationship",
                    id=rel_id,
                    name=name,
                    score=score,
                    preview=preview,
                    metadata=metadata,
                )
            )

        return search_results

    def _generate_facets(self, results: List[SearchResult]) -> Dict:
        """Generate facet counts for filtering.

        Args:
            results: All search results

        Returns:
            Facet dictionary
        """
        facets = {
            "by_type": {},
            "by_entity_type": {},
            "by_document_classification": {},
        }

        for result in results:
            # Count by result type
            result_type = result.type
            facets["by_type"][result_type] = (
                facets["by_type"].get(result_type, 0) + 1
            )

            # Count by entity type
            if result.type == "entity":
                entity_type = result.metadata.get("entity_type", "unknown")
                facets["by_entity_type"][entity_type] = (
                    facets["by_entity_type"].get(entity_type, 0) + 1
                )

            # Count by document classification
            if result.type == "document":
                classification = result.metadata.get("classification", "unknown")
                facets["by_document_classification"][classification] = (
                    facets["by_document_classification"].get(classification, 0) + 1
                )

        return facets

    def _empty_result(self, query: str) -> Dict:
        """Return empty result structure.

        Args:
            query: Original query

        Returns:
            Empty result dictionary
        """
        return {
            "query": query,
            "total_results": 0,
            "results": [],
            "facets": {
                "by_type": {},
                "by_entity_type": {},
                "by_document_classification": {},
            },
        }

    def print_results(self, results_dict: Dict, verbose: bool = False):
        """Pretty-print search results.

        Args:
            results_dict: Results dictionary from search()
            verbose: If True, show full metadata
        """
        query = results_dict["query"]
        total = results_dict["total_results"]
        results = results_dict["results"]
        facets = results_dict["facets"]

        print(f"\n{'=' * 80}")
        print(f"Query: {query}")
        print(f"Total results: {total}")
        print(f"{'=' * 80}")

        # Show facets
        if facets["by_type"]:
            print("\nResults by type:")
            for rtype, count in sorted(facets["by_type"].items()):
                print(f"  • {rtype}: {count}")

        if facets["by_entity_type"]:
            print("\nEntity types:")
            for etype, count in sorted(
                facets["by_entity_type"].items(), key=lambda x: x[1], reverse=True
            )[:5]:
                print(f"  • {etype}: {count}")

        if facets["by_document_classification"]:
            print("\nDocument classifications:")
            for classification, count in sorted(
                facets["by_document_classification"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]:
                print(f"  • {classification}: {count}")

        print(f"\n{'-' * 80}")
        print("Top Results:")
        print(f"{'-' * 80}")

        # Print results
        for i, result in enumerate(results, 1):
            print(f"\n{i}. [{result['type'].upper()}] {result['name']}")
            print(f"   Score: {result['score']:.3f}")
            print(f"   Preview: {result['preview']}")

            if verbose:
                print(f"   Metadata: {json.dumps(result['metadata'], indent=6)}")
            else:
                # Show key metadata fields
                metadata = result["metadata"]
                if result["type"] == "document":
                    print(f"   Classification: {metadata.get('classification', 'N/A')}")
                    print(f"   Source: {metadata.get('source', 'N/A')}")
                elif result["type"] == "entity":
                    print(f"   Type: {metadata.get('entity_type', 'N/A')}")
                    print(f"   Documents: {metadata.get('document_count', 0)}")
                    print(f"   Connections: {metadata.get('connection_count', 0)}")
                elif result["type"] == "relationship":
                    print(f"   Weight: {metadata.get('weight', 0)}")
                    print(f"   Documents: {metadata.get('document_count', 0)}")
                    print(
                        f"   Connection Types: {metadata.get('connection_types', 'N/A')}"
                    )

        print(f"\n{'=' * 80}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Hybrid search across all ChromaDB collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search all collections
  %(prog)s "Jeffrey Epstein connections"

  # Search only documents and entities
  %(prog)s "flight logs" --type document,entity

  # Filter by entity type
  %(prog)s "lawyers" --type entity --entity-type person

  # JSON output for API
  %(prog)s "private islands" --json

  # Custom limits per collection
  %(prog)s "FBI" --doc-limit 5 --entity-limit 10 --rel-limit 5
        """,
    )
    parser.add_argument("query", type=str, help="Search query")
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Total result limit (default: 20)",
    )
    parser.add_argument(
        "--type",
        type=str,
        help="Filter by result types (comma-separated: document,entity,relationship)",
    )
    parser.add_argument(
        "--doc-limit",
        type=int,
        help="Override limit for documents",
    )
    parser.add_argument(
        "--entity-limit",
        type=int,
        help="Override limit for entities",
    )
    parser.add_argument(
        "--rel-limit",
        type=int,
        help="Override limit for relationships",
    )
    parser.add_argument(
        "--entity-type",
        type=str,
        choices=["person", "location", "organization"],
        help="Filter entities by type",
    )
    parser.add_argument(
        "--document-classification",
        type=str,
        help="Filter documents by classification",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full metadata for each result",
    )

    args = parser.parse_args()

    try:
        # Parse result types
        result_types = None
        if args.type:
            result_types = [t.strip() for t in args.type.split(",")]
            valid_types = {"document", "entity", "relationship"}
            invalid = set(result_types) - valid_types
            if invalid:
                print(
                    f"Error: Invalid result types: {invalid}. "
                    f"Valid types: {valid_types}"
                )
                return 1

        # Initialize client
        client = HybridSearchClient()

        # Execute search
        results = client.search(
            query=args.query,
            limit=args.limit,
            result_types=result_types,
            doc_limit=args.doc_limit,
            entity_limit=args.entity_limit,
            rel_limit=args.rel_limit,
            entity_type=args.entity_type,
            document_classification=args.document_classification,
        )

        # Output results
        if args.json:
            print(json.dumps(results, indent=2))
        else:
            client.print_results(results, verbose=args.verbose)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
