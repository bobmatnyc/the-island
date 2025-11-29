#!/usr/bin/env python3
"""
Task 2: Merge Duplicate "Epstein, Jeffrey" Entities

Consolidates all "Epstein, Jeffrey" entries into a single canonical entity.
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
ENTITY_NETWORK = PROJECT_ROOT / "data/metadata/entity_network.json"
SEMANTIC_INDEX = PROJECT_ROOT / "data/metadata/semantic_index.json"
REPORT_FILE = PROJECT_ROOT / "data/metadata/epstein_merge_report.txt"


def load_json(filepath):
    """Load JSON file"""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    """Save JSON file with formatting"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_epstein_entities():
    """Find and merge all Epstein, Jeffrey entities"""
    print("Loading ENTITIES_INDEX.json...")
    entities_data = load_json(ENTITIES_INDEX)
    entities = entities_data.get("entities", [])

    # Find all Epstein entities
    epstein_entities = []
    epstein_indices = []

    for i, entity in enumerate(entities):
        name = entity.get("name", "")
        normalized = entity.get("normalized_name", "")

        # Match "Epstein, Jeffrey" or "Jeffrey Epstein" or variations
        if ("epstein" in name.lower() and "jeffrey" in name.lower()) or (
            "epstein" in normalized.lower() and "jeffrey" in normalized.lower()
        ):
            epstein_entities.append(entity)
            epstein_indices.append(i)
            print(f"Found Epstein entity #{len(epstein_entities)}: {name}")

    if len(epstein_entities) <= 1:
        print(f"\nOnly {len(epstein_entities)} Epstein entity found. No merge needed.")
        return

    print(f"\nFound {len(epstein_entities)} Epstein entities to merge.")

    # Merge strategy
    merged_entity = {
        "name": "Epstein, Jeffrey",
        "normalized_name": "Epstein, Jeffrey",
        "name_variations": [],
        "sources": [],
        "categories": [],
        "contact_info": {},
        "flights": 0,
        "is_billionaire": False,
        "in_black_book": False,
        "organizations": [],
        "merged_from": [],
        "documents": [],
        "top_connections": [],
        "bio": "",
        "black_book_page": None,
    }

    # Combine data from all duplicates
    for entity in epstein_entities:
        # Name variations
        if entity.get("name"):
            merged_entity["name_variations"].append(entity["name"])
        for variation in entity.get("name_variations", []):
            if variation not in merged_entity["name_variations"]:
                merged_entity["name_variations"].append(variation)

        # Sources
        for source in entity.get("sources", []):
            if source not in merged_entity["sources"]:
                merged_entity["sources"].append(source)

        # Categories
        for cat in entity.get("categories", []):
            if cat not in merged_entity["categories"]:
                merged_entity["categories"].append(cat)

        # Contact info - merge all fields
        for key, value in entity.get("contact_info", {}).items():
            if key not in merged_entity["contact_info"]:
                merged_entity["contact_info"][key] = value
            elif isinstance(value, list):
                # Combine lists
                existing = merged_entity["contact_info"][key]
                if isinstance(existing, list):
                    merged_entity["contact_info"][key] = list(set(existing + value))

        # Flight count
        merged_entity["flights"] += entity.get("flights", 0)

        # Boolean flags - OR logic
        merged_entity["is_billionaire"] = merged_entity["is_billionaire"] or entity.get(
            "is_billionaire", False
        )
        merged_entity["in_black_book"] = merged_entity["in_black_book"] or entity.get(
            "in_black_book", False
        )

        # Organizations
        for org in entity.get("organizations", []):
            if org not in merged_entity["organizations"]:
                merged_entity["organizations"].append(org)

        # Documents
        for doc in entity.get("documents", []):
            if doc not in merged_entity["documents"]:
                merged_entity["documents"].append(doc)

        # Top connections - will re-sort later
        merged_entity["top_connections"].extend(entity.get("top_connections", []))

        # Bio - keep longest
        entity_bio = entity.get("bio", "").strip()
        if len(entity_bio) > len(merged_entity["bio"]):
            merged_entity["bio"] = entity_bio

        # Black book page - keep first non-null
        if entity.get("black_book_page") and not merged_entity["black_book_page"]:
            merged_entity["black_book_page"] = entity["black_book_page"]

        # Track merged entities
        merged_entity["merged_from"].append(entity.get("name", "Unknown"))

    # Consolidate and re-sort top_connections
    connection_weights = defaultdict(float)
    for conn in merged_entity["top_connections"]:
        if isinstance(conn, dict):
            name = conn.get("name", "")
            weight = conn.get("weight", 0)
            connection_weights[name] = max(connection_weights[name], weight)

    merged_entity["top_connections"] = [
        {"name": name, "weight": weight}
        for name, weight in sorted(connection_weights.items(), key=lambda x: x[1], reverse=True)
    ][
        :10
    ]  # Keep top 10

    # Remove duplicates from name_variations
    merged_entity["name_variations"] = list(set(merged_entity["name_variations"]))

    # Remove old entities and add merged one
    # Remove from highest index to lowest to avoid index shifting
    for idx in sorted(epstein_indices, reverse=True):
        del entities[idx]

    # Add merged entity at beginning
    entities.insert(0, merged_entity)

    # Update total count
    entities_data["total_entities"] = len(entities)
    entities_data["entities"] = entities

    print("\nSaving updated ENTITIES_INDEX.json...")
    save_json(ENTITIES_INDEX, entities_data)

    # Update entity_network.json
    print("Updating entity_network.json...")
    try:
        network_data = load_json(ENTITY_NETWORK)

        # Find all Epstein nodes
        epstein_node_ids = []
        for node in network_data.get("nodes", []):
            name = node.get("id", "")
            if "epstein" in name.lower() and "jeffrey" in name.lower():
                epstein_node_ids.append(node["id"])

        # Update all nodes to use canonical name
        canonical_id = "Epstein, Jeffrey"
        nodes_updated = []
        for node in network_data.get("nodes", []):
            if node["id"] in epstein_node_ids:
                if node["id"] != canonical_id:
                    # Skip non-canonical nodes
                    continue
                nodes_updated.append(node)
            else:
                nodes_updated.append(node)

        # Update edges to use canonical ID
        edges_updated = []
        for edge in network_data.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")

            # Replace with canonical name
            if source in epstein_node_ids:
                edge["source"] = canonical_id
            if target in epstein_node_ids:
                edge["target"] = canonical_id

            edges_updated.append(edge)

        network_data["nodes"] = nodes_updated
        network_data["edges"] = edges_updated

        save_json(ENTITY_NETWORK, network_data)
        print(f"Network updated: {len(epstein_node_ids)} Epstein nodes consolidated to 1")
    except Exception as e:
        print(f"Warning: Could not update network: {e}")

    # Generate report
    report_lines = [
        "=" * 80,
        "EPSTEIN ENTITY MERGE REPORT",
        "=" * 80,
        f"Generated: {datetime.now().isoformat()}",
        "",
        "MERGE SUMMARY",
        "-" * 80,
        f"Entities merged: {len(epstein_entities)}",
        "Canonical name: Epstein, Jeffrey",
        "",
        "MERGED ENTITIES:",
        "-" * 80,
    ]

    for i, entity in enumerate(epstein_entities, 1):
        report_lines.append(f"{i}. {entity.get('name', 'Unknown')}")
        report_lines.append(f"   - Sources: {', '.join(entity.get('sources', []))}")
        report_lines.append(f"   - Flights: {entity.get('flights', 0)}")
        report_lines.append(f"   - In Black Book: {entity.get('in_black_book', False)}")
        report_lines.append(f"   - Is Billionaire: {entity.get('is_billionaire', False)}")

    report_lines.extend(
        [
            "",
            "CONSOLIDATED ENTITY:",
            "-" * 80,
            f"Name: {merged_entity['name']}",
            f"Name variations: {len(merged_entity['name_variations'])} total",
            f"  - {', '.join(merged_entity['name_variations'][:5])}",
            f"Sources: {', '.join(merged_entity['sources'])}",
            f"Total flights: {merged_entity['flights']}",
            f"In Black Book: {merged_entity['in_black_book']}",
            f"Is Billionaire: {merged_entity['is_billionaire']}",
            f"Categories: {', '.join(merged_entity['categories']) if merged_entity['categories'] else 'None'}",
            f"Top connections: {len(merged_entity['top_connections'])}",
            "",
            "TOP CONNECTIONS:",
            "-" * 80,
        ]
    )

    for conn in merged_entity["top_connections"][:10]:
        report_lines.append(f"  - {conn['name']}: {conn['weight']:.2f}")

    report_lines.append("\n" + "=" * 80)

    report_text = "\n".join(report_lines)

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to: {REPORT_FILE}")

    # Verify only one Epstein remains
    epstein_count = sum(
        1
        for e in entities
        if "epstein" in e.get("name", "").lower() and "jeffrey" in e.get("name", "").lower()
    )
    print(f"\n✓ Verification: {epstein_count} 'Epstein, Jeffrey' entity in index")

    if epstein_count == 1:
        print("✓ SUCCESS: Merge completed successfully!")
    else:
        print(f"✗ WARNING: Expected 1 Epstein entity, found {epstein_count}")


if __name__ == "__main__":
    merge_epstein_entities()
