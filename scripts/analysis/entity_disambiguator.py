#!/usr/bin/env python3
"""
Entity Disambiguation System
Identifies and merges duplicate entities with name variations
Uses fuzzy matching and heuristics to find similar names
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from difflib import SequenceMatcher
from collections import defaultdict
import re

PROJECT_ROOT = Path("/Users/masa/Projects/Epstein")
DATA_DIR = PROJECT_ROOT / "data"
MD_DIR = DATA_DIR / "md/entities"
METADATA_DIR = DATA_DIR / "metadata"

class EntityDisambiguator:
    """Disambiguate and merge entity name variations"""

    def __init__(self, similarity_threshold: float = 0.85):
        """
        Args:
            similarity_threshold: Minimum similarity (0-1) to consider names as duplicates
        """
        self.similarity_threshold = similarity_threshold
        self.entities = []
        self.entity_groups = []  # Groups of similar entities

    def load_entities(self, entities_index_path: Path):
        """Load entities from index"""
        with open(entities_index_path) as f:
            data = json.load(f)

        if "entities" in data:
            self.entities = data["entities"]
        else:
            # Old format - just list of entities
            self.entities = data

        print(f"Loaded {len(self.entities)} entities")

    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())

        # Remove common suffixes
        name = re.sub(r'\s+(Jr\.?|Sr\.?|III?|IV)$', '', name, flags=re.IGNORECASE)

        # Lowercase for comparison
        return name.lower()

    def name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names"""
        norm1 = self.normalize_name(name1)
        norm2 = self.normalize_name(name2)

        # Exact match
        if norm1 == norm2:
            return 1.0

        # Sequence matcher similarity
        seq_sim = SequenceMatcher(None, norm1, norm2).ratio()

        # Check for partial matches (e.g., "Bill Clinton" vs "William Clinton")
        parts1 = set(norm1.split())
        parts2 = set(norm2.split())

        # Jaccard similarity of name parts
        if parts1 and parts2:
            intersection = len(parts1.intersection(parts2))
            union = len(parts1.union(parts2))
            jaccard_sim = intersection / union

            # Use maximum of sequence and jaccard
            return max(seq_sim, jaccard_sim)

        return seq_sim

    def find_duplicates(self) -> List[List[Dict]]:
        """
        Find groups of duplicate entities

        Returns:
            List of entity groups (each group is a list of similar entities)
        """
        print("\nFinding duplicate entities...")

        # Create entity lookup by name
        entity_lookup = {}
        for entity in self.entities:
            name = entity.get("name", "")
            if name:
                entity_lookup[name] = entity

        # Find similar pairs
        duplicate_groups = []
        processed = set()

        for i, entity1 in enumerate(self.entities):
            name1 = entity1.get("name", "")
            if not name1 or name1 in processed:
                continue

            # Start a new group
            group = [entity1]
            processed.add(name1)

            # Find similar entities
            for j, entity2 in enumerate(self.entities[i+1:], i+1):
                name2 = entity2.get("name", "")
                if not name2 or name2 in processed:
                    continue

                similarity = self.name_similarity(name1, name2)

                if similarity >= self.similarity_threshold:
                    group.append(entity2)
                    processed.add(name2)

            # Only keep groups with duplicates
            if len(group) > 1:
                duplicate_groups.append(group)

        print(f"  Found {len(duplicate_groups)} duplicate groups")
        print(f"  Total duplicates: {sum(len(g) for g in duplicate_groups)}")

        self.entity_groups = duplicate_groups
        return duplicate_groups

    def merge_entities(self, entity_group: List[Dict]) -> Dict:
        """
        Merge a group of duplicate entities

        Strategy:
        - Use the longest name as canonical
        - Merge all properties (flights, sources, etc.)
        - Track all name variations
        """
        if not entity_group:
            return {}

        # Choose canonical name (longest)
        canonical = max(entity_group, key=lambda e: len(e.get("name", "")))

        # Merge properties
        merged = {
            "name": canonical.get("name", ""),
            "name_variations": [e.get("name", "") for e in entity_group],
            "in_black_book": any(e.get("in_black_book", False) for e in entity_group),
            "is_billionaire": any(e.get("is_billionaire", False) for e in entity_group),
            "trips": sum(e.get("trips", 0) for e in entity_group),
            "categories": list(set(cat for e in entity_group for cat in e.get("categories", []))),
            "sources": list(set(src for e in entity_group for src in e.get("sources", []))),
            "merged_from": len(entity_group)
        }

        # Merge contact info if available
        contact_info = {}
        for entity in entity_group:
            if "contact_info" in entity and entity["contact_info"]:
                contact_info.update(entity["contact_info"])

        if contact_info:
            merged["contact_info"] = contact_info

        return merged

    def create_disambiguation_report(self) -> str:
        """Generate human-readable disambiguation report"""
        report = [
            "=" * 70,
            "ENTITY DISAMBIGUATION REPORT",
            "=" * 70,
            "",
            f"Total entities analyzed: {len(self.entities)}",
            f"Duplicate groups found: {len(self.entity_groups)}",
            f"Entities with duplicates: {sum(len(g) for g in self.entity_groups)}",
            f"Similarity threshold: {self.similarity_threshold}",
            "",
            "DUPLICATE GROUPS (showing top 50):",
            "-" * 70
        ]

        # Sort groups by size
        sorted_groups = sorted(self.entity_groups, key=len, reverse=True)[:50]

        for i, group in enumerate(sorted_groups, 1):
            # Get merged entity
            merged = self.merge_entities(group)

            report.append(f"\n{i}. Canonical: {merged['name']} ({len(group)} variations)")
            report.append(f"   Variations:")
            for entity in group:
                name = entity.get("name", "")
                trips = entity.get("trips", 0)
                in_bb = "📖" if entity.get("in_black_book") else ""
                report.append(f"      - {name} {in_bb} (trips: {trips})")

            # Show merged stats
            report.append(f"   Merged: {merged['trips']} total trips, sources: {', '.join(merged['sources'])}")

        return "\n".join(report)

    def export_merged_index(self, output_path: Path):
        """
        Export merged entity index with canonical names

        Creates a new index with duplicates merged
        """
        print("\nMerging duplicates and exporting...")

        # Create merged entities
        merged_entities = []
        processed_names = set()

        for group in self.entity_groups:
            merged = self.merge_entities(group)
            merged_entities.append(merged)

            # Track all names in this group
            for entity in group:
                processed_names.add(entity.get("name", ""))

        # Add non-duplicate entities
        for entity in self.entities:
            name = entity.get("name", "")
            if name and name not in processed_names:
                # Add with name_variations field for consistency
                entity_copy = entity.copy()
                entity_copy["name_variations"] = [name]
                entity_copy["merged_from"] = 1
                merged_entities.append(entity_copy)

        # Save merged index
        output_data = {
            "generated": "2025-11-17T00:00:00",
            "total_entities": len(merged_entities),
            "original_entity_count": len(self.entities),
            "duplicates_merged": len(self.entity_groups),
            "entities_deduplicated": sum(len(g) for g in self.entity_groups),
            "similarity_threshold": self.similarity_threshold,
            "entities": merged_entities
        }

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"✓ Exported merged index: {output_path}")
        print(f"  Original: {len(self.entities)} entities")
        print(f"  Merged: {len(merged_entities)} entities")
        print(f"  Reduction: {len(self.entities) - len(merged_entities)} duplicates removed")

        return merged_entities

def main():
    """Run entity disambiguation"""
    print("=" * 70)
    print("ENTITY DISAMBIGUATION")
    print("=" * 70)

    disambiguator = EntityDisambiguator(similarity_threshold=0.85)

    # Load entities
    disambiguator.load_entities(MD_DIR / "ENTITIES_INDEX.json")

    # Find duplicates
    duplicate_groups = disambiguator.find_duplicates()

    # Generate report
    report = disambiguator.create_disambiguation_report()
    report_path = METADATA_DIR / "entity_disambiguation_report.txt"
    report_path.write_text(report)

    print(f"\n✓ Saved report: {report_path}")
    print("\n" + report[:2000] + "\n..." if len(report) > 2000 else report)

    # Export merged index
    merged_index_path = MD_DIR / "ENTITIES_INDEX_MERGED.json"
    merged_entities = disambiguator.export_merged_index(merged_index_path)

    print("\n" + "=" * 70)
    print("DISAMBIGUATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("  1. Review disambiguation report for accuracy")
    print("  2. Use merged index for analysis and search")
    print("  3. Rebuild network with canonical names")

if __name__ == "__main__":
    main()
