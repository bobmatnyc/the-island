# Flight Count Maintenance Guide

## Quick Reference

### When to Run Flight Count Fix

Run `fix_flight_counts.py` whenever:
- Flight logs are imported or updated
- Entity statistics show incorrect counts
- New flight data is added to the system
- After data migrations or cleanups

### Usage

```bash
# From project root
python3 scripts/data_quality/fix_flight_counts.py

# This will:
# 1. Count flights from flight_logs_by_flight.json
# 2. Update ENTITIES_INDEX.json
# 3. Create automatic backup
# 4. Show verification report
```

### After Running Fix

Always rebuild entity statistics:

```bash
python3 scripts/data_quality/rebuild_entity_statistics.py
```

### Validation

Check top passengers to ensure accuracy:

```bash
jq -r '.statistics | to_entries | sort_by(-.value.flight_count) | limit(10;.[]) | "\(.key): \(.value.flight_count)"' data/metadata/entity_statistics.json
```

Expected output:
```
Jeffrey Epstein: 1018
Ghislaine Maxwell: 502
Sarah Kellen: 293
Emmy Tayler: 200
Larry Visoski: 150
...
```

### Troubleshooting

**Issue**: Entity has flight_logs source but 0 flights

**Solution**: Check name variations in ENTITIES_INDEX.json. The entity name might not match the passenger name in flight logs exactly.

**Example**:
```json
{
  "name": "William Clinton",
  "normalized_name": "William Clinton",
  "aliases": ["Bill Clinton"],  // Flight logs use "Bill Clinton"
  "flights": 11
}
```

**Issue**: Duplicate entities for same person

**Solution**: Merge entities in ENTITIES_INDEX.json, update name_variations, then rerun scripts.

### File Dependencies

```
flight_logs_by_flight.json (SOURCE)
    ↓
fix_flight_counts.py (RECOUNT)
    ↓
ENTITIES_INDEX.json (UPDATED)
    ↓
rebuild_entity_statistics.py (REBUILD)
    ↓
entity_statistics.json (DISPLAY)
```

### Safety

- ✅ Automatic backups created before changes
- ✅ Backup naming: `ENTITIES_INDEX.backup_YYYYMMDD_HHMMSS.json`
- ✅ No data modification without confirmation
- ✅ Rollback possible from any backup

### Monitoring

Add to CI/CD pipeline:

```bash
# Validate flight counts match source
python3 scripts/validation/validate_flight_counts.py

# Expected: No discrepancies found
```

### Common Patterns

#### Check Single Entity
```bash
jq '.statistics["Jeffrey Epstein"]' data/metadata/entity_statistics.json
```

#### Check All Epstein Entities
```bash
jq -r '.statistics | keys[] | select(. | contains("Epstein"))' data/metadata/entity_statistics.json
```

#### Count Total Flights in System
```bash
jq '[.flights[].passenger_count] | add' data/md/entities/flight_logs_by_flight.json
```

#### Find Entities with Mismatched Counts
```bash
# Compare entity_statistics to source flight logs
python3 scripts/validation/compare_flight_counts.py
```

### Future Automation

Consider implementing:
1. Real-time sync trigger on flight log updates
2. Automated validation in pre-commit hooks
3. Monitoring dashboard for count discrepancies
4. Scheduled nightly recalculation

### Contact

For issues or questions about flight count calculations:
- Review: `docs/fixes/ENTITY_FLIGHT_COUNT_FIX_20251120.md`
- Script: `scripts/data_quality/fix_flight_counts.py`
- Validation: `scripts/data_quality/rebuild_entity_statistics.py`
