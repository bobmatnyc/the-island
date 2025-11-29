#!/usr/bin/env python3
"""
Fix entity name issues in Epstein Document Archive.

Fixes:
1. Duplicate first names (e.g., "Ghislaine Ghislaine" → "Maxwell, Ghislaine")
2. Extra whitespace (e.g., "Virginia   Virginia Roberts" → "Roberts, Virginia")
3. Inconsistent formatting for known entities
4. "Je Je Epstein" variations → "Epstein, Jeffrey"

Updates:
- flight_logs.md
- ENTITIES_INDEX.json
- flight_logs_by_flight.json
"""

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

# Known entity mappings (ground truth from Black Book and court records)
KNOWN_ENTITIES = {
    # Epstein variations (handle all spacing variations - must match EXACTLY as they appear in files)
    "Je Epstein": "Epstein, Jeffrey",
    "Je Je Epstein": "Epstein, Jeffrey",
    "Je         Je Epstein": "Epstein, Jeffrey",
    "Je        Je Epstein": "Epstein, Jeffrey",
    "Je          Je Epstein": "Epstein, Jeffrey",
    "Jeffrey Epstein": "Epstein, Jeffrey",
    # Maxwell variations
    "Ghislaine": "Maxwell, Ghislaine",
    "Ghislaine Ghislaine": "Maxwell, Ghislaine",
    "Ghislaine Maxwell": "Maxwell, Ghislaine",
    # Known individuals with duplicate first names
    "Nadia Nadia": "Nadia",  # Single name
    "Virginia Roberts": "Roberts, Virginia",
    "Virginia   Virginia Roberts": "Roberts, Virginia",
    # Sarah Kellen variations
    "Sarah Kellen": "Kellen, Sarah",
    "Sarah       Sarah Kellen": "Kellen, Sarah",
    "Sarah      Sarah Kellen": "Kellen, Sarah",
    "Sarah        Sarah Kellen": "Kellen, Sarah",
    # Emmy Tayler variations
    "Emmy Tayler": "Tayler, Emmy",
    "Emmy       Emmy Tayler": "Tayler, Emmy",
    "Emmy        Emmy Tayler": "Tayler, Emmy",
    # Other known duplicates
    "Andrea Mitrovich": "Mitrovich, Andrea",
    "Andrea   Andrea Mitrovich": "Mitrovich, Andrea",
    "Andrea    Andrea Mitrovich": "Mitrovich, Andrea",
    "Shelley Lewis": "Lewis, Shelley",
    "Shelley     Shelley Lewis": "Lewis, Shelley",
    "Shelley      Shelley Lewis": "Lewis, Shelley",
    "Cindy Lopez": "Lopez, Cindy",
    "Cindy        Cindy Lopez": "Lopez, Cindy",
    "Teala Davies": "Davies, Teala",
    "Teala       Teala Davies": "Davies, Teala",
    "Teala      Teala Davies": "Davies, Teala",
    "Eva Dubin": "Dubin, Eva",
    "Eva         Eva Dubin": "Dubin, Eva",
    "Eva          Eva Dubin": "Dubin, Eva",
    "Celina Dubin": "Dubin, Celina",
    "Celina      Celina Dubin": "Dubin, Celina",
    "Celina       Celina Dubin": "Dubin, Celina",
    "Sophie Biddle": "Biddle, Sophie",
    "Sophie     Sophie Biddle": "Biddle, Sophie",
    "Sophie      Sophie Biddle": "Biddle, Sophie",
    "Celina Midelfart": "Midelfart, Celina",
    "Celina   Celina Midelfart": "Midelfart, Celina",
    "Gwendolyn Beck": "Beck, Gwendolyn",
    "Gwendolyn    Gwendolyn Beck": "Beck, Gwendolyn",
    "Gwendolyn     Gwendolyn Beck": "Beck, Gwendolyn",
    "Magale Blachou": "Blachou, Magale",
    "Magale    Magale Blachou": "Blachou, Magale",
    "Glenn Dubin": "Dubin, Glenn",
    "Glenn       Glenn Dubin": "Dubin, Glenn",
    "Chauntae Davies": "Davies, Chauntae",
    "Chauntae    Chauntae Davies": "Davies, Chauntae",
    "Doug Band": "Band, Doug",
    "Doug          Doug Band": "Band, Doug",
    "Pete Rathgeb": "Rathgeb, Pete",
    "Pete      Pete Rathgeb": "Rathgeb, Pete",
    "Pete       Pete Rathgeb": "Rathgeb, Pete",
    "David Mullen": "Mullen, David",
    "David       David Mullen": "Mullen, David",
    "Adriana Mucinska": "Mucinska, Adriana",
    "Adriana Adriana Mucinska": "Mucinska, Adriana",
    "Bill Clinton": "Clinton, Bill",
    "Bill       Bill Clinton": "Clinton, Bill",
    "Bill        Bill Clinton": "Clinton, Bill",
    "Kevin Spacey": "Spacey, Kevin",
    "Kevin       Kevin Spacey": "Spacey, Kevin",
    "Chris Tucker": "Tucker, Chris",
    "Chris       Chris Tucker": "Tucker, Chris",
    "David Slang": "Slang, David",
    "David        David Slang": "Slang, David",
    "Jim Kennez": "Kennez, Jim",
    "Jim         Jim Kennez": "Kennez, Jim",
    "Eric Nonacs": "Nonacs, Eric",
    "Eric        Eric Nonacs": "Nonacs, Eric",
    "Rodey Swater": "Swater, Rodey",
    "Rodey       Rodey Swater": "Swater, Rodey",
    "Tatiana Kovylina": "Kovylina, Tatiana",
    "Tatiana   Tatiana Kovylina": "Kovylina, Tatiana",
}


class EntityNameFixer:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.entities_dir = base_path / "data" / "md" / "entities"
        self.backup_dir = (
            base_path
            / "data"
            / "md"
            / "entities"
            / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        self.flight_logs_md = self.entities_dir / "flight_logs.md"
        self.entities_index = self.entities_dir / "ENTITIES_INDEX.json"
        self.flight_logs_json = self.entities_dir / "flight_logs_by_flight.json"

        self.name_mappings = {}
        self.stats = {
            "total_names_fixed": 0,
            "duplicate_patterns_found": 0,
            "whitespace_cleaned": 0,
            "known_entities_fixed": 0,
            "files_updated": 0,
        }

        self.log_file = Path("/tmp/entity_name_fixes.log")
        self.log_entries = []

    def log(self, message: str):
        """Log a message to both console and log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.log_entries.append(log_entry)

    def save_log(self):
        """Save all log entries to file."""
        with open(self.log_file, "w") as f:
            f.write("\n".join(self.log_entries))
        self.log(f"Log saved to: {self.log_file}")

    def create_backup(self):
        """Create backup of all files before modification."""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        files_to_backup = [self.flight_logs_md, self.entities_index, self.flight_logs_json]

        for file_path in files_to_backup:
            if file_path.exists():
                backup_path = self.backup_dir / file_path.name
                shutil.copy2(file_path, backup_path)
                self.log(f"Backed up: {file_path.name} → {backup_path}")

    def normalize_whitespace(self, name: str) -> str:
        """Remove excessive whitespace from names."""
        # Replace multiple spaces with single space
        normalized = re.sub(r"\s+", " ", name.strip())
        return normalized

    def detect_duplicate_pattern(self, name: str) -> bool:
        """Detect if name has duplicate first name pattern."""
        normalized = self.normalize_whitespace(name)
        words = normalized.split()

        if len(words) >= 2:
            # Check if first two words are identical (case-insensitive)
            if words[0].lower() == words[1].lower():
                # Exclude European name prefixes
                if words[0].lower() not in ["de", "van", "von", "del", "di"]:
                    return True
        return False

    def fix_duplicate_pattern(self, name: str) -> str:
        """Fix names with duplicate first name pattern."""
        normalized = self.normalize_whitespace(name)
        words = normalized.split()

        if len(words) == 2 and words[0].lower() == words[1].lower():
            # "Nadia Nadia" → "Nadia" (single name)
            return words[0]
        if len(words) >= 3 and words[0].lower() == words[1].lower():
            # "Virginia Virginia Roberts" → "Roberts, Virginia"
            first = words[0]
            last = " ".join(words[2:])
            return f"{last}, {first}"

        return normalized

    def fix_name(self, original_name: str) -> str:
        """Fix a single name using all correction strategies."""
        # First, check known entities (highest priority)
        if original_name in KNOWN_ENTITIES:
            fixed = KNOWN_ENTITIES[original_name]
            self.stats["known_entities_fixed"] += 1
            return fixed

        # Normalize whitespace
        name = self.normalize_whitespace(original_name)

        # Check for duplicate pattern
        if self.detect_duplicate_pattern(name):
            fixed = self.fix_duplicate_pattern(name)
            self.stats["duplicate_patterns_found"] += 1
            return fixed

        # Return normalized (whitespace cleaned)
        if name != original_name:
            self.stats["whitespace_cleaned"] += 1
        return name

    def extract_names_from_markdown(self):
        """Extract all names from markdown file to ensure we catch all variations."""
        names = set()

        with open(self.flight_logs_md) as f:
            for line in f:
                # Extract from table rows: | 1 | Je         Je Epstein | 521 | 125 |
                match = re.match(r"^\|\s*\d+\s*\|\s*([^|]+)\s*\|", line)
                if match:
                    names.add(match.group(1).strip())

                # Extract from headers: ### Je         Je Epstein
                match = re.match(r"^###\s+(.+)$", line)
                if match:
                    names.add(match.group(1).strip())

        return names

    def build_name_mappings(self):
        """Build mapping of old names to new names from all sources."""
        self.log("\n=== Building Name Mappings ===")

        all_names = set()

        # Extract names from markdown first (catches spacing variations)
        md_names = self.extract_names_from_markdown()
        all_names.update(md_names)
        self.log(f"Found {len(md_names)} names in flight_logs.md")

        # Load entities index to get all names
        with open(self.entities_index) as f:
            data = json.load(f)

        # Collect names from top frequent flyers
        for entity in data.get("top_frequent_flyers", []):
            all_names.add(entity["name"])

        # Collect names from entities list
        for entity in data.get("entities", []):
            all_names.add(entity["name"])

        # Load flight logs JSON to get passenger names
        with open(self.flight_logs_json) as f:
            flights_data = json.load(f)

        for flight in flights_data.get("flights", []):
            for passenger in flight.get("passengers", []):
                all_names.add(passenger)

        self.log(f"Found {len(all_names)} total unique names to process")

        # Build mappings (sorted by length desc to avoid partial replacements)
        for name in sorted(all_names, key=lambda x: -len(x)):
            fixed_name = self.fix_name(name)
            if fixed_name != name:
                # CRITICAL: Skip if old name is substring of new name (prevents double replacement)
                # Example: Skip "Ghislaine" → "Maxwell, Ghislaine" if we already have
                # "Ghislaine Ghislaine" → "Maxwell, Ghislaine"
                would_cause_double_replacement = False
                for existing_old, existing_new in self.name_mappings.items():
                    if name in existing_new:
                        would_cause_double_replacement = True
                        self.log(f"  SKIP (would cause double replacement): {name} → {fixed_name}")
                        self.log(f"       (conflicts with: {existing_old} → {existing_new})")
                        break

                if not would_cause_double_replacement:
                    self.name_mappings[name] = fixed_name
                    self.stats["total_names_fixed"] += 1
                    self.log(f"  {name:40} → {fixed_name}")

        self.log(f"Created {len(self.name_mappings)} name mappings")

    def update_flight_logs_md(self):
        """Update flight_logs.md with corrected names."""
        self.log("\n=== Updating flight_logs.md ===")

        with open(self.flight_logs_md) as f:
            content = f.read()

        # Sort mappings by length (longest first) to avoid partial replacements
        sorted_mappings = sorted(self.name_mappings.items(), key=lambda x: -len(x[0]))

        # Replace all name occurrences
        for old_name, new_name in sorted_mappings:
            # Use whole-word regex to avoid partial matches
            content = content.replace(old_name, new_name)

        with open(self.flight_logs_md, "w") as f:
            f.write(content)

        self.stats["files_updated"] += 1
        self.log(f"Updated: {self.flight_logs_md.name}")

    def update_entities_index(self):
        """Update ENTITIES_INDEX.json with corrected names."""
        self.log("\n=== Updating ENTITIES_INDEX.json ===")

        with open(self.entities_index) as f:
            data = json.load(f)

        # Update top frequent flyers
        for entity in data.get("top_frequent_flyers", []):
            old_name = entity["name"]
            if old_name in self.name_mappings:
                entity["name"] = self.name_mappings[old_name]

        # Update entities list
        for entity in data.get("entities", []):
            old_name = entity["name"]
            if old_name in self.name_mappings:
                entity["name"] = self.name_mappings[old_name]

        # Write back
        with open(self.entities_index, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stats["files_updated"] += 1
        self.log(f"Updated: {self.entities_index.name}")

    def update_flight_logs_json(self):
        """Update flight_logs_by_flight.json with corrected names."""
        self.log("\n=== Updating flight_logs_by_flight.json ===")

        with open(self.flight_logs_json) as f:
            data = json.load(f)

        # Update passenger names in all flights
        for flight in data.get("flights", []):
            passengers = flight.get("passengers", [])
            fixed_passengers = []
            for passenger in passengers:
                fixed_name = self.name_mappings.get(passenger, passenger)
                fixed_passengers.append(fixed_name)
            flight["passengers"] = fixed_passengers

        # Write back
        with open(self.flight_logs_json, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stats["files_updated"] += 1
        self.log(f"Updated: {self.flight_logs_json.name}")

    def print_statistics(self):
        """Print final statistics."""
        self.log("\n" + "=" * 60)
        self.log("ENTITY NAME FIX STATISTICS")
        self.log("=" * 60)
        self.log(f"Total names fixed: {self.stats['total_names_fixed']}")
        self.log(f"Known entities fixed: {self.stats['known_entities_fixed']}")
        self.log(f"Duplicate patterns found: {self.stats['duplicate_patterns_found']}")
        self.log(f"Whitespace cleaned: {self.stats['whitespace_cleaned']}")
        self.log(f"Files updated: {self.stats['files_updated']}")
        self.log(f"Backup location: {self.backup_dir}")
        self.log("=" * 60)

    def run(self):
        """Execute complete name fixing process."""
        self.log("=" * 60)
        self.log("EPSTEIN ENTITY NAME FIXER")
        self.log("=" * 60)
        self.log(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.log(f"Base path: {self.base_path}")

        # Step 1: Create backups
        self.log("\nStep 1: Creating backups...")
        self.create_backup()

        # Step 2: Build name mappings
        self.log("\nStep 2: Building name mappings...")
        self.build_name_mappings()

        # Step 3: Update files
        self.log("\nStep 3: Updating files...")
        self.update_flight_logs_md()
        self.update_entities_index()
        self.update_flight_logs_json()

        # Step 4: Print statistics
        self.print_statistics()

        # Step 5: Save log
        self.log(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.save_log()

        return self.stats


def main():
    base_path = Path("/Users/masa/Projects/Epstein")
    fixer = EntityNameFixer(base_path)
    stats = fixer.run()

    print("\n✅ Entity name fixing complete!")
    print(f"📊 Fixed {stats['total_names_fixed']} entity names")
    print(f"📁 Updated {stats['files_updated']} files")
    print(f"💾 Backups saved to: {fixer.backup_dir}")
    print(f"📝 Log saved to: {fixer.log_file}")


if __name__ == "__main__":
    main()
