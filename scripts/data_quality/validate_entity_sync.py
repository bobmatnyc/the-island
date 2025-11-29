#!/usr/bin/env python3
"""
Entity Data Synchronization Validator

Checks synchronization between primary entity index (ENTITIES_INDEX.json)
and secondary statistics file (entity_statistics.json).

Identifies:
- Duplicate entities
- Missing entities
- Removed entities still present
- Count mismatches

Usage:
    python3 scripts/data_quality/validate_entity_sync.py

Returns:
    Exit code 0 if in sync, 1 if issues found
"""

import json
import sys
from collections import Counter
from pathlib import Path


# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
PRIMARY_INDEX = PROJECT_ROOT / "data/md/entities/ENTITIES_INDEX.json"
SECONDARY_INDEX = PROJECT_ROOT / "data/metadata/entity_statistics.json"


def load_primary_index() -> tuple[list[dict], dict]:
    """Load primary entity index"""
    with open(PRIMARY_INDEX) as f:
        data = json.load(f)

    entities = data.get("entities", [])
    metadata = {
        "total": data.get("total_entities", len(entities)),
        "generated": data.get("generated_date", "Unknown"),
        "statistics": data.get("statistics", {}),
    }

    return entities, metadata


def load_secondary_index() -> tuple[dict, dict]:
    """Load secondary statistics index"""
    with open(SECONDARY_INDEX) as f:
        data = json.load(f)

    stats = data.get("statistics", {})
    metadata = {"total": len(stats), "generated": data.get("generated_date", "Unknown")}

    return stats, metadata


def find_duplicates(entities: list[dict]) -> dict[str, list[str]]:
    """Find duplicate entity names"""
    name_counts = Counter(e["name"] for e in entities)
    return {name: count for name, count in name_counts.items() if count > 1}


def find_jeffrey_epstein_variations(entities: dict) -> list[str]:
    """Find all Jeffrey Epstein entity variations"""
    variations = []
    for name in entities:
        name_lower = name.lower()
        if (
            "jeffrey" in name_lower and "epstein" in name_lower
        ) or name_lower == "epstein, jeffrey":
            variations.append(name)
    return variations


def check_removed_entities(stats: dict) -> list[str]:
    """Check for known removed entities"""
    removed = []

    # Known removed entities
    removed_list = ["EPSTEIN- PORTABLES", "PORTABLES, EPSTEIN-", "JEGE LLC"]

    for removed_name in removed_list:
        for stat_name in stats:
            if removed_name.lower() in stat_name.lower():
                removed.append(stat_name)

    return removed


def validate_sync() -> tuple[bool, list[str]]:
    """
    Validate entity synchronization

    Returns:
        (is_valid, issues_list)
    """
    issues = []

    print("=" * 80)
    print("ENTITY DATA SYNCHRONIZATION VALIDATOR")
    print("=" * 80)
    print()

    # Load both indices
    print("Loading entity indices...")
    primary_entities, _primary_meta = load_primary_index()
    secondary_stats, _secondary_meta = load_secondary_index()

    print(f"✓ Primary index loaded: {len(primary_entities)} entities")
    print(f"✓ Secondary index loaded: {len(secondary_stats)} entities")
    print()

    # Extract entity names
    primary_names = {e["name"] for e in primary_entities}
    secondary_names = set(secondary_stats.keys())

    # Check 1: Entity count mismatch
    print("CHECK 1: Entity Count")
    print("-" * 80)
    if len(primary_names) != len(secondary_names):
        diff = len(secondary_names) - len(primary_names)
        issues.append(
            f"Count mismatch: Primary has {len(primary_names)}, Secondary has {len(secondary_names)} (diff: {diff})"
        )
        print(f"❌ FAIL: {issues[-1]}")
    else:
        print(f"✓ PASS: Both indices have {len(primary_names)} entities")
    print()

    # Check 2: Duplicate Jeffrey Epstein
    print("CHECK 2: Jeffrey Epstein Duplicates")
    print("-" * 80)
    jeffrey_primary = find_jeffrey_epstein_variations({e["name"]: e for e in primary_entities})
    jeffrey_secondary = find_jeffrey_epstein_variations(secondary_stats)

    print(f"Primary index: {len(jeffrey_primary)} Jeffrey Epstein entities")
    for name in jeffrey_primary:
        print(f"  - {name}")

    print(f"Secondary index: {len(jeffrey_secondary)} Jeffrey Epstein entities")
    for name in jeffrey_secondary:
        print(f"  - {name}")

    if len(jeffrey_secondary) > 1:
        issues.append(f"Duplicate Jeffrey Epstein in secondary: {jeffrey_secondary}")
        print(
            f"❌ FAIL: Found {len(jeffrey_secondary)} Jeffrey Epstein entities in secondary index"
        )
    else:
        print("✓ PASS: Single Jeffrey Epstein entity")
    print()

    # Check 3: Removed entities still present
    print("CHECK 3: Removed Entities")
    print("-" * 80)
    removed_in_secondary = check_removed_entities(secondary_stats)

    if removed_in_secondary:
        issues.append(f"Removed entities still in secondary: {removed_in_secondary}")
        print(f"❌ FAIL: Found {len(removed_in_secondary)} removed entities:")
        for name in removed_in_secondary:
            print(f"  - {name}")
    else:
        print("✓ PASS: No removed entities found")
    print()

    # Check 4: Missing entities
    print("CHECK 4: Missing Entities")
    print("-" * 80)
    missing_in_secondary = primary_names - secondary_names
    extra_in_secondary = secondary_names - primary_names

    if missing_in_secondary:
        issues.append(f"Missing from secondary: {len(missing_in_secondary)} entities")
        print(f"❌ FAIL: {len(missing_in_secondary)} entities in primary but not secondary:")
        for name in sorted(list(missing_in_secondary)[:10]):
            print(f"  - {name}")
        if len(missing_in_secondary) > 10:
            print(f"  ... and {len(missing_in_secondary) - 10} more")
    else:
        print("✓ PASS: All primary entities in secondary")

    if extra_in_secondary:
        issues.append(f"Extra in secondary: {len(extra_in_secondary)} entities")
        print(f"❌ FAIL: {len(extra_in_secondary)} entities in secondary but not primary:")
        for name in sorted(list(extra_in_secondary)[:10]):
            print(f"  - {name}")
        if len(extra_in_secondary) > 10:
            print(f"  ... and {len(extra_in_secondary) - 10} more")
    else:
        print("✓ PASS: No extra entities in secondary")
    print()

    # Check 5: Entity data consistency
    print("CHECK 5: Data Consistency Sample")
    print("-" * 80)

    # Check Epstein, Jeffrey has consistent data
    if "Epstein, Jeffrey" in primary_names and "Epstein, Jeffrey" in secondary_names:
        primary_epstein = next(e for e in primary_entities if e["name"] == "Epstein, Jeffrey")
        secondary_epstein = secondary_stats["Epstein, Jeffrey"]

        print("Epstein, Jeffrey consistency:")
        print(f"  Primary sources: {primary_epstein.get('sources', [])}")
        print(f"  Primary flights: {primary_epstein.get('flights', 0)}")
        print(f"  Secondary sources: {secondary_epstein.get('sources', [])}")
        print(f"  Secondary flight_count: {secondary_epstein.get('flight_count', 0)}")
        print(f"  Secondary connections: {secondary_epstein.get('connection_count', 0)}")
        print("✓ Data retrieved successfully")
    print()

    # Summary
    print("=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)

    if issues:
        print(f"❌ VALIDATION FAILED: {len(issues)} issues found")
        print()
        print("Issues:")
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        print()
        print("Recommendation: Rebuild entity_statistics.json from ENTITIES_INDEX.json")
        return False, issues
    print("✓ VALIDATION PASSED: Entities are in sync")
    return True, []


def main():
    """Main validation function"""
    try:
        is_valid, _issues = validate_sync()

        if is_valid:
            print()
            print("✅ Entity data is synchronized")
            sys.exit(0)
        else:
            print()
            print("⚠️  Entity data synchronization issues detected")
            print()
            print("Next steps:")
            print("1. Review issues above")
            print("2. Backup entity_statistics.json")
            print("3. Rebuild from ENTITIES_INDEX.json")
            print("4. Run this validator again")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ ERROR: Required file not found: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"❌ ERROR: Validation failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
