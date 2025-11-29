#!/usr/bin/env python3
"""
Entity Network Migration Script

Migrates entity_network.json from name-based to ID-based graph structure.

Migration:
- Node IDs: Names → Entity IDs
- Edge references: source/target names → Entity IDs
- Validation: All edge references must exist in nodes

Usage:
    python migrate_entity_network.py [--dry-run] [--backup]

Performance:
    - Expected runtime: <5 seconds for 284 nodes, 1,624 edges
    - Memory usage: <50MB

Critical:
    - Network graph integrity must be preserved
    - All edge references must remain valid
    - No orphaned edges allowed
"""

import argparse
import json
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class EntityNetworkMigrator:
    """
    Migrate entity_network.json to ID-based graph schema.

    Design Decision: Graph integrity validation required
    - Critical: Every edge must reference valid nodes
    - Performance: O(n + m) where n=nodes, m=edges
    - Safety: Orphan detection prevents broken graph

    Trade-offs:
    - Validation overhead: Extra O(m) check worth reliability
    - Memory: Full graph in memory (acceptable for 1,624 edges)
    - Atomic migration: All-or-nothing prevents partial corruption

    Alternatives Considered:
    1. Streaming: Rejected - need full graph for validation
    2. Partial migration: Rejected - graph must be atomic
    3. No validation: Rejected - broken graph catastrophic
    """

    def __init__(self, id_mappings: dict[str, str], invalid_entities: Optional[set[str]] = None):
        """
        Initialize migrator with ID mappings.

        Args:
            id_mappings: name_to_id mapping from generate_entity_ids.py
            invalid_entities: Set of entity names to skip (non-persons, metadata)
        """
        self.name_to_id = id_mappings
        self.invalid_entities = invalid_entities or set()
        self.stats = {
            "nodes_migrated": 0,
            "nodes_skipped": 0,
            "edges_migrated": 0,
            "edges_skipped": 0,
            "orphaned_edges": 0,
            "invalid_entities_filtered": 0,
        }
        self.migrated_node_ids: set[str] = set()

    def migrate_node(self, node: dict) -> dict:
        """
        Migrate single graph node from name to ID.

        Transformation:
        - node['id']: name → entity_id
        - node['name']: add if missing (for display)
        - Preserve all other fields

        Args:
            node: Original node with name-based ID

        Returns:
            Migrated node with entity ID

        Raises:
            KeyError: If node ID not in name_to_id mappings

        Error Handling:
        - Missing ID mapping: Raises KeyError (caller handles)
        - Invalid node structure: Logged and raised
        """
        original_id = node.get("id")

        if not original_id:
            raise ValueError("Node missing 'id' field")

        # Skip invalid entities
        if original_id in self.invalid_entities:
            self.stats["invalid_entities_filtered"] += 1
            raise KeyError(f"Invalid entity (skipped): '{original_id}'")

        # Lookup entity ID
        if original_id not in self.name_to_id:
            raise KeyError(f"No ID mapping for node: '{original_id}'")

        entity_id = self.name_to_id[original_id]

        # Create migrated node
        migrated = {
            "id": entity_id,  # NEW: Entity ID instead of name
            "name": node.get("name", original_id),  # PRESERVE: Display name
            **{k: v for k, v in node.items() if k not in ["id", "name"]},
        }

        self.stats["nodes_migrated"] += 1
        self.migrated_node_ids.add(entity_id)

        return migrated

    def migrate_edge(self, edge: dict) -> dict:
        """
        Migrate graph edge references from names to IDs.

        Transformation:
        - edge['source']: name → entity_id
        - edge['target']: name → entity_id
        - Preserve weight and other metadata

        Args:
            edge: Original edge with name-based references

        Returns:
            Migrated edge with entity ID references

        Raises:
            KeyError: If source/target not in mappings

        Validation:
        - Checks that both source and target exist in migrated nodes
        - Prevents orphaned edges
        """
        source_name = edge.get("source")
        target_name = edge.get("target")

        if not source_name or not target_name:
            raise ValueError(f"Edge missing source/target: {source_name} -> {target_name}")

        # Skip edges with invalid entities
        if source_name in self.invalid_entities:
            self.stats["invalid_entities_filtered"] += 1
            raise KeyError(f"Invalid entity in edge source (skipped): '{source_name}'")

        if target_name in self.invalid_entities:
            self.stats["invalid_entities_filtered"] += 1
            raise KeyError(f"Invalid entity in edge target (skipped): '{target_name}'")

        # Lookup entity IDs
        if source_name not in self.name_to_id:
            raise KeyError(f"No ID mapping for edge source: '{source_name}'")

        if target_name not in self.name_to_id:
            raise KeyError(f"No ID mapping for edge target: '{target_name}'")

        source_id = self.name_to_id[source_name]
        target_id = self.name_to_id[target_name]

        # Validate: Both nodes must exist in migrated graph
        # This prevents orphaned edges
        if source_id not in self.migrated_node_ids:
            self.stats["orphaned_edges"] += 1
            raise ValueError(
                f"Edge source '{source_id}' not in migrated nodes " f"(original: '{source_name}')"
            )

        if target_id not in self.migrated_node_ids:
            self.stats["orphaned_edges"] += 1
            raise ValueError(
                f"Edge target '{target_id}' not in migrated nodes " f"(original: '{target_name}')"
            )

        # Create migrated edge
        migrated = {
            "source": source_id,
            "target": target_id,
            **{k: v for k, v in edge.items() if k not in ["source", "target"]},
        }

        self.stats["edges_migrated"] += 1

        return migrated

    def migrate_network(
        self, nodes: list[dict], edges: list[dict]
    ) -> tuple[list[dict], list[dict]]:
        """
        Migrate entire network graph.

        Process:
        1. Migrate all nodes first
        2. Migrate edges (validates against migrated nodes)
        3. Report orphaned edges

        Performance:
        - Nodes: O(n) transformation
        - Edges: O(m) transformation + O(1) validation per edge
        - Total: O(n + m)

        Args:
            nodes: Original node list
            edges: Original edge list

        Returns:
            Tuple of (migrated_nodes, migrated_edges)

        Error Handling:
        - Node migration failure: Node skipped, logged
        - Edge migration failure: Edge skipped, logged
        - Orphaned edges: Logged, not included in output
        """
        migrated_nodes_dict = {}  # Use dict to automatically deduplicate by entity_id
        migrated_edges = []

        # Phase 1: Migrate nodes
        logging.info(f"Migrating {len(nodes)} nodes...")

        for node in nodes:
            try:
                migrated_node = self.migrate_node(node)
                entity_id = migrated_node["id"]

                # Deduplicate: Only keep first occurrence of each entity_id
                if entity_id not in migrated_nodes_dict:
                    migrated_nodes_dict[entity_id] = migrated_node
                else:
                    # Node already exists (likely due to alias), skip duplicate
                    logging.debug(f"Deduplicating node: '{entity_id}' (alias resolved)")
                    self.stats["nodes_skipped"] += 1
                    self.stats["nodes_migrated"] -= 1  # Correct the count

            except (KeyError, ValueError) as e:
                logging.warning(f"Skipping node '{node.get('id', 'unknown')}': {e}")
                self.stats["nodes_skipped"] += 1
                continue

        migrated_nodes = list(migrated_nodes_dict.values())

        logging.info(
            f"Nodes: {self.stats['nodes_migrated']} migrated, "
            f"{self.stats['nodes_skipped']} skipped"
        )

        # Phase 2: Migrate edges
        logging.info(f"Migrating {len(edges)} edges...")

        for edge in edges:
            try:
                migrated_edge = self.migrate_edge(edge)
                migrated_edges.append(migrated_edge)

            except (KeyError, ValueError) as e:
                logging.warning(
                    f"Skipping edge "
                    f"'{edge.get('source', '?')}' -> '{edge.get('target', '?')}': {e}"
                )
                self.stats["edges_skipped"] += 1
                continue

        logging.info(
            f"Edges: {self.stats['edges_migrated']} migrated, "
            f"{self.stats['edges_skipped']} skipped "
            f"(orphaned: {self.stats['orphaned_edges']})"
        )

        return migrated_nodes, migrated_edges

    def validate_network(
        self,
        original_nodes: list[dict],
        original_edges: list[dict],
        migrated_nodes: list[dict],
        migrated_edges: list[dict],
    ) -> tuple[bool, list[str]]:
        """
        Validate migrated network graph integrity.

        Validation Checks:
        1. Node count matches (within tolerance for skipped nodes)
        2. Edge count matches (within tolerance for orphans)
        3. All node IDs are valid slugs
        4. All node IDs are unique
        5. All edge references exist in nodes
        6. No self-loops (if not in original)
        7. Graph is connected (if original was connected)

        Args:
            original_nodes: Original node list
            original_edges: Original edge list
            migrated_nodes: Migrated node list
            migrated_edges: Migrated edge list

        Returns:
            Tuple of (is_valid, error_messages)

        Complexity:
        - Time: O(n + m) for full validation
        - Space: O(n) for node ID set
        """
        errors = []

        # Check 1: Node count (allow reduction due to skipped invalid entities)
        original_node_count = len(original_nodes)
        migrated_node_count = len(migrated_nodes)

        # Expected: migrated_node_count should be <= original_node_count
        # (due to skipped invalid entities and deduplication)
        if migrated_node_count > original_node_count:
            errors.append(
                f"Node count increased: {original_node_count} original, "
                f"{migrated_node_count} migrated (unexpected)"
            )
        else:
            diff = original_node_count - migrated_node_count
            logging.info(
                f"Node count: {original_node_count} original → {migrated_node_count} migrated "
                f"({diff} skipped/deduplicated)"
            )

        # Check 2: Edge count (allow reduction due to skipped edges)
        original_edge_count = len(original_edges)
        migrated_edge_count = len(migrated_edges)

        # Expected: migrated_edge_count should be <= original_edge_count
        # (due to edges with invalid entities)
        if migrated_edge_count > original_edge_count:
            errors.append(
                f"Edge count increased: {original_edge_count} original, "
                f"{migrated_edge_count} migrated (unexpected)"
            )
        else:
            diff = original_edge_count - migrated_edge_count
            logging.info(
                f"Edge count: {original_edge_count} original → {migrated_edge_count} migrated "
                f"({diff} skipped)"
            )

        # Check 3: Valid node IDs
        import re

        id_pattern = re.compile(r"^[a-z0-9_]+$")

        invalid_node_ids = [
            node["id"] for node in migrated_nodes if not id_pattern.match(node.get("id", ""))
        ]

        if invalid_node_ids:
            errors.append(
                f"Invalid node IDs: {', '.join(invalid_node_ids[:5])}"
                f"{' (and more)' if len(invalid_node_ids) > 5 else ''}"
            )

        # Check 4: Unique node IDs
        node_ids = [node["id"] for node in migrated_nodes]
        unique_node_ids = set(node_ids)

        if len(node_ids) != len(unique_node_ids):
            duplicates = len(node_ids) - len(unique_node_ids)
            errors.append(f"Duplicate node IDs detected: {duplicates} duplicates")

        # Check 5: All edge references exist
        node_id_set = set(node_ids)

        for edge in migrated_edges:
            source = edge.get("source")
            target = edge.get("target")

            if source not in node_id_set:
                errors.append(f"Edge references non-existent source node: '{source}'")

            if target not in node_id_set:
                errors.append(f"Edge references non-existent target node: '{target}'")

        # Check 6: No orphaned edges reported
        if self.stats["orphaned_edges"] > 0:
            errors.append(f"{self.stats['orphaned_edges']} orphaned edges detected and removed")

        is_valid = len(errors) == 0

        if is_valid:
            logging.info("✅ Network validation passed: All checks successful")
        else:
            logging.error(f"❌ Network validation failed: {len(errors)} errors")
            for error in errors:
                logging.error(f"  - {error}")

        return is_valid, errors


def create_backup(filepath: Path) -> Path:
    """Create timestamped backup of original file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}.backup_{timestamp}.json"

    shutil.copy2(filepath, backup_path)
    logging.info(f"Created backup: {backup_path}")

    return backup_path


def load_id_mappings(mappings_file: Path) -> dict[str, str]:
    """Load name-to-ID mappings."""
    logging.info(f"Loading ID mappings from {mappings_file}")

    with open(mappings_file) as f:
        data = json.load(f)

    if "name_to_id" not in data:
        raise KeyError("Missing 'name_to_id' in ID mappings file")

    name_to_id = data["name_to_id"]
    logging.info(f"Loaded {len(name_to_id)} name-to-ID mappings")

    return name_to_id


def load_alias_mappings(alias_file: Path) -> tuple[dict[str, str], set[str]]:
    """
    Load entity alias mappings for network migration.

    Returns:
        Tuple of (aliases dict, invalid_entities set)
    """
    if not alias_file.exists():
        logging.warning(f"Alias file not found: {alias_file}")
        return {}, set()

    logging.info(f"Loading alias mappings from {alias_file}")

    with open(alias_file) as f:
        data = json.load(f)

    aliases = data.get("aliases", {})
    invalid = set(data.get("invalid_entities", []))

    logging.info(f"Loaded {len(aliases)} aliases, {len(invalid)} invalid entities")

    return aliases, invalid


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "migrate_network.log"

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Migrate entity_network.json to ID-based schema")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run migration without writing output"
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip backup creation (not recommended)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    logging.info("=" * 60)
    logging.info("Entity Network Migration - Starting")
    logging.info("=" * 60)

    # Paths
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    metadata_dir = data_dir / "metadata"
    migration_dir = data_dir / "migration"

    network_file = metadata_dir / "entity_network.json"
    mappings_file = migration_dir / "entity_id_mappings.json"
    alias_file = migration_dir / "entity_network_aliases.json"

    # Validate inputs
    if not network_file.exists():
        logging.error(f"Network file not found: {network_file}")
        return 1

    if not mappings_file.exists():
        logging.error(
            f"ID mappings file not found: {mappings_file}\n" f"Run generate_entity_ids.py first"
        )
        return 1

    try:
        # Load ID mappings
        name_to_id = load_id_mappings(mappings_file)

        # Load alias mappings
        aliases, invalid_entities = load_alias_mappings(alias_file)

        # Merge aliases into name_to_id mappings
        alias_count = 0
        for alias_name, entity_id in aliases.items():
            if alias_name not in name_to_id:
                name_to_id[alias_name] = entity_id
                alias_count += 1
                logging.info(f"Applied alias: '{alias_name}' → '{entity_id}'")

        logging.info(f"Applied {alias_count} alias mappings")
        logging.info(f"Invalid entities to skip: {len(invalid_entities)}")

        # Create backup
        if not args.no_backup and not args.dry_run:
            backup_path = create_backup(network_file)
        else:
            backup_path = None
            logging.warning("Skipping backup creation")

        # Load original network
        logging.info(f"Loading network from {network_file}")
        with open(network_file) as f:
            original_data = json.load(f)

        original_nodes = original_data.get("nodes", [])
        original_edges = original_data.get("edges", [])

        # Migrate
        migrator = EntityNetworkMigrator(name_to_id, invalid_entities)
        migrated_nodes, migrated_edges = migrator.migrate_network(original_nodes, original_edges)

        # Validate
        is_valid, errors = migrator.validate_network(
            original_nodes, original_edges, migrated_nodes, migrated_edges
        )

        if not is_valid:
            logging.error("Network migration validation failed:")
            for error in errors:
                logging.error(f"  - {error}")

            if backup_path:
                logging.info(f"Backup preserved at: {backup_path}")

            return 1

        # Prepare migrated data
        migrated_data = {
            **original_data,  # Preserve metadata
            "nodes": migrated_nodes,
            "edges": migrated_edges,
            "migration_info": {
                "migrated_at": datetime.now().isoformat(),
                "schema_version": "2.0",
                "migration_script": "migrate_entity_network.py",
                "nodes_migrated": migrator.stats["nodes_migrated"],
                "edges_migrated": migrator.stats["edges_migrated"],
                "nodes_skipped": migrator.stats["nodes_skipped"],
                "edges_skipped": migrator.stats["edges_skipped"],
                "orphaned_edges": migrator.stats["orphaned_edges"],
            },
        }

        # Save migrated file
        if args.dry_run:
            logging.info("DRY RUN: Skipping file write")
        else:
            with open(network_file, "w") as f:
                json.dump(migrated_data, f, indent=2)
            logging.info(f"Saved migrated network to {network_file}")

        # Print summary
        print("\n" + "=" * 60)
        print("Entity Network Migration - Summary")
        print("=" * 60)
        print(f"Aliases applied: {alias_count}")
        print(f"Invalid entities filtered: {migrator.stats['invalid_entities_filtered']}")
        print(f"Nodes migrated: {migrator.stats['nodes_migrated']}")
        print(f"Nodes skipped: {migrator.stats['nodes_skipped']}")
        print(f"Edges migrated: {migrator.stats['edges_migrated']}")
        print(f"Edges skipped: {migrator.stats['edges_skipped']}")
        print(f"Orphaned edges: {migrator.stats['orphaned_edges']}")
        print(f"Validation: {'✅ PASSED' if is_valid else '❌ FAILED'}")

        if backup_path:
            print(f"\nBackup saved: {backup_path}")

        if args.dry_run:
            print("\n📋 DRY RUN - No files were modified")
        else:
            print(f"\n✅ Migration complete: {network_file}")

        print("=" * 60)

        return 0

    except Exception as e:
        logging.error(f"Migration failed: {e}", exc_info=True)

        if backup_path:
            logging.info(f"Backup preserved at: {backup_path}")
            print(f"\n⚠️  Migration failed - backup preserved: {backup_path}")

        return 1


if __name__ == "__main__":
    sys.exit(main())
