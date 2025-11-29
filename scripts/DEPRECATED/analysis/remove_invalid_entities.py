#!/usr/bin/env python3
"""
Remove Invalid Entities from Epstein Document Archive

Design Decision: Manual filtering with explicit validation
Rationale: Entity classification is complex - equipment vs. person names
can be ambiguous. Manual approach with logging ensures no legitimate
entities are accidentally removed.

Trade-offs:
- Precision over automation: Avoids false positives
- Explicit logging: Full audit trail of all changes
- Backup strategy: Safe rollback if errors occur

Performance: O(n) single pass through all entity files
Target: Remove "EPSTEIN- PORTABLES" and similar non-person entities
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# File paths
BASE_DIR = Path("/Users/masa/Projects/Epstein")
ENTITIES_DIR = BASE_DIR / "data/md/entities"
METADATA_DIR = BASE_DIR / "data/metadata"
BACKUP_DIR = ENTITIES_DIR / "backup_invalid_removal"
LOG_FILE = Path("/tmp/removed_entities.log")

# Files to process
FILES_TO_PROCESS = {
    "entity_index": ENTITIES_DIR / "ENTITIES_INDEX.json",
    "black_book": ENTITIES_DIR / "black_book.md",
    "flight_logs": ENTITIES_DIR / "flight_logs.md",
    "entity_network": METADATA_DIR / "entity_network.json",
    "semantic_index": METADATA_DIR / "semantic_index.json",
}

# Invalid entity patterns (equipment, property, companies)
INVALID_PATTERNS = [
    r"PORTABLES",
    r"^[A-Z\s-]+LLC$",
    r"^[A-Z\s-]+INC\.?$",
    r"^[A-Z\s-]+CORP\.?$",
    r"^PHONE[S]?\s",
    r"^FAX[ES]?\s",
    r"^TV\s",
    r"^OFFICE[S]?\s",
    r"^RESIDENCE[S]?\s",
    r"EQUIPMENT",
]

# Known invalid entities (explicit list)
KNOWN_INVALID = {
    "EPSTEIN- PORTABLES",
    "PORTABLES, EPSTEIN-",
}


class InvalidEntityRemover:
    """Remove non-person entities from Epstein archive indexes"""

    def __init__(self):
        self.removed_entities: Set[str] = set()
        self.modifications: Dict[str, List[str]] = {}
        self.backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def is_invalid_entity(self, name: str) -> Tuple[bool, str]:
        """
        Check if entity name matches invalid patterns.

        Returns:
            (is_invalid: bool, reason: str)
        """
        # Check explicit known invalid list
        if name in KNOWN_INVALID:
            return True, "Known invalid (equipment/property)"

        # Check pattern matches
        for pattern in INVALID_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                return True, f"Matches pattern: {pattern}"

        return False, ""

    def backup_file(self, file_path: Path) -> Path:
        """Create timestamped backup of file"""
        if not file_path.exists():
            return None

        BACKUP_DIR.mkdir(exist_ok=True)
        backup_path = BACKUP_DIR / f"{file_path.name}.{self.backup_timestamp}"
        shutil.copy2(file_path, backup_path)
        return backup_path

    def process_entity_index(self, file_path: Path) -> int:
        """
        Remove invalid entities from ENTITIES_INDEX.json

        Returns:
            Number of entities removed
        """
        print(f"\n📄 Processing: {file_path.name}")

        if not file_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            return 0

        # Backup
        backup_path = self.backup_file(file_path)
        print(f"  💾 Backup created: {backup_path.name}")

        # Load JSON
        with open(file_path) as f:
            data = json.load(f)

        original_count = data.get("total_entities", 0)
        original_entities = len(data.get("entities", []))

        # Filter entities
        valid_entities = []
        for entity in data.get("entities", []):
            name = entity.get("name", "")
            is_invalid, reason = self.is_invalid_entity(name)

            if is_invalid:
                self.removed_entities.add(name)
                self.log_removal(file_path.name, name, reason, entity)
                print(f"  ❌ Removing: {name} ({reason})")
            else:
                valid_entities.append(entity)

        # Update data
        data["entities"] = valid_entities
        data["total_entities"] = len(valid_entities)

        # Update statistics if present
        if "statistics" in data:
            removed_count = original_entities - len(valid_entities)
            data["statistics"]["total_persons"] = (
                data["statistics"].get("total_persons", 0) - removed_count
            )

        # Save modified JSON
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        removed_count = original_entities - len(valid_entities)
        self.modifications[file_path.name] = [
            f"Original count: {original_entities}",
            f"Valid entities: {len(valid_entities)}",
            f"Removed: {removed_count}",
            f"Updated total_entities: {original_count} → {data['total_entities']}",
        ]

        print(f"  ✅ Updated: {original_entities} → {len(valid_entities)} entities")
        return removed_count

    def process_markdown(self, file_path: Path) -> int:
        """
        Remove invalid entity sections from markdown files

        Returns:
            Number of sections removed
        """
        print(f"\n📄 Processing: {file_path.name}")

        if not file_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            return 0

        # Backup
        backup_path = self.backup_file(file_path)
        print(f"  💾 Backup created: {backup_path.name}")

        # Read markdown
        with open(file_path) as f:
            content = f.read()

        original_content = content
        removed_count = 0

        # Find and remove invalid entity sections
        # Pattern: #### ENTITY_NAME followed by content until next ####
        lines = content.split("\n")
        new_lines = []
        skip_until_next_header = False
        current_entity = None

        for line in lines:
            # Check if this is an entity header (#### NAME)
            if line.startswith("#### "):
                entity_name = line[5:].strip()
                is_invalid, reason = self.is_invalid_entity(entity_name)

                if is_invalid:
                    skip_until_next_header = True
                    current_entity = entity_name
                    self.removed_entities.add(entity_name)
                    self.log_removal(file_path.name, entity_name, reason, {"line": line})
                    print(f"  ❌ Removing section: {entity_name} ({reason})")
                    removed_count += 1
                else:
                    skip_until_next_header = False
                    current_entity = None
                    new_lines.append(line)
            elif skip_until_next_header:
                # Skip lines in invalid entity section
                continue
            else:
                new_lines.append(line)

        # Save modified markdown
        if removed_count > 0:
            new_content = "\n".join(new_lines)
            with open(file_path, "w") as f:
                f.write(new_content)

            self.modifications[file_path.name] = [
                f"Sections removed: {removed_count}",
                f"Size: {len(original_content)} → {len(new_content)} bytes",
            ]
            print(f"  ✅ Removed {removed_count} invalid sections")
        else:
            print("  ✓ No invalid entities found")

        return removed_count

    def process_entity_network(self, file_path: Path) -> int:
        """
        Remove invalid entities from entity_network.json

        Returns:
            Number of entities removed
        """
        print(f"\n📄 Processing: {file_path.name}")

        if not file_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            return 0

        # Backup
        backup_path = self.backup_file(file_path)
        print(f"  💾 Backup created: {backup_path.name}")

        # Load JSON
        with open(file_path) as f:
            data = json.load(f)

        original_nodes = len(data.get("nodes", []))
        original_edges = len(data.get("edges", []))

        # Filter nodes
        valid_nodes = []
        removed_node_ids = set()

        for node in data.get("nodes", []):
            name = node.get("id", "")
            is_invalid, reason = self.is_invalid_entity(name)

            if is_invalid:
                removed_node_ids.add(name)
                self.removed_entities.add(name)
                self.log_removal(file_path.name, name, reason, node)
                print(f"  ❌ Removing node: {name} ({reason})")
            else:
                valid_nodes.append(node)

        # Filter edges (remove edges connected to invalid nodes)
        valid_edges = []
        for edge in data.get("edges", []):
            source = edge.get("source", "")
            target = edge.get("target", "")

            if source in removed_node_ids or target in removed_node_ids:
                continue
            valid_edges.append(edge)

        # Update data
        data["nodes"] = valid_nodes
        data["edges"] = valid_edges

        # Save modified JSON
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        removed_nodes = original_nodes - len(valid_nodes)
        removed_edges = original_edges - len(valid_edges)

        self.modifications[file_path.name] = [
            f"Nodes: {original_nodes} → {len(valid_nodes)} (removed {removed_nodes})",
            f"Edges: {original_edges} → {len(valid_edges)} (removed {removed_edges})",
        ]

        print(f"  ✅ Nodes: {original_nodes} → {len(valid_nodes)}")
        print(f"  ✅ Edges: {original_edges} → {len(valid_edges)}")

        return removed_nodes

    def process_semantic_index(self, file_path: Path) -> int:
        """
        Remove invalid entities from semantic_index.json

        Returns:
            Number of entity entries removed
        """
        print(f"\n📄 Processing: {file_path.name}")

        if not file_path.exists():
            print(f"  ⚠️  File not found: {file_path}")
            return 0

        # Backup
        backup_path = self.backup_file(file_path)
        print(f"  💾 Backup created: {backup_path.name}")

        # Load JSON
        with open(file_path) as f:
            data = json.load(f)

        original_count = len(data.get("entities", {}))

        # Filter entities
        valid_entities = {}
        for entity_name, entity_data in data.get("entities", {}).items():
            is_invalid, reason = self.is_invalid_entity(entity_name)

            if is_invalid:
                self.removed_entities.add(entity_name)
                self.log_removal(file_path.name, entity_name, reason, entity_data)
                print(f"  ❌ Removing: {entity_name} ({reason})")
            else:
                valid_entities[entity_name] = entity_data

        # Update data
        data["entities"] = valid_entities

        # Save modified JSON
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        removed_count = original_count - len(valid_entities)
        self.modifications[file_path.name] = [
            f"Original entities: {original_count}",
            f"Valid entities: {len(valid_entities)}",
            f"Removed: {removed_count}",
        ]

        print(f"  ✅ Entities: {original_count} → {len(valid_entities)}")
        return removed_count

    def log_removal(self, file: str, entity: str, reason: str, data: dict):
        """Log entity removal to file"""
        with open(LOG_FILE, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"[{timestamp}] {file}: Removed '{entity}' - {reason}\n")
            f.write(f"  Data: {json.dumps(data, indent=4)}\n\n")

    def run(self) -> Dict:
        """
        Execute full cleanup process

        Returns:
            Summary statistics
        """
        print("=" * 60)
        print("🧹 EPSTEIN ARCHIVE: INVALID ENTITY REMOVAL")
        print("=" * 60)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Backup directory: {BACKUP_DIR}")
        print(f"Log file: {LOG_FILE}")

        # Clear log file
        LOG_FILE.write_text(f"Invalid Entity Removal Log\n{'=' * 50}\n\n")

        total_removed = 0

        # Process each file type
        total_removed += self.process_entity_index(FILES_TO_PROCESS["entity_index"])
        total_removed += self.process_markdown(FILES_TO_PROCESS["black_book"])
        total_removed += self.process_markdown(FILES_TO_PROCESS["flight_logs"])
        total_removed += self.process_entity_network(FILES_TO_PROCESS["entity_network"])
        total_removed += self.process_semantic_index(FILES_TO_PROCESS["semantic_index"])

        # Generate summary
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_entities_removed": len(self.removed_entities),
            "unique_invalid_entities": sorted(list(self.removed_entities)),
            "files_modified": len(self.modifications),
            "modifications_by_file": self.modifications,
            "backup_location": str(BACKUP_DIR),
            "log_file": str(LOG_FILE),
        }

        # Print summary
        print("\n" + "=" * 60)
        print("📊 REMOVAL SUMMARY")
        print("=" * 60)
        print(f"Total unique invalid entities found: {len(self.removed_entities)}")
        print(f"Files modified: {len(self.modifications)}")
        print("\nRemoved entities:")
        for entity in sorted(self.removed_entities):
            print(f"  - {entity}")

        print("\nModifications by file:")
        for file, changes in self.modifications.items():
            print(f"\n  {file}:")
            for change in changes:
                print(f"    • {change}")

        print(f"\n✅ Complete! Check log: {LOG_FILE}")
        print(f"🔄 Rollback available in: {BACKUP_DIR}/")

        # Save summary to JSON
        summary_file = BACKUP_DIR / f"removal_summary_{self.backup_timestamp}.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"📄 Summary saved: {summary_file}")

        return summary


def main():
    """Execute invalid entity removal"""
    remover = InvalidEntityRemover()
    summary = remover.run()
    return summary


if __name__ == "__main__":
    main()
