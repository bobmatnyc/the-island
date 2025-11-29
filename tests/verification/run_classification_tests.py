#!/usr/bin/env python3
"""
Simple test runner for entity type classification tests.

Bypasses pytest configuration issues and runs tests directly.
"""

import os
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

# Load environment
env_file = Path(__file__).parent.parent.parent / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from services.entity_service import EntityService

def run_tests():
    """Run critical entity classification tests."""

    data_path = Path(__file__).parent.parent.parent / "data"
    entity_service = EntityService(data_path)

    print("=" * 80)
    print("Entity Type Classification Test - Critical Cases (1M-364)")
    print("=" * 80)
    print()

    # Critical test cases
    test_cases = [
        # Organizations (keyword priority over person names)
        ("Southern Trust Company", "organization", "Has 'Trust' and 'Company' keywords"),
        ("Clinton Foundation", "organization", "Has 'Foundation' keyword"),
        ("Trump Organization", "organization", "Has 'Organization' keyword"),
        ("FBI", "organization", "Government agency acronym"),
        ("CIA", "organization", "Intelligence agency acronym"),
        ("Interfor Inc.", "organization", "Has 'Inc.' keyword"),

        # Locations (keyword priority)
        ("Little St. James Island", "location", "Has 'Island' keyword"),
        ("Palm Beach", "location", "Has 'Beach' keyword"),
        ("Zorro Ranch", "location", "Has 'Ranch' keyword"),
        ("Manhattan", "location", "Geographic location"),

        # Persons
        ("Jeffrey Epstein", "person", "Individual person"),
        ("Ghislaine Maxwell", "person", "Individual person"),
        ("Doug Band", "person", "Individual person (previously misclassified)"),
        ("Epstein, Jeffrey", "person", "Last, First format"),
    ]

    passed = 0
    failed = 0
    failures = []

    for name, expected, description in test_cases:
        result = entity_service.detect_entity_type(name)

        # Normalize result
        normalized = "organization" if result == "business" else result

        if normalized == expected:
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1
            failures.append((name, expected, result, description))

        print(f"{status} | {name:35s} | Expected: {expected:12s} | Got: {result:12s} | {description}")

    # Summary
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    total = passed + failed
    print(f"Total tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")

    if failures:
        print()
        print("FAILURES:")
        for name, expected, got, desc in failures:
            print(f"  ❌ {name}: expected '{expected}', got '{got}' ({desc})")

    print("=" * 80)

    # Critical keyword priority test
    print()
    print("=" * 80)
    print("CRITICAL TEST: Keyword Priority Over Name Format")
    print("=" * 80)
    print()

    critical_cases = [
        ("Trump Organization", "organization",
         "Has 'Organization' keyword - should be org, not person"),
        ("Clinton Foundation", "organization",
         "Has 'Foundation' keyword - should be org, not person"),
        ("Little St. James Island", "location",
         "Has 'Island' keyword - should be location, not person"),
    ]

    critical_failures = []

    for name, expected, reason in critical_cases:
        result = entity_service.detect_entity_type(name)
        normalized = "organization" if result == "business" else result

        if normalized == expected:
            status = "✅ PASS"
            print(f"{status} {name}: {result} (correct)")
        else:
            status = "❌ FAIL"
            critical_failures.append((name, expected, result, reason))
            print(f"{status} {name}: expected '{expected}', got '{result}'")
            print(f"        Reason: {reason}")

    print()
    print("=" * 80)

    if critical_failures:
        print("❌ CRITICAL TEST FAILED")
        print()
        print("The root cause fix for 1M-364 is NOT working.")
        print("Keywords are NOT being prioritized over name format.")
        print()
        print("DO NOT run batch reclassification until this is fixed.")
        print("=" * 80)
        return 1
    else:
        print("✅ CRITICAL TEST PASSED")
        print()
        print("Root cause fix verified: Keywords are prioritized over name format.")
        print("Ready to proceed with batch reclassification.")
        print("=" * 80)
        return 0

if __name__ == "__main__":
    sys.exit(run_tests())
