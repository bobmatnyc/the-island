#!/usr/bin/env python3
"""
Extract entities from multiple Epstein sources and create unified markdown files.
"""

import csv
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set

# Paths
BASE_DIR = Path("/Users/masa/Projects/Epstein/data/sources/raw_entities")
BLACK_BOOK_CSV = Path("/Users/masa/Downloads/Jeffrey Epstein Billionaire Buddies - Black Book.csv")
FLIGHT_LOGS_PDF = Path("/Users/masa/Downloads/EPSTEIN FLIGHT LOGS UNREDACTED.pdf")
BIRTHDAY_BOOK_PDF = BASE_DIR / "epstein-birthday-book.pdf"

def extract_black_book_csv() -> List[Dict]:
    """Extract entities from the Black Book CSV."""
    entities = []

    with open(BLACK_BOOK_CSV, 'r', encoding='utf-8') as f:
        # Skip first row (seems to be header row)
        lines = f.readlines()
        reader = csv.reader(lines[1:])  # Skip first row

        for row in reader:
            if len(row) < 3:
                continue

            billionaire = row[0].strip() if len(row) > 0 else ""
            name = row[1].strip() if len(row) > 1 else ""
            entity_type = row[2].strip() if len(row) > 2 else ""
            page_num = row[3].strip() if len(row) > 3 else ""
            associated_terms = row[4].strip() if len(row) > 4 else ""
            associated_entity = row[5].strip() if len(row) > 5 else ""
            other_info = row[6].strip() if len(row) > 6 else ""
            source1 = row[7].strip() if len(row) > 7 else ""
            source2 = row[8].strip() if len(row) > 8 else ""
            flight_logs = row[9].strip() if len(row) > 9 else ""

            # Additional columns
            extra_cols = row[10:] if len(row) > 10 else []

            if not name:
                continue

            entity = {
                "name": name,
                "type": entity_type,
                "is_billionaire": billionaire.upper() == "YES",
                "page_number": page_num,
                "associated_terms": associated_terms,
                "associated_entity": associated_entity,
                "other_info": other_info,
                "sources": [s for s in [source1, source2] if s],
                "in_flight_logs": flight_logs.strip() != "",
                "extra_data": extra_cols
            }

            entities.append(entity)

    return entities

def create_black_book_markdown(entities: List[Dict]) -> str:
    """Create markdown file for Black Book entities."""

    total_entries = len(entities)
    billionaires = sum(1 for e in entities if e.get('is_billionaire'))
    in_flight_logs = sum(1 for e in entities if e.get('in_flight_logs'))

    md = f"""---
source_type: "contact_book"
source_name: "Jeffrey Epstein Black Book"
source_url: "https://www.documentcloud.org/documents/1508273-jeffrey-epsteins-little-black-book-redacted.html"
download_date: "{datetime.now().strftime('%Y-%m-%d')}"
total_entries: {total_entries}
billionaires: {billionaires}
in_flight_logs: {in_flight_logs}
extraction_method: "csv_parse"
---

# Epstein Black Book

## Metadata
- **Total Contacts**: {total_entries}
- **Billionaires**: {billionaires}
- **Also in Flight Logs**: {in_flight_logs}
- **Source**: CSV export from DocumentCloud

## Entities Extracted

"""

    # Group by type
    by_type = defaultdict(list)
    for entity in entities:
        entity_type = entity.get('type', 'Unknown')
        by_type[entity_type].append(entity)

    for entity_type, type_entities in sorted(by_type.items()):
        md += f"\n### {entity_type} ({len(type_entities)} entries)\n\n"

        for entity in sorted(type_entities, key=lambda x: x.get('name', '')):
            name = entity.get('name', 'Unknown')
            is_billionaire = " 💰" if entity.get('is_billionaire') else ""
            in_logs = " ✈️" if entity.get('in_flight_logs') else ""

            md += f"#### {name}{is_billionaire}{in_logs}\n\n"

            if entity.get('page_number'):
                md += f"- **Page Number**: {entity['page_number']}\n"
            if entity.get('associated_entity'):
                md += f"- **Organization**: {entity['associated_entity']}\n"
            if entity.get('associated_terms'):
                md += f"- **Associated Terms**: {entity['associated_terms']}\n"
            if entity.get('other_info'):
                md += f"- **Notes**: {entity['other_info']}\n"
            if entity.get('sources'):
                md += f"- **Sources**: {', '.join(entity['sources'])}\n"

            md += "\n"

    return md

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ['pdftotext', '-layout', str(pdf_path), '-'],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout
    except Exception as e:
        print(f"Error extracting PDF {pdf_path}: {e}")
        return ""

def extract_birthday_book() -> List[Dict]:
    """Extract entities from Birthday Book PDF."""
    text = extract_pdf_text(BIRTHDAY_BOOK_PDF)

    if not text:
        return []

    entities = []

    # Save raw text for manual review
    with open(BASE_DIR / "birthday_book_raw.txt", 'w') as f:
        f.write(text)

    # Pattern matching for contact entries
    # This is simplified - birthday books often have structured entries
    lines = text.split('\n')

    current_entry = None

    for line in lines:
        line = line.strip()
        if not line:
            if current_entry:
                entities.append(current_entry)
                current_entry = None
            continue

        # Detect name lines (usually capitalized or have specific format)
        # This is a basic heuristic - adjust based on actual format
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+', line):
            if current_entry:
                entities.append(current_entry)

            current_entry = {
                "name": line,
                "contact_info": [],
                "notes": []
            }
        elif current_entry:
            # Check for phone numbers
            if re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}', line):
                current_entry["contact_info"].append(line)
            # Check for email
            elif '@' in line:
                current_entry["contact_info"].append(line)
            # Check for addresses (contains numbers and street indicators)
            elif re.search(r'\d+.*(?:street|avenue|road|lane|drive|st|ave|rd)', line, re.IGNORECASE):
                current_entry["contact_info"].append(line)
            else:
                current_entry["notes"].append(line)

    if current_entry:
        entities.append(current_entry)

    return entities

def create_birthday_book_markdown(entities: List[Dict], raw_text: str) -> str:
    """Create markdown file for Birthday Book entities."""

    total_entries = len(entities)
    pages = raw_text.count('\f') + 1  # Form feed characters indicate page breaks

    md = f"""---
source_type: "birthday_book"
source_name: "Epstein Birthday Book"
source_url: "https://www.documentcloud.org/documents/26086657-epstein-birthday-book/"
download_date: "{datetime.now().strftime('%Y-%m-%d')}"
total_entries: {total_entries}
pages: {pages}
extraction_method: "pdf_extraction"
---

# Epstein Birthday Book

## Metadata
- **Pages**: ~{pages}
- **Total Contacts**: {total_entries}
- **Note**: Raw text saved to birthday_book_raw.txt for manual review

## Entities Extracted

"""

    for entity in entities:
        name = entity.get('name', 'Unknown')
        md += f"### {name}\n\n"

        if entity.get('contact_info'):
            md += f"- **Contact Info**: {', '.join(entity['contact_info'])}\n"

        if entity.get('notes'):
            md += f"- **Notes**: {' | '.join(entity['notes'])}\n"

        md += "\n"

    return md

def extract_flight_logs() -> List[Dict]:
    """Extract flight log data from PDF."""
    text = extract_pdf_text(FLIGHT_LOGS_PDF)

    if not text:
        return []

    # Save raw text
    with open(BASE_DIR / "flight_logs_raw.txt", 'w') as f:
        f.write(text)

    trips = []
    passengers_set = set()

    # Flight logs typically have structured format
    # Pattern: Date, Tail Number, From, To, Passengers
    lines = text.split('\n')

    current_trip = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for date patterns
        date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', line)

        # Look for tail numbers (N-numbers)
        tail_match = re.search(r'\b(N\d{3,5}[A-Z]{0,2})\b', line)

        if date_match:
            if current_trip:
                trips.append(current_trip)

            current_trip = {
                "date": date_match.group(1),
                "tail_number": tail_match.group(1) if tail_match else "",
                "passengers": [],
                "raw_line": line
            }
        elif current_trip:
            # Extract passenger names (usually capitalized names)
            names = re.findall(r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b', line)
            for name in names:
                if name not in current_trip["passengers"]:
                    current_trip["passengers"].append(name)
                    passengers_set.add(name)

    if current_trip:
        trips.append(current_trip)

    return trips

def create_flight_logs_markdown(trips: List[Dict]) -> str:
    """Create markdown file for flight logs."""

    # Calculate statistics
    total_trips = len(trips)

    passenger_counts = defaultdict(int)
    for trip in trips:
        for passenger in trip.get('passengers', []):
            passenger_counts[passenger] += 1

    unique_passengers = len(passenger_counts)

    md = f"""---
source_type: "flight_log"
source_name: "Epstein Flight Logs (Unredacted)"
source_url: "Court documents"
download_date: "{datetime.now().strftime('%Y-%m-%d')}"
total_trips: {total_trips}
unique_passengers: {unique_passengers}
extraction_method: "pdf_extraction"
---

# Epstein Flight Logs (Unredacted)

## Metadata
- **Total Trips**: {total_trips}
- **Unique Passengers**: {unique_passengers}
- **Note**: Raw text saved to flight_logs_raw.txt for manual review

## Frequent Flyers (Top 20)

"""

    # Add top frequent flyers
    for passenger, count in sorted(passenger_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        md += f"- **{passenger}**: {count} trips\n"

    md += "\n## Flight Log Entries\n\n"

    # Add individual trips
    for trip in trips[:100]:  # Limit to first 100 for readability
        date = trip.get('date', 'Unknown')
        tail = trip.get('tail_number', 'Unknown')
        passengers = trip.get('passengers', [])

        md += f"### {date} - {tail}\n\n"
        if passengers:
            md += f"**Passengers**: {', '.join(passengers)}\n\n"

    if len(trips) > 100:
        md += f"\n*... and {len(trips) - 100} more trips*\n"

    return md

def create_unified_index(black_book: List[Dict], birthday_book: List[Dict],
                        flight_logs: List[Dict]) -> Dict:
    """Create unified entity index across all sources."""

    entities = {}

    # Process Black Book
    for entry in black_book:
        name = entry.get('name', '')
        if not name:
            continue

        if name not in entities:
            entities[name] = {
                "name": name,
                "sources": [],
                "contact_info": {},
                "flights": 0,
                "categories": [],
                "first_seen": None,
                "last_seen": None,
                "is_billionaire": False,
                "organizations": []
            }

        entities[name]["sources"].append("black_book")
        entities[name]["is_billionaire"] = entry.get('is_billionaire', False)

        if entry.get('associated_entity'):
            entities[name]["organizations"].append(entry['associated_entity'])

        if entry.get('in_flight_logs'):
            entities[name]["sources"].append("flight_logs_referenced")

    # Process Birthday Book
    for entry in birthday_book:
        name = entry.get('name', '')
        if not name:
            continue

        if name not in entities:
            entities[name] = {
                "name": name,
                "sources": [],
                "contact_info": {},
                "flights": 0,
                "categories": [],
                "first_seen": None,
                "last_seen": None,
                "is_billionaire": False,
                "organizations": []
            }

        entities[name]["sources"].append("birthday_book")

        if entry.get('contact_info'):
            entities[name]["contact_info"]["birthday_book"] = entry['contact_info']

    # Process Flight Logs
    passenger_trips = defaultdict(int)
    for trip in flight_logs:
        for passenger in trip.get('passengers', []):
            passenger_trips[passenger] += 1

    for passenger, count in passenger_trips.items():
        if passenger not in entities:
            entities[passenger] = {
                "name": passenger,
                "sources": [],
                "contact_info": {},
                "flights": 0,
                "categories": [],
                "first_seen": None,
                "last_seen": None,
                "is_billionaire": False,
                "organizations": []
            }

        entities[passenger]["sources"].append("flight_logs")
        entities[passenger]["flights"] = count

    # Convert to list and add statistics
    entity_list = list(entities.values())

    index = {
        "generated_date": datetime.now().isoformat(),
        "total_entities": len(entity_list),
        "sources": {
            "black_book": len(black_book),
            "birthday_book": len(birthday_book),
            "flight_logs": len(passenger_trips)
        },
        "entities": entity_list
    }

    return index

def main():
    print("Starting entity extraction...")

    # Extract Black Book
    print("\n1. Extracting Black Book CSV...")
    black_book_entities = extract_black_book_csv()
    print(f"   Found {len(black_book_entities)} entries")

    black_book_md = create_black_book_markdown(black_book_entities)
    (BASE_DIR / "black_book.md").write_text(black_book_md)
    print(f"   Saved to black_book.md")

    # Extract Birthday Book
    print("\n2. Extracting Birthday Book PDF...")
    birthday_book_entities = extract_birthday_book()
    print(f"   Found {len(birthday_book_entities)} entries")

    raw_text = extract_pdf_text(BIRTHDAY_BOOK_PDF)
    birthday_book_md = create_birthday_book_markdown(birthday_book_entities, raw_text)
    (BASE_DIR / "birthday_book.md").write_text(birthday_book_md)
    print(f"   Saved to birthday_book.md")

    # Extract Flight Logs
    print("\n3. Extracting Flight Logs PDF...")
    flight_log_trips = extract_flight_logs()
    print(f"   Found {len(flight_log_trips)} trips")

    flight_logs_md = create_flight_logs_markdown(flight_log_trips)
    (BASE_DIR / "flight_logs.md").write_text(flight_logs_md)
    print(f"   Saved to flight_logs.md")

    # Create unified index
    print("\n4. Creating unified entity index...")
    unified_index = create_unified_index(
        black_book_entities,
        birthday_book_entities,
        flight_log_trips
    )

    with open(BASE_DIR / "ENTITIES_INDEX.json", 'w') as f:
        json.dump(unified_index, f, indent=2)
    print(f"   Saved to ENTITIES_INDEX.json")
    print(f"   Total unique entities: {unified_index['total_entities']}")

    # Print statistics
    print("\n" + "="*60)
    print("EXTRACTION COMPLETE")
    print("="*60)
    print(f"\nBlack Book: {len(black_book_entities)} entries")
    print(f"Birthday Book: {len(birthday_book_entities)} entries")
    print(f"Flight Logs: {len(flight_log_trips)} trips")
    print(f"Unified Index: {unified_index['total_entities']} unique entities")

    # Overlap analysis
    sources_count = defaultdict(int)
    for entity in unified_index['entities']:
        source_key = tuple(sorted(set(entity['sources'])))
        sources_count[source_key] += 1

    print("\nSource Overlaps:")
    for sources, count in sorted(sources_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {' + '.join(sources)}: {count} entities")

if __name__ == "__main__":
    main()
