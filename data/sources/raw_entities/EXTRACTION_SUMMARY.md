# Epstein Entity Extraction Summary

**Generated**: 2025-11-16 21:21:17

## Overview

This report summarizes entities extracted from multiple Jeffrey Epstein-related sources.

## Sources Processed

1. ✅ **Black Book CSV** - 1,740 entries
2. ✅ **Birthday Book PDF** - 161 entries (raw extraction)
3. ✅ **Flight Logs PDF** - 3,721 flight records
4. ⚠️ **Little Black Book (Business Insider)** - Duplicate of Black Book CSV

## Statistics

- **Total Unique Entities**: 1,773
- **Billionaires Identified**: 33
- **In Black Book**: 1,501
- **In Flight Logs**: 273
- **In Both Sources**: 1
- **Total Flight Records**: 3,721

## Source Overlaps

- **black_book**: 1,500 entities
- **flight_logs**: 272 entities
- **black_book + flight_logs**: 1 entities

## Top 20 Frequent Flyers

| Rank | Name | Trips | In Black Book | Billionaire |
|------|------|-------|---------------|-------------|
| 1 | Ghislaine Ghislaine | 520 |  |  |
| 2 | Nadia Nadia | 125 |  |  |
| 3 | Female (1) | 62 |  |  |
| 4 | Didier | 32 |  |  |
| 5 | Female (2) | 30 |  |  |
| 6 | Luc Brunel | 30 |  |  |
| 7 | Virginia   Virginia Roberts | 28 |  |  |
| 8 | Male (1) | 25 |  |  |
| 9 | Teala       Teala Davies | 23 |  |  |
| 10 | Gramza | 20 |  |  |
| 11 | Celina   Celina Midelfart | 18 |  |  |
| 12 | Lang | 18 |  |  |
| 13 | Eva         Eva Dubin | 15 |  |  |
| 14 | Celina      Celina Dubin | 15 |  |  |
| 15 | Nanny (1) | 14 |  |  |
| 16 | Doug           Doug Band | 13 |  |  |
| 17 | Pete      Pete Rathgeb | 12 |  |  |
| 18 | Adriana Adriana Mucinska | 12 |  |  |
| 19 | Sophie     Sophie Biddle | 11 |  |  |
| 20 | Bill        Bill Clinton | 11 |  |  |

## Billionaires in Flight Logs

*No billionaires found in flight logs with current matching.*


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
