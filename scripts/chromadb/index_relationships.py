#!/usr/bin/env python3
"""
ChromaDB Relationship Indexing Script

Indexes entity relationships from the entity network into ChromaDB for semantic search.

Usage:
    python scripts/chromadb/index_relationships.py [--reset] [--min-weight N]

Options:
    --reset: Delete existing collection and start fresh
    --min-weight N: Minimum relationship weight threshold (default: 2)
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings
from tqdm import tqdm

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.chromadb.config import (
    BATCH_SIZE,
    CHROMADB_DIR,
    EMBEDDING_MODEL,
    PROGRESS_INTERVAL,
    VERBOSE,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO if VERBOSE else logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Relationship-specific configuration
COLLECTION_NAME = "epstein_relationships"
ENTITY_NETWORK_PATH = Path(__file__).parent.parent.parent / "data" / "transformed" / "entity_network_full.json"
MIN_WEIGHT_DEFAULT = 2


class RelationshipIndexer:
    """Index entity relationships into ChromaDB with semantic search."""

    def __init__(self, reset: bool = False, min_weight: int = MIN_WEIGHT_DEFAULT):
        """Initialize ChromaDB client and collection.

        Args:
            reset: If True, delete existing collection and start fresh
            min_weight: Minimum relationship weight to index
        """
        self.reset = reset
        self.min_weight = min_weight
        self.stats = {
            "total_edges": 0,
            "filtered_edges": 0,
            "indexed": 0,
            "skipped_duplicates": 0,
            "errors": 0,
        }

        # Initialize ChromaDB
        logger.info(f"Initializing ChromaDB at {CHROMADB_DIR}")
        CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(CHROMADB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        # Get or create collection
        if reset:
            try:
                self.client.delete_collection(name=COLLECTION_NAME)
                logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
            except Exception as e:
                logger.debug(f"Collection does not exist yet: {e}")

        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"description": "Entity relationships from Epstein document network"},
        )

        logger.info(f"Collection '{COLLECTION_NAME}' ready")
        logger.info(f"Using embedding model: {EMBEDDING_MODEL}")
        logger.info(f"Minimum relationship weight: {self.min_weight}")

    def load_entity_network(self) -> Dict:
        """Load entity network data.

        Returns:
            Dictionary with nodes and edges
        """
        logger.info(f"Loading entity network from {ENTITY_NETWORK_PATH}")

        with open(ENTITY_NETWORK_PATH) as f:
            data = json.load(f)

        nodes = {node["id"]: node for node in data["nodes"]}
        edges = data["edges"]

        logger.info(f"Loaded {len(nodes)} nodes and {len(edges)} edges")

        return {"nodes": nodes, "edges": edges}

    def create_edge_id(self, source_id: str, target_id: str) -> str:
        """Create unique edge ID from source and target.

        Uses lexicographic ordering to ensure bidirectional edges
        have the same ID (A→B and B→A become same edge).

        Args:
            source_id: Source entity ID
            target_id: Target entity ID

        Returns:
            Unique edge ID
        """
        # Sort IDs to ensure A→B and B→A have same ID
        ids = sorted([source_id, target_id])
        return f"{ids[0]}__{ids[1]}"

    def create_relationship_description(
        self,
        source_node: Dict,
        target_node: Dict,
        edge: Dict
    ) -> str:
        """Create semantic description of relationship for embedding.

        Args:
            source_node: Source entity node data
            target_node: Target entity node data
            edge: Edge data with weight and sources

        Returns:
            Human-readable relationship description
        """
        source_name = source_node["name"]
        target_name = target_node["name"]
        source_type = source_node.get("type", "unknown")
        target_type = target_node.get("type", "unknown")
        weight = edge["weight"]

        # Get source breakdown
        sources = edge.get("sources", {})
        doc_count = sources.get("documents", 0)
        flight_count = sources.get("flight_logs", 0)

        # Build description with context
        parts = [
            f"{source_name} ({source_type})",
            "connected to",
            f"{target_name} ({target_type})"
        ]

        # Add connection details
        connection_details = []
        if doc_count > 0:
            connection_details.append(f"{doc_count} document co-appearances")
        if flight_count > 0:
            connection_details.append(f"{flight_count} flight log entries")

        if connection_details:
            parts.append("through")
            parts.append(" and ".join(connection_details))

        # Add document type context if available
        doc_types = edge.get("document_types", {})
        if doc_types:
            top_type = max(doc_types.items(), key=lambda x: x[1])
            parts.append(f"(primarily in {top_type[0]} documents)")

        description = " ".join(parts)
        return description

    def prepare_metadata(
        self,
        source_node: Dict,
        target_node: Dict,
        edge: Dict
    ) -> Dict:
        """Prepare metadata for ChromaDB storage.

        Args:
            source_node: Source entity node data
            target_node: Target entity node data
            edge: Edge data

        Returns:
            Metadata dictionary
        """
        sources = edge.get("sources", {})
        doc_types = edge.get("document_types", {})

        # Build connection types string
        connection_types = []
        if sources.get("documents", 0) > 0:
            connection_types.append("documents")
        if sources.get("flight_logs", 0) > 0:
            connection_types.append("flight_logs")

        metadata = {
            "source_id": source_node["id"],
            "target_id": target_node["id"],
            "source_name": source_node["name"],
            "target_name": target_node["name"],
            "source_type": source_node.get("type", "unknown"),
            "target_type": target_node.get("type", "unknown"),
            "weight": int(edge["weight"]),
            "document_count": int(sources.get("documents", 0)),
            "flight_log_count": int(sources.get("flight_logs", 0)),
            "connection_types": ",".join(connection_types),
        }

        # Add primary document type if available
        if doc_types:
            top_doc_type = max(doc_types.items(), key=lambda x: x[1])
            metadata["primary_doc_type"] = top_doc_type[0]
            metadata["primary_doc_type_count"] = int(top_doc_type[1])

        # Ensure all values are ChromaDB compatible types
        for key, value in metadata.items():
            if value is None:
                metadata[key] = ""

        return metadata

    def index_relationships(self):
        """Index relationships in batches."""
        data = self.load_entity_network()
        nodes = data["nodes"]
        edges = data["edges"]

        self.stats["total_edges"] = len(edges)

        # Filter edges by weight and deduplicate bidirectional edges
        logger.info(f"Filtering edges (min_weight={self.min_weight})...")

        # Track unique edges (A↔B counted once)
        seen_edges = set()
        filtered_edges = []

        for edge in edges:
            # Skip low-weight edges
            if edge["weight"] < self.min_weight:
                continue

            # Create unique edge ID
            edge_id = self.create_edge_id(edge["source"], edge["target"])

            # Skip if we've already seen this edge (bidirectional)
            if edge_id in seen_edges:
                self.stats["skipped_duplicates"] += 1
                continue

            seen_edges.add(edge_id)
            filtered_edges.append((edge_id, edge))

        self.stats["filtered_edges"] = len(filtered_edges)
        logger.info(
            f"Filtered to {len(filtered_edges)} unique relationships "
            f"(skipped {self.stats['skipped_duplicates']} bidirectional duplicates)"
        )

        # Process in batches
        logger.info(f"Indexing {len(filtered_edges)} relationships...")

        for i in tqdm(range(0, len(filtered_edges), BATCH_SIZE), desc="Indexing batches"):
            batch = filtered_edges[i : i + BATCH_SIZE]
            batch_documents = []
            batch_metadatas = []
            batch_ids = []

            for edge_id, edge in batch:
                try:
                    source_node = nodes.get(edge["source"])
                    target_node = nodes.get(edge["target"])

                    if not source_node or not target_node:
                        logger.warning(f"Missing node for edge {edge_id}")
                        self.stats["errors"] += 1
                        continue

                    # Create relationship description
                    description = self.create_relationship_description(
                        source_node, target_node, edge
                    )

                    # Prepare metadata
                    metadata = self.prepare_metadata(
                        source_node, target_node, edge
                    )

                    batch_documents.append(description)
                    batch_metadatas.append(metadata)
                    batch_ids.append(edge_id)

                except Exception as e:
                    logger.error(f"Error preparing edge {edge_id}: {e}")
                    self.stats["errors"] += 1

            # Add batch to collection
            if batch_documents:
                try:
                    self.collection.add(
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                    )
                    self.stats["indexed"] += len(batch_documents)

                    if (i // BATCH_SIZE) % (PROGRESS_INTERVAL // BATCH_SIZE) == 0:
                        logger.info(
                            f"Progress: {self.stats['indexed']}/{self.stats['filtered_edges']} "
                            f"({self.stats['indexed']/self.stats['filtered_edges']*100:.1f}%)"
                        )

                except Exception as e:
                    logger.error(f"Error adding batch {i}: {e}")
                    self.stats["errors"] += len(batch_documents)

        logger.info("Indexing complete!")

    def print_statistics(self):
        """Print indexing statistics."""
        print("\n" + "=" * 60)
        print("RELATIONSHIP INDEXING STATISTICS")
        print("=" * 60)
        print(f"Total edges in network: {self.stats['total_edges']}")
        print(f"Filtered edges (weight >= {self.min_weight}): {self.stats['filtered_edges']}")
        print(f"Skipped bidirectional duplicates: {self.stats['skipped_duplicates']}")
        print(f"Successfully indexed: {self.stats['indexed']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"\nCollection size: {self.collection.count()} relationships")
        print(f"ChromaDB location: {CHROMADB_DIR}")
        print("=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Index entity relationships into ChromaDB"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collection and start fresh",
    )
    parser.add_argument(
        "--min-weight",
        type=int,
        default=MIN_WEIGHT_DEFAULT,
        help=f"Minimum relationship weight to index (default: {MIN_WEIGHT_DEFAULT})",
    )

    args = parser.parse_args()

    try:
        indexer = RelationshipIndexer(
            reset=args.reset,
            min_weight=args.min_weight
        )
        indexer.index_relationships()
        indexer.print_statistics()

        return 0

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
