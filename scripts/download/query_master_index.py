#!/usr/bin/env python3
"""Query tool for master document index.

Provides search and analysis capabilities for the deduplicated document collection.

Usage:
    python3 query_master_index.py --stats
    python3 query_master_index.py --duplicates
    python3 query_master_index.py --source fbi_vault
    python3 query_master_index.py --hash 674c8534bc4b8b4c
"""

import argparse
import json
from pathlib import Path


class MasterIndexQuery:
    """Query interface for master document index."""

    def __init__(self, base_dir: Path):
        """Initialize query tool.

        Args:
            base_dir: Project root directory
        """
        self.base_dir = base_dir
        self.index_path = base_dir / "data" / "metadata" / "master_document_index.json"

        # Load index
        with open(self.index_path) as f:
            self.index = json.load(f)

    def print_stats(self) -> None:
        """Print comprehensive statistics."""
        print("=" * 70)
        print("MASTER DOCUMENT INDEX STATISTICS")
        print("=" * 70)
        print()

        print(f"Generated: {self.index['generated_at']}")
        print(f"Total Files: {self.index['total_files']:,}")
        print(f"Unique Documents: {self.index['unique_documents']:,}")
        print(f"Duplicate Sets: {self.index['duplicate_sets']:,}")
        print(f"Total Duplicates: {self.index['total_duplicates']:,}")
        print(
            f"Deduplication Rate: {(self.index['total_duplicates'] / self.index['total_files'] * 100):.1f}%"
        )
        print()

        print("SOURCES:")
        print("-" * 70)
        total_docs = 0
        for source, info in sorted(
            self.index["sources"].items(), key=lambda x: x[1]["document_count"], reverse=True
        ):
            count = info["document_count"]
            total_docs += count
            print(f"  {source:30s}: {count:6,} documents")
        print("-" * 70)
        print(f"  {'TOTAL':30s}: {total_docs:6,} documents")
        print()

        # Calculate total storage
        total_size = sum(doc["size"] for doc in self.index["documents"])
        print(f"Total Storage (unique docs): {total_size / (1024**3):.2f} GB")

    def list_duplicates(self, limit: int = 20) -> None:
        """List duplicate document sets.

        Args:
            limit: Maximum number of sets to show
        """
        print("=" * 70)
        print(f"DUPLICATE DOCUMENT SETS (showing top {limit})")
        print("=" * 70)
        print()

        # Get documents with duplicates
        dup_docs = [d for d in self.index["documents"] if d["duplicate_count"] > 0]
        dup_docs.sort(key=lambda x: x["duplicate_count"], reverse=True)

        for i, doc in enumerate(dup_docs[:limit], 1):
            print(f"{i}. Hash: {doc['hash'][:16]}... ({doc['duplicate_count']} duplicates)")
            print(f"   Canonical: {doc['canonical_path']}")
            print(f"   Size: {doc['size'] / (1024**2):.1f} MB")
            print(f"   Sources ({doc['source_count']}):")
            for source in doc["sources"]:
                print(f"     - {source}")
            print()

    def search_by_source(self, source_name: str) -> None:
        """Search documents from a specific source.

        Args:
            source_name: Name of source to search
        """
        print("=" * 70)
        print(f"DOCUMENTS FROM SOURCE: {source_name}")
        print("=" * 70)
        print()

        if source_name not in self.index["sources"]:
            print(f"Error: Source '{source_name}' not found")
            print(f"Available sources: {', '.join(self.index['sources'].keys())}")
            return

        # Find all docs from this source
        matching_docs = []
        for doc in self.index["documents"]:
            for source in doc["sources"]:
                if source_name in source:
                    matching_docs.append(doc)
                    break

        print(f"Found {len(matching_docs)} unique documents from {source_name}")
        print()

        # Show top 10 by size
        matching_docs.sort(key=lambda x: x["size"], reverse=True)
        print("Top 10 by size:")
        for i, doc in enumerate(matching_docs[:10], 1):
            print(f"{i}. {doc['canonical_path']}")
            print(f"   Size: {doc['size'] / (1024**2):.1f} MB")
            print(f"   Hash: {doc['hash'][:16]}...")
            if doc["duplicate_count"] > 0:
                print(f"   Duplicates: {doc['duplicate_count']} in other sources")
            print()

    def search_by_hash(self, hash_prefix: str) -> None:
        """Search document by hash prefix.

        Args:
            hash_prefix: Start of SHA256 hash
        """
        print("=" * 70)
        print(f"SEARCH BY HASH: {hash_prefix}")
        print("=" * 70)
        print()

        matching_docs = [d for d in self.index["documents"] if d["hash"].startswith(hash_prefix)]

        if not matching_docs:
            print(f"No documents found matching hash prefix: {hash_prefix}")
            return

        for doc in matching_docs:
            print(f"Hash: {doc['hash']}")
            print(f"Canonical Path: {doc['canonical_path']}")
            print(f"Size: {doc['size'] / (1024**2):.1f} MB")
            print(f"Source Count: {doc['source_count']}")
            print(f"Duplicate Count: {doc['duplicate_count']}")
            print()
            print("All sources:")
            for source in doc["sources"]:
                print(f"  - {source}")
            print()

    def find_cross_source_duplicates(self) -> None:
        """Find documents that appear in multiple different sources."""
        print("=" * 70)
        print("CROSS-SOURCE DUPLICATES")
        print("=" * 70)
        print()

        # Find docs with different source directories
        cross_source = []
        for doc in self.index["documents"]:
            if doc["source_count"] > 1:
                # Extract source directories
                source_dirs = set()
                for source_path in doc["sources"]:
                    parts = Path(source_path).parts
                    if len(parts) >= 3:  # data/sources/SOURCE_NAME
                        source_dirs.add(parts[2])

                if len(source_dirs) > 1:
                    cross_source.append({"doc": doc, "source_dirs": source_dirs})

        cross_source.sort(key=lambda x: len(x["source_dirs"]), reverse=True)

        print(f"Found {len(cross_source)} documents appearing in multiple sources")
        print()

        # Show top 20
        for i, item in enumerate(cross_source[:20], 1):
            doc = item["doc"]
            sources = item["source_dirs"]
            print(f"{i}. {doc['canonical_path']}")
            print(f"   Size: {doc['size'] / (1024**2):.1f} MB")
            print(f"   Appears in {len(sources)} different sources: {', '.join(sorted(sources))}")
            print()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Query master document index")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--duplicates", action="store_true", help="List duplicate sets")
    parser.add_argument("--source", type=str, help="Search by source name")
    parser.add_argument("--hash", type=str, help="Search by hash prefix")
    parser.add_argument("--cross-source", action="store_true", help="Find cross-source duplicates")
    parser.add_argument("--limit", type=int, default=20, help="Limit results (default: 20)")

    args = parser.parse_args()

    base_dir = Path("/Users/masa/Projects/epstein")
    query = MasterIndexQuery(base_dir)

    if args.stats:
        query.print_stats()
    elif args.duplicates:
        query.list_duplicates(limit=args.limit)
    elif args.source:
        query.search_by_source(args.source)
    elif args.hash:
        query.search_by_hash(args.hash)
    elif args.cross_source:
        query.find_cross_source_duplicates()
    else:
        # Default: show stats
        query.print_stats()


if __name__ == "__main__":
    main()
