#!/usr/bin/env python3
"""
Build Knowledge Graph from Entity Network
Converts existing entity network into NetworkX graph with rich metadata
"""

import json
from datetime import datetime
from pathlib import Path

import networkx as nx


PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
METADATA_DIR = DATA_DIR / "metadata"


def build_knowledge_graph():
    """Build NetworkX knowledge graph from entity data"""

    print("Building Knowledge Graph...")

    # Initialize graph
    G = nx.Graph()

    # Load data
    with open(METADATA_DIR / "entity_network.json") as f:
        network = json.load(f)

    with open(METADATA_DIR / "entity_statistics.json") as f:
        stats = json.load(f).get("statistics", {})

    # Add entity nodes
    print(f"Adding {len(network['nodes'])} entity nodes...")
    for node in network["nodes"]:
        entity_name = node["id"]
        entity_stats = stats.get(entity_name, {})

        G.add_node(
            entity_name,
            node_type="person",  # Could extend to organization, location
            is_billionaire=node.get("is_billionaire", False),
            in_black_book=node.get("in_black_book", False),
            flight_count=node.get("flight_count", 0),
            connection_count=node.get("connection_count", 0),
            total_documents=entity_stats.get("total_documents", 0),
            sources=entity_stats.get("sources", []),
            categories=entity_stats.get("categories", []),
            aliases=entity_stats.get("name_variations", [entity_name]),
        )

    # Add relationships (edges)
    print(f"Adding {len(network['edges'])} relationships...")
    for edge in network["edges"]:
        G.add_edge(
            edge["source"],
            edge["target"],
            relationship="flew_with",
            weight=edge.get("weight", 1),
            flights_together=edge.get("weight", 1),
            source="flight_logs",
        )

    # Calculate graph metrics
    print("Calculating graph metrics...")

    # Degree centrality
    degree_cent = nx.degree_centrality(G)
    for node, centrality in degree_cent.items():
        G.nodes[node]["degree_centrality"] = centrality

    # Betweenness centrality (for nodes with connections)
    if len(G.edges()) > 0:
        between_cent = nx.betweenness_centrality(G)
        for node, centrality in between_cent.items():
            G.nodes[node]["betweenness_centrality"] = centrality

    # Connected components
    components = list(nx.connected_components(G))
    for i, component in enumerate(components):
        for node in component:
            G.nodes[node]["component"] = i
            G.nodes[node]["component_size"] = len(component)

    # Export graph
    output_file = METADATA_DIR / "knowledge_graph.json"

    # Convert to JSON-serializable format
    graph_data = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "total_nodes": G.number_of_nodes(),
            "total_edges": G.number_of_edges(),
            "components": len(components),
            "largest_component": max(len(c) for c in components) if components else 0,
        },
        "nodes": [
            {"id": node, **{k: v for k, v in data.items() if not k.startswith("_")}}
            for node, data in G.nodes(data=True)
        ],
        "edges": [
            {"source": u, "target": v, **{k: v for k, v in data.items() if not k.startswith("_")}}
            for u, v, data in G.edges(data=True)
        ],
    }

    with open(output_file, "w") as f:
        json.dump(graph_data, f, indent=2)

    print("\n✅ Knowledge Graph created:")
    print(f"   Nodes: {G.number_of_nodes()}")
    print(f"   Edges: {G.number_of_edges()}")
    print(f"   Components: {len(components)}")
    print(f"   Output: {output_file}")

    # Print top entities by centrality
    print("\n📊 Top 10 by Degree Centrality:")
    top_degree = sorted(degree_cent.items(), key=lambda x: x[1], reverse=True)[:10]
    for entity, cent in top_degree:
        print(f"   {entity}: {cent:.4f}")

    return G


if __name__ == "__main__":
    build_knowledge_graph()
