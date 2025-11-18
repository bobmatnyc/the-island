"""
Shared Validation Functions

Design Decision: Reusable Validators
Rationale: Common validation logic extracted into reusable functions
to avoid duplication and ensure consistency across models.

Performance: Validators run during model construction and on assignment
(when validate_assignment=True). For performance-critical paths,
consider disabling validation after initial load.
"""

import re
from typing import List, Optional


def normalize_entity_name(name: str) -> str:
    """Normalize entity name for consistent matching.

    Normalization rules:
    - Strip leading/trailing whitespace
    - Collapse multiple spaces to single space
    - Preserve case (case-insensitive matching happens at query time)

    Args:
        name: Raw entity name

    Returns:
        Normalized name

    Example:
        >>> normalize_entity_name("  Epstein,  Jeffrey  ")
        "Epstein, Jeffrey"
    """
    if not name:
        return ""

    # Strip and collapse whitespace
    normalized = re.sub(r'\s+', ' ', name.strip())

    return normalized


def validate_entity_name(name: str) -> str:
    """Validate entity name format.

    Validation rules:
    - Must not be empty after normalization
    - Must be at least 2 characters
    - Must not be a generic placeholder (Male, Female, etc.)

    Args:
        name: Entity name to validate

    Returns:
        Validated name

    Raises:
        ValueError: If name is invalid

    Example:
        >>> validate_entity_name("Epstein, Jeffrey")
        "Epstein, Jeffrey"
        >>> validate_entity_name("Male")
        ValueError: Generic entity names not allowed
    """
    normalized = normalize_entity_name(name)

    if not normalized:
        raise ValueError("Entity name cannot be empty")

    if len(normalized) < 2:
        raise ValueError("Entity name must be at least 2 characters")

    # Generic names to reject (from entity_filtering.py)
    generic_names = {
        "male", "female", "adult male", "adult female",
        "child", "teenager", "unknown", "unnamed",
        "no passengers"
    }

    if normalized.lower() in generic_names:
        raise ValueError(f"Generic entity names not allowed: {normalized}")

    return normalized


def validate_connection_count(count: int) -> int:
    """Validate connection count is non-negative.

    Args:
        count: Connection count

    Returns:
        Validated count

    Raises:
        ValueError: If count is negative

    Example:
        >>> validate_connection_count(10)
        10
        >>> validate_connection_count(-1)
        ValueError: Connection count cannot be negative
    """
    if count < 0:
        raise ValueError("Connection count cannot be negative")
    return count


def validate_flight_count(count: int) -> int:
    """Validate flight count is non-negative.

    Args:
        count: Flight count

    Returns:
        Validated count

    Raises:
        ValueError: If count is negative

    Example:
        >>> validate_flight_count(5)
        5
        >>> validate_flight_count(-1)
        ValueError: Flight count cannot be negative
    """
    if count < 0:
        raise ValueError("Flight count cannot be negative")
    return count


def validate_tags(tags: List[str]) -> List[str]:
    """Validate tag list.

    Validation rules:
    - Must have at least one tag
    - Tags must not be empty strings
    - Tags are normalized (lowercase, stripped)
    - Duplicates are removed

    Args:
        tags: List of tags

    Returns:
        Validated and normalized tag list

    Raises:
        ValueError: If tags list is empty or contains invalid tags

    Example:
        >>> validate_tags(["Politics", "  Business  ", "politics"])
        ["politics", "business"]
    """
    if not tags:
        raise ValueError("At least one tag required")

    # Normalize tags: lowercase, strip, remove duplicates
    normalized = []
    seen = set()

    for tag in tags:
        tag = tag.strip().lower()
        if not tag:
            raise ValueError("Empty tags not allowed")
        if tag not in seen:
            normalized.append(tag)
            seen.add(tag)

    if not normalized:
        raise ValueError("At least one valid tag required")

    return normalized


def validate_biography_length(bio: str, min_length: int = 10) -> str:
    """Validate biography text length.

    Args:
        bio: Biography text
        min_length: Minimum required length (default: 10)

    Returns:
        Validated biography

    Raises:
        ValueError: If biography is too short

    Example:
        >>> validate_biography_length("A very short bio")
        "A very short bio"
        >>> validate_biography_length("Too short")
        ValueError: Biography must be at least 10 characters
    """
    if len(bio.strip()) < min_length:
        raise ValueError(f"Biography must be at least {min_length} characters")
    return bio.strip()


def sort_connections_by_strength(
    connections: List[dict]
) -> List[dict]:
    """Sort connections by flights_together descending.

    Args:
        connections: List of connection dicts with 'flights_together' key

    Returns:
        Sorted connection list (strongest first)

    Example:
        >>> connections = [
        ...     {"name": "A", "flights_together": 5},
        ...     {"name": "B", "flights_together": 10}
        ... ]
        >>> sorted_conns = sort_connections_by_strength(connections)
        >>> sorted_conns[0]["flights_together"]
        10
    """
    return sorted(
        connections,
        key=lambda x: x.get("flights_together", 0),
        reverse=True
    )
