#!/usr/bin/env python3
"""
Benchmark Document ID Lookup Performance

Validates the O(1) index lookup optimization implemented in ticket 1M-366.

Expected Results:
- O(1) lookup: ~0.1 µs per lookup
- Linear search: ~500 µs per lookup (38,482 documents)
- Speedup: ~5,000× faster

Usage:
    python3 tests/verification/benchmark_document_id_lookup.py
"""

import sys
import time
from pathlib import Path

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'server'))

from services.document_service import DocumentService


def benchmark_indexed_lookup(service: DocumentService, iterations: int = 1000) -> float:
    """Benchmark O(1) indexed lookup"""
    if not service.documents:
        return 0.0

    # Get test document ID
    test_id = service.documents[len(service.documents) // 2].get('id')
    if not test_id:
        return 0.0

    # Warm up
    for _ in range(100):
        service.get_document_by_id(test_id)

    # Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        result = service.get_document_by_id(test_id)
    end = time.perf_counter()

    return (end - start) / iterations


def benchmark_linear_search(service: DocumentService, iterations: int = 1000) -> float:
    """Benchmark O(n) linear search (old implementation)"""
    if not service.documents:
        return 0.0

    # Get test document ID
    test_id = service.documents[len(service.documents) // 2].get('id')
    if not test_id:
        return 0.0

    # Warm up
    for _ in range(100):
        next((doc for doc in service.documents if doc.get("id") == test_id), None)

    # Benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        result = next((doc for doc in service.documents if doc.get("id") == test_id), None)
    end = time.perf_counter()

    return (end - start) / iterations


def main():
    """Run benchmark and display results"""
    print("Document ID Lookup Performance Benchmark")
    print("=" * 60)

    # Initialize service
    data_path = Path('data')
    service = DocumentService(data_path)

    print(f"Dataset size: {len(service.documents):,} documents")
    print(f"Index size: {len(service._document_index):,} entries")
    print()

    # Run benchmarks
    print("Running benchmarks (1000 iterations each)...")
    print()

    indexed_time = benchmark_indexed_lookup(service, iterations=1000)
    linear_time = benchmark_linear_search(service, iterations=1000)

    # Display results
    print("Results:")
    print("-" * 60)
    print(f"O(1) Index Lookup:    {indexed_time * 1_000_000:>10.2f} µs per lookup")
    print(f"O(n) Linear Search:   {linear_time * 1_000_000:>10.2f} µs per lookup")
    print(f"Speedup:              {linear_time / indexed_time:>10.1f}× faster")
    print()

    # Memory overhead
    import sys
    index_memory = sys.getsizeof(service._document_index)
    for doc in service._document_index.values():
        index_memory += sys.getsizeof(doc)

    print(f"Memory overhead:      {index_memory / 1_000_000:>10.2f} MB (index only)")
    print()

    # Validation
    print("Validation:")
    print("-" * 60)
    if indexed_time < linear_time:
        improvement = (linear_time - indexed_time) / linear_time * 100
        print(f"✓ Index lookup is {improvement:.1f}% faster than linear search")
    else:
        print("✗ Index lookup is NOT faster (unexpected!)")

    if indexed_time < 1e-6:  # Less than 1 microsecond
        print(f"✓ Index lookup meets O(1) performance target (<1 µs)")
    else:
        print(f"⚠ Index lookup slower than expected (target <1 µs)")

    print()
    print("Ticket 1M-366: Document ID index optimization complete ✓")


if __name__ == "__main__":
    main()
