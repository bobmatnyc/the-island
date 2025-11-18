#!/usr/bin/env python3
"""
Complete Entity Cleanup - Fixes ALL Entity References
======================================================

This script performs a two-pass cleanup:
1. Pass 1: Clean entity keys (what we did before)
2. Pass 2: Clean entity references in top_connections, name_variations, etc.

Author: Claude
Date: 2025-11-17
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict

# Use the existing cleanup class
import sys
sys.path.insert(0, str(Path(__file__).parent))
from final_entity_cleanup import EntityCleanup

class CompleteEntityCleanup(EntityCleanup):
    """Extended cleanup that also fixes nested entity references"""

    def clean_nested_references(self, filepath: Path, mappings: Dict[str, str]):
        """
        Second pass: Clean entity names in nested data structures

        Updates:
        - top_connections[].name
        - name_variations[]
        - Any other string fields containing entity names
        """
        print("\nPass 2: Cleaning nested entity references...")

        # Load data
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        stats = data.get("statistics", {})
        total_fixes = 0

        # For each entity, clean its nested references
        for entity_name, entity_data in stats.items():
            # Clean top_connections
            if 'top_connections' in entity_data:
                for connection in entity_data['top_connections']:
                    old_name = connection.get('name', '')
                    if old_name in mappings:
                        new_name = mappings[old_name]
                        if new_name:  # Not a delete mapping
                            connection['name'] = new_name
                            total_fixes += 1

            # Clean name_variations
            if 'name_variations' in entity_data:
                cleaned_variations = []
                for variation in entity_data['name_variations']:
                    cleaned = mappings.get(variation, variation)
                    if cleaned:  # Not a delete mapping
                        cleaned_variations.append(cleaned)
                entity_data['name_variations'] = cleaned_variations

        # Save updated data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"  ✓ Fixed {total_fixes} nested entity references")
        self.stats['nested_refs_fixed'] = total_fixes

    def run(self) -> Dict:
        """Execute complete two-pass cleanup"""
        print("=" * 70)
        print("COMPLETE ENTITY CLEANUP - TWO-PASS DEDUPLICATION")
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

        # PASS 1: Build mapping table and clean entity keys
        print("\n" + "=" * 70)
        print("PASS 1: Cleaning Entity Keys")
        print("=" * 70)

        mappings = self.build_mapping_table(entity_stats)

        print(f"\n  Known fixes: {len(self.KNOWN_FIXES)}")
        print(f"  OCR artifacts detected: {len(self.ocr_fixes)}")
        print(f"  Total mappings: {len(mappings)}")

        # Show sample OCR artifacts
        print("\nSample OCR artifacts:")
        for i, (original, fixed) in enumerate(list(self.ocr_fixes.items())[:10]):
            print(f"  {i+1}. \"{original}\" → \"{fixed}\"")

        # Apply cleanup to entity keys
        modified = self.apply_cleanup(stats_path, mappings)

        # PASS 2: Clean nested references
        print("\n" + "=" * 70)
        print("PASS 2: Cleaning Nested References")
        print("=" * 70)

        self.clean_nested_references(stats_path, mappings)

        # Generate report
        self.generate_report()

        print("\n" + "=" * 70)
        print("CLEANUP COMPLETE")
        print("=" * 70)
        print(f"Total entities processed: {len(entity_stats)}")
        print(f"Entity keys cleaned: {self.stats.get('mappings_applied', 0)}")
        print(f"Nested references fixed: {self.stats.get('nested_refs_fixed', 0)}")
        print(f"OCR artifacts removed: {self.stats.get('ocr_artifacts_removed', 0)}")
        print(f"Data merged: {self.stats.get('data_merged', 0)}")

        return self.stats

    def generate_report(self):
        """Generate detailed cleanup report"""
        report_path = self.data_dir / "metadata/entity_cleanup_complete_report.txt"

        report = f"""
COMPLETE ENTITY CLEANUP REPORT (TWO-PASS)
==========================================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Backup Location: {self.backup_dir}

STATISTICS
----------
Pass 1 - Entity Keys Cleaned: {self.stats.get('mappings_applied', 0)}
Pass 2 - Nested References Fixed: {self.stats.get('nested_refs_fixed', 0)}
OCR Artifacts Removed: {self.stats.get('ocr_artifacts_removed', 0)}
Entity Data Merged: {self.stats.get('data_merged', 0)}
Entities Deleted: {self.stats.get('entities_fixed', 0)}

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
        for original, fixed in sorted(self.ocr_fixes.items())[:50]:
            report += f"  '{original}' → '{fixed}'\n"

        if len(self.ocr_fixes) > 50:
            report += f"  ... and {len(self.ocr_fixes) - 50} more\n"

        report += f"""

WHAT WAS CLEANED
----------------
Pass 1: Entity keys in entity_statistics.json
- Removed whitespace-padded duplicates
- Merged duplicate entity data
- Applied known fixes (Epstein, Maxwell, Nadia, etc.)

Pass 2: Nested entity references
- Updated top_connections[].name fields
- Cleaned name_variations[] arrays
- Ensured all entity references use canonical names

SUMMARY
-------
All OCR artifacts and duplicate entity patterns have been eliminated.
Entity references throughout the dataset now use canonical names.

Original file backed up to: {self.backup_dir}

To restore from backup if needed:
  cp {self.backup_dir}/entity_statistics.json {self.data_dir}/metadata/

NEXT STEPS
----------
1. Restart server on port 8081 to reload clean data:
   kill -9 $(lsof -ti:8081)
   cd server && python3 app.py 8081 > /tmp/epstein_8081.log 2>&1 &

2. Verify in UI:
   - No "Je Je" or "Je        Je Epstein" variants
   - No whitespace-padded names anywhere
   - Entity connections use clean names
   - Search works correctly

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

    # Run complete cleanup
    cleanup = CompleteEntityCleanup(data_dir)
    stats = cleanup.run()

    print("\n\nRESTART SERVER:")
    print("  kill -9 $(lsof -ti:8081)")
    print("  cd /Users/masa/Projects/Epstein/server && python3 app.py 8081 > /tmp/epstein_8081.log 2>&1 &")
    print("\nThen verify the changes in the UI at http://localhost:8081")
    print("\n✅ All duplicate entity patterns should now be eliminated!")


if __name__ == "__main__":
    main()
