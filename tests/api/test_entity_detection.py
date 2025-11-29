#!/usr/bin/env python3
"""Test Entity Detection Module

Tests entity detection functionality and performance.

Usage:
    python3 test_entity_detection.py
"""

import sys
import time
import json
from pathlib import Path

# Add server directory to path
sys.path.insert(0, str(Path(__file__).parent / "server"))

from entity_detector import get_entity_detector


def test_basic_detection():
    """Test basic entity detection with known entities."""
    print("=" * 80)
    print("TEST 1: Basic Entity Detection")
    print("=" * 80)

    detector = get_entity_detector()

    # Test text with known entities
    test_text = """
    Jeffrey Epstein and Ghislaine Maxwell were charged with multiple crimes.
    Bill Clinton flew on Epstein's plane several times.
    Prince Andrew denied allegations related to Jeffrey Epstein's activities.
    Virginia Roberts Giuffre filed a lawsuit against Epstein and Maxwell.
    """

    start_time = time.time()
    entities = detector.detect_entities(test_text, max_results=10)
    elapsed_ms = (time.time() - start_time) * 1000

    print(f"\nTest text length: {len(test_text)} characters")
    print(f"Detection time: {elapsed_ms:.2f}ms")
    print(f"Entities detected: {len(entities)}\n")

    for i, entity in enumerate(entities, 1):
        print(f"{i}. {entity.name}")
        print(f"   GUID: {entity.guid}")
        print(f"   Mentions: {entity.mentions}")
        print(f"   Type: {entity.entity_type}")
        print()

    # Verify expected entities
    entity_names = {e.name for e in entities}
    expected = ["Jeffrey Epstein", "Ghislaine Maxwell", "Bill Clinton", "Prince Andrew"]

    print("Expected entities check:")
    for name in expected:
        found = any(name.lower() in entity_names or entity_name.lower() in name.lower()
                   for entity_name in entity_names)
        status = "✓" if found else "✗"
        print(f"  {status} {name}")

    print()
    return elapsed_ms < 200  # Should be under 200ms for short text


def test_real_document():
    """Test with real OCR text from a document."""
    print("=" * 80)
    print("TEST 2: Real Document Entity Detection")
    print("=" * 80)

    # Find a document with OCR text
    ocr_dir = Path("data/sources/house_oversight_nov2025/ocr_text")
    if not ocr_dir.exists():
        print("⚠ OCR directory not found, skipping real document test")
        return True

    # Get first OCR file
    ocr_files = list(ocr_dir.glob("*.txt"))
    if not ocr_files:
        print("⚠ No OCR files found, skipping real document test")
        return True

    test_file = ocr_files[0]
    print(f"\nTesting with: {test_file.name}")

    with open(test_file, "r", encoding="utf-8") as f:
        full_text = f.read()

    print(f"Document length: {len(full_text):,} characters")

    detector = get_entity_detector()

    start_time = time.time()
    entities = detector.detect_entities(full_text, max_results=20)
    elapsed_ms = (time.time() - start_time) * 1000

    print(f"Detection time: {elapsed_ms:.2f}ms")
    print(f"Entities detected: {len(entities)}\n")

    print("Top 10 entities by mentions:")
    for i, entity in enumerate(entities[:10], 1):
        print(f"{i:2d}. {entity.name:<30} ({entity.mentions:3d} mentions)")

    print()
    performance_ok = elapsed_ms < 500  # Target: <500ms
    print(f"Performance: {'✓ PASS' if performance_ok else '✗ FAIL'} ({elapsed_ms:.0f}ms vs 500ms target)")
    print()

    return performance_ok


def test_edge_cases():
    """Test edge cases and error handling."""
    print("=" * 80)
    print("TEST 3: Edge Cases")
    print("=" * 80)

    detector = get_entity_detector()

    # Test 1: Empty text
    print("\n1. Empty text:")
    entities = detector.detect_entities("")
    print(f"   Result: {len(entities)} entities (expected: 0)")
    assert len(entities) == 0, "Should return empty list for empty text"
    print("   ✓ PASS")

    # Test 2: Text with no entities
    print("\n2. Text with no known entities:")
    entities = detector.detect_entities("This is a test document with no relevant names.")
    print(f"   Result: {len(entities)} entities")
    print("   ✓ PASS")

    # Test 3: Very long text
    print("\n3. Very long text (10,000 characters):")
    long_text = "Jeffrey Epstein " * 625  # ~10,000 characters
    start_time = time.time()
    entities = detector.detect_entities(long_text)
    elapsed_ms = (time.time() - start_time) * 1000
    print(f"   Detection time: {elapsed_ms:.2f}ms")
    print(f"   Mentions found: {entities[0].mentions if entities else 0}")
    print("   ✓ PASS")

    # Test 4: Case insensitivity
    print("\n4. Case insensitivity:")
    test_cases = ["JEFFREY EPSTEIN", "jeffrey epstein", "Jeffrey Epstein"]
    for text in test_cases:
        entities = detector.detect_entities(text)
        found = len(entities) > 0
        print(f"   '{text}': {'✓ Found' if found else '✗ Not found'}")

    print()
    return True


def test_performance_benchmark():
    """Benchmark entity detection performance."""
    print("=" * 80)
    print("TEST 4: Performance Benchmark")
    print("=" * 80)

    detector = get_entity_detector()

    # Create test texts of varying sizes
    test_sizes = [
        (500, "Small preview (~500 chars)"),
        (3000, "Standard preview (~3000 chars)"),
        (10000, "Large document (~10K chars)"),
        (50000, "Very large document (~50K chars)"),
    ]

    base_text = """
    Jeffrey Epstein operated a trafficking network with Ghislaine Maxwell.
    Bill Clinton and Prince Andrew were associated with Epstein.
    Virginia Roberts Giuffre testified against them.
    """

    print("\nPerformance by document size:")
    print("-" * 60)

    results = []
    for size, description in test_sizes:
        # Create text of target size
        repetitions = size // len(base_text) + 1
        test_text = (base_text * repetitions)[:size]

        start_time = time.time()
        entities = detector.detect_entities(test_text, max_results=20)
        elapsed_ms = (time.time() - start_time) * 1000

        results.append((description, size, elapsed_ms, len(entities)))
        status = "✓" if elapsed_ms < 500 else "⚠"
        print(f"{status} {description:<30} {elapsed_ms:6.1f}ms  ({len(entities)} entities)")

    print()
    print("Summary:")
    avg_time = sum(r[2] for r in results) / len(results)
    print(f"  Average detection time: {avg_time:.1f}ms")
    print(f"  Target met (<500ms): {'✓ YES' if avg_time < 500 else '✗ NO'}")
    print()

    return avg_time < 500


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Entity Detection Test Suite" + " " * 31 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    tests = [
        ("Basic Detection", test_basic_detection),
        ("Real Document", test_real_document),
        ("Edge Cases", test_edge_cases),
        ("Performance Benchmark", test_performance_benchmark),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"✗ TEST FAILED: {e}")
            results.append((test_name, False))

    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} {test_name}")

    print()
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    print(f"Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
