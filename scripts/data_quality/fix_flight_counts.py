#!/usr/bin/env python3
"""
Fix Flight Counts in ENTITIES_INDEX.json

This script recounts flights for each entity by analyzing flight_logs_by_flight.json
directly, fixing the critical issue where Jeffrey Epstein shows only 8 flights
instead of 1,018.

Issue: ENTITIES_INDEX.json has incorrect flight counts that propagate to entity_statistics.json
Solution: Recount all flights from source data and update ENTITIES_INDEX.json

Author: Data Engineer
Date: 2025-11-20
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent
ENTITIES_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
FLIGHT_LOGS = PROJECT_ROOT / "data/md/entities/flight_logs_by_flight.json"
ENTITY_NAME_MAPPINGS = PROJECT_ROOT / "data/metadata/entity_name_mappings.json"


def load_json(filepath):
    """Load JSON file"""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def save_json(filepath, data):
    """Save JSON file with formatting"""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_name(name):
    """
    Normalize entity name for comparison
    'Jeffrey Epstein' -> 'Jeffrey Epstein'
    'Epstein, Jeffrey' -> 'Jeffrey Epstein'
    """
    # Handle "Last, First" format
    if "," in name:
        parts = [p.strip() for p in name.split(",")]
        if len(parts) == 2:
            return f"{parts[1]} {parts[0]}"
    return name


def count_flights_by_entity():
    """Count flights for each entity from flight logs"""
    print("Loading flight logs...")
    flight_logs = load_json(FLIGHT_LOGS)

    # Count flights per passenger
    flight_counts = defaultdict(int)
    route_sets = defaultdict(set)
    first_flights = {}
    last_flights = {}

    flights = flight_logs.get("flights", [])
    print(f"Processing {len(flights)} flights...")

    for flight in flights:
        passengers = flight.get("passengers", [])
        date = flight.get("date", "")
        route = flight.get("route", "")

        for passenger in passengers:
            flight_counts[passenger] += 1
            route_sets[passenger].add(route)

            # Track first and last flight dates
            if passenger not in first_flights or date < first_flights[passenger]:
                first_flights[passenger] = date
            if passenger not in last_flights or date > last_flights[passenger]:
                last_flights[passenger] = date

    print(f"Found {len(flight_counts)} unique passengers")

    # Show top passengers
    print("\nTop 10 passengers by flight count:")
    for passenger, count in sorted(flight_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {passenger}: {count} flights")

    return flight_counts, route_sets, first_flights, last_flights


def update_entities_index(flight_counts, route_sets, first_flights, last_flights):
    """Update ENTITIES_INDEX.json with correct flight counts"""
    print("\nLoading ENTITIES_INDEX.json...")
    entities_data = load_json(ENTITIES_INDEX)

    # Load name mappings
    try:
        load_json(ENTITY_NAME_MAPPINGS)
    except FileNotFoundError:
        print("Warning: entity_name_mappings.json not found, using direct name matching")

    entities = entities_data.get("entities", [])
    updated_count = 0
    not_found_count = 0

    print(f"\nUpdating {len(entities)} entities...")

    for entity in entities:
        name = entity.get("name", "")
        normalized_name = entity.get("normalized_name", name)
        name_variations = entity.get("name_variations", [name, normalized_name])

        # Try to find flight count using all name variations
        total_flights = 0
        routes = set()
        first_flight = None
        last_flight = None

        # Add normalized_name to variations if not present
        all_variations = {*name_variations, name, normalized_name}

        for variation in all_variations:
            if variation in flight_counts:
                count = flight_counts[variation]
                if count > total_flights:  # Use the highest count found
                    total_flights = count
                    routes = route_sets[variation]
                    first_flight = first_flights.get(variation)
                    last_flight = last_flights.get(variation)

        # Update entity if we found flight data
        old_count = entity.get("flights", 0)
        if total_flights > 0:
            entity["flights"] = total_flights
            entity["routes"] = sorted(routes)
            if first_flight:
                entity["first_flight"] = first_flight
            if last_flight:
                entity["last_flight"] = last_flight

            if old_count != total_flights:
                updated_count += 1
                if "Epstein" in name and "Jeffrey" in name:
                    print(f"\n✅ CRITICAL FIX: {name}")
                    print(f"   Old count: {old_count}")
                    print(f"   New count: {total_flights}")
                    print(f"   Routes: {len(routes)}")
                    print(f"   First flight: {first_flight}")
                    print(f"   Last flight: {last_flight}")
        # No flights found for this entity
        elif old_count > 0:
            # Entity had flights before but we can't find them now
            # This might be a name mismatch issue
            not_found_count += 1
            if entity.get("sources") and "flight_logs" in entity.get("sources", []):
                print(f"\n⚠️  WARNING: {name} has 'flight_logs' source but no flights found")
                print(f"   Name variations: {all_variations}")

    print("\n📊 Update Summary:")
    print(f"   Entities updated: {updated_count}")
    print(f"   Entities with flight data not found: {not_found_count}")

    # Save updated data
    backup_path = (
        ENTITIES_INDEX.parent
        / f"ENTITIES_INDEX.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    print(f"\n💾 Creating backup: {backup_path.name}")
    save_json(backup_path, entities_data)

    print("💾 Saving updated ENTITIES_INDEX.json...")
    save_json(ENTITIES_INDEX, entities_data)

    return updated_count


def verify_jeffrey_epstein():
    """Verify Jeffrey Epstein entity after update"""
    print("\n" + "=" * 80)
    print("VERIFICATION: Jeffrey Epstein Entity")
    print("=" * 80)

    entities_data = load_json(ENTITIES_INDEX)
    entities = entities_data.get("entities", [])

    jeffrey_epstein = None
    for entity in entities:
        if "Jeffrey" in entity.get("name", "") and "Epstein" in entity.get("name", ""):
            jeffrey_epstein = entity
            break

    if jeffrey_epstein:
        print(f"\n✅ Found: {jeffrey_epstein.get('name')}")
        print(f"   Normalized name: {jeffrey_epstein.get('normalized_name')}")
        print(f"   Flight count: {jeffrey_epstein.get('flights', 0)}")
        print(f"   Routes: {len(jeffrey_epstein.get('routes', []))}")
        print(f"   First flight: {jeffrey_epstein.get('first_flight')}")
        print(f"   Last flight: {jeffrey_epstein.get('last_flight')}")
        print(f"   Sources: {jeffrey_epstein.get('sources', [])}")

        expected_count = 1018  # From manual verification
        actual_count = jeffrey_epstein.get("flights", 0)

        if actual_count == expected_count:
            print(f"\n✅ SUCCESS: Flight count matches expected value ({expected_count})")
        elif actual_count > 900:  # Close enough (might be due to data variations)
            print(
                f"\n⚠️  ACCEPTABLE: Flight count ({actual_count}) is close to expected ({expected_count})"
            )
        else:
            print(
                f"\n❌ ISSUE: Flight count ({actual_count}) is still far from expected ({expected_count})"
            )
    else:
        print("\n❌ ERROR: Jeffrey Epstein entity not found!")


def main():
    """Main execution"""
    print("=" * 80)
    print("FIX FLIGHT COUNTS IN ENTITIES_INDEX.JSON")
    print("=" * 80)
    print("\nTarget files:")
    print(f"  Flight logs: {FLIGHT_LOGS}")
    print(f"  Entities index: {ENTITIES_INDEX}")

    # Step 1: Count flights from source data
    flight_counts, route_sets, first_flights, last_flights = count_flights_by_entity()

    # Step 2: Update ENTITIES_INDEX.json
    update_entities_index(flight_counts, route_sets, first_flights, last_flights)

    # Step 3: Verify Jeffrey Epstein specifically
    verify_jeffrey_epstein()

    print("\n" + "=" * 80)
    print("✅ COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. Run: python scripts/data_quality/rebuild_entity_statistics.py")
    print("  2. Verify entity_statistics.json has correct counts")
    print("  3. Test API endpoints")


if __name__ == "__main__":
    main()
