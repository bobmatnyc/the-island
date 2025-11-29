#!/usr/bin/env python3
"""
Normalize raw flight logs text file

Applies entity name normalization to the raw flight logs text file
that is used by rebuild_flight_network.py
"""

# Import our normalization rules
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent))
from normalize_entity_names import KNOWN_ENTITY_MAPPINGS, NAME_DISAMBIGUATIONS


def normalize_name_in_text(name: str) -> str:
    """Apply normalization rules to a name in flight logs"""
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


def normalize_raw_flight_logs():
    """Normalize all passenger names in raw flight logs text file"""

    project_root = Path("/Users/masa/Projects/Epstein")
    raw_file = project_root / "data/raw/entities/flight_logs_raw.txt"
    backup_file = raw_file.with_suffix(".txt.backup")
    output_file = raw_file

    print(f"Normalizing raw flight logs: {raw_file}")

    # Create backup
    if not backup_file.exists():
        with open(raw_file, encoding="utf-8") as f:
            content = f.read()
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ Created backup: {backup_file}")

    # Read file
    with open(raw_file, encoding="utf-8") as f:
        lines = f.readlines()

    # Pattern to match passenger names in flight log format
    # Typical format: "11/17/1995    N908JE    CMH-PBI    Je  Je Epstein"
    # Names are separated by tabs or multiple spaces

    normalized_lines = []
    changes = 0

    for line in lines:
        if not line.strip():
            normalized_lines.append(line)
            continue

        # Split on tabs first
        parts = line.split("\t")

        if len(parts) >= 4:
            # parts[0] = date, parts[1] = tail, parts[2] = route, parts[3+] = passengers
            date = parts[0]
            tail = parts[1]
            route = parts[2]
            passengers = parts[3:]

            # Normalize each passenger name
            normalized_passengers = []
            for passenger in passengers:
                passenger = passenger.strip()
                if passenger:
                    normalized = normalize_name_in_text(passenger)
                    if normalized != passenger:
                        changes += 1
                    normalized_passengers.append(normalized)

            # Rebuild line
            if normalized_passengers:
                new_line = f"{date}\t{tail}\t{route}\t" + "\t".join(normalized_passengers)
                if not new_line.endswith("\n"):
                    new_line += "\n"
                normalized_lines.append(new_line)
            else:
                normalized_lines.append(line)
        else:
            # Not a standard flight record, keep as-is
            normalized_lines.append(line)

    # Write normalized file
    with open(output_file, "w", encoding="utf-8") as f:
        f.writelines(normalized_lines)

    print(f"✓ Normalized {changes} passenger names")
    print(f"✓ Saved: {output_file}")


if __name__ == "__main__":
    normalize_raw_flight_logs()
