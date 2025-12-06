#!/usr/bin/env python3
"""
Calculate real connection counts for organizations and locations.

Currently the backend hardcodes connection_count=0 for orgs/locations.
This script calculates actual connection counts from entity_network.json
and adds them to entity_organizations.json and entity_locations.json.

Design Decision: Use entity_network.json as source of truth for connection counts.
The network file contains edges between entities, which represent real relationships.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "metadata"

NETWORK_FILE = DATA_DIR / "entity_network.json"
ORGS_FILE = DATA_DIR / "entity_organizations.json"
LOCS_FILE = DATA_DIR / "entity_locations.json"


def calculate_connection_counts():
    """
    Calculate connection counts from entity_network.json.

    Returns: dict mapping entity_id -> connection_count
    """
    print("📊 Calculating connection counts from network data...")

    with open(NETWORK_FILE, 'r', encoding='utf-8') as f:
        network_data = json.load(f)

    # Method 1: Use nodes (they already have connection_count)
    nodes = network_data.get('nodes', [])
    node_connections = {}

    for node_data in nodes:
        if isinstance(node_data, dict):
            node_id = node_data.get('id', '')
            if node_id:
                node_connections[node_id] = node_data.get('connection_count', 0)
            # Also index by name (case-insensitive)
            name = node_data.get('name', '')
            if name:
                node_connections[name.lower()] = node_data.get('connection_count', 0)

    # Method 2: Count from edges (more accurate)
    edges = network_data.get('edges', [])
    edge_connections = defaultdict(int)

    for edge in edges:
        source = edge.get('source', '')
        target = edge.get('target', '')
        if source and target:
            edge_connections[source] += 1
            edge_connections[target] += 1

    print(f"  ✓ Nodes with connections: {len(node_connections)}")
    print(f"  ✓ Edges counted: {len(edges)}")
    print(f"  ✓ Unique entities in edges: {len(edge_connections)}")

    # Merge both methods (prefer edge counts as they're more accurate)
    connection_counts = {}
    for entity_id, count in edge_connections.items():
        connection_counts[entity_id] = count
        connection_counts[entity_id.lower()] = count  # Also index lowercase

    return connection_counts


def update_organizations(connection_counts):
    """Add connection counts to organizations."""
    print("\n🏢 Updating organizations with connection counts...")

    with open(ORGS_FILE, 'r', encoding='utf-8') as f:
        orgs_data = json.load(f)

    updated = 0
    total_connections = 0

    for entity_key, entity_data in orgs_data['entities'].items():
        name = entity_data.get('name', entity_key)

        # Try to find connection count by ID or name (case-insensitive)
        count = (
            connection_counts.get(entity_key, 0) or
            connection_counts.get(entity_key.lower(), 0) or
            connection_counts.get(name, 0) or
            connection_counts.get(name.lower(), 0)
        )

        if count > 0:
            entity_data['connection_count'] = count
            updated += 1
            total_connections += count

    orgs_data['metadata']['last_updated'] = datetime.now().isoformat()
    orgs_data['metadata']['connections_calculated'] = datetime.now().isoformat()

    with open(ORGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orgs_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Updated {updated}/{len(orgs_data['entities'])} organizations")
    print(f"  ✓ Total connections: {total_connections}")
    print(f"  ✓ Avg connections: {total_connections/max(updated, 1):.1f}")

    return updated


def update_locations(connection_counts):
    """Add connection counts to locations."""
    print("\n📍 Updating locations with connection counts...")

    with open(LOCS_FILE, 'r', encoding='utf-8') as f:
        locs_data = json.load(f)

    updated = 0
    total_connections = 0

    for entity_key, entity_data in locs_data['entities'].items():
        name = entity_data.get('name', entity_key)

        # Try to find connection count by ID or name (case-insensitive)
        count = (
            connection_counts.get(entity_key, 0) or
            connection_counts.get(entity_key.lower(), 0) or
            connection_counts.get(name, 0) or
            connection_counts.get(name.lower(), 0)
        )

        if count > 0:
            entity_data['connection_count'] = count
            updated += 1
            total_connections += count

    locs_data['metadata']['last_updated'] = datetime.now().isoformat()
    locs_data['metadata']['connections_calculated'] = datetime.now().isoformat()

    with open(LOCS_FILE, 'w', encoding='utf-8') as f:
        json.dump(locs_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Updated {updated}/{len(locs_data['entities'])} locations")
    print(f"  ✓ Total connections: {total_connections}")
    print(f"  ✓ Avg connections: {total_connections/max(updated, 1):.1f}")

    return updated


def main():
    """Run connection count calculation."""
    print("\n🔗 Entity Connection Count Calculator")
    print("="*60)

    # Calculate counts from network
    connection_counts = calculate_connection_counts()

    # Update organizations
    orgs_updated = update_organizations(connection_counts)

    # Update locations
    locs_updated = update_locations(connection_counts)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Organizations updated: {orgs_updated}")
    print(f"✓ Locations updated: {locs_updated}")
    print(f"✓ Total entities updated: {orgs_updated + locs_updated}")
    print("\n🎉 Connection counts calculated and saved!")


if __name__ == "__main__":
    main()
