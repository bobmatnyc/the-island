"""
Network Service - Business logic for entity network operations

Design Decision: Centralized Network Graph Management
Rationale: All network graph filtering, traversal, and analysis
in one service for consistency and maintainability.

Handles:
- Network graph filtering (min connections, max nodes)
- Entity deduplication in network
- Graph traversal (shortest path, subgraphs)
- Network statistics
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
import sys

# Import entity filtering and disambiguation
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts/utils"))
from entity_filtering import EntityFilter

# Import disambiguator
sys.path.insert(0, str(Path(__file__).parent))
from entity_disambiguation import get_disambiguator


class NetworkService:
    """Service for network graph operations"""

    def __init__(self, data_path: Path):
        """Initialize network service

        Args:
            data_path: Path to data directory
        """
        self.data_path = data_path
        self.metadata_dir = data_path / "metadata"

        # Initialize filters
        self.entity_filter = EntityFilter()
        self.disambiguator = get_disambiguator()

        # Data cache
        self.network_data: Dict = {}

        # Load data
        self.load_data()

    def load_data(self):
        """Load network graph data"""
        network_path = self.metadata_dir / "entity_network.json"
        if network_path.exists():
            with open(network_path) as f:
                self.network_data = json.load(f)

    def get_network(
        self,
        min_connections: int = 0,
        max_nodes: int = 500,
        deduplicate: bool = True,
        entity_filter: Optional[str] = None
    ) -> Dict:
        """Get filtered network graph

        Args:
            min_connections: Minimum connections to include node
            max_nodes: Maximum nodes to return
            deduplicate: Apply name disambiguation
            entity_filter: Filter to specific entity and connections

        Returns:
            {
                "nodes": List of nodes,
                "edges": List of edges,
                "metadata": Graph metadata
            }
        """
        nodes = self.network_data.get("nodes", []).copy()
        edges = self.network_data.get("edges", []).copy()

        # Filter out generic entities
        nodes = [n for n in nodes if not self.entity_filter.is_generic(n.get("name", ""))]

        # Apply deduplication if requested
        if deduplicate:
            original_count = len(nodes)
            nodes = self.disambiguator.merge_duplicate_nodes(nodes)
            print(f"Deduplicated {original_count - len(nodes)} nodes ({original_count} -> {len(nodes)})")

        # Filter by minimum connections
        nodes = [
            n for n in nodes
            if n.get("connection_count", 0) >= min_connections
        ]

        # Filter by specific entity
        if entity_filter:
            # Find entity node
            entity_node = next((n for n in nodes if n.get("name") == entity_filter), None)
            if entity_node:
                # Get connected node IDs
                connected_ids = {entity_node["id"]}
                for edge in edges:
                    if edge["source"] == entity_node["id"]:
                        connected_ids.add(edge["target"])
                    elif edge["target"] == entity_node["id"]:
                        connected_ids.add(edge["source"])

                # Filter nodes
                nodes = [n for n in nodes if n["id"] in connected_ids]

        # Sort by connections and limit
        nodes.sort(key=lambda n: n.get("connection_count", 0), reverse=True)
        nodes = nodes[:max_nodes]

        # Get node IDs for edge filtering
        node_ids = {n["id"] for n in nodes}

        # Filter edges
        edges = [
            e for e in edges
            if e["source"] in node_ids and e["target"] in node_ids
        ]

        # Build node name mapping for edge deduplication
        if deduplicate:
            node_mapping = {n.get("id", ""): n.get("name", "") for n in nodes}
            edges = self.disambiguator.deduplicate_edges(edges, node_mapping)

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                **self.network_data.get("metadata", {}),
                "deduplicated": deduplicate,
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "filtered": {
                    "min_connections": min_connections,
                    "max_nodes": max_nodes,
                    "entity_filter": entity_filter
                }
            }
        }

    def find_shortest_path(self, entity_a: str, entity_b: str) -> Dict:
        """Find shortest path between two entities

        Args:
            entity_a: First entity name
            entity_b: Second entity name

        Returns:
            {
                "path": List of entity names in path,
                "edges": List of edges in path,
                "distance": Number of hops,
                "found": Whether path exists
            }
        """
        # Find entity nodes
        nodes = self.network_data.get("nodes", [])
        edges = self.network_data.get("edges", [])

        node_a = next((n for n in nodes if n.get("name") == entity_a), None)
        node_b = next((n for n in nodes if n.get("name") == entity_b), None)

        if not node_a or not node_b:
            return {
                "path": [],
                "edges": [],
                "distance": -1,
                "found": False,
                "error": "One or both entities not found in network"
            }

        # Build adjacency list
        adjacency = {}
        edge_map = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]

            if source not in adjacency:
                adjacency[source] = []
            if target not in adjacency:
                adjacency[target] = []

            adjacency[source].append(target)
            adjacency[target].append(source)

            edge_map[(source, target)] = edge
            edge_map[(target, source)] = edge

        # BFS to find shortest path
        from collections import deque

        queue = deque([(node_a["id"], [node_a["id"]])])
        visited = {node_a["id"]}

        while queue:
            current_id, path = queue.popleft()

            if current_id == node_b["id"]:
                # Found path - convert to entity names
                path_nodes = [next(n for n in nodes if n["id"] == nid) for nid in path]
                path_names = [n["name"] for n in path_nodes]

                # Get edges in path
                path_edges = []
                for i in range(len(path) - 1):
                    edge = edge_map.get((path[i], path[i+1]))
                    if edge:
                        path_edges.append(edge)

                return {
                    "path": path_names,
                    "edges": path_edges,
                    "distance": len(path) - 1,
                    "found": True
                }

            # Explore neighbors
            for neighbor_id in adjacency.get(current_id, []):
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))

        return {
            "path": [],
            "edges": [],
            "distance": -1,
            "found": False,
            "error": "No path exists between entities"
        }

    def get_entity_subgraph(
        self,
        entity_name: str,
        max_hops: int = 2,
        min_strength: int = 1
    ) -> Dict:
        """Get subgraph centered on entity

        Args:
            entity_name: Entity name
            max_hops: Maximum degrees of separation
            min_strength: Minimum connection strength

        Returns:
            {
                "center": Center entity,
                "nodes": List of nodes in subgraph,
                "edges": List of edges in subgraph
            }
        """
        # Find entity node
        nodes = self.network_data.get("nodes", [])
        edges = self.network_data.get("edges", [])

        entity_node = next((n for n in nodes if n.get("name") == entity_name), None)

        if not entity_node:
            return {
                "center": None,
                "nodes": [],
                "edges": [],
                "error": "Entity not found in network"
            }

        # BFS to find nodes within max_hops
        from collections import deque

        visited = {entity_node["id"]: 0}  # node_id -> hop distance
        queue = deque([(entity_node["id"], 0)])

        while queue:
            current_id, distance = queue.popleft()

            if distance >= max_hops:
                continue

            # Find connected edges
            for edge in edges:
                if edge.get("flight_count", 0) < min_strength:
                    continue

                neighbor_id = None
                if edge["source"] == current_id:
                    neighbor_id = edge["target"]
                elif edge["target"] == current_id:
                    neighbor_id = edge["source"]

                if neighbor_id and neighbor_id not in visited:
                    visited[neighbor_id] = distance + 1
                    queue.append((neighbor_id, distance + 1))

        # Get nodes and edges in subgraph
        subgraph_nodes = [n for n in nodes if n["id"] in visited]
        subgraph_edges = [
            e for e in edges
            if e["source"] in visited and e["target"] in visited
            and e.get("flight_count", 0) >= min_strength
        ]

        return {
            "center": entity_node,
            "nodes": subgraph_nodes,
            "edges": subgraph_edges,
            "metadata": {
                "max_hops": max_hops,
                "min_strength": min_strength,
                "total_nodes": len(subgraph_nodes),
                "total_edges": len(subgraph_edges)
            }
        }

    def get_statistics(self) -> Dict:
        """Get network statistics

        Returns:
            {
                "total_nodes": Total nodes,
                "total_edges": Total edges,
                "density": Network density,
                "most_connected": Top connected entities
            }
        """
        nodes = self.network_data.get("nodes", [])
        edges = self.network_data.get("edges", [])

        # Network density (actual edges / possible edges)
        n = len(nodes)
        possible_edges = n * (n - 1) / 2 if n > 1 else 0
        density = len(edges) / possible_edges if possible_edges > 0 else 0

        # Most connected entities
        sorted_nodes = sorted(nodes, key=lambda n: n.get("connection_count", 0), reverse=True)
        most_connected = [
            {
                "name": n.get("name"),
                "connections": n.get("connection_count", 0)
            }
            for n in sorted_nodes[:10]
        ]

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "density": round(density, 4),
            "most_connected": most_connected
        }
