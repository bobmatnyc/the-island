#!/usr/bin/env python3
"""
Fix Entity Data Quality Issues

This script addresses multiple entity data quality problems:
1. Fix entity type misclassifications
2. Create location entities from airport codes
3. Merge duplicate "Ghislaine" and "Maxwell, Ghislaine" entities
4. Check for and fix any remaining "Ghislaine, Ghislaine" duplicates

Author: Entity Data Quality Team
Date: 2025-11-17
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

# Airport database (most common airports from Epstein flight logs)
AIRPORT_DATABASE = {
    'PBI': {'name': 'Palm Beach International Airport', 'city': 'West Palm Beach', 'state': 'FL', 'country': 'USA', 'lat': 26.6832, 'lon': -80.0956},
    'TEB': {'name': 'Teterboro Airport', 'city': 'Teterboro', 'state': 'NJ', 'country': 'USA', 'lat': 40.8501, 'lon': -74.0608},
    'JFK': {'name': 'John F. Kennedy International Airport', 'city': 'New York', 'state': 'NY', 'country': 'USA', 'lat': 40.6413, 'lon': -73.7781},
    'LAX': {'name': 'Los Angeles International Airport', 'city': 'Los Angeles', 'state': 'CA', 'country': 'USA', 'lat': 33.9416, 'lon': -118.4085},
    'ABQ': {'name': 'Albuquerque International Sunport', 'city': 'Albuquerque', 'state': 'NM', 'country': 'USA', 'lat': 35.0402, 'lon': -106.6091},
    'CMH': {'name': 'John Glenn Columbus International Airport', 'city': 'Columbus', 'state': 'OH', 'country': 'USA', 'lat': 39.9980, 'lon': -82.8919},
    'SAF': {'name': 'Santa Fe Municipal Airport', 'city': 'Santa Fe', 'state': 'NM', 'country': 'USA', 'lat': 35.6174, 'lon': -106.0881},
    'HPN': {'name': 'Westchester County Airport', 'city': 'White Plains', 'state': 'NY', 'country': 'USA', 'lat': 41.0670, 'lon': -73.7076},
    'ASE': {'name': 'Aspen-Pitkin County Airport', 'city': 'Aspen', 'state': 'CO', 'country': 'USA', 'lat': 39.2232, 'lon': -106.8690},
    'BED': {'name': 'Laurence G. Hanscom Field', 'city': 'Bedford', 'state': 'MA', 'country': 'USA', 'lat': 42.4700, 'lon': -71.2890},
    'VNY': {'name': 'Van Nuys Airport', 'city': 'Los Angeles', 'state': 'CA', 'country': 'USA', 'lat': 34.2098, 'lon': -118.4898},
    'MIA': {'name': 'Miami International Airport', 'city': 'Miami', 'state': 'FL', 'country': 'USA', 'lat': 25.7959, 'lon': -80.2870},
    'LGA': {'name': 'LaGuardia Airport', 'city': 'New York', 'state': 'NY', 'country': 'USA', 'lat': 40.7769, 'lon': -73.8740},
    'EWR': {'name': 'Newark Liberty International Airport', 'city': 'Newark', 'state': 'NJ', 'country': 'USA', 'lat': 40.6895, 'lon': -74.1745},
    'DFW': {'name': 'Dallas/Fort Worth International Airport', 'city': 'Dallas', 'state': 'TX', 'country': 'USA', 'lat': 32.8998, 'lon': -97.0403},
    'MDW': {'name': 'Chicago Midway International Airport', 'city': 'Chicago', 'state': 'IL', 'country': 'USA', 'lat': 41.7868, 'lon': -87.7522},
    'LZU': {'name': 'Gwinnett County Airport', 'city': 'Lawrenceville', 'state': 'GA', 'country': 'USA', 'lat': 33.9781, 'lon': -83.9624},
    'ISP': {'name': 'Long Island MacArthur Airport', 'city': 'Ronkonkoma', 'state': 'NY', 'country': 'USA', 'lat': 40.7952, 'lon': -73.1002},
    'SAN': {'name': 'San Diego International Airport', 'city': 'San Diego', 'state': 'CA', 'country': 'USA', 'lat': 32.7336, 'lon': -117.1897},
    'DCA': {'name': 'Ronald Reagan Washington National Airport', 'city': 'Washington', 'state': 'DC', 'country': 'USA', 'lat': 38.8521, 'lon': -77.0377},
    'BGR': {'name': 'Bangor International Airport', 'city': 'Bangor', 'state': 'ME', 'country': 'USA', 'lat': 44.8074, 'lon': -68.8281},
    'ISM': {'name': 'Kissimmee Gateway Airport', 'city': 'Kissimmee', 'state': 'FL', 'country': 'USA', 'lat': 28.2898, 'lon': -81.4372},
    'ABY': {'name': 'Southwest Georgia Regional Airport', 'city': 'Albany', 'state': 'GA', 'country': 'USA', 'lat': 31.5355, 'lon': -84.1945},
    'TVC': {'name': 'Cherry Capital Airport', 'city': 'Traverse City', 'state': 'MI', 'country': 'USA', 'lat': 44.7414, 'lon': -85.5822},
    'ORL': {'name': 'Orlando Executive Airport', 'city': 'Orlando', 'state': 'FL', 'country': 'USA', 'lat': 28.5455, 'lon': -81.3329},
    'FTK': {'name': 'Godman Army Airfield', 'city': 'Fort Knox', 'state': 'KY', 'country': 'USA', 'lat': 37.9071, 'lon': -85.9721},
    'CHO': {'name': 'Charlottesville-Albemarle Airport', 'city': 'Charlottesville', 'state': 'VA', 'country': 'USA', 'lat': 38.1386, 'lon': -78.4529},
    'STL': {'name': 'St. Louis Lambert International Airport', 'city': 'St. Louis', 'state': 'MO', 'country': 'USA', 'lat': 38.7487, 'lon': -90.3700},
    'BOS': {'name': 'Boston Logan International Airport', 'city': 'Boston', 'state': 'MA', 'country': 'USA', 'lat': 42.3656, 'lon': -71.0096},
    'JAN': {'name': 'Jackson-Medgar Wiley Evers International Airport', 'city': 'Jackson', 'state': 'MS', 'country': 'USA', 'lat': 32.3112, 'lon': -90.0759},
    'SJC': {'name': 'Norman Y. Mineta San Jose International Airport', 'city': 'San Jose', 'state': 'CA', 'country': 'USA', 'lat': 37.3639, 'lon': -121.9289},
    'MRY': {'name': 'Monterey Regional Airport', 'city': 'Monterey', 'state': 'CA', 'country': 'USA', 'lat': 36.5870, 'lon': -121.8429},
    'MVY': {'name': "Martha's Vineyard Airport", 'city': "Martha's Vineyard", 'state': 'MA', 'country': 'USA', 'lat': 41.3931, 'lon': -70.6143},
    'ACY': {'name': 'Atlantic City International Airport', 'city': 'Atlantic City', 'state': 'NJ', 'country': 'USA', 'lat': 39.4577, 'lon': -74.5772},
    'IAD': {'name': 'Washington Dulles International Airport', 'city': 'Washington', 'state': 'DC', 'country': 'USA', 'lat': 38.9531, 'lon': -77.4565},
    'PDK': {'name': 'DeKalb-Peachtree Airport', 'city': 'Atlanta', 'state': 'GA', 'country': 'USA', 'lat': 33.8756, 'lon': -84.3020},
    'FLL': {'name': 'Fort Lauderdale-Hollywood International Airport', 'city': 'Fort Lauderdale', 'state': 'FL', 'country': 'USA', 'lat': 26.0742, 'lon': -80.1506},
    'DAL': {'name': 'Dallas Love Field', 'city': 'Dallas', 'state': 'TX', 'country': 'USA', 'lat': 32.8471, 'lon': -96.8518},
    'ADS': {'name': 'Addison Airport', 'city': 'Dallas', 'state': 'TX', 'country': 'USA', 'lat': 32.9686, 'lon': -96.8364},
    'SAT': {'name': 'San Antonio International Airport', 'city': 'San Antonio', 'state': 'TX', 'country': 'USA', 'lat': 29.5337, 'lon': -98.4698},
    'CRG': {'name': 'Jacksonville Executive at Craig Airport', 'city': 'Jacksonville', 'state': 'FL', 'country': 'USA', 'lat': 30.3363, 'lon': -81.5144},
}

class EntityDataQualityFixer:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.entities_index_path = data_dir / 'md' / 'entities' / 'ENTITIES_INDEX.json'
        self.entity_network_path = data_dir / 'metadata' / 'entity_network.json'
        self.flight_logs_path = data_dir / 'md' / 'entities' / 'flight_logs_by_flight.json'
        self.locations_path = data_dir / 'md' / 'entities' / 'locations.json'

        self.changes_log = []

    def log_change(self, category: str, message: str):
        """Log a change for reporting"""
        self.changes_log.append(f"[{category}] {message}")
        print(f"✓ {message}")

    def load_entities_index(self) -> dict:
        """Load the entities index"""
        with open(self.entities_index_path, 'r') as f:
            return json.load(f)

    def save_entities_index(self, data: dict):
        """Save the entities index"""
        with open(self.entities_index_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_entity_network(self) -> dict:
        """Load the entity network"""
        if not self.entity_network_path.exists():
            return None
        with open(self.entity_network_path, 'r') as f:
            return json.load(f)

    def save_entity_network(self, data: dict):
        """Save the entity network"""
        with open(self.entity_network_path, 'w') as f:
            json.dump(data, f, indent=2)

    def task1_fix_entity_types(self, entities_data: dict) -> dict:
        """Task 1: Fix entity type misclassifications"""
        print("\n=== TASK 1: Fix Entity Type Misclassifications ===")

        entities = entities_data['entities']
        fixes_made = 0

        # Check for Villani
        for entity in entities:
            if 'Villani' in entity.get('name', ''):
                if entity.get('entity_type') == 'location':
                    old_type = entity['entity_type']
                    entity['entity_type'] = 'person'
                    self.log_change('TYPE_FIX', f"Fixed '{entity['name']}': {old_type} → person")
                    fixes_made += 1
                elif 'entity_type' not in entity:
                    # Add entity_type if missing
                    entity['entity_type'] = 'person'
                    self.log_change('TYPE_ADD', f"Added entity_type for '{entity['name']}': person")
                    fixes_made += 1
                else:
                    self.log_change('TYPE_OK', f"'{entity['name']}' already correctly typed as {entity.get('entity_type')}")

        if fixes_made == 0:
            print("  No entity type misclassifications found")

        return entities_data

    def task2_create_airport_locations(self) -> Dict[str, int]:
        """Task 2: Create location entities from airport codes"""
        print("\n=== TASK 2: Create Location Entities from Airport Codes ===")

        # Extract all airport codes from flight logs
        with open(self.flight_logs_path, 'r') as f:
            flights_data = json.load(f)

        airport_usage = defaultdict(int)
        all_codes = set()

        for flight in flights_data['flights']:
            route = flight.get('route', '')
            # Extract 3-letter airport codes
            codes = re.findall(r'\b[A-Z]{3}\b', route)
            for code in codes:
                all_codes.add(code)
                airport_usage[code] += 1

        print(f"  Found {len(all_codes)} unique airport codes")

        # Create location entities
        locations = []
        unknown_airports = []

        for code in sorted(all_codes):
            if code in AIRPORT_DATABASE:
                airport_info = AIRPORT_DATABASE[code]
                location = {
                    'name': airport_info['name'],
                    'code': code,
                    'entity_type': 'location',
                    'location_type': 'airport',
                    'city': airport_info['city'],
                    'state': airport_info['state'],
                    'country': airport_info['country'],
                    'coordinates': {
                        'lat': airport_info['lat'],
                        'lon': airport_info['lon']
                    },
                    'flights_count': airport_usage[code],
                    'sources': ['flight_logs']
                }
                locations.append(location)
                self.log_change('LOCATION_CREATE', f"Created location: {code} - {airport_info['name']} ({airport_usage[code]} flights)")
            else:
                unknown_airports.append(code)

        # Save locations
        locations_output = {
            'metadata': {
                'source': 'flight_logs',
                'extraction_date': '2025-11-17',
                'total_locations': len(locations),
                'total_airport_codes': len(all_codes),
                'unknown_airports': len(unknown_airports)
            },
            'locations': locations,
            'unknown_airport_codes': sorted(unknown_airports)
        }

        with open(self.locations_path, 'w') as f:
            json.dump(locations_output, f, indent=2)

        print(f"  Created {len(locations)} location entities")
        print(f"  Unknown airports: {len(unknown_airports)} codes")
        if unknown_airports:
            print(f"    Unknown codes: {', '.join(sorted(unknown_airports)[:10])}...")

        return airport_usage

    def task3_merge_maxwell_entities(self, entities_data: dict, network_data: dict) -> tuple:
        """Task 3: Merge 'Ghislaine' and 'Maxwell, Ghislaine' entities"""
        print("\n=== TASK 3: Merge Maxwell/Ghislaine Entities ===")

        entities = entities_data['entities']

        # Find the entities
        ghislaine_entity = None
        maxwell_ghislaine_entity = None
        ghislaine_idx = None
        maxwell_idx = None

        for idx, entity in enumerate(entities):
            if entity.get('name') == 'Ghislaine':
                ghislaine_entity = entity
                ghislaine_idx = idx
            elif entity.get('name') == 'Maxwell, Ghislaine':
                maxwell_ghislaine_entity = entity
                maxwell_idx = idx

        if not ghislaine_entity:
            print("  'Ghislaine' entity not found - may already be merged")
            return entities_data, network_data

        if not maxwell_ghislaine_entity:
            print("  'Maxwell, Ghislaine' entity not found - creating from 'Ghislaine'")
            # Just rename the entity
            ghislaine_entity['name'] = 'Maxwell, Ghislaine'
            ghislaine_entity['normalized_name'] = 'Ghislaine Maxwell'
            self.log_change('RENAME', f"Renamed 'Ghislaine' → 'Maxwell, Ghislaine' ({ghislaine_entity.get('flights', 0)} flights)")
            return entities_data, network_data

        # Merge the entities
        print(f"  Found 'Ghislaine' entity: {ghislaine_entity.get('flights', 0)} flights")
        print(f"  Found 'Maxwell, Ghislaine' entity: {maxwell_ghislaine_entity.get('flights', 0)} flights")

        # Merge sources
        maxwell_sources = set(maxwell_ghislaine_entity.get('sources', []))
        ghislaine_sources = set(ghislaine_entity.get('sources', []))
        merged_sources = list(maxwell_sources | ghislaine_sources)

        # Merge flights
        maxwell_flights = maxwell_ghislaine_entity.get('flights', 0)
        ghislaine_flights = ghislaine_entity.get('flights', 0)
        total_flights = max(maxwell_flights, ghislaine_flights)  # Take max to avoid double counting

        # Merge routes
        maxwell_routes = set(maxwell_ghislaine_entity.get('routes', []))
        ghislaine_routes = set(ghislaine_entity.get('routes', []))
        merged_routes = list(maxwell_routes | ghislaine_routes)

        # Update maxwell_ghislaine_entity
        maxwell_ghislaine_entity['sources'] = merged_sources
        maxwell_ghislaine_entity['flights'] = total_flights
        maxwell_ghislaine_entity['routes'] = merged_routes
        maxwell_ghislaine_entity['merged_from'] = maxwell_ghislaine_entity.get('merged_from', []) + ['Ghislaine']

        # Copy any unique fields from ghislaine_entity
        if 'first_flight' in ghislaine_entity and 'first_flight' not in maxwell_ghislaine_entity:
            maxwell_ghislaine_entity['first_flight'] = ghislaine_entity['first_flight']
        if 'last_flight' in ghislaine_entity and 'last_flight' not in maxwell_ghislaine_entity:
            maxwell_ghislaine_entity['last_flight'] = ghislaine_entity['last_flight']

        # Remove ghislaine_entity from list
        entities.pop(ghislaine_idx)

        self.log_change('MERGE', f"Merged 'Ghislaine' into 'Maxwell, Ghislaine' (total: {total_flights} flights)")

        # Update entity network if it exists
        if network_data:
            nodes_updated = 0
            edges_updated = 0

            # Update nodes
            for node in network_data.get('nodes', []):
                if node.get('id') == 'Ghislaine':
                    node['id'] = 'Maxwell, Ghislaine'
                    node['label'] = 'Maxwell, Ghislaine'
                    nodes_updated += 1

            # Update edges
            for edge in network_data.get('edges', []):
                if edge.get('source') == 'Ghislaine':
                    edge['source'] = 'Maxwell, Ghislaine'
                    edges_updated += 1
                if edge.get('target') == 'Ghislaine':
                    edge['target'] = 'Maxwell, Ghislaine'
                    edges_updated += 1

            self.log_change('NETWORK', f"Updated entity network: {nodes_updated} nodes, {edges_updated} edges")

        return entities_data, network_data

    def task4_check_ghislaine_duplicates(self, entities_data: dict) -> dict:
        """Task 4: Check for 'Ghislaine, Ghislaine' duplicates"""
        print("\n=== TASK 4: Check for 'Ghislaine, Ghislaine' Duplicates ===")

        entities = entities_data['entities']

        duplicates_found = []
        for entity in entities:
            name = entity.get('name', '')
            if 'Ghislaine, Ghislaine' in name:
                duplicates_found.append(entity)

        if duplicates_found:
            print(f"  Found {len(duplicates_found)} 'Ghislaine, Ghislaine' duplicates")
            for dup in duplicates_found:
                # Fix by renaming to Maxwell, Ghislaine
                old_name = dup['name']
                dup['name'] = 'Maxwell, Ghislaine'
                dup['normalized_name'] = 'Ghislaine Maxwell'
                self.log_change('DUPLICATE_FIX', f"Fixed duplicate: '{old_name}' → 'Maxwell, Ghislaine'")
        else:
            print("  ✓ No 'Ghislaine, Ghislaine' duplicates found")

        return entities_data

    def run_all_fixes(self):
        """Run all entity data quality fixes"""
        print("=" * 80)
        print("ENTITY DATA QUALITY FIXES")
        print("=" * 80)

        # Load data
        entities_data = self.load_entities_index()
        network_data = self.load_entity_network()

        initial_entity_count = len(entities_data['entities'])

        # Run tasks
        entities_data = self.task1_fix_entity_types(entities_data)
        airport_usage = self.task2_create_airport_locations()
        entities_data, network_data = self.task3_merge_maxwell_entities(entities_data, network_data)
        entities_data = self.task4_check_ghislaine_duplicates(entities_data)

        # Save updated data
        self.save_entities_index(entities_data)
        if network_data:
            self.save_entity_network(network_data)

        final_entity_count = len(entities_data['entities'])

        # Print summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total changes made: {len(self.changes_log)}")
        print(f"Initial entity count: {initial_entity_count}")
        print(f"Final entity count: {final_entity_count}")
        print(f"Net change: {final_entity_count - initial_entity_count}")
        print(f"\nLocation entities created: {len(airport_usage)}")
        print(f"Locations file saved: {self.locations_path}")
        print(f"Entities index updated: {self.entities_index_path}")
        if network_data:
            print(f"Entity network updated: {self.entity_network_path}")

        print("\n" + "=" * 80)
        print("DETAILED CHANGES")
        print("=" * 80)
        for change in self.changes_log:
            print(f"  {change}")

        # Write changes log
        log_path = self.data_dir / 'metadata' / 'entity_quality_fixes_log.txt'
        with open(log_path, 'w') as f:
            f.write("ENTITY DATA QUALITY FIXES\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Execution Date: 2025-11-17\n")
            f.write(f"Total Changes: {len(self.changes_log)}\n")
            f.write(f"Initial Entity Count: {initial_entity_count}\n")
            f.write(f"Final Entity Count: {final_entity_count}\n")
            f.write(f"Net Change: {final_entity_count - initial_entity_count}\n\n")
            f.write("CHANGES\n")
            f.write("=" * 80 + "\n")
            for change in self.changes_log:
                f.write(f"{change}\n")

        print(f"\nChanges log saved: {log_path}")

def main():
    data_dir = Path('/Users/masa/Projects/Epstein/data')
    fixer = EntityDataQualityFixer(data_dir)
    fixer.run_all_fixes()

if __name__ == '__main__':
    main()
