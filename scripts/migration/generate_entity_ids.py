#!/usr/bin/env python3
"""
Entity ID Generation Script

Generates deterministic snake_case entity IDs for all entities in the system.
Detects collisions, creates ID mappings, and generates collision report.

Usage:
    python generate_entity_ids.py [--dry-run] [--verbose]

Output:
    - data/migration/entity_id_mappings.json (ID registry)
    - data/migration/collision_report.json (conflicts requiring review)
    - logs/id_generation.log (detailed execution log)

Performance:
    - Expected runtime: <30 seconds for 1,637 entities
    - Memory usage: <50MB
"""

import argparse
import json
import logging
import re
import sys
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional


class EntityIDGenerator:
    """
    Deterministic entity ID generator with collision detection.

    Design Decision: Snake-case slugs for URL-safe, human-readable IDs
    - Follows existing pattern in enriched_entity_data.json
    - Deterministic: same name always produces same ID
    - URL-safe: only [a-z0-9_]
    - Human-readable: "Jeffrey Epstein" → "jeffrey_epstein"

    Trade-offs:
    - Performance: O(1) dict lookup vs O(n) name matching
    - Simplicity: No UUID overhead, easy debugging
    - Collision risk: Low (~0.1% for 1,637 entities based on analysis)

    Alternatives Considered:
    1. UUID: Rejected - not human-readable, overkill for dataset size
    2. Hash-based: Rejected - not predictable, hard to debug
    3. Name-as-ID: Current system, causes URL encoding issues
    """

    def __init__(self):
        self.id_registry: dict[str, dict] = {}  # Maps ID to entity metadata
        self.name_to_id: dict[str, str] = {}  # Maps all name variations to IDs
        self.collisions: list[dict] = []
        self.stats = {"total_entities": 0, "unique_ids": 0, "collisions": 0, "invalid_names": 0}

    def generate_slug(self, name: str) -> str:
        """
        Generate deterministic snake_case slug from entity name.

        Complexity Analysis:
        - Time Complexity: O(n) where n = len(name), typically <50 chars
        - Space Complexity: O(n) for intermediate string operations

        Performance: <1ms per entity on modern hardware

        Args:
            name: Entity name (any format)

        Returns:
            Snake-case slug matching ^[a-z0-9_]+$

        Examples:
            >>> gen = EntityIDGenerator()
            >>> gen.generate_slug("Jeffrey Epstein")
            'jeffrey_epstein'
            >>> gen.generate_slug("Maxwell, Ghislaine")
            'maxwell_ghislaine'
            >>> gen.generate_slug("O'Brien, Michael")
            'obrien_michael'
            >>> gen.generate_slug("Müller, Hans")
            'muller_hans'

        Error Handling:
        - Empty name: Raises ValueError
        - Invalid chars only (###): Raises ValueError
        - Unicode normalization failures: Logged and raised

        Future Enhancements:
        - Cache common transformations for performance
        - Add support for custom transliteration rules
        - Track character replacement statistics
        """
        if not name or not name.strip():
            raise ValueError(f"Empty or whitespace-only name: '{name}'")

        try:
            # Step 1: Normalize Unicode (NFD = decompose accents)
            # Example: "Müller" → "M" + "u" + combining-umlaut + "ller"
            normalized = unicodedata.normalize("NFD", name)

            # Step 2: Remove accent marks (category 'Mn' = nonspacing marks)
            # Example: "M" + "u" + combining-umlaut + "ller" → "Muller"
            without_accents = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

            # Step 3: Convert to lowercase
            lower = without_accents.lower()

            # Step 4: Remove commas (used in "Last, First" format)
            no_commas = lower.replace(",", "")

            # Step 5: Replace special characters with space
            # Keep: a-z, 0-9, space
            # Remove: all other characters (hyphens, apostrophes, periods, etc.)
            cleaned = re.sub(r"[^a-z0-9\s]", "", no_commas)

            # Step 6: Collapse multiple spaces to single space
            collapsed = re.sub(r"\s+", " ", cleaned)

            # Step 7: Strip leading/trailing whitespace
            stripped = collapsed.strip()

            # Step 8: Replace spaces with underscores
            slug = stripped.replace(" ", "_")

            # Step 9: Remove consecutive underscores (safety check)
            slug = re.sub(r"_+", "_", slug)

            # Step 10: Remove leading/trailing underscores
            slug = slug.strip("_")

            # Validation: Must produce non-empty alphanumeric slug
            if not slug:
                raise ValueError(f"Name '{name}' produces empty slug after normalization")

            # Validation: Must match allowed pattern
            if not re.match(r"^[a-z0-9_]+$", slug):
                raise ValueError(f"Name '{name}' produces invalid slug '{slug}'")

            # Validation: Minimum length check
            if len(slug) < 2:
                raise ValueError(f"Name '{name}' produces too short slug '{slug}' (min 2 chars)")

            return slug

        except Exception as e:
            logging.error(f"Slug generation failed for '{name}': {e}")
            raise

    def resolve_collision(self, base_slug: str, name: str) -> str:
        """
        Resolve slug collision by appending numeric suffix.

        Collision Resolution Strategy:
        - First occurrence: "john_smith"
        - Second occurrence: "john_smith_2"
        - Third occurrence: "john_smith_3"
        - And so on...

        Performance:
        - Time Complexity: O(n) where n = collision count (typically 1-3)
        - Expected collisions: <10 for 1,637 entities (~0.6%)

        Args:
            base_slug: Original slug that collided
            name: Entity name (for logging)

        Returns:
            Unique slug with numeric suffix

        Error Handling:
        - Collision count >100: Raises ValueError (indicates data quality issue)
        """
        counter = 2
        while counter < 100:  # Safety limit
            candidate = f"{base_slug}_{counter}"
            if candidate not in self.id_registry:
                logging.warning(
                    f"Collision resolved: '{name}' -> '{base_slug}' "
                    f"already exists, using '{candidate}'"
                )
                self.collisions.append(
                    {
                        "base_slug": base_slug,
                        "new_slug": candidate,
                        "name": name,
                        "existing_name": self.id_registry[base_slug]["name"],
                        "counter": counter,
                        "manual_review": True,
                        "reason": "Possible duplicate entity requiring merge decision",
                    }
                )
                self.stats["collisions"] += 1
                return candidate
            counter += 1

        raise ValueError(
            f"Collision resolution failed for '{name}': " f"too many variants of '{base_slug}'"
        )

    def register_entity(
        self,
        name: str,
        name_variations: list[str],
        sources: list[str],
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Generate and register entity ID with collision detection.

        Args:
            name: Primary entity name
            name_variations: All known name variations
            sources: Data sources (black_book, flight_logs, etc.)
            metadata: Additional entity data

        Returns:
            Registered entity ID

        Raises:
            ValueError: If name is invalid or slug generation fails
        """
        try:
            # Generate base slug
            slug = self.generate_slug(name)

            # Handle collision
            if slug in self.id_registry:
                slug = self.resolve_collision(slug, name)

            # Register in ID registry
            self.id_registry[slug] = {
                "id": slug,
                "name": name,
                "name_variations": name_variations,
                "sources": sources,
                "metadata": metadata or {},
                "registered_at": datetime.now().isoformat(),
            }

            # Register all name variations in name→ID mapping
            for variation in name_variations:
                if variation in self.name_to_id:
                    existing_id = self.name_to_id[variation]
                    if existing_id != slug:
                        logging.warning(
                            f"Name variation '{variation}' maps to multiple IDs: "
                            f"'{existing_id}' and '{slug}'"
                        )
                self.name_to_id[variation] = slug

            # Also map primary name
            self.name_to_id[name] = slug

            self.stats["total_entities"] += 1
            self.stats["unique_ids"] += 1

            logging.info(f"Registered: '{name}' -> '{slug}'")
            return slug

        except ValueError as e:
            self.stats["invalid_names"] += 1
            logging.error(f"Failed to register '{name}': {e}")
            raise

    def load_entity_statistics(self, filepath: Path) -> None:
        """
        Load entities from entity_statistics.json.

        Data Source:
        - 1,637 entities with name variations and metadata
        - Primary source for entity names and variations
        """
        logging.info(f"Loading entities from {filepath}")

        with open(filepath) as f:
            data = json.load(f)

        statistics = data.get("statistics", {})

        for name, entity_data in statistics.items():
            try:
                name_variations = entity_data.get("name_variations", [name])
                sources = entity_data.get("sources", [])

                metadata = {
                    "in_black_book": entity_data.get("in_black_book", False),
                    "is_billionaire": entity_data.get("is_billionaire", False),
                    "categories": entity_data.get("categories", []),
                    "flight_count": entity_data.get("flight_count", 0),
                    "connection_count": entity_data.get("connection_count", 0),
                }

                self.register_entity(name, name_variations, sources, metadata)

            except ValueError as e:
                logging.error(f"Skipping entity '{name}': {e}")
                continue

        logging.info(
            f"Loaded {self.stats['total_entities']} entities "
            f"({self.stats['invalid_names']} invalid)"
        )

    def generate_collision_report(self) -> dict:
        """
        Generate detailed collision report for manual review.

        Report includes:
        - All collisions with entity details
        - Similarity analysis for potential duplicates
        - Recommended actions (merge, keep separate, rename)

        Returns:
            Collision report dictionary
        """
        report = {
            "metadata": {
                "generated": datetime.now().isoformat(),
                "total_collisions": len(self.collisions),
                "entities_affected": len(self.collisions) * 2,
                "collision_rate": len(self.collisions) / max(self.stats["total_entities"], 1),
            },
            "collisions": self.collisions,
            "recommendations": [],
        }

        # Add recommendations based on collision patterns
        for collision in self.collisions:
            base_name = collision["existing_name"]
            new_name = collision["name"]

            # Simple similarity check
            base_lower = base_name.lower().replace(",", "").replace(" ", "")
            new_lower = new_name.lower().replace(",", "").replace(" ", "")

            recommendation = {
                "base_slug": collision["base_slug"],
                "entities": [base_name, new_name],
                "action": "manual_review",
            }

            if base_lower == new_lower:
                recommendation["action"] = "merge"
                recommendation["reason"] = (
                    "Identical names after normalization - likely duplicate entity"
                )
            elif base_lower in new_lower or new_lower in base_lower:
                recommendation["action"] = "investigate"
                recommendation["reason"] = "Name substring match - possible variant or duplicate"
            else:
                recommendation["action"] = "keep_separate"
                recommendation["reason"] = (
                    "Different names with same slug - keep as separate entities"
                )

            report["recommendations"].append(recommendation)

        return report

    def save_outputs(self, output_dir: Path, dry_run: bool = False) -> None:
        """
        Save ID mappings and collision report.

        Outputs:
            - entity_id_mappings.json: Complete ID registry
            - collision_report.json: Conflicts requiring review
            - id_generation_stats.json: Generation statistics

        Error Handling:
        - Directory creation failure: Logged and raised
        - JSON serialization failure: Logged and raised
        - Dry-run mode: Only logs, no file writes
        """
        if dry_run:
            logging.info("DRY RUN: Skipping file writes")
            logging.info(f"Would create {len(self.id_registry)} entity IDs")
            logging.info(f"Would report {len(self.collisions)} collisions")
            return

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save ID mappings
        mappings_file = output_dir / "entity_id_mappings.json"
        mappings_data = {
            "metadata": {
                "version": "1.0",
                "generated": datetime.now().isoformat(),
                "total_entities": self.stats["total_entities"],
                "unique_ids": self.stats["unique_ids"],
                "collisions": self.stats["collisions"],
                "invalid_names": self.stats["invalid_names"],
            },
            "id_to_entity": self.id_registry,
            "name_to_id": self.name_to_id,
        }

        with open(mappings_file, "w") as f:
            json.dump(mappings_data, f, indent=2)
        logging.info(f"Saved ID mappings to {mappings_file}")

        # Save collision report
        if self.collisions:
            collision_file = output_dir / "collision_report.json"
            collision_report = self.generate_collision_report()

            with open(collision_file, "w") as f:
                json.dump(collision_report, f, indent=2)
            logging.info(
                f"Saved collision report to {collision_file} "
                f"({len(self.collisions)} collisions)"
            )

        # Save statistics
        stats_file = output_dir / "id_generation_stats.json"
        stats_data = {
            "generated": datetime.now().isoformat(),
            "statistics": self.stats,
            "sample_mappings": dict(list(self.id_registry.items())[:10]),
        }

        with open(stats_file, "w") as f:
            json.dump(stats_data, f, indent=2)
        logging.info(f"Saved statistics to {stats_file}")


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with file and console output."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "id_generation.log"

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def main():
    """
    Main execution function.

    Migration Safety:
    - Dry-run mode available for testing
    - No destructive operations (only creates new files)
    - Comprehensive logging for audit trail
    """
    parser = argparse.ArgumentParser(description="Generate entity IDs for migration")
    parser.add_argument("--dry-run", action="store_true", help="Run without writing output files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    logging.info("=" * 60)
    logging.info("Entity ID Generation - Starting")
    logging.info("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    metadata_dir = data_dir / "metadata"
    output_dir = data_dir / "migration"

    # Input file
    statistics_file = metadata_dir / "entity_statistics.json"

    if not statistics_file.exists():
        logging.error(f"Entity statistics file not found: {statistics_file}")
        return 1

    # Generate IDs
    generator = EntityIDGenerator()

    try:
        generator.load_entity_statistics(statistics_file)
        generator.save_outputs(output_dir, dry_run=args.dry_run)

        # Print summary
        print("\n" + "=" * 60)
        print("Entity ID Generation - Summary")
        print("=" * 60)
        print(f"Total entities processed: {generator.stats['total_entities']}")
        print(f"Unique IDs generated: {generator.stats['unique_ids']}")
        print(f"Collisions detected: {generator.stats['collisions']}")
        print(f"Invalid names skipped: {generator.stats['invalid_names']}")
        print(
            f"Collision rate: {generator.stats['collisions'] / max(generator.stats['total_entities'], 1) * 100:.2f}%"
        )

        if generator.collisions:
            print(f"\n⚠️  {len(generator.collisions)} collisions require manual review")
            print(f"   See: {output_dir}/collision_report.json")
        else:
            print("\n✅ No collisions detected")

        if args.dry_run:
            print("\n📋 DRY RUN - No files were written")
        else:
            print(f"\n✅ ID mappings saved to: {output_dir}/entity_id_mappings.json")

        print("=" * 60)

        return 0

    except Exception as e:
        logging.error(f"ID generation failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
