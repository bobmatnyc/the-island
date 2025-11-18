# Searching Documents - User Guide

**Advanced search techniques for the Epstein Document Archive**

**Last Updated**: November 17, 2025

---

## Overview

This guide covers all search methods available in the Epstein Document Archive, from basic entity search to advanced multi-entity queries and network analysis.

---

## Search Methods

### 1. Web Interface Search

Access at `http://localhost:8081/`

**Entities Tab**:
- Search by name
- Filter by type
- Sort by connections
- View details and relationships

**Documents Tab**:
- Full-text search (for OCR'd documents)
- Filter by document type
- Filter by date range
- Filter by source

**Flights Tab**:
- Search by passenger name
- Filter by date range
- Browse chronologically

**Network Tab**:
- Visual search
- Interactive exploration
- Connection highlighting

### 2. Command Line Search

**Entity Search Tool**: `scripts/search/entity_search.py`

```bash
# Basic entity search
python3 scripts/search/entity_search.py --entity "NAME"

# View connections
python3 scripts/search/entity_search.py --connections "NAME"

# Multi-entity search
python3 scripts/search/entity_search.py --multiple "NAME1" "NAME2" "NAME3"

# Search by document type
python3 scripts/search/entity_search.py --type "email"
```

### 3. Direct Data Query

**Using jq** (JSON query tool):

```bash
# Find entity by name
cat data/md/entities/ENTITIES_INDEX.json | jq '.[] | select(.name == "Clinton")'

# Find flights with passenger
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.passengers | contains(["Clinton"]))'

# Count documents by type
cat data/metadata/document_classifications.json | jq 'group_by(.primary_classification) | map({type: .[0].primary_classification, count: length})'
```

---

## Entity Search

### Basic Entity Search

**Find single entity**:
```bash
python3 scripts/search/entity_search.py --entity "Clinton"
```

**Output**:
```
Found 1 entity matching "Clinton":

Name: Bill Clinton
Type: Person
Connections: 26
Documents: 4
Bio: 42nd President of the United States...

Documents mentioning this entity:
- flight_logs.md (3 mentions)
- black_book.md (1 mention)
```

### Entity Name Variations

The system handles name variations automatically:

**Examples**:
- "Clinton" → matches "Bill Clinton", "Clinton, Bill"
- "Maxwell" → matches "Ghislaine Maxwell", "G. Maxwell"
- "Epstein" → matches "Jeffrey Epstein", "Je Epstein"

**Tip**: Start with last name only for broadest results.

### Entity Type Filtering

**Search by type**:
```bash
# Web interface: Use type filter dropdown
# Command line: Filter results manually
cat data/md/entities/ENTITIES_INDEX.json | jq '.[] | select(.type == "Person")'
```

**Entity Types**:
- Person
- Organization
- Location

---

## Connection Search

### Find Entity Connections

**View all connections**:
```bash
python3 scripts/search/entity_search.py --connections "Ghislaine Maxwell"
```

**Output**:
```
Ghislaine Maxwell has 190 connections:

Top connections by strength:
1. Je Epstein (228 flights together)
2. Sarah Kellen (76 flights together)
3. Nadia Marcinkova (52 flights together)
...
```

### Connection Strength

**Interpretation**:
- **1-5 connections**: Minimal relationship
- **6-20 connections**: Moderate relationship
- **20+ connections**: Strong relationship
- **50+ connections**: Very strong relationship
- **100+ connections**: Core network member

**Source**:
- Flight co-occurrence (most connections)
- Document co-mentions
- Explicit relationships

### Finding Shared Connections

**Multi-entity search**:
```bash
python3 scripts/search/entity_search.py --multiple "Clinton" "Trump" "Epstein"
```

**Output**:
```
Documents mentioning ALL of: Clinton, Trump, Epstein:
- flight_logs.md
- black_book.md

Shared connections:
- All three appear in flight logs
- All three in contact book
```

---

## Document Search

### Search by Document Type

**Available Types**:
1. email
2. court_filing
3. financial
4. flight_log
5. contact_book
6. investigative
7. legal_agreement
8. personal
9. media
10. administrative
11. unknown

**Command Line**:
```bash
python3 scripts/search/entity_search.py --type "email"
```

**Web Interface**:
1. Go to Documents tab
2. Select type from dropdown
3. Browse results

### Full-Text Search

**Note**: Only available for OCR'd documents (currently 45% complete)

**Web Interface**:
1. Go to Documents tab
2. Enter search terms
3. Results show matching documents with highlights

**Coming Soon**: Full-text search API and command line tool

### Search by Source

**View documents by source**:
```bash
# List all sources
cat data/metadata/source_index.json | jq 'keys'

# View documents from specific source
cat data/metadata/source_index.json | jq '.house_oversight_nov2025'
```

**Major Sources**:
- house_oversight_nov2025 (67,144 PDFs)
- giuffre_maxwell (court documents)
- entities (contact books, flight logs)

### Search by Date Range

**Web Interface**:
1. Go to Documents or Flights tab
2. Use date range picker
3. Apply filters

**Data Query**:
```bash
# Flights in specific year
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.date | startswith("2001"))'
```

---

## Flight Search

### Find Flights by Passenger

**Web Interface**:
1. Go to Flights tab
2. Enter passenger name in filter
3. Browse matching flights

**Command Line**:
```bash
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.passengers | contains(["Clinton"]))'
```

### Find Flights by Date

**Date range**:
```bash
# Flights in specific month
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.date | startswith("2001-05"))'

# Flights in date range
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.date >= "2001-01-01" and .date <= "2001-12-31")'
```

### Find Co-Passengers

**Who flew together?**:
```bash
# Find flights with both passengers
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.passengers | contains(["Clinton"]) and contains(["Epstein"]))'
```

### Flight Statistics

**Per passenger**:
```bash
# Count flights per passenger
cat data/md/entities/flight_logs_by_flight.json | jq '[.[].passengers[]] | group_by(.) | map({name: .[0], count: length}) | sort_by(.count) | reverse'
```

---

## Network Search

### Visual Network Exploration

**Web Interface**:
1. Go to Network tab
2. Graph loads with all entities
3. Use search to highlight specific entities
4. Click nodes to see details
5. Zoom/pan to explore

**Features**:
- **Node size**: Scaled by connection count
- **Edge thickness**: Scaled by relationship strength
- **Colors**: Entity types
- **Tooltips**: Entity details on hover

### Filter Network by Connection Count

**Web Interface**:
1. Use "Min Connections" slider
2. Graph updates to show only highly-connected entities

**Threshold Guidelines**:
- **50+ connections**: Core network (top 10%)
- **20+ connections**: Inner circle (top 25%)
- **10+ connections**: Regular contacts (top 50%)
- **1+ connections**: All entities

### Path Finding

**Find connection path between entities**:

**Web Interface**:
1. Click first entity (becomes highlighted)
2. Click second entity
3. Shortest path highlights

**Manual Query**:
```bash
# Find all intermediaries
cat data/metadata/entity_network.json | jq '.edges | map(select(.source == "Clinton" or .target == "Clinton"))'
```

---

## Advanced Search Techniques

### 1. Combining Multiple Filters

**Example**: Find all emails mentioning Clinton from 2001

**Steps**:
1. Search entity: "Clinton"
2. Filter documents by type: "email"
3. Filter by date: 2001
4. View results

### 2. Exclusion Search

**Example**: Find Epstein connections excluding Maxwell

**Command Line**:
```bash
python3 scripts/search/entity_search.py --connections "Epstein" | grep -v "Maxwell"
```

### 3. Pattern Matching

**Example**: Find all entities with "LLC" in name (organizations)

**Query**:
```bash
cat data/md/entities/ENTITIES_INDEX.json | jq '.[] | select(.name | contains("LLC"))'
```

### 4. Aggregate Analysis

**Example**: Count documents per entity

**Query**:
```bash
cat data/metadata/semantic_index.json | jq 'to_entries | map({entity: .key, doc_count: (.value | length)}) | sort_by(.doc_count) | reverse | .[0:10]'
```

### 5. Time-Based Analysis

**Example**: Network evolution over time

**Query**:
```bash
# Flights per year
cat data/md/entities/flight_logs_by_flight.json | jq 'group_by(.date[0:4]) | map({year: .[0].date[0:4], count: length})'
```

---

## Search Tips and Best Practices

### Effective Search Strategies

1. **Start broad, then narrow**
   - Begin with entity name only
   - Add filters incrementally
   - Review each result set

2. **Use multiple perspectives**
   - Entity search for biographical context
   - Connection search for relationships
   - Document search for evidence
   - Network search for patterns

3. **Verify and cross-reference**
   - Check multiple sources
   - Look for corroboration
   - Note document dates
   - Review source provenance

4. **Understand data limitations**
   - OCR incomplete (45% done)
   - Some documents redacted
   - Name variations exist
   - Date formats vary

### Common Search Patterns

**Pattern 1: Entity Investigation**
```
1. Search entity name
2. Review biographical info
3. Check document mentions
4. Explore connections
5. Visualize in network graph
```

**Pattern 2: Relationship Investigation**
```
1. Search both entities
2. Find shared documents
3. Check flight co-occurrence
4. Review timeline
5. Identify intermediaries
```

**Pattern 3: Document Investigation**
```
1. Search by document type
2. Filter by date range
3. Filter by entities mentioned
4. Review source provenance
5. Cross-reference with other docs
```

---

## Search Examples

### Example 1: Basic Entity Search

**Question**: What do we know about Prince Andrew?

**Steps**:
```bash
# Search entity
python3 scripts/search/entity_search.py --entity "Prince Andrew"

# View connections
python3 scripts/search/entity_search.py --connections "Prince Andrew"

# Find in network
# (Use web interface Network tab, search "Prince Andrew")
```

### Example 2: Connection Investigation

**Question**: How are Clinton and Epstein connected?

**Steps**:
```bash
# Multi-entity search
python3 scripts/search/entity_search.py --multiple "Clinton" "Epstein"

# Find shared flights
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.passengers | contains(["Clinton"]) and contains(["Epstein"]))'
```

### Example 3: Timeline Analysis

**Question**: What happened in 2002?

**Steps**:
```bash
# Find flights
cat data/md/entities/flight_logs_by_flight.json | jq '.[] | select(.date | startswith("2002"))'

# Find documents (when classification complete)
# Web interface: Documents tab, date filter 2002
```

### Example 4: Organization Search

**Question**: Which organizations are in the contact book?

**Steps**:
```bash
# Find organizations
cat data/md/entities/ENTITIES_INDEX.json | jq '.[] | select(.type == "Organization") | .name'
```

---

## Troubleshooting Search Issues

### "No results found"

**Possible causes**:
1. **Spelling error**: Check entity name spelling
2. **Name variation**: Try alternative names (e.g., "Bill Clinton" vs "Clinton")
3. **Not in database**: Entity may not be in indexed documents
4. **OCR pending**: Document may not be processed yet

**Solutions**:
- Try partial name match
- Search related entities
- Check entity index directly
- Wait for OCR completion (if recent documents)

### "Too many results"

**Solutions**:
1. Add more specific filters
2. Use document type filter
3. Add date range filter
4. Search multiple entities together

### "Results seem incomplete"

**Possible causes**:
1. OCR in progress (45% complete)
2. Classification incomplete
3. Redacted documents
4. Data quality issues

**Check**:
- OCR status: `python3 scripts/extraction/check_ocr_status.py`
- Source document quality
- Document redactions

---

## Next Steps

### Learn More

- **Entity Guide**: [entities.md](entities.md) - Entity database details
- **Flight Guide**: [flights.md](flights.md) - Flight log analysis
- **Network Guide**: [network-analysis.md](network-analysis.md) - Network visualization
- **FAQ**: [faq.md](faq.md) - Common questions

### Advanced Topics

- [../developer/api/](../developer/api/) - API documentation for programmatic access
- [../content/classification.md](../content/classification.md) - Document classification system
- [../content/entity-extraction.md](../content/entity-extraction.md) - How entities are identified

---

**Need help?** Check the [FAQ](faq.md) or [open an issue](https://github.com/yourusername/epstein-document-archive/issues)
