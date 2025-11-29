#!/usr/bin/env python3
"""
Entity Filtering Utility

Filters generic, non-disambiguatable entities from network and search results.
Prevents generic terms like "Male", "Female", "Nanny (1)" from appearing as entities.

Design Decision: Centralized Filter List
Rationale: Single source of truth for generic entity patterns prevents inconsistent
filtering across different components (network, search, API).

Usage:
    from utils.entity_filtering import EntityFilter

    filter = EntityFilter()
    if filter.is_generic("Male (1)"):
        # Skip this entity
        pass

    # Filter list of entities
    clean_entities = filter.filter_entities(entities)
"""

import json
from pathlib import Path
from typing import Any


class EntityFilter:
    """Filter generic, non-disambiguatable entities.

    Loads filter list from data/metadata/entity_filter_list.json
    and provides methods to check if entity should be filtered.
    """

    def __init__(self, filter_list_path: Path | None = None):
        """Initialize entity filter.

        Args:
            filter_list_path: Path to filter list JSON. Defaults to canonical location.
        """
        if filter_list_path is None:
            # Default to canonical location
            project_root = Path(__file__).parent.parent.parent
            filter_list_path = project_root / "data/metadata/entity_filter_list.json"

        self.filter_list_path = filter_list_path
        self._generic_entities: set[str] = set()
        self._load_filter_list()

    def _load_filter_list(self) -> None:
        """Load filter list from JSON file.

        Error Handling: If file doesn't exist, creates empty filter set
        (fail-safe: no filtering is better than crashing).
        """
        if not self.filter_list_path.exists():
            print(f"WARNING: Filter list not found at {self.filter_list_path}")
            print("No entities will be filtered. Run rebuild_flight_network.py to regenerate.")
            return

        try:
            with open(self.filter_list_path) as f:
                data = json.load(f)

            # Flatten all filtered entity lists
            filtered = data.get("filtered_entities", {})
            for category_entities in filtered.values():
                if isinstance(category_entities, list):
                    self._generic_entities.update(category_entities)

            print(
                f"Loaded {len(self._generic_entities)} filtered entities from {self.filter_list_path.name}"
            )

        except Exception as e:
            print(f"ERROR loading filter list: {e}")
            print("No entities will be filtered.")

    def is_generic(self, entity_name: str) -> bool:
        """Check if entity name is generic and should be filtered.

        Args:
            entity_name: Entity name to check

        Returns:
            True if entity is generic and should be excluded
        """
        return entity_name in self._generic_entities

    def filter_entities(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Filter list of entity dictionaries.

        Removes entities where entity["name"] is in filter list.

        Args:
            entities: List of entity dicts (must have "name" key)

        Returns:
            Filtered list with generic entities removed
        """
        return [e for e in entities if not self.is_generic(e.get("name", ""))]

    def filter_entity_names(self, names: list[str]) -> list[str]:
        """Filter list of entity names.

        Args:
            names: List of entity name strings

        Returns:
            Filtered list with generic names removed
        """
        return [name for name in names if not self.is_generic(name)]

    def get_filtered_count(self) -> int:
        """Get count of filtered entities."""
        return len(self._generic_entities)

    def get_filter_categories(self) -> dict[str, list[str]]:
        """Get filter categories with entity lists.

        Returns:
            Dict mapping category names to filtered entity lists
        """
        if not self.filter_list_path.exists():
            return {}

        with open(self.filter_list_path) as f:
            data = json.load(f)

        return data.get("filtered_entities", {})

    def get_filter_rationale(self) -> str:
        """Get human-readable rationale for filtering.

        Returns:
            Explanation of why entities are filtered
        """
        if not self.filter_list_path.exists():
            return "Filter list not available"

        with open(self.filter_list_path) as f:
            data = json.load(f)

        return data.get("filtering_rationale", "No rationale provided")


# Convenience function for quick filtering
def is_generic_entity(entity_name: str, filter_instance: EntityFilter | None = None) -> bool:
    """Quick check if entity is generic (module-level function).

    Args:
        entity_name: Entity name to check
        filter_instance: Optional existing filter instance (creates new if None)

    Returns:
        True if entity is generic
    """
    if filter_instance is None:
        filter_instance = EntityFilter()

    return filter_instance.is_generic(entity_name)
