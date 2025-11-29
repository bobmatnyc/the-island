# Entity Name Aliases - Complete Reference

**Quick Summary**: **Service**: `server/services/entity_disambiguation. py`.

**Category**: Developer
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- `Je Je Epstein` → **Jeffrey Epstein**
- `Je        Je Epstein` → **Jeffrey Epstein**
- `Je Epstein` → **Jeffrey Epstein**
- `JE` → **Jeffrey Epstein**
- `J Epstein` → **Jeffrey Epstein**

---

**Last Updated**: 2025-11-16
**Service**: `server/services/entity_disambiguation.py`

This document lists all entity name variations automatically resolved by the disambiguation service.

---

## High-Profile Individuals

### Jeffrey Epstein
- `Je Je Epstein` → **Jeffrey Epstein**
- `Je        Je Epstein` → **Jeffrey Epstein**
- `Je Epstein` → **Jeffrey Epstein**
- `JE` → **Jeffrey Epstein**
- `J Epstein` → **Jeffrey Epstein**
- `Jeff Epstein` → **Jeffrey Epstein**

### Ghislaine Maxwell
- `Ghislaine Ghislaine` → **Ghislaine Maxwell**
- `Ghislaine` → **Ghislaine Maxwell**
- `G Maxwell` → **Ghislaine Maxwell**

### Bill Clinton
- `Bill Clinton` → **William Clinton**
- `President Clinton` → **William Clinton**
- `B Clinton` → **William Clinton**

### Donald Trump
- `Donald      Donald Trump` → **Donald Trump**
- `President Trump` → **Donald Trump**
- `D Trump` → **Donald Trump**

### Prince Andrew
- `Prince Andrew` → **Andrew Windsor**
- `Duke of York` → **Andrew Windsor**
- `HRH Andrew` → **Andrew Windsor**

---

## Frequent Flyers (OCR Artifacts)

These names appear in flight logs with OCR-induced duplicated first names:

### Nadia Marcinko
- `Nadia Nadia` → **Nadia Marcinko**

### Dubin Family
- `Celina      Celina Dubin` → **Celina Dubin**
- `Eva         Eva Dubin` → **Eva Dubin**
- `Glenn       Glenn Dubin` → **Glenn Dubin**
- `Jordan      Jordan Dubin` → **Jordan Dubin**
- `Maya        Maya Dubin` → **Maya Dubin**

### Others
- `Virginia   Virginia Roberts` → **Virginia Roberts**
- `Teala       Teala Davies` → **Teala Davies**
- `Emmy       Emmy Tayler` → **Emmy Tayler**

---

## Pattern Detection

The disambiguation service also auto-detects OCR patterns:

### Duplicated First Names
Any name matching the pattern `"FirstName FirstName LastName"` is automatically normalized to `"FirstName LastName"`.

**Examples**:
- `John      John Smith` → `John Smith`
- `Sarah Sarah Jones` → `Sarah Jones`

### Extra Whitespace
Excessive whitespace between names is normalized:

**Examples**:
- `John         Smith` → `John Smith`
- `Jane    Doe` → `Jane Doe`

---

## Usage Examples

### API Queries
All API endpoints that accept entity names support disambiguation:

```bash
# These all return the same entity:
curl "http://localhost:8081/api/entities/Jeffrey%20Epstein"
curl "http://localhost:8081/api/entities/Je%20Je%20Epstein"
curl "http://localhost:8081/api/entities/Je%20Epstein"
curl "http://localhost:8081/api/entities/JE"

# Response includes both searched and canonical names:
{
  "name": "Jeffrey Epstein",
  "canonical_name": "Jeffrey Epstein",
  "search_name": "Je Je Epstein",
  "total_documents": 6,
  ...
}
```

### Network Graph
The network graph automatically deduplicates entities:

```bash
# Deduplicated graph (default):
curl "http://localhost:8081/api/network?deduplicate=true"
# Returns: Jeffrey Epstein with merged connections

# Original graph (with duplicates):
curl "http://localhost:8081/api/network?deduplicate=false"
# Returns: Both "Je Je Epstein" and "Jeffrey Epstein" as separate nodes
```

---

## Adding New Aliases

To add new entity aliases, edit `server/services/entity_disambiguation.py`:

```python
class EntityDisambiguation:
    ENTITY_ALIASES: Dict[str, str] = {
        # Add new aliases here:
        "New Variation": "Canonical Name",

        # Existing aliases...
        "Je Je Epstein": "Jeffrey Epstein",
        ...
    }
```

Aliases are loaded on server startup. Restart the server after editing.

---

## Alias Statistics

### Current Coverage
- **Total Aliases Defined**: 30+
- **High-Profile Individuals**: 5 (Epstein, Maxwell, Clinton, Trump, Andrew)
- **OCR Artifacts**: 25+ (flight log duplicates)
- **Auto-Detection Patterns**: 2 (duplicated names, extra whitespace)

### Deduplication Impact
- **Network Nodes**: 387 → 292 (95 duplicates removed)
- **Reduction**: 24.5%
- **Most Common Duplicates**:
  - Epstein variations: 3 duplicates
  - Maxwell variations: 2 duplicates
  - Dubin family: 5 duplicates

---

## Technical Details

### Normalization Algorithm
1. **Direct Lookup**: Check if name exists in `ENTITY_ALIASES`
2. **Whitespace Cleanup**: Remove extra spaces and try again
3. **Pattern Detection**: Check for duplicated first names
4. **Fuzzy Fallback**: Case-insensitive search (last resort)
5. **Return Original**: If no match found, return input name

### Performance
- **Time Complexity**: O(1) for direct lookups, O(n) for fuzzy search
- **Memory**: ~5KB for alias dictionary (30+ entries)
- **Cache**: Singleton instance shared across all requests

### Error Handling
- Missing entities return 404 with suggestion message
- Invalid names return canonical form or original input
- No exceptions thrown during normalization

---

## Related Files

- **Service**: `server/services/entity_disambiguation.py`
- **Tests**: `server/test_endpoints.py` (lines 280-300)
- **Demo**: `server/demo_fixes.py` (Issue 3 demonstration)
- **API**: `server/app.py` (lines 355-379 for entity endpoint)

---

**Maintained By**: Engineering Team
**Last Alias Addition**: 2025-11-16
**Next Review**: After OCR completion (when new variations discovered)
