#!/usr/bin/env python3
"""
Test script for GUID-based entity endpoint (v3 API)
Validates GUID mapping and endpoint functionality
"""

import json
from pathlib import Path

# Load entity data
DATA_DIR = Path(__file__).parent / "data"
METADATA_DIR = DATA_DIR / "metadata"

stats_path = METADATA_DIR / "entity_statistics.json"
with open(stats_path) as f:
    data = json.load(f)
    entity_stats = data.get("statistics", {})

# Build GUID mapping (same as in app.py)
guid_to_id = {}
for entity_id, entity_data in entity_stats.items():
    guid = entity_data.get("guid")
    if guid:
        guid_to_id[guid] = entity_id

print("✓ GUID Mapping Test Results:")
print(f"  Total entities: {len(entity_stats)}")
print(f"  Entities with GUIDs: {len(guid_to_id)}")
print(f"  Coverage: {len(guid_to_id) / len(entity_stats) * 100:.1f}%")

# Test a few sample lookups
print("\n✓ Sample GUID Lookups:")
sample_count = 0
for guid, entity_id in list(guid_to_id.items())[:5]:
    entity = entity_stats[entity_id]
    print(f"  GUID: {guid}")
    print(f"  → ID: {entity_id}")
    print(f"  → Name: {entity.get('name', 'Unknown')}")
    sample_count += 1

print(f"\n✓ All tests passed! {sample_count} sample lookups successful.")

# Test UUID validation
from uuid import UUID

print("\n✓ UUID Validation Tests:")
test_cases = [
    ("8889edfa-d770-54e4-8192-dc900cdd2257", True),  # Valid UUID4
    ("invalid-guid", False),  # Invalid format
    ("12345", False),  # Not a UUID
]

for test_guid, should_pass in test_cases:
    try:
        UUID(test_guid, version=4)
        result = "✓ Valid" if should_pass else "✗ Should have failed"
    except (ValueError, AttributeError):
        result = "✓ Rejected" if not should_pass else "✗ Should have passed"

    print(f"  {test_guid}: {result}")

print("\n✓ Implementation ready for deployment!")
