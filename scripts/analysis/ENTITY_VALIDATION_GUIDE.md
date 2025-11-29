# Entity Validation Guide

## Quick Reference: Identifying Invalid Entities

### ✅ Valid Entities (Keep These)
- **Person names**: "Clinton, Bill", "Maxwell, Ghislaine"
- **Individual titles**: "Dr. Smith", "Prince Andrew"
- **Name variations**: "Je Epstein", "Jeffrey Epstein"
- **Single individuals**: Any entry representing one person

### ❌ Invalid Entities (Remove These)

#### Equipment & Property
- `PORTABLES`, `EPSTEIN- PORTABLES`
- `PHONE`, `FAX`, `TV`, `COMPUTER`
- `OFFICE`, `RESIDENCE`, `APARTMENT`
- Pattern: All-caps descriptive terms

#### Companies & Organizations
- `JEGE LLC`, `ACME INC`, `XYZ CORP`
- `FOUNDATION`, `TRUST`, `ESTATE`
- Pattern: Ends with LLC, Inc, Corp, Foundation, Trust

#### Locations & Addresses
- `NEW YORK OFFICE`, `PARIS RESIDENCE`
- `PALM BEACH`, `LITTLE ST. JAMES`
- Pattern: Location names without person reference

#### Contact Categories
- `RESTAURANTS`, `HOTELS`, `SERVICES`
- `EMERGENCY CONTACTS`, `UTILITIES`
- Pattern: Plural categories or service types

## Detection Script

**Location**: `/Users/masa/Projects/Epstein/scripts/analysis/remove_invalid_entities.py`

**Usage**:
```bash
cd /Users/masa/Projects/Epstein
python3 scripts/analysis/remove_invalid_entities.py
```

**What It Does**:
1. Scans all entity files for invalid patterns
2. Creates timestamped backups before modification
3. Removes invalid entities from:
   - ENTITIES_INDEX.json
   - black_book.md
   - flight_logs.md
   - entity_network.json
   - semantic_index.json
4. Updates entity counts
5. Generates detailed log and summary

## Pattern Matching Rules

The script uses these regex patterns:

```python
INVALID_PATTERNS = [
    r"PORTABLES",                    # Equipment
    r"^[A-Z\s-]+LLC$",              # Limited Liability Companies
    r"^[A-Z\s-]+INC\.?$",           # Incorporated
    r"^[A-Z\s-]+CORP\.?$",          # Corporations
    r"^PHONE[S]?\s",                # Phone equipment
    r"^FAX[ES]?\s",                 # Fax equipment
    r"^TV\s",                       # Television
    r"^OFFICE[S]?\s",               # Office locations
    r"^RESIDENCE[S]?\s",            # Residence locations
    r"EQUIPMENT",                   # General equipment
]
```

## Manual Validation Checklist

Before accepting a new entity extraction:

- [ ] Is this a person's name? (First + Last or Last, First)
- [ ] Does it have reasonable contact info? (phone, email, address)
- [ ] Is it a title/role without a name? (❌ "ASSISTANT", "PILOT")
- [ ] Is it all-caps without clear person context? (❌ "PORTABLES")
- [ ] Does it end in LLC, Inc, Corp, Foundation? (❌ company)
- [ ] Is it a location or property? (❌ "OFFICE", "RESIDENCE")
- [ ] Does it appear in context with person data? (✅ "Smith, John")

## Ambiguous Cases

Some entries require judgment:

### Companies Named After People
- `Trump Organization` → Person: Donald Trump ✅
- `Clinton Foundation` → Person: Bill Clinton ✅
- `JEGE LLC` → No clear person ❌

**Rule**: If company is clearly tied to individual in dataset, keep the person entry, not company.

### Titles & Roles
- `Queen Elizabeth` → Keep ✅ (person with title)
- `QUEEN` → Remove ❌ (title only)
- `Dr. Fauci` → Keep ✅ (person with title)
- `DOCTOR` → Remove ❌ (role only)

**Rule**: Keep if it identifies a specific individual.

### Location + Person
- `Epstein, New York` → Keep ✅ (location suffix)
- `NEW YORK OFFICE` → Remove ❌ (location only)

**Rule**: Person name must be present.

## Post-Extraction Validation

After running entity extraction on new documents:

1. **Scan for patterns**:
   ```bash
   python3 scripts/analysis/remove_invalid_entities.py
   ```

2. **Review log**:
   ```bash
   cat /tmp/removed_entities.log
   ```

3. **Manual spot-check**:
   - Review 10-20 random entities from ENTITIES_INDEX.json
   - Check for all-caps entries
   - Verify entries have person-like attributes

4. **Statistics check**:
   - Are >90% of entities plausible person names?
   - Are there suspiciously generic entries?
   - Do entities have contact info or flight records?

## Rollback Procedure

If validation removes legitimate entities:

1. **Locate backup**:
   ```bash
   cd /Users/masa/Projects/Epstein/data/md/entities/backup_invalid_removal
   ls -lt
   ```

2. **Restore file(s)**:
   ```bash
   # Example for most recent backup
   cp ENTITIES_INDEX.json.20251117_140235 ../ENTITIES_INDEX.json
   cp black_book.md.20251117_140235 ../black_book.md
   ```

3. **Update allowlist**:
   Edit `remove_invalid_entities.py` to exclude legitimate entity:
   ```python
   ALLOWLIST = {
       "Entity Name That Was Wrongly Removed",
   }
   ```

4. **Re-run validation**:
   ```bash
   python3 scripts/analysis/remove_invalid_entities.py
   ```

## Integration with Pipeline

To add validation to entity extraction workflow:

```python
# In entity extraction script
from remove_invalid_entities import InvalidEntityRemover

# After extraction
remover = InvalidEntityRemover()
summary = remover.run()

# Check results
if summary["total_entities_removed"] > 0:
    print(f"Removed {summary['total_entities_removed']} invalid entities")
```

## Known Issues

### False Positives (Legitimate Entities Flagged)
- Currently: None identified
- Monitor: All-caps surnames (rare but possible)
- Solution: Add to allowlist in script

### False Negatives (Invalid Entities Missed)
- Equipment with person-like names
- Nicknames for properties ("The Island")
- Solution: Expand pattern list, manual review

## Contact for Questions

See `CLAUDE.md` for project documentation and resumption guide.

Last Updated: 2025-11-17
