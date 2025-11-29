#!/usr/bin/env python3
"""
Entity Relationship Graph Builder
Creates network graph from flight co-occurrences and contact book overlaps
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
MD_DIR = DATA_DIR / "md"
METADATA_DIR = DATA_DIR / "metadata"


@dataclass
class EntityNode:
    """Entity in the network"""

    name: str
    in_black_book: bool
    is_billionaire: bool
    flight_count: int
    categories: list[str]
    connections: set[str]  # Names of connected entities


@dataclass
class EntityEdge:
    """Connection between two entities"""

    entity1: str
    entity2: str
    weight: int  # Number of co-occurrences
    contexts: list[str]  # Where they appeared together


class EntityNetworkBuilder:
    """Build entity relationship graph"""

    def __init__(self):
        """Initialize builder"""
        self.nodes: dict[str, EntityNode] = {}
        self.edges: list[EntityEdge] = []
        self.flight_cooccurrences = defaultdict(lambda: defaultdict(int))

    def load_entities(self, entities_index_path: Path):
        """Load entities from index"""
        with open(entities_index_path) as f:
            data = json.load(f)

        print(f"Loading entities from {entities_index_path.name}...")

        # Create nodes for all entities
        if "entities" in data:
            for entity in data["entities"]:
                name = entity.get("name", "").strip()
                if not name:
                    continue

                self.nodes[name] = EntityNode(
                    name=name,
                    in_black_book=entity.get("in_black_book", False),
                    is_billionaire=entity.get("is_billionaire", False),
                    flight_count=entity.get("trips", 0),
                    categories=entity.get("categories", []),
                    connections=set(),
                )

        print(f"  Loaded {len(self.nodes)} entity nodes")

    def load_flight_logs(self, flight_logs_stats_path: Path):
        """Load flight logs and build co-occurrence network"""
        with open(flight_logs_stats_path) as f:
            data = json.load(f)

        print("\nBuilding co-occurrence network from flight logs...")

        flights_processed = 0

        # Process each flight
        if "flights" in data:
            for flight in data["flights"]:
                passengers = flight.get("passengers", [])

                # Skip if only one passenger
                if len(passengers) <= 1:
                    continue

                # Create edges for all passenger pairs on this flight
                for i, passenger1 in enumerate(passengers):
                    for passenger2 in passengers[i + 1 :]:
                        # Normalize names
                        p1 = passenger1.strip()
                        p2 = passenger2.strip()

                        if not p1 or not p2:
                            continue

                        # Record co-occurrence
                        self.flight_cooccurrences[p1][p2] += 1
                        self.flight_cooccurrences[p2][p1] += 1

                        # Add to connections
                        if p1 in self.nodes:
                            self.nodes[p1].connections.add(p2)
                        if p2 in self.nodes:
                            self.nodes[p2].connections.add(p1)

                flights_processed += 1

        print(f"  Processed {flights_processed} flights")
        print(f"  Found {len(self.flight_cooccurrences)} entities with connections")

    def build_edges(self, min_weight: int = 1):
        """Create edges from co-occurrences"""
        print(f"\nBuilding edges (minimum weight: {min_weight})...")

        processed_pairs = set()

        for entity1, connections in self.flight_cooccurrences.items():
            for entity2, weight in connections.items():
                # Skip if below threshold
                if weight < min_weight:
                    continue

                # Create unique pair identifier
                pair = tuple(sorted([entity1, entity2]))
                if pair in processed_pairs:
                    continue

                processed_pairs.add(pair)

                # Create edge
                self.edges.append(
                    EntityEdge(
                        entity1=entity1, entity2=entity2, weight=weight, contexts=["flight_log"]
                    )
                )

        print(f"  Created {len(self.edges)} edges")

    def export_graph(self, output_path: Path):
        """Export graph in JSON format for visualization"""
        # Convert to exportable format
        nodes_list = [
            {
                "id": node.name,
                "name": node.name,
                "in_black_book": node.in_black_book,
                "is_billionaire": node.is_billionaire,
                "flight_count": node.flight_count,
                "categories": node.categories,
                "connection_count": len(node.connections),
            }
            for node in self.nodes.values()
        ]

        edges_list = [
            {
                "source": edge.entity1,
                "target": edge.entity2,
                "weight": edge.weight,
                "contexts": edge.contexts,
            }
            for edge in self.edges
        ]

        graph_data = {
            "generated": "2025-11-16T23:40:00",
            "metadata": {
                "total_nodes": len(nodes_list),
                "total_edges": len(edges_list),
                "nodes_with_connections": sum(1 for n in nodes_list if n["connection_count"] > 0),
                "max_connections": max((n["connection_count"] for n in nodes_list), default=0),
            },
            "nodes": nodes_list,
            "edges": edges_list,
        }

        with open(output_path, "w") as f:
            json.dump(graph_data, f, indent=2)

        print(f"\n✓ Exported graph: {output_path}")
        return graph_data

    def generate_statistics(self) -> str:
        """Generate network statistics report"""
        # Calculate statistics
        total_nodes = len(self.nodes)
        nodes_with_connections = sum(1 for n in self.nodes.values() if len(n.connections) > 0)
        total_edges = len(self.edges)

        # Find most connected entities
        most_connected = sorted(
            self.nodes.values(), key=lambda n: len(n.connections), reverse=True
        )[:20]

        # Find strongest relationships
        strongest_edges = sorted(self.edges, key=lambda e: e.weight, reverse=True)[:20]

        # Build report
        report = [
            "=" * 70,
            "ENTITY NETWORK ANALYSIS",
            "=" * 70,
            "",
            "NETWORK STATISTICS:",
            "-" * 70,
            f"  Total entities: {total_nodes}",
            f"  Entities with connections: {nodes_with_connections} ({nodes_with_connections/total_nodes*100:.1f}%)",
            f"  Total connections: {total_edges}",
            f"  Average connections per entity: {total_edges*2/total_nodes:.1f}",
            "",
            "TOP 20 MOST CONNECTED ENTITIES:",
            "-" * 70,
        ]

        for entity in most_connected:
            connections_str = f"{len(entity.connections)} connections"
            flags = []
            if entity.is_billionaire:
                flags.append("💰 Billionaire")
            if entity.in_black_book:
                flags.append("📖 Black Book")
            if entity.flight_count > 0:
                flags.append(f"✈️ {entity.flight_count} flights")

            flags_str = ", ".join(flags) if flags else "No flags"
            report.append(f"  {entity.name:30s}: {connections_str:20s} ({flags_str})")

        report.extend(["", "TOP 20 STRONGEST RELATIONSHIPS (Most Co-Occurrences):", "-" * 70])

        for edge in strongest_edges:
            report.append(f"  {edge.entity1:25s} ↔ {edge.entity2:25s}: {edge.weight:3d} flights")

        return "\n".join(report)


def main():
    """Build entity relationship graph"""
    print("=" * 70)
    print("ENTITY RELATIONSHIP GRAPH BUILDER")
    print("=" * 70)

    builder = EntityNetworkBuilder()

    # Load data
    builder.load_entities(MD_DIR / "entities" / "ENTITIES_INDEX.json")
    builder.load_flight_logs(MD_DIR / "entities" / "flight_logs_stats.json")

    # Build network
    builder.build_edges(min_weight=1)

    # Export graph
    builder.export_graph(METADATA_DIR / "entity_network.json")

    # Generate statistics
    stats_report = builder.generate_statistics()
    stats_path = METADATA_DIR / "entity_network_stats.txt"
    stats_path.write_text(stats_report)

    print(f"✓ Saved statistics: {stats_path}")
    print("\n" + stats_report)

    print("\n" + "=" * 70)
    print("NETWORK GRAPH COMPLETE")
    print("=" * 70)
    print("\nGraph can be visualized using:")
    print("  - Gephi: Import entity_network.json")
    print("  - D3.js: Use JSON format directly")
    print("  - NetworkX: Load JSON and analyze programmatically")


if __name__ == "__main__":
    main()
