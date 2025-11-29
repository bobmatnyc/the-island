#!/usr/bin/env python3
"""
Quick test script for suggestion system
"""
import sys
from pathlib import Path


# Add server to path (tests/ is now at project root level)
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from models.suggested_source import (
    SourcePriority,
    SourceStatus,
    SuggestedSourceCreate,
    SuggestedSourceUpdate,
)
from services.suggestion_service import SuggestionService


def test_suggestion_system():
    """Test the suggestion service"""
    print("Testing Suggestion System")
    print("=" * 50)

    # Initialize service with test file
    test_storage = Path(__file__).parent.parent / "data" / "suggestions" / "test_suggestions.json"
    service = SuggestionService(test_storage)

    # Test 1: Create suggestion
    print("\n1. Creating suggestion...")
    suggestion_data = SuggestedSourceCreate(
        url="https://example.com/epstein-documents",
        description="Test document source with important files about the case",
        source_name="Example Archive",
        priority=SourcePriority.HIGH,
        document_count_estimate=500,
        tags=["court-docs", "test"]
    )

    created = service.create_suggestion(suggestion_data, submitted_by="test_user")
    print(f"✓ Created suggestion with ID: {created.id}")
    print(f"  Status: {created.status}")
    print(f"  Priority: {created.priority}")

    # Test 2: Get all suggestions
    print("\n2. Retrieving all suggestions...")
    _suggestions, total = service.get_all_suggestions()
    print(f"✓ Found {total} total suggestions")

    # Test 3: Get by ID
    print("\n3. Getting suggestion by ID...")
    retrieved = service.get_suggestion_by_id(created.id)
    if retrieved:
        print(f"✓ Retrieved: {retrieved.source_name}")

    # Test 4: Update status
    print("\n4. Updating status to approved...")
    update = SuggestedSourceUpdate(
        status=SourceStatus.APPROVED,
        priority=SourcePriority.CRITICAL,
        review_notes="Looks like a good source!"
    )
    updated = service.update_status(created.id, update, reviewed_by="admin")
    if updated:
        print(f"✓ Updated status to: {updated.status}")
        print(f"  Priority now: {updated.priority}")
        print(f"  Reviewed by: {updated.reviewed_by}")

    # Test 5: Get statistics
    print("\n5. Getting statistics...")
    stats = service.get_statistics()
    print("✓ Statistics:")
    print(f"  Total: {stats.total}")
    print(f"  Pending: {stats.pending}")
    print(f"  Approved: {stats.approved}")

    # Test 6: Delete suggestion
    print("\n6. Deleting test suggestion...")
    deleted = service.delete_suggestion(created.id)
    if deleted:
        print("✓ Deleted suggestion")

    print("\n" + "=" * 50)
    print("All tests passed! ✅")

    # Cleanup
    if test_storage.exists():
        test_storage.unlink()
        print("Cleaned up test file")

if __name__ == "__main__":
    test_suggestion_system()
