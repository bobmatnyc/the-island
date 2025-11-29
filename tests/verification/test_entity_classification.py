#!/usr/bin/env python3
"""
Test Entity Type Classification

Tests the 3-tier entity classification system:
1. LLM classification (Claude Haiku)
2. NLP fallback (spaCy NER)
3. Procedural fallback (keyword matching)

Usage:
    python tests/verification/test_entity_classification.py
"""

import os
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

from services.entity_service import EntityService

def test_classification():
    """Test entity classification with various entity types."""

    # Initialize entity service
    data_path = Path(__file__).parent.parent.parent / "data"
    service = EntityService(data_path)

    # Test cases (name, expected_type)
    test_cases = [
        # People
        ("Boardman", "person"),
        ("Epstein, Jeffrey", "person"),
        ("Maxwell, Ghislaine", "person"),
        ("Clinton, Bill", "person"),
        ("Trump, Donald", "person"),

        # Organizations
        ("Clinton Foundation", "organization"),
        ("Trump Organization", "organization"),
        ("Harvard University", "organization"),
        ("FBI", "organization"),
        ("U.S. Department of Justice", "organization"),

        # Locations
        ("Little St James Island", "location"),
        ("Zorro Ranch", "location"),
        ("Palm Beach", "location"),
        ("Manhattan", "location"),
        ("Paris", "location"),
    ]

    print("=" * 80)
    print("Entity Type Classification Test")
    print("=" * 80)
    print()

    # Test with different configurations
    configs = [
        ("LLM + NLP + Procedural", True, True),
        ("NLP + Procedural (no LLM)", False, True),
        ("Procedural only", False, False),
    ]

    for config_name, enable_llm, enable_nlp in configs:
        print(f"\n{'=' * 80}")
        print(f"Configuration: {config_name}")
        print(f"{'=' * 80}\n")

        # Set environment variables
        os.environ["ENABLE_LLM_CLASSIFICATION"] = "true" if enable_llm else "false"
        os.environ["ENABLE_NLP_CLASSIFICATION"] = "true" if enable_nlp else "false"

        # Reload service to pick up new config
        service = EntityService(data_path)

        correct = 0
        total = len(test_cases)

        for name, expected in test_cases:
            result = service.detect_entity_type(name)

            # Map 'business' to 'organization' for comparison
            normalized_result = 'organization' if result == 'business' else result

            is_correct = normalized_result == expected
            correct += is_correct

            status = "✓" if is_correct else "✗"
            print(f"{status} {name:40s} → {result:15s} (expected: {expected})")

        accuracy = (correct / total) * 100
        print(f"\nAccuracy: {correct}/{total} ({accuracy:.1f}%)")

    print("\n" + "=" * 80)
    print("Testing Context-Aware Classification")
    print("=" * 80 + "\n")

    # Test with context
    os.environ["ENABLE_LLM_CLASSIFICATION"] = "true"
    service = EntityService(data_path)

    # Test ambiguous name with context
    ambiguous_cases = [
        ("Washington", None, "person"),  # Ambiguous without context
        ("Washington", {"bio": "First President of the United States"}, "person"),
        ("Washington", {"bio": "The capital city of the United States"}, "location"),
    ]

    for name, context, expected in ambiguous_cases:
        result = service.detect_entity_type(name, context)
        status = "✓" if result == expected else "✗"
        context_str = "no context" if not context else f"context: {context['bio'][:40]}..."
        print(f"{status} {name:20s} ({context_str:50s}) → {result}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    test_classification()
