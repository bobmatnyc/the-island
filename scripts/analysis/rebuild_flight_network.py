#!/usr/bin/env python3
"""
Rebuild flight network from raw flight logs
Groups passengers by flight to find co-occurrences
"""

import json
from pathlib import Path
from collections import defaultdict
import re

PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw/entities"
MD_DIR = DATA_DIR / "md/entities"
METADATA_DIR = DATA_DIR / "metadata"

def parse_flight_logs_for_network():
    """
    Parse flight logs and group passengers by flight
    Each flight is identified by date + tail number + route
    """

    raw_text = RAW_DIR / "flight_logs_raw.txt"

    print(f"Reading flight logs from {raw_text.name}...")

    with open(raw_text, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Group by flight
    flights = defaultdict(lambda: {
        "passengers": set(),
        "date": "",
        "tail": "",
        "route": ""
    })

    print("Parsing flight records...")

    for line in lines[2:]:  # Skip headers
        if not line.strip() or "Flight Log" not in line:
            continue

        # Extract date
        date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
        if not date_match:
            continue
        date = date_match.group(1)

        # Extract tail number
        tail_match = re.search(r'(N\d{3,5}[A-Z]{0,2})', line)
        tail = tail_match.group(1) if tail_match else "UNKNOWN"

        # Extract airports
        airport_matches = re.findall(r'\b([A-Z]{3})\b', line)
        dep = airport_matches[0] if len(airport_matches) > 0 else ""
        arr = airport_matches[1] if len(airport_matches) > 1 else ""
        route = f"{dep}-{arr}" if dep and arr else "UNKNOWN"

        # Extract passenger name
        # Try main pattern first
        name_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+[A-Z?]{1,3}\s+(?:Yes|No)\s+Flight Log', line)

        if name_match:
            full_name = name_match.group(1).strip()
        else:
            # Try alternate pattern for "Female (1)" etc
            alt_match = re.search(r'((?:Female|Male|Nanny)\s*\(\d+\))', line)
            if alt_match:
                full_name = alt_match.group(1).strip()
            else:
                # Try another pattern
                cols_match = re.search(r'([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+\2,\s+\1\s+\1\s+\2', line)
                if cols_match:
                    full_name = f"{cols_match.group(1)} {cols_match.group(2)}"
                else:
                    continue

        if not full_name or len(full_name) < 2:
            continue

        # Create unique flight identifier
        flight_id = f"{date}_{tail}_{route}"

        flights[flight_id]["passengers"].add(full_name)
        flights[flight_id]["date"] = date
        flights[flight_id]["tail"] = tail
        flights[flight_id]["route"] = route

    print(f"  Parsed {len(flights)} unique flights")

    # Convert to list format
    flights_list = []
    for flight_id, data in flights.items():
        flights_list.append({
            "id": flight_id,
            "date": data["date"],
            "tail_number": data["tail"],
            "route": data["route"],
            "passengers": list(data["passengers"]),
            "passenger_count": len(data["passengers"])
        })

    # Save flights with passengers
    flights_output = MD_DIR / "flight_logs_by_flight.json"
    with open(flights_output, 'w') as f:
        json.dump({
            "total_flights": len(flights_list),
            "flights": flights_list
        }, f, indent=2)

    print(f"✓ Saved flights with passengers: {flights_output}")

    return flights_list

def build_cooccurrence_network(flights_list):
    """Build co-occurrence network from flights"""

    print("\nBuilding co-occurrence network...")

    cooccurrences = defaultdict(lambda: defaultdict(int))
    connections = defaultdict(set)

    flights_with_multiple = 0

    for flight in flights_list:
        passengers = flight["passengers"]

        # Only process flights with multiple passengers
        if len(passengers) <= 1:
            continue

        flights_with_multiple += 1

        # Create edges for all passenger pairs
        for i, p1 in enumerate(passengers):
            for p2 in passengers[i+1:]:
                cooccurrences[p1][p2] += 1
                cooccurrences[p2][p1] += 1
                connections[p1].add(p2)
                connections[p2].add(p1)

    print(f"  Processed {flights_with_multiple} flights with multiple passengers")
    print(f"  Found {len(connections)} passengers with co-occurrences")

    # Create edges
    edges = []
    processed_pairs = set()

    for p1, others in cooccurrences.items():
        for p2, count in others.items():
            pair = tuple(sorted([p1, p2]))
            if pair in processed_pairs:
                continue

            processed_pairs.add(pair)
            edges.append({
                "source": p1,
                "target": p2,
                "weight": count,
                "contexts": ["flight_log"]
            })

    print(f"  Created {len(edges)} edges")

    return edges, connections

def export_network_graph(edges, connections):
    """Export network graph with entity data"""

    print("\nExporting network graph...")

    # Load entity index
    entities_index = MD_DIR / "ENTITIES_INDEX.json"
    with open(entities_index) as f:
        entities_data = json.load(f)

    # Create lookup
    entity_lookup = {}
    if "entities" in entities_data:
        for entity in entities_data["entities"]:
            name = entity.get("name", "").strip()
            if name:
                entity_lookup[name] = entity

    # Create nodes
    nodes = []
    for passenger, connected_to in connections.items():
        # Get entity data if available
        entity_data = entity_lookup.get(passenger, {})

        nodes.append({
            "id": passenger,
            "name": passenger,
            "in_black_book": entity_data.get("in_black_book", False),
            "is_billionaire": entity_data.get("is_billionaire", False),
            "flight_count": entity_data.get("trips", 0),
            "categories": entity_data.get("categories", []),
            "connection_count": len(connected_to)
        })

    # Save graph
    graph_output = METADATA_DIR / "entity_network.json"
    graph_data = {
        "generated": "2025-11-16T23:50:00",
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "max_connections": max((n["connection_count"] for n in nodes), default=0)
        },
        "nodes": nodes,
        "edges": edges
    }

    with open(graph_output, 'w') as f:
        json.dump(graph_data, f, indent=2)

    print(f"✓ Saved network graph: {graph_output}")

    return graph_data

def generate_network_stats(graph_data):
    """Generate network statistics"""

    nodes = graph_data["nodes"]
    edges = graph_data["edges"]

    # Sort by connections
    most_connected = sorted(nodes, key=lambda n: n["connection_count"], reverse=True)[:20]

    # Sort edges by weight
    strongest_edges = sorted(edges, key=lambda e: e["weight"], reverse=True)[:20]

    # Generate report
    report = [
        "=" * 70,
        "ENTITY RELATIONSHIP NETWORK (Flight Co-Occurrences)",
        "=" * 70,
        "",
        "NETWORK STATISTICS:",
        "-" * 70,
        f"  Total entities: {len(nodes)}",
        f"  Total connections: {len(edges)}",
        f"  Average connections per entity: {len(edges)*2/len(nodes):.1f}",
        "",
        "TOP 20 MOST CONNECTED ENTITIES:",
        "-" * 70
    ]

    for entity in most_connected:
        flags = []
        if entity["is_billionaire"]:
            flags.append("💰")
        if entity["in_black_book"]:
            flags.append("📖")
        if entity["flight_count"] > 50:
            flags.append(f"✈️{entity['flight_count']}")

        flags_str = " ".join(flags) if flags else ""
        report.append(f"  {entity['name']:35s}: {entity['connection_count']:3d} connections {flags_str}")

    report.extend([
        "",
        "TOP 20 STRONGEST RELATIONSHIPS:",
        "-" * 70
    ])

    for edge in strongest_edges:
        report.append(f"  {edge['source']:30s} ↔ {edge['target']:30s}: {edge['weight']:3d} flights together")

    report_text = "\n".join(report)

    # Save report
    report_path = METADATA_DIR / "entity_network_stats.txt"
    report_path.write_text(report_text)

    print(f"✓ Saved network stats: {report_path}")
    print("\n" + report_text)

def main():
    """Rebuild flight network"""
    print("=" * 70)
    print("FLIGHT NETWORK REBUILD")
    print("=" * 70)

    flights_list = parse_flight_logs_for_network()
    edges, connections = build_cooccurrence_network(flights_list)
    graph_data = export_network_graph(edges, connections)
    generate_network_stats(graph_data)

    print("\n" + "=" * 70)
    print("NETWORK REBUILD COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
