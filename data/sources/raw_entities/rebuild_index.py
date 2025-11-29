#!/usr/bin/env python3
"""
Rebuild unified entity index with corrected flight log data.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path("/Users/masa/Projects/Epstein/data/sources/raw_entities")

def load_flight_logs():
    """Load flight log statistics."""
    with open(BASE_DIR / "flight_logs_stats.json", 'r') as f:
        return json.load(f)

def load_black_book():
    """Parse black book markdown to extract entities."""
    # We'll use the original extraction from CSV
    import csv
    BLACK_BOOK_CSV = Path("/Users/masa/Downloads/Jeffrey Epstein Billionaire Buddies - Black Book.csv")

    entities = {}

    with open(BLACK_BOOK_CSV, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        reader = csv.reader(lines[1:])

        for row in reader:
            if len(row) < 3:
                continue

            billionaire = row[0].strip() if len(row) > 0 else ""
            name = row[1].strip() if len(row) > 1 else ""
            entity_type = row[2].strip() if len(row) > 2 else ""
            page_num = row[3].strip() if len(row) > 3 else ""
            associated_entity = row[5].strip() if len(row) > 5 else ""

            if not name or entity_type != "Person":
                continue

            entities[name] = {
                "name": name,
                "is_billionaire": billionaire.upper() == "YES",
                "page_number": page_num,
                "organization": associated_entity
            }

    return entities

def normalize_name(name):
    """Normalize name for matching."""
    # Remove extra spaces, convert to title case
    return ' '.join(name.split()).title()

def create_unified_index():
    """Create unified entity index with all sources."""

    print("Loading data sources...")

    # Load all data
    flight_logs = load_flight_logs()
    black_book = load_black_book()

    print(f"  Black Book: {len(black_book)} persons")
    print(f"  Flight Logs: {len(flight_logs['passengers'])} passengers")

    # Build unified entity map
    entities = {}

    # Add Black Book entries
    for name, data in black_book.items():
        norm_name = normalize_name(name)

        entities[norm_name] = {
            "name": name,
            "normalized_name": norm_name,
            "sources": ["black_book"],
            "contact_info": {},
            "flights": 0,
            "is_billionaire": data["is_billionaire"],
            "organizations": [data["organization"]] if data["organization"] else [],
            "black_book_page": data["page_number"],
            "categories": []
        }

    # Add Flight Log entries
    for passenger, stats in flight_logs["passengers"].items():
        norm_name = normalize_name(passenger)

        if norm_name in entities:
            # Merge with existing
            entities[norm_name]["sources"].append("flight_logs")
            entities[norm_name]["flights"] = stats["trips"]
            entities[norm_name]["first_flight"] = stats["first_flight"]
            entities[norm_name]["last_flight"] = stats["last_flight"]
            entities[norm_name]["routes"] = stats["routes"]
        else:
            # New entity from flight logs only
            entities[norm_name] = {
                "name": passenger,
                "normalized_name": norm_name,
                "sources": ["flight_logs"],
                "contact_info": {},
                "flights": stats["trips"],
                "first_flight": stats["first_flight"],
                "last_flight": stats["last_flight"],
                "routes": stats["routes"],
                "is_billionaire": False,
                "organizations": [],
                "categories": []
            }

    # Calculate statistics
    entity_list = list(entities.values())

    # Source overlaps
    source_counts = defaultdict(int)
    for entity in entity_list:
        source_key = tuple(sorted(set(entity["sources"])))
        source_counts[source_key] += 1

    # Billionaires
    billionaires = [e for e in entity_list if e.get("is_billionaire")]
    in_both_sources = [e for e in entity_list if len(set(e["sources"])) > 1]

    # Top frequent flyers
    top_flyers = sorted([e for e in entity_list if e.get("flights", 0) > 0],
                       key=lambda x: x["flights"], reverse=True)[:50]

    index = {
        "generated_date": datetime.now().isoformat(),
        "total_entities": len(entity_list),
        "statistics": {
            "total_persons": len(entity_list),
            "billionaires": len(billionaires),
            "in_black_book": len([e for e in entity_list if "black_book" in e["sources"]]),
            "in_flight_logs": len([e for e in entity_list if "flight_logs" in e["sources"]]),
            "in_both_sources": len(in_both_sources),
            "total_flight_records": flight_logs["total_flights"]
        },
        "source_overlaps": {
            " + ".join(sources): count
            for sources, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
        },
        "top_frequent_flyers": [
            {
                "name": e["name"],
                "trips": e["flights"],
                "in_black_book": "black_book" in e["sources"],
                "is_billionaire": e.get("is_billionaire", False)
            }
            for e in top_flyers[:20]
        ],
        "billionaires_in_flight_logs": [
            {
                "name": e["name"],
                "trips": e.get("flights", 0),
                "organizations": e.get("organizations", [])
            }
            for e in billionaires if e.get("flights", 0) > 0
        ],
        "entities": entity_list
    }

    return index

def create_summary_report(index):
    """Create human-readable summary report."""

    md = f"""# Epstein Entity Extraction Summary

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview

This report summarizes entities extracted from multiple Jeffrey Epstein-related sources.

## Sources Processed

1. ✅ **Black Book CSV** - 1,740 entries
2. ✅ **Birthday Book PDF** - 161 entries (raw extraction)
3. ✅ **Flight Logs PDF** - 3,721 flight records
4. ⚠️ **Little Black Book (Business Insider)** - Duplicate of Black Book CSV

## Statistics

- **Total Unique Entities**: {index['statistics']['total_persons']:,}
- **Billionaires Identified**: {index['statistics']['billionaires']}
- **In Black Book**: {index['statistics']['in_black_book']:,}
- **In Flight Logs**: {index['statistics']['in_flight_logs']:,}
- **In Both Sources**: {index['statistics']['in_both_sources']}
- **Total Flight Records**: {index['statistics']['total_flight_records']:,}

## Source Overlaps

"""

    for sources, count in index['source_overlaps'].items():
        md += f"- **{sources}**: {count:,} entities\n"

    md += "\n## Top 20 Frequent Flyers\n\n"
    md += "| Rank | Name | Trips | In Black Book | Billionaire |\n"
    md += "|------|------|-------|---------------|-------------|\n"

    for i, flyer in enumerate(index['top_frequent_flyers'], 1):
        in_bb = "✓" if flyer['in_black_book'] else ""
        is_bill = "💰" if flyer['is_billionaire'] else ""
        md += f"| {i} | {flyer['name']} | {flyer['trips']} | {in_bb} | {is_bill} |\n"

    md += "\n## Billionaires in Flight Logs\n\n"

    if index['billionaires_in_flight_logs']:
        md += "| Name | Trips | Organizations |\n"
        md += "|------|-------|---------------|\n"

        for b in sorted(index['billionaires_in_flight_logs'], key=lambda x: x['trips'], reverse=True):
            orgs = ', '.join(b['organizations'][:2]) if b['organizations'] else 'N/A'
            md += f"| {b['name']} | {b['trips']} | {orgs} |\n"
    else:
        md += "*No billionaires found in flight logs with current matching.*\n"

    md += """

## Files Generated

### Markdown Files

1. **black_book.md** - All entities from the Black Book
   - 1,740 entries including persons, organizations, and services
   - Organized by type with billionaire markers

2. **birthday_book.md** - Contacts from Birthday Book
   - 161 entries extracted from PDF
   - Note: Requires manual review for OCR errors

3. **flight_logs.md** - Flight log analysis
   - 3,721 flight records
   - 358 unique passengers
   - Top frequent flyers with detailed statistics

4. **little_black_book.md** - Notes on Business Insider source
   - Identified as duplicate of Black Book CSV
   - Web scraping blocked

### Data Files

1. **ENTITIES_INDEX.json** - Unified entity index
   - All entities with cross-referenced sources
   - Complete metadata and statistics

2. **flight_logs_stats.json** - Flight log statistics
   - Per-passenger trip counts
   - Routes and date ranges

3. **Raw extraction files**:
   - birthday_book_raw.txt
   - flight_logs_raw.txt

## Data Quality Notes

### Black Book
- ✅ High quality, structured CSV data
- ✅ Complete with page numbers and categories
- ✅ Billionaire flags included

### Birthday Book
- ⚠️ OCR extraction has errors
- ⚠️ Names partially corrupted
- 📝 Requires manual cleanup
- ✅ Raw text preserved for review

### Flight Logs
- ✅ Structured table successfully parsed
- ✅ 3,721 flight records extracted
- ✅ Passenger names, dates, routes captured
- ⚠️ Some duplicate name variations (e.g., "Je Epstein" vs "Je         Je Epstein")
- 📝 Name normalization needed

## Recommended Next Steps

1. **Name Normalization**: Consolidate name variations in flight logs
2. **Birthday Book OCR**: Manual review and correction of birthday book entries
3. **Cross-Reference Matching**: Fuzzy matching to link similar names across sources
4. **Entity Classification**: Tag entities by role (associate, employee, victim, etc.)
5. **Network Analysis**: Build relationship graph from co-occurrence in flight logs
6. **Timeline Construction**: Create chronological timeline from flight dates

## Files Location

All files are located in:
```
/Users/masa/Projects/Epstein/data/sources/raw_entities/
```

## Usage

To load and analyze the unified index:

```python
import json

with open('ENTITIES_INDEX.json', 'r') as f:
    index = json.load(f)

# Example: Find all billionaires
billionaires = [e for e in index['entities'] if e['is_billionaire']]

# Example: Find frequent flyers (>10 trips)
frequent_flyers = [e for e in index['entities'] if e.get('flights', 0) > 10]

# Example: Find entities in both sources
in_both = [e for e in index['entities'] if len(set(e['sources'])) > 1]
```

---

*This extraction is part of ongoing research and documentation efforts.*
"""

    return md

def main():
    print("Building unified entity index...\n")

    index = create_unified_index()

    # Save index
    index_file = BASE_DIR / "ENTITIES_INDEX.json"
    with open(index_file, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"\nSaved unified index to {index_file}")
    print(f"Total entities: {index['total_entities']:,}")

    # Create summary report
    print("\nGenerating summary report...")
    summary = create_summary_report(index)

    summary_file = BASE_DIR / "EXTRACTION_SUMMARY.md"
    summary_file.write_text(summary)

    print(f"Saved summary report to {summary_file}")

    print("\n" + "="*60)
    print("INDEX REBUILD COMPLETE")
    print("="*60)

    print(f"\nStatistics:")
    for key, value in index['statistics'].items():
        print(f"  {key}: {value:,}")

if __name__ == "__main__":
    main()
