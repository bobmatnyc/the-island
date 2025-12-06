#!/usr/bin/env python3
"""
Fix critical entity classification issues:
1. Ghislaine Maxwell: organization -> person
2. NPA (Non-Prosecution Agreement): Remove from locations (it's an acronym, not a location)

Related Linear ticket: Entity classification cleanup
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Paths to metadata files
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data" / "metadata"

ENTITY_ORGS_FILE = DATA_DIR / "entity_organizations.json"
ENTITY_LOCS_FILE = DATA_DIR / "entity_locations.json"
ENTITY_BIOS_FILE = DATA_DIR / "entity_biographies.json"


def backup_file(filepath: Path) -> Path:
    """Create timestamped backup of file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = filepath.parent / f"{filepath.stem}_backup_{timestamp}{filepath.suffix}"

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Created backup: {backup_path.name}")
    return backup_path


def fix_ghislaine_maxwell():
    """
    Move Ghislaine Maxwell from organizations to person.

    Design Decision: Ghislaine Maxwell is a person, not an organization.
    This was likely misclassified due to entity extraction issues.
    """
    print("\n" + "="*60)
    print("FIXING GHISLAINE MAXWELL CLASSIFICATION")
    print("="*60)

    # Load organizations file
    with open(ENTITY_ORGS_FILE, 'r', encoding='utf-8') as f:
        orgs_data = json.load(f)

    # Find Ghislaine Maxwell in organizations (entities is a dict, not array)
    ghislaine_org = orgs_data['entities'].get("Ghislaine Maxwell")

    if not ghislaine_org:
        print("⚠ Ghislaine Maxwell not found in organizations file")
        return False

    print(f"Found Ghislaine Maxwell in organizations:")
    print(f"  - Mention count: {ghislaine_org['mention_count']}")
    print(f"  - Document count: {len(ghislaine_org['documents'])}")

    # Load entity_biographies.json to add person entry
    with open(ENTITY_BIOS_FILE, 'r', encoding='utf-8') as f:
        bios_data = json.load(f)

    # Create person entry in entity_biographies.json
    bios_data["Ghislaine Maxwell"] = {
        "name": "Ghislaine Maxwell",
        "entity_type": "person",
        "summary": "British socialite and close associate of Jeffrey Epstein. Convicted in 2021 on federal charges including sex trafficking of minors.",
        "metadata": {
            "corrected_from": "organization",
            "correction_date": datetime.now().isoformat(),
            "correction_reason": "Misclassified as organization - is actually a person"
        }
    }

    # Remove from organizations file
    if "Ghislaine Maxwell" in orgs_data['entities']:
        del orgs_data['entities']["Ghislaine Maxwell"]
    orgs_data['metadata']['total_organizations'] = len(orgs_data['entities'])
    orgs_data['metadata']['last_updated'] = datetime.now().isoformat()

    # Save updated files
    with open(ENTITY_BIOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(bios_data, f, indent=2, ensure_ascii=False)

    with open(ENTITY_ORGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orgs_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Moved Ghislaine Maxwell from organizations to persons")
    print(f"✓ Updated organization count: {orgs_data['metadata']['total_organizations']}")
    return True


def remove_npa():
    """
    Remove NPA (Non-Prosecution Agreement) from locations.

    Design Decision: NPA is an acronym for "Non-Prosecution Agreement",
    not a geographic location. Should not be in entity_locations.json.
    """
    print("\n" + "="*60)
    print("REMOVING NPA FROM LOCATIONS")
    print("="*60)

    # Load locations file
    with open(ENTITY_LOCS_FILE, 'r', encoding='utf-8') as f:
        locs_data = json.load(f)

    # Find NPA in locations (entities is a dict, not array)
    npa_loc = locs_data['entities'].get("NPA")

    if not npa_loc:
        print("⚠ NPA not found in locations file")
        return False

    print(f"Found NPA in locations:")
    print(f"  - Mention count: {npa_loc['mention_count']}")
    print(f"  - Document count: {len(npa_loc['documents'])}")

    # Remove from locations file
    if "NPA" in locs_data['entities']:
        del locs_data['entities']["NPA"]
    locs_data['metadata']['total_locations'] = len(locs_data['entities'])
    locs_data['metadata']['last_updated'] = datetime.now().isoformat()

    # Save updated file
    with open(ENTITY_LOCS_FILE, 'w', encoding='utf-8') as f:
        json.dump(locs_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Removed NPA from locations")
    print(f"✓ Updated location count: {locs_data['metadata']['total_locations']}")
    return True


def main():
    """Run all entity classification fixes."""
    print("\n🔧 Entity Classification Fixes")
    print("="*60)

    # Create backups
    print("\n📦 Creating backups...")
    backup_file(ENTITY_ORGS_FILE)
    backup_file(ENTITY_LOCS_FILE)
    backup_file(ENTITY_BIOS_FILE)

    # Apply fixes
    ghislaine_fixed = fix_ghislaine_maxwell()
    npa_fixed = remove_npa()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"✓ Ghislaine Maxwell: {'Fixed' if ghislaine_fixed else 'No change'}")
    print(f"✓ NPA removal: {'Fixed' if npa_fixed else 'No change'}")
    print("\n🎉 Entity classification fixes complete!")


if __name__ == "__main__":
    main()
