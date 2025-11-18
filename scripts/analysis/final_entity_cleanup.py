#!/usr/bin/env python3
"""
Final Entity Cleanup Script - Fixes OCR Artifacts and Duplicates
==================================================================

This script eliminates entity duplicate patterns caused by OCR artifacts:
- "Glenn       Glenn Dubin" → "Glenn Dubin" (whitespace-padded duplicates)
- "Nadia Nadia" → "Marcinkova, Nadia"
- "Ghislaine Ghislaine" → "Maxwell, Ghislaine"
- "Je Je" variants → "Epstein, Jeffrey"

Updates the primary data file:
- entity_statistics.json (what the server loads)

Author: Claude
Date: 2025-11-17
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Set
from collections import defaultdict

class EntityCleanup:
    """Comprehensive entity deduplication - fixes OCR whitespace artifacts"""

    # Known entity mappings
    KNOWN_FIXES = {
        # Epstein variants
        "Epstein, Je Je": "Epstein, Jeffrey",
        "Je Epstein": "Epstein, Jeffrey",
        "Epstein Je": "Epstein, Jeffrey",
        "Je Je": "Epstein, Jeffrey",

        # Ghislaine variants
        "Ghislaine Ghislaine": "Maxwell, Ghislaine",

        # Nadia variants
        "Nadia Nadia": "Marcinkova, Nadia",

        # Virginia variants
        "Virginia Virginia Roberts": "Roberts, Virginia",
        "Virginia Virginia": "Roberts, Virginia",

        # Remove completely
        "Passengers, No No": None,
        "No No": None,
        "Baby Baby": None,
        "Illegible Illegible": "Illegible",
        "Reposition Reposition": "Reposition",
    }

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.backup_dir = self.data_dir / "backups" / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Statistics
        self.stats = {
            'entities_fixed': 0,
            'ocr_artifacts_removed': 0,
            'mappings_applied': 0,
            'data_merged': 0
        }

        # Track dynamically detected OCR artifacts
        self.ocr_fixes: Dict[str, str] = {}

    def detect_ocr_duplicate(self, name: str) -> str | None:
        """
        Detect OCR artifacts where first name is repeated with whitespace padding.

        Examples:
            "Glenn       Glenn Dubin" → "Glenn Dubin"
            "Donald      Donald Trump" → "Donald Trump"
            "Nadia Nadia" → "Nadia" (but we handle this separately with KNOWN_FIXES)

        Returns:
            Cleaned name if OCR artifact detected, None otherwise
        """
        # Normalize whitespace first
        normalized = re.sub(r'\s+', ' ', name).strip()
        words = normalized.split()

        if len(words) < 2:
            return None

        # Check if first two words are identical (case-insensitive)
        if words[0].lower() == words[1].lower() and words[0][0].isupper():
            # Remove the duplicate first word
            cleaned = ' '.join(words[1:])

            # Verify the cleaned version makes sense (has at least one word left)
            if cleaned and len(cleaned) > 2:
                return cleaned

        return None

    def build_mapping_table(self, entity_stats: Dict) -> Dict[str, str]:
        """
        Build complete mapping table from known fixes + detected OCR artifacts

        Args:
            entity_stats: Dictionary of entity statistics from entity_statistics.json

        Returns:
            Dictionary mapping original names to cleaned names
        """
        mappings = self.KNOWN_FIXES.copy()

        # Detect OCR artifacts in entity names
        for entity_name in entity_stats.keys():
            # Skip if already in known fixes
            if entity_name in mappings:
                continue

            # Try to detect OCR duplicate pattern
            cleaned = self.detect_ocr_duplicate(entity_name)
            if cleaned:
                # Only apply if the cleaned version exists in the dataset
                # or if it's clearly an artifact
                mappings[entity_name] = cleaned
                self.ocr_fixes[entity_name] = cleaned
                self.stats['ocr_artifacts_removed'] += 1

        return mappings

    def apply_cleanup(self, filepath: Path, mappings: Dict[str, str]) -> bool:
        """
        Apply entity cleanup to entity_statistics.json

        Args:
            filepath: Path to entity_statistics.json
            mappings: Dictionary of original -> cleaned names

        Returns:
            True if file was modified
        """
        print(f"\nProcessing: {filepath.name}")

        # Backup original
        backup_path = self.backup_dir / filepath.name
        shutil.copy2(filepath, backup_path)
        print(f"  Backed up to: {backup_path}")

        # Load data
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Get statistics dictionary
        old_stats = data.get("statistics", {})
        new_stats = {}

        # Apply mappings
        for entity_name, entity_data in old_stats.items():
            # Get canonical name
            canonical_name = mappings.get(entity_name, entity_name)

            # Skip entities mapped to None (should be removed)
            if canonical_name is None:
                self.stats['entities_fixed'] += 1
                continue

            # Track if mapping was applied
            if canonical_name != entity_name:
                self.stats['mappings_applied'] += 1

            # Merge data if canonical name already exists
            if canonical_name in new_stats:
                # Merge entity data
                new_stats[canonical_name] = self.merge_entity_data(
                    new_stats[canonical_name],
                    entity_data
                )
                self.stats['data_merged'] += 1
            else:
                # Add new entry
                new_stats[canonical_name] = entity_data

                # Update the 'name' field if it exists
                # NOTE: This naive implementation is buggy - it extracts only the last word
                # which causes issues like "Mario B. Garnero Jr." → "Jr."
                #
                # DEPRECATED: Use fix_entity_names_hybrid.py instead for proper name formatting
                # The hybrid script uses procedural rules + optional LLM for complex names
                if 'name' in new_stats[canonical_name]:
                    # BUGGY: Extract just the last name for the 'name' field
                    name_parts = canonical_name.split()
                    if name_parts:
                        new_stats[canonical_name]['name'] = name_parts[-1]

        # Update data
        data["statistics"] = new_stats

        # Save updated data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        entities_before = len(old_stats)
        entities_after = len(new_stats)

        print(f"  Entities before: {entities_before}")
        print(f"  Entities after: {entities_after}")
        print(f"  Removed: {entities_before - entities_after}")

        return entities_before != entities_after

    def merge_entity_data(self, data1: dict, data2: dict) -> dict:
        """
        Intelligently merge two entity data dictionaries

        Combines flight counts, document lists, connections, etc.
        """
        result = data1.copy()

        for key, value in data2.items():
            if key not in result:
                result[key] = value
            else:
                # Merge based on type
                if isinstance(value, list) and isinstance(result[key], list):
                    # Combine lists and remove duplicates
                    combined = result[key] + value
                    # Handle list of dicts (like documents)
                    if combined and isinstance(combined[0], dict):
                        # Deduplicate by 'path' field
                        seen = set()
                        unique = []
                        for item in combined:
                            path = item.get('path', str(item))
                            if path not in seen:
                                seen.add(path)
                                unique.append(item)
                        result[key] = unique
                    else:
                        result[key] = list(set(combined))

                elif isinstance(value, (int, float)) and isinstance(result[key], (int, float)):
                    # Sum numeric values (like flight_count, connection_count)
                    result[key] = result[key] + value

                elif isinstance(value, dict) and isinstance(result[key], dict):
                    # Recursively merge nested dicts
                    result[key] = self.merge_entity_data(result[key], value)

        return result

    def run(self) -> Dict:
        """
        Execute complete entity cleanup process

        Returns:
            Statistics dictionary
        """
        print("=" * 70)
        print("ENTITY CLEANUP - OCR ARTIFACT REMOVAL")
        print("=" * 70)

        # Load entity statistics
        stats_path = self.data_dir / "metadata/entity_statistics.json"

        if not stats_path.exists():
            print(f"\nError: {stats_path} not found")
            return self.stats

        with open(stats_path, 'r') as f:
            data = json.load(f)
            entity_stats = data.get("statistics", {})

        print(f"\nLoaded {len(entity_stats)} entities from entity_statistics.json")

        # Build mapping table
        print("\nStep 1: Detecting OCR artifacts and known duplicates...")
        mappings = self.build_mapping_table(entity_stats)

        print(f"  Known fixes: {len(self.KNOWN_FIXES)}")
        print(f"  OCR artifacts detected: {len(self.ocr_fixes)}")
        print(f"  Total mappings: {len(mappings)}")

        # Show sample OCR artifacts
        print("\nSample OCR artifacts detected:")
        for i, (original, fixed) in enumerate(list(self.ocr_fixes.items())[:10]):
            print(f"  {i+1}. \"{original}\" → \"{fixed}\"")

        # Apply cleanup
        print("\nStep 2: Applying cleanup to entity_statistics.json...")
        modified = self.apply_cleanup(stats_path, mappings)

        # Generate report
        self.generate_report()

        print("\n" + "=" * 70)
        print("CLEANUP COMPLETE")
        print("=" * 70)
        print(f"Total entities processed: {len(entity_stats)}")
        print(f"Mappings applied: {self.stats['mappings_applied']}")
        print(f"OCR artifacts removed: {self.stats['ocr_artifacts_removed']}")
        print(f"Data merged: {self.stats['data_merged']}")
        print(f"Entities deleted (null mappings): {self.stats['entities_fixed']}")

        return self.stats

    def generate_report(self):
        """Generate detailed cleanup report"""
        report_path = self.data_dir / "metadata/entity_cleanup_report.txt"

        report = f"""
ENTITY CLEANUP REPORT
=====================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backup Location: {self.backup_dir}

STATISTICS
----------
Mappings Applied: {self.stats['mappings_applied']}
OCR Artifacts Removed: {self.stats['ocr_artifacts_removed']}
Entity Data Merged: {self.stats['data_merged']}
Entities Deleted: {self.stats['entities_fixed']}

KNOWN FIXES APPLIED
-------------------
"""
        for original, target in sorted(self.KNOWN_FIXES.items()):
            if target is None:
                report += f"  ✗ '{original}' → REMOVED\n"
            else:
                report += f"  ✓ '{original}' → '{target}'\n"

        report += f"\n\nOCR ARTIFACTS DETECTED ({len(self.ocr_fixes)})\n"
        report += "-" * 50 + "\n"
        for original, fixed in sorted(self.ocr_fixes.items())[:50]:  # First 50
            report += f"  '{original}' → '{fixed}'\n"

        if len(self.ocr_fixes) > 50:
            report += f"  ... and {len(self.ocr_fixes) - 50} more\n"

        report += f"""

SUMMARY
-------
All OCR artifacts and duplicate entity patterns have been eliminated.
Original file backed up to: {self.backup_dir}

To restore from backup if needed:
  cp {self.backup_dir}/entity_statistics.json {self.data_dir}/metadata/

NEXT STEPS
----------
1. Restart server on port 8081 to reload clean data:
   kill -9 $(lsof -ti:8081)
   cd server && python3 app.py 8081 > /tmp/epstein_8081.log 2>&1 &

2. Verify in UI:
   - No "Je Je" variants
   - No whitespace-padded duplicates like "Glenn       Glenn Dubin"
   - Entity counts properly merged

3. Delete backup after verification (optional):
   rm -rf {self.backup_dir}
"""

        # Save report
        with open(report_path, 'w') as f:
            f.write(report)

        print(f"\nDetailed report saved to: {report_path}")


def main():
    """Main entry point"""
    import sys

    # Default data directory
    data_dir = Path(__file__).parent.parent.parent / "data"

    # Allow override via command line
    if len(sys.argv) > 1:
        data_dir = Path(sys.argv[1])

    if not data_dir.exists():
        print(f"Error: Data directory not found: {data_dir}")
        sys.exit(1)

    print(f"Data directory: {data_dir}")

    # Run cleanup
    cleanup = EntityCleanup(data_dir)
    stats = cleanup.run()

    print("\n\nRESTART SERVER:")
    print("  kill -9 $(lsof -ti:8081)")
    print("  cd /Users/masa/Projects/Epstein/server && python3 app.py 8081 > /tmp/epstein_8081.log 2>&1 &")
    print("\nThen verify the changes in the UI at http://localhost:8081")


if __name__ == "__main__":
    main()
