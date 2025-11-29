#!/usr/bin/env python3
"""
Add alias system to entity index for improved search.

This script adds aliases to priority entities including:
- Politicians and public figures
- Royalty and nobility
- High-profile individuals
- Anyone with common alternative names

Aliases improve search by allowing users to find entities using:
- Shortened names (Bill Clinton vs. William Clinton)
- Titles (President, Duke, etc.)
- Nicknames (Fergie, etc.)
- Full formal names
"""
import json
from datetime import datetime
from pathlib import Path


def add_aliases():
    """Add alias system to priority entities."""
    entities_dir = Path("data/md/entities")
    index_path = entities_dir / "ENTITIES_INDEX.json"

    # Load index
    print(f"Loading entity index from: {index_path}")
    with open(index_path) as f:
        data = json.load(f)

    entities = data["entities"]
    print(f"Total entities: {len(entities)}")

    # Define comprehensive alias mappings
    alias_mappings = {
        # Politicians
        "William Clinton": [
            "Bill Clinton",
            "President Clinton",
            "William J. Clinton",
            "William Jefferson Clinton",
        ],
        "Donald Trump": ["President Trump", "Donald J. Trump", "The Donald"],
        # Key figures
        "Ghislaine Maxwell": ["Ghislaine", "Maxwell"],
        "Virginia Roberts Giuffre": ["Virginia Roberts", "Virginia Giuffre"],
        # Business figures
        "Bill Gates": ["William Gates", "William H. Gates", "William Henry Gates III"],
        # Celebrities
        "Naomi Campbell": ["Naomi"],
        "Chris Tucker": ["Christopher Tucker"],
        "Kevin Spacey": ["Kevin Spacey Fowler"],
        # Legal/Academic
        "Alan Dershowitz": ["Alan M. Dershowitz", "Professor Dershowitz"],
        # Nobility - extract base names from titles
        "Alistair McAlpine, Baron of West": ["Alistair McAlpine", "Baron of West", "Lord McAlpine"],
        "Edward Stanley, Earl of Derby": ["Edward Stanley", "Earl of Derby", "Lord Derby"],
        "Lady Anouska Weinberg": ["Anouska Weinberg"],
        "Lady Carina Frost": ["Carina Frost"],
        "Lady Carole Bamford": ["Carole Bamford"],
        "Lady Maria Fairweather": ["Maria Fairweather"],
        "Lady Marina Cowdray": ["Marina Cowdray"],
        "Lady Victoria White O'Gara": ["Victoria White O'Gara", "Victoria O'Gara"],
        "Lord George Weidenfeld": ["George Weidenfeld"],
        "Countess Caroline Stanley": ["Caroline Stanley"],
        "Countess Debonnaire Von Bismarck": ["Debonnaire Von Bismarck", "Debonnaire Bismarck"],
        "Duchess Rutland": ["Rutland"],
        "Baroness Francesca Theilmann": ["Francesca Theilmann"],
    }

    # Automatically generate aliases for titles
    title_patterns = {
        "Prince": lambda name: [name.replace("Prince ", ""), name.split(",")[0]],
        "Princess": lambda name: [name.replace("Princess ", ""), name.split(",")[0]],
        "Duke": lambda name: [name.split(",")[0], name.replace("Duke of ", "")],
        "Duchess": lambda name: [name.split(",")[0], name.replace("Duchess of ", "")],
        "Lord": lambda name: [name.replace("Lord ", "")],
        "Lady": lambda name: [name.replace("Lady ", "")],
        "Baron": lambda name: [name.replace("Baron ", ""), name.split(",")[0]],
        "Baroness": lambda name: [name.replace("Baroness ", "")],
        "Count": lambda name: [name.replace("Count ", "")],
        "Countess": lambda name: [name.replace("Countess ", "")],
        "Earl": lambda name: [name.split(",")[0], name.replace("Earl of ", "")],
        "Sir": lambda name: [name.replace("Sir ", "")],
        "Dame": lambda name: [name.replace("Dame ", "")],
    }

    aliases_added = 0
    auto_aliases_added = 0

    print(f"\n{'='*60}")
    print("Adding aliases to priority entities...")
    print(f"{'='*60}\n")

    for entity in entities:
        entity_name = entity.get("name", "")

        # Skip if already has aliases
        if "aliases" in entity:
            continue

        # Check manual mappings first
        if entity_name in alias_mappings:
            entity["aliases"] = alias_mappings[entity_name]
            aliases_added += 1
            print(f"✅ {entity_name}")
            print(f"   Aliases: {alias_mappings[entity_name]}")

        # Auto-generate for titled individuals
        else:
            for title, generator in title_patterns.items():
                if title in entity_name:
                    try:
                        auto_aliases = generator(entity_name)
                        # Clean up and deduplicate
                        auto_aliases = [
                            a.strip()
                            for a in auto_aliases
                            if a.strip() and a.strip() != entity_name
                        ]
                        if auto_aliases:
                            entity["aliases"] = auto_aliases
                            auto_aliases_added += 1
                            print(f"🔄 {entity_name}")
                            print(f"   Auto-aliases: {auto_aliases}")
                            break
                    except Exception as e:
                        print(f"⚠️  Error generating aliases for {entity_name}: {e}")

    # Update metadata
    data["generated_date"] = datetime.now().isoformat()

    # Save updated index
    print(f"\n{'='*60}")
    print("Saving updated index...")
    print(f"{'='*60}")
    with open(index_path, "w") as f:
        json.dump(data, f, indent=2)

    print("\n✅ SUCCESS!")
    print(f"   Manual aliases added: {aliases_added}")
    print(f"   Auto-generated aliases: {auto_aliases_added}")
    print(f"   Total entities with aliases: {aliases_added + auto_aliases_added}")
    print(f"   Index updated: {index_path}")


if __name__ == "__main__":
    add_aliases()
