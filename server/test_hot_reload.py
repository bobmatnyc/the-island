#!/usr/bin/env python3
"""
Test script for hot-reload functionality

This script simulates file updates to test the SSE hot-reload system:
1. Touches a watched JSON file
2. Waits for file watcher to detect change
3. Broadcasts event to connected SSE clients
4. Frontend should reload data automatically

Usage:
    python3 test_hot_reload.py [file_to_touch]

Examples:
    python3 test_hot_reload.py entity_network.json
    python3 test_hot_reload.py timeline_events.json
"""

import sys
import time
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"

# Files that can be touched for testing
WATCHABLE_FILES = {
    "entity_network": METADATA_DIR / "entity_network.json",
    "timeline": METADATA_DIR / "timeline_events.json",
    "entities": METADATA_DIR / "master_document_index.json",
    "documents": METADATA_DIR / "unified_document_index.json",
    "cases": METADATA_DIR / "cases_index.json",
    "victims": METADATA_DIR / "victims_index.json",
    "entity_mappings": METADATA_DIR / "entity_name_mappings.json",
    "entity_filter": METADATA_DIR / "entity_filter_list.json",
}


def touch_file(file_path: Path):
    """Touch a file to update its modification time"""
    if not file_path.exists():
        print(f"❌ File does not exist: {file_path}")
        return False

    # Update modification time
    file_path.touch()
    print(f"✅ Touched file: {file_path.name}")
    print(f"   Path: {file_path}")
    print(f"   Modified: {time.ctime(file_path.stat().st_mtime)}")
    return True


def main():
    """Main test function"""
    print("=" * 70)
    print("HOT-RELOAD TESTING SCRIPT")
    print("=" * 70)
    print()

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage: python3 test_hot_reload.py [file_type]")
        print()
        print("Available file types:")
        for key, path in WATCHABLE_FILES.items():
            status = "✓" if path.exists() else "✗"
            print(f"  {status} {key:20s} → {path.name}")
        print()
        print("Examples:")
        print("  python3 test_hot_reload.py entity_network")
        print("  python3 test_hot_reload.py timeline")
        return 1

    file_type = sys.argv[1]

    # Find file to touch
    if file_type in WATCHABLE_FILES:
        file_path = WATCHABLE_FILES[file_type]
    elif file_type.endswith('.json'):
        # Direct filename specified
        file_path = METADATA_DIR / file_type
    else:
        print(f"❌ Unknown file type: {file_type}")
        print()
        print("Available types:", ", ".join(WATCHABLE_FILES.keys()))
        return 1

    # Touch the file
    print(f"Testing hot-reload for: {file_type}")
    print()

    if not touch_file(file_path):
        return 1

    print()
    print("Expected behavior:")
    print(f"  1. File watcher detects change to {file_path.name}")
    print(f"  2. After 1 second debounce, broadcasts '{file_type}_updated' event")
    print("  3. Connected SSE clients receive event")
    print("  4. Frontend shows toast notification and reloads data")
    print()
    print("To verify:")
    print("  - Check server logs for file change detection")
    print("  - Open browser console to see '[App] ... updated, reloading...'")
    print("  - Look for toast notification in bottom-right corner")
    print()
    print("✅ Test complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
