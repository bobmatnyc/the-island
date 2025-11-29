# Entity System - Complete Documentation

**Quick Summary**: The Entity System is a comprehensive person and organization tracking system that consolidates data from multiple sources (Black Book, Flight Logs) with intelligent name normalization, disambiguation, and network visualization. .

**Category**: Documentation
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **Duplicate Entities?** → NO - All duplicates removed 2025-11-17
- **Aliases System?** → YES - `entity_name_mappings.json` (772 mappings)
- **Current Entity Count**: 1,639 unique entities
- **Jeffrey Epstein Aliases**: 7 OCR variations → all resolved to "Jeffrey Epstein"
- `"Je           Je Epstein"` (multiple spaces)

---

## Overview

The Entity System is a comprehensive person and organization tracking system that consolidates data from multiple sources (Black Book, Flight Logs) with intelligent name normalization, disambiguation, and network visualization.

**Total Entities**: 1,639 unique entities
**Status**: ✅ Production Ready (Duplicates removed 2025-11-17)
**Entity ID Scheme**: Name-based (no UUIDs)

## Quick Reference

### TL;DR

- **Duplicate Entities?** → NO - All duplicates removed 2025-11-17
- **Aliases System?** → YES - `entity_name_mappings.json` (772 mappings)
- **Current Entity Count**: 1,639 unique entities
- **Jeffrey Epstein Aliases**: 7 OCR variations → all resolved to "Jeffrey Epstein"

### Key Stats

| Metric | Count |
|--------|-------|
| Total entities | 1,639 |
| Jeffrey Epstein entities | 1 (canonical) |
| Jeffrey Epstein aliases | 7 mapped variations |
| Duplicate entities | 0 ✅ |
| Name mappings | 772 |
| Network graph nodes | 284 |
| Entities with bios | 21 |
| Entities with tags | 70 |

## Architecture

### Data Files

| File | Count | Purpose |
|------|-------|---------|
| `ENTITIES_INDEX.json` | 1,639 | Master entity list (Black Book + Flight Logs) |
| `entity_network.json` | 284 nodes | Network visualization graph |
| `entity_name_mappings.json` | 772 | OCR fixes and name variations |
| `entity_tags.json` | 70 | Role/category tags |
| `entity_biographies.json` | 21 | Biographical data |
| `semantic_index.json` | 2,667 | Entity-to-document links |
| `timeline.json` | 98 events | Timeline with entity references |

### Entity ID Schemes

**Name-Based IDs (Primary)**:
```
"Jeffrey Epstein"           ← Used everywhere
"Epstein, Jeffrey"          ← ENTITIES_INDEX format only
```

**No UUIDs or numeric IDs are used in this system.**

### Data Flow

```
Source Documents (PDF/Images)
    ↓ OCR extraction
Raw Entity Names (with artifacts)
    ↓ entity_name_mappings.json
Normalized Names
    ↓ EntityDisambiguation service
Canonical Entity Names
    ↓ Used in
[ENTITIES_INDEX.json, entity_network.json, flight_logs.json, timeline.json]
```

## Features

### 1. Name Normalization & Disambiguation

**Problem**: OCR artifacts create name variations
- `"Je           Je Epstein"` (multiple spaces)
- `"Glenn       Glenn Dubin"` (duplicate names)
- `"J. Epstein"` vs `"Jeffrey Epstein"` (abbreviations)

**Solution**: Automatic disambiguation via `EntityDisambiguation` service

**Example Usage**:
```python
from services.entity_disambiguation import EntityDisambiguation

disambiguator = EntityDisambiguation()
canonical = disambiguator.normalize_name("Je Je Epstein")
# Returns: "Jeffrey Epstein"
```

**API Integration**:
```
User request:  GET /api/entities/Je%20Je%20Epstein
API resolves:  "Je Je Epstein" → "Jeffrey Epstein"
API returns:   Canonical entity data
```

**Jeffrey Epstein Aliases** (all automatically resolved):
```
"Je           Je Epstein" → "Jeffrey Epstein"
"Je          Je Epstein" → "Jeffrey Epstein"
"Je         Je Epstein" → "Jeffrey Epstein"
"Je        Je Epstein" → "Jeffrey Epstein"
"Je       Je Epstein" → "Jeffrey Epstein"
"Je Je Epstein" → "Jeffrey Epstein"
"Je Je" → "Jeffrey Epstein" (via code)
```

### 2. Multi-Source Integration

**Data Sources**:
1. **Black Book** (Address book with 1,571 contacts)
   - Contact information
   - Phone numbers
   - Addresses
   - Notes

2. **Flight Logs** (922 flights with passenger data)
   - Flight dates
   - Origins and destinations
   - Passenger lists
   - Flight IDs

**Entity Fields**:
```json
{
  "name": "Jeffrey Epstein",
  "sources": ["black_book", "flight_logs"],
  "flights": 8,
  "network_connections": 262,
  "black_book_pages": "64, 67, 71, 72, 82, 85",
  "tags": ["Financier", "Associate"],
  "biography": "Full biography text..."
}
```

### 3. Network Visualization

**Network Graph Structure**:
```json
{
  "nodes": [
    {
      "id": "Jeffrey Epstein",
      "name": "Jeffrey Epstein",
      "connection_count": 262,
      "tags": ["Financier", "Associate"],
      "bio_available": true
    }
  ],
  "edges": [
    {
      "source": "Jeffrey Epstein",
      "target": "Ghislaine Maxwell",
      "type": "flight",
      "weight": 15
    }
  ]
}
```

**Node Properties**:
- `id`: Canonical entity name
- `connection_count`: Number of connections
- `tags`: Category labels
- `bio_available`: Biography exists

**Edge Properties**:
- `source`: Origin entity
- `target`: Destination entity
- `type`: Connection type (flight, contact, etc.)
- `weight`: Connection strength (number of occurrences)

### 4. Entity Cards with Navigation

**Features**:
- Click entity card → View entity details
- Entity card shows: name, tags, bio excerpt
- Navigate to entity connections
- View flight history
- See timeline events

**Implementation**:
```javascript
// Entity card click handler
function handleEntityCardClick(entityName) {
    // Normalize name
    const canonical = normalizeEntityName(entityName);

    // Load entity data
    fetch(`/api/entities/${encodeURIComponent(canonical)}`)
        .then(response => response.json())
        .then(entity => {
            displayEntityDetails(entity);
        });
}
```

### 5. Entity Filtering

**Filter Types**:
1. **By Source**: Black Book, Flight Logs, Both
2. **By Tag**: Financier, Associate, Political, etc.
3. **By Connection Count**: Minimum connections threshold
4. **By Text Search**: Name search with fuzzy matching

**Combined Filtering**:
```javascript
// Example: Politicians with >10 connections from Black Book
filters = {
    source: 'black_book',
    tags: ['Political'],
    min_connections: 10
}
```

**Filter UI**:
- Source dropdown (All / Black Book / Flight Logs)
- Tag multiselect
- Connection slider
- Search bar with autocomplete

### 6. Entity Tags & Categories

**Tag System**:
```json
{
  "entities": {
    "Jeffrey Epstein": {
      "tags": ["Financier", "Associate"],
      "description": "Primary subject"
    },
    "Bill Clinton": {
      "tags": ["Political", "Former President"],
      "description": "Flight log passenger"
    }
  }
}
```

**Tag Categories**:
- **Professional**: Financier, Lawyer, Scientist, etc.
- **Political**: Political, Former President, Government Official
- **Social**: Associate, Friend, Family Member
- **Location**: New York, Florida, Caribbean
- **Custom**: User-defined tags

**Tag Operations**:
- Add tag: `POST /api/entities/{name}/tags`
- Remove tag: `DELETE /api/entities/{name}/tags/{tag}`
- List tags: `GET /api/entity-tags`
- Filter by tag: `GET /api/entities?tag=Political`

### 7. Entity Biographies

**Biography Structure**:
```json
{
  "entities": {
    "Jeffrey Epstein": {
      "full_name": "Jeffrey Edward Epstein",
      "born": "1953-01-20",
      "died": "2019-08-10",
      "occupation": "Financier",
      "known_for": "...",
      "biography": "Full biographical text...",
      "sources": ["Wikipedia", "Court Documents"],
      "last_updated": "2025-11-18"
    }
  }
}
```

**Biography Features**:
- Full biographical text
- Birth/death dates
- Occupation and roles
- Known associations
- Source attribution
- Last updated timestamp

**API Endpoints**:
- Get all bios: `GET /api/entity-biographies`
- Get single bio: `GET /api/entities/{name}/biography`
- Update bio: `POST /api/entities/{name}/biography`

## Implementation Details

### Entity Service (`server/services/entity_service.py`)

**Core Functions**:

```python
class EntityService:
    def get_all_entities(self, filters=None):
        """Get all entities with optional filtering"""
        pass

    def get_entity(self, name):
        """Get single entity by name (auto-disambiguates)"""
        pass

    def get_entity_connections(self, name):
        """Get entity network connections"""
        pass

    def search_entities(self, query):
        """Search entities by text query"""
        pass

    def enrich_entity(self, name, data):
        """Add tags, bio, etc. to entity"""
        pass
```

**Disambiguation Integration**:
```python
from services.entity_disambiguation import EntityDisambiguation

class EntityService:
    def __init__(self):
        self.disambiguator = EntityDisambiguation()

    def get_entity(self, name):
        canonical = self.disambiguator.normalize_name(name)
        return self._load_entity_data(canonical)
```

### Entity Disambiguation (`server/services/entity_disambiguation.py`)

**Normalization Pipeline**:

```python
class EntityDisambiguation:
    def normalize_name(self, name):
        """
        1. Load name mappings
        2. Check exact match
        3. Check fuzzy match
        4. Apply OCR fixes
        5. Return canonical name
        """
        # Check mappings
        if name in self.mappings:
            return self.mappings[name]

        # Check fuzzy match
        canonical = self._fuzzy_match(name)
        if canonical:
            return canonical

        # Return as-is if no match
        return name

    def _fuzzy_match(self, name):
        """Use difflib for similarity matching"""
        from difflib import get_close_matches
        matches = get_close_matches(name, self.canonical_names, n=1, cutoff=0.85)
        return matches[0] if matches else None
```

### API Routes (`server/api_routes.py`)

**Entity Endpoints**:

```python
@app.route('/api/entities', methods=['GET'])
def list_entities():
    """List entities with optional filters"""
    filters = {
        'source': request.args.get('source'),
        'tag': request.args.get('tag'),
        'search': request.args.get('search'),
        'min_connections': request.args.get('min_connections', type=int)
    }
    entities = entity_service.get_all_entities(filters)
    return jsonify(entities)

@app.route('/api/entities/<name>', methods=['GET'])
def get_entity(name):
    """Get single entity (auto-disambiguates)"""
    entity = entity_service.get_entity(name)
    if not entity:
        return jsonify({'error': 'Entity not found'}), 404
    return jsonify(entity)

@app.route('/api/entities/<name>/connections', methods=['GET'])
def get_entity_connections(name):
    """Get entity network connections"""
    connections = entity_service.get_entity_connections(name)
    return jsonify(connections)
```

## Data Quality & Cleanup

### Historical Cleanup (2025-11-17)

**Problem**: OCR artifacts created duplicate entities
- `"Glenn       Glenn Dubin"` (excessive whitespace)
- `"Je Je Epstein"` (repeated name parts)
- Name variations across sources

**Solution**: Two-pass cleanup script
1. **Pass 1**: Fixed 238 OCR artifacts in entity keys
2. **Pass 2**: Cleaned 1,188 nested entity references
3. **Backup**: Created backups in `data/backups/`

**Result**: Zero duplicates remaining ✅

**Cleanup Script** (`scripts/analysis/final_entity_cleanup.py`):
```python
def clean_entity_name(name):
    """Remove OCR artifacts from entity names"""
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', name)

    # Remove duplicate name parts
    parts = cleaned.split()
    if len(parts) >= 2 and parts[0] == parts[1]:
        cleaned = ' '.join(parts[1:])

    return cleaned.strip()
```

### Entity Validation

**Validation Checks**:
1. No duplicate entity IDs in network graph
2. All entity references resolve to canonical names
3. No orphaned entities (in network but not in index)
4. All tags are valid
5. All biographies reference existing entities

**Validation Script** (`scripts/data_quality/verify_normalization.py`):
```bash
python3 scripts/data_quality/verify_normalization.py
```

**Expected Output**:
```
✅ No duplicate entities found
✅ All entity references valid
✅ Network graph consistent
✅ Tags validated
✅ Biographies validated
Total entities: 1,639
Entities with bios: 21
Entities with tags: 70
```

### Entity Mapping Management

**When to Add Mappings**:
- OCR artifacts discovered
- Alternate spellings found
- Name variations in documents
- Typos in source data

**Example Mapping**:
```json
{
  "Jeffrey E. Epstein": "Jeffrey Epstein",
  "J. Epstein": "Jeffrey Epstein",
  "Epstein, J.": "Jeffrey Epstein"
}
```

**Rebuild Mappings**:
```bash
python3 scripts/utils/build_entity_mappings.py
```

**Mapping File Format** (`data/metadata/entity_name_mappings.json`):
```json
{
  "variations": {
    "Je Je Epstein": "Jeffrey Epstein",
    "Je           Je Epstein": "Jeffrey Epstein",
    "Glenn       Glenn Dubin": "Glenn Dubin"
  },
  "metadata": {
    "total_mappings": 772,
    "last_updated": "2025-11-17",
    "ocr_fixes": 238
  }
}
```

## Common Operations

### Find Entity in Network

```javascript
// JavaScript (frontend)
const node = networkData.nodes.find(n => n.id === "Jeffrey Epstein");
console.log(node.connection_count); // 262
```

```python
# Python (backend)
with open('data/metadata/entity_network.json') as f:
    network = json.load(f)
    node = next(n for n in network['nodes'] if n['id'] == 'Jeffrey Epstein')
    print(node['connection_count'])  # 262
```

### Get Entity Connections

```bash
# API request
curl -u user:pass 'http://localhost:8000/api/entities/Jeffrey%20Epstein/connections'
```

```javascript
// JavaScript
fetch('/api/entities/Jeffrey%20Epstein/connections')
    .then(r => r.json())
    .then(connections => {
        console.log(`${connections.length} connections`);
    });
```

### Search Entities

```bash
# API request
curl -u user:pass 'http://localhost:8000/api/entities?search=Epstein'
```

```javascript
// JavaScript with filters
fetch('/api/entities?search=Clinton&tag=Political&min_connections=5')
    .then(r => r.json())
    .then(entities => {
        console.log(entities);
    });
```

### Get Entity Biography

```python
# Python
import json

with open('data/metadata/entity_biographies.json') as f:
    bios = json.load(f)
    epstein_bio = bios['entities']['Jeffrey Epstein']
    print(epstein_bio['biography'])
```

```javascript
// JavaScript
fetch('/api/entities/Jeffrey%20Epstein/biography')
    .then(r => r.json())
    .then(bio => {
        console.log(bio.full_name);
        console.log(bio.biography);
    });
```

### Check for Duplicates

```python
# Python
from collections import Counter
import json

with open('data/metadata/entity_network.json') as f:
    network = json.load(f)

node_ids = [n['id'] for n in network['nodes']]
duplicates = {id: count for id, count in Counter(node_ids).items() if count > 1}

if duplicates:
    print("Duplicates found:", duplicates)
else:
    print("✅ No duplicates")
```

## API Reference

### Entity Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/entities` | GET | List entities with filters |
| `/api/entities/{name}` | GET | Get single entity (auto-disambiguates) |
| `/api/entities/{name}/connections` | GET | Get entity network connections |
| `/api/entities/{name}/biography` | GET | Get entity biography |
| `/api/entities/{name}/tags` | GET | Get entity tags |
| `/api/entities/{name}/tags` | POST | Add tag to entity |
| `/api/entities/{name}/tags/{tag}` | DELETE | Remove tag from entity |
| `/api/entity-biographies` | GET | Get all biographies |
| `/api/entity-tags` | GET | Get all tags |
| `/api/entities/enrich/batch` | POST | Enrich multiple entities |

### Query Parameters

**`GET /api/entities`**:
- `source`: Filter by source (`black_book`, `flight_logs`, `both`)
- `tag`: Filter by tag (comma-separated for multiple)
- `search`: Text search query
- `min_connections`: Minimum connection count
- `limit`: Results limit (default: 100)
- `offset`: Results offset (for pagination)

**Example Queries**:
```bash
# All entities from Black Book
GET /api/entities?source=black_book

# Political entities with >10 connections
GET /api/entities?tag=Political&min_connections=10

# Search for "Clinton"
GET /api/entities?search=Clinton

# Combine filters
GET /api/entities?source=flight_logs&tag=Political&search=Clinton&min_connections=5
```

### Response Formats

**Entity List Response**:
```json
{
  "entities": [
    {
      "name": "Jeffrey Epstein",
      "sources": ["black_book", "flight_logs"],
      "flights": 8,
      "connections": 262,
      "tags": ["Financier", "Associate"],
      "bio_available": true
    }
  ],
  "total": 1639,
  "limit": 100,
  "offset": 0
}
```

**Single Entity Response**:
```json
{
  "name": "Jeffrey Epstein",
  "canonical_name": "Jeffrey Epstein",
  "aliases": ["Je Je Epstein", "Je Je"],
  "sources": ["black_book", "flight_logs"],
  "flights": 8,
  "connections": 262,
  "black_book_pages": "64, 67, 71, 72, 82, 85",
  "tags": ["Financier", "Associate"],
  "biography": {
    "full_name": "Jeffrey Edward Epstein",
    "born": "1953-01-20",
    "died": "2019-08-10",
    "occupation": "Financier",
    "biography": "Full text..."
  }
}
```

## Troubleshooting

### "Entity not found"

**Symptoms**:
- API returns 404
- Entity doesn't appear in search

**Solutions**:
1. Check name capitalization: `"Jeffrey Epstein"` not `"jeffrey epstein"`
2. Try normalized form: `"Jeffrey Epstein"` not `"Epstein, Jeffrey"`
3. Check `entity_name_mappings.json` for variations
4. Use API endpoint (handles disambiguation automatically)

**Debug**:
```python
from services.entity_disambiguation import EntityDisambiguation

disambiguator = EntityDisambiguation()
canonical = disambiguator.normalize_name("your input name")
print(f"Normalized to: {canonical}")
```

### "Duplicate entity detected"

**Symptoms**:
- Same entity appears twice in network graph
- Duplicate IDs in validation script

**Solutions**:
1. Run validation: `python3 scripts/data_quality/verify_normalization.py`
2. Add mapping to `entity_name_mappings.json`
3. Rebuild mappings: `python3 scripts/utils/build_entity_mappings.py`
4. Report to data quality team

**This should not happen** - all duplicates cleaned 2025-11-17.

### "Name variation not resolved"

**Symptoms**:
- OCR artifact not mapped to canonical name
- API doesn't recognize alias

**Solutions**:
1. Add to `entity_name_mappings.json`:
   ```json
   {
     "Je Je Epstein": "Jeffrey Epstein"
   }
   ```
2. Rebuild mappings: `python3 scripts/utils/build_entity_mappings.py`
3. Restart server to reload mappings
4. Test: `GET /api/entities/Je%20Je%20Epstein`

### "Entity network not displaying"

**Symptoms**:
- Network graph empty or incomplete
- Missing connections

**Solutions**:
1. Check network file: `cat data/metadata/entity_network.json | jq '.nodes | length'`
2. Verify API endpoint: `curl /api/network`
3. Check browser console for JavaScript errors
4. Clear browser cache

## Best Practices

### ✅ DO

- **Use canonical entity names** in new code
- **Check mappings file** before adding entities
- **Use API disambiguation** for user input
- **Document entity merges** in git commits
- **Validate data** after bulk operations
- **Create backups** before modifications

### ❌ DON'T

- **Hardcode entity names** (use mappings file)
- **Create duplicate entities** (check network first)
- **Use numeric IDs** (system is name-based)
- **Skip normalization** (always normalize)
- **Modify data files** without backups
- **Add entities** without checking existing data

## Testing

### Manual Testing Checklist

**1. Entity Search**
- [ ] Search for "Epstein" returns Jeffrey Epstein
- [ ] Search for "Je Je Epstein" returns Jeffrey Epstein
- [ ] Search is case-insensitive
- [ ] Partial matches work

**2. Entity Filtering**
- [ ] Filter by Black Book source works
- [ ] Filter by Flight Logs source works
- [ ] Tag filtering works
- [ ] Connection count filtering works
- [ ] Combined filters work

**3. Entity Cards**
- [ ] Click entity card opens details
- [ ] Entity name displays correctly
- [ ] Tags display correctly
- [ ] Biography preview shows
- [ ] Navigation to connections works

**4. Entity Disambiguation**
- [ ] OCR artifacts resolve to canonical names
- [ ] API auto-disambiguates entity names
- [ ] Mapping file is loaded correctly
- [ ] Fuzzy matching works

**5. Network Graph**
- [ ] All entities display
- [ ] No duplicate nodes
- [ ] Connections render correctly
- [ ] Node labels are readable

### Automated Testing

```bash
# Run validation suite
python3 scripts/data_quality/verify_normalization.py

# Expected output:
# ✅ No duplicate entities found
# ✅ All entity references valid
# ✅ Network graph consistent
# ✅ Tags validated
# ✅ Biographies validated
```

## Performance Metrics

**Entity System Performance**:
| Operation | Time | Notes |
|-----------|------|-------|
| Load all entities | <100ms | 1,639 entities |
| Search entities | <50ms | Indexed search |
| Normalize entity name | <5ms | With mappings cache |
| Get entity connections | <30ms | Network graph lookup |
| Filter entities | <80ms | Combined filters |

**Data File Sizes**:
| File | Size | Load Time |
|------|------|-----------|
| ENTITIES_INDEX.json | 450KB | <50ms |
| entity_network.json | 180KB | <30ms |
| entity_name_mappings.json | 35KB | <10ms |
| entity_biographies.json | 25KB | <10ms |

## Related Documentation

**Feature Documentation**:
- Entity Card Navigation: `/docs/archive/entities/ENTITY_CARD_NAVIGATION_IMPLEMENTATION.md`
- Entity Filtering: `/docs/archive/entities/ENTITY_FILTERING_SUMMARY.md`
- Entity Validation: `/docs/archive/entities/ENTITY_VALIDATION_QUICK_START.md`

**Research Reports**:
- Deduplication Research: `/docs/research/ENTITY_DEDUPLICATION_RESEARCH.md`
- Entity Expansion: `/docs/archive/entities/ENTITY_EXPANSION_EXECUTIVE_SUMMARY.md`
- Normalization Report: `/data/metadata/entity_normalization_final_report.md`

**Code References**:
- Entity Service: `/server/services/entity_service.py`
- Disambiguation: `/server/services/entity_disambiguation.py`
- API Routes: `/server/api_routes.py`

**Data Quality**:
- Validation Script: `/scripts/data_quality/verify_normalization.py`
- Cleanup Script: `/scripts/analysis/final_entity_cleanup.py`
- Mappings Builder: `/scripts/utils/build_entity_mappings.py`

---

**Implementation Date**: November 17-18, 2025
**Version**: 2.0.0
**Status**: ✅ Production Ready
**Total Entities**: 1,639
**Duplicates**: 0
**Developer**: Data Quality Agent (Claude Code)

**System is clean and production-ready!**
