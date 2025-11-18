#!/usr/bin/env python3
"""
Verification script for entity normalization

Compares before/after states and validates normalization quality
"""

import json
from pathlib import Path


def verify_normalization():
    """Run comprehensive verification checks"""

    project_root = Path("/Users/masa/Projects/Epstein")

    print("=" * 80)
    print("ENTITY NORMALIZATION VERIFICATION")
    print("=" * 80)

    # 1. Check key entities are present and consolidated
    print("\n1. KEY ENTITY VERIFICATION")
    print("-" * 80)

    entities_path = project_root / "data/md/entities/ENTITIES_INDEX.json"
    with open(entities_path, 'r') as f:
        entities_data = json.load(f)

    key_entities = {
        'Jeffrey Epstein': False,
        'Ghislaine Maxwell': False,
        'Bill Clinton': False,
        'Sarah Kellen': False,
        'Prince Andrew': False,
        'Alan Dershowitz': False
    }

    for entity in entities_data['entities']:
        name = entity['normalized_name']
        for key in key_entities:
            if key == name or key in name:
                key_entities[key] = True
                print(f"  ✓ {name}")

    missing = [k for k, v in key_entities.items() if not v]
    if missing:
        print(f"\n  ⚠️  Missing entities: {missing}")
    else:
        print("\n  ✓ All key entities found!")

    # 2. Check for remaining duplicated first names
    print("\n2. DUPLICATED FIRST NAME CHECK")
    print("-" * 80)

    duplicates = []
    for entity in entities_data['entities']:
        name = entity['normalized_name']
        words = name.split()
        if len(words) >= 2 and words[0] == words[1]:
            duplicates.append(name)

    if duplicates:
        print(f"  Found {len(duplicates)} duplicated first names:")
        for dup in duplicates:
            print(f"    - {dup}")
    else:
        print("  ✓ No duplicated first names found!")

    # 3. Check entity network
    print("\n3. ENTITY NETWORK VERIFICATION")
    print("-" * 80)

    network_path = project_root / "data/metadata/entity_network.json"
    with open(network_path, 'r') as f:
        network = json.load(f)

    print(f"  Total nodes: {len(network['nodes'])}")
    print(f"  Total edges: {len(network['edges'])}")

    # Find top connected entities
    top_entities = sorted(network['nodes'], key=lambda x: x.get('connections', 0), reverse=True)[:5]
    print(f"\n  Top 5 most connected entities:")
    for entity in top_entities:
        print(f"    - {entity['id']}: {entity.get('connections', 0)} connections")

    # Check for duplicate entities in network
    network_duplicates = []
    for node in network['nodes']:
        name = node['id']
        words = name.split()
        if len(words) >= 2 and words[0] == words[1]:
            network_duplicates.append(name)

    if network_duplicates:
        print(f"\n  ⚠️  Found {len(network_duplicates)} duplicated names in network:")
        for dup in network_duplicates:
            print(f"    - {dup}")
    else:
        print(f"\n  ✓ No duplicated names in network!")

    # 4. Check entity mappings
    print("\n4. ENTITY MAPPING VERIFICATION")
    print("-" * 80)

    mappings_path = project_root / "data/metadata/entity_name_mappings.json"
    with open(mappings_path, 'r') as f:
        mappings = json.load(f)

    print(f"  Total mappings: {len(mappings)}")
    print(f"  Unique canonical entities: {len(set(mappings.values()))}")

    # Check key entity mappings
    key_mappings = {
        'Epstein': [],
        'Maxwell': [],
        'Clinton': [],
        'Kellen': []
    }

    for orig, canon in mappings.items():
        for key in key_mappings:
            if key in orig:
                key_mappings[key].append(f"{orig} → {canon}")

    print(f"\n  Key entity mappings:")
    for key, maps in key_mappings.items():
        if maps:
            print(f"\n    {key} ({len(maps)} mappings):")
            for m in maps[:5]:
                print(f"      - {m}")
            if len(maps) > 5:
                print(f"      ... and {len(maps) - 5} more")

    # 5. Check flight logs
    print("\n5. FLIGHT LOG VERIFICATION")
    print("-" * 80)

    flights_path = project_root / "data/md/entities/flight_logs_by_flight.json"
    with open(flights_path, 'r') as f:
        flights_data = json.load(f)

    total_flights = flights_data['total_flights']
    flights = flights_data['flights']

    print(f"  Total flights: {total_flights}")

    # Check for duplicated names in flight passengers
    all_passengers = set()
    for flight in flights:
        all_passengers.update(flight.get('passengers', []))

    passenger_duplicates = []
    for passenger in all_passengers:
        words = passenger.split()
        if len(words) >= 2 and words[0] == words[1]:
            passenger_duplicates.append(passenger)

    if passenger_duplicates:
        print(f"\n  ⚠️  Found {len(passenger_duplicates)} passengers with duplicated first names:")
        for dup in passenger_duplicates[:10]:
            print(f"    - {dup}")
    else:
        print(f"\n  ✓ No duplicated passenger names!")

    print(f"\n  Total unique passengers: {len(all_passengers)}")

    # 6. Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    issues = []
    if missing:
        issues.append(f"{len(missing)} key entities missing")
    if duplicates:
        issues.append(f"{len(duplicates)} duplicated entity names")
    if network_duplicates:
        issues.append(f"{len(network_duplicates)} duplicated network nodes")
    if passenger_duplicates:
        issues.append(f"{len(passenger_duplicates)} duplicated passenger names")

    if issues:
        print(f"\n⚠️  Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅  ALL CHECKS PASSED!")
        print(f"\nNormalization Statistics:")
        print(f"  - {len(entities_data['entities'])} entities indexed")
        print(f"  - {len(mappings)} entity name mappings")
        print(f"  - {len(network['nodes'])} entities in network")
        print(f"  - {len(network['edges'])} relationship connections")
        print(f"  - {total_flights} flights with {len(all_passengers)} unique passengers")


if __name__ == "__main__":
    verify_normalization()
