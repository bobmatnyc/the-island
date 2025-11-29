#!/usr/bin/env python3
"""
Test Entity Type Classification Fix (Ticket 1M-364)

Verifies that the enhanced LLM prompt correctly classifies known test cases.

Test Cases:
- Organizations: FBI, CIA, Interfor Inc, Southern Trust Company
- Locations: Little St. James Island, Palm Beach, Mar-a-Lago
- Persons: Epstein Jeffrey, Maxwell Ghislaine

Usage:
    python3 tests/verification/test_entity_classification_fix.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'server'))

# Load environment from .env.local
env_file = project_root / '.env.local'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

# Enable LLM classification
os.environ['ENABLE_LLM_CLASSIFICATION'] = 'true'

from services.entity_service import EntityService

class TestEntityClassificationFix:
    """Test suite for entity type classification fix."""

    def __init__(self):
        """Initialize entity service."""
        data_dir = project_root / 'data'
        self.entity_service = EntityService(data_dir)

        # Test cases (name, expected_type, description)
        self.test_cases = [
            # Organizations
            ("FBI", "organization", "Federal agency"),
            ("CIA", "organization", "Intelligence agency"),
            ("Interfor Inc", "organization", "Investigation company"),
            ("Southern Trust Company", "organization", "Trust company"),
            ("Clinton Foundation", "organization", "Non-profit foundation"),

            # Locations
            ("Little St. James Island", "location", "Epstein's island"),
            ("Palm Beach", "location", "City in Florida"),
            ("Mar-a-Lago", "location", "Trump property"),
            ("Zorro Ranch", "location", "New Mexico property"),

            # Persons
            ("Epstein, Jeffrey", "person", "Individual (Last, First format)"),
            ("Maxwell, Ghislaine", "person", "Individual (Last, First format)"),
            ("Clinton, Bill", "person", "Individual (Last, First format)"),
        ]

    def run_tests(self):
        """Run all test cases."""
        print("=" * 70)
        print("Entity Type Classification Fix - Test Suite")
        print("=" * 70)
        print(f"Testing {len(self.test_cases)} cases with enhanced LLM prompt\n")

        passed = 0
        failed = 0
        errors = []

        for name, expected_type, description in self.test_cases:
            try:
                # Classify using the fixed LLM method
                result = self.entity_service.detect_entity_type(name)

                # Check result
                status = "✅ PASS" if result == expected_type else "❌ FAIL"
                if result == expected_type:
                    passed += 1
                else:
                    failed += 1
                    errors.append((name, expected_type, result))

                print(f"{status} | {name:30s} | Expected: {expected_type:12s} | Got: {result:12s} | {description}")

            except Exception as e:
                print(f"❌ ERROR | {name:30s} | Exception: {e}")
                failed += 1
                errors.append((name, expected_type, f"ERROR: {e}"))

        # Print summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total tests: {len(self.test_cases)}")
        print(f"Passed: {passed} ({passed / len(self.test_cases) * 100:.1f}%)")
        print(f"Failed: {failed} ({failed / len(self.test_cases) * 100:.1f}%)")

        if errors:
            print("\nFAILURES:")
            for name, expected, got in errors:
                print(f"  - {name}: expected '{expected}', got '{got}'")

        # Print assessment
        print("\n" + "=" * 70)
        if passed == len(self.test_cases):
            print("✅ ALL TESTS PASSED - Fix is working correctly!")
            print("Ready to run full re-classification on 1,637 entities.")
        elif passed >= len(self.test_cases) * 0.9:
            print("⚠️ MOST TESTS PASSED - Fix is mostly working.")
            print(f"Fix success rate: {passed / len(self.test_cases) * 100:.1f}%")
            print("Consider reviewing failures before full re-classification.")
        else:
            print("❌ FIX NOT WORKING - Too many test failures.")
            print("Do NOT run full re-classification until prompt is fixed.")

        return passed == len(self.test_cases)

def main():
    """Main entry point."""
    # Check for API key
    if not os.environ.get('OPENROUTER_API_KEY'):
        print("❌ ERROR: OPENROUTER_API_KEY not set")
        print("Please set OPENROUTER_API_KEY in .env.local or environment")
        sys.exit(1)

    # Run tests
    tester = TestEntityClassificationFix()
    success = tester.run_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
