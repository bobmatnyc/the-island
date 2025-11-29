# Epstein Entity Extraction - Raw Entities

**Date**: November 16, 2025
**Location**: `/Users/masa/Projects/Epstein/data/sources/raw_entities/`

## Overview

This directory contains extracted entities from multiple Jeffrey Epstein-related sources, processed into structured markdown and JSON formats for further classification and indexing.

## Sources Processed

### 1. ✅ Black Book CSV
- **File**: `Jeffrey Epstein Billionaire Buddies - Black Book.csv`
- **Entries**: 1,740 total (1,501 persons)
- **Quality**: High - structured CSV with complete metadata
- **Output**: `black_book.md`

### 2. ✅ Birthday Book PDF
- **Source**: DocumentCloud (https://www.documentcloud.org/documents/26086657-epstein-birthday-book/)
- **Entries**: 161 contacts extracted
- **Quality**: Medium - OCR errors present, manual review needed
- **Output**: `birthday_book.md`, `birthday_book_raw.txt`

### 3. ✅ Flight Logs PDF (Unredacted)
- **File**: `EPSTEIN FLIGHT LOGS UNREDACTED.pdf`
- **Records**: 3,721 flight records
- **Passengers**: 358 unique passengers
- **Date Range**: 1/1/1996 to 9/9/2002
- **Quality**: High - structured table successfully parsed
- **Output**: `flight_logs.md`, `flight_logs_stats.json`

### 4. ⚠️ Little Black Book (Business Insider)
- **Status**: Identified as duplicate of Black Book CSV
- **Action**: Web scraping blocked; using CSV source instead
- **Output**: `little_black_book.md` (notes only)

## Generated Files

### Primary Outputs

| File | Description | Size | Format |
|------|-------------|------|--------|
| `ENTITIES_INDEX.json` | Unified entity index across all sources | 552 KB | JSON |
| `EXTRACTION_SUMMARY.md` | Human-readable extraction summary | 4.4 KB | Markdown |
| `black_book.md` | Black Book entities with metadata | 93 KB | Markdown |
| `flight_logs.md` | Flight log analysis and statistics | 16 KB | Markdown |
| `birthday_book.md` | Birthday Book contacts | 46 KB | Markdown |
| `flight_logs_stats.json` | Per-passenger flight statistics | 81 KB | JSON |

### Raw Data Files

| File | Description | Size |
|------|-------------|------|
| `birthday_book_raw.txt` | Raw OCR text from Birthday Book PDF | 194 KB |
| `flight_logs_raw.txt` | Raw text from Flight Logs PDF | 2.1 MB |
| `epstein-birthday-book.pdf` | Original Birthday Book PDF | 54 MB |

### Processing Scripts

| File | Purpose |
|------|---------|
| `extract_entities.py` | Initial extraction from all sources |
| `parse_flight_logs.py` | Improved flight log parser |
| `rebuild_index.py` | Unified index builder |

## Statistics

### Overall Numbers

- **Total Unique Entities**: 1,773
- **Billionaires Identified**: 33
- **In Black Book**: 1,501
- **In Flight Logs**: 273
- **In Both Sources**: 1
- **Total Flight Records**: 3,721

### Source Overlap

- **Black Book only**: 1,500 entities
- **Flight Logs only**: 272 entities
- **Both sources**: 1 entity

### Top Frequent Flyers

1. **Ghislaine Maxwell** - 520 trips
2. **Nadia Nadia** - 125 trips
3. **Sarah Kellen** - 305 trips (combined variations)
4. **Emmy Tayler** - 198 trips (combined variations)
5. **Virginia Roberts** - 28 trips

### Notable Passengers

- **Bill Clinton** - 11 trips
- **Kevin Spacey** - 11 trips
- **Chris Tucker** - 11 trips
- **Eva Dubin** - 33 trips (combined)
- **Glenn Dubin** - 13 trips

## Data Quality

### Black Book
- ✅ High quality, structured CSV data
- ✅ Complete with page numbers and categories
- ✅ Billionaire flags included
- ✅ Organization associations preserved

### Birthday Book
- ⚠️ OCR extraction has significant errors
- ⚠️ Names partially corrupted (e.g., "Ban Feren" instead of proper names)
- 📝 Requires manual cleanup
- ✅ Raw text preserved for review in `birthday_book_raw.txt`

### Flight Logs
- ✅ Structured table successfully parsed
- ✅ 3,721 flight records extracted
- ✅ Passenger names, dates, routes, tail numbers captured
- ⚠️ Name variations present (e.g., "Je Epstein" appears as multiple variants)
- 📝 Name normalization recommended

## Data Schema

### ENTITIES_INDEX.json Structure

```json
{
  "generated_date": "ISO timestamp",
  "total_entities": 1773,
  "statistics": {
    "total_persons": 1773,
    "billionaires": 33,
    "in_black_book": 1501,
    "in_flight_logs": 273,
    "in_both_sources": 1,
    "total_flight_records": 3721
  },
  "entities": [
    {
      "name": "Full Name",
      "normalized_name": "Normalized Name",
      "sources": ["black_book", "flight_logs"],
      "contact_info": {},
      "flights": 0,
      "is_billionaire": false,
      "organizations": [],
      "black_book_page": "",
      "categories": [],
      "first_flight": "date",
      "last_flight": "date",
      "routes": []
    }
  ]
}
```

### Markdown Frontmatter Format

Each markdown file includes YAML frontmatter:

```yaml
---
source_type: "contact_book|flight_log|birthday_book"
source_name: "Source Name"
source_url: "https://..."
download_date: "2025-11-16"
total_entries: 1740
extraction_method: "csv_parse|pdf_extraction|structured_table_parse"
---
```

## Usage Examples

### Load Unified Index

```python
import json

with open('ENTITIES_INDEX.json', 'r') as f:
    index = json.load(f)

# Find all billionaires
billionaires = [e for e in index['entities'] if e['is_billionaire']]
print(f"Found {len(billionaires)} billionaires")

# Find frequent flyers (>10 trips)
frequent_flyers = [e for e in index['entities'] if e.get('flights', 0) > 10]
print(f"Found {len(frequent_flyers)} frequent flyers")

# Find entities in both sources
in_both = [e for e in index['entities'] if len(set(e['sources'])) > 1]
print(f"Found {len(in_both)} entities in multiple sources")
```

### Load Flight Statistics

```python
import json

with open('flight_logs_stats.json', 'r') as f:
    stats = json.load(f)

# Analyze passenger patterns
for passenger, data in stats['passengers'].items():
    if data['trips'] > 20:
        print(f"{passenger}: {data['trips']} trips")
        print(f"  Routes: {len(data['routes'])}")
        print(f"  Period: {data['first_flight']} to {data['last_flight']}")
```

## Known Issues

1. **Name Variations in Flight Logs**
   - Jeffrey Epstein appears as multiple variants
   - Name normalization needed for accurate counting
   - Recommend fuzzy matching for consolidation

2. **Birthday Book OCR Errors**
   - Many names corrupted by OCR
   - Manual review required for accuracy
   - Consider re-extraction with better OCR tool

3. **Missing Cross-References**
   - Only 1 entity matched across Black Book and Flight Logs
   - Name matching algorithm too strict
   - Recommend fuzzy matching implementation

4. **Anonymous Passengers**
   - Flight logs contain "Female (1)", "Male (1)", etc.
   - Cannot be cross-referenced
   - Represent unidentified passengers

## Recommended Next Steps

1. **Name Normalization**
   - Consolidate name variations (e.g., "Je Epstein" variants)
   - Implement fuzzy matching for cross-referencing
   - Create name mapping table

2. **Birthday Book Manual Review**
   - Review `birthday_book_raw.txt`
   - Correct OCR errors
   - Re-extract with manual verification

3. **Entity Classification**
   - Tag entities by role: associate, employee, victim, etc.
   - Add relationship types
   - Create entity categories

4. **Network Analysis**
   - Build co-occurrence graph from flight logs
   - Identify clusters and frequent travelers together
   - Map relationship networks

5. **Timeline Construction**
   - Create chronological timeline from flight dates
   - Map entity interactions over time
   - Identify key periods of activity

6. **Enhanced Cross-Referencing**
   - Implement fuzzy name matching
   - Cross-reference with public records
   - Add additional metadata sources

## File Locations

All files are in: `/Users/masa/Projects/Epstein/data/sources/raw_entities/`

## Metadata

- **Extraction Date**: 2025-11-16
- **Extractor**: Automated Python scripts with manual verification
- **Sources**: DocumentCloud, court documents, public records
- **Purpose**: Research and documentation

## License & Ethics

This data is extracted from public court documents and publicly available sources for research and documentation purposes. All sources are properly attributed.

## Contact

For questions about this extraction or to report issues with the data, please refer to the main project documentation.

---

*Last updated: 2025-11-16 21:21*
