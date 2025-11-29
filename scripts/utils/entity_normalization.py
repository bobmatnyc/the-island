#!/usr/bin/env python3
"""
Entity name normalization utilities.

Provides functions to normalize entity names across all data sources.
"""

import json
import re
from pathlib import Path
from typing import Optional


class EntityNormalizer:
    """Handles entity name normalization using mapping file."""

    def __init__(self, mappings_path: Optional[Path] = None):
        """Initialize normalizer with mappings file.

        Args:
            mappings_path: Path to entity_name_mappings.json
                          If None, uses default location
        """
        if mappings_path is None:
            project_root = Path(__file__).parent.parent.parent
            mappings_path = project_root / "data" / "metadata" / "entity_name_mappings.json"

        self.mappings_path = mappings_path
        self.mappings: dict[str, str] = {}
        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load name mappings from JSON file."""
        if not self.mappings_path.exists():
            print(f"Warning: Mappings file not found at {self.mappings_path}")
            print("Run: python3 scripts/utils/build_entity_mappings.py")
            return

        with open(self.mappings_path) as f:
            self.mappings = json.load(f)

    def normalize(self, name: str) -> str:
        """Normalize a single entity name.

        Args:
            name: Original entity name

        Returns:
            Canonical entity name (or original if no mapping exists)
        """
        if not name:
            return name

        # Step 1: Normalize whitespace first
        normalized_ws = re.sub(r"\s+", " ", name).strip()

        # Step 2: Check direct mapping
        if normalized_ws in self.mappings:
            return self.mappings[normalized_ws]

        # Step 3: Check original name mapping
        if name in self.mappings:
            return self.mappings[name]

        # Step 4: No mapping found, return whitespace-normalized version
        return normalized_ws

    def normalize_list(self, names: list[str]) -> list[str]:
        """Normalize a list of entity names.

        Args:
            names: List of original entity names

        Returns:
            List of canonical entity names
        """
        return [self.normalize(name) for name in names]

    def get_all_variants(self, canonical_name: str) -> list[str]:
        """Get all known variants of a canonical name.

        Args:
            canonical_name: The canonical entity name

        Returns:
            List of all variant names (including canonical)
        """
        variants = [canonical_name]
        for variant, canonical in self.mappings.items():
            if canonical == canonical_name and variant != canonical_name:
                variants.append(variant)
        return variants

    def stats(self) -> dict:
        """Get statistics about loaded mappings.

        Returns:
            Dictionary with mapping statistics
        """
        if not self.mappings:
            return {"total_mappings": 0, "unique_canonical": 0}

        unique_canonical = len(set(self.mappings.values()))

        return {
            "total_mappings": len(self.mappings),
            "unique_canonical": unique_canonical,
            "top_entities": self._get_top_entities(5),
        }

    def _get_top_entities(self, n: int = 5) -> list[tuple[str, int]]:
        """Get entities with most variants.

        Args:
            n: Number of top entities to return

        Returns:
            List of (canonical_name, variant_count) tuples
        """
        from collections import Counter

        canonical_counts = Counter(self.mappings.values())
        return canonical_counts.most_common(n)


# Singleton instance for easy importing
_normalizer_instance: Optional[EntityNormalizer] = None


def get_normalizer() -> EntityNormalizer:
    """Get singleton normalizer instance.

    Returns:
        EntityNormalizer instance
    """
    global _normalizer_instance
    if _normalizer_instance is None:
        _normalizer_instance = EntityNormalizer()
    return _normalizer_instance


def normalize_name(name: str) -> str:
    """Convenience function to normalize a single name.

    Args:
        name: Original entity name

    Returns:
        Canonical entity name
    """
    return get_normalizer().normalize(name)


def normalize_names(names: list[str]) -> list[str]:
    """Convenience function to normalize a list of names.

    Args:
        names: List of original entity names

    Returns:
        List of canonical entity names
    """
    return get_normalizer().normalize_list(names)


if __name__ == "__main__":
    # Test normalization
    normalizer = EntityNormalizer()

    test_names = [
        "Je        Je Epstein",
        "Je         Je Epstein",
        "Je          Je Epstein",
        "Jeffrey Epstein",
        "Ghislaine Ghislaine",
        "Ghislaine Maxwell",
        "Bill Clinton",
        "Bill        Bill Clinton",
        "Unknown Person",
    ]

    print("Entity Name Normalization Test")
    print("=" * 70)
    print(f"\nLoaded {normalizer.stats()['total_mappings']} mappings")
    print(f"Covering {normalizer.stats()['unique_canonical']} unique entities")

    print("\nTest Normalizations:")
    print("-" * 70)
    for name in test_names:
        canonical = normalizer.normalize(name)
        status = "✓" if canonical != name else "→"
        print(f"{status} '{name}' -> '{canonical}'")

    print("\nTop Entities by Variant Count:")
    print("-" * 70)
    for canonical, count in normalizer.stats()["top_entities"]:
        print(f"  {canonical}: {count} variants")
        variants = normalizer.get_all_variants(canonical)
        for variant in variants[:3]:
            if variant != canonical:
                print(f"    - {variant}")
        if len(variants) > 4:
            print(f"    ... and {len(variants) - 4} more")
