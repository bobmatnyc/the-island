#!/usr/bin/env python3
"""Build comprehensive entity network graph from co-appearances and flight logs.

This script:
1. Loads entity co-appearances from documents
2. Loads existing flight log network
3. Merges both sources into unified network graph
4. Ensures bidirectional edges with consistent weights
5. Calculates network statistics

Output: entity_network_full.json with nodes and weighted edges.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TRANSFORMED_DIR = DATA_DIR / "transformed"
METADATA_DIR = DATA_DIR / "metadata"


def load_json(filepath: Path) -> dict:
    """Load JSON file with error handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        raise


def load_entity_uuid_mappings() -> Dict[str, dict]:
    """Load entity UUID mappings."""
    logger.info("Loading entity UUID mappings...")
    uuid_file = TRANSFORMED_DIR / "entity_uuid_mappings.json"

    if not uuid_file.exists():
        logger.warning(f"UUID mappings not found at {uuid_file}")
        return {}

    data = load_json(uuid_file)
    return data.get("mappings", {})


def load_entity_to_documents() -> Dict[str, List[str]]:
    """Load entity-to-documents mapping for document counts."""
    logger.info("Loading entity-to-documents mapping...")
    entity_docs_file = TRANSFORMED_DIR / "entity_to_documents.json"
    data = load_json(entity_docs_file)
    return data.get("entity_to_documents", {})


def normalize_flight_log_id(name: str) -> str:
    """Normalize flight log entity names to match UUID mappings.

    Flight log uses underscore IDs like 'jeffrey_epstein', 'ghislaine_maxwell'.
    UUID mappings use similar normalized names.
    """
    # Remove commas and convert to lowercase underscore format
    normalized = name.lower().replace(",", "").replace(" ", "_")
    return normalized


def build_network_from_coappearances(
    coappearances: List[dict],
    uuid_mappings: Dict[str, dict]
) -> Tuple[Dict[str, dict], Dict[Tuple[str, str], dict]]:
    """Build network nodes and edges from co-appearance data.

    Args:
        coappearances: List of co-appearance dicts
        uuid_mappings: Entity UUID mappings

    Returns:
        Tuple of (nodes_dict, edges_dict)
        - nodes_dict: {entity_id: node_data}
        - edges_dict: {(source, target): edge_data}
    """
    logger.info("Building network from co-appearances...")

    nodes = {}
    edges = {}

    for pair in coappearances:
        entity_a = pair["entity_a"]
        entity_b = pair["entity_b"]
        count = pair["count"]
        doc_types = pair["document_types"]

        # Add nodes
        for entity in [entity_a, entity_b]:
            if entity["id"] not in nodes:
                nodes[entity["id"]] = {
                    "id": entity["id"],
                    "name": entity["name"],
                    "type": entity["type"],
                    "connection_count": 0
                }

        # Add bidirectional edges (A->B and B->A)
        edge_key_ab = (entity_a["id"], entity_b["id"])
        edge_key_ba = (entity_b["id"], entity_a["id"])

        edge_data = {
            "source": entity_a["id"],
            "target": entity_b["id"],
            "weight": count,
            "sources": {
                "documents": count
            },
            "document_types": doc_types
        }

        edges[edge_key_ab] = edge_data
        edges[edge_key_ba] = {
            **edge_data,
            "source": entity_b["id"],
            "target": entity_a["id"]
        }

        # Increment connection counts
        nodes[entity_a["id"]]["connection_count"] += 1
        nodes[entity_b["id"]]["connection_count"] += 1

    logger.info(f"Built {len(nodes)} nodes and {len(edges)} edges from co-appearances")
    return nodes, edges


def merge_flight_log_network(
    nodes: Dict[str, dict],
    edges: Dict[Tuple[str, str], dict],
    flight_log_file: Path,
    uuid_mappings: Dict[str, dict]
) -> Tuple[Dict[str, dict], Dict[Tuple[str, str], dict]]:
    """Merge flight log network data into existing network.

    Args:
        nodes: Existing nodes dict
        edges: Existing edges dict
        flight_log_file: Path to flight log network JSON
        uuid_mappings: Entity UUID mappings

    Returns:
        Updated (nodes, edges)
    """
    if not flight_log_file.exists():
        logger.warning(f"Flight log network not found at {flight_log_file}")
        return nodes, edges

    logger.info("Loading flight log network...")
    flight_data = load_json(flight_log_file)

    flight_nodes = flight_data.get("nodes", [])
    flight_edges = flight_data.get("edges", [])

    logger.info(f"Flight log: {len(flight_nodes)} nodes, {len(flight_edges)} edges")

    # Create mapping: flight_log_id -> UUID
    flight_id_to_uuid = {}
    for flight_node in flight_nodes:
        flight_id = flight_node.get("id", "")
        normalized = normalize_flight_log_id(flight_node.get("name", ""))

        # Try to find matching UUID
        matched_uuid = None
        if normalized in uuid_mappings:
            matched_uuid = uuid_mappings[normalized].get("id")
        else:
            # Try with the flight_id directly
            for uuid, entity in uuid_mappings.items():
                if entity.get("normalized_name") == normalized:
                    matched_uuid = uuid
                    break

        if matched_uuid:
            flight_id_to_uuid[flight_id] = matched_uuid
        else:
            # Use flight_id as-is if no UUID match
            logger.debug(f"No UUID match for flight log entity: {flight_id} ({normalized})")
            flight_id_to_uuid[flight_id] = flight_id

    # Merge flight log nodes
    for flight_node in flight_nodes:
        flight_id = flight_node.get("id", "")
        entity_id = flight_id_to_uuid.get(flight_id, flight_id)

        if entity_id not in nodes:
            # Add new node from flight logs
            nodes[entity_id] = {
                "id": entity_id,
                "name": flight_node.get("name", ""),
                "type": "person",  # Flight logs are typically people
                "connection_count": flight_node.get("connection_count", 0)
            }

    # Merge flight log edges
    edges_added = 0
    for flight_edge in flight_edges:
        source_flight = flight_edge.get("source", "")
        target_flight = flight_edge.get("target", "")
        weight = flight_edge.get("weight", 1)

        # Map to UUIDs
        source_id = flight_id_to_uuid.get(source_flight, source_flight)
        target_id = flight_id_to_uuid.get(target_flight, target_flight)

        # Ensure consistent ordering for edge key
        if source_id > target_id:
            source_id, target_id = target_id, source_id

        edge_key = (source_id, target_id)
        reverse_key = (target_id, source_id)

        # Merge or add edge
        if edge_key in edges:
            # Edge exists - merge weights
            existing = edges[edge_key]
            if "sources" not in existing:
                existing["sources"] = {"documents": existing.get("weight", 0)}

            # Add flight_logs source
            existing["sources"]["flight_logs"] = weight
            existing["weight"] += weight

            # Update document types
            if "document_types" not in existing:
                existing["document_types"] = {}
            existing["document_types"]["flight_log"] = weight

            # Update reverse edge
            edges[reverse_key]["sources"]["flight_logs"] = weight
            edges[reverse_key]["weight"] += weight
            edges[reverse_key]["document_types"]["flight_log"] = weight
        else:
            # New edge from flight logs
            edge_data = {
                "source": source_id,
                "target": target_id,
                "weight": weight,
                "sources": {
                    "flight_logs": weight
                },
                "document_types": {
                    "flight_log": weight
                }
            }

            edges[edge_key] = edge_data
            edges[reverse_key] = {
                **edge_data,
                "source": target_id,
                "target": source_id
            }

            # Update connection counts
            if source_id in nodes:
                nodes[source_id]["connection_count"] += 1
            if target_id in nodes:
                nodes[target_id]["connection_count"] += 1

            edges_added += 1

    logger.info(f"Merged flight logs: added {edges_added} new edges")
    return nodes, edges


def add_document_counts(
    nodes: Dict[str, dict],
    entity_to_docs: Dict[str, List[str]],
    uuid_mappings: Dict[str, dict]
) -> None:
    """Add document_count to each node.

    Args:
        nodes: Nodes dict to update
        entity_to_docs: Entity name to documents mapping
        uuid_mappings: Entity UUID mappings
    """
    logger.info("Adding document counts to nodes...")

    # Create reverse mapping: uuid -> normalized_name
    uuid_to_normalized = {}
    for uuid, entity in uuid_mappings.items():
        uuid_to_normalized[uuid] = entity.get("normalized_name", "")

    # Update document counts
    for entity_id, node in nodes.items():
        # Try to find entity in entity_to_docs
        doc_count = 0

        # Try normalized name from UUID mappings
        if entity_id in uuid_to_normalized:
            normalized_name = uuid_to_normalized[entity_id]
            if normalized_name in entity_to_docs:
                doc_count = len(entity_to_docs[normalized_name])

        # Try lowercase node name
        if doc_count == 0:
            name_lower = node["name"].lower()
            if name_lower in entity_to_docs:
                doc_count = len(entity_to_docs[name_lower])

        # Try name with underscores
        if doc_count == 0:
            name_underscore = node["name"].lower().replace(" ", "_")
            if name_underscore in entity_to_docs:
                doc_count = len(entity_to_docs[name_underscore])

        node["document_count"] = doc_count


def calculate_network_stats(
    nodes: Dict[str, dict],
    edges: Dict[Tuple[str, str], dict]
) -> dict:
    """Calculate network statistics.

    Args:
        nodes: Network nodes
        edges: Network edges

    Returns:
        Dict with network statistics
    """
    logger.info("Calculating network statistics...")

    # Find most connected entities
    sorted_nodes = sorted(
        nodes.values(),
        key=lambda x: x.get("connection_count", 0),
        reverse=True
    )

    top_connected = [
        {
            "name": node["name"],
            "id": node["id"],
            "connections": node["connection_count"],
            "documents": node.get("document_count", 0)
        }
        for node in sorted_nodes[:10]
    ]

    # Calculate average connections
    total_connections = sum(n.get("connection_count", 0) for n in nodes.values())
    avg_connections = total_connections / len(nodes) if nodes else 0

    # Unique edge count (bidirectional edges counted once)
    unique_edges = len(edges) // 2

    stats = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "unique_edges": unique_edges,
        "average_connections_per_node": round(avg_connections, 2),
        "top_10_most_connected": top_connected
    }

    return stats


def main():
    """Main execution function."""
    logger.info("Starting entity network graph construction...")

    # Load co-appearances
    logger.info("Loading entity co-appearances...")
    coappearances_file = TRANSFORMED_DIR / "entity_coappearances.json"
    coapp_data = load_json(coappearances_file)
    coappearances = coapp_data.get("coappearances", [])

    # Load UUID mappings
    uuid_mappings = load_entity_uuid_mappings()

    # Build initial network from co-appearances
    nodes, edges = build_network_from_coappearances(coappearances, uuid_mappings)

    # Merge flight log network
    flight_log_file = METADATA_DIR / "entity_network.json"
    nodes, edges = merge_flight_log_network(nodes, edges, flight_log_file, uuid_mappings)

    # Add document counts
    entity_to_docs = load_entity_to_documents()
    add_document_counts(nodes, entity_to_docs, uuid_mappings)

    # Calculate statistics
    stats = calculate_network_stats(nodes, edges)

    # Build output data
    output_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "sources": ["documents", "flight_logs"],
            "statistics": stats
        },
        "nodes": list(nodes.values()),
        "edges": list(edges.values())
    }

    # Write output
    output_file = TRANSFORMED_DIR / "entity_network_full.json"
    logger.info(f"Writing output to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    # Print summary
    logger.info("\n" + "="*60)
    logger.info("NETWORK SUMMARY")
    logger.info("="*60)
    logger.info(f"Total nodes: {len(nodes)}")
    logger.info(f"Total edges: {len(edges)} ({len(edges)//2} unique)")
    logger.info(f"Average connections per node: {stats['average_connections_per_node']}")
    logger.info("\nTop 5 most connected entities:")
    for i, entity in enumerate(stats["top_10_most_connected"][:5], 1):
        logger.info(f"  {i}. {entity['name']}: {entity['connections']} connections")

    logger.info(f"\nOutput: {output_file}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
