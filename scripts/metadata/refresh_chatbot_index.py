#!/usr/bin/env python3
"""Refresh chatbot knowledge index.

Lightweight script to rebuild the chatbot knowledge index.
Should be run after:
- New documents downloaded
- Classifications completed
- Entity extraction updates
- Network analysis updates

Usage:
    python3 scripts/metadata/refresh_chatbot_index.py
"""

import sys
from pathlib import Path


# Add scripts directory to path
scripts_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(scripts_dir))

from metadata.build_chatbot_knowledge_index import build_knowledge_index


def main():
    """Refresh the knowledge index."""
    base_path = Path(__file__).resolve().parents[2]

    print("Refreshing chatbot knowledge index...")

    # Build index
    index = build_knowledge_index(base_path)

    # Write to file
    output_path = base_path / "data" / "metadata" / "chatbot_knowledge_index.json"
    import json
    with open(output_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\n✓ Knowledge index refreshed: {output_path}")
    print("\nQuick Stats:")
    for key, value in index["quick_stats"].items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
