#!/usr/bin/env python3
"""
Generate entity_name_mappings.json from normalization results

Creates a mapping file compatible with the existing EntityNormalizer class
that other scripts use (rebuild_flight_network.py, etc.)
"""

import json
import re

# Import normalization rules
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))
from normalize_entity_names import KNOWN_ENTITY_MAPPINGS, NAME_DISAMBIGUATIONS


def normalize_name_rule(name: str) -> str:
    """Apply same normalization rules as main normalizer"""
    if not name or not isinstance(name, str):
        return name

    original_name = name.strip()
    name = original_name

    # Handle duplicated first names
    words = name.split()
    if len(words) >= 2 and words[0] == words[1]:
        words = [words[0], *words[2:]]
        name = " ".join(words)

    # Apply abbreviation disambiguations
    for abbrev, full in NAME_DISAMBIGUATIONS.items():
        if name == abbrev or name.startswith(abbrev + " "):
            if " " in name:
                parts = name.split(" ", 1)
                if parts[0] == abbrev:
                    name = full + " " + parts[1]
                    break
            else:
                name = full
                break

    # Apply known entity mappings
    if name in KNOWN_ENTITY_MAPPINGS:
        name = KNOWN_ENTITY_MAPPINGS[name]

    return name


def generate_mappings():
    """
    Generate entity mappings from normalized entities and normalization report.

    Creates mappings for:
    1. Duplicated first names (from normalization report)
    2. Abbreviation expansions (from normalization report)
    3. Entity merges (from ENTITIES_INDEX.json merged_from field)
    4. Whitespace variations (from raw flight logs)
    """

    project_root = Path("/Users/masa/Projects/Epstein")

    mappings = {}

    # Load normalization report to extract all name transformations
    report_path = project_root / "data/metadata/normalization_report.txt"
    with open(report_path) as f:
        lines = f.readlines()

    in_normalization_section = False
    for line in lines:
        if "NAME NORMALIZATIONS APPLIED" in line:
            in_normalization_section = True
            continue
        if in_normalization_section and line.startswith("ENTITY MERGE"):
            break
        if in_normalization_section and "→" in line:
            line = line.strip()
            if line and not line.startswith("-"):
                parts = line.split(" → ")
                if len(parts) == 2:
                    original = parts[0].strip()
                    normalized = parts[1].strip()
                    mappings[original] = normalized

    # Load entities index for merge information
    entities_path = project_root / "data/md/entities/ENTITIES_INDEX.json"
    with open(entities_path) as f:
        entities_data = json.load(f)

    # Add mappings from merged entities
    for entity in entities_data["entities"]:
        canonical = entity["normalized_name"]
        if entity.get("merged_from"):
            for variant in entity["merged_from"]:
                mappings[variant] = canonical

    # Extract all name variations from raw flight logs
    raw_file = project_root / "data/raw/entities/flight_logs_raw.txt"
    with open(raw_file, encoding="utf-8") as f:
        raw_lines = f.readlines()

    raw_names = set()
    for line in raw_lines[2:]:
        if not line.strip() or "Flight Log" not in line:
            continue

        # Extract name using same pattern as rebuild script
        name_match = re.search(
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+[A-Z?]{1,3}\s+(?:Yes|No)\s+Flight Log", line
        )
        if name_match:
            raw_name = name_match.group(1).strip()
            raw_names.add(raw_name)

    print(f"Found {len(raw_names)} unique names in raw flight logs")

    # Generate mappings for all raw names
    new_mappings = 0
    for raw_name in raw_names:
        # Normalize whitespace first (same as EntityNormalizer)
        ws_normalized = re.sub(r"\s+", " ", raw_name).strip()

        # Apply our normalization rules
        canonical = normalize_name_rule(ws_normalized)

        # Add mapping if transformation occurred
        if canonical != raw_name:
            # Add both raw name and whitespace-normalized version
            mappings[raw_name] = canonical
            if ws_normalized not in (raw_name, canonical):
                mappings[ws_normalized] = canonical
            new_mappings += 1

    print(f"Generated {new_mappings} new mappings from raw file")

    # Save mappings
    output_path = project_root / "data/metadata/entity_name_mappings.json"
    with open(output_path, "w") as f:
        json.dump(mappings, f, indent=2, sort_keys=True)

    print(f"✓ Generated {len(mappings)} total entity name mappings")
    print(f"✓ Saved: {output_path}")

    # Show statistics
    unique_canonical = len(set(mappings.values()))
    print("\nStatistics:")
    print(f"  Total mappings: {len(mappings)}")
    print(f"  Unique canonical entities: {unique_canonical}")
    print(f"  Average variants per entity: {len(mappings) / unique_canonical:.1f}")

    # Show key mappings
    print("\nKey entity mappings:")
    key_entities = ["Epstein", "Maxwell", "Clinton", "Kellen"]
    for key in key_entities:
        key_mappings = {k: v for k, v in mappings.items() if key in k}
        if key_mappings:
            print(f"\n  {key} variants:")
            for orig, canon in sorted(key_mappings.items())[:10]:
                print(f"    {orig} → {canon}")

    return mappings


if __name__ == "__main__":
    generate_mappings()
