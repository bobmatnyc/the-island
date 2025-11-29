# Deduplication & Aliasing Implementation Guide

**Quick Summary**: Implementation summary documenting changes, files modified, and testing results.

**Category**: Implementation
**Status**: Complete
**Last Updated**: 2025-11-24

**Key Points**:
- 🎯 Quick Summary
- 📋 Week 1 Checklist: Critical Fixes
- Task 1: Merge Royal Duplicates (2-3 hours)

---

**Quick Reference for Data Engineer**
**Date**: 2025-11-19

---

## 🎯 Quick Summary

**Current State**: 1,639 entities, 86% bio coverage, 2 active duplicates
**Goal**: Merge duplicates, implement aliases, achieve 93%+ bio coverage
**Timeline**: 4 weeks
**Priority**: HIGH - Duplicate data affects entity network accuracy

---

## 📋 Week 1 Checklist: Critical Fixes

### Task 1: Merge Royal Duplicates (2-3 hours)

**Create**: `/scripts/data_quality/merge_royal_duplicates.py`

```python
#!/usr/bin/env python3
"""Merge royal title duplicate entities."""

import json
from datetime import datetime

DUPLICATES_TO_MERGE = [
    {
        "canonical": "Prince Andrew, Duke of York",
        "duplicate": "Prince Andrew",
        "aliases": ["Prince Andrew", "Duke of York"]
    },
    {
        "canonical": "Sarah Ferguson, Duchess of York",
        "duplicate": "Sarah Ferguson",
        "aliases": ["Sarah Ferguson", "Fergie"]
    }
]

def merge_entities(entities_index, canonical_name, duplicate_name, aliases):
    """Merge duplicate entity into canonical entity."""
    canonical = None
    duplicate = None

    # Find entities
    for entity in entities_index['entities'].values():
        if entity['name'] == canonical_name:
            canonical = entity
        elif entity['name'] == duplicate_name:
            duplicate = entity

    if not canonical or not duplicate:
        print(f"ERROR: Could not find both entities")
        return False

    # Merge sources
    canonical['sources'] = list(set(canonical['sources'] + duplicate['sources']))

    # Sum flights
    canonical['flights'] += duplicate['flights']

    # Merge contact info
    canonical['contact_info'].update(duplicate['contact_info'])

    # Track merge history
    if 'merged_from' not in canonical:
        canonical['merged_from'] = []
    canonical['merged_from'].append(duplicate_name)

    # Add aliases
    canonical['aliases'] = aliases

    # Remove duplicate from index
    # (Need to find by key, not name)
    dup_key = None
    for key, entity in entities_index['entities'].items():
        if entity['name'] == duplicate_name:
            dup_key = key
            break

    if dup_key:
        del entities_index['entities'][dup_key]

    print(f"✓ Merged '{duplicate_name}' into '{canonical_name}'")
    print(f"  Sources: {canonical['sources']}")
    print(f"  Flights: {canonical['flights']}")
    print(f"  Aliases: {canonical['aliases']}")

    return True

def main():
    # Load entities
    with open('data/md/entities/ENTITIES_INDEX.json', 'r') as f:
        entities_index = json.load(f)

    # Backup
    backup_file = f"data/md/entities/ENTITIES_INDEX.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(entities_index, f, indent=2)
    print(f"✓ Backup created: {backup_file}")

    # Merge duplicates
    for merge in DUPLICATES_TO_MERGE:
        merge_entities(
            entities_index,
            merge['canonical'],
            merge['duplicate'],
            merge['aliases']
        )

    # Save
    with open('data/md/entities/ENTITIES_INDEX.json', 'w') as f:
        json.dump(entities_index, f, indent=2)

    print(f"\n✓ Merges complete. Updated ENTITIES_INDEX.json")

if __name__ == '__main__':
    main()
```

**Run**:
```bash
cd /Users/masa/Projects/epstein
python3 scripts/data_quality/merge_royal_duplicates.py
```

**Verify**:
```bash
# Should return only 1 result (the canonical entity)
jq '.entities | to_entries | map(.value | select(.name | contains("Prince Andrew")))' data/md/entities/ENTITIES_INDEX.json
```

---

### Task 2: Implement Alias System (3-4 hours)

**Create**: `/scripts/data_quality/add_entity_aliases.py`

```python
#!/usr/bin/env python3
"""Add alias support to entity system."""

import json
from datetime import datetime

# Complete alias mapping for priority entities
ALIAS_MAPPINGS = {
    "Prince Andrew, Duke of York": ["Prince Andrew", "Duke of York"],
    "Sarah Ferguson, Duchess of York": ["Sarah Ferguson", "Fergie"],
    "Prince Bandar bin Sultan": ["Bandar bin Sultan"],
    "Prince Michel of Yugoslavia": ["Michel of Yugoslavia"],
    "Prince Pavlos": ["Pavlos of Greece"],
    "Prince Pierre d'Arenberg": ["Pierre d'Arenberg"],
    "Prince Salman": ["Salman bin Abdulaziz"],
    "Princess Firyal": ["Firyal of Jordan"],
    "Princess Georgina Brandolini d'Adda": ["Georgina Brandolini"],
    "Princess Hermine de Clermont-Tonnerre": ["Hermine de Clermont-Tonnerre"],
    "Princess Marie-Claire": ["Marie-Claire"],
    "Princess Olga": ["Olga"],
    "Edward Stanley, Earl of Derby": ["Edward Stanley", "Earl of Derby"],
    "Alistair McAlpine, Baron of West": ["Alistair McAlpine", "Baron McAlpine"],
    "Baron Bentinck": ["Bentinck"],
    "Baroness Francesca Theilmann": ["Francesca Theilmann"],
    "Duchess Rutland": ["Emma Rutland"],
    "William Clinton": ["Bill Clinton", "President Clinton"],
    "Donald Trump": ["President Trump"]
}

def add_aliases(entities_index):
    """Add aliases to entities."""
    added_count = 0

    for entity in entities_index['entities'].values():
        entity_name = entity['name']

        if entity_name in ALIAS_MAPPINGS:
            entity['aliases'] = ALIAS_MAPPINGS[entity_name]
            added_count += 1
            print(f"✓ Added aliases to '{entity_name}': {entity['aliases']}")

    return added_count

def build_alias_index(entities_index):
    """Build reverse alias index: alias -> canonical_name."""
    alias_index = {}

    for entity in entities_index['entities'].values():
        canonical_name = entity['name']

        for alias in entity.get('aliases', []):
            alias_index[alias] = canonical_name

    return alias_index

def main():
    # Load entities
    with open('data/md/entities/ENTITIES_INDEX.json', 'r') as f:
        entities_index = json.load(f)

    # Backup
    backup_file = f"data/md/entities/ENTITIES_INDEX.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(entities_index, f, indent=2)
    print(f"✓ Backup created: {backup_file}\n")

    # Add aliases
    count = add_aliases(entities_index)
    print(f"\n✓ Added aliases to {count} entities")

    # Save updated entities
    with open('data/md/entities/ENTITIES_INDEX.json', 'w') as f:
        json.dump(entities_index, f, indent=2)
    print(f"✓ Updated ENTITIES_INDEX.json")

    # Build and save alias index
    alias_index = build_alias_index(entities_index)
    with open('data/md/entities/ALIAS_INDEX.json', 'w') as f:
        json.dump(alias_index, f, indent=2, sort_keys=True)
    print(f"✓ Created ALIAS_INDEX.json with {len(alias_index)} aliases")

if __name__ == '__main__':
    main()
```

**Run**:
```bash
python3 scripts/data_quality/add_entity_aliases.py
```

**Verify**:
```bash
# Check that aliases were added
jq '.entities | to_entries | map(.value | select(.aliases)) | length' data/md/entities/ENTITIES_INDEX.json

# Check alias index was created
ls -lh data/md/entities/ALIAS_INDEX.json
jq 'keys | length' data/md/entities/ALIAS_INDEX.json
```

---

### Task 3: Update Search Functions (2 hours)

**File**: `/server/routes/entities.py` (or wherever entity search is)

**Before**:
```python
def search_entities(query):
    results = []
    for entity in entities:
        if query.lower() in entity['name'].lower():
            results.append(entity)
    return results
```

**After**:
```python
# Load alias index (do this once at startup)
with open('data/md/entities/ALIAS_INDEX.json', 'r') as f:
    ALIAS_INDEX = json.load(f)

def get_canonical_name(name):
    """Get canonical name from name or alias."""
    # Check if it's an alias
    if name in ALIAS_INDEX:
        return ALIAS_INDEX[name]
    return name  # Already canonical

def search_entities(query):
    results = []
    query_lower = query.lower()

    for entity in entities:
        # Search in name
        if query_lower in entity['name'].lower():
            results.append(entity)
            continue

        # Search in aliases
        if 'aliases' in entity:
            if any(query_lower in alias.lower() for alias in entity['aliases']):
                results.append(entity)

    return results

def get_entity_by_name(name):
    """Get entity by name or alias."""
    canonical_name = get_canonical_name(name)

    for entity in entities:
        if entity['name'] == canonical_name:
            return entity

    return None
```

**Test**:
```python
# These should all return the same entity
get_entity_by_name("Prince Andrew, Duke of York")
get_entity_by_name("Prince Andrew")
get_entity_by_name("Duke of York")

# Search should find via alias
search_entities("Bill Clinton")  # Should find "William Clinton"
```

---

### Task 4: Generate Merge Report (30 min)

**Create**: `/scripts/reporting/generate_merge_report.py`

```python
#!/usr/bin/env python3
"""Generate post-merge quality report."""

import json

def main():
    with open('data/md/entities/ENTITIES_INDEX.json', 'r') as f:
        entities = json.load(f)

    # Count stats
    total = len(entities['entities'])
    with_aliases = sum(1 for e in entities['entities'].values() if 'aliases' in e)
    with_bios = sum(1 for e in entities['entities'].values() if 'bio' in e)
    merged = sum(1 for e in entities['entities'].values() if e.get('merged_from'))

    print("=" * 60)
    print("ENTITY MERGE & ALIAS REPORT")
    print("=" * 60)
    print(f"Total entities: {total}")
    print(f"Entities with aliases: {with_aliases}")
    print(f"Entities with bios: {with_bios} ({with_bios/total*100:.1f}%)")
    print(f"Entities with merge history: {merged}")
    print()

    # Show alias coverage
    print("Alias Coverage:")
    for entity in entities['entities'].values():
        if 'aliases' in entity:
            print(f"  {entity['name']}: {entity['aliases']}")
    print()

    # Show recent merges
    print("Recent Merges:")
    for entity in entities['entities'].values():
        if entity.get('merged_from'):
            print(f"  {entity['name']} ← {entity['merged_from']}")

    print("=" * 60)

if __name__ == '__main__':
    main()
```

---

## 🔍 Week 2 Checklist: Misspelling Investigation

### Task 1: Identify Misspellings (2 hours)

**Create**: `/scripts/research/identify_misspellings.py`

```python
#!/usr/bin/env python3
"""Identify potential misspellings using fuzzy matching."""

import json
from difflib import get_close_matches

# Known correct entity names (from Wikipedia, billionaires list, etc.)
KNOWN_ENTITIES = [
    "Ronald Burkle",  # vs "Ronald Durkle"
    "James Kennedy",  # vs "James Kennez"
    # Add more from research
]

def find_misspellings(entities):
    """Find potential misspellings."""
    candidates = []

    for entity in entities['entities'].values():
        # Skip if has bio
        if 'bio' in entity:
            continue

        entity_name = entity['name']

        # Check for close matches
        matches = get_close_matches(entity_name, KNOWN_ENTITIES, n=1, cutoff=0.8)

        if matches:
            candidates.append({
                'current_name': entity_name,
                'suggested_correction': matches[0],
                'flights': entity['flights'],
                'sources': entity['sources']
            })

    return sorted(candidates, key=lambda x: -x['flights'])

def main():
    with open('data/md/entities/ENTITIES_INDEX.json', 'r') as f:
        entities = json.load(f)

    candidates = find_misspellings(entities)

    print(f"Found {len(candidates)} potential misspellings:\n")

    for c in candidates:
        print(f"'{c['current_name']}' → '{c['suggested_correction']}'")
        print(f"  Flights: {c['flights']}, Sources: {c['sources']}")
        print()

    # Save report
    with open('data/metadata/misspelling_candidates.json', 'w') as f:
        json.dump(candidates, f, indent=2)

if __name__ == '__main__':
    main()
```

**Manual Research Required**:
1. Google: `"Ronald Durkle" "Epstein"` → likely "Ronald Burkle"
2. Google: `"James Kennez" "Epstein"` → check court docs
3. Google: `"Sherrie Crape" "Epstein"` → verify spelling

---

## 📊 Verification Checklist

After Week 1 implementation:

- [ ] Run merge script, verify 2 duplicates merged
- [ ] Run alias script, verify 19+ entities have aliases
- [ ] Check ALIAS_INDEX.json created with 30+ aliases
- [ ] Test search: "Prince Andrew" returns canonical entity
- [ ] Test search: "Bill Clinton" finds "William Clinton"
- [ ] Verify entity count reduced by 2 (1637 total)
- [ ] Check entity network graph still renders correctly
- [ ] Generate merge report, verify no errors

---

## 🚨 Common Issues & Solutions

### Issue 1: Entity Not Found During Merge
**Symptom**: "ERROR: Could not find both entities"
**Cause**: Name doesn't match exactly (capitalization, punctuation)
**Solution**:
```python
# Debug: Find exact names
jq '.entities | to_entries | map(.value | select(.name | contains("Andrew"))) | map(.name)' data/md/entities/ENTITIES_INDEX.json
```

### Issue 2: Search Returns Duplicates
**Symptom**: Both canonical and alias return as separate results
**Cause**: Duplicate entity not removed after merge
**Solution**: Verify duplicate removed from ENTITIES_INDEX.json

### Issue 3: Alias Index Out of Sync
**Symptom**: Alias lookup fails
**Cause**: ALIAS_INDEX.json not rebuilt after adding aliases
**Solution**: Re-run `add_entity_aliases.py`

---

## 📈 Success Metrics

### Week 1 Targets
- ✅ Total entities: 1639 → 1637 (2 duplicates merged)
- ✅ Entities with aliases: 0 → 19+
- ✅ Alias index entries: 0 → 30+
- ✅ Active duplicates: 2 → 0

### Week 2 Targets
- ✅ Misspellings identified: 0 → 30-40
- ✅ Misspellings corrected: 0 → 15-20
- ✅ Bio coverage: 86% → 91%

### Week 3 Targets
- ✅ Manual bios added: 0 → 20+
- ✅ Bio coverage: 91% → 93%+

---

## 📞 Questions?

**Reference**: `/ENTITY_DATA_QUALITY_ANALYSIS.md` (comprehensive report)

**Data Quality Issues**: See sections 2 (Deduplication) and 3 (Aliasing)

**Implementation Details**: See section 5 (Technical Recommendations)

---

**Last Updated**: 2025-11-19
**Next Review**: After Week 1 implementation
