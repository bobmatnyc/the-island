# Entity Alias System - Quick Reference

**Quick Summary**: Step-by-step guide and instructions for developers or users.

**Category**: Guide
**Status**: Active
**Last Updated**: 2025-11-24

**Key Points**:
- **William Clinton**
- `Bill Clinton` ✅
- `President Clinton` ✅
- `William J. Clinton` ✅
- `William Jefferson Clinton` ✅

---

**Status**: ✅ Operational (as of 2025-11-20)
**Coverage**: 37 entities, 53 aliases
**Auto-loaded**: Yes (server initialization)

---

## Quick Start

### Search by Alias (Automatic)

The alias system is automatically integrated into all search functions:

```bash
# Search using common names
curl "http://localhost:8081/api/entities/Bill%20Clinton"
# → Returns "William Clinton" entity

curl "http://localhost:8081/api/rag/entity/Fergie"
# → Returns documents for "Sarah Ferguson, Duchess of York"

curl "http://localhost:8081/api/entities/Prince%20Andrew"
# → Returns "Prince Andrew, Duke of York"
```

---

## Supported Aliases (37 Entities)

### Politicians
- **William Clinton**
  - `Bill Clinton` ✅
  - `President Clinton` ✅
  - `William J. Clinton` ✅
  - `William Jefferson Clinton` ✅

- **Donald Trump**
  - `President Trump` ✅
  - `Donald J. Trump` ✅
  - `The Donald` ✅

### Key Figures
- **Ghislaine Maxwell**
  - `Ghislaine` ✅
  - `Maxwell` ✅

- **Virginia Roberts Giuffre**
  - `Virginia Roberts` ✅
  - `Virginia Giuffre` ✅

### Royalty (Sample)
- **Prince Andrew, Duke of York**
  - `Prince Andrew` ✅
  - `Duke of York` ✅
  - `Andrew Mountbatten-Windsor` ✅

- **Sarah Ferguson, Duchess of York**
  - `Sarah Ferguson` ✅
  - `Fergie` ✅
  - `Duchess of York` ✅

- **Edward Stanley, Earl of Derby**
  - `Edward Stanley` ✅
  - `Earl of Derby` ✅
  - `Lord Derby` ✅

### Academic/Legal
- **Alan Dershowitz**
  - `Alan M. Dershowitz` ✅
  - `Professor Dershowitz` ✅

### Nobility (Auto-generated)
All titled individuals have aliases without their titles:
- `Prince X` → `X`
- `Lady Y` → `Y`
- `Lord Z` → `Z`
- `Duchess of ABC` → `ABC`

---

## API Usage

### Python (Backend)

```python
from services.entity_disambiguation import get_disambiguator

# Get the global disambiguator instance
disambiguator = get_disambiguator()

# Normalize a name (resolve alias)
canonical = disambiguator.normalize_name("Bill Clinton")
# Returns: "William Clinton"

# Search entity with alias support
entity_data = disambiguator.search_entity("Duke of York", entity_stats)
# Returns: Entity data for "Prince Andrew, Duke of York"

# Get all variations of a canonical name
variations = disambiguator.get_all_variations("William Clinton")
# Returns: {"William Clinton", "Bill Clinton", "President Clinton", ...}
```

### REST API

**Entity Search** (with alias resolution):
```bash
GET /api/entities/{name}

# Examples:
GET /api/entities/Bill%20Clinton
GET /api/entities/President%20Trump
GET /api/entities/Fergie
```

**RAG Entity Documents** (with alias resolution):
```bash
GET /api/rag/entity/{entity_name}

# Examples:
GET /api/rag/entity/Prince%20Andrew
GET /api/rag/entity/Duke%20of%20York
```

---

## Adding New Aliases

### Method 1: Manual Addition (Recommended)

Edit `scripts/data_quality/add_entity_aliases.py`:

```python
alias_mappings = {
    # ... existing aliases ...

    "Your Entity Name": [
        "Alias 1",
        "Alias 2",
        "Nickname"
    ],
}
```

Run the script:
```bash
python3 scripts/data_quality/add_entity_aliases.py
```

### Method 2: Direct Edit (Advanced)

Edit `data/md/entities/ENTITIES_INDEX.json`:

```json
{
  "name": "Your Entity Name",
  "aliases": ["Alias 1", "Alias 2", "Nickname"],
  ...
}
```

Restart the server to reload aliases:
```bash
# Server auto-loads aliases on startup
```

### Method 3: Programmatic (Dynamic)

```python
from services.entity_disambiguation import get_disambiguator

disambiguator = get_disambiguator()
disambiguator.add_alias("Alias Name", "Canonical Name")
```

---

## Alias System Architecture

### Data Flow

```
1. Startup
   └─> Load ENTITIES_INDEX.json
       └─> Extract aliases for each entity
           └─> Build alias → canonical mapping
               └─> Build reverse index (canonical → aliases)

2. Search Request
   └─> Check exact match
       └─> Check alias mapping
           └─> Check fuzzy match (fallback)
               └─> Return entity or 404
```

### Storage Location

**Primary Data**: `data/md/entities/ENTITIES_INDEX.json`
```json
{
  "entities": [
    {
      "name": "William Clinton",
      "aliases": ["Bill Clinton", "President Clinton", ...],
      ...
    }
  ]
}
```

**In-Memory Cache**: `server/services/entity_disambiguation.py`
- Loaded once on server startup
- Shared across all API requests
- Automatically includes aliases

---

## Testing Aliases

### Verify Alias Loading

```python
python3 << 'EOF'
import sys
sys.path.insert(0, 'server')
from services.entity_disambiguation import EntityDisambiguation

disambiguator = EntityDisambiguation()

# Test specific alias
test_alias = "Bill Clinton"
canonical = disambiguator.normalize_name(test_alias)
print(f"'{test_alias}' → '{canonical}'")

# List all loaded aliases
print(f"\nTotal aliases: {len(disambiguator.ENTITY_ALIASES)}")
EOF
```

### Test API Endpoint

```bash
# Start server
python3 server/app.py

# Test alias search
curl "http://localhost:8081/api/entities/Bill%20Clinton"
curl "http://localhost:8081/api/rag/entity/Fergie"
```

---

## Common Patterns

### Name Variations Supported

1. **Full Formal Names**
   - "William Jefferson Clinton" → "William Clinton"

2. **Common Nicknames**
   - "Bill Clinton" → "William Clinton"
   - "Fergie" → "Sarah Ferguson, Duchess of York"

3. **Titles**
   - "President Clinton" → "William Clinton"
   - "Duke of York" → "Prince Andrew, Duke of York"

4. **Shortened Forms**
   - "Prince Andrew" → "Prince Andrew, Duke of York"
   - "Sarah Ferguson" → "Sarah Ferguson, Duchess of York"

5. **Multiple Last Names**
   - "Virginia Roberts" → "Virginia Roberts Giuffre"
   - "Virginia Giuffre" → "Virginia Roberts Giuffre"

---

## Troubleshooting

### Alias Not Working

1. **Check if alias exists**:
   ```bash
   grep -i "your alias" data/md/entities/ENTITIES_INDEX.json
   ```

2. **Verify server loaded it**:
   ```python
   from services.entity_disambiguation import get_disambiguator
   d = get_disambiguator()
   print("Your Alias" in d.ENTITY_ALIASES)
   ```

3. **Restart server** (if alias was added after startup):
   ```bash
   # Ctrl+C to stop
   python3 server/app.py
   ```

### Alias Conflict

If two entities have overlapping aliases:
- The first one loaded wins (order in ENTITIES_INDEX.json)
- Consider making aliases more specific
- Use full titles to disambiguate

### Case Sensitivity

Aliases are **case-sensitive** in storage but **case-insensitive** in fallback matching:
- Stored: `"Bill Clinton"`
- Matches: `"bill clinton"`, `"BILL CLINTON"`, `"Bill Clinton"`

---

## Performance

- **Alias Loading**: ~5ms (once on startup)
- **Alias Resolution**: O(1) hash lookup (~0.001ms)
- **Memory Overhead**: ~50KB for 53 aliases
- **Search Impact**: Negligible (adds one extra lookup)

---

## Statistics (Current)

```
Total Entities:         1,637
Entities with Aliases:  37 (2.3%)
Total Aliases:          53
Alias Mappings:         825 (includes 772 existing + 53 new)
Average Aliases/Entity: 1.4
Canonical Forms:        435
```

---

## Future Enhancements

### Planned (Week 2-4)
- [ ] Add aliases for remaining 15+ priority entities
- [ ] Extract aliases from biographies automatically
- [ ] Add alias management API endpoint
- [ ] Implement alias suggestion system

### Under Consideration
- [ ] Fuzzy alias matching (typo tolerance)
- [ ] Multi-language aliases (if needed)
- [ ] Alias popularity tracking
- [ ] Crowdsourced alias submissions

---

## Support

**Implementation**: Week 1 (2025-11-20)
**Status**: Production-ready
**Coverage**: High-priority entities only
**Tested**: ✅ Unit, Integration, Manual

For issues or questions, check:
1. `WEEK_1_ENTITY_DEDUPLICATION_REPORT.md` (detailed implementation)
2. `scripts/data_quality/add_entity_aliases.py` (current aliases)
3. `server/services/entity_disambiguation.py` (implementation)

---

**Last Updated**: 2025-11-20
**Version**: 1.0
**Maintained By**: Data Engineering Team
