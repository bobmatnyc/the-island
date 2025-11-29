#!/usr/bin/env python3
"""
Test OpenRouter entity classification integration.

This script verifies that:
1. OpenRouter API key is set
2. Entity classification service can call OpenRouter
3. Classification returns valid entity types
"""

import os
import sys
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "server"))

from services.entity_service import EntityService

def test_openrouter_classification():
    """Test OpenRouter-based entity type classification."""

    # Initialize entity service
    data_path = Path(__file__).parent.parent.parent / "data"
    service = EntityService(data_path)

    # Test cases with expected types
    test_entities = [
        ("Epstein, Jeffrey", "person"),
        ("Clinton Foundation", "organization"),
        ("Little St James Island", "location"),
        ("Trump, Donald", "person"),
        ("Maxwell, Ghislaine", "person"),
    ]

    print("Testing OpenRouter Entity Classification")
    print("=" * 50)
    print()

    # Check API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set in environment")
        print("   Set it in .env.local or export it manually")
        return False
    else:
        print(f"✅ OPENROUTER_API_KEY is set (length: {len(api_key)})")

    print()
    print("Testing entity classifications:")
    print("-" * 50)

    success_count = 0
    fail_count = 0

    for entity_name, expected_type in test_entities:
        # Test LLM classification directly
        result = service._classify_entity_type_llm(entity_name)

        status = "✅" if result == expected_type else "❌"
        print(f"{status} {entity_name:30} -> {result or 'NONE':12} (expected: {expected_type})")

        if result == expected_type:
            success_count += 1
        else:
            fail_count += 1

    print()
    print("=" * 50)
    print(f"Results: {success_count}/{len(test_entities)} passed")

    if fail_count > 0:
        print()
        print("Note: If classifications are returning None, check:")
        print("  1. OPENROUTER_API_KEY is valid and has credits")
        print("  2. ENABLE_LLM_CLASSIFICATION=true in .env.local")
        print("  3. Network connectivity to openrouter.ai")
        print("  4. PM2 logs for error messages: pm2 logs epstein-backend")

    return fail_count == 0

if __name__ == "__main__":
    success = test_openrouter_classification()
    sys.exit(0 if success else 1)
