# Entity System Quick Reference

**Last Updated**: 2025-11-18
**Status**: ✅ No duplicates, system healthy

---

## TL;DR

**Duplicate Epstein Entities?** → **NO** - Already fixed 2025-11-17
**Need Aliases System?** → **NO** - Already exists (`entity_name_mappings.json`)
**Current Entity Count**: 1,639 unique entities
**Jeffrey Epstein Aliases**: 7 OCR variations → all resolved to "Jeffrey Epstein"

---

## Quick Stats

| Metric | Count |
|--------|-------|
| Total entities | 1,639 |
| Jeffrey Epstein entities | **1** (canonical) |
| Jeffrey Epstein aliases | 7 mapped variations |
| Duplicate entities | **0** ✅ |
| Name mappings | 772 |
| Network graph nodes | 284 |
| Entities with bios | 21 |
| Entities with tags | 70 |

---

## Entity ID Schemes

### Name-Based IDs (Primary)
```
"Jeffrey Epstein"           ← Used everywhere
"Epstein, Jeffrey"          ← ENTITIES_INDEX format
```

**No UUIDs or numeric IDs used.**

---

## Data Files Overview

| File | Count | What It Contains |
|------|-------|------------------|
| `ENTITIES_INDEX.json` | 1,639 | Master entity list (Black Book + Flight Logs) |
| `entity_network.json` | 284 nodes | Network visualization graph |
| `entity_name_mappings.json` | 772 | OCR fixes and name variations |
| `entity_tags.json` | 70 | Role/category tags |
| `entity_biographies.json` | 21 | Biographical data |
| `semantic_index.json` | 2,667 | Entity-to-document links |
| `timeline.json` | 98 events | Timeline with entity references |

---

## How Entity References Work

### In Flight Logs
```json
{
  "passengers": ["Jeffrey Epstein", "Ghislaine Maxwell"]
}
```

### In Network Graph
```json
{
  "id": "Jeffrey Epstein",
  "name": "Jeffrey Epstein",
  "connection_count": 262
}
```

### In Timeline
```json
{
  "related_entities": ["Jeffrey Epstein"]
}
```

### In API Calls
```
GET /api/entities/Jeffrey%20Epstein
GET /api/entities/Je%20Je%20Epstein  ← Auto-resolved to canonical
```

---

## Name Disambiguation

**Automatic Resolution Via `EntityDisambiguation`:**

```python
from services.entity_disambiguation import EntityDisambiguation

disambiguator = EntityDisambiguation()
canonical = disambiguator.normalize_name("Je Je Epstein")
# Returns: "Jeffrey Epstein"
```

**Handled Automatically by API:**
- User requests: `/api/entities/Je Je Epstein`
- API resolves to: `Jeffrey Epstein`
- Returns canonical entity data

---

## Jeffrey Epstein Data Summary

### Canonical Name
```
Primary: "Jeffrey Epstein"
Alternative: "Epstein, Jeffrey" (ENTITIES_INDEX only)
```

### Known Aliases (All Resolved)
```
"Je           Je Epstein" → "Jeffrey Epstein"
"Je          Je Epstein" → "Jeffrey Epstein"
"Je         Je Epstein" → "Jeffrey Epstein"
"Je        Je Epstein" → "Jeffrey Epstein"
"Je       Je Epstein" → "Jeffrey Epstein"
"Je Je Epstein" → "Jeffrey Epstein"
"Je Je" → "Jeffrey Epstein" (via code)
```

### Entity Data
```json
{
  "sources": ["black_book", "flight_logs"],
  "flights": 8,
  "network_connections": 262,
  "black_book_pages": "64, 67, 71, 72, 82, 85",
  "tags": ["Financier", "Associate"],
  "biography": "Yes (full bio in entity_biographies.json)"
}
```

---

## Historical Cleanup (2025-11-17)

**Problem**: OCR artifacts created duplicates
**Examples**: `"Glenn       Glenn Dubin"`, `"Je Je Epstein"`

**Solution**: Two-pass cleanup script
- Fixed 238 OCR artifacts in entity keys
- Cleaned 1,188 nested entity references
- Created backups in `data/backups/`

**Result**: Zero duplicates remaining ✅

---

## When to Add Entity Mappings

**Add to `entity_name_mappings.json` if you find**:
- OCR artifacts (whitespace duplicates)
- Alternate spellings
- Name variations in documents
- Typos in source data

**Example**:
```json
{
  "Jeffrey E. Epstein": "Jeffrey Epstein",
  "J. Epstein": "Jeffrey Epstein"
}
```

**Rebuild mappings**:
```bash
python3 scripts/utils/build_entity_mappings.py
```

---

## Common Operations

### Find Entity in Network
```javascript
const node = networkData.nodes.find(n => n.id === "Jeffrey Epstein");
```

### Get Entity Connections
```bash
curl -u user:pass 'http://localhost:8000/api/entities/Jeffrey%20Epstein/connections'
```

### Search Entities
```bash
curl -u user:pass 'http://localhost:8000/api/entities?search=Epstein'
```

### Get Entity Biography
```python
with open('data/metadata/entity_biographies.json') as f:
    bios = json.load(f)
    epstein_bio = bios['entities']['Jeffrey Epstein']
```

### Check for Duplicates
```python
from collections import Counter
with open('data/metadata/entity_network.json') as f:
    network = json.load(f)
node_ids = [n['id'] for n in network['nodes']]
duplicates = {id: count for id, count in Counter(node_ids).items() if count > 1}
# Should return: {}
```

---

## API Endpoints Reference

| Endpoint | Purpose |
|----------|---------|
| `GET /api/entities` | List entities (with filters) |
| `GET /api/entities/{name}` | Get single entity (auto-disambiguates) |
| `GET /api/entities/{name}/connections` | Get entity network |
| `GET /api/entity-biographies` | Get all biographies |
| `GET /api/entity-tags` | Get all tags |
| `POST /api/entities/enrich/batch` | Enrich multiple entities |

---

## Troubleshooting

### "Entity not found"
1. Check name capitalization: `"Jeffrey Epstein"` not `"jeffrey epstein"`
2. Try normalized form: `"Jeffrey Epstein"` not `"Epstein, Jeffrey"`
3. Check `entity_name_mappings.json` for variations
4. Use API endpoint (handles disambiguation automatically)

### "Duplicate entity detected"
1. This should not happen (all duplicates cleaned 2025-11-17)
2. If found, add mapping to `entity_name_mappings.json`
3. Run `scripts/utils/build_entity_mappings.py`
4. Report to data quality team

### "Name variation not resolved"
1. Add to `entity_name_mappings.json`
2. Rebuild mappings: `python3 scripts/utils/build_entity_mappings.py`
3. Restart server to reload mappings

---

## Best Practices

### ✅ DO
- Use canonical entity names in new code
- Check `entity_name_mappings.json` before adding entities
- Use API disambiguation for user input
- Document entity merges in git commits

### ❌ DON'T
- Hardcode entity names (use mappings file)
- Create duplicate entities (check network first)
- Use numeric IDs (system is name-based)
- Skip entity normalization (always normalize)

---

## Related Documentation

- Full research report: `/ENTITY_DEDUPLICATION_RESEARCH_REPORT.md`
- Entity cleanup summary: `/data/metadata/FINAL_ENTITY_CLEANUP_SUMMARY.md`
- Entity service: `/server/services/entity_service.py`
- Disambiguation logic: `/server/services/entity_disambiguation.py`

---

## Contact

Questions about entity system?
- Check this guide first
- Review full research report
- Examine code in `server/services/entity_service.py`
- Run verification: `python3 scripts/data_quality/verify_normalization.py`
