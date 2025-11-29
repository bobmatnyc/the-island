#!/usr/bin/env python3
"""
Comprehensive Test Suite for Entity Type Classification (1M-364)

This test suite validates the fix for the LLM prompt prioritization bug where
keywords were being overridden by name format, causing 97.3% of entities to be
misclassified as "person".

Root Cause (1M-364):
    The LLM prompt had contradictory prioritization rules:
    - Rule #1-2: "If name contains org/location keywords → classify accordingly"
    - Rule #3: "If name is formatted like person's name → person"

    Problem: Rule #3 was being prioritized OVER rules #1-2, causing entities like
    "Trump Organization" and "Clinton Foundation" to be classified as "person"
    instead of "organization".

Testing Strategy:
    - Test known entities that should be classified correctly
    - Test edge cases that were previously misclassified
    - Test keyword priority over name format (CRITICAL for root cause fix)
    - Test ambiguous cases with contextual classification
    - Measure accuracy before/after fix

Related Documents:
    - Linear Ticket: 1M-364
    - Research: docs/research/entity-type-classification-bug-1M-364-2025-11-29.md
    - Implementation: server/services/entity_service.py (lines 388-641)

Usage:
    # Run all tests
    pytest tests/verification/test_entity_type_classification.py -v

    # Run specific test category
    pytest tests/verification/test_entity_type_classification.py::TestEntityTypeClassification::test_organizations -v

    # Run with coverage
    pytest tests/verification/test_entity_type_classification.py --cov=server.services.entity_service
"""

import os
import sys
from pathlib import Path
from typing import Optional

import pytest

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

from services.entity_service import EntityService


# Load environment variables from .env.local if available
def load_env():
    """Load environment variables from .env.local."""
    env_file = Path(__file__).parent.parent.parent / '.env.local'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value


load_env()


class TestEntityTypeClassification:
    """
    Comprehensive test suite for entity type classification (1M-364).

    Tests verify that the LLM prompt correctly identifies:
    - Organizations (companies, agencies, institutions)
    - Locations (geographic places, properties)
    - Persons (individual humans)

    Critical Test: Keyword priority over name format (root cause fix)
    """

    @pytest.fixture
    def entity_service(self):
        """Fixture to initialize EntityService for testing."""
        data_path = Path(__file__).parent.parent.parent / "data"
        return EntityService(data_path)

    @pytest.fixture
    def entity_service_llm_only(self):
        """Fixture with only LLM classification enabled (for isolated testing)."""
        # Save current env
        old_llm = os.environ.get("ENABLE_LLM_CLASSIFICATION")
        old_nlp = os.environ.get("ENABLE_NLP_CLASSIFICATION")

        # Set LLM only
        os.environ["ENABLE_LLM_CLASSIFICATION"] = "true"
        os.environ["ENABLE_NLP_CLASSIFICATION"] = "false"

        data_path = Path(__file__).parent.parent.parent / "data"
        service = EntityService(data_path)

        yield service

        # Restore env
        if old_llm:
            os.environ["ENABLE_LLM_CLASSIFICATION"] = old_llm
        if old_nlp:
            os.environ["ENABLE_NLP_CLASSIFICATION"] = old_nlp

    # =========================================================================
    # ORGANIZATIONS - Known Entities
    # =========================================================================

    @pytest.mark.parametrize("entity_name,description", [
        ("Southern Trust Company", "Trust company"),
        ("Clinton Foundation", "Non-profit foundation"),
        ("Trump Organization", "Real estate organization"),
        ("FBI", "Federal law enforcement agency"),
        ("CIA", "Intelligence agency"),
        ("Interfor Inc.", "Investigation company"),
        ("J.P. Morgan & Co.", "Investment bank"),
        ("Deutsche Bank", "German financial institution"),
    ])
    def test_organizations(self, entity_service, entity_name, description):
        """
        Test that known organizations are correctly classified.

        Critical: These entities contain organization keywords (Foundation, Inc,
        Company, etc.) and should be classified as "organization" regardless of
        name format or person names embedded in them.
        """
        result = entity_service.detect_entity_type(entity_name)

        # Normalize result (business -> organization)
        normalized_result = "organization" if result == "business" else result

        assert normalized_result == "organization", (
            f"Expected '{entity_name}' ({description}) to be classified as "
            f"'organization', got '{result}'"
        )

    # =========================================================================
    # LOCATIONS - Known Entities
    # =========================================================================

    @pytest.mark.parametrize("entity_name,description", [
        ("Little St. James Island", "Epstein's private island"),
        ("Palm Beach", "City in Florida"),
        ("New York", "Major US city"),
        ("Paris", "French capital"),
        ("Zorro Ranch", "New Mexico property"),
        ("Manhattan", "NYC borough"),
        ("US Virgin Islands", "US territory"),
        ("New Mexico", "US state"),
    ])
    def test_locations(self, entity_service, entity_name, description):
        """
        Test that known locations are correctly classified.

        Critical: These entities contain location keywords (Island, Beach, Ranch,
        city names, etc.) and should be classified as "location" regardless of
        whether they could be interpreted as person names.
        """
        result = entity_service.detect_entity_type(entity_name)

        assert result == "location", (
            f"Expected '{entity_name}' ({description}) to be classified as "
            f"'location', got '{result}'"
        )

    # =========================================================================
    # PERSONS - Known Entities
    # =========================================================================

    @pytest.mark.parametrize("entity_name,description", [
        ("Jeffrey Epstein", "Individual (full name)"),
        ("Ghislaine Maxwell", "Individual (full name)"),
        ("Virginia Giuffre", "Individual (full name)"),
        ("Prince Andrew", "Individual (with title)"),
        ("Bill Clinton", "Individual (full name)"),
        ("Donald Trump", "Individual (full name)"),
        ("Alan Dershowitz", "Individual (full name)"),
        ("Leslie Wexner", "Individual (full name)"),
    ])
    def test_persons(self, entity_service, entity_name, description):
        """
        Test that known persons are correctly classified.

        These entities should be classified as "person" when they are actual
        human names without organization or location keywords.
        """
        result = entity_service.detect_entity_type(entity_name)

        assert result == "person", (
            f"Expected '{entity_name}' ({description}) to be classified as "
            f"'person', got '{result}'"
        )

    # =========================================================================
    # EDGE CASES - Previously Misclassified
    # =========================================================================

    def test_edge_case_doug_band(self, entity_service):
        """
        Test "Doug Band" - previously misclassified as organization.

        Critical Edge Case: This entity was incorrectly classified as
        "organization" when it should be "person" (individual human).

        Evidence: Entity doug_band in entity_biographies.json has:
        - name: "Douglas Jay Band"
        - summary: "Former top advisor to Bill Clinton..."
        - Clearly an individual person, not an organization
        """
        result = entity_service.detect_entity_type("Doug Band")

        assert result == "person", (
            f"Edge case failure: 'Doug Band' should be classified as 'person', "
            f"got '{result}'. This entity was previously misclassified as "
            f"'organization' (see 1M-364 research doc)."
        )

    def test_edge_case_last_first_format(self, entity_service):
        """
        Test "Last, First" name format is recognized as person.

        Critical: Names in "Epstein, Jeffrey" format should be classified as
        person even if they don't have titles or other person indicators.
        """
        test_cases = [
            ("Epstein, Jeffrey", "person"),
            ("Maxwell, Ghislaine", "person"),
            ("Clinton, Bill", "person"),
        ]

        for name, expected in test_cases:
            result = entity_service.detect_entity_type(name)
            assert result == expected, (
                f"Expected '{name}' (Last, First format) to be '{expected}', "
                f"got '{result}'"
            )

    def test_edge_case_empty_string(self, entity_service):
        """
        Test empty string classification.

        Edge Case: Empty strings should default to "person" (or handle gracefully).
        Previously, some empty name entities were classified as "location".
        """
        result = entity_service.detect_entity_type("")

        # Empty strings should default to person (or any consistent default)
        assert result == "person", (
            f"Empty string should default to 'person', got '{result}'"
        )

    @pytest.mark.parametrize("entity_name,expected_type,reason", [
        ("Clinton", "person", "Single surname, likely person"),
        ("Trump", "person", "Single surname, likely person"),
        ("Epstein", "person", "Single surname, likely person"),
        ("Maxwell", "person", "Single surname, likely person (though also company name)"),
    ])
    def test_ambiguous_single_names(self, entity_service, entity_name, expected_type, reason):
        """
        Test ambiguous single-name entities.

        Edge Case: Single names like "Clinton" or "Trump" could be:
        - Person (surname)
        - Organization (company with that name)
        - Location (city/place with that name)

        Expected Behavior: Should default to "person" for single names unless
        context (bio) suggests otherwise.
        """
        result = entity_service.detect_entity_type(entity_name)

        assert result == expected_type, (
            f"Ambiguous name '{entity_name}' expected '{expected_type}' "
            f"({reason}), got '{result}'"
        )

    # =========================================================================
    # CRITICAL TEST: Keyword Priority Over Name Format (Root Cause Fix)
    # =========================================================================

    def test_keyword_priority_organization_over_person_name(self, entity_service):
        """
        CRITICAL TEST: Verify keywords take priority over name format.

        This is the ROOT CAUSE fix for 1M-364. The LLM prompt must prioritize
        keyword matching BEFORE checking name format.

        Root Cause Problem:
            The old prompt had contradictory rules:
            1. "If name contains organization keywords → organization"
            2. "If name is formatted like person's name → person"

            The LLM prioritized rule #2 over rule #1, causing:
            - "Trump Organization" → person (WRONG!)
            - "Clinton Foundation" → person (WRONG!)

        Expected Fix Behavior:
            Keywords should take priority:
            - "Trump Organization" → organization (keyword priority)
            - "Clinton Foundation" → organization (keyword priority)
        """
        critical_test_cases = [
            # Organization keywords should override person names
            ("Trump Organization", "organization",
             "Contains 'Organization' keyword - should be org, not person"),

            ("Clinton Foundation", "organization",
             "Contains 'Foundation' keyword - should be org, not person"),

            ("Epstein Foundation", "organization",
             "Contains 'Foundation' keyword - should be org, not person"),

            # Location keywords should override person names
            ("Little St. James Island", "location",
             "Contains 'Island' keyword - should be location, not person"),

            ("Trump Tower", "location",
             "Contains 'Tower' keyword - should be location, not person"),
        ]

        failures = []

        for name, expected, reason in critical_test_cases:
            result = entity_service.detect_entity_type(name)

            # Normalize result
            normalized_result = "organization" if result == "business" else result

            if normalized_result != expected:
                failures.append(
                    f"CRITICAL FAILURE: '{name}' should be '{expected}' ({reason}), "
                    f"got '{result}'"
                )

        assert len(failures) == 0, (
            "\n\n" + "=" * 80 + "\n"
            "CRITICAL TEST FAILURE: Keyword Priority Not Working\n"
            "=" * 80 + "\n\n"
            "The root cause fix for 1M-364 is NOT working correctly.\n"
            "Keywords are NOT being prioritized over name format.\n\n"
            "Failures:\n" + "\n".join(f"  - {f}" for f in failures) + "\n\n"
            "This indicates the LLM prompt still has the prioritization bug.\n"
            "DO NOT run batch reclassification until this test passes.\n"
            "=" * 80
        )

    # =========================================================================
    # Keyword Detection Tests
    # =========================================================================

    def test_organization_keywords(self, entity_service):
        """
        Test that organization keywords are detected correctly.

        Organization keywords include:
        - Foundation, Organization, Inc, LLC, Corp, Company
        - Agency, Bureau, Department, Institute, University
        - Association, Trust, Bank, Group
        """
        organization_keyword_cases = [
            ("Acme Corporation", "organization", "Corp keyword"),
            ("Tech Inc", "organization", "Inc keyword"),
            ("Global LLC", "organization", "LLC keyword"),
            ("Federal Bureau of Investigation", "organization", "Bureau keyword"),
            ("Harvard University", "organization", "University keyword"),
            ("National Association", "organization", "Association keyword"),
            ("First Bank", "organization", "Bank keyword"),
        ]

        for name, expected, keyword_type in organization_keyword_cases:
            result = entity_service.detect_entity_type(name)
            normalized_result = "organization" if result == "business" else result

            assert normalized_result == expected, (
                f"Organization keyword test failed for '{name}' ({keyword_type}): "
                f"expected '{expected}', got '{result}'"
            )

    def test_location_keywords(self, entity_service):
        """
        Test that location keywords are detected correctly.

        Location keywords include:
        - Island, Beach, Ranch, Estate, Airport, Hotel, Resort
        - Street, Avenue, Road, Club, Palace, Villa
        - City, State, Country
        """
        location_keyword_cases = [
            ("Paradise Island", "location", "Island keyword"),
            ("Miami Beach", "location", "Beach keyword"),
            ("Sunset Ranch", "location", "Ranch keyword"),
            ("Luxury Estate", "location", "Estate keyword"),
            ("Main Street", "location", "Street keyword"),
            ("Park Avenue", "location", "Avenue keyword"),
            ("Ocean Resort", "location", "Resort keyword"),
        ]

        for name, expected, keyword_type in location_keyword_cases:
            result = entity_service.detect_entity_type(name)

            assert result == expected, (
                f"Location keyword test failed for '{name}' ({keyword_type}): "
                f"expected '{expected}', got '{result}'"
            )

    def test_person_name_formats(self, entity_service):
        """
        Test that person name formats are recognized.

        Person name patterns:
        - "Last, First" format
        - "Title Name" format (Dr., Mr., Ms., etc.)
        - Full names without keywords
        """
        person_format_cases = [
            ("Smith, John", "person", "Last, First format"),
            ("Dr. Jane Doe", "person", "Title format"),
            ("Mr. Robert Johnson", "person", "Title format"),
            ("John Smith", "person", "Full name"),
        ]

        for name, expected, format_type in person_format_cases:
            result = entity_service.detect_entity_type(name)

            assert result == expected, (
                f"Person format test failed for '{name}' ({format_type}): "
                f"expected '{expected}', got '{result}'"
            )

    # =========================================================================
    # Context-Aware Classification Tests
    # =========================================================================

    @pytest.mark.parametrize("entity_name,context,expected_type,reason", [
        (
            "Washington",
            {"bio": "First President of the United States"},
            "person",
            "Bio indicates person"
        ),
        (
            "Washington",
            {"bio": "The capital city of the United States"},
            "location",
            "Bio indicates location"
        ),
        (
            "Maxwell",
            {"bio": "Maxwell is a major telecommunications company"},
            "organization",
            "Bio indicates organization"
        ),
        (
            "Maxwell",
            {"bio": "Ghislaine Maxwell was a British socialite"},
            "person",
            "Bio indicates person"
        ),
    ])
    def test_context_aware_classification(
        self,
        entity_service,
        entity_name,
        context,
        expected_type,
        reason
    ):
        """
        Test that context (biography) is used for ambiguous cases.

        When entity name is ambiguous (could be person, org, or location),
        the classification should use biography context to disambiguate.
        """
        result = entity_service.detect_entity_type(entity_name, context)

        assert result == expected_type, (
            f"Context-aware classification failed for '{entity_name}': "
            f"expected '{expected_type}' ({reason}), got '{result}'. "
            f"Context: {context.get('bio', 'N/A')[:50]}..."
        )

    # =========================================================================
    # Accuracy Metrics
    # =========================================================================

    def test_overall_accuracy_target(self, entity_service):
        """
        Test that overall classification accuracy meets target threshold.

        Success Criteria:
        - Organizations: >80% accuracy
        - Locations: >80% accuracy
        - Persons: >80% accuracy

        This test collects all test cases and calculates accuracy by category.
        """
        # Collect all test cases
        all_test_cases = [
            # Organizations
            ("Southern Trust Company", "organization"),
            ("Clinton Foundation", "organization"),
            ("Trump Organization", "organization"),
            ("FBI", "organization"),
            ("CIA", "organization"),
            ("Interfor Inc.", "organization"),
            ("J.P. Morgan & Co.", "organization"),
            ("Deutsche Bank", "organization"),

            # Locations
            ("Little St. James Island", "location"),
            ("Palm Beach", "location"),
            ("New York", "location"),
            ("Paris", "location"),
            ("Zorro Ranch", "location"),
            ("Manhattan", "location"),
            ("US Virgin Islands", "location"),
            ("New Mexico", "location"),

            # Persons
            ("Jeffrey Epstein", "person"),
            ("Ghislaine Maxwell", "person"),
            ("Virginia Giuffre", "person"),
            ("Prince Andrew", "person"),
            ("Bill Clinton", "person"),
            ("Donald Trump", "person"),
            ("Alan Dershowitz", "person"),
            ("Leslie Wexner", "person"),
            ("Doug Band", "person"),
            ("Epstein, Jeffrey", "person"),
        ]

        # Calculate accuracy by category
        accuracy_by_type = {
            "organization": {"correct": 0, "total": 0},
            "location": {"correct": 0, "total": 0},
            "person": {"correct": 0, "total": 0},
        }

        for name, expected in all_test_cases:
            result = entity_service.detect_entity_type(name)
            normalized_result = "organization" if result == "business" else result

            accuracy_by_type[expected]["total"] += 1
            if normalized_result == expected:
                accuracy_by_type[expected]["correct"] += 1

        # Calculate percentages
        results = {}
        for entity_type, stats in accuracy_by_type.items():
            if stats["total"] > 0:
                accuracy_pct = (stats["correct"] / stats["total"]) * 100
                results[entity_type] = accuracy_pct
            else:
                results[entity_type] = 0.0

        # Print results
        print("\n" + "=" * 70)
        print("ACCURACY METRICS")
        print("=" * 70)
        for entity_type, accuracy in results.items():
            status = "✅ PASS" if accuracy >= 80.0 else "❌ FAIL"
            print(f"{status} {entity_type.capitalize():15s}: {accuracy:.1f}% "
                  f"({accuracy_by_type[entity_type]['correct']}/{accuracy_by_type[entity_type]['total']})")
        print("=" * 70 + "\n")

        # Assert all categories meet threshold
        failures = [
            f"{entity_type}: {accuracy:.1f}% (threshold: 80%)"
            for entity_type, accuracy in results.items()
            if accuracy < 80.0
        ]

        assert len(failures) == 0, (
            f"\n\nAccuracy threshold not met for:\n" +
            "\n".join(f"  - {f}" for f in failures) +
            f"\n\nTarget: >80% accuracy for each category"
        )

    # =========================================================================
    # Tier-Specific Tests (LLM, NLP, Procedural)
    # =========================================================================

    def test_llm_classification_isolated(self, entity_service_llm_only):
        """
        Test LLM classification in isolation (no NLP/procedural fallback).

        This verifies the LLM prompt itself is working correctly without
        interference from fallback classification methods.
        """
        # Require API key for this test
        if not os.environ.get("OPENROUTER_API_KEY"):
            pytest.skip("OPENROUTER_API_KEY not set, skipping LLM-only test")

        critical_llm_cases = [
            ("Clinton Foundation", "organization"),
            ("Trump Organization", "organization"),
            ("Little St. James Island", "location"),
            ("Jeffrey Epstein", "person"),
        ]

        for name, expected in critical_llm_cases:
            result = entity_service_llm_only.detect_entity_type(name)
            normalized_result = "organization" if result == "business" else result

            assert normalized_result == expected, (
                f"LLM-only classification failed for '{name}': "
                f"expected '{expected}', got '{result}'"
            )

    def test_procedural_fallback(self, entity_service):
        """
        Test procedural (keyword-based) classification fallback.

        Verifies the procedural tier works correctly when LLM/NLP unavailable.
        """
        # Temporarily disable LLM and NLP
        old_llm = os.environ.get("ENABLE_LLM_CLASSIFICATION")
        old_nlp = os.environ.get("ENABLE_NLP_CLASSIFICATION")

        os.environ["ENABLE_LLM_CLASSIFICATION"] = "false"
        os.environ["ENABLE_NLP_CLASSIFICATION"] = "false"

        # Recreate service with procedural only
        data_path = Path(__file__).parent.parent.parent / "data"
        service = EntityService(data_path)

        procedural_test_cases = [
            ("Acme Corporation", "organization"),
            ("Paradise Island", "location"),
            ("Smith, John", "person"),
        ]

        for name, expected in procedural_test_cases:
            result = service.detect_entity_type(name)
            normalized_result = "organization" if result == "business" else result

            assert normalized_result == expected, (
                f"Procedural fallback failed for '{name}': "
                f"expected '{expected}', got '{result}'"
            )

        # Restore environment
        if old_llm:
            os.environ["ENABLE_LLM_CLASSIFICATION"] = old_llm
        if old_nlp:
            os.environ["ENABLE_NLP_CLASSIFICATION"] = old_nlp


# =============================================================================
# Test Execution and Reporting
# =============================================================================

def main():
    """
    Main entry point for running tests standalone.

    Provides detailed test execution report with pass/fail statistics.
    """
    print("\n" + "=" * 80)
    print("Entity Type Classification Test Suite (1M-364)")
    print("=" * 80)
    print("\nRunning comprehensive test suite...\n")

    # Run pytest programmatically
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes",
    ])

    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
        print("\nRoot cause fix verified: Keywords are prioritized over name format.")
        print("Ready to run batch reclassification on all entities.")
    else:
        print("❌ TESTS FAILED")
        print("\nRoot cause fix NOT working correctly.")
        print("DO NOT run batch reclassification until all tests pass.")
    print("=" * 80 + "\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
