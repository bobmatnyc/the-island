# Entity Import Action Plan

**Status:** Ready to Execute
**Target:** Import 1,337 missing entities to achieve 100% coverage
**Current Coverage:** 18.3% (300 of 1,637 entities)

---

## Quick Reference

### Total Entity Count: 1,637

| Category | Count | Status |
|----------|-------|--------|
| **In Database** | 300 | ✅ Loaded |
| **Missing from DB** | 1,337 | ❌ Not Loaded |
| **Black Book Contacts** | 1,422 | 17.6% loaded |
| **Flight Passengers** | 258 | ~19% loaded |
| **Document Mentions** | 69 | ~72% loaded |

---

## Three-Phase Import Strategy

### Phase 1: High Priority (Immediate) 📊
**Target:** 81 entities → Coverage: 23.3%

#### Import Criteria:
- Document mentions ≥ 2 (59 entities)
- Multiple sources (22 entities)

#### Command:
```bash
python3 scripts/import_priority_entities.py \
  --phase 1 \
  --min-documents 2 \
  --min-sources 2 \
  --dry-run  # Remove after verification
```

#### Top Entities in Phase 1:
1. **Michael** - 82 document mentions
2. **Sally** - 17 document mentions
3. **Peter** - 13 document mentions
4. **Edward Epstein** - 9 document mentions
5. **Isabel Maxwell** - 3 document mentions

---

### Phase 2: Medium Priority (Short-term) 📈
**Target:** 263 entities → Coverage: 49%

#### Import Criteria:
- In flight logs (208 entities)
- In network graph (55 entities)

#### Command:
```bash
python3 scripts/import_priority_entities.py \
  --phase 2 \
  --include-flights \
  --include-network \
  --dry-run  # Remove after verification
```

#### Categories:
- Flight log passengers: 208
- Network graph nodes: 55

---

### Phase 3: Complete Coverage (Long-term) 📚
**Target:** 1,337 entities → Coverage: 100%

#### Import Criteria:
- All remaining Black Book contacts (1,172 entities)

#### Command:
```bash
python3 scripts/import_priority_entities.py \
  --phase 3 \
  --import-all-remaining \
  --source black_book \
  --batch-size 100  # Import in batches
```

---

## Import Script Template

```python
#!/usr/bin/env python3
"""
Entity Import Script - Import missing entities to database
Usage: python3 scripts/import_priority_entities.py --phase [1|2|3]
"""

import json
import sqlite3
from datetime import datetime

def import_entities(phase=1, dry_run=True):
    """Import entities based on phase criteria"""

    # Load source data
    with open('data/metadata/entity_statistics.json', 'r') as f:
        data = json.load(f)
        all_entities = data.get('statistics', {})

    # Get existing database entities
    conn = sqlite3.connect('data/metadata/entities.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM entities')
    existing_ids = {row[0] for row in cursor.fetchall()}

    # Filter entities based on phase
    to_import = []

    if phase == 1:
        # High priority: docs >= 2 OR multiple sources
        for eid, edata in all_entities.items():
            if eid in existing_ids:
                continue
            if edata.get('total_documents', 0) >= 2 or len(edata.get('sources', [])) >= 2:
                to_import.append((eid, edata))

    elif phase == 2:
        # Medium priority: flights or network
        for eid, edata in all_entities.items():
            if eid in existing_ids:
                continue
            if edata.get('flight_count', 0) > 0 or edata.get('connection_count', 0) > 0:
                to_import.append((eid, edata))

    elif phase == 3:
        # All remaining
        for eid, edata in all_entities.items():
            if eid in existing_ids:
                continue
            to_import.append((eid, edata))

    print(f"Phase {phase}: {len(to_import)} entities to import")

    if dry_run:
        print("DRY RUN - No changes made")
        print("Top 10 entities to import:")
        for eid, edata in to_import[:10]:
            print(f"  - {edata.get('name')} (docs: {edata.get('total_documents', 0)}, flights: {edata.get('flight_count', 0)})")
        return

    # Import entities
    for eid, edata in to_import:
        cursor.execute('''
            INSERT INTO entities (id, display_name, normalized_name, entity_type, aliases, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            eid,
            edata.get('name', ''),
            eid,
            'person',  # Default type
            json.dumps(edata.get('name_variations', [])),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()
    print(f"Successfully imported {len(to_import)} entities")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', type=int, required=True, choices=[1,2,3])
    parser.add_argument('--dry-run', action='store_true', default=True)
    args = parser.parse_args()

    import_entities(phase=args.phase, dry_run=args.dry_run)
```

---

## Pre-Import Checklist

### Data Validation
- [ ] Backup current database: `cp entities.db entities.db.backup`
- [ ] Verify entity_statistics.json is up-to-date
- [ ] Check for GUID field in all entities
- [ ] Validate entity name normalization

### Database Preparation
- [ ] Check database schema compatibility
- [ ] Verify entity table has required columns
- [ ] Test import script with 5 sample entities
- [ ] Confirm no duplicate entity IDs

### Quality Controls
- [ ] Entity name deduplication check
- [ ] Source attribution validation
- [ ] Type classification logic
- [ ] Alias management strategy

---

## Post-Import Verification

### Database Checks
```sql
-- Count entities after import
SELECT COUNT(*) FROM entities;

-- Verify entity types
SELECT entity_type, COUNT(*) FROM entities GROUP BY entity_type;

-- Check for nulls
SELECT COUNT(*) FROM entities WHERE display_name IS NULL OR display_name = '';

-- Verify GUIDs assigned
SELECT COUNT(*) FROM entities WHERE guid IS NULL;
```

### Data Quality Tests
```python
# Verify no duplicates
SELECT normalized_name, COUNT(*) as count
FROM entities
GROUP BY normalized_name
HAVING count > 1;

# Check source tracking
SELECT id, display_name FROM entities
WHERE NOT EXISTS (
    SELECT 1 FROM entity_sources
    WHERE entity_sources.entity_id = entities.id
);
```

---

## Files Generated

This analysis produced:

1. **ENTITY_COVERAGE_ANALYSIS.md** - Comprehensive coverage report
2. **entity_coverage_detailed.csv** - All 1,637 entities with status
3. **entity_missing_priority_list.csv** - 1,337 missing entities ranked by priority
4. **ENTITY_IMPORT_ACTION_PLAN.md** - This file (action plan)

---

## Expected Outcomes

### After Phase 1 (Immediate)
- ✅ Database coverage: 23.3% (381 entities)
- ✅ All high-priority document-mentioned entities loaded
- ✅ Multi-source entities verified

### After Phase 2 (Short-term)
- ✅ Database coverage: 49% (644 entities)
- ✅ All flight passengers loaded
- ✅ Complete network graph represented

### After Phase 3 (Long-term)
- ✅ Database coverage: 100% (1,637 entities)
- ✅ Complete Black Book imported
- ✅ Full archive represented in database

---

## Risk Mitigation

### Potential Issues
1. **Duplicate entities** - Mitigated by normalized name checks
2. **Data quality** - Mitigated by source validation
3. **Database size** - Mitigated by batch imports
4. **Name variations** - Mitigated by alias management

### Rollback Plan
```bash
# If import fails or causes issues
cp entities.db.backup entities.db
sqlite3 entities.db "DELETE FROM entities WHERE created_at > 'IMPORT_START_TIME';"
```

---

## Next Steps

1. **Immediate:** Review this action plan and approve import strategy
2. **Create script:** Develop `import_priority_entities.py` based on template
3. **Test:** Run Phase 1 with `--dry-run` flag
4. **Validate:** Check 10-20 sample entities manually
5. **Execute:** Run Phase 1 without dry-run
6. **Verify:** Confirm data quality and coverage
7. **Repeat:** Execute Phase 2 and 3 sequentially

---

## Contact & Support

For questions or issues during import:
- Review source data: `/data/metadata/entity_statistics.json`
- Check database: `/data/metadata/entities.db`
- Reference CSV reports: `/docs/entity_*.csv`
- Consult coverage analysis: `/docs/ENTITY_COVERAGE_ANALYSIS.md`

---

**Last Updated:** 2025-11-25
**Status:** Ready for Implementation
**Approval Required:** Yes (user decision on import strategy)
