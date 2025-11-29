#!/usr/bin/env python3
"""
Test script for entity type detection with word boundary fix.

Verifies that the detect_entity_type() function correctly identifies entity types
and does not produce false positives from substring matches.
"""

import sys
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

from services.entity_service import EntityService


def test_entity_type_detection():
    """Test entity type detection with both false positive cases and correct cases."""

    # Initialize service with data path
    data_path = Path(__file__).parent.parent.parent / "data"
    service = EntityService(data_path=data_path)

    # Test cases that were previously false positives (should all be "person")
    false_positive_cases = [
        ("Boardman, Samantha", "person", "board substring should not match"),
        ("Boardman, Serena", "person", "board substring should not match"),
        ("Villani, Carmine S.", "person", "villa substring should not match"),
        ("Broadhurst, Julia", "person", "road substring should not match"),
        ("Driver, Minnie", "person", "drive substring should not match"),
    ]

    # Test cases that should still work correctly
    correct_cases = [
        ("Trump Organization", "organization", "organization whole word should match"),
        ("Clinton Foundation", "organization", "foundation whole word should match"),
        ("Little St James Island", "location", "island whole word should match"),
        ("Zorro Ranch", "location", "ranch whole word should match"),
        ("Palm Beach Estate", "location", "estate whole word should match"),
        ("Microsoft Corporation", "business", "corporation whole word should match"),
        ("Apple Inc", "business", "inc whole word should match"),
        ("Harvard University", "organization", "university whole word should match"),
        ("The Ritz Hotel", "location", "hotel whole word should match"),
        ("Fifth Avenue", "location", "avenue whole word should match"),
        ("Main Street", "location", "street whole word should match"),
        ("Park Drive", "location", "drive whole word should match (when it's a place)"),
    ]

    # Test cases that should default to person
    person_cases = [
        ("John Doe", "person", "regular name should be person"),
        ("Jane Smith", "person", "regular name should be person"),
        ("Bill Gates", "person", "regular name should be person"),
    ]

    print("=" * 80)
    print("TESTING ENTITY TYPE DETECTION - WORD BOUNDARY FIX")
    print("=" * 80)

    all_passed = True

    # Test false positive cases (was broken, should now be fixed)
    print("\n1. Testing False Positive Cases (Previously Broken):")
    print("-" * 80)
    for name, expected, reason in false_positive_cases:
        result = service.detect_entity_type(name)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name:<30} -> {result:<15} (expected: {expected})")
        if not passed:
            print(f"   Reason: {reason}")
            all_passed = False

    # Test correct cases (should still work)
    print("\n2. Testing Correct Cases (Should Still Work):")
    print("-" * 80)
    for name, expected, reason in correct_cases:
        result = service.detect_entity_type(name)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name:<30} -> {result:<15} (expected: {expected})")
        if not passed:
            print(f"   Reason: {reason}")
            all_passed = False

    # Test person cases
    print("\n3. Testing Person Cases (Default Behavior):")
    print("-" * 80)
    for name, expected, reason in person_cases:
        result = service.detect_entity_type(name)
        passed = result == expected
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name:<30} -> {result:<15} (expected: {expected})")
        if not passed:
            print(f"   Reason: {reason}")
            all_passed = False

    # Summary
    print("\n" + "=" * 80)
    if all_passed:
        print("✓ ALL TESTS PASSED - Entity type detection is working correctly!")
    else:
        print("✗ SOME TESTS FAILED - See details above")
    print("=" * 80)

    return all_passed


if __name__ == "__main__":
    success = test_entity_type_detection()
    sys.exit(0 if success else 1)
