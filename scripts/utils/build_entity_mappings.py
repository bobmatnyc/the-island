#!/usr/bin/env python3
"""
Build entity name normalization mappings.

Analyzes entity names to identify variations and create canonical mappings.
Handles:
- Whitespace normalization (Je        Je Epstein -> Jeffrey Epstein)
- Duplicated names (Ghislaine Ghislaine -> Ghislaine Maxwell)
- Common abbreviations (Bill -> William, etc.)
- Prefix/title removal (President, Mr., etc.)
"""

import json
import re
from pathlib import Path


def normalize_whitespace(name: str) -> str:
    """Normalize excessive whitespace in names."""
    # Replace multiple spaces with single space
    name = re.sub(r"\s+", " ", name)
    # Strip leading/trailing whitespace
    return name.strip()


def detect_duplicated_names(name: str) -> str | None:
    """Detect patterns like 'Ghislaine Ghislaine' and return canonical form."""
    parts = name.split()
    if len(parts) == 2 and parts[0] == parts[1]:
        # Duplicated single name (e.g., "Ghislaine Ghislaine")
        return parts[0]
    return None


def build_name_mappings(entities_index_path: Path) -> dict[str, str]:
    """Build comprehensive name normalization mappings.

    Returns:
        Dictionary mapping variant names to canonical names
    """
    with open(entities_index_path) as f:
        data = json.load(f)

    entities = data["entities"]
    mappings: dict[str, str] = {}

    # Track all variations of each normalized base name
    base_name_variations: dict[str, set[str]] = {}

    for entity in entities:
        original_name = entity["name"]

        # Step 1: Normalize whitespace
        normalized = normalize_whitespace(original_name)

        # Step 2: Check for duplicated names
        deduped = detect_duplicated_names(normalized)
        if deduped:
            normalized = deduped

        # Track this variation
        if normalized != original_name:
            if normalized not in base_name_variations:
                base_name_variations[normalized] = set()
            base_name_variations[normalized].add(original_name)

    # Manual mappings for known entities
    manual_mappings = {
        # Jeffrey Epstein variations
        "Je Epstein": "Jeffrey Epstein",
        "Je Je Epstein": "Jeffrey Epstein",
        "J Epstein": "Jeffrey Epstein",
        "Jeff Epstein": "Jeffrey Epstein",
        "JE": "Jeffrey Epstein",
        "Mark Epstein": "Mark Epstein",  # Brother - keep separate
        "Paula Epstein": "Paula Epstein",  # Keep separate
        # Ghislaine Maxwell variations
        "Ghislaine": "Ghislaine Maxwell",
        "Ghislaine Ghislaine": "Ghislaine Maxwell",
        "GM": "Ghislaine Maxwell",
        "G Maxwell": "Ghislaine Maxwell",
        # Bill Clinton variations
        "Bill Clinton": "William Clinton",
        "Bill Bill Clinton": "William Clinton",
        "President Clinton": "William Clinton",
        "WJC": "William Clinton",
        # Donald Trump variations
        "Donald Trump": "Donald Trump",
        "President Trump": "Donald Trump",
        "DJT": "Donald Trump",
        # Prince Andrew variations
        "Prince Andrew": "Andrew Windsor",
        "Andrew": "Andrew Windsor",
        "HRH Andrew": "Andrew Windsor",
        # Alan Dershowitz variations
        "Alan Dershowitz": "Alan Dershowitz",
        "Dershowitz": "Alan Dershowitz",
        "Prof Dershowitz": "Alan Dershowitz",
        # Other known individuals with duplicated names in flight logs
        "Nadia Nadia": "Nadia Marcinkova",
        "Sarah Kellen": "Sarah Kellen",
        "Sarah Sarah Kellen": "Sarah Kellen",
        "Emmy Tayler": "Emmy Tayler",
        "Emmy Emmy Tayler": "Emmy Tayler",
        "Virginia Roberts": "Virginia Giuffre",
        "Virginia Virginia Roberts": "Virginia Giuffre",
    }

    # Build final mappings
    for base_name, variants in base_name_variations.items():
        for variant in variants:
            # Check if we have a manual mapping for the base name
            canonical = manual_mappings.get(base_name, base_name)
            mappings[variant] = canonical

            # Also map the normalized version if different
            if base_name != canonical:
                mappings[base_name] = canonical

    # Add manual mappings directly
    mappings.update(manual_mappings)

    return mappings


def analyze_mappings(mappings: dict[str, str]) -> None:
    """Print analysis of the mappings."""
    print(f"Total mappings: {len(mappings)}")

    # Group by canonical name
    by_canonical: dict[str, list[str]] = {}
    for variant, canonical in mappings.items():
        if canonical not in by_canonical:
            by_canonical[canonical] = []
        by_canonical[canonical].append(variant)

    print("\nMost mapped entities (top 10):")
    sorted_entities = sorted(by_canonical.items(), key=lambda x: len(x[1]), reverse=True)
    for canonical, variants in sorted_entities[:10]:
        print(f"  {canonical}: {len(variants)} variants")
        for variant in sorted(variants)[:5]:
            if variant != canonical:
                print(f"    - {variant}")
        if len(variants) > 5:
            print(f"    ... and {len(variants) - 5} more")


def main():
    """Build and save entity name mappings."""
    project_root = Path(__file__).parent.parent.parent
    entities_index = project_root / "data" / "md" / "entities" / "ENTITIES_INDEX.json"
    output_path = project_root / "data" / "metadata" / "entity_name_mappings.json"

    print("Building entity name mappings...")
    mappings = build_name_mappings(entities_index)

    print("\nAnalyzing mappings...")
    analyze_mappings(mappings)

    # Save mappings
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(mappings, f, indent=2, sort_keys=True)

    print(f"\nMappings saved to: {output_path}")

    # Show some example mappings
    print("\nExample mappings:")
    examples = [
        "Je        Je Epstein",
        "Ghislaine Ghislaine",
        "Bill Clinton",
        "Bill        Bill Clinton",
    ]
    for name in examples:
        if name in mappings:
            print(f"  '{name}' -> '{mappings[name]}'")


if __name__ == "__main__":
    main()
