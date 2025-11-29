# Batch Files Archival Checklist

**Date:** 2025-11-26
**Action:** Archive biography batch files after successful merge verification

---

## Pre-Archival Verification ✅

- [x] QA verification complete
- [x] Entity count verified (634/634)
- [x] Sample entities verified (batch 9 & 10)
- [x] Data integrity confirmed
- [x] Backups present (5 backup files)
- [x] Coverage meets target (79.7% > 75%)

**Status:** ✅ All checks passed - ready to archive

---

## Archival Commands

### 1. Create Archive Directory
```bash
mkdir -p data/metadata/archive/batch_biographies
```

### 2. Archive Batch Files
```bash
# Move batch 9
mv data/metadata/entity_biographies_batch9.json data/metadata/archive/batch_biographies/

# Move batch 10
mv data/metadata/entity_biographies_batch10.json data/metadata/archive/batch_biographies/

# Optional: Archive checkpoint and other batch files
mv data/metadata/entity_biographies_batch*.json data/metadata/archive/batch_biographies/
```

### 3. Verify Archive
```bash
# List archived files
ls -lh data/metadata/archive/batch_biographies/

# Verify master file still exists
ls -lh data/metadata/entity_biographies.json
```

---

## Post-Archival Verification

- [ ] Archive directory created
- [ ] Batch 9 file moved to archive
- [ ] Batch 10 file moved to archive
- [ ] Master file still present and valid
- [ ] Working directory cleaned up

### Verification Commands
```bash
# Check master file
python3 -c "import json; data=json.load(open('data/metadata/entity_biographies.json')); print(f'Entities: {len(data[\"entities\"])}')"

# Expected output: Entities: 634

# Check archive
ls data/metadata/archive/batch_biographies/ | wc -l

# Expected: At least 2 files (batch 9 & 10)
```

---

## Files to Archive

### Required
- [x] `entity_biographies_batch9.json` (149K) - New entities
- [x] `entity_biographies_batch10.json` (140K) - Updated entities

### Optional (Additional Batches)
- [ ] `entity_biographies_batch2_checkpoint.json` (197K)
- [ ] `entity_biographies_batch2a.json` (111K)
- [ ] `entity_biographies_batch2b.json` (108K)
- [ ] `entity_biographies_batch3a.json` (111K)
- [ ] `entity_biographies_batch3b.json` (110K)
- [ ] `entity_biographies_batch4.json` (224K)
- [ ] `entity_biographies_batch5.json` (223K)
- [ ] `entity_biographies_batch6.json` (219K)
- [ ] `entity_biographies_batch7.json` (228K)
- [ ] `entity_biographies_batch8.json` (230K)

**Note:** Consider archiving all batch files to clean up the working directory.

---

## Safety Checks

### Before Archiving
✅ Master file verified (entity_biographies.json)
✅ Backups present (5 backup files)
✅ QA report generated

### During Archiving
- Use `mv` not `rm` (files moved, not deleted)
- Verify each command completes successfully
- Check file exists in archive after move

### After Archiving
- Verify master file still loads
- Confirm entity count unchanged (634)
- Test sample entity retrieval

---

## Rollback Plan

If issues occur after archiving:

### Restore from Archive
```bash
# Copy batch file back from archive
cp data/metadata/archive/batch_biographies/entity_biographies_batch9.json data/metadata/

# Or restore from backup
cp data/metadata/entity_biographies_backup_20251126_195322.json data/metadata/entity_biographies.json
```

### Verify Restoration
```bash
python3 -c "import json; data=json.load(open('data/metadata/entity_biographies.json')); print(f'Restored: {len(data[\"entities\"])} entities')"
```

---

## Sign-Off

**Archival Approved By:** Claude (QA Agent)
**Date:** 2025-11-26
**QA Report:** See `BATCH_9_10_MERGE_QA_REPORT.md`

**Status:** ✅ Ready to archive

---

## Quick Commands (Copy-Paste)

```bash
# One-liner to archive all batch files
mkdir -p data/metadata/archive/batch_biographies && \
mv data/metadata/entity_biographies_batch*.json data/metadata/archive/batch_biographies/ && \
ls -lh data/metadata/archive/batch_biographies/ && \
python3 -c "import json; data=json.load(open('data/metadata/entity_biographies.json')); print(f'Master file OK: {len(data[\"entities\"])} entities')"
```

**Expected output:**
- Files moved to archive (listed)
- Master file OK: 634 entities

---

**End of Checklist**
